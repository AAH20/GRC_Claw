"""Shared Pydantic models for the GRC Unified SDK.

This module defines the core data structures used across all 75 GRC
projects.  All models inherit from :class:`GRCBaseModel` which provides
common configuration (extra-field forbidding, population by name, and
serialization helpers).

Models are organized into logical groups:

- **Base** — :class:`GRCBaseModel` and shared mixins.
- **Projects** — :class:`Project`, :class:`ProjectSummary`.
- **Controls** — :class:`Control`, :class:`ControlStatus`.
- **Evidence** — :class:`Evidence`, :class:`EvidenceType`.
- **Findings** — :class:`Finding`, :class:`FindingSeverity`, :class:`FindingStatus`.
- **Assessments** — :class:`Assessment`, :class:`AssessmentStatus`.
- **Pagination** — :class:`PaginatedResponse`, :class:`PageMetadata`.
- **Audit** — :class:`AuditEntry`.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

# ---------------------------------------------------------------------------
# Base model
# ---------------------------------------------------------------------------


class GRCBaseModel(BaseModel):
    """Base model for all GRC SDK data structures.

    Configuration:
        - ``extra="forbid"``: reject unknown fields to catch API drift.
        - ``populate_by_name=True``: allow both field name and alias.
        - ``use_enum_values`` is NOT enabled; enums are kept as enum
          members for type safety.
    """

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    def to_api_dict(self) -> dict[str, Any]:
        """Serialize to a dictionary suitable for API requests.

        Excludes ``None`` values and serializes enums to their values.
        """
        return self.model_dump(mode="json", exclude_none=True, by_alias=True)

    def to_json(self, *, indent: int | None = None) -> str:
        """Serialize to a JSON string."""
        return self.model_dump_json(indent=indent, exclude_none=True, by_alias=True)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class ControlStatus(str, Enum):
    """Status of a control within a GRC project."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    DEPRECATED = "deprecated"
    DRAFT = "draft"


class EvidenceType(str, Enum):
    """Type of evidence artifact."""

    DOCUMENT = "document"
    SCREENSHOT = "screenshot"
    LOG = "log"
    API_RESPONSE = "api_response"
    MANUAL_ATTESTATION = "manual_attestation"
    AUTOMATED_TEST = "automated_test"
    POLICY = "policy"
    CONFIGURATION = "configuration"


class FindingSeverity(str, Enum):
    """Severity level of a finding."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class FindingStatus(str, Enum):
    """Lifecycle status of a finding."""

    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    ACCEPTED = "accepted"
    FALSE_POSITIVE = "false_positive"
    RISK_ACCEPTED = "risk_accepted"


class AssessmentStatus(str, Enum):
    """Status of a compliance assessment."""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# ---------------------------------------------------------------------------
# Projects
# ---------------------------------------------------------------------------


class ProjectSummary(GRCBaseModel):
    """Lightweight project representation for list views.

    Attributes:
        id: Unique project identifier.
        name: Human-readable project name.
        description: Short description.
        status: Current project status.
        control_count: Number of controls in the project.
        created_at: Creation timestamp.
        updated_at: Last update timestamp.
    """

    id: str
    name: str
    description: str | None = None
    status: str = "active"
    control_count: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None


class Project(ProjectSummary):
    """Full project representation with all metadata.

    Extends :class:`ProjectSummary` with additional fields available
    when fetching a single project.

    Attributes:
        owner: User or team that owns the project.
        tags: Arbitrary tags for categorization.
        framework: Compliance framework (e.g. SOC2, ISO27001, NIST).
        metadata: Additional project-specific metadata.
    """

    owner: str | None = None
    tags: list[str] = Field(default_factory=list)
    framework: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Controls
# ---------------------------------------------------------------------------


class Control(GRCBaseModel):
    """A security or compliance control.

    Attributes:
        id: Unique control identifier.
        project_id: Parent project ID.
        name: Control name.
        description: Detailed description.
        status: Current control status.
        control_type: Type of control (preventive, detective, corrective).
        owner: Control owner.
        tags: Categorization tags.
        evidence_ids: IDs of linked evidence artifacts.
        created_at: Creation timestamp.
        updated_at: Last update timestamp.
    """

    id: str
    project_id: str
    name: str
    description: str | None = None
    status: ControlStatus = ControlStatus.ACTIVE
    control_type: str | None = None
    owner: str | None = None
    tags: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None


# ---------------------------------------------------------------------------
# Evidence
# ---------------------------------------------------------------------------


class Evidence(GRCBaseModel):
    """An evidence artifact linked to a control.

    Attributes:
        id: Unique evidence identifier.
        project_id: Parent project ID.
        control_id: ID of the control this evidence supports.
        name: Evidence name.
        description: Detailed description.
        evidence_type: Type of evidence artifact.
        uri: Location of the evidence (URL, file path, etc.).
        content_type: MIME type of the evidence content.
        size_bytes: Size of the evidence file in bytes.
        uploaded_by: User who uploaded the evidence.
        uploaded_at: Upload timestamp.
        expires_at: Expiration timestamp, if applicable.
        metadata: Additional evidence-specific metadata.
    """

    id: str
    project_id: str
    control_id: str
    name: str
    description: str | None = None
    evidence_type: EvidenceType = EvidenceType.DOCUMENT
    uri: str | None = None
    content_type: str | None = None
    size_bytes: int | None = None
    uploaded_by: str | None = None
    uploaded_at: datetime | None = None
    expires_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Findings
# ---------------------------------------------------------------------------


class Finding(GRCBaseModel):
    """A finding discovered during an assessment or audit.

    Attributes:
        id: Unique finding identifier.
        project_id: Parent project ID.
        control_id: Related control ID, if applicable.
        title: Short finding title.
        description: Detailed description.
        severity: Severity level.
        status: Current lifecycle status.
        remediation: Recommended remediation steps.
        remediated_by: User who remediated the finding.
        remediated_at: Remediation timestamp.
        due_date: Remediation due date.
        created_at: Creation timestamp.
        updated_at: Last update timestamp.
    """

    id: str
    project_id: str
    title: str
    description: str | None = None
    control_id: str | None = None
    severity: FindingSeverity = FindingSeverity.MEDIUM
    status: FindingStatus = FindingStatus.OPEN
    remediation: str | None = None
    remediated_by: str | None = None
    remediated_at: datetime | None = None
    due_date: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


# ---------------------------------------------------------------------------
# Assessments
# ---------------------------------------------------------------------------


class Assessment(GRCBaseModel):
    """A compliance assessment run against a project.

    Attributes:
        id: Unique assessment identifier.
        project_id: Parent project ID.
        name: Assessment name.
        framework: Compliance framework being assessed.
        status: Current assessment status.
        started_at: Assessment start timestamp.
        completed_at: Assessment completion timestamp.
        assessor: User or team that performed the assessment.
        score: Numeric assessment score (0-100).
        finding_count: Number of findings in this assessment.
        metadata: Additional assessment-specific metadata.
    """

    id: str
    project_id: str
    name: str
    framework: str | None = None
    status: AssessmentStatus = AssessmentStatus.NOT_STARTED
    started_at: datetime | None = None
    completed_at: datetime | None = None
    assessor: str | None = None
    score: float | None = None
    finding_count: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Pagination
# ---------------------------------------------------------------------------


T = TypeVar("T", bound=GRCBaseModel)


class PageMetadata(GRCBaseModel):
    """Pagination metadata for list responses.

    Attributes:
        page: Current page number (1-indexed).
        page_size: Number of items per page.
        total_items: Total number of items across all pages.
        total_pages: Total number of pages.
        has_next: Whether a next page exists.
        has_previous: Whether a previous page exists.
    """

    page: int = 1
    page_size: int = 100
    total_items: int = 0
    total_pages: int = 0
    has_next: bool = False
    has_previous: bool = False


class PaginatedResponse(GRCBaseModel, Generic[T]):
    """Generic paginated response wrapper.

    Attributes:
        data: List of items on the current page.
        pagination: Pagination metadata.
    """

    data: list[T] = Field(default_factory=list)
    pagination: PageMetadata = Field(default_factory=PageMetadata)


# ---------------------------------------------------------------------------
# Audit
# ---------------------------------------------------------------------------


class AuditEntry(GRCBaseModel):
    """An audit log entry.

    Attributes:
        id: Unique audit entry identifier.
        project_id: Parent project ID.
        action: Action performed (e.g. "control.created").
        actor: User or system that performed the action.
        target_type: Type of the affected resource.
        target_id: ID of the affected resource.
        timestamp: When the action occurred.
        details: Additional action-specific details.
        ip_address: IP address of the actor, if available.
    """

    id: str
    project_id: str
    action: str
    actor: str | None = None
    target_type: str | None = None
    target_id: str | None = None
    timestamp: datetime | None = None
    details: dict[str, Any] = Field(default_factory=dict)
    ip_address: str | None = None


# ---------------------------------------------------------------------------
# Health & Status
# ---------------------------------------------------------------------------


class HealthStatus(GRCBaseModel):
    """Health status of a GRC project or the overall system.

    Attributes:
        status: Overall health status ("healthy", "degraded", "unhealthy").
        project_id: Project ID, if this is a project-level health check.
        checks: Individual health check results.
        timestamp: When the health check was performed.
    """

    status: str = "healthy"
    project_id: str | None = None
    checks: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime | None = None


class ProjectStats(GRCBaseModel):
    """Aggregate statistics for a project.

    Attributes:
        project_id: Parent project ID.
        total_controls: Total number of controls.
        active_controls: Number of active controls.
        total_evidence: Total number of evidence artifacts.
        total_findings: Total number of findings.
        open_findings: Number of open findings.
        critical_findings: Number of critical findings.
        assessments_completed: Number of completed assessments.
        last_assessment_date: Date of the most recent assessment.
        compliance_score: Overall compliance score (0-100).
    """

    project_id: str
    total_controls: int = 0
    active_controls: int = 0
    total_evidence: int = 0
    total_findings: int = 0
    open_findings: int = 0
    critical_findings: int = 0
    assessments_completed: int = 0
    last_assessment_date: datetime | None = None
    compliance_score: float | None = None
