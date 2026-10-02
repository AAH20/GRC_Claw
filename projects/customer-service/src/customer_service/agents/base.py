"""Base Agent — Abstract base class for all customer service agents."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import structlog
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI

logger = structlog.get_logger(__name__)


class BaseAgent(ABC):
    """Abstract base class for all customer service agents.

    Provides common functionality for LLM-based agents including
    model initialization, prompt building, and response parsing.
    """

    def __init__(self, name: str, model: str = "gpt-4o", temperature: float = 0.1) -> None:
        """Initialize the base agent.

        Args:
            name: Agent identifier name.
            model: The LLM model to use.
            temperature: Sampling temperature for the LLM.
        """
        self._name = name
        self._model_name = model
        self._temperature = temperature
        self._llm: BaseChatModel | None = None

    @property
    def name(self) -> str:
        """Get the agent name."""
        return self._name

    @property
    def model_name(self) -> str:
        """Get the model name."""
        return self._model_name

    def _get_llm(self) -> BaseChatModel:
        """Get or initialize the LLM instance.

        Returns:
            Initialized LLM chat model.
        """
        if self._llm is None:
            self._llm = ChatOpenAI(
                model=self._model_name,
                temperature=self._temperature,
            )
        return self._llm

    async def _call_llm(self, prompt: str) -> str:
        """Call the LLM with a prompt.

        Args:
            prompt: The prompt to send to the LLM.

        Returns:
            The LLM response text.

        Raises:
            RuntimeError: If the LLM call fails.
        """
        try:
            llm = self._get_llm()
            response = await llm.ainvoke(prompt)
            return str(response.content)
        except Exception as e:
            logger.error(
                "LLM call failed",
                agent=self._name,
                error=str(e),
            )
            raise RuntimeError(f"LLM call failed for agent {self._name}: {e}") from e

    @abstractmethod
    async def run(self, *args: Any, **kwargs: Any) -> Any:
        """Execute the agent's primary function.

        Args:
            *args: Positional arguments.
            **kwargs: Keyword arguments.

        Returns:
            Agent-specific result.
        """
        ...
