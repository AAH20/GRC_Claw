"""Unit tests for quality scoring module."""

import pytest
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_content():
    """Return a sample content item for scoring tests."""
    return {
        "id": "content-001",
        "title": "Amazing Product Review",
        "body": "This product exceeded my expectations in every way.",
        "rating": 5,
        "media_count": 3,
        "word_count": 120,
        "author_id": "user-42",
        "category": "electronics",
    }


@pytest.fixture
def sample_content_low_quality():
    """Return a low-quality content item for comparison tests."""
    return {
        "id": "content-002",
        "title": "ok",
        "body": "fine",
        "rating": 2,
        "media_count": 0,
        "word_count": 5,
        "author_id": "user-99",
        "category": "misc",
    }


@pytest.fixture
def mock_scorer():
    """Return a mock quality scorer with predictable behavior."""
    scorer = MagicMock()
    scorer.score_content.return_value = 0.85
    scorer.compare_quality.return_value = {
        "winner": "content-001",
        "scores": {"content-001": 0.85, "content-002": 0.25},
        "margin": 0.60,
    }
    scorer.quality_breakdown.return_value = {
        "readability": 0.90,
        "engagement": 0.80,
        "media_richness": 0.75,
        "authenticity": 0.85,
        "overall": 0.85,
    }
    return scorer


@pytest.fixture
def scoring_config():
    """Return a scoring configuration dict."""
    return {
        "weights": {
            "readability": 0.30,
            "engagement": 0.25,
            "media_richness": 0.20,
            "authenticity": 0.25,
        },
        "min_word_count": 10,
        "max_word_count": 2000,
        "min_media_count": 0,
        "max_media_count": 10,
    }


# ---------------------------------------------------------------------------
# Tests: score_content
# ---------------------------------------------------------------------------

class TestScoreContent:
    """Tests for content scoring functionality."""

    def test_score_content(self, sample_content, mock_scorer):
        """Test that content scoring returns a valid score for good content."""
        score = mock_scorer.score_content(sample_content)

        assert score == pytest.approx(0.85)
        assert 0.0 <= score <= 1.0
        mock_scorer.score_content.assert_called_once_with(sample_content)

    def test_score_content_returns_float(self, sample_content, mock_scorer):
        """Test that score_content returns a float value."""
        score = mock_scorer.score_content(sample_content)
        assert isinstance(score, float)

    def test_score_content_low_quality(self, sample_content_low_quality, mock_scorer):
        """Test that low-quality content receives a lower score."""
        mock_scorer.score_content.return_value = 0.25
        score = mock_scorer.score_content(sample_content_low_quality)

        assert score == pytest.approx(0.25)
        assert score < 0.5

    def test_score_content_empty_body(self, mock_scorer):
        """Test scoring of content with empty body."""
        empty_content = {
            "id": "content-empty",
            "title": "",
            "body": "",
            "rating": 0,
            "media_count": 0,
            "word_count": 0,
        }
        mock_scorer.score_content.return_value = 0.0
        score = mock_scorer.score_content(empty_content)

        assert score == pytest.approx(0.0)

    def test_score_content_high_word_count(self, mock_scorer):
        """Test scoring of content with very high word count."""
        long_content = {
            "id": "content-long",
            "title": "Extensive Review",
            "body": "word " * 5000,
            "rating": 4,
            "media_count": 5,
            "word_count": 5000,
        }
        mock_scorer.score_content.return_value = 0.70
        score = mock_scorer.score_content(long_content)

        assert score == pytest.approx(0.70)
        assert 0.0 <= score <= 1.0


# ---------------------------------------------------------------------------
# Tests: compare_quality
# ---------------------------------------------------------------------------

class TestCompareQuality:
    """Tests for quality comparison functionality."""

    def test_compare_quality(self, sample_content, sample_content_low_quality, mock_scorer):
        """Test that quality comparison correctly identifies the better content."""
        result = mock_scorer.compare_quality(sample_content, sample_content_low_quality)

        assert result["winner"] == "content-001"
        assert result["scores"]["content-001"] > result["scores"]["content-002"]
        assert result["margin"] == pytest.approx(0.60)
        mock_scorer.compare_quality.assert_called_once_with(
            sample_content, sample_content_low_quality
        )

    def test_compare_quality_returns_dict(self, sample_content, sample_content_low_quality, mock_scorer):
        """Test that compare_quality returns a properly structured dict."""
        result = mock_scorer.compare_quality(sample_content, sample_content_low_quality)

        assert isinstance(result, dict)
        assert "winner" in result
        assert "scores" in result
        assert "margin" in result

    def test_compare_quality_tie(self, sample_content, mock_scorer):
        """Test comparison when both items have equal quality."""
        mock_scorer.compare_quality.return_value = {
            "winner": None,
            "scores": {"content-001": 0.50, "content-002": 0.50},
            "margin": 0.0,
        }
        result = mock_scorer.compare_quality(sample_content, sample_content)

        assert result["winner"] is None
        assert result["margin"] == pytest.approx(0.0)

    def test_compare_quality_margin_positive(self, sample_content, sample_content_low_quality, mock_scorer):
        """Test that the margin is always non-negative."""
        result = mock_scorer.compare_quality(sample_content, sample_content_low_quality)
        assert result["margin"] >= 0.0


# ---------------------------------------------------------------------------
# Tests: quality_breakdown
# ---------------------------------------------------------------------------

class TestQualityBreakdown:
    """Tests for quality breakdown functionality."""

    def test_quality_breakdown(self, sample_content, mock_scorer):
        """Test that quality breakdown returns all expected components."""
        breakdown = mock_scorer.quality_breakdown(sample_content)

        expected_keys = {"readability", "engagement", "media_richness", "authenticity", "overall"}
        assert expected_keys.issubset(breakdown.keys())
        mock_scorer.quality_breakdown.assert_called_once_with(sample_content)

    def test_quality_breakdown_values_in_range(self, sample_content, mock_scorer):
        """Test that all breakdown values are between 0 and 1."""
        breakdown = mock_scorer.quality_breakdown(sample_content)

        for key, value in breakdown.items():
            assert 0.0 <= value <= 1.0, f"{key} score {value} out of range [0, 1]"

    def test_quality_breakdown_overall_is_weighted_average(self, sample_content, mock_scorer, scoring_config):
        """Test that overall score is consistent with weighted component scores."""
        breakdown = mock_scorer.quality_breakdown(sample_content)
        weights = scoring_config["weights"]

        weighted_sum = (
            breakdown["readability"] * weights["readability"]
            + breakdown["engagement"] * weights["engagement"]
            + breakdown["media_richness"] * weights["media_richness"]
            + breakdown["authenticity"] * weights["authenticity"]
        )

        assert breakdown["overall"] == pytest.approx(weighted_sum, abs=0.01)

    def test_quality_breakdown_low_quality_content(self, sample_content_low_quality, mock_scorer):
        """Test breakdown for low-quality content shows low scores across components."""
        mock_scorer.quality_breakdown.return_value = {
            "readability": 0.30,
            "engagement": 0.20,
            "media_richness": 0.10,
            "authenticity": 0.25,
            "overall": 0.25,
        }
        breakdown = mock_scorer.quality_breakdown(sample_content_low_quality)

        assert breakdown["overall"] < 0.5
        assert breakdown["media_richness"] < 0.3

    def test_quality_breakdown_returns_dict(self, sample_content, mock_scorer):
        """Test that quality_breakdown returns a dict."""
        breakdown = mock_scorer.quality_breakdown(sample_content)
        assert isinstance(breakdown, dict)
        assert len(breakdown) >= 4
