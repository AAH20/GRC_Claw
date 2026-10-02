"""Base agent module with shared functionality for all event management agents."""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Generic, TypeVar

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)

T = TypeVar("T", bound=BaseModel)
R = TypeVar("R", bound=BaseModel)


@dataclass
class AgentContext:
    """Context passed to agents during execution."""

    event_id: str
    user_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    trace_id: str | None = None


class AgentConfig(BaseModel):
    """Configuration for an agent."""

    model: str = "gpt-4"
    max_tokens: int = 4096
    temperature: float = 0.7
    timeout_seconds: int = 120
    retry_attempts: int = 3
    retry_delay_seconds: float = 1.0


class AgentResult(BaseModel):
    """Standard result wrapper for agent outputs."""

    success: bool
    data: dict[str, Any] = Field(default_factory=dict)
    message: str = ""
    execution_time_ms: float = 0.0
    agent_name: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class BaseAgent(ABC, Generic[T, R]):
    """Abstract base class for all event management agents."""

    def __init__(self, config: AgentConfig | None = None) -> None:
        self.config = config or AgentConfig()
        self.logger = logger.bind(agent=self.__class__.__name__)

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the agent's name."""
        ...

    @abstractmethod
    async def execute(self, input_data: T, context: AgentContext) -> R:
        """Execute the agent's primary task."""
        ...

    async def run(self, input_data: T, context: AgentContext) -> AgentResult:
        """Run the agent with timing, logging, and error handling."""
        start_time = time.monotonic()
        self.logger.info(
            "agent_started",
            agent=self.name,
            event_id=context.event_id,
            trace_id=context.trace_id,
        )

        try:
            result = await self.execute(input_data, context)
            execution_time = (time.monotonic() - start_time) * 1000

            self.logger.info(
                "agent_completed",
                agent=self.name,
                event_id=context.event_id,
                execution_time_ms=execution_time,
            )

            return AgentResult(
                success=True,
                data=result.model_dump() if isinstance(result, BaseModel) else {"result": result},
                message=f"{self.name} completed successfully",
                execution_time_ms=execution_time,
                agent_name=self.name,
            )

        except Exception as exc:
            execution_time = (time.monotonic() - start_time) * 1000
            self.logger.error(
                "agent_failed",
                agent=self.name,
                event_id=context.event_id,
                error=str(exc),
                execution_time_ms=execution_time,
            )

            return AgentResult(
                success=False,
                data={},
                message=f"{self.name} failed: {exc}",
                execution_time_ms=execution_time,
                agent_name=self.name,
                metadata={"error_type": type(exc).__name__},
            )
