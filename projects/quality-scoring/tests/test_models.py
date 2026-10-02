"""Tests for Pydantic models."""

from __future__ import annotations

from datetime import datetime

import pytest
from pydantic import ValidationError

from quality_scoring.models.schemas import (
    ContentInput,
    ContentType,
    DimensionScore,
    QualityScore,
    ScoreDimension,
    ScoreLevel,
)


class TestContentInput:
    """Tests for ContentInput model."""

    def test_valid_content_input(self):
        content = ContentInput(content="This is valid content for testing.")
        assert content.content_type == ContentType.GENERAL
        assert content.language == "en"

    def test_empty_content_raises_error(self):
        with pytest.raises(ValidationError):
            ContentInput(content="")

    def test_whitespace_only_content_raises_error(self):
        with pytest.raises(ValidationError):
            ContentInput(content="   \n\t  ")

    def test_content_with_metadata(self):
        content = ContentInput(
            content="Test content",
            metadata={"author": "test", "tags": ["test"]},
        )
        assert content.metadata["author"] == "test"


class TestDimensionScore:
    """Tests for DimensionScore model."""

    def test_valid_dimension_score(self):
        score = DimensionScore(
            dimension=ScoreDimension.READABILITY,
            score=75.5,
            level=ScoreLevel.GOOD,
            confidence=0.9,
            reasoning="Good readability",
        )
        assert score.score == 75.5
        assert score.level == ScoreLevel.GOOD

    def test_score_out_of_range_raises_error(self):
        with pytest.raises(ValidationError):
            DimensionScore(
                dimension=ScoreDimension.READABILITY,
                score=150.0,
                level=ScoreLevel.EXCELLENT,
                confidence=0.9,
                reasoning="Invalid",
            )

    def test_confidence_out_of_range_raises_error(self):
        with pytest.raises(ValidationError):
            DimensionScore(
                dimension=ScoreDimension.READABILITY,
                score=50.0,
                level=ScoreLevel.AVERAGE,
                confidence=1.5,
                reasoning="Invalid",
            )


class TestQualityScore:
    """Tests for QualityScore model."""

    def test_valid_quality_score(self):
        score = QualityScore(
            id="test-123",
            content_type=ContentType.ARTICLE,
            overall_score=80.0,
            overall_level=ScoreLevel.GOOD,
            dimensions=[],
            word_count=100,
            reading_time_minutes=0.5,
            processing_time_ms=150.0,
        )
        assert score.overall_score == 80.0
        assert score.word_count == 100

    def test_quality_score_with_dimensions(self):
        dim_score = DimensionScore(
            dimension=ScoreDimension.READABILITY,
            score=85.0,
            level=ScoreLevel.GOOD,
            confidence=0.9,
            reasoning="Good",
        )
        score = QualityScore(
            id="test-456",
            content_type=ContentType.BLOG_POST,
            overall_score=85.0,
            overall_level=ScoreLevel.GOOD,
            dimensions=[dim_score],
            word_count=200,
            reading_time_minutes=1.0,
            processing_time_ms=200.0,
        )
        assert len(score.dimensions) == 1
