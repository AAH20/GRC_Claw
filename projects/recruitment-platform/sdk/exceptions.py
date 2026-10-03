"""Custom exceptions for the Recruitment Platform SDK.

Provides a hierarchy of exceptions for different HTTP error categories
with rich context information for debugging and error handling.
"""

from __future__ import annotations

from typing import Any


class RecruitmentPlatformError(Exception):
    """Base exception for all Recruitment Platform SDK errors.

    Attributes:
        message: Human-readable error description.
        status_code: HTTP status code if available.
        response_body: Raw response body if available.
        request_id: Request ID from response headers if available.
    """

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response_body: Any = None,
        request_id: str | None = None,
    ) -> None:
        super().__init__(message)
        self.message: str = message
        self.status_code: int | None = status_code
        self.response_body: Any = response_body
        self.request_id: str | None = request_id

    def __str__(self) -> str:
        parts = [self.message]
        if self.status_code is not None:
            parts.append(f"(status: {self.status_code})")
        if self.request_id is not None:
            parts.append(f"(request_id: {self.request_id})")
        return " ".join(parts)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"message={self.message!r}, "
            f"status_code={self.status_code!r}, "
            f"request_id={self.request_id!r})"
        )


class AuthenticationError(RecruitmentPlatformError):
    """Raised when authentication fails (401).

    This typically indicates an invalid or expired API key.
    """


class NotFoundError(RecruitmentPlatformError):
    """Raised when a resource is not found (404).

    The requested endpoint or resource does not exist.
    """


class RateLimitError(RecruitmentPlatformError):
    """Raised when rate limit is exceeded (429).

    The API rate limit has been exceeded. Wait before retrying.
    """


class ServerError(RecruitmentPlatformError):
    """Raised when the server returns a 5xx error.

    The server encountered an internal error. This is typically
    transient and the request may succeed on retry.
    """


class ValidationError(RecruitmentPlatformError):
    """Raised when request validation fails (422).

    The request body or parameters failed server-side validation.
    Check the response_body for specific validation errors.
    """


class TimeoutError(RecruitmentPlatformError):  # noqa: A001
    """Raised when a request times out.

    The server did not respond within the configured timeout period.
    """


class ConnectionError(RecruitmentPlatformError):  # noqa: A001
    """Raised when a connection to the server fails.

    The server could not be reached. Check network connectivity
    and the base_url configuration.
    """
