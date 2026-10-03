"""Tier Analytics Agent - Generates analytics and insights for tiers.

Uses LangChain DeepAgents to analyze member behavior, tier performance,
and generate actionable insights for community management.
"""

from __future__ import annotations

from datetime import UTC
from typing import Any
from uuid import UUID

from langchain_core.language_models import BaseLanguageModel
from langchain_core.tools import BaseTool

from tier_management.agents.base import BaseAgent
from tier_management.config.logging_config import get_logger
from tier_management.models.schemas import TierAnalytics

logger = get_logger(__name__)


class TierAnalyticsAgent(BaseAgent[dict[str, Any], TierAnalytics]):
    """Agent that generates analytics and insights for tiers.

    This agent uses LangChain DeepAgents to process member data,
    calculate performance metrics, identify trends, and generate
    actionable insights for community managers.
    """

    def __init__(
        self,
        llm: BaseLanguageModel | None = None,
        tools: list[BaseTool] | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the Tier Analytics Agent.

        Args:
            llm: LangChain language model for analytics reasoning.
            tools: Tools available to the agent (e.g., metrics aggregation).
            **kwargs: Additional configuration parameters.
        """
        super().__init__(name="TierAnalyticsAgent", llm=llm, tools=tools, **kwargs)
        self.analytics_history: list[TierAnalytics] = []

    async def execute(self, input_data: dict[str, Any]) -> TierAnalytics:
        """Generate analytics for a tier over a time period.

        Args:
            input_data: Dictionary containing:
                - tier_id: UUID of the tier to analyze
                - period_start: Start of analysis period
                - period_end: End of analysis period
                - metrics: Optional pre-aggregated metrics data

        Returns:
            TierAnalytics with computed metrics and insights.

        Raises:
            ValueError: If required fields are missing.
        """
        tier_id = input_data.get("tier_id")
        period_start = input_data.get("period_start")
        period_end = input_data.get("period_end")

        if not tier_id or not period_start or not period_end:
            raise ValueError("tier_id, period_start, and period_end are required")

        logger.info(
            "generating_analytics",
            tier_id=str(tier_id),
            period_start=str(period_start),
            period_end=str(period_end),
        )

        analytics = await self._generate_analytics(input_data)
        self.analytics_history.append(analytics)

        logger.info(
            "analytics_complete",
            tier_id=str(tier_id),
            total_members=analytics.total_members,
            insights_count=len(analytics.insights),
        )

        return analytics

    async def _generate_analytics(self, input_data: dict[str, Any]) -> TierAnalytics:
        """Generate the analytics report.

        Args:
            input_data: The analytics input data.

        Returns:
            A TierAnalytics instance with computed metrics.
        """
        from datetime import datetime
        from uuid import uuid4

        tier_id = input_data["tier_id"]
        period_start = input_data["period_start"]
        period_end = input_data["period_end"]
        metrics = input_data.get("metrics", {})

        # Calculate derived metrics
        total_members = metrics.get("total_members", 0)
        active_members = metrics.get("active_members", 0)
        new_members = metrics.get("new_members", 0)
        churned_members = metrics.get("churned_members", 0)

        # Calculate engagement score
        avg_engagement = self._calculate_engagement(metrics)

        # Calculate revenue
        revenue = metrics.get("monthly_fee", 0.0) * total_members

        # Generate insights
        insights = self._generate_insights(metrics, total_members, active_members, churned_members)

        return TierAnalytics(
            id=uuid4(),
            tier_id=UUID(str(tier_id)),
            period_start=period_start,
            period_end=period_end,
            total_members=total_members,
            active_members=active_members,
            new_members=new_members,
            churned_members=churned_members,
            upgrade_requests=metrics.get("upgrade_requests", 0),
            downgrade_requests=metrics.get("downgrade_requests", 0),
            avg_engagement_score=avg_engagement,
            revenue=revenue,
            metrics=metrics,
            insights=insights,
            generated_at=datetime.now(UTC),
            generated_by=self.name,
        )

    def _calculate_engagement(self, metrics: dict[str, Any]) -> float:
        """Calculate average engagement score from metrics.

        Args:
            metrics: Raw metrics data.

        Returns:
            Average engagement score between 0 and 100.
        """
        engagement_metrics = [
            metrics.get("daily_active_rate", 0.0),
            metrics.get("weekly_active_rate", 0.0),
            metrics.get("content_creation_rate", 0.0),
            metrics.get("interaction_rate", 0.0),
        ]
        valid = [m for m in engagement_metrics if m > 0]
        return sum(valid) / len(valid) if valid else 0.0

    def _generate_insights(
        self,
        metrics: dict[str, Any],
        total_members: int,
        active_members: int,
        churned_members: int,
    ) -> list[str]:
        """Generate actionable insights from analytics data.

        Args:
            metrics: Raw metrics data.
            total_members: Total member count.
            active_members: Active member count.
            churned_members: Churned member count.

        Returns:
            List of insight strings.
        """
        insights: list[str] = []

        # Churn analysis
        if total_members > 0:
            churn_rate = churned_members / total_members
            if churn_rate > 0.1:
                insights.append(
                    f"High churn rate detected: {churn_rate:.1%}. Consider retention initiatives."
                )
            elif churn_rate < 0.02:
                insights.append(f"Excellent retention: churn rate at {churn_rate:.1%}.")

        # Engagement analysis
        if total_members > 0:
            activity_rate = active_members / total_members
            if activity_rate < 0.3:
                insights.append(
                    f"Low activity rate: {activity_rate:.1%}. Consider engagement campaigns."
                )
            elif activity_rate > 0.7:
                insights.append(f"Strong engagement: {activity_rate:.1%} activity rate.")

        # Growth analysis
        if total_members > 0:
            growth_rate = (metrics.get("new_members", 0) - churned_members) / total_members
            if growth_rate > 0.05:
                insights.append(f"Healthy growth: {growth_rate:.1%} net member increase.")
            elif growth_rate < 0:
                insights.append(f"Declining membership: {growth_rate:.1%} net decrease.")

        if not insights:
            insights.append("Tier performance is stable. No significant changes detected.")

        return insights
