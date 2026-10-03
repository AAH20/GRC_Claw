"""Base agent class for moderation analytics agents."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Generic, TypeVar

import structlog
from langchain_openai import ChatOpenAI
from moderation_analytics.config import get_settings

if TYPE_CHECKING:
    from langchain_core.language_models import BaseLanguageModel

logger = structlog.get_logger(__name__)

T = TypeVar("T")


class BaseAgent(ABC, Generic[T]):
    """Abstract base class for all moderation analytics agents.

    Provides common functionality for LLM initialization, logging, and error handling.
    All concrete agents must implement the `run` method.
    """

    def __init__(self, name: str, llm: BaseLanguageModel | None = None) -> None:
        """Initialize the base agent.

        Args:
            name: Human-readable agent name for logging.
            llm: Optional pre-configured language model. If None, creates default.
        """
        self.name = name
        self.logger = logger.bind(agent=name)
        self._llm = llm
        self._settings = get_settings()

    @property
    def llm(self) -> BaseLanguageModel:
        """Get or create the language model.

        Returns:
            BaseLanguageModel: Configured language model instance.
        """
        if self._llm is None:
            self._llm = ChatOpenAI(
                model=self._settings.langchain_model,
                temperature=self._settings.langchain_temperature,
                max_tokens=self._settings.langchain_max_tokens,
            )
        return self._llm

    @abstractmethod
    async def run(self, **kwargs: Any) -> T:
        """Execute the agent's primary task.

        Args:
            **kwargs: Agent-specific input parameters.

        Returns:
            T: Agent-specific output type.

        Raises:
            NotImplementedError: Must be implemented by subclasses.
        """
        raise NotImplementedError

    def _log_start(self, **kwargs: Any) -> None:
        """Log agent execution start.

        Args:
            **kwargs: Input parameters for context.
        """
        self.logger.info(f"Starting {self.name}", **kwargs)

    def _log_complete(self, result: Any = None) -> None:
        """Log agent execution completion.

        Args:
            result: Optional result summary.
        """
        self.logger.info(
            f"Completed {self.name}",
            result_type=type(result).__name__ if result else None,
        )

    def _log_error(self, error: Exception, **kwargs: Any) -> None:
        """Log agent execution error.

        Args:
            error: The exception that occurred.
            **kwargs: Additional context.
        """
        self.logger.error(
            f"Error in {self.name}",
            error=str(error),
            error_type=type(error).__name__,
            **kwargs,
        )
