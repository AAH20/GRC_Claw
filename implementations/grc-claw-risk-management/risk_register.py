"""
GRC_Claw Risk Register Implementation
=====================================
Central repository for all identified and assessed risks.
Implements the Risk Register Entry Schema from GRC-RISK-001 §5.3.

Usage:
    from risk_register import RiskRegister, RiskEntry, RiskStatus

    register = RiskRegister()
    risk = register.create_risk(
        title="Customer service agent may produce biased responses",
        domain="DAT", category="DAT-03",
        likelihood=4, impact=4, detectability=3, velocity=3, persistence=4
    )
"""

from __future__ import annotations

import json
import csv
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, date
from enum import Enum
from pathlib import Path
from typing import Optional


# ─── Enums ───────────────────────────────────────────────────────────────────

class RiskStatus(str, Enum):
    IDENTIFIED = "identified"
    ASSESSED = "assessed"
    TREATMENT_PLANNED = "treatment_planned"
    TREATMENT_IN_PROGRESS = "treatment_in_progress"
    TREATED = "treated"
    ACCEPTED = "accepted"
    ESCALATED = "escalated"
    CLOSED = "closed"
    RETIRED = "retired"


class RiskTier(str, Enum):
    MINIMAL = "Minimal"
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class TreatmentStrategy(str, Enum):
    AVOID = "Avoid"
    TRANSFER = "Transfer"
    MITIGATE = "Mitigate"
    ACCEPT = "Accept"


# ─── Data Classes ────────────────────────────────────────────────────────────

@dataclass
class RiskScore:
    """MDRS score components (GRC-RISK-001 §4.1)."""
    likelihood: int       # 1-5, weight 25%
    impact: int           # 1-5, weight 30%
    detectability: int    # 1-5, weight 15%
    velocity: int         # 1-5, weight 15%
    persistence: int      # 1-5, weight 15%

    WEIGHTS = {
        "likelihood": 0.25,
        "impact": 0.30,
        "detectability": 0.15,
        "velocity": 0.15,
        "persistence": 0.15,
    }

    def __post_init__(self):
        for name, val in [
            ("likelihood", self.likelihood),
            ("impact", self.impact),
            ("detectability", self.detectability),
            ("velocity", self.velocity),
            ("persistence", self.persistence),
        ]:
            if not 1 <= val <= 5:
                raise ValueError(f"{name} must be 1-5, got {val}")

    @property
    def mdrs(self) -> float:
        """Multi-Dimensional Risk Score (GRC-RISK-001 §4.2)."""
        return round(
            self.likelihood * self.WEIGHTS["likelihood"]
            + self.impact * self.WEIGHTS["impact"]
            + self.detectability * self.WEIGHTS["detectability"]
            + self.velocity * self.WEIGHTS["velocity"]
            + self.persistence * self.WEIGHTS["persistence"],
            2,
        )

    @property
    def tier(self) -> RiskTier:
        """Risk tier classification (GRC-RISK-001 §4.3)."""
        s = self.mdrs
        if s >= 4.50:
            return RiskTier.CRITICAL
        elif s >= 3.50:
            return RiskTier.HIGH
        elif s >= 2.50:
            return RiskTier.MEDIUM
        elif s >= 1.50:
            return RiskTier.LOW
        else:
            return RiskTier.MINIMAL

    def to_dict(self) -> dict:
        return {
            "likelihood": self.likelihood,
            "impact": self.impact,
            "detectability": self.detectability,
            "velocity": self.velocity,
            "persistence": self.persistence,
            "mdrs": self.mdrs,
            "tier": self.tier.value,
        }


@dataclass
class AuditEvent:
    """Single audit trail entry."""
    timestamp: str
    action: str
    actor: str
    details: str = ""


@dataclass
class RiskEntry:
    """Complete risk register entry (GRC-RISK-001 §5.3 schema)."""
    risk_id: str
    risk_title: str
    risk_description: str
    risk_domain: str
    risk_category: str
    risk_subcategory: str = ""
    affected_assets: list[str] = field(default_factory=list)
    affected_stakeholders: list[str] = field(default_factory=list)
    inherent_score: Optional[RiskScore] = None
    residual_score: Optional[RiskScore] = None
    risk_owner: str = ""
    risk_status: RiskStatus = RiskStatus.IDENTIFIED
    identified_date: str = field(default_factory=lambda: date.today().isoformat())
    identified_source: str = ""
    evidence_refs: list[str] = field(default_factory=list)
    framework_mapping: dict = field(default_factory=dict)
    treatment_plan: Optional[dict] = None
    review_date: str = ""
    audit_trail: list[AuditEvent] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict:
        d = asdict(self)
        d["risk_status"] = self.risk_status.value
        if self.inherent_score:
            d["inherent_score"] = self.inherent_score.to_dict()
        if self.residual_score:
            d["residual_score"] = self.residual_score.to_dict()
        return d

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, default=str)

    def add_audit(self, action: str, actor: str, details: str = ""):
        self.audit_trail.append(
            AuditEvent(
                timestamp=datetime.utcnow().isoformat(),
                action=action,
                actor=actor,
                details=details,
            )
        )
        self.updated_at = datetime.utcnow().isoformat()


# ─── Risk Register ───────────────────────────────────────────────────────────

class RiskRegister:
    """
    Central risk register — CRUD operations, querying, export.
    Thread-safe for single-process use; use external locking for multi-process.
    """

    VALID_DOMAINS = {"GOV", "DAT", "MOD", "SEC", "HUM", "OPS", "TPR", "CMP"}

    def __init__(self):
        self._risks: dict[str, RiskEntry] = {}
        self._counter = 0

    # ── Create ──────────────────────────────────────────────────────────

    def create_risk(
        self,
        title: str,
        domain: str,
        category: str,
        description: str = "",
        subcategory: str = "",
        likelihood: int = 3,
        impact: int = 3,
        detectability: int = 3,
        velocity: int = 3,
        persistence: int = 3,
        owner: str = "",
        source: str = "manual",
        assets: Optional[list[str]] = None,
        stakeholders: Optional[list[str]] = None,
        evidence_refs: Optional[list[str]] = None,
        framework_mapping: Optional[dict] = None,
        tags: Optional[list[str]] = None,
    ) -> RiskEntry:
        """Create and register a new risk entry."""
        domain = domain.upper()
        if domain not in self.VALID_DOMAINS:
            raise ValueError(f"Invalid domain '{domain}'. Must be one of {self.VALID_DOMAINS}")

        self._counter += 1
        risk_id = f"RISK-{datetime.now().year}-{self._counter:04d}"

        score = RiskScore(likelihood, impact, detectability, velocity, persistence)

        entry = RiskEntry(
            risk_id=risk_id,
            risk_title=title,
            risk_description=description,
            risk_domain=domain,
            risk_category=category,
            risk_subcategory=subcategory,
            affected_assets=assets or [],
            affected_stakeholders=stakeholders or [],
            inherent_score=score,
            risk_owner=owner,
            risk_status=RiskStatus.ASSESSED,
            identified_source=source,
            evidence_refs=evidence_refs or [],
            framework_mapping=framework_mapping or {},
            tags=tags or [],
        )
        entry.add_audit("created", "system", f"Risk created with MDRS {score.mdrs} ({score.tier.value})")

        self._risks[risk_id] = entry
        return entry

    # ── Read ────────────────────────────────────────────────────────────

    def get(self, risk_id: str) -> Optional[RiskEntry]:
        return self._risks.get(risk_id)

    def all(self) -> list[RiskEntry]:
        return list(self._risks.values())

    def find_by_domain(self, domain: str) -> list[RiskEntry]:
        return [r for r in self._risks.values() if r.risk_domain == domain.upper()]

    def find_by_category(self, category: str) -> list[RiskEntry]:
        return [r for r in self._risks.values() if r.risk_category == category]

    def find_by_status(self, status: RiskStatus) -> list[RiskEntry]:
        return [r for r in self._risks.values() if r.risk_status == status]

    def find_by_tier(self, tier: RiskTier) -> list[RiskEntry]:
        results = []
        for r in self._risks.values():
            score = r.residual_score or r.inherent_score
            if score and score.tier == tier:
                results.append(r)
        return results

    def find_by_owner(self, owner: str) -> list[RiskEntry]:
        return [r for r in self._risks.values() if r.risk_owner == owner]

    def search(self, query: str) -> list[RiskEntry]:
        """Full-text search across title, description, and tags."""
        q = query.lower()
        return [
            r for r in self._risks.values()
            if q in r.risk_title.lower()
            or q in r.risk_description.lower()
            or any(q in t.lower() for t in r.tags)
        ]

    def overdue_reviews(self, as_of: Optional[date] = None) -> list[RiskEntry]:
        """Find risks past their review date."""
        today = as_of or date.today()
        overdue = []
        for r in self._risks.values():
            if r.review_date and r.risk_status not in (
                RiskStatus.CLOSED, RiskStatus.RETIRED
            ):
                try:
                    rd = date.fromisoformat(r.review_date)
                    if rd < today:
                        overdue.append(r)
                except ValueError:
                    pass
        return overdue

    # ── Update ──────────────────────────────────────────────────────────

    def update_status(self, risk_id: str, status: RiskStatus, actor: str, details: str = ""):
        risk = self._get_or_raise(risk_id)
        old = risk.risk_status
        risk.risk_status = status
        risk.add_audit("status_changed", actor, f"{old.value} → {status.value}. {details}")

    def update_residual_score(
        self, risk_id: str, likelihood: int, impact: int,
        detectability: int, velocity: int, persistence: int,
        actor: str, details: str = "",
    ):
        risk = self._get_or_raise(risk_id)
        old = risk.residual_score or risk.inherent_score
        risk.residual_score = RiskScore(likelihood, impact, detectability, velocity, persistence)
        risk.add_audit(
            "residual_scored", actor,
            f"Residual MDRS {risk.residual_score.mdrs} ({risk.residual_score.tier.value}). {details}",
        )

    def assign_treatment_plan(self, risk_id: str, plan: dict, actor: str):
        risk = self._get_or_raise(risk_id)
        risk.treatment_plan = plan
        risk.risk_status = RiskStatus.TREATMENT_PLANNED
        risk.add_audit("treatment_planned", actor, f"Strategy: {plan.get('strategy', 'N/A')}")

    def set_review_date(self, risk_id: str, review_date: str, actor: str):
        risk = self._get_or_raise(risk_id)
        risk.review_date = review_date
        risk.add_audit("review_scheduled", actor, f"Review date: {review_date}")

    def add_evidence(self, risk_id: str, evidence_id: str, actor: str):
        risk = self._get_or_raise(risk_id)
        risk.evidence_refs.append(evidence_id)
        risk.add_audit("evidence_added", actor, f"Evidence: {evidence_id}")

    # ── Delete ──────────────────────────────────────────────────────────

    def retire(self, risk_id: str, actor: str, reason: str = ""):
        risk = self._get_or_raise(risk_id)
        risk.risk_status = RiskStatus.RETIRED
        risk.add_audit("retired", actor, reason)

    def close(self, risk_id: str, actor: str, reason: str = ""):
        risk = self._get_or_raise(risk_id)
        risk.risk_status = RiskStatus.CLOSED
        risk.add_audit("closed", actor, reason)

    # ── Export ──────────────────────────────────────────────────────────

    def export_json(self, path: str):
        data = [r.to_dict() for r in self._risks.values()]
        Path(path).write_text(json.dumps(data, indent=2, default=str))

    def export_csv(self, path: str):
        if not self._risks:
            return
        rows = []
        for r in self._risks.values():
            score = r.residual_score or r.inherent_score
            rows.append({
                "risk_id": r.risk_id,
                "title": r.risk_title,
                "domain": r.risk_domain,
                "category": r.risk_category,
                "status": r.risk_status.value,
                "owner": r.risk_owner,
                "mdrs": score.mdrs if score else "",
                "tier": score.tier.value if score else "",
                "review_date": r.review_date,
                "identified_date": r.identified_date,
            })
        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)

    # ── Stats ───────────────────────────────────────────────────────────

    def summary(self) -> dict:
        """Register summary statistics."""
        total = len(self._risks)
        by_tier: dict[str, int] = {}
        by_domain: dict[str, int] = {}
        by_status: dict[str, int] = {}
        for r in self._risks.values():
            score = r.residual_score or r.inherent_score
            if score:
                by_tier[score.tier.value] = by_tier.get(score.tier.value, 0) + 1
            by_domain[r.risk_domain] = by_domain.get(r.risk_domain, 0) + 1
            by_status[r.risk_status.value] = by_status.get(r.risk_status.value, 0) + 1
        return {
            "total_risks": total,
            "by_tier": by_tier,
            "by_domain": by_domain,
            "by_status": by_status,
            "overdue_reviews": len(self.overdue_reviews()),
        }

    # ── Internal ────────────────────────────────────────────────────────

    def _get_or_raise(self, risk_id: str) -> RiskEntry:
        risk = self._risks.get(risk_id)
        if not risk:
            raise KeyError(f"Risk '{risk_id}' not found")
        return risk

    def __len__(self) -> int:
        return len(self._risks)


# ─── Demo / Self-Test ────────────────────────────────────────────────────────

if __name__ == "__main__":
    register = RiskRegister()

    # Create sample risks
    r1 = register.create_risk(
        title="Customer service agent may produce biased responses for loan applicants",
        domain="DAT", category="DAT-03",
        description="Historical data contains demographic biases",
        likelihood=4, impact=4, detectability=3, velocity=3, persistence=4,
        owner="data-science-lead@org.com",
        source="automated_discovery",
        assets=["agent-customer-support-v2", "model-llama-3-8b-customer"],
    )
    print(f"Created: {r1.risk_id} | MDRS: {r1.inherent_score.mdrs} | Tier: {r1.inherent_score.tier.value}")

    r2 = register.create_risk(
        title="Agent goal hijacking via prompt injection",
        domain="SEC", category="SEC-02",
        description="Adversarial input subverts agent objectives",
        likelihood=3, impact=5, detectability=4, velocity=5, persistence=3,
        owner="security-lead@org.com",
        source="red_team",
    )
    print(f"Created: {r2.risk_id} | MDRS: {r2.inherent_score.mdrs} | Tier: {r2.inherent_score.tier.value}")

    r3 = register.create_risk(
        title="Vendor model update changes behavior without notice",
        domain="TPR", category="TPR-03",
        description="Silent model update from third-party provider",
        likelihood=3, impact=3, detectability=3, velocity=2, persistence=3,
        owner="vendor-mgmt@org.com",
    )
    print(f"Created: {r3.risk_id} | MDRS: {r3.inherent_score.mdrs} | Tier: {r3.inherent_score.tier.value}")

    # Update residual score
    register.update_residual_score(
        r1.risk_id, likelihood=2, impact=3, detectability=2, velocity=2, persistence=3,
        actor="data-science-lead@org.com", details="After bias testing and retraining",
    )
    print(f"Updated residual: {r1.residual_score.mdrs} ({r1.residual_score.tier.value})")

    # Summary
    print(f"\nRegister Summary: {json.dumps(register.summary(), indent=2)}")

    # Export
    register.export_json("/tmp/risk_register.json")
    register.export_csv("/tmp/risk_register.csv")
    print("\nExported to /tmp/risk_register.json and /tmp/risk_register.csv")
