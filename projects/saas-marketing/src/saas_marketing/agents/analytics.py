"""Analytics agent for metrics aggregation and funnel analysis."""

from __future__ import annotations

from datetime import datetime, timedelta
from enum import StrEnum

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


class FunnelStage(StrEnum):
    """Standard SaaS PLG funnel stages."""

    VISITOR = "visitor"
    SIGNUP = "signup"
    ACTIVATED = "activated"
    ENGAGED = "engaged"
    PAYING = "paying"
    EXPANDED = "expanded"


class FunnelMetrics(BaseModel):
    """Metrics for a single funnel stage."""

    stage: FunnelStage = Field(..., description="Funnel stage name")
    count: int = Field(..., description="Number of users at this stage")
    conversion_rate: float = Field(..., ge=0, le=1, description="Conversion from previous stage")
    dropoff_rate: float = Field(..., ge=0, le=1, description="Dropoff from previous stage")
    avg_time_to_convert_hours: float | None = Field(
        default=None, description="Avg time to next stage"
    )


class CohortMetrics(BaseModel):
    """Cohort analysis metrics."""

    cohort_month: str = Field(..., description="Cohort month (YYYY-MM)")
    cohort_size: int = Field(..., description="Initial cohort size")
    retention_rates: dict[int, float] = Field(
        default_factory=dict, description="Retention rate by month number"
    )
    avg_revenue_per_user: float = Field(default=0.0, description="ARPU for this cohort")


class AnalyticsQuery(BaseModel):
    """Query parameters for analytics."""

    start_date: datetime = Field(..., description="Start date for analysis")
    end_date: datetime = Field(..., description="End date for analysis")
    granularity: str = Field(default="day", description="Time granularity: hour, day, week, month")
    segment_by: str | None = Field(default=None, description="Segment dimension")
    metrics: list[str] = Field(default_factory=list, description="Specific metrics to compute")


class AnalyticsResult(BaseModel):
    """Analytics query result."""

    query: AnalyticsQuery = Field(..., description="Original query parameters")
    funnel: list[FunnelMetrics] = Field(default_factory=list, description="Funnel stage metrics")
    cohorts: list[CohortMetrics] = Field(default_factory=list, description="Cohort analysis")
    summary: dict[str, float | int | str] = Field(default_factory=dict, description="Summary KPIs")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="Result timestamp")


class AnalyticsAgent:
    """Agent for aggregating metrics, funnels, and cohort analysis.

    Processes raw event data into actionable marketing and product analytics.
    """

    VALID_GRANULARITIES = {"hour", "day", "week", "month"}

    def __init__(
        self,
        model: str = "gpt-4",
        temperature: float = 0.2,
        default_lookback_days: int = 30,
    ) -> None:
        """Initialize the AnalyticsAgent.

        Args:
            model: LLM model identifier.
            temperature: Sampling temperature.
            default_lookback_days: Default number of days to look back.
        """
        self.model = model
        self.temperature = temperature
        self.default_lookback_days = default_lookback_days
        logger.info("analytics_agent_initialized")

    async def analyze(self, query: AnalyticsQuery) -> AnalyticsResult:
        """Run analytics analysis based on query parameters.

        Args:
            query: Analytics query parameters.

        Returns:
            Analytics results with funnel, cohorts, and summary.

        Raises:
            ValueError: If query parameters are invalid.
        """
        self._validate_query(query)

        logger.info(
            "running_analytics",
            start=query.start_date.isoformat(),
            end=query.end_date.isoformat(),
            granularity=query.granularity,
        )

        # In production, this would query a data warehouse
        funnel = self._compute_funnel(query)
        cohorts = self._compute_cohorts(query)
        summary = self._compute_summary(query, funnel)

        logger.info("analytics_complete", funnel_stages=len(funnel))

        return AnalyticsResult(
            query=query,
            funnel=funnel,
            cohorts=cohorts,
            summary=summary,
        )

    def _validate_query(self, query: AnalyticsQuery) -> None:
        """Validate analytics query parameters.

        Args:
            query: Query to validate.

        Raises:
            ValueError: If parameters are invalid.
        """
        if query.end_date <= query.start_date:
            raise ValueError("end_date must be after start_date")
        if query.granularity not in self.VALID_GRANULARITIES:
            raise ValueError(
                f"Invalid granularity: {query.granularity}. "
                f"Must be one of {self.VALID_GRANULARITIES}"
            )

    def _compute_funnel(self, query: AnalyticsQuery) -> list[FunnelMetrics]:
        """Compute funnel stage metrics.

        In production, this would query actual event data.

        Args:
            query: Analytics query.

        Returns:
            List of funnel stage metrics.
        """
        # Mock data for development
        mock_counts = {
            FunnelStage.VISITOR: 10000,
            FunnelStage.SIGNUP: 2500,
            FunnelStage.ACTIVATED: 1200,
            FunnelStage.ENGAGED: 800,
            FunnelStage.PAYING: 300,
            FunnelStage.EXPANDED: 150,
        }

        funnel: list[FunnelMetrics] = []
        prev_count: int | None = None

        for stage in FunnelStage:
            count = mock_counts[stage]
            conversion = count / prev_count if prev_count else 1.0
            dropoff = 1.0 - conversion if prev_count else 0.0

            funnel.append(
                FunnelMetrics(
                    stage=stage,
                    count=count,
                    conversion_rate=round(conversion, 4),
                    dropoff_rate=round(dropoff, 4),
                    avg_time_to_convert_hours=None,
                )
            )
            prev_count = count

        return funnel

    def _compute_cohorts(self, query: AnalyticsQuery) -> list[CohortMetrics]:
        """Compute cohort retention analysis.

        Args:
            query: Analytics query.

        Returns:
            List of cohort metrics.
        """
        # Mock cohort data
        cohorts = []
        start = query.start_date
        for i in range(3):
            cohort_date = start - timedelta(days=30 * i)
            cohorts.append(
                CohortMetrics(
                    cohort_month=cohort_date.strftime("%Y-%m"),
                    cohort_size=500 + i * 100,
                    retention_rates={
                        1: 0.65 - i * 0.05,
                        2: 0.45 - i * 0.03,
                        3: 0.35 - i * 0.02,
                    },
                    avg_revenue_per_user=49.0 + i * 10,
                )
            )
        return cohorts

    def _compute_summary(
        self, query: AnalyticsQuery, funnel: list[FunnelMetrics]
    ) -> dict[str, float | int | str]:
        """Compute summary KPIs.

        Args:
            query: Analytics query.
            funnel: Computed funnel metrics.

        Returns:
            Dictionary of summary KPIs.
        """
        total_visitors = funnel[0].count if funnel else 0
        total_paying = funnel[-2].count if len(funnel) >= 2 else 0
        overall_conversion = total_paying / total_visitors if total_visitors else 0.0

        return {
            "total_visitors": total_visitors,
            "total_signups": funnel[1].count if len(funnel) > 1 else 0,
            "total_paying": total_paying,
            "overall_conversion_rate": round(overall_conversion, 4),
            "visitor_to_signup": round(
                funnel[1].conversion_rate if len(funnel) > 1 else 0, 4
            ),
            "signup_to_paying": round(
                funnel[-2].conversion_rate if len(funnel) >= 2 else 0, 4
            ),
            "analysis_period_days": (query.end_date - query.start_date).days,
        }
