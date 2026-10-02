"""Engagement analysis Pydantic models."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class EngagementType(StrEnum):
    """Types of engagement."""

    LIKE = "like"
    COMMENT = "comment"
    SHARE = "share"
    SAVE = "save"
    CLICK = "click"
    VIEW = "view"
    FOLLOW = "follow"
    MENTION = "mention"
    REPOST = "repost"


class EngagementMetrics(BaseModel):
    """Engagement metrics breakdown."""

    total_interactions: int = Field(default=0, ge=0, description="Total interactions")
    interactions_by_type: dict[EngagementType, int] = Field(
        default_factory=dict, description="Interactions by type"
    )
    engagement_rate: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Overall engagement rate"
    )
    response_rate: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Creator response rate"
    )
    average_response_time_minutes: float = Field(
        default=0.0, ge=0.0, description="Average response time in minutes"
    )
    sentiment_distribution: dict[str, float] = Field(
        default_factory=dict, description="Sentiment distribution"
    )
    peak_engagement_times: list[dict[str, str]] = Field(
        default_factory=list, description="Peak engagement time windows"
    )


class EngagementReport(BaseModel):
    """Comprehensive engagement analysis report."""

    creator_id: str = Field(..., description="Creator identifier")
    report_period_start: datetime = Field(..., description="Report period start")
    report_period_end: datetime = Field(..., description="Report period end")
    metrics: EngagementMetrics = Field(..., description="Engagement metrics")
    top_engaging_content: list[dict[str, str]] = Field(
        default_factory=list, description="Top engaging content"
    )
    audience_loyalty_score: float = Field(
        ..., ge=0.0, le=100.0, description="Audience loyalty score"
    )
    community_health_score: float = Field(
        ..., ge=0.0, le=100.0, description="Community health score"
    )
    trending_topics: list[str] = Field(
        default_factory=list, description="Trending topics in comments"
    )
    influencer_collaborations: list[dict[str, str]] = Field(
        default_factory=list, description="Influencer collaboration data"
    )
    insights: list[str] = Field(
        default_factory=list, description="AI-generated engagement insights"
    )
    recommendations: list[str] = Field(
        default_factory=list, description="AI-generated recommendations"
    )
    generated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Report generation timestamp"
    )
