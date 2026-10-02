"""OpenAI client integration for bias-detector."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from bias_detector.config import get_settings

logger = logging.getLogger(__name__)


class OpenAIClient:
    """Client for interacting with OpenAI API.

    Attributes:
        api_key: OpenAI API key.
        model: Model to use for completions.
        base_url: OpenAI API base URL.
    """

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        """Initialize the OpenAI client.

        Args:
            api_key: OpenAI API key. If None, uses settings.
            model: Model name. If None, uses settings.
        """
        settings = get_settings()
        self.api_key = api_key or settings.openai_api_key
        self.model = model or settings.openai_model
        self.base_url = "https://api.openai.com/v1"

    async def complete(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.0,
        max_tokens: int = 1000,
    ) -> str:
        """Generate a completion using OpenAI API.

        Args:
            prompt: User prompt.
            system_prompt: System prompt.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.

        Returns:
            Generated completion text.

        Raises:
            ValueError: If API key is not configured.
            httpx.HTTPError: If API request fails.
        """
        if not self.api_key:
            raise ValueError("OpenAI API key is not configured")

        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
                timeout=60.0,
            )
            response.raise_for_status()
            data: dict[str, Any] = response.json()
            return data["choices"][0]["message"]["content"]
