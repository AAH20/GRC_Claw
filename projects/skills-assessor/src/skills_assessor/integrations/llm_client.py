"""LLM client integration for skills-assessor."""

from __future__ import annotations

from typing import TYPE_CHECKING

from langchain_openai import ChatOpenAI

if TYPE_CHECKING:
    from langchain_core.language_models import BaseChatModel

    from skills_assessor.config.settings import Settings


class LLMClient:
    """Client for interacting with LLM providers.

    Provides a unified interface for creating and managing LLM instances
    with proper configuration and error handling.
    """

    def __init__(self, settings: Settings) -> None:
        """Initialize the LLM client.

        Args:
            settings: Application settings containing LLM configuration.
        """
        self._settings = settings
        self._model: BaseChatModel | None = None

    def get_model(self) -> BaseChatModel:
        """Get or create the default chat model.

        Returns:
            BaseChatModel: Configured chat model instance.

        Raises:
            ValueError: If OpenAI API key is not configured.
        """
        if self._model is None:
            if not self._settings.openai_api_key:
                raise ValueError(
                    "OPENAI_API_KEY is required for LLM operations. "
                    "Set it in your environment or .env file."
                )
            self._model = ChatOpenAI(
                model=self._settings.llm_model,
                temperature=self._settings.llm_temperature,
                max_tokens=self._settings.llm_max_tokens,
                api_key=self._settings.openai_api_key,
            )
        return self._model

    def create_model(
        self,
        model_name: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> BaseChatModel:
        """Create a new chat model with custom parameters.

        Args:
            model_name: Override model name.
            temperature: Override temperature.
            max_tokens: Override max tokens.

        Returns:
            BaseChatModel: New chat model instance.

        Raises:
            ValueError: If OpenAI API key is not configured.
        """
        if not self._settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required for LLM operations.")

        return ChatOpenAI(
            model=model_name or self._settings.llm_model,
            temperature=temperature if temperature is not None else self._settings.llm_temperature,
            max_tokens=max_tokens or self._settings.llm_max_tokens,
            api_key=self._settings.openai_api_key,
        )

    @property
    def is_configured(self) -> bool:
        """Check if the LLM client is properly configured.

        Returns:
            bool: True if API key is set.
        """
        return bool(self._settings.openai_api_key)
