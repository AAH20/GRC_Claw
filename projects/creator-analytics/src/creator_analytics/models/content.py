"""Content performance Pydantic models."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class ContentType(str, Enum):
    """Types of content."""

    VIDEO = "video"
    SHORT = "short"
    POST = "post"
    STORY = "story"
    LIVE = "live"
    REEL = "reel"
    ARTICLE = "article"
    PODCAST = "podcast"


class ContentMetrics(BaseModel):
    """Metrics for a piece of content."""

    views: int = Field(default=0, ge=0, description="Total views")
    likes: int = Field(default=0, ge=0, description="Total likes")
    comments: int = Field(default=0, ge=0, description="Total comments")
    shares: int = Field(default=0, ge=0, description="Total shares")
    saves: int = Field(default=0, ge=0, description="Total saves")
    click_throughs: int = Field(default=0, ge=0, description="Total click-throughs")
    watch_time_seconds: float = Field(
        default=0.0, ge=0.0, description="Total watch time in seconds"
    )
    average_watch_percentage: float = Field(
        default=0.0, ge=0.0, le=100.0, description="Average watch percentage"
    )
    engagement_rate: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Engagement rate"
    )
    sentiment_score: float = Field(
        default=0.0, ge=-1.0, le=1.0, description="Sentiment score from -1 to 1"
    )


class ContentPerformance(BaseModel):
    """Performance analysis for a piece of content."""

    content_id: str = Field(..., description="Content identifier")
    creator_id: str = Field(..., description="Creator identifier")
    content_type: ContentType = Field(..., description="Type of content")
    title: str = Field(..., description="Content title")
    description: Optional[str] = Field(default=None, description="Content description")
    published_at: datetime = Field(..., description="Publication timestamp")
    metrics: ContentMetrics = Field(..., description="Content metrics")
    tags: list[str] = Field(default_factory=list, description="Content tags")
    topics: list[str] = Field(default_factory=list, description="Detected topics")
    performance_score: float = Field(
        default=0.0, ge=0.0, le=100.0, description="Overall performance score"
    )
    benchmark_comparison: dict[str, float] = Field(
        default_factory=dict, description="Comparison to benchmarks"
    )
    insights: list[str] = Field(
        default_factory=list, description="AI-generated insights"
    )
    recommendations: list[str] = Field(
        default_factory=list, description="AI-generated recommendations"
    )
    analyzed_at: datetime = Field(
        default_factory=datetime.utcnow, description="Analysis timestamp"
    )
