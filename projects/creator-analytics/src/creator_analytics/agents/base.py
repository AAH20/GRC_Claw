"""Base agent class for all creator analytics agents."""

from abc import ABC, abstractmethod
from typing import Any, Optional
import structlog
from langchain_core.language_models import BaseLanguageModel

try:
    from langchain_deepagents import DeepAgent
except ImportError:
    DeepAgent = None  # type: ignore

logger = structlog.get_logger(__name__)


class BaseCreatorAgent(ABC):
    """Base class for all creator analytics agents using LangChain DeepAgents."""

    def __init__(
        self,
        llm: Optional[BaseLanguageModel] = None,
        name: str = "base_agent",
    ) -> None:
        """Initialize the base agent.

        Args:
            llm: Language model to use for agent reasoning.
            name: Human-readable name for the agent.
        """
        self.llm = llm
        self.name = name
        self._agent: Optional[DeepAgent] = None
        self._initialize_agent()

    def _initialize_agent(self) -> None:
        """Initialize the DeepAgent with tools and instructions."""
        if DeepAgent is None:
            logger.warning(
                f"langchain_deepagents not installed; agent {self.name} running without LLM"
            )
            return
        try:
            self._agent = DeepAgent(
                name=self.name,
                instructions=self._get_instructions(),
                tools=self._get_tools(),
                llm=self.llm,
            )
            logger.info(f"Agent {self.name} initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize agent {self.name}: {e}")
            raise

    @abstractmethod
    def _get_instructions(self) -> str:
        """Get the system instructions for the agent."""
        pass

    @abstractmethod
    def _get_tools(self) -> list[Any]:
        """Get the tools available to the agent."""
        pass

    @abstractmethod
    async def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Run the agent with the given input data.

        Args:
            input_data: Input data for the agent to process.

        Returns:
            Agent output as a dictionary.
        """
        pass

    async def arun(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Async wrapper for run method.

        Args:
            input_data: Input data for the agent to process.

        Returns:
            Agent output as a dictionary.
        """
        return await self.run(input_data)
