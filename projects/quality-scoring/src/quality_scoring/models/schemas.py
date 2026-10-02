"""Pydantic models for quality scoring service."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class ScoreDimension(StrEnum):
    """Enumeration of scoring dimensions."""

    READABILITY = "readability"
    ORIGINALITY = "originality"
    ENGAGEMENT = "engagement"
    SEO = "seo"


class ContentType(StrEnum):
    """Supported content types for scoring."""

    ARTICLE = "article"
    BLOG_POST = "blog_post"
    PRODUCT_DESCRIPTION = "product_description"
    LANDING_PAGE = "landing_page"
    SOCIAL_MEDIA = "social_media"
    EMAIL = "email"
    TECHNICAL_DOC = "technical_doc"
    GENERAL = "general"


class ScoreLevel(StrEnum):
    """Qualitative score levels."""

    EXCELLENT = "excellent"
    GOOD = "good"
    AVERAGE = "average"
    BELOW_AVERAGE = "below_average"
    POOR = "poor"


class ContentInput(BaseModel):
    """Input model for content to be scored."""

    content: str = Field(..., min_length=1, description="The content text to analyze")
    content_type: ContentType = Field(default=ContentType.GENERAL, description="Type of content")
    title: str | None = Field(default=None, description="Optional content title")
    url: str | None = Field(default=None, description="Optional source URL")
    language: str = Field(default="en", description="ISO 639-1 language code")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    @field_validator("content")
    @classmethod
    def validate_content_not_empty(cls, v: str) -> str:
        """Ensure content is not just whitespace."""
        if not v.strip():
            raise ValueError("Content cannot be empty or whitespace only")
        return v


class DimensionScore(BaseModel):
    """Score for a single dimension."""

    dimension: ScoreDimension = Field(..., description="Scoring dimension")
    score: float = Field(..., ge=0.0, le=100.0, description="Score from 0 to 100")
    level: ScoreLevel = Field(..., description="Qualitative score level")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in the score")
    reasoning: str = Field(..., description="Explanation of the score")
    metrics: dict[str, Any] = Field(default_factory=dict, description="Raw metrics used")


class QualityScore(BaseModel):
    """Complete quality score with all dimensions."""

    id: str = Field(..., description="Unique score identifier")
    content_type: ContentType = Field(..., description="Type of content scored")
    overall_score: float = Field(..., ge=0.0, le=100.0, description="Weighted overall score")
    overall_level: ScoreLevel = Field(..., description="Overall qualitative level")
    dimensions: list[DimensionScore] = Field(..., description="Individual dimension scores")
    word_count: int = Field(..., ge=0, description="Word count of content")
    reading_time_minutes: float = Field(..., ge=0.0, description="Estimated reading time")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Score timestamp")
    processing_time_ms: float = Field(..., ge=0.0, description="Processing time in milliseconds")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ImprovementSuggestion(BaseModel):
    """A single improvement suggestion."""

    id: str = Field(..., description="Unique suggestion identifier")
    dimension: ScoreDimension = Field(..., description="Related dimension")
    priority: Literal["high", "medium", "low"] = Field(..., description="Suggestion priority")
    title: str = Field(..., description="Short suggestion title")
    description: str = Field(..., description="Detailed suggestion description")
    current_state: str = Field(..., description="Current state of the content")
    target_state: str = Field(..., description="Desired state after improvement")
    expected_impact: float = Field(..., ge=0.0, le=100.0, description="Expected score improvement")
    examples: list[str] = Field(default_factory=list, description="Example improvements")


class ImprovementPlan(BaseModel):
    """Complete improvement plan with multiple suggestions."""

    id: str = Field(..., description="Unique plan identifier")
    score_id: str = Field(..., description="Reference to original quality score")
    suggestions: list[ImprovementSuggestion] = Field(..., description="List of suggestions")
    total_expected_improvement: float = Field(..., ge=0.0, description="Total expected improvement")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Plan creation time")


class BenchmarkData(BaseModel):
    """Benchmark data for a specific content type and dimension."""

    content_type: ContentType = Field(..., description="Content type")
    dimension: ScoreDimension = Field(..., description="Scoring dimension")
    mean: float = Field(..., ge=0.0, le=100.0, description="Mean benchmark score")
    median: float = Field(..., ge=0.0, le=100.0, description="Median benchmark score")
    p25: float = Field(..., ge=0.0, le=100.0, description="25th percentile")
    p75: float = Field(..., ge=0.0, le=100.0, description="75th percentile")
    p90: float = Field(..., ge=0.0, le=100.0, description="90th percentile")
    sample_size: int = Field(..., ge=0, description="Number of samples in benchmark")


class BenchmarkComparison(BaseModel):
    """Comparison of content score against benchmarks."""

    id: str = Field(..., description="Unique comparison identifier")
    score_id: str = Field(..., description="Reference to quality score")
    content_type: ContentType = Field(..., description="Content type")
    comparisons: list[BenchmarkData] = Field(..., description="Benchmark comparisons per dimension")
    percentile_overall: float = Field(
        ..., ge=0.0, le=100.0, description="Overall percentile ranking"
    )
    summary: str = Field(..., description="Human-readable comparison summary")
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Comparison timestamp"
    )


class BatchScoreRequest(BaseModel):
    """Request model for batch scoring."""

    items: list[ContentInput] = Field(
        ..., min_length=1, max_length=50, description="Content items to score"
    )
    dimensions: list[ScoreDimension] | None = Field(
        default=None, description="Specific dimensions to score (all if None)"
    )


class BatchScoreResponse(BaseModel):
    """Response model for batch scoring."""

    id: str = Field(..., description="Batch identifier")
    results: list[QualityScore] = Field(..., description="Individual scores")
    total_items: int = Field(..., ge=0, description="Total items processed")
    successful: int = Field(..., ge=0, description="Successfully scored items")
    failed: int = Field(..., ge=0, description="Failed items")
    processing_time_ms: float = Field(..., ge=0.0, description="Total processing time")


class ScoreRequest(BaseModel):
    """Request model for single content scoring."""

    content: ContentInput = Field(..., description="Content to score")
    dimensions: list[ScoreDimension] | None = Field(
        default=None, description="Specific dimensions to score (all if None)"
    )
    include_benchmark: bool = Field(default=False, description="Include benchmark comparison")
    include_improvements: bool = Field(default=False, description="Include improvement suggestions")


class ScoreResponse(BaseModel):
    """Response model for content scoring."""

    score: QualityScore = Field(..., description="Quality score result")
    benchmark: BenchmarkComparison | None = Field(default=None, description="Benchmark comparison")
    improvements: ImprovementPlan | None = Field(
        default=None, description="Improvement suggestions"
    )


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Service status")
    version: str = Field(..., description="Service version")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    uptime_seconds: float = Field(..., ge=0.0, description="Service uptime in seconds")


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: dict[str, Any] | None = Field(default=None, description="Additional error details")
    request_id: str | None = Field(default=None, description="Request identifier for debugging")
