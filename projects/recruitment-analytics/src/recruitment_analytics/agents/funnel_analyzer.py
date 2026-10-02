"""Funnel Analyzer Agent - analyzes recruitment funnel metrics and bottlenecks."""

from __future__ import annotations

import uuid
from datetime import date

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel

from recruitment_analytics.agents.base import BaseAgent
from recruitment_analytics.integrations.ats_client import ATSClient
from recruitment_analytics.models.schemas import (
    Funnel,
    FunnelAnalysisRequest,
    FunnelAnalysisResponse,
    FunnelStage,
    FunnelStageMetrics,
)


class FunnelAnalyzerAgent(BaseAgent[FunnelAnalysisRequest, FunnelAnalysisResponse]):
    """Agent that analyzes recruitment funnel data to identify bottlenecks,
    conversion rates, and optimization opportunities.
    """

    def __init__(self, ats_client: ATSClient | None = None) -> None:
        super().__init__()
        self.ats_client = ats_client

    @property
    def agent_name(self) -> str:
        return "Funnel Analyzer"

    async def run(self, request: FunnelAnalysisRequest) -> FunnelAnalysisResponse:
        """Analyze recruitment funnel and generate insights.

        Args:
            request: Funnel analysis request with date range and filters.

        Returns:
            Funnel analysis response with metrics and recommendations.
        """
        # Fetch data from ATS if client available
        if self.ats_client:
            raw_data = await self.ats_client.get_funnel_data(
                start_date=request.start_date,
                end_date=request.end_date,
                department=request.department,
                role=request.role,
            )
        else:
            raw_data = self._generate_sample_data(request)

        stages = self._compute_stage_metrics(raw_data)
        total_applicants = stages[0].count if stages else 0
        total_hired = next(
            (s.count for s in stages if s.stage == FunnelStage.HIRED), 0
        )

        funnel = Funnel(
            id=str(uuid.uuid4()),
            name=f"Funnel {request.start_date} to {request.end_date}",
            start_date=request.start_date,
            end_date=request.end_date,
            department=request.department,
            role=request.role,
            stages=stages,
            total_applicants=total_applicants,
            total_hired=total_hired,
            overall_conversion_rate=(
                total_hired / total_applicants if total_applicants > 0 else 0.0
            ),
            avg_time_to_hire_days=self._compute_avg_time_to_hire(stages),
        )

        insights = self._generate_insights(funnel)
        recommendations = self._generate_recommendations(funnel)

        return FunnelAnalysisResponse(
            funnel=funnel,
            insights=insights,
            recommendations=recommendations,
        )

    def _compute_stage_metrics(self, raw_data: dict) -> list[FunnelStageMetrics]:
        """Compute metrics for each funnel stage."""
        stages: list[FunnelStageMetrics] = []
        stage_counts: dict[str, int] = raw_data.get("stage_counts", {})
        prev_count = 0

        for stage in FunnelStage:
            if stage in (FunnelStage.REJECTED, FunnelStage.WITHDRAWN):
                continue
            count = stage_counts.get(stage.value, 0)
            conversion = count / prev_count if prev_count > 0 else 0.0
            dropoff = 1.0 - conversion if prev_count > 0 else 0.0
            avg_days = raw_data.get("avg_days_in_stage", {}).get(stage.value, 0.0)

            stages.append(
                FunnelStageMetrics(
                    stage=stage,
                    count=count,
                    conversion_rate=round(conversion, 4),
                    avg_time_in_stage_days=avg_days,
                    dropoff_rate=round(dropoff, 4),
                )
            )
            prev_count = count

        return stages

    def _compute_avg_time_to_hire(self, stages: list[FunnelStageMetrics]) -> float:
        """Compute average time to hire from stage metrics."""
        return sum(s.avg_time_in_stage_days for s in stages)

    def _generate_insights(self, funnel: Funnel) -> list[str]:
        """Generate actionable insights from funnel data."""
        insights: list[str] = []

        for stage in funnel.stages:
            if stage.dropoff_rate > 0.5 and stage.count > 0:
                insights.append(
                    f"High dropoff rate ({stage.dropoff_rate:.0%}) at {stage.stage.value} stage"
                )

        if funnel.overall_conversion_rate < 0.05:
            insights.append(
                f"Overall conversion rate ({funnel.overall_conversion_rate:.1%}) is below industry average"
            )

        if funnel.avg_time_to_hire_days > 45:
            insights.append(
                f"Time to hire ({funnel.avg_time_to_hire_days:.0f} days) exceeds recommended 45 days"
            )

        if not insights:
            insights.append("Funnel metrics are within normal parameters")

        return insights

    def _generate_recommendations(self, funnel: Funnel) -> list[str]:
        """Generate recommendations based on funnel analysis."""
        recommendations: list[str] = []

        for stage in funnel.stages:
            if stage.dropoff_rate > 0.4:
                recommendations.append(
                    f"Review {stage.stage.value} process to reduce dropoff rate"
                )
                recommendations.append(
                    f"Consider additional training for {stage.stage.value} evaluators"
                )

        if funnel.avg_time_to_hire_days > 30:
            recommendations.append(
                "Streamline interview scheduling to reduce time to hire"
            )

        if not recommendations:
            recommendations.append("Continue monitoring funnel metrics for trends")

        return recommendations

    def _generate_sample_data(self, request: FunnelAnalysisRequest) -> dict:
        """Generate sample funnel data for testing/demo purposes."""
        return {
            "stage_counts": {
                "applied": 1000,
                "screening": 600,
                "phone_interview": 300,
                "technical_interview": 150,
                "onsite_interview": 75,
                "offer": 30,
                "hired": 20,
            },
            "avg_days_in_stage": {
                "applied": 0,
                "screening": 3.0,
                "phone_interview": 5.0,
                "technical_interview": 7.0,
                "onsite_interview": 10.0,
                "offer": 5.0,
                "hired": 0,
            },
        }
