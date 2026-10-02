"""
Pricing Factors Engine — transparent pricing logic for GRC_Claw.

All pricing factors are explicit, documented, and configurable.
No hidden multipliers — every cost driver is visible.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
from .models import OrganizationProfile, DeploymentModel, SupportLevel, PricingTier


# ── Base Unit Prices (annual, USD) ──────────────────────────────────────────

BASE_PRICES = {
    "agent_base": 12_000,          # per agent/year
    "model_base": 6_000,           # per model/year
    "policy_base": 240,           # per policy/year
    "evidence_base": 0.50,         # per GB/year
    "framework_base": 3_600,       # per framework/year
}

# ── Volume Discount Tiers ───────────────────────────────────────────────────

VOLUME_DISCOUNT_TIERS = [
    (1, 10, 0),        # 1-10 agents: 0%
    (11, 50, 5),       # 11-50 agents: 5%
    (51, 200, 10),     # 51-200 agents: 10%
    (201, 500, 15),    # 201-500 agents: 15%
    (501, 1000, 20),   # 501-1000 agents: 20%
    (1001, float("inf"), 25),  # 1000+ agents: 25%
]

# ── Deployment Model Multipliers ─────────────────────────────────────────────

DEPLOYMENT_MULTIPLIERS = {
    DeploymentModel.CLOUD_SAAS: 1.0,
    DeploymentModel.PRIVATE_CLOUD: 1.35,
    DeploymentModel.ON_PREMISES: 1.60,
    DeploymentModel.HYBRID: 1.20,
}

# ── Support Level Multipliers ───────────────────────────────────────────────

SUPPORT_MULTIPLIERS = {
    SupportLevel.STANDARD: 1.0,
    SupportLevel.PREMIUM: 1.25,
    SupportLevel.ENTERPRISE: 1.50,
}

# ── Pricing Tier Adjustments ────────────────────────────────────────────────

TIER_ADJUSTMENTS = {
    PricingTier.STARTUP: -0.10,     # 10% discount for startups
    PricingTier.GROWTH: 0.0,        # baseline
    PricingTier.ENTERPRISE: 0.15,   # 15% premium for enterprise features
}

# ── Industry Risk Adjustments ───────────────────────────────────────────────

INDUSTRY_RISK_MULTIPLIERS = {
    "healthcare": 1.20,
    "finance": 1.25,
    "banking": 1.25,
    "insurance": 1.15,
    "government": 1.10,
    "defense": 1.30,
    "energy": 1.15,
    "technology": 1.00,
    "retail": 1.05,
    "manufacturing": 1.05,
    "education": 0.90,
    "nonprofit": 0.85,
    "other": 1.00,
}

# ── Compliance Maturity Adjustment ──────────────────────────────────────────
# Less mature organizations need more hand-holding → higher cost

def maturity_adjustment(maturity: float) -> float:
    """Return multiplier based on compliance maturity (1-10 scale).
    Lower maturity = higher cost (more support needed).
    """
    if maturity <= 3:
        return 1.20
    elif maturity <= 5:
        return 1.10
    elif maturity <= 7:
        return 1.00
    elif maturity <= 9:
        return 0.95
    else:
        return 0.90


@dataclass
class PricingFactor:
    """A single transparent pricing factor."""

    name: str
    description: str
    value: float
    unit: str
    category: str
    applied: bool = True


@dataclass
class PricingBreakdown:
    """Complete pricing breakdown for transparency."""

    base_costs: dict[str, float] = field(default_factory=dict)
    factors: list[PricingFactor] = field(default_factory=list)
    volume_discount_pct: float = 0.0
    volume_discount_amount: float = 0.0
    subtotal: float = 0.0
    total_multiplier: float = 1.0
    final_cost: float = 0.0


class PricingEngine:
    """
    Transparent pricing engine that computes all cost factors.
    
    Every factor is exposed and documented. No black-box pricing.
    """

    def __init__(self, base_prices: Optional[dict] = None):
        self.base_prices = base_prices or BASE_PRICES.copy()

    def get_volume_discount(self, agents: int) -> float:
        """Get volume discount percentage based on agent count."""
        for min_agents, max_agents, discount in VOLUME_DISCOUNT_TIERS:
            if min_agents <= agents <= max_agents:
                return float(discount)
        return 0.0

    def get_deployment_multiplier(self, model: DeploymentModel) -> float:
        """Get deployment model cost multiplier."""
        return DEPLOYMENT_MULTIPLIERS.get(model, 1.0)

    def get_support_multiplier(self, level: SupportLevel) -> float:
        """Get support level cost multiplier."""
        return SUPPORT_MULTIPLIERS.get(level, 1.0)

    def get_tier_adjustment(self, tier: PricingTier) -> float:
        """Get pricing tier adjustment (can be negative for discounts)."""
        return TIER_ADJUSTMENTS.get(tier, 0.0)

    def get_industry_multiplier(self, industry: str) -> float:
        """Get industry risk multiplier."""
        return INDUSTRY_RISK_MULTIPLIERS.get(industry.lower(), 1.0)

    def compute_base_costs(self, profile: OrganizationProfile) -> dict[str, float]:
        """Compute base costs before any adjustments."""
        return {
            "agents": profile.agents * self.base_prices["agent_base"],
            "models": profile.models * self.base_prices["model_base"],
            "policies": profile.policies * self.base_prices["policy_base"],
            "evidence": profile.evidence_volume_gb * self.base_prices["evidence_base"],
            "frameworks": len(profile.frameworks) * self.base_prices["framework_base"],
        }

    def compute_all_factors(self, profile: OrganizationProfile) -> list[PricingFactor]:
        """Compute all pricing factors for full transparency."""
        factors = []

        # Volume discount
        vol_disc = self.get_volume_discount(profile.agents)
        factors.append(PricingFactor(
            name="Volume Discount",
            description=f"Based on {profile.agents} agents",
            value=vol_disc,
            unit="%",
            category="discount",
        ))

        # Deployment multiplier
        dep_mult = self.get_deployment_multiplier(profile.deployment_model)
        factors.append(PricingFactor(
            name="Deployment Model",
            description=profile.deployment_model.value.replace("_", " ").title(),
            value=dep_mult,
            unit="x",
            category="multiplier",
        ))

        # Support multiplier
        sup_mult = self.get_support_multiplier(profile.support_level)
        factors.append(PricingFactor(
            name="Support Level",
            description=profile.support_level.value.title(),
            value=sup_mult,
            unit="x",
            category="multiplier",
        ))

        # Tier adjustment
        tier_adj = self.get_tier_adjustment(profile.pricing_tier)
        factors.append(PricingFactor(
            name="Pricing Tier",
            description=profile.pricing_tier.value.title(),
            value=tier_adj,
            unit="%" if tier_adj >= 0 else "% discount",
            category="adjustment",
        ))

        # Industry multiplier
        ind_mult = self.get_industry_multiplier(profile.industry)
        factors.append(PricingFactor(
            name="Industry Risk",
            description=profile.industry.title(),
            value=ind_mult,
            unit="x",
            category="multiplier",
        ))

        # Maturity adjustment
        mat_adj = maturity_adjustment(profile.compliance_maturity)
        factors.append(PricingFactor(
            name="Compliance Maturity",
            description=f"Maturity score: {profile.compliance_maturity}/10",
            value=mat_adj,
            unit="x",
            category="adjustment",
        ))

        return factors

    def compute_breakdown(self, profile: OrganizationProfile) -> PricingBreakdown:
        """Compute complete pricing breakdown."""
        base_costs = self.compute_base_costs(profile)
        factors = self.compute_all_factors(profile)

        subtotal = sum(base_costs.values())
        vol_disc = self.get_volume_discount(profile.agents)
        vol_disc_amount = subtotal * (vol_disc / 100)

        # Apply multipliers
        dep_mult = self.get_deployment_multiplier(profile.deployment_model)
        sup_mult = self.get_support_multiplier(profile.support_level)
        tier_adj = self.get_tier_adjustment(profile.pricing_tier)
        ind_mult = self.get_industry_multiplier(profile.industry)
        mat_adj = maturity_adjustment(profile.compliance_maturity)

        total_multiplier = dep_mult * sup_mult * ind_mult * mat_adj
        if tier_adj != 0:
            total_multiplier *= (1 + tier_adj)

        after_discount = subtotal - vol_disc_amount
        final_cost = after_discount * total_multiplier

        return PricingBreakdown(
            base_costs=base_costs,
            factors=factors,
            volume_discount_pct=vol_disc,
            volume_discount_amount=vol_disc_amount,
            subtotal=subtotal,
            total_multiplier=total_multiplier,
            final_cost=final_cost,
        )
