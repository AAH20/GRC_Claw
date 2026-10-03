"""Gated Communities API client.

Provides a fully-typed, authenticated HTTP client for the Gated Communities
REST API. Supports API key authentication, automatic retries with
exponential backoff, and both synchronous and asynchronous usage patterns.
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any, TypeVar, overload

import httpx
from pydantic import BaseModel

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

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

DEFAULT_BASE_URL = "https://api.gatedcommunities.io/v1"
DEFAULT_TIMEOUT = 30.0
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_DELAY = 1.0


class GatedCommunitiesClient:
    """Client for the Gated Communities REST API.

    Args:
        api_key: API key for authentication. Can also be set via the
            ``GATED_COMMUNITIES_API_KEY`` environment variable.
        base_url: Override the default API base URL.
        timeout: Request timeout in seconds.
        max_retries: Maximum number of retry attempts for transient failures.
        retry_delay: Initial delay between retries in seconds (doubles each attempt).
        http_client: Optional pre-configured ``httpx.Client`` for advanced use.

    Example:
        >>> from gated_communities import GatedCommunitiesClient
        >>> client = GatedCommunitiesClient(api_key="gc_live_...")
        >>> communities = client.communities.list()
        >>> for community in communities.data:
        ...     print(community.name)
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_delay: float = DEFAULT_RETRY_DELAY,
        http_client: httpx.Client | None = None,
    ) -> None:
        import os

        self._api_key = api_key or os.environ.get("GATED_COMMUNITIES_API_KEY")
        if not self._api_key:
            raise AuthenticationError(
                "API key is required. Pass it as the `api_key` argument "
                "or set the GATED_COMMUNITIES_API_KEY environment variable."
            )

        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._max_retries = max_retries
        self._retry_delay = retry_delay

        self._client = http_client or httpx.Client(
            base_url=self._base_url,
            timeout=self._timeout,
            headers=self._default_headers(),
        )

        # Resource namespaces
        self._communities: CommunitiesResource | None = None
        self._members: MembersResource | None = None
        self._users: UsersResource | None = None
        self._api_keys: ApiKeysResource | None = None

    # ─── Properties ─────────────────────────────────────────────────────

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

    # ─── Public Methods ──────────────────────────────────────────────────

    def close(self) -> None:
        """Close the underlying HTTP client and release resources."""
        self._client.close()

    def __enter__(self) -> GatedCommunitiesClient:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    # ─── Internal Helpers ────────────────────────────────────────────────

    def _default_headers(self) -> dict[str, str]:
        """Build default headers for all requests."""
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": f"gated-communities-sdk/1.0.0",
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
        """Execute an HTTP request with retry logic.

        Retries on rate-limit (429) and server (5xx) errors with
        exponential backoff. Authentication and validation errors
        are raised immediately without retry.
        """
        url = self._url(path)
        request_headers = {**self._default_headers(), **(headers or {})}

        last_exception: Exception | None = None

        for attempt in range(self._max_retries + 1):
            try:
                logger.debug(
                    "Request: %s %s (attempt %d/%d)",
                    method,
                    url,
                    attempt + 1,
                    self._max_retries + 1,
                )
                response = self._client.request(
                    method,
                    url,
                    params=params,
                    json=json_body,
                    headers=request_headers,
                )

                if response.is_success:
                    return response

                # Don't retry client errors (except 429)
                if response.status_code < 500 and response.status_code != 429:
                    self._handle_error(response)

                # Retryable error — check if we should retry
                if attempt < self._max_retries:
                    delay = self._retry_delay * (2**attempt)
                    if response.status_code == 429:
                        retry_after = response.headers.get("Retry-After")
                        if retry_after:
                            delay = max(delay, float(retry_after))
                    logger.warning(
                        "Retryable error (HTTP %d) on %s %s — retrying in %.1fs",
                        response.status_code,
                        method,
                        url,
                        delay,
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
                        "Timeout on %s %s — retrying in %.1fs",
                        method,
                        url,
                        delay,
                    )
                    time.sleep(delay)
                    continue
                raise last_exception from e

            except httpx.ConnectError as e:
                last_exception = ConnectionError(f"Connection failed: {e}")
                if attempt < self._max_retries:
                    delay = self._retry_delay * (2**attempt)
                    logger.warning(
                        "Connection error on %s %s — retrying in %.1fs",
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
        raise GatedCommunitiesError("Unexpected error: request failed after all retries")

    def _get(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        model: type[T] | None = None,
    ) -> T | dict[str, Any]:
        """Execute a GET request and optionally parse the response."""
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
        """Execute a POST request and optionally parse the response."""
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
        """Execute a PATCH request and optionally parse the response."""
        response = self._request("PATCH", path, json_body=json_body)
        data = response.json()
        if model is not None:
            return model.model_validate(data)
        return data

    def _delete(self, path: str) -> None:
        """Execute a DELETE request."""
        self._request("DELETE", path)


# ─── Resource: Communities ─────────────────────────────────────────────────────


class CommunitiesResource:
    """Resource namespace for community endpoints."""

    def __init__(self, client: GatedCommunitiesClient) -> None:
        self._client = client

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


# ─── Resource: Members ─────────────────────────────────────────────────────────


class MembersResource:
    """Resource namespace for member endpoints."""

    def __init__(self, client: GatedCommunitiesClient) -> None:
        self._client = client

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


# ─── Resource: Users ───────────────────────────────────────────────────────────


class UsersResource:
    """Resource namespace for user endpoints."""

    def __init__(self, client: GatedCommunitiesClient) -> None:
        self._client = client

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


# ─── Resource: API Keys ────────────────────────────────────────────────────────


class ApiKeysResource:
    """Resource namespace for API key management endpoints."""

    def __init__(self, client: GatedCommunitiesClient) -> None:
        self._client = client

    def list(
        self, *, page: int = 1, per_page: int = 20
    ) -> PaginatedResponse[ApiKey]:
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
