"""Custom exceptions for the Recruitment Platform SDK."""

from __future__ import annotations

from typing import Any


class RecruitmentPlatformError(Exception):
    """Base exception for all Recruitment Platform SDK errors.

    Attributes:
        message: Human-readable error description.
        status_code: HTTP status code if available.
        response_body: Raw response body if available.
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
            parts.append(f"(status: {self.status_code})")
        return " ".join(parts)


class AuthenticationError(RecruitmentPlatformError):
    """Raised when authentication fails (401)."""


class NotFoundError(RecruitmentPlatformError):
    """Raised when a resource is not found (404)."""


class RateLimitError(RecruitmentPlatformError):
    """Raised when rate limit is exceeded (429)."""


class ServerError(RecruitmentPlatformError):
    """Raised when the server returns a 5xx error."""


class ValidationError(RecruitmentPlatformError):
    """Raised when request validation fails (422)."""
