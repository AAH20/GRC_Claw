"""Base agent class for all skills-assessor agents."""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI

from skills_assessor.config.settings import get_settings

T = TypeVar("T")
R = TypeVar("R")


class BaseAgent(ABC, Generic[T, R]):
    """Abstract base class for all skills-assessor agents.

    Provides common functionality for LLM initialization, timing, and error handling.
    All concrete agents must implement the `run` method.
    """

    def __init__(self, model: BaseChatModel | None = None) -> None:
        """Initialize the base agent.

        Args:
            model: Optional pre-configured chat model. If not provided,
                   creates a default ChatOpenAI instance from settings.
        """
        self._settings = get_settings()
        self._model = model or self._create_default_model()

    def _create_default_model(self) -> BaseChatModel:
        """Create a default chat model from application settings.

        Returns:
            BaseChatModel: Configured chat model instance.
        """
        return ChatOpenAI(
            model=self._settings.llm_model,
            temperature=self._settings.llm_temperature,
            max_tokens=self._settings.llm_max_tokens,
            api_key=self._settings.openai_api_key or None,
        )

    @property
    def model(self) -> BaseChatModel:
        """Get the chat model used by this agent.

        Returns:
            BaseChatModel: The chat model instance.
        """
        return self._model

    def _timed_run(self, func: Any, *args: Any, **kwargs: Any) -> tuple[R, float]:
        """Execute a function with timing.

        Args:
            func: The function to execute.
            *args: Positional arguments for the function.
            **kwargs: Keyword arguments for the function.

        Returns:
            tuple[R, float]: A tuple of (result, processing_time_ms).
        """
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed_ms = (time.perf_counter() - start) * 1000
        return result, elapsed_ms

    @abstractmethod
    async def run(self, input_data: T) -> R:
        """Execute the agent's primary task.

        Args:
            input_data: The input data for the agent.

        Returns:
            R: The agent's output.
        """
        ...
