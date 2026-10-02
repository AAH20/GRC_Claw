"""Pydantic models for lead scoring."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class LeadStatus(StrEnum):
    """Lead status values."""

    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    UNQUALIFIED = "unqualified"
    CONVERTED = "converted"
    ARCHIVED = "archived"


class LeadSource(StrEnum):
    """Lead source values."""

    WEBSITE = "website"
    REFERRAL = "referral"
    SOCIAL = "social"
    EMAIL = "email"
    EVENT = "event"
    PAID = "paid"
    ORGANIC = "organic"
    API = "api"


class Lead(BaseModel):
    """Core lead model."""

    id: str = Field(..., min_length=1, description="Unique lead identifier")
    email: str = Field(..., min_length=3, description="Lead email address")
    first_name: str = Field(default="", description="First name")
    last_name: str = Field(default="", description="Last name")
    company: str = Field(default="", description="Company name")
    domain: str = Field(default="", description="Company domain")
    phone: str = Field(default="", description="Phone number")
    job_title: str = Field(default="", description="Job title")
    industry: str = Field(default="", description="Industry")
    company_size: int = Field(default=0, ge=0, description="Number of employees")
    annual_revenue: float | None = Field(default=None, ge=0, description="Annual revenue")
    source: LeadSource = Field(default=LeadSource.API, description="Lead source")
    status: LeadStatus = Field(default=LeadStatus.NEW, description="Lead status")
    score: float | None = Field(default=None, ge=0, le=100, description="Lead score")
    grade: str = Field(default="", description="Lead grade (hot/warm/cold)")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Custom metadata")
    created_at: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat(),
        description="Creation timestamp",
    )
    updated_at: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat(),
        description="Last update timestamp",
    )

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Validate email format."""
        if "@" not in v:
            raise ValueError("Invalid email format")
        return v.lower().strip()

    @field_validator("domain")
    @classmethod
    def validate_domain(cls, v: str) -> str:
        """Normalize domain."""
        return v.strip().lower()

    def full_name(self) -> str:
        """Get full name of the lead."""
        return f"{self.first_name} {self.last_name}".strip()

    def is_qualified(self) -> bool:
        """Check if lead is qualified."""
        return self.status == LeadStatus.QUALIFIED

    def update_score(self, score: float, grade: str) -> None:
        """Update lead score and grade."""
        self.score = max(0.0, min(score, 100.0))
        self.grade = grade
        self.updated_at = datetime.now(UTC).isoformat()


class LeadCreate(BaseModel):
    """Model for creating a new lead."""

    email: str = Field(..., min_length=3)
    first_name: str = ""
    last_name: str = ""
    company: str = ""
    domain: str = ""
    phone: str = ""
    job_title: str = ""
    industry: str = ""
    company_size: int = Field(default=0, ge=0)
    annual_revenue: float | None = Field(default=None, ge=0)
    source: LeadSource = LeadSource.API
    metadata: dict[str, Any] = Field(default_factory=dict)


class LeadUpdate(BaseModel):
    """Model for updating an existing lead."""

    first_name: str | None = None
    last_name: str | None = None
    company: str | None = None
    domain: str | None = None
    phone: str | None = None
    job_title: str | None = None
    industry: str | None = None
    company_size: int | None = Field(default=None, ge=0)
    annual_revenue: float | None = Field(default=None, ge=0)
    status: LeadStatus | None = None
    metadata: dict[str, Any] | None = None


class LeadScoreHistory(BaseModel):
    """Model for lead score history entry."""

    lead_id: str
    score: float = Field(ge=0, le=100)
    grade: str
    scored_at: str
    components: dict[str, Any] = Field(default_factory=dict)


class ScoringWeights(BaseModel):
    """Model for scoring weights configuration."""

    firmographic: float = Field(default=0.25, ge=0.0, le=1.0)
    technographic: float = Field(default=0.15, ge=0.0, le=1.0)
    engagement: float = Field(default=0.30, ge=0.0, le=1.0)
    intent: float = Field(default=0.20, ge=0.0, le=1.0)
    timing: float = Field(default=0.10, ge=0.0, le=1.0)

    @field_validator("*")
    @classmethod
    def validate_weights(cls, v: float) -> float:
        """Validate individual weight values."""
        return round(v, 2)

    def validate_total(self) -> bool:
        """Check if weights sum to 1.0."""
        return abs(sum(self.model_dump().values()) - 1.0) < 0.01
