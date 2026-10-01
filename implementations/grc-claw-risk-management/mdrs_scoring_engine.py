"""
GRC_Claw MDRS Scoring Engine
=============================
Multi-Dimensional Risk Score (MDRS) calculation engine.
Implements GRC-RISK-001 §4.1-4.6: scoring formula, tier classification,
inherent vs residual risk, cascading risk, and risk appetite.

Usage:
    from mdrs_scoring_engine import MDRSEngine, RiskScore

    engine = MDRSEngine()
    score = engine.calculate(likelihood=4, impact=4, detectability=3, velocity=3, persistence=4)
    print(f"MDRS: {score.mdrs} | Tier: {score.tier.value}")
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Optional


# ─── Enums & Constants ───────────────────────────────────────────────────────

class RiskTier(str, Enum):
    MINIMAL = "Minimal"
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class EUAIActTier(str, Enum):
    MINIMAL = "Minimal Risk"
    LIMITED = "Limited Risk"
    HIGH = "High Risk (Annex III)"
    PROHIBITED = "Prohibited (Art. 5)"


# MDRS dimension weights (GRC-RISK-001 §4.1)
WEIGHTS = {
    "likelihood": 0.25,
    "impact": 0.30,
    "detectability": 0.15,
    "velocity": 0.15,
    "persistence": 0.15,
}

# Tier boundaries (GRC-RISK-001 §4.3)
TIER_BOUNDARIES = {
    RiskTier.MINIMAL: (1.00, 1.49),
    RiskTier.LOW: (1.50, 2.49),
    RiskTier.MEDIUM: (2.50, 3.49),
    RiskTier.HIGH: (3.50, 4.49),
    RiskTier.CRITICAL: (4.50, 5.00),
}

# EU AI Act mapping (GRC-RISK-001 §4.4)
EU_AI_ACT_MAPPING = {
    RiskTier.MINIMAL: EUAIActTier.MINIMAL,
    RiskTier.LOW: EUAIActTier.LIMITED,
    RiskTier.MEDIUM: EUAIActTier.HIGH,
    RiskTier.HIGH: EUAIActTier.HIGH,
    RiskTier.CRITICAL: EUAIActTier.PROHIBITED,
}

# Default risk appetite thresholds (GRC-RISK-001 §4.6)
DEFAULT_APPETITE = {
    "max_acceptable_mdrs": 3.49,
    "max_acceptable_tier": RiskTier.MEDIUM,
    "critical_approval_authority": "Risk Committee",
    "high_approval_authority": "CISO / CTO",
    "medium_approval_authority": "Department Head",
    "low_approval_authority": "Business Unit Owner",
    "minimal_approval_authority": "System Owner",
}

# Review frequency by tier (GRC-RISK-001 §4.3)
REVIEW_FREQUENCY = {
    RiskTier.MINIMAL: "Annual",
    RiskTier.LOW: "Semi-annual",
    RiskTier.MEDIUM: "Quarterly",
    RiskTier.HIGH: "Monthly",
    RiskTier.CRITICAL: "Continuous",
}

# Response SLA by tier (GRC-RISK-001 §4.3)
RESPONSE_SLA = {
    RiskTier.MINIMAL: "30 days",
    RiskTier.LOW: "14 days",
    RiskTier.MEDIUM: "7 days",
    RiskTier.HIGH: "48 hours",
    RiskTier.CRITICAL: "4 hours",
}


# ─── Scoring Scales (GRC-RISK-001 Appendix B) ────────────────────────────────

LIKELIHOOD_SCALE = {
    1: ("Rare", "<1% per year"),
    2: ("Unlikely", "1-10% per year"),
    3: ("Possible", "10-50% per year"),
    4: ("Likely", "50-90% per year"),
    5: ("Almost Certain", ">90% per year"),
}

IMPACT_SCALE = {
    1: ("Negligible", "No discernible impact"),
    2: ("Minor", "Small impact, easily recoverable"),
    3: ("Moderate", "Significant impact, recoverable with effort"),
    4: ("Major", "Severe impact, difficult to recover"),
    5: ("Catastrophic", "Existential impact"),
}

DETECTABILITY_SCALE = {
    1: ("Easy", "Immediately visible and detectable"),
    2: ("Moderate", "Detectable with standard monitoring"),
    3: ("Difficult", "Requires specialized detection capability"),
    4: ("Very Difficult", "Hidden, requires active investigation"),
    5: ("Impossible", "Cannot be detected before harm occurs"),
}

VELOCITY_SCALE = {
    1: ("Slow", "Weeks or months"),
    2: ("Moderate", "Days"),
    3: ("Fast", "Hours"),
    4: ("Very Fast", "Minutes"),
    5: ("Instant", "Immediate upon trigger"),
}

PERSISTENCE_SCALE = {
    1: ("Transient", "Resolves automatically within minutes"),
    2: ("Short-term", "Resolves within hours"),
    3: ("Medium-term", "Resolves within days"),
    4: ("Long-term", "Persists for weeks or months"),
    5: ("Permanent", "Irreversible"),
}


# ─── Data Classes ────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class RiskScore:
    """Immutable MDRS score with all five dimensions."""
    likelihood: int
    impact: int
    detectability: int
    velocity: int
    persistence: int

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
        """Calculate MDRS using the weighted formula."""
        return round(
            self.likelihood * WEIGHTS["likelihood"]
            + self.impact * WEIGHTS["impact"]
            + self.detectability * WEIGHTS["detectability"]
            + self.velocity * WEIGHTS["velocity"]
            + self.persistence * WEIGHTS["persistence"],
            2,
        )

    @property
    def tier(self) -> RiskTier:
        return classify_tier(self.mdrs)

    @property
    def eu_ai_act_tier(self) -> EUAIActTier:
        return EU_AI_ACT_MAPPING[self.tier]

    def to_dict(self) -> dict:
        return {
            "likelihood": self.likelihood,
            "impact": self.impact,
            "detectability": self.detectability,
            "velocity": self.velocity,
            "persistence": self.persistence,
            "mdrs": self.mdrs,
            "tier": self.tier.value,
            "eu_ai_act_tier": self.eu_ai_act_tier.value,
        }


@dataclass
class CascadingRiskResult:
    """Result of cascading risk analysis."""
    base_score: RiskScore
    active_upstream_count: int
    propagation_factor: float
    effective_mdrs: float
    effective_tier: RiskTier


@dataclass
class ControlEffectiveness:
    """Control effectiveness calculation (GRC-RISK-001 §4.5)."""
    inherent_mdrs: float
    residual_mdrs: float
    effectiveness_pct: float
    risk_reduction: float


# ─── Core Engine ─────────────────────────────────────────────────────────────

class MDRSEngine:
    """
    MDRS Scoring Engine — calculates, classifies, and analyzes risk scores.
    """

    def __init__(self, appetite: Optional[dict] = None):
        self.appetite = appetite or DEFAULT_APPETITE.copy()

    # ── Basic Scoring ──────────────────────────────────────────────────

    def calculate(
        self,
        likelihood: int,
        impact: int,
        detectability: int,
        velocity: int,
        persistence: int,
    ) -> RiskScore:
        """Create a RiskScore from raw dimension values."""
        return RiskScore(likelihood, impact, detectability, velocity, persistence)

    def score_from_dict(self, data: dict) -> RiskScore:
        """Create a RiskScore from a dictionary."""
        return RiskScore(
            likelihood=data["likelihood"],
            impact=data["impact"],
            detectability=data["detectability"],
            velocity=data["velocity"],
            persistence=data["persistence"],
        )

    # ── Tier Classification ─────────────────────────────────────────────

    def classify(self, mdrs: float) -> RiskTier:
        return classify_tier(mdrs)

    def get_approval_authority(self, tier: RiskTier) -> str:
        return DEFAULT_APPETITE[f"{tier.name.lower()}_approval_authority"]

    def get_review_frequency(self, tier: RiskTier) -> str:
        return REVIEW_FREQUENCY[tier]

    def get_response_sla(self, tier: RiskTier) -> str:
        return RESPONSE_SLA[tier]

    # ── Inherent vs Residual ───────────────────────────────────────────

    def calculate_control_effectiveness(
        self, inherent: RiskScore, residual: RiskScore
    ) -> ControlEffectiveness:
        """
        Control Effectiveness = (Inherent - Residual) / Inherent × 100
        (GRC-RISK-001 §4.5)
        """
        inh = inherent.mdrs
        res = residual.mdrs
        if inh == 0:
            return ControlEffectiveness(inh, res, 0.0, 0.0)
        effectiveness = round((inh - res) / inh * 100, 2)
        reduction = round(inh - res, 2)
        return ControlEffectiveness(inh, res, effectiveness, reduction)

    # ── Cascading Risk ─────────────────────────────────────────────────

    def calculate_cascading_impact(
        self, base_score: RiskScore, active_upstream_count: int
    ) -> CascadingRiskResult:
        """
        Effective MDRS = Base MDRS × (1 + 0.2 × Number of Active Upstream Risks)
        Capped at 5.00 (GRC-RISK-001 §6.4)
        """
        factor = 1 + 0.2 * active_upstream_count
        effective = min(round(base_score.mdrs * factor, 2), 5.00)
        return CascadingRiskResult(
            base_score=base_score,
            active_upstream_count=active_upstream_count,
            propagation_factor=factor,
            effective_mdrs=effective,
            effective_tier=classify_tier(effective),
        )

    # ── Risk Appetite ───────────────────────────────────────────────────

    def within_appetite(self, score: RiskScore) -> bool:
        """Check if risk score is within defined risk appetite."""
        return score.mdrs <= self.appetite["max_acceptable_mdrs"]

    def appetite_status(self, score: RiskScore) -> dict:
        """Detailed appetite check with metadata."""
        within = self.within_appetite(score)
        return {
            "mdrs": score.mdrs,
            "tier": score.tier.value,
            "within_appetite": within,
            "max_acceptable_mdrs": self.appetite["max_acceptable_mdrs"],
            "max_acceptable_tier": self.appetite["max_acceptable_tier"].value,
            "requires_executive_approval": score.tier in (RiskTier.HIGH, RiskTier.CRITICAL),
            "approval_authority": self.get_approval_authority(score.tier),
        }

    # ── Sensitivity Analysis ────────────────────────────────────────────

    def sensitivity_analysis(self, base: RiskScore) -> dict:
        """
        Analyze how each dimension affects the overall score.
        Shows the MDRS impact of +/-1 on each dimension.
        """
        base_mdrs = base.mdrs
        results = {}
        for dim in ["likelihood", "impact", "detectability", "velocity", "persistence"]:
            current_val = getattr(base, dim)
            # +1 scenario
            if current_val < 5:
                plus_kwargs = {
                    "likelihood": base.likelihood,
                    "impact": base.impact,
                    "detectability": base.detectability,
                    "velocity": base.velocity,
                    "persistence": base.persistence,
                }
                plus_kwargs[dim] = current_val + 1
                plus_score = RiskScore(**plus_kwargs).mdrs
            else:
                plus_score = base_mdrs
            # -1 scenario
            if current_val > 1:
                minus_kwargs = {
                    "likelihood": base.likelihood,
                    "impact": base.impact,
                    "detectability": base.detectability,
                    "velocity": base.velocity,
                    "persistence": base.persistence,
                }
                minus_kwargs[dim] = current_val - 1
                minus_score = RiskScore(**minus_kwargs).mdrs
            else:
                minus_score = base_mdrs
            results[dim] = {
                "current": current_val,
                "weight": WEIGHTS[dim],
                "mdrs_if_plus_1": plus_score,
                "mdrs_if_minus_1": minus_score,
                "swing": round(plus_score - minus_score, 2),
            }
        return results

    # ── Scale Descriptions ──────────────────────────────────────────────

    @staticmethod
    def describe_score(score: RiskScore) -> dict:
        """Human-readable description of each dimension."""
        return {
            "likelihood": {"value": score.likelihood, "label": LIKELIHOOD_SCALE[score.likelihood][0], "description": LIKELIHOOD_SCALE[score.likelihood][1]},
            "impact": {"value": score.impact, "label": IMPACT_SCALE[score.impact][0], "description": IMPACT_SCALE[score.impact][1]},
            "detectability": {"value": score.detectability, "label": DETECTABILITY_SCALE[score.detectability][0], "description": DETECTABILITY_SCALE[score.detectability][1]},
            "velocity": {"value": score.velocity, "label": VELOCITY_SCALE[score.velocity][0], "description": VELOCITY_SCALE[score.velocity][1]},
            "persistence": {"value": score.persistence, "label": PERSISTENCE_SCALE[score.persistence][0], "description": PERSISTENCE_SCALE[score.persistence][1]},
        }


# ─── Standalone Functions ────────────────────────────────────────────────────

def classify_tier(mdrs: float) -> RiskTier:
    """Classify MDRS into risk tier (GRC-RISK-001 §4.3)."""
    if mdrs >= 4.50:
        return RiskTier.CRITICAL
    elif mdrs >= 3.50:
        return RiskTier.HIGH
    elif mdrs >= 2.50:
        return RiskTier.MEDIUM
    elif mdrs >= 1.50:
        return RiskTier.LOW
    else:
        return RiskTier.MINIMAL


def tier_color(tier: RiskTier) -> str:
    """Return color indicator for tier."""
    return {
        RiskTier.MINIMAL: "🟢 Green",
        RiskTier.LOW: "🟢 Green",
        RiskTier.MEDIUM: "🟡 Amber",
        RiskTier.HIGH: "🔴 Red",
        RiskTier.CRITICAL: "🔴 Red",
    }[tier]


# ─── Demo / Self-Test ────────────────────────────────────────────────────────

if __name__ == "__main__":
    engine = MDRSEngine()

    # Basic scoring
    score = engine.calculate(likelihood=4, impact=4, detectability=3, velocity=3, persistence=4)
    print(f"MDRS: {score.mdrs} | Tier: {score.tier.value} | EU AI Act: {score.eu_ai_act_tier.value}")
    print(f"Color: {tier_color(score.tier)}")
    print(f"Approval Authority: {engine.get_approval_authority(score.tier)}")
    print(f"Review Frequency: {engine.get_review_frequency(score.tier)}")
    print(f"Response SLA: {engine.get_response_sla(score.tier)}")

    # Appetite check
    appetite = engine.appetite_status(score)
    print(f"\nAppetite Check: {appetite}")

    # Control effectiveness
    residual = engine.calculate(likelihood=2, impact=3, detectability=2, velocity=2, persistence=3)
    effectiveness = engine.calculate_control_effectiveness(score, residual)
    print(f"\nControl Effectiveness: {effectiveness.effectiveness_pct}% (reduction: {effectiveness.risk_reduction})")

    # Cascading risk
    cascade = engine.calculate_cascading_impact(score, active_upstream_count=2)
    print(f"\nCascading Risk: Base {cascade.base_score.mdrs} → Effective {cascade.effective_mdrs} ({cascade.effective_tier.value})")

    # Sensitivity analysis
    sens = engine.sensitivity_analysis(score)
    print(f"\nSensitivity Analysis:")
    for dim, data in sens.items():
        print(f"  {dim}: swing={data['swing']} (+1={data['mdrs_if_plus_1']}, -1={data['mdrs_if_minus_1']})")

    # Scale descriptions
    desc = engine.describe_score(score)
    print(f"\nScale Descriptions:")
    for dim, info in desc.items():
        print(f"  {dim}: {info['value']} ({info['label']}) — {info['description']}")
