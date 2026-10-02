"""Tests for the agent implementations."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from community_curation.agents import (
    ContentRankerAgent,
    TrendSurferAgent,
    QualityFilterAgent,
    TopicClusterAgent,
    CurationExplainerAgent,
)
from community_curation.models import ContentItem, ContentSource


@pytest.fixture
def sample_content_items() -> list[ContentItem]:
    """Create sample content items for testing.

    Returns:
        List of sample content items.
    """
    now = datetime.now(timezone.utc)
    return [
        ContentItem(
            id="item_1",
            title="AI revolution in healthcare",
            body="Artificial intelligence is transforming healthcare with new diagnostics.",
            author="user1",
            source=ContentSource.REDDIT,
            score=150.0,
            comment_count=45,
            created_at=now,
            metadata={"upvote_ratio": 0.95, "award_count": 2, "verified_author": True},
        ),
        ContentItem(
            id="item_2",
            title="Machine learning breakthroughs",
            body="New ML models show promising results in natural language processing.",
            author="user2",
            source=ContentSource.HACKER_NEWS,
            score=89.0,
            comment_count=23,
            created_at=now,
            metadata={"verified_author": False},
        ),
        ContentItem(
            id="item_3",
            title="SPAM BUY NOW!!!",
            body="Click here for amazing deals",
            author="spammer",
            source=ContentSource.REDDIT,
            score=500.0,
            comment_count=0,
            created_at=now,
            metadata={"is_spam": True},
        ),
    ]


class TestContentRankerAgent:
    """Tests for the ContentRankerAgent."""

    @pytest.mark.asyncio
    async def test_rank_returns_ranked_content(self, sample_content_items: list[ContentItem]) -> None:
        """Test that ranker returns ranked content."""
        agent = ContentRankerAgent()
        result = await agent.run(sample_content_items, query="AI")
        assert len(result) > 0
        assert all(hasattr(item, "rank") for item in result)
        assert all(hasattr(item, "ranking_score") for item in result)

    @pytest.mark.asyncio
    async def test_rank_sorts_by_score(self, sample_content_items: list[ContentItem]) -> None:
        """Test that ranker sorts by score descending."""
        agent = ContentRankerAgent()
        result = await agent.run(sample_content_items, query="AI")
        scores = [item.ranking_score for item in result]
        assert scores == sorted(scores, reverse=True)

    @pytest.mark.asyncio
    async def test_rank_assigns_sequential_ranks(self, sample_content_items: list[ContentItem]) -> None:
        """Test that ranker assigns sequential ranks."""
        agent = ContentRankerAgent()
        result = await agent.run(sample_content_items, query="AI")
        ranks = [item.rank for item in result]
        assert ranks == list(range(1, len(result) + 1))


class TestTrendSurferAgent:
    """Tests for the TrendSurferAgent."""

    @pytest.mark.asyncio
    async def test_trends_returns_list(self, sample_content_items: list[ContentItem]) -> None:
        """Test that trend surfer returns a list."""
        agent = TrendSurferAgent()
        result = await agent.run(sample_content_items)
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_trends_empty_input(self) -> None:
        """Test that trend surfer handles empty input."""
        agent = TrendSurferAgent()
        result = await agent.run([])
        assert result == []


class TestQualityFilterAgent:
    """Tests for the QualityFilterAgent."""

    @pytest.mark.asyncio
    async def test_filter_returns_assessments(self, sample_content_items: list[ContentItem]) -> None:
        """Test that filter returns quality assessments."""
        agent = QualityFilterAgent()
        result = await agent.run(sample_content_items)
        assert len(result) == len(sample_content_items)
        assert all(hasattr(item, "quality_score") for item in result)
        assert all(hasattr(item, "is_spam") for item in result)

    @pytest.mark.asyncio
    async def test_filter_detects_spam(self, sample_content_items: list[ContentItem]) -> None:
        """Test that filter detects spam content."""
        agent = QualityFilterAgent()
        result = await agent.run(sample_content_items)
        spam_items = [r for r in result if r.is_spam]
        assert len(spam_items) > 0


class TestTopicClusterAgent:
    """Tests for the TopicClusterAgent."""

    @pytest.mark.asyncio
    async def test_cluster_returns_list(self, sample_content_items: list[ContentItem]) -> None:
        """Test that cluster agent returns a list."""
        agent = TopicClusterAgent()
        result = await agent.run(sample_content_items)
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_cluster_empty_input(self) -> None:
        """Test that cluster agent handles empty input."""
        agent = TopicClusterAgent()
        result = await agent.run([])
        assert result == []


class TestCurationExplainerAgent:
    """Tests for the CurationExplainerAgent."""

    @pytest.mark.asyncio
    async def test_explainer_returns_string(self, sample_content_items: list[ContentItem]) -> None:
        """Test that explainer returns a string."""
        agent = CurationExplainerAgent()
        ranked = []
        trends = []
        clusters = []
        quality = []
        result = await agent.run((ranked, trends, clusters, quality))
        assert isinstance(result, str)
        assert len(result) > 0
