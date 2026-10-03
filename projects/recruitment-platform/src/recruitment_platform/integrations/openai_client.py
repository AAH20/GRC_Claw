"""OpenAI client integration."""

from __future__ import annotations

import logging
from typing import Any

from recruitment_platform.integrations.base import BaseIntegration

logger = logging.getLogger(__name__)


class OpenAIClient(BaseIntegration):
    """Client for OpenAI API interactions.

    Provides access to GPT models for text generation,
    analysis, and other AI-powered features.
    """

    def __init__(self, api_key: str, model: str = "gpt-4") -> None:
        """Initialize the OpenAI client.

        Args:
            api_key: OpenAI API key.
            model: Default model to use.
        """
        super().__init__(
            base_url="https://api.openai.com/v1",
            api_key=api_key,
        )
        self.model = model

    async def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> str:
        """Send a chat completion request.

        Args:
            messages: List of message dicts with role and content.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.

        Returns:
            Generated response text.
        """
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

    async def analyze(self, text: str, task: str) -> str:
        """Analyze text with a specific task.

        Args:
            text: Text to analyze.
            task: Analysis task description.

        Returns:
            Analysis result.
        """
        return await self.chat([
            {"role": "system", "content": task},
            {"role": "user", "content": text},
        ])

    async def health_check(self) -> bool:
        """Check if the OpenAI API is available.

        Returns:
            True if the service is healthy.
        """
        try:
            await self.get("/models")
            return True
        except Exception:
            return False
