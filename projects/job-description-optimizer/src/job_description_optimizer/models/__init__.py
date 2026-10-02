"""Pydantic models for the job description optimizer."""

from datetime import datetime
from enum import Enum, StrEnum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class JobDescription(BaseModel):
    """Input model for a job description to be optimized."""

    title: str = Field(..., min_length=1, max_length=200, description="Job title")
    description: str = Field(
        ..., min_length=10, max_length=50000, description="Full job description text"
    )
    company: str | None = Field(
        default=None, max_length=200, description="Company name"
    )
    location: str | None = Field(
        default=None, max_length=200, description="Job location"
    )
    department: str | None = Field(
        default=None, max_length=200, description="Department name"
    )
    employment_type: str | None = Field(
        default=None,
        description="Employment type (full-time, part-time, contract, etc.)",
    )
    experience_level: str | None = Field(
        default=None,
        description="Experience level (entry, mid, senior, executive)",
    )
    skills: list[str] = Field(
        default_factory=list, description="Required skills for the position"
    )
    responsibilities: list[str] = Field(
        default_factory=list, description="Key responsibilities"
    )
    qualifications: list[str] = Field(
        default_factory=list, description="Required qualifications"
    )
    salary_range: str | None = Field(
        default=None, description="Salary range information"
    )
    benefits: list[str] = Field(
        default_factory=list, description="Benefits offered"
    )
    industry: str | None = Field(
        default=None, description="Industry sector"
    )
    remote_policy: str | None = Field(
        default=None, description="Remote work policy"
    )

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        """Ensure title is not just whitespace."""
        if not v.strip():
            raise ValueError("Title cannot be empty or whitespace only")
        return v.strip()

    @field_validator("description")
    @classmethod
    def description_not_empty(cls, v: str) -> str:
        """Ensure description is not just whitespace."""
        if not v.strip():
            raise ValueError("Description cannot be empty or whitespace only")
        return v.strip()


class BiasType(StrEnum):
    """Types of bias that can be detected."""

    GENDERED_LANGUAGE = "gendered_language"
    AGE_RELATED = "age_related"
    CULTURAL = "cultural"
    ABLEIST = "ableist"
    RACIAL = "racial"
    SOCIOECONOMIC = "socioeconomic"
    OTHER = "other"


class BiasInstance(BaseModel):
    """A single instance of detected bias."""

    bias_type: BiasType = Field(..., description="Type of bias detected")
    original_text: str = Field(..., description="Original biased text")
    suggestion: str = Field(..., description="Suggested replacement")
    explanation: str = Field(..., description="Explanation of why this is biased")
    severity: float = Field(
        ..., ge=0.0, le=1.0, description="Severity score from 0 to 1"
    )


class BiasReport(BaseModel):
    """Report of bias analysis results."""

    original_text: str = Field(..., description="Original job description text")
    cleaned_text: str = Field(..., description="Text with bias removed")
    instances: list[BiasInstance] = Field(
        default_factory=list, description="Detected bias instances"
    )
    overall_score: float = Field(
        ..., ge=0.0, le=1.0, description="Overall bias score (0 = no bias, 1 = high bias)"
    )
    summary: str = Field(default="", description="Summary of bias analysis")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Analysis timestamp"
    )


class SEOReport(BaseModel):
    """Report of SEO optimization results."""

    original_text: str = Field(..., description="Original job description text")
    optimized_text: str = Field(..., description="SEO-optimized text")
    title_suggestions: list[str] = Field(
        default_factory=list, description="Suggested SEO-friendly titles"
    )
    meta_description: str | None = Field(
        default=None, description="Suggested meta description"
    )
    keyword_density: dict[str, float] = Field(
        default_factory=dict, description="Keyword density analysis"
    )
    readability_score: float = Field(
        ..., ge=0.0, le=1.0, description="Readability score"
    )
    seo_score: float = Field(
        ..., ge=0.0, le=1.0, description="Overall SEO score"
    )
    recommendations: list[str] = Field(
        default_factory=list, description="SEO recommendations"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Analysis timestamp"
    )


class ATSReport(BaseModel):
    """Report of ATS compatibility analysis."""

    original_text: str = Field(..., description="Original job description text")
    compatible_text: str = Field(..., description="ATS-compatible text")
    ats_score: float = Field(
        ..., ge=0.0, le=1.0, description="ATS compatibility score"
    )
    issues: list[str] = Field(
        default_factory=list, description="ATS compatibility issues found"
    )
    warnings: list[str] = Field(
        default_factory=list, description="ATS warnings"
    )
    formatting_suggestions: list[str] = Field(
        default_factory=list, description="Formatting suggestions for ATS"
    )
    keyword_matches: dict[str, bool] = Field(
        default_factory=dict, description="Keyword match results"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Analysis timestamp"
    )


class ToneType(StrEnum):
    """Types of tone that can be detected."""

    FORMAL = "formal"
    CASUAL = "casual"
    PROFESSIONAL = "professional"
    FRIENDLY = "friendly"
    AUTHORITATIVE = "authoritative"
    INCLUSIVE = "inclusive"
    ENTHUSIASTIC = "enthusiastic"
    NEUTRAL = "neutral"


class ToneReport(BaseModel):
    """Report of tone analysis results."""

    original_text: str = Field(..., description="Original job description text")
    detected_tones: list[ToneType] = Field(
        default_factory=list, description="Detected tones in the text"
    )
    primary_tone: ToneType = Field(..., description="Primary tone detected")
    tone_scores: dict[str, float] = Field(
        default_factory=dict, description="Score for each tone type"
    )
    inclusivity_score: float = Field(
        ..., ge=0.0, le=1.0, description="Inclusivity score"
    )
    suggestions: list[str] = Field(
        default_factory=list, description="Tone improvement suggestions"
    )
    improved_text: str | None = Field(
        default=None, description="Text with improved tone"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Analysis timestamp"
    )


class KeywordReport(BaseModel):
    """Report of keyword optimization results."""

    original_text: str = Field(..., description="Original job description text")
    optimized_text: str = Field(..., description="Text with optimized keywords")
    extracted_keywords: list[str] = Field(
        default_factory=list, description="Keywords extracted from text"
    )
    suggested_keywords: list[str] = Field(
        default_factory=list, description="Suggested additional keywords"
    )
    missing_keywords: list[str] = Field(
        default_factory=list, description="Important keywords missing from text"
    )
    keyword_density: dict[str, float] = Field(
        default_factory=dict, description="Keyword density analysis"
    )
    industry_relevance: float = Field(
        ..., ge=0.0, le=1.0, description="Industry relevance score"
    )
    recommendations: list[str] = Field(
        default_factory=list, description="Keyword recommendations"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Analysis timestamp"
    )


class OptimizedDescription(BaseModel):
    """Complete optimized job description with all reports."""

    original: JobDescription = Field(..., description="Original job description")
    optimized_text: str = Field(..., description="Fully optimized text")
    bias_report: BiasReport | None = Field(
        default=None, description="Bias analysis report"
    )
    seo_report: SEOReport | None = Field(
        default=None, description="SEO optimization report"
    )
    ats_report: ATSReport | None = Field(
        default=None, description="ATS compatibility report"
    )
    tone_report: ToneReport | None = Field(
        default=None, description="Tone analysis report"
    )
    keyword_report: KeywordReport | None = Field(
        default=None, description="Keyword optimization report"
    )
    overall_score: float = Field(
        ..., ge=0.0, le=1.0, description="Overall optimization score"
    )
    processing_time_ms: float = Field(
        ..., ge=0.0, description="Processing time in milliseconds"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Optimization timestamp"
    )


class OptimizationRequest(BaseModel):
    """Request model for optimization endpoint."""

    job_description: JobDescription = Field(..., description="Job description to optimize")
    options: dict[str, Any] = Field(
        default_factory=dict,
        description="Optimization options (e.g., skip certain agents)",
    )


class AnalysisRequest(BaseModel):
    """Request model for analysis endpoint."""

    job_description: JobDescription = Field(..., description="Job description to analyze")
    analyses: list[str] = Field(
        default_factory=lambda: ["bias", "seo", "ats", "tone", "keywords"],
        description="List of analyses to perform",
    )


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str = Field(..., description="Service status")
    version: str = Field(default="1.0.0", description="Service version")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Response timestamp"
    )


class AgentInfo(BaseModel):
    """Information about an available agent."""

    name: str = Field(..., description="Agent name")
    description: str = Field(..., description="Agent description")
    capabilities: list[str] = Field(
        default_factory=list, description="Agent capabilities"
    )
    status: str = Field(default="available", description="Agent status")


class ErrorResponse(BaseModel):
    """Standard error response model."""

    error: str = Field(..., description="Error message")
    detail: str | None = Field(default=None, description="Detailed error information")
    code: str | None = Field(default=None, description="Error code")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Error timestamp"
    )
