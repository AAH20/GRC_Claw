"""Pydantic models for the community curation service."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field


class ContentSource(StrEnum):
    """Supported content sources."""

    REDDIT = "reddit"
    HACKER_NEWS = "hacker_news"
    TWITTER = "twitter"
    RSS = "rss"
    MANUAL = "manual"


class ContentItem(BaseModel):
    """A single piece of community content."""

    id: str = Field(..., description="Unique content identifier")
    title: str = Field(..., description="Content title")
    body: str = Field(default="", description="Content body text")
    author: str = Field(default="", description="Content author")
    source: ContentSource = Field(..., description="Content source platform")
    url: str | None = Field(default=None, description="Content URL")
    score: float = Field(default=0.0, description="Platform score (e.g., upvotes)")
    comment_count: int = Field(default=0, description="Number of comments")
    created_at: datetime = Field(..., description="Content creation timestamp")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class CurationRequest(BaseModel):
    """Request model for content curation."""

    query: str = Field(..., min_length=1, description="Search query or topic")
    sources: list[ContentSource] = Field(
        default_factory=lambda: [ContentSource.REDDIT, ContentSource.HACKER_NEWS],
        description="Content sources to search",
    )
    limit: int = Field(default=20, ge=1, le=100, description="Maximum results to return")
    time_range: Literal["hour", "day", "week", "month"] = Field(
        default="week", description="Time range filter"
    )
    min_quality_score: float = Field(
        default=0.5, ge=0.0, le=1.0, description="Minimum quality score threshold"
    )
    include_trends: bool = Field(default=True, description="Whether to include trend analysis")
    include_clusters: bool = Field(default=True, description="Whether to include topic clustering")
    language: str = Field(default="en", description="Content language filter")


class RankedContent(BaseModel):
    """A piece of content with ranking information."""

    content: ContentItem = Field(..., description="The content item")
    rank: int = Field(..., ge=1, description="Rank position (1-based)")
    ranking_score: float = Field(..., ge=0.0, le=1.0, description="Overall ranking score")
    score_breakdown: dict[str, float] = Field(
        default_factory=dict, description="Score component breakdown"
    )
    ranking_reason: str = Field(default="", description="Explanation of ranking")


class Trend(BaseModel):
    """A detected trend in community content."""

    id: str = Field(..., description="Unique trend identifier")
    name: str = Field(..., description="Trend name/label")
    description: str = Field(default="", description="Trend description")
    keywords: list[str] = Field(default_factory=list, description="Associated keywords")
    content_count: int = Field(default=0, description="Number of related content items")
    velocity: float = Field(default=0.0, description="Trend velocity (items per hour)")
    sentiment: float = Field(default=0.0, ge=-1.0, le=1.0, description="Sentiment score")
    started_at: datetime | None = Field(default=None, description="When the trend started")
    peak_at: datetime | None = Field(default=None, description="When the trend peaked")
    related_trends: list[str] = Field(default_factory=list, description="Related trend IDs")


class TopicCluster(BaseModel):
    """A cluster of related content topics."""

    id: str = Field(..., description="Unique cluster identifier")
    name: str = Field(..., description="Cluster name")
    description: str = Field(default="", description="Cluster description")
    keywords: list[str] = Field(default_factory=list, description="Cluster keywords")
    content_ids: list[str] = Field(
        default_factory=list, description="IDs of content in this cluster"
    )
    coherence_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Cluster coherence")
    size: int = Field(default=0, description="Number of items in cluster")


class QualityAssessment(BaseModel):
    """Quality assessment for a piece of content."""

    content_id: str = Field(..., description="Content identifier")
    quality_score: float = Field(..., ge=0.0, le=1.0, description="Overall quality score")
    is_spam: bool = Field(default=False, description="Whether content is spam")
    is_low_quality: bool = Field(default=False, description="Whether content is low quality")
    flags: list[str] = Field(default_factory=list, description="Quality flags")
    reasons: list[str] = Field(default_factory=list, description="Quality assessment reasons")


class CurationResult(BaseModel):
    """Result of a content curation request."""

    request_id: str = Field(..., description="Unique request identifier")
    query: str = Field(..., description="Original search query")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Result timestamp")
    ranked_content: list[RankedContent] = Field(
        default_factory=list, description="Ranked content items"
    )
    trends: list[Trend] = Field(default_factory=list, description="Detected trends")
    clusters: list[TopicCluster] = Field(default_factory=list, description="Topic clusters")
    quality_filtered: list[QualityAssessment] = Field(
        default_factory=list, description="Quality assessment results"
    )
    explanation: str = Field(default="", description="Curation explanation")
    total_candidates: int = Field(default=0, description="Total candidates before filtering")
    processing_time_ms: float = Field(default=0.0, description="Processing time in milliseconds")


class AgentInfo(BaseModel):
    """Information about an agent."""

    name: str = Field(..., description="Agent name")
    description: str = Field(default="", description="Agent description")
    status: Literal["available", "unavailable", "error"] = Field(
        default="available", description="Agent status"
    )
    capabilities: list[str] = Field(default_factory=list, description="Agent capabilities")


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(default="ok", description="Service status")
    version: str = Field(default="0.1.0", description="Service version")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    agents: list[AgentInfo] = Field(default_factory=list, description="Agent health info")


class ErrorResponse(BaseModel):
    """Error response model."""

    error: str = Field(..., description="Error type")
    detail: str = Field(default="", description="Error details")
    request_id: str | None = Field(default=None, description="Request identifier")
