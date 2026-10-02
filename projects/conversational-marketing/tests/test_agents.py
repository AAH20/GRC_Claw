"""Tests for Conversational Marketing agents."""

from __future__ import annotations

import pytest

from conversational_marketing.agents.analytics import AnalyticsAgent
from conversational_marketing.agents.handoff import HandoffAgent
from conversational_marketing.agents.intent_detection import IntentDetectionAgent
from conversational_marketing.agents.optimization import OptimizationAgent
from conversational_marketing.agents.response_generation import ResponseGenerationAgent


class TestIntentDetectionAgent:
    """Tests for IntentDetectionAgent."""

    @pytest.fixture
    def agent(self) -> IntentDetectionAgent:
        return IntentDetectionAgent()

    @pytest.mark.asyncio
    async def test_detect(self, agent: IntentDetectionAgent) -> None:
        result = await agent.detect("I want to buy a product")
        assert result is not None
        assert result.intent is not None

    @pytest.mark.asyncio
    async def test_detect_with_context(self, agent: IntentDetectionAgent) -> None:
        context = [{"role": "user", "content": "Hello"}]
        result = await agent.detect("I want to buy", context=context)
        assert result is not None


class TestResponseGenerationAgent:
    """Tests for ResponseGenerationAgent."""

    @pytest.fixture
    def agent(self) -> ResponseGenerationAgent:
        return ResponseGenerationAgent()

    @pytest.mark.asyncio
    async def test_generate(self, agent: ResponseGenerationAgent) -> None:
        result = await agent.generate("Hello, I need help")
        assert result is not None


class TestHandoffAgent:
    """Tests for HandoffAgent."""

    @pytest.fixture
    def agent(self) -> HandoffAgent:
        return HandoffAgent()

    @pytest.mark.asyncio
    async def test_evaluate(self, agent: HandoffAgent) -> None:
        result = await agent.evaluate("I want to talk to a human")
        assert result is not None

    def test_is_explicit_handoff_request(self, agent: HandoffAgent) -> None:
        assert agent._is_explicit_handoff_request("talk to human") is True
        assert agent._is_explicit_handoff_request("hello") is False


class TestAnalyticsAgent:
    """Tests for AnalyticsAgent."""

    @pytest.fixture
    def agent(self) -> AnalyticsAgent:
        return AnalyticsAgent()

    @pytest.mark.asyncio
    async def test_track_conversation(self, agent: AnalyticsAgent) -> None:
        from conversational_marketing.agents.analytics import ConversationMetrics

        metrics = ConversationMetrics(
            conversation_id="conv-123",
            intent="purchase",
            outcome="converted",
        )
        await agent.track_conversation(metrics)

    @pytest.mark.asyncio
    async def test_get_summary(self, agent: AnalyticsAgent) -> None:
        summary = await agent.get_summary()
        assert isinstance(summary, dict)

    @pytest.mark.asyncio
    async def test_get_realtime_metrics(self, agent: AnalyticsAgent) -> None:
        metrics = await agent.get_realtime_metrics()
        assert isinstance(metrics, dict)


class TestOptimizationAgent:
    """Tests for OptimizationAgent."""

    @pytest.fixture
    def agent(self) -> OptimizationAgent:
        return OptimizationAgent()

    @pytest.mark.asyncio
    async def test_analyze(self, agent: OptimizationAgent) -> None:
        result = await agent.analyze()
        assert result is not None
