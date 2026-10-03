"""Base agent class for member verification agents."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from langchain_core.language_models import BaseLanguageModel
from pydantic import BaseModel, Field

T = TypeVar("T", bound=BaseModel)
R = TypeVar("R", bound=BaseModel)


class AgentConfig(BaseModel):
    """Configuration for an agent."""

    name: str = Field(..., description="Agent name")
    description: str = Field(default="", description="Agent description")
    model: str = Field(default="gpt-4o-mini", description="LLM model to use")
    temperature: float = Field(default=0.1, description="LLM temperature")
    max_iterations: int = Field(default=10, description="Maximum agent iterations")
    timeout_seconds: int = Field(default=30, description="Agent timeout in seconds")


class BaseAgent(ABC, Generic[T, R]):
    """Abstract base class for all verification agents."""

    def __init__(
        self,
        config: AgentConfig,
        llm: BaseLanguageModel | None = None,
    ) -> None:
        """Initialize the agent.

        Args:
            config: Agent configuration.
            llm: Optional language model instance.
        """
        self.config = config
        self.llm = llm
        self._status: str = "available"
        self._last_used: str | None = None

    @property
    def status(self) -> str:
        """Get current agent status.

        Returns:
            Current status string.
        """
        return self._status

    @property
    def last_used(self) -> str | None:
        """Get last usage timestamp.

        Returns:
            ISO format timestamp of last usage.
        """
        return self._last_used

    @abstractmethod
    async def run(self, input_data: T) -> R:
        """Execute the agent's primary function.

        Args:
            input_data: Input data for the agent.

        Returns:
            Agent output.
        """
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the agent is healthy and ready.

        Returns:
            True if the agent is operational.
        """
        ...

    def get_capabilities(self) -> list[str]:
        """Get list of agent capabilities.

        Returns:
            List of capability strings.
        """
        return []

    def _mark_used(self) -> None:
        """Mark the agent as recently used."""
        from datetime import datetime

        self._last_used = datetime.utcnow().isoformat()
