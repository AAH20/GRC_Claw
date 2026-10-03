"""Base scoring agent for quality assessment."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from langchain_core.language_models import BaseLanguageModel
from pydantic import BaseModel

from ugc_marketplace.config import get_settings

logger = logging.getLogger(__name__)

T = TypeVar("T")


class AgentResult(BaseModel, Generic[T]):
    """Generic agent result wrapper."""

    success: bool = True
    data: T | None = None
    error: str | None = None
    reasoning: str = ""
    execution_time_ms: float = 0.0


class BaseScoringAgent(ABC, Generic[T]):
    """Abstract base class for quality scoring agents.

    Provides common functionality for LLM-based quality assessment.
    """

    def __init__(self) -> None:
        """Initialize the base scoring agent."""
        self.settings = get_settings()
        self._llm: BaseLanguageModel | None = None

    @property
    def llm(self) -> BaseLanguageModel:
        """Lazy-initialize the language model.

        Returns:
            The configured language model instance.
        """
        if self._llm is None:
            from langchain_openai import ChatOpenAI

            self._llm = ChatOpenAI(
                model=self.settings.llm_model,
                temperature=self.settings.llm_temperature,
                api_key=self.settings.openai_api_key or None,
            )
        return self._llm

    @abstractmethod
    async def score(
        self, content: str, context: dict[str, Any] | None = None
    ) -> AgentResult[T]:
        """Score content quality.

        Args:
            content: Content to score.
            context: Optional context for scoring.

        Returns:
            Agent result with score data.
        """
        ...
