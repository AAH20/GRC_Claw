"""Base client for external review platform integrations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import httpx
import structlog

from employer_branding.config import get_settings

logger = structlog.get_logger(__name__)


class BaseReviewClient(ABC):
    """Abstract base class for review platform API clients."""

    def __init__(self, api_key: str | None = None) -> None:
        """Initialize the review client.

        Args:
            api_key: API key for the platform. If not provided, uses settings.
        """
        self._settings = get_settings()
        self._api_key = api_key
        self._logger = logger.bind(client=self.__class__.__name__)
        self._client = httpx.AsyncClient(
            timeout=30.0,
            headers={"Accept": "application/json"},
        )

    async def __aenter__(self) -> "BaseReviewClient":
        """Async context manager entry."""
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Async context manager exit."""
        await self._client.aclose()

    @abstractmethod
    async def fetch_reviews(
        self, company_name: str, limit: int = 50
    ) -> list[dict[str, Any]]:
        """Fetch reviews for a company.

        Args:
            company_name: Company name to search.
            limit: Maximum number of reviews to fetch.

        Returns:
            List of raw review dictionaries.
        """
        raise NotImplementedError

    @abstractmethod
    async def get_company_info(self, company_name: str) -> dict[str, Any]:
        """Get company information.

        Args:
            company_name: Company name to search.

        Returns:
            Dictionary with company information.
        """
        raise NotImplementedError
