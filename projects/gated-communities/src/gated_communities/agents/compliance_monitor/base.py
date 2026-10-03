"""Base agent class for compliance monitoring agents."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Generic, TypeVar

import structlog
from deepagents import create_deep_agent

if TYPE_CHECKING:
    from deepagents import DeepAgent  # noqa: F401

logger = structlog.get_logger(__name__)

T = TypeVar("T")
R = TypeVar("R")


class BaseComplianceAgent(ABC, Generic[T, R]):
    """Base class for all compliance monitoring agents.

    Provides common functionality for LangChain DeepAgents-based agents
    including logging, error handling, and result validation.

    Type Parameters:
        T: Input type for the agent.
        R: Output type for the agent.
    """

    def __init__(self, name: str, model: str = "gpt-4o") -> None:
        """Initialize the base compliance agent.

        Args:
            name: Agent name for identification.
            model: LLM model to use for agent reasoning.
        """
        self.name = name
        self.model = model
        self._agent: Any | None = None
        self._logger = logger.bind(agent=name)

    @property
    def agent(self) -> Any:
        """Get or create the LangChain DeepAgent instance.

        Returns:
            Configured DeepAgent instance.
        """
        if self._agent is None:
            self._agent = self._create_agent()
        return self._agent

    def _create_agent(self) -> Any:
        """Create the LangChain DeepAgent instance.

        Returns:
            Configured DeepAgent instance.
        """
        return create_deep_agent(
            name=self.name,
            model=self.model,
            tools=self._get_tools(),
        )

    def _get_tools(self) -> list[Any]:
        """Get the tools available to this agent.

        Returns:
            List of LangChain tools.
        """
        return []

    @abstractmethod
    async def run(self, input_data: T) -> R:
        """Execute the agent's primary function.

        Args:
            input_data: Input data for the agent.

        Returns:
            Agent execution result.
        """
        ...

    async def safe_run(self, input_data: T) -> R:
        """Execute the agent with error handling and logging.

        Args:
            input_data: Input data for the agent.

        Returns:
            Agent execution result.

        Raises:
            AgentExecutionError: If agent execution fails.
        """
        self._logger.info(
            "Starting agent execution", input_type=type(input_data).__name__
        )
        try:
            result = await self.run(input_data)
            self._logger.info("Agent execution completed successfully")
            return result
        except Exception as exc:
            self._logger.error("Agent execution failed", error=str(exc))
            raise AgentExecutionError(f"Agent {self.name} failed: {exc}") from exc


class AgentExecutionError(Exception):
    """Exception raised when an agent fails to execute."""
