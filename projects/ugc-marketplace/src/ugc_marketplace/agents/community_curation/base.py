"""Base curation agent with common functionality."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

import structlog
from deepagents import create_deep_agent

logger = structlog.get_logger(__name__)

T = TypeVar("T")
R = TypeVar("R")


class BaseCurationAgent(ABC, Generic[T, R]):
    """Abstract base class for community curation agents.

    Provides common functionality for content curation, ranking,
    and quality assessment.
    """

    def __init__(self) -> None:
        """Initialize the base curation agent."""
        self._agent = self._build_agent()
        self._tasks_processed = 0
        self._error_count = 0

    @abstractmethod
    def _build_agent(self) -> Any:
        """Build the LangChain DeepAgent.

        Returns:
            Configured DeepAgent instance.
        """
        ...

    @abstractmethod
    async def execute(self, input_data: T) -> R:
        """Execute the agent's primary task.

        Args:
            input_data: Input data for the agent task.

        Returns:
            Agent output.
        """
        ...

    def get_status(self) -> dict[str, Any]:
        """Get agent status.

        Returns:
            Agent status dictionary.
        """
        return {
            "agent_name": self.__class__.__name__,
            "tasks_processed": self._tasks_processed,
            "error_count": self._error_count,
        }
