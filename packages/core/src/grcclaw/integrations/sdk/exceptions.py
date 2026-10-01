"""
Custom exceptions for the connector SDK.
"""

from __future__ import annotations


class ConnectorError(Exception):
    """Base exception for all connector errors."""

    def __init__(self, message: str, *, connector: str = "", details: dict | None = None):
        super().__init__(message)
        self.connector = connector
        self.details = details or {}


class AuthenticationError(ConnectorError):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Authentication failed", *, connector: str = "", details: dict | None = None):
        super().__init__(message, connector=connector, details=details)


class ConnectionError(ConnectorError):
    """Raised when a connection cannot be established."""

    def __init__(self, message: str = "Connection failed", *, connector: str = "", details: dict | None = None):
        super().__init__(message, connector=connector, details=details)


class TimeoutError(ConnectorError):
    """Raised when a request times out."""

    def __init__(self, message: str = "Request timed out", *, connector: str = "", details: dict | None = None):
        super().__init__(message, connector=connector, details=details)


class RateLimitError(ConnectorError):
    """Raised when rate limit is exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        *,
        connector: str = "",
        retry_after_seconds: float = 60.0,
        details: dict | None = None,
    ):
        super().__init__(message, connector=connector, details=details)
        self.retry_after_seconds = retry_after_seconds


class ValidationError(ConnectorError):
    """Raised when data validation fails."""

    def __init__(self, message: str = "Validation failed", *, connector: str = "", details: dict | None = None):
        super().__init__(message, connector=connector, details=details)


class ConfigurationError(ConnectorError):
    """Raised when connector configuration is invalid."""

    def __init__(self, message: str = "Invalid configuration", *, connector: str = "", details: dict | None = None):
        super().__init__(message, connector=connector, details=details)


class TransformationError(ConnectorError):
    """Raised when data transformation fails."""

    def __init__(self, message: str = "Transformation failed", *, connector: str = "", details: dict | None = None):
        super().__init__(message, connector=connector, details=details)


class WebhookError(ConnectorError):
    """Raised when webhook processing fails."""

    def __init__(self, message: str = "Webhook processing failed", *, connector: str = "", details: dict | None = None):
        super().__init__(message, connector=connector, details=details)
