"""
Policy Enforcement Engine for GRC_Claw.

Provides configurable enforcement rules with pluggable evaluators,
batch enforcement, and finding management.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from datetime import UTC, datetime

from .models import (
    EnforcementEvent,
    EnforcementFinding,
    EnforcementMode,
    EnforcementResult,
    EnforcementRule,
    Policy,
    PolicyPriority,
)

logger = logging.getLogger(__name__)


class RuleEvaluator(ABC):
    """Abstract base class for rule evaluators."""

    @abstractmethod
    def evaluate(self, rule: EnforcementRule, target: dict, context: dict | None = None) -> EnforcementEvent:
        """Evaluate a rule against a target."""
        pass


class TagCheckEvaluator(RuleEvaluator):
    """Evaluates tag-based compliance rules."""

    def evaluate(self, rule: EnforcementRule, target: dict, context: dict | None = None) -> EnforcementEvent:
        condition = rule.condition
        required_tags = condition.get("required_tags", [])
        target_tags = target.get("tags", [])

        missing_tags = [t for t in required_tags if t not in target_tags]
        findings: list[EnforcementFinding] = []

        if missing_tags:
            findings.append(EnforcementFinding(
                severity=rule.severity,
                title=f"Missing required tags: {', '.join(missing_tags)}",
                description=f"Target {target.get('id', 'unknown')} is missing required tags",
                evidence=f"Required: {required_tags}, Found: {target_tags}",
                remediation=f"Add missing tags: {', '.join(missing_tags)}",
            ))

        result = EnforcementResult.PASS if not findings else EnforcementResult.FAIL
        return EnforcementEvent(
            policy_id=rule.policy_id,
            rule_id=rule.id,
            target_id=target.get("id", ""),
            target_type=target.get("type", "unknown"),
            result=result,
            findings=findings,
            remediation="; ".join(f.remediation for f in findings) if findings else "",
        )


class ConfigScanEvaluator(RuleEvaluator):
    """Evaluates configuration-based compliance rules."""

    def evaluate(self, rule: EnforcementRule, target: dict, context: dict | None = None) -> EnforcementEvent:
        condition = rule.condition
        config_key = condition.get("config_key", "")
        expected_value = condition.get("expected_value")
        operator = condition.get("operator", "equals")

        target_config = target.get("config", {})
        actual_value = target_config.get(config_key)

        findings: list[EnforcementFinding] = []
        passed = self._compare(actual_value, expected_value, operator)

        if not passed:
            findings.append(EnforcementFinding(
                severity=rule.severity,
                title=f"Configuration mismatch: {config_key}",
                description=f"Expected {config_key} {operator} {expected_value}, got {actual_value}",
                evidence=f"Config key: {config_key}, Actual: {actual_value}",
                remediation=f"Set {config_key} to {expected_value}",
            ))

        result = EnforcementResult.PASS if not findings else EnforcementResult.FAIL
        return EnforcementEvent(
            policy_id=rule.policy_id,
            rule_id=rule.id,
            target_id=target.get("id", ""),
            target_type=target.get("type", "unknown"),
            result=result,
            findings=findings,
            remediation="; ".join(f.remediation for f in findings) if findings else "",
        )

    def _compare(self, actual, expected, operator: str) -> bool:
        """Compare values based on operator."""
        if operator == "equals":
            return actual == expected
        elif operator == "not_equals":
            return actual != expected
        elif operator == "contains":
            return expected in actual if actual else False
        elif operator == "greater_than":
            return actual > expected if actual is not None else False
        elif operator == "less_than":
            return actual < expected if actual is not None else False
        elif operator == "exists":
            return actual is not None
        return False


class AccessReviewEvaluator(RuleEvaluator):
    """Evaluates access review compliance rules."""

    def evaluate(self, rule: EnforcementRule, target: dict, context: dict | None = None) -> EnforcementEvent:
        condition = rule.condition
        max_access_age_days = condition.get("max_access_age_days", 90)
        required_review = condition.get("required_review", True)

        target_access = target.get("access", {})
        last_review = target_access.get("last_review_date")
        has_access = target_access.get("has_access", False)

        findings: list[EnforcementFinding] = []

        if has_access and required_review:
            if not last_review:
                findings.append(EnforcementFinding(
                    severity=rule.severity,
                    title="Access review missing",
                    description=f"Target {target.get('id', 'unknown')} has access but no review date",
                    evidence="No last_review_date found",
                    remediation="Conduct access review immediately",
                ))
            else:
                try:
                    review_date = datetime.fromisoformat(last_review)
                    age_days = (datetime.now(UTC) - review_date).days
                    if age_days > max_access_age_days:
                        findings.append(EnforcementFinding(
                            severity=rule.severity,
                            title=f"Access review overdue ({age_days} days)",
                            description=f"Last review was {age_days} days ago (max: {max_access_age_days})",
                            evidence=f"Last review: {last_review}",
                            remediation="Schedule access review",
                        ))
                except ValueError:
                    findings.append(EnforcementFinding(
                        severity=rule.severity,
                        title="Invalid review date format",
                        description=f"Cannot parse last_review_date: {last_review}",
                        evidence=f"Value: {last_review}",
                        remediation="Fix date format to ISO 8601",
                    ))

        result = EnforcementResult.PASS if not findings else EnforcementResult.FAIL
        return EnforcementEvent(
            policy_id=rule.policy_id,
            rule_id=rule.id,
            target_id=target.get("id", ""),
            target_type=target.get("type", "unknown"),
            result=result,
            findings=findings,
            remediation="; ".join(f.remediation for f in findings) if findings else "",
        )


class PolicyEnforcementEngine:
    """Core enforcement engine."""

    def __init__(self) -> None:
        self._evaluators: dict[str, RuleEvaluator] = {}
        self._events: dict[str, list[EnforcementEvent]] = {}
        self._register_default_evaluators()

    def _register_default_evaluators(self) -> None:
        """Register built-in evaluators."""
        self._evaluators["tag_check"] = TagCheckEvaluator()
        self._evaluators["config_scan"] = ConfigScanEvaluator()
        self._evaluators["access_review"] = AccessReviewEvaluator()

    def register_evaluator(self, rule_type: str, evaluator: RuleEvaluator) -> None:
        """Register a custom rule evaluator."""
        self._evaluators[rule_type] = evaluator

    def add_rule(
        self,
        policy_id: str,
        name: str,
        rule_type: str,
        condition: dict,
        action: dict | None = None,
        severity: PolicyPriority = PolicyPriority.MEDIUM,
        target_scope: list[str] | None = None,
    ) -> EnforcementRule:
        """Add an enforcement rule."""
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

    def evaluate_policy(
        self,
        policy: Policy,
        target: dict,
        context: dict | None = None,
    ) -> EnforcementEvent:
        """Evaluate all rules in a policy against a target."""
        if policy.enforcement_mode == EnforcementMode.DISABLED:
            return EnforcementEvent(
                policy_id=policy.id,
                rule_id="",
                target_id=target.get("id", ""),
                target_type=target.get("type", "unknown"),
                result=EnforcementResult.NOT_APPLICABLE,
                findings=[],
                remediation="",
            )

        all_findings: list[EnforcementFinding] = []
        overall_result = EnforcementResult.PASS

        for rule in policy.enforcement_rules:
            if not rule.enabled:
                continue
            if rule.target_scope and target.get("type", "") not in rule.target_scope:
                continue

            evaluator = self._evaluators.get(rule.rule_type)
            if not evaluator:
                logger.warning(f"No evaluator for rule type '{rule.rule_type}'")
                continue

            event = evaluator.evaluate(rule, target, context)
            all_findings.extend(event.findings)

            if event.result == EnforcementResult.FAIL:
                overall_result = EnforcementResult.FAIL
            elif event.result == EnforcementResult.WARNING and overall_result == EnforcementResult.PASS:
                overall_result = EnforcementResult.WARNING

        # Aggregate event
        event = EnforcementEvent(
            policy_id=policy.id,
            rule_id="",
            target_id=target.get("id", ""),
            target_type=target.get("type", "unknown"),
            result=overall_result,
            findings=all_findings,
            remediation="; ".join(f.remediation for f in all_findings) if all_findings else "",
        )

        if policy.id not in self._events:
            self._events[policy.id] = []
        self._events[policy.id].append(event)

        return event

    def batch_evaluate(
        self,
        policy: Policy,
        targets: list[dict],
        context: dict | None = None,
    ) -> list[EnforcementEvent]:
        """Evaluate a policy against multiple targets."""
        return [self.evaluate_policy(policy, target, context) for target in targets]

    def get_events_for_policy(self, policy_id: str) -> list[EnforcementEvent]:
        """Get all enforcement events for a policy."""
        return self._events.get(policy_id, [])

    def get_open_findings(self, policy_id: str | None = None) -> list[dict]:
        """Get all open findings, optionally filtered by policy."""
        findings: list[dict] = []
        events = self._events.get(policy_id, []) if policy_id else [e for events in self._events.values() for e in events]
        for event in events:
            for finding in event.findings:
                if finding.status == "open":
                    findings.append({
                        "id": finding.id,
                        "policy_id": event.policy_id,
                        "target_id": event.target_id,
                        "severity": finding.severity.value,
                        "title": finding.title,
                        "description": finding.description,
                        "remediation": finding.remediation,
                        "status": finding.status,
                    })
        return findings
