"""Respond agent: generates remediation actions for detected violations."""

from __future__ import annotations

from typing import Any

from compliance.agents.base import AgentResult, BaseAgent, Severity

_ESCALATION_ORDER = {
    Severity.LOW.value: 0,
    Severity.MEDIUM.value: 1,
    Severity.HIGH.value: 2,
    Severity.CRITICAL.value: 3,
}


class RespondAgent(BaseAgent):
    """Produces remediation guidance and escalation decisions.

    The respond agent never mutates external systems directly unless
    ``auto_respond`` is explicitly enabled in configuration; by default it
    emits recommendations for human review.
    """

    name = "respond"

    async def run(self, payload: dict[str, Any]) -> AgentResult:
        """Generate remediation responses for the supplied violations.

        Args:
            payload: Mapping containing a ``violations`` list and optional
                ``escalation_threshold``.

        Returns:
            An :class:`AgentResult` whose ``items`` are response records.
        """
        violations: list[dict[str, Any]] = payload.get("violations", [])
        threshold = payload.get(
            "escalation_threshold", self.config.get("escalation_threshold", Severity.HIGH.value)
        )
        auto_respond: bool = bool(self.config.get("auto_respond", False))
        threshold_rank = _ESCALATION_ORDER.get(str(threshold), 2)

        responses: list[dict[str, Any]] = []
        for violation in violations:
            severity = str(violation.get("severity", Severity.LOW.value))
            escalate = _ESCALATION_ORDER.get(severity, 0) >= threshold_rank
            responses.append(
                {
                    "content_id": violation.get("content_id"),
                    "rule": violation.get("rule"),
                    "severity": severity,
                    "action": "escalate" if escalate else "recommend",
                    "auto_applied": auto_respond and not escalate,
                    "recommendation": self._recommendation(violation),
                }
            )

        return AgentResult(
            agent=self.name,
            items=responses,
            metrics={
                "responses_generated": float(len(responses)),
                "escalations": float(sum(1 for r in responses if r["action"] == "escalate")),
            },
        )

    @staticmethod
    def _recommendation(violation: dict[str, Any]) -> str:
        """Build a human-readable remediation recommendation.

        Args:
            violation: A violation record from the detect agent.

        Returns:
            A remediation string.
        """
        rule = violation.get("rule", "unknown")
        templates = {
            "unsubscribe_missing": "Add a compliant unsubscribe link before sending.",
            "guaranteed_claims": "Soften absolute claims and cite substantiation.",
            "pii_leak": "Remove personal data and notify the privacy office immediately.",
        }
        return templates.get(rule, "Review content against the applicable policy.")
