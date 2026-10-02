"""Trust score models for content marketplace."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class TrustLevel(str, Enum):
    """Trust level classification."""

    UNTRUSTED = "untrusted"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERIFIED = "verified"


class TrustScoreCreate(BaseModel):
    """Schema for creating a trust score."""

    user_id: str = Field(..., min_length=1, description="User identifier")
    transaction_count: int = Field(default=0, ge=0)
    successful_transactions: int = Field(default=0, ge=0)
    dispute_count: int = Field(default=0, ge=0)
    average_rating: float = Field(default=0.0, ge=0.0, le=5.0)
    account_age_days: int = Field(default=0, ge=0)
    verification_status: bool = False


class TrustScore(BaseModel):
    """Full trust score model with all fields."""

    id: UUID = Field(default_factory=uuid4)
    user_id: str
    score: float = Field(..., ge=0.0, le=1.0, description="Trust score between 0 and 1")
    level: TrustLevel
    transaction_count: int = 0
    successful_transactions: int = 0
    dispute_count: int = 0
    average_rating: float = 0.0
    account_age_days: int = 0
    verification_status: bool = False
    risk_factors: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True
