"""Tests for SEO Optimizer agents."""

from __future__ import annotations

import pytest

from seo_optimizer.agents.base import AgentResult, BaseAgent
from seo_optimizer.agents.content_optimization import ContentOptimizationAgent
from seo_optimizer.agents.keyword_research import KeywordResearchAgent
from seo_optimizer.agents.link_building import LinkBuildingAgent
from seo_optimizer.agents.performance_analytics import PerformanceAnalyticsAgent
from seo_optimizer.agents.seo_monitoring import SEOMonitoringAgent
from seo_optimizer.agents.technical_seo import TechnicalSEOAgent


class TestBaseAgent:
    """Test cases for the BaseAgent abstract class."""

    def test_agent_result_creation(self) -> None:
        """Test AgentResult dataclass creation."""
        result = AgentResult(success=True, data={"key": "value"})
        assert result.success is True
        assert result.data == {"key": "value"}
        assert result.error is None
        assert result.execution_time_ms == 0.0

    def test_agent_result_with_error(self) -> None:
        """Test AgentResult with error state."""
        result = AgentResult(success=False, error="Test error")
        assert result.success is False
        assert result.error == "Test error"
        assert result.data is None


class TestKeywordResearchAgent:
    """Test cases for KeywordResearchAgent."""

    @pytest.fixture
    def agent(self) -> KeywordResearchAgent:
        """Create a KeywordResearchAgent instance."""
        return KeywordResearchAgent()

    @pytest.mark.asyncio
    async def test_execute_returns_result(self, agent: KeywordResearchAgent) -> None:
        """Test that execute returns an AgentResult."""
        result = await agent.execute(domain="example.com")
        assert isinstance(result, AgentResult)

    @pytest.mark.asyncio
    async def test_execute_with_seed_keywords(
        self, agent: KeywordResearchAgent
    ) -> None:
        """Test keyword research with seed keywords."""
        result = await agent.execute(
            domain="example.com",
            seed_keywords=["seo", "marketing"],
            max_results=10,
        )
        assert isinstance(result, AgentResult)

    def test_filter_keywords(self, agent: KeywordResearchAgent) -> None:
        """Test keyword filtering logic."""
        keywords = [
            {"keyword": "seo", "search_volume": 1000, "difficulty": 30},
            {"keyword": "marketing", "search_volume": 50, "difficulty": 80},
            {"keyword": "optimization", "search_volume": 500, "difficulty": 50},
        ]
        filtered = agent._filter_keywords(keywords, min_search_volume=100, max_difficulty=70)
        assert len(filtered) == 2
        assert all(kw["search_volume"] >= 100 for kw in filtered)
        assert all(kw["difficulty"] <= 70 for kw in filtered)


class TestContentOptimizationAgent:
    """Test cases for ContentOptimizationAgent."""

    @pytest.fixture
    def agent(self) -> ContentOptimizationAgent:
        """Create a ContentOptimizationAgent instance."""
        return ContentOptimizationAgent()

    @pytest.mark.asyncio
    async def test_execute_returns_result(self, agent: ContentOptimizationAgent) -> None:
        """Test that execute returns an AgentResult."""
        result = await agent.execute(
            content="This is test content for SEO optimization.",
            target_keywords=["seo", "optimization"],
        )
        assert isinstance(result, AgentResult)

    def test_analyze_readability(self, agent: ContentOptimizationAgent) -> None:
        """Test readability analysis."""
        content = "This is a simple sentence. It has two sentences."
        result = agent._analyze_readability(content)
        assert "flesch_reading_ease" in result
        assert "word_count" in result
        assert result["word_count"] > 0

    def test_count_syllables(self, agent: ContentOptimizationAgent) -> None:
        """Test syllable counting."""
        assert agent._count_syllables("hello") == 2
        assert agent._count_syllables("the") == 1
        assert agent._count_syllables("beautiful") == 3


class TestTechnicalSEOAgent:
    """Test cases for TechnicalSEOAgent."""

    @pytest.fixture
    def agent(self) -> TechnicalSEOAgent:
        """Create a TechnicalSEOAgent instance."""
        return TechnicalSEOAgent()

    @pytest.mark.asyncio
    async def test_execute_returns_result(self, agent: TechnicalSEOAgent) -> None:
        """Test that execute returns an AgentResult."""
        result = await agent.execute(domain="example.com")
        assert isinstance(result, AgentResult)

    @pytest.mark.asyncio
    async def test_check_crawlability(self, agent: TechnicalSEOAgent) -> None:
        """Test crawlability check."""
        result = await agent._check_crawlability("example.com")
        assert "robots_txt_accessible" in result
        assert "score" in result


class TestLinkBuildingAgent:
    """Test cases for LinkBuildingAgent."""

    @pytest.fixture
    def agent(self) -> LinkBuildingAgent:
        """Create a LinkBuildingAgent instance."""
        return LinkBuildingAgent()

    @pytest.mark.asyncio
    async def test_execute_returns_result(self, agent: LinkBuildingAgent) -> None:
        """Test that execute returns an AgentResult."""
        result = await agent.execute(domain="example.com")
        assert isinstance(result, AgentResult)


class TestSEOMonitoringAgent:
    """Test cases for SEOMonitoringAgent."""

    @pytest.fixture
    def agent(self) -> SEOMonitoringAgent:
        """Create a SEOMonitoringAgent instance."""
        return SEOMonitoringAgent()

    @pytest.mark.asyncio
    async def test_execute_returns_result(self, agent: SEOMonitoringAgent) -> None:
        """Test that execute returns an AgentResult."""
        result = await agent.execute(domain="example.com")
        assert isinstance(result, AgentResult)

    def test_detect_anomalies(self, agent: SEOMonitoringAgent) -> None:
        """Test anomaly detection."""
        rankings = {
            "keywords": {
                "seo": {"current_position": 5, "previous_position": 15},
                "marketing": {"current_position": 20, "previous_position": 22},
            }
        }
        alerts = agent._detect_anomalies(rankings, threshold=5)
        assert len(alerts) == 1
        assert alerts[0]["keyword"] == "seo"


class TestPerformanceAnalyticsAgent:
    """Test cases for PerformanceAnalyticsAgent."""

    @pytest.fixture
    def agent(self) -> PerformanceAnalyticsAgent:
        """Create a PerformanceAnalyticsAgent instance."""
        return PerformanceAnalyticsAgent()

    @pytest.mark.asyncio
    async def test_execute_returns_result(
        self, agent: PerformanceAnalyticsAgent
    ) -> None:
        """Test that execute returns an AgentResult."""
        result = await agent.execute(domain="example.com")
        assert isinstance(result, AgentResult)

    def test_calculate_kpis(self, agent: PerformanceAnalyticsAgent) -> None:
        """Test KPI calculation."""
        analytics = {
            "traffic": {"clicks": 1000, "impressions": 10000},
            "rankings": {"average_position": 15.5, "keywords_in_top_100": 25},
        }
        kpis = agent._calculate_kpis(analytics)
        assert kpis["total_clicks"] == 1000
        assert kpis["total_impressions"] == 10000
        assert kpis["average_ctr"] == 10.0
