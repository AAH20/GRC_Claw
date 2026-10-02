"""Tests for moderation agents."""

import pytest

from moderation_queue.agents.auto_moderator import AutoModeratorAgent
from moderation_queue.agents.human_review_router import HumanReviewRouterAgent
from moderation_queue.agents.priority_scorer import PriorityScorerAgent


class TestPriorityScorerAgent:
    @pytest.fixture
    def agent(self):
        return PriorityScorerAgent()

    async def test_heuristic_score_low_priority(self, agent):
        result = await agent.process({
            "content": "Hello, this is a normal message.",
            "content_type": "text",
            "user_history": {"prior_violations": 0},
        })
        assert result.success
        assert result.data["priority"] <= 3

    async def test_heuristic_score_high_priority(self, agent):
        result = await agent.process({
            "content": "This contains violence and hate speech",
            "content_type": "text",
            "user_history": {"prior_violations": 5},
        })
        assert result.success
        assert result.data["priority"] >= 7

    async def test_empty_content_fails(self, agent):
        result = await agent.process({"content": ""})
        assert not result.success
        assert "No content" in result.error


class TestAutoModeratorAgent:
    @pytest.fixture
    def agent(self):
        return AutoModeratorAgent()

    async def test_heuristic_approve(self, agent):
        result = await agent.process({
            "content": "This is a perfectly fine message.",
            "content_type": "text",
        })
        assert result.success
        assert result.data["decision"] == "approve"

    async def test_heuristic_reject(self, agent):
        result = await agent.process({
            "content": "I will kill and murder everyone",
            "content_type": "text",
        })
        assert result.success
        assert result.data["decision"] == "reject"

    async def test_heuristic_escalate(self, agent):
        result = await agent.process({
            "content": "This is a controversial political opinion",
            "content_type": "text",
        })
        assert result.success
        assert result.data["decision"] == "escalate"


class TestHumanReviewRouterAgent:
    @pytest.fixture
    def agent(self):
        return HumanReviewRouterAgent()

    async def test_heuristic_route_general(self, agent):
        result = await agent.process({
            "content": "Some borderline content",
            "content_type": "text",
            "auto_moderation_result": {"decision": "escalate", "categories": []},
            "priority_score": 5,
        })
        assert result.success
        assert result.data["queue"] == "general"

    async def test_heuristic_route_safety(self, agent):
        result = await agent.process({
            "content": "Content with violence",
            "content_type": "text",
            "auto_moderation_result": {
                "decision": "escalate",
                "categories": ["violence"],
            },
            "priority_score": 8,
        })
        assert result.success
        assert result.data["queue"] == "safety"
        assert result.data["urgency"] == "high"
