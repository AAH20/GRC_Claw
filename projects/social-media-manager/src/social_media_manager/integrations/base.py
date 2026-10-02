"""Shared async HTTP client for social platform integrations."""

from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class PlatformError(Exception):
    """Raised when a platform API call fails."""

    def __init__(self, platform: str, status: int | None, message: str) -> None:
        self.platform = platform
        self.status = status
        self.message = message
        super().__init__(f"[{platform}] {status or 'n/a'}: {message}")


class BasePlatformClient:
    """Async base client with retries and unified error handling."""

    platform: str = "base"
    base_url: str = ""

    def __init__(
        self,
        access_token: str | None = None,
        *,
        timeout: float = 30.0,
        max_retries: int = 3,
    ) -> None:
        """Initialise the client.

        Args:
            access_token: Bearer/OAuth token used for authentication.
            timeout: Per-request timeout in seconds.
            max_retries: Number of retry attempts for transient failures.
        """
        self.access_token = access_token
        self.timeout = timeout
        self.max_retries = max_retries

    @property
    def is_configured(self) -> bool:
        """Whether the client has the credentials it needs."""
        return bool(self.access_token)

    def _headers(self) -> dict[str, str]:
        """Return default request headers including auth when available."""
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        return headers

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute an HTTP request with retry on transient errors.

        Args:
            method: HTTP verb.
            path: Path appended to ``base_url``.
            json: Optional JSON body.
            params: Optional query parameters.

        Returns:
            Parsed JSON response as a dictionary.

        Raises:
            PlatformError: On non-retryable or exhausted failures.
        """
        url = f"{self.base_url.rstrip('/')}/{path.lstrip('/')}"
        last_exc: Exception | None = None

        for attempt in range(1, self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.request(
                        method, url, headers=self._headers(), json=json, params=params
                    )
                if response.status_code >= 500:
                    last_exc = PlatformError(
                        self.platform, response.status_code, "server error"
                    )
                    logger.warning(
                        "platform=%s status=%s attempt=%s retrying",
                        self.platform,
                        response.status_code,
                        attempt,
                    )
                    continue
                if response.status_code >= 400:
                    raise PlatformError(
                        self.platform, response.status_code, response.text[:500]
                    )
                if not response.content:
                    return {}
                return response.json()
            except httpx.HTTPError as exc:
                last_exc = exc
                logger.warning(
                    "platform=%s transport_error=%s attempt=%s",
                    self.platform,
                    exc,
                    attempt,
                )

        raise PlatformError(
            self.platform, None, f"request failed after {self.max_retries} attempts: {last_exc}"
        )
