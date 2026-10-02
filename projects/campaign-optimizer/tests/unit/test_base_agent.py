"""Unit tests for the base agent class."""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agents.base import AgentContext, AgentResult, AgentStatus, BaseAgent
from core.exceptions import AgentError, AgentMaxIterationsError


class ConcreteAgent(BaseAgent[dict[str, Any]]):
    """Concrete implementation of BaseAgent for testing."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(
            name="Test Agent",
            description="A test agent",
            **kwargs,
        )
        self._execute_call_count = 0

    async def _execute(self, context: AgentContext) -> AgentResult[dict[str, Any]]:
        """Execute test logic.

        Args:
            context: Execution context.

        Returns:
            AgentResult with test data.
        """
        self._execute_call_count += 1
        return AgentResult(
            success=True,
            data={"result": "test_data", "call_count": self._execute_call_count},
            metadata={"test": True},
        )


class FailingAgent(BaseAgent[dict[str, Any]]):
    """Agent that always fails for testing retry logic."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(
            name="Failing Agent",
            description="An agent that fails",
            max_retries=2,
            **kwargs,
        )

    async def _execute(self, context: AgentContext) -> AgentResult[dict[str, Any]]:
        """Always raise an error.

        Args:
            context: Execution context.

        Raises:
            AgentError: Always raised.
        """
        raise AgentError("Intentional failure")


class TestAgentResult:
    """Tests for AgentResult dataclass."""

    def test_success_result(self) -> None:
        """Test creating a successful result."""
        result = AgentResult(success=True, data={"key": "value"})
        assert result.success is True
        assert result.data == {"key": "value"}
        assert result.error is None
        assert result.iterations == 0

    def test_failure_result(self) -> None:
        """Test creating a failure result."""
        result = AgentResult(success=False, error="Something went wrong")
        assert result.success is False
        assert result.error == "Something went wrong"

    def test_duration_calculation(self) -> None:
        """Test duration calculation."""
        start = datetime(2024, 1, 1, 0, 0, 0)
        end = datetime(2024, 1, 1, 0, 0, 5)
        result = AgentResult(success=True, started_at=start, completed_at=end)
        assert result.duration_seconds == 5.0


class TestAgentContext:
    """Tests for AgentContext dataclass."""

    def test_context_creation(self) -> None:
        """Test creating an agent context."""
        context = AgentContext(
            campaign_id="camp_123",
            task="test_task",
            parameters={"key": "value"},
        )
        assert context.campaign_id == "camp_123"
        assert context.task == "test_task"
        assert context.parameters == {"key": "value"}
        assert context.parent_result is None


class TestBaseAgent:
    """Tests for the BaseAgent class."""

    @pytest.mark.asyncio
    async def test_successful_execution(self) -> None:
        """Test successful agent execution."""
        agent = ConcreteAgent()
        context = AgentContext(campaign_id="camp_1", task="test")

        result = await agent.execute(context)

        assert result.success is True
        assert result.data is not None
        assert result.data["result"] == "test_data"
        assert agent.status == AgentStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_execution_with_retries(self) -> None:
        """Test that failing agent retries correctly."""
        agent = FailingAgent(max_retries=2)
        context = AgentContext(campaign_id="camp_1", task="test")

        result = await agent.execute(context)

        assert result.success is False
        assert "Intentional failure" in result.error
        assert agent.status == AgentStatus.FAILED

    @pytest.mark.asyncio
    async def test_execution_timeout(self) -> None:
        """Test that agent times out correctly."""

        class SlowAgent(BaseAgent[dict[str, Any]]):
            def __init__(self, **kwargs: Any) -> None:
                super().__init__(name="Slow Agent", description="Slow", timeout=1, **kwargs)

            async def _execute(self, context: AgentContext) -> AgentResult[dict[str, Any]]:
                await asyncio.sleep(10)
                return AgentResult(success=True)

        agent = SlowAgent()
        context = AgentContext(campaign_id="camp_1", task="test")

        result = await agent.execute(context)

        assert result.success is False
        assert "timed out" in result.error
        assert agent.status == AgentStatus.TIMED_OUT

    def test_agent_status(self) -> None:
        """Test agent status reporting."""
        agent = ConcreteAgent(timeout=60, max_iterations=5)
        status = agent.get_status()

        assert status["name"] == "Test Agent"
        assert status["status"] == "idle"
        assert status["timeout"] == 60
        assert status["max_iterations"] == 5

    def test_agent_properties(self) -> None:
        """Test agent property accessors."""
        agent = ConcreteAgent()
        assert agent.name == "Test Agent"
        assert agent.description == "A test agent"
        assert agent.status == AgentStatus.IDLE
        assert agent.tools == []
