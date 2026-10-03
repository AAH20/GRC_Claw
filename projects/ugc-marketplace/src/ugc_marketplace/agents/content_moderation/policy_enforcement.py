"""Policy enforcement agent for content moderation."""

from __future__ import annotations

import re
from typing import Any

from ugc_marketplace.agents.content_moderation.base import BaseModerationAgent
from ugc_marketplace.models.schemas import ContentType, Policy


class PolicyEnforcementAgent(BaseModerationAgent):
    """Agent that enforces content policies using regex and keyword matching."""

    @property
    def content_type(self) -> ContentType:
        """Content type this agent handles."""
        return ContentType.TEXT

    async def _analyze(self, content: str, context: dict[str, Any]) -> dict[str, Any]:
        """Analyze content against configured policies.

        Args:
            content: Content to analyze.
            context: Must contain 'policies' key with list of Policy objects.

        Returns:
            Analysis result with action, confidence, categories, and reasons.
        """
        policies: list[Policy] = context.get("policies", [])
        violations: list[str] = []
        categories: list[str] = []
        reasons: list[str] = []
        max_severity = "low"

        severity_order = {"low": 0, "medium": 1, "high": 2, "critical": 3}

        for policy in policies:
            if not policy.enabled:
                continue
            for rule in policy.rules:
                if not rule.enabled:
                    continue
                if re.search(rule.pattern, content, re.IGNORECASE):
                    violations.append(str(rule.id))
                    categories.append(rule.name)
                    reasons.append(f"Policy rule triggered: {rule.name}")
                    if severity_order.get(rule.severity.value, 0) > severity_order.get(
                        max_severity, 0
                    ):
                        max_severity = rule.severity.value

        if violations:
            action = "block" if max_severity in ("high", "critical") else "flag"
            confidence = 0.9 if max_severity == "critical" else 0.75
        else:
            action = "allow"
            confidence = 0.95

        return {
            "action": action,
            "confidence": confidence,
            "categories": categories,
            "reasons": reasons,
            "policy_violations": violations,
        }
