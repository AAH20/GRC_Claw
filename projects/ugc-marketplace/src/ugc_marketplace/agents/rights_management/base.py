"""Base agent for rights management with common functionality."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from langchain_core.language_models import BaseLanguageModel

from ugc_marketplace.config import get_settings

InputT = TypeVar("InputT")
OutputT = TypeVar("OutputT")


class BaseAgent(ABC, Generic[InputT, OutputT]):
    """Abstract base class for rights management agents.

    Provides common functionality for LLM initialization and execution.
    """

    def __init__(self) -> None:
        """Initialize the base agent."""
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
                max_tokens=self.settings.llm_max_tokens,
                api_key=self.settings.openai_api_key or None,
            )
        return self._llm

    @abstractmethod
    async def execute(self, input_data: InputT) -> OutputT:
        """Execute the agent's primary task.

        Args:
            input_data: Input data for the agent task.

        Returns:
            Agent output.
        """
        ...
