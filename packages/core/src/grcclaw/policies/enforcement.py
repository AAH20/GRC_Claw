"""
Policy Enforcement

Evaluates enforcement rules against targets, collects findings,
tracks remediation, and generates evidence.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Callable, Optional

from .models import (
    Policy,
    EnforcementRule,
    EnforcementEvent,
    EnforcementFinding,
    EnforcementResult,
    EnforcementMode,
    PolicyPriority,
    PolicyStatus,
)


class PolicyEnforcementError(Exception):
    """Raised when enforcement evaluation fails."""
    pass


class RuleEvaluator:
    """Base class for rule evaluators."""

    def evaluate(
        self,
        rule: EnforcementRule,
        target: dict[str, Any],
        context: Optional[dict[str, Any]] = None,
    ) -> list[EnforcementFinding]:
        """Evaluate a rule against a target. Override in subclasses."""
        return []


class TagCheckEvaluator(RuleEvaluator):
    """Evaluates tag-based compliance rules."""

    def evaluate(
        self,
        rule: EnforcementRule,
        target: dict[str, Any],
        context: Optional[dict[str, Any]] = None,
    ) -> list[EnforcementFinding]:
        findings: list[EnforcementFinding] = []
        condition = rule.condition
        required_tags = condition.get("required_tags", [])
        target_tags = target.get("tags", [])

        missing = [t for t in required_tags if t not in target_tags]
        if missing:
            findings.append(EnforcementFinding(
                severity=rule.severity,
                title=f"Missing required tags: {', '.join(missing)}",
                description=f"Target {target.get('id', 'unknown')} is missing required tags",
                evidence=f"Required: {required_tags}, Found: {target_tags}",
                remediation=f"Add missing tags: {', '.join(missing)}",
            ))

        return findings


class ConfigScanEvaluator(RuleEvaluator):
    """Evaluates configuration compliance rules."""

    def evaluate(
        self,
        rule: EnforcementRule,
        target: dict[str, Any],
        context: Optional[dict[str, Any]] = None,
    ) -> list[EnforcementFinding]:
        findings: list[EnforcementFinding] = []
        condition = rule.condition
        config = target.get("config", {})
        checks = condition.get("checks", [])

        for check in checks:
            path = check.get("path", "")
            expected = check.get("expected")
            actual = self._get_nested_value(config, path)

            if actual != expected:
                findings.append(EnforcementFinding(
                    severity=rule.severity,
                    title=f"Config mismatch at {path}",
                    description=f"Expected '{expected}', found '{actual}'",
                    evidence=f"Config path: {path}, Actual: {actual}",
                    remediation=check.get("remediation", f"Set {path} to {expected}"),
                ))

        return findings

    def _get_nested_value(self, data: dict[str, Any], path: str) -> Any:
        """Get a nested dictionary value by dot-separated path."""
        keys = path.split(".")
        current = data
        for key in keys:
            if isinstance(current, dict):
                current = current.get(key)
            else:
                return None
        return current


class AccessReviewEvaluator(RuleEvaluator):
    """Evaluates access control compliance rules."""

    def evaluate(
        self,
        rule: EnforcementRule,
        target: dict[str, Any],
        context: Optional[dict[str, Any]] = None,
    ) -> list[EnforcementFinding]:
        findings: list[EnforcementFinding] = []
        condition = rule.condition
        max_permissions = condition.get("max_permissions", 10)
        required_approvals = condition.get("required_approvals", [])
        permissions = target.get("permissions", [])

        if len(permissions) > max_permissions:
            findings.append(EnforcementFinding(
                severity=rule.severity,
                title="Excessive permissions",
                description=f"Target has {len(permissions)} permissions (max: {max_permissions})",
                evidence=f"Permissions: {permissions}",
                remediation="Review and reduce permissions to minimum required",
            ))

        for req in required_approvals:
            if req not in permissions:
                findings.append(EnforcementFinding(
                    severity=rule.severity,
                    title=f"Missing required approval: {req}",
                    description=f"Required approval '{req}' not found",
                    evidence=f"Required: {required_approvals}, Found: {permissions}",
                    remediation=f"Add required approval: {req}",
                ))

        return findings


class PolicyEnforcementEngine:
    """Engine for evaluating policy enforcement rules."""

    def __init__(self) -> None:
        self._evaluators: dict[str, RuleEvaluator] = {
            "tag_check": TagCheckEvaluator(),
            "config_scan": ConfigScanEvaluator(),
            "access_review": AccessReviewEvaluator(),
        }
        self._events: dict[str, EnforcementEvent] = {}
        self._custom_evaluators: dict[str, Callable] = {}

    # ── Evaluator Registration ─────────────────────────────────────────────

    def register_evaluator(self, rule_type: str, evaluator: RuleEvaluator) -> None:
        """Register a custom rule evaluator."""
        self._evaluators[rule_type] = evaluator

    def register_custom_evaluator(
        self,
        rule_type: str,
        evaluator_fn: Callable[[EnforcementRule, dict[str, Any], Optional[dict[str, Any]]], list[EnforcementFinding]],
    ) -> None:
        """Register a custom evaluator function."""
        self._custom_evaluators[rule_type] = evaluator_fn

    # ── Rule Management ────────────────────────────────────────────────────

    def add_rule(
        self,
        policy_id: str,
        name: str,
        rule_type: str,
        condition: dict[str, Any],
        action: Optional[dict[str, Any]] = None,
        severity: PolicyPriority = PolicyPriority.MEDIUM,
        target_scope: Optional[list[str]] = None,
    ) -> EnforcementRule:
        """Add an enforcement rule to a policy."""
        rule = EnforcementRule(
            policy_id=policy_id,
            name=name,
            rule_type=rule_type,
            condition=condition,
            action=action or {},
            severity=severity,
            target_scope=target_scope or [],
        )
        return rule

    def remove_rule(self, policy: Policy, rule_id: str) -> bool:
        """Remove an enforcement rule from a policy."""
        original_len = len(policy.enforcement_rules)
        policy.enforcement_rules = [r for r in policy.enforcement_rules if r.id != rule_id]
        return len(policy.enforcement_rules) < original_len

    def enable_rule(self, rule: EnforcementRule) -> None:
        """Enable an enforcement rule."""
        rule.enabled = True

    def disable_rule(self, rule: EnforcementRule) -> None:
        """Disable an enforcement rule."""
        rule.enabled = False

    # ── Enforcement Execution ──────────────────────────────────────────────

    def evaluate_policy(
        self,
        policy: Policy,
        target: dict[str, Any],
        context: Optional[dict[str, Any]] = None,
    ) -> EnforcementEvent:
        """Evaluate all enabled rules in a policy against a target."""
        if policy.enforcement_mode == EnforcementMode.DISABLED:
            return EnforcementEvent(
                policy_id=policy.id,
                target_id=target.get("id", "unknown"),
                target_type=target.get("type", "unknown"),
                result=EnforcementResult.NOT_APPLICABLE,
                findings=[],
                enforced_by="system",
            )

        all_findings: list[EnforcementFinding] = []

        for rule in policy.enforcement_rules:
            if not rule.enabled:
                continue

            if rule.target_scope and target.get("type", "") not in rule.target_scope:
                continue

            findings = self._evaluate_rule(rule, target, context)
            all_findings.extend(findings)

        # Determine overall result
        if not all_findings:
            result = EnforcementResult.PASS
        elif any(f.severity == PolicyPriority.CRITICAL for f in all_findings):
            result = EnforcementResult.FAIL
        elif any(f.severity == PolicyPriority.HIGH for f in all_findings):
            result = EnforcementResult.FAIL
        elif any(f.severity == PolicyPriority.MEDIUM for f in all_findings):
            result = EnforcementResult.WARNING
        else:
            result = EnforcementResult.WARNING

        # Advisory mode downgrades FAIL to WARNING
        if policy.enforcement_mode == EnforcementMode.ADVISORY and result == EnforcementResult.FAIL:
            result = EnforcementResult.WARNING

        event = EnforcementEvent(
            policy_id=policy.id,
            target_id=target.get("id", "unknown"),
            target_type=target.get("type", "unknown"),
            result=result,
            findings=all_findings,
            enforced_by="system",
        )

        self._events[event.id] = event
        return event

    def evaluate_rule(
        self,
        rule: EnforcementRule,
        target: dict[str, Any],
        context: Optional[dict[str, Any]] = None,
    ) -> list[EnforcementFinding]:
        """Evaluate a single rule against a target."""
        return self._evaluate_rule(rule, target, context)

    def batch_evaluate(
        self,
        policy: Policy,
        targets: list[dict[str, Any]],
        context: Optional[dict[str, Any]] = None,
    ) -> list[EnforcementEvent]:
        """Evaluate a policy against multiple targets."""
        return [self.evaluate_policy(policy, target, context) for target in targets]

    # ── Remediation Tracking ───────────────────────────────────────────────

    def acknowledge_finding(
        self,
        event_id: str,
        finding_id: str,
        acknowledged_by: str,
    ) -> bool:
        """Acknowledge a finding without remediation."""
        event = self._events.get(event_id)
        if not event:
            return False

        for finding in event.findings:
            if finding.id == finding_id:
                finding.status = "acknowledged"
                return True
        return False

    def mark_remediated(
        self,
        event_id: str,
        finding_id: str,
        remediated_by: str,
        evidence: str = "",
    ) -> bool:
        """Mark a finding as remediated."""
        event = self._events.get(event_id)
        if not event:
            return False

        for finding in event.findings:
            if finding.id == finding_id:
                finding.status = "remediated"
                if evidence:
                    finding.evidence = evidence
                return True
        return False

    def accept_risk(
        self,
        event_id: str,
        finding_id: str,
        accepted_by: str,
        reason: str = "",
    ) -> bool:
        """Accept a finding as risk."""
        event = self._events.get(event_id)
        if not event:
            return False

        for finding in event.findings:
            if finding.id == finding_id:
                finding.status = "accepted_risk"
                if reason:
                    finding.remediation = reason
                return True
        return False

    # ── Event Queries ──────────────────────────────────────────────────────

    def get_event(self, event_id: str) -> Optional[EnforcementEvent]:
        """Retrieve an enforcement event."""
        return self._events.get(event_id)

    def get_events_for_policy(self, policy_id: str) -> list[EnforcementEvent]:
        """Get all enforcement events for a policy."""
        return [e for e in self._events.values() if e.policy_id == policy_id]

    def get_events_for_target(self, target_id: str) -> list[EnforcementEvent]:
        """Get all enforcement events for a target."""
        return [e for e in self._events.values() if e.target_id == target_id]

    def get_open_findings(self, policy_id: Optional[str] = None) -> list[dict[str, Any]]:
        """Get all open findings, optionally filtered by policy."""
        findings: list[dict[str, Any]] = []
        for event in self._events.values():
            if policy_id and event.policy_id != policy_id:
                continue
            for finding in event.findings:
                if finding.status == "open":
                    findings.append({
                        "event_id": event.id,
                        "policy_id": event.policy_id,
                        "target_id": event.target_id,
                        "finding": finding,
                    })
        return findings

    # ── Internal Helpers ───────────────────────────────────────────────────

    def _evaluate_rule(
        self,
        rule: EnforcementRule,
        target: dict[str, Any],
        context: Optional[dict[str, Any]] = None,
    ) -> list[EnforcementFinding]:
        """Evaluate a single rule using the appropriate evaluator."""
        # Check custom evaluators first
        if rule.rule_type in self._custom_evaluators:
            return self._custom_evaluators[rule.rule_type](rule, target, context)

        # Use registered evaluators
        evaluator = self._evaluators.get(rule.rule_type)
        if evaluator:
            return evaluator.evaluate(rule, target, context)

        # Unknown rule type — return error finding
        return [EnforcementFinding(
            severity=PolicyPriority.HIGH,
            title=f"Unknown rule type: {rule.rule_type}",
            description=f"No evaluator registered for rule type '{rule.rule_type}'",
            remediation="Register an evaluator for this rule type",
        )]
