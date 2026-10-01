"""Compliance-related schemas."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ComplianceStatus(str, Enum):
    """Compliance status."""

    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PARTIAL = "partial"
    NOT_ASSESSED = "not_assessed"
    EXEMPT = "exempt"


class ComplianceFramework(BaseModel):
    """Compliance framework."""

    id: str
    framework_key: str
    name: str
    version: str
    description: str | None = None
    authority: str | None = None
    effective_date: datetime | None = None
    control_count: int = 0


class ComplianceControl(BaseModel):
    """Compliance control."""

    id: str
    framework_id: str
    control_key: str
    title: str
    description: str | None = None
    category: str | None = None
    guidance: str | None = None


class ComplianceMapping(BaseModel):
    """Compliance mapping."""

    id: str
    control_id: str
    policy_id: str | None = None
    assessment_id: str | None = None
    mapping_type: str
    coverage: str
    notes: str | None = None
    mapped_by: str
    mapped_at: datetime
    updated_at: datetime


class ComplianceMappingCreate(BaseModel):
    """Create compliance mapping request."""

    control_id: str
    policy_id: str | None = None
    assessment_id: str | None = None
    mapping_type: str
    coverage: str
    notes: str | None = None


class ComplianceGap(BaseModel):
    """Compliance gap."""

    control_id: str
    control_title: str
    status: ComplianceStatus
    severity: str
    evidence_count: int
    last_assessed: datetime | None = None


class ComplianceTrend(BaseModel):
    """Compliance trend."""

    direction: str
    change: str
    period: str


class CompliancePosture(BaseModel):
    """Compliance posture response."""

    framework: str
    target_id: str
    target_type: str
    controls_assessed: int
    controls_compliant: int
    controls_non_compliant: int
    controls_not_assessed: int
    compliance_score: float
    gaps: list[ComplianceGap] = Field(default_factory=list)
    trend: ComplianceTrend | None = None


class CompliancePostureFilter(BaseModel):
    """Compliance posture filter parameters."""

    framework: str | None = None
    target_id: str | None = None
    target_type: str | None = None


class GenerateComplianceReportRequest(BaseModel):
    """Generate compliance report request."""

    framework: str
    time_range: dict[str, datetime]
    format: str = "json"
    include_evidence: bool = True
    include_gaps: bool = True


class CrosswalkResponse(BaseModel):
    """Cross-framework mapping response."""

    grc_control_id: str
    mappings: dict[str, list[str]]
