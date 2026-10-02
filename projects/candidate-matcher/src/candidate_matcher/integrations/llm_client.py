"""LLM client integration using LangChain."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from candidate_matcher.config.exceptions import LLMConnectionError
from candidate_matcher.config.logging_config import get_logger
from candidate_matcher.config.settings import Settings, get_settings

logger = get_logger(__name__)


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients."""

    @abstractmethod
    async def generate(
        self,
        messages: list[BaseMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Generate a response from the LLM.

        Args:
            messages: Chat messages to send.
            temperature: Optional temperature override.
            max_tokens: Optional max tokens override.

        Returns:
            The generated response text.
        """
        ...

    @abstractmethod
    async def generate_structured(
        self,
        messages: list[BaseMessage],
        schema: dict[str, Any],
    ) -> dict[str, Any]:
        """Generate a structured response from the LLM.

        Args:
            messages: Chat messages to send.
            schema: JSON schema for the expected output.

        Returns:
            The structured response as a dictionary.
        """
        ...


class LangChainLLMClient(BaseLLMClient):
    """LLM client backed by LangChain chat models."""

    def __init__(self, settings: Optional[Settings] = None) -> None:
        """Initialize the LLM client.

        Args:
            settings: Application settings. Uses global settings if not provided.
        """
        self._settings = settings or get_settings()
        self._model = self._create_model()

    def _create_model(self) -> BaseChatModel:
        """Create the LangChain chat model.

        Returns:
            Configured chat model instance.

        Raises:
            LLMConnectionError: If the model cannot be created.
        """
        try:
            if self._settings.llm_provider == "openai":
                return ChatOpenAI(
                    model=self._settings.llm_model,
                    temperature=self._settings.llm_temperature,
                    max_tokens=self._settings.llm_max_tokens,
                    api_key=self._settings.openai_api_key or None,
                )
            raise LLMConnectionError(
                f"Unsupported LLM provider: {self._settings.llm_provider}"
            )
        except Exception as e:
            if isinstance(e, LLMConnectionError):
                raise
            raise LLMConnectionError(f"Failed to create LLM model: {e}") from e

    async def generate(
        self,
        messages: list[BaseMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Generate a response from the LLM.

        Args:
            messages: Chat messages to send.
            temperature: Optional temperature override.
            max_tokens: Optional max tokens override.

        Returns:
            The generated response text.

        Raises:
            LLMConnectionError: If generation fails.
        """
        try:
            if temperature is not None:
                self._model.temperature = temperature
            if max_tokens is not None:
                self._model.max_tokens = max_tokens

            response = await self._model.ainvoke(messages)
            return response.content if isinstance(response.content, str) else str(response.content)
        except Exception as e:
            logger.error("llm_generation_failed", error=str(e))
            raise LLMConnectionError(f"LLM generation failed: {e}") from e

    async def generate_structured(
        self,
        messages: list[BaseMessage],
        schema: dict[str, Any],
    ) -> dict[str, Any]:
        """Generate a structured response from the LLM.

        Args:
            messages: Chat messages to send.
            schema: JSON schema for the expected output.

        Returns:
            The structured response as a dictionary.

        Raises:
            LLMConnectionError: If generation fails.
        """
        try:
            structured_model = self._model.with_structured_output(schema)
            response = await structured_model.ainvoke(messages)
            if isinstance(response, dict):
                return response
            return response.model_dump() if hasattr(response, "model_dump") else dict(response)
        except Exception as e:
            logger.error("llm_structured_generation_failed", error=str(e))
            raise LLMConnectionError(f"Structured LLM generation failed: {e}") from e


class MockLLMClient(BaseLLMClient):
    """Mock LLM client for testing and development."""

    def __init__(self, responses: Optional[list[str]] = None) -> None:
        """Initialize the mock client.

        Args:
            responses: Optional predefined responses to cycle through.
        """
        self._responses = responses or ["Mock response"]
        self._call_count = 0

    async def generate(
        self,
        messages: list[BaseMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Return a mock response.

        Args:
            messages: Ignored.
            temperature: Ignored.
            max_tokens: Ignored.

        Returns:
            A mock response string.
        """
        response = self._responses[self._call_count % len(self._responses)]
        self._call_count += 1
        return response

    async def generate_structured(
        self,
        messages: list[BaseMessage],
        schema: dict[str, Any],
    ) -> dict[str, Any]:
        """Return a mock structured response.

        Args:
            messages: Ignored.
            schema: JSON schema to base the response on.

        Returns:
            A mock structured response.
        """
        self._call_count += 1
        return {"result": "mock", "confidence": 0.95}


def create_llm_client(settings: Optional[Settings] = None) -> BaseLLMClient:
    """Factory function to create an LLM client.

    Args:
        settings: Application settings. Uses global settings if not provided.

    Returns:
        An LLM client instance.
    """
    settings = settings or get_settings()
    if settings.llm_provider == "mock":
        return MockLLMClient()
    return LangChainLLMClient(settings)
