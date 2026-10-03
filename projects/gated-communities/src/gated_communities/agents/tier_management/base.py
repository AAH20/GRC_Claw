"""Base agent class for tier management agents."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from langchain_core.language_models import BaseLanguageModel
from langchain_core.tools import BaseTool

from tier_management.config.logging_config import get_logger

logger = get_logger(__name__)

T = TypeVar("T")
R = TypeVar("R")


class BaseAgent(ABC, Generic[T, R]):
    """Abstract base class for all tier management agents.

    Provides common functionality for agent initialization, LLM binding,
    and execution lifecycle management using LangChain DeepAgents.

    Type Parameters:
        T: The input type the agent accepts.
        R: The output type the agent produces.
    """

    def __init__(
        self,
        name: str,
        llm: BaseLanguageModel | None = None,
        tools: list[BaseTool] | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the base agent.

        Args:
            name: Human-readable agent name.
            llm: Optional LangChain language model instance.
            tools: Optional list of tools available to the agent.
            **kwargs: Additional configuration parameters.
        """
        self.name = name
        self.llm = llm
        self.tools = tools or []
        self.config = kwargs
        self._initialized = False
        logger.info("agent_initialized", agent_name=self.name)

    async def initialize(self) -> None:
        """Initialize the agent and its resources.

        Subclasses should override this to perform async initialization
        such as loading policies, connecting to databases, etc.
        """
        self._initialized = True
        logger.info("agent_ready", agent_name=self.name)

    @abstractmethod
    async def execute(self, input_data: T) -> R:
        """Execute the agent's primary function.

        Args:
            input_data: The input data for the agent to process.

        Returns:
            The agent's output.

        Raises:
            NotImplementedError: Must be implemented by subclasses.
        """
        raise NotImplementedError

    async def health_check(self) -> bool:
        """Check if the agent is healthy and ready.

        Returns:
            True if the agent is operational, False otherwise.
        """
        return self._initialized

    def __repr__(self) -> str:
        """Return string representation of the agent."""
        return f"{self.__class__.__name__}(name='{self.name}')"
