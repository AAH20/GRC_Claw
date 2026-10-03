"""Gated Communities API client.

Provides a fully-typed, authenticated HTTP client for the Gated Communities
REST API. Supports API key authentication, automatic retries with
exponential backoff, rate limiting, caching, structured logging, and
both synchronous and asynchronous usage patterns.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import os
import time
import uuid
from typing import Any, TypeVar

import httpx
from pydantic import BaseModel

from .cache import ResponseCache
from .exceptions import (
    AuthenticationError,
    AuthorizationError,
    ConnectionError,
    GatedCommunitiesError,
    NotFoundError,
    RateLimitError,
    ServerError,
    TimeoutError,
    ValidationError,
)
from .logging_config import RequestContext
from .models import (
    ApiKey,
    Community,
    CommunityCreate,
    CommunityUpdate,
    Member,
    MemberCreate,
    MemberUpdate,
    PaginatedResponse,
    User,
)
from .rate_limiter import AsyncRateLimiter, RateLimiter

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

DEFAULT_BASE_URL = "https://api.gatedcommunities.io/v1"
DEFAULT_TIMEOUT = 30.0
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_DELAY = 1.0
DEFAULT_RATE_LIMIT_RPS = 10.0
DEFAULT_RATE_LIMIT_BURST = 20.0
DEFAULT_CACHE_TTL = 300


class GatedCommunitiesClient:
    """Client for the Gated Communities REST API.

    Supports both synchronous and asynchronous operations. Includes
    automatic retries with exponential backoff, token-bucket rate
    limiting, Redis-backed response caching, and structured logging.

    Args:
        api_key: API key for authentication. Can also be set via the
            GATED_COMMUNITIES_API_KEY environment variable.
        base_url: Override the default API base URL.
        timeout: Request timeout in seconds.
        max_retries: Maximum number of retry attempts for transient failures.
        retry_delay: Initial delay between retries in seconds (doubles each attempt).
        http_client: Optional pre-configured httpx.Client for advanced use.
        async_http_client: Optional pre-configured httpx.AsyncClient.
        enable_caching: Whether to enable response caching.
        cache_ttl: Cache time-to-live in seconds.
        enable_rate_limiting: Whether to enable client-side rate limiting.
        rate_limit_rps: Requests per second limit.
        rate_limit_burst: Maximum burst size.
        enable_structured_logging: Whether to enable JSON structured logging.

    Example:
        >>> from gated_communities import GatedCommunitiesClient
        >>> client = GatedCommunitiesClient(api_key="gc_live_...")
        >>> communities = client.communities.list()
        >>> for community in communities.data:
        ...     print(community.name)

    Async Example:
        >>> from gated_communities import GatedCommunitiesClient
        >>> async with GatedCommunitiesClient(api_key="gc_live_...") as client:
        ...     communities = await client.communities.list_async()
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_delay: float = DEFAULT_RETRY_DELAY,
        http_client: httpx.Client | None = None,
        async_http_client: httpx.AsyncClient | None = None,
        enable_caching: bool = True,
        cache_ttl: int = DEFAULT_CACHE_TTL,
        enable_rate_limiting: bool = True,
        rate_limit_rps: float = DEFAULT_RATE_LIMIT_RPS,
        rate_limit_burst: float = DEFAULT_RATE_LIMIT_BURST,
        enable_structured_logging: bool = True,
    ) -> None:
        self._api_key = api_key or os.environ.get("GATED_COMMUNITIES_API_KEY")
        if not self._api_key:
            raise AuthenticationError(
                "API key is required. Pass it as the api_key argument "
                "or set the GATED_COMMUNITIES_API_KEY environment variable."
            )

        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._max_retries = max_retries
        self._retry_delay = retry_delay

        # HTTP clients
        self._client = http_client or httpx.Client(
            base_url=self._base_url,
            timeout=self._timeout,
            headers=self._default_headers(),
        )
        self._async_client = async_http_client

        # Caching
        self._cache = ResponseCache(default_ttl=cache_ttl) if enable_caching else None

        # Rate limiting
        self._rate_limiter = (
            RateLimiter(requests_per_second=rate_limit_rps, burst_size=rate_limit_burst)
            if enable_rate_limiting
            else None
        )
        self._async_rate_limiter = (
            AsyncRateLimiter(
                requests_per_second=rate_limit_rps, burst_size=rate_limit_burst
            )
            if enable_rate_limiting
            else None
        )

        # Logging
        if enable_structured_logging:
            from .logging_config import setup_logging

            setup_logging()

        # Resource namespaces
        self._communities: CommunitiesResource | None = None
        self._members: MembersResource | None = None
        self._users: UsersResource | None = None
        self._api_keys: ApiKeysResource | None = None

    # Properties

    @property
    def communities(self) -> CommunitiesResource:
        """Access community-related endpoints."""
        if self._communities is None:
            self._communities = CommunitiesResource(self)
        return self._communities

    @property
    def members(self) -> MembersResource:
        """Access member-related endpoints."""
        if self._members is None:
            self._members = MembersResource(self)
        return self._members

    @property
    def users(self) -> UsersResource:
        """Access user-related endpoints."""
        if self._users is None:
            self._users = UsersResource(self)
        return self._users

    @property
    def api_keys(self) -> ApiKeysResource:
        """Access API key management endpoints."""
        if self._api_keys is None:
            self._api_keys = ApiKeysResource(self)
        return self._api_keys

    # Public Methods

    def close(self) -> None:
        """Close the underlying HTTP client and release resources."""
        self._client.close()

    async def close_async(self) -> None:
        """Close the underlying async HTTP client and release resources."""
        if self._async_client is not None:
            await self._async_client.aclose()

    def __enter__(self) -> GatedCommunitiesClient:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    async def __aenter__(self) -> GatedCommunitiesClient:
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close_async()

    # Internal Helpers

    def _default_headers(self) -> dict[str, str]:
        """Build default headers for all requests."""
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "gated-communities-sdk/1.0.0",
        }

    def _url(self, path: str) -> str:
        """Build a full URL from a path."""
        return f"{self._base_url}/{path.lstrip('/')}"

    def _handle_error(self, response: httpx.Response) -> None:
        """Map an HTTP error response to the appropriate SDK exception."""
        status = response.status_code
        body: Any = None
        try:
            body = response.json()
        except (json.JSONDecodeError, ValueError):
            body = response.text

        message = "An error occurred"
        if isinstance(body, dict):
            message = body.get("message") or body.get("error") or message
        elif isinstance(body, str) and body:
            message = body

        if status == 401:
            raise AuthenticationError(message, status, body)
        elif status == 403:
            raise AuthorizationError(message, status, body)
        elif status == 404:
            raise NotFoundError(message, status, body)
        elif status == 422:
            raise ValidationError(message, status, body)
        elif status == 429:
            retry_after = None
            if isinstance(body, dict):
                retry_after = body.get("retry_after")
            raise RateLimitError(message, status, body, retry_after)
        elif 500 <= status < 600:
            raise ServerError(message, status, body)
        else:
            raise GatedCommunitiesError(message, status, body)

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        """Execute an HTTP request with retry logic, rate limiting, and caching.

        Retries on rate-limit (429) and server (5xx) errors with
        exponential backoff. Authentication and validation errors
        are raised immediately without retry.

        Args:
            method: HTTP method (GET, POST, PATCH, DELETE).
            path: API path.
            params: Query parameters.
            json_body: JSON request body.
            headers: Additional headers.

        Returns:
            The HTTP response object.

        Raises:
            AuthenticationError: On 401 responses.
            AuthorizationError: On 403 responses.
            NotFoundError: On 404 responses.
            ValidationError: On 422 responses.
            RateLimitError: On 429 responses after retries exhausted.
            ServerError: On 5xx responses after retries exhausted.
            TimeoutError: On request timeout after retries exhausted.
            ConnectionError: On connection failure after retries exhausted.
        """
        url = self._url(path)
        request_headers = {**self._default_headers(), **(headers or {})}
        request_id = str(uuid.uuid4())[:8]

        # Check cache for GET requests
        if method == "GET" and self._cache is not None:
            cached = self._cache.get(method, url, params)
            if cached is not None:
                logger.debug("Cache hit for %s %s", method, url)
                return httpx.Response(200, json=cached)

        # Rate limiting
        if self._rate_limiter is not None:
            self._rate_limiter.acquire()

        last_exception: Exception | None = None

        for attempt in range(self._max_retries + 1):
            ctx = RequestContext(logger, request_id, method, url)
            try:
                with ctx:
                    ctx.log(
                        logging.DEBUG,
                        f"Request attempt {attempt + 1}/{self._max_retries + 1}",
                        attempt=attempt + 1,
                        max_retries=self._max_retries + 1,
                    )
                    response = self._client.request(
                        method,
                        url,
                        params=params,
                        json=json_body,
                        headers=request_headers,
                    )

                    if response.is_success:
                        # Cache successful GET responses
                        if method == "GET" and self._cache is not None:
                            with contextlib.suppress(json.JSONDecodeError, ValueError):
                                self._cache.set(method, url, response.json(), params)
                        return response

                    # Don't retry client errors (except 429)
                    if response.status_code < 500 and response.status_code != 429:
                        self._handle_error(response)

                    # Retryable error - check if we should retry
                    if attempt < self._max_retries:
                        delay = self._retry_delay * (2**attempt)
                        if response.status_code == 429:
                            retry_after = response.headers.get("Retry-After")
                            if retry_after:
                                delay = max(delay, float(retry_after))
                        ctx.log(
                            logging.WARNING,
                            f"Retryable error (HTTP {response.status_code}), "
                            f"retrying in {delay:.1f}s",
                            status_code=response.status_code,
                            attempt=attempt + 1,
                            max_retries=self._max_retries + 1,
                        )
                        time.sleep(delay)
                        continue

                    # Exhausted retries
                    self._handle_error(response)

            except httpx.TimeoutException as e:
                last_exception = TimeoutError(f"Request timed out: {e}")
                if attempt < self._max_retries:
                    delay = self._retry_delay * (2**attempt)
                    logger.warning(
                        "Timeout on %s %s - retrying in %.1fs", method, url, delay
                    )
                    time.sleep(delay)
                    continue
                raise last_exception from e

            except httpx.ConnectError as e:
                last_exception = ConnectionError(f"Connection failed: {e}")
                if attempt < self._max_retries:
                    delay = self._retry_delay * (2**attempt)
                    logger.warning(
                        "Connection error on %s %s - retrying in %.1fs",
                        method,
                        url,
                        delay,
                    )
                    time.sleep(delay)
                    continue
                raise last_exception from e

        # Should not reach here, but just in case
        if last_exception:
            raise last_exception
        raise GatedCommunitiesError(
            "Unexpected error: request failed after all retries"
        )

    async def _request_async(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        """Execute an async HTTP request with retry logic, rate limiting, and caching.

        Retries on rate-limit (429) and server (5xx) errors with
        exponential backoff. Authentication and validation errors
        are raised immediately without retry.

        Args:
            method: HTTP method (GET, POST, PATCH, DELETE).
            path: API path.
            params: Query parameters.
            json_body: JSON request body.
            headers: Additional headers.

        Returns:
            The HTTP response object.

        Raises:
            AuthenticationError: On 401 responses.
            AuthorizationError: On 403 responses.
            NotFoundError: On 404 responses.
            ValidationError: On 422 responses.
            RateLimitError: On 429 responses after retries exhausted.
            ServerError: On 5xx responses after retries exhausted.
            TimeoutError: On request timeout after retries exhausted.
            ConnectionError: On connection failure after retries exhausted.
        """
        url = self._url(path)
        request_headers = {**self._default_headers(), **(headers or {})}
        request_id = str(uuid.uuid4())[:8]

        # Check cache for GET requests
        if method == "GET" and self._cache is not None:
            cached = self._cache.get(method, url, params)
            if cached is not None:
                logger.debug("Cache hit for %s %s", method, url)
                return httpx.Response(200, json=cached)

        # Rate limiting
        if self._async_rate_limiter is not None:
            await self._async_rate_limiter.acquire()

        # Create async client if needed
        if self._async_client is None:
            self._async_client = httpx.AsyncClient(
                base_url=self._base_url,
                timeout=self._timeout,
                headers=self._default_headers(),
            )

        last_exception: Exception | None = None

        for attempt in range(self._max_retries + 1):
            ctx = RequestContext(logger, request_id, method, url)
            try:
                with ctx:
                    ctx.log(
                        logging.DEBUG,
                        f"Async request attempt {attempt + 1}/{self._max_retries + 1}",
                        attempt=attempt + 1,
                        max_retries=self._max_retries + 1,
                    )
                    response = await self._async_client.request(
                        method,
                        url,
                        params=params,
                        json=json_body,
                        headers=request_headers,
                    )

                    if response.is_success:
                        # Cache successful GET responses
                        if method == "GET" and self._cache is not None:
                            with contextlib.suppress(json.JSONDecodeError, ValueError):
                                self._cache.set(method, url, response.json(), params)
                        return response

                    # Don't retry client errors (except 429)
                    if response.status_code < 500 and response.status_code != 429:
                        self._handle_error(response)

                    # Retryable error - check if we should retry
                    if attempt < self._max_retries:
                        delay = self._retry_delay * (2**attempt)
                        if response.status_code == 429:
                            retry_after = response.headers.get("Retry-After")
                            if retry_after:
                                delay = max(delay, float(retry_after))
                        ctx.log(
                            logging.WARNING,
                            f"Retryable error (HTTP {response.status_code}), "
                            f"retrying in {delay:.1f}s",
                            status_code=response.status_code,
                            attempt=attempt + 1,
                            max_retries=self._max_retries + 1,
                        )
                        await asyncio.sleep(delay)
                        continue

                    # Exhausted retries
                    self._handle_error(response)

            except httpx.TimeoutException as e:
                last_exception = TimeoutError(f"Request timed out: {e}")
                if attempt < self._max_retries:
                    delay = self._retry_delay * (2**attempt)
                    logger.warning(
                        "Timeout on %s %s - retrying in %.1fs", method, url, delay
                    )
                    await asyncio.sleep(delay)
                    continue
                raise last_exception from e

            except httpx.ConnectError as e:
                last_exception = ConnectionError(f"Connection failed: {e}")
                if attempt < self._max_retries:
                    delay = self._retry_delay * (2**attempt)
                    logger.warning(
                        "Connection error on %s %s - retrying in %.1fs",
                        method,
                        url,
                        delay,
                    )
                    await asyncio.sleep(delay)
                    continue
                raise last_exception from e

        # Should not reach here, but just in case
        if last_exception:
            raise last_exception
        raise GatedCommunitiesError(
            "Unexpected error: request failed after all retries"
        )

    def _get(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        model: type[T] | None = None,
    ) -> T | dict[str, Any]:
        """Execute a GET request and optionally parse the response.

        Args:
            path: API path.
            params: Query parameters.
            model: Pydantic model to parse the response into.

        Returns:
            Parsed response data.
        """
        response = self._request("GET", path, params=params)
        data = response.json()
        if model is not None:
            return model.model_validate(data)
        return data

    def _post(
        self,
        path: str,
        *,
        json_body: dict[str, Any] | None = None,
        model: type[T] | None = None,
    ) -> T | dict[str, Any]:
        """Execute a POST request and optionally parse the response.

        Args:
            path: API path.
            json_body: JSON request body.
            model: Pydantic model to parse the response into.

        Returns:
            Parsed response data.
        """
        response = self._request("POST", path, json_body=json_body)
        data = response.json()
        if model is not None:
            return model.model_validate(data)
        return data

    def _patch(
        self,
        path: str,
        *,
        json_body: dict[str, Any] | None = None,
        model: type[T] | None = None,
    ) -> T | dict[str, Any]:
        """Execute a PATCH request and optionally parse the response.

        Args:
            path: API path.
            json_body: JSON request body.
            model: Pydantic model to parse the response into.

        Returns:
            Parsed response data.
        """
        response = self._request("PATCH", path, json_body=json_body)
        data = response.json()
        if model is not None:
            return model.model_validate(data)
        return data

    def _delete(self, path: str) -> None:
        """Execute a DELETE request.

        Args:
            path: API path.
        """
        self._request("DELETE", path)

    async def _get_async(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        model: type[T] | None = None,
    ) -> T | dict[str, Any]:
        """Execute an async GET request and optionally parse the response.

        Args:
            path: API path.
            params: Query parameters.
            model: Pydantic model to parse the response into.

        Returns:
            Parsed response data.
        """
        response = await self._request_async("GET", path, params=params)
        data = response.json()
        if model is not None:
            return model.model_validate(data)
        return data

    async def _post_async(
        self,
        path: str,
        *,
        json_body: dict[str, Any] | None = None,
        model: type[T] | None = None,
    ) -> T | dict[str, Any]:
        """Execute an async POST request and optionally parse the response.

        Args:
            path: API path.
            json_body: JSON request body.
            model: Pydantic model to parse the response into.

        Returns:
            Parsed response data.
        """
        response = await self._request_async("POST", path, json_body=json_body)
        data = response.json()
        if model is not None:
            return model.model_validate(data)
        return data

    async def _patch_async(
        self,
        path: str,
        *,
        json_body: dict[str, Any] | None = None,
        model: type[T] | None = None,
    ) -> T | dict[str, Any]:
        """Execute an async PATCH request and optionally parse the response.

        Args:
            path: API path.
            json_body: JSON request body.
            model: Pydantic model to parse the response into.

        Returns:
            Parsed response data.
        """
        response = await self._request_async("PATCH", path, json_body=json_body)
        data = response.json()
        if model is not None:
            return model.model_validate(data)
        return data

    async def _delete_async(self, path: str) -> None:
        """Execute an async DELETE request.

        Args:
            path: API path.
        """
        await self._request_async("DELETE", path)


# Resource: Communities


class CommunitiesResource:
    """Resource namespace for community endpoints.

    Provides both synchronous and asynchronous methods for managing
    communities.
    """

    def __init__(self, client: GatedCommunitiesClient) -> None:
        self._client = client

    # Sync Methods

    def list(
        self,
        *,
        page: int = 1,
        per_page: int = 20,
        visibility: str | None = None,
        tag: str | None = None,
    ) -> PaginatedResponse[Community]:
        """List all communities visible to the authenticated user.

        Args:
            page: Page number (1-indexed).
            per_page: Number of results per page (max 100).
            visibility: Filter by visibility level.
            tag: Filter by tag.

        Returns:
            Paginated list of communities.
        """
        params: dict[str, Any] = {"page": page, "per_page": per_page}
        if visibility:
            params["visibility"] = visibility
        if tag:
            params["tag"] = tag

        data = self._client._get("/communities", params=params)
        return PaginatedResponse[Community].model_validate(data)

    def get(self, community_id: str) -> Community:
        """Get a single community by ID.

        Args:
            community_id: The unique community identifier.

        Returns:
            The community object.
        """
        data = self._client._get(f"/communities/{community_id}")
        return Community.model_validate(data)

    def create(self, payload: CommunityCreate) -> Community:
        """Create a new community.

        Args:
            payload: Community creation data.

        Returns:
            The newly created community.
        """
        data = self._client._post(
            "/communities",
            json_body=payload.model_dump(exclude_none=True),
        )
        return Community.model_validate(data)

    def update(self, community_id: str, payload: CommunityUpdate) -> Community:
        """Update an existing community.

        Args:
            community_id: The unique community identifier.
            payload: Fields to update.

        Returns:
            The updated community.
        """
        data = self._client._patch(
            f"/communities/{community_id}",
            json_body=payload.model_dump(exclude_none=True),
        )
        return Community.model_validate(data)

    def delete(self, community_id: str) -> None:
        """Delete a community permanently.

        Args:
            community_id: The unique community identifier.
        """
        self._client._delete(f"/communities/{community_id}")

    # Async Methods

    async def list_async(
        self,
        *,
        page: int = 1,
        per_page: int = 20,
        visibility: str | None = None,
        tag: str | None = None,
    ) -> PaginatedResponse[Community]:
        """List all communities visible to the authenticated user (async).

        Args:
            page: Page number (1-indexed).
            per_page: Number of results per page (max 100).
            visibility: Filter by visibility level.
            tag: Filter by tag.

        Returns:
            Paginated list of communities.
        """
        params: dict[str, Any] = {"page": page, "per_page": per_page}
        if visibility:
            params["visibility"] = visibility
        if tag:
            params["tag"] = tag

        data = await self._client._get_async("/communities", params=params)
        return PaginatedResponse[Community].model_validate(data)

    async def get_async(self, community_id: str) -> Community:
        """Get a single community by ID (async).

        Args:
            community_id: The unique community identifier.

        Returns:
            The community object.
        """
        data = await self._client._get_async(f"/communities/{community_id}")
        return Community.model_validate(data)

    async def create_async(self, payload: CommunityCreate) -> Community:
        """Create a new community (async).

        Args:
            payload: Community creation data.

        Returns:
            The newly created community.
        """
        data = await self._client._post_async(
            "/communities",
            json_body=payload.model_dump(exclude_none=True),
        )
        return Community.model_validate(data)

    async def update_async(
        self, community_id: str, payload: CommunityUpdate
    ) -> Community:
        """Update an existing community (async).

        Args:
            community_id: The unique community identifier.
            payload: Fields to update.

        Returns:
            The updated community.
        """
        data = await self._client._patch_async(
            f"/communities/{community_id}",
            json_body=payload.model_dump(exclude_none=True),
        )
        return Community.model_validate(data)

    async def delete_async(self, community_id: str) -> None:
        """Delete a community permanently (async).

        Args:
            community_id: The unique community identifier.
        """
        await self._client._delete_async(f"/communities/{community_id}")


# Resource: Members


class MembersResource:
    """Resource namespace for member endpoints.

    Provides both synchronous and asynchronous methods for managing
    community members.
    """

    def __init__(self, client: GatedCommunitiesClient) -> None:
        self._client = client

    # Sync Methods

    def list(
        self,
        community_id: str,
        *,
        page: int = 1,
        per_page: int = 20,
        role: str | None = None,
        status: str | None = None,
    ) -> PaginatedResponse[Member]:
        """List members of a community.

        Args:
            community_id: The community to list members for.
            page: Page number (1-indexed).
            per_page: Number of results per page.
            role: Filter by member role.
            status: Filter by membership status.

        Returns:
            Paginated list of members.
        """
        params: dict[str, Any] = {"page": page, "per_page": per_page}
        if role:
            params["role"] = role
        if status:
            params["status"] = status

        data = self._client._get(f"/communities/{community_id}/members", params=params)
        return PaginatedResponse[Member].model_validate(data)

    def get(self, community_id: str, member_id: str) -> Member:
        """Get a specific member of a community.

        Args:
            community_id: The community identifier.
            member_id: The membership identifier.

        Returns:
            The member object.
        """
        data = self._client._get(f"/communities/{community_id}/members/{member_id}")
        return Member.model_validate(data)

    def add(self, community_id: str, payload: MemberCreate) -> Member:
        """Add a member to a community.

        Args:
            community_id: The community to add the member to.
            payload: Member creation data.

        Returns:
            The newly created membership.
        """
        data = self._client._post(
            f"/communities/{community_id}/members",
            json_body=payload.model_dump(exclude_none=True),
        )
        return Member.model_validate(data)

    def update(
        self, community_id: str, member_id: str, payload: MemberUpdate
    ) -> Member:
        """Update a membership (role, status, etc.).

        Args:
            community_id: The community identifier.
            member_id: The membership identifier.
            payload: Fields to update.

        Returns:
            The updated membership.
        """
        data = self._client._patch(
            f"/communities/{community_id}/members/{member_id}",
            json_body=payload.model_dump(exclude_none=True),
        )
        return Member.model_validate(data)

    def remove(self, community_id: str, member_id: str) -> None:
        """Remove a member from a community.

        Args:
            community_id: The community identifier.
            member_id: The membership identifier.
        """
        self._client._delete(f"/communities/{community_id}/members/{member_id}")

    # Async Methods

    async def list_async(
        self,
        community_id: str,
        *,
        page: int = 1,
        per_page: int = 20,
        role: str | None = None,
        status: str | None = None,
    ) -> PaginatedResponse[Member]:
        """List members of a community (async).

        Args:
            community_id: The community to list members for.
            page: Page number (1-indexed).
            per_page: Number of results per page.
            role: Filter by member role.
            status: Filter by membership status.

        Returns:
            Paginated list of members.
        """
        params: dict[str, Any] = {"page": page, "per_page": per_page}
        if role:
            params["role"] = role
        if status:
            params["status"] = status

        data = await self._client._get_async(
            f"/communities/{community_id}/members", params=params
        )
        return PaginatedResponse[Member].model_validate(data)

    async def get_async(self, community_id: str, member_id: str) -> Member:
        """Get a specific member of a community (async).

        Args:
            community_id: The community identifier.
            member_id: The membership identifier.

        Returns:
            The member object.
        """
        data = await self._client._get_async(
            f"/communities/{community_id}/members/{member_id}"
        )
        return Member.model_validate(data)

    async def add_async(self, community_id: str, payload: MemberCreate) -> Member:
        """Add a member to a community (async).

        Args:
            community_id: The community to add the member to.
            payload: Member creation data.

        Returns:
            The newly created membership.
        """
        data = await self._client._post_async(
            f"/communities/{community_id}/members",
            json_body=payload.model_dump(exclude_none=True),
        )
        return Member.model_validate(data)

    async def update_async(
        self, community_id: str, member_id: str, payload: MemberUpdate
    ) -> Member:
        """Update a membership (async).

        Args:
            community_id: The community identifier.
            member_id: The membership identifier.
            payload: Fields to update.

        Returns:
            The updated membership.
        """
        data = await self._client._patch_async(
            f"/communities/{community_id}/members/{member_id}",
            json_body=payload.model_dump(exclude_none=True),
        )
        return Member.model_validate(data)

    async def remove_async(self, community_id: str, member_id: str) -> None:
        """Remove a member from a community (async).

        Args:
            community_id: The community identifier.
            member_id: The membership identifier.
        """
        await self._client._delete_async(
            f"/communities/{community_id}/members/{member_id}"
        )


# Resource: Users


class UsersResource:
    """Resource namespace for user endpoints.

    Provides both synchronous and asynchronous methods for user operations.
    """

    def __init__(self, client: GatedCommunitiesClient) -> None:
        self._client = client

    # Sync Methods

    def get(self, user_id: str) -> User:
        """Get a user by ID.

        Args:
            user_id: The unique user identifier.

        Returns:
            The user object.
        """
        data = self._client._get(f"/users/{user_id}")
        return User.model_validate(data)

    def me(self) -> User:
        """Get the currently authenticated user.

        Returns:
            The authenticated user's profile.
        """
        data = self._client._get("/users/me")
        return User.model_validate(data)

    # Async Methods

    async def get_async(self, user_id: str) -> User:
        """Get a user by ID (async).

        Args:
            user_id: The unique user identifier.

        Returns:
            The user object.
        """
        data = await self._client._get_async(f"/users/{user_id}")
        return User.model_validate(data)

    async def me_async(self) -> User:
        """Get the currently authenticated user (async).

        Returns:
            The authenticated user's profile.
        """
        data = await self._client._get_async("/users/me")
        return User.model_validate(data)


# Resource: API Keys


class ApiKeysResource:
    """Resource namespace for API key management endpoints.

    Provides both synchronous and asynchronous methods for API key operations.
    """

    def __init__(self, client: GatedCommunitiesClient) -> None:
        self._client = client

    # Sync Methods

    def list(self, *, page: int = 1, per_page: int = 20) -> PaginatedResponse[ApiKey]:
        """List all API keys for the authenticated account.

        Args:
            page: Page number (1-indexed).
            per_page: Number of results per page.

        Returns:
            Paginated list of API keys.
        """
        params: dict[str, Any] = {"page": page, "per_page": per_page}
        data = self._client._get("/api-keys", params=params)
        return PaginatedResponse[ApiKey].model_validate(data)

    def get(self, key_id: str) -> ApiKey:
        """Get a specific API key by ID.

        Args:
            key_id: The unique API key identifier.

        Returns:
            The API key object.
        """
        data = self._client._get(f"/api-keys/{key_id}")
        return ApiKey.model_validate(data)

    def revoke(self, key_id: str) -> None:
        """Revoke an API key, immediately invalidating it.

        Args:
            key_id: The unique API key identifier.
        """
        self._client._delete(f"/api-keys/{key_id}")

    # Async Methods

    async def list_async(
        self, *, page: int = 1, per_page: int = 20
    ) -> PaginatedResponse[ApiKey]:
        """List all API keys for the authenticated account (async).

        Args:
            page: Page number (1-indexed).
            per_page: Number of results per page.

        Returns:
            Paginated list of API keys.
        """
        params: dict[str, Any] = {"page": page, "per_page": per_page}
        data = await self._client._get_async("/api-keys", params=params)
        return PaginatedResponse[ApiKey].model_validate(data)

    async def get_async(self, key_id: str) -> ApiKey:
        """Get a specific API key by ID (async).

        Args:
            key_id: The unique API key identifier.

        Returns:
            The API key object.
        """
        data = await self._client._get_async(f"/api-keys/{key_id}")
        return ApiKey.model_validate(data)

    async def revoke_async(self, key_id: str) -> None:
        """Revoke an API key, immediately invalidating it (async).

        Args:
            key_id: The unique API key identifier.
        """
        await self._client._delete_async(f"/api-keys/{key_id}")
