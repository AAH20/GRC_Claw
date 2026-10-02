"""Pydantic models for request/response schemas."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    """Request model for semantic search queries."""

    query: str = Field(..., min_length=1, max_length=500, description="Search query text")
    user_id: str | None = Field(None, description="Optional user ID for personalization")
    filters: dict[str, Any] = Field(default_factory=dict, description="Search filters")
    limit: int = Field(default=10, ge=1, le=50, description="Maximum results to return")
    offset: int = Field(default=0, ge=0, description="Pagination offset")
    include_explanation: bool = Field(default=False, description="Include AI explanation")
    min_score: float = Field(default=0.3, ge=0.0, le=1.0, description="Minimum relevance score")


class SearchResult(BaseModel):
    """Individual search result item."""

    id: str = Field(..., description="Unique content identifier")
    title: str = Field(..., description="Content title")
    content: str = Field(..., description="Content body or summary")
    url: str | None = Field(None, description="Content URL")
    score: float = Field(..., ge=0.0, le=1.0, description="Relevance score")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    content_type: str = Field(default="article", description="Type of content")
    published_at: datetime | None = Field(None, description="Publication timestamp")
    author: str | None = Field(None, description="Content author")
    tags: list[str] = Field(default_factory=list, description="Content tags")


class SearchResponse(BaseModel):
    """Response model for search queries."""

    results: list[SearchResult] = Field(..., description="Search results")
    total: int = Field(..., description="Total matching results")
    query: str = Field(..., description="Original search query")
    took_ms: float = Field(..., description="Query execution time in milliseconds")
    explanation: str | None = Field(None, description="AI-generated explanation")
    personalized: bool = Field(default=False, description="Whether results were personalized")


class Recommendation(BaseModel):
    """Content recommendation item."""

    id: str = Field(..., description="Unique recommendation identifier")
    content_id: str = Field(..., description="Recommended content ID")
    title: str = Field(..., description="Content title")
    reason: str = Field(..., description="Reason for recommendation")
    score: float = Field(..., ge=0.0, le=1.0, description="Recommendation confidence")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class RecommendationRequest(BaseModel):
    """Request model for content recommendations."""

    user_id: str = Field(..., description="User identifier")
    context: str | None = Field(None, description="Current context or query")
    limit: int = Field(default=10, ge=1, le=50, description="Maximum recommendations")
    content_types: list[str] = Field(default_factory=list, description="Filter by content types")


class RecommendationResponse(BaseModel):
    """Response model for recommendations."""

    recommendations: list[Recommendation] = Field(..., description="Recommended items")
    user_id: str = Field(..., description="User identifier")
    took_ms: float = Field(..., description="Execution time in milliseconds")


class TrendDirection(str, Enum):
    """Direction of a trend."""

    RISING = "rising"
    FALLING = "falling"
    STABLE = "stable"
    VOLATILE = "volatile"


class Trend(BaseModel):
    """Trend detection result."""

    id: str = Field(..., description="Unique trend identifier")
    topic: str = Field(..., description="Trend topic or keyword")
    direction: TrendDirection = Field(..., description="Trend direction")
    score: float = Field(..., ge=0.0, le=1.0, description="Trend strength score")
    volume: int = Field(..., description="Search/query volume")
    change_percent: float = Field(..., description="Percentage change from previous period")
    related_topics: list[str] = Field(default_factory=list, description="Related topics")
    started_at: datetime | None = Field(None, description="When the trend started")
    peak_at: datetime | None = Field(None, description="When the trend peaked")


class TrendRequest(BaseModel):
    """Request model for trend detection."""

    topics: list[str] = Field(default_factory=list, description="Topics to analyze")
    window_days: int = Field(default=7, ge=1, le=30, description="Analysis window in days")
    limit: int = Field(default=10, ge=1, le=50, description="Maximum trends to return")


class TrendResponse(BaseModel):
    """Response model for trend detection."""

    trends: list[Trend] = Field(..., description="Detected trends")
    window_days: int = Field(..., description="Analysis window in days")
    took_ms: float = Field(..., description="Execution time in milliseconds")


class SearchExplanation(BaseModel):
    """AI-generated explanation of search results."""

    query: str = Field(..., description="Original search query")
    explanation: str = Field(..., description="Human-readable explanation")
    factors: list[str] = Field(default_factory=list, description="Key ranking factors")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Explanation confidence")
    suggested_refinements: list[str] = Field(default_factory=list, description="Suggested query refinements")


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Service status")
    version: str = Field(..., description="Service version")
    timestamp: datetime = Field(..., description="Current timestamp")
    checks: dict[str, bool] = Field(default_factory=dict, description="Component health checks")


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: dict[str, Any] = Field(default_factory=dict, description="Additional error details")
    request_id: str | None = Field(None, description="Request correlation ID")


T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper."""

    items: list[T] = Field(..., description="Result items")
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")
    has_more: bool = Field(..., description="Whether more pages exist")
