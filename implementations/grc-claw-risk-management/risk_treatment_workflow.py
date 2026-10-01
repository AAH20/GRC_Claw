"""
GRC_Claw Risk Treatment Workflow
=================================
Implements the 4-strategy treatment hierarchy (Avoid/Transfer/Mitigate/Accept),
treatment decision matrix, mitigation control catalog, and residual risk acceptance.
References GRC-RISK-001 §7.1-7.6.

Usage:
    from risk_treatment_workflow import TreatmentWorkflow, TreatmentStrategy

    workflow = TreatmentWorkflow()
    plan = workflow.create_treatment_plan(risk_id="RISK-2026-0001", strategy=TreatmentStrategy.MITIGATE)
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, date, timedelta
from enum import Enum
from typing import Optional


# ─── Enums ───────────────────────────────────────────────────────────────────

class TreatmentStrategy(str, Enum):
    AVOID = "Avoid"
    TRANSFER = "Transfer"
    MITIGATE = "Mitigate"
    ACCEPT = "Accept"


class TreatmentStatus(str, Enum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    IMPLEMENTED = "implemented"
    VERIFIED = "verified"
    CLOSED = "closed"
    OVERDUE = "overdue"


class ControlStatus(str, Enum):
    PLANNED = "planned"
    IMPLEMENTED = "implemented"
    VERIFIED = "verified"
    FAILED = "failed"


class RiskTier(str, Enum):
    MINIMAL = "Minimal"
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


# ─── Treatment Decision Matrix (GRC-RISK-001 §7.2) ──────────────────────────

DECISION_MATRIX = {
    RiskTier.CRITICAL: {
        "default_strategy": TreatmentStrategy.AVOID,
        "escalation": "Risk Committee",
        "max_acceptance_days": 30,
        "requires_mitigation_plan": True,
    },
    RiskTier.HIGH: {
        "default_strategy": TreatmentStrategy.MITIGATE,
        "escalation": "CISO / CTO",
        "max_acceptance_days": 90,
        "requires_mitigation_plan": True,
    },
    RiskTier.MEDIUM: {
        "default_strategy": TreatmentStrategy.MITIGATE,
        "escalation": "Department Head",
        "max_acceptance_days": 180,
        "requires_mitigation_plan": False,
    },
    RiskTier.LOW: {
        "default_strategy": TreatmentStrategy.ACCEPT,
        "escalation": "Business Unit Owner",
        "max_acceptance_days": 365,
        "requires_mitigation_plan": False,
    },
    RiskTier.MINIMAL: {
        "default_strategy": TreatmentStrategy.ACCEPT,
        "escalation": "System Owner",
        "max_acceptance_days": 365,
        "requires_mitigation_plan": False,
    },
}


# ─── Mitigation Control Catalog (GRC-RISK-001 §7.3) ────────────────────────

MITIGATION_CATALOG = {
    "GOV-01": [
        {"control": "AI policy establishment", "implementation": "Policy engine with version control"},
        {"control": "Policy review cycle", "implementation": "Annual policy review workflow"},
    ],
    "GOV-02": [
        {"control": "RACI matrix for AI roles", "implementation": "Role registry with accountability chains"},
        {"control": "AI ownership registry", "implementation": "Named owner per AI system"},
    ],
    "GOV-03": [
        {"control": "Whistleblower hotline", "implementation": "Anonymous reporting workflow"},
        {"control": "Incident reporting portal", "implementation": "Self-service reporting system"},
    ],
    "GOV-04": [
        {"control": "AI literacy program", "implementation": "LMS integration with role-based curriculum"},
        {"control": "Competency assessment", "implementation": "Annual skills evaluation"},
    ],
    "GOV-05": [
        {"control": "Vendor risk assessment", "implementation": "VARQ workflow with CRS scoring"},
        {"control": "Third-party audit rights", "implementation": "Contractual audit clauses"},
    ],
    "DAT-01": [
        {"control": "Data quality gates", "implementation": "5-stage quality pipeline (G1-G5)"},
        {"control": "Data validation framework", "implementation": "Schema and constraint validation"},
    ],
    "DAT-02": [
        {"control": "Provenance tracking", "implementation": "Cryptographic lineage with hash chains"},
        {"control": "Data catalog integration", "implementation": "Automated metadata capture"},
    ],
    "DAT-03": [
        {"control": "Bias testing", "implementation": "Fairlearn/AIF360 integration in CI/CD"},
        {"control": "Fairness metrics monitoring", "implementation": "Continuous demographic parity tracking"},
    ],
    "DAT-04": [
        {"control": "PII detection", "implementation": "Presidio + custom NER at ingestion"},
        {"control": "Data anonymization", "implementation": "k-anonymity and differential privacy"},
    ],
    "DAT-05": [
        {"control": "Data validation", "implementation": "Anomaly detection on training data"},
        {"control": "Poisoning detection", "implementation": "Statistical outlier analysis"},
    ],
    "DAT-06": [
        {"control": "Retention enforcement", "implementation": "Automated deletion with certificates"},
        {"control": "Data lifecycle policy", "implementation": "Policy-driven retention schedules"},
    ],
    "MOD-01": [
        {"control": "Performance monitoring", "implementation": "Real-time metrics with SLA alerts"},
        {"control": "Accuracy regression testing", "implementation": "Automated eval in CI/CD"},
    ],
    "MOD-02": [
        {"control": "Drift detection", "implementation": "PSI/KL divergence monitoring"},
        {"control": "Retraining triggers", "implementation": "Automated retrain on drift threshold"},
    ],
    "MOD-03": [
        {"control": "Robustness testing", "implementation": "Adversarial test suite in CI/CD"},
        {"control": "Distribution shift detection", "implementation": "Input distribution monitoring"},
    ],
    "MOD-04": [
        {"control": "Explainability", "implementation": "SHAP/LIME integration with model cards"},
        {"control": "Decision audit trail", "implementation": "Per-decision explanation logging"},
    ],
    "MOD-05": [
        {"control": "Model versioning", "implementation": "Governance-aware model registry"},
        {"control": "Change control", "implementation": "Approval workflow for model updates"},
    ],
    "MOD-06": [
        {"control": "Hallucination detection", "implementation": "LLM-as-judge with ground truth validation"},
        {"control": "Output grounding", "implementation": "RAG with citation verification"},
    ],
    "SEC-01": [
        {"control": "Input sanitization", "implementation": "Prompt injection filter pipeline"},
        {"control": "System prompt hardening", "implementation": "Immutable system prompt layer"},
    ],
    "SEC-02": [
        {"control": "Goal integrity monitoring", "implementation": "Agent objective verification"},
        {"control": "Behavioral constraints", "implementation": "Hard-coded action boundaries"},
    ],
    "SEC-03": [
        {"control": "Tool access controls", "implementation": "MCP tool permission scoping"},
        {"control": "Least privilege enforcement", "implementation": "Role-based tool access"},
    ],
    "SEC-04": [
        {"control": "Identity management", "implementation": "Agent identity registry with attestation"},
        {"control": "Privilege boundary", "implementation": "Separation of duties for agents"},
    ],
    "SEC-05": [
        {"control": "Supply chain verification", "implementation": "AI-SBOM with provenance checks"},
        {"control": "Dependency scanning", "implementation": "Automated vulnerability scanning"},
    ],
    "SEC-06": [
        {"control": "Code execution sandboxing", "implementation": "Isolated execution environment"},
        {"control": "Network egress controls", "implementation": "Egress filtering for agent actions"},
    ],
    "SEC-07": [
        {"control": "Circuit breakers", "implementation": "Kill-and-quarantine on invariant violation"},
        {"control": "Rate limiting", "implementation": "Action frequency caps"},
    ],
    "HUM-01": [
        {"control": "Impact assessment", "implementation": "FRIA workflow per EU Art. 27"},
        {"control": "Harm monitoring", "implementation": "User complaint tracking and analysis"},
    ],
    "HUM-02": [
        {"control": "Fairness monitoring", "implementation": "Continuous bias metrics on outputs"},
        {"control": "Disparate impact testing", "implementation": "Regular fairness audits"},
    ],
    "HUM-03": [
        {"control": "Human oversight", "implementation": "Human-in-the-loop approval workflow"},
        {"control": "Override capability", "implementation": "Human override for critical decisions"},
    ],
    "HUM-04": [
        {"control": "Trust calibration", "implementation": "Output confidence scoring"},
        {"control": "Transparency notices", "implementation": "AI interaction disclosure"},
    ],
    "HUM-05": [
        {"control": "Societal impact review", "implementation": "Ethics board review process"},
        {"control": "Stakeholder engagement", "implementation": "Regular community feedback loops"},
    ],
    "OPS-01": [
        {"control": "Real-time monitoring", "implementation": "AI-Risk-Radar with sub-100ms latency"},
        {"control": "Anomaly detection", "implementation": "Statistical process control"},
    ],
    "OPS-02": [
        {"control": "Incident response", "implementation": "AI-IR-Playbooks with automated containment"},
        {"control": "Escalation automation", "implementation": "Tiered alert routing"},
    ],
    "OPS-03": [
        {"control": "High availability", "implementation": "Multi-region deployment with failover"},
        {"control": "Disaster recovery", "implementation": "RPO/RTO-defined recovery plans"},
    ],
    "OPS-04": [
        {"control": "Immutable audit trail", "implementation": "Hash-chained append-only log"},
        {"control": "Log integrity verification", "implementation": "Periodic hash verification"},
    ],
    "OPS-05": [
        {"control": "Post-market monitoring", "implementation": "Continuous production surveillance"},
        {"control": "Feedback loops", "implementation": "User feedback integration"},
    ],
    "TPR-01": [
        {"control": "Vendor due diligence", "implementation": "VARQ + CRS scoring per GRC-TPR-001"},
        {"control": "Contractual risk clauses", "implementation": "Risk allocation in vendor contracts"},
    ],
    "TPR-02": [
        {"control": "Fourth-party tracking", "implementation": "Fourth-party risk register (FPRS)"},
        {"control": "Concentration limits", "implementation": "Max dependency thresholds"},
    ],
    "TPR-03": [
        {"control": "Update notification", "implementation": "Contractual 30-day notification clause"},
        {"control": "Change monitoring", "implementation": "Behavioral diff testing on updates"},
    ],
    "TPR-04": [
        {"control": "Exit planning", "implementation": "Data portability requirements"},
        {"control": "Vendor diversification", "implementation": "Multi-vendor strategy"},
    ],
    "CMP-01": [
        {"control": "Prohibited practice screening", "implementation": "Automated Art. 5 compliance check"},
        {"control": "Use case review", "implementation": "Pre-deployment compliance gate"},
    ],
    "CMP-02": [
        {"control": "Risk classification engine", "implementation": "EU AI Act tier triage automation"},
        {"control": "Classification review", "implementation": "Human review of auto-classification"},
    ],
    "CMP-03": [
        {"control": "Conformity assessment", "implementation": "Assessment workflow per Art. 43"},
        {"control": "Technical documentation", "implementation": "Annex IV documentation generator"},
    ],
    "CMP-04": [
        {"control": "Cross-border engine", "implementation": "GlobalAI-Compliance rules engine"},
        {"control": "Jurisdiction mapping", "implementation": "Multi-region compliance matrix"},
    ],
}


# ─── Data Classes ────────────────────────────────────────────────────────────

@dataclass
class MitigationControl:
    """Single mitigation control within a treatment plan."""
    control_id: str
    name: str
    description: str
    owner: str
    status: ControlStatus = ControlStatus.PLANNED
    evidence_ref: str = ""
    implemented_date: str = ""
    verified_date: str = ""
    notes: str = ""


@dataclass
class TreatmentPlan:
    """Complete treatment plan for a risk."""
    plan_id: str
    risk_id: str
    strategy: TreatmentStrategy
    status: TreatmentStatus
    created_date: str
    target_date: str
    rationale: str = ""
    controls: list[MitigationControl] = field(default_factory=list)
    expected_residual_mdrs: float = 0.0
    expected_residual_tier: str = ""
    actual_residual_mdrs: float = 0.0
    actual_residual_tier: str = ""
    approver: str = ""
    approval_date: str = ""
    review_trigger: str = ""
    notes: str = ""
    audit_trail: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["strategy"] = self.strategy.value
        d["status"] = self.status.value
        for c in d["controls"]:
            c["status"] = c["status"].value if isinstance(c["status"], ControlStatus) else c["status"]
        return d


# ─── Treatment Workflow Engine ───────────────────────────────────────────────

class TreatmentWorkflow:
    """
    Manages the full risk treatment lifecycle:
    assess → select strategy → implement controls → verify → document → close
    """

    def __init__(self):
        self._plans: dict[str, TreatmentPlan] = {}
        self._counter = 0

    # ── Strategy Selection ──────────────────────────────────────────────

    def recommend_strategy(self, tier: RiskTier, risk_description: str = "") -> TreatmentStrategy:
        """
        Recommend treatment strategy based on risk tier.
        Uses the decision matrix from GRC-RISK-001 §7.2.
        """
        return DECISION_MATRIX[tier]["default_strategy"]

    def get_decision_matrix_entry(self, tier: RiskTier) -> dict:
        """Get the full decision matrix entry for a tier."""
        entry = DECISION_MATRIX[tier].copy()
        entry["default_strategy"] = entry["default_strategy"].value
        return entry

    # ── Plan Creation ───────────────────────────────────────────────────

    def create_treatment_plan(
        self,
        risk_id: str,
        strategy: TreatmentStrategy,
        risk_category: str,
        risk_tier: RiskTier,
        target_date: Optional[str] = None,
        rationale: str = "",
        approver: str = "",
    ) -> TreatmentPlan:
        """Create a new treatment plan with recommended controls."""
        self._counter += 1
        plan_id = f"TP-{datetime.now().year}-{self._counter:04d}"

        if not target_date:
            days = DECISION_MATRIX[risk_tier]["max_acceptance_days"]
            target_date = (date.today() + timedelta(days=days)).isoformat()

        # Auto-populate controls from catalog
        controls = []
        catalog = MITIGATION_CATALOG.get(risk_category, [])
        for i, cat in enumerate(catalog):
            controls.append(MitigationControl(
                control_id=f"CTRL-{i+1:03d}",
                name=cat["control"],
                description=cat["implementation"],
                owner="",
                status=ControlStatus.PLANNED,
            ))

        plan = TreatmentPlan(
            plan_id=plan_id,
            risk_id=risk_id,
            strategy=strategy,
            status=TreatmentStatus.PLANNED,
            created_date=date.today().isoformat(),
            target_date=target_date,
            rationale=rationale,
            controls=controls,
            approver=approver,
        )
        plan.audit_trail.append({
            "timestamp": datetime.utcnow().isoformat(),
            "action": "plan_created",
            "details": f"Strategy: {strategy.value}, Controls: {len(controls)}",
        })

        self._plans[plan_id] = plan
        return plan

    # ── Plan Management ─────────────────────────────────────────────────

    def get_plan(self, plan_id: str) -> Optional[TreatmentPlan]:
        return self._plans.get(plan_id)

    def start_treatment(self, plan_id: str, actor: str):
        plan = self._get_or_raise(plan_id)
        plan.status = TreatmentStatus.IN_PROGRESS
        plan.audit_trail.append({
            "timestamp": datetime.utcnow().isoformat(),
            "action": "treatment_started",
            "actor": actor,
        })

    def update_control_status(
        self, plan_id: str, control_id: str,
        status: ControlStatus, actor: str,
        evidence_ref: str = "", notes: str = "",
    ):
        plan = self._get_or_raise(plan_id)
        for ctrl in plan.controls:
            if ctrl.control_id == control_id:
                ctrl.status = status
                if evidence_ref:
                    ctrl.evidence_ref = evidence_ref
                if notes:
                    ctrl.notes = notes
                if status == ControlStatus.IMPLEMENTED:
                    ctrl.implemented_date = date.today().isoformat()
                elif status == ControlStatus.VERIFIED:
                    ctrl.verified_date = date.today().isoformat()
                break
        plan.audit_trail.append({
            "timestamp": datetime.utcnow().isoformat(),
            "action": "control_updated",
            "actor": actor,
            "details": f"Control {control_id} → {status.value}",
        })

    def verify_effectiveness(
        self, plan_id: str,
        actual_residual_mdrs: float,
        actual_residual_tier: str,
        actor: str,
    ):
        """Record post-treatment residual risk and verify effectiveness."""
        plan = self._get_or_raise(plan_id)
        plan.actual_residual_mdrs = actual_residual_mdrs
        plan.actual_residual_tier = actual_residual_tier
        plan.status = TreatmentStatus.VERIFIED
        plan.audit_trail.append({
            "timestamp": datetime.utcnow().isoformat(),
            "action": "effectiveness_verified",
            "actor": actor,
            "details": f"Residual MDRS: {actual_residual_mdrs} ({actual_residual_tier})",
        })

    def approve_plan(self, plan_id: str, approver: str, notes: str = ""):
        plan = self._get_or_raise(plan_id)
        plan.approver = approver
        plan.approval_date = date.today().isoformat()
        if notes:
            plan.notes = notes
        plan.audit_trail.append({
            "timestamp": datetime.utcnow().isoformat(),
            "action": "plan_approved",
            "actor": approver,
        })

    def close_plan(self, plan_id: str, actor: str, reason: str = ""):
        plan = self._get_or_raise(plan_id)
        plan.status = TreatmentStatus.CLOSED
        plan.audit_trail.append({
            "timestamp": datetime.utcnow().isoformat(),
            "action": "plan_closed",
            "actor": actor,
            "details": reason,
        })

    # ── Residual Risk Acceptance (GRC-RISK-001 §7.5) ────────────────────

    def accept_residual_risk(
        self,
        plan_id: str,
        residual_mdrs: float,
        residual_tier: RiskTier,
        approver: str,
        review_date: str,
        rationale: str = "",
    ) -> dict:
        """
        Document residual risk acceptance with approval.
        Returns acceptance record.
        """
        plan = self._get_or_raise(plan_id)
        max_days = DECISION_MATRIX[residual_tier]["max_acceptance_days"]

        acceptance = {
            "acceptance_id": f"ACC-{datetime.now().year}-{self._counter:04d}",
            "plan_id": plan_id,
            "risk_id": plan.risk_id,
            "residual_mdrs": residual_mdrs,
            "residual_tier": residual_tier.value,
            "approver": approver,
            "approval_date": date.today().isoformat(),
            "review_date": review_date,
            "rationale": rationale,
            "max_review_window_days": max_days,
            "status": "accepted",
        }
        plan.audit_trail.append({
            "timestamp": datetime.utcnow().isoformat(),
            "action": "residual_accepted",
            "actor": approver,
            "details": f"Residual MDRS {residual_mdrs} accepted, review by {review_date}",
        })
        return acceptance

    # ── Queries ─────────────────────────────────────────────────────────

    def find_by_risk(self, risk_id: str) -> list[TreatmentPlan]:
        return [p for p in self._plans.values() if p.risk_id == risk_id]

    def find_by_status(self, status: TreatmentStatus) -> list[TreatmentPlan]:
        return [p for p in self._plans.values() if p.status == status]

    def find_overdue(self, as_of: Optional[date] = None) -> list[TreatmentPlan]:
        today = as_of or date.today()
        overdue = []
        for p in self._plans.values():
            if p.status not in (TreatmentStatus.CLOSED, TreatmentStatus.VERIFIED):
                try:
                    td = date.fromisoformat(p.target_date)
                    if td < today:
                        p.status = TreatmentStatus.OVERDUE
                        overdue.append(p)
                except ValueError:
                    pass
        return overdue

    def find_by_strategy(self, strategy: TreatmentStrategy) -> list[TreatmentPlan]:
        return [p for p in self._plans.values() if p.strategy == strategy]

    # ── Control Catalog ─────────────────────────────────────────────────

    @staticmethod
    def get_controls_for_category(category: str) -> list[dict]:
        """Get mitigation controls for a risk category."""
        return MITIGATION_CATALOG.get(category, [])

    @staticmethod
    def get_all_categories() -> list[str]:
        """List all categories with defined controls."""
        return sorted(MITIGATION_CATALOG.keys())

    # ── Reporting ───────────────────────────────────────────────────────

    def summary(self) -> dict:
        """Treatment workflow summary statistics."""
        total = len(self._plans)
        by_status: dict[str, int] = {}
        by_strategy: dict[str, int] = {}
        for p in self._plans.values():
            by_status[p.status.value] = by_status.get(p.status.value, 0) + 1
            by_strategy[p.strategy.value] = by_strategy.get(p.strategy.value, 0) + 1
        return {
            "total_plans": total,
            "by_status": by_status,
            "by_strategy": by_strategy,
            "overdue": len(self.find_overdue()),
        }

    # ── Internal ────────────────────────────────────────────────────────

    def _get_or_raise(self, plan_id: str) -> TreatmentPlan:
        plan = self._plans.get(plan_id)
        if not plan:
            raise KeyError(f"Treatment plan '{plan_id}' not found")
        return plan

    def __len__(self) -> int:
        return len(self._plans)


# ─── Demo / Self-Test ────────────────────────────────────────────────────────

if __name__ == "__main__":
    workflow = TreatmentWorkflow()

    # Create treatment plan
    plan = workflow.create_treatment_plan(
        risk_id="RISK-2026-0001",
        strategy=TreatmentStrategy.MITIGATE,
        risk_category="DAT-03",
        risk_tier=RiskTier.HIGH,
        rationale="Bias testing and retraining required",
        approver="data-science-lead@org.com",
    )
    print(f"Created plan: {plan.plan_id} | Strategy: {plan.strategy.value} | Controls: {len(plan.controls)}")

    # Start treatment
    workflow.start_treatment(plan.plan_id, "data-science-lead@org.com")

    # Update control statuses
    for ctrl in plan.controls:
        workflow.update_control_status(
            plan.plan_id, ctrl.control_id,
            ControlStatus.IMPLEMENTED, "data-science-lead@org.com",
            evidence_ref=f"EVID-{ctrl.control_id}",
        )
    print(f"Implemented {len(plan.controls)} controls")

    # Verify effectiveness
    workflow.verify_effectiveness(
        plan.plan_id,
        actual_residual_mdrs=2.3,
        actual_residual_tier="Medium",
        actor="data-science-lead@org.com",
    )
    print(f"Verified: Residual MDRS 2.3 (Medium)")

    # Accept residual risk
    acceptance = workflow.accept_residual_risk(
        plan.plan_id,
        residual_mdrs=2.3,
        residual_tier=RiskTier.MEDIUM,
        approver="department-head@org.com",
        review_date="2027-01-01",
        rationale="Within risk appetite after mitigation",
    )
    print(f"Accepted: {acceptance['acceptance_id']}")

    # Summary
    print(f"\nWorkflow Summary: {json.dumps(workflow.summary(), indent=2)}")

    # Show controls for a category
    controls = TreatmentWorkflow.get_controls_for_category("SEC-01")
    print(f"\nSEC-01 Controls: {len(controls)}")
    for c in controls:
        print(f"  - {c['control']}: {c['implementation']}")
