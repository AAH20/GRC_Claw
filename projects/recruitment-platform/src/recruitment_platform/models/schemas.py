"""Pydantic schemas for the recruitment platform."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class BaseSchema(BaseModel):
    """Base schema with common configuration."""

    model_config = {"from_attributes": True}


class HealthResponse(BaseSchema):
    """Health check response schema."""

    status: str
    service: str
    version: Optional[str] = None
    timestamp: Optional[datetime] = None


class AgentResponse(BaseSchema, Generic[T]):
    """Generic agent response wrapper."""

    success: bool = True
    data: Optional[T] = None
    error: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None


class ResumeParseRequest(BaseSchema):
    """Resume parsing request schema."""

    text: str = Field(..., description="Resume text content")
    extract_contact: bool = True
    extract_education: bool = True
    extract_experience: bool = True
    extract_skills: bool = True


class ResumeParseResponse(BaseSchema):
    """Resume parsing response schema."""

    contact: dict[str, str] = Field(default_factory=dict)
    education: list[dict[str, str]] = Field(default_factory=list)
    experience: list[dict[str, Any]] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)


class MatchRequest(BaseSchema):
    """Candidate matching request schema."""

    candidates: list[dict[str, Any]] = Field(..., description="List of candidate profiles")
    job_requirements: dict[str, Any] = Field(..., description="Job requirements")


class MatchResponse(BaseSchema):
    """Candidate matching response schema."""

    matches: list[dict[str, Any]] = Field(default_factory=list)
    total_candidates: int = 0
    processing_time_ms: float = 0.0


class InterviewSlotRequest(BaseSchema):
    """Interview slot optimization request schema."""

    participants: list[dict[str, Any]] = Field(..., description="Participant availability data")
    duration_minutes: int = Field(default=60, ge=15, le=480)
    preferred_days: list[str] = Field(default_factory=list)


class SkillsAssessmentRequest(BaseSchema):
    """Skills assessment request schema."""

    skill_assessments: dict[str, Any] = Field(..., description="Skill assessment data")
    target_level: Optional[str] = None


class BiasAnalysisRequest(BaseSchema):
    """Bias analysis request schema."""

    text: Optional[str] = None
    hiring_data: Optional[dict[str, Any]] = None
    analysis_type: str = Field(default="language", description="Type of bias analysis")


class TalentPoolRequest(BaseSchema):
    """Talent pool request schema."""

    job_requirements: Optional[dict[str, Any]] = None
    pool_criteria: Optional[dict[str, Any]] = None
    action: str = Field(default="source", description="Action to perform")


class AnalyticsRequest(BaseSchema):
    """Analytics request schema."""

    analysis_type: str = Field(..., description="Type of analytics")
    date_range: Optional[dict[str, str]] = None
    filters: Optional[dict[str, Any]] = None


class OnboardingRequest(BaseSchema):
    """Onboarding request schema."""

    employee_id: Optional[str] = None
    employee_data: Optional[dict[str, Any]] = None
    action: str = Field(default="track_progress", description="Onboarding action")


class JobDescriptionRequest(BaseSchema):
    """Job description optimization request schema."""

    job_description: str = Field(..., description="Job description text")
    target_role: Optional[str] = None
    brand_voice: Optional[str] = None
    platform: Optional[str] = None


class EmployerBrandingRequest(BaseSchema):
    """Employer branding request schema."""

    action: str = Field(..., description="Branding action to perform")
    company_data: Optional[dict[str, Any]] = None
    content_type: Optional[str] = None
    texts: Optional[list[str]] = None
