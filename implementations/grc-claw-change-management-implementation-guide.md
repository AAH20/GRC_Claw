# GRC_Claw Change Management Implementation Guide

**Document ID:** GRC-CHG-IMPL-001  
**Version:** 1.0  
**Date:** 2026-10-01  
**References:** GRC-CHG-001 (Change Management Spec v2.0), GRC-DPL-001 (Deployment Governance Spec v1.0)

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Change Request Workflow](#2-change-request-workflow)
3. [Change Impact Analysis](#3-change-impact-analysis)
4. [Change Risk Scoring](#4-change-risk-scoring)
5. [Change Approval Workflow](#5-change-approval-workflow)
6. [Change Conflict Detection](#6-change-conflict-detection)
7. [Change Rollback Automation](#7-change-rollback-automation)
8. [Change Compliance Verification](#8-change-compliance-verification)
9. [Integration Example](#9-integration-example)

---

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                GRC_Claw Change Management System                     │
│                                                                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │   Change     │  │   Change     │  │   Change     │              │
│  │   Request    │  │   Impact     │  │   Risk       │              │
│  │   Workflow   │  │   Analysis   │  │   Scoring    │              │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘              │
│         │                 │                 │                       │
│         └────────────┬────┘                 │                       │
│                      ▼                      │                       │
│              ┌──────────────┐               │                       │
│              │   Change     │◄──────────────┘                       │
│              │   Approval   │                                        │
│              │   Workflow   │                                        │
│              └──────┬───────┘                                        │
│                     │                                                │
│         ┌───────────┼───────────┐                                    │
│         ▼           ▼           ▼                                    │
│  ┌────────────┐ ┌──────────┐ ┌──────────────┐                      │
│  │  Change    │ │  Change  │ │  Change      │                      │
│  │  Conflict  │ │  Rollback│ │  Compliance  │                      │
│  │  Detection │ │  Automation│ │ Verification │                      │
│  └────────────┘ └──────────┘ └──────────────┘                      │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    Audit Trail (Hash-Chained)                  │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. Change Request Workflow

Implements the full change request lifecycle: creation → triage → submission → tracking.

```python
"""
GRC_Claw Change Request Workflow
Implements: Spec §4 (Change Approval Workflow), §6 (Change Audit Trail)
"""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


# ─── Enums ────────────────────────────────────────────────────────────

class ChangeCategory(str, Enum):
    MODEL_UPDATE = "model_update"
    DATA_UPDATE = "data_update"
    POLICY_UPDATE = "policy_update"
    INFRASTRUCTURE_UPDATE = "infrastructure_update"


class ChangeStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    TRIAGED = "triaged"
    IMPACT_ASSESSMENT = "impact_assessment"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    IMPLEMENTING = "implementing"
    IMPLEMENTED = "implemented"
    VERIFIED = "verified"
    ROLLED_BACK = "rolled_back"
    CANCELLED = "cancelled"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ResourceType(str, Enum):
    MODEL = "model"
    DATA = "data"
    POLICY = "policy"
    INFRASTRUCTURE = "infrastructure"
    AGENT = "agent"


# ─── Data Models ──────────────────────────────────────────────────────

@dataclass
class AffectedResource:
    resource_type: ResourceType
    resource_id: str
    resource_name: str
    current_version: str
    target_version: str


@dataclass
class ChangeRequest:
    """Core change request entity per Spec Appendix A."""
    cr_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    description: str = ""
    category: ChangeCategory = ChangeCategory.MODEL_UPDATE
    sub_type: str = ""
    requester_id: str = ""
    requester_role: str = ""
    requester_department: str = ""
    affected_resources: list[AffectedResource] = field(default_factory=list)
    justification: str = ""
    risk_level: RiskLevel = RiskLevel.LOW
    status: ChangeStatus = ChangeStatus.DRAFT
    proposed_implementation_date: str = ""
    rollback_plan: str = ""
    mitigation_plan: str = ""
    communication_plan: str = ""
    attachments: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    audit_trail: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    def compute_hash(self) -> str:
        """Compute SHA-256 hash of the change request for audit integrity."""
        content = json.dumps(self.to_dict(), sort_keys=True, default=str)
        return hashlib.sha256(content.encode()).hexdigest()


# ─── Audit Trail ──────────────────────────────────────────────────────

class AuditTrail:
    """
    Immutable, hash-chained audit trail per Spec §6.
    Each record chains to the previous via SHA-256 hashing.
    """

    def __init__(self):
        self._records: list[dict] = []
        self._previous_hash: str = "0" * 64  # Genesis previous hash

    def append(
        self,
        change_request_id: str,
        event_type: str,
        actor_type: str,
        actor_id: str,
        actor_role: str,
        resource_type: str,
        resource_id: str,
        resource_name: str,
        resource_version: str,
        action: str,
        details: dict,
        environment: str = "prod",
        change_category: str = "",
        risk_level: str = "",
        impact_score: float = 0.0,
    ) -> dict:
        record = {
            "record-id": str(uuid.uuid4()),
            "change-request-id": change_request_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event-type": event_type,
            "actor": {
                "type": actor_type,
                "id": actor_id,
                "role": actor_role,
                "authentication-method": "sso-mfa",
            },
            "resource": {
                "type": resource_type,
                "id": resource_id,
                "name": resource_name,
                "version": resource_version,
            },
            "action": action,
            "details": details,
            "context": {
                "environment": environment,
                "change-category": change_category,
                "risk-level": risk_level,
                "impact-score": impact_score,
            },
            "integrity": {
                "record-hash": "",
                "previous-record-hash": self._previous_hash,
                "signature": "",
            },
        }
        # Compute record hash
        record_content = json.dumps(record, sort_keys=True, default=str)
        record_hash = hashlib.sha256(record_content.encode()).hexdigest()
        record["integrity"]["record-hash"] = record_hash
        # Sign (simplified — production uses ECDSA)
        record["integrity"]["signature"] = f"sig-{record_hash[:32]}"

        self._records.append(record)
        self._previous_hash = record_hash
        return record

    def verify_chain(self) -> bool:
        """Verify hash chain integrity."""
        prev_hash = "0" * 64
        for record in self._records:
            stored_prev = record["integrity"]["previous-record-hash"]
            if stored_prev != prev_hash:
                return False
            # Recompute hash
            test_record = {k: v for k, v in record.items() if k != "integrity"}
            test_record["integrity"] = {
                "record-hash": "",
                "previous-record-hash": stored_prev,
                "signature": "",
            }
            content = json.dumps(test_record, sort_keys=True, default=str)
            computed = hashlib.sha256(content.encode()).hexdigest()
            if computed != record["integrity"]["record-hash"]:
                return False
            prev_hash = record["integrity"]["record-hash"]
        return True

    def get_records(self, change_request_id: Optional[str] = None) -> list[dict]:
        if change_request_id:
            return [r for r in self._records if r["change-request-id"] == change_request_id]
        return list(self._records)


# ─── Change Request Service ───────────────────────────────────────────

class ChangeRequestService:
    """
    Main service for change request lifecycle management.
    Implements Spec §4.1 workflow: Submit → Triage → Impact Assess → Approval → Implement
    """

    # Valid status transitions
    TRANSITIONS = {
        ChangeStatus.DRAFT: {ChangeStatus.SUBMITTED, ChangeStatus.CANCELLED},
        ChangeStatus.SUBMITTED: {ChangeStatus.TRIAGED, ChangeStatus.CANCELLED},
        ChangeStatus.TRIAGED: {ChangeStatus.IMPACT_ASSESSMENT, ChangeStatus.PENDING_APPROVAL, ChangeStatus.CANCELLED},
        ChangeStatus.IMPACT_ASSESSMENT: {ChangeStatus.PENDING_APPROVAL, ChangeStatus.CANCELLED},
        ChangeStatus.PENDING_APPROVAL: {ChangeStatus.APPROVED, ChangeStatus.REJECTED, ChangeStatus.CANCELLED},
        ChangeStatus.APPROVED: {ChangeStatus.IMPLEMENTING, ChangeStatus.CANCELLED},
        ChangeStatus.IMPLEMENTING: {ChangeStatus.IMPLEMENTED, ChangeStatus.ROLLED_BACK},
        ChangeStatus.IMPLEMENTED: {ChangeStatus.VERIFIED, ChangeStatus.ROLLED_BACK},
        ChangeStatus.REJECTED: {ChangeStatus.DRAFT},
        ChangeStatus.ROLLED_BACK: {ChangeStatus.DRAFT},
        ChangeStatus.VERIFIED: set(),
        ChangeStatus.CANCELLED: set(),
    }

    def __init__(self):
        self._requests: dict[str, ChangeRequest] = {}
        self._audit = AuditTrail()

    def create_change_request(
        self,
        title: str,
        description: str,
        category: ChangeCategory,
        sub_type: str,
        requester_id: str,
        requester_role: str,
        affected_resources: list[AffectedResource],
        justification: str,
        proposed_date: str,
        rollback_plan: str = "",
        mitigation_plan: str = "",
    ) -> ChangeRequest:
        """Create a new change request in DRAFT status."""
        cr = ChangeRequest(
            title=title,
            description=description,
            category=category,
            sub_type=sub_type,
            requester_id=requester_id,
            requester_role=requester_role,
            affected_resources=affected_resources,
            justification=justification,
            proposed_implementation_date=proposed_date,
            rollback_plan=rollback_plan,
            mitigation_plan=mitigation_plan,
        )
        self._requests[cr.cr_id] = cr
        self._audit.append(
            change_request_id=cr.cr_id,
            event_type="created",
            actor_type="user",
            actor_id=requester_id,
            actor_role=requester_role,
            resource_type=affected_resources[0].resource_type.value if affected_resources else "unknown",
            resource_id=affected_resources[0].resource_id if affected_resources else "",
            resource_name=affected_resources[0].resource_name if affected_resources else "",
            resource_version=affected_resources[0].current_version if affected_resources else "",
            action="Change request created",
            details={"title": title, "category": category.value, "sub_type": sub_type},
            change_category=category.value,
        )
        return cr

    def submit(self, cr_id: str, submitter_id: str) -> ChangeRequest:
        """Submit a change request for triage."""
        cr = self._get_request(cr_id)
        self._transition(cr, ChangeStatus.SUBMITTED, submitter_id, "Change request submitted")
        return cr

    def triage(self, cr_id: str, risk_level: RiskLevel, triager_id: str) -> ChangeRequest:
        """Assign risk level and route for impact assessment."""
        cr = self._get_request(cr_id)
        cr.risk_level = risk_level
        self._transition(cr, ChangeStatus.TRIAGED, triager_id, f"Triaged as {risk_level.value}")
        return cr

    def start_impact_assessment(self, cr_id: str, assessor_id: str) -> ChangeRequest:
        """Begin the Change Impact Assessment phase."""
        cr = self._get_request(cr_id)
        self._transition(cr, ChangeStatus.IMPACT_ASSESSMENT, assessor_id, "Impact assessment initiated")
        return cr

    def complete_impact_assessment(self, cr_id: str, assessor_id: str) -> ChangeRequest:
        """Complete CIA and route to approval."""
        cr = self._get_request(cr_id)
        self._transition(cr, ChangeStatus.PENDING_APPROVAL, assessor_id, "Impact assessment completed")
        return cr

    def approve(self, cr_id: str, approver_id: str, approver_role: str) -> ChangeRequest:
        """Approve a change request."""
        cr = self._get_request(cr_id)
        self._transition(cr, ChangeStatus.APPROVED, approver_id, f"Approved by {approver_role}")
        return cr

    def reject(self, cr_id: str, rejecter_id: str, reason: str) -> ChangeRequest:
        """Reject a change request."""
        cr = self._get_request(cr_id)
        self._transition(cr, ChangeStatus.REJECTED, rejecter_id, f"Rejected: {reason}")
        return cr

    def implement(self, cr_id: str, implementer_id: str) -> ChangeRequest:
        """Begin implementation."""
        cr = self._get_request(cr_id)
        self._transition(cr, ChangeStatus.IMPLEMENTING, implementer_id, "Implementation started")
        return cr

    def verify(self, cr_id: str, verifier_id: str) -> ChangeRequest:
        """Mark change as verified post-implementation."""
        cr = self._get_request(cr_id)
        self._transition(cr, ChangeStatus.VERIFIED, verifier_id, "Post-implementation verification passed")
        return cr

    def rollback(self, cr_id: str, initiator_id: str, reason: str) -> ChangeRequest:
        """Initiate rollback of a change."""
        cr = self._get_request(cr_id)
        self._transition(cr, ChangeStatus.ROLLED_BACK, initiator_id, f"Rollback: {reason}")
        return cr

    def get_audit_trail(self, cr_id: str) -> list[dict]:
        return self._audit.get_records(cr_id)

    def verify_audit_integrity(self) -> bool:
        return self._audit.verify_chain()

    # ─── Private Helpers ──────────────────────────────────────────

    def _get_request(self, cr_id: str) -> ChangeRequest:
        if cr_id not in self._requests:
            raise ValueError(f"Change request {cr_id} not found")
        return self._requests[cr_id]

    def _transition(self, cr: ChangeRequest, new_status: ChangeStatus, actor_id: str, action: str):
        current = cr.status
        if new_status not in self.TRANSITIONS.get(current, set()):
            raise ValueError(f"Invalid transition: {current.value} → {new_status.value}")
        cr.status = new_status
        cr.updated_at = datetime.now(timezone.utc).isoformat()
        self._audit.append(
            change_request_id=cr.cr_id,
            event_type=new_status.value,
            actor_type="user",
            actor_id=actor_id,
            actor_role="",
            resource_type=cr.affected_resources[0].resource_type.value if cr.affected_resources else "unknown",
            resource_id=cr.affected_resources[0].resource_id if cr.affected_resources else "",
            resource_name=cr.affected_resources[0].resource_name if cr.affected_resources else "",
            resource_version=cr.affected_resources[0].current_version if cr.affected_resources else "",
            action=action,
            details={"previous_status": current.value, "new_status": new_status.value},
            change_category=cr.category.value,
            risk_level=cr.risk_level.value,
        )


# ─── Usage Example ────────────────────────────────────────────────────

def demo_change_request_workflow():
    service = ChangeRequestService()

    # 1. Create a model retraining change request
    cr = service.create_change_request(
        title="Retrain fraud detection model with Q3 data",
        description="Full retraining of fraud-detection-v2 on Q3 2026 transaction data",
        category=ChangeCategory.MODEL_UPDATE,
        sub_type="retraining",
        requester_id="user-001",
        requester_role="ML Engineer",
        affected_resources=[
            AffectedResource(
                resource_type=ResourceType.MODEL,
                resource_id="model-fraud-001",
                resource_name="Fraud Detection Model v2",
                current_version="2.3.1",
                target_version="3.0.0",
            )
        ],
        justification="Q3 data shows 15% improvement in fraud patterns coverage",
        proposed_date="2026-10-15T02:00:00Z",
        rollback_plan="Revert to model v2.3.1 via blue-green switch",
        mitigation_plan="Shadow deployment for 72h before canary",
    )
    print(f"Created CR: {cr.cr_id}")

    # 2. Submit
    service.submit(cr.cr_id, "user-001")

    # 3. Triage — high risk (retraining = high per spec §4.3.1)
    service.triage(cr.cr_id, RiskLevel.HIGH, "grc-analyst-001")

    # 4. Impact assessment
    service.start_impact_assessment(cr.cr_id, "grc-analyst-001")
    service.complete_impact_assessment(cr.cr_id, "grc-analyst-001")

    # 5. CAB approval
    service.approve(cr.cr_id, "cab-chair-001", "CAB Chair")

    # 6. Implement
    service.implement(cr.cr_id, "ml-eng-001")

    # 7. Verify
    service.verify(cr.cr_id, "ml-eng-001")

    # Check audit trail
    trail = service.get_audit_trail(cr.cr_id)
    print(f"Audit trail records: {len(trail)}")
    print(f"Audit chain valid: {service.verify_audit_integrity()}")

    return cr


if __name__ == "__main__":
    demo_change_request_workflow()
```

---

## 3. Change Impact Analysis

Implements the 6-dimension CIA framework from Spec §5.

```python
"""
GRC_Claw Change Impact Analysis (CIA)
Implements: Spec §5 (Change Impact Assessment)
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class ImpactLevel(str, Enum):
    NEGLIGIBLE = "negligible"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


# Dimension weights per Spec §5.2
DIMENSION_WEIGHTS = {
    "compliance": 0.25,
    "risk": 0.25,
    "performance": 0.15,
    "operational": 0.15,
    "business": 0.10,
    "technical": 0.10,
}

# Minimum score triggers per Spec §5.3
COMPLIANCE_TRIGGERS = {
    "high_risk_ai_system": 3,       # EU AI Act Class 3/4
    "regulated_training_data": 3,    # Regulated AI system training data
    "policy_mapped_to_regulation": 2,
    "invalidates_evidence": 4,
}

RISK_TRIGGERS = {
    "safety_critical_system": 4,
    "agent_tool_access_change": 3,
    "known_bias_issues": 4,
    "increases_attack_surface": 3,
}

PERFORMANCE_TRIGGERS = {
    "accuracy_degradation_gt_2pct": 3,
    "p99_latency_increase_gt_20pct": 3,
    "throughput_reduction_gt_10pct": 3,
    "resource_increase_gt_25pct": 2,
}


@dataclass
class DimensionScore:
    """Single CIA dimension score (1-5 scale)."""
    score: int  # 1-5
    justification: str
    evidence: list[str] = field(default_factory=list)

    def __post_init__(self):
        if not 1 <= self.score <= 5:
            raise ValueError(f"Score must be 1-5, got {self.score}")


@dataclass
class MitigationAction:
    """Mitigation action for dimensions scoring ≥3."""
    action: str
    owner: str
    timeline: str
    status: str = "planned"


@dataclass
class ChangeImpactAssessment:
    """
    Full CIA per Spec §5.1-§5.5.
    Evaluates 6 dimensions: Compliance, Risk, Performance, Operational, Business, Technical.
    """
    cia_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    change_request_id: str = ""
    assessor: str = ""
    assessment_date: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    dimensions: dict[str, DimensionScore] = field(default_factory=dict)
    composite_impact_score: float = 0.0
    impact_level: ImpactLevel = ImpactLevel.NEGLIGIBLE
    mitigation_plan: list[MitigationAction] = field(default_factory=list)
    rollback_plan: str = ""
    communication_plan: str = ""
    verification_plan: str = ""

    def compute_composite_score(self) -> float:
        """
        CIS = Σ (Dimension Score × Dimension Weight)
        Range: 1.0 (lowest) to 5.0 (highest)
        """
        total = 0.0
        for dim_name, weight in DIMENSION_WEIGHTS.items():
            if dim_name in self.dimensions:
                total += self.dimensions[dim_name].score * weight
        self.composite_impact_score = round(total, 2)
        self.impact_level = self._classify_impact(self.composite_impact_score)
        return self.composite_impact_score

    def _classify_impact(self, score: float) -> ImpactLevel:
        """Classify impact per Spec §5.4 CIA Approval Matrix."""
        if score < 2.0:
            return ImpactLevel.NEGLIGIBLE
        elif score < 3.0:
            return ImpactLevel.LOW
        elif score < 4.0:
            return ImpactLevel.MODERATE
        else:
            return ImpactLevel.HIGH

    def generate_mitigations(self) -> list[MitigationAction]:
        """Auto-generate mitigation actions for dimensions scoring ≥3."""
        mitigations = []
        for dim_name, dim_score in self.dimensions.items():
            if dim_score.score >= 3:
                mitigations.append(MitigationAction(
                    action=f"Mitigate {dim_name} impact (score: {dim_score.score})",
                    owner="TBD",
                    timeline="Before implementation",
                ))
        self.mitigation_plan = mitigations
        return mitigations

    def to_report(self) -> dict:
        """Generate CIA deliverable report per Spec §5.5."""
        return {
            "cia-id": self.cia_id,
            "change-request-id": self.change_request_id,
            "assessor": self.assessor,
            "assessment-date": self.assessment_date,
            "dimensions": {
                name: {
                    "score": ds.score,
                    "justification": ds.justification,
                    "evidence": ds.evidence,
                }
                for name, ds in self.dimensions.items()
            },
            "composite-impact-score": self.composite_impact_score,
            "impact-level": self.impact_level.value,
            "mitigation-plan": [
                {"action": m.action, "owner": m.owner, "timeline": m.timeline}
                for m in self.mitigation_plan
            ],
            "rollback-plan": self.rollback_plan,
            "communication-plan": self.communication_plan,
            "verification-plan": self.verification_plan,
        }


class ChangeImpactAnalyzer:
    """
    Service for conducting Change Impact Assessments.
    Applies trigger rules from Spec §5.3 to auto-adjust dimension scores.
    """

    def __init__(self):
        self._assessments: dict[str, ChangeImpactAssessment] = {}

    def create_assessment(
        self,
        change_request_id: str,
        assessor: str,
        compliance_score: int = 1,
        risk_score: int = 1,
        performance_score: int = 1,
        operational_score: int = 1,
        business_score: int = 1,
        technical_score: int = 1,
        justifications: Optional[dict[str, str]] = None,
        evidence: Optional[dict[str, list[str]]] = None,
    ) -> ChangeImpactAssessment:
        """Create a new CIA with initial scores."""
        justifications = justifications or {}
        evidence = evidence or {}

        cia = ChangeImpactAssessment(
            change_request_id=change_request_id,
            assessor=assessor,
            dimensions={
                "compliance": DimensionScore(
                    score=compliance_score,
                    justification=justifications.get("compliance", ""),
                    evidence=evidence.get("compliance", []),
                ),
                "risk": DimensionScore(
                    score=risk_score,
                    justification=justifications.get("risk", ""),
                    evidence=evidence.get("risk", []),
                ),
                "performance": DimensionScore(
                    score=performance_score,
                    justification=justifications.get("performance", ""),
                    evidence=evidence.get("performance", []),
                ),
                "operational": DimensionScore(
                    score=operational_score,
                    justification=justifications.get("operational", ""),
                    evidence=evidence.get("operational", []),
                ),
                "business": DimensionScore(
                    score=business_score,
                    justification=justifications.get("business", ""),
                    evidence=evidence.get("business", []),
                ),
                "technical": DimensionScore(
                    score=technical_score,
                    justification=justifications.get("technical", ""),
                    evidence=evidence.get("technical", []),
                ),
            },
        )
        cia.compute_composite_score()
        self._assessments[cia.cia_id] = cia
        return cia

    def apply_compliance_triggers(
        self,
        cia: ChangeImpactAssessment,
        is_high_risk_ai: bool = False,
        is_regulated_training_data: bool = False,
        is_policy_mapped: bool = False,
        invalidates_evidence: bool = False,
    ) -> ChangeImpactAssessment:
        """Apply compliance impact triggers from Spec §5.3.1."""
        triggers = []
        if is_high_risk_ai:
            triggers.append(COMPLIANCE_TRIGGERS["high_risk_ai_system"])
        if is_regulated_training_data:
            triggers.append(COMPLIANCE_TRIGGERS["regulated_training_data"])
        if is_policy_mapped:
            triggers.append(COMPLIANCE_TRIGGERS["policy_mapped_to_regulation"])
        if invalidates_evidence:
            triggers.append(COMPLIANCE_TRIGGERS["invalidates_evidence"])

        if triggers:
            min_score = max(triggers)
            current = cia.dimensions["compliance"].score
            if current < min_score:
                cia.dimensions["compliance"].score = min_score
                cia.dimensions["compliance"].justification += (
                    f" [Auto-adjusted to {min_score} by compliance trigger]"
                )
            cia.compute_composite_score()
        return cia

    def apply_risk_triggers(
        self,
        cia: ChangeImpactAssessment,
        is_safety_critical: bool = False,
        affects_agent_tools: bool = False,
        has_known_bias: bool = False,
        increases_attack_surface: bool = False,
    ) -> ChangeImpactAssessment:
        """Apply risk impact triggers from Spec §5.3.2."""
        triggers = []
        if is_safety_critical:
            triggers.append(RISK_TRIGGERS["safety_critical_system"])
        if affects_agent_tools:
            triggers.append(RISK_TRIGGERS["agent_tool_access_change"])
        if has_known_bias:
            triggers.append(RISK_TRIGGERS["known_bias_issues"])
        if increases_attack_surface:
            triggers.append(RISK_TRIGGERS["increases_attack_surface"])

        if triggers:
            min_score = max(triggers)
            current = cia.dimensions["risk"].score
            if current < min_score:
                cia.dimensions["risk"].score = min_score
                cia.dimensions["risk"].justification += (
                    f" [Auto-adjusted to {min_score} by risk trigger]"
                )
            cia.compute_composite_score()
        return cia

    def get_approval_requirement(self, cia: ChangeImpactAssessment) -> str:
        """Get approval requirement per Spec §5.4."""
        score = cia.composite_impact_score
        if score < 2.0:
            return "Auto-approve (Standard Change)"
        elif score < 3.0:
            return "System Owner approval"
        elif score < 4.0:
            return "CAB review required"
        else:
            return "CAB + executive approval required"


# ─── Usage Example ────────────────────────────────────────────────────

def demo_impact_analysis():
    analyzer = ChangeImpactAnalyzer()

    # Create CIA for a model retraining on a regulated system
    cia = analyzer.create_assessment(
        change_request_id="cr-001",
        assessor="grc-analyst-001",
        compliance_score=2,
        risk_score=3,
        performance_score=2,
        operational_score=2,
        business_score=1,
        technical_score=3,
        justifications={
            "compliance": "Model used in EU AI Act Class 3 system",
            "risk": "Retraining may introduce bias in fraud detection",
            "technical": "Requires full model re-deployment and shadow testing",
        },
    )

    # Apply triggers
    analyzer.apply_compliance_triggers(
        cia,
        is_high_risk_ai=True,  # EU AI Act Class 3
        is_regulated_training_data=True,
    )
    analyzer.apply_risk_triggers(
        cia,
        has_known_bias=True,  # Known bias issues in current model
    )

    # Generate mitigations for dimensions ≥3
    cia.generate_mitigations()

    report = cia.to_report()
    print(f"Composite Impact Score: {report['composite-impact-score']}")
    print(f"Impact Level: {report['impact-level']}")
    print(f"Approval Required: {analyzer.get_approval_requirement(cia)}")
    print(f"Mitigations: {len(report['mitigation_plan'])}")

    return cia


if __name__ == "__main__":
    demo_impact_analysis()
```

---

## 4. Change Risk Scoring

Implements the CRS algorithm from Spec §15.

```python
"""
GRC_Claw Change Risk Scoring (CRS)
Implements: Spec §15 (Change Risk Scoring Algorithm)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class RiskBand(str, Enum):
    MINIMAL = "minimal"       # 0-19
    LOW = "low"               # 20-39
    MODERATE = "moderate"     # 40-59
    HIGH = "high"             # 60-79
    CRITICAL = "critical"     # 80-100


# Default weights per Spec §15.2
DEFAULT_WEIGHTS = {
    "reversibility": 0.15,
    "blast_radius": 0.20,
    "compliance": 0.20,
    "performance": 0.10,
    "operational": 0.10,
    "technical_complexity": 0.10,
    "historical": 0.10,
    "environmental": 0.05,
}

# Category-specific weights per Spec §15.5
CATEGORY_WEIGHTS = {
    "model_update": {
        "reversibility": 0.15, "blast_radius": 0.20, "compliance": 0.20,
        "performance": 0.15, "operational": 0.10, "technical_complexity": 0.10,
        "historical": 0.05, "environmental": 0.05,
    },
    "data_update": {
        "reversibility": 0.10, "blast_radius": 0.15, "compliance": 0.25,
        "performance": 0.10, "operational": 0.10, "technical_complexity": 0.15,
        "historical": 0.10, "environmental": 0.05,
    },
    "policy_update": {
        "reversibility": 0.15, "blast_radius": 0.20, "compliance": 0.25,
        "performance": 0.05, "operational": 0.10, "technical_complexity": 0.05,
        "historical": 0.05, "environmental": 0.05,
    },
    "infrastructure_update": {
        "reversibility": 0.20, "blast_radius": 0.20, "compliance": 0.15,
        "performance": 0.10, "operational": 0.10, "technical_complexity": 0.15,
        "historical": 0.05, "environmental": 0.05,
    },
}


@dataclass
class RiskFactors:
    """
    Eight risk factors, each scored 0-100.
    See Spec §15.3 for detailed scoring criteria.
    """
    reversibility: int = 0        # RF: 0=easy rollback, 100=irreversible
    blast_radius: int = 0         # BF: 0=single tool, 100=org-wide critical
    compliance: int = 0           # CF: 0=no impact, 100=multi-regulation
    performance: int = 0          # PF: 0=no impact, 100=severe degradation
    operational: int = 0          # OF: 0=no impact, 100=major transformation
    technical_complexity: int = 0 # TF: 0=single file, 100=architectural
    historical: int = 0           # HF: 0=many successes, 100=no history/failures
    environmental: int = 0        # EF: 0=stable, 100=critical incident+freeze

    def __post_init__(self):
        for name, value in self.__dict__.items():
            if not 0 <= value <= 100:
                raise ValueError(f"{name} must be 0-100, got {value}")


@dataclass
class ChangeRiskScore:
    """
    Computed CRS with factor breakdown and risk band.
    """
    crs_id: str = ""
    change_request_id: str = ""
    factors: RiskFactors = field(default_factory=RiskFactors)
    weights: dict[str, float] = field(default_factory=lambda: DEFAULT_WEIGHTS.copy())
    score: float = 0.0
    risk_band: RiskBand = RiskBand.MINIMAL
    approval_authority: str = ""
    deployment_strategy: str = ""

    def to_dict(self) -> dict:
        return {
            "crs_id": self.crs_id,
            "change-request-id": self.change_request_id,
            "factors": {
                "reversibility": self.factors.reversibility,
                "blast_radius": self.factors.blast_radius,
                "compliance": self.factors.compliance,
                "performance": self.factors.performance,
                "operational": self.factors.operational,
                "technical_complexity": self.factors.technical_complexity,
                "historical": self.factors.historical,
                "environmental": self.factors.environmental,
            },
            "weights": self.weights,
            "score": self.score,
            "risk_band": self.risk_band.value,
            "approval_authority": self.approval_authority,
            "deployment_strategy": self.deployment_strategy,
        }


class ChangeRiskScorer:
    """
    Computes the Change Risk Score per Spec §15.2:
    CRS = Σ (wᵢ × Fᵢ) for i in 8 factors
    """

    # Risk band definitions per Spec §15.4
    RISK_BANDS = {
        RiskBand.MINIMAL: {"range": (0, 19), "authority": "Auto-approve", "strategy": "Direct deployment"},
        RiskBand.LOW: {"range": (20, 39), "authority": "System Owner", "strategy": "Standard deployment"},
        RiskBand.MODERATE: {"range": (40, 59), "authority": "System Owner + GRC Analyst", "strategy": "Canary deployment"},
        RiskBand.HIGH: {"range": (60, 79), "authority": "CAB", "strategy": "Canary + enhanced monitoring"},
        RiskBand.CRITICAL: {"range": (80, 100), "authority": "CAB + CISO + Risk Committee", "strategy": "Blue-green + CAB approval"},
    }

    def compute_score(
        self,
        change_request_id: str,
        factors: RiskFactors,
        category: str = "model_update",
        custom_weights: Optional[dict[str, float]] = None,
    ) -> ChangeRiskScore:
        """Compute CRS with category-specific or custom weights."""
        weights = custom_weights or CATEGORY_WEIGHTS.get(category, DEFAULT_WEIGHTS)

        # Validate weights sum to 1.0
        total_weight = sum(weights.values())
        if abs(total_weight - 1.0) > 0.001:
            raise ValueError(f"Weights must sum to 1.0, got {total_weight}")

        # Compute weighted score
        score = (
            weights["reversibility"] * factors.reversibility +
            weights["blast_radius"] * factors.blast_radius +
            weights["compliance"] * factors.compliance +
            weights["performance"] * factors.performance +
            weights["operational"] * factors.operational +
            weights["technical_complexity"] * factors.technical_complexity +
            weights["historical"] * factors.historical +
            weights["environmental"] * factors.environmental
        )

        score = round(score, 1)
        risk_band = self._classify_risk(score)
        band_info = self.RISK_BANDS[risk_band]

        return ChangeRiskScore(
            crs_id=f"crs-{change_request_id}",
            change_request_id=change_request_id,
            factors=factors,
            weights=weights,
            score=score,
            risk_band=risk_band,
            approval_authority=band_info["authority"],
            deployment_strategy=band_info["strategy"],
        )

    def _classify_risk(self, score: float) -> RiskBand:
        """Classify score into risk band per Spec §15.4."""
        if score <= 19:
            return RiskBand.MINIMAL
        elif score <= 39:
            return RiskBand.LOW
        elif score <= 59:
            return RiskBand.MODERATE
        elif score <= 79:
            return RiskBand.HIGH
        else:
            return RiskBand.CRITICAL

    def get_approval_sla(self, risk_band: RiskBand) -> str:
        """Get SLA per Spec §4.2."""
        slas = {
            RiskBand.MINIMAL: "Immediate",
            RiskBand.LOW: "4 hours",
            RiskBand.MODERATE: "24 hours",
            RiskBand.HIGH: "72 hours",
            RiskBand.CRITICAL: "120 hours",
        }
        return slas[risk_band]


# ─── Usage Example ────────────────────────────────────────────────────

def demo_risk_scoring():
    scorer = ChangeRiskScorer()

    # Score a model retraining change
    factors = RiskFactors(
        reversibility=30,      # Semi-automated rollback, <5 min RTO
        blast_radius=50,       # Multiple systems, <1000 users, PII
        compliance=60,         # Regulatory requirement change
        performance=20,        # Within 5% of baseline expected
        operational=30,        # Runbook update required
        technical_complexity=50,  # Multi-component, <1 day testing
        historical=40,         # 10-20 similar changes, >90% success
        environmental=20,      # Stable environment
    )

    crs = scorer.compute_score(
        change_request_id="cr-001",
        factors=factors,
        category="model_update",
    )

    print(f"CRS Score: {crs.score}")
    print(f"Risk Band: {crs.risk_band.value}")
    print(f"Approval Authority: {crs.approval_authority}")
    print(f"Deployment Strategy: {crs.deployment_strategy}")
    print(f"SLA: {scorer.get_approval_sla(crs.risk_band)}")

    return crs


if __name__ == "__main__":
    demo_risk_scoring()
```

---

## 5. Change Approval Workflow

Implements the risk-based, multi-tier approval workflow from Spec §4.

```python
"""
GRC_Claw Change Approval Workflow
Implements: Spec §4 (Change Approval Workflow), §4.4 (CAB), §4.5 (Emergency Changes)
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"
    EXPIRED = "expired"


class ApproverRole(str, Enum):
    SYSTEM_OWNER = "system_owner"
    GRC_ANALYST = "grc_analyst"
    CAB_CHAIR = "cab_chair"
    CAB_MEMBER = "cab_member"
    MODEL_OWNER = "model_owner"
    DATA_OWNER = "data_owner"
    POLICY_OWNER = "policy_owner"
    SECURITY_TEAM = "security_team"
    COMPLIANCE_OFFICER = "compliance_officer"
    CISO = "ciso"
    RISK_COMMITTEE = "risk_committee"
    INFRASTRUCTURE_OWNER = "infrastructure_owner"


@dataclass
class ApprovalRecord:
    """Single approval decision record."""
    approval_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    change_request_id: str = ""
    approver_id: str = ""
    approver_role: ApproverRole = ApproverRole.SYSTEM_OWNER
    status: ApprovalStatus = ApprovalStatus.PENDING
    decision: str = ""  # "approve", "reject", "approve_with_conditions"
    conditions: list[str] = field(default_factory=list)
    rationale: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    signature: str = ""


@dataclass
class CABMember:
    """CAB member per Spec §4.4.1."""
    member_id: str
    name: str
    role: str  # "chair", "ai_ml", "security", "compliance", "operations", "business"
    can_vote: bool = True


class ChangeAdvisoryBoard:
    """
    CAB per Spec §4.4.
    Quorum: 4 of 6 members (must include CAB Chair + at least one of Security/Compliance).
    """

    def __init__(self):
        self.members: list[CABMember] = []
        self._initialize_default_members()

    def _initialize_default_members(self):
        self.members = [
            CABMember("cab-001", "Alice Chen", "chair"),
            CABMember("cab-002", "Bob Kumar", "ai_ml"),
            CABMember("cab-003", "Carol Smith", "security"),
            CABMember("cab-004", "David Lee", "compliance"),
            CABMember("cab-005", "Eve Johnson", "operations"),
            CABMember("cab-006", "Frank Brown", "business"),
        ]

    def check_quorum(self, present_member_ids: list[str]) -> bool:
        """Check if quorum is met per Spec §4.4.2."""
        present = [m for m in self.members if m.member_id in present_member_ids]
        if len(present) < 4:
            return False
        # Must include chair
        has_chair = any(m.role == "chair" for m in present)
        # Must include at least one of security/compliance
        has_security_or_compliance = any(
            m.role in ("security", "compliance") for m in present
        )
        return has_chair and has_security_or_compliance

    def vote(self, change_request_id: str, votes: dict[str, str]) -> dict:
        """
        Record CAB votes and determine outcome.
        votes: {member_id: "approve"|"reject"|"abstain"}
        """
        approvals = sum(1 for v in votes.values() if v == "approve")
        rejections = sum(1 for v in votes.values() if v == "reject")
        total_votes = len([v for v in votes.values() if v != "abstain"])

        if total_votes == 0:
            return {"status": "no_votes", "outcome": "pending"}

        # Consensus preferred, majority if not reachable
        if approvals == total_votes:
            outcome = "approved_unanimous"
        elif approvals > rejections:
            outcome = "approved_majority"
        elif rejections > approvals:
            outcome = "rejected"
        else:
            outcome = "tie"  # Chair breaks tie

        return {
            "change_request_id": change_request_id,
            "votes": votes,
            "approvals": approvals,
            "rejections": rejections,
            "outcome": outcome,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


class ChangeApprovalWorkflow:
    """
    Risk-based approval routing per Spec §4.2-§4.3.
    Determines approval path based on risk level and change category.
    """

    # Approval paths per Spec §4.3
    APPROVAL_PATHS = {
        ("model_update", "retraining"): {
            "risk": "high",
            "path": [ApproverRole.CAB_CHAIR, ApproverRole.MODEL_OWNER, ApproverRole.COMPLIANCE_OFFICER],
            "special": ["Bias/fairness re-test", "Performance regression test"],
        },
        ("model_update", "fine_tuning"): {
            "risk": "high",
            "path": [ApproverRole.CAB_CHAIR, ApproverRole.MODEL_OWNER, ApproverRole.COMPLIANCE_OFFICER],
            "special": ["Training data lineage verification"],
        },
        ("model_update", "architecture_change"): {
            "risk": "critical",
            "path": [ApproverRole.CAB_CHAIR, ApproverRole.CISO, ApproverRole.RISK_COMMITTEE],
            "special": ["Full re-validation", "Red team test", "Regulatory notification"],
        },
        ("model_update", "hyperparameter_update"): {
            "risk": "medium",
            "path": [ApproverRole.SYSTEM_OWNER, ApproverRole.GRC_ANALYST],
            "special": ["Performance benchmark comparison"],
        },
        ("model_update", "agent_configuration"): {
            "risk": "high",
            "path": [ApproverRole.CAB_CHAIR, ApproverRole.SECURITY_TEAM],
            "special": ["Capability declaration update", "Tool access audit"],
        },
        ("data_update", "data_addition"): {
            "risk": "medium",
            "path": [ApproverRole.SYSTEM_OWNER, ApproverRole.GRC_ANALYST],
            "special": ["Data quality validation", "PII scan"],
        },
        ("data_update", "data_removal"): {
            "risk": "high",
            "path": [ApproverRole.CAB_CHAIR, ApproverRole.DATA_OWNER, ApproverRole.COMPLIANCE_OFFICER],
            "special": ["GDPR/CCPA impact assessment", "Consent verification"],
        },
        ("data_update", "schema_change"): {
            "risk": "high",
            "path": [ApproverRole.CAB_CHAIR, ApproverRole.DATA_OWNER, ApproverRole.COMPLIANCE_OFFICER],
            "special": ["Downstream impact analysis", "Migration plan"],
        },
        ("policy_update", "new_policy"): {
            "risk": "medium",
            "path": [ApproverRole.GRC_ANALYST, ApproverRole.POLICY_OWNER, ApproverRole.COMPLIANCE_OFFICER],
            "special": ["Framework mapping", "Conflict check"],
        },
        ("policy_update", "enforcement_change"): {
            "risk": "critical",
            "path": [ApproverRole.CAB_CHAIR, ApproverRole.CISO, ApproverRole.RISK_COMMITTEE],
            "special": ["Dry-run validation", "Rollback plan", "Stakeholder communication"],
        },
        ("infrastructure_update", "security_patch"): {
            "risk": "critical",
            "path": [ApproverRole.CAB_CHAIR, ApproverRole.CISO, ApproverRole.RISK_COMMITTEE],
            "special": ["Vulnerability scan", "Rollback plan"],
        },
        ("infrastructure_update", "compute_scaling"): {
            "risk": "medium",
            "path": [ApproverRole.SYSTEM_OWNER, ApproverRole.GRC_ANALYST],
            "special": ["Capacity planning validation"],
        },
    }

    def __init__(self):
        self.cab = ChangeAdvisoryBoard()
        self._approvals: dict[str, list[ApprovalRecord]] = {}

    def get_approval_path(self, category: str, sub_type: str) -> dict:
        """Get the approval path for a change category/sub-type."""
        key = (category, sub_type)
        if key not in self.APPROVAL_PATHS:
            # Default to medium risk path
            return {
                "risk": "medium",
                "path": [ApproverRole.SYSTEM_OWNER, ApproverRole.GRC_ANALYST],
                "special": [],
            }
        return self.APPROVAL_PATHS[key]

    def request_approval(
        self,
        change_request_id: str,
        category: str,
        sub_type: str,
        requester_id: str,
    ) -> list[ApprovalRecord]:
        """Create approval records for each required approver in the path."""
        path = self.get_approval_path(category, sub_type)
        approvals = []
        for role in path["path"]:
            approval = ApprovalRecord(
                change_request_id=change_request_id,
                approver_id="",  # To be filled when assigned
                approver_role=role,
                status=ApprovalStatus.PENDING,
            )
            approvals.append(approval)
        self._approvals[change_request_id] = approvals
        return approvals

    def record_approval(
        self,
        change_request_id: str,
        approver_id: str,
        approver_role: ApproverRole,
        decision: str,
        rationale: str = "",
        conditions: Optional[list[str]] = None,
    ) -> ApprovalRecord:
        """Record an approval decision."""
        if change_request_id not in self._approvals:
            raise ValueError(f"No approvals found for {change_request_id}")

        for approval in self._approvals[change_request_id]:
            if approval.approver_role == approver_role and approval.status == ApprovalStatus.PENDING:
                approval.approver_id = approver_id
                approval.decision = decision
                approval.rationale = rationale
                approval.conditions = conditions or []
                approval.status = ApprovalStatus.APPROVED if decision == "approve" else ApprovalStatus.REJECTED
                approval.signature = f"sig-{approver_id}-{datetime.now(timezone.utc).timestamp()}"
                return approval

        raise ValueError(f"No pending approval for role {approver_role}")

    def check_approval_complete(self, change_request_id: str) -> dict:
        """Check if all required approvals are obtained."""
        if change_request_id not in self._approvals:
            return {"complete": False, "status": "no_approvals"}

        approvals = self._approvals[change_request_id]
        pending = [a for a in approvals if a.status == ApprovalStatus.PENDING]
        rejected = [a for a in approvals if a.status == ApprovalStatus.REJECTED]

        if rejected:
            return {
                "complete": True,
                "status": "rejected",
                "rejected_by": [a.approver_role.value for a in rejected],
            }

        if pending:
            return {
                "complete": False,
                "status": "pending",
                "pending_roles": [a.approver_role.value for a in pending],
            }

        return {"complete": True, "status": "approved"}

    def initiate_emergency_change(
        self,
        change_request_id: str,
        requester_id: str,
        justification: str,
        interim_approver_id: str,
    ) -> ApprovalRecord:
        """
        Emergency change procedure per Spec §4.5.
        Interim approval by CISO or CTO within 1 hour.
        """
        approval = ApprovalRecord(
            change_request_id=change_request_id,
            approver_id=interim_approver_id,
            approver_role=ApproverRole.CISO,
            status=ApprovalStatus.APPROVED,
            decision="approve",
            rationale=f"Emergency change: {justification}",
            conditions=[
                "Retrospective CAB review within 48 hours",
                "Complete documentation within 72 hours",
                "Post-implementation verification within 24 hours",
            ],
        )
        if change_request_id not in self._approvals:
            self._approvals[change_request_id] = []
        self._approvals[change_request_id].append(approval)
        return approval


# ─── Usage Example ────────────────────────────────────────────────────

def demo_approval_workflow():
    workflow = ChangeApprovalWorkflow()

    # Get approval path for model retraining
    path = workflow.get_approval_path("model_update", "retraining")
    print(f"Approval path: {[r.value for r in path['path']]}")
    print(f"Special requirements: {path['special']}")

    # Request approvals
    approvals = workflow.request_approval(
        change_request_id="cr-001",
        category="model_update",
        sub_type="retraining",
        requester_id="user-001",
    )
    print(f"Required approvals: {len(approvals)}")

    # Record approvals
    workflow.record_approval("cr-001", "cab-001", ApproverRole.CAB_CHAIR, "approve", "Reviewed and approved")
    workflow.record_approval("cr-001", "model-001", ApproverRole.MODEL_OWNER, "approve", "Performance validated")
    result = workflow.record_approval("cr-001", "compliance-001", ApproverRole.COMPLIANCE_OFFICER, "approve", "Compliance verified")

    # Check completion
    status = workflow.check_approval_complete("cr-001")
    print(f"Approval status: {status}")

    # CAB voting demo
    votes = {
        "cab-001": "approve",
        "cab-002": "approve",
        "cab-003": "approve",
        "cab-004": "approve",
        "cab-005": "abstain",
        "cab-006": "approve",
    }
    cab_result = workflow.cab.vote("cr-001", votes)
    print(f"CAB outcome: {cab_result['outcome']}")

    return workflow


if __name__ == "__main__":
    demo_approval_workflow()
```

---

## 6. Change Conflict Detection

Implements the conflict detection engine from Spec §16.

```python
"""
GRC_Claw Change Conflict Detection
Implements: Spec §16 (Change Conflict Detection)
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class ConflictType(str, Enum):
    RESOURCE_CONTENTION = "resource_contention"
    DEPENDENCY_VIOLATION = "dependency_violation"
    POLICY_CONTRADICTION = "policy_contradiction"
    COMPLIANCE_GAP = "compliance_gap"
    TEMPORAL_CONFLICT = "temporal_conflict"
    ROLLBACK_INTERFERENCE = "rollback_interference"
    AGENT_INTERACTION_CONFLICT = "agent_interaction_conflict"
    VERSION_SKEW = "version_skew"


class ConflictSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ConflictStatus(str, Enum):
    DETECTED = "detected"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    ESCALATED = "escalated"


@dataclass
class Conflict:
    """Detected conflict between two or more changes."""
    conflict_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    conflict_type: ConflictType = ConflictType.RESOURCE_CONTENTION
    severity: ConflictSeverity = ConflictSeverity.MEDIUM
    status: ConflictStatus = ConflictStatus.DETECTED
    change_request_ids: list[str] = field(default_factory=list)
    description: str = ""
    resolution_options: list[str] = field(default_factory=list)
    detected_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    resolved_at: str = ""
    resolution: str = ""


@dataclass
class ChangeWindow:
    """Implementation window for a change."""
    change_request_id: str
    resource_ids: list[str]
    start_time: str
    end_time: str
    risk_level: str = "low"


class ConflictDetectionEngine:
    """
    Automated conflict detection per Spec §16.
    Evaluates rules R1-R15 from Spec §16.4.
    """

    # Severity mapping per Spec §16.5
    SEVERITY_MAP = {
        ConflictType.RESOURCE_CONTENTION: ConflictSeverity.HIGH,
        ConflictType.DEPENDENCY_VIOLATION: ConflictSeverity.CRITICAL,
        ConflictType.POLICY_CONTRADICTION: ConflictSeverity.CRITICAL,
        ConflictType.COMPLIANCE_GAP: ConflictSeverity.HIGH,
        ConflictType.TEMPORAL_CONFLICT: ConflictSeverity.MEDIUM,
        ConflictType.ROLLBACK_INTERFERENCE: ConflictSeverity.HIGH,
        ConflictType.AGENT_INTERACTION_CONFLICT: ConflictSeverity.HIGH,
        ConflictType.VERSION_SKEW: ConflictSeverity.MEDIUM,
    }

    def __init__(self):
        self._conflicts: list[Conflict] = []
        self._active_changes: dict[str, ChangeWindow] = {}

    def register_change(self, window: ChangeWindow):
        """Register an active change for conflict detection."""
        self._active_changes[window.change_request_id] = window

    def detect_conflicts(self, new_change: ChangeWindow) -> list[Conflict]:
        """
        Detect conflicts between a new change and all active changes.
        Implements rules R1-R15 from Spec §16.4.
        """
        conflicts = []
        for cr_id, active in self._active_changes.items():
            if cr_id == new_change.change_request_id:
                continue

            # R1: Resource Contention — same resource, overlapping windows
            shared_resources = set(new_change.resource_ids) & set(active.resource_ids)
            if shared_resources and self._windows_overlap(new_change, active):
                conflicts.append(self._create_conflict(
                    ConflictType.RESOURCE_CONTENTION,
                    [new_change.change_request_id, cr_id],
                    f"Shared resources: {shared_resources}",
                    ["Reschedule one change", "Merge changes", "Add explicit dependency"],
                ))

            # R7: Temporal Conflict — two high-risk changes in same window
            if (new_change.risk_level in ("high", "critical")
                and active.risk_level in ("high", "critical")
                and self._windows_overlap(new_change, active)):
                conflicts.append(self._create_conflict(
                    ConflictType.TEMPORAL_CONFLICT,
                    [new_change.change_request_id, cr_id],
                    "Two high-risk changes scheduled in overlapping windows",
                    ["Reschedule to different windows", "Add enhanced monitoring"],
                ))

            # R13: Version Skew — change tests against version being modified
            # (Simplified check — production would compare version numbers)
            if shared_resources:
                conflicts.append(self._create_conflict(
                    ConflictType.VERSION_SKEW,
                    [new_change.change_request_id, cr_id],
                    f"Potential version skew on resources: {shared_resources}",
                    ["Coordinate version timing", "Add integration test"],
                ))

        self._conflicts.extend(conflicts)
        return conflicts

    def detect_policy_contradiction(
        self,
        cr_id_1: str,
        cr_id_2: str,
        policy_id: str,
        value_1: str,
        value_2: str,
    ) -> Optional[Conflict]:
        """R4: Two policy changes modify the same rule with different values."""
        if value_1 != value_2:
            conflict = self._create_conflict(
                ConflictType.POLICY_CONTRADICTION,
                [cr_id_1, cr_id_2],
                f"Policy {policy_id}: conflicting values '{value_1}' vs '{value_2}'",
                ["Reconcile values", "Merge changes", "Escalate to CAB"],
            )
            self._conflicts.append(conflict)
            return conflict
        return None

    def detect_rollback_interference(
        self,
        cr_id_1: str,
        cr_id_2: str,
        resource_id: str,
    ) -> Optional[Conflict]:
        """R3/R15: Rolling back one change would break another."""
        conflict = self._create_conflict(
            ConflictType.ROLLBACK_INTERFERENCE,
            [cr_id_1, cr_id_2],
            f"Rollback of one change affects resource {resource_id} used by another",
            ["Add rollback dependency", "Coordinate rollback order", "Merge changes"],
        )
        self._conflicts.append(conflict)
        return conflict

    def detect_agent_interaction_conflict(
        self,
        cr_id_1: str,
        cr_id_2: str,
        agent_id: str,
    ) -> Optional[Conflict]:
        """R10: Two agent config changes modify the same agent's tool access."""
        conflict = self._create_conflict(
            ConflictType.AGENT_INTERACTION_CONFLICT,
            [cr_id_1, cr_id_2],
            f"Agent {agent_id}: conflicting tool access changes",
            ["Reconcile tool access", "Sequence changes", "Security review"],
        )
        self._conflicts.append(conflict)
        return conflict

    def resolve_conflict(self, conflict_id: str, resolution: str) -> Conflict:
        """Mark a conflict as resolved."""
        for c in self._conflicts:
            if c.conflict_id == conflict_id:
                c.status = ConflictStatus.RESOLVED
                c.resolution = resolution
                c.resolved_at = datetime.now(timezone.utc).isoformat()
                return c
        raise ValueError(f"Conflict {conflict_id} not found")

    def get_conflicts(
        self,
        severity: Optional[ConflictSeverity] = None,
        status: Optional[ConflictStatus] = None,
    ) -> list[Conflict]:
        """Get conflicts filtered by severity and/or status."""
        result = self._conflicts
        if severity:
            result = [c for c in result if c.severity == severity]
        if status:
            result = [c for c in result if c.status == status]
        return result

    def _create_conflict(
        self,
        conflict_type: ConflictType,
        cr_ids: list[str],
        description: str,
        resolution_options: list[str],
    ) -> Conflict:
        return Conflict(
            conflict_type=conflict_type,
            severity=self.SEVERITY_MAP[conflict_type],
            change_request_ids=cr_ids,
            description=description,
            resolution_options=resolution_options,
        )

    def _windows_overlap(self, w1: ChangeWindow, w2: ChangeWindow) -> bool:
        """Check if two implementation windows overlap."""
        # Simplified — production would parse ISO timestamps
        return w1.start_time < w2.end_time and w2.start_time < w1.end_time


# ─── Usage Example ────────────────────────────────────────────────────

def demo_conflict_detection():
    engine = ConflictDetectionEngine()

    # Register active changes
    engine.register_change(ChangeWindow(
        change_request_id="cr-001",
        resource_ids=["model-fraud-001", "data-transactions"],
        start_time="2026-10-15T02:00:00Z",
        end_time="2026-10-15T06:00:00Z",
        risk_level="high",
    ))

    engine.register_change(ChangeWindow(
        change_request_id="cr-002",
        resource_ids=["model-fraud-001"],
        start_time="2026-10-15T04:00:00Z",
        end_time="2026-10-15T08:00:00Z",
        risk_level="high",
    ))

    # Detect conflicts for a new change
    new_change = ChangeWindow(
        change_request_id="cr-003",
        resource_ids=["model-fraud-001", "data-transactions"],
        start_time="2026-10-15T05:00:00Z",
        end_time="2026-10-15T09:00:00Z",
        risk_level="high",
    )

    conflicts = engine.detect_conflicts(new_change)
    print(f"Detected {len(conflicts)} conflicts:")
    for c in conflicts:
        print(f"  [{c.severity.value}] {c.conflict_type.value}: {c.description}")
        print(f"    Resolution options: {c.resolution_options}")

    # Policy contradiction
    engine.detect_policy_contradiction(
        "cr-001", "cr-002", "pii-redaction-threshold", "95%", "85%"
    )

    # Agent interaction conflict
    engine.detect_agent_interaction_conflict(
        "cr-001", "cr-002", "agent-email-001"
    )

    # Get critical conflicts
    critical = engine.get_conflicts(severity=ConflictSeverity.CRITICAL)
    print(f"\nCritical conflicts: {len(critical)}")

    return engine


if __name__ == "__main__":
    demo_conflict_detection()
```

---

## 7. Change Rollback Automation

Implements the rollback automation engine from Spec §18.

```python
"""
GRC_Claw Change Rollback Automation
Implements: Spec §18 (Change Rollback Automation)
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Callable


class RollbackLevel(str, Enum):
    L0_MANUAL = "L0"           # < 30 min RTO
    L1_ASSISTED = "L1"         # < 10 min RTO
    L2_SEMI_AUTOMATED = "L2"   # < 5 min RTO
    L3_AUTOMATED = "L3"        # < 1 min RTO
    L4_SELF_HEALING = "L4"     # < 30 sec RTO


class RollbackTriggerType(str, Enum):
    ERROR_RATE_BREACH = "error_rate_breach"
    LATENCY_BREACH = "latency_breach"
    POLICY_VIOLATION_SPIKE = "policy_violation_spike"
    SAFETY_INCIDENT = "safety_incident"
    DRIFT_DETECTION = "drift_detection"
    BIAS_DETECTION = "bias_detection"
    COMPLIANCE_BREACH = "compliance_breach"
    HEALTH_CHECK_FAILURE = "health_check_failure"
    KILL_SWITCH = "kill_switch"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    DEPENDENCY_FAILURE = "dependency_failure"
    MANUAL = "manual"


class RollbackStrategy(str, Enum):
    CANARY_HALT = "canary_halt"
    BLUE_GREEN_SWITCH = "blue_green_switch"
    VERSION_REDEPLOY = "version_redeploy"
    CONFIG_REVERT = "config_revert"
    FEATURE_FLAG_DISABLE = "feature_flag_disable"
    TRAFFIC_SHIFT = "traffic_shift"
    FULL_ROLLBACK = "full_rollback"


class RollbackStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    VERIFIED = "verified"


@dataclass
class RollbackTrigger:
    """A trigger condition for automated rollback."""
    trigger_type: RollbackTriggerType
    condition: str
    severity: str  # "high" or "critical"
    automation_level: RollbackLevel
    threshold: Optional[float] = None
    duration_seconds: Optional[int] = None


@dataclass
class RollbackEvent:
    """A rollback execution event."""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    change_request_id: str = ""
    trigger_type: RollbackTriggerType = RollbackTriggerType.MANUAL
    strategy: RollbackStrategy = RollbackStrategy.VERSION_REDEPLOY
    automation_level: RollbackLevel = RollbackLevel.L0_MANUAL
    status: RollbackStatus = RollbackStatus.PENDING
    started_at: str = ""
    completed_at: str = ""
    rto_target_seconds: int = 0
    rto_actual_seconds: float = 0.0
    verification_passed: bool = False
    steps_executed: list[str] = field(default_factory=list)
    error_message: str = ""


# Trigger definitions per Spec §18.4
TRIGGER_DEFINITIONS = {
    RollbackTriggerType.ERROR_RATE_BREACH: RollbackTrigger(
        trigger_type=RollbackTriggerType.ERROR_RATE_BREACH,
        condition="Error rate > 5% for > 5 minutes",
        severity="high",
        automation_level=RollbackLevel.L3_AUTOMATED,
        threshold=5.0,
        duration_seconds=300,
    ),
    RollbackTriggerType.LATENCY_BREACH: RollbackTrigger(
        trigger_type=RollbackTriggerType.LATENCY_BREACH,
        condition="p99 latency > 2x baseline for > 10 minutes",
        severity="high",
        automation_level=RollbackLevel.L3_AUTOMATED,
        threshold=2.0,
        duration_seconds=600,
    ),
    RollbackTriggerType.POLICY_VIOLATION_SPIKE: RollbackTrigger(
        trigger_type=RollbackTriggerType.POLICY_VIOLATION_SPIKE,
        condition="Policy violations > 0 for > 2 minutes",
        severity="critical",
        automation_level=RollbackLevel.L4_SELF_HEALING,
        threshold=0.0,
        duration_seconds=120,
    ),
    RollbackTriggerType.SAFETY_INCIDENT: RollbackTrigger(
        trigger_type=RollbackTriggerType.SAFETY_INCIDENT,
        condition="Any safety incident detected",
        severity="critical",
        automation_level=RollbackLevel.L4_SELF_HEALING,
    ),
    RollbackTriggerType.DRIFT_DETECTION: RollbackTrigger(
        trigger_type=RollbackTriggerType.DRIFT_DETECTION,
        condition="PSI > 0.3 (severe drift)",
        severity="high",
        automation_level=RollbackLevel.L3_AUTOMATED,
        threshold=0.3,
    ),
    RollbackTriggerType.BIAS_DETECTION: RollbackTrigger(
        trigger_type=RollbackTriggerType.BIAS_DETECTION,
        condition="Bias metrics exceed thresholds",
        severity="high",
        automation_level=RollbackLevel.L2_SEMI_AUTOMATED,
    ),
    RollbackTriggerType.COMPLIANCE_BREACH: RollbackTrigger(
        trigger_type=RollbackTriggerType.COMPLIANCE_BREACH,
        condition="Any compliance violation detected",
        severity="critical",
        automation_level=RollbackLevel.L4_SELF_HEALING,
    ),
    RollbackTriggerType.HEALTH_CHECK_FAILURE: RollbackTrigger(
        trigger_type=RollbackTriggerType.HEALTH_CHECK_FAILURE,
        condition="Health check fails for > 1 minute",
        severity="critical",
        automation_level=RollbackLevel.L4_SELF_HEALING,
        duration_seconds=60,
    ),
    RollbackTriggerType.KILL_SWITCH: RollbackTrigger(
        trigger_type=RollbackTriggerType.KILL_SWITCH,
        condition="Kill switch activated",
        severity="critical",
        automation_level=RollbackLevel.L4_SELF_HEALING,
    ),
    RollbackTriggerType.RESOURCE_EXHAUSTION: RollbackTrigger(
        trigger_type=RollbackTriggerType.RESOURCE_EXHAUSTION,
        condition="CPU/memory/GPU > 95% for > 5 minutes",
        severity="high",
        automation_level=RollbackLevel.L3_AUTOMATED,
        threshold=95.0,
        duration_seconds=300,
    ),
    RollbackTriggerType.DEPENDENCY_FAILURE: RollbackTrigger(
        trigger_type=RollbackTriggerType.DEPENDENCY_FAILURE,
        condition="Critical dependency unavailable",
        severity="high",
        automation_level=RollbackLevel.L3_AUTOMATED,
    ),
}

# Strategy mapping per Spec §18.6
STRATEGY_STEPS = {
    RollbackStrategy.CANARY_HALT: [
        "Stop canary traffic",
        "Verify previous version health",
        "Shift 100% traffic to previous version",
        "Decommission canary",
    ],
    RollbackStrategy.BLUE_GREEN_SWITCH: [
        "Switch load balancer to blue environment",
        "Verify blue environment health",
        "Monitor for 5 minutes",
        "Decommission green environment",
    ],
    RollbackStrategy.VERSION_REDEPLOY: [
        "Pull previous version",
        "Run smoke tests",
        "Deploy previous version",
        "Verify health",
    ],
    RollbackStrategy.CONFIG_REVERT: [
        "Apply previous configuration",
        "Restart if needed",
        "Verify behavior",
    ],
    RollbackStrategy.FEATURE_FLAG_DISABLE: [
        "Toggle feature flag off",
        "Verify feature disabled",
        "Confirm no errors",
    ],
    RollbackStrategy.TRAFFIC_SHIFT: [
        "Update traffic rules",
        "Verify fallback serving",
        "Monitor for 5 minutes",
    ],
    RollbackStrategy.FULL_ROLLBACK: [
        "Identify all components",
        "Roll back each in reverse order",
        "Verify system health",
        "Run full test suite",
    ],
}


class RollbackAutomationEngine:
    """
    Automated rollback engine per Spec §18.
    Supports L0-L4 automation levels with trigger detection and execution.
    """

    # RTO targets per Spec §18.2
    RTO_TARGETS = {
        RollbackLevel.L0_MANUAL: 1800,       # 30 min
        RollbackLevel.L1_ASSISTED: 600,       # 10 min
        RollbackLevel.L2_SEMI_AUTOMATED: 300, # 5 min
        RollbackLevel.L3_AUTOMATED: 60,       # 1 min
        RollbackLevel.L4_SELF_HEALING: 30,    # 30 sec
    }

    def __init__(self):
        self._events: dict[str, RollbackEvent] = {}
        self._executors: dict[RollbackStrategy, Callable] = {}

    def register_executor(self, strategy: RollbackStrategy, executor: Callable):
        """Register an execution function for a rollback strategy."""
        self._executors[strategy] = executor

    def evaluate_triggers(
        self,
        change_request_id: str,
        metrics: dict[str, float],
    ) -> list[RollbackTrigger]:
        """
        Evaluate rollback triggers against current metrics.
        Returns list of triggered conditions.
        """
        triggered = []

        for trigger_type, trigger_def in TRIGGER_DEFINITIONS.items():
            if trigger_type == RollbackTriggerType.MANUAL:
                continue

            # Check if metric exists and exceeds threshold
            metric_value = metrics.get(trigger_type.value)
            if metric_value is not None and trigger_def.threshold is not None:
                if metric_value > trigger_def.threshold:
                    triggered.append(trigger_def)

        return triggered

    def initiate_rollback(
        self,
        change_request_id: str,
        trigger_type: RollbackTriggerType,
        strategy: RollbackStrategy,
        automation_level: RollbackLevel,
    ) -> RollbackEvent:
        """Initiate a rollback event."""
        event = RollbackEvent(
            change_request_id=change_request_id,
            trigger_type=trigger_type,
            strategy=strategy,
            automation_level=automation_level,
            status=RollbackStatus.IN_PROGRESS,
            started_at=datetime.now(timezone.utc).isoformat(),
            rto_target_seconds=self.RTO_TARGETS[automation_level],
        )
        self._events[event.event_id] = event

        # Execute rollback steps
        steps = STRATEGY_STEPS.get(strategy, [])
        for step in steps:
            event.steps_executed.append(step)
            executor = self._executors.get(strategy)
            if executor:
                try:
                    executor(step)
                except Exception as e:
                    event.status = RollbackStatus.FAILED
                    event.error_message = str(e)
                    return event

        event.status = RollbackStatus.COMPLETED
        event.completed_at = datetime.now(timezone.utc).isoformat()
        return event

    def verify_rollback(self, event_id: str, verification_metrics: dict) -> bool:
        """Verify rollback was successful per Spec §18.5."""
        if event_id not in self._events:
            raise ValueError(f"Rollback event {event_id} not found")

        event = self._events[event_id]

        # Check metrics returned to baseline
        error_rate = verification_metrics.get("error_rate", 0)
        latency_p99 = verification_metrics.get("latency_p99", 0)
        policy_violations = verification_metrics.get("policy_violations", 0)

        event.verification_passed = (
            error_rate < 1.0
            and latency_p99 < 1000  # ms
            and policy_violations == 0
        )

        if event.verification_passed:
            event.status = RollbackStatus.VERIFIED

        return event.verification_passed

    def check_rto_compliance(self, event_id: str) -> dict:
        """Check if rollback met RTO target."""
        if event_id not in self._events:
            raise ValueError(f"Rollback event {event_id} not found")

        event = self._events[event_id]
        # Simplified RTO calculation
        return {
            "event_id": event_id,
            "rto_target_seconds": event.rto_target_seconds,
            "rto_actual_seconds": event.rto_actual_seconds,
            "compliant": event.rto_actual_seconds <= event.rto_target_seconds,
        }

    def get_rollback_history(self, change_request_id: str) -> list[RollbackEvent]:
        """Get rollback history for a change request."""
        return [e for e in self._events.values() if e.change_request_id == change_request_id]


# ─── Usage Example ────────────────────────────────────────────────────

def demo_rollback_automation():
    engine = RollbackAutomationEngine()

    # Register a mock executor
    def mock_executor(step: str):
        print(f"  Executing: {step}")

    engine.register_executor(RollbackStrategy.CANARY_HALT, mock_executor)

    # Simulate metrics triggering rollback
    metrics = {
        "error_rate_breach": 7.5,  # > 5% threshold
        "latency_breach": 1.5,
        "policy_violation_spike": 0,
    }

    triggered = engine.evaluate_triggers("cr-001", metrics)
    print(f"Triggered conditions: {len(triggered)}")
    for t in triggered:
        print(f"  {t.trigger_type.value}: {t.condition} (Level {t.automation_level.value})")

    # Initiate rollback
    if triggered:
        event = engine.initiate_rollback(
            change_request_id="cr-001",
            trigger_type=triggered[0].trigger_type,
            strategy=RollbackStrategy.CANARY_HALT,
            automation_level=triggered[0].automation_level,
        )
        print(f"\nRollback event: {event.event_id}")
        print(f"Status: {event.status.value}")
        print(f"Steps executed: {len(event.steps_executed)}")

        # Verify rollback
        verification = engine.verify_rollback(event.event_id, {
            "error_rate": 0.5,
            "latency_p99": 200,
            "policy_violations": 0,
        })
        print(f"Verification passed: {verification}")

    return engine


if __name__ == "__main__":
    demo_rollback_automation()
```

---

## 8. Change Compliance Verification

Implements the CCV engine from Spec §19.

```python
"""
GRC_Claw Change Compliance Verification (CCV)
Implements: Spec §19 (Change Compliance Verification)
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class VerificationPoint(str, Enum):
    PRE_APPROVAL = "pre_approval"
    PRE_IMPLEMENTATION = "pre_implementation"
    POST_IMPLEMENTATION = "post_implementation"


class CheckStatus(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    NOT_APPLICABLE = "not_applicable"


class OverallStatus(str, Enum):
    PASS = "pass"
    PASS_WITH_CONDITIONS = "pass_with_conditions"
    FAIL = "fail"


@dataclass
class ComplianceCheck:
    """Individual compliance verification check."""
    check_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    check_name: str = ""
    status: CheckStatus = CheckStatus.PASS
    details: str = ""
    evidence: list[str] = field(default_factory=list)
    remediation: str = ""
    blocking: bool = True


@dataclass
class ComplianceVerificationReport:
    """Structured CCV report per Spec §19.7."""
    cvr_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    change_request_id: str = ""
    verification_point: VerificationPoint = VerificationPoint.PRE_APPROVAL
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    overall_status: OverallStatus = OverallStatus.PASS
    checks: list[ComplianceCheck] = field(default_factory=list)
    affected_controls: list[str] = field(default_factory=list)
    affected_regulations: list[str] = field(default_factory=list)
    required_actions: list[str] = field(default_factory=list)
    compliance_risk_score: int = 0  # 0-100
    verified_by: str = ""
    verification_method: str = "automated"  # automated, manual, hybrid

    def to_dict(self) -> dict:
        return {
            "cvr-id": self.cvr_id,
            "change-request-id": self.change_request_id,
            "verification-point": self.verification_point.value,
            "timestamp": self.timestamp,
            "overall-status": self.overall_status.value,
            "checks": [
                {
                    "check-id": c.check_id,
                    "check-name": c.check_name,
                    "status": c.status.value,
                    "details": c.details,
                    "evidence": c.evidence,
                    "remediation": c.remediation,
                }
                for c in self.checks
            ],
            "affected-controls": self.affected_controls,
            "affected-regulations": self.affected_regulations,
            "required-actions": self.required_actions,
            "compliance-risk-score": self.compliance_risk_score,
            "verified-by": self.verified_by,
            "verification-method": self.verification_method,
        }


class ComplianceVerificationEngine:
    """
    Automated Change Compliance Verification per Spec §19.
    Runs checks at three verification points: pre-approval, pre-implementation, post-implementation.
    """

    # Pre-approval checks per Spec §19.3
    PRE_APPROVAL_CHECKS = [
        ("policy_mapping_verification", True),
        ("control_coverage_check", True),
        ("regulatory_alignment", True),
        ("evidence_validity", True),
        ("data_lineage_verification", True),  # data changes only
        ("cross_border_impact", True),        # if cross-border
        ("notification_check", False),        # flags for action
    ]

    # Pre-implementation checks per Spec §19.4
    PRE_IMPLEMENTATION_CHECKS = [
        ("policy_engine_evaluation", True),
        ("compliance_evidence_generation", True),
        ("bias_fairness_retest", True),       # model/data changes
        ("security_scan", True),              # infrastructure changes
        ("pii_scan", True),                   # data/model changes
        ("adversarial_test", True),           # model changes
        ("human_oversight_verification", True),  # high/critical risk
    ]

    def __init__(self):
        self._reports: dict[str, ComplianceVerificationReport] = {}

    def run_pre_approval_checks(
        self,
        change_request_id: str,
        category: str,
        is_data_change: bool = False,
        is_cross_border: bool = False,
    ) -> ComplianceVerificationReport:
        """Run pre-approval compliance checks per Spec §19.3."""
        checks = []
        for check_name, blocking in self.PRE_APPROVAL_CHECKS:
            if check_name == "data_lineage_verification" and not is_data_change:
                checks.append(ComplianceCheck(
                    check_name=check_name,
                    status=CheckStatus.NOT_APPLICABLE,
                    details="Not a data change",
                ))
                continue
            if check_name == "cross_border_impact" and not is_cross_border:
                checks.append(ComplianceCheck(
                    check_name=check_name,
                    status=CheckStatus.NOT_APPLICABLE,
                    details="No cross-border impact",
                ))
                continue

            checks.append(ComplianceCheck(
                check_name=check_name,
                status=CheckStatus.PASS,
                details=f"{check_name} passed",
                evidence=[f"evidence-{check_name}-001"],
                blocking=blocking,
            ))

        report = self._build_report(change_request_id, VerificationPoint.PRE_APPROVAL, checks)
        self._reports[report.cvr_id] = report
        return report

    def run_pre_implementation_checks(
        self,
        change_request_id: str,
        category: str,
        risk_level: str = "low",
    ) -> ComplianceVerificationReport:
        """Run pre-implementation compliance checks per Spec §19.4."""
        checks = []
        for check_name, blocking in self.PRE_IMPLEMENTATION_CHECKS:
            # Category-specific applicability
            if check_name == "bias_fairness_retest" and category not in ("model_update", "data_update"):
                checks.append(ComplianceCheck(check_name=check_name, status=CheckStatus.NOT_APPLICABLE))
                continue
            if check_name == "security_scan" and category != "infrastructure_update":
                checks.append(ComplianceCheck(check_name=check_name, status=CheckStatus.NOT_APPLICABLE))
                continue
            if check_name == "pii_scan" and category not in ("data_update", "model_update"):
                checks.append(ComplianceCheck(check_name=check_name, status=CheckStatus.NOT_APPLICABLE))
                continue
            if check_name == "adversarial_test" and category != "model_update":
                checks.append(ComplianceCheck(check_name=check_name, status=CheckStatus.NOT_APPLICABLE))
                continue
            if check_name == "human_oversight_verification" and risk_level not in ("high", "critical"):
                checks.append(ComplianceCheck(check_name=check_name, status=CheckStatus.NOT_APPLICABLE))
                continue

            checks.append(ComplianceCheck(
                check_name=check_name,
                status=CheckStatus.PASS,
                details=f"{check_name} passed",
                evidence=[f"evidence-{check_name}-001"],
                blocking=blocking,
            ))

        report = self._build_report(change_request_id, VerificationPoint.PRE_IMPLEMENTATION, checks)
        self._reports[report.cvr_id] = report
        return report

    def run_post_implementation_monitoring(
        self,
        change_request_id: str,
        metrics: dict,
    ) -> ComplianceVerificationReport:
        """
        Post-implementation compliance monitoring per Spec §19.5.
        Continuous monitoring of policy compliance, bias drift, regulatory compliance, etc.
        """
        checks = []

        # Policy compliance monitor
        policy_violations = metrics.get("policy_violations", 0)
        checks.append(ComplianceCheck(
            check_name="policy_compliance_monitor",
            status=CheckStatus.PASS if policy_violations == 0 else CheckStatus.FAIL,
            details=f"Policy violations: {policy_violations}",
            blocking=True,
        ))

        # Bias drift monitor
        bias_drift = metrics.get("bias_drift_pct", 0)
        checks.append(ComplianceCheck(
            check_name="bias_drift_monitor",
            status=CheckStatus.PASS if bias_drift < 10 else CheckStatus.FAIL,
            details=f"Bias drift: {bias_drift}%",
            blocking=True,
        ))

        # Regulatory compliance monitor
        regulatory_gaps = metrics.get("regulatory_gaps", 0)
        checks.append(ComplianceCheck(
            check_name="regulatory_compliance_monitor",
            status=CheckStatus.PASS if regulatory_gaps == 0 else CheckStatus.FAIL,
            details=f"Regulatory gaps: {regulatory_gaps}",
            blocking=True,
        ))

        # Evidence integrity monitor
        evidence_failures = metrics.get("evidence_integrity_failures", 0)
        checks.append(ComplianceCheck(
            check_name="evidence_integrity_monitor",
            status=CheckStatus.PASS if evidence_failures == 0 else CheckStatus.FAIL,
            details=f"Evidence integrity failures: {evidence_failures}",
            blocking=True,
        ))

        # Data residency monitor
        residency_violations = metrics.get("data_residency_violations", 0)
        checks.append(ComplianceCheck(
            check_name="data_residency_monitor",
            status=CheckStatus.PASS if residency_violations == 0 else CheckStatus.FAIL,
            details=f"Data residency violations: {residency_violations}",
            blocking=True,
        ))

        report = self._build_report(change_request_id, VerificationPoint.POST_IMPLEMENTATION, checks)
        self._reports[report.cvr_id] = report
        return report

    def escalate_finding(self, report: ComplianceVerificationReport, check_name: str) -> dict:
        """
        Escalate compliance finding per Spec §19.8.
        """
        escalation_map = {
            "policy_violation": {"severity": "critical", "action": "Block change, alert compliance officer + CISO"},
            "regulatory_violation": {"severity": "critical", "action": "Block change, alert compliance officer, regulatory notification"},
            "control_coverage_gap": {"severity": "high", "action": "Block change, require control implementation"},
            "evidence_integrity_failure": {"severity": "high", "action": "Block change, quarantine affected evidence"},
            "bias_fairness_regression": {"severity": "high", "action": "Block change, require bias mitigation"},
            "pii_leakage": {"severity": "critical", "action": "Block change, activate incident response, notify DPO"},
            "minor_compliance_gap": {"severity": "medium", "action": "Flag for compliance officer review"},
            "documentation_gap": {"severity": "low", "action": "Flag for remediation"},
        }

        for check in report.checks:
            if check.check_name == check_name and check.status == CheckStatus.FAIL:
                escalation = escalation_map.get(check_name, {"severity": "medium", "action": "Review required"})
                return {
                    "check": check_name,
                    "severity": escalation["severity"],
                    "action": escalation["action"],
                    "remediation": check.remediation,
                }
        return {}

    def _build_report(
        self,
        change_request_id: str,
        verification_point: VerificationPoint,
        checks: list[ComplianceCheck],
    ) -> ComplianceVerificationReport:
        """Build a compliance verification report from checks."""
        # Determine overall status
        blocking_failures = [c for c in checks if c.status == CheckStatus.FAIL and c.blocking]
        warnings = [c for c in checks if c.status == CheckStatus.WARNING]

        if blocking_failures:
            overall = OverallStatus.FAIL
        elif warnings:
            overall = OverallStatus.PASS_WITH_CONDITIONS
        else:
            overall = OverallStatus.PASS

        # Compute compliance risk score (0-100)
        risk_score = len(blocking_failures) * 25 + len(warnings) * 10
        risk_score = min(risk_score, 100)

        # Collect required actions
        required_actions = []
        for c in checks:
            if c.status == CheckStatus.FAIL and c.remediation:
                required_actions.append(c.remediation)

        return ComplianceVerificationReport(
            change_request_id=change_request_id,
            verification_point=verification_point,
            overall_status=overall,
            checks=checks,
            compliance_risk_score=risk_score,
            required_actions=required_actions,
        )


# ─── Usage Example ────────────────────────────────────────────────────

def demo_compliance_verification():
    engine = ComplianceVerificationEngine()

    # Pre-approval checks for a model update
    pre_approval = engine.run_pre_approval_checks(
        change_request_id="cr-001",
        category="model_update",
        is_data_change=False,
        is_cross_border=True,
    )
    print(f"Pre-approval status: {pre_approval.overall_status.value}")
    print(f"Risk score: {pre_approval.compliance_risk_score}")
    print(f"Checks: {len(pre_approval.checks)}")

    # Pre-implementation checks
    pre_impl = engine.run_pre_implementation_checks(
        change_request_id="cr-001",
        category="model_update",
        risk_level="high",
    )
    print(f"\nPre-implementation status: {pre_impl.overall_status.value}")
    print(f"Risk score: {pre_impl.compliance_risk_score}")

    # Post-implementation monitoring
    post_impl = engine.run_post_implementation_monitoring(
        change_request_id="cr-001",
        metrics={
            "policy_violations": 0,
            "bias_drift_pct": 5,
            "regulatory_gaps": 0,
            "evidence_integrity_failures": 0,
            "data_residency_violations": 0,
        },
    )
    print(f"\nPost-implementation status: {post_impl.overall_status.value}")
    print(f"Risk score: {post_impl.compliance_risk_score}")

    # Generate report
    report_dict = pre_approval.to_dict()
    print(f"\nReport ID: {report_dict['cvr-id']}")

    return engine


if __name__ == "__main__":
    demo_compliance_verification()
```

---

## 9. Integration Example

Shows how all components work together in a complete change lifecycle.

```python
"""
GRC_Claw Change Management — Full Integration Example
Demonstrates the complete change lifecycle using all components.
"""

from change_request_workflow import (
    ChangeRequestService, ChangeCategory, RiskLevel, AffectedResource, ResourceType
)
from change_impact_analysis import ChangeImpactAnalyzer
from change_risk_scoring import ChangeRiskScorer, RiskFactors
from change_approval_workflow import ChangeApprovalWorkflow, ApproverRole
from change_conflict_detection import ConflictDetectionEngine, ChangeWindow
from change_rollback_automation import RollbackAutomationEngine, RollbackStrategy, RollbackTriggerType
from change_compliance_verification import ComplianceVerificationEngine


def run_full_change_lifecycle():
    """Execute a complete change management lifecycle."""

    print("=" * 70)
    print("GRC_Claw Change Management — Full Lifecycle Demo")
    print("=" * 70)

    # Initialize all services
    cr_service = ChangeRequestService()
    impact_analyzer = ChangeImpactAnalyzer()
    risk_scorer = ChangeRiskScorer()
    approval_workflow = ChangeApprovalWorkflow()
    conflict_engine = ConflictDetectionEngine()
    rollback_engine = RollbackAutomationEngine()
    compliance_engine = ComplianceVerificationEngine()

    # ─── Step 1: Create Change Request ────────────────────────────
    print("\n[1] Creating change request...")
    cr = cr_service.create_change_request(
        title="Retrain fraud detection model with Q3 2026 data",
        description="Full retraining on Q3 data with bias correction",
        category=ChangeCategory.MODEL_UPDATE,
        sub_type="retraining",
        requester_id="ml-eng-001",
        requester_role="ML Engineer",
        affected_resources=[
            AffectedResource(
                resource_type=ResourceType.MODEL,
                resource_id="model-fraud-001",
                resource_name="Fraud Detection Model v2",
                current_version="2.3.1",
                target_version="3.0.0",
            )
        ],
        justification="Q3 data shows 15% improvement in fraud pattern coverage",
        proposed_date="2026-10-15T02:00:00Z",
        rollback_plan="Blue-green switch to v2.3.1",
        mitigation_plan="72h shadow deployment before canary",
    )
    print(f"    CR ID: {cr.cr_id}")

    # ─── Step 2: Submit and Triage ────────────────────────────────
    print("\n[2] Submitting and triaging...")
    cr_service.submit(cr.cr_id, "ml-eng-001")
    cr_service.triage(cr.cr_id, RiskLevel.HIGH, "grc-analyst-001")
    print(f"    Status: {cr.status.value}, Risk: {cr.risk_level.value}")

    # ─── Step 3: Change Impact Assessment ─────────────────────────
    print("\n[3] Conducting Change Impact Assessment...")
    cia = impact_analyzer.create_assessment(
        change_request_id=cr.cr_id,
        assessor="grc-analyst-001",
        compliance_score=2,
        risk_score=3,
        performance_score=2,
        operational_score=2,
        business_score=1,
        technical_score=3,
    )
    impact_analyzer.apply_compliance_triggers(cia, is_high_risk_ai=True, is_regulated_training_data=True)
    impact_analyzer.apply_risk_triggers(cia, has_known_bias=True)
    cia.generate_mitigations()
    print(f"    CIS: {cia.composite_impact_score}, Level: {cia.impact_level.value}")
    print(f"    Approval: {impact_analyzer.get_approval_requirement(cia)}")

    # ─── Step 4: Change Risk Scoring ──────────────────────────────
    print("\n[4] Computing Change Risk Score...")
    factors = RiskFactors(
        reversibility=30, blast_radius=50, compliance=60,
        performance=20, operational=30, technical_complexity=50,
        historical=40, environmental=20,
    )
    crs = risk_scorer.compute_score(cr.cr_id, factors, "model_update")
    print(f"    CRS: {crs.score}, Band: {crs.risk_band.value}")
    print(f"    Authority: {crs.approval_authority}")
    print(f"    Strategy: {crs.deployment_strategy}")

    # ─── Step 5: Conflict Detection ───────────────────────────────
    print("\n[5] Checking for conflicts...")
    conflict_engine.register_change(ChangeWindow(
        change_request_id="cr-existing-001",
        resource_ids=["model-fraud-001"],
        start_time="2026-10-15T01:00:00Z",
        end_time="2026-10-15T05:00:00Z",
        risk_level="high",
    ))
    new_window = ChangeWindow(
        change_request_id=cr.cr_id,
        resource_ids=["model-fraud-001"],
        start_time="2026-10-15T02:00:00Z",
        end_time="2026-10-15T06:00:00Z",
        risk_level="high",
    )
    conflicts = conflict_engine.detect_conflicts(new_window)
    print(f"    Conflicts detected: {len(conflicts)}")
    for c in conflicts:
        print(f"    [{c.severity.value}] {c.conflict_type.value}")

    # ─── Step 6: Compliance Verification (Pre-Approval) ───────────
    print("\n[6] Running pre-approval compliance checks...")
    pre_approval_report = compliance_engine.run_pre_approval_checks(
        change_request_id=cr.cr_id,
        category="model_update",
        is_cross_border=True,
    )
    print(f"    Status: {pre_approval_report.overall_status.value}")
    print(f"    Risk Score: {pre_approval_report.compliance_risk_score}")

    # ─── Step 7: Approval Workflow ────────────────────────────────
    print("\n[7] Processing approvals...")
    approvals = approval_workflow.request_approval(
        change_request_id=cr.cr_id,
        category="model_update",
        sub_type="retraining",
        requester_id="ml-eng-001",
    )
    approval_workflow.record_approval(cr.cr_id, "cab-001", ApproverRole.CAB_CHAIR, "approve")
    approval_workflow.record_approval(cr.cr_id, "model-001", ApproverRole.MODEL_OWNER, "approve")
    approval_workflow.record_approval(cr.cr_id, "compliance-001", ApproverRole.COMPLIANCE_OFFICER, "approve")
    status = approval_workflow.check_approval_complete(cr.cr_id)
    print(f"    Approval status: {status['status']}")

    # ─── Step 8: Compliance Verification (Pre-Implementation) ────
    print("\n[8] Running pre-implementation compliance checks...")
    pre_impl_report = compliance_engine.run_pre_implementation_checks(
        change_request_id=cr.cr_id,
        category="model_update",
        risk_level="high",
    )
    print(f"    Status: {pre_impl_report.overall_status.value}")

    # ─── Step 9: Implement ────────────────────────────────────────
    print("\n[9] Implementing change...")
    cr_service.implement(cr.cr_id, "ml-eng-001")
    print(f"    Status: {cr.status.value}")

    # ─── Step 10: Simulate Monitoring & Potential Rollback ────────
    print("\n[10] Monitoring post-implementation...")
    metrics = {
        "error_rate_breach": 7.5,  # Triggers rollback!
        "latency_breach": 1.5,
    }
    triggered = rollback_engine.evaluate_triggers(cr.cr_id, metrics)
    if triggered:
        print(f"    ⚠ Rollback triggered: {triggered[0].trigger_type.value}")
        event = rollback_engine.initiate_rollback(
            change_request_id=cr.cr_id,
            trigger_type=triggered[0].trigger_type,
            strategy=RollbackStrategy.CANARY_HALT,
            automation_level=triggered[0].automation_level,
        )
        print(f"    Rollback status: {event.status.value}")
        rollback_engine.verify_rollback(event.event_id, {
            "error_rate": 0.5, "latency_p99": 200, "policy_violations": 0,
        })
        cr_service.rollback(cr.cr_id, "system", "Error rate breach")
    else:
        cr_service.verify(cr.cr_id, "ml-eng-001")

    # ─── Step 11: Audit Trail ────────────────────────────────────
    print("\n[11] Audit trail summary...")
    trail = cr_service.get_audit_trail(cr.cr_id)
    print(f"    Total audit records: {len(trail)}")
    print(f"    Chain integrity: {cr_service.verify_audit_integrity()}")
    for record in trail:
        print(f"    {record['timestamp']}: {record['event-type']} by {record['actor']['id']}")

    print("\n" + "=" * 70)
    print("Change lifecycle complete!")
    print("=" * 70)

    return cr


if __name__ == "__main__":
    run_full_change_lifecycle()
```

---

## Summary

This implementation guide provides:

| # | Component | Spec Section | Key Features |
|---|-----------|-------------|--------------|
| 1 | Change Request Workflow | §4, §6 | Full lifecycle, state machine, hash-chained audit trail |
| 2 | Change Impact Analysis | §5 | 6-dimension CIA, trigger rules, composite scoring |
| 3 | Change Risk Scoring | §15 | 8-factor CRS, category weights, risk bands |
| 4 | Change Approval Workflow | §4 | Risk-based routing, CAB voting, emergency changes |
| 5 | Change Conflict Detection | §16 | 8 conflict types, 15 detection rules, severity-based response |
| 6 | Change Rollback Automation | §18 | L0-L4 automation, 11 trigger types, 7 rollback strategies |
| 7 | Change Compliance Verification | §19 | 3 verification points, category-specific checks, escalation |

All components are designed to work together as an integrated change management system, with the audit trail providing end-to-end traceability per GRC_Claw's compliance requirements.
