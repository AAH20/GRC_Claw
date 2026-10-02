"""Unit tests for the Bidding Agent."""

from __future__ import annotations

import pytest

from agents.base import AgentContext, AgentStatus
from agents.bidding import BiddingAgent


class TestBiddingAgent:
    """Tests for the Bidding Agent."""

    @pytest.mark.asyncio
    async def test_successful_execution(self) -> None:
        """Test successful bid optimization."""
        agent = BiddingAgent()
        context = AgentContext(
            campaign_id="camp_123",
            task="optimize_bids",
            parameters={
                "current_bids": {"ad_group_1": 2.50, "ad_group_2": 3.00},
                "performance_data": {
                    "ad_group_1": {"roas": 4.5, "cpa": 30, "spend": 1000, "revenue": 4500},
                    "ad_group_2": {"roas": 2.0, "cpa": 60, "spend": 800, "revenue": 1600},
                },
                "daily_budget": 500,
                "target_roas": 3.0,
            },
        )

        result = await agent.execute(context)

        assert result.success is True
        assert result.data is not None
        assert agent.status == AgentStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_bid_adjustments(self) -> None:
        """Test bid adjustment calculations."""
        agent = BiddingAgent()
        context = AgentContext(
            campaign_id="camp_123",
            task="optimize_bids",
            parameters={
                "current_bids": {
                    "high_performer": 2.00,
                    "low_performer": 3.00,
                },
                "performance_data": {
                    "high_performer": {"roas": 5.0, "cpa": 20},
                    "low_performer": {"roas": 1.5, "cpa": 80},
                },
                "daily_budget": 500,
                "target_roas": 3.0,
            },
        )

        result = await agent.execute(context)

        assert result.success is True
        adjustments = result.data["bid_adjustments"]
        assert len(adjustments) == 2

        high_adj = next(a for a in adjustments if a["entity_id"] == "high_performer")
        low_adj = next(a for a in adjustments if a["entity_id"] == "low_performer")

        assert high_adj["action"] == "increase"
        assert high_adj["recommended_bid"] > high_adj["current_bid"]
        assert low_adj["action"] == "decrease"
        assert low_adj["recommended_bid"] < low_adj["current_bid"]

    @pytest.mark.asyncio
    async def test_pacing_plan(self) -> None:
        """Test budget pacing plan creation."""
        agent = BiddingAgent()
        context = AgentContext(
            campaign_id="camp_123",
            task="optimize_bids",
            parameters={
                "current_bids": {"ad_group_1": 2.00},
                "performance_data": {"ad_group_1": {"roas": 3.0}},
                "daily_budget": 1000,
                "target_roas": 3.0,
            },
        )

        result = await agent.execute(context)

        assert result.success is True
        pacing = result.data["pacing_plan"]
        assert pacing["daily_budget"] == 1000
        assert "daypart_distribution" in pacing
        total_daypart_budget = sum(
            d["budget"] for d in pacing["daypart_distribution"].values()
        )
        assert total_daypart_budget == pytest.approx(1000, rel=0.01)

    @pytest.mark.asyncio
    async def test_budget_reallocation(self) -> None:
        """Test budget reallocation recommendations."""
        agent = BiddingAgent()
        context = AgentContext(
            campaign_id="camp_123",
            task="optimize_bids",
            parameters={
                "current_bids": {"ch1": 2.0, "ch2": 2.0},
                "performance_data": {
                    "ch1": {"roas": 5.0},
                    "ch2": {"roas": 1.0},
                },
                "daily_budget": 1000,
                "target_roas": 3.0,
            },
        )

        result = await agent.execute(context)

        assert result.success is True
        reallocations = result.data["budget_reallocation"]
        assert len(reallocations) > 0

    @pytest.mark.asyncio
    async def test_roas_projection(self) -> None:
        """Test ROAS projection."""
        agent = BiddingAgent()
        context = AgentContext(
            campaign_id="camp_123",
            task="optimize_bids",
            parameters={
                "current_bids": {"ad_group_1": 2.00},
                "performance_data": {
                    "ad_group_1": {"roas": 3.5, "spend": 1000, "revenue": 3500},
                },
                "daily_budget": 500,
                "target_roas": 3.0,
            },
        )

        result = await agent.execute(context)

        assert result.success is True
        assert result.data["projected_roas"] > 0

    def test_agent_metadata(self) -> None:
        """Test agent metadata."""
        agent = BiddingAgent()
        assert agent.name == "Bidding Agent"
        assert "bid optimization" in agent.description.lower()
