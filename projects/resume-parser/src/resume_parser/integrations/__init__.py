"""LLM and external service integrations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from langchain_openai import ChatOpenAI

if TYPE_CHECKING:
    from resume_parser.config import Settings


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients."""

    @abstractmethod
    def generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate a response from the LLM.

        Args:
            prompt: The input prompt.
            **kwargs: Additional generation parameters.

        Returns:
            str: Generated response text.
        """
        ...

    @abstractmethod
    async def agenerate(self, prompt: str, **kwargs: Any) -> str:
        """Asynchronously generate a response from the LLM.

        Args:
            prompt: The input prompt.
            **kwargs: Additional generation parameters.

        Returns:
            str: Generated response text.
        """
        ...


class OpenAIClient(BaseLLMClient):
    """OpenAI LLM client using LangChain."""

    def __init__(self, settings: Settings) -> None:
        """Initialize the OpenAI client.

        Args:
            settings: Application settings.
        """
        self._settings = settings
        self._client = ChatOpenAI(
            api_key=settings.openai_api_key,
            model=settings.openai_model,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens,
        )

    def generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate a response from OpenAI.

        Args:
            prompt: The input prompt.
            **kwargs: Additional generation parameters.

        Returns:
            str: Generated response text.
        """
        response = self._client.invoke(prompt, **kwargs)
        return str(response.content)

    async def agenerate(self, prompt: str, **kwargs: Any) -> str:
        """Asynchronously generate a response from OpenAI.

        Args:
            prompt: The input prompt.
            **kwargs: Additional generation parameters.

        Returns:
            str: Generated response text.
        """
        response = await self._client.ainvoke(prompt, **kwargs)
        return str(response.content)


def create_llm_client(settings: Settings) -> BaseLLMClient:
    """Factory function to create an LLM client.

    Args:
        settings: Application settings.

    Returns:
        BaseLLMClient: Configured LLM client.
    """
    return OpenAIClient(settings)
