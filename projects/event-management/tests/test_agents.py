"""Tests for Event Management agents."""

from __future__ import annotations

import pytest

from event_management.agents.base import AgentConfig, AgentContext, AgentResult
from event_management.agents.execution import ExecutionAgent, ExecutionInput
from event_management.agents.followup import FollowUpAgent, FollowUpInput
from event_management.agents.performance_analytics import (
    AnalyticsInput,
    PerformanceAnalyticsAgent,
)
from event_management.agents.planning import PlanningAgent, PlanningInput
from event_management.agents.promotion import PromotionAgent, PromotionInput


class TestAgentConfig:
    """Tests for AgentConfig."""

    def test_default_values(self) -> None:
        config = AgentConfig()
        assert config.model == "gpt-4"
        assert config.max_tokens == 4096
        assert config.temperature == 0.7
        assert config.timeout_seconds == 120
        assert config.retry_attempts == 3
        assert config.retry_delay_seconds == 1.0

    def test_custom_values(self) -> None:
        config = AgentConfig(model="gpt-3.5", max_tokens=2048, temperature=0.5)
        assert config.model == "gpt-3.5"
        assert config.max_tokens == 2048
        assert config.temperature == 0.5


class TestAgentContext:
    """Tests for AgentContext."""

    def test_create_context(self) -> None:
        ctx = AgentContext(event_id="evt-123", user_id="user-456")
        assert ctx.event_id == "evt-123"
        assert ctx.user_id == "user-456"
        assert ctx.metadata == {}
        assert ctx.trace_id is None

    def test_context_with_metadata(self) -> None:
        ctx = AgentContext(
            event_id="evt-123",
            metadata={"key": "value"},
            trace_id="trace-789",
        )
        assert ctx.metadata == {"key": "value"}
        assert ctx.trace_id == "trace-789"


class TestAgentResult:
    """Tests for AgentResult."""

    def test_success_result(self) -> None:
        result = AgentResult(success=True, data={"key": "value"}, message="OK")
        assert result.success is True
        assert result.data == {"key": "value"}
        assert result.message == "OK"
        assert result.execution_time_ms == 0.0
        assert result.agent_name == ""

    def test_failure_result(self) -> None:
        result = AgentResult(success=False, message="Error occurred")
        assert result.success is False
        assert result.message == "Error occurred"


class TestPlanningAgent:
    """Tests for PlanningAgent."""

    @pytest.fixture
    def agent(self) -> PlanningAgent:
        return PlanningAgent()

    def test_name(self, agent: PlanningAgent) -> None:
        assert agent.name == "PlanningAgent"

    @pytest.mark.asyncio
    async def test_execute(self, agent: PlanningAgent) -> None:
        input_data = PlanningInput(
            event_name="Test Event",
            event_type="conference",
            expected_attendees=200,
            date="2026-01-01",
            duration_hours=8.0,
            budget_total=10000.0,
        )
        ctx = AgentContext(event_id="evt-123")
        result = await agent.execute(input_data, ctx)
        assert result is not None


class TestExecutionAgent:
    """Tests for ExecutionAgent."""

    @pytest.fixture
    def agent(self) -> ExecutionAgent:
        return ExecutionAgent()

    def test_name(self, agent: ExecutionAgent) -> None:
        assert agent.name == "ExecutionAgent"

    @pytest.mark.asyncio
    async def test_execute(self, agent: ExecutionAgent) -> None:
        input_data = ExecutionInput(
            event_name="Test Event",
            event_date="2026-01-01",
            venue="Convention Center",
            expected_attendees=200,
            staff_count=20,
        )
        ctx = AgentContext(event_id="evt-123")
        result = await agent.execute(input_data, ctx)
        assert result is not None


class TestPromotionAgent:
    """Tests for PromotionAgent."""

    @pytest.fixture
    def agent(self) -> PromotionAgent:
        return PromotionAgent()

    def test_name(self, agent: PromotionAgent) -> None:
        assert agent.name == "PromotionAgent"

    @pytest.mark.asyncio
    async def test_execute(self, agent: PromotionAgent) -> None:
        input_data = PromotionInput(
            event_name="Test Event",
            event_type="conference",
            event_date="2026-01-01",
            target_audience="developers",
            ticket_price=100.0,
            expected_attendees=200,
            marketing_budget=5000.0,
        )
        ctx = AgentContext(event_id="evt-123")
        result = await agent.execute(input_data, ctx)
        assert result is not None


class TestFollowUpAgent:
    """Tests for FollowUpAgent."""

    @pytest.fixture
    def agent(self) -> FollowUpAgent:
        return FollowUpAgent()

    def test_name(self, agent: FollowUpAgent) -> None:
        assert agent.name == "FollowUpAgent"

    @pytest.mark.asyncio
    async def test_execute(self, agent: FollowUpAgent) -> None:
        input_data = FollowUpInput(
            event_name="Test Event",
            event_date="2026-01-01",
            attendee_count=150,
            speaker_count=5,
            sponsor_count=3,
        )
        ctx = AgentContext(event_id="evt-123")
        result = await agent.execute(input_data, ctx)
        assert result is not None


class TestPerformanceAnalyticsAgent:
    """Tests for PerformanceAnalyticsAgent."""

    @pytest.fixture
    def agent(self) -> PerformanceAnalyticsAgent:
        return PerformanceAnalyticsAgent()

    def test_name(self, agent: PerformanceAnalyticsAgent) -> None:
        assert agent.name == "PerformanceAnalyticsAgent"

    @pytest.mark.asyncio
    async def test_execute(self, agent: PerformanceAnalyticsAgent) -> None:
        input_data = AnalyticsInput(
            event_name="Test Event",
            event_date="2026-01-01",
            total_budget=10000.0,
            actual_spend=8000.0,
            ticket_revenue=15000.0,
            sponsorship_revenue=5000.0,
            attendee_count=150,
            registered_count=200,
            check_in_count=140,
        )
        ctx = AgentContext(event_id="evt-123")
        result = await agent.execute(input_data, ctx)
        assert result is not None
