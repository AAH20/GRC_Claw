"""Tests for creator analytics agents."""

from __future__ import annotations

import pytest

from ugc_marketplace.agents.creator_analytics import (AudienceAnalyzerAgent,
                                                      ContentPerformanceAgent,
                                                      EngagementAnalyzerAgent,
                                                      GrowthPredictorAgent,
                                                      RevenueTrackerAgent)


@pytest.mark.asyncio
async def test_audience_analyzer_agent() -> None:
    """Test audience analyzer agent."""
    agent = AudienceAnalyzerAgent()
    result = await agent.execute("creator_123")
    assert result["creator_id"] == "creator_123"


@pytest.mark.asyncio
async def test_content_performance_agent() -> None:
    """Test content performance agent."""
    agent = ContentPerformanceAgent()
    result = await agent.execute("content_123")
    assert result["content_id"] == "content_123"


@pytest.mark.asyncio
async def test_engagement_analyzer_agent() -> None:
    """Test engagement analyzer agent."""
    agent = EngagementAnalyzerAgent()
    result = await agent.execute("creator_123")
    assert result["creator_id"] == "creator_123"


@pytest.mark.asyncio
async def test_growth_predictor_agent() -> None:
    """Test growth predictor agent."""
    agent = GrowthPredictorAgent()
    result = await agent.execute("creator_123")
    assert result["creator_id"] == "creator_123"


@pytest.mark.asyncio
async def test_revenue_tracker_agent() -> None:
    """Test revenue tracker agent."""
    agent = RevenueTrackerAgent()
    result = await agent.execute("creator_123")
    assert result["creator_id"] == "creator_123"
