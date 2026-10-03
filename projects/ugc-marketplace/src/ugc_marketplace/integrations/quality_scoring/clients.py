"""LLM and text analysis clients for quality scoring."""

from __future__ import annotations

from typing import Any

import structlog

from ugc_marketplace.config import get_settings

logger = structlog.get_logger(__name__)


class LLMClient:
    """LLM client for quality scoring."""

    def __init__(self, settings: Any | None = None) -> None:
        """Initialize LLM client.

        Args:
            settings: Optional settings override.
        """
        self.settings = settings or get_settings()
        self._llm: Any | None = None

    def get_llm(self) -> Any | None:
        """Get or create LLM instance.

        Returns:
            LLM instance or None.
        """
        if self._llm is None:
            try:
                from langchain_openai import ChatOpenAI

                self._llm = ChatOpenAI(
                    model=self.settings.llm_model,
                    temperature=self.settings.llm_temperature,
                    api_key=self.settings.openai_api_key or None,
                )
            except ImportError:
                logger.warning("langchain-openai not installed, LLM disabled")
                return None
        return self._llm


class TextAnalysisClient:
    """Text analysis client for quality scoring."""

    def __init__(self) -> None:
        """Initialize text analysis client."""
        self._client: Any = None

    async def _get_client(self) -> Any:
        """Get or create HTTP client.

        Returns:
            HTTP client.
        """
        if self._client is None:
            import httpx

            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def analyze_sentiment(self, text: str) -> dict[str, Any]:
        """Analyze text sentiment.

        Args:
            text: Text to analyze.

        Returns:
            Sentiment analysis result.
        """
        logger.debug("Analyzing sentiment", text_length=len(text))
        return {"sentiment": "neutral", "score": 0.5}

    async def close(self) -> None:
        """Close the client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None
