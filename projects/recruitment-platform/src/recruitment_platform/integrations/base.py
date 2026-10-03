"""Base integration class for external services."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class BaseIntegration(ABC):
    """Abstract base class for external service integrations.

    Provides common functionality for HTTP-based integrations
    including retry logic, error handling, and logging.
    """

    def __init__(self, base_url: str, api_key: str = "", timeout: float = 30.0) -> None:
        """Initialize the base integration.

        Args:
            base_url: The base URL for the external service.
            api_key: API key for authentication.
            timeout: Request timeout in seconds.
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
            headers=self._default_headers(),
        )

    def _default_headers(self) -> dict[str, str]:
        """Get default headers for requests.

        Returns:
            Dictionary of default headers.
        """
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10)
    )
    async def request(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> httpx.Response:
        """Make an HTTP request with retry logic.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE).
            path: Request path relative to base URL.
            **kwargs: Additional arguments for httpx.

        Returns:
            HTTP response.

        Raises:
            httpx.HTTPError: If the request fails after retries.
        """
        self._logger.debug(f"Making {method} request to {path}")
        response = await self._client.request(method, path, **kwargs)
        response.raise_for_status()
        return response

    async def get(self, path: str, **kwargs: Any) -> httpx.Response:
        """Make a GET request.

        Args:
            path: Request path.
            **kwargs: Additional arguments.

        Returns:
            HTTP response.
        """
        return await self.request("GET", path, **kwargs)

    async def post(self, path: str, **kwargs: Any) -> httpx.Response:
        """Make a POST request.

        Args:
            path: Request path.
            **kwargs: Additional arguments.

        Returns:
            HTTP response.
        """
        return await self.request("POST", path, **kwargs)

    async def put(self, path: str, **kwargs: Any) -> httpx.Response:
        """Make a PUT request.

        Args:
            path: Request path.
            **kwargs: Additional arguments.

        Returns:
            HTTP response.
        """
        return await self.request("PUT", path, **kwargs)

    async def delete(self, path: str, **kwargs: Any) -> httpx.Response:
        """Make a DELETE request.

        Args:
            path: Request path.
            **kwargs: Additional arguments.

        Returns:
            HTTP response.
        """
        return await self.request("DELETE", path, **kwargs)

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the external service is healthy.

        Returns:
            True if the service is healthy, False otherwise.
        """
        raise NotImplementedError
