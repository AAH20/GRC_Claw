"""Performance Analytics Agent for tracking KPIs and campaign performance."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from enum import StrEnum
from typing import Any

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


class MetricType(StrEnum):
    """Types of performance metrics."""

    ROI = "roi"
    CONVERSION_RATE = "conversion_rate"
    CUSTOMER_ACQUISITION_COST = "customer_acquisition_cost"
    LIFETIME_VALUE = "lifetime_value"
    MARKET_SHARE = "market_share"
    REVENUE_GROWTH = "revenue_growth"
    CUSTOMER_RETENTION = "customer_retention"
    NET_PROMOTER_SCORE = "net_promoter_score"


class AggregationPeriod(StrEnum):
    """Time periods for metric aggregation."""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class MetricValue(BaseModel):
    """A single metric value at a point in time."""

    metric_type: MetricType
    value: float
    unit: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)


class MetricAggregation(BaseModel):
    """Aggregated metric data over a period."""

    metric_type: MetricType
    period: AggregationPeriod
    start_date: datetime
    end_date: datetime
    values: list[MetricValue] = Field(default_factory=list)
    average: float = 0.0
    minimum: float = 0.0
    maximum: float = 0.0
    median: float = 0.0
    standard_deviation: float = 0.0
    count: int = 0


class PerformanceSnapshot(BaseModel):
    """A snapshot of performance at a point in time."""

    snapshot_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metrics: list[MetricValue] = Field(default_factory=list)
    overall_score: float = Field(default=0.0, ge=0.0, le=100.0)
    period_over_period_change: float | None = None


class PerformanceRequest(BaseModel):
    """Request to retrieve performance analytics."""

    metric_types: list[MetricType] = Field(default_factory=lambda: list(MetricType))
    period: AggregationPeriod = AggregationPeriod.MONTHLY
    start_date: datetime | None = None
    end_date: datetime | None = None
    comparison_baseline: str = "previous_period"
    filters: dict[str, Any] = Field(default_factory=dict)


class PerformanceResult(BaseModel):
    """Result of a performance analytics query."""

    request_id: str
    period: AggregationPeriod
    aggregations: list[MetricAggregation] = Field(default_factory=list)
    snapshots: list[PerformanceSnapshot] = Field(default_factory=list)
    summary: dict[str, Any] = Field(default_factory=dict)
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class PerformanceAnalyticsAgent:
    """Agent responsible for tracking KPIs and campaign performance.

    This agent collects, aggregates, and analyzes performance metrics
    including ROI, conversion rates, customer acquisition costs, and
    other key business indicators.
    """

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize the Performance Analytics Agent.

        Args:
            config: Optional configuration dictionary for the agent.
        """
        self.config = config or {}
        self.metrics = self.config.get(
            "metrics", [m.value for m in MetricType]
        )
        self.aggregation_period = AggregationPeriod(
            self.config.get("aggregation_period", "monthly")
        )
        self.comparison_baseline = self.config.get(
            "comparison_baseline", "previous_period"
        )
        logger.info(
            "performance_analytics_agent_initialized",
            metrics=self.metrics,
            period=self.aggregation_period.value,
        )

    async def get_performance(self, request: PerformanceRequest) -> PerformanceResult:
        """Retrieve performance analytics data.

        Args:
            request: The performance analytics request.

        Returns:
            PerformanceResult with aggregated metrics and analysis.

        Raises:
            ValueError: If the request is invalid.
        """
        if not request.metric_types:
            raise ValueError("At least one metric type must be specified")

        request_id = f"perf_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{id(request)}"
        logger.info(
            "retrieving_performance_analytics",
            request_id=request_id,
            metric_types=[m.value for m in request.metric_types],
            period=request.period.value,
        )

        end_date = request.end_date or datetime.utcnow()
        start_date = request.start_date or (end_date - timedelta(days=90))

        aggregations = await self._aggregate_metrics(
            request.metric_types,
            request.period,
            start_date,
            end_date,
        )

        snapshots = await self._generate_snapshots(
            request.metric_types,
            start_date,
            end_date,
        )

        summary = self._generate_summary(aggregations, snapshots)

        logger.info(
            "performance_analytics_completed",
            request_id=request_id,
            aggregations_count=len(aggregations),
            snapshots_count=len(snapshots),
        )

        return PerformanceResult(
            request_id=request_id,
            period=request.period,
            aggregations=aggregations,
            snapshots=snapshots,
            summary=summary,
        )

    async def _aggregate_metrics(
        self,
        metric_types: list[MetricType],
        period: AggregationPeriod,
        start_date: datetime,
        end_date: datetime,
    ) -> list[MetricAggregation]:
        """Aggregate metrics over the specified period.

        Args:
            metric_types: The metric types to aggregate.
            period: The aggregation period.
            start_date: Start date for aggregation.
            end_date: End date for aggregation.

        Returns:
            List of metric aggregations.
        """
        aggregations: list[MetricAggregation] = []

        for metric_type in metric_types:
            values = await self._fetch_metric_values(metric_type, start_date, end_date)
            agg = self._compute_aggregation(metric_type, period, start_date, end_date, values)
            aggregations.append(agg)

        return aggregations

    async def _fetch_metric_values(
        self,
        metric_type: MetricType,
        start_date: datetime,
        end_date: datetime,
    ) -> list[MetricValue]:
        """Fetch metric values from the data store.

        Args:
            metric_type: The metric type to fetch.
            start_date: Start date for data.
            end_date: End date for data.

        Returns:
            List of metric values.
        """
        # In production, this would query a database or analytics API
        logger.info(
            "fetching_metric_values",
            metric_type=metric_type.value,
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
        )
        await asyncio.sleep(0.05)

        # Generate sample data points
        values: list[MetricValue] = []
        current = start_date
        while current <= end_date:
            base_value = self._get_base_value(metric_type)
            variation = base_value * 0.1
            import random
            value = base_value + random.uniform(-variation, variation)
            values.append(
                MetricValue(
                    metric_type=metric_type,
                    value=round(value, 2),
                    unit=self._get_unit(metric_type),
                    timestamp=current,
                )
            )
            current += timedelta(days=30)

        return values

    def _compute_aggregation(
        self,
        metric_type: MetricType,
        period: AggregationPeriod,
        start_date: datetime,
        end_date: datetime,
        values: list[MetricValue],
    ) -> MetricAggregation:
        """Compute aggregation statistics for a set of values.

        Args:
            metric_type: The metric type.
            period: The aggregation period.
            start_date: Start date.
            end_date: End date.
            values: The values to aggregate.

        Returns:
            MetricAggregation with computed statistics.
        """
        if not values:
            return MetricAggregation(
                metric_type=metric_type,
                period=period,
                start_date=start_date,
                end_date=end_date,
            )

        numeric_values = [v.value for v in values]
        sorted_values = sorted(numeric_values)
        count = len(sorted_values)

        return MetricAggregation(
            metric_type=metric_type,
            period=period,
            start_date=start_date,
            end_date=end_date,
            values=values,
            average=sum(numeric_values) / count,
            minimum=min(numeric_values),
            maximum=max(numeric_values),
            median=sorted_values[count // 2],
            standard_deviation=self._compute_std_dev(numeric_values),
            count=count,
        )

    def _compute_std_dev(self, values: list[float]) -> float:
        """Compute standard deviation of a list of values.

        Args:
            values: The values.

        Returns:
            Standard deviation.
        """
        if len(values) < 2:
            return 0.0
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
        return variance ** 0.5

    async def _generate_snapshots(
        self,
        metric_types: list[MetricType],
        start_date: datetime,
        end_date: datetime,
    ) -> list[PerformanceSnapshot]:
        """Generate performance snapshots.

        Args:
            metric_types: The metric types to include.
            start_date: Start date.
            end_date: End date.

        Returns:
            List of performance snapshots.
        """
        snapshots: list[PerformanceSnapshot] = []
        current = start_date

        while current <= end_date:
            metrics: list[MetricValue] = []
            for metric_type in metric_types:
                base_value = self._get_base_value(metric_type)
                import random
                value = base_value + random.uniform(-base_value * 0.1, base_value * 0.1)
                metrics.append(
                    MetricValue(
                        metric_type=metric_type,
                        value=round(value, 2),
                        unit=self._get_unit(metric_type),
                        timestamp=current,
                    )
                )

            overall = sum(m.value for m in metrics) / len(metrics) if metrics else 0.0
            snapshots.append(
                PerformanceSnapshot(
                    snapshot_id=f"snap_{current.strftime('%Y%m%d%H%M%S')}",
                    timestamp=current,
                    metrics=metrics,
                    overall_score=min(overall / 10, 100.0),
                )
            )
            current += timedelta(days=30)

        return snapshots

    def _generate_summary(
        self,
        aggregations: list[MetricAggregation],
        snapshots: list[PerformanceSnapshot],
    ) -> dict[str, Any]:
        """Generate a summary of performance analytics.

        Args:
            aggregations: The metric aggregations.
            snapshots: The performance snapshots.

        Returns:
            Summary dictionary.
        """
        summary: dict[str, Any] = {
            "total_metrics_tracked": len(aggregations),
            "total_snapshots": len(snapshots),
            "metrics": {},
        }

        for agg in aggregations:
            summary["metrics"][agg.metric_type.value] = {
                "average": round(agg.average, 2),
                "trend": (
                    "up"
                    if agg.values
                    and len(agg.values) > 1
                    and agg.values[-1].value > agg.values[0].value
                    else "down"
                ),
                "volatility": round(agg.standard_deviation, 2) if agg.standard_deviation else 0.0,
            }

        if snapshots:
            latest = snapshots[-1]
            summary["latest_overall_score"] = round(latest.overall_score, 2)
            summary["latest_snapshot_date"] = latest.timestamp.isoformat()

        return summary

    def _get_base_value(self, metric_type: MetricType) -> float:
        """Get a base value for a metric type.

        Args:
            metric_type: The metric type.

        Returns:
            Base value for the metric.
        """
        base_values = {
            MetricType.ROI: 0.25,
            MetricType.CONVERSION_RATE: 0.035,
            MetricType.CUSTOMER_ACQUISITION_COST: 150.0,
            MetricType.LIFETIME_VALUE: 2500.0,
            MetricType.MARKET_SHARE: 0.15,
            MetricType.REVENUE_GROWTH: 0.12,
            MetricType.CUSTOMER_RETENTION: 0.85,
            MetricType.NET_PROMOTER_SCORE: 45.0,
        }
        return base_values.get(metric_type, 0.0)

    def _get_unit(self, metric_type: MetricType) -> str:
        """Get the unit for a metric type.

        Args:
            metric_type: The metric type.

        Returns:
            Unit string.
        """
        units = {
            MetricType.ROI: "ratio",
            MetricType.CONVERSION_RATE: "ratio",
            MetricType.CUSTOMER_ACQUISITION_COST: "USD",
            MetricType.LIFETIME_VALUE: "USD",
            MetricType.MARKET_SHARE: "ratio",
            MetricType.REVENUE_GROWTH: "ratio",
            MetricType.CUSTOMER_RETENTION: "ratio",
            MetricType.NET_PROMOTER_SCORE: "score",
        }
        return units.get(metric_type, "unknown")
