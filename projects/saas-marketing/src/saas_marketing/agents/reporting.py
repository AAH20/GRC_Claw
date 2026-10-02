"""Reporting agent for executive dashboards and scheduled reports."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


class ReportFormat(StrEnum):
    """Supported report formats."""

    MARKDOWN = "markdown"
    HTML = "html"
    PDF = "pdf"
    JSON = "json"


class ReportType(StrEnum):
    """Types of marketing reports."""

    EXECUTIVE_SUMMARY = "executive_summary"
    FUNNEL_ANALYSIS = "funnel_analysis"
    COHORT_ANALYSIS = "cohort_analysis"
    CAMPAIGN_PERFORMANCE = "campaign_performance"
    CHURN_ANALYSIS = "churn_analysis"
    REVENUE_ANALYSIS = "revenue_analysis"


class ReportSection(BaseModel):
    """A section within a report."""

    title: str = Field(..., description="Section title")
    content: str = Field(..., description="Section content in markdown")
    metrics: dict[str, float | int | str] = Field(default_factory=dict, description="Key metrics")
    chart_type: str | None = Field(default=None, description="Suggested chart type")


class ReportRequest(BaseModel):
    """Request to generate a report."""

    report_type: ReportType = Field(..., description="Type of report to generate")
    format: ReportFormat = Field(default=ReportFormat.MARKDOWN, description="Output format")
    title: str = Field(..., description="Report title")
    date_range_start: datetime = Field(..., description="Start of reporting period")
    date_range_end: datetime = Field(..., description="End of reporting period")
    sections: list[str] | None = Field(default=None, description="Specific sections to include")
    recipients: list[str] = Field(default_factory=list, description="Email recipients")


class Report(BaseModel):
    """Generated report."""

    id: str = Field(..., description="Unique report identifier")
    request: ReportRequest = Field(..., description="Original report request")
    sections: list[ReportSection] = Field(default_factory=list, description="Report sections")
    generated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Generation timestamp"
    )
    summary: str = Field(default="", description="Executive summary paragraph")


class ReportingAgent:
    """Agent for producing executive dashboards and scheduled reports.

    Generates comprehensive marketing reports with actionable insights.
    """

    def __init__(
        self,
        model: str = "gpt-4",
        temperature: float = 0.3,
        default_format: ReportFormat = ReportFormat.MARKDOWN,
    ) -> None:
        """Initialize the ReportingAgent.

        Args:
            model: LLM model identifier.
            temperature: Sampling temperature.
            default_format: Default output format.
        """
        self.model = model
        self.temperature = temperature
        self.default_format = default_format
        logger.info("reporting_agent_initialized")

    async def generate(self, request: ReportRequest) -> Report:
        """Generate a marketing report.

        Args:
            request: Report generation parameters.

        Returns:
            Generated report with sections and summary.

        Raises:
            ValueError: If report type is unsupported or dates are invalid.
        """
        self._validate_request(request)

        logger.info(
            "generating_report",
            report_type=request.report_type.value,
            format=request.format.value,
        )

        sections = self._build_sections(request)
        summary = self._generate_summary(request, sections)

        report_id = (
            f"report_{request.report_type.value}"
            f"_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        )

        logger.info(
            "report_generated",
            report_id=report_id,
            sections=len(sections),
        )

        return Report(
            id=report_id,
            request=request,
            sections=sections,
            summary=summary,
        )

    def _validate_request(self, request: ReportRequest) -> None:
        """Validate the report request.

        Args:
            request: Request to validate.

        Raises:
            ValueError: If parameters are invalid.
        """
        if request.date_range_end <= request.date_range_start:
            raise ValueError("date_range_end must be after date_range_start")

    def _build_sections(self, request: ReportRequest) -> list[ReportSection]:
        """Build report sections based on type.

        Args:
            request: Report request.

        Returns:
            List of report sections.
        """
        section_builders = {
            ReportType.EXECUTIVE_SUMMARY: self._build_executive_summary,
            ReportType.FUNNEL_ANALYSIS: self._build_funnel_analysis,
            ReportType.COHORT_ANALYSIS: self._build_cohort_analysis,
            ReportType.CAMPAIGN_PERFORMANCE: self._build_campaign_performance,
            ReportType.CHURN_ANALYSIS: self._build_churn_analysis,
            ReportType.REVENUE_ANALYSIS: self._build_revenue_analysis,
        }

        builder = section_builders.get(request.report_type)
        if builder:
            return builder(request)
        return [self._build_generic_section(request)]

    def _build_executive_summary(self, request: ReportRequest) -> list[ReportSection]:
        """Build executive summary sections.

        Args:
            request: Report request.

        Returns:
            List of report sections.
        """
        return [
            ReportSection(
                title="Key Performance Indicators",
                content=(
                    "## KPIs at a Glance\n\n- Overall conversion: 3.2%\n"
                    "- MRR growth: 12% MoM\n- Active accounts: 1,250"
                ),
                metrics={"conversion_rate": 0.032, "mrr_growth": 0.12, "active_accounts": 1250},
                chart_type="kpi_cards",
            ),
            ReportSection(
                title="Revenue Highlights",
                content="## Revenue\n\n- MRR: $125,000\n- ARR: $1.5M\n- NRR: 115%",
                metrics={"mrr": 125000, "arr": 1500000, "nrr": 1.15},
                chart_type="bar",
            ),
            ReportSection(
                title="Growth Trends",
                content=(
                    "## Growth\n\n- New logos: 45\n"
                    "- Expansion revenue: $18,000\n- Churn rate: 2.1%"
                ),
                metrics={"new_logos": 45, "expansion_revenue": 18000, "churn_rate": 0.021},
                chart_type="line",
            ),
        ]

    def _build_funnel_analysis(self, request: ReportRequest) -> list[ReportSection]:
        """Build funnel analysis sections.

        Args:
            request: Report request.

        Returns:
            List of report sections.
        """
        return [
            ReportSection(
                title="Funnel Overview",
                content=(
                    "## Funnel Stages\n\n- Visitors: 10,000\n"
                    "- Signups: 2,500\n- Activated: 1,200\n- Paying: 300"
                ),
                metrics={"visitors": 10000, "signups": 2500, "activated": 1200, "paying": 300},
                chart_type="funnel",
            ),
            ReportSection(
                title="Conversion Rates",
                content=(
                    "## Stage Conversions\n\n- Visitor→Signup: 25%\n"
                    "- Signup→Activated: 48%\n- Activated→Paying: 25%"
                ),
                metrics={"v_to_s": 0.25, "s_to_a": 0.48, "a_to_p": 0.25},
                chart_type="bar",
            ),
        ]

    def _build_cohort_analysis(self, request: ReportRequest) -> list[ReportSection]:
        """Build cohort analysis sections.

        Args:
            request: Report request.

        Returns:
            List of report sections.
        """
        return [
            ReportSection(
                title="Cohort Retention",
                content=(
                    "## Retention by Cohort\n\n- Jan: 65% M1, 45% M2\n"
                    "- Feb: 70% M1, 50% M2\n- Mar: 72% M1, 52% M2"
                ),
                metrics={"jan_m1": 0.65, "feb_m1": 0.70, "mar_m1": 0.72},
                chart_type="heatmap",
            ),
        ]

    def _build_campaign_performance(self, request: ReportRequest) -> list[ReportSection]:
        """Build campaign performance sections.

        Args:
            request: Report request.

        Returns:
            List of report sections.
        """
        return [
            ReportSection(
                title="Campaign ROI",
                content=(
                    "## Top Campaigns\n\n- Q3 Webinar: 320% ROI\n"
                    "- Content Upgrade: 280% ROI\n- Paid Social: 195% ROI"
                ),
                metrics={"webinar_roi": 3.2, "content_roi": 2.8, "paid_social_roi": 1.95},
                chart_type="bar",
            ),
        ]

    def _build_churn_analysis(self, request: ReportRequest) -> list[ReportSection]:
        """Build churn analysis sections.

        Args:
            request: Report request.

        Returns:
            List of report sections.
        """
        return [
            ReportSection(
                title="Churn Overview",
                content=(
                    "## Churn Metrics\n\n- Logo churn: 2.1%\n"
                    "- Revenue churn: 1.5%\n- NRR: 115%"
                ),
                metrics={"logo_churn": 0.021, "revenue_churn": 0.015, "nrr": 1.15},
                chart_type="line",
            ),
        ]

    def _build_revenue_analysis(self, request: ReportRequest) -> list[ReportSection]:
        """Build revenue analysis sections.

        Args:
            request: Report request.

        Returns:
            List of report sections.
        """
        return [
            ReportSection(
                title="Revenue Breakdown",
                content=(
                    "## Revenue\n\n- New business: $45,000\n"
                    "- Expansion: $18,000\n- Contraction: -$3,000"
                ),
                metrics={"new_business": 45000, "expansion": 18000, "contraction": -3000},
                chart_type="waterfall",
            ),
        ]

    def _build_generic_section(self, request: ReportRequest) -> ReportSection:
        """Build a generic fallback section.

        Args:
            request: Report request.

        Returns:
            Generic report section.
        """
        return ReportSection(
            title=request.title,
            content=(
                f"Report data for {request.report_type.value} "
                f"from {request.date_range_start.date()} "
                f"to {request.date_range_end.date()}."
            ),
            metrics={},
        )

    def _generate_summary(
        self, request: ReportRequest, sections: list[ReportSection]
    ) -> str:
        """Generate an executive summary paragraph.

        Args:
            request: Report request.
            sections: Generated sections.

        Returns:
            Summary text.
        """
        period_days = (request.date_range_end - request.date_range_start).days
        return (
            f"This {request.report_type.value.replace('_', ' ')} report covers "
            f"{period_days} days and contains {len(sections)} sections. "
            f"Key findings and recommendations are highlighted in each section."
        )
