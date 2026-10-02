"""Base agent module providing the foundation for all SEO agents."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Generic, TypeVar

import structlog

logger = structlog.get_logger(__name__)

T = TypeVar("T")


@dataclass
class AgentResult(Generic[T]):
    """Result container for agent execution.

    Attributes:
        success: Whether the agent execution was successful.
        data: The result data if successful.
        error: Error message if execution failed.
        metadata: Additional metadata about the execution.
        execution_time_ms: Execution time in milliseconds.
        timestamp: When the result was created.
    """

    success: bool
    data: T | None = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    execution_time_ms: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)


class BaseAgent(ABC, Generic[T]):
    """Abstract base class for all SEO agents.

    Provides common functionality for agent execution, error handling,
    and result formatting.
    """

    def __init__(self, name: str, config: dict[str, Any] | None = None) -> None:
        """Initialize the base agent.

        Args:
            name: Human-readable agent name.
            config: Optional configuration dictionary.
        """
        self.name = name
        self.config = config or {}
        self.logger = logger.bind(agent=name)

    @abstractmethod
    async def execute(self, **kwargs: Any) -> AgentResult[T]:
        """Execute the agent's primary task.

        Args:
            **kwargs: Agent-specific input parameters.

        Returns:
            AgentResult containing the execution outcome.
        """
        ...

    async def run(self, **kwargs: Any) -> AgentResult[T]:
        """Run the agent with timing and error handling.

        Args:
            **kwargs: Agent-specific input parameters.

        Returns:
            AgentResult containing the execution outcome.
        """
        import time

        start_time = time.perf_counter()
        self.logger.info("Agent execution started", kwargs=kwargs)

        try:
            result = await self.execute(**kwargs)
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            result.execution_time_ms = elapsed_ms

            if result.success:
                self.logger.info(
                    "Agent execution completed",
                    execution_time_ms=elapsed_ms,
                )
            else:
                self.logger.warning(
                    "Agent execution failed",
                    error=result.error,
                    execution_time_ms=elapsed_ms,
                )

            return result

        except Exception as exc:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            self.logger.error(
                "Agent execution raised exception",
                error=str(exc),
                execution_time_ms=elapsed_ms,
            )
            return AgentResult(
                success=False,
                error=f"Agent execution failed: {exc}",
                execution_time_ms=elapsed_ms,
            )
