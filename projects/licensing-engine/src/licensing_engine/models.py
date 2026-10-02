"""Pydantic models for the licensing engine API."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

# ── Enums ────────────────────────────────────────────────────────────────────


class LicenseType(StrEnum):
    """Types of content licenses."""

    EXCLUSIVE = "exclusive"
    NON_EXCLUSIVE = "non_exclusive"
    PERPETUAL = "perpetual"
    TEMPORARY = "temporary"
    SUBSCRIPTION = "subscription"
    USAGE_BASED = "usage_based"


class LicenseStatus(StrEnum):
    """Status of a license."""

    DRAFT = "draft"
    PENDING = "pending"
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    SUSPENDED = "suspended"


class ContentType(StrEnum):
    """Types of licensable content."""

    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    SOFTWARE = "software"
    DATA = "data"
    MUSIC = "music"


class ComplianceStatus(StrEnum):
    """Compliance check status."""

    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PENDING_REVIEW = "pending_review"
    EXEMPT = "exempt"


class RiskLevel(StrEnum):
    """Risk assessment levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class NegotiationStatus(StrEnum):
    """Status of a negotiation."""

    INITIATED = "initiated"
    IN_PROGRESS = "in_progress"
    COUNTERED = "countered"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"


# ── Base Models ──────────────────────────────────────────────────────────────


class BaseSchema(BaseModel):
    """Base schema with common configuration."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class TimestampedSchema(BaseSchema):
    """Base schema with timestamps."""

    id: UUID = Field(default_factory=uuid4, description="Unique identifier")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation time")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update time")


# ── License Models ───────────────────────────────────────────────────────────


class LicenseTerms(BaseSchema):
    """Terms and conditions of a license."""

    usage_rights: list[str] = Field(default_factory=list, description="Permitted usage rights")
    restrictions: list[str] = Field(default_factory=list, description="Usage restrictions")
    territory: list[str] = Field(default_factory=list, description="Licensed territories")
    duration_days: int | None = Field(default=None, description="License duration in days")
    max_usage_count: int | None = Field(default=None, description="Maximum usage count")
    attribution_required: bool = Field(default=True, description="Whether attribution is required")
    commercial_use: bool = Field(default=False, description="Whether commercial use is allowed")
    sublicensable: bool = Field(default=False, description="Whether sublicensing is allowed")
    transferable: bool = Field(default=False, description="Whether license is transferable")
    custom_clauses: dict[str, Any] = Field(
        default_factory=dict, description="Custom license clauses"
    )


class LicenseCreate(BaseSchema):
    """Request model for creating a license."""

    content_id: str = Field(..., description="ID of the content being licensed")
    content_type: ContentType = Field(..., description="Type of content")
    license_type: LicenseType = Field(..., description="Type of license")
    licensor_id: str = Field(..., description="ID of the licensor")
    licensee_id: str = Field(..., description="ID of the licensee")
    terms: LicenseTerms = Field(..., description="License terms")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class LicenseUpdate(BaseSchema):
    """Request model for updating a license."""

    terms: LicenseTerms | None = Field(default=None, description="Updated license terms")
    status: LicenseStatus | None = Field(default=None, description="Updated status")
    metadata: dict[str, Any] | None = Field(default=None, description="Updated metadata")


class License(TimestampedSchema):
    """Full license model."""

    content_id: str = Field(..., description="ID of the content being licensed")
    content_type: ContentType = Field(..., description="Type of content")
    license_type: LicenseType = Field(..., description="Type of license")
    licensor_id: str = Field(..., description="ID of the licensor")
    licensee_id: str = Field(..., description="ID of the licensee")
    terms: LicenseTerms = Field(..., description="License terms")
    status: LicenseStatus = Field(default=LicenseStatus.DRAFT, description="License status")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class LicenseResponse(BaseSchema):
    """API response model for a license."""

    license: License = Field(..., description="The license object")
    message: str = Field(default="Success", description="Response message")


class LicenseListResponse(BaseSchema):
    """API response model for a list of licenses."""

    licenses: list[License] = Field(default_factory=list, description="List of licenses")
    total: int = Field(default=0, description="Total count")
    page: int = Field(default=1, description="Current page")
    page_size: int = Field(default=20, description="Page size")


# ── Terms Models ─────────────────────────────────────────────────────────────


class TermsProposal(BaseSchema):
    """A proposal for license terms."""

    proposed_by: str = Field(..., description="ID of the proposing party")
    terms: LicenseTerms = Field(..., description="Proposed terms")
    rationale: str = Field(default="", description="Rationale for the proposal")
    priority: int = Field(default=5, ge=1, le=10, description="Priority (1-10)")


class TermsNegotiationCreate(BaseSchema):
    """Request model for creating a negotiation."""

    license_id: UUID = Field(..., description="ID of the license being negotiated")
    initial_proposal: TermsProposal = Field(..., description="Initial terms proposal")


class TermsNegotiationUpdate(BaseSchema):
    """Request model for updating a negotiation."""

    counter_proposal: TermsProposal | None = Field(
        default=None, description="Counter proposal"
    )
    status: NegotiationStatus | None = Field(default=None, description="Updated status")


class TermsNegotiation(TimestampedSchema):
    """Full negotiation model."""

    license_id: UUID = Field(..., description="ID of the license being negotiated")
    proposals: list[TermsProposal] = Field(
        default_factory=list, description="All proposals in the negotiation"
    )
    status: NegotiationStatus = Field(
        default=NegotiationStatus.INITIATED, description="Negotiation status"
    )
    current_proposal_index: int = Field(
        default=0, description="Index of the current active proposal"
    )


class TermsNegotiationResponse(BaseSchema):
    """API response model for a negotiation."""

    negotiation: TermsNegotiation = Field(..., description="The negotiation object")
    message: str = Field(default="Success", description="Response message")


# ── Compliance Models ────────────────────────────────────────────────────────


class ComplianceCheckCreate(BaseSchema):
    """Request model for creating a compliance check."""

    license_id: UUID = Field(..., description="ID of the license to check")
    check_type: Literal["usage", "territory", "duration", "attribution", "full"] = Field(
        default="full", description="Type of compliance check"
    )
    context: dict[str, Any] = Field(
        default_factory=dict, description="Additional context for the check"
    )


class ComplianceViolation(BaseSchema):
    """A compliance violation."""

    rule_id: str = Field(..., description="ID of the violated rule")
    severity: RiskLevel = Field(..., description="Severity of the violation")
    description: str = Field(..., description="Description of the violation")
    remediation: str = Field(default="", description="Suggested remediation")


class ComplianceReport(TimestampedSchema):
    """Full compliance report model."""

    license_id: UUID = Field(..., description="ID of the license checked")
    check_type: str = Field(..., description="Type of compliance check performed")
    status: ComplianceStatus = Field(..., description="Overall compliance status")
    violations: list[ComplianceViolation] = Field(
        default_factory=list, description="List of violations found"
    )
    score: float = Field(default=100.0, ge=0, le=100, description="Compliance score (0-100)")
    checked_at: datetime = Field(default_factory=datetime.utcnow, description="Check timestamp")
    details: dict[str, Any] = Field(
        default_factory=dict, description="Additional check details"
    )


class ComplianceReportResponse(BaseSchema):
    """API response model for a compliance report."""

    report: ComplianceReport = Field(..., description="The compliance report")
    message: str = Field(default="Success", description="Response message")


class ComplianceListResponse(BaseSchema):
    """API response model for a list of compliance reports."""

    reports: list[ComplianceReport] = Field(
        default_factory=list, description="List of compliance reports"
    )
    total: int = Field(default=0, description="Total count")


# ── Royalty Models ───────────────────────────────────────────────────────────


class RoyaltyTier(BaseSchema):
    """A royalty tier."""

    min_usage: int = Field(..., description="Minimum usage for this tier")
    max_usage: int | None = Field(default=None, description="Maximum usage for this tier")
    rate: float = Field(..., description="Royalty rate for this tier")
    flat_fee: float = Field(default=0.0, description="Flat fee for this tier")


class RoyaltyCalculationCreate(BaseSchema):
    """Request model for creating a royalty calculation."""

    license_id: UUID = Field(..., description="ID of the license")
    usage_count: int = Field(..., ge=0, description="Number of usages")
    revenue: float = Field(default=0.0, ge=0, description="Total revenue generated")
    tiers: list[RoyaltyTier] = Field(
        default_factory=list, description="Royalty tiers to apply"
    )
    currency: str = Field(default="USD", description="Currency code")


class RoyaltyBreakdown(BaseSchema):
    """Breakdown of a royalty calculation."""

    tier_index: int = Field(..., description="Index of the tier applied")
    tier_rate: float = Field(..., description="Rate of the tier applied")
    usage_in_tier: int = Field(..., description="Usage count in this tier")
    amount: float = Field(..., description="Royalty amount for this tier")


class RoyaltyCalculation(TimestampedSchema):
    """Full royalty calculation model."""

    license_id: UUID = Field(..., description="ID of the license")
    usage_count: int = Field(..., description="Number of usages")
    revenue: float = Field(default=0.0, description="Total revenue generated")
    currency: str = Field(default="USD", description="Currency code")
    total_royalty: float = Field(..., description="Total royalty amount")
    breakdown: list[RoyaltyBreakdown] = Field(
        default_factory=list, description="Royalty breakdown by tier"
    )
    calculated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Calculation timestamp"
    )


class RoyaltyCalculationResponse(BaseSchema):
    """API response model for a royalty calculation."""

    calculation: RoyaltyCalculation = Field(..., description="The royalty calculation")
    message: str = Field(default="Success", description="Response message")


# ── Contract Models ──────────────────────────────────────────────────────────


class ContractClause(BaseSchema):
    """A contract clause."""

    clause_id: str = Field(..., description="Unique clause identifier")
    title: str = Field(..., description="Clause title")
    content: str = Field(..., description="Clause content")
    clause_type: str = Field(..., description="Type of clause")
    risk_level: RiskLevel = Field(default=RiskLevel.LOW, description="Risk level")
    is_negotiable: bool = Field(default=True, description="Whether clause is negotiable")


class ContractAnalysisCreate(BaseSchema):
    """Request model for creating a contract analysis."""

    contract_text: str = Field(..., description="Full contract text to analyze")
    contract_type: Literal["license", "purchase", "subscription", "custom"] = Field(
        default="license", description="Type of contract"
    )
    focus_areas: list[str] = Field(
        default_factory=list, description="Specific areas to focus analysis on"
    )


class ContractRisk(BaseSchema):
    """A contract risk."""

    risk_id: str = Field(..., description="Unique risk identifier")
    description: str = Field(..., description="Risk description")
    severity: RiskLevel = Field(..., description="Risk severity")
    related_clauses: list[str] = Field(
        default_factory=list, description="Related clause IDs"
    )
    recommendation: str = Field(default="", description="Recommendation for mitigation")


class ContractAnalysis(TimestampedSchema):
    """Full contract analysis model."""

    contract_type: str = Field(..., description="Type of contract analyzed")
    clauses: list[ContractClause] = Field(
        default_factory=list, description="Extracted contract clauses"
    )
    risks: list[ContractRisk] = Field(
        default_factory=list, description="Identified risks"
    )
    overall_risk: RiskLevel = Field(..., description="Overall risk assessment")
    summary: str = Field(default="", description="Analysis summary")
    recommendations: list[str] = Field(
        default_factory=list, description="Recommendations"
    )
    analyzed_at: datetime = Field(
        default_factory=datetime.utcnow, description="Analysis timestamp"
    )


class ContractAnalysisResponse(BaseSchema):
    """API response model for a contract analysis."""

    analysis: ContractAnalysis = Field(..., description="The contract analysis")
    message: str = Field(default="Success", description="Response message")


# ── Agent Models ─────────────────────────────────────────────────────────────


class AgentTask(BaseSchema):
    """A task for an agent to execute."""

    task_id: UUID = Field(default_factory=uuid4, description="Task identifier")
    agent_type: str = Field(..., description="Type of agent")
    input_data: dict[str, Any] = Field(..., description="Task input data")
    context: dict[str, Any] = Field(default_factory=dict, description="Task context")


class AgentResult(BaseSchema):
    """Result from an agent execution."""

    task_id: UUID = Field(..., description="Task identifier")
    agent_type: str = Field(..., description="Type of agent")
    success: bool = Field(..., description="Whether the task succeeded")
    output: dict[str, Any] = Field(default_factory=dict, description="Task output")
    error: str | None = Field(default=None, description="Error message if failed")
    execution_time_ms: float = Field(default=0.0, description="Execution time in ms")


# ── Health Models ────────────────────────────────────────────────────────────


class HealthResponse(BaseSchema):
    """Health check response."""

    status: str = Field(..., description="Service status")
    version: str = Field(..., description="Service version")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
