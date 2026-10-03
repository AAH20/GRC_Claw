"""Tests for community health scorer agents."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from community_health_scorer.agents.engagement_metrics_agent import EngagementMetricsAgent
from community_health_scorer.agents.toxicity_detector_agent import ToxicityDetectorAgent
from community_health_scorer.models import EngagementLevel, ToxicityLevel


class TestEngagementMetricsAgent:
    """Tests for EngagementMetricsAgent."""

    @pytest.fixture
    def agent(self) -> EngagementMetricsAgent:
        """Create an engagement metrics agent."""
        with patch(
            "community_health_scorer.agents.engagement_metrics_agent.get_settings"
        ):
            agent = EngagementMetricsAgent()
            agent._agent = None
            return agent

    def test_agent_info(self, agent: EngagementMetricsAgent) -> None:
        """Test agent info."""
        info = agent.get_info()
        assert info["name"] == "engagement_metrics_agent"
        assert "engagement_analysis" in info["type"]
        assert len(info["capabilities"]) > 0

    @pytest.mark.asyncio
    async def test_heuristic_score_high_engagement(
        self, agent: EngagementMetricsAgent
    ) -> None:
        """Test heuristic scoring with high engagement metrics."""
        metrics = {
            "dau": 500,
            "mau": 1000,
            "avg_session_duration_minutes": 20.0,
            "avg_sessions_per_user": 4.0,
            "interaction_depth": 0.8,
            "content_creation_rate": 0.6,
            "response_rate": 0.9,
            "retention_rate_7d": 0.7,
            "retention_rate_30d": 0.5,
        }
        result = await agent.run("test-community", metrics)
        assert result.score > 60
        assert result.engagement_level in (
            EngagementLevel.HIGHLY_ENGAGED,
            EngagementLevel.ENGAGED,
        )

    @pytest.mark.asyncio
    async def test_heuristic_score_low_engagement(
        self, agent: EngagementMetricsAgent
    ) -> None:
        """Test heuristic scoring with low engagement metrics."""
        metrics = {
            "dau": 10,
            "mau": 1000,
            "avg_session_duration_minutes": 1.0,
            "avg_sessions_per_user": 0.1,
            "interaction_depth": 0.05,
            "content_creation_rate": 0.01,
            "response_rate": 0.05,
            "retention_rate_7d": 0.02,
            "retention_rate_30d": 0.01,
        }
        result = await agent.run("test-community", metrics)
        assert result.score < 40
        assert result.engagement_level in (
            EngagementLevel.LOW_ENGAGEMENT,
            EngagementLevel.DISENGAGED,
        )

    @pytest.mark.asyncio
    async def test_heuristic_score_zero_metrics(
        self, agent: EngagementMetricsAgent
    ) -> None:
        """Test heuristic scoring with zero metrics."""
        metrics = {
            "dau": 0,
            "mau": 0,
            "avg_session_duration_minutes": 0,
            "avg_sessions_per_user": 0,
            "interaction_depth": 0,
            "content_creation_rate": 0,
            "response_rate": 0,
            "retention_rate_7d": 0,
            "retention_rate_30d": 0,
        }
        result = await agent.run("test-community", metrics)
        assert result.score == 0
        assert result.engagement_level == EngagementLevel.DISENGAGED

    @pytest.mark.asyncio
    async def test_heuristic_score_moderate_engagement(
        self, agent: EngagementMetricsAgent
    ) -> None:
        """Test heuristic scoring with moderate engagement metrics."""
        metrics = {
            "dau": 100,
            "mau": 500,
            "avg_session_duration_minutes": 8.0,
            "avg_sessions_per_user": 1.5,
            "interaction_depth": 0.4,
            "content_creation_rate": 0.2,
            "response_rate": 0.5,
            "retention_rate_7d": 0.3,
            "retention_rate_30d": 0.2,
        }
        result = await agent.run("test-community", metrics)
        assert 30 < result.score < 70


class TestToxicityDetectorAgent:
    """Tests for ToxicityDetectorAgent."""

    @pytest.fixture
    def agent(self) -> ToxicityDetectorAgent:
        """Create a toxicity detector agent."""
        with patch(
            "community_health_scorer.agents.toxicity_detector_agent.get_settings"
        ):
            agent = ToxicityDetectorAgent()
            agent._agent = None
            return agent

    def test_agent_info(self, agent: ToxicityDetectorAgent) -> None:
        """Test agent info."""
        info = agent.get_info()
        assert info["name"] == "toxicity_detector_agent"
        assert "toxicity_detection" in info["type"]
        assert len(info["capabilities"]) > 0

    @pytest.mark.asyncio
    async def test_heuristic_score_no_toxicity(
        self, agent: ToxicityDetectorAgent
    ) -> None:
        """Test heuristic scoring with no toxicity."""
        data = {
            "toxic_content_count": 0,
            "total_content_analyzed": 1000,
            "toxic_user_count": 0,
            "total_users": 500,
            "toxicity_categories": {},
        }
        result = await agent.run("test-community", data)
        assert result.overall_toxicity_score == 0
        assert result.toxicity_level == ToxicityLevel.NONE
        assert result.score == 100

    @pytest.mark.asyncio
    async def test_heuristic_score_low_toxicity(
        self, agent: ToxicityDetectorAgent
    ) -> None:
        """Test heuristic scoring with low toxicity."""
        data = {
            "toxic_content_count": 5,
            "total_content_analyzed": 1000,
            "toxic_user_count": 2,
            "total_users": 500,
            "toxicity_categories": {"spam": 0.1},
        }
        result = await agent.run("test-community", data)
        assert result.overall_toxicity_score < 25
        assert result.toxicity_level in (ToxicityLevel.NONE, ToxicityLevel.LOW)

    @pytest.mark.asyncio
    async def test_heuristic_score_moderate_toxicity(
        self, agent: ToxicityDetectorAgent
    ) -> None:
        """Test heuristic scoring with moderate toxicity."""
        data = {
            "toxic_content_count": 100,
            "total_content_analyzed": 1000,
            "toxic_user_count": 50,
            "total_users": 500,
            "toxicity_categories": {"harassment": 0.3, "spam": 0.2},
        }
        result = await agent.run("test-community", data)
        assert result.overall_toxicity_score >= 10
        assert result.toxicity_level in (
            ToxicityLevel.LOW,
            ToxicityLevel.MODERATE,
        )

    @pytest.mark.asyncio
    async def test_heuristic_score_high_toxicity(
        self, agent: ToxicityDetectorAgent
    ) -> None:
        """Test heuristic scoring with high toxicity."""
        data = {
            "toxic_content_count": 500,
            "total_content_analyzed": 1000,
            "toxic_user_count": 200,
            "total_users": 500,
            "toxicity_categories": {
                "harassment": 0.5,
                "hate_speech": 0.3,
                "spam": 0.4,
            },
        }
        result = await agent.run("test-community", data)
        assert result.overall_toxicity_score >= 40
        assert result.toxicity_level in (
            ToxicityLevel.MODERATE,
            ToxicityLevel.HIGH,
            ToxicityLevel.SEVERE,
        )
        assert len(result.recommendations) > 0

    @pytest.mark.asyncio
    async def test_heuristic_score_severe_toxicity(
        self, agent: ToxicityDetectorAgent
    ) -> None:
        """Test heuristic scoring with severe toxicity."""
        data = {
            "toxic_content_count": 800,
            "total_content_analyzed": 1000,
            "toxic_user_count": 400,
            "total_users": 500,
            "toxicity_categories": {
                "harassment": 0.8,
                "hate_speech": 0.6,
                "spam": 0.7,
            },
        }
        result = await agent.run("test-community", data)
        assert result.overall_toxicity_score >= 75
        assert result.toxicity_level == ToxicityLevel.SEVERE

    @pytest.mark.asyncio
    async def test_recommendations_for_high_toxicity(
        self, agent: ToxicityDetectorAgent
    ) -> None:
        """Test that recommendations are generated for high toxicity."""
        data = {
            "toxic_content_count": 600,
            "total_content_analyzed": 1000,
            "toxic_user_count": 300,
            "total_users": 500,
            "toxicity_categories": {
                "harassment": 0.6,
                "hate_speech": 0.4,
                "spam": 0.5,
            },
        }
        result = await agent.run("test-community", data)
        assert len(result.recommendations) >= 3
