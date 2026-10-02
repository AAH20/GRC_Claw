"""
Policy Approval Workflow for GRC_Claw.

Provides multi-step approval chains with delegation, escalation, and tracking.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

from .models import (
    Policy,
    ApprovalRecord,
    ApprovalStep,
    ApprovalStatus,
    PolicyStatus,
    PolicyChange,
    ChangeType,
)

logger = logging.getLogger(__name__)


class ApprovalWorkflowError(Exception):
    """Raised when an approval workflow operation fails."""
    pass


class PolicyApprovalWorkflow:
    """Manages policy approval workflows."""

    def __init__(self) -> None:
        self._approvals: dict[str, ApprovalRecord] = {}

    def configure_approval_chain(
        self,
        policy: Policy,
        approvers: list[str],
        required_approvals: Optional[int] = None,
    ) -> ApprovalRecord:
        """Configure an approval chain for a policy."""
        if not approvers:
            raise ApprovalWorkflowError("At least one approver is required")

        steps = [
            ApprovalStep(
                order=i + 1,
                approver=approver,
                status=ApprovalStatus.PENDING,
            )
            for i, approver in enumerate(approvers)
        ]

        record = ApprovalRecord(
            policy_id=policy.id,
            version=policy.metadata.version,
            status=ApprovalStatus.PENDING,
            approver=approvers[0],
            required_approvers=approvers,
            approval_chain=steps,
        )

        self._approvals[record.id] = record
        policy.approvals.append(record)
        policy.status = PolicyStatus.UNDER_REVIEW

        change = PolicyChange(
            change_type=ChangeType.UPDATED,
            version_from=policy.metadata.version,
            version_to=policy.metadata.version,
            changed_by=policy.metadata.owner,
            summary=f"Policy submitted for approval with {len(approvers)} approver(s)",
        )
        policy.change_log.append(change)

        return record

    def approve(
        self,
        approval_id: str,
        approver: str,
        comments: str = "",
    ) -> ApprovalStatus:
        """Approve a policy."""
        record = self._approvals.get(approval_id)
        if not record:
            raise ApprovalWorkflowError(f"Approval '{approval_id}' not found")

        if record.status != ApprovalStatus.PENDING:
            raise ApprovalWorkflowError(f"Approval is not pending (current: {record.status.value})")

        # Find the current pending step for this approver
        current_step = None
        for step in record.approval_chain:
            if step.status == ApprovalStatus.PENDING and step.approver == approver:
                current_step = step
                break

        if not current_step:
            raise ApprovalWorkflowError(f"No pending step found for approver '{approver}'")

        current_step.status = ApprovalStatus.APPROVED
        current_step.comments = comments
        current_step.decided_at = datetime.now(timezone.utc).isoformat()

        # Check if all steps are approved
        all_approved = all(s.status == ApprovalStatus.APPROVED for s in record.approval_chain)
        if all_approved:
            record.status = ApprovalStatus.APPROVED
            record.decided_at = datetime.now(timezone.utc).isoformat()

            # Update policy status
            policy = self._find_policy(record.policy_id)
            if policy:
                policy.status = PolicyStatus.APPROVED
                policy.updated_at = datetime.now(timezone.utc).isoformat()
                change = PolicyChange(
                    change_type=ChangeType.UPDATED,
                    version_from=policy.metadata.version,
                    version_to=policy.metadata.version,
                    changed_by=approver,
                    summary="Policy approved",
                )
                policy.change_log.append(change)

        return record.status

    def reject(
        self,
        approval_id: str,
        approver: str,
        reason: str,
    ) -> ApprovalStatus:
        """Reject a policy."""
        record = self._approvals.get(approval_id)
        if not record:
            raise ApprovalWorkflowError(f"Approval '{approval_id}' not found")

        if record.status != ApprovalStatus.PENDING:
            raise ApprovalWorkflowError(f"Approval is not pending (current: {record.status.value})")

        # Find the current pending step for this approver
        current_step = None
        for step in record.approval_chain:
            if step.status == ApprovalStatus.PENDING and step.approver == approver:
                current_step = step
                break

        if not current_step:
            raise ApprovalWorkflowError(f"No pending step found for approver '{approver}'")

        current_step.status = ApprovalStatus.REJECTED
        current_step.comments = reason
        current_step.decided_at = datetime.now(timezone.utc).isoformat()

        record.status = ApprovalStatus.REJECTED
        record.decided_at = datetime.now(timezone.utc).isoformat()
        record.comments = reason

        # Update policy status
        policy = self._find_policy(record.policy_id)
        if policy:
            policy.status = PolicyStatus.DRAFT
            policy.updated_at = datetime.now(timezone.utc).isoformat()
            change = PolicyChange(
                change_type=ChangeType.UPDATED,
                version_from=policy.metadata.version,
                version_to=policy.metadata.version,
                changed_by=approver,
                summary=f"Policy rejected: {reason}",
            )
            policy.change_log.append(change)

        return record.status

    def delegate(
        self,
        approval_id: str,
        from_approver: str,
        to_approver: str,
        reason: str = "",
    ) -> ApprovalStatus:
        """Delegate an approval to another approver."""
        record = self._approvals.get(approval_id)
        if not record:
            raise ApprovalWorkflowError(f"Approval '{approval_id}' not found")

        # Find the current pending step
        current_step = None
        for step in record.approval_chain:
            if step.status == ApprovalStatus.PENDING and step.approver == from_approver:
                current_step = step
                break

        if not current_step:
            raise ApprovalWorkflowError(f"No pending step found for approver '{from_approver}'")

        current_step.approver = to_approver
        current_step.comments = f"Delegated from {from_approver}: {reason}"
        record.delegated_to = to_approver

        return record.status

    def escalate(
        self,
        approval_id: str,
        escalated_by: str,
        reason: str,
        escalate_to: Optional[str] = None,
    ) -> ApprovalStatus:
        """Escalate a stalled approval."""
        record = self._approvals.get(approval_id)
        if not record:
            raise ApprovalWorkflowError(f"Approval '{approval_id}' not found")

        record.status = ApprovalStatus.ESCALATED
        record.escalation_reason = reason

        # Add escalation step
        escalation_step = ApprovalStep(
            order=len(record.approval_chain) + 1,
            approver=escalate_to or record.approver,
            status=ApprovalStatus.PENDING,
            comments=f"Escalated by {escalated_by}: {reason}",
        )
        record.approval_chain.append(escalation_step)

        return record.status

    def get_pending_approvals(self, approver: Optional[str] = None) -> list[ApprovalRecord]:
        """Get pending approvals, optionally filtered by approver."""
        records = [r for r in self._approvals.values() if r.status == ApprovalStatus.PENDING]
        if approver:
            records = [
                r for r in records
                if any(s.approver == approver and s.status == ApprovalStatus.PENDING for s in r.approval_chain)
            ]
        return records

    def get_approval(self, approval_id: str) -> Optional[ApprovalRecord]:
        """Get an approval record by ID."""
        return self._approvals.get(approval_id)

    def _find_policy(self, policy_id: str) -> Optional[Policy]:
        """Find a policy by ID (uses the engine's storage)."""
        # This is a simplified lookup - in production, this would use a shared registry
        from .engine import PolicyDefinitionEngine
        # The engine instance is managed by PolicyManager, so we use a module-level cache
        return _POLICY_CACHE.get(policy_id)


# Module-level policy cache for cross-module lookups
_POLICY_CACHE: dict[str, Policy] = {}


def register_policy(policy: Policy) -> None:
    """Register a policy in the module-level cache."""
    _POLICY_CACHE[policy.id] = policy


def unregister_policy(policy_id: str) -> None:
    """Remove a policy from the module-level cache."""
    _POLICY_CACHE.pop(policy_id, None)
