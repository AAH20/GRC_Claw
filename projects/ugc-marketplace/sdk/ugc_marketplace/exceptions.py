"""Custom exceptions for the UGC Marketplace SDK."""

from __future__ import annotations

from typing import Any


class UGCMarketplaceError(Exception):
    """Base exception for all UGC Marketplace SDK errors."""

    def __init__(self, message: str, status_code: int | None = None, response: Any = None) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response = response


class UGCAuthenticationError(UGCMarketplaceError):
    """Raised when authentication fails (401)."""

    def __init__(self, message: str = "Authentication failed", response: Any = None) -> None:
        super().__init__(message, status_code=401, response=response)


class UGCNotFoundError(UGCMarketplaceError):
    """Raised when a requested resource is not found (404)."""

    def __init__(self, message: str = "Resource not found", response: Any = None) -> None:
        super().__init__(message, status_code=404, response=response)


class UGCRateLimitError(UGCMarketplaceError):
    """Raised when rate limit is exceeded (429)."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: int | None = None,
        response: Any = None,
    ) -> None:
        super().__init__(message, status_code=429, response=response)
        self.retry_after = retry_after


class UGCValidationError(UGCMarketplaceError):
    """Raised when request validation fails (422)."""

    def __init__(self, message: str = "Validation error", errors: dict | None = None, response: Any = None) -> None:
        super().__init__(message, status_code=422, response=response)
        self.errors = errors or {}


class UGCServerError(UGCMarketplaceError):
    """Raised when the server returns a 5xx error."""

    def __init__(self, message: str = "Internal server error", response: Any = None) -> None:
        super().__init__(message, status_code=500, response=response)
