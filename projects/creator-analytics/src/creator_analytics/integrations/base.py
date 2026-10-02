"""Base integration class for external platforms."""

from abc import ABC, abstractmethod
from typing import Any

import httpx
import structlog

logger = structlog.get_logger(__name__)


class BaseIntegration(ABC):
    """Base class for platform integrations."""

    def __init__(self, api_key: str, base_url: str) -> None:
        """Initialize the integration.

        Args:
            api_key: API key for the platform.
            base_url: Base URL for the platform API.
        """
        self.api_key = api_key
        self.base_url = base_url
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client.

        Returns:
            Configured HTTP client.
        """
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers=self._get_headers(),
                timeout=30.0,
            )
        return self._client

    def _get_headers(self) -> dict[str, str]:
        """Get request headers.

        Returns:
            Headers dictionary.
        """
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    @abstractmethod
    async def fetch_analytics(self, creator_id: str) -> dict[str, Any]:
        """Fetch analytics data for a creator.

        Args:
            creator_id: Creator identifier on the platform.

        Returns:
            Analytics data.
        """
        pass

    @abstractmethod
    async def fetch_content_performance(self, content_ids: list[str]) -> list[dict[str, Any]]:
        """Fetch performance data for specific content.

        Args:
            content_ids: List of content identifiers.

        Returns:
            List of content performance data.
        """
        pass
