"""Pydantic models for reputation system entities."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class TrustTierLevel(str, Enum):
    """Trust tier levels."""

    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"
    DIAMOND = "diamond"


class BadgeCategory(str, Enum):
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
    last_activity_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ReputationScoreCreate(BaseModel):
    """Create reputation score request."""

    member_id: str = Field(..., min_length=1, max_length=255)
    initial_score: int = Field(default=100, ge=0, le=1000)
    metadata: Optional[Dict[str, Any]] = None


class ReputationScoreUpdate(BaseModel):
    """Update reputation score request."""

    score: Optional[int] = Field(None, ge=0, le=1000)
    trust_tier: Optional[TrustTierLevel] = None
    metadata: Optional[Dict[str, Any]] = None


class Badge(BaseModel):
    """Badge model."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., max_length=1000)
    category: BadgeCategory = BadgeCategory.CONTRIBUTION
    icon_url: Optional[str] = None
    criteria: Dict[str, Any] = Field(default_factory=dict)
    points: int = Field(default=10, ge=0)
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class BadgeCreate(BaseModel):
    """Create badge request."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., max_length=1000)
    category: BadgeCategory = BadgeCategory.CONTRIBUTION
    icon_url: Optional[str] = None
    criteria: Optional[Dict[str, Any]] = None
    points: int = Field(default=10, ge=0)


class BadgeUpdate(BaseModel):
    """Update badge request."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    category: Optional[BadgeCategory] = None
    icon_url: Optional[str] = None
    criteria: Optional[Dict[str, Any]] = None
    points: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None


class TrustTier(BaseModel):
    """Trust tier model."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(default_factory=uuid4)
    level: TrustTierLevel
    name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., max_length=1000)
    min_score: int = Field(..., ge=0)
    max_score: int = Field(..., ge=0)
    benefits: List[str] = Field(default_factory=list)
    requirements: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class TrustTierCreate(BaseModel):
    """Create trust tier request."""

    level: TrustTierLevel
    name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., max_length=1000)
    min_score: int = Field(..., ge=0)
    max_score: int = Field(..., ge=0)
    benefits: Optional[List[str]] = None
    requirements: Optional[Dict[str, Any]] = None


class TrustTierUpdate(BaseModel):
    """Update trust tier request."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    min_score: Optional[int] = Field(None, ge=0)
    max_score: Optional[int] = Field(None, ge=0)
    benefits: Optional[List[str]] = None
    requirements: Optional[Dict[str, Any]] = None


class ReputationHistory(BaseModel):
    """Reputation history entry model."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(default_factory=uuid4)
    member_id: str = Field(..., min_length=1, max_length=255)
    action: str = Field(..., min_length=1, max_length=255)
    score_change: int = Field(...)
    previous_score: int = Field(..., ge=0)
    new_score: int = Field(..., ge=0)
    badge_id: Optional[UUID] = None
    reason: Optional[str] = Field(None, max_length=1000)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ReputationHistoryCreate(BaseModel):
    """Create reputation history entry request."""

    member_id: str = Field(..., min_length=1, max_length=255)
    action: str = Field(..., min_length=1, max_length=255)
    score_change: int = Field(...)
    previous_score: int = Field(..., ge=0)
    new_score: int = Field(..., ge=0)
    badge_id: Optional[UUID] = None
    reason: Optional[str] = Field(None, max_length=1000)
    metadata: Optional[Dict[str, Any]] = None


class ReputationExplanation(BaseModel):
    """Reputation explanation model."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(default_factory=uuid4)
    member_id: str = Field(..., min_length=1, max_length=255)
    explanation: str = Field(..., max_length=5000)
    factors: List[Dict[str, Any]] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ReputationExplanationCreate(BaseModel):
    """Create reputation explanation request."""

    member_id: str = Field(..., min_length=1, max_length=255)
    explanation: str = Field(..., max_length=5000)
    factors: Optional[List[Dict[str, Any]]] = None
    recommendations: Optional[List[str]] = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str = "0.1.0"
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ErrorResponse(BaseModel):
    """Error response model."""

    error: str
    detail: Optional[str] = None
    code: Optional[str] = None
