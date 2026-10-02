"""Pydantic models for moderation analytics."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class ModerationAction(str, Enum):
    """Types of moderation actions."""

    APPROVE = "approve"
    REJECT = "reject"
    FLAG = "flag"
    ESCALATE = "escalate"
    WARN = "warn"
    BAN = "ban"
    SHADOW_BAN = "shadow_ban"


class SeverityLevel(str, Enum):
    """Severity levels for moderation events."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TrendDirection(str, Enum):
    """Direction of a trend."""

    INCREASING = "increasing"
    DECREASING = "decreasing"
    STABLE = "stable"
    VOLATILE = "volatile"


class ModerationAnalytics(BaseModel):
    """Aggregated moderation analytics data."""

    total_events: int = Field(..., ge=0, description="Total moderation events")
    total_actions: int = Field(..., ge=0, description="Total actions taken")
    action_breakdown: dict[ModerationAction, int] = Field(
        default_factory=dict, description="Breakdown of actions by type"
    )
    severity_distribution: dict[SeverityLevel, int] = Field(
        default_factory=dict, description="Distribution of severity levels"
    )
    average_response_time_seconds: float = Field(
        ..., ge=0, description="Average response time in seconds"
    )
    period_start: datetime = Field(..., description="Start of analytics period")
    period_end: datetime = Field(..., description="End of analytics period")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    @field_validator("period_end")
    @classmethod
    def validate_period(cls, v: datetime, info: Any) -> datetime:
        """Validate that period_end is after period_start."""
        if "period_start" in info.data and v <= info.data["period_start"]:
            raise ValueError("period_end must be after period_start")
        return v


class Trend(BaseModel):
    """A single trend data point."""

    metric_name: str = Field(..., min_length=1, description="Name of the metric")
    direction: TrendDirection = Field(..., description="Direction of the trend")
    change_percentage: float = Field(..., description="Percentage change")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    data_points: list[float] = Field(default_factory=list, description="Raw data points")
    start_date: datetime = Field(..., description="Start date of trend")
    end_date: datetime = Field(..., description="End date of trend")
    description: str = Field(default="", description="Human-readable description")


class ModeratorPerformance(BaseModel):
    """Performance metrics for a moderator."""

    moderator_id: str = Field(..., min_length=1, description="Moderator identifier")
    moderator_name: str = Field(..., min_length=1, description="Moderator display name")
    total_reviews: int = Field(..., ge=0, description="Total reviews completed")
    accuracy: float = Field(..., ge=0.0, le=1.0, description="Decision accuracy")
    average_response_time_seconds: float = Field(
        ..., ge=0, description="Average response time in seconds"
    )
    consistency_score: float = Field(..., ge=0.0, le=1.0, description="Decision consistency")
    escalation_rate: float = Field(..., ge=0.0, le=1.0, description="Rate of escalations")
    period_start: datetime = Field(..., description="Start of evaluation period")
    period_end: datetime = Field(..., description="End of evaluation period")
    strengths: list[str] = Field(default_factory=list, description="Identified strengths")
    weaknesses: list[str] = Field(default_factory=list, description="Identified weaknesses")
    recommendations: list[str] = Field(default_factory=list, description="Improvement recommendations")


class PolicyEffectiveness(BaseModel):
    """Effectiveness metrics for a moderation policy."""

    policy_id: str = Field(..., min_length=1, description="Policy identifier")
    policy_name: str = Field(..., min_length=1, description="Policy name")
    policy_version: str = Field(..., description="Policy version")
    total_violations: int = Field(..., ge=0, description="Total violations detected")
    total_enforcements: int = Field(..., ge=0, description="Total enforcements applied")
    detection_rate: float = Field(..., ge=0.0, le=1.0, description="Violation detection rate")
    false_positive_rate: float = Field(..., ge=0.0, le=1.0, description="False positive rate")
    false_negative_rate: float = Field(..., ge=0.0, le=1.0, description="False negative rate")
    user_appeal_rate: float = Field(..., ge=0.0, le=1.0, description="User appeal rate")
    appeal_success_rate: float = Field(..., ge=0.0, le=1.0, description="Appeal success rate")
    period_start: datetime = Field(..., description="Start of evaluation period")
    period_end: datetime = Field(..., description="End of evaluation period")
    effectiveness_score: float = Field(..., ge=0.0, le=1.0, description="Overall effectiveness")
    recommendations: list[str] = Field(default_factory=list, description="Policy improvement recommendations")


class ModerationPrediction(BaseModel):
    """Prediction for future moderation metrics."""

    prediction_type: Literal["workload", "risk", "trend"] = Field(
        ..., description="Type of prediction"
    )
    target_date: datetime = Field(..., description="Date for which prediction is made")
    predicted_value: float = Field(..., description="Predicted value")
    confidence_interval: tuple[float, float] = Field(
        ..., description="Confidence interval (lower, upper)"
    )
    confidence: float = Field(..., ge=0.0, le=1.0, description="Prediction confidence")
    factors: list[str] = Field(default_factory=list, description="Contributing factors")
    model_version: str = Field(default="v1", description="Model version used")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")


class AnalyticsSummary(BaseModel):
    """Complete analytics summary response."""

    analytics: ModerationAnalytics = Field(..., description="Core analytics data")
    trends: list[Trend] = Field(default_factory=list, description="Identified trends")
    top_moderators: list[ModeratorPerformance] = Field(
        default_factory=list, description="Top performing moderators"
    )
    policy_scores: list[PolicyEffectiveness] = Field(
        default_factory=list, description="Policy effectiveness scores"
    )
    predictions: list[ModerationPrediction] = Field(
        default_factory=list, description="Generated predictions"
    )
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="Generation time")
    summary_text: str = Field(default="", description="AI-generated summary")


class HealthResponse(BaseModel):
    """Health check response."""

    status: Literal["healthy", "degraded", "unhealthy"] = Field(..., description="Service status")
    version: str = Field(..., description="Service version")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    checks: dict[str, bool] = Field(default_factory=dict, description="Individual health checks")


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: dict[str, Any] = Field(default_factory=dict, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
