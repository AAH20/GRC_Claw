"""Base agent class for community governance agents."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from langchain_core.language_models import BaseLanguageModel
from langchain_core.messages import BaseMessage

from community_governance.config.logging_config import get_logger

logger = get_logger(__name__)

T = TypeVar("T")
R = TypeVar("R")


class BaseAgent(ABC, Generic[T, R]):
    """Abstract base class for all governance agents.

    Provides common functionality for agent initialization, execution,
    and error handling. Uses LangChain DeepAgents for LLM-powered
    decision making.
    """

    def __init__(
        self,
        llm: BaseLanguageModel | None = None,
        name: str = "base_agent",
        **kwargs: Any,
    ) -> None:
        """Initialize the base agent.

        Args:
            llm: Optional language model for agent reasoning.
            name: Human-readable agent name.
            **kwargs: Additional agent-specific configuration.
        """
        self.llm = llm
        self.name = name
        self.config = kwargs
        self._is_initialized = False
        logger.info(f"Agent '{name}' initialized", agent_name=name)

    async def initialize(self) -> None:
        """Initialize the agent and its dependencies."""
        if not self._is_initialized:
            await self._setup()
            self._is_initialized = True
            logger.info(f"Agent '{self.name}' setup complete", agent_name=self.name)

    async def _setup(self) -> None:
        """Setup agent-specific resources. Override in subclasses."""
        pass

    @abstractmethod
    async def execute(self, input_data: T) -> R:
        """Execute the agent's primary function.

        Args:
            input_data: The input data for the agent.

        Returns:
            The agent's output.
        """
        ...

    async def health_check(self) -> dict[str, Any]:
        """Check the health of the agent.

        Returns:
            A dictionary with health status information.
        """
        return {
            "agent_name": self.name,
            "status": "healthy" if self._is_initialized else "uninitialized",
            "llm_configured": self.llm is not None,
        }

    def _build_messages(self, system_prompt: str, user_message: str) -> list[BaseMessage]:
        """Build a message list for LLM invocation.

        Args:
            system_prompt: The system prompt for the LLM.
            user_message: The user message for the LLM.

        Returns:
            A list of LangChain messages.
        """
        from langchain_core.messages import HumanMessage, SystemMessage

        return [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message),
        ]
