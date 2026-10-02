"""Policy enforcement agent using LangChain DeepAgents."""

from __future__ import annotations

import re
from typing import Any

from content_moderation.agents.base import BaseModerationAgent
from content_moderation.models.schemas import ContentType, Policy, PolicyRule

POLICY_ENFORCEMENT_PROMPT = """You are a policy enforcement AI.
Given content and a set of policy rules, determine if any rules are violated.

Policy rules in JSON format:
{policy_rules}

Content to check:
{content}

Respond with a JSON object containing:
- action: one of "allow", "flag", "block", "escalate"
- confidence: float between 0.0 and 1.0
- categories: list of violated rule names
- reasons: list of human-readable violation reasons
- policy_violations: list of violated rule IDs
"""


class PolicyEnforcementAgent(BaseModerationAgent):
    """Agent for enforcing content policies against moderation results."""

    @property
    def content_type(self) -> ContentType:
        """Content type this agent handles - applies to all types."""
        return ContentType.TEXT

    async def _analyze(self, content: str, context: dict[str, Any]) -> dict[str, Any]:
        """Check content against policy rules.

        Args:
            content: Content to check against policies.
            context: Must contain 'policies' key with list of Policy objects.

        Returns:
            Analysis result with violations found.
        """
        policies: list[Policy] = context.get("policies", [])
        if not policies:
            return {
                "action": "allow",
                "confidence": 1.0,
                "categories": [],
                "reasons": ["No policies to enforce"],
            }

        all_violations: list[dict[str, Any]] = []
        for policy in policies:
            if not policy.enabled:
                continue
            for rule in policy.rules:
                if not rule.enabled:
                    continue
                violation = self._check_rule(content, rule)
                if violation:
                    all_violations.append(violation)

        if not all_violations:
            return {
                "action": "allow",
                "confidence": 1.0,
                "categories": [],
                "reasons": ["No policy violations detected"],
            }

        max_severity = self._get_max_severity(all_violations)
        action = self._severity_to_action(max_severity)

        return {
            "action": action,
            "confidence": min(0.5 + len(all_violations) * 0.1, 1.0),
            "categories": [v["rule_name"] for v in all_violations],
            "reasons": [v["reason"] for v in all_violations],
            "policy_violations": [v["rule_id"] for v in all_violations],
        }

    def _check_rule(self, content: str, rule: PolicyRule) -> dict[str, Any] | None:
        """Check if content violates a specific rule.

        Args:
            content: Content to check.
            rule: Policy rule to check against.

        Returns:
            Violation details if rule is triggered, None otherwise.
        """
        if re.search(rule.pattern, content, re.IGNORECASE):
            return {
                "rule_id": str(rule.id),
                "rule_name": rule.name,
                "severity": rule.severity.value,
                "reason": f"Matched rule '{rule.name}': {rule.description}",
            }
        return None

    def _get_max_severity(self, violations: list[dict[str, Any]]) -> str:
        """Get the highest severity from violations.

        Args:
            violations: List of violation dictionaries.

        Returns:
            Highest severity level string.
        """
        severity_order = {"low": 0, "medium": 1, "high": 2, "critical": 3}
        return max(
            (v["severity"] for v in violations),
            key=lambda s: severity_order.get(s, 0),
        )

    def _severity_to_action(self, severity: str) -> str:
        """Convert severity level to moderation action.

        Args:
            severity: Severity level string.

        Returns:
            Corresponding moderation action.
        """
        mapping = {
            "low": "flag",
            "medium": "flag",
            "high": "block",
            "critical": "block",
        }
        return mapping.get(severity, "flag")
