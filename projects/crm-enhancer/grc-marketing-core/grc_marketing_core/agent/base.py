"""Base agent framework for GRC Marketing Core.

Provides the foundational agent abstractions: BaseAgent, AgentOrchestrator,
AgentTool, and supporting data structures.
"""

from __future__ import annotations

import asyncio
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Coroutine, Generic, TypeVar

import structlog

logger = structlog.get_logger(__name__)

T = TypeVar("T")


class AgentStatus(str, Enum):
    """Agent execution status."""

    IDLE = "idle"
    RUNNING = "running"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class AgentContext:
    """Context passed through agent execution pipeline."""

    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str | None = None
    conversation_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    parent_context: AgentContext | None = None
    depth: int = 0
    max_depth: int = 10
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    trace_id: str | None = None
    span_id: str | None = None

    def child_context(self, **overrides: Any) -> AgentContext:
        """Create a child context for nested agent execution."""
        data = {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "conversation_id": self.conversation_id,
            "metadata": dict(self.metadata),
            "parent_context": self,
            "depth": self.depth + 1,
            "max_depth": self.max_depth,
            "created_at": datetime.now(timezone.utc),
            "trace_id": self.trace_id,
            "span_id": self.span_id,
        }
        data.update(overrides)
        return AgentContext(**data)


@dataclass
class AgentResult(Generic[T]):
    """Result of an agent execution."""

    success: bool
    data: T | None = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    execution_time_ms: float = 0.0
    tokens_used: int = 0
    agent_id: str | None = None
    status: AgentStatus = AgentStatus.COMPLETED

    @property
    def failed(self) -> bool:
        return not self.success


@dataclass
class AgentTool:
    """Definition of a tool that an agent can invoke."""

    name: str
    description: str
    parameters: dict[str, Any] = field(default_factory=dict)
    handler: Callable[..., Coroutine[Any, Any, Any]] | None = None
    is_async: bool = True
    timeout_seconds: float = 30.0
    retry_count: int = 3
    metadata: dict[str, Any] = field(default_factory=dict)

    async def execute(self, **kwargs: Any) -> Any:
        """Execute the tool handler with given parameters."""
        if self.handler is None:
            raise ToolError(f"Tool '{self.name}' has no handler")
        if self.is_async:
            return await asyncio.wait_for(self.handler(**kwargs), timeout=self.timeout_seconds)
        loop = asyncio.get_event_loop()
        return await asyncio.wait_for(
            loop.run_in_executor(None, lambda: self.handler(**kwargs)),
            timeout=self.timeout_seconds,
        )


class AgentError(Exception):
    """Base exception for agent errors."""


class ToolError(AgentError):
    """Exception raised when a tool execution fails."""


class OrchestrationError(AgentError):
    """Exception raised when orchestration fails."""


class BaseAgent(ABC, Generic[T]):
    """Abstract base class for all agents in the GRC Marketing Core.

    Subclasses must implement the `run` method and may override
    `setup` and `teardown` for lifecycle management.
    """

    def __init__(
        self,
        name: str,
        description: str = "",
        tools: list[AgentTool] | None = None,
        max_iterations: int = 10,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.name = name
        self.description = description
        self.tools = tools or []
        self.max_iterations = max_iterations
        self.metadata = metadata or {}
        self._status = AgentStatus.IDLE
        self._logger = logger.bind(agent=name)

    @property
    def status(self) -> AgentStatus:
        return self._status

    @property
    def tool_map(self) -> dict[str, AgentTool]:
        return {t.name: t for t in self.tools}

    async def setup(self, context: AgentContext) -> None:
        """Initialize agent resources before execution."""

    async def teardown(self, context: AgentContext) -> None:
        """Clean up agent resources after execution."""

    @abstractmethod
    async def run(self, input_data: T, context: AgentContext) -> AgentResult[Any]:
        """Execute the agent's primary logic.

        Args:
            input_data: The input data for this agent.
            context: The execution context.

        Returns:
            AgentResult containing the execution outcome.
        """

    async def execute_tool(self, tool_name: str, **kwargs: Any) -> Any:
        """Execute a registered tool by name."""
        tool = self.tool_map.get(tool_name)
        if tool is None:
            raise ToolError(f"Tool '{tool_name}' not found on agent '{self.name}'")
        return await tool.execute(**kwargs)

    async def __call__(self, input_data: T, context: AgentContext | None = None) -> AgentResult[Any]:
        """Execute the agent with full lifecycle management."""
        ctx = context or AgentContext()
        self._status = AgentStatus.RUNNING
        start = datetime.now(timezone.utc)
        try:
            await self.setup(ctx)
            result = await self.run(input_data, ctx)
            elapsed = (datetime.now(timezone.utc) - start).total_seconds() * 1000
            result.execution_time_ms = elapsed
            result.agent_id = self.name
            self._status = AgentStatus.COMPLETED if result.success else AgentStatus.FAILED
            return result
        except Exception as exc:
            elapsed = (datetime.now(timezone.utc) - start).total_seconds() * 1000
            self._status = AgentStatus.FAILED
            self._logger.error("agent_execution_failed", error=str(exc))
            return AgentResult(
                success=False,
                error=str(exc),
                execution_time_ms=elapsed,
                agent_id=self.name,
                status=AgentStatus.FAILED,
            )
        finally:
            await self.teardown(ctx)


class AgentOrchestrator:
    """Orchestrates multi-agent execution with routing and coordination.

    Supports sequential, parallel, and conditional agent execution patterns.
    """

    def __init__(
        self,
        agents: dict[str, BaseAgent[Any]] | None = None,
        max_concurrent: int = 5,
        enable_caching: bool = True,
    ) -> None:
        self.agents = agents or {}
        self.max_concurrent = max_concurrent
        self.enable_caching = enable_caching
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._logger = logger.bind(component="orchestrator")
        self._execution_history: list[dict[str, Any]] = []

    def register_agent(self, name: str, agent: BaseAgent[Any]) -> None:
        """Register an agent with the orchestrator."""
        self.agents[name] = agent
        self._logger.info("agent_registered", agent=name)

    def unregister_agent(self, name: str) -> None:
        """Remove an agent from the orchestrator."""
        self.agents.pop(name, None)

    async def execute_single(
        self,
        agent_name: str,
        input_data: Any,
        context: AgentContext | None = None,
    ) -> AgentResult[Any]:
        """Execute a single agent by name."""
        agent = self.agents.get(agent_name)
        if agent is None:
            raise OrchestrationError(f"Agent '{agent_name}' not registered")
        ctx = context or AgentContext()
        async with self._semaphore:
            result = await agent(input_data, ctx)
        self._execution_history.append({
            "agent": agent_name,
            "success": result.success,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        return result

    async def execute_parallel(
        self,
        tasks: list[tuple[str, Any]],
        context: AgentContext | None = None,
    ) -> list[AgentResult[Any]]:
        """Execute multiple agents in parallel."""
        ctx = context or AgentContext()
        coros = [self.execute_single(name, data, ctx) for name, data in tasks]
        return await asyncio.gather(*coros, return_exceptions=False)

    async def execute_sequential(
        self,
        steps: list[tuple[str, Any]],
        context: AgentContext | None = None,
    ) -> list[AgentResult[Any]]:
        """Execute agents sequentially, passing results forward."""
        ctx = context or AgentContext()
        results: list[AgentResult[Any]] = []
        current_input: Any = None
        for i, (agent_name, step_input) in enumerate(steps):
            input_data = current_input if i > 0 and current_input is not None else step_input
            result = await self.execute_single(agent_name, input_data, ctx)
            results.append(result)
            if not result.success:
                break
            current_input = result.data
        return results

    async def execute_pipeline(
        self,
        pipeline: list[dict[str, Any]],
        initial_input: Any,
        context: AgentContext | None = None,
    ) -> AgentResult[Any]:
        """Execute a pipeline with conditional routing.

        Each step in the pipeline is a dict with:
            - agent: agent name
            - condition: optional callable to check if step should run
            - transform: optional callable to transform input
        """
        ctx = context or AgentContext()
        current = initial_input
        for step in pipeline:
            condition = step.get("condition")
            if condition and not condition(current):
                continue
            transform = step.get("transform")
            if transform:
                current = transform(current)
            result = await self.execute_single(step["agent"], current, ctx)
            if not result.success:
                return result
            current = result.data
        return AgentResult(success=True, data=current)

    def get_execution_history(self) -> list[dict[str, Any]]:
        """Return the execution history of this orchestrator."""
        return list(self._execution_history)
