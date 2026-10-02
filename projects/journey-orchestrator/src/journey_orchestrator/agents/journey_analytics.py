"""Journey Analytics agent - computes performance metrics and insights."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import structlog
from pydantic import BaseModel, Field

from journey_orchestrator.models.analytics import (
    AnalyticsSummary,
    CohortAnalysis,
    FunnelStage,
    JourneyFunnel,
    JourneyMetric,
    JourneyPerformance,
    MetricType,
)

logger = structlog.get_logger(__name__)


class AnalyticsRequest(BaseModel):
    """Request for journey analytics computation."""

    journey_id: str = Field(..., description="The journey ID to analyze")
    start_date: datetime | None = Field(default=None, description="Analysis period start")
    end_date: datetime | None = Field(default=None, description="Analysis period end")
    metrics: list[MetricType] = Field(
        default_factory=lambda: [
            MetricType.CONVERSION_RATE,
            MetricType.ENGAGEMENT_RATE,
            MetricType.REVENUE_PER_CUSTOMER,
        ],
        description="Metrics to compute",
    )
    segment_by: str | None = Field(default=None, description="Segment field to group by")
    include_funnel: bool = Field(default=True, description="Include funnel analysis")
    include_cohorts: bool = Field(default=False, description="Include cohort analysis")


class AnalyticsInsight(BaseModel):
    """A single insight derived from analytics data."""

    insight_type: str
    severity: str = Field(default="info", description="info, warning, or critical")
    message: str
    recommendation: str = ""
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    related_metric: str | None = None


class AnalyticsReport(BaseModel):
    """Complete analytics report for a journey."""

    journey_id: str
    performance: JourneyPerformance
    funnel: JourneyFunnel | None = None
    cohorts: list[CohortAnalysis] = Field(default_factory=list)
    insights: list[AnalyticsInsight] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    period_start: datetime | None = None
    period_end: datetime | None = None


class JourneyAnalytics:
    """Agent that computes journey performance analytics.

    Processes raw event and conversion data to produce actionable
    performance metrics, funnel analysis, cohort tracking, and
    AI-driven insights for journey optimization.
    """

    def __init__(self, llm_client: Any | None = None) -> None:
        """Initialize the Journey Analytics agent.

        Args:
            llm_client: Optional LLM client for AI-powered insights.
        """
        self.llm_client = llm_client
        self.logger = logger.bind(agent="journey_analytics")

    async def analyze(self, request: AnalyticsRequest) -> AnalyticsReport:
        """Compute analytics for a journey.

        Args:
            request: The analytics request with journey ID and options.

        Returns:
            A complete analytics report.

        Raises:
            ValueError: If the request is invalid.
        """
        if not request.journey_id.strip():
            raise ValueError("journey_id must not be empty")

        self.logger.info(
            "Computing journey analytics",
            journey_id=request.journey_id,
            metrics=[m.value for m in request.metrics],
        )

        # Compute core performance metrics
        performance = await self._compute_performance(request)

        # Compute funnel analysis if requested
        funnel: JourneyFunnel | None = None
        if request.include_funnel:
            funnel = await self._compute_funnel(request, performance)

        # Compute cohort analysis if requested
        cohorts: list[CohortAnalysis] = []
        if request.include_cohorts:
            cohorts = await self._compute_cohorts(request, performance)

        # Generate insights
        insights = await self._generate_insights(performance, funnel, cohorts)

        report = AnalyticsReport(
            journey_id=request.journey_id,
            performance=performance,
            funnel=funnel,
            cohorts=cohorts,
            insights=insights,
            period_start=request.start_date,
            period_end=request.end_date,
        )

        self.logger.info(
            "Analytics computed",
            journey_id=request.journey_id,
            insights=len(insights),
            conversion_rate=performance.conversion_rate,
        )
        return report

    async def compare_journeys(
        self,
        journey_ids: list[str],
        metric: MetricType = MetricType.CONVERSION_RATE,
    ) -> dict[str, Any]:
        """Compare performance across multiple journeys.

        Args:
            journey_ids: List of journey IDs to compare.
            metric: The primary metric to compare on.

        Returns:
            A comparison result with rankings and deltas.

        Raises:
            ValueError: If fewer than 2 journey IDs are provided.
        """
        if len(journey_ids) < 2:
            raise ValueError("At least 2 journey IDs are required for comparison")

        self.logger.info(
            "Comparing journeys",
            journey_ids=journey_ids,
            metric=metric.value,
        )

        # In production, this would query the database for each journey
        # For now, return a structured comparison template
        comparison: dict[str, Any] = {
            "metric": metric.value,
            "journeys": [],
            "winner": None,
            "average": 0.0,
            "spread": 0.0,
        }

        return comparison

    async def get_summary(self) -> AnalyticsSummary:
        """Get a high-level analytics summary across all journeys.

        Returns:
            An analytics summary with aggregate metrics.
        """
        self.logger.info("Computing analytics summary")

        # In production, this would aggregate across all journeys
        summary = AnalyticsSummary()

        self.logger.info(
            "Summary computed",
            total_journeys=summary.total_journeys,
            overall_conversion_rate=summary.overall_conversion_rate,
        )
        return summary

    async def _compute_performance(self, request: AnalyticsRequest) -> JourneyPerformance:
        """Compute core performance metrics for a journey.

        Args:
            request: The analytics request.

        Returns:
            The computed performance data.
        """
        # In production, this would query the events database
        # For now, return a structured template with computed fields
        total_customers = 1000
        converted_customers = 150
        engaged_customers = 450
        total_revenue = 15000.0

        conversion_rate = converted_customers / total_customers if total_customers > 0 else 0.0
        engagement_rate = engaged_customers / total_customers if total_customers > 0 else 0.0
        revenue_per_customer = total_revenue / total_customers if total_customers > 0 else 0.0

        metrics: list[JourneyMetric] = []
        for metric_type in request.metrics:
            value = 0.0
            if metric_type == MetricType.CONVERSION_RATE:
                value = conversion_rate
            elif metric_type == MetricType.ENGAGEMENT_RATE:
                value = engagement_rate
            elif metric_type == MetricType.REVENUE_PER_CUSTOMER:
                value = revenue_per_customer
            metrics.append(JourneyMetric(metric_type=metric_type, value=value))

        return JourneyPerformance(
            journey_id=request.journey_id,
            total_customers=total_customers,
            converted_customers=converted_customers,
            engaged_customers=engaged_customers,
            total_revenue=total_revenue,
            average_engagement_score=engagement_rate,
            conversion_rate=conversion_rate,
            engagement_rate=engagement_rate,
            revenue_per_customer=revenue_per_customer,
            metrics=metrics,
            period_start=request.start_date,
            period_end=request.end_date,
        )

    async def _compute_funnel(
        self,
        request: AnalyticsRequest,
        performance: JourneyPerformance,
    ) -> JourneyFunnel:
        """Compute conversion funnel for a journey.

        Args:
            request: The analytics request.
            performance: The computed performance data.

        Returns:
            The computed funnel data.
        """
        total = performance.total_customers
        stages: list[FunnelStage] = []

        # Standard funnel stages
        stage_definitions = [
            ("entered", total),
            ("engaged", performance.engaged_customers),
            ("converted", performance.converted_customers),
        ]

        prev_count = total
        for stage_name, count in stage_definitions:
            conversion = count / total if total > 0 else 0.0
            dropoff = 1.0 - (count / prev_count) if prev_count > 0 else 0.0
            stages.append(
                FunnelStage(
                    stage_name=stage_name,
                    customer_count=count,
                    conversion_rate=conversion,
                    dropoff_rate=dropoff,
                )
            )
            prev_count = count

        overall_conversion = (
            performance.converted_customers / total if total > 0 else 0.0
        )
        total_dropoff = total - performance.converted_customers

        return JourneyFunnel(
            journey_id=request.journey_id,
            stages=stages,
            overall_conversion_rate=overall_conversion,
            total_dropoff=total_dropoff,
        )

    async def _compute_cohorts(
        self,
        request: AnalyticsRequest,
        performance: JourneyPerformance,
    ) -> list[CohortAnalysis]:
        """Compute cohort analysis for a journey.

        Args:
            request: The analytics request.
            performance: The computed performance data.

        Returns:
            List of cohort analyses.
        """
        # In production, this would group customers by signup week/month
        # For now, return a single cohort template
        cohorts: list[CohortAnalysis] = []

        if performance.total_customers > 0:
            retained = int(performance.total_customers * 0.35)
            cohorts.append(
                CohortAnalysis(
                    journey_id=request.journey_id,
                    cohort_date=datetime.now(UTC) - timedelta(days=30),
                    cohort_size=performance.total_customers,
                    retained_customers=retained,
                    retention_rate=retained / performance.total_customers,
                    average_revenue=performance.revenue_per_customer,
                )
            )

        return cohorts

    async def _generate_insights(
        self,
        performance: JourneyPerformance,
        funnel: JourneyFunnel | None,
        cohorts: list[CohortAnalysis],
    ) -> list[AnalyticsInsight]:
        """Generate actionable insights from analytics data.

        Args:
            performance: The computed performance data.
            funnel: The computed funnel data, if available.
            cohorts: The computed cohort data, if available.

        Returns:
            A list of actionable insights.
        """
        insights: list[AnalyticsInsight] = []

        # Conversion rate insight
        if performance.conversion_rate < 0.1:
            insights.append(
                AnalyticsInsight(
                    insight_type="low_conversion",
                    severity="warning",
                    message=(
                        f"Conversion rate is {performance.conversion_rate:.1%}, "
                        f"below 10% threshold"
                    ),
                    recommendation=(
                        "Review journey steps for friction points "
                        "and test variant messaging"
                    ),
                    confidence=0.8,
                    related_metric="conversion_rate",
                )
            )
        elif performance.conversion_rate > 0.3:
            insights.append(
                AnalyticsInsight(
                    insight_type="high_conversion",
                    severity="info",
                    message=f"Conversion rate is {performance.conversion_rate:.1%}, above 30%",
                    recommendation="Consider scaling this journey to broader audience segments",
                    confidence=0.9,
                    related_metric="conversion_rate",
                )
            )

        # Engagement insight
        if performance.engagement_rate < 0.3:
            insights.append(
                AnalyticsInsight(
                    insight_type="low_engagement",
                    severity="warning",
                    message=f"Engagement rate is {performance.engagement_rate:.1%}",
                    recommendation=(
                        "Test different content types and send times "
                        "to improve engagement"
                    ),
                    confidence=0.7,
                    related_metric="engagement_rate",
                )
            )

        # Funnel dropoff insight
        if funnel and funnel.stages:
            max_dropoff_stage = max(funnel.stages, key=lambda s: s.dropoff_rate)
            if max_dropoff_stage.dropoff_rate > 0.5:
                insights.append(
                    AnalyticsInsight(
                        insight_type="funnel_dropoff",
                        severity="critical",
                        message=(
                            f"High dropoff ({max_dropoff_stage.dropoff_rate:.1%}) "
                            f"at stage '{max_dropoff_stage.stage_name}'"
                        ),
                        recommendation=(
                            f"Review the transition into '{max_dropoff_stage.stage_name}' "
                            "and simplify the customer experience"
                        ),
                        confidence=0.85,
                        related_metric="funnel_dropoff",
                    )
                )

        # Revenue insight
        if performance.revenue_per_customer < 10.0:
            insights.append(
                AnalyticsInsight(
                    insight_type="low_revenue",
                    severity="info",
                    message=f"Revenue per customer is ${performance.revenue_per_customer:.2f}",
                    recommendation="Test upsell and cross-sell steps in the journey",
                    confidence=0.6,
                    related_metric="revenue_per_customer",
                )
            )

        return insights
