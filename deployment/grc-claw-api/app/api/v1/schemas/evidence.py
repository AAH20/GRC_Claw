"""Evidence-related schemas."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class EvidenceType(str, Enum):
    """Evidence type."""

    ARTIFACT = "artifact"
    OBSERVATION = "observation"
    INTERVIEW = "interview"
    ANALYSIS = "analysis"
    LOG = "log"


class VerificationLevel(str, Enum):
    """Evidence verification level."""

    L0 = "L0"
    L1 = "L1"
    L2 = "L2"
    L3 = "L3"
    L4 = "L4"


class EvidenceSource(BaseModel):
    """Evidence source information."""

    type: str
    system: str
    collection_method: str


class EvidenceContent(BaseModel):
    """Evidence content."""

    format: str
    data: str
    hash: str | None = None


class EvidenceContext(BaseModel):
    """Evidence collection context."""

    environment: str
    region: str | None = None
    timestamp: datetime | None = None
    metadata: dict[str, Any] | None = None


class ControlMapping(BaseModel):
    """Control mapping for evidence."""

    control_id: str
    framework: str
    control_title: str | None = None
    control_family: str | None = None


class ValidationStatus(BaseModel):
    """Evidence validation status."""

    status: str
    validated_by: str | None = None
    validated_at: datetime | None = None
    confidence_score: float = 0.0


class CustodyEvent(BaseModel):
    """Chain of custody event."""

    action: str
    actor: str
    timestamp: datetime
    hash: str


class EvidenceBase(BaseModel):
    """Base evidence attributes."""

    policy_id: str | None = None
    assessment_id: str | None = None
    source: EvidenceSource
    evidence_type: EvidenceType
    content: EvidenceContent
    context: EvidenceContext
    control_mapping: ControlMapping | None = None


class EvidenceCreate(EvidenceBase):
    """Create evidence request."""

    pass


class EvidenceInDB(EvidenceBase):
    """Evidence as stored in database."""

    evidence_id: str
    validation: ValidationStatus
    verification_level: VerificationLevel
    chain_of_custody: list[CustodyEvent] = Field(default_factory=list)
    retention_class: str = "standard"
    created_at: datetime
    expires_at: datetime | None = None

    model_config = {"from_attributes": True}


class EvidenceResponse(EvidenceInDB):
    """Evidence response model."""

    pass


class EvidenceFilter(BaseModel):
    """Evidence search filter parameters."""

    policy_id: str | None = None
    assessment_id: str | None = None
    evidence_type: EvidenceType | None = None
    framework: str | None = None
    control_id: str | None = None
    verification_level: VerificationLevel | None = None
    environment: str | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
    query: str | None = None


class VerifyEvidenceResponse(BaseModel):
    """Evidence verification response."""

    evidence_id: str
    verification_result: dict[str, Any]


class ExportEvidenceRequest(BaseModel):
    """Export evidence package request."""

    framework: str
    time_range: dict[str, datetime]
    format: str = "json"
    include_chain_of_custody: bool = True


class ExportPackageResponse(BaseModel):
    """Export package response."""

    package_id: str
    status: str
    estimated_completion: datetime | None = None
    download_url: str | None = None


class ExportPackageStatus(BaseModel):
    """Export package status response."""

    package_id: str
    status: str
    download_url: str | None = None
    expires_at: datetime | None = None
    package_hash: str | None = None
    manifest: dict[str, Any] | None = None
