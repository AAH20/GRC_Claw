"""Custom exceptions for Campaign Optimizer."""

from __future__ import annotations


class CampaignOptimizerError(Exception):
    """Base exception for all Campaign Optimizer errors."""

    def __init__(self, message: str, details: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class AgentError(CampaignOptimizerError):
    """Raised when an agent encounters an error."""


class AgentTimeoutError(AgentError):
    """Raised when an agent exceeds its execution timeout."""


class AgentMaxIterationsError(AgentError):
    """Raised when an agent exceeds its maximum iteration count."""


class GovernanceError(CampaignOptimizerError):
    """Raised when a governance policy is violated."""


class GovernanceApprovalRequired(GovernanceError):
    """Raised when an action requires governance approval."""


class CampaignNotFoundError(CampaignOptimizerError):
    """Raised when a campaign is not found."""


class CampaignValidationError(CampaignOptimizerError):
    """Raised when campaign data fails validation."""


class ConfigurationError(CampaignOptimizerError):
    """Raised when there is a configuration error."""


class LLMError(CampaignOptimizerError):
    """Raised when an LLM call fails."""


class LLMTimeoutError(LLMError):
    """Raised when an LLM call times out."""


class LLMQuotaError(LLMError):
    """Raised when LLM quota is exceeded."""


class DatabaseError(CampaignOptimizerError):
    """Raised when a database operation fails."""


class CacheError(CampaignOptimizerError):
    """Raised when a cache operation fails."""
