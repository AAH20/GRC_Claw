"""Base HTTP client shared by all integration adapters."""

from __future__ import annotations

import logging
from typing import Any

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger(__name__)


class IntegrationError(RuntimeError):
    """Raised when an integration call fails irrecoverably."""


class BaseIntegrationClient:
    """Common HTTP plumbing for integration adapters.

    Provides retrying request helpers, uniform error translation, and async
    context-manager lifecycle management.
    """

    name = "base"

    def __init__(
        self,
        base_url: str,
        *,
        timeout: float = 30.0,
        max_attempts: int = 3,
        headers: dict[str, str] | None = None,
    ) -> None:
        """Initialise the client.

        Args:
            base_url: Root URL for the API.
            timeout: Per-request timeout in seconds.
            max_attempts: Retry attempts for transient failures.
            headers: Default headers applied to every request.
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_attempts = max_attempts
        self.headers = headers or {}
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> BaseIntegrationClient:
        """Enter the async context, creating the underlying HTTP client."""
        self._client = httpx.AsyncClient(
            base_url=self.base_url, timeout=self.timeout, headers=self.headers
        )
        return self

    async def __aexit__(self, *exc_info: Any) -> None:
        """Close the underlying HTTP client."""
        await self.close()

    async def close(self) -> None:
        """Close the underlying HTTP client if it is open."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    @property
    def client(self) -> httpx.AsyncClient:
        """Return the active HTTP client, creating one lazily if needed."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url, timeout=self.timeout, headers=self.headers
            )
        return self._client

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Perform an HTTP request with retries and error translation.

        Args:
            method: HTTP method.
            path: Request path relative to ``base_url``.
            params: Optional query parameters.
            json: Optional JSON body.

        Returns:
            The decoded JSON response body.

        Raises:
            IntegrationError: If the request fails after all retries.
        """

        @retry(
            stop=stop_after_attempt(self.max_attempts),
            wait=wait_exponential(multiplier=0.5, max=8),
            retry=retry_if_exception_type((httpx.TransportError, httpx.HTTPStatusError)),
            reraise=True,
        )
        async def _do_request() -> dict[str, Any]:
            response = await self.client.request(method, path, params=params, json=json)
            if response.status_code >= 500:
                response.raise_for_status()
            if response.status_code >= 400:
                raise IntegrationError(
                    f"{self.name} request failed [{response.status_code}]: {response.text[:200]}"
                )
            if not response.content:
                return {}
            return response.json()

        try:
            return await _do_request()
        except IntegrationError:
            raise
        except Exception as exc:  # noqa: BLE001 - translate to a domain error
            logger.exception("%s request to %s failed", self.name, path)
            raise IntegrationError(f"{self.name} request failed: {exc}") from exc

    async def health(self) -> bool:
        """Check whether the upstream API is reachable.

        Returns:
            ``True`` if a lightweight request succeeds, ``False`` otherwise.
        """
        try:
            await self.request("GET", "/")
            return True
        except IntegrationError:
            return False
