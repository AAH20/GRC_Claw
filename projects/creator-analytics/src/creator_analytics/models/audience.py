"""Audience-related Pydantic models."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class AgeGroup(StrEnum):
    """Age group categories for audience demographics."""

    UNDER_18 = "under_18"
    AGE_18_24 = "18_24"
    AGE_25_34 = "25_34"
    AGE_35_44 = "35_44"
    AGE_45_54 = "45_54"
    AGE_55_64 = "55_64"
    AGE_65_PLUS = "65_plus"


class Gender(StrEnum):
    """Gender categories for audience demographics."""

    MALE = "male"
    FEMALE = "female"
    NON_BINARY = "non_binary"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"


class AudienceDemographics(BaseModel):
    """Demographic breakdown of an audience."""

    age_distribution: dict[AgeGroup, float] = Field(
        default_factory=dict, description="Percentage distribution across age groups"
    )
    gender_distribution: dict[Gender, float] = Field(
        default_factory=dict, description="Percentage distribution across genders"
    )
    top_countries: dict[str, float] = Field(
        default_factory=dict, description="Top countries by audience percentage"
    )
    top_cities: dict[str, float] = Field(
        default_factory=dict, description="Top cities by audience percentage"
    )
    languages: dict[str, float] = Field(
        default_factory=dict, description="Language distribution"
    )
    interests: list[str] = Field(
        default_factory=list, description="Top audience interests"
    )


class AudienceSegment(BaseModel):
    """A segment of the audience with specific characteristics."""

    segment_id: str = Field(..., description="Unique segment identifier")
    name: str = Field(..., description="Segment name")
    size: int = Field(..., ge=0, description="Number of users in segment")
    engagement_rate: float = Field(
        ..., ge=0.0, le=1.0, description="Engagement rate for this segment"
    )
    demographics: AudienceDemographics = Field(
        ..., description="Demographic information for this segment"
    )
    characteristics: list[str] = Field(
        default_factory=list, description="Key characteristics of this segment"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Segment creation timestamp"
    )


class Audience(BaseModel):
    """Complete audience analysis for a creator."""

    creator_id: str = Field(..., description="Creator identifier")
    total_followers: int = Field(..., ge=0, description="Total follower count")
    active_followers: int = Field(..., ge=0, description="Active followers in last 30 days")
    demographics: AudienceDemographics = Field(
        ..., description="Overall demographic breakdown"
    )
    segments: list[AudienceSegment] = Field(
        default_factory=list, description="Audience segments"
    )
    growth_rate: float = Field(
        ..., description="Monthly audience growth rate as a decimal"
    )
    churn_rate: float = Field(
        ..., ge=0.0, le=1.0, description="Monthly churn rate"
    )
    peak_activity_hours: list[int] = Field(
        default_factory=list, description="Hours of day with peak activity (0-23)"
    )
    analysis_timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="When analysis was performed"
    )
    insights: list[str] = Field(
        default_factory=list, description="AI-generated audience insights"
    )
    recommendations: list[str] = Field(
        default_factory=list, description="AI-generated recommendations"
    )
