"""Custom exceptions for the Recruitment Platform SDK.

Provides a hierarchy of exceptions for different HTTP error categories
with rich context information for debugging and error handling.
"""

from __future__ import annotations

from typing import Any

from .logging_config import get_logger

logger = get_logger(__name__)


class RecruitmentPlatformError(Exception):
    """Base exception for all Recruitment Platform SDK errors.

    Attributes:
        message: Human-readable error description.
        status_code: HTTP status code if available.
        response_body: Raw response body if available.
        request_id: Request ID from response headers if available.
        error_code: Application-specific error code if available.
        retry_after: Seconds to wait before retrying (for rate limits).
    """

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response_body: Any = None,
        request_id: str | None = None,
        error_code: str | None = None,
        retry_after: float | None = None,
    ) -> None:
        super().__init__(message)
        self.message: str = message
        self.status_code: int | None = status_code
        self.response_body: Any = response_body
        self.request_id: str | None = request_id
        self.error_code: str | None = error_code
        self.retry_after: float | None = retry_after

    def __str__(self) -> str:
        parts = [self.message]
        if self.status_code is not None:
            parts.append(f"(status: {self.status_code})")
        if self.request_id is not None:
            parts.append(f"(request_id: {self.request_id})")
        if self.error_code is not None:
            parts.append(f"(code: {self.error_code})")
        return " ".join(parts)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"message={self.message!r}, "
            f"status_code={self.status_code!r}, "
            f"request_id={self.request_id!r}, "
            f"error_code={self.error_code!r})"
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize the exception to a dictionary.

        Returns:
            Dictionary representation of the error for logging or API responses.
        """
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "status_code": self.status_code,
            "request_id": self.request_id,
            "error_code": self.error_code,
            "retry_after": self.retry_after,
            "response_body": self.response_body,
        }

    @classmethod
    def from_response(
        cls,
        status_code: int,
        body: Any,
        request_id: str | None = None,
    ) -> RecruitmentPlatformError:
        """Create an appropriate exception from an HTTP response.

        Args:
            status_code: HTTP status code.
            body: Response body (parsed JSON or raw text).
            request_id: Request ID from response headers.

        Returns:
            An instance of the appropriate exception subclass.
        """
        message = ""
        error_code = None
        retry_after = None

        if isinstance(body, dict):
            message = str(body.get("detail", body.get("message", "")))
            error_code = body.get("error_code")
            retry_after_raw = body.get("retry_after")
            if retry_after_raw is not None:
                try:
                    retry_after = float(retry_after_raw)
                except (TypeError, ValueError):
                    retry_after = None

        if not message:
            message = f"HTTP {status_code}"

        common_args: dict[str, Any] = {
            "status_code": status_code,
            "response_body": body,
            "request_id": request_id,
            "error_code": error_code,
        }

        if status_code == 401:
            return AuthenticationError(message, **common_args)
        if status_code == 404:
            return NotFoundError(message, **common_args)
        if status_code == 422:
            return ValidationError(message, **common_args)
        if status_code == 429:
            return RateLimitError(message, retry_after=retry_after, **common_args)
        if status_code >= 500:
            return ServerError(message, **common_args)
        return cls(message, **common_args)


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
    The retry_after attribute indicates how many seconds to wait.
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


class CacheError(RecruitmentPlatformError):
    """Raised when a cache operation fails.

    This may indicate Redis connectivity issues or serialization errors.
    """


class ConfigurationError(RecruitmentPlatformError):
    """Raised when the SDK is misconfigured.

    This may indicate invalid parameters, missing required settings,
    or incompatible configuration combinations.
    """
