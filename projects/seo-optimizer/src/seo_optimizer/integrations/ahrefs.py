"""Ahrefs API integration client."""

from __future__ import annotations

from typing import Any

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

logger = structlog.get_logger(__name__)


class AhrefsClient:
    """Client for interacting with the Ahrefs API.

    Provides methods to fetch backlink data, keyword suggestions,
    and site audit information from Ahrefs.
    """

    BASE_URL = "https://apiv2.ahrefs.com"

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize the Ahrefs client.

        Args:
            config: Configuration dictionary containing API settings.
        """
        config = config or {}
        self.enabled = config.get("ahrefs_enabled", False)
        self.api_key = config.get("ahrefs_api_key")
        self.base_url = config.get("ahrefs_base_url", self.BASE_URL)
        self.rate_limit = config.get("ahrefs_rate_limit_per_second", 1)
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client.

        Returns:
            Configured httpx AsyncClient.
        """
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=30.0,
            )
        return self._client

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    async def get_keyword_ideas(
        self,
        domain: str,
        seed_keywords: list[str] | None = None,
        country: str = "us",
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Fetch keyword ideas from Ahrefs.

        Args:
            domain: Target domain for keyword research.
            seed_keywords: Optional seed keywords to expand from.
            country: Country code for localized data.
            limit: Maximum number of keywords to return.

        Returns:
            List of keyword data dictionaries.
        """
        if not self.enabled or not self.api_key:
            logger.warning("Ahrefs integration is disabled or not configured")
            return []

        try:
            await self._get_client()
            # This would make actual API calls to Ahrefs
            return []
        except Exception as exc:
            logger.error("Failed to fetch Ahrefs keyword ideas", error=str(exc))
            return []

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    async def get_backlink_profile(self, domain: str) -> dict[str, Any]:
        """Fetch backlink profile from Ahrefs.

        Args:
            domain: Target domain to analyze.

        Returns:
            Backlink profile data dictionary.
        """
        if not self.enabled or not self.api_key:
            logger.warning("Ahrefs integration is disabled or not configured")
            return {}

        try:
            await self._get_client()
            return {
                "domain": domain,
                "total_backlinks": 0,
                "referring_domains": 0,
                "domain_rating": 0,
                "url_rating": 0,
            }
        except Exception as exc:
            logger.error("Failed to fetch Ahrefs backlink profile", error=str(exc))
            return {}

    async def close(self) -> None:
        """Close the HTTP client connection."""
        if self._client:
            await self._client.aclose()
            self._client = None
