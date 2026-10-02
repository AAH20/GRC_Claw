"""Custom exceptions for moderation analytics."""

from __future__ import annotations


class ModerationAnalyticsError(Exception):
    """Base exception for moderation analytics service."""

    def __init__(self, message: str, details: dict | None = None) -> None:
        """Initialize the exception.

        Args:
            message: Error message.
            details: Additional error details.
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}


class AgentExecutionError(ModerationAnalyticsError):
    """Raised when an agent fails to execute."""


class ConfigurationError(ModerationAnalyticsError):
    """Raised when there is a configuration error."""


class ValidationError(ModerationAnalyticsError):
    """Raised when input validation fails."""


class IntegrationError(ModerationAnalyticsError):
    """Raised when an external integration fails."""


class NotFoundError(ModerationAnalyticsError):
    """Raised when a requested resource is not found."""
