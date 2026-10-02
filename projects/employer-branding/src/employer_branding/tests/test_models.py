"""Tests for Pydantic models."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from employer_branding.models import (
    BrandAsset,
    BrandStrategy,
    ContentTone,
    ContentType,
    ReputationLevel,
    ReputationScore,
    Review,
    ReviewSource,
    SentimentLabel,
    SentimentReport,
)


def test_brand_asset_creation():
    """Test BrandAsset model creation."""
    asset = BrandAsset(
        title="Test Job Posting",
        content="This is a test job posting content.",
        content_type=ContentType.JOB_POSTING,
        tone=ContentTone.PROFESSIONAL,
    )
    assert asset.title == "Test Job Posting"
    assert asset.content_type == ContentType.JOB_POSTING
    assert asset.tone == ContentTone.PROFESSIONAL
    assert asset.language == "en"
    assert asset.is_published is False
    assert asset.id is not None


def test_brand_asset_validation():
    """Test BrandAsset validation."""
    with pytest.raises(ValidationError):
        BrandAsset(title="", content="Test", content_type=ContentType.JOB_POSTING)


def test_sentiment_report_creation():
    """Test SentimentReport model creation."""
    report = SentimentReport(
        source_text="Great company to work for!",
        overall_sentiment=SentimentLabel.POSITIVE,
        sentiment_score=0.8,
        confidence=0.95,
    )
    assert report.overall_sentiment == SentimentLabel.POSITIVE
    assert report.sentiment_score == 0.8
    assert report.confidence == 0.95


def test_sentiment_report_score_validation():
    """Test SentimentReport score validation."""
    with pytest.raises(ValidationError):
        SentimentReport(
            source_text="Test",
            overall_sentiment=SentimentLabel.POSITIVE,
            sentiment_score=2.0,  # Invalid: > 1.0
            confidence=0.5,
        )


def test_reputation_score_creation():
    """Test ReputationScore model creation."""
    score = ReputationScore(
        company_name="TestCorp",
        overall_score=85.0,
        reputation_level=ReputationLevel.GOOD,
        rating=4.2,
    )
    assert score.company_name == "TestCorp"
    assert score.overall_score == 85.0
    assert score.reputation_level == ReputationLevel.GOOD


def test_review_creation():
    """Test Review model creation."""
    review = Review(
        source=ReviewSource.GLASSDOOR,
        rating=4.5,
        content="Great place to work!",
        pros="Good benefits",
        cons="Limited parking",
    )
    assert review.source == ReviewSource.GLASSDOOR
    assert review.rating == 4.5
    assert review.sentiment is None


def test_brand_strategy_creation():
    """Test BrandStrategy model creation."""
    strategy = BrandStrategy(
        company_name="TestCorp",
        mission="To innovate",
        vision="To be the best",
        values=["Innovation", "Integrity"],
        employee_value_proposition="Great place to grow",
        target_audience=["Engineers"],
        key_messages=["We innovate"],
        content_pillars=["Tech", "Culture"],
        channels=["LinkedIn", "Twitter"],
    )
    assert strategy.company_name == "TestCorp"
    assert len(strategy.values) == 2
    assert strategy.is_active is True


def test_brand_strategy_validation():
    """Test BrandStrategy validation."""
    with pytest.raises(ValidationError):
        BrandStrategy(
            company_name="TestCorp",
            mission="Test",
            vision="Test",
            values=[],  # Invalid: min_length=1
            employee_value_proposition="Test",
            target_audience=["Test"],
            key_messages=["Test"],
            content_pillars=["Test"],
            channels=["Test"],
        )
