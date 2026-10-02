"""Tests for agent implementations."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from content_discovery.agents import (
    PersonalizationAgent,
    RecommendationAgent,
    SearchExplainerAgent,
    SemanticSearchAgent,
    TrendDetectorAgent,
)
from content_discovery.models import (
    RecommendationRequest,
    SearchRequest,
    SearchResponse,
    SearchResult,
    TrendRequest,
)


class TestSemanticSearchAgent:
    """Tests for SemanticSearchAgent."""

    @pytest.fixture
    def mock_vector_store(self) -> MagicMock:
        """Create mock vector store.

        Returns:
            MagicMock: Mock vector store client.
        """
        store = MagicMock()
        store.search = MagicMock(return_value=[
            {
                "id": "1",
                "title": "Test Article",
                "content": "Test content about AI",
                "score": 0.95,
                "metadata": {"tags": ["ai", "ml"]},
                "content_type": "article",
            },
            {
                "id": "2",
                "title": "Another Article",
                "content": "More content",
                "score": 0.85,
                "metadata": {},
                "content_type": "blog",
            },
        ])
        return store

    @pytest.fixture
    def agent(self, mock_vector_store: MagicMock) -> SemanticSearchAgent:
        """Create semantic search agent.

        Args:
            mock_vector_store: Mock vector store.

        Returns:
            SemanticSearchAgent: Agent instance.
        """
        return SemanticSearchAgent(vector_store=mock_vector_store)

    @pytest.mark.asyncio
    async def test_search_returns_results(
        self, agent: SemanticSearchAgent
    ) -> None:
        """Test that search returns results.

        Args:
            agent: Semantic search agent.
        """
        request = SearchRequest(query="AI", limit=5)
        response = await agent.execute(request)

        assert isinstance(response, SearchResponse)
        assert response.query == "AI"
        assert len(response.results) > 0
        assert response.took_ms > 0

    @pytest.mark.asyncio
    async def test_search_with_empty_results(
        self, mock_vector_store: MagicMock
    ) -> None:
        """Test search with no results.

        Args:
            mock_vector_store: Mock vector store.
        """
        mock_vector_store.search.return_value = []
        agent = SemanticSearchAgent(vector_store=mock_vector_store)
        request = SearchRequest(query="nonexistent", limit=5)
        response = await agent.execute(request)

        assert len(response.results) == 0
        assert response.total == 0

    @pytest.mark.asyncio
    async def test_search_applies_min_score_filter(
        self, mock_vector_store: MagicMock
    ) -> None:
        """Test that min_score filter is applied.

        Args:
            mock_vector_store: Mock vector store.
        """
        mock_vector_store.search.return_value = [
            {"id": "1", "title": "High", "content": "Content", "score": 0.9},
            {"id": "2", "title": "Low", "content": "Content", "score": 0.1},
        ]
        agent = SemanticSearchAgent(vector_store=mock_vector_store)
        request = SearchRequest(query="test", min_score=0.5)
        response = await agent.execute(request)

        assert all(r.score >= 0.5 for r in response.results)


class TestPersonalizationAgent:
    """Tests for PersonalizationAgent."""

    @pytest.fixture
    def mock_user_profile(self) -> MagicMock:
        """Create mock user profile client.

        Returns:
            MagicMock: Mock user profile client.
        """
        profile = MagicMock()
        profile.get_history = MagicMock(return_value=[
            {
                "id": "1",
                "title": "Python Tutorial",
                "tags": ["python", "programming"],
                "content_type": "article",
                "author": "John",
            },
        ])
        profile.get_candidates = MagicMock(return_value=[
            {
                "id": "2",
                "title": "Advanced Python",
                "tags": ["python", "advanced"],
                "content_type": "article",
            },
        ])
        return profile

    @pytest.fixture
    def agent(self, mock_user_profile: MagicMock) -> PersonalizationAgent:
        """Create personalization agent.

        Args:
            mock_user_profile: Mock user profile.

        Returns:
            PersonalizationAgent: Agent instance.
        """
        return PersonalizationAgent(user_profile=mock_user_profile)

    @pytest.mark.asyncio
    async def test_recommendations_returned(
        self, agent: PersonalizationAgent
    ) -> None:
        """Test that recommendations are returned.

        Args:
            agent: Personalization agent.
        """
        request = RecommendationRequest(user_id="user_1", limit=5)
        response = await agent.execute(request)

        assert response.user_id == "user_1"
        assert isinstance(response.recommendations, list)
        assert response.took_ms > 0

    @pytest.mark.asyncio
    async def test_empty_history_handled(
        self, mock_user_profile: MagicMock
    ) -> None:
        """Test handling of empty user history.

        Args:
            mock_user_profile: Mock user profile.
        """
        mock_user_profile.get_history.return_value = []
        mock_user_profile.get_candidates.return_value = []
        agent = PersonalizationAgent(user_profile=mock_user_profile)
        request = RecommendationRequest(user_id="new_user", limit=5)
        response = await agent.execute(request)

        assert len(response.recommendations) == 0


class TestTrendDetectorAgent:
    """Tests for TrendDetectorAgent."""

    @pytest.fixture
    def mock_analytics(self) -> MagicMock:
        """Create mock analytics client.

        Returns:
            MagicMock: Mock analytics client.
        """
        analytics = MagicMock()
        analytics.get_top_topics = MagicMock(return_value=["AI", "blockchain", "cloud"])
        analytics.get_volume = MagicMock(return_value=[
            {"date": "2024-01-01", "count": 100},
            {"date": "2024-01-02", "count": 150},
            {"date": "2024-01-03", "count": 200},
        ])
        analytics.get_related_topics = MagicMock(return_value=["ML", "deep learning"])
        return analytics

    @pytest.fixture
    def agent(self, mock_analytics: MagicMock) -> TrendDetectorAgent:
        """Create trend detector agent.

        Args:
            mock_analytics: Mock analytics client.

        Returns:
            TrendDetectorAgent: Agent instance.
        """
        return TrendDetectorAgent(analytics=mock_analytics)

    @pytest.mark.asyncio
    async def test_trends_detected(
        self, agent: TrendDetectorAgent
    ) -> None:
        """Test that trends are detected.

        Args:
            agent: Trend detector agent.
        """
        request = TrendRequest(topics=["AI"], window_days=7, limit=5)
        response = await agent.execute(request)

        assert isinstance(response.trends, list)
        assert response.window_days == 7
        assert response.took_ms > 0

    @pytest.mark.asyncio
    async def test_empty_topics_discovers_topics(
        self, agent: TrendDetectorAgent, mock_analytics: MagicMock
    ) -> None:
        """Test that empty topics triggers topic discovery.

        Args:
            agent: Trend detector agent.
            mock_analytics: Mock analytics.
        """
        request = TrendRequest(topics=[], window_days=7)
        response = await agent.execute(request)

        mock_analytics.get_top_topics.assert_called_once()
        assert isinstance(response.trends, list)


class TestRecommendationAgent:
    """Tests for RecommendationAgent."""

    @pytest.fixture
    def mock_content_client(self) -> MagicMock:
        """Create mock content client.

        Returns:
            MagicMock: Mock content client.
        """
        client = MagicMock()
        client.get_features = MagicMock(return_value={
            "id": "1",
            "title": "Test Content",
            "tags": ["python"],
        })
        client.get_by_tags = MagicMock(return_value=[
            {"id": "2", "title": "Related", "tags": ["python"]},
        ])
        return client

    @pytest.fixture
    def mock_user_profile(self) -> MagicMock:
        """Create mock user profile client.

        Returns:
            MagicMock: Mock user profile client.
        """
        profile = MagicMock()
        profile.get_history = MagicMock(return_value=[
            {"id": "1", "title": "Python", "tags": ["python"]},
        ])
        profile.get_similar_users = MagicMock(return_value=["user_2", "user_3"])
        return profile

    @pytest.fixture
    def agent(
        self,
        mock_content_client: MagicMock,
        mock_user_profile: MagicMock,
    ) -> RecommendationAgent:
        """Create recommendation agent.

        Args:
            mock_content_client: Mock content client.
            mock_user_profile: Mock user profile.

        Returns:
            RecommendationAgent: Agent instance.
        """
        return RecommendationAgent(
            content_client=mock_content_client,
            user_profile=mock_user_profile,
        )

    @pytest.mark.asyncio
    async def test_recommendations_generated(
        self, agent: RecommendationAgent
    ) -> None:
        """Test that recommendations are generated.

        Args:
            agent: Recommendation agent.
        """
        request = RecommendationRequest(user_id="user_1", limit=5)
        response = await agent.execute(request)

        assert response.user_id == "user_1"
        assert isinstance(response.recommendations, list)
        assert response.took_ms > 0

    @pytest.mark.asyncio
    async def test_deduplication(
        self, agent: RecommendationAgent
    ) -> None:
        """Test that duplicate recommendations are removed.

        Args:
            agent: Recommendation agent.
        """
        request = RecommendationRequest(user_id="user_1", limit=10)
        response = await agent.execute(request)

        content_ids = [r.content_id for r in response.recommendations]
        assert len(content_ids) == len(set(content_ids))


class TestSearchExplainerAgent:
    """Tests for SearchExplainerAgent."""

    @pytest.fixture
    def agent(self) -> SearchExplainerAgent:
        """Create search explainer agent.

        Returns:
            SearchExplainerAgent: Agent instance.
        """
        return SearchExplainerAgent()

    @pytest.mark.asyncio
    async def test_explanation_generated(
        self, agent: SearchExplainerAgent
    ) -> None:
        """Test that explanation is generated.

        Args:
            agent: Search explainer agent.
        """
        request = SearchRequest(query="test")
        response = SearchResponse(
            results=[
                SearchResult(id="1", title="Test", content="Content", score=0.9),
            ],
            total=1,
            query="test",
            took_ms=100.0,
        )

        explanation = await agent.execute((request, response))

        assert explanation.query == "test"
        assert explanation.explanation
        assert isinstance(explanation.factors, list)
        assert 0 <= explanation.confidence <= 1

    @pytest.mark.asyncio
    async def test_empty_results_explanation(
        self, agent: SearchExplainerAgent
    ) -> None:
        """Test explanation for empty results.

        Args:
            agent: Search explainer agent.
        """
        request = SearchRequest(query="nonexistent")
        response = SearchResponse(
            results=[],
            total=0,
            query="nonexistent",
            took_ms=50.0,
        )

        explanation = await agent.execute((request, response))

        assert "no results" in explanation.explanation.lower() or "0" in explanation.explanation
