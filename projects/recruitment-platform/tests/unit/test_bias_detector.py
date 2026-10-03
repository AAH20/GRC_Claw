"""Unit tests for the BiasDetector module."""

import pytest
from unittest.mock import MagicMock, patch

from src.agents.bias_detector import BiasDetector, BiasResult


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def detector():
    """Return a fresh BiasDetector instance."""
    return BiasDetector()


@pytest.fixture
def sample_job_description():
    """Return a neutral job description for testing."""
    return (
        "We are looking for a software engineer with strong problem-solving "
        "skills. The ideal candidate will have experience with Python and "
        "cloud platforms. Responsibilities include designing scalable systems "
        "and collaborating with cross-functional teams."
    )


@pytest.fixture
def biased_job_description():
    """Return a job description containing biased language."""
    return (
        "We are seeking a young, energetic rockstar developer who is a "
        "digital native. The ideal candidate is a recent college graduate "
        "with a aggressive, competitive mindset. Must be a cultural fit "
        "for our fast-paced, high-energy team."
    )


@pytest.fixture
def mock_bias_result():
    """Return a mock BiasResult for testing."""
    return BiasResult(
        has_bias=True,
        biased_terms=["rockstar", "young", "aggressive", "cultural fit"],
        bias_score=0.75,
        category="age/gender",
        suggestions=[
            "Use 'skilled professional' instead of 'rockstar'",
            "Remove age-related terms like 'young'",
            "Use 'collaborative' instead of 'aggressive'",
            "Replace 'cultural fit' with 'values alignment'",
        ],
    )


# ---------------------------------------------------------------------------
# Tests: detect_bias
# ---------------------------------------------------------------------------

class TestDetectBias:
    """Tests for BiasDetector.detect_bias."""

    def test_detect_bias_returns_result(self, detector, sample_job_description):
        """detect_bias should return a BiasResult instance."""
        result = detector.detect_bias(sample_job_description)
        assert isinstance(result, BiasResult)

    def test_detect_bias_neutral_text(self, detector, sample_job_description):
        """Neutral job description should have low or zero bias score."""
        result = detector.detect_bias(sample_job_description)
        assert result.has_bias is False
        assert result.bias_score < 0.3
        assert len(result.biased_terms) == 0

    def test_detect_bias_biased_text(self, detector, biased_job_description):
        """Biased job description should be flagged with high score."""
        result = detector.detect_bias(biased_job_description)
        assert result.has_bias is True
        assert result.bias_score > 0.5
        assert len(result.biased_terms) > 0

    def test_detect_bias_empty_string(self, detector):
        """Empty input should return a result with no bias."""
        result = detector.detect_bias("")
        assert isinstance(result, BiasResult)
        assert result.has_bias is False
        assert result.bias_score == 0.0

    def test_detect_bias_none_input(self, detector):
        """None input should raise TypeError."""
        with pytest.raises(TypeError):
            detector.detect_bias(None)

    def test_detect_bias_case_insensitive(self, detector):
        """Bias detection should be case-insensitive."""
        lower = detector.detect_bias("we need a young rockstar")
        upper = detector.detect_bias("WE NEED A YOUNG ROCKSTAR")
        assert lower.has_bias == upper.has_bias
        assert lower.bias_score == upper.bias_score

    def test_detect_bias_multiple_categories(self, detector):
        """Detection should identify multiple bias categories."""
        text = "We need a young, aggressive male nurse who is a cultural fit."
        result = detector.detect_bias(text)
        assert result.has_bias is True
        assert result.category is not None

    def test_detect_bias_preserves_original_text(self, detector, biased_job_description):
        """Detection should not mutate the input string."""
        original = biased_job_description
        detector.detect_bias(biased_job_description)
        assert biased_job_description == original


# ---------------------------------------------------------------------------
# Tests: suggest_alternatives
# ---------------------------------------------------------------------------

class TestSuggestAlternatives:
    """Tests for BiasDetector.suggest_alternatives."""

    def test_suggest_alternatives_returns_list(self, detector, biased_job_description):
        """suggest_alternatives should return a list of suggestions."""
        result = detector.suggest_alternatives(biased_job_description)
        assert isinstance(result, list)
        assert len(result) > 0

    def test_suggest_alternatives_neutral_text(self, detector, sample_job_description):
        """Neutral text should yield no suggestions."""
        result = detector.suggest_alternatives(sample_job_description)
        assert isinstance(result, list)
        assert len(result) == 0

    def test_suggest_alternatives_content(self, detector, biased_job_description):
        """Suggestions should reference the biased terms found."""
        result = detector.suggest_alternatives(biased_job_description)
        assert any("rockstar" in s.lower() for s in result)
        assert any("young" in s.lower() for s in result)

    def test_suggest_alternatives_empty_string(self, detector):
        """Empty input should return empty list."""
        result = detector.suggest_alternatives("")
        assert result == []

    def test_suggest_alternatives_none_input(self, detector):
        """None input should raise TypeError."""
        with pytest.raises(TypeError):
            detector.suggest_alternatives(None)

    def test_suggest_alternatives_returns_strings(self, detector, biased_job_description):
        """All suggestions should be non-empty strings."""
        result = detector.suggest_alternatives(biased_job_description)
        for suggestion in result:
            assert isinstance(suggestion, str)
            assert len(suggestion.strip()) > 0

    def test_suggest_alternatives_ordered_by_severity(self, detector):
        """Suggestions should be ordered by severity (most biased first)."""
        text = "We need a young rockstar who is aggressive and a cultural fit."
        result = detector.suggest_alternatives(text)
        assert len(result) >= 2
        # First suggestion should address the most severe bias
        assert isinstance(result[0], str)


# ---------------------------------------------------------------------------
# Tests: bias_score
# ---------------------------------------------------------------------------

class TestBiasScore:
    """Tests for BiasDetector.bias_score."""

    def test_bias_score_returns_float(self, detector, sample_job_description):
        """bias_score should return a float."""
        score = detector.bias_score(sample_job_description)
        assert isinstance(score, float)

    def test_bias_score_neutral_text(self, detector, sample_job_description):
        """Neutral text should have a score near zero."""
        score = detector.bias_score(sample_job_description)
        assert 0.0 <= score < 0.3

    def test_bias_score_biased_text(self, detector, biased_job_description):
        """Biased text should have a high score."""
        score = detector.bias_score(biased_job_description)
        assert score > 0.5

    def test_bias_score_range(self, detector, biased_job_description):
        """Score should always be between 0.0 and 1.0."""
        score = detector.bias_score(biased_job_description)
        assert 0.0 <= score <= 1.0

    def test_bias_score_empty_string(self, detector):
        """Empty input should return 0.0."""
        score = detector.bias_score("")
        assert score == 0.0

    def test_bias_score_none_input(self, detector):
        """None input should raise TypeError."""
        with pytest.raises(TypeError):
            detector.bias_score(None)

    def test_bias_score_monotonic(self, detector):
        """More biased text should yield a higher score."""
        neutral = detector.bias_score("software engineer with Python experience")
        slightly_biased = detector.bias_score("software engineer with Python experience, must be a rockstar")
        very_biased = detector.bias_score("young aggressive rockstar ninja who is a cultural fit")
        assert neutral < slightly_biased < very_biased

    def test_bias_score_consistent_with_detect(self, detector, biased_job_description):
        """bias_score should be consistent with detect_bias result."""
        score = detector.bias_score(biased_job_description)
        result = detector.detect_bias(biased_job_description)
        assert score == result.bias_score

    def test_bias_score_single_biased_term(self, detector):
        """A single biased term should produce a moderate score."""
        score = detector.bias_score("We need a rockstar developer.")
        assert 0.1 < score < 0.8

    def test_bias_score_repeated_biased_terms(self, detector):
        """Repeated biased terms should increase the score."""
        single = detector.bias_score("We need a rockstar developer.")
        repeated = detector.bias_score("We need a rockstar ninja rockstar developer.")
        assert repeated > single
