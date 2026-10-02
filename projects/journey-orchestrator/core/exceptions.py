"""Custom exceptions for the Journey Orchestrator."""

from __future__ import annotations


class JourneyOrchestratorError(Exception):
    """Base exception for all Journey Orchestrator errors."""

    def __init__(self, message: str, *, code: str | None = None, details: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}


class AgentError(JourneyOrchestratorError):
    """Raised when an agent encounters an error."""


class AgentTimeoutError(AgentError):
    """Raised when an agent operation times out."""


class AgentConfigurationError(AgentError):
    """Raised when an agent is misconfigured."""


class JourneyNotFoundError(JourneyOrchestratorError):
    """Raised when a requested journey does not exist."""


class JourneyValidationError(JourneyOrchestratorError):
    """Raised when journey data fails validation."""


class JourneyExecutionError(JourneyOrchestratorError):
    """Raised when journey execution fails."""


class ChannelError(JourneyOrchestratorError):
    """Raised when a channel operation fails."""


class ChannelConfigurationError(ChannelError):
    """Raised when a channel is misconfigured."""


class ExperimentError(JourneyOrchestratorError):
    """Raised when an experiment operation fails."""


class PersonalizationError(JourneyOrchestratorError):
    """Raised when personalization fails."""


class TimingOptimizationError(JourneyOrchestratorError):
    """Raised when timing optimization fails."""


class CriticError(JourneyOrchestratorError):
    """Raised when the critic agent encounters an error."""


class GovernanceError(JourneyOrchestratorError):
    """Raised when a governance policy is violated."""


class RateLimitError(JourneyOrchestratorError):
    """Raised when a rate limit is exceeded."""


class AuthenticationError(JourneyOrchestratorError):
    """Raised when authentication fails."""


class AuthorizationError(JourneyOrchestratorError):
    """Raised when authorization fails."""
