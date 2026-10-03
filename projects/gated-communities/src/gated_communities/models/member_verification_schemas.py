"""Pydantic models for member verification service."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator

# ─── Enums ────────────────────────────────────────────────────────────────────


class VerificationStatus(StrEnum):
    """Verification status enumeration."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    VERIFIED = "verified"
    REJECTED = "rejected"
    NEEDS_REVIEW = "needs_review"
    EXPIRED = "expired"


class RiskLevel(StrEnum):
    """Risk level enumeration."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DocumentType(StrEnum):
    """Document type enumeration."""

    PASSPORT = "passport"
    DRIVERS_LICENSE = "drivers_license"
    NATIONAL_ID = "national_id"
    UTILITY_BILL = "utility_bill"
    BANK_STATEMENT = "bank_statement"


class FraudType(StrEnum):
    """Fraud type enumeration."""

    IDENTITY_THEFT = "identity_theft"
    DOCUMENT_FORGERY = "document_forgery"
    ACCOUNT_TAKEOVER = "account_takeover"
    SYNTHETIC_IDENTITY = "synthetic_identity"
    COLLUSION = "collusion"


# ─── Request Models ───────────────────────────────────────────────────────────


class IdentityData(BaseModel):
    """Identity data for verification."""

    model_config = ConfigDict(extra="forbid")

    full_name: str = Field(
        ..., min_length=1, max_length=200, description="Full legal name"
    )
    date_of_birth: str = Field(
        ..., description="Date of birth in ISO format (YYYY-MM-DD)"
    )
    email: str = Field(..., description="Email address")
    phone: str | None = Field(default=None, description="Phone number")
    address: str | None = Field(default=None, description="Physical address")
    government_id: str | None = Field(
        default=None, description="Government-issued ID number"
    )

    @field_validator("date_of_birth")
    @classmethod
    def validate_dob(cls, v: str) -> str:
        """Validate date of birth format."""
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError as exc:
            raise ValueError("date_of_birth must be in YYYY-MM-DD format") from exc
        return v


class DocumentData(BaseModel):
    """Document data for verification."""

    model_config = ConfigDict(extra="forbid")

    document_type: DocumentType = Field(..., description="Type of document")
    document_number: str = Field(..., min_length=1, description="Document number")
    issuing_country: str = Field(
        ..., min_length=2, max_length=2, description="ISO 3166-1 alpha-2 country code"
    )
    issue_date: str | None = Field(default=None, description="Document issue date")
    expiry_date: str | None = Field(default=None, description="Document expiry date")
    document_hash: str | None = Field(
        default=None, description="SHA-256 hash of document image"
    )


class VerificationRequest(BaseModel):
    """Request model for member verification."""

    model_config = ConfigDict(extra="forbid")

    request_id: UUID = Field(
        default_factory=uuid4, description="Unique request identifier"
    )
    member_id: str = Field(
        ..., min_length=1, max_length=100, description="Community member identifier"
    )
    identity: IdentityData = Field(..., description="Identity information")
    documents: list[DocumentData] = Field(
        default_factory=list, description="Supporting documents"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )
    callback_url: str | None = Field(default=None, description="Webhook callback URL")
    priority: Literal["low", "normal", "high", "urgent"] = Field(
        default="normal", description="Processing priority"
    )


class TrustScoreRequest(BaseModel):
    """Request model for trust score calculation."""

    model_config = ConfigDict(extra="forbid")

    member_id: str = Field(..., min_length=1, description="Member identifier")
    include_history: bool = Field(default=True, description="Include historical data")
    factors: list[str] | None = Field(
        default=None, description="Specific factors to evaluate"
    )


class FraudCheckRequest(BaseModel):
    """Request model for fraud check."""

    model_config = ConfigDict(extra="forbid")

    member_id: str = Field(..., min_length=1, description="Member identifier")
    identity: IdentityData = Field(..., description="Identity to check")
    check_depth: Literal["basic", "standard", "deep"] = Field(
        default="standard", description="Depth of fraud check"
    )


class DocumentVerifyRequest(BaseModel):
    """Request model for document verification."""

    model_config = ConfigDict(extra="forbid")

    member_id: str = Field(..., min_length=1, description="Member identifier")
    document: DocumentData = Field(..., description="Document to verify")
    cross_reference: bool = Field(
        default=True, description="Cross-reference with identity data"
    )


class ExplanationRequest(BaseModel):
    """Request model for verification explanation."""

    model_config = ConfigDict(extra="forbid")

    request_id: UUID = Field(..., description="Verification request ID")
    detail_level: Literal["summary", "detailed", "technical"] = Field(
        default="detailed", description="Level of detail in explanation"
    )


# ─── Response Models ──────────────────────────────────────────────────────────


class VerificationResult(BaseModel):
    """Result of a verification request."""

    model_config = ConfigDict(extra="forbid")

    request_id: UUID = Field(..., description="Original request identifier")
    member_id: str = Field(..., description="Member identifier")
    status: VerificationStatus = Field(..., description="Verification status")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    trust_score: float = Field(
        ..., ge=0.0, le=1.0, description="Associated trust score"
    )
    fraud_risk: float = Field(..., ge=0.0, le=1.0, description="Fraud risk score")
    risk_level: RiskLevel = Field(..., description="Overall risk level")
    verified_at: datetime = Field(
        default_factory=datetime.utcnow, description="Verification timestamp"
    )
    expires_at: datetime | None = Field(
        default=None, description="Result expiration time"
    )
    checks_performed: list[str] = Field(
        default_factory=list, description="List of checks performed"
    )
    failure_reasons: list[str] = Field(
        default_factory=list, description="Reasons for failure if rejected"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional result metadata"
    )


class TrustScore(BaseModel):
    """Trust score result."""

    model_config = ConfigDict(extra="forbid")

    member_id: str = Field(..., description="Member identifier")
    score: float = Field(..., ge=0.0, le=1.0, description="Trust score from 0 to 1")
    level: RiskLevel = Field(..., description="Trust level")
    factors: dict[str, float] = Field(
        default_factory=dict, description="Factor breakdown"
    )
    history: list[dict[str, Any]] = Field(
        default_factory=list, description="Historical scores"
    )
    calculated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Calculation timestamp"
    )
    next_review_at: datetime | None = Field(
        default=None, description="Next review date"
    )


class FraudReport(BaseModel):
    """Fraud check report."""

    model_config = ConfigDict(extra="forbid")

    member_id: str = Field(..., description="Member identifier")
    risk_score: float = Field(
        ..., ge=0.0, le=1.0, description="Overall fraud risk score"
    )
    risk_level: RiskLevel = Field(..., description="Fraud risk level")
    flags: list[dict[str, Any]] = Field(
        default_factory=list, description="Fraud indicators found"
    )
    matched_patterns: list[str] = Field(
        default_factory=list, description="Matched fraud patterns"
    )
    recommendation: Literal["allow", "review", "block"] = Field(
        ..., description="Recommended action"
    )
    checked_at: datetime = Field(
        default_factory=datetime.utcnow, description="Check timestamp"
    )
    check_depth: str = Field(..., description="Depth of check performed")


class DocumentVerificationResult(BaseModel):
    """Document verification result."""

    model_config = ConfigDict(extra="forbid")

    document_type: DocumentType = Field(..., description="Type of document verified")
    is_authentic: bool = Field(..., description="Whether document appears authentic")
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence in assessment"
    )
    tampering_detected: bool = Field(
        default=False, description="Whether tampering was detected"
    )
    expiry_status: Literal["valid", "expired", "expiring_soon", "unknown"] = Field(
        default="unknown", description="Document expiry status"
    )
    cross_reference_match: bool | None = Field(
        default=None, description="Whether document matches identity data"
    )
    issues: list[str] = Field(
        default_factory=list, description="Issues found with document"
    )
    verified_at: datetime = Field(
        default_factory=datetime.utcnow, description="Verification timestamp"
    )


class VerificationExplanation(BaseModel):
    """Explanation of a verification decision."""

    model_config = ConfigDict(extra="forbid")

    request_id: UUID = Field(..., description="Verification request ID")
    summary: str = Field(..., description="Human-readable summary")
    factors: list[dict[str, Any]] = Field(
        default_factory=list, description="Decision factors"
    )
    recommendations: list[str] = Field(
        default_factory=list, description="Recommendations for member"
    )
    appeal_process: str | None = Field(
        default=None, description="How to appeal the decision"
    )
    generated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Generation timestamp"
    )
    detail_level: str = Field(..., description="Detail level of explanation")


class AgentInfo(BaseModel):
    """Information about an agent."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., description="Agent name")
    description: str = Field(..., description="Agent description")
    status: Literal["available", "busy", "error", "disabled"] = Field(
        ..., description="Current agent status"
    )
    capabilities: list[str] = Field(
        default_factory=list, description="Agent capabilities"
    )
    last_used: datetime | None = Field(default=None, description="Last usage timestamp")


class HealthResponse(BaseModel):
    """Health check response."""

    model_config = ConfigDict(extra="forbid")

    status: str = Field(..., description="Service status")
    version: str = Field(..., description="Service version")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Response timestamp"
    )
    checks: dict[str, bool] = Field(
        default_factory=dict, description="Component health checks"
    )


class ErrorResponse(BaseModel):
    """Standard error response."""

    model_config = ConfigDict(extra="forbid")

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: dict[str, Any] | None = Field(
        default=None, description="Additional error details"
    )
    request_id: UUID | None = Field(
        default=None, description="Request identifier for tracking"
    )
