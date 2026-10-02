"""Tests for Pydantic models."""

import pytest
from pydantic import ValidationError

from job_description_optimizer.models import (
    ATSReport,
    BiasInstance,
    BiasReport,
    BiasType,
    JobDescription,
    KeywordReport,
    OptimizationRequest,
    OptimizedDescription,
    SEOReport,
    ToneReport,
    ToneType,
)


class TestJobDescription:
    """Tests for JobDescription model."""

    def test_valid_job_description(self) -> None:
        """Test creating a valid job description."""
        jd = JobDescription(
            title="Software Engineer",
            description="We are looking for a software engineer to join our team.",
        )
        assert jd.title == "Software Engineer"
        assert jd.company is None
        assert jd.skills == []

    def test_empty_title_raises_error(self) -> None:
        """Test that empty title raises validation error."""
        with pytest.raises(ValidationError):
            JobDescription(title="", description="Valid description")

    def test_whitespace_title_raises_error(self) -> None:
        """Test that whitespace-only title raises validation error."""
        with pytest.raises(ValidationError):
            JobDescription(title="   ", description="Valid description")

    def test_empty_description_raises_error(self) -> None:
        """Test that empty description raises validation error."""
        with pytest.raises(ValidationError):
            JobDescription(title="Valid Title", description="")

    def test_title_too_long_raises_error(self) -> None:
        """Test that overly long title raises validation error."""
        with pytest.raises(ValidationError):
            JobDescription(title="x" * 201, description="Valid description")

    def test_description_too_long_raises_error(self) -> None:
        """Test that overly long description raises validation error."""
        with pytest.raises(ValidationError):
            JobDescription(title="Valid Title", description="x" * 50001)


class TestBiasReport:
    """Tests for BiasReport model."""

    def test_valid_bias_report(self) -> None:
        """Test creating a valid bias report."""
        report = BiasReport(
            original_text="Original text",
            cleaned_text="Cleaned text",
            instances=[],
            overall_score=0.5,
        )
        assert report.overall_score == 0.5

    def test_bias_instance_creation(self) -> None:
        """Test creating a bias instance."""
        instance = BiasInstance(
            bias_type=BiasType.GENDERED_LANGUAGE,
            original_text="mankind",
            suggestion="humankind",
            explanation="Gendered term",
            severity=0.8,
        )
        assert instance.bias_type == BiasType.GENDERED_LANGUAGE
        assert instance.severity == 0.8


class TestSEOReport:
    """Tests for SEOReport model."""

    def test_valid_seo_report(self) -> None:
        """Test creating a valid SEO report."""
        report = SEOReport(
            original_text="Original",
            optimized_text="Optimized",
            seo_score=0.8,
            readability_score=0.9,
        )
        assert report.seo_score == 0.8


class TestATSReport:
    """Tests for ATSReport model."""

    def test_valid_ats_report(self) -> None:
        """Test creating a valid ATS report."""
        report = ATSReport(
            original_text="Original",
            compatible_text="Compatible",
            ats_score=0.7,
        )
        assert report.ats_score == 0.7


class TestToneReport:
    """Tests for ToneReport model."""

    def test_valid_tone_report(self) -> None:
        """Test creating a valid tone report."""
        report = ToneReport(
            original_text="Original",
            detected_tones=[ToneType.PROFESSIONAL],
            primary_tone=ToneType.PROFESSIONAL,
            inclusivity_score=0.8,
        )
        assert report.primary_tone == ToneType.PROFESSIONAL


class TestKeywordReport:
    """Tests for KeywordReport model."""

    def test_valid_keyword_report(self) -> None:
        """Test creating a valid keyword report."""
        report = KeywordReport(
            original_text="Original",
            optimized_text="Optimized",
            industry_relevance=0.75,
        )
        assert report.industry_relevance == 0.75


class TestOptimizationRequest:
    """Tests for OptimizationRequest model."""

    def test_valid_optimization_request(self) -> None:
        """Test creating a valid optimization request."""
        jd = JobDescription(title="Test", description="Test description")
        request = OptimizationRequest(job_description=jd)
        assert request.options == {}

    def test_optimization_request_with_options(self) -> None:
        """Test creating optimization request with options."""
        jd = JobDescription(title="Test", description="Test description")
        request = OptimizationRequest(
            job_description=jd,
            options={"skip_bias": True},
        )
        assert request.options["skip_bias"] is True


class TestOptimizedDescription:
    """Tests for OptimizedDescription model."""

    def test_valid_optimized_description(self) -> None:
        """Test creating a valid optimized description."""
        jd = JobDescription(title="Test", description="Test description")
        result = OptimizedDescription(
            original=jd,
            optimized_text="Optimized text",
            overall_score=0.85,
            processing_time_ms=1500.0,
        )
        assert result.overall_score == 0.85
        assert result.processing_time_ms == 1500.0
