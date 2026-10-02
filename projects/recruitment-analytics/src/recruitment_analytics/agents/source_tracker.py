"""Source Tracker Agent - tracks and analyzes recruitment source effectiveness."""

from typing import TYPE_CHECKING
from __future__ import annotations

from decimal import Decimal

from recruitment_analytics.agents.base import BaseAgent

if TYPE_CHECKING:
    from recruitment_analytics.integrations.ats_client import ATSClient

from recruitment_analytics.models.schemas import (
    SourceMetrics,
    SourceTrackingRequest,
    SourceTrackingResponse,
    SourceType,
)


class SourceTrackerAgent(BaseAgent[SourceTrackingRequest, SourceTrackingResponse]):
    """Agent that tracks recruitment sources and analyzes their effectiveness
    in terms of candidate quality, conversion rates, and cost efficiency.
    """

    def __init__(self, ats_client: ATSClient | None = None) -> None:
        super().__init__()
        self.ats_client = ats_client

    @property
    def agent_name(self) -> str:
        return "Source Tracker"

    async def run(self, request: SourceTrackingRequest) -> SourceTrackingResponse:
        """Analyze recruitment sources and generate performance report.

        Args:
            request: Source tracking request with date range and filters.

        Returns:
            Source tracking response with metrics and insights.
        """
        if self.ats_client:
            raw_data = await self.ats_client.get_sources(
                start_date=request.start_date,
                end_date=request.end_date,
            )
        else:
            raw_data = self._generate_sample_data()

        sources = self._compute_source_metrics(raw_data)
        top_performing = self._identify_top_performers(sources)
        underperforming = self._identify_underperformers(sources)
        insights = self._generate_insights(sources)

        return SourceTrackingResponse(
            sources=sources,
            top_performing=top_performing,
            underperforming=underperforming,
            insights=insights,
        )

    def _compute_source_metrics(self, raw_data: list[dict]) -> list[SourceMetrics]:
        """Compute metrics for each recruitment source."""
        sources: list[SourceMetrics] = []

        for item in raw_data:
            source_type = SourceType(item.get("source_type", "other"))
            total = item.get("total_candidates", 0)
            qualified = item.get("qualified_candidates", 0)
            hires = item.get("hires", 0)
            cost = Decimal(str(item.get("total_cost", 0)))

            sources.append(
                SourceMetrics(
                    source=source_type,
                    label=item.get("label", source_type.value),
                    total_candidates=total,
                    qualified_candidates=qualified,
                    hires=hires,
                    conversion_rate=round(hires / total, 4) if total > 0 else 0.0,
                    cost_per_hire=round(cost / hires, 2) if hires > 0 else Decimal("0"),
                    avg_time_to_hire_days=item.get("avg_time_to_hire_days", 0.0),
                    quality_score=item.get("quality_score", 0.0),
                )
            )

        return sources

    def _identify_top_performers(self, sources: list[SourceMetrics]) -> list[SourceMetrics]:
        """Identify top performing sources by quality score and conversion."""
        return sorted(
            sources,
            key=lambda s: (s.quality_score, s.conversion_rate),
            reverse=True,
        )[:3]

    def _identify_underperformers(self, sources: list[SourceMetrics]) -> list[SourceMetrics]:
        """Identify underperforming sources with low conversion and high cost."""
        return sorted(
            sources,
            key=lambda s: (s.conversion_rate, -s.cost_per_hire),
        )[:3]

    def _generate_insights(self, sources: list[SourceMetrics]) -> list[str]:
        """Generate insights from source tracking data."""
        insights: list[str] = []

        if not sources:
            return ["No source data available for analysis"]

        best = max(sources, key=lambda s: s.conversion_rate)
        worst = min(sources, key=lambda s: s.conversion_rate)

        insights.append(
            f"Best converting source: {best.label} ({best.conversion_rate:.1%})"
        )
        insights.append(
            f"Worst converting source: {worst.label} ({worst.conversion_rate:.1%})"
        )

        avg_cost = sum(s.cost_per_hire for s in sources) / len(sources)
        expensive = [s for s in sources if s.cost_per_hire > avg_cost * 2]
        if expensive:
            insights.append(
                f"{len(expensive)} sources have cost per hire above 2x average"
            )

        return insights

    def _generate_sample_data(self) -> list[dict]:
        """Generate sample source data for testing/demo purposes."""
        return [
            {
                "source_type": "referral",
                "label": "Employee Referral",
                "total_candidates": 50,
                "qualified_candidates": 35,
                "hires": 15,
                "total_cost": 7500.0,
                "avg_time_to_hire_days": 25.0,
                "quality_score": 0.85,
            },
            {
                "source_type": "linkedin",
                "label": "LinkedIn",
                "total_candidates": 200,
                "qualified_candidates": 80,
                "hires": 10,
                "total_cost": 5000.0,
                "avg_time_to_hire_days": 35.0,
                "quality_score": 0.65,
            },
            {
                "source_type": "job_board",
                "label": "Indeed",
                "total_candidates": 500,
                "qualified_candidates": 100,
                "hires": 8,
                "total_cost": 3000.0,
                "avg_time_to_hire_days": 40.0,
                "quality_score": 0.45,
            },
            {
                "source_type": "agency",
                "label": "Recruitment Agency",
                "total_candidates": 30,
                "qualified_candidates": 20,
                "hires": 5,
                "total_cost": 15000.0,
                "avg_time_to_hire_days": 20.0,
                "quality_score": 0.75,
            },
        ]
