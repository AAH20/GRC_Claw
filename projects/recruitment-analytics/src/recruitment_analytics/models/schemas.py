"""Pydantic models for recruitment analytics data structures."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


# --- Enums --------------------------------------------------------------------


class FunnelStage(str, Enum):
    """Recruitment funnel stages."""
    APPLIED = "applied"
    SCREENING = "screening"
    PHONE_INTERVIEW = "phone_interview"
    TECHNICAL_INTERVIEW = "technical_interview"
    ONSITE_INTERVIEW = "onsite_interview"
    OFFER = "offer"
    HIRED = "hired"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class SourceType(str, Enum):
    """Candidate source types."""
    JOB_BOARD = "job_board"
    REFERRAL = "referral"
    CAREERS_PAGE = "careers_page"
    LINKEDIN = "linkedin"
    RECRUITER = "recruiter"
    AGENCY = "agency"
    CAMPUS = "campus"
    SOCIAL_MEDIA = "social_media"
    DIRECT = "direct"
    OTHER = "other"


class Gender(str, Enum):
    """Gender categories for diversity reporting."""
    MALE = "male"
    FEMALE = "female"
    NON_BINARY = "non_binary"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"
    OTHER = "other"


class Ethnicity(str, Enum):
    """Ethnicity categories for diversity reporting."""
    ASIAN = "asian"
    BLACK = "black"
    HISPANIC = "hispanic"
    WHITE = "white"
    NATIVE_AMERICAN = "native_american"
    PACIFIC_ISLANDER = "pacific_islander"
    TWO_OR_MORE = "two_or_more"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"
    OTHER = "other"


class PredictionOutcome(str, Enum):
    """Possible outcomes for predictive hiring."""
    STRONG_HIRE = "strong_hire"
    HIRE = "hire"
    LEAN_HIRE = "lean_hire"
    LEAN_NO_HIRE = "lean_no_hire"
    NO_HIRE = "no_hire"


class CostCategory(str, Enum):
    """Cost categories for recruitment spend."""
    JOB_BOARD = "job_board"
    RECRUITER = "recruiter"
    AGENCY = "agency"
    REFERRAL_BONUS = "referral_bonus"
    CAMPUS = "campus"
    SOCIAL_MEDIA = "social_media"
    TOOLS = "tools"
    TRAVEL = "travel"
    OTHER = "other"


# --- Funnel Models ------------------------------------------------------------


class FunnelStageMetrics(BaseModel):
    """Metrics for a single funnel stage."""
    model_config = ConfigDict(frozen=True)

    stage: FunnelStage
    count: int = Field(default=0, ge=0)
    conversion_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    avg_time_in_stage_days: float = Field(default=0.0, ge=0.0)
    dropoff_rate: float = Field(default=0.0, ge=0.0, le=1.0)


class Funnel(BaseModel):
    """Complete recruitment funnel for a given period and optional filters."""
    model_config = ConfigDict(frozen=True)

    id: str
    name: str
    start_date: date
    end_date: date
    department: Optional[str] = None
    role: Optional[str] = None
    stages: list[FunnelStageMetrics] = Field(default_factory=list)
    total_applicants: int = Field(default=0, ge=0)
    total_hired: int = Field(default=0, ge=0)
    overall_conversion_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    avg_time_to_hire_days: float = Field(default=0.0, ge=0.0)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("end_date")
    @classmethod
    def validate_date_range(cls, v: date, info) -> date:
        """Ensure end_date is not before start_date."""
        values = info.data
        if "start_date" in values and v < values["start_date"]:
            raise ValueError("end_date must be on or after start_date")
        return v


class FunnelAnalysisRequest(BaseModel):
    """Request model for funnel analysis."""
    start_date: date
    end_date: date
    department: Optional[str] = None
    role: Optional[str] = None
    source: Optional[SourceType] = None


class FunnelAnalysisResponse(BaseModel):
    """Response model for funnel analysis results."""
    funnel: Funnel
    insights: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=datetime.utcnow)


# --- Source Models ------------------------------------------------------------


class SourceMetrics(BaseModel):
    """Metrics for a single recruitment source."""
    model_config = ConfigDict(frozen=True)

    source: SourceType
    label: str
    total_candidates: int = Field(default=0, ge=0)
    qualified_candidates: int = Field(default=0, ge=0)
    hires: int = Field(default=0, ge=0)
    conversion_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    cost_per_hire: Decimal = Field(default=Decimal("0"), ge=Decimal("0"))
    avg_time_to_hire_days: float = Field(default=0.0, ge=0.0)
    quality_score: float = Field(default=0.0, ge=0.0, le=1.0)


class Source(BaseModel):
    """Recruitment source with aggregated metrics."""
    model_config = ConfigDict(frozen=True)

    id: str
    source_type: SourceType
    label: str
    description: Optional[str] = None
    is_active: bool = True
    metrics: SourceMetrics
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class SourceTrackingRequest(BaseModel):
    """Request model for source tracking analysis."""
    start_date: date
    end_date: date
    department: Optional[str] = None
    role: Optional[str] = None


class SourceTrackingResponse(BaseModel):
    """Response model for source tracking results."""
    sources: list[SourceMetrics] = Field(default_factory=list)
    top_performing: list[SourceMetrics] = Field(default_factory=list)
    underperforming: list[SourceMetrics] = Field(default_factory=list)
    insights: list[str] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=datetime.utcnow)


# --- Prediction Models --------------------------------------------------------


class CandidateFeatures(BaseModel):
    """Features used for predictive hiring."""
    model_config = ConfigDict(frozen=True)

    years_experience: float = Field(default=0.0, ge=0.0)
    education_level: str = Field(default="bachelor")
    skills_match_score: float = Field(default=0.0, ge=0.0, le=1.0)
    interview_scores: list[float] = Field(default_factory=list)
    cultural_fit_score: float = Field(default=0.0, ge=0.0, le=1.0)
    referral_boost: bool = False
    previous_company_tier: Optional[str] = None
    certifications: list[str] = Field(default_factory=list)


class Prediction(BaseModel):
    """Predictive hiring result for a candidate."""
    model_config = ConfigDict(frozen=True)

    id: str
    candidate_id: str
    role: str
    outcome: PredictionOutcome
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    score: float = Field(default=0.0, ge=0.0, le=1.0)
    features: CandidateFeatures
    reasoning: str = ""
    risk_factors: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class PredictiveHiringRequest(BaseModel):
    """Request model for predictive hiring analysis."""
    candidate_id: str
    role: str
    features: CandidateFeatures


class PredictiveHiringResponse(BaseModel):
    """Response model for predictive hiring results."""
    prediction: Prediction
    similar_successful_hires: list[dict[str, Any]] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=datetime.utcnow)


# --- Diversity Models ---------------------------------------------------------


class DiversityDimension(BaseModel):
    """Diversity metrics for a single dimension."""
    model_config = ConfigDict(frozen=True)

    dimension: str
    categories: dict[str, int] = Field(default_factory=dict)
    percentages: dict[str, float] = Field(default_factory=dict)
    representation_index: float = Field(default=0.0, ge=0.0, le=1.0)


class DiversityReport(BaseModel):
    """Diversity analysis report."""
    model_config = ConfigDict(frozen=True)

    id: str
    name: str
    start_date: date
    end_date: date
    department: Optional[str] = None
    role: Optional[str] = None
    total_candidates: int = Field(default=0, ge=0)
    gender: DiversityDimension
    ethnicity: DiversityDimension
    additional_dimensions: list[DiversityDimension] = Field(default_factory=list)
    overall_diversity_score: float = Field(default=0.0, ge=0.0, le=1.0)
    insights: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class DiversityAnalysisRequest(BaseModel):
    """Request model for diversity analysis."""
    start_date: date
    end_date: date
    department: Optional[str] = None
    role: Optional[str] = None
    dimensions: list[str] = Field(default_factory=lambda: ["gender", "ethnicity"])


class DiversityAnalysisResponse(BaseModel):
    """Response model for diversity analysis results."""
    report: DiversityReport
    benchmark_comparison: dict[str, Any] = Field(default_factory=dict)
    generated_at: datetime = Field(default_factory=datetime.utcnow)


# --- Cost Models --------------------------------------------------------------


class CostBreakdown(BaseModel):
    """Cost breakdown for a single category."""
    model_config = ConfigDict(frozen=True)

    category: CostCategory
    amount: Decimal = Field(default=Decimal("0"), ge=Decimal("0"))
    percentage_of_total: float = Field(default=0.0, ge=0.0, le=1.0)
    hires_attributed: int = Field(default=0, ge=0)
    cost_per_hire: Decimal = Field(default=Decimal("0"), ge=Decimal("0"))


class CostReport(BaseModel):
    """Recruitment cost analysis report."""
    model_config = ConfigDict(frozen=True)

    id: str
    name: str
    start_date: date
    end_date: date
    department: Optional[str] = None
    role: Optional[str] = None
    total_cost: Decimal = Field(default=Decimal("0"), ge=Decimal("0"))
    total_hires: int = Field(default=0, ge=0)
    cost_per_hire: Decimal = Field(default=Decimal("0"), ge=Decimal("0"))
    breakdown: list[CostBreakdown] = Field(default_factory=list)
    budget_variance: Optional[Decimal] = None
    insights: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class CostAnalysisRequest(BaseModel):
    """Request model for cost analysis."""
    start_date: date
    end_date: date
    department: Optional[str] = None
    role: Optional[str] = None
    budget: Optional[Decimal] = Field(default=None, ge=Decimal("0"))


class CostAnalysisResponse(BaseModel):
    """Response model for cost analysis results."""
    report: CostReport
    trends: list[dict[str, Any]] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=datetime.utcnow)


# --- Health & Generic Models --------------------------------------------------


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    checks: dict[str, str] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str
    detail: str
    code: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
