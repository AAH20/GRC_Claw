"""Pydantic data models for skills-assessor."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProficiencyLevel(str, Enum):
    """Enumeration of skill proficiency levels."""

    NOVICE = "novice"
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class SkillCategory(str, Enum):
    """Enumeration of skill categories."""

    TECHNICAL = "technical"
    SOFT = "soft"
    LEADERSHIP = "leadership"
    DOMAIN = "domain"
    TOOL = "tool"
    LANGUAGE = "language"
    FRAMEWORK = "framework"
    METHODOLOGY = "methodology"


class Skill(BaseModel):
    """Represents a single skill with metadata."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., min_length=1, max_length=200, description="Skill name")
    category: SkillCategory = Field(default=SkillCategory.TECHNICAL)
    description: Optional[str] = Field(default=None, max_length=1000)
    keywords: list[str] = Field(default_factory=list)
    parent_skill_id: Optional[UUID] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate and normalize skill name."""
        normalized = v.strip().lower()
        if not normalized:
            raise ValueError("Skill name cannot be empty")
        return normalized


class SkillProficiency(BaseModel):
    """Represents a skill with its proficiency assessment."""

    model_config = ConfigDict(from_attributes=True)

    skill: Skill
    level: ProficiencyLevel
    confidence: float = Field(..., ge=0.0, le=1.0)
    years_experience: Optional[float] = Field(default=None, ge=0.0)
    last_used: Optional[datetime] = None
    evidence: list[str] = Field(default_factory=list)
    notes: Optional[str] = None


class SkillAssessment(BaseModel):
    """Represents a complete skill assessment for a candidate."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(default_factory=uuid4)
    candidate_id: str = Field(..., min_length=1, max_length=200)
    candidate_name: Optional[str] = Field(default=None, max_length=200)
    target_role: Optional[str] = Field(default=None, max_length=200)
    status: str = Field(default="pending", pattern="^(pending|in_progress|completed|failed)$")
    skills: list[SkillProficiency] = Field(default_factory=list)
    overall_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None


class GapReport(BaseModel):
    """Represents a gap analysis report."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(default_factory=uuid4)
    assessment_id: UUID
    target_role: str = Field(..., min_length=1, max_length=200)
    current_skills: list[SkillProficiency] = Field(default_factory=list)
    required_skills: list[SkillProficiency] = Field(default_factory=list)
    missing_skills: list[Skill] = Field(default_factory=list)
    skill_gaps: list[SkillGap] = Field(default_factory=list)
    overall_readiness: float = Field(..., ge=0.0, le=1.0)
    recommendations: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class SkillGap(BaseModel):
    """Represents a gap between current and required skill levels."""

    model_config = ConfigDict(from_attributes=True)

    skill: Skill
    current_level: ProficiencyLevel
    required_level: ProficiencyLevel
    gap_severity: str = Field(..., pattern="^(none|minor|moderate|major|critical)$")
    priority: int = Field(..., ge=1, le=5)
    estimated_hours_to_close: Optional[float] = Field(default=None, ge=0.0)


class LearningPath(BaseModel):
    """Represents a personalized learning path."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(default_factory=uuid4)
    assessment_id: UUID
    candidate_id: str = Field(..., min_length=1, max_length=200)
    target_role: str = Field(..., min_length=1, max_length=200)
    title: str = Field(..., min_length=1, max_length=300)
    description: Optional[str] = Field(default=None, max_length=2000)
    steps: list[LearningStep] = Field(default_factory=list)
    total_estimated_hours: float = Field(default=0.0, ge=0.0)
    difficulty: str = Field(default="intermediate", pattern="^(beginner|intermediate|advanced)$")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class LearningStep(BaseModel):
    """Represents a single step in a learning path."""

    model_config = ConfigDict(from_attributes=True)

    order: int = Field(..., ge=1)
    title: str = Field(..., min_length=1, max_length=300)
    description: Optional[str] = Field(default=None, max_length=1000)
    skill_target: Skill
    proficiency_goal: ProficiencyLevel
    estimated_hours: float = Field(..., ge=0.0)
    resources: list[LearningResource] = Field(default_factory=list)
    milestones: list[str] = Field(default_factory=list)


class LearningResource(BaseModel):
    """Represents a learning resource."""

    model_config = ConfigDict(from_attributes=True)

    title: str = Field(..., min_length=1, max_length=300)
    type: str = Field(..., pattern="^(course|article|video|book|tutorial|documentation|project|other)$")
    url: Optional[str] = Field(default=None, max_length=500)
    provider: Optional[str] = Field(default=None, max_length=200)
    is_free: bool = Field(default=True)
    estimated_hours: Optional[float] = Field(default=None, ge=0.0)


class SkillValidationResult(BaseModel):
    """Represents the result of skill validation."""

    model_config = ConfigDict(from_attributes=True)

    skill: Skill
    is_valid: bool
    confidence: float = Field(..., ge=0.0, le=1.0)
    validation_method: str = Field(..., min_length=1, max_length=100)
    evidence: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    validated_at: datetime = Field(default_factory=datetime.utcnow)


class ExtractionRequest(BaseModel):
    """Request model for skill extraction."""

    text: str = Field(..., min_length=1, max_length=50000, description="Text to extract skills from")
    context: Optional[str] = Field(default=None, max_length=5000)
    source_type: str = Field(default="resume", pattern="^(resume|job_description|linkedin|manual|other)$")
    max_skills: int = Field(default=20, ge=1, le=100)


class ExtractionResponse(BaseModel):
    """Response model for skill extraction."""

    skills: list[Skill]
    total_found: int = Field(..., ge=0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    processing_time_ms: float = Field(..., ge=0.0)


class ScoringRequest(BaseModel):
    """Request model for proficiency scoring."""

    skills: list[Skill] = Field(..., min_length=1)
    candidate_context: Optional[str] = Field(default=None, max_length=10000)
    target_role: Optional[str] = Field(default=None, max_length=200)


class ScoringResponse(BaseModel):
    """Response model for proficiency scoring."""

    proficiencies: list[SkillProficiency]
    overall_score: float = Field(..., ge=0.0, le=1.0)
    processing_time_ms: float = Field(..., ge=0.0)


class GapAnalysisRequest(BaseModel):
    """Request model for gap analysis."""

    assessment_id: UUID
    target_role: str = Field(..., min_length=1, max_length=200)
    required_skills: Optional[list[Skill]] = None


class GapAnalysisResponse(BaseModel):
    """Response model for gap analysis."""

    report: GapReport
    processing_time_ms: float = Field(..., ge=0.0)


class LearningPathRequest(BaseModel):
    """Request model for learning path generation."""

    assessment_id: UUID
    target_role: str = Field(..., min_length=1, max_length=200)
    max_steps: int = Field(default=10, ge=1, le=50)
    preferred_formats: list[str] = Field(default_factory=list)


class LearningPathResponse(BaseModel):
    """Response model for learning path generation."""

    learning_path: LearningPath
    processing_time_ms: float = Field(..., ge=0.0)


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str
    version: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    environment: str


class ErrorResponse(BaseModel):
    """Standard error response model."""

    error: str
    detail: Optional[str] = None
    code: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
