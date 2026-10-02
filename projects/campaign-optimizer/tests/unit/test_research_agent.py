"""Unit tests for the Research Agent."""

from __future__ import annotations

import pytest

from agents.base import AgentContext, AgentStatus
from agents.research import ResearchAgent


class TestResearchAgent:
    """Tests for the Research Agent."""

    @pytest.mark.asyncio
    async def test_successful_execution(self) -> None:
        """Test successful research execution."""
        agent = ResearchAgent()
        context = AgentContext(
            campaign_id="camp_123",
            task="market_research",
            parameters={
                "industry": "technology",
                "competitors": ["competitor_a", "competitor_b"],
                "target_audience": {"demographics": {"age_ranges": ["25-34"]}},
            },
        )

        result = await agent.execute(context)

        assert result.success is True
        assert result.data is not None
        assert agent.status == AgentStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_industry_analysis(self) -> None:
        """Test industry analysis generation."""
        agent = ResearchAgent()
        context = AgentContext(
            campaign_id="camp_123",
            task="market_research",
            parameters={
                "industry": "ecommerce",
                "competitors": [],
                "target_audience": {},
            },
        )

        result = await agent.execute(context)

        assert result.success is True
        industry = result.data["industry_analysis"]
        assert industry["industry"] == "ecommerce"

    @pytest.mark.asyncio
    async def test_competitor_analysis(self) -> None:
        """Test competitor analysis generation."""
        agent = ResearchAgent()
        context = AgentContext(
            campaign_id="camp_123",
            task="market_research",
            parameters={
                "industry": "technology",
                "competitors": ["shopify", "bigcommerce"],
                "target_audience": {},
            },
        )

        result = await agent.execute(context)

        assert result.success is True
        competitors = result.data["competitor_analysis"]
        assert len(competitors) == 2
        competitor_names = [c["name"] for c in competitors]
        assert "shopify" in competitor_names
        assert "bigcommerce" in competitor_names

    @pytest.mark.asyncio
    async def test_market_trends(self) -> None:
        """Test market trend identification."""
        agent = ResearchAgent()
        context = AgentContext(
            campaign_id="camp_123",
            task="market_research",
            parameters={
                "industry": "technology",
                "competitors": [],
                "target_audience": {},
            },
        )

        result = await agent.execute(context)

        assert result.success is True
        trends = result.data["market_trends"]
        assert len(trends) > 0
        assert all("relevance" in t for t in trends)

    @pytest.mark.asyncio
    async def test_recommendations(self) -> None:
        """Test recommendation generation."""
        agent = ResearchAgent()
        context = AgentContext(
            campaign_id="camp_123",
            task="market_research",
            parameters={
                "industry": "technology",
                "competitors": ["competitor_a"],
                "target_audience": {},
            },
        )

        result = await agent.execute(context)

        assert result.success is True
        recommendations = result.data["recommendations"]
        assert len(recommendations) > 0
        assert all(isinstance(r, str) for r in recommendations)

    def test_agent_metadata(self) -> None:
        """Test agent metadata."""
        agent = ResearchAgent()
        assert agent.name == "Research Agent"
        assert "market research" in agent.description.lower()
