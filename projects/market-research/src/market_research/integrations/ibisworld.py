"""IBISWorld API integration for industry and market research data."""

from __future__ import annotations

import os
from typing import Any

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

logger = structlog.get_logger(__name__)


class IBISWorldError(Exception):
    """Custom exception for IBISWorld API errors."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        """Initialize the IBISWorld error.

        Args:
            message: Error message.
            status_code: Optional HTTP status code.
        """
        super().__init__(message)
        self.status_code = status_code


class IBISWorldClient:
    """Client for interacting with the IBISWorld API.

    This client provides methods to search for industry reports,
    retrieve industry data, and access market research information
    from the IBISWorld platform.
    """

    BASE_URL = "https://api.ibisworld.com"

    def __init__(
        self,
        api_key: str | None = None,
        timeout: float = 30.0,
        max_retries: int = 3,
    ) -> None:
        """Initialize the IBISWorld client.

        Args:
            api_key: IBISWorld API key. Defaults to IBISWORLD_API_KEY env var.
            timeout: Request timeout in seconds.
            max_retries: Maximum number of retry attempts.

        Raises:
            IBISWorldError: If no API key is provided.
        """
        self.api_key = api_key or os.getenv("IBISWORLD_API_KEY")
        if not self.api_key:
            raise IBISWorldError("IBISWORLD_API_KEY is required")

        self.timeout = timeout
        self.max_retries = max_retries
        self._client: httpx.AsyncClient | None = None
        logger.info("ibisworld_client_initialized", timeout=timeout)

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

    async def __aenter__(self) -> IBISWorldClient:
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
    async def search_industries(
        self,
        query: str,
        limit: int = 10,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Search for industries on IBISWorld.

        Args:
            query: Search query string.
            limit: Maximum number of results.
            offset: Pagination offset.

        Returns:
            Search results dictionary.

        Raises:
            IBISWorldError: If the API request fails.
        """
        client = await self._get_client()
        logger.info("ibisworld_search_industries", query=query, limit=limit)

        try:
            response = await client.get(
                "/industries/search",
                params={"query": query, "limit": limit, "offset": offset},
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            logger.error(
                "ibisworld_search_failed",
                status_code=exc.response.status_code,
                response=exc.response.text,
            )
            raise IBISWorldError(
                f"IBISWorld API error: {exc.response.status_code}",
                status_code=exc.response.status_code,
            ) from exc
        except httpx.RequestError as exc:
            logger.error("ibisworld_request_failed", error=str(exc))
            raise IBISWorldError(f"IBISWorld request failed: {exc}") from exc

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def get_industry_report(self, industry_id: str) -> dict[str, Any]:
        """Get a specific industry report by ID.

        Args:
            industry_id: The industry identifier.

        Returns:
            Industry report data dictionary.

        Raises:
            IBISWorldError: If the API request fails.
        """
        client = await self._get_client()
        logger.info("ibisworld_get_industry_report", industry_id=industry_id)

        try:
            response = await client.get(f"/industries/{industry_id}/report")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            logger.error(
                "ibisworld_report_failed",
                industry_id=industry_id,
                status_code=exc.response.status_code,
            )
            raise IBISWorldError(
                f"IBISWorld API error: {exc.response.status_code}",
                status_code=exc.response.status_code,
            ) from exc
        except httpx.RequestError as exc:
            logger.error("ibisworld_request_failed", error=str(exc))
            raise IBISWorldError(f"IBISWorld request failed: {exc}") from exc

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def get_industry_statistics(self, industry_id: str) -> dict[str, Any]:
        """Get key statistics for an industry.

        Args:
            industry_id: The industry identifier.

        Returns:
            Industry statistics dictionary.

        Raises:
            IBISWorldError: If the API request fails.
        """
        client = await self._get_client()
        logger.info("ibisworld_get_industry_statistics", industry_id=industry_id)

        try:
            response = await client.get(f"/industries/{industry_id}/statistics")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            logger.error(
                "ibisworld_statistics_failed",
                industry_id=industry_id,
                status_code=exc.response.status_code,
            )
            raise IBISWorldError(
                f"IBISWorld API error: {exc.response.status_code}",
                status_code=exc.response.status_code,
            ) from exc
        except httpx.RequestError as exc:
            logger.error("ibisworld_request_failed", error=str(exc))
            raise IBISWorldError(f"IBISWorld request failed: {exc}") from exc

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def get_market_size(self, industry_id: str) -> dict[str, Any]:
        """Get market size data for an industry.

        Args:
            industry_id: The industry identifier.

        Returns:
            Market size data dictionary.

        Raises:
            IBISWorldError: If the API request fails.
        """
        client = await self._get_client()
        logger.info("ibisworld_get_market_size", industry_id=industry_id)

        try:
            response = await client.get(f"/industries/{industry_id}/market-size")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            logger.error(
                "ibisworld_market_size_failed",
                industry_id=industry_id,
                status_code=exc.response.status_code,
            )
            raise IBISWorldError(
                f"IBISWorld API error: {exc.response.status_code}",
                status_code=exc.response.status_code,
            ) from exc
        except httpx.RequestError as exc:
            logger.error("ibisworld_request_failed", error=str(exc))
            raise IBISWorldError(f"IBISWorld request failed: {exc}") from exc

    async def get_industry_list(self) -> list[dict[str, Any]]:
        """Get list of all available industries.

        Returns:
            List of industry dictionaries.

        Raises:
            IBISWorldError: If the API request fails.
        """
        client = await self._get_client()
        logger.info("ibisworld_get_industry_list")

        try:
            response = await client.get("/industries")
            response.raise_for_status()
            data = response.json()
            return data.get("industries", [])
        except httpx.HTTPStatusError as exc:
            logger.error(
                "ibisworld_industry_list_failed",
                status_code=exc.response.status_code,
            )
            raise IBISWorldError(
                f"IBISWorld API error: {exc.response.status_code}",
                status_code=exc.response.status_code,
            ) from exc
        except httpx.RequestError as exc:
            logger.error("ibisworld_request_failed", error=str(exc))
            raise IBISWorldError(f"IBISWorld request failed: {exc}") from exc
