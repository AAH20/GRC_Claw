"""Pydantic models for reputation system entities."""

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class TrustTierLevel(StrEnum):
    """Trust tier levels."""

    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"
    DIAMOND = "diamond"


class BadgeCategory(StrEnum):
    """Badge categories."""

    CONTRIBUTION = "contribution"
    QUALITY = "quality"
    COMMUNITY = "community"
    EXPERTISE = "expertise"
    SPECIAL = "special"


class ReputationScore(BaseModel):
    """Reputation score model."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(default_factory=uuid4)
    member_id: str = Field(..., min_length=1, max_length=255)
    score: int = Field(..., ge=0, le=1000)
    trust_tier: TrustTierLevel = TrustTierLevel.BRONZE
    badge_count: int = Field(default=0, ge=0)
    total_contributions: int = Field(default=0, ge=0)
    positive_feedback: int = Field(default=0, ge=0)
    negative_feedback: int = Field(default=0, ge=0)
    last_activity_at: datetime | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ReputationScoreCreate(BaseModel):
    """Create reputation score request."""

    member_id: str = Field(..., min_length=1, max_length=255)
    initial_score: int = Field(default=100, ge=0, le=1000)
    metadata: dict[str, Any] | None = None


class ReputationScoreUpdate(BaseModel):
    """Update reputation score request."""

    score: int | None = Field(None, ge=0, le=1000)
    trust_tier: TrustTierLevel | None = None
    metadata: dict[str, Any] | None = None


class Badge(BaseModel):
    """Badge model."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., max_length=1000)
    category: BadgeCategory = BadgeCategory.CONTRIBUTION
    icon_url: str | None = None
    criteria: dict[str, Any] = Field(default_factory=dict)
    points: int = Field(default=10, ge=0)
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class BadgeCreate(BaseModel):
    """Create badge request."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., max_length=1000)
    category: BadgeCategory = BadgeCategory.CONTRIBUTION
    icon_url: str | None = None
    criteria: dict[str, Any] | None = None
    points: int = Field(default=10, ge=0)


class BadgeUpdate(BaseModel):
    """Update badge request."""

    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, max_length=1000)
    category: BadgeCategory | None = None
    icon_url: str | None = None
    criteria: dict[str, Any] | None = None
    points: int | None = Field(None, ge=0)
    is_active: bool | None = None


class TrustTier(BaseModel):
    """Trust tier model."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(default_factory=uuid4)
    level: TrustTierLevel
    name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., max_length=1000)
    min_score: int = Field(..., ge=0)
    max_score: int = Field(..., ge=0)
    benefits: list[str] = Field(default_factory=list)
    requirements: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class TrustTierCreate(BaseModel):
    """Create trust tier request."""

    level: TrustTierLevel
    name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., max_length=1000)
    min_score: int = Field(..., ge=0)
    max_score: int = Field(..., ge=0)
    benefits: list[str] | None = None
    requirements: dict[str, Any] | None = None


class TrustTierUpdate(BaseModel):
    """Update trust tier request."""

    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, max_length=1000)
    min_score: int | None = Field(None, ge=0)
    max_score: int | None = Field(None, ge=0)
    benefits: list[str] | None = None
    requirements: dict[str, Any] | None = None


class ReputationHistory(BaseModel):
    """Reputation history entry model."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(default_factory=uuid4)
    member_id: str = Field(..., min_length=1, max_length=255)
    action: str = Field(..., min_length=1, max_length=255)
    score_change: int = Field(...)
    previous_score: int = Field(..., ge=0)
    new_score: int = Field(..., ge=0)
    badge_id: UUID | None = None
    reason: str | None = Field(None, max_length=1000)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ReputationHistoryCreate(BaseModel):
    """Create reputation history entry request."""

    member_id: str = Field(..., min_length=1, max_length=255)
    action: str = Field(..., min_length=1, max_length=255)
    score_change: int = Field(...)
    previous_score: int = Field(..., ge=0)
    new_score: int = Field(..., ge=0)
    badge_id: UUID | None = None
    reason: str | None = Field(None, max_length=1000)
    metadata: dict[str, Any] | None = None


class ReputationExplanation(BaseModel):
    """Reputation explanation model."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(default_factory=uuid4)
    member_id: str = Field(..., min_length=1, max_length=255)
    explanation: str = Field(..., max_length=5000)
    factors: list[dict[str, Any]] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ReputationExplanationCreate(BaseModel):
    """Create reputation explanation request."""

    member_id: str = Field(..., min_length=1, max_length=255)
    explanation: str = Field(..., max_length=5000)
    factors: list[dict[str, Any]] | None = None
    recommendations: list[str] | None = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str = "0.1.0"
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ErrorResponse(BaseModel):
    """Error response model."""

    error: str
    detail: str | None = None
    code: str | None = None
