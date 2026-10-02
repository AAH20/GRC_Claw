"""Pydantic schemas for Creator Monetization Platform."""
from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class TierLevel(StrEnum):
    """Creator tier levels."""

    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"
    DIAMOND = "diamond"


class PayoutStatus(StrEnum):
    """Status of a payout."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class SubscriptionStatus(StrEnum):
    """Status of a subscription."""

    ACTIVE = "active"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    PAST_DUE = "past_due"
    TRIALING = "trialing"


class MonetizationPlan(BaseModel):
    """A creator's monetization plan with revenue strategies."""

    plan_id: str = Field(..., description="Unique plan identifier")
    creator_id: str = Field(..., description="Creator identifier")
    name: str = Field(..., min_length=1, max_length=200, description="Plan name")
    description: str = Field(default="", max_length=5000)
    strategies: list[str] = Field(default_factory=list, description="Revenue strategies")
    target_monthly_revenue: Decimal = Field(default=Decimal("0"), ge=0)
    current_monthly_revenue: Decimal = Field(default=Decimal("0"), ge=0)
    currency: str = Field(default="USD", description="Currency code")
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = Field(default_factory=dict)


class Payout(BaseModel):
    """Represents a payout to a creator."""

    payout_id: str = Field(..., description="Unique payout identifier")
    creator_id: str = Field(..., description="Creator identifier")
    amount: Decimal = Field(..., gt=0, description="Payout amount")
    currency: str = Field(default="USD", description="Currency code")
    status: PayoutStatus = Field(default=PayoutStatus.PENDING)
    period_start: datetime = Field(..., description="Payout period start")
    period_end: datetime = Field(..., description="Payout period end")
    payment_method: str = Field(default="bank_transfer", description="Payment method")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    paid_at: datetime | None = Field(default=None, description="When payout was completed")
    metadata: dict[str, Any] = Field(default_factory=dict)


class PayoutCreate(BaseModel):
    """Request model for creating a payout."""

    creator_id: str = Field(..., description="Creator identifier")
    amount: Decimal = Field(..., gt=0, description="Payout amount")
    currency: str = Field(default="USD")
    period_start: datetime = Field(..., description="Payout period start")
    period_end: datetime = Field(..., description="Payout period end")
    payment_method: str = Field(default="bank_transfer")


class Tier(BaseModel):
    """Creator tier with benefits and thresholds."""

    tier_id: str = Field(..., description="Unique tier identifier")
    name: str = Field(..., min_length=1, max_length=100)
    level: TierLevel = Field(..., description="Tier level")
    monthly_price: Decimal = Field(..., ge=0, description="Monthly subscription price")
    yearly_price: Decimal = Field(..., ge=0, description="Yearly subscription price")
    benefits: list[str] = Field(default_factory=list)
    min_subscribers: int = Field(default=0, ge=0)
    max_subscribers: int | None = Field(default=None, ge=0)
    revenue_share: Decimal = Field(default=Decimal("0.10"), ge=0, le=1)
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class TierCreate(BaseModel):
    """Request model for creating a tier."""

    name: str = Field(..., min_length=1, max_length=100)
    level: TierLevel = Field(..., description="Tier level")
    monthly_price: Decimal = Field(..., ge=0)
    yearly_price: Decimal = Field(..., ge=0)
    benefits: list[str] = Field(default_factory=list)
    min_subscribers: int = Field(default=0, ge=0)
    max_subscribers: int | None = Field(default=None, ge=0)
    revenue_share: Decimal = Field(default=Decimal("0.10"), ge=0, le=1)


class Subscription(BaseModel):
    """A subscriber's subscription to a creator tier."""

    subscription_id: str = Field(..., description="Unique subscription identifier")
    creator_id: str = Field(..., description="Creator identifier")
    subscriber_id: str = Field(..., description="Subscriber identifier")
    tier_id: str = Field(..., description="Tier identifier")
    status: SubscriptionStatus = Field(default=SubscriptionStatus.ACTIVE)
    start_date: datetime = Field(..., description="Subscription start date")
    end_date: datetime | None = Field(default=None, description="Subscription end date")
    auto_renew: bool = True
    amount: Decimal = Field(..., gt=0, description="Subscription amount")
    currency: str = Field(default="USD")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = Field(default_factory=dict)


class SubscriptionCreate(BaseModel):
    """Request model for creating a subscription."""

    creator_id: str = Field(..., description="Creator identifier")
    subscriber_id: str = Field(..., description="Subscriber identifier")
    tier_id: str = Field(..., description="Tier identifier")
    amount: Decimal = Field(..., gt=0)
    currency: str = Field(default="USD")
    auto_renew: bool = True


class RevenueReport(BaseModel):
    """Revenue analytics report for a creator."""

    report_id: str = Field(..., description="Unique report identifier")
    creator_id: str = Field(..., description="Creator identifier")
    period_start: datetime = Field(..., description="Report period start")
    period_end: datetime = Field(..., description="Report period end")
    total_revenue: Decimal = Field(default=Decimal("0"), ge=0)
    subscription_revenue: Decimal = Field(default=Decimal("0"), ge=0)
    tip_revenue: Decimal = Field(default=Decimal("0"), ge=0)
    merchandise_revenue: Decimal = Field(default=Decimal("0"), ge=0)
    sponsorship_revenue: Decimal = Field(default=Decimal("0"), ge=0)
    other_revenue: Decimal = Field(default=Decimal("0"), ge=0)
    subscriber_count: int = Field(default=0, ge=0)
    active_subscribers: int = Field(default=0, ge=0)
    churned_subscribers: int = Field(default=0, ge=0)
    currency: str = Field(default="USD")
    insights: list[str] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))