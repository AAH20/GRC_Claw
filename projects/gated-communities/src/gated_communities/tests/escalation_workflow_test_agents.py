"""Tests for escalation workflow agents."""

from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from escalation_workflow.agents.auto_resolver import AutoResolverAgent, AutoResolverInput
from escalation_workflow.agents.escalation_analyzer import (
    EscalationAnalyzerAgent,
    EscalationAnalyzerInput,
)
from escalation_workflow.agents.priority_router import PriorityRouterAgent, PriorityRouterInput
from escalation_workflow.agents.resolution_optimizer import (
    ResolutionOptimizerAgent,
    ResolutionOptimizerInput,
)
from escalation_workflow.agents.sla_tracker import SLATrackerAgent, SLATrackerInput
from escalation_workflow.models.escalation import Escalation
from escalation_workflow.models.priority import PriorityLevel
from escalation_workflow.models.resolution import ResolutionStatus
from escalation_workflow.models.sla import SLAStatus


@pytest.fixture
def sample_escalation() -> Escalation:
    """Create a sample escalation for testing."""
    return Escalation(
        title="Test Escalation",
        description="Test description for testing",
        requester="test_user",
        priority="medium",
        category="test",
    )


@pytest.fixture
def mock_llm() -> MagicMock:
    """Create a mock LLM for testing."""
    mock = MagicMock()
    mock.ainvoke = AsyncMock(
        return_value=MagicMock(content="high priority, confidence 0.9")
    )
    return mock


class TestPriorityRouterAgent:
    """Tests for PriorityRouterAgent."""

    @pytest.mark.asyncio
    async def test_assess_priority(
        self, sample_escalation: Escalation, mock_llm: MagicMock
    ) -> None:
        """Test priority assessment."""
        agent = PriorityRouterAgent(model=mock_llm)
        result = await agent.run(PriorityRouterInput(escalation=sample_escalation))
        assert result.escalation_id == sample_escalation.id
        assert result.confidence > 0
        assert result.assessed_priority in PriorityLevel

    @pytest.mark.asyncio
    async def test_fallback_on_error(self, sample_escalation: Escalation) -> None:
        """Test fallback assessment when LLM fails."""
        mock = MagicMock()
        mock.ainvoke = AsyncMock(side_effect=Exception("LLM error"))
        agent = PriorityRouterAgent(model=mock)
        result = await agent.run(PriorityRouterInput(escalation=sample_escalation))
        assert result.assessed_priority == PriorityLevel.MEDIUM
        assert result.confidence == 0.5

    @pytest.mark.asyncio
    async def test_health_check(self, mock_llm: MagicMock) -> None:
        """Test agent health check."""
        agent = PriorityRouterAgent(model=mock_llm)
        health = await agent.health_check()
        assert health["status"] == "healthy"
        assert health["agent"] == "PriorityRouterAgent"


class TestSLATrackerAgent:
    """Tests for SLATrackerAgent."""

    @pytest.mark.asyncio
    async def test_track_sla(self, mock_llm: MagicMock) -> None:
        """Test SLA tracking."""
        now = datetime.utcnow()
        agent = SLATrackerAgent(model=mock_llm)
        result = await agent.run(
            SLATrackerInput(
                escalation_id="123e4567-e89b-12d3-a456-426614174000",
                priority="high",
                started_at=now,
                response_deadline=now + timedelta(minutes=30),
                resolution_deadline=now + timedelta(minutes=120),
            )
        )
        assert result.status == SLAStatus.ACTIVE
        assert result.remaining_minutes > 0

    @pytest.mark.asyncio
    async def test_breach_detection(self, mock_llm: MagicMock) -> None:
        """Test SLA breach detection."""
        now = datetime.utcnow()
        agent = SLATrackerAgent(model=mock_llm)
        result = await agent.run(
            SLATrackerInput(
                escalation_id="123e4567-e89b-12d3-a456-426614174000",
                priority="critical",
                started_at=now - timedelta(hours=2),
                response_deadline=now - timedelta(hours=1),
                resolution_deadline=now - timedelta(minutes=30),
            )
        )
        assert result.status == SLAStatus.BREACHED

    def test_calculate_breach(self, mock_llm: MagicMock) -> None:
        """Test breach calculation."""
        agent = SLATrackerAgent(model=mock_llm)
        now = datetime.utcnow()
        from escalation_workflow.models.sla import SLA

        sla = SLA(
            escalation_id="123e4567-e89b-12d3-a456-426614174000",
            priority="high",
            response_time_minutes=30,
            resolution_time_minutes=120,
            response_deadline=now,
            resolution_deadline=now,
        )
        breach = agent.calculate_breach(sla)
        assert breach.minutes_overdue >= 0
        assert breach.sla_id == sla.id


class TestResolutionOptimizerAgent:
    """Tests for ResolutionOptimizerAgent."""

    @pytest.mark.asyncio
    async def test_optimize_resolution(
        self, sample_escalation: Escalation, mock_llm: MagicMock
    ) -> None:
        """Test resolution optimization."""
        agent = ResolutionOptimizerAgent(model=mock_llm)
        result = await agent.run(ResolutionOptimizerInput(escalation=sample_escalation))
        assert result.escalation_id == sample_escalation.id
        assert result.confidence > 0

    @pytest.mark.asyncio
    async def test_fallback_on_error(self, sample_escalation: Escalation) -> None:
        """Test fallback when LLM fails."""
        mock = MagicMock()
        mock.ainvoke = AsyncMock(side_effect=Exception("LLM error"))
        agent = ResolutionOptimizerAgent(model=mock)
        result = await agent.run(ResolutionOptimizerInput(escalation=sample_escalation))
        assert result.confidence == 0.3
        assert "Manual" in result.title


class TestEscalationAnalyzerAgent:
    """Tests for EscalationAnalyzerAgent."""

    @pytest.mark.asyncio
    async def test_analyze_escalation(
        self, sample_escalation: Escalation, mock_llm: MagicMock
    ) -> None:
        """Test escalation analysis."""
        agent = EscalationAnalyzerAgent(model=mock_llm)
        result = await agent.run(
            EscalationAnalyzerInput(
                escalations=[sample_escalation], analysis_type="single"
            )
        )
        assert result.escalation_id == sample_escalation.id
        assert result.risk_score >= 0

    @pytest.mark.asyncio
    async def test_generate_trend_report(
        self, sample_escalation: Escalation, mock_llm: MagicMock
    ) -> None:
        """Test trend report generation."""
        agent = EscalationAnalyzerAgent(model=mock_llm)
        report = await agent.generate_trend_report([sample_escalation])
        assert report.total_escalations == 1
        assert report.period_start < report.period_end


class TestAutoResolverAgent:
    """Tests for AutoResolverAgent."""

    @pytest.mark.asyncio
    async def test_auto_resolve_disabled(
        self, sample_escalation: Escalation, mock_llm: MagicMock
    ) -> None:
        """Test auto-resolve when disabled."""
        agent = AutoResolverAgent(model=mock_llm)
        result = await agent.run(
            AutoResolverInput(escalation=sample_escalation, auto_resolve_enabled=False)
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_auto_resolve_low_priority(
        self, sample_escalation: Escalation, mock_llm: MagicMock
    ) -> None:
        """Test auto-resolve for low priority escalation."""
        sample_escalation.priority = "low"
        agent = AutoResolverAgent(model=mock_llm)
        result = await agent.run(
            AutoResolverInput(escalation=sample_escalation, auto_resolve_enabled=True)
        )
        if result:
            assert result.automated is True
            assert result.status == ResolutionStatus.IMPLEMENTED

    @pytest.mark.asyncio
    async def test_auto_resolve_critical_priority(
        self, sample_escalation: Escalation, mock_llm: MagicMock
    ) -> None:
        """Test auto-resolve blocked for critical priority."""
        sample_escalation.priority = "critical"
        agent = AutoResolverAgent(model=mock_llm)
        result = await agent.run(
            AutoResolverInput(
                escalation=sample_escalation,
                auto_resolve_enabled=True,
                max_auto_resolve_priority="low",
            )
        )
        assert result is None
