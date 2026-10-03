"""Audit Reporter Agent - generates audit reports with findings and evidence."""

from __future__ import annotations

from typing import Any

from compliance_monitor.agents.base import BaseComplianceAgent
from compliance_monitor.models.schemas import AuditReport, AuditRequest


class AuditReporterAgent(BaseComplianceAgent[AuditRequest, AuditReport]):
    """Agent responsible for generating compliance audit reports.

    Uses LangChain DeepAgents to compile findings, analyze evidence,
    and produce comprehensive audit reports.
    """

    def __init__(self, model: str = "gpt-4o") -> None:
        """Initialize the Audit Reporter Agent.

        Args:
            model: LLM model to use for report generation.
        """
        super().__init__(name="AuditReporterAgent", model=model)

    async def run(self, input_data: AuditRequest) -> AuditReport:
        """Generate an audit report.

        Args:
            input_data: Audit request data.

        Returns:
            Generated AuditReport instance.
        """
        report = AuditReport(
            title=input_data.title,
            description=input_data.description,
            period_start=input_data.period_start,
            period_end=input_data.period_end,
            policies_reviewed=input_data.policy_ids,
        )
        return report

    async def compile_findings(
        self,
        policies: list[dict[str, Any]],
        violations: list[dict[str, Any]],
    ) -> list[str]:
        """Compile audit findings from policies and violations.

        Args:
            policies: List of policy data.
            violations: List of violation data.

        Returns:
            List of audit findings.
        """
        prompt = f"""Compile audit findings from the following data:

Policies Reviewed:
{policies}

Violations Found:
{violations}

Generate a comprehensive list of audit findings with:
1. Finding description
2. Risk level
3. Recommended action
4. Priority
"""
        result = await self.agent.ainvoke(
            {"messages": [{"role": "user", "content": prompt}]}
        )
        return [str(result)]

    async def generate_executive_summary(self, report_data: dict[str, Any]) -> str:
        """Generate an executive summary for an audit report.

        Args:
            report_data: Audit report data.

        Returns:
            Executive summary text.
        """
        prompt = f"""Generate an executive summary for this compliance audit report:

{report_data}

The summary should be concise, highlight key findings, and provide
recommendations for leadership.
"""
        result = await self.agent.ainvoke(
            {"messages": [{"role": "user", "content": prompt}]}
        )
        return str(result)

    async def export_report(
        self, report: AuditReport, format: str = "json"  # noqa: A002
    ) -> dict[str, Any]:
        """Export an audit report in the specified format.

        Args:
            report: Audit report to export.
            format: Export format (json, pdf, html).

        Returns:
            Exported report data.
        """
        return {
            "format": format,
            "report_id": str(report.id),
            "title": report.title,
            "generated_at": report.generated_at.isoformat(),
            "content": report.model_dump(),
        }
