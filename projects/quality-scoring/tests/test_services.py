"""Tests for scoring services."""

from __future__ import annotations

import pytest

from quality_scoring.models.schemas import (
    ContentInput,
    ContentType,
    DimensionScore,
    ScoreDimension,
    ScoreLevel,
)
from quality_scoring.services import BenchmarkService, ScoringService


class TestScoringService:
    """Tests for ScoringService."""

    @pytest.fixture
    def service(self):
        return ScoringService()

    @pytest.fixture
    def sample_input(self):
        return ContentInput(
            content="# Test Article\n\nThis is a test article with enough content to be scored properly. It has multiple sentences and some structure.",
            content_type=ContentType.ARTICLE,
        )

    @pytest.mark.asyncio
    async def test_score_content_returns_quality_score(self, service, sample_input):
        result = await service.score_content(sample_input)
        assert result.id is not None
        assert result.content_type == ContentType.ARTICLE
        assert 0 <= result.overall_score <= 100
        assert len(result.dimensions) == 4
        assert result.word_count > 0
        assert result.processing_time_ms > 0

    @pytest.mark.asyncio
    async def test_score_content_specific_dimensions(self, service, sample_input):
        result = await service.score_content(
            sample_input,
            dimensions=[ScoreDimension.READABILITY],
        )
        assert len(result.dimensions) == 1
        assert result.dimensions[0].dimension == ScoreDimension.READABILITY

    @pytest.mark.asyncio
    async def test_score_content_caching(self, service, sample_input):
        result1 = await service.score_content(sample_input)
        result2 = await service.score_content(sample_input)
        assert result1.id == result2.id  # Should return cached result

    @pytest.mark.asyncio
    async def test_get_improvements(self, service, sample_input):
        score = await service.score_content(sample_input)
        plan = await service.get_improvements(
            sample_input.content,
            score.id,
            score.dimensions,
        )
        assert plan.id is not None
        assert plan.score_id == score.id
        assert isinstance(plan.suggestions, list)


class TestBenchmarkService:
    """Tests for BenchmarkService."""

    @pytest.fixture
    def service(self):
        return BenchmarkService()

    def test_compare_returns_benchmark_comparison(self, service):
        dimensions = [
            DimensionScore(
                dimension=ScoreDimension.READABILITY,
                score=70.0,
                level=ScoreLevel.GOOD,
                confidence=0.8,
                reasoning="Good",
            ),
            DimensionScore(
                dimension=ScoreDimension.ORIGINALITY,
                score=65.0,
                level=ScoreLevel.GOOD,
                confidence=0.8,
                reasoning="Good",
            ),
        ]
        result = service.compare("test-score-id", ContentType.ARTICLE, dimensions)
        assert result.id is not None
        assert result.score_id == "test-score-id"
        assert result.content_type == ContentType.ARTICLE
        assert len(result.comparisons) == 2
        assert 0 <= result.percentile_overall <= 100
        assert result.summary is not None

    def test_compare_with_high_scores(self, service):
        dimensions = [
            DimensionScore(
                dimension=ScoreDimension.READABILITY,
                score=95.0,
                level=ScoreLevel.EXCELLENT,
                confidence=0.9,
                reasoning="Excellent",
            ),
        ]
        result = service.compare("test-id", ContentType.ARTICLE, dimensions)
        assert result.percentile_overall > 75

    def test_compare_with_low_scores(self, service):
        dimensions = [
            DimensionScore(
                dimension=ScoreDimension.READABILITY,
                score=10.0,
                level=ScoreLevel.POOR,
                confidence=0.9,
                reasoning="Poor",
            ),
        ]
        result = service.compare("test-id", ContentType.ARTICLE, dimensions)
        assert result.percentile_overall < 25
