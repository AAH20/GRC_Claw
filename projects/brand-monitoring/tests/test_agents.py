"""Tests for Brand Monitoring agents."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from brand_monitoring.agents.analysis import AnalysisAgent, AnalysisResult, Sentiment, Topic
from brand_monitoring.agents.listening import ListeningAgent, Mention, MentionType, Platform
from brand_monitoring.agents.response import ResponseAgent, ResponseChannel, ResponseType


class TestListeningAgent:
    """Tests for ListeningAgent."""

    @pytest.fixture
    def agent(self) -> ListeningAgent:
        return ListeningAgent(config={})

    def test_register_collector(self, agent: ListeningAgent) -> None:
        collector = MagicMock()
        agent.register_collector(Platform.TWITTER, collector)
        assert Platform.TWITTER in agent.collectors

    @pytest.mark.asyncio
    async def test_health_check(self, agent: ListeningAgent) -> None:
        result = await agent.health_check()
        assert isinstance(result, dict)


class TestAnalysisAgent:
    """Tests for AnalysisAgent."""

    @pytest.fixture
    def agent(self) -> AnalysisAgent:
        return AnalysisAgent(config={})

    @pytest.mark.asyncio
    async def test_analyze(self, agent: AnalysisAgent) -> None:
        mention = MagicMock()
        mention.id = "mention-123"
        mention.content = "This is a great product!"
        result = await agent.analyze(mention)
        assert isinstance(result, AnalysisResult)
        assert result.mention_id == "mention-123"

    @pytest.mark.asyncio
    async def test_analyze_batch(self, agent: AnalysisAgent) -> None:
        mention1 = MagicMock()
        mention1.id = "mention-1"
        mention1.content = "Great product!"
        mention2 = MagicMock()
        mention2.id = "mention-2"
        mention2.content = "Terrible service!"
        results = await agent.analyze_batch([mention1, mention2])
        assert len(results) == 2
        assert all(isinstance(r, AnalysisResult) for r in results)


class TestResponseAgent:
    """Tests for ResponseAgent."""

    @pytest.fixture
    def agent(self) -> ResponseAgent:
        return ResponseAgent(config={})

    @pytest.mark.asyncio
    async def test_generate_response(self, agent: ResponseAgent) -> None:
        mention = MagicMock()
        mention.id = "mention-123"
        mention.content = "This is terrible!"
        mention.platform = Platform.TWITTER
        analysis = AnalysisResult(
            mention_id="mention-123",
            sentiment=Sentiment.NEGATIVE,
            sentiment_score=-0.8,
            topics=[Topic.SUPPORT],
            keywords=["terrible"],
            entities=[],
            urgency=8,
            analyzed_at=datetime.utcnow(),
        )
        result = await agent.generate_response(mention, analysis)
        assert result is not None
        assert result.mention_id == "mention-123"

    def test_determine_response_type(self, agent: ResponseAgent) -> None:
        analysis = AnalysisResult(
            mention_id="m1",
            sentiment=Sentiment.NEGATIVE,
            sentiment_score=-0.8,
            topics=[Topic.SUPPORT],
            keywords=[],
            entities=[],
            urgency=8,
            analyzed_at=datetime.utcnow(),
        )
        response_type = agent._determine_response_type(analysis)
        assert response_type == ResponseType.APOLOGY

    def test_requires_approval(self, agent: ResponseAgent) -> None:
        assert agent._requires_approval(ResponseType.APOLOGY, 0.5) is True
        assert agent._requires_approval(ResponseType.THANK_YOU, 0.9) is False
