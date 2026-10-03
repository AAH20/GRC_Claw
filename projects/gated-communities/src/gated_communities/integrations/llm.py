"""LLM integration client for LangChain DeepAgents."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from tier_management.config.logging_config import get_logger
from tier_management.config.settings import get_settings

if TYPE_CHECKING:
    from langchain_core.language_models import BaseLanguageModel

logger = get_logger(__name__)


class LLMClient:
    """Client for interacting with LLM providers via LangChain.

    Provides a unified interface for creating and configuring
    language models used by the tier management agents.
    """

    def __init__(self, settings: Any = None) -> None:
        """Initialize the LLM client.

        Args:
            settings: Application settings. Uses global settings if None.
        """
        self.settings = settings or get_settings()
        self._model: BaseLanguageModel | None = None

    def get_model(self) -> BaseLanguageModel:
        """Get or create the language model instance.

        Returns:
            Configured LangChain language model.

        Raises:
            ValueError: If OpenAI API key is not configured.
        """
        if self._model is not None:
            return self._model

        if not self.settings.openai_api_key:
            raise ValueError(
                "OPENAI_API_KEY is required for LLM integration. "
                "Set TIER_MANAGEMENT_OPENAI_API_KEY environment variable."
            )

        try:
            from langchain_openai import ChatOpenAI

            self._model = ChatOpenAI(
                model=self.settings.llm_model,
                temperature=self.settings.llm_temperature,
                max_tokens=self.settings.llm_max_tokens,
                api_key=self.settings.openai_api_key,
            )
            logger.info("llm_model_initialized", model=self.settings.llm_model)
        except ImportError as e:
            raise ValueError(
                "langchain-openai is required for LLM integration. "
                "Install with: pip install langchain-openai"
            ) from e

        return self._model

    async def health_check(self) -> bool:
        """Check if the LLM service is accessible.

        Returns:
            True if the LLM is reachable, False otherwise.
        """
        try:
            model = self.get_model()
            return model is not None
        except (ValueError, ImportError):
            return False
