"""Base connector abstract class for all integration connectors."""

from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, AsyncIterator, Callable, Coroutine, Dict, List, Optional, TypeVar, Union

import aiohttp

logger = logging.getLogger(__name__)


class ConnectionState(str, Enum):
    """Connection lifecycle states."""

    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    AUTHENTICATING = "authenticating"
    AUTHENTICATED = "authenticated"
    ERROR = "error"
    CLOSED = "closed"


class ConnectorError(Exception):
    """Base exception for connector errors."""

    def __init__(self, message: str, *, status_code: Optional[int] = None, response_body: Optional[str] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body


class AuthenticationError(ConnectorError):
    """Raised when authentication fails."""


class RateLimitError(ConnectorError):
    """Raised when rate limit is exceeded."""

    def __init__(self, message: str, *, retry_after: Optional[float] = None, **kwargs: Any):
        super().__init__(message, **kwargs)
        self.retry_after = retry_after


class ResourceNotFoundError(ConnectorError):
    """Raised when a requested resource is not found."""


class ValidationError(ConnectorError):
    """Raised when request validation fails."""


@dataclass
class ConnectorConfig:
    """Base configuration for connectors."""

    base_url: str
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    timeout: float = 30.0
    max_retries: int = 3
    retry_delay: float = 1.0
    verify_ssl: bool = True
    extra_headers: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class APIResponse:
    """Standardized API response wrapper."""

    status_code: int
    data: Any
    headers: Dict[str, str] = field(default_factory=dict)
    raw: Optional[bytes] = None

    @property
    def is_success(self) -> bool:
        return 200 <= self.status_code < 300

    @property
    def is_rate_limited(self) -> bool:
        return self.status_code == 429

    def raise_for_status(self) -> None:
        """Raise appropriate exception for non-success status codes."""
        if self.is_success:
            return
        if self.status_code == 401:
            raise AuthenticationError("Authentication failed", status_code=self.status_code)
        if self.status_code == 404:
            raise ResourceNotFoundError("Resource not found", status_code=self.status_code)
        if self.status_code == 429:
            raise RateLimitError("Rate limit exceeded", status_code=self.status_code)
        if 400 <= self.status_code < 500:
            raise ValidationError(f"Client error: {self.status_code}", status_code=self.status_code)
        raise ConnectorError(f"Server error: {self.status_code}", status_code=self.status_code)


T = TypeVar("T")


class BaseConnector(ABC):
    """Abstract base class for all integration connectors.

    Provides common HTTP session management, authentication hooks,
    retry logic, and standardized request/response handling.
    """

    def __init__(self, config: ConnectorConfig) -> None:
        self.config = config
        self._state = ConnectionState.DISCONNECTED
        self._session: Optional[aiohttp.ClientSession] = None
        self._auth_token: Optional[str] = None
        self._token_expires_at: Optional[float] = None
        self._rate_limit_remaining: Optional[int] = None
        self._rate_limit_reset: Optional[float] = None
        self._middleware: List[Callable[[Dict[str, Any]], Coroutine[Any, Any, Dict[str, Any]]]] = []
        self._response_hooks: List[Callable[[APIResponse], Coroutine[Any, Any, None]]] = []

    @property
    def state(self) -> ConnectionState:
        """Current connection state."""
        return self._state

    @property
    def is_connected(self) -> bool:
        """Whether the connector has an active session."""
        return self._state == ConnectionState.CONNECTED and self._session is not None

    @property
    def is_authenticated(self) -> bool:
        """Whether the connector has valid authentication."""
        return self._state == ConnectionState.AUTHENTICATED

    @abstractmethod
    async def authenticate(self) -> None:
        """Authenticate with the external service.

        Must set self._auth_token and self._state appropriately.
        """
        ...

    @abstractmethod
    async def refresh_auth(self) -> None:
        """Refresh authentication tokens if supported."""
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the connector is healthy and reachable."""
        ...

    async def connect(self) -> None:
        """Establish HTTP session and authenticate."""
        if self._state == ConnectionState.CONNECTED:
            return

        self._state = ConnectionState.CONNECTING
        try:
            connector = aiohttp.TCPConnector(verify_ssl=self.config.verify_ssl)
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            self._session = aiohttp.ClientSession(
                base_url=self.config.base_url,
                connector=connector,
                timeout=timeout,
                headers=self._default_headers(),
            )
            self._state = ConnectionState.CONNECTED
            await self.authenticate()
        except Exception as e:
            self._state = ConnectionState.ERROR
            raise ConnectorError(f"Connection failed: {e}") from e

    async def disconnect(self) -> None:
        """Close the HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()
        self._state = ConnectionState.CLOSED
        self._session = None
        self._auth_token = None

    async def __aenter__(self) -> BaseConnector:
        await self.connect()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.disconnect()

    def _default_headers(self) -> Dict[str, str]:
        """Default headers for all requests."""
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "GRC-Claw-Integration-Hub/1.0",
        }
        headers.update(self.config.extra_headers)
        return headers

    def _auth_headers(self) -> Dict[str, str]:
        """Headers for authenticated requests. Override in subclasses."""
        if self._auth_token:
            return {"Authorization": f"Bearer {self._auth_token}"}
        return {}

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        files: Optional[Dict[str, Any]] = None,
        auth: bool = True,
        retry_count: int = 0,
    ) -> APIResponse:
        """Make an HTTP request with retry logic and error handling.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, PATCH).
            path: API path (relative to base_url).
            params: Query parameters.
            data: JSON body data.
            headers: Additional headers.
            files: Files to upload.
            auth: Whether to include authentication headers.
            retry_count: Current retry attempt (internal use).

        Returns:
            APIResponse with status, data, and headers.

        Raises:
            ConnectorError: On request failure after all retries.
        """
        if not self._session:
            raise ConnectorError("Not connected. Call connect() first.")

        request_headers = self._default_headers()
        if auth:
            request_headers.update(self._auth_headers())
        if headers:
            request_headers.update(headers)

        # Apply request middleware
        request_context: Dict[str, Any] = {
            "method": method,
            "path": path,
            "params": params,
            "data": data,
            "headers": request_headers,
        }
        for mw in self._middleware:
            request_context = await mw(request_context)

        url = path if path.startswith("http") else f"{self.config.base_url.rstrip('/')}/{path.lstrip('/')}"

        try:
            async with self._session.request(
                method=method,
                url=url,
                params=request_context.get("params"),
                json=request_context.get("data") if not files else None,
                data=files,
                headers=request_context.get("headers"),
            ) as resp:
                response_headers = dict(resp.headers)
                self._rate_limit_remaining = self._parse_rate_limit_remaining(response_headers)
                self._rate_limit_reset = self._parse_rate_limit_reset(response_headers)

                body = await resp.read()
                try:
                    resp_data = await resp.json()
                except Exception:
                    resp_data = body.decode("utf-8", errors="replace") if body else None

                api_response = APIResponse(
                    status_code=resp.status,
                    data=resp_data,
                    headers=response_headers,
                    raw=body,
                )

                # Apply response hooks
                for hook in self._response_hooks:
                    await hook(api_response)

                if api_response.is_rate_limited and retry_count < self.config.max_retries:
                    retry_after = self._extract_retry_after(response_headers)
                    logger.warning("Rate limited. Retrying after %.1fs", retry_after)
                    await asyncio.sleep(retry_after)
                    return await self.request(
                        method, path, params=params, data=data, headers=headers,
                        files=files, auth=auth, retry_count=retry_count + 1,
                    )

                if resp_status >= 500 and retry_count < self.config.max_retries:
                    delay = self.config.retry_delay * (2 ** retry_count)
                    logger.warning("Server error %d. Retrying in %.1fs", resp_status, delay)
                    await asyncio.sleep(delay)
                    return await self.request(
                        method, path, params=params, data=data, headers=headers,
                        files=files, auth=auth, retry_count=retry_count + 1,
                    )

                api_response.raise_for_status()
                return api_response

        except aiohttp.ClientError as e:
            if retry_count < self.config.max_retries:
                delay = self.config.retry_delay * (2 ** retry_count)
                logger.warning("Request failed: %s. Retrying in %.1fs", e, delay)
                await asyncio.sleep(delay)
                return await self.request(
                    method, path, params=params, data=data, headers=headers,
                    files=files, auth=auth, retry_count=retry_count + 1,
                )
            raise ConnectorError(f"Request failed after {retry_count + 1} attempts: {e}") from e

    async def get(self, path: str, **kwargs: Any) -> APIResponse:
        """Convenience method for GET requests."""
        return await self.request("GET", path, **kwargs)

    async def post(self, path: str, **kwargs: Any) -> APIResponse:
        """Convenience method for POST requests."""
        return await self.request("POST", path, **kwargs)

    async def put(self, path: str, **kwargs: Any) -> APIResponse:
        """Convenience method for PUT requests."""
        return await self.request("PUT", path, **kwargs)

    async def patch(self, path: str, **kwargs: Any) -> APIResponse:
        """Convenience method for PATCH requests."""
        return await self.request("PATCH", path, **kwargs)

    async def delete(self, path: str, **kwargs: Any) -> APIResponse:
        """Convenience method for DELETE requests."""
        return await self.request("DELETE", path, **kwargs)

    async def paginate(
        self,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        data_key: str = "data",
        next_key: str = "paging",
        next_url_key: str = "next",
        max_pages: Optional[int] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Generic pagination iterator.

        Args:
            path: API endpoint path.
            params: Query parameters.
            data_key: Key in response containing the data array.
            next_key: Key containing pagination info.
            next_url_key: Key containing the next page URL.
            max_pages: Maximum number of pages to fetch.

        Yields:
            Individual items from paginated results.
        """
        current_path: Optional[str] = path
        current_params = params or {}
        page_count = 0

        while current_path:
            if max_pages and page_count >= max_pages:
                break

            response = await self.get(current_path, params=current_params)
            data = response.data or {}

            items = data.get(data_key, [])
            for item in items:
                yield item

            page_count += 1

            # Determine next page
            paging = data.get(next_key, {})
            next_url = paging.get(next_url_key) if isinstance(paging, dict) else None

            if next_url:
                current_path = next_url
                current_params = {}  # Next URL contains all params
            else:
                # Try cursor-based pagination
                cursors = paging.get("cursors", {}) if isinstance(paging, dict) else {}
                after = cursors.get("after")
                if after:
                    current_path = path
                    current_params = {**current_params, "after": after}
                else:
                    current_path = None

    def add_middleware(
        self, middleware: Callable[[Dict[str, Any]], Coroutine[Any, Any, Dict[str, Any]]]
    ) -> None:
        """Add a request middleware function."""
        self._middleware.append(middleware)

    def add_response_hook(self, hook: Callable[[APIResponse], Coroutine[Any, Any, None]]) -> None:
        """Add a response hook function."""
        self._response_hooks.append(hook)

    @staticmethod
    def _parse_rate_limit_remaining(headers: Dict[str, str]) -> Optional[int]:
        for key in ("X-RateLimit-Remaining", "x-ratelimit-remaining", "RateLimit-Remaining"):
            if key in headers:
                try:
                    return int(headers[key])
                except (ValueError, TypeError):
                    pass
        return None

    @staticmethod
    def _parse_rate_limit_reset(headers: Dict[str, str]) -> Optional[float]:
        for key in ("X-RateLimit-Reset", "x-ratelimit-reset", "RateLimit-Reset"):
            if key in headers:
                try:
                    return float(headers[key])
                except (ValueError, TypeError):
                    pass
        return None

    @staticmethod
    def _extract_retry_after(headers: Dict[str, str]) -> float:
        for key in ("Retry-After", "retry-after"):
            if key in headers:
                try:
                    return float(headers[key])
                except (ValueError, TypeError):
                    pass
        return 1.0
