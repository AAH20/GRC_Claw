"""
GRC_Claw Policy Lifecycle Management System

Unified policy management providing:
  - Policy definition engine with templates and validation
  - Semantic versioning with rollback and diffing
  - Multi-step approval workflows with delegation and escalation
  - Configurable enforcement rules with pluggable evaluators
  - Portfolio analytics and compliance dashboards

Usage:
    from grcclaw.policies import PolicyManager

    mgr = PolicyManager()
    policy = mgr.create_from_template("tpl-infosec", owner="CISO", approver="CEO")
    mgr.submit_for_approval(policy.id)
    mgr.publish(policy.id)
    mgr.enforce(policy.id, target={"id": "server-01", "type": "server"})
"""

from datetime import datetime, timezone, timedelta
from typing import Optional

from .models import (
    Policy,
    PolicyMetadata,
    PolicySection,
    PolicyTemplate,
    PolicyStatus,
    PolicyCategory,
    PolicyPriority,
    EnforcementMode,
    EnforcementResult,
    PolicyChange,
    PolicyVersion,
    ApprovalRecord,
    ApprovalStep,
    ApprovalStatus,
    Attestation,
    EnforcementRule,
    EnforcementEvent,
    EnforcementFinding,
    PolicyAnalytics,
)
from .engine import PolicyDefinitionEngine, PolicyValidationError
from .versioning import PolicyVersioning, VersionBumpType
from .approval import PolicyApprovalWorkflow, ApprovalWorkflowError
from .enforcement import (
    PolicyEnforcementEngine,
    RuleEvaluator,
    TagCheckEvaluator,
    ConfigScanEvaluator,
    AccessReviewEvaluator,
)
from .analytics import PolicyAnalyticsEngine


class PolicyManager:
    """
    Facade that unifies all policy lifecycle subsystems.

    Provides a single entry point for the complete policy lifecycle:
    definition → versioning → approval → enforcement → analytics.
    """

    def __init__(self) -> None:
        self._engine = PolicyDefinitionEngine()
        self._versioning = PolicyVersioning()
        self._approval = PolicyApprovalWorkflow()
        self._enforcement = PolicyEnforcementEngine()
        self._analytics = PolicyAnalyticsEngine()

    # ── Definition ─────────────────────────────────────────────────────────

    def create_from_template(
        self,
        template_id: str,
        owner: str,
        approver: str,
        overrides: Optional[dict] = None,
    ) -> Policy:
        """Create a policy from a registered template."""
        policy = self._engine.create_from_template(template_id, owner, approver, overrides)
        self._analytics.register_policy(policy)
        return policy

    def create_policy(
        self,
        metadata: PolicyMetadata,
        sections: Optional[list[PolicySection]] = None,
        created_by: str = "",
    ) -> Policy:
        """Create a policy from scratch."""
        policy = self._engine.create_policy(metadata, sections, created_by)
        self._analytics.register_policy(policy)
        return policy

    def get_policy(self, policy_id: str) -> Optional[Policy]:
        """Retrieve a policy by ID."""
        return self._engine.get_policy(policy_id)

    def update_policy(
        self,
        policy_id: str,
        updates: dict,
        updated_by: str = "",
    ) -> Optional[Policy]:
        """Update a policy."""
        return self._engine.update_policy(policy_id, updates, updated_by)

    def delete_policy(self, policy_id: str) -> bool:
        """Delete a policy."""
        return self._engine.delete_policy(policy_id)

    def list_policies(
        self,
        status: Optional[PolicyStatus] = None,
        category: Optional[PolicyCategory] = None,
        framework: Optional[str] = None,
        owner: Optional[str] = None,
    ) -> list[Policy]:
        """List policies with optional filtering."""
        return self._engine.list_policies(status, category, framework, owner)

    def validate_policy(self, policy: Policy) -> list[str]:
        """Validate a policy definition."""
        return self._engine.validate_policy(policy)

    def register_template(self, template: PolicyTemplate) -> PolicyTemplate:
        """Register a policy template."""
        return self._engine.register_template(template)

    def list_templates(
        self,
        category: Optional[PolicyCategory] = None,
        framework: Optional[str] = None,
    ) -> list[PolicyTemplate]:
        """List available templates."""
        return self._engine.list_templates(category, framework)

    # ── Versioning ─────────────────────────────────────────────────────────

    def create_version(
        self,
        policy: Policy,
        change_summary: str,
        created_by: str,
        bump_type: str = VersionBumpType.MINOR,
    ) -> PolicyVersion:
        """Create a new version of a policy."""
        return self._versioning.create_version(policy, change_summary, created_by, bump_type)

    def get_version(self, policy_id: str, version: str) -> Optional[PolicyVersion]:
        """Get a specific version."""
        return self._versioning.get_version(policy_id, version)

    def list_versions(self, policy_id: str) -> list[PolicyVersion]:
        """List all versions of a policy."""
        return self._versioning.list_versions(policy_id)

    def compare_versions(
        self,
        policy_id: str,
        version_a: str,
        version_b: str,
    ) -> dict:
        """Compare two versions."""
        return self._versioning.compare_versions(policy_id, version_a, version_b)

    def rollback(self, policy: Policy, target_version: str, rolled_back_by: str) -> bool:
        """Roll back to a previous version."""
        return self._versioning.rollback_to_version(policy, target_version, rolled_back_by)

    # ── Approval ───────────────────────────────────────────────────────────

    def submit_for_approval(
        self,
        policy: Policy,
        approvers: list[str],
        required_approvals: Optional[int] = None,
    ) -> ApprovalRecord:
        """Submit a policy for approval."""
        return self._approval.configure_approval_chain(policy, approvers, required_approvals)

    def approve(self, approval_id: str, approver: str, comments: str = "") -> ApprovalStatus:
        """Approve a policy."""
        return self._approval.approve(approval_id, approver, comments)

    def reject(self, approval_id: str, approver: str, reason: str) -> ApprovalStatus:
        """Reject a policy."""
        return self._approval.reject(approval_id, approver, reason)

    def delegate(
        self,
        approval_id: str,
        from_approver: str,
        to_approver: str,
        reason: str = "",
    ) -> ApprovalStatus:
        """Delegate an approval."""
        return self._approval.delegate(approval_id, from_approver, to_approver, reason)

    def escalate(
        self,
        approval_id: str,
        escalated_by: str,
        reason: str,
        escalate_to: Optional[str] = None,
    ) -> ApprovalStatus:
        """Escalate a stalled approval."""
        return self._approval.escalate(approval_id, escalated_by, reason, escalate_to)

    def get_pending_approvals(self, approver: Optional[str] = None) -> list[ApprovalRecord]:
        """Get pending approvals."""
        return self._approval.get_pending_approvals(approver)

    # ── Lifecycle Transitions ──────────────────────────────────────────────

    def publish(self, policy: Policy, published_by: str) -> bool:
        """Publish a policy (make it effective)."""
        if policy.status != PolicyStatus.APPROVED:
            return False

        policy.status = PolicyStatus.PUBLISHED
        policy.metadata.effective_date = datetime.now(timezone.utc).isoformat()
        policy.metadata.review_date = (
            datetime.now(timezone.utc) + timedelta(days=365)
        ).isoformat()
        policy.updated_at = datetime.now(timezone.utc).isoformat()
        policy.updated_by = published_by

        from .models import ChangeType, PolicyChange
        change = PolicyChange(
            change_type=ChangeType.PUBLISHED,
            version_from=policy.metadata.version,
            version_to=policy.metadata.version,
            changed_by=published_by,
            summary="Policy published",
        )
        policy.change_log.append(change)
        return True

    def suspend(self, policy: Policy, suspended_by: str, reason: str = "") -> bool:
        """Suspend a published policy."""
        if policy.status != PolicyStatus.PUBLISHED:
            return False

        policy.status = PolicyStatus.SUSPENDED
        policy.updated_at = datetime.now(timezone.utc).isoformat()
        policy.updated_by = suspended_by

        from .models import ChangeType, PolicyChange
        change = PolicyChange(
            change_type=ChangeType.SUSPENDED,
            version_from=policy.metadata.version,
            version_to=policy.metadata.version,
            changed_by=suspended_by,
            summary=f"Policy suspended: {reason}",
        )
        policy.change_log.append(change)
        return True

    def archive(self, policy: Policy, archived_by: str) -> bool:
        """Archive a policy."""
        policy.status = PolicyStatus.ARCHIVED
        policy.updated_at = datetime.now(timezone.utc).isoformat()
        policy.updated_by = archived_by

        from .models import ChangeType, PolicyChange
        change = PolicyChange(
            change_type=ChangeType.ARCHIVED,
            version_from=policy.metadata.version,
            version_to=policy.metadata.version,
            changed_by=archived_by,
            summary="Policy archived",
        )
        policy.change_log.append(change)
        return True

    def deprecate(self, policy: Policy, deprecated_by: str, replacement_id: Optional[str] = None) -> bool:
        """Deprecate a policy, optionally specifying a replacement."""
        policy.status = PolicyStatus.DEPRECATED
        policy.supersedes = replacement_id
        policy.updated_at = datetime.now(timezone.utc).isoformat()
        policy.updated_by = deprecated_by

        from .models import ChangeType, PolicyChange
        change = PolicyChange(
            change_type=ChangeType.DEPRECATED,
            version_from=policy.metadata.version,
            version_to=policy.metadata.version,
            changed_by=deprecated_by,
            summary=f"Policy deprecated. Replacement: {replacement_id or 'none'}",
        )
        policy.change_log.append(change)
        return True

    # ── Attestation ───────────────────────────────────────────────────────

    def add_attestation(
        self,
        policy_id: str,
        employee_id: str,
        employee_name: str,
        employee_email: str = "",
        department: str = "",
        attestation_method: str = "digital_signature",
    ) -> Optional[Attestation]:
        """Record an employee attestation."""
        policy = self._engine.get_policy(policy_id)
        if not policy:
            return None

        attestation = Attestation(
            policy_id=policy_id,
            version=policy.metadata.version,
            employee_id=employee_id,
            employee_name=employee_name,
            employee_email=employee_email,
            department=department,
            attestation_method=attestation_method,
        )
        policy.attestations.append(attestation)
        return attestation

    def get_attestations(self, policy_id: str) -> list[Attestation]:
        """Get all attestations for a policy."""
        policy = self._engine.get_policy(policy_id)
        return policy.attestations if policy else []

    # ── Enforcement ────────────────────────────────────────────────────────

    def add_enforcement_rule(
        self,
        policy_id: str,
        name: str,
        rule_type: str,
        condition: dict,
        action: Optional[dict] = None,
        severity: PolicyPriority = PolicyPriority.MEDIUM,
        target_scope: Optional[list[str]] = None,
    ) -> Optional[EnforcementRule]:
        """Add an enforcement rule to a policy."""
        policy = self._engine.get_policy(policy_id)
        if not policy:
            return None

        rule = self._enforcement.add_rule(
            policy_id, name, rule_type, condition, action, severity, target_scope
        )
        policy.enforcement_rules.append(rule)
        return rule

    def enforce(
        self,
        policy_id: str,
        target: dict,
        context: Optional[dict] = None,
    ) -> Optional[EnforcementEvent]:
        """Evaluate a policy against a target."""
        policy = self._engine.get_policy(policy_id)
        if not policy:
            return None

        event = self._enforcement.evaluate_policy(policy, target, context)
        self._analytics.register_event(event)
        return event

    def batch_enforce(
        self,
        policy_id: str,
        targets: list[dict],
        context: Optional[dict] = None,
    ) -> list[EnforcementEvent]:
        """Evaluate a policy against multiple targets."""
        policy = self._engine.get_policy(policy_id)
        if not policy:
            return []

        events = self._enforcement.batch_evaluate(policy, targets, context)
        for event in events:
            self._analytics.register_event(event)
        return events

    def get_enforcement_events(self, policy_id: str) -> list[EnforcementEvent]:
        """Get enforcement events for a policy."""
        return self._enforcement.get_events_for_policy(policy_id)

    def get_open_findings(self, policy_id: Optional[str] = None) -> list[dict]:
        """Get open findings."""
        return self._enforcement.get_open_findings(policy_id)

    def register_evaluator(self, rule_type: str, evaluator: RuleEvaluator) -> None:
        """Register a custom rule evaluator."""
        self._enforcement.register_evaluator(rule_type, evaluator)

    # ── Analytics ──────────────────────────────────────────────────────────

    def get_portfolio_analytics(self) -> PolicyAnalytics:
        """Get portfolio-wide analytics."""
        return self._analytics.generate_portfolio_analytics()

    def get_policy_analytics(self, policy_id: str) -> dict:
        """Get analytics for a specific policy."""
        return self._analytics.get_policy_analytics(policy_id)

    def get_compliance_dashboard(self) -> dict:
        """Get executive compliance dashboard."""
        return self._analytics.generate_compliance_dashboard()


# ── Module Exports ───────────────────────────────────────────────────────────

__all__ = [
    # Models
    "Policy",
    "PolicyMetadata",
    "PolicySection",
    "PolicyTemplate",
    "PolicyStatus",
    "PolicyCategory",
    "PolicyPriority",
    "EnforcementMode",
    "EnforcementResult",
    "PolicyChange",
    "PolicyVersion",
    "ApprovalRecord",
    "ApprovalStep",
    "ApprovalStatus",
    "Attestation",
    "EnforcementRule",
    "EnforcementEvent",
    "EnforcementFinding",
    "PolicyAnalytics",
    # Engines
    "PolicyDefinitionEngine",
    "PolicyValidationError",
    "PolicyVersioning",
    "VersionBumpType",
    "PolicyApprovalWorkflow",
    "ApprovalWorkflowError",
    "PolicyEnforcementEngine",
    "RuleEvaluator",
    "TagCheckEvaluator",
    "ConfigScanEvaluator",
    "AccessReviewEvaluator",
    "PolicyAnalyticsEngine",
    # Facade
    "PolicyManager",
]
