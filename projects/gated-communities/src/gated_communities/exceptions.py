"""Custom exceptions for the tier management service."""

from __future__ import annotations

from typing import Any


class TierManagementError(Exception):
    """Base exception for all tier management errors."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the tier management error.

        Args:
            message: Human-readable error message.
            status_code: HTTP status code to return.
            details: Additional error details.
        """
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}


class TierNotFoundError(TierManagementError):
    """Raised when a requested tier is not found."""

    def __init__(self, tier_id: str) -> None:
        """Initialize with the missing tier ID.

        Args:
            tier_id: The tier identifier that was not found.
        """
        super().__init__(
            message=f"Tier '{tier_id}' not found",
            status_code=404,
            details={"tier_id": tier_id},
        )


class MemberNotFoundError(TierManagementError):
    """Raised when a requested member is not found."""

    def __init__(self, member_id: str) -> None:
        """Initialize with the missing member ID.

        Args:
            member_id: The member identifier that was not found.
        """
        super().__init__(
            message=f"Member '{member_id}' not found",
            status_code=404,
            details={"member_id": member_id},
        )


class EvaluationError(TierManagementError):
    """Raised when tier evaluation fails."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        """Initialize with error details.

        Args:
            message: Error description.
            details: Additional context about the failure.
        """
        super().__init__(
            message=message,
            status_code=422,
            details=details,
        )


class AccessDeniedError(TierManagementError):
    """Raised when access is denied by policy."""

    def __init__(
        self,
        member_id: str,
        resource: str,
        reason: str | None = None,
    ) -> None:
        """Initialize with access denial context.

        Args:
            member_id: The member denied access.
            resource: The resource that was denied.
            reason: Optional explanation for the denial.
        """
        super().__init__(
            message=f"Access denied for member '{member_id}' to '{resource}'",
            status_code=403,
            details={"member_id": member_id, "resource": resource, "reason": reason},
        )


class UpgradeNotEligibleError(TierManagementError):
    """Raised when a member is not eligible for an upgrade."""

    def __init__(
        self,
        member_id: str,
        target_tier_id: str,
        reason: str,
    ) -> None:
        """Initialize with ineligibility context.

        Args:
            member_id: The member requesting upgrade.
            target_tier_id: The tier they wanted to upgrade to.
            reason: Why the upgrade was denied.
        """
        super().__init__(
            message=(
                f"Member '{member_id}' is not eligible for upgrade to "
                f"'{target_tier_id}': {reason}"
            ),
            status_code=400,
            details={
                "member_id": member_id,
                "target_tier_id": target_tier_id,
                "reason": reason,
            },
        )


class BenefitNotFoundError(TierManagementError):
    """Raised when a requested benefit is not found."""

    def __init__(self, benefit_id: str) -> None:
        """Initialize with the missing benefit ID.

        Args:
            benefit_id: The benefit identifier that was not found.
        """
        super().__init__(
            message=f"Benefit '{benefit_id}' not found",
            status_code=404,
            details={"benefit_id": benefit_id},
        )


class PolicyNotFoundError(TierManagementError):
    """Raised when a requested access policy is not found."""

    def __init__(self, policy_id: str) -> None:
        """Initialize with the missing policy ID.

        Args:
            policy_id: The policy identifier that was not found.
        """
        super().__init__(
            message=f"Access policy '{policy_id}' not found",
            status_code=404,
            details={"policy_id": policy_id},
        )


class AgentExecutionError(TierManagementError):
    """Raised when an agent fails to execute."""

    def __init__(
        self,
        agent_name: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize with agent failure context.

        Args:
            agent_name: Name of the agent that failed.
            message: Error description.
            details: Additional context.
        """
        super().__init__(
            message=f"Agent '{agent_name}' failed: {message}",
            status_code=500,
            details={"agent_name": agent_name, **(details or {})},
        )
