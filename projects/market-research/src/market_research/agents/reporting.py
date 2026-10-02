"""Reporting Agent for generating structured market research reports."""

from __future__ import annotations

import asyncio
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING, Any

import structlog
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from market_research.agents.analysis import AnalysisResult

logger = structlog.get_logger(__name__)


class ReportFormat(StrEnum):
    """Supported report output formats."""

    JSON = "json"
    MARKDOWN = "markdown"
    PDF = "pdf"
    HTML = "html"


class ReportSection(BaseModel):
    """A section within a report."""

    title: str
    content: str
    order: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)


class ReportRequest(BaseModel):
    """Request to generate a market research report."""

    title: str
    analysis_result: AnalysisResult
    formats: list[ReportFormat] = Field(default_factory=lambda: [ReportFormat.MARKDOWN])
    include_visualizations: bool = True
    include_executive_summary: bool = True
    include_appendix: bool = False
    custom_sections: list[ReportSection] = Field(default_factory=list)
    output_dir: str = "outputs"


class ReportMetadata(BaseModel):
    """Metadata about a generated report."""

    report_id: str
    title: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    formats: list[ReportFormat]
    section_count: int
    word_count: int
    file_paths: dict[str, str] = Field(default_factory=dict)


class ReportResult(BaseModel):
    """Result of a report generation operation."""

    metadata: ReportMetadata
    content: dict[str, str] = Field(default_factory=dict)
    sections: list[ReportSection] = Field(default_factory=list)
    success: bool = True
    errors: list[str] = Field(default_factory=list)


class ReportingAgent:
    """Agent responsible for generating structured market research reports.

    This agent takes analysis results and produces professional reports
    in multiple formats (JSON, Markdown, PDF, HTML) with optional
    visualizations and custom sections.
    """

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize the Reporting Agent.

        Args:
            config: Optional configuration dictionary for the agent.
        """
        self.config = config or {}
        self.output_dir = Path(self.config.get("output_dir", "outputs"))
        self.template_dir = Path(self.config.get("template_dir", "templates"))
        logger.info("reporting_agent_initialized", output_dir=str(self.output_dir))

    async def generate(self, request: ReportRequest) -> ReportResult:
        """Generate a market research report.

        Args:
            request: The report generation request.

        Returns:
            ReportResult with generated content and metadata.

        Raises:
            ValueError: If the request is invalid.
        """
        if not request.title.strip():
            raise ValueError("Report title must not be empty")

        if not request.formats:
            raise ValueError("At least one output format must be specified")

        report_id = f"rpt_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{id(request)}"
        logger.info(
            "starting_report_generation",
            report_id=report_id,
            title=request.title,
            formats=[f.value for f in request.formats],
        )

        sections = self._build_sections(request)
        content: dict[str, str] = {}
        errors: list[str] = []
        file_paths: dict[str, str] = {}

        for fmt in request.formats:
            try:
                fmt_content = await self._generate_format(fmt, request, sections)
                content[fmt.value] = fmt_content

                if fmt != ReportFormat.JSON:
                    file_path = await self._save_report(report_id, fmt, fmt_content, request)
                    file_paths[fmt.value] = str(file_path)
            except Exception as exc:
                error_msg = f"Failed to generate {fmt.value} format: {exc}"
                logger.error("format_generation_failed", format=fmt.value, error=str(exc))
                errors.append(error_msg)

        word_count = sum(len(s.content.split()) for s in sections)
        metadata = ReportMetadata(
            report_id=report_id,
            title=request.title,
            formats=request.formats,
            section_count=len(sections),
            word_count=word_count,
            file_paths=file_paths,
        )

        success = len(errors) < len(request.formats)

        logger.info(
            "report_generation_completed",
            report_id=report_id,
            success=success,
            sections_count=len(sections),
            word_count=word_count,
        )

        return ReportResult(
            metadata=metadata,
            content=content,
            sections=sections,
            success=success,
            errors=errors,
        )

    def _build_sections(self, request: ReportRequest) -> list[ReportSection]:
        """Build the report sections.

        Args:
            request: The report request.

        Returns:
            List of report sections.
        """
        sections: list[ReportSection] = []
        order = 0

        if request.include_executive_summary:
            sections.append(self._build_executive_summary(request, order))
            order += 1

        analysis = request.analysis_result

        if analysis.swot:
            sections.append(self._build_swot_section(analysis, order))
            order += 1

        if analysis.porters_five_forces:
            sections.append(self._build_porters_section(analysis, order))
            order += 1

        if analysis.pestel:
            sections.append(self._build_pestel_section(analysis, order))
            order += 1

        if analysis.market_sizing:
            sections.append(self._build_market_sizing_section(analysis, order))
            order += 1

        if analysis.trend_analysis:
            sections.append(self._build_trend_section(analysis, order))
            order += 1

        if analysis.insights:
            sections.append(self._build_insights_section(analysis, order))
            order += 1

        if analysis.recommendations:
            sections.append(self._build_recommendations_section(analysis, order))
            order += 1

        for custom in request.custom_sections:
            sections.append(custom)

        return sorted(sections, key=lambda s: s.order)

    def _build_executive_summary(self, request: ReportRequest, order: int) -> ReportSection:
        """Build the executive summary section.

        Args:
            request: The report request.
            order: Section order.

        Returns:
            ReportSection for executive summary.
        """
        analysis = request.analysis_result
        content = f"""# Executive Summary

## {request.title}

This report presents a comprehensive market analysis based on
{analysis.data_points_analyzed} data points collected from multiple research sources.
The analysis covers {len(analysis.analysis_types)} dimensions
including {', '.join(t.value.replace('_', ' ') for t in analysis.analysis_types)}.

### Key Findings

"""
        if analysis.insights:
            for insight in analysis.insights[:5]:
                content += f"- {insight}\n"

        content += f"\n### Confidence Level: {analysis.confidence_level.value.upper()}\n"

        return ReportSection(
            title="Executive Summary",
            content=content,
            order=order,
        )

    def _build_swot_section(self, analysis: AnalysisResult, order: int) -> ReportSection:
        """Build the SWOT analysis section.

        Args:
            analysis: The analysis result.
            order: Section order.

        Returns:
            ReportSection for SWOT.
        """
        swot = analysis.swot
        if not swot:
            return ReportSection(title="SWOT Analysis", content="", order=order)

        content = "# SWOT Analysis\n\n"
        content += "## Strengths\n" + "\n".join(f"- {s}" for s in swot.strengths) + "\n\n"
        content += "## Weaknesses\n" + "\n".join(f"- {w}" for w in swot.weaknesses) + "\n\n"
        content += "## Opportunities\n" + "\n".join(f"- {o}" for o in swot.opportunities) + "\n\n"
        content += "## Threats\n" + "\n".join(f"- {t}" for t in swot.threats) + "\n"

        return ReportSection(title="SWOT Analysis", content=content, order=order)

    def _build_porters_section(self, analysis: AnalysisResult, order: int) -> ReportSection:
        """Build the Porter's Five Forces section.

        Args:
            analysis: The analysis result.
            order: Section order.

        Returns:
            ReportSection for Porter's Five Forces.
        """
        p5f = analysis.porters_five_forces
        if not p5f:
            return ReportSection(title="Porter's Five Forces", content="", order=order)

        content = f"""# Porter's Five Forces Analysis

| Force | Intensity |
|-------|-----------|
| Competitive Rivalry | {p5f.competitive_rivalry:.0%} |
| Supplier Power | {p5f.supplier_power:.0%} |
| Buyer Power | {p5f.buyer_power:.0%} |
| Threat of Substitution | {p5f.threat_of_substitution:.0%} |
| Threat of New Entry | {p5f.threat_of_new_entry:.0%} |

**Overall Market Attractiveness:** {p5f.overall_attractiveness:.0%}
"""
        return ReportSection(title="Porter's Five Forces", content=content, order=order)

    def _build_pestel_section(self, analysis: AnalysisResult, order: int) -> ReportSection:
        """Build the PESTEL analysis section.

        Args:
            analysis: The analysis result.
            order: Section order.

        Returns:
            ReportSection for PESTEL.
        """
        pestel = analysis.pestel
        if not pestel:
            return ReportSection(title="PESTEL Analysis", content="", order=order)

        content = "# PESTEL Analysis\n\n"
        content += "## Political\n" + "\n".join(f"- {p}" for p in pestel.political) + "\n\n"
        content += "## Economic\n" + "\n".join(f"- {e}" for e in pestel.economic) + "\n\n"
        content += "## Social\n" + "\n".join(f"- {s}" for s in pestel.social) + "\n\n"
        content += "## Technological\n" + "\n".join(f"- {t}" for t in pestel.technological) + "\n\n"
        content += "## Environmental\n" + "\n".join(f"- {e}" for e in pestel.environmental) + "\n\n"
        content += "## Legal\n" + "\n".join(f"- {item}" for item in pestel.legal) + "\n"

        return ReportSection(title="PESTEL Analysis", content=content, order=order)

    def _build_market_sizing_section(self, analysis: AnalysisResult, order: int) -> ReportSection:
        """Build the market sizing section.

        Args:
            analysis: The analysis result.
            order: Section order.

        Returns:
            ReportSection for market sizing.
        """
        sizing = analysis.market_sizing
        if not sizing:
            return ReportSection(title="Market Sizing", content="", order=order)

        content = f"""# Market Sizing

| Metric | Value |
|--------|-------|
| Total Addressable Market (TAM) | {sizing.tam:,.0f} {sizing.currency} |
| Serviceable Addressable Market (SAM) | {sizing.sam:,.0f} {sizing.currency} |
| Serviceable Obtainable Market (SOM) | {sizing.som:,.0f} {sizing.currency} |
"""
        if sizing.growth_rate is not None:
            content += f"| Annual Growth Rate | {sizing.growth_rate:.1%} |\n"

        return ReportSection(title="Market Sizing", content=content, order=order)

    def _build_trend_section(self, analysis: AnalysisResult, order: int) -> ReportSection:
        """Build the trend analysis section.

        Args:
            analysis: The analysis result.
            order: Section order.

        Returns:
            ReportSection for trend analysis.
        """
        trend = analysis.trend_analysis
        if not trend:
            return ReportSection(title="Trend Analysis", content="", order=order)

        content = f"""# Trend Analysis

- **Direction:** {trend.trend_direction}
- **Strength:** {trend.trend_strength:.0%}

## Key Drivers
""" + "\n".join(f"- {d}" for d in trend.key_drivers)

        if trend.forecast:
            content += "\n\n## Forecast\n\n| Period | Value |\n|--------|-------|\n"
            for point in trend.forecast:
                content += f"| {point['period']} | {point['value']:,.0f} |\n"

        return ReportSection(title="Trend Analysis", content=content, order=order)

    def _build_insights_section(self, analysis: AnalysisResult, order: int) -> ReportSection:
        """Build the insights section.

        Args:
            analysis: The analysis result.
            order: Section order.

        Returns:
            ReportSection for insights.
        """
        content = "# Key Insights\n\n" + "\n".join(f"- {i}" for i in analysis.insights)
        return ReportSection(title="Key Insights", content=content, order=order)

    def _build_recommendations_section(self, analysis: AnalysisResult, order: int) -> ReportSection:
        """Build the recommendations section.

        Args:
            analysis: The analysis result.
            order: Section order.

        Returns:
            ReportSection for recommendations.
        """
        content = "# Recommendations\n\n" + "\n".join(
            f"{idx + 1}. {r}" for idx, r in enumerate(analysis.recommendations)
        )
        return ReportSection(title="Recommendations", content=content, order=order)

    async def _generate_format(
        self,
        fmt: ReportFormat,
        request: ReportRequest,
        sections: list[ReportSection],
    ) -> str:
        """Generate report content in a specific format.

        Args:
            fmt: The output format.
            request: The report request.
            sections: The report sections.

        Returns:
            Formatted report content.
        """
        if fmt == ReportFormat.MARKDOWN:
            return self._generate_markdown(request, sections)
        elif fmt == ReportFormat.JSON:
            return self._generate_json(request, sections)
        elif fmt == ReportFormat.HTML:
            return self._generate_html(request, sections)
        elif fmt == ReportFormat.PDF:
            return self._generate_pdf_markdown(request, sections)
        else:
            raise ValueError(f"Unsupported format: {fmt}")

    def _generate_markdown(self, request: ReportRequest, sections: list[ReportSection]) -> str:
        """Generate Markdown report content.

        Args:
            request: The report request.
            sections: The report sections.

        Returns:
            Markdown formatted string.
        """
        content = f"# {request.title}\n\n"
        content += f"*Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}*\n\n"
        content += "---\n\n"
        for section in sections:
            content += section.content + "\n\n---\n\n"
        return content

    def _generate_json(self, request: ReportRequest, sections: list[ReportSection]) -> str:
        """Generate JSON report content.

        Args:
            request: The report request.
            sections: The report sections.

        Returns:
            JSON formatted string.
        """
        import json

        data = {
            "title": request.title,
            "generated_at": datetime.utcnow().isoformat(),
            "analysis_id": request.analysis_result.analysis_id,
            "sections": [s.model_dump() for s in sections],
        }
        return json.dumps(data, indent=2, default=str)

    def _generate_html(self, request: ReportRequest, sections: list[ReportSection]) -> str:
        """Generate HTML report content.

        Args:
            request: The report request.
            sections: The report sections.

        Returns:
            HTML formatted string.
        """
        html_parts = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            f"<title>{request.title}</title>",
            "<style>",
            "body { font-family: sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }",
            "h1 { color: #333; }",
            "h2 { color: #666; border-bottom: 1px solid #eee; }",
            "table { border-collapse: collapse; width: 100%; }",
            "th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }",
            "</style>",
            "</head>",
            "<body>",
            f"<h1>{request.title}</h1>",
            f"<p><em>Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}</em></p>",
        ]
        for section in sections:
            html_parts.append(f"<h2>{section.title}</h2>")
            html_parts.append(f"<pre>{section.content}</pre>")
        html_parts.extend(["</body>", "</html>"])
        return "\n".join(html_parts)

    def _generate_pdf_markdown(self, request: ReportRequest, sections: list[ReportSection]) -> str:
        """Generate PDF-ready markdown content.

        Args:
            request: The report request.
            sections: The report sections.

        Returns:
            Markdown formatted string suitable for PDF conversion.
        """
        return self._generate_markdown(request, sections)

    async def _save_report(
        self,
        report_id: str,
        fmt: ReportFormat,
        content: str,
        request: ReportRequest,
    ) -> Path:
        """Save report content to a file.

        Args:
            report_id: The report identifier.
            fmt: The output format.
            content: The report content.
            request: The report request.

        Returns:
            Path to the saved file.
        """
        self.output_dir.mkdir(parents=True, exist_ok=True)
        extension = "md" if fmt == ReportFormat.MARKDOWN else fmt.value
        file_path = self.output_dir / f"{report_id}.{extension}"

        await asyncio.to_thread(file_path.write_text, content, encoding="utf-8")
        logger.info("report_saved", file_path=str(file_path), format=fmt.value)
        return file_path
