"""Custom exceptions for the Onboarding & Training platform."""

from __future__ import annotations


class OnboardingError(Exception):
    """Base exception for all platform errors."""


class AgentError(OnboardingError):
    """Raised when an agent fails to complete its task."""

    def __init__(self, agent_name: str, message: str) -> None:
        self.agent_name = agent_name
        super().__init__(f"[{agent_name}] {message}")


class LmsIntegrationError(OnboardingError):
    """Raised when an LMS API call fails."""

    def __init__(self,
        provider: str, message: str, status_code: int | None = None) -> None:
        self.provider = provider
        self.status_code = status_code
        super().__init__(f"[{provider}] {message}")


class ValidationError(OnboardingError):
    """Raised when input validation fails."""


class NotFoundError(OnboardingError):
    """Raised when a requested resource does not exist."""


class ConfigurationError(OnboardingError):
    """Raised when the application is misconfigured."""
