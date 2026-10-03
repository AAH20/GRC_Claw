"""LLM client integration for AI-powered agents."""

from __future__ import annotations

import logging

from recruitment_platform.integrations.base import BaseIntegration

logger = logging.getLogger(__name__)


class LLMClient(BaseIntegration):
    """Client for interacting with LLM APIs (OpenAI, etc.).

    Provides a unified interface for text generation,
    embeddings, and other LLM operations.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4",
        base_url: str = "https://api.openai.com/v1",
    ) -> None:
        """Initialize the LLM client.

        Args:
            api_key: API key for the LLM service.
            model: Default model to use.
            base_url: Base URL for the LLM API.
        """
        super().__init__(base_url=base_url, api_key=api_key)
        self.model = model

    async def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> str:
        """Generate text using the LLM.

        Args:
            prompt: The user prompt.
            system_prompt: Optional system prompt.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.

        Returns:
            Generated text.
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = await self.post(
            "/chat/completions",
            json={
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
        )
        data = response.json()
        return data["choices"][0]["message"]["content"]

    async def embed(self, text: str) -> list[float]:
        """Generate embeddings for text.

        Args:
            text: Text to embed.

        Returns:
            Embedding vector.
        """
        response = await self.post(
            "/embeddings",
            json={"model": "text-embedding-ada-002", "input": text},
        )
        data = response.json()
        return data["data"][0]["embedding"]

    async def health_check(self) -> bool:
        """Check if the LLM service is available.

        Returns:
            True if the service is healthy.
        """
        try:
            await self.get("/models")
            return True
        except Exception:
            return False
