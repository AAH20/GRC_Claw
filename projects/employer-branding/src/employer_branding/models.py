"""Pydantic models for employer branding data structures."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class ContentType(StrEnum):
    """Types of brand content."""

    JOB_POSTING = "job_posting"
    SOCIAL_MEDIA = "social_media"
    BLOG_POST = "blog_post"
    EMPLOYER_VIDEO_SCRIPT = "employer_video_script"
    CAREERS_PAGE = "careers_page"
    EMAIL_CAMPAIGN = "email_campaign"
    PRESS_RELEASE = "press_release"


class ContentTone(StrEnum):
    """Tone options for content generation."""

    PROFESSIONAL = "professional"
    FRIENDLY = "friendly"
    INSPIRATIONAL = "inspirational"
    CASUAL = "casual"
    FORMAL = "formal"
    ENTHUSIASTIC = "enthusiastic"


class SentimentLabel(StrEnum):
    """Sentiment classification labels."""

    VERY_POSITIVE = "very_positive"
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    VERY_NEGATIVE = "very_negative"


class ReviewSource(StrEnum):
    """Sources for employer reviews."""

    GLASSDOOR = "glassdoor"
    INDEED = "indeed"
    LINKEDIN = "linkedin"
    GOOGLE = "google"
    TRUSTPILOT = "trustpilot"


class ReputationLevel(StrEnum):
    """Reputation quality levels."""

    EXCELLENT = "excellent"
    GOOD = "good"
    AVERAGE = "average"
    POOR = "poor"
    CRITICAL = "critical"


class BrandAsset(BaseModel):
    """Represents a brand asset/content piece."""

    id: UUID = Field(default_factory=uuid4, description="Unique asset identifier")
    title: str = Field(..., min_length=1, max_length=200, description="Asset title")
    content: str = Field(..., min_length=1, description="Asset content body")
    content_type: ContentType = Field(..., description="Type of content")
    tone: ContentTone = Field(default=ContentTone.PROFESSIONAL, description="Content tone")
    language: str = Field(default="en", description="Content language code")
    tags: list[str] = Field(default_factory=list, description="Content tags")
    target_audience: str | None = Field(default=None, description="Target audience description")
    call_to_action: str | None = Field(default=None, description="Call to action text")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Last update timestamp")
    is_published: bool = Field(default=False, description="Whether the asset is published")
    published_at: datetime | None = Field(default=None, description="Publication timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Join Our Engineering Team",
                "content": "We're looking for passionate engineers...",
                "content_type": "job_posting",
                "tone": "enthusiastic",
            }
        }


class SentimentReport(BaseModel):
    """Represents a sentiment analysis report."""

    id: UUID = Field(default_factory=uuid4, description="Unique report identifier")
    source_text: str = Field(..., description="Original text analyzed")
    overall_sentiment: SentimentLabel = Field(..., description="Overall sentiment classification")
    sentiment_score: float = Field(..., ge=-1.0, le=1.0, description="Sentiment score from -1 to 1")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence level of analysis")
    aspects: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Aspect-based sentiment breakdown")
    keywords: list[str] = Field(default_factory=list, description="Key sentiment-bearing keywords")
    emotions: dict[str, float] = Field(default_factory=dict, description="Emotion detection scores")
    language: str = Field(default="en", description="Detected language")
    analyzed_at: datetime = Field(default_factory=datetime.utcnow, description="Analysis timestamp")
    model_version: str = Field(default="1.0", description="Model version used")


class ReputationScore(BaseModel):
    """Represents an employer reputation score."""

    id: UUID = Field(default_factory=uuid4, description="Unique score identifier")
    company_name: str = Field(..., description="Company name")
    overall_score: float = Field(..., ge=0.0, le=100.0, description="Overall reputation score")
    reputation_level: ReputationLevel = Field(..., description="Reputation quality level")
    rating: float = Field(..., ge=0.0, le=5.0, description="Star rating equivalent")
    review_count: int = Field(default=0, description="Total reviews analyzed")
    positive_percentage: float = Field(
        default=0.0, ge=0.0, le=100.0,
        description="Positive review percentage")
    negative_percentage: float = Field(
        default=0.0, ge=0.0, le=100.0,
        description="Negative review percentage")
    neutral_percentage: float = Field(
        default=0.0, ge=0.0, le=100.0,
        description="Neutral review percentage")
    category_scores: dict[str, float] = Field(
        default_factory=dict,
        description="Scores by category")
    trend: str = Field(
        default="stable",
        description="Reputation trend (improving/stable/declining)")
    period_start: datetime | None = Field(default=None, description="Analysis period start")
    period_end: datetime | None = Field(default=None, description="Analysis period end")
    recommendations: list[str] = Field(
        default_factory=list,
        description="Improvement recommendations")
    calculated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Calculation timestamp")


class Review(BaseModel):
    """Represents an employer review."""

    id: UUID = Field(default_factory=uuid4, description="Unique review identifier")
    source: ReviewSource = Field(..., description="Review source platform")
    author: str | None = Field(default=None, description="Review author (anonymized)")
    rating: float = Field(..., ge=0.0, le=5.0, description="Star rating")
    title: str | None = Field(default=None, description="Review title")
    content: str = Field(..., description="Review content")
    pros: str | None = Field(default=None, description="Pros mentioned")
    cons: str | None = Field(default=None, description="Cons mentioned")
    sentiment: SentimentLabel | None = Field(default=None, description="Detected sentiment")
    sentiment_score: float | None = Field(
        default=None, ge=-1.0, le=1.0,
        description="Sentiment score")
    is_recommended: bool | None = Field(
        default=None,
        description="Whether reviewer recommends company")
    review_date: datetime | None = Field(default=None, description="Original review date")
    fetched_at: datetime = Field(default_factory=datetime.utcnow, description="Fetch timestamp")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class BrandStrategy(BaseModel):
    """Represents an employer brand strategy."""

    id: UUID = Field(default_factory=uuid4, description="Unique strategy identifier")
    company_name: str = Field(..., description="Company name")
    mission: str = Field(..., description="Company mission statement")
    vision: str = Field(..., description="Company vision statement")
    values: list[str] = Field(..., min_length=1, description="Company values")
    employee_value_proposition: str = Field(..., description="Employee value proposition (EVP)")
    target_audience: list[str] = Field(..., description="Target candidate personas")
    key_messages: list[str] = Field(..., description="Key brand messages")
    content_pillars: list[str] = Field(..., description="Content strategy pillars")
    channels: list[str] = Field(..., description="Recommended marketing channels")
    tone_guidelines: dict[str, str] = Field(
        default_factory=dict,
        description="Tone guidelines by context")
    competitive_positioning: str | None = Field(
        default=None,
        description="Competitive positioning statement")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Last update timestamp")
    is_active: bool = Field(default=True, description="Whether strategy is active")


class ContentGenerationRequest(BaseModel):
    """Request model for content generation."""

    content_type: ContentType = Field(..., description="Type of content to generate")
    topic: str = Field(..., min_length=1, description="Content topic or subject")
    tone: ContentTone = Field(default=ContentTone.PROFESSIONAL, description="Desired tone")
    language: str = Field(default="en", description="Content language")
    max_length: int = Field(default=2000, ge=100, le=10000, description="Maximum content length")
    keywords: list[str] = Field(default_factory=list, description="Keywords to include")
    target_audience: str | None = Field(default=None, description="Target audience")
    additional_context: str | None = Field(
        default=None,
        description="Additional context for generation")


class SentimentAnalysisRequest(BaseModel):
    """Request model for sentiment analysis."""

    text: str = Field(..., min_length=1, description="Text to analyze")
    analyze_aspects: bool = Field(
        default=True,
        description="Whether to perform aspect-based analysis")
    detect_emotions: bool = Field(default=True, description="Whether to detect emotions")
    language: str | None = Field(default=None, description="Text language (auto-detect if None)")


class ReputationAnalysisRequest(BaseModel):
    """Request model for reputation analysis."""

    company_name: str = Field(..., description="Company name to analyze")
    sources: list[ReviewSource] = Field(
        default_factory=lambda: [ReviewSource.GLASSDOOR],
        description="Review sources")
    period_days: int = Field(default=90, ge=1, le=365, description="Analysis period in days")
    include_recommendations: bool = Field(
        default=True,
        description="Include improvement recommendations")


class ReviewFetchRequest(BaseModel):
    """Request model for fetching reviews."""

    company_name: str = Field(..., description="Company name")
    source: ReviewSource = Field(..., description="Review source")
    limit: int = Field(default=50, ge=1, le=500, description="Maximum reviews to fetch")
    since_date: datetime | None = Field(default=None, description="Fetch reviews since this date")


class BrandStrategyRequest(BaseModel):
    """Request model for brand strategy creation."""

    company_name: str = Field(..., description="Company name")
    industry: str = Field(..., description="Industry sector")
    company_size: str = Field(..., description="Company size category")
    mission: str = Field(..., description="Company mission")
    vision: str = Field(..., description="Company vision")
    values: list[str] = Field(..., min_length=1, description="Company values")
    target_audience: list[str] = Field(..., description="Target candidate personas")
    additional_context: str | None = Field(default=None, description="Additional context")


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str = Field(..., description="Service status")
    version: str = Field(..., description="Application version")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    environment: str = Field(..., description="Current environment")
