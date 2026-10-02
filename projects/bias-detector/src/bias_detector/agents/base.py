"""Base agent class for bias detection agents."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from langchain_deepagents import DeepAgent

T = TypeVar("T")


class BaseBiasAgent(ABC, DeepAgent, Generic[T]):
    """Abstract base class for all bias detection agents.

    All bias detection agents inherit from this class and implement
    the ``analyze`` method using LangChain DeepAgents for orchestration.

    Attributes:
        name: Human-readable agent name.
        description: Agent description for logging and debugging.
    """

    name: str = "base_agent"
    description: str = "Base bias detection agent"

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the base bias agent.

        Args:
            **kwargs: Additional keyword arguments passed to DeepAgent.
        """
        super().__init__(name=self.name, description=self.description, **kwargs)

    @abstractmethod
    async def analyze(self, data: T) -> Any:
        """Run analysis on the provided data.

        Args:
            data: Input data for analysis.

        Returns:
            Analysis result.
        """
        ...
