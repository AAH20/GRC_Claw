"""Base agent for creator analytics with common functionality."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import structlog
from langchain_core.language_models import BaseLanguageModel

logger = structlog.get_logger(__name__)


class BaseCreatorAgent(ABC):
    """Abstract base class for creator analytics agents.

    Provides common functionality for LLM initialization and execution.
    """

    def __init__(self) -> None:
        """Initialize the base creator agent."""
        self._llm: BaseLanguageModel | None = None

    @property
    def llm(self) -> BaseLanguageModel:
        """Lazy-initialize the language model.

        Returns:
            The configured language model instance.
        """
        if self._llm is None:
            from langchain_openai import ChatOpenAI

            from ugc_marketplace.config import get_settings

            settings = get_settings()
            self._llm = ChatOpenAI(
                model=settings.llm_model,
                temperature=settings.llm_temperature,
                api_key=settings.openai_api_key or None,
            )
        return self._llm

    @abstractmethod
    async def execute(self, input_data: Any) -> Any:
        """Execute the agent's primary task.

        Args:
            input_data: Input data for the agent task.

        Returns:
            Agent output.
        """
        ...
