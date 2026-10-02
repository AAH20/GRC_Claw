"""Unit tests for the Creative Agent."""

from __future__ import annotations

import pytest

from agents.base import AgentContext, AgentStatus
from agents.creative import CreativeAgent


class TestCreativeAgent:
    """Tests for the Creative Agent."""

    @pytest.mark.asyncio
    async def test_successful_execution(self) -> None:
        """Test successful creative generation."""
        agent = CreativeAgent()
        context = AgentContext(
            campaign_id="camp_123",
            task="generate_creative",
            parameters={
                "brand_voice": "professional",
                "channels": ["search", "social"],
                "key_message": "The best product for your needs",
                "target_audience": {"demographics": {"age_ranges": ["25-34"]}},
            },
        )

        result = await agent.execute(context)

        assert result.success is True
        assert result.data is not None
        assert agent.status == AgentStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_ad_copy_generation(self) -> None:
        """Test ad copy generation for multiple channels."""
        agent = CreativeAgent()
        context = AgentContext(
            campaign_id="camp_123",
            task="generate_creative",
            parameters={
                "brand_voice": "professional",
                "channels": ["search", "social"],
                "key_message": "Best product ever",
                "target_audience": {},
            },
        )

        result = await agent.execute(context)

        assert result.success is True
        ad_copy = result.data["ad_copy_variants"]
        assert "search" in ad_copy
        assert "social" in ad_copy
        assert len(ad_copy["search"]) > 0
        assert len(ad_copy["social"]) > 0

    @pytest.mark.asyncio
    async def test_creative_recommendations(self) -> None:
        """Test creative asset recommendations."""
        agent = CreativeAgent()
        context = AgentContext(
            campaign_id="camp_123",
            task="generate_creative",
            parameters={
                "brand_voice": "professional",
                "channels": ["social", "display"],
                "key_message": "Amazing product",
                "target_audience": {},
            },
        )

        result = await agent.execute(context)

        assert result.success is True
        recommendations = result.data["creative_recommendations"]
        assert len(recommendations) > 0
        assert all("type" in r for r in recommendations)

    @pytest.mark.asyncio
    async def test_ab_test_variants(self) -> None:
        """Test A/B test variant creation."""
        agent = CreativeAgent()
        context = AgentContext(
            campaign_id="camp_123",
            task="generate_creative",
            parameters={
                "brand_voice": "professional",
                "channels": ["search", "social"],
                "key_message": "Test message",
                "target_audience": {},
            },
        )

        result = await agent.execute(context)

        assert result.success is True
        variants = result.data["ab_test_variants"]
        assert len(variants) == 2  # One per channel
        assert all("variant_a" in v for v in variants)
        assert all("variant_b" in v for v in variants)

    @pytest.mark.asyncio
    async def test_landing_page_suggestions(self) -> None:
        """Test landing page suggestions."""
        agent = CreativeAgent()
        context = AgentContext(
            campaign_id="camp_123",
            task="generate_creative",
            parameters={
                "brand_voice": "professional",
                "channels": ["search"],
                "key_message": "Test message",
                "target_audience": {},
            },
        )

        result = await agent.execute(context)

        assert result.success is True
        suggestions = result.data["landing_page_suggestions"]
        assert len(suggestions) > 0
        assert all("type" in s for s in suggestions)

    def test_agent_metadata(self) -> None:
        """Test agent metadata."""
        agent = CreativeAgent()
        assert agent.name == "Creative Agent"
        assert "ad copy" in agent.description.lower()
