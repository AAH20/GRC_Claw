"""
GRC_Claw Risk-Based Decision Making
====================================
Decision support system that uses risk data to recommend actions:
  - Go/No-Go deployment decisions
  - Risk appetite evaluation
  - Treatment prioritization
  - Resource allocation recommendations
  - Exception handling workflow

References GRC-RISK-001 §4.6 (Risk Appetite), §7.2 (Decision Matrix),
and grc-claw-unified-metrics-layer.md §5 (Escalation Thresholds).

Usage:
    from risk_based_decision_making import DecisionEngine

    engine = DecisionEngine(register)
    decision = engine.deployment_decision("agent-customer-support-v2")
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, date
from enum import Enum
from typing import Optional


# ─── Enums ───────────────────────────────────────────────────────────────────

class DecisionOutcome(str, Enum):
    GO = "Go"
    GO_WITH_CONDITIONS = "Go with Conditions"
    NO_GO = "No Go"
    DEFER = "Defer"
    ESCALATE = "Escalate"


class DecisionPriority(str, Enum):
    IMMEDIATE = "Immediate"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


# ─── Data Classes ────────────────────────────────────────────────────────────

@dataclass
class Decision:
    """A risk-based decision record."""
    decision_id: str
    decision_type: str
    subject: str  # system/risk being decided on
    outcome: DecisionOutcome
    priority: DecisionPriority
    rationale: str
    conditions: list[str] = field(default_factory=list)
    approver: str = ""
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    review_date: str = ""
    metadata: dict = field(default_factory=dict)


@dataclass
class DeploymentAssessment:
    """Result of a deployment go/no-go assessment."""
    system_id: str
    outcome: DecisionOutcome
    blocking_risks: list[dict]
    conditional_risks: list[dict]
    required_actions: list[str]
    risk_score: float
    risk_tier: str
    assessment_date: str


# ─── Decision Engine ─────────────────────────────────────────────────────────

class DecisionEngine:
    """
    Risk-based decision making engine.
    Evaluates risks and recommends actions based on appetite, tier, and context.
    """

    def __init__(self, register, workflow=None, monitor=None):
        self.register = register
        self.workflow = workflow
        self.monitor = monitor
        self._decisions: list[Decision] = []
        self._counter = 0

    # ── Deployment Go/No-Go ────────────────────────────────────────────

    def deployment_decision(self, system_id: str) -> DeploymentAssessment:
        """
        Evaluate whether an AI system should be deployed.
        Considers all risks associated with the system's assets.
        """
        # Find risks affecting this system
        system_risks = [
            r for r in self.register.all()
            if system_id in r.affected_assets
        ]

        if not system_risks:
            return DeploymentAssessment(
                system_id=system_id,
                outcome=DecisionOutcome.GO,
                blocking_risks=[],
                conditional_risks=[],
                required_actions=[],
                risk_score=0.0,
                risk_tier="Minimal",
                assessment_date=date.today().isoformat(),
            )

        # Categorize risks
        blocking = []
        conditional = []
        max_score = 0.0
        max_tier = "Minimal"

        for risk in system_risks:
            score = risk.residual_score or risk.inherent_score
            if not score:
                continue

            risk_info = {
                "risk_id": risk.risk_id,
                "category": risk.risk_category,
                "title": risk.risk_title,
                "mdrs": score.mdrs,
                "tier": score.tier.value,
                "status": risk.risk_status.value,
            }

            if score.tier.value == "Critical":
                blocking.append(risk_info)
            elif score.tier.value == "High":
                blocking.append(risk_info)
            elif score.tier.value == "Medium":
                conditional.append(risk_info)

            if score.mdrs > max_score:
                max_score = score.mdrs
                max_tier = score.tier.value

        # Determine outcome
        if blocking:
            outcome = DecisionOutcome.NO_GO
        elif conditional:
            outcome = DecisionOutcome.GO_WITH_CONDITIONS
        else:
            outcome = DecisionOutcome.GO

        # Required actions
        actions = []
        for risk in blocking:
            actions.append(f"Resolve blocking risk {risk['risk_id']}: {risk['title']}")
        for risk in conditional:
            actions.append(f"Mitigate conditional risk {risk['risk_id']}: {risk['title']}")

        return DeploymentAssessment(
            system_id=system_id,
            outcome=outcome,
            blocking_risks=blocking,
            conditional_risks=conditional,
            required_actions=actions,
            risk_score=max_score,
            risk_tier=max_tier,
            assessment_date=date.today().isoformat(),
        )

    # ── Risk Appetite Evaluation ────────────────────────────────────────

    def evaluate_risk_appetite(self, proposed_risk_mdrs: float, domain: str) -> dict:
        """
        Evaluate whether a proposed risk level is within appetite.
        Returns detailed assessment with recommendations.
        """
        from mdrs_scoring_engine import classify_tier, RiskTier

        tier = classify_tier(proposed_risk_mdrs)
        within_appetite = proposed_risk_mdrs <= 3.49  # Default appetite

        result = {
            "proposed_mdrs": proposed_risk_mdrs,
            "proposed_tier": tier.value,
            "domain": domain,
            "within_appetite": within_appetite,
            "max_acceptable_mdrs": 3.49,
            "max_acceptable_tier": "Medium",
        }

        if tier == RiskTier.CRITICAL:
            result["recommendation"] = "REJECT — Risk exceeds appetite. Avoid or implement immediate mitigation."
            result["approval_authority"] = "Risk Committee"
            result["max_treatment_window"] = "30 days"
        elif tier == RiskTier.HIGH:
            result["recommendation"] = "CONDITIONAL — Risk exceeds default appetite. Requires executive approval and active mitigation."
            result["approval_authority"] = "CISO / CTO"
            result["max_treatment_window"] = "90 days"
        elif tier == RiskTier.MEDIUM:
            result["recommendation"] = "ACCEPTABLE — Risk within appetite. Standard mitigation and monitoring."
            result["approval_authority"] = "Department Head"
            result["max_treatment_window"] = "180 days"
        else:
            result["recommendation"] = "ACCEPTABLE — Risk within appetite. Routine monitoring."
            result["approval_authority"] = "Business Unit Owner" if tier == RiskTier.LOW else "System Owner"
            result["max_treatment_window"] = "12 months"

        return result

    # ── Treatment Prioritization ────────────────────────────────────────

    def prioritize_treatments(self) -> list[dict]:
        """
        Generate prioritized treatment queue.
        Considers risk tier, business impact, and treatment readiness.
        """
        active_risks = [
            r for r in self.register.all()
            if r.risk_status.value not in ("closed", "retired", "treated")
        ]

        prioritized = []
        for risk in active_risks:
            score = risk.residual_score or risk.inherent_score
            if not score:
                continue

            # Calculate priority score (higher = more urgent)
            tier_weight = {"Critical": 5, "High": 4, "Medium": 3, "Low": 2, "Minimal": 1}
            priority_score = score.mdrs * tier_weight.get(score.tier.value, 1)

            # Boost for overdue reviews
            if risk.review_date and risk.review_date < date.today().isoformat():
                priority_score *= 1.5

            # Boost for risks without treatment plans
            if not risk.treatment_plan:
                priority_score *= 1.2

            prioritized.append({
                "risk_id": risk.risk_id,
                "title": risk.risk_title,
                "category": risk.risk_category,
                "domain": risk.risk_domain,
                "mdrs": score.mdrs,
                "tier": score.tier.value,
                "priority_score": round(priority_score, 2),
                "has_treatment_plan": risk.treatment_plan is not None,
                "review_date": risk.review_date,
                "recommended_strategy": self._recommend_strategy(score.tier.value),
            })

        # Sort by priority score descending
        prioritized.sort(key=lambda x: x["priority_score"], reverse=True)
        return prioritized

    # ── Resource Allocation ────────────────────────────────────────────

    def recommend_resource_allocation(self) -> dict:
        """
        Recommend resource allocation based on risk distribution.
        Identifies domains and categories needing most attention.
        """
        domain_risks: dict[str, list[float]] = {}
        category_risks: dict[str, list[float]] = {}

        for risk in self.register.all():
            score = risk.residual_score or risk.inherent_score
            if not score:
                continue
            domain_risks.setdefault(risk.risk_domain, []).append(score.mdrs)
            category_risks.setdefault(risk.risk_category, []).append(score.mdrs)

        # Calculate risk exposure by domain
        domain_exposure = {}
        for domain, scores in domain_risks.items():
            domain_exposure[domain] = {
                "risk_count": len(scores),
                "total_exposure": round(sum(scores), 2),
                "mean_score": round(sum(scores) / len(scores), 2),
                "max_score": max(scores),
            }

        # Calculate risk exposure by category
        category_exposure = {}
        for cat, scores in category_risks.items():
            category_exposure[cat] = {
                "risk_count": len(scores),
                "total_exposure": round(sum(scores), 2),
                "mean_score": round(sum(scores) / len(scores), 2),
            }

        # Sort by total exposure
        sorted_domains = sorted(domain_exposure.items(), key=lambda x: x[1]["total_exposure"], reverse=True)
        sorted_categories = sorted(category_exposure.items(), key=lambda x: x[1]["total_exposure"], reverse=True)

        # Recommendations
        recommendations = []
        if sorted_domains:
            top_domain = sorted_domains[0]
            recommendations.append(
                f"Allocate additional resources to {top_domain[0]} domain "
                f"(exposure: {top_domain[1]['total_exposure']}, {top_domain[1]['risk_count']} risks)"
            )
        if sorted_categories:
            top_cat = sorted_categories[0]
            recommendations.append(
                f"Prioritize {top_cat[0]} category treatment "
                f"(exposure: {top_cat[1]['total_exposure']})"
            )

        return {
            "domain_exposure": dict(sorted_domains),
            "category_exposure": dict(sorted_categories),
            "recommendations": recommendations,
            "total_risks": sum(d["risk_count"] for d in domain_exposure.values()),
            "total_exposure": round(sum(d["total_exposure"] for d in domain_exposure.values()), 2),
        }

    # ── Exception Handling ─────────────────────────────────────────────

    def evaluate_exception_request(
        self,
        risk_id: str,
        requested_by: str,
        exception_type: str,
        justification: str,
        proposed_duration_days: int,
        compensating_controls: list[str],
    ) -> dict:
        """
        Evaluate a risk exception request (accepting risk beyond appetite).
        Returns recommendation with conditions.
        """
        risk = self.register.get(risk_id)
        if not risk:
            return {"error": f"Risk {risk_id} not found"}

        score = risk.residual_score or risk.inherent_score
        if not score:
            return {"error": "Risk has no score"}

        # Evaluate based on tier
        if score.tier.value == "Critical":
            return {
                "recommendation": "REJECT",
                "rationale": "Critical risks cannot be accepted via exception. Must be mitigated or avoided.",
                "alternative": "Implement mitigation plan and re-assess.",
            }
        elif score.tier.value == "High":
            if proposed_duration_days > 90:
                return {
                    "recommendation": "REJECT",
                    "rationale": f"Exception duration {proposed_duration_days} days exceeds 90-day maximum for High risks.",
                    "alternative": "Request shorter duration or escalate to Risk Committee.",
                }
            if len(compensating_controls) < 2:
                return {
                    "recommendation": "CONDITIONAL",
                    "rationale": "High risk exceptions require at least 2 compensating controls.",
                    "conditions": [
                        "Minimum 2 compensating controls required",
                        "Monthly review mandatory",
                        "CISO approval required",
                    ],
                }
            return {
                "recommendation": "CONDITIONAL",
                "rationale": "High risk exception may be acceptable with adequate controls.",
                "conditions": [
                    "Implement all compensating controls",
                    "Monthly review mandatory",
                    "CISO approval required",
                    f"Maximum duration: {proposed_duration_days} days",
                ],
            }
        else:
            return {
                "recommendation": "ACCEPT",
                "rationale": f"{score.tier.value} risk within acceptable exception parameters.",
                "conditions": [
                    "Document compensating controls",
                    "Quarterly review",
                    "Risk owner approval",
                ],
            }

    # ── Decision Recording ─────────────────────────────────────────────

    def record_decision(
        self,
        decision_type: str,
        subject: str,
        outcome: DecisionOutcome,
        priority: DecisionPriority,
        rationale: str,
        conditions: Optional[list[str]] = None,
        approver: str = "",
    ) -> Decision:
        """Record a decision for audit trail."""
        self._counter += 1
        decision = Decision(
            decision_id=f"DEC-{datetime.now().year}-{self._counter:04d}",
            decision_type=decision_type,
            subject=subject,
            outcome=outcome,
            priority=priority,
            rationale=rationale,
            conditions=conditions or [],
            approver=approver,
        )
        self._decisions.append(decision)
        return decision

    def get_decisions(
        self, decision_type: Optional[str] = None,
        outcome: Optional[DecisionOutcome] = None,
    ) -> list[Decision]:
        """Query recorded decisions."""
        results = self._decisions
        if decision_type:
            results = [d for d in results if d.decision_type == decision_type]
        if outcome:
            results = [d for d in results if d.outcome == outcome]
        return results

    # ── Helper Methods ─────────────────────────────────────────────────

    @staticmethod
    def _recommend_strategy(tier: str) -> str:
        strategies = {
            "Critical": "Avoid",
            "High": "Mitigate",
            "Medium": "Mitigate",
            "Low": "Accept",
            "Minimal": "Accept",
        }
        return strategies.get(tier, "Mitigate")


# ─── Demo / Self-Test ────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from risk_register import RiskRegister, RiskTier

    register = RiskRegister()
    engine = DecisionEngine(register)

    # Create risks for a system
    r1 = register.create_risk(
        title="Agent goal hijacking vulnerability",
        domain="SEC", category="SEC-02",
        likelihood=3, impact=5, detectability=4, velocity=5, persistence=3,
        assets=["agent-customer-support-v2"],
        owner="security-lead@org.com",
    )
    r2 = register.create_risk(
        title="Bias in customer responses",
        domain="DAT", category="DAT-03",
        likelihood=4, impact=4, detectability=3, velocity=3, persistence=4,
        assets=["agent-customer-support-v2"],
        owner="data-science-lead@org.com",
    )
    r3 = register.create_risk(
        title="Minor latency degradation",
        domain="OPS", category="OPS-03",
        likelihood=2, impact=2, detectability=2, velocity=1, persistence=1,
        assets=["agent-customer-support-v2"],
        owner="sre@org.com",
    )

    # Deployment decision
    assessment = engine.deployment_decision("agent-customer-support-v2")
    print("=== Deployment Decision ===")
    print(f"Outcome: {assessment.outcome.value}")
    print(f"Risk Score: {assessment.risk_score} ({assessment.risk_tier})")
    print(f"Blocking Risks: {len(assessment.blocking_risks)}")
    print(f"Conditional Risks: {len(assessment.conditional_risks)}")
    print(f"Required Actions: {assessment.required_actions}")

    # Risk appetite evaluation
    print("\n=== Risk Appetite Evaluation ===")
    appetite = engine.evaluate_risk_appetite(3.8, "SEC")
    print(f"MDRS 3.8 in SEC: {appetite['recommendation']}")

    # Treatment prioritization
    print("\n=== Treatment Prioritization ===")
    prioritized = engine.prioritize_treatments()
    for i, item in enumerate(prioritized[:3], 1):
        print(f"{i}. [{item['risk_id']}] {item['title']} — Priority: {item['priority_score']}")

    # Resource allocation
    print("\n=== Resource Allocation ===")
    allocation = engine.recommend_resource_allocation()
    print(f"Total Exposure: {allocation['total_exposure']}")
    for rec in allocation['recommendations']:
        print(f"  - {rec}")

    # Exception request
    print("\n=== Exception Request ===")
    exception = engine.evaluate_exception_request(
        risk_id=r1.risk_id,
        requested_by="security-lead@org.com",
        exception_type="risk_acceptance",
        justification="Compensating controls in place",
        proposed_duration_days=60,
        compensating_controls=["goal_monitoring", "rate_limiting"],
    )
    print(f"Recommendation: {exception['recommendation']}")
    if 'conditions' in exception:
        print(f"Conditions: {exception['conditions']}")
