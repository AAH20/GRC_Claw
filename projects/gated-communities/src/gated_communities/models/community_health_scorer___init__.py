"""Pydantic models for community health scoring."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class HealthCategory(StrEnum):
    """Health score categories."""

    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    CRITICAL = "critical"


class EngagementLevel(StrEnum):
    """Engagement level classifications."""

    HIGHLY_ENGAGED = "highly_engaged"
    ENGAGED = "engaged"
    MODERATELY_ENGAGED = "moderately_engaged"
    LOW_ENGAGEMENT = "low_engagement"
    DISENGAGED = "disengaged"


class ToxicityLevel(StrEnum):
    """Toxicity level classifications."""

    NONE = "none"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    SEVERE = "severe"


class GrowthTrend(StrEnum):
    """Growth trend classifications."""

    RAPID_GROWTH = "rapid_growth"
    STEADY_GROWTH = "steady_growth"
    STABLE = "stable"
    SLOW_DECLINE = "slow_decline"
    RAPID_DECLINE = "rapid_decline"


class ChurnRisk(StrEnum):
    """Churn risk classifications."""

    VERY_LOW = "very_low"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"


class EngagementMetrics(BaseModel):
    """Engagement metrics for a community."""

    dau: int = Field(..., ge=0, description="Daily active users")
    mau: int = Field(..., ge=0, description="Monthly active users")
    avg_session_duration_minutes: float = Field(
        ..., ge=0, description="Average session duration in minutes"
    )
    avg_sessions_per_user: float = Field(..., ge=0, description="Average sessions per user per day")
    interaction_depth: float = Field(..., ge=0, le=1, description="Interaction depth score (0-1)")
    content_creation_rate: float = Field(..., ge=0, description="Content creation rate per user")
    response_rate: float = Field(..., ge=0, le=1, description="Response rate (0-1)")
    retention_rate_7d: float = Field(..., ge=0, le=1, description="7-day retention rate")
    retention_rate_30d: float = Field(..., ge=0, le=1, description="30-day retention rate")
    engagement_level: EngagementLevel = Field(default=EngagementLevel.MODERATELY_ENGAGED)
    score: float = Field(default=0.0, ge=0, le=100, description="Engagement score (0-100)")

    @field_validator("mau")
    @classmethod
    def validate_mau_gte_dau(cls, v: int, info: Any) -> int:
        """Validate MAU >= DAU."""
        if "dau" in info.data and v < info.data["dau"]:
            raise ValueError("MAU must be >= DAU")
        return v

    @property
    def dau_mau_ratio(self) -> float:
        """Calculate DAU/MAU ratio (stickiness)."""
        if self.mau == 0:
            return 0.0
        return round(self.dau / self.mau, 4)


class ToxicityReport(BaseModel):
    """Toxicity analysis report for a community."""

    overall_toxicity_score: float = Field(
        ..., ge=0, le=100, description="Overall toxicity score (0-100, higher = more toxic)"
    )
    toxicity_level: ToxicityLevel = Field(default=ToxicityLevel.NONE)
    toxic_content_count: int = Field(
        default=0, ge=0, description="Number of toxic content items detected"
    )
    total_content_analyzed: int = Field(default=0, ge=0, description="Total content items analyzed")
    toxic_user_count: int = Field(
        default=0, ge=0, description="Number of users flagged for toxic behavior"
    )
    total_users: int = Field(default=0, ge=0, description="Total users in community")
    toxicity_categories: dict[str, float] = Field(
        default_factory=dict,
        description="Toxicity breakdown by category (harassment, hate_speech, spam, etc.)",
    )
    flagged_content: list[dict[str, Any]] = Field(
        default_factory=list,
        description="List of flagged content items with details",
    )
    recommendations: list[str] = Field(
        default_factory=list,
        description="Recommendations for reducing toxicity",
    )
    score: float = Field(
        default=0.0, ge=0, le=100, description="Toxicity health score (0-100, higher = healthier)"
    )

    @property
    def toxicity_rate(self) -> float:
        """Calculate toxicity rate as percentage."""
        if self.total_content_analyzed == 0:
            return 0.0
        return round(self.toxic_content_count / self.total_content_analyzed * 100, 2)


class GrowthAnalysis(BaseModel):
    """Growth analysis for a community."""

    current_members: int = Field(..., ge=0, description="Current number of members")
    new_members_7d: int = Field(default=0, ge=0, description="New members in last 7 days")
    new_members_30d: int = Field(default=0, ge=0, description="New members in last 30 days")
    churned_members_7d: int = Field(default=0, ge=0, description="Churned members in last 7 days")
    churned_members_30d: int = Field(default=0, ge=0, description="Churned members in last 30 days")
    growth_rate_7d: float = Field(default=0.0, description="7-day growth rate")
    growth_rate_30d: float = Field(default=0.0, description="30-day growth rate")
    net_growth_rate: float = Field(default=0.0, description="Net growth rate (acquisition - churn)")
    growth_trend: GrowthTrend = Field(default=GrowthTrend.STABLE)
    projected_members_30d: int = Field(default=0, ge=0, description="Projected members in 30 days")
    projected_members_90d: int = Field(default=0, ge=0, description="Projected members in 90 days")
    acquisition_channels: dict[str, int] = Field(
        default_factory=dict,
        description="Member acquisition by channel",
    )
    score: float = Field(default=0.0, ge=0, le=100, description="Growth health score (0-100)")


class ChurnPrediction(BaseModel):
    """Churn prediction for a community."""

    overall_churn_risk: ChurnRisk = Field(default=ChurnRisk.LOW)
    churn_probability: float = Field(..., ge=0, le=1, description="Overall churn probability (0-1)")
    at_risk_members: int = Field(
        default=0, ge=0, description="Number of members at risk of churning"
    )
    total_members: int = Field(default=0, ge=0, description="Total members in community")
    risk_factors: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Identified risk factors with severity and affected members",
    )
    protective_factors: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Factors protecting against churn",
    )
    predicted_churn_rate_30d: float = Field(
        default=0.0, ge=0, le=1, description="Predicted 30-day churn rate"
    )
    predicted_churn_rate_90d: float = Field(
        default=0.0, ge=0, le=1, description="Predicted 90-day churn rate"
    )
    segment_risk: dict[str, float] = Field(
        default_factory=dict,
        description="Churn risk by member segment",
    )
    recommendations: list[str] = Field(
        default_factory=list,
        description="Recommendations for reducing churn",
    )
    score: float = Field(
        default=0.0, ge=0, le=100, description="Churn health score (0-100, higher = healthier)"
    )

    @property
    def at_risk_percentage(self) -> float:
        """Calculate at-risk member percentage."""
        if self.total_members == 0:
            return 0.0
        return round(self.at_risk_members / self.total_members * 100, 2)


class HealthScore(BaseModel):
    """Overall community health score."""

    community_id: str = Field(..., description="Unique community identifier")
    overall_score: float = Field(..., ge=0, le=100, description="Overall health score (0-100)")
    category: HealthCategory | None = Field(default=None, description="Health category")
    engagement_score: float = Field(..., ge=0, le=100, description="Engagement component score")
    toxicity_score: float = Field(..., ge=0, le=100, description="Toxicity component score")
    growth_score: float = Field(..., ge=0, le=100, description="Growth component score")
    churn_score: float = Field(..., ge=0, le=100, description="Churn component score")
    engagement_weight: float = Field(default=0.30)
    toxicity_weight: float = Field(default=0.25)
    growth_weight: float = Field(default=0.25)
    churn_weight: float = Field(default=0.20)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    period_start: datetime | None = Field(default=None, description="Analysis period start")
    period_end: datetime | None = Field(default=None, description="Analysis period end")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    @model_validator(mode="after")
    def set_category(self) -> "HealthScore":
        """Auto-derive category from overall_score if not provided."""
        if self.category is None:
            score = self.overall_score
            if score >= 80:
                self.category = HealthCategory.EXCELLENT
            elif score >= 60:
                self.category = HealthCategory.GOOD
            elif score >= 40:
                self.category = HealthCategory.FAIR
            elif score >= 20:
                self.category = HealthCategory.POOR
            else:
                self.category = HealthCategory.CRITICAL
        return self


class HealthExplanation(BaseModel):
    """Human-readable explanation of a health score."""

    community_id: str = Field(..., description="Community identifier")
    summary: str = Field(..., description="Executive summary of community health")
    engagement_summary: str = Field(..., description="Explanation of engagement metrics")
    toxicity_summary: str = Field(..., description="Explanation of toxicity findings")
    growth_summary: str = Field(..., description="Explanation of growth analysis")
    churn_summary: str = Field(..., description="Explanation of churn predictions")
    key_strengths: list[str] = Field(default_factory=list, description="Key community strengths")
    key_concerns: list[str] = Field(default_factory=list, description="Key areas of concern")
    actionable_recommendations: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Prioritized actionable recommendations",
    )
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    model_used: str = Field(default="gpt-4o-mini", description="LLM model used for explanation")


class ScoreRequest(BaseModel):
    """Request model for health score calculation."""

    community_id: str = Field(..., min_length=1, description="Community identifier")
    period_days: int = Field(default=30, ge=1, le=365, description="Analysis period in days")
    include_explanation: bool = Field(default=True, description="Whether to include AI explanation")
    metrics_data: dict[str, Any] | None = Field(
        default=None,
        description="Optional pre-fetched metrics data",
    )


class AgentRunRequest(BaseModel):
    """Request model for running a specific agent."""

    community_id: str = Field(..., min_length=1, description="Community identifier")
    parameters: dict[str, Any] = Field(
        default_factory=dict, description="Agent-specific parameters"
    )


class AgentRunResponse(BaseModel):
    """Response model for agent execution."""

    agent_name: str = Field(..., description="Name of the executed agent")
    community_id: str = Field(..., description="Community identifier")
    status: str = Field(..., description="Execution status")
    result: dict[str, Any] = Field(default_factory=dict, description="Agent execution result")
    execution_time_ms: float = Field(..., ge=0, description="Execution time in milliseconds")
    error: str | None = Field(default=None, description="Error message if execution failed")


class HealthResponse(BaseModel):
    """Standard health check response."""

    status: str = Field(default="healthy")
    version: str = Field(default="0.1.0")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ReadinessResponse(BaseModel):
    """Readiness probe response."""

    ready: bool = Field(...)
    checks: dict[str, bool] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: dict[str, Any] | None = Field(default=None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
