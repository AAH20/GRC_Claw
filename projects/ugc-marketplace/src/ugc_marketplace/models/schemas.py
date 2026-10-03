"""Pydantic models for UGC Marketplace."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class ContentType(str, Enum):
    """Supported content types for moderation."""

    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"


class ModerationAction(str, Enum):
    """Possible moderation actions."""

    ALLOW = "allow"
    FLAG = "flag"
    BLOCK = "block"
    ESCALATE = "escalate"


class PolicySeverity(str, Enum):
    """Policy violation severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AppealStatus(str, Enum):
    """Appeal processing status."""

    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"


class ModerationRequest(BaseModel):
    """Request model for content moderation."""

    content: str = Field(
        ..., min_length=1, max_length=100_000, description="Content to moderate"
    )
    content_type: ContentType = Field(..., description="Type of content")
    user_id: str | None = Field(None, description="User identifier")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )
    callback_url: str | None = Field(None, description="Webhook for async results")


class ModerationResult(BaseModel):
    """Result model for content moderation."""

    id: UUID = Field(default_factory=uuid4)
    request_id: UUID = Field(default_factory=uuid4)
    content_type: ContentType
    action: ModerationAction
    confidence: float = Field(..., ge=0.0, le=1.0)
    categories: list[str] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)
    policy_violations: list[str] = Field(default_factory=list)
    processing_time_ms: float = Field(default=0.0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    agent_trace: dict[str, Any] | None = None


class BatchModerationRequest(BaseModel):
    """Request model for batch content moderation."""

    items: list[ModerationRequest] = Field(..., min_length=1, max_length=100)
    priority: str = Field(default="normal", pattern="^(low|normal|high)$")


class BatchModerationResult(BaseModel):
    """Result model for batch content moderation."""

    batch_id: UUID = Field(default_factory=uuid4)
    results: list[ModerationResult]
    total_processed: int
    total_flagged: int
    total_blocked: int


class PolicyRule(BaseModel):
    """Individual rule within a policy."""

    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(default="")
    pattern: str = Field(..., min_length=1)
    severity: PolicySeverity
    action: ModerationAction
    enabled: bool = True


class Policy(BaseModel):
    """Content moderation policy."""

    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(default="")
    rules: list[PolicyRule] = Field(default_factory=list)
    content_types: list[ContentType] = Field(default_factory=list)
    enabled: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class AppealSubmission(BaseModel):
    """Request model for submitting an appeal."""

    moderation_result_id: UUID
    user_id: str = Field(..., min_length=1)
    reason: str = Field(..., min_length=10, max_length=5000)
    evidence: dict[str, Any] = Field(default_factory=dict)


class Appeal(BaseModel):
    """Appeal model representing a moderation appeal."""

    id: UUID = Field(default_factory=uuid4)
    moderation_result_id: UUID
    user_id: str
    reason: str
    evidence: dict[str, Any] = Field(default_factory=dict)
    status: AppealStatus = AppealStatus.PENDING
    reviewer_notes: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: datetime | None = None


class ScoreDimension(str, Enum):
    """Quality scoring dimensions."""

    READABILITY = "readability"
    ORIGINALITY = "originality"
    ENGAGEMENT = "engagement"
    SEO = "seo"


class ScoreLevel(str, Enum):
    """Quality score levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class DimensionScore(BaseModel):
    """Score for a single quality dimension."""

    dimension: ScoreDimension
    score: float = Field(..., ge=0.0, le=1.0)
    level: ScoreLevel


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str = Field(..., description="Service status")
    version: str = Field(..., description="Service version")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Response timestamp"
    )


# ── Marketplace models ──────────────────────────────────────────────────────


class ListingStatus(str, Enum):
    """Listing status values."""

    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
    SOLD = "sold"
    REMOVED = "removed"


class ListingCreate(BaseModel):
    """Request model for creating a listing."""

    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(default="")
    seller_id: str = Field(..., min_length=1)
    category: str = Field(..., min_length=1)
    tags: list[str] = Field(default_factory=list)


class ListingUpdate(BaseModel):
    """Request model for updating a listing."""

    title: str | None = None
    description: str | None = None
    status: ListingStatus | None = None


class Listing(BaseModel):
    """Marketplace listing model."""

    listing_id: str
    title: str
    description: str = ""
    seller_id: str
    category: str
    tags: list[str] = Field(default_factory=list)
    status: ListingStatus = ListingStatus.DRAFT


class TransactionStatus(str, Enum):
    """Transaction status values."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    REFUNDED = "refunded"


class TransactionCreate(BaseModel):
    """Request model for creating a transaction."""

    listing_id: str = Field(..., min_length=1)
    buyer_id: str = Field(..., min_length=1)
    seller_id: str = Field(..., min_length=1)
    amount: float = Field(..., gt=0)
    currency: str = Field(default="USD")


class Transaction(BaseModel):
    """Transaction model."""

    transaction_id: str
    listing_id: str
    buyer_id: str
    seller_id: str
    amount: float
    currency: str = "USD"
    status: TransactionStatus = TransactionStatus.PENDING


class PricingCreate(BaseModel):
    """Request model for creating pricing."""

    listing_id: str = Field(..., min_length=1)
    base_price: float = Field(..., gt=0)
    currency: str = Field(default="USD")


class Pricing(BaseModel):
    """Pricing model."""

    pricing_id: str
    listing_id: str
    base_price: float
    currency: str = "USD"


class TrustLevel(str, Enum):
    """Trust level values."""

    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    VERIFIED = "verified"


class TrustScoreCreate(BaseModel):
    """Request model for creating a trust score."""

    user_id: str = Field(..., min_length=1)


class TrustScore(BaseModel):
    """Trust score model."""

    user_id: str
    score: float = Field(default=0.5, ge=0.0, le=1.0)
    level: TrustLevel = TrustLevel.BRONZE
    factors: dict[str, Any] = Field(default_factory=dict)


class MarketplaceAnalytics(BaseModel):
    """Marketplace analytics report model."""

    report_id: str
    period_start: datetime
    period_end: datetime
    total_listings: int = 0
    total_transactions: int = 0
    total_volume: float = 0.0
    average_price: float = 0.0
    top_categories: list[str] = Field(default_factory=list)
    insights: list[str] = Field(default_factory=list)


class MarketplaceInsight(BaseModel):
    """Marketplace insight model."""

    insight_id: str
    category: str
    title: str
    description: str
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    impact: str = "medium"


class DemandPrediction(BaseModel):
    """Demand prediction model."""

    category: str
    predicted_demand: float = Field(default=0.5, ge=0.0, le=1.0)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    factors: list[str] = Field(default_factory=list)


# ── Fraud detection models ──────────────────────────────────────────────────


class RiskLevel(str, Enum):
    """Risk level values."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskFactor(BaseModel):
    """Risk factor model."""

    name: str
    contribution: float = Field(default=0.0, ge=0.0, le=1.0)
    description: str = ""


class RiskScore(BaseModel):
    """Risk score model."""

    score_id: str
    transaction_id: str
    overall_score: float = Field(default=0.5, ge=0.0, le=1.0)
    factors: list[RiskFactor] = Field(default_factory=list)


class Anomaly(BaseModel):
    """Anomaly model."""

    transaction_id: str
    anomaly_type: str
    severity: str = "medium"
    score: float = Field(default=0.5, ge=0.0, le=1.0)
    description: str = ""
    detected_at: datetime = Field(default_factory=datetime.utcnow)


class Pattern(BaseModel):
    """Pattern model."""

    pattern_type: str
    transaction_ids: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    description: str = ""
    detected_at: datetime = Field(default_factory=datetime.utcnow)


class AccountAnalysis(BaseModel):
    """Account analysis model."""

    user_id: str
    risk_score: float = Field(default=0.5, ge=0.0, le=1.0)
    anomalies: list[Anomaly] = Field(default_factory=list)
    patterns: list[Pattern] = Field(default_factory=list)
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)


# ── Quality scoring models ──────────────────────────────────────────────────


class ImprovementSuggestion(BaseModel):
    """Improvement suggestion model."""

    id: UUID = Field(default_factory=uuid4)
    category: str
    title: str
    description: str
    priority: str = "medium"


class ImprovementPlan(BaseModel):
    """Improvement plan model."""

    content_id: str
    current_score: float = Field(default=0.0, ge=0.0, le=1.0)
    target_score: float = Field(default=1.0, ge=0.0, le=1.0)
    recommendations: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class QualityAssessment(BaseModel):
    """Quality assessment model."""

    content_id: str
    overall_score: float = Field(default=0.0, ge=0.0, le=1.0)
    quality_level: str = "medium"
    passed: bool = False
    issues: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    assessed_at: datetime = Field(default_factory=datetime.utcnow)


# ── Content discovery models ─────────────────────────────────────────────────


class SearchRequest(BaseModel):
    """Search request model."""

    query: str = Field(..., min_length=1)
    user_id: str | None = None
    filters: dict[str, Any] = Field(default_factory=dict)
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class SearchResponse(BaseModel):
    """Search response model."""

    results: list[dict[str, Any]] = Field(default_factory=list)
    total_count: int = 0
    query_time_ms: float = 0.0
    facets: dict[str, Any] = Field(default_factory=dict)


class RecommendationRequest(BaseModel):
    """Recommendation request model."""

    user_id: str = Field(..., min_length=1)
    context: dict[str, Any] = Field(default_factory=dict)
    limit: int = Field(default=10, ge=1, le=50)


class RecommendationResponse(BaseModel):
    """Recommendation response model."""

    recommendations: list[dict[str, Any]] = Field(default_factory=list)
    total_count: int = 0


class TrendRequest(BaseModel):
    """Trend request model."""

    category: str | None = None
    timeframe: str = "7d"


class TrendResponse(BaseModel):
    """Trend response model."""

    trends: list[dict[str, Any]] = Field(default_factory=list)
    total_count: int = 0
