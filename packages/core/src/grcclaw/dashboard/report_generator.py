"""
Governance Report Generator for GRC_Claw.

Generates comprehensive governance reports in multiple formats (HTML, JSON, Markdown,
CSV, PDF-ready) from dashboard snapshots and analytics data.
"""

from __future__ import annotations

import csv
import io
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Optional
import uuid


# ─── Enums ───────────────────────────────────────────────────────────────────

class ReportFormat(str, Enum):
    """Supported report output formats."""

    JSON = "json"
    HTML = "html"
    MARKDOWN = "markdown"
    CSV = "csv"
    PDF = "pdf"
    XML = "xml"


class ReportType(str, Enum):
    """Types of governance reports."""

    EXECUTIVE_SUMMARY = "executive_summary"
    COMPLIANCE_STATUS = "compliance_status"
    RISK_ASSESSMENT = "risk_assessment"
    AUDIT_FINDINGS = "audit_findings"
    OPERATIONAL_METRICS = "operational_metrics"
    COST_ANALYSIS = "cost_analysis"
    INCIDENT_REPORT = "incident_report"
    TREND_ANALYSIS = "trend_analysis"
    CUSTOM = "custom"


class ReportSection(str, Enum):
    """Standard report sections."""

    OVERVIEW = "overview"
    KEY_METRICS = "key_metrics"
    FINDINGS = "findings"
    RECOMMENDATIONS = "recommendations"
    APPENDIX = "appendix"
    TIMELINE = "timeline"
    DETAILED_DATA = "detailed_data"


class ReportFrequency(str, Enum):
    """Report generation frequency."""

    ON_DEMAND = "on_demand"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUALLY = "annually"


# ─── Data Models ─────────────────────────────────────────────────────────────

@dataclass
class ReportFilter:
    """Filter criteria for report data."""

    frameworks: list[str] = field(default_factory=list)
    severity_levels: list[str] = field(default_factory=list)
    status_filter: list[str] = field(default_factory=list)
    date_range_start: Optional[str] = None
    date_range_end: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    categories: list[str] = field(default_factory=list)
    entities: list[str] = field(default_factory=list)
    custom_filters: dict[str, Any] = field(default_factory=dict)


@dataclass
class ReportSchedule:
    """Schedule configuration for automated report generation."""

    schedule_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    report_type: ReportType = ReportType.EXECUTIVE_SUMMARY
    frequency: ReportFrequency = ReportFrequency.WEEKLY
    format: ReportFormat = ReportFormat.HTML
    recipients: list[str] = field(default_factory=list)
    dashboard_ids: list[str] = field(default_factory=list)
    template_id: Optional[str] = None
    filters: ReportFilter = field(default_factory=ReportFilter)
    enabled: bool = True
    last_run_at: Optional[str] = None
    next_run_at: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class ReportSectionData:
    """Content for a single report section."""

    section_type: ReportSection = ReportSection.OVERVIEW
    title: str = ""
    content: Any = None
    summary: str = ""
    metrics: dict[str, Any] = field(default_factory=dict)
    tables: list[dict[str, Any]] = field(default_factory=list)
    charts: list[dict[str, Any]] = field(default_factory=list)
    findings: list[dict[str, Any]] = field(default_factory=list)
    order: int = 0


@dataclass
class GeneratedReport:
    """A fully generated governance report."""

    report_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    report_type: ReportType = ReportType.EXECUTIVE_SUMMARY
    format: ReportFormat = ReportFormat.HTML
    title: str = ""
    description: str = ""
    sections: list[ReportSectionData] = field(default_factory=list)
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    period_start: str = ""
    period_end: str = ""
    filters_applied: ReportFilter = field(default_factory=ReportFilter)
    dashboard_sources: list[str] = field(default_factory=list)
    summary: str = ""
    key_findings: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    file_size_bytes: int = 0
    generation_time_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "report_type": self.report_type.value,
            "format": self.format.value,
            "title": self.title,
            "description": self.description,
            "generated_at": self.generated_at,
            "period_start": self.period_start,
            "period_end": self.period_end,
            "summary": self.summary,
            "key_findings": self.key_findings,
            "recommendations": self.recommendations,
            "dashboard_sources": self.dashboard_sources,
            "metadata": self.metadata,
            "file_size_bytes": self.file_size_bytes,
            "generation_time_ms": self.generation_time_ms,
            "section_count": len(self.sections),
        }


# ─── Report Generator ────────────────────────────────────────────────────────

class ReportGenerator:
    """
    Generates governance reports from dashboard data and analytics.
    Supports multiple output formats and customizable sections.
    """

    def __init__(self):
        self._schedules: dict[str, ReportSchedule] = {}
        self._report_history: list[GeneratedReport] = []
        self._templates: dict[str, dict[str, Any]] = {}
        self._max_history = 100

    # ── Report Generation ────────────────────────────────────────────────

    def generate(
        self,
        report_type: ReportType,
        dashboard_snapshots: dict[str, Any],
        format: ReportFormat = ReportFormat.HTML,
        filters: Optional[ReportFilter] = None,
        period_start: Optional[str] = None,
        period_end: Optional[str] = None,
        title: Optional[str] = None,
        custom_sections: Optional[list[ReportSectionData]] = None,
    ) -> GeneratedReport:
        import time
        start = time.time()

        now = datetime.now(timezone.utc)
        if period_end is None:
            period_end = now.isoformat()
        if period_start is None:
            period_start = (now - timedelta(days=30)).isoformat()

        filters = filters or ReportFilter()

        sections: list[ReportSectionData] = custom_sections or self._build_sections(
            report_type, dashboard_snapshots, filters
        )

        key_findings = self._extract_findings(sections)
        recommendations = self._generate_recommendations(sections, report_type)
        summary = self._generate_summary(sections, report_type)

        report = GeneratedReport(
            report_type=report_type,
            format=format,
            title=title or self._default_title(report_type),
            description=self._default_description(report_type),
            sections=sections,
            period_start=period_start,
            period_end=period_end,
            filters_applied=filters,
            dashboard_sources=list(dashboard_snapshots.keys()),
            summary=summary,
            key_findings=key_findings,
            recommendations=recommendations,
        )

        # Serialize to target format
        content = self._serialize(report, format)
        report.file_size_bytes = len(content.encode("utf-8")) if isinstance(content, str) else len(content)
        report.generation_time_ms = round((time.time() - start) * 1000, 2)

        self._add_to_history(report)
        return report

    def generate_from_template(
        self,
        template_id: str,
        dashboard_snapshots: dict[str, Any],
        format: Optional[ReportFormat] = None,
    ) -> GeneratedReport:
        template = self._templates.get(template_id)
        if template is None:
            raise ValueError(f"report template '{template_id}' not found")
        return self.generate(
            report_type=ReportType(template.get("report_type", "custom")),
            dashboard_snapshots=dashboard_snapshots,
            format=format or ReportFormat(template.get("format", "html")),
            filters=ReportFilter(**template.get("filters", {})),
            title=template.get("title"),
        )

    # ── Format Serializers ───────────────────────────────────────────────

    def serialize_report(self, report: GeneratedReport, format: ReportFormat) -> str:
        return self._serialize(report, format)

    def _serialize(self, report: GeneratedReport, format: ReportFormat) -> str:
        if format == ReportFormat.JSON:
            return self._to_json(report)
        elif format == ReportFormat.HTML:
            return self._to_html(report)
        elif format == ReportFormat.MARKDOWN:
            return self._to_markdown(report)
        elif format == ReportFormat.CSV:
            return self._to_csv(report)
        elif format == ReportFormat.XML:
            return self._to_xml(report)
        elif format == ReportFormat.PDF:
            return self._to_pdf(report)
        else:
            raise ValueError(f"unsupported report format: {format}")

    def _to_json(self, report: GeneratedReport) -> str:
        data = report.to_dict()
        data["sections"] = [
            {
                "section_type": s.section_type.value,
                "title": s.title,
                "summary": s.summary,
                "metrics": s.metrics,
                "findings": s.findings,
                "order": s.order,
            }
            for s in report.sections
        ]
        return json.dumps(data, indent=2, default=str)

    def _to_html(self, report: GeneratedReport) -> str:
        parts = [
            "<!DOCTYPE html>",
            "<html><head>",
            f"<title>{report.title}</title>",
            "<style>",
            "body{font-family:system-ui,sans-serif;margin:2rem;color:#1a1a2e;}",
            "h1{color:#16213e;border-bottom:3px solid #0f3460;padding-bottom:0.5rem;}",
            "h2{color:#0f3460;margin-top:2rem;}",
            ".metric-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:1rem;margin:1rem 0;}",
            ".metric-card{background:#f0f4f8;border-radius:8px;padding:1rem;text-align:center;}",
            ".metric-value{font-size:2rem;font-weight:bold;color:#0f3460;}",
            ".metric-label{font-size:0.85rem;color:#555;}",
            ".finding{background:#fff3cd;border-left:4px solid #ffc107;padding:0.75rem;margin:0.5rem 0;}",
            ".recommendation{background:#d1ecf1;border-left:4px solid #17a2b8;padding:0.75rem;margin:0.5rem 0;}",
            "table{border-collapse:collapse;width:100%;margin:1rem 0;}",
            "th,td{border:1px solid #ddd;padding:0.5rem;text-align:left;}",
            "th{background:#0f3460;color:white;}",
            ".footer{margin-top:3rem;padding-top:1rem;border-top:1px solid #ddd;font-size:0.8rem;color:#777;}",
            "</style>",
            "</head><body>",
            f"<h1>{report.title}</h1>",
            f"<p><em>{report.description}</em></p>",
            f"<p>Generated: {report.generated_at} | Period: {report.period_start} to {report.period_end}</p>",
        ]

        # Summary
        if report.summary:
            parts.append(f"<h2>Executive Summary</h2><p>{report.summary}</p>")

        # Key metrics from all sections
        all_metrics: dict[str, Any] = {}
        for section in report.sections:
            all_metrics.update(section.metrics)
        if all_metrics:
            parts.append("<h2>Key Metrics</h2><div class='metric-grid'>")
            for key, value in all_metrics.items():
                parts.append(
                    f"<div class='metric-card'>"
                    f"<div class='metric-value'>{value}</div>"
                    f"<div class='metric-label'>{key.replace('_', ' ').title()}</div>"
                    f"</div>"
                )
            parts.append("</div>")

        # Sections
        for section in sorted(report.sections, key=lambda s: s.order):
            parts.append(f"<h2>{section.title}</h2>")
            if section.summary:
                parts.append(f"<p>{section.summary}</p>")
            if section.findings:
                for finding in section.findings:
                    parts.append(
                        f"<div class='finding'>"
                        f"<strong>{finding.get('severity', 'INFO')}</strong>: "
                        f"{finding.get('description', '')}"
                        f"</div>"
                    )
            if section.tables:
                for table in section.tables:
                    parts.append(self._table_to_html(table))

        # Recommendations
        if report.recommendations:
            parts.append("<h2>Recommendations</h2>")
            for rec in report.recommendations:
                parts.append(f"<div class='recommendation'>{rec}</div>")

        # Footer
        parts.append(
            f"<div class='footer'>"
            f"Report ID: {report.report_id} | "
            f"Type: {report.report_type.value} | "
            f"Format: {report.format.value} | "
            f"Size: {report.file_size_bytes} bytes | "
            f"Generation time: {report.generation_time_ms}ms"
            f"</div>"
        )
        parts.append("</body></html>")
        return "\n".join(parts)

    def _to_markdown(self, report: GeneratedReport) -> str:
        lines = [
            f"# {report.title}",
            "",
            f"*{report.description}*",
            "",
            f"**Generated:** {report.generated_at}",
            f"**Period:** {report.period_start} to {report.period_end}",
            "",
        ]
        if report.summary:
            lines.extend(["## Executive Summary", "", report.summary, ""])

        all_metrics: dict[str, Any] = {}
        for section in report.sections:
            all_metrics.update(section.metrics)
        if all_metrics:
            lines.extend(["## Key Metrics", ""])
            for key, value in all_metrics.items():
                lines.append(f"- **{key.replace('_', ' ').title()}:** {value}")
            lines.append("")

        for section in sorted(report.sections, key=lambda s: s.order):
            lines.extend([f"## {section.title}", ""])
            if section.summary:
                lines.extend([section.summary, ""])
            if section.findings:
                for finding in section.findings:
                    lines.append(
                        f"- **[{finding.get('severity', 'INFO')}]** "
                        f"{finding.get('description', '')}"
                    )
                lines.append("")
            if section.tables:
                for table in section.tables:
                    lines.append(self._table_to_markdown(table))

        if report.recommendations:
            lines.extend(["## Recommendations", ""])
            for rec in report.recommendations:
                lines.append(f"- {rec}")
            lines.append("")

        lines.append("---")
        lines.append(
            f"*Report ID: {report.report_id} | Type: {report.report_type.value} | "
            f"Format: {report.format.value}*"
        )
        return "\n".join(lines)

    def _to_csv(self, report: GeneratedReport) -> str:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "Report ID", "Type", "Title", "Generated At",
            "Period Start", "Period End", "Section", "Key", "Value"
        ])
        for section in sorted(report.sections, key=lambda s: s.order):
            for key, value in section.metrics.items():
                writer.writerow([
                    report.report_id,
                    report.report_type.value,
                    report.title,
                    report.generated_at,
                    report.period_start,
                    report.period_end,
                    section.title,
                    key,
                    value,
                ])
            for finding in section.findings:
                writer.writerow([
                    report.report_id,
                    report.report_type.value,
                    report.title,
                    report.generated_at,
                    report.period_start,
                    report.period_end,
                    section.title,
                    f"finding:{finding.get('severity', 'INFO')}",
                    finding.get("description", ""),
                ])
        return output.getvalue()

    def _to_xml(self, report: GeneratedReport) -> str:
        parts = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            "<report>",
            f"  <report_id>{report.report_id}</report_id>",
            f"  <type>{report.report_type.value}</type>",
            f"  <title>{report.title}</title>",
            f"  <description>{report.description}</description>",
            f"  <generated_at>{report.generated_at}</generated_at>",
            f"  <period_start>{report.period_start}</period_start>",
            f"  <period_end>{report.period_end}</period_end>",
            "  <sections>",
        ]
        for section in sorted(report.sections, key=lambda s: s.order):
            parts.append(f"    <section type=\"{section.section_type.value}\">")
            parts.append(f"      <title>{section.title}</title>")
            parts.append(f"      <summary>{section.summary}</summary>")
            parts.append("      <metrics>")
            for key, value in section.metrics.items():
                parts.append(f"        <metric name=\"{key}\">{value}</metric>")
            parts.append("      </metrics>")
            parts.append("    </section>")
        parts.append("  </sections>")
        parts.append("</report>")
        return "\n".join(parts)

    def _to_pdf(self, report: GeneratedReport) -> str:
        # Returns HTML optimized for PDF conversion via headless browser
        html = self._to_html(report)
        # Add PDF-specific styles
        pdf_html = html.replace(
            "<style>",
            "<style>"
            "@page{size:A4;margin:2cm;}"
            "body{font-size:11pt;}"
            "h1{font-size:18pt;page-break-after:avoid;}"
            "h2{font-size:14pt;page-break-after:avoid;}"
            ".metric-card{page-break-inside:avoid;}"
            "table{page-break-inside:avoid;}",
        )
        return pdf_html

    # ── Section Builders ─────────────────────────────────────────────────

    def _build_sections(
        self,
        report_type: ReportType,
        snapshots: dict[str, Any],
        filters: ReportFilter,
    ) -> list[ReportSectionData]:
        builders = {
            ReportType.EXECUTIVE_SUMMARY: self._build_executive_summary,
            ReportType.COMPLIANCE_STATUS: self._build_compliance_status,
            ReportType.RISK_ASSESSMENT: self._build_risk_assessment,
            ReportType.AUDIT_FINDINGS: self._build_audit_findings,
            ReportType.OPERATIONAL_METRICS: self._build_operational_metrics,
            ReportType.COST_ANALYSIS: self._build_cost_analysis,
            ReportType.INCIDENT_REPORT: self._build_incident_report,
            ReportType.TREND_ANALYSIS: self._build_trend_analysis,
            ReportType.CUSTOM: self._build_custom_report,
        }
        builder = builders.get(report_type, self._build_custom_report)
        return builder(snapshots, filters)

    def _build_executive_summary(
        self, snapshots: dict[str, Any], filters: ReportFilter
    ) -> list[ReportSectionData]:
        total_dashboards = len(snapshots)
        total_widgets = 0
        total_errors = 0
        for snap in snapshots.values():
            if isinstance(snap, dict):
                widgets = snap.get("widget_data", {})
                total_widgets += len(widgets)
                total_errors += sum(
                    1 for w in widgets.values()
                    if isinstance(w, dict) and w.get("error")
                )

        return [
            ReportSectionData(
                section_type=ReportSection.OVERVIEW,
                title="Executive Overview",
                summary=f"Analysis across {total_dashboards} dashboards with {total_widgets} widgets.",
                metrics={
                    "dashboards_analyzed": total_dashboards,
                    "total_widgets": total_widgets,
                    "widget_errors": total_errors,
                    "overall_health_pct": round(
                        ((total_widgets - total_errors) / total_widgets * 100)
                        if total_widgets else 100.0, 1
                    ),
                },
                order=0,
            ),
            ReportSectionData(
                section_type=ReportSection.KEY_METRICS,
                title="Key Performance Indicators",
                metrics=self._aggregate_metrics(snapshots),
                order=1,
            ),
        ]

    def _build_compliance_status(
        self, snapshots: dict[str, Any], filters: ReportFilter
    ) -> list[ReportSectionData]:
        findings: list[dict[str, Any]] = []
        metrics: dict[str, Any] = {
            "frameworks_tracked": 0,
            "controls_passing": 0,
            "controls_failing": 0,
            "controls_unknown": 0,
            "compliance_score_pct": 0.0,
        }
        for dash_name, snap in snapshots.items():
            if isinstance(snap, dict):
                summary = snap.get("summary_metrics", {})
                metrics["controls_passing"] += summary.get("success_count", 0)
                metrics["controls_failing"] += summary.get("error_count", 0)
                findings.append({
                    "severity": "INFO" if summary.get("error_count", 0) == 0 else "WARNING",
                    "description": f"Dashboard '{dash_name}': {summary.get('success_count', 0)} controls passing, {summary.get('error_count', 0)} failing",
                })
        total = metrics["controls_passing"] + metrics["controls_failing"]
        metrics["compliance_score_pct"] = round(
            (metrics["controls_passing"] / total * 100) if total else 100.0, 1
        )
        return [
            ReportSectionData(
                section_type=ReportSection.OVERVIEW,
                title="Compliance Status Report",
                summary=f"Compliance score: {metrics['compliance_score_pct']}%",
                metrics=metrics,
                findings=findings,
                order=0,
            ),
        ]

    def _build_risk_assessment(
        self, snapshots: dict[str, Any], filters: ReportFilter
    ) -> list[ReportSectionData]:
        risk_items: list[dict[str, Any]] = []
        for dash_name, snap in snapshots.items():
            if isinstance(snap, dict):
                status = snap.get("overall_status", "unknown")
                if status in ("error", "degraded"):
                    risk_items.append({
                        "severity": "HIGH" if status == "error" else "MEDIUM",
                        "description": f"Dashboard '{dash_name}' status: {status}",
                        "source": dash_name,
                    })
        return [
            ReportSectionData(
                section_type=ReportSection.FINDINGS,
                title="Risk Assessment",
                findings=risk_items,
                metrics={
                    "risk_items_count": len(risk_items),
                    "high_risk_count": sum(1 for r in risk_items if r["severity"] == "HIGH"),
                    "medium_risk_count": sum(1 for r in risk_items if r["severity"] == "MEDIUM"),
                },
                order=0,
            ),
        ]

    def _build_audit_findings(
        self, snapshots: dict[str, Any], filters: ReportFilter
    ) -> list[ReportSectionData]:
        findings: list[dict[str, Any]] = []
        for dash_name, snap in snapshots.items():
            if isinstance(snap, dict):
                widgets = snap.get("widget_data", {})
                for wid, wdata in widgets.items():
                    if isinstance(wdata, dict) and wdata.get("error"):
                        findings.append({
                            "severity": "HIGH",
                            "description": f"Widget '{wid}' in '{dash_name}': {wdata['error']}",
                            "widget_id": wid,
                            "dashboard": dash_name,
                        })
        return [
            ReportSectionData(
                section_type=ReportSection.FINDINGS,
                title="Audit Findings",
                findings=findings,
                metrics={"total_findings": len(findings)},
                order=0,
            ),
        ]

    def _build_operational_metrics(
        self, snapshots: dict[str, Any], filters: ReportFilter
    ) -> list[ReportSectionData]:
        all_metrics = self._aggregate_metrics(snapshots)
        return [
            ReportSectionData(
                section_type=ReportSection.DETAILED_DATA,
                title="Operational Metrics",
                metrics=all_metrics,
                order=0,
            ),
        ]

    def _build_cost_analysis(
        self, snapshots: dict[str, Any], filters: ReportFilter
    ) -> list[ReportSectionData]:
        return [
            ReportSectionData(
                section_type=ReportSection.OVERVIEW,
                title="Cost Analysis",
                summary="Cost analysis across all monitored dashboards.",
                metrics=self._aggregate_metrics(snapshots),
                order=0,
            ),
        ]

    def _build_incident_report(
        self, snapshots: dict[str, Any], filters: ReportFilter
    ) -> list[ReportSectionData]:
        incidents: list[dict[str, Any]] = []
        for dash_name, snap in snapshots.items():
            if isinstance(snap, dict) and snap.get("overall_status") == "error":
                incidents.append({
                    "severity": "CRITICAL",
                    "description": f"Dashboard '{dash_name}' is in error state",
                    "dashboard": dash_name,
                })
        return [
            ReportSectionData(
                section_type=ReportSection.TIMELINE,
                title="Incident Report",
                findings=incidents,
                metrics={"incident_count": len(incidents)},
                order=0,
            ),
        ]

    def _build_trend_analysis(
        self, snapshots: dict[str, Any], filters: ReportFilter
    ) -> list[ReportSectionData]:
        return [
            ReportSectionData(
                section_type=ReportSection.DETAILED_DATA,
                title="Trend Analysis",
                metrics=self._aggregate_metrics(snapshots),
                order=0,
            ),
        ]

    def _build_custom_report(
        self, snapshots: dict[str, Any], filters: ReportFilter
    ) -> list[ReportSectionData]:
        return [
            ReportSectionData(
                section_type=ReportSection.OVERVIEW,
                title="Custom Report",
                metrics=self._aggregate_metrics(snapshots),
                order=0,
            ),
        ]

    # ── Helpers ──────────────────────────────────────────────────────────

    def _aggregate_metrics(self, snapshots: dict[str, Any]) -> dict[str, Any]:
        aggregated: dict[str, Any] = {}
        for snap in snapshots.values():
            if isinstance(snap, dict):
                for key, value in snap.get("summary_metrics", {}).items():
                    if isinstance(value, (int, float)):
                        aggregated[key] = aggregated.get(key, 0) + value
        return aggregated

    def _extract_findings(self, sections: list[ReportSectionData]) -> list[str]:
        findings: list[str] = []
        for section in sections:
            for finding in section.findings:
                findings.append(
                    f"[{finding.get('severity', 'INFO')}] {finding.get('description', '')}"
                )
        return findings

    def _generate_recommendations(
        self, sections: list[ReportSectionData], report_type: ReportType
    ) -> list[str]:
        recs: list[str] = []
        for section in sections:
            for finding in section.findings:
                severity = finding.get("severity", "INFO")
                desc = finding.get("description", "")
                if severity in ("HIGH", "CRITICAL"):
                    recs.append(f"URGENT: Investigate and resolve: {desc}")
                elif severity == "MEDIUM":
                    recs.append(f"Review: {desc}")
        if not recs:
            recs.append("No critical issues detected. Continue monitoring.")
        return recs

    def _generate_summary(
        self, sections: list[ReportSectionData], report_type: ReportType
    ) -> str:
        total_findings = sum(len(s.findings) for s in sections)
        total_metrics = sum(len(s.metrics) for s in sections)
        return (
            f"{report_type.value.replace('_', ' ').title()} report generated with "
            f"{len(sections)} sections, {total_metrics} metrics, and "
            f"{total_findings} findings."
        )

    def _default_title(self, report_type: ReportType) -> str:
        titles = {
            ReportType.EXECUTIVE_SUMMARY: "Executive Governance Summary",
            ReportType.COMPLIANCE_STATUS: "Compliance Status Report",
            ReportType.RISK_ASSESSMENT: "Risk Assessment Report",
            ReportType.AUDIT_FINDINGS: "Audit Findings Report",
            ReportType.OPERATIONAL_METRICS: "Operational Metrics Report",
            ReportType.COST_ANALYSIS: "Cost Analysis Report",
            ReportType.INCIDENT_REPORT: "Incident Report",
            ReportType.TREND_ANALYSIS: "Trend Analysis Report",
            ReportType.CUSTOM: "Custom Governance Report",
        }
        return titles.get(report_type, "Governance Report")

    def _default_description(self, report_type: ReportType) -> str:
        descriptions = {
            ReportType.EXECUTIVE_SUMMARY: "High-level overview of governance posture",
            ReportType.COMPLIANCE_STATUS: "Current compliance status across all frameworks",
            ReportType.RISK_ASSESSMENT: "Identified risks and their severity assessment",
            ReportType.AUDIT_FINDINGS: "Detailed audit findings and remediation status",
            ReportType.OPERATIONAL_METRICS: "Operational performance metrics and KPIs",
            ReportType.COST_ANALYSIS: "Cost breakdown and optimization opportunities",
            ReportType.INCIDENT_REPORT: "Active incidents and their resolution status",
            ReportType.TREND_ANALYSIS: "Historical trends and pattern analysis",
            ReportType.CUSTOM: "Custom governance report",
        }
        return descriptions.get(report_type, "Governance report")

    def _table_to_html(self, table: dict[str, Any]) -> str:
        headers = table.get("headers", [])
        rows = table.get("rows", [])
        parts = ["<table>"]
        if headers:
            parts.append("<tr>" + "".join(f"<th>{h}</th>" for h in headers) + "</tr>")
        for row in rows:
            parts.append("<tr>" + "".join(f"<td>{c}</td>" for c in row) + "</tr>")
        parts.append("</table>")
        return "".join(parts)

    def _table_to_markdown(self, table: dict[str, Any]) -> str:
        headers = table.get("headers", [])
        rows = table.get("rows", [])
        lines = []
        if headers:
            lines.append("| " + " | ".join(headers) + " |")
            lines.append("| " + " | ".join("---" for _ in headers) + " |")
        for row in rows:
            lines.append("| " + " | ".join(str(c) for c in row) + " |")
        lines.append("")
        return "\n".join(lines)

    # ── Scheduling ───────────────────────────────────────────────────────

    def create_schedule(self, schedule: ReportSchedule) -> ReportSchedule:
        self._schedules[schedule.schedule_id] = schedule
        return schedule

    def get_schedule(self, schedule_id: str) -> Optional[ReportSchedule]:
        return self._schedules.get(schedule_id)

    def list_schedules(
        self, report_type: Optional[ReportType] = None, enabled_only: bool = False
    ) -> list[ReportSchedule]:
        results = list(self._schedules.values())
        if report_type:
            results = [s for s in results if s.report_type == report_type]
        if enabled_only:
            results = [s for s in results if s.enabled]
        return results

    def delete_schedule(self, schedule_id: str) -> bool:
        return self._schedules.pop(schedule_id, None) is not None

    # ── Templates ────────────────────────────────────────────────────────

    def register_template(self, template_id: str, config: dict[str, Any]) -> None:
        self._templates[template_id] = config

    def get_template(self, template_id: str) -> Optional[dict[str, Any]]:
        return self._templates.get(template_id)

    def list_templates(self) -> list[str]:
        return list(self._templates.keys())

    # ── History ──────────────────────────────────────────────────────────

    def _add_to_history(self, report: GeneratedReport) -> None:
        self._report_history.append(report)
        if len(self._report_history) > self._max_history:
            self._report_history = self._report_history[-self._max_history:]

    def get_history(
        self, report_type: Optional[ReportType] = None, limit: int = 20
    ) -> list[GeneratedReport]:
        results = self._report_history
        if report_type:
            results = [r for r in results if r.report_type == report_type]
        return results[-limit:]

    def get_report_by_id(self, report_id: str) -> Optional[GeneratedReport]:
        for report in self._report_history:
            if report.report_id == report_id:
                return report
        return None


class ReportBuilder:
    """
    Fluent builder for constructing report definitions.
    """

    def __init__(self):
        self._name = ""
        self._description = ""
        self._category = "general"
        self._format = ReportFormat.HTML
        self._frequency = ReportFrequency.ON_DEMAND
        self._data_sources: list[DataSourceType] = []
        self._sections: list[dict[str, Any]] = []
        self._filters: list[Any] = []
        self._parameters: dict[str, Any] = {}
        self._template = ""
        self._recipients: list[str] = []
        self._tags: list[str] = []
        self._owner = ""

    def name(self, name: str) -> ReportBuilder:
        self._name = name
        return self

    def description(self, desc: str) -> ReportBuilder:
        self._description = desc
        return self

    def category(self, category: str) -> ReportBuilder:
        self._category = category
        return self

    def format(self, fmt: ReportFormat) -> ReportBuilder:
        self._format = fmt
        return self

    def frequency(self, freq: ReportFrequency) -> ReportBuilder:
        self._frequency = freq
        return self

    def data_source(self, source: DataSourceType) -> ReportBuilder:
        self._data_sources.append(source)
        return self

    def section(self, title: str, section_type: str = "text", **kwargs) -> ReportBuilder:
        self._sections.append({
            "title": title,
            "type": section_type,
            **kwargs,
        })
        return self

    def filter(self, criteria: Any) -> ReportBuilder:
        self._filters.append(criteria)
        return self

    def parameter(self, key: str, value: Any) -> ReportBuilder:
        self._parameters[key] = value
        return self

    def template(self, template: str) -> ReportBuilder:
        self._template = template
        return self

    def recipients(self, recipients: list[str]) -> ReportBuilder:
        self._recipients = recipients
        return self

    def tags(self, tags: list[str]) -> ReportBuilder:
        self._tags = tags
        return self

    def owner(self, owner: str) -> ReportBuilder:
        self._owner = owner
        return self

    def build(self) -> ReportDefinition:
        import uuid
        return ReportDefinition(
            id=str(uuid.uuid4())[:12],
            name=self._name,
            description=self._description,
            category=self._category,
            report_format=self._format,
            frequency=self._frequency,
            data_sources=self._data_sources,
            sections=self._sections,
            filters=self._filters,
            parameters=self._parameters,
            template=self._template,
            recipients=self._recipients,
            tags=self._tags,
            owner=self._owner,
        )


class ReportExporter:
    """
    Exports reports to various file formats and destinations.
    """

    def __init__(self):
        self._export_handlers: dict[ReportFormat, Any] = {}

    def register_handler(self, fmt: ReportFormat, handler: Any) -> None:
        self._export_handlers[fmt] = handler

    def export(self, output: ReportOutput, file_path: str) -> str:
        fmt = output.format
        content = output.content
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return file_path

    def export_to_json(self, output: ReportOutput) -> str:
        return json.dumps({
            "output_id": output.output_id,
            "report_id": output.report_id,
            "report_name": output.report_name,
            "format": output.format.value,
            "content": output.content,
            "generated_at": output.generated_at,
            "success": output.success,
            "metadata": output.metadata,
        }, indent=2, default=str)

    def export_summary(self, outputs: list[ReportOutput]) -> str:
        lines = [
            "# Report Generation Summary",
            "",
            f"**Total Reports:** {len(outputs)}",
            f"**Successful:** {sum(1 for o in outputs if o.success)}",
            f"**Failed:** {sum(1 for o in outputs if not o.success)}",
            "",
            "| Report | Format | Status | Generated |",
            "|--------|--------|--------|-----------|",
        ]
        for o in outputs:
            status = "OK" if o.success else "FAIL"
            lines.append(f"| {o.report_name} | {o.format.value} | {status} | {o.generated_at} |")
        return "\n".join(lines)
