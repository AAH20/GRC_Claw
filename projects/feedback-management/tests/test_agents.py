"""Tests for feedback management agent implementations."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from feedback_management.agents.action import (
    Action,
    ActionAgent,
    ActionPriority,
    ActionStatus,
    ActionType,
)
from feedback_management.agents.analysis import (
    AnalysisAgent,
    SentimentResult,
)
from feedback_management.agents.collection import (
    CollectionAgent,
    CollectionResult,
    FeedbackItem,
)
from feedback_management.agents.response import ResponseAgent


def _make_feedback_item(
    text: str = "Great product, love it!",
    rating: float = 5.0,
) -> FeedbackItem:
    return FeedbackItem(
        id="fb_1",
        source="surveymonkey",
        platform="surveymonkey",
        rating=rating,
        text=text,
    )


class TestCollectionAgent:
    """Tests for CollectionAgent."""

    @pytest.fixture
    def agent(self) -> CollectionAgent:
        return CollectionAgent()

    async def test_collect_all(self, agent: CollectionAgent) -> None:
        result = await agent.collect_all(max_items=10)
        assert isinstance(result, CollectionResult)

    async def test_collect_single_unknown_platform(self, agent: CollectionAgent) -> None:
        with pytest.raises(ValueError, match="Unknown platform"):
            await agent.collect_single("unknown", "fb_1")


class TestAnalysisAgent:
    """Tests for AnalysisAgent."""

    @pytest.fixture
    def agent(self) -> AnalysisAgent:
        return AnalysisAgent()

    async def test_analyze_positive(self, agent: AnalysisAgent) -> None:
        item = _make_feedback_item("This is amazing! Great product!")
        result = await agent.analyze(item)
        assert result.feedback_id == "fb_1"
        assert result.sentiment.label == "positive"

    async def test_analyze_negative(self, agent: AnalysisAgent) -> None:
        item = _make_feedback_item("Terrible service, very disappointed", rating=1.0)
        result = await agent.analyze(item)
        assert result.sentiment.label == "negative"

    async def test_analyze_neutral(self, agent: AnalysisAgent) -> None:
        item = _make_feedback_item("The product is okay.")
        result = await agent.analyze(item)
        assert result.sentiment.label in ("neutral", "positive")

    async def test_analyze_batch(self, agent: AnalysisAgent) -> None:
        items = [
            _make_feedback_item("Great!"),
            _make_feedback_item("Terrible!"),
        ]
        result = await agent.analyze_batch(items)
        assert result.total_items == 2
        assert len(result.results) == 2

    async def test_extract_topics(self, agent: AnalysisAgent) -> None:
        item = _make_feedback_item("The customer service was great and delivery was fast")
        result = await agent.analyze(item)
        assert isinstance(result.topics, list)


class TestResponseAgent:
    """Tests for ResponseAgent."""

    @pytest.fixture
    def agent(self) -> ResponseAgent:
        return ResponseAgent()

    async def test_generate_response_positive(self, agent: ResponseAgent) -> None:
        item = _make_feedback_item("Great product!")
        analysis = AnalysisAgent()
        analysis_result = await analysis.analyze(item)
        response = await agent.generate_response(item, analysis_result)
        assert response.feedback_id == "fb_1"
        assert len(response.body) > 0

    async def test_generate_response_negative(self, agent: ResponseAgent) -> None:
        item = _make_feedback_item("Terrible experience", rating=1.0)
        analysis = AnalysisAgent()
        analysis_result = await analysis.analyze(item)
        response = await agent.generate_response(item, analysis_result)
        assert response.requires_approval is True

    async def test_generate_batch(self, agent: ResponseAgent) -> None:
        items = [
            _make_feedback_item("Great!"),
            _make_feedback_item("Bad!"),
        ]
        analysis_agent = AnalysisAgent()
        analyses = [await analysis_agent.analyze(item) for item in items]
        result = await agent.generate_batch(items, analyses)
        assert result.total_generated == 2


class TestActionAgent:
    """Tests for ActionAgent."""

    @pytest.fixture
    def agent(self) -> ActionAgent:
        return ActionAgent()

    async def test_determine_actions_positive(self, agent: ActionAgent) -> None:
        item = _make_feedback_item("Great product!", rating=5.0)
        analysis_agent = AnalysisAgent()
        analysis = await analysis_agent.analyze(item)
        actions = await agent.determine_actions(item, analysis)
        assert isinstance(actions, list)

    async def test_determine_actions_negative(self, agent: ActionAgent) -> None:
        item = _make_feedback_item("Terrible service", rating=1.0)
        analysis_agent = AnalysisAgent()
        analysis = await analysis_agent.analyze(item)
        actions = await agent.determine_actions(item, analysis)
        assert len(actions) > 0

    async def test_execute_action(self, agent: ActionAgent) -> None:
        action = Action(
            id="act_1",
            type=ActionType.CREATE_TICKET,
            priority=ActionPriority.HIGH,
            feedback_id="fb_1",
            description="Test action",
        )
        result = await agent.execute_action(action)
        assert result.success is True
        assert result.action_type == ActionType.CREATE_TICKET
