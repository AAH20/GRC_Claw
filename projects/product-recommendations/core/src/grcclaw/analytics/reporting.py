"""
Executive Reporting — board-ready report generation for GRC_Claw.

Generates compliance summaries, risk dashboards, program status reports,
regulatory evidence packs, and transparency reports with RAG status,
trend charts, and material risk identification.
"""

from __future__ import annotations

from typing import Any

from .engine import AnalyticsEngine
from .models import (
    DashboardLayer,
    ExecutiveReport,
    MetricCategory,
    MetricSnapshot,
    RAGStatus,
    ReportFrequency,
    ReportSection,
    ReportType,
)


class ReportTemplate:
    """Base class for report templates."""

    def __init__(
        self,
        report_type: ReportType,
        title: str,
        frequency: ReportFrequency,
        audience: list[str],
    ):
        self.report_type = report_type
        self.title = title
        self.frequency = frequency
        self.audience = audience

    def generate(
        self,
        snapshots: list[MetricSnapshot],
        period: str = "",
        engine: AnalyticsEngine | None = None,
    ) -> ExecutiveReport:
        raise NotImplementedError


class BoardComplianceSummary(ReportTemplate):
    """Quarterly board compliance summary report."""

    def __init__(self):
        super().__init__(
            ReportType.BOARD_COMPLIANCE_SUMMARY,
            "AI Governance Board Report",
            ReportFrequency.QUARTERLY,
            ["Board", "C-Suite"],
        )

    def generate(
        self,
        snapshots: list[MetricSnapshot],
        period: str = "",
        engine: AnalyticsEngine | None = None,
    ) -> ExecutiveReport:
        engine = engine or AnalyticsEngine()

        # Executive summary section
        exec_kpi = engine.compute_kpi_summary(DashboardLayer.EXECUTIVE, snapshots, period)
        summary_text = self._build_executive_summary(exec_kpi, snapshots)

        # Compliance scores by framework
        framework_scores = self._compute_framework_scores(snapshots)

        # Material risks
        material_risks = self._identify_material_risks(snapshots)

        # Decisions required
        decisions = self._identify_decisions(snapshots)

        # Trend analysis
        trend_charts = self._build_trend_charts(snapshots)

        # Build sections
        sections = [
            ReportSection(
                title="Executive Summary",
                content=summary_text,
                order=1,
                insights=[
                    f"Overall compliance score: {exec_kpi.overall_score}%",
                    f"Metrics at green: {exec_kpi.green_count}/{exec_kpi.total_metrics}",
                    f"Metrics requiring attention: {exec_kpi.red_count + exec_kpi.critical_count}",
                ],
            ),
            ReportSection(
                title="Compliance Score by Framework",
                tables=[{"framework_scores": framework_scores}],
                charts=[{"type": "bar", "data": framework_scores}],
                order=2,
            ),
            ReportSection(
                title="Material Risks",
                tables=[{"material_risks": material_risks}],
                insights=[f"{len(material_risks)} material risk(s) identified"],
                order=3,
            ),
            ReportSection(
                title="Decisions Required",
                tables=[{"decisions": decisions}],
                order=4,
            ),
            ReportSection(
                title="Trend Analysis",
                charts=trend_charts,
                order=5,
            ),
        ]

        # Overall RAG status
        if exec_kpi.critical_count > 0:
            overall_rag = RAGStatus.CRITICAL
        elif exec_kpi.red_count > 0:
            overall_rag = RAGStatus.RED
        elif exec_kpi.amber_count > 0:
            overall_rag = RAGStatus.AMBER
        else:
            overall_rag = RAGStatus.GREEN

        return ExecutiveReport(
            report_type=self.report_type,
            title=f"{self.title} — {period}" if period else self.title,
            frequency=self.frequency,
            audience=self.audience,
            period=period,
            sections=sections,
            summary=summary_text,
            overall_rag_status=overall_rag,
            compliance_scores={fs["framework"]: fs["score"] for fs in framework_scores},
            material_risks=material_risks,
            decisions_required=decisions,
            trend_charts=trend_charts,
        )

    def _build_executive_summary(
        self, kpi, snapshots: list[MetricSnapshot]
    ) -> str:
        lines = [
            f"Overall Compliance Score: {kpi.overall_score}%",
            f"Systems Governed: {kpi.total_metrics} metrics tracked",
            f"Green: {kpi.green_count} | Amber: {kpi.amber_count} | Red: {kpi.red_count} | Critical: {kpi.critical_count}",
        ]
        if kpi.top_risks:
            lines.append(f"Top Risk: {kpi.top_risks[0]['name']} ({kpi.top_risks[0]['rag_status']})")
        return "\n".join(lines)

    def _compute_framework_scores(
        self, snapshots: list[MetricSnapshot]
    ) -> list[dict[str, Any]]:
        frameworks: dict[str, list[float]] = {}
        for s in snapshots:
            fw = self._metric_to_framework(s.metric_id)
            if fw:
                frameworks.setdefault(fw, []).append(s.current_value)

        result = []
        for fw, values in frameworks.items():
            avg = round(sum(values) / len(values), 1) if values else 0.0
            result.append({"framework": fw, "score": avg, "metric_count": len(values)})
        return sorted(result, key=lambda x: x["score"], reverse=True)

    def _metric_to_framework(self, metric_id: str) -> str | None:
        mapping = {
            "UC1-001": "ISO 42001", "UC1-002": "NIST AI RMF", "UC1-003": "NIST AI RMF",
            "UC1-004": "ISO 42001", "UC1-005": "EU AI Act",
            "UC2-001": "NIST AI RMF", "UC2-002": "NIST AI RMF", "UC2-003": "EU AI Act",
            "UC2-004": "NIST AI RMF", "UC2-005": "ISO 42001", "UC2-006": "ISO 42001",
            "UC3-001": "EU AI Act", "UC3-002": "EU AI Act", "UC3-003": "EU AI Act",
            "UC3-004": "EU AI Act", "UC3-005": "EU AI Act",
            "UC4-001": "EU AI Act", "UC4-002": "EU AI Act", "UC4-003": "EU AI Act",
            "UC4-004": "EU AI Act", "UC4-005": "NIST AI RMF", "UC4-006": "NIST AI RMF",
            "UC5-001": "NIST AI RMF", "UC5-002": "NIST AI RMF", "UC5-003": "ISO 42001",
            "UC5-004": "ISO 42001", "UC5-005": "ISO 42001",
            "UC6-001": "EU AI Act", "UC6-002": "EU AI Act", "UC6-003": "EU AI Act",
            "UC6-004": "EU AI Act",
            "UC7-001": "NIST AI RMF", "UC7-002": "NIST AI RMF", "UC7-003": "NIST AI RMF",
            "UC7-004": "NIST AI RMF", "UC7-005": "ISO 42001",
            "UC8-001": "EU AI Act", "UC8-002": "EU AI Act", "UC8-003": "EU AI Act",
            "UC8-004": "NIST AI RMF",
        }
        return mapping.get(metric_id)

    def _identify_material_risks(
        self, snapshots: list[MetricSnapshot]
    ) -> list[dict[str, Any]]:
        risks = []
        for s in snapshots:
            if s.rag_status in (RAGStatus.RED, RAGStatus.CRITICAL):
                risks.append({
                    "metric_id": s.metric_id,
                    "name": s.name,
                    "category": s.category.value,
                    "value": s.current_value,
                    "target": s.target,
                    "status": s.rag_status.value,
                    "trend": s.trend_direction.value,
                    "severity": "critical" if s.rag_status == RAGStatus.CRITICAL else "high",
                })
        return sorted(risks, key=lambda x: x["value"], reverse=True)

    def _identify_decisions(
        self, snapshots: list[MetricSnapshot]
    ) -> list[dict[str, Any]]:
        decisions = []
        for s in snapshots:
            if s.escalation_required:
                decisions.append({
                    "metric_id": s.metric_id,
                    "name": s.name,
                    "escalation_tier": s.escalation_tier.value if s.escalation_tier else None,
                    "action": f"Review {s.name} — status: {s.rag_status.value}",
                    "owner": s.owner,
                })
        return decisions

    def _build_trend_charts(
        self, snapshots: list[MetricSnapshot]
    ) -> list[dict[str, Any]]:
        charts = []
        for s in snapshots:
            if s.history and len(s.history) >= 2:
                charts.append({
                    "metric_id": s.metric_id,
                    "name": s.name,
                    "type": "line",
                    "data_points": len(s.history),
                    "current": s.current_value,
                    "previous": s.previous_value,
                    "trend": s.trend_direction.value,
                })
        return charts


class RegulatoryEvidencePack(ReportTemplate):
    """On-demand regulatory evidence pack."""

    def __init__(self):
        super().__init__(
            ReportType.REGULATORY_EVIDENCE_PACK,
            "Regulatory Evidence Pack",
            ReportFrequency.ON_DEMAND,
            ["Regulators", "Auditors"],
        )

    def generate(
        self,
        snapshots: list[MetricSnapshot],
        period: str = "",
        engine: AnalyticsEngine | None = None,
    ) -> ExecutiveReport:
        # Group metrics by framework
        framework_metrics: dict[str, list[MetricSnapshot]] = {}
        for s in snapshots:
            fw = self._metric_to_framework(s.metric_id)
            if fw:
                framework_metrics.setdefault(fw, []).append(s)

        sections = []
        for fw, metrics in sorted(framework_metrics.items()):
            sections.append(ReportSection(
                title=f"{fw} Evidence",
                metrics=metrics,
                insights=[
                    f"{len(metrics)} metric(s) mapped to {fw}",
                    f"Compliance score: {round(sum(m.current_value for m in metrics) / len(metrics), 1)}%",
                ],
                order=len(sections) + 1,
            ))

        return ExecutiveReport(
            report_type=self.report_type,
            title=f"{self.title} — {period}" if period else self.title,
            frequency=self.frequency,
            audience=self.audience,
            period=period,
            sections=sections,
            summary=f"Evidence pack covering {len(framework_metrics)} framework(s)",
            overall_rag_status=self._compute_overall_rag(snapshots),
        )

    def _metric_to_framework(self, metric_id: str) -> str | None:
        mapping = {
            "UC1-001": "ISO 42001", "UC1-002": "NIST AI RMF", "UC1-003": "NIST AI RMF",
            "UC1-004": "ISO 42001", "UC1-005": "EU AI Act",
            "UC2-001": "NIST AI RMF", "UC2-002": "NIST AI RMF", "UC2-003": "EU AI Act",
            "UC2-004": "NIST AI RMF", "UC2-005": "ISO 42001", "UC2-006": "ISO 42001",
            "UC3-001": "EU AI Act", "UC3-002": "EU AI Act", "UC3-003": "EU AI Act",
            "UC3-004": "EU AI Act", "UC3-005": "EU AI Act",
            "UC4-001": "EU AI Act", "UC4-002": "EU AI Act", "UC4-003": "EU AI Act",
            "UC4-004": "EU AI Act", "UC4-005": "NIST AI RMF", "UC4-006": "NIST AI RMF",
            "UC5-001": "NIST AI RMF", "UC5-002": "NIST AI RMF", "UC5-003": "ISO 42001",
            "UC5-004": "ISO 42001", "UC5-005": "ISO 42001",
            "UC6-001": "EU AI Act", "UC6-002": "EU AI Act", "UC6-003": "EU AI Act",
            "UC6-004": "EU AI Act",
            "UC7-001": "NIST AI RMF", "UC7-002": "NIST AI RMF", "UC7-003": "NIST AI RMF",
            "UC7-004": "NIST AI RMF", "UC7-005": "ISO 42001",
            "UC8-001": "EU AI Act", "UC8-002": "EU AI Act", "UC8-003": "EU AI Act",
            "UC8-004": "NIST AI RMF",
        }
        return mapping.get(metric_id)

    def _compute_overall_rag(self, snapshots: list[MetricSnapshot]) -> RAGStatus:
        if any(s.rag_status == RAGStatus.CRITICAL for s in snapshots):
            return RAGStatus.CRITICAL
        if any(s.rag_status == RAGStatus.RED for s in snapshots):
            return RAGStatus.RED
        if any(s.rag_status == RAGStatus.AMBER for s in snapshots):
            return RAGStatus.AMBER
        return RAGStatus.GREEN


class ProgramStatusReport(ReportTemplate):
    """Monthly program status report for governance committee."""

    def __init__(self):
        super().__init__(
            ReportType.PROGRAM_STATUS_REPORT,
            "Program Status Report",
            ReportFrequency.MONTHLY,
            ["Governance Committee", "Risk Officers"],
        )

    def generate(
        self,
        snapshots: list[MetricSnapshot],
        period: str = "",
        engine: AnalyticsEngine | None = None,
    ) -> ExecutiveReport:
        engine = engine or AnalyticsEngine()
        program_kpi = engine.compute_kpi_summary(DashboardLayer.PROGRAM, snapshots, period)

        sections = [
            ReportSection(
                title="Program Overview",
                content=f"Overall program health: {program_kpi.overall_score}%",
                order=1,
            ),
            ReportSection(
                title="Control Status",
                tables=[{"controls": [
                    {"metric_id": s.metric_id, "name": s.name, "status": s.rag_status.value}
                    for s in snapshots
                ]}],
                order=2,
            ),
            ReportSection(
                title="Exception Exposure",
                insights=[f"{program_kpi.red_count + program_kpi.critical_count} metric(s) require attention"],
                order=3,
            ),
            ReportSection(
                title="Remediation Progress",
                tables=[{"remediation": [
                    {"metric_id": s.metric_id, "name": s.name, "value": s.current_value, "target": s.target}
                    for s in snapshots if s.category == MetricCategory.REMEDIATION_IMPROVEMENT
                ]}],
                order=4,
            ),
        ]

        return ExecutiveReport(
            report_type=self.report_type,
            title=f"{self.title} — {period}" if period else self.title,
            frequency=self.frequency,
            audience=self.audience,
            period=period,
            sections=sections,
            summary=f"Program health: {program_kpi.overall_score}% | Green: {program_kpi.green_count} | Red: {program_kpi.red_count}",
            overall_rag_status=RAGStatus.RED if program_kpi.critical_count > 0 else RAGStatus.AMBER if program_kpi.red_count > 0 else RAGStatus.GREEN,
        )


class TransparencyReport(ReportTemplate):
    """Annual public transparency report."""

    def __init__(self):
        super().__init__(
            ReportType.TRANSPARENCY_REPORT,
            "AI Governance Transparency Report",
            ReportFrequency.ANNUALLY,
            ["Public"],
        )

    def generate(
        self,
        snapshots: list[MetricSnapshot],
        period: str = "",
        engine: AnalyticsEngine | None = None,
    ) -> ExecutiveReport:
        # Public-facing: only high-level metrics
        public_metrics = [
            s for s in snapshots
            if s.category in (
                MetricCategory.RISK_COMPLIANCE,
                MetricCategory.CULTURE_TRAINING_ETHICS,
            )
        ]

        sections = [
            ReportSection(
                title="AI Governance Commitments",
                content="Our commitment to responsible AI governance",
                order=1,
            ),
            ReportSection(
                title="Incident Disclosures",
                tables=[{"incidents": [
                    {"metric_id": s.metric_id, "name": s.name, "value": s.current_value}
                    for s in snapshots if s.category == MetricCategory.INCIDENT_MANAGEMENT
                ]}],
                order=2,
            ),
            ReportSection(
                title="Compliance Summary",
                insights=[
                    f"Overall compliance: {round(sum(s.current_value for s in public_metrics) / len(public_metrics), 1)}%" if public_metrics else "No data",
                ],
                order=3,
            ),
        ]

        return ExecutiveReport(
            report_type=self.report_type,
            title=f"{self.title} — {period}" if period else self.title,
            frequency=self.frequency,
            audience=self.audience,
            period=period,
            sections=sections,
            summary="Annual transparency report on AI governance practices",
            overall_rag_status=RAGStatus.GREEN,
        )


class ReportGenerator:
    """
    Main report generator. Creates executive reports from metric snapshots.
    """

    def __init__(self, engine: AnalyticsEngine | None = None):
        self.engine = engine or AnalyticsEngine()
        self.templates: dict[ReportType, ReportTemplate] = {
            ReportType.BOARD_COMPLIANCE_SUMMARY: BoardComplianceSummary(),
            ReportType.REGULATORY_EVIDENCE_PACK: RegulatoryEvidencePack(),
            ReportType.PROGRAM_STATUS_REPORT: ProgramStatusReport(),
            ReportType.TRANSPARENCY_REPORT: TransparencyReport(),
        }

    def generate_report(
        self,
        report_type: ReportType,
        snapshots: list[MetricSnapshot],
        period: str = "",
    ) -> ExecutiveReport:
        """Generate a report of the specified type."""
        template = self.templates.get(report_type)
        if not template:
            raise ValueError(f"Unknown report type: {report_type}")
        return template.generate(snapshots, period, self.engine)

    def generate_board_summary(
        self,
        snapshots: list[MetricSnapshot],
        period: str = "",
    ) -> ExecutiveReport:
        """Generate a board compliance summary."""
        return self.generate_report(ReportType.BOARD_COMPLIANCE_SUMMARY, snapshots, period)

    def generate_evidence_pack(
        self,
        snapshots: list[MetricSnapshot],
        period: str = "",
    ) -> ExecutiveReport:
        """Generate a regulatory evidence pack."""
        return self.generate_report(ReportType.REGULATORY_EVIDENCE_PACK, snapshots, period)

    def generate_program_status(
        self,
        snapshots: list[MetricSnapshot],
        period: str = "",
    ) -> ExecutiveReport:
        """Generate a program status report."""
        return self.generate_report(ReportType.PROGRAM_STATUS_REPORT, snapshots, period)

    def generate_transparency_report(
        self,
        snapshots: list[MetricSnapshot],
        period: str = "",
    ) -> ExecutiveReport:
        """Generate a transparency report."""
        return self.generate_report(ReportType.TRANSPARENCY_REPORT, snapshots, period)

    def list_available_reports(self) -> list[dict[str, str]]:
        """List all available report types."""
        return [
            {
                "type": rt.value,
                "title": template.title,
                "frequency": template.frequency.value,
                "audience": ", ".join(template.audience),
            }
            for rt, template in self.templates.items()
        ]
