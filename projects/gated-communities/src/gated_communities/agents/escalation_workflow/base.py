"""Base agent class for escalation workflow agents."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Generic, TypeVar

import structlog
from escalation_workflow.config import get_settings
from langchain_openai import ChatOpenAI

if TYPE_CHECKING:
    from langchain_core.language_models import BaseChatModel

logger = structlog.get_logger(__name__)

T = TypeVar("T")
R = TypeVar("R")


class BaseAgent(ABC, Generic[T, R]):
    """Abstract base class for all escalation workflow agents.

    Provides common functionality for LLM initialization, logging,
    and error handling across all agent implementations.
    """

    def __init__(self, model: BaseChatModel | None = None) -> None:
        """Initialize the base agent.

        Args:
            model: Optional pre-configured chat model. If not provided,
                creates a default ChatOpenAI instance from settings.
        """
        self.settings = get_settings()
        self.model = model or self._create_default_model()
        self.logger = logger.bind(agent=self.__class__.__name__)

    def _create_default_model(self) -> BaseChatModel:
        """Create a default chat model from application settings.

        Returns:
            BaseChatModel: Configured chat model instance.
        """
        return ChatOpenAI(
            model=self.settings.llm_model,
            temperature=self.settings.llm_temperature,
            api_key=self.settings.openai_api_key or None,
        )

    @abstractmethod
    async def run(self, input_data: T) -> R:
        """Execute the agent's primary function.

        Args:
            input_data: Input data for the agent to process.

        Returns:
            R: The agent's output.
        """
        ...

    async def health_check(self) -> dict[str, Any]:
        """Check agent health and readiness.

        Returns:
            dict: Health status information.
        """
        return {
            "agent": self.__class__.__name__,
            "status": "healthy",
            "model": self.settings.llm_model,
        }
