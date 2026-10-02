"""Base client for external API integrations."""

from __future__ import annotations

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential


class BaseAPIClient:
    """Base HTTP client with retry logic for external APIs."""

    def __init__(self, base_url: str, api_key: str, timeout: float = 30.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers=self._default_headers(),
                timeout=self.timeout,
            )
        return self._client

    def _default_headers(self) -> dict[str, str]:
        """Return default headers for API requests."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def get(self, path: str, params: dict | None = None) -> dict:
        """Perform GET request with retry logic."""
        client = await self._get_client()
        response = await client.get(path, params=params)
        response.raise_for_status()
        return response.json()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def post(self, path: str, data: dict | None = None) -> dict:
        """Perform POST request with retry logic."""
        client = await self._get_client()
        response = await client.post(path, json=data)
        response.raise_for_status()
        return response.json()

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
