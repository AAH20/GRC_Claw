"""Diversity Analyzer Agent - analyzes diversity metrics across the recruitment funnel."""

from typing import TYPE_CHECKING
from __future__ import annotations

import uuid

from recruitment_analytics.agents.base import BaseAgent

if TYPE_CHECKING:
    from recruitment_analytics.integrations.ats_client import ATSClient

from recruitment_analytics.models.schemas import (
    DiversityAnalysisRequest,
    DiversityAnalysisResponse,
    DiversityDimension,
    DiversityReport,
)


class DiversityAnalyzerAgent(BaseAgent[DiversityAnalysisRequest, DiversityAnalysisResponse]):
    """Agent that analyzes diversity metrics across the recruitment pipeline
    and generates reports with benchmark comparisons.
    """

    def __init__(self, ats_client: ATSClient | None = None) -> None:
        super().__init__()
        self.ats_client = ats_client

    @property
    def agent_name(self) -> str:
        return "Diversity Analyzer"

    async def run(self, request: DiversityAnalysisRequest) -> DiversityAnalysisResponse:
        """Analyze diversity metrics and generate report.

        Args:
            request: Diversity analysis request with date range and dimensions.

        Returns:
            Diversity analysis response with report and benchmarks.
        """
        if self.ats_client:
            raw_data = await self.ats_client.get_diversity_data(
                start_date=request.start_date,
                end_date=request.end_date,
                department=request.department,
            )
        else:
            raw_data = self._generate_sample_data()

        gender_dim = self._compute_dimension("gender", raw_data.get("gender", {}))
        ethnicity_dim = self._compute_dimension("ethnicity", raw_data.get("ethnicity", {}))

        additional: list[DiversityDimension] = []
        for dim_name in request.dimensions:
            if dim_name not in ("gender", "ethnicity"):
                additional.append(
                    self._compute_dimension(dim_name, raw_data.get(dim_name, {}))
                )

        total = sum(gender_dim.categories.values()) if gender_dim.categories else 0
        overall_score = (gender_dim.representation_index + ethnicity_dim.representation_index) / 2

        report = DiversityReport(
            id=str(uuid.uuid4()),
            name=f"Diversity Report {request.start_date} to {request.end_date}",
            start_date=request.start_date,
            end_date=request.end_date,
            department=request.department,
            role=request.role,
            total_candidates=total,
            gender=gender_dim,
            ethnicity=ethnicity_dim,
            additional_dimensions=additional,
            overall_diversity_score=round(overall_score, 4),
            insights=self._generate_insights(gender_dim, ethnicity_dim),
            recommendations=self._generate_recommendations(gender_dim, ethnicity_dim),
        )

        benchmark = self._generate_benchmark_comparison(report)

        return DiversityAnalysisResponse(
            report=report,
            benchmark_comparison=benchmark,
        )

    def _compute_dimension(self, name: str, data: dict) -> DiversityDimension:
        """Compute diversity dimension metrics."""
        categories = data.get("counts", {})
        total = sum(categories.values())

        percentages: dict[str, float] = {}
        representation_index = 0.0

        if total > 0:
            for key, count in categories.items():
                percentages[key] = round(count / total, 4)

            # Compute representation index (1.0 = perfect representation)
            expected = 1.0 / len(categories) if categories else 0
            variance = sum(
                (pct - expected) ** 2 for pct in percentages.values()
            ) / len(percentages) if percentages else 0
            representation_index = max(0.0, 1.0 - variance * 2)

        return DiversityDimension(
            dimension=name,
            categories=categories,
            percentages=percentages,
            representation_index=round(representation_index, 4),
        )

    def _generate_insights(
        self, gender: DiversityDimension, ethnicity: DiversityDimension
    ) -> list[str]:
        """Generate insights from diversity data."""
        insights: list[str] = []

        # Gender insights
        if gender.percentages:
            female_pct = gender.percentages.get("female", 0)
            if female_pct < 0.3:
                insights.append(
                    f"Female representation ({female_pct:.1%}) is below target range"
                )
            elif female_pct > 0.6:
                insights.append(
                    f"Female representation ({female_pct:.1%}) is above target range"
                )

        # Ethnicity insights
        if ethnicity.percentages:
            underrepresented = [
                k for k, v in ethnicity.percentages.items()
                if v < 0.1 and k not in ("prefer_not_to_say", "other")
            ]
            if underrepresented:
                insights.append(
                    f"Underrepresented groups: {', '.join(underrepresented)}"
                )

        if not insights:
            insights.append("Diversity metrics are within expected ranges")

        return insights

    def _generate_recommendations(
        self, gender: DiversityDimension, ethnicity: DiversityDimension
    ) -> list[str]:
        """Generate recommendations based on diversity analysis."""
        recs: list[str] = []

        if gender.representation_index < 0.7:
            recs.append("Implement blind resume screening to reduce gender bias")
            recs.append("Partner with women-in-tech organizations for sourcing")

        if ethnicity.representation_index < 0.7:
            recs.append("Expand sourcing to HBCUs and Hispanic-serving institutions")
            recs.append("Review job descriptions for inclusive language")

        if not recs:
            recs.append("Continue monitoring diversity metrics across funnel stages")
            recs.append("Conduct quarterly diversity hiring reviews")

        return recs

    def _generate_benchmark_comparison(self, report: DiversityReport) -> dict:
        """Generate industry benchmark comparison."""
        return {
            "industry_average_diversity_score": 0.65,
            "company_score": report.overall_diversity_score,
            "percentile": (
                "above_average" if report.overall_diversity_score > 0.65 else "below_average"
            ),
            "gender_benchmark": {
                "industry_female_avg": 0.35,
                "company_female_pct": report.gender.percentages.get("female", 0),
            },
        }

    def _generate_sample_data(self) -> dict:
        """Generate sample diversity data for testing/demo purposes."""
        return {
            "gender": {
                "counts": {
                    "male": 600,
                    "female": 350,
                    "non_binary": 30,
                    "prefer_not_to_say": 20,
                }
            },
            "ethnicity": {
                "counts": {
                    "asian": 300,
                    "black": 150,
                    "hispanic": 120,
                    "white": 350,
                    "two_or_more": 50,
                    "prefer_not_to_say": 30,
                }
            },
        }
