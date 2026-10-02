"""Anthropic API integration with retry logic and error handling."""

from __future__ import annotations

import logging
from typing import Any

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import BaseMessage
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class AnthropicClient:
    """Client for interacting with the Anthropic API via LangChain.

    Provides a wrapper around ChatAnthropic with retry logic,
    structured logging, and error handling.
    """

    def __init__(
        self,
        *,
        model: str = "claude-sonnet-4-20250514",
        max_tokens: int = 4096,
        temperature: float = 0.7,
        api_key: str | None = None,
    ) -> None:
        """Initialize the Anthropic client.

        Args:
            model: Anthropic model identifier.
            max_tokens: Maximum tokens for completions.
            temperature: Sampling temperature.
            api_key: Anthropic API key (falls back to ANTHROPIC_API_KEY env var).
        """
        self._model = model
        self._max_tokens = max_tokens
        self._temperature = temperature
        self._llm = ChatAnthropic(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            anthropic_api_key=api_key,
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def generate(
        self,
        messages: list[BaseMessage],
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        """Generate a completion from the given messages.

        Args:
            messages: List of LangChain messages.
            temperature: Override temperature for this call.
            max_tokens: Override max tokens for this call.

        Returns:
            Generated text content.

        Raises:
            RuntimeError: If the API call fails after retries.
        """
        try:
            if temperature is not None:
                self._llm.temperature = temperature
            if max_tokens is not None:
                self._llm.max_tokens = max_tokens

            response = await self._llm.ainvoke(messages)
            content = response.content

            if isinstance(content, list):
                content = "".join(
                    block.get("text", "") if isinstance(block, dict) else str(block)
                    for block in content
                )

            return content.strip()

        except Exception as exc:
            logger.error("Anthropic API call failed: %s", exc)
            raise RuntimeError(f"Anthropic API call failed: {exc}") from exc

    async def generate_json(
        self,
        messages: list[BaseMessage],
        *,
        temperature: float = 0.3,
    ) -> dict[str, Any]:
        """Generate a JSON completion from the given messages.

        Args:
            messages: List of LangChain messages.
            temperature: Sampling temperature (default: 0.3 for JSON).

        Returns:
            Parsed JSON response.

        Raises:
            RuntimeError: If the API call fails or returns invalid JSON.
        """
        import json

        content = await self.generate(messages, temperature=temperature)

        # Try to extract JSON from markdown code block if present
        if "```json" in content:
            start = content.index("```json") + 7
            end = content.index("```", start)
            content = content[start:end].strip()
        elif "```" in content:
            start = content.index("```") + 3
            end = content.index("```", start)
            content = content[start:end].strip()

        try:
            return json.loads(content)
        except json.JSONDecodeError as exc:
            logger.error("Failed to parse JSON response: %s", exc)
            raise RuntimeError(f"Invalid JSON response: {exc}") from exc
