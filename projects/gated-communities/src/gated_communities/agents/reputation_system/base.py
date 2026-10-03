"""Base agent class for reputation system agents."""

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from langchain_core.language_models import BaseLanguageModel
from pydantic import BaseModel
from reputation_system.config.settings import Settings, get_settings

InputT = TypeVar("InputT", bound=BaseModel)
OutputT = TypeVar("OutputT", bound=BaseModel)


class BaseAgent(ABC, Generic[InputT, OutputT]):
    """Base class for all reputation system agents."""

    def __init__(
        self,
        settings: Settings | None = None,
        llm: BaseLanguageModel | None = None,
    ) -> None:
        """Initialize the agent.

        Args:
            settings: Application settings.
            llm: Language model for agent reasoning.
        """
        self.settings = settings or get_settings()
        self.llm = llm
        self._initialize_agent()

    def _initialize_agent(self) -> None:
        """Initialize the underlying agent framework."""
        try:
            from langchain_core.prompts import ChatPromptTemplate

            self._agent_type = "react"
            self._prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", self._get_system_prompt()),
                    ("human", "{input}"),
                ]
            )
        except ImportError:
            self._agent_type = "simple"

    @abstractmethod
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the agent."""
        ...

    @abstractmethod
    async def run(self, input_data: InputT) -> OutputT:
        """Execute the agent with the given input.

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
            "agent": self.__class__.__name__,
            "status": "healthy",
            "type": getattr(self, "_agent_type", "unknown"),
        }
