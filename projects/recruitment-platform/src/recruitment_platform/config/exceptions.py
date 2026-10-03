"""Custom exceptions for the recruitment platform."""

from __future__ import annotations


class RecruitmentPlatformError(Exception):
    """Base exception for all recruitment platform errors."""


class AgentError(RecruitmentPlatformError):
    """Raised when an agent encounters an error."""


class ValidationError(RecruitmentPlatformError):
    """Raised when input validation fails."""


class NotFoundError(RecruitmentPlatformError):
    """Raised when a requested resource is not found."""


class ExternalServiceError(RecruitmentPlatformError):
    """Raised when an external service call fails."""


class ConfigurationError(RecruitmentPlatformError):
    """Raised when there is a configuration error."""
