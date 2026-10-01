"""Assessment-related schemas."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class AssessmentType(str, Enum):
    """Assessment type."""

    RISK = "risk"
    COMPLIANCE = "compliance"
    MATURITY = "maturity"
    READINESS = "readiness"


class AssessmentStatus(str, Enum):
    """Assessment status."""

    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class FindingSeverity(str, Enum):
    """Finding severity."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFORMATIONAL = "informational"


class FindingStatus(str, Enum):
    """Finding status."""

    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    ACCEPTED = "accepted"
    FALSE_POSITIVE = "false_positive"


class AssessmentBase(BaseModel):
    """Base assessment attributes."""

    assessment_key: str
    title: str
    description: str | None = None
    assessment_type: AssessmentType
    target_id: str
    target_type: str
    methodology: str | None = None
    lead_assessor: str
    metadata: dict[str, Any] | None = None


class AssessmentCreate(AssessmentBase):
    """Create assessment request."""

    pass


class AssessmentUpdate(BaseModel):
    """Update assessment request."""

    title: str | None = None
    description: str | None = None
    status: AssessmentStatus | None = None
    score: float | None = None
    risk_level: str | None = None
    metadata: dict[str, Any] | None = None


class AssessmentFinding(BaseModel):
    """Assessment finding."""

    id: str
    finding_key: str
    title: str
    description: str | None = None
    severity: FindingSeverity
    category: str | None = None
    status: FindingStatus
    policy_id: str | None = None
    evidence_ids: list[str] = Field(default_factory=list)
    remediation: str | None = None
    remediated_by: str | None = None
    remediated_at: datetime | None = None
    due_date: datetime | None = None


class AssessmentInDB(AssessmentBase):
    """Assessment as stored in database."""

    id: str
    status: AssessmentStatus
    score: float | None = None
    risk_level: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    next_assessment_at: datetime | None = None
    findings: list[AssessmentFinding] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AssessmentResponse(AssessmentInDB):
    """Assessment response model."""

    pass


class FindingCreate(BaseModel):
    """Create finding request."""

    finding_key: str
    title: str
    description: str | None = None
    severity: FindingSeverity
    category: str | None = None
    policy_id: str | None = None
    evidence_ids: list[str] = Field(default_factory=list)
    remediation: str | None = None
    due_date: datetime | None = None


class GenerateReportRequest(BaseModel):
    """Generate assessment report request."""

    format: str = "pdf"
    include_evidence: bool = True
    include_remediation: bool = True


class AssessmentFilter(BaseModel):
    """Assessment list filter parameters."""

    assessment_type: AssessmentType | None = None
    status: AssessmentStatus | None = None
    target_type: str | None = None
    target_id: str | None = None
    methodology: str | None = None
