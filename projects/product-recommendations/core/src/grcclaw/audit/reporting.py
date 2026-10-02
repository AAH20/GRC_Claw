"""
Audit reporting — generate structured audit reports with opinions,
findings summaries, and management responses.
"""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import UTC, datetime
from typing import Any

from .models import (
    AuditEngagement,
    AuditReport,
    ComplianceAssessment,
    Finding,
    FindingSeverity,
    FindingStatus,
    OverallOpinion,
    Workpaper,
)


class AuditReporter:
    """
    Generates audit reports from engagement data.

    Features:
    - Executive summary generation
    - Findings aggregation and severity analysis
    - Overall opinion determination
    - Compliance score integration
    - Management response tracking
    - Report export (JSON, Markdown, HTML)
    """

    def __init__(self):
        self._reports: dict[str, AuditReport] = {}

    # ------------------------------------------------------------------
    # Report generation
    # ------------------------------------------------------------------

    def generate_report(
        self,
        audit: AuditEngagement,
        findings: list[Finding],
        workpapers: list[Workpaper],
        controls: list | None = None,
        assessment: ComplianceAssessment | None = None,
        generated_by: str | None = None,
    ) -> AuditReport:
        """
        Generate a comprehensive audit report.

        Determines overall opinion based on finding severity distribution
        and compliance scores.
        """
        # Count findings by severity
        by_severity: dict[str, int] = defaultdict(int)
        by_status: dict[str, int] = defaultdict(int)
        for f in findings:
            by_severity[f.severity.value] += 1
            by_status[f.status.value] += 1

        # Determine overall opinion
        opinion = self._determine_opinion(findings, assessment)

        # Build executive summary
        exec_summary = self._build_executive_summary(
            audit, findings, opinion, assessment
        )

        # Build recommendations
        recommendations = self._build_recommendations(findings)

        report = AuditReport(
            audit_id=audit.audit_id,
            title=f"Audit Report: {audit.name}",
            executive_summary=exec_summary,
            scope_and_objectives=self._format_scope(audit),
            methodology=self._format_methodology(workpapers),
            total_findings=len(findings),
            critical_findings=by_severity.get("critical", 0),
            high_findings=by_severity.get("high", 0),
            medium_findings=by_severity.get("medium", 0),
            low_findings=by_severity.get("low", 0),
            informational_findings=by_severity.get("informational", 0),
            open_findings=by_status.get("open", 0) + by_status.get("in_progress", 0),
            closed_findings=by_status.get("closed", 0) + by_status.get("verified", 0),
            overall_opinion=opinion,
            opinion_basis=self._build_opinion_basis(findings, opinion, assessment),
            recommendations=recommendations,
            generated_by=generated_by,
        )

        self._reports[report.report_id] = report
        return report

    def _determine_opinion(
        self,
        findings: list[Finding],
        assessment: ComplianceAssessment | None = None,
    ) -> OverallOpinion:
        """Determine the overall audit opinion."""
        critical_count = sum(1 for f in findings if f.severity == FindingSeverity.CRITICAL)
        high_count = sum(1 for f in findings if f.severity == FindingSeverity.HIGH)
        open_critical = sum(
            1 for f in findings
            if f.severity == FindingSeverity.CRITICAL
            and f.status in (FindingStatus.OPEN, FindingStatus.IN_PROGRESS)
        )

        # Adverse: multiple critical findings or systemic failures
        if critical_count >= 3 or open_critical >= 2:
            return OverallOpinion.ADVERSE

        # Qualified: critical or high findings present
        if critical_count > 0 or high_count > 0:
            return OverallOpinion.QUALIFIED

        # Disclaimer: insufficient evidence (no workpapers, no controls assessed)
        if assessment and assessment.not_assessed_controls == assessment.total_controls:
            return OverallOpinion.DISCLAIMER

        # Unqualified: no critical/high findings
        return OverallOpinion.UNQUALIFIED

    def _build_executive_summary(
        self,
        audit: AuditEngagement,
        findings: list[Finding],
        opinion: OverallOpinion,
        assessment: ComplianceAssessment | None = None,
    ) -> str:
        """Build the executive summary text."""
        parts = [
            f"Audit of {audit.name} was conducted"
        ]
        if audit.start_date and audit.end_date:
            parts.append(f" from {audit.start_date} to {audit.end_date}")
        parts.append(".\n\n")

        parts.append(
            f"A total of {len(findings)} findings were identified: "
            f"{sum(1 for f in findings if f.severity == FindingSeverity.CRITICAL)} critical, "
            f"{sum(1 for f in findings if f.severity == FindingSeverity.HIGH)} high, "
            f"{sum(1 for f in findings if f.severity == FindingSeverity.MEDIUM)} medium, "
            f"{sum(1 for f in findings if f.severity == FindingSeverity.LOW)} low, and "
            f"{sum(1 for f in findings if f.severity == FindingSeverity.INFORMATIONAL)} informational.\n\n"
        )

        if assessment:
            parts.append(
                f"The compliance assessment against {assessment.framework.value} "
                f"yielded a score of {assessment.compliance_score}% "
                f"({assessment.compliant_controls} compliant, "
                f"{assessment.partially_compliant_controls} partially compliant, "
                f"{assessment.non_compliant_controls} non-compliant out of "
                f"{assessment.total_controls} controls).\n\n"
            )

        parts.append(f"Overall audit opinion: {opinion.value.upper()}.")

        return "".join(parts)

    def _format_scope(self, audit: AuditEngagement) -> str:
        """Format the audit scope section."""
        parts = ["## Scope and Objectives\n"]
        if audit.scope:
            parts.append("### Scope\n")
            for item in audit.scope:
                parts.append(f"- {item}\n")
        if audit.objectives:
            parts.append("\n### Objectives\n")
            for obj in audit.objectives:
                parts.append(f"- {obj}\n")
        return "".join(parts)

    def _format_methodology(self, workpapers: list[Workpaper]) -> str:
        """Format the methodology section."""
        parts = ["## Methodology\n"]
        parts.append(
            f"The audit was conducted using {len(workpapers)} workpapers "
            f"covering control testing, substantive procedures, and analytical review.\n\n"
        )
        if workpapers:
            parts.append("### Workpapers Reviewed\n")
            for wp in workpapers:
                conclusion = wp.conclusion or "pending"
                parts.append(f"- **{wp.title}** — {conclusion}\n")
        return "".join(parts)

    def _build_opinion_basis(
        self,
        findings: list[Finding],
        opinion: OverallOpinion,
        assessment: ComplianceAssessment | None = None,
    ) -> str:
        """Build the basis for the overall opinion."""
        parts = [f"The overall opinion of {opinion.value} is based on the following:\n\n"]

        critical = [f for f in findings if f.severity == FindingSeverity.CRITICAL]
        high = [f for f in findings if f.severity == FindingSeverity.HIGH]

        if critical:
            parts.append(f"**Critical Findings ({len(critical)}):**\n")
            for f in critical:
                parts.append(f"- {f.title}: {f.description[:200]}...\n")
            parts.append("\n")

        if high:
            parts.append(f"**High Findings ({len(high)}):**\n")
            for f in high:
                parts.append(f"- {f.title}: {f.description[:200]}...\n")
            parts.append("\n")

        if assessment:
            parts.append(
                f"**Compliance Score:** {assessment.compliance_score}% "
                f"against {assessment.framework.value} framework.\n\n"
            )

        if opinion == OverallOpinion.UNQUALIFIED:
            parts.append(
                "No critical or high severity findings were identified. "
                "The organization's controls are operating effectively."
            )
        elif opinion == OverallOpinion.QUALIFIED:
            parts.append(
                "One or more critical or high severity findings were identified "
                "that affect the overall control environment."
            )
        elif opinion == OverallOpinion.ADVERSE:
            parts.append(
                "Multiple critical findings were identified indicating systemic "
                "control failures that materially affect the control environment."
            )
        elif opinion == OverallOpinion.DISCLAIMER:
            parts.append(
                "Insufficient evidence was available to form an opinion on the "
                "operating effectiveness of controls."
            )

        return "".join(parts)

    def _build_recommendations(self, findings: list[Finding]) -> list[str]:
        """Build prioritized recommendations from findings."""
        recommendations = []
        critical = [f for f in findings if f.severity == FindingSeverity.CRITICAL]
        high = [f for f in findings if f.severity == FindingSeverity.HIGH]

        for f in critical:
            rec = f"[CRITICAL] {f.recommendation or f.title}"
            if rec not in recommendations:
                recommendations.append(rec)

        for f in high:
            rec = f"[HIGH] {f.recommendation or f.title}"
            if rec not in recommendations:
                recommendations.append(rec)

        return recommendations

    # ------------------------------------------------------------------
    # Report retrieval
    # ------------------------------------------------------------------

    def get_report(self, report_id: str) -> AuditReport | None:
        """Get a report by ID."""
        return self._reports.get(report_id)

    def list_reports(self) -> list[AuditReport]:
        """List all generated reports."""
        return list(self._reports.values())

    # ------------------------------------------------------------------
    # Report export
    # ------------------------------------------------------------------

    def export_report_json(self, report: AuditReport) -> str:
        """Export report as JSON."""
        return json.dumps(self._report_to_dict(report), indent=2, default=str)

    def export_report_markdown(self, report: AuditReport) -> str:
        """Export report as Markdown."""
        parts = [
            f"# {report.title}\n\n",
            f"**Report ID:** {report.report_id}\n",
            f"**Audit ID:** {report.audit_id}\n",
            f"**Generated:** {report.generated_at}\n",
            f"**Generated By:** {report.generated_by or 'System'}\n\n",
            "---\n\n",
            "## Executive Summary\n\n",
            f"{report.executive_summary}\n\n",
            "---\n\n",
            f"{report.scope_and_objectives}\n\n",
            "---\n\n",
            f"{report.methodology}\n\n",
            "---\n\n",
            "## Findings Summary\n\n",
            "| Severity | Count |\n|----------|-------|\n",
            f"| Critical | {report.critical_findings} |\n",
            f"| High | {report.high_findings} |\n",
            f"| Medium | {report.medium_findings} |\n",
            f"| Low | {report.low_findings} |\n",
            f"| Informational | {report.informational_findings} |\n",
            f"| **Total** | **{report.total_findings}** |\n\n",
            f"**Open Findings:** {report.open_findings}\n",
            f"**Closed Findings:** {report.closed_findings}\n\n",
            "---\n\n",
            "## Overall Opinion\n\n",
            f"**{report.overall_opinion.value.upper() if report.overall_opinion else 'N/A'}**\n\n",
            f"{report.opinion_basis}\n\n",
            "---\n\n",
            "## Recommendations\n\n",
        ]
        for i, rec in enumerate(report.recommendations, 1):
            parts.append(f"{i}. {rec}\n")

        if report.management_response:
            parts.append("\n---\n\n## Management Response\n\n")
            parts.append(f"{report.management_response}\n")

        return "".join(parts)

    def export_report_html(self, report: AuditReport) -> str:
        """Export report as HTML."""
        opinion_color = {
            "unqualified": "#28a745",
            "qualified": "#ffc107",
            "adverse": "#dc3545",
            "disclaimer": "#6c757d",
        }
        color = opinion_color.get(
            report.overall_opinion.value if report.overall_opinion else "", "#6c757d"
        )

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{report.title}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 900px; margin: 0 auto; padding: 2rem; color: #333; }}
        h1 {{ color: #1a1a2e; border-bottom: 3px solid #16213e; padding-bottom: 0.5rem; }}
        h2 {{ color: #16213e; margin-top: 2rem; }}
        h3 {{ color: #0f3460; }}
        table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
        th, td {{ border: 1px solid #ddd; padding: 0.5rem; text-align: left; }}
        th {{ background: #16213e; color: white; }}
        tr:nth-child(even) {{ background: #f8f9fa; }}
        .opinion {{ padding: 1rem; border-radius: 4px; color: white; font-weight: bold; font-size: 1.2rem; display: inline-block; }}
        .meta {{ color: #666; font-size: 0.9rem; }}
        .severity-critical {{ color: #dc3545; font-weight: bold; }}
        .severity-high {{ color: #fd7e14; font-weight: bold; }}
        .severity-medium {{ color: #ffc107; }}
        .severity-low {{ color: #17a2b8; }}
    </style>
</head>
<body>
    <h1>{report.title}</h1>
    <p class="meta">
        <strong>Report ID:</strong> {report.report_id}<br>
        <strong>Audit ID:</strong> {report.audit_id}<br>
        <strong>Generated:</strong> {report.generated_at}<br>
        <strong>Generated By:</strong> {report.generated_by or 'System'}
    </p>

    <h2>Executive Summary</h2>
    <p>{report.executive_summary}</p>

    <h2>Findings Summary</h2>
    <table>
        <tr><th>Severity</th><th>Count</th></tr>
        <tr><td class="severity-critical">Critical</td><td>{report.critical_findings}</td></tr>
        <tr><td class="severity-high">High</td><td>{report.high_findings}</td></tr>
        <tr><td class="severity-medium">Medium</td><td>{report.medium_findings}</td></tr>
        <tr><td class="severity-low">Low</td><td>{report.low_findings}</td></tr>
        <tr><td>Informational</td><td>{report.informational_findings}</td></tr>
        <tr><td><strong>Total</strong></td><td><strong>{report.total_findings}</strong></td></tr>
    </table>
    <p><strong>Open:</strong> {report.open_findings} | <strong>Closed:</strong> {report.closed_findings}</p>

    <h2>Overall Opinion</h2>
    <div class="opinion" style="background-color: {color};">
        {report.overall_opinion.value.upper() if report.overall_opinion else 'N/A'}
    </div>
    <p>{report.opinion_basis}</p>

    <h2>Recommendations</h2>
    <ol>
        {''.join(f'<li>{rec}</li>' for rec in report.recommendations)}
    </ol>

    {f'<h2>Management Response</h2><p>{report.management_response}</p>' if report.management_response else ''}
</body>
</html>"""
        return html

    def _report_to_dict(self, report: AuditReport) -> dict[str, Any]:
        """Convert report to dictionary."""
        return {
            "report_id": report.report_id,
            "audit_id": report.audit_id,
            "title": report.title,
            "executive_summary": report.executive_summary,
            "scope_and_objectives": report.scope_and_objectives,
            "methodology": report.methodology,
            "total_findings": report.total_findings,
            "critical_findings": report.critical_findings,
            "high_findings": report.high_findings,
            "medium_findings": report.medium_findings,
            "low_findings": report.low_findings,
            "informational_findings": report.informational_findings,
            "open_findings": report.open_findings,
            "closed_findings": report.closed_findings,
            "overall_opinion": report.overall_opinion.value if report.overall_opinion else None,
            "opinion_basis": report.opinion_basis,
            "recommendations": report.recommendations,
            "management_response": report.management_response,
            "generated_at": report.generated_at,
            "generated_by": report.generated_by,
            "metadata": report.metadata,
        }

    # ------------------------------------------------------------------
    # Management response
    # ------------------------------------------------------------------

    def add_management_response(
        self, report_id: str, response: str
    ) -> AuditReport | None:
        """Add a management response to a report."""
        report = self._reports.get(report_id)
        if not report:
            return None
        report.management_response = response
        return report

    # ------------------------------------------------------------------
    # Compliance report
    # ------------------------------------------------------------------

    def generate_compliance_report(
        self,
        assessment: ComplianceAssessment,
        controls: list,
        findings: list[Finding],
    ) -> dict[str, Any]:
        """Generate a compliance assessment report."""
        by_status: dict[str, int] = defaultdict(int)
        by_type: dict[str, int] = defaultdict(int)
        for c in controls:
            by_status[c.status.value] += 1
            by_type[c.control_type.value] += 1

        open_findings = [
            f for f in findings
            if f.status in (FindingStatus.OPEN, FindingStatus.IN_PROGRESS)
        ]
        overdue_findings = [
            f for f in open_findings
            if f.due_date and datetime.fromisoformat(f.due_date) < datetime.now(UTC)
        ]

        return {
            "assessment_id": assessment.assessment_id,
            "framework": assessment.framework.value,
            "assessment_name": assessment.assessment_name,
            "status": assessment.status.value,
            "compliance_score": assessment.compliance_score,
            "total_controls": assessment.total_controls,
            "controls_by_status": dict(by_status),
            "controls_by_type": dict(by_type),
            "open_findings": len(open_findings),
            "overdue_findings": len(overdue_findings),
            "start_date": assessment.start_date,
            "end_date": assessment.end_date,
            "assessor": assessment.assessor,
            "generated_at": datetime.now(UTC).isoformat(),
        }
