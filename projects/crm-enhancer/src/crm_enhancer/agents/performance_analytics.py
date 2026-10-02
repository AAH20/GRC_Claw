"""Performance Analytics Agent.

CRM performance metrics and insights for sales teams,
managers, and executives to track and optimize performance.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


class MetricValue(BaseModel):
    """Metric value model."""

    name: str
    value: float
    unit: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    previous_value: float | None = None
    change_percent: float | None = None


class SalesMetrics(BaseModel):
    """Sales performance metrics model."""

    period_start: datetime
    period_end: datetime
    total_revenue: float = 0.0
    deals_won: int = 0
    deals_lost: int = 0
    deals_in_progress: int = 0
    average_deal_size: float = 0.0
    average_sales_cycle_days: float = 0.0
    win_rate: float = 0.0
    pipeline_value: float = 0.0
    quota_attainment: float = 0.0


class AgentEffectiveness(BaseModel):
    """Agent effectiveness metrics model."""

    agent_name: str
    actions_taken: int = 0
    success_rate: float = 0.0
    average_processing_time_seconds: float = 0.0
    user_satisfaction: float | None = None
    cost_savings: float = 0.0


class PerformanceAnalyticsAgent:
    """Agent for CRM performance analytics.

    This agent collects, analyzes, and reports on CRM performance
    metrics to help sales teams and managers optimize their processes.
    """

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize the Performance Analytics Agent.

        Args:
            config: Optional configuration dictionary.
        """
        self.config = config or {}
        self.enabled = self.config.get("enabled", True)
        self.refresh_interval = self.config.get("metrics_refresh_interval_minutes", 15)
        self.retention_days = self.config.get("retention_days", 365)
        logger.info("PerformanceAnalyticsAgent initialized", enabled=self.enabled)

    async def calculate_sales_metrics(
        self,
        period_start: datetime,
        period_end: datetime,
        deals: list[dict[str, Any]],
    ) -> SalesMetrics:
        """Calculate sales performance metrics for a period.

        Args:
            period_start: Start of the period.
            period_end: End of the period.
            deals: List of deal dictionaries with status and value.

        Returns:
            SalesMetrics for the period.
        """
        logger.info(
            "Calculating sales metrics",
            period_start=period_start.isoformat(),
            period_end=period_end.isoformat(),
        )

        won_deals = [d for d in deals if d.get("status") == "closed_won"]
        lost_deals = [d for d in deals if d.get("status") == "closed_lost"]
        open_deals = [d for d in deals if d.get("status") not in ["closed_won", "closed_lost"]]

        total_revenue = sum(d.get("value", 0) for d in won_deals)
        total_deals = len(won_deals) + len(lost_deals)
        win_rate = len(won_deals) / total_deals if total_deals > 0 else 0.0
        avg_deal_size = total_revenue / len(won_deals) if won_deals else 0.0
        pipeline_value = sum(d.get("value", 0) for d in open_deals)

        # Calculate average sales cycle
        sales_cycles = []
        for deal in won_deals:
            created = deal.get("created_date")
            closed = deal.get("closed_date")
            if created and closed:
                if isinstance(created, str):
                    created = datetime.fromisoformat(created.replace("Z", "+00:00"))
                if isinstance(closed, str):
                    closed = datetime.fromisoformat(closed.replace("Z", "+00:00"))
                sales_cycles.append((closed - created).days)

        avg_sales_cycle = sum(sales_cycles) / len(sales_cycles) if sales_cycles else 0.0

        metrics = SalesMetrics(
            period_start=period_start,
            period_end=period_end,
            total_revenue=total_revenue,
            deals_won=len(won_deals),
            deals_lost=len(lost_deals),
            deals_in_progress=len(open_deals),
            average_deal_size=round(avg_deal_size, 2),
            average_sales_cycle_days=round(avg_sales_cycle, 1),
            win_rate=round(win_rate, 2),
            pipeline_value=pipeline_value,
        )

        logger.info(
            "Sales metrics calculated",
            revenue=total_revenue,
            win_rate=win_rate,
            deals_won=len(won_deals),
        )
        return metrics

    async def calculate_agent_effectiveness(
        self,
        agent_name: str,
        actions: list[dict[str, Any]],
    ) -> AgentEffectiveness:
        """Calculate effectiveness metrics for an agent.

        Args:
            agent_name: Name of the agent.
            actions: List of action dictionaries with outcome data.

        Returns:
            AgentEffectiveness metrics.
        """
        logger.info("Calculating agent effectiveness", agent=agent_name)

        total = len(actions)
        if total == 0:
            return AgentEffectiveness(agent_name=agent_name)

        successful = sum(1 for a in actions if a.get("status") == "success")
        success_rate = successful / total

        processing_times = [
            a.get("processing_time_seconds", 0) for a in actions if "processing_time_seconds" in a
        ]
        avg_time = sum(processing_times) / len(processing_times) if processing_times else 0.0

        satisfaction_scores = [
            a.get("user_satisfaction") for a in actions if a.get("user_satisfaction") is not None
        ]
        avg_satisfaction = (
            sum(satisfaction_scores) / len(satisfaction_scores) if satisfaction_scores else None
        )

        cost_savings = sum(a.get("cost_savings", 0) for a in actions)

        return AgentEffectiveness(
            agent_name=agent_name,
            actions_taken=total,
            success_rate=round(success_rate, 2),
            average_processing_time_seconds=round(avg_time, 2),
            user_satisfaction=round(avg_satisfaction, 2) if avg_satisfaction else None,
            cost_savings=round(cost_savings, 2),
        )

    async def generate_weekly_report(
        self,
        sales_metrics: SalesMetrics,
        agent_metrics: list[AgentEffectiveness],
    ) -> dict[str, Any]:
        """Generate a weekly performance report.

        Args:
            sales_metrics: Sales performance metrics.
            agent_metrics: List of agent effectiveness metrics.

        Returns:
            Weekly report dictionary.
        """
        logger.info("Generating weekly report")

        report = {
            "report_type": "weekly",
            "generated_at": datetime.utcnow().isoformat(),
            "period": {
                "start": sales_metrics.period_start.isoformat(),
                "end": sales_metrics.period_end.isoformat(),
            },
            "summary": {
                "total_revenue": sales_metrics.total_revenue,
                "deals_won": sales_metrics.deals_won,
                "win_rate": sales_metrics.win_rate,
                "pipeline_value": sales_metrics.pipeline_value,
                "average_deal_size": sales_metrics.average_deal_size,
                "average_sales_cycle_days": sales_metrics.average_sales_cycle_days,
            },
            "agent_performance": [
                {
                    "agent": m.agent_name,
                    "actions_taken": m.actions_taken,
                    "success_rate": m.success_rate,
                    "cost_savings": m.cost_savings,
                }
                for m in agent_metrics
            ],
            "insights": self._generate_insights(sales_metrics, agent_metrics),
        }

        return report

    def _generate_insights(
        self,
        sales_metrics: SalesMetrics,
        agent_metrics: list[AgentEffectiveness],
    ) -> list[str]:
        """Generate actionable insights from metrics.

        Args:
            sales_metrics: Sales performance metrics.
            agent_metrics: List of agent effectiveness metrics.

        Returns:
            List of insight strings.
        """
        insights: list[str] = []

        if sales_metrics.win_rate < 0.3:
            insights.append("Win rate is below 30% - consider reviewing qualification criteria")
        elif sales_metrics.win_rate > 0.6:
            insights.append("Strong win rate above 60% - consider increasing pipeline volume")

        if sales_metrics.average_sales_cycle_days > 60:
            insights.append("Sales cycle exceeds 60 days - identify bottlenecks in the process")

        if sales_metrics.pipeline_value < sales_metrics.total_revenue * 3:
            insights.append("Pipeline coverage is low - increase prospecting efforts")

        for metric in agent_metrics:
            if metric.success_rate < 0.8:
                insights.append(
                    f"{metric.agent_name} success rate is "
                    f"{metric.success_rate:.0%} - review configuration"
                )

        return insights

    async def get_metric_trend(
        self,
        current: float,
        previous: float,
    ) -> MetricValue:
        """Calculate metric trend with percentage change.

        Args:
            current: Current metric value.
            previous: Previous metric value.

        Returns:
            MetricValue with trend information.
        """
        change = None
        if previous != 0:
            change = round((current - previous) / previous * 100, 2)

        return MetricValue(
            name="metric",
            value=current,
            unit="count",
            previous_value=previous,
            change_percent=change,
        )
