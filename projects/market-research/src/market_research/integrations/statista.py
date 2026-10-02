"""Statista API integration for market data collection."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from datetime import datetime

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

logger = structlog.get_logger(__name__)


class StatistaError(Exception):
    """Custom exception for Statista API errors."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        """Initialize the Statista error.

        Args:
            message: Error message.
            status_code: Optional HTTP status code.
        """
        super().__init__(message)
        self.status_code = status_code


class StatistaClient:
    """Client for interacting with the Statista API.

    This client provides methods to search for statistics, retrieve data,
    and access market research data from the Statista platform.
    """

    BASE_URL = "https://api.statista.com"

    def __init__(
        self,
        api_key: str | None = None,
        timeout: float = 30.0,
        max_retries: int = 3,
    ) -> None:
        """Initialize the Statista client.

        Args:
            api_key: Statista API key. Defaults to STATISTA_API_KEY env var.
            timeout: Request timeout in seconds.
            max_retries: Maximum number of retry attempts.

        Raises:
            StatistaError: If no API key is provided.
        """
        self.api_key = api_key or os.getenv("STATISTA_API_KEY")
        if not self.api_key:
            raise StatistaError("STATISTA_API_KEY is required")

        self.timeout = timeout
        self.max_retries = max_retries
        self._client: httpx.AsyncClient | None = None
        logger.info("statista_client_initialized", timeout=timeout)

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client.

        Returns:
            Configured httpx AsyncClient.
        """
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.BASE_URL,
                timeout=self.timeout,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self) -> StatistaClient:
        """Async context manager entry."""
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Async context manager exit."""
        await self.close()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def search_statistics(
        self,
        query: str,
        limit: int = 10,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Search for statistics on Statista.

        Args:
            query: Search query string.
            limit: Maximum number of results.
            offset: Pagination offset.

        Returns:
            Search results dictionary.

        Raises:
            StatistaError: If the API request fails.
        """
        client = await self._get_client()
        logger.info("statista_search", query=query, limit=limit)

        try:
            response = await client.get(
                "/statistics/search",
                params={"query": query, "limit": limit, "offset": offset},
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            logger.error(
                "statista_search_failed",
                status_code=exc.response.status_code,
                response=exc.response.text,
            )
            raise StatistaError(
                f"Statista API error: {exc.response.status_code}",
                status_code=exc.response.status_code,
            ) from exc
        except httpx.RequestError as exc:
            logger.error("statista_request_failed", error=str(exc))
            raise StatistaError(f"Statista request failed: {exc}") from exc

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def get_statistic(self, statistic_id: str) -> dict[str, Any]:
        """Get a specific statistic by ID.

        Args:
            statistic_id: The statistic identifier.

        Returns:
            Statistic data dictionary.

        Raises:
            StatistaError: If the API request fails.
        """
        client = await self._get_client()
        logger.info("statista_get_statistic", statistic_id=statistic_id)

        try:
            response = await client.get(f"/statistics/{statistic_id}")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            logger.error(
                "statista_get_failed",
                statistic_id=statistic_id,
                status_code=exc.response.status_code,
            )
            raise StatistaError(
                f"Statista API error: {exc.response.status_code}",
                status_code=exc.response.status_code,
            ) from exc
        except httpx.RequestError as exc:
            logger.error("statista_request_failed", error=str(exc))
            raise StatistaError(f"Statista request failed: {exc}") from exc

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def get_market_data(
        self,
        market_id: str,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> dict[str, Any]:
        """Get market data for a specific market.

        Args:
            market_id: The market identifier.
            start_date: Optional start date filter.
            end_date: Optional end date filter.

        Returns:
            Market data dictionary.

        Raises:
            StatistaError: If the API request fails.
        """
        client = await self._get_client()
        logger.info("statista_get_market_data", market_id=market_id)

        params: dict[str, str] = {}
        if start_date:
            params["startDate"] = start_date.strftime("%Y-%m-%d")
        if end_date:
            params["endDate"] = end_date.strftime("%Y-%m-%d")

        try:
            response = await client.get(
                f"/markets/{market_id}/data",
                params=params,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            logger.error(
                "statista_market_data_failed",
                market_id=market_id,
                status_code=exc.response.status_code,
            )
            raise StatistaError(
                f"Statista API error: {exc.response.status_code}",
                status_code=exc.response.status_code,
            ) from exc
        except httpx.RequestError as exc:
            logger.error("statista_request_failed", error=str(exc))
            raise StatistaError(f"Statista request failed: {exc}") from exc

    async def get_categories(self) -> list[dict[str, Any]]:
        """Get available statistic categories.

        Returns:
            List of category dictionaries.

        Raises:
            StatistaError: If the API request fails.
        """
        client = await self._get_client()
        logger.info("statista_get_categories")

        try:
            response = await client.get("/categories")
            response.raise_for_status()
            data = response.json()
            return data.get("categories", [])
        except httpx.HTTPStatusError as exc:
            logger.error(
                "statista_categories_failed",
                status_code=exc.response.status_code,
            )
            raise StatistaError(
                f"Statista API error: {exc.response.status_code}",
                status_code=exc.response.status_code,
            ) from exc
        except httpx.RequestError as exc:
            logger.error("statista_request_failed", error=str(exc))
            raise StatistaError(f"Statista request failed: {exc}") from exc
