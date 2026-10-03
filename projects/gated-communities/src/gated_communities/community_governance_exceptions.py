"""Custom exceptions for the community governance application."""

from __future__ import annotations

from typing import Any


class GovernanceError(Exception):
    """Base exception for all governance-related errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        """Initialize the governance exception.

        Args:
            message: Human-readable error message.
            details: Optional additional error details.
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}


class RuleNotFoundError(GovernanceError):
    """Raised when a requested rule cannot be found."""

    def __init__(self, rule_id: str) -> None:
        """Initialize the rule not found exception.

        Args:
            rule_id: The ID of the rule that was not found.
        """
        super().__init__(f"Rule with ID '{rule_id}' not found", {"rule_id": rule_id})
        self.rule_id = rule_id


class DisputeNotFoundError(GovernanceError):
    """Raised when a requested dispute cannot be found."""

    def __init__(self, dispute_id: str) -> None:
        """Initialize the dispute not found exception.

        Args:
            dispute_id: The ID of the dispute that was not found.
        """
        super().__init__(
            f"Dispute with ID '{dispute_id}' not found", {"dispute_id": dispute_id}
        )
        self.dispute_id = dispute_id


class PolicyNotFoundError(GovernanceError):
    """Raised when a requested policy cannot be found."""

    def __init__(self, policy_id: str) -> None:
        """Initialize the policy not found exception.

        Args:
            policy_id: The ID of the policy that was not found.
        """
        super().__init__(
            f"Policy with ID '{policy_id}' not found", {"policy_id": policy_id}
        )
        self.policy_id = policy_id


class RuleValidationError(GovernanceError):
    """Raised when rule validation fails."""

    def __init__(
        self, message: str, field_errors: dict[str, str] | None = None
    ) -> None:
        """Initialize the rule validation exception.

        Args:
            message: Human-readable error message.
            field_errors: Optional field-specific error messages.
        """
        super().__init__(message, {"field_errors": field_errors or {}})
        self.field_errors = field_errors or {}


class DisputeResolutionError(GovernanceError):
    """Raised when dispute resolution fails."""

    def __init__(self, dispute_id: str, reason: str) -> None:
        """Initialize the dispute resolution exception.

        Args:
            dispute_id: The ID of the dispute that failed to resolve.
            reason: The reason for the resolution failure.
        """
        super().__init__(
            f"Failed to resolve dispute '{dispute_id}': {reason}",
            {"dispute_id": dispute_id, "reason": reason},
        )
        self.dispute_id = dispute_id
        self.reason = reason


class PolicyEnforcementError(GovernanceError):
    """Raised when policy enforcement fails."""

    def __init__(self, policy_id: str, action_id: str, reason: str) -> None:
        """Initialize the policy enforcement exception.

        Args:
            policy_id: The ID of the policy that failed to enforce.
            action_id: The ID of the action that triggered the failure.
            reason: The reason for the enforcement failure.
        """
        super().__init__(
            f"Failed to enforce policy '{policy_id}' on action '{action_id}': {reason}",
            {"policy_id": policy_id, "action_id": action_id, "reason": reason},
        )
        self.policy_id = policy_id
        self.action_id = action_id
        self.reason = reason


class AgentExecutionError(GovernanceError):
    """Raised when an agent fails to execute."""

    def __init__(self, agent_name: str, reason: str) -> None:
        """Initialize the agent execution exception.

        Args:
            agent_name: The name of the agent that failed.
            reason: The reason for the execution failure.
        """
        super().__init__(
            f"Agent '{agent_name}' execution failed: {reason}",
            {"agent_name": agent_name, "reason": reason},
        )
        self.agent_name = agent_name
        self.reason = reason


class RateLimitError(GovernanceError):
    """Raised when a rate limit is exceeded."""

    def __init__(self, limit: int, window_seconds: int) -> None:
        """Initialize the rate limit exception.

        Args:
            limit: The maximum number of requests allowed.
            window_seconds: The time window in seconds.
        """
        super().__init__(
            f"Rate limit exceeded: {limit} requests per {window_seconds} seconds",
            {"limit": limit, "window_seconds": window_seconds},
        )
        self.limit = limit
        self.window_seconds = window_seconds
