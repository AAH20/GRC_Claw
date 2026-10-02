"""Growth prediction Pydantic models."""

from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class GrowthMetric(str, Enum):
    """Types of growth metrics."""

    FOLLOWERS = "followers"
    ENGAGEMENT = "engagement"
    REVENUE = "revenue"
    REACH = "reach"
    VIEWS = "views"
    CONVERSIONS = "conversions"


class GrowthScenario(str, Enum):
    """Growth prediction scenarios."""

    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"


class GrowthPrediction(BaseModel):
    """Growth prediction for a creator."""

    creator_id: str = Field(..., description="Creator identifier")
    prediction_period_months: int = Field(
        ..., ge=1, le=24, description="Prediction period in months"
    )
    current_followers: int = Field(..., ge=0, description="Current follower count")
    predicted_followers: dict[GrowthScenario, int] = Field(
        ..., description="Predicted followers by scenario"
    )
    current_monthly_revenue: float = Field(
        ..., ge=0.0, description="Current monthly revenue"
    )
    predicted_monthly_revenue: dict[GrowthScenario, float] = Field(
        ..., description="Predicted monthly revenue by scenario"
    )
    growth_rate_predictions: dict[GrowthScenario, float] = Field(
        ..., description="Predicted monthly growth rates by scenario"
    )
    key_growth_drivers: list[str] = Field(
        default_factory=list, description="Key factors driving growth"
    )
    risk_factors: list[str] = Field(
        default_factory=list, description="Potential risk factors"
    )
    milestones: list[dict[str, str]] = Field(
        default_factory=list, description="Predicted milestones with dates"
    )
    confidence_score: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence score for predictions"
    )
    insights: list[str] = Field(
        default_factory=list, description="AI-generated growth insights"
    )
    recommendations: list[str] = Field(
        default_factory=list, description="AI-generated recommendations"
    )
    predicted_at: datetime = Field(
        default_factory=datetime.utcnow, description="Prediction timestamp"
    )
