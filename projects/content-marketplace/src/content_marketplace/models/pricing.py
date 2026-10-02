"""Pricing models for content marketplace."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class PricingStrategy(str, Enum):
    """Pricing strategy types."""

    FIXED = "fixed"
    DYNAMIC = "dynamic"
    AUCTION = "auction"
    SUBSCRIPTION = "subscription"
    USAGE_BASED = "usage_based"


class PricingCreate(BaseModel):
    """Schema for creating a pricing entry."""

    listing_id: UUID = Field(..., description="Associated listing ID")
    strategy: PricingStrategy = Field(default=PricingStrategy.FIXED)
    base_price: float = Field(..., gt=0, description="Base price")
    currency: str = Field(default="USD", min_length=3, max_length=3)
    min_price: float | None = Field(default=None, gt=0, description="Minimum acceptable price")
    max_price: float | None = Field(default=None, gt=0, description="Maximum price cap")
    demand_multiplier: float = Field(default=1.0, ge=0.1, le=10.0)
    competitor_price: float | None = Field(default=None, gt=0)
    metadata: dict[str, str] = Field(default_factory=dict)


class PricingUpdate(BaseModel):
    """Schema for updating a pricing entry."""

    strategy: PricingStrategy | None = None
    base_price: float | None = Field(default=None, gt=0)
    min_price: float | None = Field(default=None, gt=0)
    max_price: float | None = Field(default=None, gt=0)
    demand_multiplier: float | None = Field(default=None, ge=0.1, le=10.0)
    competitor_price: float | None = Field(default=None, gt=0)
    metadata: dict[str, str] | None = None


class Pricing(BaseModel):
    """Full pricing model with all fields."""

    id: UUID = Field(default_factory=uuid4)
    listing_id: UUID
    strategy: PricingStrategy = PricingStrategy.FIXED
    base_price: float
    currency: str = "USD"
    min_price: float | None = None
    max_price: float | None = None
    demand_multiplier: float = 1.0
    competitor_price: float | None = None
    final_price: float = Field(..., description="Computed final price after strategy")
    metadata: dict[str, str] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True
