"""Core data models for GRC_Claw — the 5 core abstractions."""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


# ─── Enums ───────────────────────────────────────────────────────────────────

class PolicyStatus(str, Enum):
    DRAFT = "draft"
    REVIEW = "review"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class PolicyCategory(str, Enum):
    DATA_HANDLING = "data_handling"
    AGENT_BEHAVIOR = "agent_behavior"
    MODEL_GOVERNANCE = "model_governance"
    ACCESS_CONTROL = "access_control"
    CONTENT_SAFETY = "content_safety"
    PRIVACY = "privacy"
    CUSTOM = "custom"


class PolicyLanguage(str, Enum):
    CEDAR = "cedar"
    REGO = "rego"
    YAML = "yaml"
    JSON = "json"


class Action(str, Enum):
    ALLOW = "allow"
    DENY = "deny"
    WARN = "warn"
    REQUIRE_APPROVAL = "require_approval"
    TRANSFORM = "transform"
    ESCALATE = "escalate"
    THROTTLE = "throttle"
    LOG = "log"


class EnforcementStrategy(str, Enum):
    DENY_OVERRIDES = "deny_overrides"
    ALLOW_OVERRIDES = "allow_overrides"
    FIRST_MATCH = "first_match"
    PRIORITY_ORDER = "priority_order"


class EvidenceType(str, Enum):
    POLICY_EVALUATION = "policy_evaluation"
    ASSESSMENT_RESULT = "assessment_result"
    INCIDENT_RECORD = "incident_record"
    AUDIT_EVENT = "audit_event"
    COMPLIANCE_MAPPING = "compliance_mapping"
    RISK_ASSESSMENT = "risk_assessment"


class AssessmentType(str, Enum):
    FAIRNESS = "fairness"
    BIAS = "bias"
    ROBUSTNESS = "robustness"
    EXPLAINABILITY = "explainability"
    SECURITY = "security"
    LLM_EVALUATION = "llm_evaluation"
    RED_TEAM = "red_team"


class AssessmentStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"


class ComplianceStatus(str, Enum):
    COMPLIANT = "compliant"
    PARTIALLY_COMPLIANT = "partially_compliant"
    NON_COMPLIANT = "non_compliant"
    NOT_ASSESSED = "not_assessed"


class ObligationLevel(str, Enum):
    MANDATORY = "mandatory"
    RECOMMENDED = "recommended"
    INFORMATIVE = "informative"


class VerificationLevel(str, Enum):
    L0 = "L0"
    L1 = "L1"
    L2 = "L2"
    L3 = "L3"
    L4 = "L4"


# ─── Value Objects ───────────────────────────────────────────────────────────

@dataclass(frozen=True)
class PolicyRule:
    """A single rule within a policy."""
    name: str
    description: str
    condition: dict[str, Any]  # {"type": "cedar"|"rego", "expression": "..."}
    effect: Action
    priority: int = 0
    approvers: list[str] = field(default_factory=list)
    limit_expression: Optional[str] = None


@dataclass(frozen=True)
class PolicyScope:
    """Scope defining which agents/resources/environments a policy applies to."""
    agents: list[str] = field(default_factory=list)  # empty = all
    models: list[str] = field(default_factory=list)
    resources: list[str] = field(default_factory=list)
    environments: list[str] = field(default_factory=list)
    risk_tiers: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class FrameworkMapping:
    """Mapping to a specific compliance framework."""
    framework: str
    version: str
    control_ids: list[str]
    section_refs: list[str] = field(default_factory=list)
    obligation_level: ObligationLevel = ObligationLevel.MANDATORY


@dataclass(frozen=True)
class EvidenceRequirement:
    """Requirement for evidence to satisfy a control."""
    evidence_type: EvidenceType
    criteria: list[str] = field(default_factory=list)
    threshold: float = 0.0
    retention: Optional[str] = None


@dataclass(frozen=True)
class AssessmentCriterion:
    """A single assessment criterion."""
    criterion_id: str
    name: str
    description: str
    framework_mapping: dict[str, str]  # framework -> control_id
    test_method: str
    threshold: float = 0.8
    weight: float = 1.0


@dataclass(frozen=True)
class AssessmentResult:
    """Result of a single criterion evaluation."""
    criterion_id: str
    score: float  # 0.0 to 1.0
    passed: bool
    details: dict[str, Any] = field(default_factory=dict)
    evidence_refs: list[str] = field(default_factory=list)
    raw_output: Optional[str] = None


@dataclass(frozen=True)
class EvidenceProof:
    """Cryptographic proof for evidence."""
    merkle_root: str
    merkle_path: list[str] = field(default_factory=list)
    signature: str = ""


@dataclass(frozen=True)
class EvidenceSubject:
    """What/who the evidence is about."""
    agent_id: str
    agent_did: str = ""
    session_id: str = ""
    action: str = ""
    tool: str = ""
    resource: str = ""


@dataclass(frozen=True)
class EvidenceDecision:
    """The governance decision recorded in evidence."""
    effect: Action
    reason: str
    confidence: float = 1.0


@dataclass(frozen=True)
class EvidenceContext:
    """Additional context for evidence."""
    input_hash: str = ""
    output_hash: str = ""
    environment: str = ""
    trace_id: str = ""


# ─── Core Abstraction 1: Policy ──────────────────────────────────────────────

@dataclass
class Policy:
    """A declarative, version-controlled rule set that governs AI agent behavior."""

    name: str
    version: str
    description: str = ""
    owner: str = ""
    status: PolicyStatus = PolicyStatus.DRAFT
    category: PolicyCategory = PolicyCategory.CUSTOM
    policy_language: PolicyLanguage = PolicyLanguage.CEDAR
    rules: list[PolicyRule] = field(default_factory=list)
    scope: PolicyScope = field(default_factory=PolicyScope)
    framework_mappings: list[FrameworkMapping] = field(default_factory=list)
    default_action: Action = Action.DENY
    on_timeout: Action = Action.DENY
    enforcement_strategy: EnforcementStrategy = EnforcementStrategy.DENY_OVERRIDES
    effective_date: Optional[datetime] = None
    expiration_date: Optional[datetime] = None
    review_cycle: str = "quarterly"
    approvers: list[str] = field(default_factory=list)
    parent_policy_id: Optional[str] = None
    change_description: str = ""
    tags: list[str] = field(default_factory=list)
    labels: dict[str, str] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: str = ""
    updated_by: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "owner": self.owner,
            "status": self.status.value,
            "category": self.category.value,
            "policy_language": self.policy_language.value,
            "rules": [
                {
                    "name": r.name,
                    "description": r.description,
                    "condition": r.condition,
                    "effect": r.effect.value,
                    "priority": r.priority,
                    "approvers": r.approvers,
                    "limit_expression": r.limit_expression,
                }
                for r in self.rules
            ],
            "scope": {
                "agents": self.scope.agents,
                "models": self.scope.models,
                "resources": self.scope.resources,
                "environments": self.scope.environments,
                "risk_tiers": self.scope.risk_tiers,
            },
            "framework_mappings": [
                {
                    "framework": fm.framework,
                    "version": fm.version,
                    "control_ids": fm.control_ids,
                    "section_refs": fm.section_refs,
                    "obligation_level": fm.obligation_level.value,
                }
                for fm in self.framework_mappings
            ],
            "default_action": self.default_action.value,
            "on_timeout": self.on_timeout.value,
            "enforcement_strategy": self.enforcement_strategy.value,
            "effective_date": self.effective_date.isoformat() if self.effective_date else None,
            "expiration_date": self.expiration_date.isoformat() if self.expiration_date else None,
            "review_cycle": self.review_cycle,
            "approvers": self.approvers,
            "parent_policy_id": self.parent_policy_id,
            "change_description": self.change_description,
            "tags": self.tags,
            "labels": self.labels,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "created_by": self.created_by,
            "updated_by": self.updated_by,
        }

    def sorted_rules(self) -> list[PolicyRule]:
        """Return rules sorted by priority (highest first)."""
        return sorted(self.rules, key=lambda r: r.priority, reverse=True)

    def compute_hash(self) -> str:
        """Compute SHA-256 hash of the policy content for integrity verification."""
        content = json.dumps(self.to_dict(), sort_keys=True, default=str)
        return hashlib.sha256(content.encode()).hexdigest()


# ─── Core Abstraction 2: Evidence ────────────────────────────────────────────

@dataclass
class Evidence:
    """A structured, cryptographically verifiable record of a governance decision."""

    evidence_id: str
    schema_version: str = "grcclaw/evidence/v1"
    type: EvidenceType = EvidenceType.POLICY_EVALUATION
    subject: EvidenceSubject = field(default_factory=EvidenceSubject)
    policy_id: str = ""
    policy_version: str = ""
    rule_id: str = ""
    decision: EvidenceDecision = field(
        default_factory=lambda: EvidenceDecision(effect=Action.DENY, reason="")
    )
    context: EvidenceContext = field(default_factory=EvidenceContext)
    compliance_tags: list[str] = field(default_factory=list)
    proof: Optional[EvidenceProof] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    title: str = ""
    description: str = ""
    verification_level: VerificationLevel = VerificationLevel.L0
    verification_details: dict[str, bool] = field(default_factory=dict)
    chain_of_custody: list[dict[str, Any]] = field(default_factory=list)
    oscal_version: str = "1.1"
    retention_class: str = "security_log"
    retention_period: str = "7years"
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "evidence_id": self.evidence_id,
            "schema_version": self.schema_version,
            "type": self.type.value,
            "subject": {
                "agent_id": self.subject.agent_id,
                "agent_did": self.subject.agent_did,
                "session_id": self.subject.session_id,
                "action": self.subject.action,
                "tool": self.subject.tool,
                "resource": self.subject.resource,
            },
            "policy_id": self.policy_id,
            "policy_version": self.policy_version,
            "rule_id": self.rule_id,
            "decision": {
                "effect": self.decision.effect.value,
                "reason": self.decision.reason,
                "confidence": self.decision.confidence,
            },
            "context": {
                "input_hash": self.context.input_hash,
                "output_hash": self.context.output_hash,
                "environment": self.context.environment,
                "trace_id": self.context.trace_id,
            },
            "compliance_tags": self.compliance_tags,
            "proof": {
                "merkle_root": self.proof.merkle_root if self.proof else "",
                "merkle_path": self.proof.merkle_path if self.proof else [],
                "signature": self.proof.signature if self.proof else "",
            },
            "timestamp": self.timestamp.isoformat(),
            "title": self.title,
            "description": self.description,
            "verification_level": self.verification_level.value,
            "verification_details": self.verification_details,
            "chain_of_custody": self.chain_of_custody,
            "oscal_version": self.oscal_version,
            "retention_class": self.retention_class,
            "retention_period": self.retention_period,
        }

    def compute_hash(self) -> str:
        """Compute SHA-256 hash of the evidence for integrity verification."""
        content = json.dumps(self.to_dict(), sort_keys=True, default=str)
        return hashlib.sha256(content.encode()).hexdigest()


# ─── Core Abstraction 3: Enforcement ─────────────────────────────────────────

@dataclass
class AgentAction:
    """An action the agent wants to take."""
    agent_id: str
    action: str
    tool: str = ""
    arguments: dict[str, Any] = field(default_factory=dict)
    resource: str = ""
    session_id: str = ""


@dataclass
class EnforcementContext:
    """Full context for enforcement evaluation."""
    environment: str = "production"
    trace_id: str = ""
    span_id: str = ""
    tenant_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class EnforcementResult:
    """Result of an enforcement decision."""
    effect: Action
    reason: str
    policy_id: str = ""
    rule_id: str = ""
    evidence_id: str = ""
    transformed_input: Optional[dict[str, Any]] = None
    approval_ticket: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)
    evaluation_latency_ms: int = 0
    total_latency_ms: int = 0
    deterministic: bool = True
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "effect": self.effect.value,
            "reason": self.reason,
            "policy_id": self.policy_id,
            "rule_id": self.rule_id,
            "evidence_id": self.evidence_id,
            "transformed_input": self.transformed_input,
            "approval_ticket": self.approval_ticket,
            "metadata": self.metadata,
            "evaluation_latency_ms": self.evaluation_latency_ms,
            "total_latency_ms": self.total_latency_ms,
            "deterministic": self.deterministic,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class Enforcement:
    """A runtime governance decision applied to an agent action or system event."""

    decision: Action
    agent_id: str
    action_type: str
    resource: str = ""
    tool_name: str = ""
    parameters: dict[str, Any] = field(default_factory=dict)
    policy_id: str = ""
    policy_version: str = ""
    rules_evaluated: list[dict[str, Any]] = field(default_factory=list)
    evaluation_context: dict[str, Any] = field(default_factory=dict)
    decision_reason: str = ""
    confidence_score: float = 1.0
    deterministic: bool = True
    redaction_fields: list[str] = field(default_factory=list)
    redaction_method: str = "mask"
    escalation_id: Optional[str] = None
    escalated_to: str = ""
    escalation_status: str = ""
    quarantine_id: Optional[str] = None
    quarantine_scope: str = ""
    evidence_ids: list[str] = field(default_factory=list)
    audit_trail_id: str = ""
    requested_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    decided_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    executed_at: Optional[datetime] = None
    evaluation_latency_ms: int = 0
    total_latency_ms: int = 0
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "decision": self.decision.value,
            "agent_id": self.agent_id,
            "action_type": self.action_type,
            "resource": self.resource,
            "tool_name": self.tool_name,
            "parameters": self.parameters,
            "policy_id": self.policy_id,
            "policy_version": self.policy_version,
            "rules_evaluated": self.rules_evaluated,
            "evaluation_context": self.evaluation_context,
            "decision_reason": self.decision_reason,
            "confidence_score": self.confidence_score,
            "deterministic": self.deterministic,
            "redaction_fields": self.redaction_fields,
            "redaction_method": self.redaction_method,
            "escalation_id": self.escalation_id,
            "escalated_to": self.escalated_to,
            "escalation_status": self.escalation_status,
            "quarantine_id": self.quarantine_id,
            "quarantine_scope": self.quarantine_scope,
            "evidence_ids": self.evidence_ids,
            "audit_trail_id": self.audit_trail_id,
            "requested_at": self.requested_at.isoformat(),
            "decided_at": self.decided_at.isoformat(),
            "executed_at": self.executed_at.isoformat() if self.executed_at else None,
            "evaluation_latency_ms": self.evaluation_latency_ms,
            "total_latency_ms": self.total_latency_ms,
        }


# ─── Core Abstraction 4: Assessment ──────────────────────────────────────────

@dataclass
class Assessment:
    """A technical assessment of an AI system."""

    assessment_id: str
    system_id: str
    assessment_type: AssessmentType
    criteria: list[AssessmentCriterion] = field(default_factory=list)
    results: list[AssessmentResult] = field(default_factory=list)
    overall_score: float = 0.0
    overall_result: ComplianceStatus = ComplianceStatus.NOT_ASSESSED
    evidence: list[Evidence] = field(default_factory=list)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    assessor: str = ""
    status: AssessmentStatus = AssessmentStatus.NOT_STARTED
    framework: str = ""
    control_ids: list[str] = field(default_factory=list)
    assessment_period_start: Optional[datetime] = None
    assessment_period_end: Optional[datetime] = None
    methodology: str = ""
    assessor_type: str = "automated"
    risks_identified: int = 0
    risks_mitigated: int = 0
    risks_accepted: int = 0
    residual_risk_score: float = 0.0
    previous_assessment_id: Optional[str] = None
    change_summary: str = ""
    next_assessment_date: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def compute_overall_score(self) -> float:
        """Compute weighted overall score from individual criterion results."""
        if not self.results:
            return 0.0
        total_weight = sum(
            c.weight for c in self.criteria if any(r.criterion_id == c.criterion_id for r in self.results)
        )
        if total_weight == 0:
            return sum(r.score for r in self.results) / len(self.results)
        weighted_sum = sum(
            r.score * next((c.weight for c in self.criteria if c.criterion_id == r.criterion_id), 1.0)
            for r in self.results
        )
        return round(weighted_sum / total_weight, 4)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "assessment_id": self.assessment_id,
            "system_id": self.system_id,
            "assessment_type": self.assessment_type.value,
            "criteria": [
                {
                    "criterion_id": c.criterion_id,
                    "name": c.name,
                    "description": c.description,
                    "framework_mapping": c.framework_mapping,
                    "test_method": c.test_method,
                    "threshold": c.threshold,
                    "weight": c.weight,
                }
                for c in self.criteria
            ],
            "results": [
                {
                    "criterion_id": r.criterion_id,
                    "score": r.score,
                    "passed": r.passed,
                    "details": r.details,
                    "evidence_refs": r.evidence_refs,
                    "raw_output": r.raw_output,
                }
                for r in self.results
            ],
            "overall_score": self.overall_score,
            "overall_result": self.overall_result.value,
            "evidence": [e.to_dict() for e in self.evidence],
            "timestamp": self.timestamp.isoformat(),
            "assessor": self.assessor,
            "status": self.status.value,
            "framework": self.framework,
            "control_ids": self.control_ids,
            "assessment_period_start": self.assessment_period_start.isoformat() if self.assessment_period_start else None,
            "assessment_period_end": self.assessment_period_end.isoformat() if self.assessment_period_end else None,
            "methodology": self.methodology,
            "assessor_type": self.assessor_type,
            "risks_identified": self.risks_identified,
            "risks_mitigated": self.risks_mitigated,
            "risks_accepted": self.risks_accepted,
            "residual_risk_score": self.residual_risk_score,
            "previous_assessment_id": self.previous_assessment_id,
            "change_summary": self.change_summary,
            "next_assessment_date": self.next_assessment_date.isoformat() if self.next_assessment_date else None,
            "valid_until": self.valid_until.isoformat() if self.valid_until else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


# ─── Core Abstraction 5: Compliance ──────────────────────────────────────────

@dataclass
class ComplianceControlMapping:
    """Compliance status for a single control."""
    control_id: str
    control_title: str
    control_family: str = ""
    status: ComplianceStatus = ComplianceStatus.NOT_ASSESSED
    evidence_ids: list[str] = field(default_factory=list)
    assessment_id: str = ""
    last_verified: Optional[datetime] = None
    next_due: Optional[datetime] = None
    gap_description: str = ""
    remediation_plan_id: Optional[str] = None


@dataclass
class Compliance:
    """A computed compliance posture mapping controls to frameworks with evidence status."""

    organization_id: str
    scope_type: str = "organization"
    scope_id: str = ""
    scope_name: str = ""
    framework: str = ""
    framework_version: str = ""
    framework_name: str = ""
    overall_status: ComplianceStatus = ComplianceStatus.NOT_ASSESSED
    compliance_score: float = 0.0
    trend: str = "unknown"  # improving, stable, declining, unknown
    control_mappings: list[ComplianceControlMapping] = field(default_factory=list)
    total_controls: int = 0
    compliant_controls: int = 0
    partial_controls: int = 0
    non_compliant_controls: int = 0
    not_applicable_controls: int = 0
    not_assessed_controls: int = 0
    coverage_percentage: float = 0.0
    total_evidence_items: int = 0
    evidence_by_type: dict[str, int] = field(default_factory=dict)
    evidence_by_verification_level: dict[str, int] = field(default_factory=dict)
    oldest_evidence: Optional[datetime] = None
    newest_evidence: Optional[datetime] = None
    last_report_generated: Optional[datetime] = None
    report_ids: list[str] = field(default_factory=list)
    computed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    valid_until: Optional[datetime] = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def compute_score(self) -> float:
        """Compute compliance score from control mappings."""
        if not self.control_mappings:
            return 0.0
        total = len(self.control_mappings)
        compliant = sum(1 for cm in self.control_mappings if cm.status == ComplianceStatus.COMPLIANT)
        partial = sum(1 for cm in self.control_mappings if cm.status == ComplianceStatus.PARTIALLY_COMPLIANT)
        return round((compliant + partial * 0.5) / total, 4)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "organization_id": self.organization_id,
            "scope_type": self.scope_type,
            "scope_id": self.scope_id,
            "scope_name": self.scope_name,
            "framework": self.framework,
            "framework_version": self.framework_version,
            "framework_name": self.framework_name,
            "overall_status": self.overall_status.value,
            "compliance_score": self.compliance_score,
            "trend": self.trend,
            "control_mappings": [
                {
                    "control_id": cm.control_id,
                    "control_title": cm.control_title,
                    "control_family": cm.control_family,
                    "status": cm.status.value,
                    "evidence_ids": cm.evidence_ids,
                    "assessment_id": cm.assessment_id,
                    "last_verified": cm.last_verified.isoformat() if cm.last_verified else None,
                    "next_due": cm.next_due.isoformat() if cm.next_due else None,
                    "gap_description": cm.gap_description,
                    "remediation_plan_id": cm.remediation_plan_id,
                }
                for cm in self.control_mappings
            ],
            "total_controls": self.total_controls,
            "compliant_controls": self.compliant_controls,
            "partial_controls": self.partial_controls,
            "non_compliant_controls": self.non_compliant_controls,
            "not_applicable_controls": self.not_applicable_controls,
            "not_assessed_controls": self.not_assessed_controls,
            "coverage_percentage": self.coverage_percentage,
            "total_evidence_items": self.total_evidence_items,
            "evidence_by_type": self.evidence_by_type,
            "evidence_by_verification_level": self.evidence_by_verification_level,
            "oldest_evidence": self.oldest_evidence.isoformat() if self.oldest_evidence else None,
            "newest_evidence": self.newest_evidence.isoformat() if self.newest_evidence else None,
            "last_report_generated": self.last_report_generated.isoformat() if self.last_report_generated else None,
            "report_ids": self.report_ids,
            "computed_at": self.computed_at.isoformat(),
            "valid_until": self.valid_until.isoformat() if self.valid_until else None,
        }


# ─── Compliance Mapping ──────────────────────────────────────────────────────

@dataclass
class ComplianceMapping:
    """Maps a single control to multiple frameworks."""

    mapping_id: str
    control_id: str
    control_name: str
    description: str = ""
    framework_mappings: dict[str, FrameworkMapping] = field(default_factory=dict)
    evidence_requirements: list[EvidenceRequirement] = field(default_factory=list)
    assessment_criteria: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "mapping_id": self.mapping_id,
            "control_id": self.control_id,
            "control_name": self.control_name,
            "description": self.description,
            "framework_mappings": {
                k: {
                    "framework": v.framework,
                    "version": v.version,
                    "control_ids": v.control_ids,
                    "section_refs": v.section_refs,
                    "obligation_level": v.obligation_level.value,
                }
                for k, v in self.framework_mappings.items()
            },
            "evidence_requirements": [
                {
                    "evidence_type": er.evidence_type.value,
                    "criteria": er.criteria,
                    "threshold": er.threshold,
                    "retention": er.retention,
                }
                for er in self.evidence_requirements
            ],
            "assessment_criteria": self.assessment_criteria,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
