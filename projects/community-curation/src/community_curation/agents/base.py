"""Base agent class for community curation agents."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

import structlog
from deepagents import create_deep_agent

logger = structlog.get_logger(__name__)

T = TypeVar("T")
R = TypeVar("R")


class BaseCurationAgent(ABC, Generic[T, R]):
    """Base class for all curation agents using LangChain DeepAgents."""

    def __init__(self, name: str, description: str, model: str | None = None) -> None:
        """Initialize the base agent.

        Args:
            name: Agent name.
            description: Agent description.
            model: Optional LLM model override.
        """
        self.name = name
        self.description = description
        self.model = model
        self._agent: DeepAgent | None = None
        self._initialize_agent()

    def _initialize_agent(self) -> None:
        """Initialize the LangChain DeepAgent."""
        try:
            self._agent = create_deep_agent(
                name=self.name,
                system_prompt=self.description,
            )
            logger.info("agent_initialized", agent=self.name)
        except Exception as exc:
            logger.error("agent_init_failed", agent=self.name, error=str(exc))
            self._agent = None

    @property
    def is_available(self) -> bool:
        """Check if the agent is available.

        Returns:
            True if the agent is initialized and ready.
        """
        return self._agent is not None

    @abstractmethod
    async def run(self, input_data: T) -> R:
        """Execute the agent on the given input.

        Args:
            input_data: Input data for the agent.

        Returns:
            Agent output.
        """
        ...

    async def health_check(self) -> dict[str, Any]:
        """Check agent health.

        Returns:
            Health status dictionary.
        """
        return {
            "name": self.name,
            "status": "available" if self.is_available else "unavailable",
            "description": self.description,
        }
