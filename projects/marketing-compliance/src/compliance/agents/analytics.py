"""Analytics agent: tracks compliance metrics and trends."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from compliance.agents.base import AgentResult, BaseAgent


class AnalyticsAgent(BaseAgent):
    """Computes compliance KPIs and trends over time."""

    name = "analytics"

    async def run(self, payload: dict[str, Any]) -> AgentResult:
        """Compute analytics over a batch of violations.

        Args:
            payload: Mapping containing a ``violations`` list, each optionally
                carrying a ``detected_at`` ISO timestamp.

        Returns:
            An :class:`AgentResult` whose single item holds the analytics
            payload, with ``metrics`` mirroring the headline KPIs.
        """
        violations: list[dict[str, Any]] = payload.get("violations", [])

        by_severity = Counter(str(v.get("severity", "unknown")) for v in violations)
        by_rule = Counter(str(v.get("rule", "unknown")) for v in violations)
        by_source = Counter(str(v.get("source", "unknown")) for v in violations)

        trend: dict[str, int] = defaultdict(int)
        for violation in violations:
            detected_at = violation.get("detected_at")
            if isinstance(detected_at, str) and len(detected_at) >= 10:
                trend[detected_at[:10]] += 1

        total = len(violations)
        critical = by_severity.get("critical", 0)
        compliance_rate = 0.0 if total == 0 else max(0.0, 1.0 - (critical / total))

        analytics = {
            "total_violations": total,
            "by_severity": dict(by_severity),
            "by_rule": dict(by_rule),
            "by_source": dict(by_source),
            "trend": dict(sorted(trend.items())),
            "compliance_rate": round(compliance_rate, 4),
        }

        return AgentResult(
            agent=self.name,
            items=[analytics],
            metrics={
                "total_violations": float(total),
                "critical_violations": float(critical),
                "compliance_rate": round(compliance_rate, 4),
            },
        )
