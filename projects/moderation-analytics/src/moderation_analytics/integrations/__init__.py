"""External integrations for moderation analytics."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import httpx
import structlog

from moderation_analytics.config import get_settings
from moderation_analytics.exceptions import IntegrationError

logger = structlog.get_logger(__name__)


class BaseIntegration(ABC):
    """Abstract base class for external integrations."""

    def __init__(self, base_url: str, api_key: str | None = None) -> None:
        """Initialize the integration.

        Args:
            base_url: Base URL for the external service.
            api_key: Optional API key for authentication.
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.logger = logger.bind(integration=self.__class__.__name__)

    @property
    def _headers(self) -> dict[str, str]:
        """Get default headers for requests.

        Returns:
            dict: Default headers.
        """
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    @abstractmethod
    async def fetch_data(
        self, endpoint: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Fetch data from the external service.

        Args:
            endpoint: API endpoint to call.
            params: Optional query parameters.

        Returns:
            dict: Response data.

        Raises:
            NotImplementedError: Must be implemented by subclasses.
        """
        raise NotImplementedError


class ModerationAPIIntegration(BaseIntegration):
    """Integration with external moderation API."""

    def __init__(self) -> None:
        """Initialize the moderation API integration."""
        settings = get_settings()
        super().__init__(
            base_url=settings.moderation_api_url,
            api_key=settings.moderation_api_key or None,
        )

    async def fetch_data(
        self, endpoint: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Fetch data from moderation API.

        Args:
            endpoint: API endpoint.
            params: Query parameters.

        Returns:
            dict: Response data.

        Raises:
            IntegrationError: If the request fails.
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self._headers, params=params)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            self.logger.error("Failed to fetch data from moderation API", error=str(e))
            raise IntegrationError(f"Moderation API error: {e}") from e

    async def get_moderation_events(
        self, start_date: str, end_date: str, limit: int = 1000
    ) -> list[dict[str, Any]]:
        """Fetch moderation events.

        Args:
            start_date: Start date (ISO format).
            end_date: End date (ISO format).
            limit: Maximum number of events.

        Returns:
            list: Moderation events.
        """
        result = await self.fetch_data(
            "/events",
            params={"start_date": start_date, "end_date": end_date, "limit": limit},
        )
        return result.get("events", [])

    async def get_moderator_stats(self, moderator_id: str) -> dict[str, Any]:
        """Fetch moderator statistics.

        Args:
            moderator_id: Moderator identifier.

        Returns:
            dict: Moderator statistics.
        """
        return await self.fetch_data(f"/moderators/{moderator_id}/stats")


class AnalyticsDatabaseIntegration(BaseIntegration):
    """Integration with analytics database."""

    def __init__(self) -> None:
        """Initialize the analytics database integration."""
        settings = get_settings()
        super().__init__(base_url=settings.analytics_db_url)

    async def fetch_data(
        self, endpoint: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Fetch data from analytics database.

        Args:
            endpoint: API endpoint.
            params: Query parameters.

        Returns:
            dict: Response data.

        Raises:
            IntegrationError: If the request fails.
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self._headers, params=params)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            self.logger.error("Failed to fetch data from analytics DB", error=str(e))
            raise IntegrationError(f"Analytics DB error: {e}") from e

    async def query_analytics(
        self, query: str, params: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Execute analytics query.

        Args:
            query: Query string.
            params: Query parameters.

        Returns:
            list: Query results.
        """
        result = await self.fetch_data("/query", params={"q": query, **(params or {})})
        return result.get("results", [])
