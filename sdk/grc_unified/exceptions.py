"""Custom exceptions for the GRC Unified SDK.

This module defines the exception hierarchy used throughout the SDK.
All exceptions inherit from :class:`GRCError` so callers can catch a single
base class for any SDK-related failure.
"""

from __future__ import annotations

from typing import Any


class GRCError(Exception):
    """Base exception for all GRC Unified SDK errors.

    Attributes:
        message: Human-readable error description.
        code: Optional machine-readable error code.
        details: Optional dict with additional context (e.g. project ID,
            HTTP status, retry-after).
    """

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}

    def __str__(self) -> str:
        parts = [self.message]
        if self.code:
            parts.append(f"(code={self.code})")
        if self.details:
            parts.append(f"details={self.details}")
        return " ".join(parts)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(message={self.message!r}, "
            f"code={self.code!r}, details={self.details!r})"
        )


class AuthenticationError(GRCError):
    """Raised when authentication with a GRC project fails.

    This includes invalid credentials, expired tokens, or missing
    authentication configuration.
    """

    def __init__(
        self,
        message: str = "Authentication failed",
        *,
        code: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, code=code or "AUTH_ERROR", details=details)


class AuthorizationError(GRCError):
    """Raised when the authenticated identity lacks permission.

    The caller is authenticated but does not have sufficient privileges
    for the requested operation.
    """

    def __init__(
        self,
        message: str = "Access denied",
        *,
        code: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, code=code or "FORBIDDEN", details=details)


class NotFoundError(GRCError):
    """Raised when a requested resource does not exist."""

    def __init__(
        self,
        message: str = "Resource not found",
        *,
        code: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, code=code or "NOT_FOUND", details=details)


class ValidationError(GRCError):
    """Raised when input validation fails.

    This is distinct from Pydantic's ``ValidationError`` — it is raised
    by SDK-level pre-flight checks before a request is sent.
    """

    def __init__(
        self,
        message: str = "Validation failed",
        *,
        code: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, code=code or "VALIDATION_ERROR", details=details)


class RateLimitError(GRCError):
    """Raised when a rate limit is exceeded.

    Attributes:
        retry_after: Seconds to wait before retrying, if provided by the
            server.
    """

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        *,
        retry_after: float | None = None,
        code: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        merged_details = details or {}
        if retry_after is not None:
            merged_details.setdefault("retry_after", retry_after)
        super().__init__(message, code=code or "RATE_LIMITED", details=merged_details)
        self.retry_after = retry_after


class ServerError(GRCError):
    """Raised when the server returns a 5xx response."""

    def __init__(
        self,
        message: str = "Server error",
        *,
        status_code: int | None = None,
        code: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        merged_details = details or {}
        if status_code is not None:
            merged_details.setdefault("status_code", status_code)
        super().__init__(message, code=code or "SERVER_ERROR", details=merged_details)
        self.status_code = status_code


class ConnectionError(GRCError):
    """Raised when a network connection to a GRC project fails."""

    def __init__(
        self,
        message: str = "Connection failed",
        *,
        code: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, code=code or "CONNECTION_ERROR", details=details)


class TimeoutError(GRCError):
    """Raised when a request to a GRC project times out."""

    def __init__(
        self,
        message: str = "Request timed out",
        *,
        timeout: float | None = None,
        code: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        merged_details = details or {}
        if timeout is not None:
            merged_details.setdefault("timeout", timeout)
        super().__init__(message, code=code or "TIMEOUT", details=merged_details)
        self.timeout = timeout


class ConfigurationError(GRCError):
    """Raised when SDK configuration is invalid or incomplete."""

    def __init__(
        self,
        message: str = "Configuration error",
        *,
        code: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, code=code or "CONFIG_ERROR", details=details)


class ProjectNotFoundError(GRCError):
    """Raised when a requested project ID is not in the registry."""

    def __init__(
        self,
        message: str = "Project not found",
        *,
        project_id: str | None = None,
        code: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        merged_details = details or {}
        if project_id is not None:
            merged_details.setdefault("project_id", project_id)
        super().__init__(message, code=code or "PROJECT_NOT_FOUND", details=merged_details)
        self.project_id = project_id


class ConflictError(GRCError):
    """Raised when an operation conflicts with the current resource state."""

    def __init__(
        self,
        message: str = "Resource conflict",
        *,
        code: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, code=code or "CONFLICT", details=details)
