"""Reporting Agent - Generates marketing performance reports."""

from __future__ import annotations

import csv
import io
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any

import structlog

from analytics.agents.attribution_engine import AggregatedAttribution
from analytics.agents.data_collection import CollectionResult
from analytics.agents.predictive_analytics import ForecastResult

logger = structlog.get_logger(__name__)


class ReportFormat(StrEnum):
    """Supported report formats."""

    JSON = "json"
    CSV = "csv"
    PDF = "pdf"


class ReportType(StrEnum):
    """Supported report types."""

    PERFORMANCE = "performance"
    ATTRIBUTION = "attribution"
    FORECAST = "forecast"
    COMPREHENSIVE = "comprehensive"


@dataclass
class ReportSection:
    """A section within a report."""

    title: str
    content: dict[str, Any]
    summary: str = ""


@dataclass
class Report:
    """A generated marketing report."""

    report_id: str
    report_type: ReportType
    format: ReportFormat
    title: str
    generated_at: datetime
    period_start: datetime
    period_end: datetime
    sections: list[ReportSection] = field(default_factory=list)
    summary: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


class ReportingAgent:
    """Agent for generating marketing performance reports."""

    def __init__(self) -> None:
        self.logger = logger.bind(agent="reporting")
        self._reports: dict[str, Report] = {}

    def generate_performance_report(
        self,
        collection_results: list[CollectionResult],
        period_start: datetime,
        period_end: datetime,
        format: ReportFormat = ReportFormat.JSON,
    ) -> Report:
        """Generate a marketing performance report."""
        self.logger.info(
            "generating_performance_report",
            format=format.value,
            period_start=period_start.isoformat(),
            period_end=period_end.isoformat(),
        )

        total_events = sum(r.total_count for r in collection_results)
        successful_sources = sum(1 for r in collection_results if r.success)
        failed_sources = len(collection_results) - successful_sources

        # Aggregate metrics by source
        source_metrics: dict[str, dict[str, Any]] = {}
        for result in collection_results:
            source_metrics[result.source.value] = {
                "total_events": result.total_count,
                "success": result.success,
                "error": result.error_message,
            }

        # Calculate revenue by source
        revenue_by_source: dict[str, float] = {}
        for result in collection_results:
            revenue = sum(e.revenue for e in result.events)
            revenue_by_source[result.source.value] = revenue

        sections = [
            ReportSection(
                title="Executive Summary",
                content={
                    "total_events": total_events,
                    "sources_successful": successful_sources,
                    "sources_failed": failed_sources,
                    "total_revenue": sum(revenue_by_source.values()),
                },
                summary=f"Collected {total_events} events from {len(collection_results)} sources.",
            ),
            ReportSection(
                title="Source Performance",
                content=source_metrics,
                summary="Breakdown of data collection by source.",
            ),
            ReportSection(
                title="Revenue Analysis",
                content=revenue_by_source,
                summary="Revenue attributed to each data source.",
            ),
        ]

        report = Report(
            report_id=f"perf_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            report_type=ReportType.PERFORMANCE,
            format=format,
            title="Marketing Performance Report",
            generated_at=datetime.utcnow(),
            period_start=period_start,
            period_end=period_end,
            sections=sections,
            summary=f"Performance report for {period_start.date()} to {period_end.date()}",
        )

        self._reports[report.report_id] = report
        return report

    def generate_attribution_report(
        self,
        attribution_results: dict[str, AggregatedAttribution],
        period_start: datetime,
        period_end: datetime,
        format: ReportFormat = ReportFormat.JSON,
    ) -> Report:
        """Generate an attribution analysis report."""
        self.logger.info("generating_attribution_report", format=format.value)

        sections: list[ReportSection] = []
        for model_name, result in attribution_results.items():
            sections.append(
                ReportSection(
                    title=f"Attribution Model: {model_name}",
                    content={
                        "channel_totals": result.channel_totals,
                        "channel_percentages": result.channel_percentages,
                        "total_revenue": result.total_revenue,
                        "journey_count": result.journey_count,
                        "converted_journeys": result.converted_journeys,
                    },
                    summary=f"Total attributed revenue: ${result.total_revenue:,.2f}",
                )
            )

        report = Report(
            report_id=f"attr_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            report_type=ReportType.ATTRIBUTION,
            format=format,
            title="Attribution Analysis Report",
            generated_at=datetime.utcnow(),
            period_start=period_start,
            period_end=period_end,
            sections=sections,
            summary="Multi-touch attribution analysis across all models.",
        )

        self._reports[report.report_id] = report
        return report

    def generate_forecast_report(
        self,
        forecast_result: ForecastResult,
        period_start: datetime,
        period_end: datetime,
        format: ReportFormat = ReportFormat.JSON,
    ) -> Report:
        """Generate a forecasting report."""
        self.logger.info("generating_forecast_report", format=format.value)

        total_predicted = sum(p.predicted_value for p in forecast_result.points)
        avg_daily = total_predicted / len(forecast_result.points) if forecast_result.points else 0

        sections = [
            ReportSection(
                title="Forecast Summary",
                content={
                    "model_type": forecast_result.model_type.value,
                    "horizon_days": forecast_result.forecast_horizon_days,
                    "total_predicted_revenue": total_predicted,
                    "average_daily_revenue": avg_daily,
                    "confidence_metrics": forecast_result.metrics,
                },
                summary=(
                    f"Predicted ${total_predicted:,.2f} over "
                    f"{forecast_result.forecast_horizon_days} days."
                ),
            ),
            ReportSection(
                title="Daily Forecast",
                content={
                    "points": [
                        {
                            "date": p.date.isoformat(),
                            "predicted": p.predicted_value,
                            "lower_bound": p.lower_bound,
                            "upper_bound": p.upper_bound,
                        }
                        for p in forecast_result.points
                    ]
                },
                summary="Day-by-day revenue forecast with confidence intervals.",
            ),
        ]

        report = Report(
            report_id=f"fc_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            report_type=ReportType.FORECAST,
            format=format,
            title="Revenue Forecast Report",
            generated_at=datetime.utcnow(),
            period_start=period_start,
            period_end=period_end,
            sections=sections,
            summary=f"Revenue forecast for next {forecast_result.forecast_horizon_days} days.",
        )

        self._reports[report.report_id] = report
        return report

    def export_report(self, report: Report) -> str:
        """Export a report to the specified format."""
        if report.format == ReportFormat.JSON:
            return self._export_json(report)
        elif report.format == ReportFormat.CSV:
            return self._export_csv(report)
        elif report.format == ReportFormat.PDF:
            return self._export_pdf(report)
        else:
            raise ValueError(f"Unsupported format: {report.format}")

    def _export_json(self, report: Report) -> str:
        """Export report as JSON."""
        data = {
            "report_id": report.report_id,
            "report_type": report.report_type.value,
            "format": report.format.value,
            "title": report.title,
            "generated_at": report.generated_at.isoformat(),
            "period_start": report.period_start.isoformat(),
            "period_end": report.period_end.isoformat(),
            "summary": report.summary,
            "sections": [
                {
                    "title": s.title,
                    "content": s.content,
                    "summary": s.summary,
                }
                for s in report.sections
            ],
            "metadata": report.metadata,
        }
        return json.dumps(data, indent=2, default=str)

    def _export_csv(self, report: Report) -> str:
        """Export report as CSV."""
        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow(["Report ID", report.report_id])
        writer.writerow(["Type", report.report_type.value])
        writer.writerow(["Title", report.title])
        writer.writerow(["Generated At", report.generated_at.isoformat()])
        writer.writerow([])
        writer.writerow(["Section", "Summary"])

        for section in report.sections:
            writer.writerow([section.title, section.summary])

        return output.getvalue()

    def _export_pdf(self, report: Report) -> str:
        """Export report as PDF (placeholder - returns structured text)."""
        # In production, use a library like reportlab or weasyprint
        lines = [
            f"# {report.title}",
            "",
            f"**Report ID:** {report.report_id}",
            f"**Type:** {report.report_type.value}",
            f"**Generated:** {report.generated_at.isoformat()}",
            f"**Period:** {report.period_start.date()} to {report.period_end.date()}",
            "",
            "## Summary",
            "",
            report.summary,
            "",
        ]
        for section in report.sections:
            lines.extend(
                [
                    f"## {section.title}",
                    "",
                    section.summary,
                    "",
                    "```json",
                    json.dumps(section.content, indent=2, default=str),
                    "```",
                    "",
                ]
            )
        return "\n".join(lines)

    def get_report(self, report_id: str) -> Report | None:
        """Retrieve a previously generated report."""
        return self._reports.get(report_id)

    def list_reports(
        self,
        report_type: ReportType | None = None,
    ) -> list[Report]:
        """List all generated reports, optionally filtered by type."""
        reports = list(self._reports.values())
        if report_type:
            reports = [r for r in reports if r.report_type == report_type]
        return sorted(reports, key=lambda r: r.generated_at, reverse=True)
