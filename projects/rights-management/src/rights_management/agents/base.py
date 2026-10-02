"""Base agent class for rights-management agents."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from langchain_core.language_models import BaseLanguageModel

from rights_management.config.settings import get_settings

InputT = TypeVar("InputT")
OutputT = TypeVar("OutputT")


class BaseAgent(ABC, Generic[InputT, OutputT]):
    """Abstract base class for all rights-management agents.

    Each agent wraps a LangChain DeepAgents instance and exposes a
    single ``run`` method that accepts a typed input and returns a
    typed output.
    """

    def __init__(self, llm: BaseLanguageModel | None = None) -> None:
        """Initialize the agent.

        Args:
            llm: Optional language model. If not provided, one is
                created lazily from the application settings.
        """
        self._settings = get_settings()
        self._llm = llm
        self._agent: Any = None

    def _get_llm(self) -> BaseLanguageModel:
        """Get or create the language model.

        Returns:
            The language model instance.
        """
        if self._llm is None:
            self._llm = self._create_llm()
        return self._llm

    def _get_agent(self) -> Any:
        """Get or create the underlying agent.

        Returns:
            The configured agent instance.
        """
        if self._agent is None:
            self._agent = self._build_agent()
        return self._agent

    def _create_llm(self) -> BaseLanguageModel:
        """Create a default language model from settings.

        Returns:
            A configured language model instance.
        """
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=self._settings.llm_model,
            api_key=self._settings.llm_api_key,
        )

    @abstractmethod
    def _build_agent(self) -> Any:
        """Build the underlying LangChain agent.

        Returns:
            The configured agent instance.
        """
        ...

    @abstractmethod
    async def run(self, payload: InputT) -> OutputT:
        """Execute the agent on the given input.

        Args:
            payload: The typed input for the agent.

        Returns:
            The typed output from the agent.
        """
        ...
