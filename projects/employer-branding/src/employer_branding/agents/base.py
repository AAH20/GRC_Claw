"""Base agent class for all employer branding agents."""

from __future__ import annotations

import structlog
from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI

from employer_branding.config import get_settings

logger = structlog.get_logger(__name__)

T = TypeVar("T")


class BaseAgent(ABC, Generic[T]):
    """Abstract base class for all employer branding agents.

    Provides common functionality for LLM initialization, logging,
    and error handling across all agent implementations.
    """

    def __init__(self, model: BaseChatModel | None = None) -> None:
        """Initialize the base agent.

        Args:
            model: Optional pre-configured chat model. If not provided,
                   creates a default OpenAI model from settings.
        """
        self._settings = get_settings()
        self._model = model or self._create_default_model()
        self._logger = logger.bind(agent=self.__class__.__name__)

    def _create_default_model(self) -> BaseChatModel:
        """Create a default chat model from application settings.

        Returns:
            Configured BaseChatModel instance.

        Raises:
            ValueError: If OpenAI API key is not configured.
        """
        if not self._settings.openai_api_key:
            raise ValueError(
                "OPENAI_API_KEY is required. Set it in environment variables or .env file."
            )
        return ChatOpenAI(
            model=self._settings.openai_model,
            api_key=self._settings.openai_api_key,
            temperature=0.7,
            max_tokens=4096,
        )

    @property
    def model(self) -> BaseChatModel:
        """Get the chat model used by this agent."""
        return self._model

    @property
    def logger(self) -> structlog.BoundLogger:
        """Get the structured logger for this agent."""
        return self._logger

    @abstractmethod
    async def run(self, *args: Any, **kwargs: Any) -> T:
        """Execute the agent's primary task.

        Args:
            *args: Positional arguments for the task.
            **kwargs: Keyword arguments for the task.

        Returns:
            The result of type T.

        Raises:
            NotImplementedError: Must be implemented by subclasses.
        """
        raise NotImplementedError

    async def health_check(self) -> dict[str, Any]:
        """Check agent health and model availability.

        Returns:
            Dictionary with health status information.
        """
        return {
            "agent": self.__class__.__name__,
            "status": "healthy",
            "model": self._settings.openai_model,
        }
