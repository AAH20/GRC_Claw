"""Pydantic models for the rights-management service."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class LicenseType(str, Enum):
    """Supported license types."""

    CC0 = "CC0"
    CC_BY = "CC_BY"
    CC_BY_SA = "CC_BY_SA"
    CC_BY_NC = "CC_BY_NC"
    CC_BY_ND = "CC_BY_ND"
    CC_BY_NC_SA = "CC_BY_NC_SA"
    CC_BY_NC_ND = "CC_BY_NC_ND"
    PROPRIETARY = "PROPRIETARY"
    CUSTOM = "CUSTOM"


class LicenseStatus(str, Enum):
    """License lifecycle status."""

    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    PENDING = "pending"


class License(BaseModel):
    """Content license definition."""

    id: str = Field(..., description="Unique license identifier")
    content_id: str = Field(..., description="Identifier of the licensed content")
    license_type: LicenseType = Field(..., description="Type of license")
    holder: str = Field(..., description="License holder name or organization")
    status: LicenseStatus = Field(default=LicenseStatus.ACTIVE)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime | None = Field(default=None)
    terms: dict[str, Any] = Field(default_factory=dict, description="License-specific terms")
    metadata: dict[str, Any] = Field(default_factory=dict)


class LicenseCreate(BaseModel):
    """Request model for creating a license."""

    content_id: str
    license_type: LicenseType
    holder: str
    expires_at: datetime | None = None
    terms: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class LicenseDetectionRequest(BaseModel):
    """Request model for license detection."""

    content_id: str
    content_text: str | None = None
    content_url: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class LicenseDetectionResult(BaseModel):
    """Result of license detection."""

    content_id: str
    detected_license: LicenseType | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[str] = Field(default_factory=list)
    matched_license_id: str | None = None


class UsageType(str, Enum):
    """Types of content usage."""

    VIEW = "view"
    DOWNLOAD = "download"
    REPRODUCE = "reproduce"
    DISTRIBUTE = "distribute"
    MODIFY = "modify"
    COMMERCIAL = "commercial"


class UsageRecord(BaseModel):
    """Record of content usage."""

    id: str
    content_id: str
    usage_type: UsageType
    user_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    context: dict[str, Any] = Field(default_factory=dict)
    license_id: str | None = None


class UsageRecordCreate(BaseModel):
    """Request model for recording usage."""

    content_id: str
    usage_type: UsageType
    user_id: str
    context: dict[str, Any] = Field(default_factory=dict)
    license_id: str | None = None


class UsageSummary(BaseModel):
    """Aggregated usage statistics for a piece of content."""

    content_id: str
    total_uses: int
    by_type: dict[str, int]
    unique_users: int
    first_used: datetime | None = None
    last_used: datetime | None = None


class InfringementSeverity(str, Enum):
    """Severity levels for infringement reports."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class InfringementStatus(str, Enum):
    """Status of an infringement report."""

    OPEN = "open"
    UNDER_REVIEW = "under_review"
    CONFIRMED = "confirmed"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class InfringementReport(BaseModel):
    """Report of potential content infringement."""

    id: str
    content_id: str
    reporter_id: str
    description: str
    severity: InfringementSeverity
    status: InfringementStatus = Field(default=InfringementStatus.OPEN)
    evidence_urls: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class InfringementReportCreate(BaseModel):
    """Request model for filing an infringement report."""

    content_id: str
    reporter_id: str
    description: str
    severity: InfringementSeverity = InfringementSeverity.MEDIUM
    evidence_urls: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class InfringementDetectionRequest(BaseModel):
    """Request model for automated infringement detection."""

    content_id: str
    content_text: str | None = None
    content_url: str | None = None
    reference_content_ids: list[str] = Field(default_factory=list)


class InfringementDetectionResult(BaseModel):
    """Result of automated infringement detection."""

    content_id: str
    potential_infringements: list[dict[str, Any]] = Field(default_factory=list)
    risk_score: float = Field(ge=0.0, le=1.0)
    recommendations: list[str] = Field(default_factory=list)


class ValidationStatus(str, Enum):
    """Outcome of a rights validation check."""

    VALID = "valid"
    INVALID = "invalid"
    EXPIRED = "expired"
    REVOKED = "revoked"
    UNKNOWN = "unknown"


class RightsValidation(BaseModel):
    """Result of validating content usage against its license."""

    id: str
    content_id: str
    usage_type: UsageType
    license_id: str | None
    status: ValidationStatus
    reason: str | None = None
    validated_at: datetime = Field(default_factory=datetime.utcnow)
    details: dict[str, Any] = Field(default_factory=dict)


class RightsValidationRequest(BaseModel):
    """Request model for rights validation."""

    content_id: str
    usage_type: UsageType
    user_id: str
    context: dict[str, Any] = Field(default_factory=dict)


class TakedownStatus(str, Enum):
    """Status of a takedown request."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"


class TakedownRequest(BaseModel):
    """Request to take down infringing content."""

    id: str
    content_id: str
    requester_id: str
    reason: str
    legal_basis: str | None = None
    status: TakedownStatus = Field(default=TakedownStatus.PENDING)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    processed_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class TakedownRequestCreate(BaseModel):
    """Request model for submitting a takedown request."""

    content_id: str
    requester_id: str
    reason: str
    legal_basis: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class TakedownProcessRequest(BaseModel):
    """Request model for processing a takedown request."""

    action: TakedownStatus
    reviewer_id: str
    notes: str | None = None
