"""Base agent class for job description optimization agents."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, TypeVar

from langchain_core.language_models import BaseLanguageModel
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel

from job_description_optimizer.config import Settings

InputT = TypeVar("InputT", bound=BaseModel)
OutputT = TypeVar("OutputT", bound=BaseModel)


class BaseAgent(ABC, Generic[InputT, OutputT]):
    """Abstract base class for all optimization agents.

    All agents inherit from this class and implement the analyze method
    using LangChain DeepAgents patterns.
    """

    def __init__(
        self,
        llm: BaseLanguageModel,
        settings: Settings,
    ) -> None:
        """Initialize the base agent.

        Args:
            llm: Language model instance for agent reasoning.
            settings: Application settings.
        """
        self.llm = llm
        self.settings = settings
        self._system_prompt = self._build_system_prompt()

    @property
    @abstractmethod
    def name(self) -> str:
        """Get the agent name."""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """Get the agent description."""
        ...

    @abstractmethod
    def _build_system_prompt(self) -> str:
        """Build the system prompt for this agent.

        Returns:
            System prompt string.
        """
        ...

    @abstractmethod
    async def analyze(self, input_data: InputT) -> OutputT:
        """Analyze the input data and return results.

        Args:
            input_data: Input data for analysis.

        Returns:
            Analysis results.
        """
        ...

    async def _invoke_llm(self, prompt: str) -> str:
        """Invoke the LLM with a prompt.

        Args:
            prompt: User prompt to send to the LLM.

        Returns:
            LLM response text.
        """
        messages = [
            SystemMessage(content=self._system_prompt),
            HumanMessage(content=prompt),
        ]
        response = await self.llm.ainvoke(messages)
        return str(response.content)

    def get_capabilities(self) -> list[str]:
        """Get list of agent capabilities.

        Returns:
            List of capability strings.
        """
        return ["analysis", "optimization"]

    def to_info(self) -> Dict[str, Any]:
        """Convert agent info to dictionary.

        Returns:
            Dictionary with agent information.
        """
        return {
            "name": self.name,
            "description": self.description,
            "capabilities": self.get_capabilities(),
            "status": "available",
        }
