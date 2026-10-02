"""Unit tests for the Critic Agent."""

from __future__ import annotations

import pytest

from agents.base import AgentContext, AgentStatus
from agents.critic import CriticAgent
from core.config import Settings


class TestCriticAgent:
    """Tests for the Critic Agent."""

    @pytest.mark.asyncio
    async def test_successful_execution(self) -> None:
        """Test successful critic evaluation."""
        agent = CriticAgent()
        context = AgentContext(
            campaign_id="camp_123",
            task="evaluate_campaign",
            parameters={
                "campaign_data": {
                    "budget_change_pct": 10,
                    "total_budget": 5000,
                    "creative_variants": 3,
                    "ab_test_configured": True,
                    "landing_page_url": "https://example.com/lp",
                    "tracking_configured": True,
                    "performance_metrics": {
                        "ctr": 0.03,
                        "cpa": 40.0,
                        "roas": 3.5,
                    },
                    "data_privacy_compliant": True,
                    "audience_restrictions_met": True,
                    "creative_compliant": True,
                },
            },
        )

        result = await agent.execute(context)

        assert result.success is True
        assert result.data is not None
        assert agent.status == AgentStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_governance_check_pass(self) -> None:
        """Test governance check passes for compliant campaign."""
        agent = CriticAgent()
        context = AgentContext(
            campaign_id="camp_123",
            task="evaluate_campaign",
            parameters={
                "campaign_data": {
                    "budget_change_pct": 5,
                    "total_budget": 500,
                    "creative_variants": 2,
                    "ab_test_configured": True,
                    "landing_page_url": "https://example.com",
                    "tracking_configured": True,
                    "data_privacy_compliant": True,
                    "audience_restrictions_met": True,
                    "creative_compliant": True,
                },
            },
        )

        result = await agent.execute(context)

        assert result.success is True
        assert result.data["governance"]["all_passed"] is True
        assert result.data["approval_required"] is False

    @pytest.mark.asyncio
    async def test_governance_check_fail_budget(self) -> None:
        """Test governance check fails for excessive budget change."""
        agent = CriticAgent()
        context = AgentContext(
            campaign_id="camp_123",
            task="evaluate_campaign",
            parameters={
                "campaign_data": {
                    "budget_change_pct": 50,  # Exceeds 20% limit
                    "total_budget": 500,
                    "creative_variants": 2,
                    "ab_test_configured": True,
                    "landing_page_url": "https://example.com",
                    "tracking_configured": True,
                    "data_privacy_compliant": True,
                    "audience_restrictions_met": True,
                    "creative_compliant": True,
                },
            },
        )

        result = await agent.execute(context)

        assert result.success is True
        assert result.data["governance"]["all_passed"] is False

    @pytest.mark.asyncio
    async def test_approval_required_high_budget(self) -> None:
        """Test that high budgets require approval."""
        agent = CriticAgent()
        context = AgentContext(
            campaign_id="camp_123",
            task="evaluate_campaign",
            parameters={
                "campaign_data": {
                    "budget_change_pct": 5,
                    "total_budget": 5000,  # Above $1000 threshold
                    "creative_variants": 2,
                    "ab_test_configured": True,
                    "landing_page_url": "https://example.com",
                    "tracking_configured": True,
                    "data_privacy_compliant": True,
                    "audience_restrictions_met": True,
                    "creative_compliant": True,
                },
            },
        )

        result = await agent.execute(context)

        assert result.success is True
        assert result.data["approval_required"] is True

    @pytest.mark.asyncio
    async def test_quality_check_missing_creative(self) -> None:
        """Test quality check fails with insufficient creative variants."""
        agent = CriticAgent()
        context = AgentContext(
            campaign_id="camp_123",
            task="evaluate_campaign",
            parameters={
                "campaign_data": {
                    "budget_change_pct": 5,
                    "total_budget": 500,
                    "creative_variants": 1,  # Less than required 2
                    "ab_test_configured": False,
                    "landing_page_url": "",
                    "tracking_configured": False,
                    "data_privacy_compliant": True,
                    "audience_restrictions_met": True,
                    "creative_compliant": True,
                },
            },
        )

        result = await agent.execute(context)

        assert result.success is True
        assert result.data["quality"]["all_passed"] is False

    @pytest.mark.asyncio
    async def test_performance_evaluation(self) -> None:
        """Test performance evaluation against benchmarks."""
        agent = CriticAgent()
        context = AgentContext(
            campaign_id="camp_123",
            task="evaluate_campaign",
            parameters={
                "campaign_data": {
                    "budget_change_pct": 5,
                    "total_budget": 500,
                    "creative_variants": 2,
                    "ab_test_configured": True,
                    "landing_page_url": "https://example.com",
                    "tracking_configured": True,
                    "performance_metrics": {
                        "ctr": 0.01,  # Below 0.02 benchmark
                        "cpa": 100.0,  # Above 75.0 benchmark
                        "roas": 1.5,  # Below 2.5 benchmark
                    },
                    "data_privacy_compliant": True,
                    "audience_restrictions_met": True,
                    "creative_compliant": True,
                },
            },
        )

        result = await agent.execute(context)

        assert result.success is True
        performance = result.data["performance"]
        assert performance["overall_status"] == "needs_attention"

    @pytest.mark.asyncio
    async def test_recommendations_generated(self) -> None:
        """Test that recommendations are generated."""
        agent = CriticAgent()
        context = AgentContext(
            campaign_id="camp_123",
            task="evaluate_campaign",
            parameters={
                "campaign_data": {
                    "budget_change_pct": 5,
                    "total_budget": 500,
                    "creative_variants": 2,
                    "ab_test_configured": True,
                    "landing_page_url": "https://example.com",
                    "tracking_configured": True,
                    "data_privacy_compliant": True,
                    "audience_restrictions_met": True,
                    "creative_compliant": True,
                },
            },
        )

        result = await agent.execute(context)

        assert result.success is True
        recommendations = result.data["recommendations"]
        assert len(recommendations) > 0

    def test_agent_metadata(self) -> None:
        """Test agent metadata."""
        agent = CriticAgent()
        assert agent.name == "Critic Agent"
        assert "quality assurance" in agent.description.lower()
