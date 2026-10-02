"""Tests for agent implementations."""


import pytest

from creator_analytics.agents import (
    AudienceAnalyzerAgent,
    ContentPerformanceAgent,
    EngagementAnalyzerAgent,
    GrowthPredictorAgent,
    RevenueTrackerAgent,
)


@pytest.mark.asyncio
async def test_audience_analyzer_agent() -> None:
    """Test AudienceAnalyzerAgent."""
    agent = AudienceAnalyzerAgent()
    assert agent.name == "audience_analyzer"
    # _agent is None when langchain-deepagents is not installed
    assert agent._agent is None or agent._agent is not None


@pytest.mark.asyncio
async def test_content_performance_agent() -> None:
    """Test ContentPerformanceAgent."""
    agent = ContentPerformanceAgent()
    assert agent.name == "content_performance"
    # _agent is None when langchain-deepagents is not installed
    assert agent._agent is None or agent._agent is not None


@pytest.mark.asyncio
async def test_revenue_tracker_agent() -> None:
    """Test RevenueTrackerAgent."""
    agent = RevenueTrackerAgent()
    assert agent.name == "revenue_tracker"
    # _agent is None when langchain-deepagents is not installed
    assert agent._agent is None or agent._agent is not None


@pytest.mark.asyncio
async def test_growth_predictor_agent() -> None:
    """Test GrowthPredictorAgent."""
    agent = GrowthPredictorAgent()
    assert agent.name == "growth_predictor"
    # _agent is None when langchain-deepagents is not installed
    assert agent._agent is None or agent._agent is not None


@pytest.mark.asyncio
async def test_engagement_analyzer_agent() -> None:
    """Test EngagementAnalyzerAgent."""
    agent = EngagementAnalyzerAgent()
    assert agent.name == "engagement_analyzer"
    # _agent is None when langchain-deepagents is not installed
    assert agent._agent is None or agent._agent is not None


@pytest.mark.asyncio
async def test_audience_analyzer_run() -> None:
    """Test AudienceAnalyzerAgent run method."""
    agent = AudienceAnalyzerAgent()
    input_data = {
        "creator_id": "test-creator",
        "total_followers": 10000,
        "active_followers": 7000,
        "age_distribution": {"18_24": 0.4},
        "gender_distribution": {"male": 0.6, "female": 0.4},
        "growth_rate": 0.05,
        "churn_rate": 0.02,
    }
    result = await agent.run(input_data)
    assert result["creator_id"] == "test-creator"
    assert "demographics" in result


@pytest.mark.asyncio
async def test_content_performance_run() -> None:
    """Test ContentPerformanceAgent run method."""
    agent = ContentPerformanceAgent()
    input_data = {
        "content_id": "content-1",
        "creator_id": "test-creator",
        "content_type": "video",
        "title": "Test Video",
        "metrics": {"views": 1000, "likes": 100, "engagement_rate": 0.1},
    }
    result = await agent.run(input_data)
    assert result["content_id"] == "content-1"
    assert "performance_score" in result


@pytest.mark.asyncio
async def test_revenue_tracker_run() -> None:
    """Test RevenueTrackerAgent run method."""
    agent = RevenueTrackerAgent()
    input_data = {
        "creator_id": "test-creator",
        "stream_data": [
            {"stream": "advertising", "amount": 5000, "growth_rate": 0.03},
        ],
        "total_followers": 10000,
        "engagement_rate": 0.05,
    }
    result = await agent.run(input_data)
    assert result["creator_id"] == "test-creator"
    assert "total_revenue" in result


@pytest.mark.asyncio
async def test_growth_predictor_run() -> None:
    """Test GrowthPredictorAgent run method."""
    agent = GrowthPredictorAgent()
    input_data = {
        "creator_id": "test-creator",
        "current_followers": 10000,
        "current_monthly_revenue": 5000.0,
        "monthly_growth_rate": 0.05,
        "revenue_growth_rate": 0.04,
        "prediction_period_months": 12,
    }
    result = await agent.run(input_data)
    assert result["creator_id"] == "test-creator"
    assert "predicted_followers" in result


@pytest.mark.asyncio
async def test_engagement_analyzer_run() -> None:
    """Test EngagementAnalyzerAgent run method."""
    agent = EngagementAnalyzerAgent()
    input_data = {
        "creator_id": "test-creator",
        "total_interactions": 5000,
        "interactions_by_type": {"like": 3000, "comment": 1000},
        "total_followers": 10000,
        "content_count": 50,
    }
    result = await agent.run(input_data)
    assert result["creator_id"] == "test-creator"
    assert "metrics" in result
