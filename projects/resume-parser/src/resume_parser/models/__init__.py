"""Pydantic data models for resume parsing."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class FileType(StrEnum):
    """Supported resume file types."""

    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    UNKNOWN = "unknown"


class ParsingStatus(StrEnum):
    """Resume parsing status."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ContactInfo(BaseModel):
    """Contact information extracted from a resume."""

    model_config = ConfigDict(str_strip_whitespace=True)

    full_name: str = Field(..., description="Full name of the candidate")
    email: str | None = Field(default=None, description="Email address")
    phone: str | None = Field(default=None, description="Phone number")
    address: str | None = Field(default=None, description="Physical address")
    linkedin: str | None = Field(default=None, description="LinkedIn profile URL")
    github: str | None = Field(default=None, description="GitHub profile URL")
    website: str | None = Field(default=None, description="Personal website URL")
    summary: str | None = Field(default=None, description="Professional summary")

    @field_validator("email")
    @classmethod
    def _validate_email(cls, v: str | None) -> str | None:
        """Basic email validation."""
        if v and "@" not in v:
            return None
        return v


class Skill(BaseModel):
    """A skill extracted from a resume."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(..., description="Skill name")
    category: Literal["technical", "soft", "language", "tool", "other"] = Field(
        default="other", description="Skill category"
    )
    proficiency: Literal["beginner", "intermediate", "advanced", "expert"] | None = Field(
        default=None, description="Proficiency level"
    )
    years_experience: float | None = Field(
        default=None, ge=0, description="Years of experience with this skill"
    )


class Experience(BaseModel):
    """Work experience extracted from a resume."""

    model_config = ConfigDict(str_strip_whitespace=True)

    company: str = Field(..., description="Company name")
    title: str = Field(..., description="Job title")
    location: str | None = Field(default=None, description="Job location")
    start_date: str | None = Field(default=None, description="Start date")
    end_date: str | None = Field(default=None, description="End date (None if current)")
    is_current: bool = Field(default=False, description="Whether this is the current position")
    description: str | None = Field(default=None, description="Job description")
    achievements: list[str] = Field(default_factory=list, description="Key achievements")


class Education(BaseModel):
    """Education entry extracted from a resume."""

    model_config = ConfigDict(str_strip_whitespace=True)

    institution: str = Field(..., description="Educational institution name")
    degree: str = Field(..., description="Degree or certification")
    field_of_study: str | None = Field(default=None, description="Field of study")
    location: str | None = Field(default=None, description="Institution location")
    start_date: str | None = Field(default=None, description="Start date")
    end_date: str | None = Field(default=None, description="End date or graduation date")
    gpa: float | None = Field(default=None, ge=0, le=4.0, description="GPA if available")
    honors: list[str] = Field(default_factory=list, description="Honors and awards")


class Resume(BaseModel):
    """Raw resume data before parsing."""

    model_config = ConfigDict(str_strip_whitespace=True)

    id: str = Field(..., description="Unique resume identifier")
    file_name: str = Field(..., description="Original file name")
    file_type: FileType = Field(..., description="File type")
    file_size_bytes: int = Field(..., ge=0, description="File size in bytes")
    content: str = Field(..., description="Extracted text content")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional file metadata"
    )
    uploaded_at: datetime = Field(
        default_factory=datetime.utcnow, description="Upload timestamp"
    )


class ParsedResume(BaseModel):
    """Fully parsed resume with all extracted information."""

    model_config = ConfigDict(str_strip_whitespace=True)

    id: str = Field(..., description="Unique resume identifier")
    resume_id: str = Field(..., description="Reference to source resume ID")
    contact: ContactInfo = Field(..., description="Contact information")
    skills: list[Skill] = Field(default_factory=list, description="Extracted skills")
    experience: list[Experience] = Field(default_factory=list, description="Work experience")
    education: list[Education] = Field(default_factory=list, description="Education history")
    languages: list[str] = Field(default_factory=list, description="Spoken languages")
    certifications: list[str] = Field(default_factory=list, description="Certifications")
    raw_text: str = Field(default="", description="Original extracted text")
    parsing_metadata: dict[str, Any] = Field(
        default_factory=dict, description="Parsing metadata and confidence scores"
    )
    parsed_at: datetime = Field(
        default_factory=datetime.utcnow, description="Parsing timestamp"
    )
    status: ParsingStatus = Field(
        default=ParsingStatus.COMPLETED, description="Parsing status"
    )
    errors: list[str] = Field(default_factory=list, description="Parsing errors if any")


class AgentResult(BaseModel):
    """Result from a single agent execution."""

    model_config = ConfigDict(str_strip_whitespace=True)

    agent_name: str = Field(..., description="Agent name")
    success: bool = Field(..., description="Whether the agent succeeded")
    data: dict[str, Any] = Field(default_factory=dict, description="Agent output data")
    error: str | None = Field(default=None, description="Error message if failed")
    execution_time_seconds: float = Field(
        default=0.0, ge=0, description="Execution time in seconds"
    )
    tokens_used: int | None = Field(default=None, ge=0, description="Tokens consumed")


class ParseRequest(BaseModel):
    """Request model for resume parsing."""

    model_config = ConfigDict(str_strip_whitespace=True)

    text: str | None = Field(default=None, description="Raw text to parse")
    file_path: str | None = Field(default=None, description="Path to resume file")
    file_type: FileType | None = Field(default=None, description="File type hint")
    use_agents: list[str] | None = Field(
        default=None, description="Specific agents to use (None for all)"
    )
    options: dict[str, Any] = Field(
        default_factory=dict, description="Additional parsing options"
    )


class ParseResponse(BaseModel):
    """Response model for resume parsing."""

    model_config = ConfigDict(str_strip_whitespace=True)

    success: bool = Field(..., description="Whether parsing succeeded")
    resume_id: str = Field(..., description="Resume identifier")
    parsed_resume: ParsedResume | None = Field(
        default=None, description="Parsed resume data"
    )
    agent_results: list[AgentResult] = Field(
        default_factory=list, description="Individual agent results"
    )
    total_execution_time_seconds: float = Field(
        default=0.0, ge=0, description="Total execution time"
    )
    errors: list[str] = Field(default_factory=list, description="Errors if any")


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Service status")
    version: str = Field(..., description="Service version")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Response timestamp"
    )
    details: dict[str, Any] = Field(
        default_factory=dict, description="Additional health details"
    )


class StatsResponse(BaseModel):
    """Service statistics response."""

    total_resumes_parsed: int = Field(default=0, ge=0, description="Total resumes parsed")
    total_agents_executed: int = Field(default=0, ge=0, description="Total agent executions")
    average_parsing_time_seconds: float = Field(
        default=0.0, ge=0, description="Average parsing time"
    )
    success_rate: float = Field(default=0.0, ge=0, le=1.0, description="Success rate")
    active_agents: list[str] = Field(
        default_factory=list, description="List of active agent names"
    )
    uptime_seconds: float = Field(default=0.0, ge=0, description="Service uptime in seconds")
