"""
Data models for the GRC_Claw audit and compliance tracking system.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional
from datetime import datetime, timezone
import uuid


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class AuditEventType(str, Enum):
    """Types of audit trail events."""
    CONTROL_EVALUATED = "control_evaluated"
    EVIDENCE_COLLECTED = "evidence_collected"
    EVIDENCE_REVIEWED = "evidence_reviewed"
    FINDING_RAISED = "finding_raised"
    FINDING_REMEDIATED = "finding_remediated"
    FINDING_CLOSED = "finding_closed"
    POLICY_CREATED = "policy_created"
    POLICY_UPDATED = "policy_updated"
    POLICY_REVIEWED = "policy_reviewed"
    RISK_ASSESSED = "risk_assessed"
    RISK_MITIGATED = "risk_mitigated"
    ASSESSMENT_STARTED = "assessment_started"
    ASSESSMENT_COMPLETED = "assessment_completed"
    WORKPAPER_CREATED = "workpaper_created"
    WORKPAPER_REVIEWED = "workpaper_reviewed"
    REPORT_GENERATED = "report_generated"
    ACCESS_GRANTED = "access_granted"
    ACCESS_REVOKED = "access_revoked"
    CONFIG_CHANGED = "config_changed"
    DATA_EXPORTED = "data_exported"
    DATA_DELETED = "data_deleted"


class AuditEventSeverity(str, Enum):
    """Severity levels for audit events."""
    INFO = "info"
    NOTICE = "notice"
    WARNING = "warning"
    ALERT = "alert"
    CRITICAL = "critical"


class ComplianceFramework(str, Enum):
    """Supported compliance frameworks."""
    SOC2 = "soc2"
    ISO27001 = "iso27001"
    ISO27017 = "iso27017"
    ISO27018 = "iso27018"
    NIST_CSF = "nist_csf"
    NIST_800_53 = "nist_800_53"
    PCI_DSS = "pci_dss"
    HIPAA = "hipaa"
    GDPR = "gdpr"
    CCPA = "ccpa"
    SOX = "sox"
    COBIT = "cobit"
    FedRAMP = "fedramp"
    CMMC = "cmmc"
    TISAX = "tisax"
    CUSTOM = "custom"


class ControlStatus(str, Enum):
    """Status of a compliance control."""
    NOT_ASSESSED = "not_assessed"
    ASSESSMENT_IN_PROGRESS = "assessment_in_progress"
    COMPLIANT = "compliant"
    PARTIALLY_COMPLIANT = "partially_compliant"
    NON_COMPLIANT = "non_compliant"
    NOT_APPLICABLE = "not_applicable"
    COMPENSATING_CONTROL = "compensating_control"


class ControlType(str, Enum):
    """Type of control."""
    PREVENTIVE = "preventive"
    DETECTIVE = "detective"
    CORRECTIVE = "corrective"
    DETERRENT = "deterrent"
    RECOVERY = "recovery"
    COMPENSATING = "compensating"


class FindingSeverity(str, Enum):
    """Severity of an audit finding."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFORMATIONAL = "informational"


class FindingStatus(str, Enum):
    """Status of an audit finding."""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    REMEDIATED = "remediated"
    VERIFIED = "verified"
    CLOSED = "closed"
    ACCEPTED_RISK = "accepted_risk"
    DEFERRED = "deferred"


class EvidenceType(str, Enum):
    """Type of evidence."""
    DOCUMENT = "document"
    SCREENSHOT = "screenshot"
    LOG_FILE = "log_file"
    CONFIG_FILE = "config_file"
    INTERVIEW_RECORD = "interview_record"
    OBSERVATION = "observation"
    SYSTEM_OUTPUT = "system_output"
    THIRD_PARTY_REPORT = "third_party_report"
    POLICY = "policy"
    PROCEDURE = "procedure"
    TRAINING_RECORD = "training_record"
    ACCESS_REVIEW = "access_review"
    CHANGE_REQUEST = "change_request"
    INCIDENT_REPORT = "incident_report"
    RISK_ASSESSMENT = "risk_assessment"
    PENETRATION_TEST = "penetration_test"
    VULNERABILITY_SCAN = "vulnerability_scan"


class EvidenceStatus(str, Enum):
    """Status of evidence."""
    PENDING = "pending"
    COLLECTED = "collected"
    UNDER_REVIEW = "under_review"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"
    EXPIRED = "expired"


class AuditStatus(str, Enum):
    """Status of an audit engagement."""
    PLANNING = "planning"
    FIELDWORK = "fieldwork"
    REVIEW = "review"
    REPORTING = "reporting"
    CLOSED = "closed"
    ARCHIVED = "archived"


class AuditType(str, Enum):
    """Type of audit."""
    INTERNAL = "internal"
    EXTERNAL = "external"
    REGULATORY = "regulatory"
    SOX = "sox"
    ISO27001 = "iso27001"
    SOC2 = "soc2"
    OPERATIONAL = "operational"
    COMPLIANCE = "compliance"
    FORENSIC = "forensic"


class OverallOpinion(str, Enum):
    """Overall audit opinion."""
    UNQUALIFIED = "unqualified"
    QUALIFIED = "qualified"
    ADVERSE = "adverse"
    DISCLAIMER = "disclaimer"


class CAPAType(str, Enum):
    """Type of corrective/preventive action."""
    CORRECTIVE = "corrective"
    PREVENTIVE = "preventive"


class CAPAStatus(str, Enum):
    """Status of a CAPA."""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    VERIFIED = "verified"
    CLOSED = "closed"
    OVERDUE = "overdue"


class ChainOfCustodyStatus(str, Enum):
    """Chain of custody status."""
    INTACT = "intact"
    TRANSFERRED = "transferred"
    ACCESSED = "accessed"
    ARCHIVED = "archived"
    DISPOSED = "disposed"


# ---------------------------------------------------------------------------
# Core data models
# ---------------------------------------------------------------------------

@dataclass
class Actor:
    """Who performed the action."""

    type: str  # user, system, agent, api, service
    id: str
    name: Optional[str] = None
    email: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


@dataclass
class Resource:
    """What was acted upon."""

    type: str  # control, policy, finding, evidence, report, etc.
    id: str
    name: Optional[str] = None
    parent_id: Optional[str] = None


@dataclass
class AuditEvent:
    """A single immutable audit trail event."""

    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: AuditEventType = AuditEventType.CONFIG_CHANGED
    severity: AuditEventSeverity = AuditEventSeverity.INFO
    actor: Actor = field(default_factory=lambda: Actor(type="system", id="system"))
    resource: Resource = field(default_factory=lambda: Resource(type="unknown", id="unknown"))
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    details: dict[str, Any] = field(default_factory=dict)
    integrity_hash: Optional[str] = None
    previous_event_hash: Optional[str] = None
    correlation_id: Optional[str] = None
    session_id: Optional[str] = None
    tenant_id: Optional[str] = None

    def __post_init__(self):
        if self.integrity_hash is None:
            self.integrity_hash = self._compute_hash()

    def _compute_hash(self) -> str:
        """Compute SHA-256 hash of the event for tamper detection."""
        import hashlib
        data = (
            f"{self.event_id}|{self.event_type.value}|{self.actor.id}|"
            f"{self.resource.id}|{self.timestamp}|{sorted(self.details.items())}"
        )
        return hashlib.sha256(data.encode()).hexdigest()

    def verify_integrity(self) -> bool:
        """Verify the event's integrity hash."""
        return self.integrity_hash == self._compute_hash()


@dataclass
class ComplianceControl:
    """A compliance control within a framework."""

    control_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8].upper())
    framework: ComplianceFramework = ComplianceFramework.CUSTOM
    control_identifier: str = ""  # e.g., "CC6.1" for SOC 2
    title: str = ""
    description: str = ""
    control_type: ControlType = ControlType.PREVENTIVE
    status: ControlStatus = ControlStatus.NOT_ASSESSED
    owner: Optional[str] = None
    assessor: Optional[str] = None
    assessment_date: Optional[str] = None
    next_assessment_date: Optional[str] = None
    evidence_ids: list[str] = field(default_factory=list)
    finding_ids: list[str] = field(default_factory=list)
    risk_ids: list[str] = field(default_factory=list)
    compensating_controls: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Finding:
    """An audit finding."""

    finding_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8].upper())
    audit_id: Optional[str] = None
    control_id: Optional[str] = None
    severity: FindingSeverity = FindingSeverity.MEDIUM
    status: FindingStatus = FindingStatus.OPEN
    title: str = ""
    description: str = ""
    root_cause: Optional[str] = None
    impact: Optional[str] = None
    recommendation: Optional[str] = None
    remediation: Optional[str] = None
    remediation_owner: Optional[str] = None
    due_date: Optional[str] = None
    remediated_at: Optional[str] = None
    verified_at: Optional[str] = None
    verified_by: Optional[str] = None
    evidence_ids: list[str] = field(default_factory=list)
    risk_ids: list[str] = field(default_factory=list)
    capa_ids: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Evidence:
    """Audit evidence with chain of custody."""

    evidence_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8].upper())
    evidence_type: EvidenceType = EvidenceType.DOCUMENT
    status: EvidenceStatus = EvidenceStatus.PENDING
    title: str = ""
    description: Optional[str] = None
    source: Optional[str] = None
    collector: Optional[str] = None
    collection_date: Optional[str] = None
    storage_location: Optional[str] = None
    file_hash: Optional[str] = None
    file_size_bytes: Optional[int] = None
    mime_type: Optional[str] = None
    retention_period_days: Optional[int] = None
    expiry_date: Optional[str] = None
    control_ids: list[str] = field(default_factory=list)
    finding_ids: list[str] = field(default_factory=list)
    audit_ids: list[str] = field(default_factory=list)
    chain_of_custody: list[dict[str, Any]] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AuditEngagement:
    """An audit engagement."""

    audit_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8].upper())
    name: str = ""
    audit_type: AuditType = AuditType.INTERNAL
    status: AuditStatus = AuditStatus.PLANNING
    framework: Optional[ComplianceFramework] = None
    scope: list[str] = field(default_factory=list)
    objectives: list[str] = field(default_factory=list)
    lead_auditor: Optional[str] = None
    team: list[str] = field(default_factory=list)
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    fieldwork_start: Optional[str] = None
    fieldwork_end: Optional[str] = None
    report_date: Optional[str] = None
    control_ids: list[str] = field(default_factory=list)
    finding_ids: list[str] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)
    workpaper_ids: list[str] = field(default_factory=list)
    report_id: Optional[str] = None
    overall_opinion: Optional[OverallOpinion] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Workpaper:
    """An audit workpaper."""

    workpaper_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8].upper())
    audit_id: Optional[str] = None
    control_id: Optional[str] = None
    title: str = ""
    description: Optional[str] = None
    procedure: Optional[str] = None
    conclusion: Optional[str] = None  # satisfactory, needs_improvement, unsatisfactory
    preparer: Optional[str] = None
    reviewer: Optional[str] = None
    preparation_date: Optional[str] = None
    review_date: Optional[str] = None
    evidence_ids: list[str] = field(default_factory=list)
    finding_ids: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CAPA:
    """Corrective and Preventive Action."""

    capa_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8].upper())
    finding_id: Optional[str] = None
    capa_type: CAPAType = CAPAType.CORRECTIVE
    status: CAPAStatus = CAPAStatus.OPEN
    title: str = ""
    description: str = ""
    root_cause: Optional[str] = None
    action_plan: Optional[str] = None
    owner: Optional[str] = None
    due_date: Optional[str] = None
    completed_at: Optional[str] = None
    verified_at: Optional[str] = None
    verified_by: Optional[str] = None
    effectiveness_review: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AuditReport:
    """Generated audit report."""

    report_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8].upper())
    audit_id: Optional[str] = None
    title: str = ""
    executive_summary: Optional[str] = None
    scope_and_objectives: Optional[str] = None
    methodology: Optional[str] = None
    total_findings: int = 0
    critical_findings: int = 0
    high_findings: int = 0
    medium_findings: int = 0
    low_findings: int = 0
    informational_findings: int = 0
    open_findings: int = 0
    closed_findings: int = 0
    overall_opinion: Optional[OverallOpinion] = None
    opinion_basis: Optional[str] = None
    recommendations: list[str] = field(default_factory=list)
    management_response: Optional[str] = None
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    generated_by: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ComplianceAssessment:
    """A compliance assessment against a framework."""

    assessment_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8].upper())
    framework: ComplianceFramework = ComplianceFramework.CUSTOM
    assessment_name: str = ""
    status: AuditStatus = AuditStatus.PLANNING
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    assessor: Optional[str] = None
    total_controls: int = 0
    compliant_controls: int = 0
    partially_compliant_controls: int = 0
    non_compliant_controls: int = 0
    not_assessed_controls: int = 0
    not_applicable_controls: int = 0
    compliance_score: float = 0.0  # 0-100
    control_ids: list[str] = field(default_factory=list)
    finding_ids: list[str] = field(default_factory=list)
    report_id: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AuditAnalytics:
    """Aggregated audit analytics."""

    period_start: Optional[str] = None
    period_end: Optional[str] = None
    total_events: int = 0
    events_by_type: dict[str, int] = field(default_factory=dict)
    events_by_severity: dict[str, int] = field(default_factory=dict)
    total_audits: int = 0
    active_audits: int = 0
    completed_audits: int = 0
    total_findings: int = 0
    open_findings: int = 0
    closed_findings: int = 0
    overdue_findings: int = 0
    findings_by_severity: dict[str, int] = field(default_factory=dict)
    findings_by_status: dict[str, int] = field(default_factory=dict)
    total_evidence: int = 0
    evidence_by_type: dict[str, int] = field(default_factory=dict)
    evidence_by_status: dict[str, int] = field(default_factory=dict)
    total_controls: int = 0
    controls_by_status: dict[str, int] = field(default_factory=dict)
    compliance_score_avg: float = 0.0
    mean_time_to_remediate_days: Optional[float] = None
    findings_trend: list[dict[str, Any]] = field(default_factory=dict)
    top_risk_areas: list[dict[str, Any]] = field(default_factory=list)
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
