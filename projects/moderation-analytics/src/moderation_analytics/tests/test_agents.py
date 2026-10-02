"""Tests for agents."""

from __future__ import annotations

import pytest

from moderation_analytics.agents import (
    AnalyticsExplainerAgent,
    ModerationPredictorAgent,
    ModeratorPerformanceAgent,
    PolicyEffectivenessAgent,
    TrendAnalyzerAgent,
)


@pytest.mark.asyncio
async def test_trend_analyzer_agent():
    """Test TrendAnalyzerAgent."""
    agent = TrendAnalyzerAgent()
    data = [
        {"count": 100, "avg_severity": 2.0},
        {"count": 110, "avg_severity": 2.1},
        {"count": 120, "avg_severity": 2.2},
    ]
    result = await agent.run(data=data)
    assert isinstance(result, list)


@pytest.mark.asyncio
async def test_moderator_performance_agent():
    """Test ModeratorPerformanceAgent."""
    agent = ModeratorPerformanceAgent()
    data = [
        {
            "moderator_id": "mod_001",
            "moderator_name": "Test Mod",
            "total_reviews": 100,
            "correct_decisions": 95,
            "escalations": 5,
            "avg_response_time": 1.5,
            "consistency_score": 0.9,
        }
    ]
    result = await agent.run(moderator_data=data)
    assert len(result) == 1
    assert result[0].moderator_id == "mod_001"
    assert result[0].accuracy == 0.95


@pytest.mark.asyncio
async def test_policy_effectiveness_agent():
    """Test PolicyEffectivenessAgent."""
    agent = PolicyEffectivenessAgent()
    data = [
        {
            "policy_id": "pol_001",
            "policy_name": "Test Policy",
            "policy_version": "1.0",
            "total_violations": 100,
            "total_enforcements": 90,
            "false_positives": 10,
            "false_negatives": 5,
            "user_appeals": 20,
            "successful_appeals": 5,
        }
    ]
    result = await agent.run(policy_data=data)
    assert len(result) == 1
    assert result[0].policy_id == "pol_001"
    assert 0 <= result[0].effectiveness_score <= 1


@pytest.mark.asyncio
async def test_moderation_predictor_agent():
    """Test ModerationPredictorAgent."""
    agent = ModerationPredictorAgent()
    data = [{"count": 100 + i * 5, "avg_severity": 2.0} for i in range(10)]
    result = await agent.run(historical_data=data)
    assert isinstance(result, list)
    assert len(result) > 0


@pytest.mark.asyncio
async def test_analytics_explainer_agent():
    """Test AnalyticsExplainerAgent."""
    agent = AnalyticsExplainerAgent()
    data = {"total_events": 1000, "total_actions": 800}
    result = await agent.run(analytics_data=data)
    assert isinstance(result, str)
    assert len(result) > 0


@pytest.mark.asyncio
async def test_trend_analyzer_empty_data():
    """Test TrendAnalyzerAgent with empty data raises error."""
    agent = TrendAnalyzerAgent()
    with pytest.raises(ValueError, match="empty data"):
        await agent.run(data=[])


@pytest.mark.asyncio
async def test_moderator_performance_empty_data():
    """Test ModeratorPerformanceAgent with empty data raises error."""
    agent = ModeratorPerformanceAgent()
    with pytest.raises(ValueError, match="empty"):
        await agent.run(moderator_data=[])


@pytest.mark.asyncio
async def test_policy_effectiveness_empty_data():
    """Test PolicyEffectivenessAgent with empty data raises error."""
    agent = PolicyEffectivenessAgent()
    with pytest.raises(ValueError, match="empty"):
        await agent.run(policy_data=[])


@pytest.mark.asyncio
async def test_moderation_predictor_empty_data():
    """Test ModerationPredictorAgent with empty data raises error."""
    agent = ModerationPredictorAgent()
    with pytest.raises(ValueError, match="empty"):
        await agent.run(historical_data=[])


@pytest.mark.asyncio
async def test_analytics_explainer_empty_data():
    """Test AnalyticsExplainerAgent with empty data raises error."""
    agent = AnalyticsExplainerAgent()
    with pytest.raises(ValueError, match="empty"):
        await agent.run(analytics_data={})
