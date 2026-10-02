"""Analytics API routes."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Query

from content_marketplace.agents.listing_manager import ListingManagerAgent
from content_marketplace.agents.marketplace_analytics import MarketplaceAnalyticsAgent
from content_marketplace.agents.transaction_processor import TransactionProcessorAgent
from content_marketplace.models.analytics import MarketplaceAnalytics

logger = logging.getLogger(__name__)
router = APIRouter()


_analytics_agent_instance: MarketplaceAnalyticsAgent | None = None


def get_analytics_agent() -> MarketplaceAnalyticsAgent:
    """Dependency to get the analytics agent (singleton)."""
    global _analytics_agent_instance
    if _analytics_agent_instance is None:
        _analytics_agent_instance = MarketplaceAnalyticsAgent()
    return _analytics_agent_instance


def get_listing_agent() -> ListingManagerAgent:
    """Dependency to get the listing agent (singleton)."""
    from content_marketplace.api.listings import get_listing_agent as _get_listing_agent
    return _get_listing_agent()


def get_transaction_agent() -> TransactionProcessorAgent:
    """Dependency to get the transaction agent (singleton)."""
    from content_marketplace.api.transactions import get_transaction_agent as _get_transaction_agent
    return _get_transaction_agent()


@router.get("/report", response_model=MarketplaceAnalytics)
async def get_analytics_report(
    days: int = Query(30, ge=1, le=365),
    analytics_agent: MarketplaceAnalyticsAgent = Depends(get_analytics_agent),  # noqa: B008
    listing_agent: ListingManagerAgent = Depends(get_listing_agent),  # noqa: B008
    transaction_agent: TransactionProcessorAgent = Depends(get_transaction_agent),  # noqa: B008
) -> MarketplaceAnalytics:
    """Generate marketplace analytics report."""
    period_end = datetime.now(tz=UTC)
    period_start = period_end - timedelta(days=days)

    listings = await listing_agent.list_listings(limit=1000)
    transactions = await transaction_agent.list_transactions(limit=1000)

    return await analytics_agent.generate_analytics(
        period_start=period_start,
        period_end=period_end,
        listings=listings,
        transactions=transactions,
    )


@router.get("/insights")
async def get_marketplace_insights(
    days: int = Query(30, ge=1, le=365),
    analytics_agent: MarketplaceAnalyticsAgent = Depends(get_analytics_agent),  # noqa: B008
    listing_agent: ListingManagerAgent = Depends(get_listing_agent),  # noqa: B008
    transaction_agent: TransactionProcessorAgent = Depends(get_transaction_agent),  # noqa: B008
) -> dict:
    """Get AI-powered marketplace insights."""
    period_end = datetime.now(tz=UTC)
    period_start = period_end - timedelta(days=days)

    listings = await listing_agent.list_listings(limit=1000)
    transactions = await transaction_agent.list_transactions(limit=1000)

    analytics = await analytics_agent.generate_analytics(
        period_start=period_start,
        period_end=period_end,
        listings=listings,
        transactions=transactions,
    )
    return await analytics_agent.get_insights(analytics)


@router.get("/compare")
async def compare_periods(
    current_days: int = Query(30, ge=1, le=365),
    previous_days: int = Query(30, ge=1, le=365),
    analytics_agent: MarketplaceAnalyticsAgent = Depends(get_analytics_agent),  # noqa: B008
    listing_agent: ListingManagerAgent = Depends(get_listing_agent),  # noqa: B008
    transaction_agent: TransactionProcessorAgent = Depends(get_transaction_agent),  # noqa: B008
) -> dict:
    """Compare two analytics periods."""
    now = datetime.now(tz=UTC)

    current_end = now
    current_start = now - timedelta(days=current_days)
    previous_end = current_start
    previous_start = previous_end - timedelta(days=previous_days)

    listings = await listing_agent.list_listings(limit=1000)
    transactions = await transaction_agent.list_transactions(limit=1000)

    current = await analytics_agent.generate_analytics(
        period_start=current_start, period_end=current_end,
        listings=listings, transactions=transactions,
    )
    previous = await analytics_agent.generate_analytics(
        period_start=previous_start, period_end=previous_end,
        listings=listings, transactions=transactions,
    )
    return await analytics_agent.compare_periods(current, previous)


@router.get("/demand-prediction/{category}")
async def predict_demand(
    category: str,
    analytics_agent: MarketplaceAnalyticsAgent = Depends(get_analytics_agent),  # noqa: B008
) -> dict:
    """Predict demand for a category."""
    from content_marketplace.models.analytics import TimeSeriesData
    historical = [
        TimeSeriesData(timestamp=datetime.now(tz=UTC) - timedelta(days=i), value=100.0 + i * 10)
        for i in range(30)
    ]
    return await analytics_agent.predict_demand(category, historical)
