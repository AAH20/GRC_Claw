"""Base agent for content discovery with common functionality."""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

import structlog
from deepagents import create_deep_agent

logger = structlog.get_logger(__name__)

InputT = TypeVar("InputT")
OutputT = TypeVar("OutputT")


class AgentExecutionError(Exception):
    """Exception raised when agent execution fails."""

    def __init__(self, message: str, agent_name: str, details: dict[str, Any] | None = None) -> None:
        """Initialize the execution error.

        Args:
            message: Error message.
            agent_name: Name of the agent that failed.
            details: Optional error details.
        """
        super().__init__(message)
        self.agent_name = agent_name
        self.details = details or {}


class BaseAgent(ABC, Generic[InputT, OutputT]):
    """Abstract base class for content discovery agents.

    Provides common functionality for LLM-based agents including
    execution timing, error handling, and result construction.
    """

    def __init__(self) -> None:
        """Initialize the base agent."""
        self._agent = self._build_agent()
        self._tasks_processed = 0
        self._error_count = 0
        self._last_activity: float | None = None

    @abstractmethod
    def _build_agent(self) -> Any:
        """Build the LangChain DeepAgent.

        Returns:
            Configured DeepAgent instance.
        """
        ...

    @abstractmethod
    async def execute(self, input_data: InputT) -> OutputT:
        """Execute the agent's primary task.

        Args:
            input_data: Input data for the agent task.

        Returns:
            Agent output.
        """
        ...

    async def _timed_execute(self, input_data: InputT, method_name: str) -> OutputT:
        """Execute with timing and error handling.

        Args:
            input_data: Input data.
            method_name: Name of the method being executed.

        Returns:
            Agent output.

        Raises:
            AgentExecutionError: If execution fails.
        """
        start_time = time.monotonic()
        try:
            result = await self.execute(input_data)
            elapsed_ms = (time.monotonic() - start_time) * 1000
            self._tasks_processed += 1
            self._last_activity = time.time()
            logger.info(
                "Agent execution completed",
                agent=self.__class__.__name__,
                method=method_name,
                elapsed_ms=elapsed_ms,
            )
            return result
        except Exception as exc:
            self._error_count += 1
            elapsed_ms = (time.monotonic() - start_time) * 1000
            logger.error(
                "Agent execution failed",
                agent=self.__class__.__name__,
                method=method_name,
                error=str(exc),
                elapsed_ms=elapsed_ms,
            )
            raise AgentExecutionError(
                message=str(exc),
                agent_name=self.__class__.__name__,
                details={"method": method_name, "elapsed_ms": elapsed_ms},
            ) from exc

    def get_status(self) -> dict[str, Any]:
        """Get agent status.

        Returns:
            Agent status dictionary.
        """
        return {
            "agent_name": self.__class__.__name__,
            "status": "idle" if self._last_activity is None else "running",
            "last_activity": self._last_activity,
            "tasks_processed": self._tasks_processed,
            "error_count": self._error_count,
        }
