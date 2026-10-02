"""Tests for Pydantic models."""

from __future__ import annotations

from datetime import datetime

import pytest
from pydantic import ValidationError

from content_discovery.models import (
    HealthResponse,
    Recommendation,
    RecommendationRequest,
    SearchExplanation,
    SearchRequest,
    SearchResponse,
    SearchResult,
    Trend,
    TrendDirection,
    TrendRequest,
)


class TestSearchRequest:
    """Tests for SearchRequest model."""

    def test_valid_request(self) -> None:
        """Test valid search request."""
        req = SearchRequest(query="test query")
        assert req.query == "test query"
        assert req.limit == 10
        assert req.offset == 0

    def test_empty_query_fails(self) -> None:
        """Test that empty query fails validation."""
        with pytest.raises(ValidationError):
            SearchRequest(query="")

    def test_limit_bounds(self) -> None:
        """Test limit validation bounds."""
        with pytest.raises(ValidationError):
            SearchRequest(query="test", limit=0)
        with pytest.raises(ValidationError):
            SearchRequest(query="test", limit=100)

    def test_optional_fields(self) -> None:
        """Test optional fields."""
        req = SearchRequest(
            query="test",
            user_id="user_1",
            filters={"category": "tech"},
            include_explanation=True,
        )
        assert req.user_id == "user_1"
        assert req.filters == {"category": "tech"}
        assert req.include_explanation is True


class TestSearchResult:
    """Tests for SearchResult model."""

    def test_valid_result(self) -> None:
        """Test valid search result."""
        result = SearchResult(
            id="1",
            title="Test",
            content="Test content",
            score=0.95,
        )
        assert result.id == "1"
        assert result.score == 0.95

    def test_score_bounds(self) -> None:
        """Test score validation."""
        with pytest.raises(ValidationError):
            SearchResult(id="1", title="Test", content="Content", score=1.5)
        with pytest.raises(ValidationError):
            SearchResult(id="1", title="Test", content="Content", score=-0.1)


class TestSearchResponse:
    """Tests for SearchResponse model."""

    def test_valid_response(self) -> None:
        """Test valid search response."""
        result = SearchResult(id="1", title="Test", content="Content", score=0.9)
        response = SearchResponse(
            results=[result],
            total=1,
            query="test",
            took_ms=100.0,
        )
        assert len(response.results) == 1
        assert response.total == 1


class TestRecommendation:
    """Tests for Recommendation model."""

    def test_valid_recommendation(self) -> None:
        """Test valid recommendation."""
        rec = Recommendation(
            id="rec_1",
            content_id="content_1",
            title="Test Article",
            reason="Because you liked similar content",
            score=0.85,
        )
        assert rec.id == "rec_1"
        assert rec.score == 0.85


class TestRecommendationRequest:
    """Tests for RecommendationRequest model."""

    def test_valid_request(self) -> None:
        """Test valid recommendation request."""
        req = RecommendationRequest(user_id="user_1")
        assert req.user_id == "user_1"
        assert req.limit == 10

    def test_with_context(self) -> None:
        """Test request with context."""
        req = RecommendationRequest(
            user_id="user_1",
            context="reading about AI",
            content_types=["article", "video"],
        )
        assert req.context == "reading about AI"
        assert req.content_types == ["article", "video"]


class TestTrend:
    """Tests for Trend model."""

    def test_valid_trend(self) -> None:
        """Test valid trend."""
        trend = Trend(
            id="trend_1",
            topic="AI",
            direction=TrendDirection.RISING,
            score=0.9,
            volume=1000,
            change_percent=25.0,
        )
        assert trend.topic == "AI"
        assert trend.direction == TrendDirection.RISING

    def test_trend_direction_values(self) -> None:
        """Test trend direction enum values."""
        assert TrendDirection.RISING == "rising"
        assert TrendDirection.FALLING == "falling"
        assert TrendDirection.STABLE == "stable"
        assert TrendDirection.VOLATILE == "volatile"


class TestTrendRequest:
    """Tests for TrendRequest model."""

    def test_valid_request(self) -> None:
        """Test valid trend request."""
        req = TrendRequest(topics=["AI", "ML"], window_days=14)
        assert req.topics == ["AI", "ML"]
        assert req.window_days == 14

    def test_default_values(self) -> None:
        """Test default values."""
        req = TrendRequest()
        assert req.topics == []
        assert req.window_days == 7


class TestSearchExplanation:
    """Tests for SearchExplanation model."""

    def test_valid_explanation(self) -> None:
        """Test valid search explanation."""
        expl = SearchExplanation(
            query="test",
            explanation="Results were selected based on semantic similarity",
            factors=["topic match", "recency"],
            confidence=0.9,
        )
        assert expl.query == "test"
        assert expl.confidence == 0.9


class TestHealthResponse:
    """Tests for HealthResponse model."""

    def test_valid_response(self) -> None:
        """Test valid health response."""
        resp = HealthResponse(
            status="healthy",
            version="0.1.0",
            timestamp=datetime.utcnow(),
            checks={"api": True},
        )
        assert resp.status == "healthy"
