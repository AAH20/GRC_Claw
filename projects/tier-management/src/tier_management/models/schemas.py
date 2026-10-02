"""Pydantic models for tier management domain objects."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TierLevel(StrEnum):
    """Enumeration of available tier levels."""

    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"
    DIAMOND = "diamond"


class TierStatus(StrEnum):
    """Enumeration of possible tier statuses."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"
    EXPIRED = "expired"


class AccessDecision(StrEnum):
    """Enumeration of access control decisions."""

    GRANTED = "granted"
    DENIED = "denied"
    PENDING_REVIEW = "pending_review"
    CONDITIONAL = "conditional"


class UpgradeEligibility(StrEnum):
    """Enumeration of upgrade eligibility statuses."""

    ELIGIBLE = "eligible"
    NOT_ELIGIBLE = "not_eligible"
    PENDING = "pending"
    COOLDOWN = "cooldown"
    MAX_TIER = "max_tier"


class BenefitType(StrEnum):
    """Enumeration of benefit types."""

    PERCENTAGE_DISCOUNT = "percentage_discount"
    FIXED_DISCOUNT = "fixed_discount"
    FREE_SHIPPING = "free_shipping"
    PRIORITY_SUPPORT = "priority_support"
    EXCLUSIVE_ACCESS = "exclusive_access"
    BONUS_CREDITS = "bonus_credits"


class Tier(BaseModel):
    """Represents a membership tier in the gated community.

    A tier defines the level of access, benefits, and requirements
    for community members.
    """

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    id: UUID = Field(default_factory=uuid4, description="Unique tier identifier")
    name: str = Field(..., min_length=1, max_length=100, description="Tier display name")
    level: TierLevel = Field(..., description="Tier level in the hierarchy")
    status: TierStatus = Field(default=TierStatus.ACTIVE, description="Current tier status")
    description: str | None = Field(default=None, max_length=500, description="Tier description")
    requirements: dict[str, Any] = Field(
        default_factory=dict,
        description="Requirements to achieve this tier",
    )
    benefits: list[str] = Field(default_factory=list, description="List of benefit identifiers")
    max_members: int | None = Field(default=None, ge=1, description="Maximum members allowed")
    monthly_fee: float = Field(default=0.0, ge=0, description="Monthly subscription fee")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Creation timestamp",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Last update timestamp",
    )
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate tier name is not empty after stripping."""
        stripped = v.strip()
        if not stripped:
            raise ValueError("Tier name cannot be empty")
        return stripped


class TierEvaluation(BaseModel):
    """Result of evaluating a member against tier requirements.

    Produced by the TierEvaluatorAgent after analyzing member
    activity, contributions, and engagement metrics.
    """

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    id: UUID = Field(default_factory=uuid4, description="Unique evaluation identifier")
    member_id: UUID = Field(..., description="Member being evaluated")
    current_tier_id: UUID = Field(..., description="Member's current tier")
    target_tier_id: UUID = Field(..., description="Tier being evaluated for")
    eligible: bool = Field(..., description="Whether member meets requirements")
    score: float = Field(..., ge=0.0, le=100.0, description="Evaluation score (0-100)")
    criteria_results: dict[str, Any] = Field(
        default_factory=dict,
        description="Per-criterion evaluation results",
    )
    gaps: list[str] = Field(default_factory=list, description="Unmet requirements")
    recommendations: list[str] = Field(
        default_factory=list,
        description="Suggestions to improve eligibility",
    )
    evaluated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Evaluation timestamp",
    )
    evaluated_by: str = Field(
        default="TierEvaluatorAgent", description="Agent that performed evaluation"
    )
    confidence: float = Field(default=0.8, ge=0.0, le=1.0, description="Evaluation confidence")


class UpgradeRequest(BaseModel):
    """Request to upgrade a member to a higher tier.

    Created by the UpgradeRecommenderAgent or directly by members
    through the API.
    """

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    id: UUID = Field(default_factory=uuid4, description="Unique request identifier")
    member_id: UUID = Field(..., description="Member requesting upgrade")
    current_tier_id: UUID = Field(..., description="Member's current tier")
    target_tier_id: UUID = Field(..., description="Desired target tier")
    reason: str | None = Field(default=None, max_length=1000, description="Upgrade justification")
    eligibility: UpgradeEligibility = Field(
        default=UpgradeEligibility.PENDING,
        description="Current eligibility status",
    )
    status: str = Field(default="pending", description="Request status")
    requested_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Request timestamp",
    )
    processed_at: datetime | None = Field(default=None, description="Processing timestamp")
    processed_by: str | None = Field(default=None, description="Agent/admin who processed it")
    denial_reason: str | None = Field(default=None, description="Reason if denied")


class AccessPolicy(BaseModel):
    """Defines access control rules for a tier or resource.

    Created and managed by the AccessControllerAgent to enforce
    community gating rules.
    """

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    id: UUID = Field(default_factory=uuid4, description="Unique policy identifier")
    name: str = Field(..., min_length=1, max_length=200, description="Policy name")
    tier_id: UUID = Field(..., description="Tier this policy applies to")
    resource: str = Field(..., description="Resource being gated (e.g., 'forum', 'api')")
    action: str = Field(..., description="Action being controlled (e.g., 'read', 'write')")
    effect: AccessDecision = Field(..., description="Policy effect")
    conditions: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional conditions (time-based, quota, etc.)",
    )
    priority: int = Field(
        default=0, ge=0, le=100, description="Policy priority (higher = more important)"
    )
    enabled: bool = Field(default=True, description="Whether policy is active")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Creation timestamp",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Last update timestamp",
    )
    expires_at: datetime | None = Field(default=None, description="Policy expiration")


class Benefit(BaseModel):
    """Represents a benefit that can be assigned to a tier.

    Managed by the BenefitManagerAgent.
    """

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    id: UUID = Field(default_factory=uuid4, description="Unique benefit identifier")
    name: str = Field(..., min_length=1, max_length=200, description="Benefit name")
    benefit_type: BenefitType = Field(..., description="Type of benefit")
    description: str | None = Field(default=None, max_length=500, description="Benefit description")
    value: float = Field(default=0.0, description="Benefit value (discount %, amount, etc.)")
    tier_ids: list[UUID] = Field(default_factory=list, description="Tiers this benefit applies to")
    active: bool = Field(default=True, description="Whether benefit is active")
    start_date: datetime | None = Field(default=None, description="Benefit start date")
    end_date: datetime | None = Field(default=None, description="Benefit end date")
    usage_limit: int | None = Field(default=None, ge=1, description="Max uses per member")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class TierAnalytics(BaseModel):
    """Analytics data for tier performance and member behavior.

    Generated by the TierAnalyticsAgent for reporting and insights.
    """

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    id: UUID = Field(default_factory=uuid4, description="Unique analytics record identifier")
    tier_id: UUID = Field(..., description="Tier being analyzed")
    period_start: datetime = Field(..., description="Analysis period start")
    period_end: datetime = Field(..., description="Analysis period end")
    total_members: int = Field(default=0, ge=0, description="Total members in tier")
    active_members: int = Field(default=0, ge=0, description="Active members in tier")
    new_members: int = Field(default=0, ge=0, description="New members in period")
    churned_members: int = Field(default=0, ge=0, description="Members who left in period")
    upgrade_requests: int = Field(default=0, ge=0, description="Upgrade requests in period")
    downgrade_requests: int = Field(default=0, ge=0, description="Downgrade requests in period")
    avg_engagement_score: float = Field(
        default=0.0, ge=0.0, le=100.0, description="Average engagement"
    )
    revenue: float = Field(default=0.0, ge=0.0, description="Revenue generated in period")
    metrics: dict[str, Any] = Field(default_factory=dict, description="Additional metrics")
    insights: list[str] = Field(default_factory=list, description="Generated insights")
    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Generation timestamp",
    )
    generated_by: str = Field(default="TierAnalyticsAgent", description="Agent that generated this")


class AccessCheckRequest(BaseModel):
    """Request to check access for a member to a resource."""

    model_config = ConfigDict(from_attributes=True)

    member_id: UUID = Field(..., description="Member requesting access")
    resource: str = Field(..., description="Resource being accessed")
    action: str = Field(default="read", description="Action being performed")
    context: dict[str, Any] = Field(default_factory=dict, description="Additional context")


class AccessCheckResponse(BaseModel):
    """Response to an access check request."""

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    member_id: UUID = Field(..., description="Member identifier")
    resource: str = Field(..., description="Resource accessed")
    action: str = Field(..., description="Action performed")
    decision: AccessDecision = Field(..., description="Access decision")
    tier_id: UUID | None = Field(default=None, description="Member's tier at check time")
    reason: str | None = Field(default=None, description="Decision explanation")
    checked_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Check timestamp",
    )
    policy_id: UUID | None = Field(default=None, description="Policy that determined decision")


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str = Field(..., description="Service status")
    version: str = Field(..., description="Service version")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Response timestamp",
    )
    checks: dict[str, bool] = Field(default_factory=dict, description="Individual health checks")
