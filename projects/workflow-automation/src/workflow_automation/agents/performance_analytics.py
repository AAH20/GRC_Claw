"""Performance Analytics Agent - tracks KPIs and generates insights."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import StrEnum
from typing import Any

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


class MetricType(StrEnum):
    """Types of metrics that can be tracked."""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    RATE = "rate"


class MetricUnit(StrEnum):
    """Units for metrics."""

    COUNT = "count"
    PERCENTAGE = "percentage"
    DURATION_SECONDS = "duration_seconds"
    CURRENCY = "currency"
    BYTES = "bytes"


class MetricEvent(BaseModel):
    """A single metric event."""

    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    metric_name: str
    metric_type: MetricType
    value: float
    unit: MetricUnit = MetricUnit.COUNT
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    labels: dict[str, str] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class MetricAggregate(BaseModel):
    """Aggregated metric data."""

    metric_name: str
    count: int = 0
    sum: float = 0.0
    min: float = 0.0
    max: float = 0.0
    avg: float = 0.0
    p50: float = 0.0
    p95: float = 0.0
    p99: float = 0.0
    unit: MetricUnit = MetricUnit.COUNT
    period_start: datetime | None = None
    period_end: datetime | None = None


class KPI(BaseModel):
    """Key Performance Indicator."""

    kpi_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str = ""
    target_value: float
    current_value: float = 0.0
    unit: MetricUnit = MetricUnit.COUNT
    trend: str = "stable"  # improving, declining, stable
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class ReportPeriod(BaseModel):
    """Report time period."""

    start: datetime
    end: datetime
    granularity: str = "hour"  # minute, hour, day, week, month


class PerformanceReport(BaseModel):
    """Complete performance report."""

    report_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    period: ReportPeriod
    kpis: list[KPI] = Field(default_factory=list)
    metrics: list[MetricAggregate] = Field(default_factory=list)
    insights: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class TrackMetricRequest(BaseModel):
    """Request to track a metric event."""

    metric_name: str
    metric_type: MetricType = MetricType.COUNTER
    value: float
    unit: MetricUnit = MetricUnit.COUNT
    labels: dict[str, str] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ReportRequest(BaseModel):
    """Request to generate a performance report."""

    period: ReportPeriod
    metric_names: list[str] = Field(default_factory=list)
    include_insights: bool = True
    include_recommendations: bool = True


@dataclass
class PerformanceAnalyticsAgent:
    """Agent responsible for tracking KPIs and generating performance insights.

    This agent collects metric events, aggregates data, calculates KPIs,
    and generates actionable insights and recommendations.
    """

    _events: list[MetricEvent] = field(default_factory=list)
    _kpis: dict[str, KPI] = field(default_factory=dict)
    _reports: list[PerformanceReport] = field(default_factory=list)
    _is_initialized: bool = False

    async def initialize(self) -> None:
        """Initialize the performance analytics agent."""
        logger.info("Initializing PerformanceAnalyticsAgent")
        self._register_default_kpis()
        self._is_initialized = True

    def _register_default_kpis(self) -> None:
        """Register default marketing KPIs."""
        default_kpis = [
            KPI(
                name="workflow_execution_rate",
                description="Percentage of workflow executions that complete successfully",
                target_value=95.0,
                unit=MetricUnit.PERCENTAGE,
            ),
            KPI(
                name="average_execution_time",
                description="Average time to complete a workflow execution",
                target_value=60.0,
                unit=MetricUnit.DURATION_SECONDS,
            ),
            KPI(
                name="leads_processed",
                description="Total number of leads processed through workflows",
                target_value=1000.0,
                unit=MetricUnit.COUNT,
            ),
            KPI(
                name="cost_per_lead",
                description="Average cost to acquire a lead through automated workflows",
                target_value=5.0,
                unit=MetricUnit.CURRENCY,
            ),
            KPI(
                name="integration_uptime",
                description="Percentage of time integrations are operational",
                target_value=99.9,
                unit=MetricUnit.PERCENTAGE,
            ),
        ]

        for kpi in default_kpis:
            self._kpis[kpi.name] = kpi

    async def track_metric(self, request: TrackMetricRequest) -> MetricEvent:
        """Track a metric event.

        Args:
            request: Metric tracking request.

        Returns:
            The recorded metric event.

        Raises:
            RuntimeError: If the agent is not initialized.
        """
        if not self._is_initialized:
            raise RuntimeError("Agent not initialized. Call initialize() first.")

        event = MetricEvent(
            metric_name=request.metric_name,
            metric_type=request.metric_type,
            value=request.value,
            unit=request.unit,
            labels=request.labels,
            metadata=request.metadata,
        )

        self._events.append(event)

        # Update related KPIs
        await self._update_kpis(event)

        logger.info(
            "Tracked metric",
            metric_name=request.metric_name,
            value=request.value,
            unit=request.unit.value,
        )

        return event

    async def _update_kpis(self, event: MetricEvent) -> None:
        """Update KPIs based on a new metric event.

        Args:
            event: The metric event to process.
        """
        # Map metric names to KPIs
        kpi_mapping = {
            "workflow_execution_success": "workflow_execution_rate",
            "workflow_execution_time": "average_execution_time",
            "lead_processed": "leads_processed",
            "integration_health_check": "integration_uptime",
        }

        kpi_name = kpi_mapping.get(event.metric_name)
        if not kpi_name or kpi_name not in self._kpis:
            return

        kpi = self._kpis[kpi_name]

        if event.metric_name == "workflow_execution_success":
            # Calculate success rate
            recent_events = [
                e
                for e in self._events
                if e.metric_name == "workflow_execution_success"
                and e.timestamp > datetime.utcnow() - timedelta(hours=24)
            ]
            if recent_events:
                success_count = sum(1 for e in recent_events if e.value == 1.0)
                kpi.current_value = (success_count / len(recent_events)) * 100

        elif event.metric_name == "workflow_execution_time":
            # Calculate average execution time
            recent_events = [
                e
                for e in self._events
                if e.metric_name == "workflow_execution_time"
                and e.timestamp > datetime.utcnow() - timedelta(hours=24)
            ]
            if recent_events:
                kpi.current_value = sum(e.value for e in recent_events) / len(recent_events)

        elif event.metric_name == "lead_processed":
            # Sum leads processed
            kpi.current_value += event.value

        elif event.metric_name == "integration_health_check":
            # Calculate uptime percentage
            recent_events = [
                e
                for e in self._events
                if e.metric_name == "integration_health_check"
                and e.timestamp > datetime.utcnow() - timedelta(hours=24)
            ]
            if recent_events:
                healthy_count = sum(1 for e in recent_events if e.value == 1.0)
                kpi.current_value = (healthy_count / len(recent_events)) * 100

        kpi.last_updated = datetime.utcnow()

        # Determine trend
        if kpi.current_value >= kpi.target_value:
            kpi.trend = "improving"
        elif kpi.current_value < kpi.target_value * 0.8:
            kpi.trend = "declining"
        else:
            kpi.trend = "stable"

    async def generate_report(self, request: ReportRequest) -> PerformanceReport:
        """Generate a performance report.

        Args:
            request: Report generation request.

        Returns:
            Complete performance report.

        Raises:
            RuntimeError: If the agent is not initialized.
        """
        if not self._is_initialized:
            raise RuntimeError("Agent not initialized. Call initialize() first.")

        logger.info(
            "Generating performance report",
            start=request.period.start.isoformat(),
            end=request.period.end.isoformat(),
        )

        # Aggregate metrics for the period
        metrics = await self._aggregate_metrics(
            request.period, request.metric_names
        )

        # Get current KPIs
        kpis = list(self._kpis.values())

        # Generate insights
        insights: list[str] = []
        if request.include_insights:
            insights = await self._generate_insights(kpis, metrics)

        # Generate recommendations
        recommendations: list[str] = []
        if request.include_recommendations:
            recommendations = await self._generate_recommendations(kpis, insights)

        report = PerformanceReport(
            period=request.period,
            kpis=kpis,
            metrics=metrics,
            insights=insights,
            recommendations=recommendations,
        )

        self._reports.append(report)

        logger.info(
            "Performance report generated",
            report_id=report.report_id,
            kpis_count=len(kpis),
            metrics_count=len(metrics),
            insights_count=len(insights),
        )

        return report

    async def _aggregate_metrics(
        self, period: ReportPeriod, metric_names: list[str]
    ) -> list[MetricAggregate]:
        """Aggregate metrics for a time period.

        Args:
            period: Report period.
            metric_names: Metrics to aggregate.

        Returns:
            List of aggregated metrics.
        """
        # Filter events by period and metric names
        filtered_events = [
            e
            for e in self._events
            if period.start <= e.timestamp <= period.end
            and (not metric_names or e.metric_name in metric_names)
        ]

        # Group by metric name
        metric_groups: dict[str, list[MetricEvent]] = {}
        for event in filtered_events:
            if event.metric_name not in metric_groups:
                metric_groups[event.metric_name] = []
            metric_groups[event.metric_name].append(event)

        aggregates: list[MetricAggregate] = []

        for metric_name, events in metric_groups.items():
            if not events:
                continue

            values = sorted([e.value for e in events])
            count = len(values)
            total = sum(values)

            aggregates.append(
                MetricAggregate(
                    metric_name=metric_name,
                    count=count,
                    sum=total,
                    min=values[0],
                    max=values[-1],
                    avg=total / count if count > 0 else 0,
                    p50=values[count // 2] if count > 0 else 0,
                    p95=values[int(count * 0.95)] if count > 0 else 0,
                    p99=values[int(count * 0.99)] if count > 0 else 0,
                    unit=events[0].unit,
                    period_start=period.start,
                    period_end=period.end,
                )
            )

        return aggregates

    async def _generate_insights(
        self, kpis: list[KPI], metrics: list[MetricAggregate]
    ) -> list[str]:
        """Generate insights from KPI and metric data.

        Args:
            kpis: Current KPI values.
            metrics: Aggregated metrics.

        Returns:
            List of insight strings.
        """
        insights: list[str] = []

        for kpi in kpis:
            if kpi.trend == "declining":
                insights.append(
                    f"KPI '{kpi.name}' is declining. Current: {kpi.current_value:.2f}, "
                    f"Target: {kpi.target_value:.2f}. Immediate attention required."
                )
            elif kpi.trend == "stable" and kpi.current_value < kpi.target_value:
                insights.append(
                    f"KPI '{kpi.name}' is stable but below target. "
                    f"Current: {kpi.current_value:.2f}, Target: {kpi.target_value:.2f}."
                )
            elif kpi.trend == "improving":
                insights.append(
                    f"KPI '{kpi.name}' is improving and meeting targets. "
                    f"Current: {kpi.current_value:.2f}, Target: {kpi.target_value:.2f}."
                )

        # Analyze metric patterns
        for metric in metrics:
            if metric.count > 0 and metric.max > metric.avg * 3:
                insights.append(
                    f"Metric '{metric.metric_name}' shows high variance. "
                    f"Max: {metric.max:.2f}, Avg: {metric.avg:.2f}. "
                    f"Consider investigating outliers."
                )

        return insights

    async def _generate_recommendations(
        self, kpis: list[KPI], insights: list[str]
    ) -> list[str]:
        """Generate recommendations based on KPIs and insights.

        Args:
            kpis: Current KPI values.
            insights: Generated insights.

        Returns:
            List of recommendation strings.
        """
        recommendations: list[str] = []

        for kpi in kpis:
            if kpi.name == "workflow_execution_rate" and kpi.trend == "declining":
                recommendations.append(
                    "Review failed workflow executions and implement better error handling."
                )
            elif kpi.name == "average_execution_time" and kpi.current_value > kpi.target_value:
                recommendations.append(
                    "Optimize workflow steps to reduce execution time. "
                    "Consider parallelizing independent steps."
                )
            elif kpi.name == "integration_uptime" and kpi.current_value < kpi.target_value:
                recommendations.append(
                    "Implement health checks and automatic failover for integrations."
                )
            elif kpi.name == "cost_per_lead" and kpi.current_value > kpi.target_value:
                recommendations.append(
                    "Review and optimize marketing spend. Focus on high-converting channels."
                )

        return recommendations

    async def get_kpis(self) -> list[KPI]:
        """Get all registered KPIs.

        Returns:
            List of KPIs.
        """
        return list(self._kpis.values())

    async def get_recent_events(
        self,
        metric_name: str | None = None,
        limit: int = 100,
    ) -> list[MetricEvent]:
        """Get recent metric events.

        Args:
            metric_name: Filter by metric name.
            limit: Maximum number of events to return.

        Returns:
            List of recent metric events.
        """
        events = self._events
        if metric_name:
            events = [e for e in events if e.metric_name == metric_name]
        return sorted(events, key=lambda e: e.timestamp, reverse=True)[:limit]

    async def get_report_history(self, limit: int = 10) -> list[PerformanceReport]:
        """Get report generation history.

        Args:
            limit: Maximum number of reports to return.

        Returns:
            List of recent reports.
        """
        return sorted(self._reports, key=lambda r: r.generated_at, reverse=True)[:limit]
