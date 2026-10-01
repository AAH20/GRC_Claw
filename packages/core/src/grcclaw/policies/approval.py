"""
Policy Approval Workflow

Multi-step approval chains with delegation, escalation, and conditional
routing based on policy attributes.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Optional

from .models import (
    Policy,
    PolicyStatus,
    ApprovalRecord,
    ApprovalStep,
    ApprovalStatus,
    PolicyCategory,
    PolicyPriority,
    ChangeType,
    PolicyChange,
)


class ApprovalWorkflowError(Exception):
    """Raised when an approval workflow operation fails."""
    pass


class PolicyApprovalWorkflow:
    """Manages policy approval workflows with multi-step chains."""

    def __init__(self) -> None:
        self._approvals: dict[str, ApprovalRecord] = {}
        self._escalation_threshold_hours: float = 48.0
        self._policy_finder = None

    def set_policy_finder(self, finder) -> None:
        """Set a callback to find policies by ID."""
        self._policy_finder = finder

    # ── Approval Chain Configuration ───────────────────────────────────────

    def configure_approval_chain(
        self,
        policy: Policy,
        approvers: list[str],
        required_approvals: Optional[int] = None,
    ) -> ApprovalRecord:
        """Set up a multi-step approval chain for a policy."""
        if not approvers:
            raise ApprovalWorkflowError("At least one approver is required")

        required = required_approvals or len(approvers)

        steps = []
        for i, approver in enumerate(approvers):
            steps.append(ApprovalStep(
                order=i + 1,
                approver=approver,
                status=ApprovalStatus.PENDING,
            ))

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

        # Transition policy to under_review
        self._transition_policy_status(policy, PolicyStatus.UNDER_REVIEW, approvers[0])

        return record

    def configure_conditional_chain(
        self,
        policy: Policy,
        category_approvers: dict[PolicyCategory, list[str]],
        default_approvers: list[str],
        priority_approvers: Optional[dict[PolicyPriority, list[str]]] = None,
    ) -> ApprovalRecord:
        """Configure approval chain based on policy category and priority."""
        approvers = category_approvers.get(policy.metadata.category, default_approvers)

        # For critical policies, add priority-specific approvers
        if priority_approvers and policy.metadata.priority == PolicyPriority.CRITICAL:
            extra = priority_approvers.get(PolicyPriority.CRITICAL, [])
            approvers = approvers + [a for a in extra if a not in approvers]

        return self.configure_approval_chain(policy, approvers)

    # ── Approval Actions ───────────────────────────────────────────────────

    def approve(
        self,
        approval_id: str,
        approver: str,
        comments: str = "",
    ) -> ApprovalStatus:
        """Record an approval decision."""
        record = self._approvals.get(approval_id)
        if not record:
            raise ApprovalWorkflowError(f"Approval '{approval_id}' not found")

        if record.status != ApprovalStatus.PENDING:
            raise ApprovalWorkflowError(f"Approval already {record.status.value}")

        # Find the current pending step
        current_step = None
        for step in record.approval_chain:
            if step.status == ApprovalStatus.PENDING:
                current_step = step
                break

        if not current_step:
            raise ApprovalWorkflowError("No pending approval step found")

        if current_step.approver != approver:
            raise ApprovalWorkflowError(f"Expected approver '{current_step.approver}', got '{approver}'")

        current_step.status = ApprovalStatus.APPROVED
        current_step.decided_at = datetime.now(timezone.utc).isoformat()
        current_step.comments = comments

        # Check if all required approvals are complete
        approved_count = sum(1 for s in record.approval_chain if s.status == ApprovalStatus.APPROVED)
        required = len(record.required_approvers)

        if approved_count >= required:
            record.status = ApprovalStatus.APPROVED
            record.decided_at = datetime.now(timezone.utc).isoformat()
            record.comments = comments

            # Update policy status
            policy = self._find_policy(record.policy_id)
            if policy:
                self._transition_policy_status(policy, PolicyStatus.APPROVED, approver)

        return record.status

    def reject(
        self,
        approval_id: str,
        approver: str,
        reason: str,
    ) -> ApprovalStatus:
        """Reject a policy approval."""
        record = self._approvals.get(approval_id)
        if not record:
            raise ApprovalWorkflowError(f"Approval '{approval_id}' not found")

        if record.status != ApprovalStatus.PENDING:
            raise ApprovalWorkflowError(f"Approval already {record.status.value}")

        # Mark current step as rejected
        for step in record.approval_chain:
            if step.status == ApprovalStatus.PENDING:
                step.status = ApprovalStatus.REJECTED
                step.decided_at = datetime.now(timezone.utc).isoformat()
                step.comments = reason
                break

        record.status = ApprovalStatus.REJECTED
        record.decided_at = datetime.now(timezone.utc).isoformat()
        record.comments = reason

        # Return policy to draft
        policy = self._find_policy(record.policy_id)
        if policy:
            self._transition_policy_status(policy, PolicyStatus.DRAFT, approver)

        return record.status

    def delegate(
        self,
        approval_id: str,
        from_approver: str,
        to_approver: str,
        reason: str = "",
    ) -> ApprovalStatus:
        """Delegate an approval to another person."""
        record = self._approvals.get(approval_id)
        if not record:
            raise ApprovalWorkflowError(f"Approval '{approval_id}' not found")

        if record.status != ApprovalStatus.PENDING:
            raise ApprovalWorkflowError(f"Approval already {record.status.value}")

        # Verify the delegating approver is the current approver
        current_step = None
        for step in record.approval_chain:
            if step.status == ApprovalStatus.PENDING:
                current_step = step
                break

        if not current_step or current_step.approver != from_approver:
            raise ApprovalWorkflowError("Only the current approver can delegate")

        current_step.approver = to_approver
        record.delegated_to = to_approver
        record.status = ApprovalStatus.DELEGATED

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

        if escalate_to:
            # Add an escalation step
            new_step = ApprovalStep(
                order=len(record.approval_chain) + 1,
                approver=escalate_to,
                status=ApprovalStatus.PENDING,
            )
            record.approval_chain.append(new_step)
            record.required_approvers.append(escalate_to)

        return record.status

    # ── Workflow Queries ───────────────────────────────────────────────────

    def get_approval(self, approval_id: str) -> Optional[ApprovalRecord]:
        """Retrieve an approval record."""
        return self._approvals.get(approval_id)

    def get_pending_approvals(self, approver: Optional[str] = None) -> list[ApprovalRecord]:
        """List pending approvals, optionally filtered by approver."""
        records = [r for r in self._approvals.values() if r.status == ApprovalStatus.PENDING]
        if approver:
            records = [r for r in records if r.approver == approver or r.delegated_to == approver]
        return records

    def get_approval_history(self, policy_id: str) -> list[ApprovalRecord]:
        """Get all approval records for a policy."""
        return [r for r in self._approvals.values() if r.policy_id == policy_id]

    def check_escalation_needed(self, approval_id: str) -> bool:
        """Check if an approval has exceeded the escalation threshold."""
        record = self._approvals.get(approval_id)
        if not record or record.status != ApprovalStatus.PENDING:
            return False

        requested = datetime.fromisoformat(record.requested_at.replace("Z", "+00:00"))
        elapsed = datetime.now(timezone.utc) - requested
        return elapsed > timedelta(hours=self._escalation_threshold_hours)

    def set_escalation_threshold(self, hours: float) -> None:
        """Configure the escalation threshold in hours."""
        self._escalation_threshold_hours = hours

    # ── Auto-Approval Rules ────────────────────────────────────────────────

    def setup_auto_approval(
        self,
        policy: Policy,
        conditions: dict[str, Any],
        auto_approver: str,
    ) -> None:
        """Configure auto-approval for policies matching conditions."""
        # This would integrate with a rules engine
        # For now, store as metadata on the policy
        if not hasattr(policy, "_auto_approval_rules"):
            policy._auto_approval_rules = []
        policy._auto_approval_rules.append({
            "conditions": conditions,
            "auto_approver": auto_approver,
        })

    def check_auto_approval(self, policy: Policy) -> Optional[str]:
        """Check if a policy qualifies for auto-approval."""
        rules = getattr(policy, "_auto_approval_rules", [])
        for rule in rules:
            if self._matches_conditions(policy, rule["conditions"]):
                return rule["auto_approver"]
        return None

    # ── Internal Helpers ───────────────────────────────────────────────────

    def _transition_policy_status(
        self,
        policy: Policy,
        new_status: PolicyStatus,
        changed_by: str,
    ) -> None:
        """Transition a policy to a new status."""
        old_status = policy.status
        policy.status = new_status
        policy.updated_at = datetime.now(timezone.utc).isoformat()
        policy.updated_by = changed_by

        change = PolicyChange(
            change_type=ChangeType.UPDATED,
            version_from=policy.metadata.version,
            version_to=policy.metadata.version,
            changed_by=changed_by,
            summary=f"Status changed from {old_status.value} to {new_status.value}",
        )
        policy.change_log.append(change)

    def _find_policy(self, policy_id: str) -> Optional[Policy]:
        """Find a policy by ID — requires external registry."""
        # This is a placeholder; in production, this would use a shared registry
        return None

    def _matches_conditions(self, policy: Policy, conditions: dict[str, Any]) -> bool:
        """Check if a policy matches auto-approval conditions."""
        for key, value in conditions.items():
            if key == "category" and policy.metadata.category.value != value:
                return False
            if key == "priority" and policy.metadata.priority.value != value:
                return False
            if key == "framework" and policy.metadata.framework != value:
                return False
        return True
