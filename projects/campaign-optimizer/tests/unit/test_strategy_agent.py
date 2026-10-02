"""Unit tests for the Strategy Agent."""

from __future__ import annotations

from typing import Any

import pytest

from agents.base import AgentContext, AgentStatus
from agents.strategy import StrategyAgent


class TestStrategyAgent:
    """Tests for the Strategy Agent."""

    @pytest.mark.asyncio
    async def test_successful_execution(self) -> None:
        """Test successful strategy planning."""
        agent = StrategyAgent()
        context = AgentContext(
            campaign_id="camp_123",
            task="plan_campaign",
            parameters={
                "goals": ["awareness", "conversion"],
                "total_budget": 50000,
                "channels": ["search", "social", "display"],
                "duration_days": 30,
            },
        )

        result = await agent.execute(context)

        assert result.success is True
        assert result.data is not None
        assert agent.status == AgentStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_budget_allocation(self) -> None:
        """Test budget allocation across channels."""
        agent = StrategyAgent()
        context = AgentContext(
            campaign_id="camp_123",
            task="plan_campaign",
            parameters={
                "goals": ["awareness"],
                "total_budget": 10000,
                "channels": ["search", "social"],
                "duration_days": 14,
            },
        )

        result = await agent.execute(context)

        assert result.success is True
        allocation = result.data["budget_allocation"]
        assert "search" in allocation
        assert "social" in allocation
        assert sum(allocation.values()) == pytest.approx(10000, rel=0.01)

    @pytest.mark.asyncio
    async def test_kpi_definition(self) -> None:
        """Test KPI definition based on goals."""
        agent = StrategyAgent()
        context = AgentContext(
            campaign_id="camp_123",
            task="plan_campaign",
            parameters={
                "goals": ["awareness", "conversion"],
                "total_budget": 10000,
                "channels": ["search"],
                "duration_days": 14,
            },
        )

        result = await agent.execute(context)

        assert result.success is True
        kpis = result.data["kpis"]
        assert len(kpis) == 2
        kpi_goals = [k["goal"] for k in kpis]
        assert "awareness" in kpi_goals
        assert "conversion" in kpi_goals

    @pytest.mark.asyncio
    async def test_timeline_creation(self) -> None:
        """Test campaign timeline creation."""
        agent = StrategyAgent()
        context = AgentContext(
            campaign_id="camp_123",
            task="plan_campaign",
            parameters={
                "goals": ["awareness"],
                "total_budget": 10000,
                "channels": ["search"],
                "duration_days": 30,
            },
        )

        result = await agent.execute(context)

        assert result.success is True
        timeline = result.data["timeline"]
        assert len(timeline) > 0
        phases = [p["phase"] for p in timeline]
        assert "research" in phases
        assert "launch" in phases
        assert "optimize" in phases

    @pytest.mark.asyncio
    async def test_risk_assessment(self) -> None:
        """Test risk assessment for high-budget campaigns."""
        agent = StrategyAgent()
        context = AgentContext(
            campaign_id="camp_123",
            task="plan_campaign",
            parameters={
                "goals": ["awareness"],
                "total_budget": 150000,
                "channels": ["search"],
                "duration_days": 30,
            },
        )

        result = await agent.execute(context)

        assert result.success is True
        risks = result.data["risk_assessment"]
        assert len(risks) > 0
        risk_types = [r["type"] for r in risks]
        assert "high_budget" in risk_types

    def test_agent_metadata(self) -> None:
        """Test agent metadata."""
        agent = StrategyAgent()
        assert agent.name == "Strategy Agent"
        assert "campaign planning" in agent.description.lower()
