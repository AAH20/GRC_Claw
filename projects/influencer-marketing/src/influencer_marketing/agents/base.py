"""Base agent class for all marketing agents."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Generic, TypeVar

import structlog
from langchain_openai import ChatOpenAI

if TYPE_CHECKING:
    from langchain_core.language_models import BaseChatModel

logger = structlog.get_logger(__name__)

T = TypeVar("T")
R = TypeVar("R")


@dataclass
class AgentConfig:
    """Configuration for an agent."""

    name: str
    description: str
    max_retries: int = 3
    timeout_seconds: int = 60
    temperature: float = 0.7
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentResult(Generic[R]):
    """Result from an agent execution."""

    success: bool
    data: R | None = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseAgent(ABC, Generic[T, R]):
    """Abstract base class for all marketing agents."""

    def __init__(self, config: AgentConfig, llm: BaseChatModel | None = None) -> None:
        self.config = config
        self.llm = llm or self._default_llm()
        self.logger = logger.bind(agent=config.name)

    def _default_llm(self) -> BaseChatModel:
        """Create default LLM instance."""
        return ChatOpenAI(
            model="gpt-4o",
            temperature=self.config.temperature,
            max_tokens=4096,
        )

    @abstractmethod
    async def execute(self, input_data: T) -> AgentResult[R]:
        """Execute the agent's primary task.

        Args:
            input_data: Input data for the agent to process.

        Returns:
            AgentResult containing the execution result.
        """
        ...

    @abstractmethod
    async def validate_input(self, input_data: T) -> bool:
        """Validate input data before execution.

        Args:
            input_data: Input data to validate.

        Returns:
            True if input is valid, False otherwise.
        """
        ...

    async def run(self, input_data: T) -> AgentResult[R]:
        """Run the agent with validation and error handling.

        Args:
            input_data: Input data for the agent.

        Returns:
            AgentResult with success status and data or error.
        """
        self.logger.info("Starting agent execution")

        if not await self.validate_input(input_data):
            self.logger.warning("Input validation failed")
            return AgentResult(success=False, error="Input validation failed")

        try:
            result = await self.execute(input_data)
            self.logger.info("Agent execution completed", success=result.success)
            return result
        except Exception as exc:
            self.logger.error("Agent execution failed", error=str(exc))
            return AgentResult(success=False, error=str(exc))
