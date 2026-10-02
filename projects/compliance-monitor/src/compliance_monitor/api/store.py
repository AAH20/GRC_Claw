"""In-memory storage for compliance data."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from compliance_monitor.models.schemas import (
    AuditReport,
    ComplianceScore,
    Policy,
    RemediationAction,
    Violation,
)


class ComplianceStore:
    """Thread-safe in-memory storage for compliance data.

    Stores policies, violations, audit reports, compliance scores,
    and remediation actions in memory. Suitable for development
    and testing; replace with persistent storage for production.
    """

    def __init__(self) -> None:
        """Initialize empty storage."""
        self._policies: dict[UUID, Policy] = {}
        self._violations: dict[UUID, Violation] = {}
        self._audits: dict[UUID, AuditReport] = {}
        self._scores: dict[UUID, ComplianceScore] = {}
        self._remediations: dict[UUID, RemediationAction] = {}

    # Policies
    def create_policy(self, policy: Policy) -> Policy:
        """Store a new policy.

        Args:
            policy: Policy to store.

        Returns:
            Stored policy.
        """
        self._policies[policy.id] = policy
        return policy

    def get_policy(self, policy_id: UUID) -> Policy | None:
        """Get a policy by ID.

        Args:
            policy_id: Policy identifier.

        Returns:
            Policy if found, None otherwise.
        """
        return self._policies.get(policy_id)

    def list_policies(self) -> list[Policy]:
        """List all policies.

        Returns:
            List of all policies.
        """
        return list(self._policies.values())

    def update_policy(self, policy_id: UUID, updates: dict[str, Any]) -> Policy | None:
        """Update a policy.

        Args:
            policy_id: Policy identifier.
            updates: Fields to update.

        Returns:
            Updated policy if found, None otherwise.
        """
        policy = self._policies.get(policy_id)
        if policy:
            for key, value in updates.items():
                if hasattr(policy, key):
                    setattr(policy, key, value)
        return policy

    def delete_policy(self, policy_id: UUID) -> bool:
        """Delete a policy.

        Args:
            policy_id: Policy identifier.

        Returns:
            True if deleted, False if not found.
        """
        return self._policies.pop(policy_id, None) is not None

    # Violations
    def create_violation(self, violation: Violation) -> Violation:
        """Store a new violation.

        Args:
            violation: Violation to store.

        Returns:
            Stored violation.
        """
        self._violations[violation.id] = violation
        return violation

    def get_violation(self, violation_id: UUID) -> Violation | None:
        """Get a violation by ID.

        Args:
            violation_id: Violation identifier.

        Returns:
            Violation if found, None otherwise.
        """
        return self._violations.get(violation_id)

    def list_violations(self) -> list[Violation]:
        """List all violations.

        Returns:
            List of all violations.
        """
        return list(self._violations.values())

    def update_violation(self, violation_id: UUID, updates: dict[str, Any]) -> Violation | None:
        """Update a violation.

        Args:
            violation_id: Violation identifier.
            updates: Fields to update.

        Returns:
            Updated violation if found, None otherwise.
        """
        violation = self._violations.get(violation_id)
        if violation:
            for key, value in updates.items():
                if hasattr(violation, key):
                    setattr(violation, key, value)
        return violation

    # Audit Reports
    def create_audit(self, audit: AuditReport) -> AuditReport:
        """Store a new audit report.

        Args:
            audit: Audit report to store.

        Returns:
            Stored audit report.
        """
        self._audits[audit.id] = audit
        return audit

    def get_audit(self, audit_id: UUID) -> AuditReport | None:
        """Get an audit report by ID.

        Args:
            audit_id: Audit report identifier.

        Returns:
            Audit report if found, None otherwise.
        """
        return self._audits.get(audit_id)

    def list_audits(self) -> list[AuditReport]:
        """List all audit reports.

        Returns:
            List of all audit reports.
        """
        return list(self._audits.values())

    # Compliance Scores
    def create_score(self, score: ComplianceScore) -> ComplianceScore:
        """Store a new compliance score.

        Args:
            score: Compliance score to store.

        Returns:
            Stored compliance score.
        """
        self._scores[score.id] = score
        return score

    def get_score(self, score_id: UUID) -> ComplianceScore | None:
        """Get a compliance score by ID.

        Args:
            score_id: Compliance score identifier.

        Returns:
            Compliance score if found, None otherwise.
        """
        return self._scores.get(score_id)

    def list_scores(self) -> list[ComplianceScore]:
        """List all compliance scores.

        Returns:
            List of all compliance scores.
        """
        return list(self._scores.values())

    # Remediation Actions
    def create_remediation(self, action: RemediationAction) -> RemediationAction:
        """Store a new remediation action.

        Args:
            action: Remediation action to store.

        Returns:
            Stored remediation action.
        """
        self._remediations[action.id] = action
        return action

    def get_remediation(self, action_id: UUID) -> RemediationAction | None:
        """Get a remediation action by ID.

        Args:
            action_id: Remediation action identifier.

        Returns:
            Remediation action if found, None otherwise.
        """
        return self._remediations.get(action_id)

    def list_remediations(self) -> list[RemediationAction]:
        """List all remediation actions.

        Returns:
            List of all remediation actions.
        """
        return list(self._remediations.values())


# Global store instance
store = ComplianceStore()
