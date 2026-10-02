"""Tests for the Pydantic models."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from community_curation.models import (
    CurationRequest,
    CurationResult,
    ContentItem,
    ContentSource,
    RankedContent,
    Trend,
    TopicCluster,
    QualityAssessment,
    HealthResponse,
    ErrorResponse,
)


class TestContentItem:
    """Tests for ContentItem model."""

    def test_valid_content_item(self) -> None:
        """Test creating a valid content item."""
        item = ContentItem(
            id="test_1",
            title="Test Title",
            body="Test body",
            source=ContentSource.REDDIT,
            created_at=datetime.now(timezone.utc),
        )
        assert item.id == "test_1"
        assert item.title == "Test Title"
        assert item.source == ContentSource.REDDIT

    def test_content_item_requires_id(self) -> None:
        """Test that content item requires an ID."""
        with pytest.raises(ValidationError):
            ContentItem(
                title="Test",
                source=ContentSource.REDDIT,
                created_at=datetime.now(timezone.utc),
            )

    def test_content_item_defaults(self) -> None:
        """Test content item default values."""
        item = ContentItem(
            id="test_1",
            title="Test",
            source=ContentSource.REDDIT,
            created_at=datetime.now(timezone.utc),
        )
        assert item.body == ""
        assert item.score == 0.0
        assert item.comment_count == 0
        assert item.metadata == {}


class TestCurationRequest:
    """Tests for CurationRequest model."""

    def test_valid_request(self) -> None:
        """Test creating a valid curation request."""
        request = CurationRequest(
            query="AI",
            sources=[ContentSource.REDDIT],
            limit=10,
        )
        assert request.query == "AI"
        assert request.limit == 10

    def test_request_requires_query(self) -> None:
        """Test that request requires a query."""
        with pytest.raises(ValidationError):
            CurationRequest(sources=[ContentSource.REDDIT])

    def test_request_validates_limit_range(self) -> None:
        """Test that request validates limit range."""
        with pytest.raises(ValidationError):
            CurationRequest(query="test", limit=0)
        with pytest.raises(ValidationError):
            CurationRequest(query="test", limit=101)

    def test_request_validates_quality_score(self) -> None:
        """Test that request validates quality score range."""
        with pytest.raises(ValidationError):
            CurationRequest(query="test", min_quality_score=-0.1)
        with pytest.raises(ValidationError):
            CurationRequest(query="test", min_quality_score=1.1)


class TestRankedContent:
    """Tests for RankedContent model."""

    def test_valid_ranked_content(self) -> None:
        """Test creating valid ranked content."""
        item = ContentItem(
            id="test_1",
            title="Test",
            source=ContentSource.REDDIT,
            created_at=datetime.now(timezone.utc),
        )
        ranked = RankedContent(
            content=item,
            rank=1,
            ranking_score=0.95,
        )
        assert ranked.rank == 1
        assert ranked.ranking_score == 0.95


class TestTrend:
    """Tests for Trend model."""

    def test_valid_trend(self) -> None:
        """Test creating a valid trend."""
        trend = Trend(
            id="trend_1",
            name="AI",
            description="AI trend",
            keywords=["ai", "ml"],
            content_count=10,
            velocity=1.5,
            sentiment=0.8,
        )
        assert trend.id == "trend_1"
        assert trend.name == "AI"

    def test_trend_sentiment_range(self) -> None:
        """Test that trend sentiment is within valid range."""
        with pytest.raises(ValidationError):
            Trend(
                id="trend_1",
                name="Test",
                sentiment=1.5,
            )


class TestTopicCluster:
    """Tests for TopicCluster model."""

    def test_valid_cluster(self) -> None:
        """Test creating a valid topic cluster."""
        cluster = TopicCluster(
            id="cluster_1",
            name="AI Topics",
            keywords=["ai", "ml"],
            content_ids=["item_1", "item_2"],
            coherence_score=0.85,
            size=2,
        )
        assert cluster.id == "cluster_1"
        assert cluster.size == 2


class TestQualityAssessment:
    """Tests for QualityAssessment model."""

    def test_valid_assessment(self) -> None:
        """Test creating a valid quality assessment."""
        assessment = QualityAssessment(
            content_id="item_1",
            quality_score=0.9,
            is_spam=False,
            is_low_quality=False,
        )
        assert assessment.content_id == "item_1"
        assert assessment.quality_score == 0.9


class TestCurationResult:
    """Tests for CurationResult model."""

    def test_valid_result(self) -> None:
        """Test creating a valid curation result."""
        result = CurationResult(
            request_id="req_1",
            query="AI",
        )
        assert result.request_id == "req_1"
        assert result.query == "AI"
        assert result.ranked_content == []
        assert result.trends == []
        assert result.clusters == []


class TestHealthResponse:
    """Tests for HealthResponse model."""

    def test_valid_health_response(self) -> None:
        """Test creating a valid health response."""
        response = HealthResponse(
            status="ok",
            version="0.1.0",
        )
        assert response.status == "ok"
        assert response.version == "0.1.0"


class TestErrorResponse:
    """Tests for ErrorResponse model."""

    def test_valid_error_response(self) -> None:
        """Test creating a valid error response."""
        error = ErrorResponse(
            error="not_found",
            detail="Resource not found",
        )
        assert error.error == "not_found"
        assert error.detail == "Resource not found"
