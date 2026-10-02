"""Core domain models for candidates and jobs."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class SkillLevel(StrEnum):
    """Proficiency levels for skills."""

    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class Skill(BaseModel):
    """A skill with proficiency level and years of experience."""

    model_config = ConfigDict(frozen=True)

    name: str = Field(..., min_length=1, max_length=100, description="Skill name")
    level: SkillLevel = Field(default=SkillLevel.INTERMEDIATE, description="Proficiency level")
    years_experience: float = Field(default=0.0, ge=0, le=50, description="Years of experience")
    category: str | None = Field(default=None, max_length=50, description="Skill category")


class Candidate(BaseModel):
    """A candidate profile."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(default_factory=uuid4, description="Unique candidate identifier")
    name: str = Field(..., min_length=1, max_length=200, description="Candidate full name")
    email: str = Field(..., max_length=255, description="Candidate email address")
    skills: list[Skill] = Field(default_factory=list, description="Candidate skills")
    experience_years: float = Field(
        default=0.0, ge=0, le=60, description="Total years of experience"
    )
    education: list[dict[str, Any]] = Field(default_factory=list, description="Education history")
    work_history: list[dict[str, Any]] = Field(default_factory=list, description="Work history")
    preferences: dict[str, Any] = Field(default_factory=dict, description="Job preferences")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Last update timestamp"
    )


class JobRequirement(BaseModel):
    """A job requirement with importance weight."""

    model_config = ConfigDict(frozen=True)

    skill_name: str = Field(..., min_length=1, max_length=100, description="Required skill name")
    minimum_level: SkillLevel = Field(
        default=SkillLevel.INTERMEDIATE, description="Minimum proficiency"
    )
    preferred: bool = Field(
        default=False, description="Whether this is a preferred (not required) skill"
    )
    weight: float = Field(default=1.0, ge=0.0, le=1.0, description="Importance weight")


class JobPosting(BaseModel):
    """A job posting with requirements."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(default_factory=uuid4, description="Unique job identifier")
    title: str = Field(..., min_length=1, max_length=200, description="Job title")
    description: str = Field(..., min_length=1, description="Job description")
    company: str = Field(..., min_length=1, max_length=200, description="Company name")
    department: str | None = Field(default=None, max_length=100, description="Department")
    location: str | None = Field(default=None, max_length=200, description="Job location")
    requirements: list[JobRequirement] = Field(default_factory=list, description="Job requirements")
    responsibilities: list[str] = Field(default_factory=list, description="Job responsibilities")
    culture_values: list[str] = Field(default_factory=list, description="Company culture values")
    benefits: list[str] = Field(default_factory=list, description="Benefits offered")
    salary_range: dict[str, float] | None = Field(default=None, description="Salary range")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Last update timestamp"
    )


class MatchRequest(BaseModel):
    """Request to match candidates to a job posting."""

    model_config = ConfigDict(from_attributes=True)

    job_id: UUID = Field(..., description="Job posting identifier")
    candidate_ids: list[UUID] = Field(
        default_factory=list,
        description="Candidate identifiers to match (empty = match all)",
    )
    top_k: int = Field(default=10, ge=1, le=100, description="Number of top matches to return")
    include_explanation: bool = Field(
        default=True, description="Whether to include match explanations"
    )
    bias_mitigation: bool = Field(default=True, description="Whether to apply bias mitigation")
    min_similarity: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Minimum similarity threshold"
    )
    weights: dict[str, float] = Field(
        default_factory=lambda: {
            "semantic": 0.35,
            "skills": 0.30,
            "experience": 0.20,
            "culture": 0.15,
        },
        description="Scoring weights for each dimension",
    )


class MatchResult(BaseModel):
    """Result of matching a candidate to a job."""

    model_config = ConfigDict(from_attributes=True)

    match_id: UUID = Field(default_factory=uuid4, description="Unique match identifier")
    job_id: UUID = Field(..., description="Job posting identifier")
    candidate_id: UUID = Field(..., description="Candidate identifier")
    overall_score: float = Field(..., ge=0.0, le=1.0, description="Overall match score")
    semantic_score: float = Field(..., ge=0.0, le=1.0, description="Semantic similarity score")
    skills_score: float = Field(..., ge=0.0, le=1.0, description="Skills match score")
    experience_score: float = Field(..., ge=0.0, le=1.0, description="Experience match score")
    culture_score: float = Field(..., ge=0.0, le=1.0, description="Culture fit score")
    bias_adjusted: bool = Field(default=False, description="Whether bias adjustment was applied")
    bias_penalty: float = Field(default=0.0, ge=0.0, le=1.0, description="Bias penalty applied")
    rank: int = Field(default=0, ge=0, description="Rank among all matches")
    explanation: str | None = Field(default=None, description="Human-readable explanation")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Match timestamp")


class SkillsGap(BaseModel):
    """Skills gap analysis between a candidate and job."""

    model_config = ConfigDict(from_attributes=True)

    candidate_id: UUID = Field(..., description="Candidate identifier")
    job_id: UUID = Field(..., description="Job identifier")
    missing_skills: list[dict[str, Any]] = Field(
        default_factory=list, description="Skills the candidate lacks"
    )
    skill_gaps: list[dict[str, Any]] = Field(
        default_factory=list, description="Skills where candidate is below required level"
    )
    matching_skills: list[dict[str, Any]] = Field(
        default_factory=list, description="Skills that match requirements"
    )
    gap_score: float = Field(
        ..., ge=0.0, le=1.0, description="Overall gap score (0=no gap, 1=large gap)"
    )
    coverage_ratio: float = Field(
        ..., ge=0.0, le=1.0, description="Ratio of required skills covered"
    )
    recommendations: list[str] = Field(
        default_factory=list, description="Upskilling recommendations"
    )


class BiasReport(BaseModel):
    """Bias analysis report for a match or set of matches."""

    model_config = ConfigDict(from_attributes=True)

    report_id: UUID = Field(default_factory=uuid4, description="Unique report identifier")
    match_id: UUID | None = Field(default=None, description="Associated match identifier")
    bias_detected: bool = Field(default=False, description="Whether bias was detected")
    bias_types: list[str] = Field(default_factory=list, description="Types of bias detected")
    bias_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Overall bias score")
    affected_attributes: list[str] = Field(
        default_factory=list, description="Attributes affected by bias"
    )
    mitigation_applied: bool = Field(default=False, description="Whether mitigation was applied")
    mitigation_strategy: str | None = Field(default=None, description="Mitigation strategy used")
    details: dict[str, Any] = Field(default_factory=dict, description="Detailed bias analysis")
    recommendations: list[str] = Field(
        default_factory=list, description="Bias mitigation recommendations"
    )


class MatchExplanation(BaseModel):
    """Human-readable explanation of a match result."""

    model_config = ConfigDict(from_attributes=True)

    explanation_id: UUID = Field(default_factory=uuid4, description="Unique explanation identifier")
    match_id: UUID = Field(..., description="Associated match identifier")
    summary: str = Field(..., description="Brief summary of the match")
    strengths: list[str] = Field(
        default_factory=list, description="Candidate strengths for this role"
    )
    weaknesses: list[str] = Field(default_factory=list, description="Areas for improvement")
    key_factors: list[dict[str, Any]] = Field(
        default_factory=list, description="Key factors influencing the score"
    )
    suggestions: list[str] = Field(
        default_factory=list, description="Suggestions for candidate improvement"
    )
    confidence: float = Field(..., ge=0.0, le=1.0, description="Explanation confidence level")
    generated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Generation timestamp"
    )


class BatchMatchRequest(BaseModel):
    """Request for batch matching multiple candidates."""

    model_config = ConfigDict(from_attributes=True)

    job_id: UUID = Field(..., description="Job posting identifier")
    candidate_ids: list[UUID] = Field(
        ..., min_length=1, max_length=100, description="Candidate identifiers to match"
    )
    include_explanations: bool = Field(default=False, description="Whether to include explanations")
    bias_mitigation: bool = Field(default=True, description="Whether to apply bias mitigation")


class BatchMatchResponse(BaseModel):
    """Response for batch matching."""

    model_config = ConfigDict(from_attributes=True)

    job_id: UUID = Field(..., description="Job posting identifier")
    results: list[MatchResult] = Field(default_factory=list, description="Match results")
    total_candidates: int = Field(..., description="Total candidates processed")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Service status")
    version: str = Field(..., description="Service version")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    checks: dict[str, bool] = Field(default_factory=dict, description="Component health checks")


class ReadinessResponse(BaseModel):
    """Readiness probe response."""

    ready: bool = Field(..., description="Whether the service is ready")
    checks: dict[str, bool] = Field(default_factory=dict, description="Readiness checks")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")


class CultureFitResult(BaseModel):
    """Culture fit assessment result."""

    model_config = ConfigDict(from_attributes=True)

    fit_score: float = Field(..., ge=0.0, le=1.0, description="Overall culture fit score")
    aligned_values: list[str] = Field(default_factory=list, description="Values that align")
    potential_conflicts: list[str] = Field(
        default_factory=list, description="Potential cultural conflicts"
    )
    work_style_compatibility: str = Field(
        default="", description="Work style compatibility description"
    )
    summary: str = Field(default="", description="Brief summary of cultural fit")
