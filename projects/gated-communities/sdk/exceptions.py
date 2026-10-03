"""Custom exceptions for the Gated Communities SDK.

All exceptions raised by this SDK inherit from :class:`GatedCommunitiesError`,
allowing callers to catch a single base class for any SDK-specific failure.
"""

from __future__ import annotations

from typing import Any


class GatedCommunitiesError(Exception):
    """Base exception for all Gated Communities SDK errors.

    Attributes:
        message: Human-readable error description.
        status_code: HTTP status code, if applicable.
        response_body: Raw response body from the server, if available.
    """

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response_body: Any = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response_body = response_body

    def __str__(self) -> str:
        parts = [self.message]
        if self.status_code is not None:
            parts.append(f"(HTTP {self.status_code})")
        return " ".join(parts)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"message={self.message!r}, "
            f"status_code={self.status_code!r}, "
            f"response_body={self.response_body!r})"
        )


class AuthenticationError(GatedCommunitiesError):
    """Raised when authentication fails (HTTP 401).

    This typically means the API key is missing, invalid, or expired.
    """


class AuthorizationError(GatedCommunitiesError):
    """Raised when the authenticated user lacks permission (HTTP 403)."""


class NotFoundError(GatedCommunitiesError):
    """Raised when a requested resource does not exist (HTTP 404)."""


class ValidationError(GatedCommunitiesError):
    """Raised when the server rejects the request payload (HTTP 422).

    The ``response_body`` attribute typically contains a dict with
    field-level error details.
    """


class RateLimitError(GatedCommunitiesError):
    """Raised when the API rate limit is exceeded (HTTP 429).

    Attributes:
        retry_after: Seconds to wait before retrying, if provided by the server.
    """

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        status_code: int | None = 429,
        response_body: Any = None,
        retry_after: float | None = None,
    ) -> None:
        super().__init__(message, status_code, response_body)
        self.retry_after = retry_after


class ServerError(GatedCommunitiesError):
    """Raised when the server returns a 5xx error."""


class ConnectionError(GatedCommunitiesError):
    """Raised when a network-level connection error occurs."""


class TimeoutError(GatedCommunitiesError):
    """Raised when a request times out."""
