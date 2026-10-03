"""Tests for creator monetization agents."""

from __future__ import annotations

from decimal import Decimal

import pytest

from ugc_marketplace.agents.creator_monetization import (
    AnalyticsAgent,
    PayoutManagerAgent,
    RevenueOptimizerAgent,
    SubscriptionAgent,
    TierRecommenderAgent,
)


@pytest.mark.asyncio
async def test_analytics_agent() -> None:
    """Test analytics agent."""
    agent = AnalyticsAgent()
    point = await agent.record_metric("revenue", 100.0)
    assert point.value == 100.0


@pytest.mark.asyncio
async def test_payout_manager_agent() -> None:
    """Test payout manager agent."""
    agent = PayoutManagerAgent()
    payout = await agent.create_payout("creator_1", Decimal("100.00"))
    assert payout["status"] == "pending"


@pytest.mark.asyncio
async def test_revenue_optimizer_agent() -> None:
    """Test revenue optimizer agent."""
    agent = RevenueOptimizerAgent()
    suggestions = await agent.generate_suggestions("creator_1")
    assert isinstance(suggestions, list)


@pytest.mark.asyncio
async def test_subscription_agent() -> None:
    """Test subscription agent."""
    agent = SubscriptionAgent()
    sub = await agent.create_subscription(
        "creator_1", "user_1", "tier_1", Decimal("10.00")
    )
    assert sub["status"] == "active"


@pytest.mark.asyncio
async def test_tier_recommender_agent() -> None:
    """Test tier recommender agent."""
    agent = TierRecommenderAgent()
    from ugc_marketplace.agents.creator_monetization.tier_recommender import CreatorProfile

    profile = CreatorProfile(creator_id="creator_1", subscriber_count=500)
    recommendations = await agent.recommend_tiers(profile)
    assert len(recommendations) > 0
