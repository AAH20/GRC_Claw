"""Error handling for the GRC Marketing SDK."""

from __future__ import annotations

from typing import Any, Dict, Optional


class GRCMarketingError(Exception):
    """Base exception for all GRC Marketing SDK errors."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_body: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response_body = response_body or {}

    def __str__(self) -> str:
        if self.status_code:
            return f"[{self.status_code}] {self.message}"
        return self.message


class AuthenticationError(GRCMarketingError):
    """Raised when authentication fails (401)."""

    def __init__(
        self,
        message: str = "Authentication failed",
        response_body: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, status_code=401, response_body=response_body)


class AuthorizationError(GRCMarketingError):
    """Raised when the user lacks permission (403)."""

    def __init__(
        self,
        message: str = "Access denied",
        response_body: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, status_code=403, response_body=response_body)


class NotFoundError(GRCMarketingError):
    """Raised when a resource is not found (404)."""

    def __init__(
        self,
        message: str = "Resource not found",
        response_body: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, status_code=404, response_body=response_body)


class ValidationError(GRCMarketingError):
    """Raised when request validation fails (422)."""

    def __init__(
        self,
        message: str = "Validation failed",
        response_body: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, status_code=422, response_body=response_body)


class RateLimitError(GRCMarketingError):
    """Raised when rate limit is exceeded (429)."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        response_body: Optional[Dict[str, Any]] = None,
        retry_after: Optional[int] = None,
    ) -> None:
        super().__init__(message, status_code=429, response_body=response_body)
        self.retry_after = retry_after


class ServerError(GRCMarketingError):
    """Raised when the server returns a 5xx error."""

    def __init__(
        self,
        message: str = "Internal server error",
        status_code: int = 500,
        response_body: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, status_code=status_code, response_body=response_body)


class NetworkError(GRCMarketingError):
    """Raised when a network-level error occurs."""

    def __init__(
        self,
        message: str = "Network error",
        original_error: Optional[Exception] = None,
    ) -> None:
        super().__init__(message)
        self.original_error = original_error


class TimeoutError(GRCMarketingError):
    """Raised when a request times out."""

    def __init__(
        self,
        message: str = "Request timed out",
        timeout_seconds: Optional[float] = None,
    ) -> None:
        super().__init__(message)
        self.timeout_seconds = timeout_seconds


class ConfigurationError(GRCMarketingError):
    """Raised when the SDK is misconfigured."""

    def __init__(self, message: str = "SDK configuration error") -> None:
        super().__init__(message)


def raise_for_status(
    status_code: int,
    response_body: Optional[Dict[str, Any]] = None,
) -> None:
    """Raise the appropriate exception for an HTTP status code.

    Args:
        status_code: The HTTP status code.
        response_body: The parsed response body, if available.

    Raises:
        GRCMarketingError: The appropriate error subclass.
    """
    message = "Unknown error"
    if response_body and isinstance(response_body, dict):
        message = response_body.get("message", response_body.get("error", message))

    error_map = {
        401: AuthenticationError,
        403: AuthorizationError,
        404: NotFoundError,
        422: ValidationError,
        429: RateLimitError,
    }

    error_cls = error_map.get(status_code)
    if error_cls:
        raise error_cls(message=message, response_body=response_body)

    if status_code >= 500:
        raise ServerError(
            message=message, status_code=status_code, response_body=response_body
        )

    if status_code >= 400:
        raise GRCMarketingError(
            message=message, status_code=status_code, response_body=response_body
        )
