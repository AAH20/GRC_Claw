"""Tests for content marketplace agents."""

from __future__ import annotations

import pytest

from ugc_marketplace.agents.content_marketplace import (
    ListingManagerAgent, MarketplaceAnalyticsAgent, PricingOptimizerAgent,
    TransactionProcessorAgent, TrustScorerAgent)


@pytest.mark.asyncio
async def test_listing_manager_agent() -> None:
    """Test listing manager agent."""
    agent = ListingManagerAgent()
    assert agent is not None


@pytest.mark.asyncio
async def test_marketplace_analytics_agent() -> None:
    """Test marketplace analytics agent."""
    agent = MarketplaceAnalyticsAgent()
    assert agent is not None


@pytest.mark.asyncio
async def test_pricing_optimizer_agent() -> None:
    """Test pricing optimizer agent."""
    agent = PricingOptimizerAgent()
    assert agent is not None


@pytest.mark.asyncio
async def test_transaction_processor_agent() -> None:
    """Test transaction processor agent."""
    agent = TransactionProcessorAgent()
    assert agent is not None


@pytest.mark.asyncio
async def test_trust_scorer_agent() -> None:
    """Test trust scorer agent."""
    agent = TrustScorerAgent()
    assert agent is not None
