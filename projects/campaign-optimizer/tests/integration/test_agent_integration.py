"""Integration tests for agent orchestration."""

from __future__ import annotations

import pytest

from agents.audience import AudienceAgent
from agents.base import AgentContext, AgentStatus
from agents.bidding import BiddingAgent
from agents.creative import CreativeAgent
from agents.critic import CriticAgent
from agents.research import ResearchAgent
from agents.strategy import StrategyAgent


class TestAgentOrchestration:
    """Integration tests for multi-agent orchestration."""

    @pytest.mark.asyncio
    async def test_full_agent_pipeline(self) -> None:
        """Test the full agent pipeline from strategy to critic."""
        campaign_id = "camp_integration_001"
        context = AgentContext(
            campaign_id=campaign_id,
            task="full_campaign_planning",
            parameters={
                "goals": ["awareness", "conversion"],
                "total_budget": 50000,
                "channels": ["search", "social", "display"],
                "duration_days": 30,
                "industry": "technology",
                "competitors": ["competitor_a", "competitor_b"],
                "target_audience": {
                    "demographics": {"age_ranges": ["25-34"], "locations": ["US"]},
                },
                "brand_voice": "professional",
                "key_message": "The future of marketing is here",
            },
        )

        # 1. Strategy Agent
        strategy_agent = StrategyAgent()
        strategy_result = await strategy_agent.execute(context)
        assert strategy_result.success is True
        assert strategy_result.data is not None
        assert "budget_allocation" in strategy_result.data

        # 2. Research Agent
        research_agent = ResearchAgent()
        research_result = await research_agent.execute(context)
        assert research_result.success is True
        assert research_result.data is not None
        assert "industry_analysis" in research_result.data

        # 3. Creative Agent
        creative_agent = CreativeAgent()
        creative_result = await creative_agent.execute(context)
        assert creative_result.success is True
        assert creative_result.data is not None
        assert "ad_copy_variants" in creative_result.data

        # 4. Audience Agent
        audience_agent = AudienceAgent()
        audience_result = await audience_agent.execute(context)
        assert audience_result.success is True
        assert audience_result.data is not None
        assert "segments" in audience_result.data

        # 5. Bidding Agent
        bidding_agent = BiddingAgent()
        bidding_context = AgentContext(
            campaign_id=campaign_id,
            task="optimize_bids",
            parameters={
                "current_bids": {"search": 2.50, "social": 1.80, "display": 1.20},
                "performance_data": {
                    "search": {"roas": 4.0, "cpa": 35, "spend": 5000, "revenue": 20000},
                    "social": {"roas": 3.2, "cpa": 45, "spend": 3000, "revenue": 9600},
                    "display": {"roas": 2.1, "cpa": 60, "spend": 2000, "revenue": 4200},
                },
                "daily_budget": 1666,
                "target_roas": 3.0,
            },
        )
        bidding_result = await bidding_agent.execute(bidding_context)
        assert bidding_result.success is True
        assert bidding_result.data is not None
        assert "bid_adjustments" in bidding_result.data

        # 6. Critic Agent
        critic_agent = CriticAgent()
        critic_context = AgentContext(
            campaign_id=campaign_id,
            task="evaluate_campaign",
            parameters={
                "campaign_data": {
                    "budget_change_pct": 10,
                    "total_budget": 50000,
                    "creative_variants": 3,
                    "ab_test_configured": True,
                    "landing_page_url": "https://example.com/lp",
                    "tracking_configured": True,
                    "performance_metrics": {
                        "ctr": 0.025,
                        "cpa": 40.0,
                        "roas": 3.5,
                    },
                    "data_privacy_compliant": True,
                    "audience_restrictions_met": True,
                    "creative_compliant": True,
                },
            },
        )
        critic_result = await critic_agent.execute(critic_context)
        assert critic_result.success is True
        assert critic_result.data is not None
        assert "governance" in critic_result.data

    @pytest.mark.asyncio
    async def test_agent_status_tracking(self) -> None:
        """Test that all agents properly track their status."""
        agents = [
            StrategyAgent(),
            ResearchAgent(),
            CreativeAgent(),
            BiddingAgent(),
            AudienceAgent(),
            CriticAgent(),
        ]

        # All should start idle
        for agent in agents:
            assert agent.status == AgentStatus.IDLE

        # Execute one and verify status changes
        context = AgentContext(
            campaign_id="camp_status_test",
            task="test",
            parameters={"goals": ["awareness"], "total_budget": 1000, "channels": ["search"], "duration_days": 7},
        )

        await agents[0].execute(context)
        assert agents[0].status == AgentStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_agent_result_metadata(self) -> None:
        """Test that agent results include proper metadata."""
        agent = StrategyAgent()
        context = AgentContext(
            campaign_id="camp_meta_test",
            task="test_task",
            parameters={
                "goals": ["awareness"],
                "total_budget": 10000,
                "channels": ["search"],
                "duration_days": 14,
            },
        )

        result = await agent.execute(context)

        assert result.metadata is not None
        assert result.metadata["agent"] == "Strategy Agent"
        assert result.metadata["campaign_id"] == "camp_meta_test"
        assert result.duration_seconds >= 0

    @pytest.mark.asyncio
    async def test_agent_error_handling(self) -> None:
        """Test agent error handling and recovery."""
        agent = StrategyAgent()
        context = AgentContext(
            campaign_id="camp_error_test",
            task="test_task",
            parameters={},  # Empty parameters should still work
        )

        result = await agent.execute(context)
        # Agent should handle empty parameters gracefully
        assert isinstance(result.success, bool)
