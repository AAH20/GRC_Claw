"""Base agent class for all lead scoring agents."""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Generic, TypeVar

import structlog
from langchain_core.language_models import BaseLanguageModel
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)

T = TypeVar("T", bound=BaseModel)
R = TypeVar("R", bound=BaseModel)


@dataclass
class AgentContext:
    """Context passed to agents during execution."""

    lead_id: str
    tenant_id: str
    trace_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentResult(Generic[R]):
    """Result returned by an agent."""

    success: bool
    data: R | None = None
    error: str | None = None
    latency_ms: float = 0.0
    tokens_used: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


class AgentConfig(BaseModel):
    """Configuration for an agent."""

    enabled: bool = True
    timeout_seconds: float = 60.0
    max_retries: int = 2
    temperature: float = 0.1
    max_tokens: int = 4096


class BaseAgent(ABC, Generic[T, R]):
    """Abstract base class for all lead scoring agents.

    All agents must implement the `run` method and define their
    input and output Pydantic models.
    """

    name: str = "base_agent"
    description: str = "Base agent"
    config: AgentConfig = Field(default_factory=AgentConfig)

    def __init__(
        self,
        llm: BaseLanguageModel | None = None,
        config: AgentConfig | None = None,
    ) -> None:
        """Initialize the agent.

        Args:
            llm: Language model for LLM-powered agents.
            config: Agent-specific configuration overrides.
        """
        self.llm = llm
        if config:
            self.config = config
        self._logger = logger.bind(agent=self.name)

    @property
    @abstractmethod
    def input_model(self) -> type[T]:
        """Pydantic model for agent input."""
        ...

    @property
    @abstractmethod
    def output_model(self) -> type[R]:
        """Pydantic model for agent output."""
        ...

    @abstractmethod
    async def run(self, input_data: T, context: AgentContext) -> AgentResult[R]:
        """Execute the agent's primary logic.

        Args:
            input_data: Validated input data.
            context: Execution context with lead/tenant info.

        Returns:
            AgentResult containing the output or error.
        """
        ...

    async def execute(self, input_data: T, context: AgentContext) -> AgentResult[R]:
        """Execute the agent with timing, logging, and error handling.

        Args:
            input_data: Validated input data.
            context: Execution context.

        Returns:
            AgentResult with execution metadata.
        """
        if not self.config.enabled:
            return AgentResult(
                success=False,
                error=f"Agent '{self.name}' is disabled",
            )

        start = time.monotonic()
        self._logger.info(
            "agent_started",
            lead_id=context.lead_id,
            trace_id=context.trace_id,
        )

        try:
            result = await self.run(input_data, context)
            elapsed = (time.monotonic() - start) * 1000
            result.latency_ms = elapsed

            self._logger.info(
                "agent_completed",
                lead_id=context.lead_id,
                trace_id=context.trace_id,
                latency_ms=elapsed,
                success=result.success,
            )
            return result

        except Exception as exc:
            elapsed = (time.monotonic() - start) * 1000
            self._logger.error(
                "agent_failed",
                lead_id=context.lead_id,
                trace_id=context.trace_id,
                latency_ms=elapsed,
                error=str(exc),
            )
            return AgentResult(
                success=False,
                error=str(exc),
                latency_ms=elapsed,
            )

    def validate_input(self, data: dict[str, Any]) -> T:
        """Validate raw input data against the agent's input model.

        Args:
            data: Raw input dictionary.

        Returns:
            Validated input model instance.

        Raises:
            ValueError: If validation fails.
        """
        return self.input_model.model_validate(data)
