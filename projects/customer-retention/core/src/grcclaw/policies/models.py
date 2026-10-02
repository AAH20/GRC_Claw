"""
Policy Lifecycle Management — Data Models

Core data structures for policy definition, versioning, approval,
enforcement, and analytics across the GRC_Claw platform.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
import uuid


# ── Enumerations ─────────────────────────────────────────────────────────────


class PolicyStatus(str, Enum):
    DRAFT = "draft"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    PUBLISHED = "published"
    SUSPENDED = "suspended"
    ARCHIVED = "archived"
    DEPRECATED = "deprecated"


class PolicyCategory(str, Enum):
    SECURITY = "security"
    PRIVACY = "privacy"
    COMPLIANCE = "compliance"
    OPERATIONAL = "operational"
    HR = "hr"
    FINANCIAL = "financial"
    AI_GOVERNANCE = "ai_governance"
    DATA_GOVERNANCE = "data_governance"
    THIRD_PARTY = "third_party"
    BUSINESS_CONTINUITY = "business_continuity"


class PolicyPriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"
    DELEGATED = "delegated"
    EXPIRED = "expired"


class EnforcementMode(str, Enum):
    ENFORCING = "enforcing"
    ADVISORY = "advisory"
    DISABLED = "disabled"


class EnforcementResult(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    NOT_APPLICABLE = "not_applicable"
    ERROR = "error"


class ChangeType(str, Enum):
    CREATED = "created"
    UPDATED = "updated"
    PUBLISHED = "published"
    SUSPENDED = "suspended"
    ARCHIVED = "archived"
    DEPRECATED = "deprecated"
    REINSTATED = "reinstated"


# ── Core Policy Models ───────────────────────────────────────────────────────


@dataclass
class PolicyMetadata:
    """Descriptive metadata for a policy."""
    title: str
    description: str = ""
    category: PolicyCategory = PolicyCategory.COMPLIANCE
    priority: PolicyPriority = PolicyPriority.MEDIUM
    framework: str = ""
    framework_mappings: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    owner: str = ""
    approver: str = ""
    department: str = ""
    jurisdiction: str = ""
    version: str = "1.0.0"
    effective_date: str = ""
    review_date: str = ""
    expiry_date: str = ""


@dataclass
class PolicySection:
    """A structured section within a policy document."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    content: str = ""
    order: int = 0
    required: bool = True
    subsections: list[PolicySection] = field(default_factory=list)


@dataclass
class Policy:
    """Complete policy entity with lifecycle state."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    metadata: PolicyMetadata = field(default_factory=PolicyMetadata)
    sections: list[PolicySection] = field(default_factory=list)
    status: PolicyStatus = PolicyStatus.DRAFT
    enforcement_mode: EnforcementMode = EnforcementMode.ADVISORY
    change_log: list[PolicyChange] = field(default_factory=list)
    versions: list[PolicyVersion] = field(default_factory=list)
    approvals: list[ApprovalRecord] = field(default_factory=list)
    attestations: list[Attestation] = field(default_factory=list)
    enforcement_rules: list[EnforcementRule] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    created_by: str = ""
    updated_by: str = ""
    parent_policy_id: Optional[str] = None
    supersedes: Optional[str] = None


@dataclass
class PolicyChange:
    """Audit trail entry for policy modifications."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    change_type: ChangeType = ChangeType.UPDATED
    version_from: str = ""
    version_to: str = ""
    changed_by: str = ""
    changed_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    summary: str = ""
    diff: dict[str, Any] = field(default_factory=dict)
    reason: str = ""


@dataclass
class PolicyVersion:
    """Immutable snapshot of a policy at a specific version."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    policy_id: str = ""
    version: str = "1.0.0"
    sections: list[PolicySection] = field(default_factory=list)
    metadata_snapshot: dict[str, Any] = field(default_factory=dict)
    change_summary: str = ""
    created_by: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    is_active: bool = False


@dataclass
class ApprovalRecord:
    """Tracks approval workflow state for a policy."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    policy_id: str = ""
    version: str = "1.0.0"
    status: ApprovalStatus = ApprovalStatus.PENDING
    approver: str = ""
    delegated_to: Optional[str] = None
    requested_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    decided_at: Optional[str] = None
    comments: str = ""
    escalation_reason: str = ""
    required_approvers: list[str] = field(default_factory=list)
    approval_chain: list[ApprovalStep] = field(default_factory=list)


@dataclass
class ApprovalStep:
    """Individual step in a multi-step approval chain."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    order: int = 0
    approver: str = ""
    status: ApprovalStatus = ApprovalStatus.PENDING
    decided_at: Optional[str] = None
    comments: str = ""


@dataclass
class Attestation:
    """Employee or system attestation of policy acknowledgment."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    policy_id: str = ""
    version: str = "1.0.0"
    employee_id: str = ""
    employee_name: str = ""
    employee_email: str = ""
    department: str = ""
    acknowledged_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    attestation_method: str = "digital_signature"
    ip_address: str = ""
    user_agent: str = ""


@dataclass
class EnforcementRule:
    """A rule that can be automatically enforced against targets."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    policy_id: str = ""
    name: str = ""
    description: str = ""
    rule_type: str = ""  # e.g., "tag_check", "config_scan", "access_review"
    condition: dict[str, Any] = field(default_factory=dict)
    action: dict[str, Any] = field(default_factory=dict)
    severity: PolicyPriority = PolicyPriority.MEDIUM
    enabled: bool = True
    target_scope: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class EnforcementEvent:
    """Result of an enforcement check against a target."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    policy_id: str = ""
    rule_id: str = ""
    target_id: str = ""
    target_type: str = ""
    result: EnforcementResult = EnforcementResult.NOT_APPLICABLE
    findings: list[EnforcementFinding] = field(default_factory=list)
    remediation: str = ""
    enforced_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    enforced_by: str = "system"
    evidence_refs: list[str] = field(default_factory=list)


@dataclass
class EnforcementFinding:
    """Individual finding from an enforcement check."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    severity: PolicyPriority = PolicyPriority.MEDIUM
    title: str = ""
    description: str = ""
    evidence: str = ""
    remediation: str = ""
    status: str = "open"  # open, acknowledged, remediated, accepted_risk
    cwe_id: Optional[str] = None
    owasp_category: Optional[str] = None


@dataclass
class PolicyTemplate:
    """Reusable policy template for rapid policy creation."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    category: PolicyCategory = PolicyCategory.COMPLIANCE
    framework: str = ""
    framework_mappings: list[str] = field(default_factory=list)
    required_sections: list[str] = field(default_factory=list)
    default_content: str = ""
    default_rules: list[EnforcementRule] = field(default_factory=list)
    is_builtin: bool = False
    version: str = "1.0.0"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class PolicyAnalytics:
    """Aggregated analytics for policy portfolio."""
    total_policies: int = 0
    by_status: dict[str, int] = field(default_factory=dict)
    by_category: dict[str, int] = field(default_factory=dict)
    by_priority: dict[str, int] = field(default_factory=dict)
    by_enforcement_mode: dict[str, int] = field(default_factory=dict)
    upcoming_reviews: int = 0
    overdue_reviews: int = 0
    pending_approvals: int = 0
    attestations_pending: int = 0
    attestations_completed: int = 0
    enforcement_pass_rate: float = 0.0
    enforcement_fail_count: int = 0
    enforcement_warning_count: int = 0
    average_approval_time_hours: float = 0.0
    policies_created_last_30d: int = 0
    policies_updated_last_30d: int = 0
    top_violated_rules: list[dict[str, Any]] = field(default_factory=list)
    compliance_trend: list[dict[str, Any]] = field(default_factory=list)
