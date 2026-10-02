"""Base agent class for all content discovery agents."""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

import structlog
from deepagents import create_deep_agent

logger = structlog.get_logger()

InputT = TypeVar("InputT")
OutputT = TypeVar("OutputT")


class BaseAgent(ABC, Generic[InputT, OutputT]):
    """Abstract base class for all content discovery agents.

    All agents inherit from this class and implement the execute method.
    Provides common functionality for logging, metrics, and error handling.
    """

    def __init__(self, name: str, llm: Any | None = None) -> None:
        """Initialize the base agent.

        Args:
            name: Human-readable agent name.
            llm: Optional LLM instance for agent reasoning.
        """
        self.name = name
        self.llm = llm
        self._agent = self._build_agent()

    def _build_agent(self):
        """Build the underlying deep agent instance.

        Returns:
            Configured deep agent instance.
        """
        return create_deep_agent(
            model=self.llm,
            tools=self._get_tools(),
            name=self.name,
        )

    def _get_tools(self) -> list[Any]:
        """Get the list of tools available to this agent.

        Returns:
            list[Any]: List of tool instances.
        """
        return []

    @abstractmethod
    async def execute(self, input_data: InputT) -> OutputT:
        """Execute the agent's primary task.

        Args:
            input_data: Input data for the agent.

        Returns:
            OutputT: Agent execution result.

        Raises:
            AgentExecutionError: If agent execution fails.
        """
        ...

    async def run(self, input_data: InputT) -> OutputT:
        """Run the agent with timing and error handling.

        Args:
            input_data: Input data for the agent.

        Returns:
            OutputT: Agent execution result.
        """
        start = time.monotonic()
        try:
            result = await self.execute(input_data)
            elapsed = (time.monotonic() - start) * 1000
            logger.info(
                "agent_execution_completed",
                agent=self.name,
                elapsed_ms=round(elapsed, 2),
            )
            return result
        except Exception as exc:
            elapsed = (time.monotonic() - start) * 1000
            logger.error(
                "agent_execution_failed",
                agent=self.name,
                elapsed_ms=round(elapsed, 2),
                error=str(exc),
            )
            raise AgentExecutionError(f"Agent {self.name} failed: {exc}") from exc


class AgentExecutionError(Exception):
    """Raised when an agent fails to execute successfully."""
