"""Analytics Agent - Revenue analytics, reporting, and insights for creators."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


class MetricPoint(BaseModel):
    """A single metric data point."""

    timestamp: datetime = Field(..., description="Timestamp of the metric")
    value: float = Field(..., description="Metric value")
    label: str | None = Field(default=None, description="Optional label")


class ReportPeriod(BaseModel):
    """Time period for a report."""

    start: datetime = Field(..., description="Period start")
    end: datetime = Field(..., description="Period end")


class AnalyticsAgent:
    """Agent responsible for creator revenue analytics.

    Generates performance reports, identifies trends,
    and provides actionable insights for creators.
    """

    def __init__(self) -> None:
        """Initialize the analytics agent."""
        self._reports: dict[str, dict[str, Any]] = {}
        self._metrics: dict[str, list[MetricPoint]] = {}

    async def record_metric(
        self, name: str, value: float, label: str | None = None
    ) -> MetricPoint:
        """Record a metric data point.

        Args:
            name: Metric name.
            value: Metric value.
            label: Optional label.

        Returns:
            The recorded metric point.
        """
        point = MetricPoint(
            timestamp=datetime.now(UTC),
            value=value,
            label=label,
        )
        if name not in self._metrics:
            self._metrics[name] = []
        self._metrics[name].append(point)
        logger.debug("Recorded metric", name=name, value=value)
        return point

    async def generate_report(
        self, report_id: str, creator_id: str, period: ReportPeriod
    ) -> dict[str, Any]:
        """Generate an analytics report for a creator.

        Args:
            report_id: Unique report identifier.
            creator_id: Creator identifier.
            period: Report time period.

        Returns:
            Generated analytics report.

        Raises:
            ValueError: If report_id already exists or period is invalid.
        """
        if report_id in self._reports:
            raise ValueError(f"Report {report_id} already exists")
        if period.start >= period.end:
            raise ValueError("Period start must be before end")

        logger.info(
            "Generating report", report_id=report_id, creator_id=creator_id
        )

        period_metrics: dict[str, list[MetricPoint]] = {}
        for name, points in self._metrics.items():
            filtered = [p for p in points if period.start <= p.timestamp <= period.end]
            if filtered:
                period_metrics[name] = filtered

        summary: dict[str, float] = {}
        for name, points in period_metrics.items():
            values = [p.value for p in points]
            summary[f"{name}_total"] = sum(values)
            summary[f"{name}_avg"] = sum(values) / len(values) if values else 0.0
            summary[f"{name}_max"] = max(values) if values else 0.0
            summary[f"{name}_min"] = min(values) if values else 0.0

        insights = self._generate_insights(period_metrics, summary)

        report = {
            "report_id": report_id,
            "creator_id": creator_id,
            "period": period.model_dump(),
            "metrics": {
                name: [p.model_dump() for p in points]
                for name, points in period_metrics.items()
            },
            "summary": summary,
            "insights": insights,
            "generated_at": datetime.now(UTC).isoformat(),
        }

        self._reports[report_id] = report
        return report

    def _generate_insights(
        self,
        metrics: dict[str, list[MetricPoint]],
        summary: dict[str, float],
    ) -> list[str]:
        """Generate actionable insights from metrics.

        Args:
            metrics: Filtered metrics data.
            summary: Summary statistics.

        Returns:
            List of insight strings.
        """
        insights: list[str] = []

        if "revenue_total" in summary and summary["revenue_total"] > 0:
            insights.append(f"Total revenue: ${summary['revenue_total']:.2f}")

        if "subscribers_total" in summary:
            if summary["subscribers_total"] > 1000:
                insights.append("Large subscriber base - focus on retention strategies")
            elif summary["subscribers_total"] < 50:
                insights.append("Growing subscriber base - consider promotional campaigns")

        if "churn_rate_avg" in summary:
            if summary["churn_rate_avg"] > 0.1:
                insights.append("High churn rate - implement retention initiatives")
            elif summary["churn_rate_avg"] < 0.03:
                insights.append("Excellent churn rate - maintain current engagement")

        if "engagement_rate_avg" in summary:
            if summary["engagement_rate_avg"] < 0.05:
                insights.append("Low engagement - experiment with content formats")
            elif summary["engagement_rate_avg"] > 0.15:
                insights.append("Strong engagement - leverage for upselling opportunities")

        if not insights:
            insights.append("Performance within normal ranges")

        return insights

    async def forecast_metric(
        self, name: str, days: int = 30
    ) -> list[MetricPoint]:
        """Forecast a metric for future days using simple linear regression.

        Args:
            name: Metric name to forecast.
            days: Number of days to forecast.

        Returns:
            List of forecasted metric points.

        Raises:
            ValueError: If insufficient data or invalid days.
        """
        if days <= 0:
            raise ValueError("Days must be positive")
        if name not in self._metrics or len(self._metrics[name]) < 2:
            raise ValueError(f"Insufficient data for metric {name}")

        points = self._metrics[name]
        n = len(points)

        x_mean = (n - 1) / 2
        y_mean = sum(p.value for p in points) / n

        numerator = sum(
            (i - x_mean) * (p.value - y_mean) for i, p in enumerate(points)
        )
        denominator = sum((i - x_mean) ** 2 for i in range(n))

        slope = numerator / denominator if denominator != 0 else 0
        intercept = y_mean - slope * x_mean

        last_time = points[-1].timestamp
        forecast: list[MetricPoint] = []
        for i in range(1, days + 1):
            value = intercept + slope * (n - 1 + i)
            forecast.append(
                MetricPoint(
                    timestamp=last_time + timedelta(days=i),
                    value=max(0, value),
                    label="forecast",
                )
            )

        logger.info("Generated forecast", name=name, days=days)
        return forecast

    def get_report(self, report_id: str) -> dict[str, Any] | None:
        """Get a generated report by ID.

        Args:
            report_id: The report identifier.

        Returns:
            The report if found, None otherwise.
        """
        return self._reports.get(report_id)

    def get_available_metrics(self) -> list[str]:
        """Get list of available metric names.

        Returns:
            List of metric names.
        """
        return list(self._metrics.keys())

    def get_report_count(self) -> int:
        """Get total number of generated reports.

        Returns:
            Report count.
        """
        return len(self._reports)
