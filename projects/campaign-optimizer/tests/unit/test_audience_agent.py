"""Unit tests for the Audience Agent."""

from __future__ import annotations

import pytest

from agents.base import AgentContext, AgentStatus
from agents.audience import AudienceAgent


class TestAudienceAgent:
    """Tests for the Audience Agent."""

    @pytest.mark.asyncio
    async def test_successful_execution(self) -> None:
        """Test successful audience analysis."""
        agent = AudienceAgent()
        context = AgentContext(
            campaign_id="camp_123",
            task="analyze_audience",
            parameters={
                "base_audience": {
                    "demographics": {"age_ranges": ["25-34"], "locations": ["US"]},
                },
                "goals": ["awareness", "conversion"],
                "lookalike_seed": [" converters_30d"],
            },
        )

        result = await agent.execute(context)

        assert result.success is True
        assert result.data is not None
        assert agent.status == AgentStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_segment_creation(self) -> None:
        """Test audience segment creation."""
        agent = AudienceAgent()
        context = AgentContext(
            campaign_id="camp_123",
            task="analyze_audience",
            parameters={
                "base_audience": {
                    "demographics": {"age_ranges": ["25-34", "35-44"], "locations": ["US", "CA"]},
                },
                "goals": ["conversion"],
                "lookalike_seed": [],
            },
        )

        result = await agent.execute(context)

        assert result.success is True
        segments = result.data["segments"]
        assert len(segments) > 0
        assert all("name" in s for s in segments)
        assert all("type" in s for s in segments)

    @pytest.mark.asyncio
    async def test_lookalike_creation(self) -> None:
        """Test lookalike audience creation."""
        agent = AudienceAgent()
        context = AgentContext(
            campaign_id="camp_123",
            task="analyze_audience",
            parameters={
                "base_audience": {},
                "goals": ["awareness"],
                "lookalike_seed": ["high_value_customers", "cart_abandoners"],
            },
        )

        result = await agent.execute(context)

        assert result.success is True
        lookalikes = result.data["lookalike_audiences"]
        assert len(lookalikes) == 6  # 2 seeds × 3 similarity levels
        assert all("similarity" in l for l in lookalikes)

    @pytest.mark.asyncio
    async def test_targeting_recommendations(self) -> None:
        """Test targeting recommendations."""
        agent = AudienceAgent()
        context = AgentContext(
            campaign_id="camp_123",
            task="analyze_audience",
            parameters={
                "base_audience": {
                    "interests": ["technology", "productivity"],
                    "behaviors": ["frequent_buyers"],
                },
                "goals": ["conversion"],
                "lookalike_seed": [],
            },
        )

        result = await agent.execute(context)

        assert result.success is True
        targeting = result.data["targeting_recommendations"]
        assert "auto_targeting" in targeting
        assert "manual_overlays" in targeting
        assert "bid_adjustments" in targeting

    @pytest.mark.asyncio
    async def test_exclusion_lists(self) -> None:
        """Test exclusion list definitions."""
        agent = AudienceAgent()
        context = AgentContext(
            campaign_id="camp_123",
            task="analyze_audience",
            parameters={
                "base_audience": {},
                "goals": ["conversion"],
                "lookalike_seed": [],
            },
        )

        result = await agent.execute(context)

        assert result.success is True
        exclusions = result.data["exclusion_lists"]
        assert len(exclusions) > 0
        assert all("name" in e for e in exclusions)
        assert all("reason" in e for e in exclusions)

    @pytest.mark.asyncio
    async def test_personalization_strategy(self) -> None:
        """Test personalization strategy."""
        agent = AudienceAgent()
        context = AgentContext(
            campaign_id="camp_123",
            task="analyze_audience",
            parameters={
                "base_audience": {},
                "goals": ["awareness", "conversion"],
                "lookalike_seed": [],
            },
        )

        result = await agent.execute(context)

        assert result.success is True
        strategy = result.data["personalization_strategy"]
        assert "dynamic_creative_optimization" in strategy
        assert "message_by_segment" in strategy

    def test_agent_metadata(self) -> None:
        """Test agent metadata."""
        agent = AudienceAgent()
        assert agent.name == "Audience Agent"
        assert "audience segmentation" in agent.description.lower()
