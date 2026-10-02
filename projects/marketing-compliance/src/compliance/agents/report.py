"""Report agent: produces compliance reports and audit trails."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from compliance.agents.base import AgentResult, BaseAgent


class ReportAgent(BaseAgent):
    """Aggregates agent outputs into an auditable compliance report."""

    name = "report"

    async def run(self, payload: dict[str, Any]) -> AgentResult:
        """Generate a compliance report from pipeline results.

        Args:
            payload: Mapping containing optional ``violations``,
                ``responses``, and ``format`` keys.

        Returns:
            An :class:`AgentResult` whose single item is the report document.
        """
        violations: list[dict[str, Any]] = payload.get("violations", [])
        responses: list[dict[str, Any]] = payload.get("responses", [])
        report_format: str = payload.get(
            "format", self.config.get("default_format", "json")
        )

        report = {
            "generated_at": datetime.now(UTC).isoformat(),
            "format": report_format,
            "summary": self._summarise(violations, responses),
            "violations": violations,
            "responses": responses,
        }

        return AgentResult(
            agent=self.name,
            items=[report],
            metrics={
                "violations_in_report": float(len(violations)),
                "responses_in_report": float(len(responses)),
            },
        )

    @staticmethod
    def _summarise(
        violations: list[dict[str, Any]], responses: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Compute summary statistics for a report.

        Args:
            violations: Violation records.
            responses: Response records.

        Returns:
            A summary mapping with counts by severity and action.
        """
        by_severity: dict[str, int] = {}
        for violation in violations:
            severity = str(violation.get("severity", "unknown"))
            by_severity[severity] = by_severity.get(severity, 0) + 1

        by_action: dict[str, int] = {}
        for response in responses:
            action = str(response.get("action", "unknown"))
            by_action[action] = by_action.get(action, 0) + 1

        return {
            "total_violations": len(violations),
            "total_responses": len(responses),
            "by_severity": by_severity,
            "by_action": by_action,
        }

    def to_json(self, report: dict[str, Any]) -> str:
        """Serialise a report document to a JSON string.

        Args:
            report: The report document produced by :meth:`run`.

        Returns:
            A pretty-printed JSON string.
        """
        return json.dumps(report, indent=2, default=str)
