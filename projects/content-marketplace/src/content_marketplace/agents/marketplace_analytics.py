"""Marketplace Analytics Agent using LangChain DeepAgents."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Optional
from uuid import UUID

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage

from content_marketplace.models.analytics import (
    AnalyticsSummary,
    MarketplaceAnalytics,
    TimeSeriesData,
)

logger = logging.getLogger(__name__)


class MarketplaceAnalyticsAgent:
    """Agent responsible for marketplace analytics and insights.

    Uses LangChain DeepAgents to analyze marketplace data,
    generate reports, and provide actionable insights.
    """

    def __init__(self, llm: Optional[BaseChatModel] = None) -> None:
        """Initialize the MarketplaceAnalyticsAgent.

        Args:
            llm: Optional LangChain chat model for AI-powered analytics.
        """
        self.llm = llm
        self._analytics_cache: dict[str, MarketplaceAnalytics] = {}

    async def generate_analytics(
        self,
        period_start: datetime,
        period_end: datetime,
        listings: list[Any],
        transactions: list[Any],
    ) -> MarketplaceAnalytics:
        """Generate marketplace analytics for a given period.

        Args:
            period_start: Start of the analytics period.
            period_end: End of the analytics period.
            listings: List of listings in the period.
            transactions: List of transactions in the period.

        Returns:
            Marketplace analytics data.
        """
        total_listings = len(listings)
        active_listings = sum(1 for l in listings if l.status == "active")
        total_transactions = len(transactions)
        completed_transactions = [t for t in transactions if t.status == "completed"]
        total_volume = sum(t.amount for t in completed_transactions)
        avg_transaction = total_volume / len(completed_transactions) if completed_transactions else 0.0

        # Category breakdown
        category_breakdown: dict[str, int] = {}
        for listing in listings:
            category_breakdown[listing.category] = category_breakdown.get(listing.category, 0) + 1

        # Seller leaderboard
        seller_volume: dict[str, float] = {}
        for t in completed_transactions:
            seller_volume[t.seller_id] = seller_volume.get(t.seller_id, 0.0) + t.amount
        seller_leaderboard = [
            {"seller_id": k, "volume": v}
            for k, v in sorted(seller_volume.items(), key=lambda x: x[1], reverse=True)[:10]
        ]

        # Buyer leaderboard
        buyer_volume: dict[str, float] = {}
        for t in completed_transactions:
            buyer_volume[t.buyer_id] = buyer_volume.get(t.buyer_id, 0.0) + t.amount
        buyer_leaderboard = [
            {"buyer_id": k, "volume": v}
            for k, v in sorted(buyer_volume.items(), key=lambda x: x[1], reverse=True)[:10]
        ]

        # Revenue trend (daily)
        revenue_trend: list[TimeSeriesData] = []
        current = period_start
        while current <= period_end:
            day_end = current + timedelta(days=1)
            day_volume = sum(
                t.amount
                for t in completed_transactions
                if current <= t.created_at < day_end
            )
            revenue_trend.append(TimeSeriesData(timestamp=current, value=day_volume))
            current = day_end

        # Conversion rate
        conversion_rate = (
            len(completed_transactions) / total_listings if total_listings > 0 else 0.0
        )

        summary = AnalyticsSummary(
            total_listings=total_listings,
            active_listings=active_listings,
            total_transactions=total_transactions,
            total_volume=total_volume,
            average_transaction_value=avg_transaction,
            conversion_rate=conversion_rate,
            top_categories=[
                {"category": k, "count": v}
                for k, v in sorted(category_breakdown.items(), key=lambda x: x[1], reverse=True)[:5]
            ],
            revenue_trend=revenue_trend,
        )

        analytics = MarketplaceAnalytics(
            period_start=period_start,
            period_end=period_end,
            summary=summary,
            category_breakdown=category_breakdown,
            seller_leaderboard=seller_leaderboard,
            buyer_leaderboard=buyer_leaderboard,
        )

        logger.info("Generated analytics for period %s to %s", period_start, period_end)
        return analytics

    async def get_insights(self, analytics: MarketplaceAnalytics) -> dict[str, Any]:
        """Use AI to generate actionable insights from analytics.

        Args:
            analytics: The marketplace analytics data.

        Returns:
            Dictionary with insights and recommendations.
        """
        if self.llm is None:
            return {
                "insights": ["No AI model available for insights"],
                "recommendations": [],
            }

        prompt = (
            f"Analyze this marketplace data and provide actionable insights:\n"
            f"Total listings: {analytics.summary.total_listings}\n"
            f"Active listings: {analytics.summary.active_listings}\n"
            f"Total transactions: {analytics.summary.total_transactions}\n"
            f"Total volume: {analytics.summary.total_volume}\n"
            f"Conversion rate: {analytics.summary.conversion_rate}\n"
            f"Top categories: {analytics.summary.top_categories}\n"
            f"Provide 3-5 actionable insights and recommendations.\n"
            f"Respond with JSON: {{\"insights\": [\"...\"], \"recommendations\": [\"...\"]}}"
        )

        response = await self.llm.ainvoke([HumanMessage(content=prompt)])
        import json
        try:
            result = json.loads(response.content)
            return result
        except (json.JSONDecodeError, TypeError):
            return {"insights": [], "recommendations": []}

    async def compare_periods(
        self,
        current: MarketplaceAnalytics,
        previous: MarketplaceAnalytics,
    ) -> dict[str, Any]:
        """Compare two analytics periods.

        Args:
            current: Current period analytics.
            previous: Previous period analytics.

        Returns:
            Dictionary with period-over-period changes.
        """
        def pct_change(new: float, old: float) -> float:
            if old == 0:
                return 0.0
            return round(((new - old) / old) * 100, 2)

        return {
            "volume_change_pct": pct_change(
                current.summary.total_volume, previous.summary.total_volume
            ),
            "transaction_change_pct": pct_change(
                float(current.summary.total_transactions),
                float(previous.summary.total_transactions),
            ),
            "conversion_rate_change_pct": pct_change(
                current.summary.conversion_rate, previous.summary.conversion_rate
            ),
            "active_listings_change_pct": pct_change(
                float(current.summary.active_listings),
                float(previous.summary.active_listings),
            ),
        }

    async def predict_demand(
        self,
        category: str,
        historical_data: list[TimeSeriesData],
    ) -> dict[str, Any]:
        """Use AI to predict future demand for a category.

        Args:
            category: The content category.
            historical_data: Historical time series data.

        Returns:
            Dictionary with demand predictions.
        """
        if self.llm is None:
            return {"predicted_demand": "medium", "confidence": 0.0}

        data_str = ", ".join(f"{d.timestamp.isoformat()}:{d.value}" for d in historical_data[-30:])
        prompt = (
            f"Predict demand for category '{category}' based on historical data:\n"
            f"{data_str}\n"
            f"Respond with JSON: {{\"predicted_demand\": \"low/medium/high\", \"confidence\": 0.0-1.0}}"
        )

        response = await self.llm.ainvoke([HumanMessage(content=prompt)])
        import json
        try:
            result = json.loads(response.content)
            return result
        except (json.JSONDecodeError, TypeError):
            return {"predicted_demand": "medium", "confidence": 0.0}
