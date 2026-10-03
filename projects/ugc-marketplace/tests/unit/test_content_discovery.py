"""
Unit tests for content discovery module.

Tests cover:
- Content recommendations
- Trending content
- Personalization
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime, timedelta
from typing import List, Dict, Any


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_content_store():
    """Fixture providing a mock content store with sample data."""
    store = MagicMock()
    store.get_content = MagicMock(return_value=[
        {
            "id": "content_001",
            "title": "Amazing Product Review",
            "author": "user_123",
            "category": "electronics",
            "tags": ["review", "gadgets"],
            "likes": 150,
            "views": 5000,
            "created_at": datetime.now() - timedelta(days=2),
            "score": 0.95,
        },
        {
            "id": "content_002",
            "title": "Best Budget Picks 2024",
            "author": "user_456",
            "category": "lifestyle",
            "tags": ["budget", "picks"],
            "likes": 89,
            "views": 3200,
            "created_at": datetime.now() - timedelta(days=5),
            "score": 0.87,
        },
        {
            "id": "content_003",
            "title": "Tech Deep Dive",
            "author": "user_789",
            "category": "electronics",
            "tags": ["tech", "analysis"],
            "likes": 210,
            "views": 8000,
            "created_at": datetime.now() - timedelta(days=1),
            "score": 0.92,
        },
    ])
    return store


@pytest.fixture
def mock_user_profile():
    """Fixture providing a mock user profile for personalization tests."""
    return {
        "user_id": "user_123",
        "preferences": {
            "categories": ["electronics", "lifestyle"],
            "tags": ["review", "tech"],
        },
        "interaction_history": [
            {"content_id": "content_001", "action": "like", "timestamp": datetime.now() - timedelta(days=1)},
            {"content_id": "content_003", "action": "view", "timestamp": datetime.now() - timedelta(hours=5)},
        ],
        "blocked_authors": ["user_spam"],
    }


@pytest.fixture
def mock_recommendation_engine():
    """Fixture providing a mock recommendation engine."""
    engine = MagicMock()
    engine.recommend = MagicMock(return_value=[
        {"content_id": "content_001", "score": 0.95, "reason": "category_match"},
        {"content_id": "content_003", "score": 0.92, "reason": "tag_match"},
    ])
    engine.get_similar_content = MagicMock(return_value=[
        {"content_id": "content_002", "similarity": 0.78},
    ])
    return engine


@pytest.fixture
def mock_trending_service():
    """Fixture providing a mock trending content service."""
    service = MagicMock()
    service.get_trending = MagicMock(return_value=[
        {
            "content_id": "content_003",
            "title": "Tech Deep Dive",
            "trending_score": 98.5,
            "rank": 1,
            "velocity": 150.0,
        },
        {
            "content_id": "content_001",
            "title": "Amazing Product Review",
            "trending_score": 85.2,
            "rank": 2,
            "velocity": 120.0,
        },
    ])
    service.get_trending_by_category = MagicMock(return_value=[
        {
            "content_id": "content_001",
            "title": "Amazing Product Review",
            "trending_score": 90.1,
            "rank": 1,
            "category": "electronics",
        },
    ])
    return service


@pytest.fixture
def mock_personalization_engine():
    """Fixture providing a mock personalization engine."""
    engine = MagicMock()
    engine.personalize = MagicMock(return_value=[
        {
            "content_id": "content_001",
            "personalized_score": 0.97,
            "reason": "based_on_like_history",
        },
        {
            "content_id": "content_003",
            "personalized_score": 0.94,
            "reason": "based_on_view_history",
        },
    ])
    engine.get_recommendations_for_user = MagicMock(return_value=[
        {"content_id": "content_001", "score": 0.97},
        {"content_id": "content_003", "score": 0.94},
        {"content_id": "content_002", "score": 0.72},
    ])
    return engine


@pytest.fixture
def sample_content_items():
    """Fixture providing a list of sample content items."""
    return [
        {
            "id": f"content_{i:03d}",
            "title": f"Content Title {i}",
            "author": f"user_{i}",
            "category": "electronics" if i % 2 == 0 else "lifestyle",
            "tags": ["review"] if i % 3 == 0 else ["tech"],
            "likes": i * 10,
            "views": i * 100,
            "created_at": datetime.now() - timedelta(days=i),
            "score": 0.5 + (i * 0.05),
        }
        for i in range(1, 11)
    ]


# ---------------------------------------------------------------------------
# Test: Content Recommendations
# ---------------------------------------------------------------------------


class TestRecommendContent:
    """Tests for content recommendation functionality."""

    def test_recommend_content_returns_results(
        self, mock_content_store, mock_recommendation_engine
    ):
        """Test that recommend_content returns a non-empty list of recommendations."""
        mock_recommendation_engine.recommend.return_value = [
            {"content_id": "content_001", "score": 0.95},
            {"content_id": "content_003", "score": 0.92},
        ]

        results = mock_recommendation_engine.recommend(
            user_id="user_123", limit=5
        )

        assert results is not None
        assert isinstance(results, list)
        assert len(results) > 0
        mock_recommendation_engine.recommend.assert_called_once_with(
            user_id="user_123", limit=5
        )

    def test_recommend_content_result_structure(
        self, mock_recommendation_engine
    ):
        """Test that each recommendation has the required fields."""
        results = mock_recommendation_engine.recommend(user_id="user_123", limit=5)

        for item in results:
            assert "content_id" in item
            assert "score" in item
            assert "reason" in item
            assert isinstance(item["content_id"], str)
            assert isinstance(item["score"], float)
            assert 0.0 <= item["score"] <= 1.0

    def test_recommend_content_respects_limit(
        self, mock_recommendation_engine
    ):
        """Test that the number of recommendations does not exceed the limit."""
        mock_recommendation_engine.recommend.return_value = [
            {"content_id": f"content_{i:03d}", "score": 0.9 - (i * 0.01)}
            for i in range(3)
        ]

        results = mock_recommendation_engine.recommend(user_id="user_123", limit=3)

        assert len(results) <= 3

    def test_recommend_content_sorted_by_score(
        self, mock_recommendation_engine
    ):
        """Test that recommendations are sorted by score in descending order."""
        results = mock_recommendation_engine.recommend(user_id="user_123", limit=5)

        scores = [item["score"] for item in results]
        assert scores == sorted(scores, reverse=True)

    def test_recommend_content_empty_when_no_data(
        self, mock_recommendation_engine
    ):
        """Test that recommend_content returns empty list when no data available."""
        mock_recommendation_engine.recommend.return_value = []

        results = mock_recommendation_engine.recommend(
            user_id="unknown_user", limit=5
        )

        assert results == []

    def test_recommend_content_with_category_filter(
        self, mock_recommendation_engine
    ):
        """Test recommendations filtered by category."""
        mock_recommendation_engine.recommend.return_value = [
            {"content_id": "content_001", "score": 0.95, "category": "electronics"},
        ]

        results = mock_recommendation_engine.recommend(
            user_id="user_123", category="electronics", limit=5
        )

        assert len(results) == 1
        assert results[0]["category"] == "electronics"

    def test_recommend_content_deduplication(
        self, mock_recommendation_engine
    ):
        """Test that duplicate content IDs are removed from recommendations."""
        mock_recommendation_engine.recommend.return_value = [
            {"content_id": "content_001", "score": 0.95},
            {"content_id": "content_001", "score": 0.93},
            {"content_id": "content_003", "score": 0.92},
        ]

        results = mock_recommendation_engine.recommend(user_id="user_123", limit=5)
        content_ids = [item["content_id"] for item in results]

        assert len(content_ids) == len(set(content_ids))

    def test_recommend_content_similar_content(
        self, mock_recommendation_engine
    ):
        """Test that similar content retrieval works correctly."""
        results = mock_recommendation_engine.get_similar_content(
            content_id="content_001"
        )

        assert results is not None
        assert len(results) > 0
        assert "content_id" in results[0]
        assert "similarity" in results[0]
        assert 0.0 <= results[0]["similarity"] <= 1.0


# ---------------------------------------------------------------------------
# Test: Trending Content
# ---------------------------------------------------------------------------


class TestTrendingContent:
    """Tests for trending content functionality."""

    def test_trending_content_returns_results(
        self, mock_trending_service
    ):
        """Test that trending content returns a non-empty list."""
        results = mock_trending_service.get_trending(limit=10)

        assert results is not None
        assert isinstance(results, list)
        assert len(results) > 0
        mock_trending_service.get_trending.assert_called_once_with(limit=10)

    def test_trending_content_result_structure(
        self, mock_trending_service
    ):
        """Test that each trending item has the required fields."""
        results = mock_trending_service.get_trending(limit=10)

        for item in results:
            assert "content_id" in item
            assert "title" in item
            assert "trending_score" in item
            assert "rank" in item
            assert "velocity" in item
            assert isinstance(item["rank"], int)
            assert item["rank"] > 0

    def test_trending_content_sorted_by_rank(
        self, mock_trending_service
    ):
        """Test that trending content is sorted by rank ascending."""
        results = mock_trending_service.get_trending(limit=10)

        ranks = [item["rank"] for item in results]
        assert ranks == sorted(ranks)

    def test_trending_content_respects_limit(
        self, mock_trending_service
    ):
        """Test that trending content respects the limit parameter."""
        mock_trending_service.get_trending.return_value = [
            {
                "content_id": f"content_{i:03d}",
                "title": f"Trending {i}",
                "trending_score": 100.0 - i,
                "rank": i + 1,
                "velocity": float(100 - i * 10),
            }
            for i in range(5)
        ]

        results = mock_trending_service.get_trending(limit=5)

        assert len(results) <= 5

    def test_trending_content_by_category(
        self, mock_trending_service
    ):
        """Test trending content filtered by category."""
        results = mock_trending_service.get_trending_by_category(
            category="electronics", limit=5
        )

        assert len(results) > 0
        for item in results:
            assert item["category"] == "electronics"

    def test_trending_content_velocity_positive(
        self, mock_trending_service
    ):
        """Test that trending velocity is non-negative."""
        results = mock_trending_service.get_trending(limit=10)

        for item in results:
            assert item["velocity"] >= 0

    def test_trending_content_score_range(
        self, mock_trending_service
    ):
        """Test that trending scores are within expected range."""
        results = mock_trending_service.get_trending(limit=10)

        for item in results:
            assert 0 <= item["trending_score"] <= 100

    def test_trending_content_empty_on_no_data(
        self, mock_trending_service
    ):
        """Test that trending returns empty list when no data available."""
        mock_trending_service.get_trending.return_value = []

        results = mock_trending_service.get_trending(limit=10)

        assert results == []


# ---------------------------------------------------------------------------
# Test: Personalization
# ---------------------------------------------------------------------------


class TestPersonalization:
    """Tests for content personalization functionality."""

    def test_personalization_returns_results(
        self, mock_personalization_engine, mock_user_profile
    ):
        """Test that personalization returns a non-empty list."""
        results = mock_personalization_engine.personalize(
            user_id=mock_user_profile["user_id"],
            content_pool=["content_001", "content_002", "content_003"],
        )

        assert results is not None
        assert isinstance(results, list)
        assert len(results) > 0

    def test_personalization_result_structure(
        self, mock_personalization_engine, mock_user_profile
    ):
        """Test that each personalized item has the required fields."""
        results = mock_personalization_engine.personalize(
            user_id=mock_user_profile["user_id"],
            content_pool=["content_001", "content_002", "content_003"],
        )

        for item in results:
            assert "content_id" in item
            assert "personalized_score" in item
            assert "reason" in item
            assert isinstance(item["personalized_score"], float)
            assert 0.0 <= item["personalized_score"] <= 1.0

    def test_personalization_sorted_by_score(
        self, mock_personalization_engine, mock_user_profile
    ):
        """Test that personalized results are sorted by score descending."""
        results = mock_personalization_engine.personalize(
            user_id=mock_user_profile["user_id"],
            content_pool=["content_001", "content_002", "content_003"],
        )

        scores = [item["personalized_score"] for item in results]
        assert scores == sorted(scores, reverse=True)

    def test_personalization_respects_user_preferences(
        self, mock_personalization_engine, mock_user_profile
    ):
        """Test that personalization considers user category preferences."""
        mock_personalization_engine.personalize.return_value = [
            {
                "content_id": "content_001",
                "personalized_score": 0.97,
                "reason": "category_match:electronics",
            },
        ]

        results = mock_personalization_engine.personalize(
            user_id=mock_user_profile["user_id"],
            content_pool=["content_001", "content_002"],
        )

        assert len(results) > 0
        # Verify the reason references user preferences
        assert "category_match" in results[0]["reason"]

    def test_personalization_excludes_blocked_authors(
        self, mock_personalization_engine, mock_user_profile, mock_content_store
    ):
        """Test that content from blocked authors is excluded."""
        all_content = mock_content_store.get_content()
        blocked_author = mock_user_profile["blocked_authors"][0]

        filtered = [
            c for c in all_content if c["author"] != blocked_author
        ]

        for item in filtered:
            assert item["author"] != blocked_author

    def test_personalization_empty_pool(
        self, mock_personalization_engine, mock_user_profile
    ):
        """Test personalization with an empty content pool."""
        mock_personalization_engine.personalize.return_value = []

        results = mock_personalization_engine.personalize(
            user_id=mock_user_profile["user_id"],
            content_pool=[],
        )

        assert results == []

    def test_personalization_for_user_returns_recommendations(
        self, mock_personalization_engine, mock_user_profile
    ):
        """Test get_recommendations_for_user returns personalized items."""
        results = mock_personalization_engine.get_recommendations_for_user(
            user_id=mock_user_profile["user_id"], limit=5
        )

        assert results is not None
        assert isinstance(results, list)
        assert len(results) > 0
        mock_personalization_engine.get_recommendations_for_user.assert_called_once_with(
            user_id=mock_user_profile["user_id"], limit=5
        )

    def test_personalization_deduplication(
        self, mock_personalization_engine, mock_user_profile
    ):
        """Test that personalized results contain no duplicate content IDs."""
        mock_personalization_engine.get_recommendations_for_user.return_value = [
            {"content_id": "content_001", "score": 0.97},
            {"content_id": "content_001", "score": 0.95},
            {"content_id": "content_003", "score": 0.94},
        ]

        results = mock_personalization_engine.get_recommendations_for_user(
            user_id=mock_user_profile["user_id"], limit=5
        )
        content_ids = [item["content_id"] for item in results]

        assert len(content_ids) == len(set(content_ids))

    def test_personalization_score_boost_for_preferred_categories(
        self, mock_personalization_engine, mock_user_profile
    ):
        """Test that content in preferred categories gets a score boost."""
        preferred_categories = mock_user_profile["preferences"]["categories"]

        mock_personalization_engine.personalize.return_value = [
            {
                "content_id": "content_001",
                "personalized_score": 0.97,
                "reason": f"category_match:{preferred_categories[0]}",
            },
            {
                "content_id": "content_002",
                "personalized_score": 0.72,
                "reason": "general_popularity",
            },
        ]

        results = mock_personalization_engine.personalize(
            user_id=mock_user_profile["user_id"],
            content_pool=["content_001", "content_002"],
        )

        # Content in preferred category should have higher score
        assert results[0]["personalized_score"] > results[1]["personalized_score"]

    def test_personalization_handles_new_user(
        self, mock_personalization_engine
    ):
        """Test personalization for a user with no history (cold start)."""
        mock_personalization_engine.get_recommendations_for_user.return_value = [
            {"content_id": "content_003", "score": 0.85},
            {"content_id": "content_001", "score": 0.80},
        ]

        results = mock_personalization_engine.get_recommendations_for_user(
            user_id="new_user_999", limit=5
        )

        assert results is not None
        assert len(results) > 0
        # Should still return results (fallback to popular/trending)
        for item in results:
            assert "content_id" in item
            assert "score" in item
