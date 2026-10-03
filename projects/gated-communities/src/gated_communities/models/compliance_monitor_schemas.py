"""Pydantic models for compliance monitoring."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class PolicyStatus(StrEnum):
    """Policy lifecycle status."""

    DRAFT = "draft"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    ARCHIVED = "archived"


class ViolationSeverity(StrEnum):
    """Violation severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ViolationStatus(StrEnum):
    """Violation lifecycle status."""

    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    IN_REMEDIATION = "in_remediation"
    RESOLVED = "resolved"
    CLOSED = "closed"


class RemediationStatus(StrEnum):
    """Remediation action status."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class Policy(BaseModel):
    """Compliance policy model.

    Attributes:
        id: Unique policy identifier.
        name: Policy name.
        description: Policy description.
        category: Policy category (e.g., security, privacy, financial).
        status: Current policy status.
        version: Policy version string.
        effective_date: When the policy takes effect.
        rules: List of policy rules.
        metadata: Additional policy metadata.
        created_at: Creation timestamp.
        updated_at: Last update timestamp.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(default="", max_length=2000)
    category: str = Field(..., min_length=1, max_length=100)
    status: PolicyStatus = PolicyStatus.DRAFT
    version: str = Field(default="1.0.0", pattern=r"^\d+\.\d+\.\d+$")
    effective_date: datetime = Field(default_factory=datetime.utcnow)
    rules: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Violation(BaseModel):
    """Compliance violation model.

    Attributes:
        id: Unique violation identifier.
        policy_id: Associated policy ID.
        title: Violation title.
        description: Violation description.
        severity: Violation severity level.
        status: Current violation status.
        detected_at: Detection timestamp.
        resolved_at: Resolution timestamp.
        evidence: Evidence supporting the violation.
        remediation_actions: List of remediation action IDs.
        assignee: Person assigned to resolve.
        metadata: Additional violation metadata.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(default_factory=uuid4)
    policy_id: UUID
    title: str = Field(..., min_length=1, max_length=500)
    description: str = Field(default="", max_length=5000)
    severity: ViolationSeverity = ViolationSeverity.MEDIUM
    status: ViolationStatus = ViolationStatus.OPEN
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: datetime | None = None
    evidence: list[str] = Field(default_factory=list)
    remediation_actions: list[UUID] = Field(default_factory=list)
    assignee: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class AuditReport(BaseModel):
    """Audit report model.

    Attributes:
        id: Unique audit report identifier.
        title: Report title.
        description: Report description.
        period_start: Audit period start.
        period_end: Audit period end.
        findings: List of audit findings.
        policies_reviewed: List of policy IDs reviewed.
        violations_found: List of violation IDs found.
        overall_score: Overall compliance score.
        recommendations: List of recommendations.
        generated_at: Report generation timestamp.
        generated_by: Agent or user who generated the report.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(default_factory=uuid4)
    title: str = Field(..., min_length=1, max_length=500)
    description: str = Field(default="", max_length=5000)
    period_start: datetime
    period_end: datetime
    findings: list[str] = Field(default_factory=list)
    policies_reviewed: list[UUID] = Field(default_factory=list)
    violations_found: list[UUID] = Field(default_factory=list)
    overall_score: float = Field(default=0.0, ge=0.0, le=100.0)
    recommendations: list[str] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    generated_by: str = Field(default="AuditReporterAgent")


class ComplianceScore(BaseModel):
    """Compliance score model.

    Attributes:
        id: Unique score identifier.
        policy_id: Associated policy ID.
        domain: Compliance domain.
        score: Compliance score (0-100).
        max_score: Maximum possible score.
        factors: Scoring factors and weights.
        computed_at: Score computation timestamp.
        trend: Score trend direction.
        previous_score: Previous score for comparison.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(default_factory=uuid4)
    policy_id: UUID
    domain: str = Field(..., min_length=1, max_length=100)
    score: float = Field(..., ge=0.0, le=100.0)
    max_score: float = Field(default=100.0, ge=0.0)
    factors: dict[str, float] = Field(default_factory=dict)
    computed_at: datetime = Field(default_factory=datetime.utcnow)
    trend: str = Field(default="stable", pattern=r"^(improving|declining|stable)$")
    previous_score: float | None = None


class ComplianceReport(BaseModel):
    """Comprehensive compliance report model.

    Attributes:
        id: Unique report identifier.
        organization: Organization name.
        period_start: Report period start.
        period_end: Report period end.
        policies: List of policies assessed.
        violations: List of violations found.
        scores: List of compliance scores.
        audit_reports: List of audit report references.
        overall_compliance_score: Overall compliance percentage.
        risk_level: Overall risk level.
        executive_summary: Executive summary text.
        generated_at: Report generation timestamp.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(default_factory=uuid4)
    organization: str = Field(..., min_length=1, max_length=255)
    period_start: datetime
    period_end: datetime
    policies: list[Policy] = Field(default_factory=list)
    violations: list[Violation] = Field(default_factory=list)
    scores: list[ComplianceScore] = Field(default_factory=list)
    audit_reports: list[UUID] = Field(default_factory=list)
    overall_compliance_score: float = Field(default=0.0, ge=0.0, le=100.0)
    risk_level: str = Field(default="medium", pattern=r"^(low|medium|high|critical)$")
    executive_summary: str = Field(default="", max_length=10000)
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class RemediationAction(BaseModel):
    """Remediation action model.

    Attributes:
        id: Unique action identifier.
        violation_id: Associated violation ID.
        action_type: Type of remediation action.
        description: Action description.
        status: Current action status.
        executed_at: Execution timestamp.
        result: Execution result.
        error_message: Error message if failed.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(default_factory=uuid4)
    violation_id: UUID
    action_type: str = Field(..., min_length=1, max_length=100)
    description: str = Field(default="", max_length=2000)
    status: RemediationStatus = RemediationStatus.PENDING
    executed_at: datetime | None = None
    result: str | None = None
    error_message: str | None = None


class PolicyCreate(BaseModel):
    """Request model for creating a policy."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(default="", max_length=2000)
    category: str = Field(..., min_length=1, max_length=100)
    version: str = Field(default="1.0.0", pattern=r"^\d+\.\d+\.\d+$")
    effective_date: datetime | None = None
    rules: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ViolationCreate(BaseModel):
    """Request model for reporting a violation."""

    policy_id: UUID
    title: str = Field(..., min_length=1, max_length=500)
    description: str = Field(default="", max_length=5000)
    severity: ViolationSeverity = ViolationSeverity.MEDIUM
    evidence: list[str] = Field(default_factory=list)
    assignee: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class AuditRequest(BaseModel):
    """Request model for generating an audit report."""

    title: str = Field(..., min_length=1, max_length=500)
    description: str = Field(default="", max_length=5000)
    period_start: datetime
    period_end: datetime
    policy_ids: list[UUID] = Field(default_factory=list)


class ScoreRequest(BaseModel):
    """Request model for computing a compliance score."""

    policy_id: UUID
    domain: str = Field(..., min_length=1, max_length=100)
    factors: dict[str, float] = Field(default_factory=dict)


class RemediationRequest(BaseModel):
    """Request model for remediation."""

    action_type: str = Field(..., min_length=1, max_length=100)
    description: str = Field(default="", max_length=2000)
    auto_execute: bool = False
