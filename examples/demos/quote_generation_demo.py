#!/usr/bin/env python3
"""
GRC_Claw Quote Generation Demo
===============================
Demonstrates the complete quote generation workflow:
  1. Define organization profile
  2. Calculate pricing with transparent factors
  3. Generate quotes in multiple formats (JSON, HTML, Markdown, Text)

Usage:
    python quote_generation_demo.py
"""

import json
import uuid
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional
from pathlib import Path


# ── Enums & Types ──────────────────────────────────────────────────────────

class DeploymentModel(Enum):
    CLOUD_SAAS = "cloud_saas"
    PRIVATE_CLOUD = "private_cloud"
    ON_PREMISES = "on_premises"
    HYBRID = "hybrid"


class SupportLevel(Enum):
    STANDARD = "standard"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


class PricingTier(Enum):
    STARTUP = "startup"
    GROWTH = "growth"
    ENTERPRISE = "enterprise"


# ── Base Pricing ───────────────────────────────────────────────────────────

BASE_PRICES = {
    "agent_base": 12000,
    "model_base": 6000,
    "policy_base": 240,
    "evidence_base": 0.50,
    "framework_base": 3600,
}

VOLUME_DISCOUNT_TIERS = [
    (1, 10, 0),
    (11, 50, 5),
    (51, 200, 10),
    (201, 500, 15),
    (501, 1000, 20),
    (1001, float("inf"), 25),
]

DEPLOYMENT_MULTIPLIERS = {
    DeploymentModel.CLOUD_SAAS: 1.0,
    DeploymentModel.PRIVATE_CLOUD: 1.35,
    DeploymentModel.ON_PREMISES: 1.60,
    DeploymentModel.HYBRID: 1.20,
}

SUPPORT_MULTIPLIERS = {
    SupportLevel.STANDARD: 1.0,
    SupportLevel.PREMIUM: 1.25,
    SupportLevel.ENTERPRISE: 1.50,
}

TIER_ADJUSTMENTS = {
    PricingTier.STARTUP: -0.10,
    PricingTier.GROWTH: 0.0,
    PricingTier.ENTERPRISE: 0.15,
}

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


# ── Data Models ────────────────────────────────────────────────────────────

@dataclass
class OrganizationProfile:
    name: str
    industry: str
    agents: int
    models: int = 1
    policies: int = 10
    evidence_volume_gb: float = 100
    frameworks: list = field(default_factory=list)
    deployment_model: str = "cloud_saas"
    support_level: str = "standard"
    pricing_tier: str = "growth"
    compliance_maturity: float = 5.0


@dataclass
class QuoteLineItem:
    description: str
    quantity: float
    unit_price: float
    unit: str
    category: str
    subtotal: float = 0.0
    discount_pct: float = 0.0
    discount_amount: float = 0.0
    total: float = 0.0


@dataclass
class PricingFactor:
    name: str
    description: str
    value: float
    unit: str
    category: str
    applied: bool = True


@dataclass
class PricingBreakdown:
    base_costs: dict = field(default_factory=dict)
    factors: list = field(default_factory=list)
    volume_discount_pct: float = 0.0
    volume_discount_amount: float = 0.0
    subtotal: float = 0.0
    total_multiplier: float = 1.0
    final_cost: float = 0.0


@dataclass
class Quote:
    quote_id: str
    created_at: str
    valid_until: str
    organization: OrganizationProfile = None
    line_items: list = field(default_factory=list)
    volume_discount_pct: float = 0.0
    volume_discount_amount: float = 0.0
    support_multiplier: float = 1.0
    deployment_multiplier: float = 1.0
    subtotal: float = 0.0
    total_before_tax: float = 0.0
    tax_rate: float = 0.0
    tax_amount: float = 0.0
    total: float = 0.0
    annual_cost: float = 0.0
    monthly_cost: float = 0.0
    assumptions: list = field(default_factory=list)
    notes: list = field(default_factory=list)


# ── Pricing Engine ────────────────────────────────────────────────────────

class PricingEngine:
    """Transparent pricing engine with all factors exposed."""

    def __init__(self, base_prices: dict = None):
        self.base_prices = base_prices or BASE_PRICES.copy()

    def get_volume_discount(self, agents: int) -> float:
        for min_agents, max_agents, discount in VOLUME_DISCOUNT_TIERS:
            if min_agents <= agents <= max_agents:
                return float(discount)
        return 0.0

    def get_deployment_multiplier(self, model: DeploymentModel) -> float:
        return DEPLOYMENT_MULTIPLIERS.get(model, 1.0)

    def get_support_multiplier(self, level: SupportLevel) -> float:
        return SUPPORT_MULTIPLIERS.get(level, 1.0)

    def get_tier_adjustment(self, tier: PricingTier) -> float:
        return TIER_ADJUSTMENTS.get(tier, 0.0)

    def get_industry_multiplier(self, industry: str) -> float:
        return INDUSTRY_RISK_MULTIPLIERS.get(industry.lower(), 1.0)

    def maturity_adjustment(self, maturity: float) -> float:
        if maturity <= 3:
            return 1.20
        elif maturity <= 5:
            return 1.10
        elif maturity <= 7:
            return 1.00
        elif maturity <= 9:
            return 0.95
        return 0.90

    def compute_base_costs(self, profile: OrganizationProfile) -> dict:
        return {
            "agents": profile.agents * self.base_prices["agent_base"],
            "models": profile.models * self.base_prices["model_base"],
            "policies": profile.policies * self.base_prices["policy_base"],
            "evidence": profile.evidence_volume_gb * self.base_prices["evidence_base"],
            "frameworks": len(profile.frameworks) * self.base_prices["framework_base"],
        }

    def compute_all_factors(self, profile: OrganizationProfile) -> list:
        factors = []
        vol_disc = self.get_volume_discount(profile.agents)
        factors.append(PricingFactor(
            name="Volume Discount",
            description=f"Based on {profile.agents} agents",
            value=vol_disc,
            unit="%",
            category="discount",
        ))
        dep_mult = self.get_deployment_multiplier(DeploymentModel(profile.deployment_model))
        factors.append(PricingFactor(
            name="Deployment Model",
            description=DeploymentModel(profile.deployment_model).value.replace("_", " ").title(),
            value=dep_mult,
            unit="x",
            category="multiplier",
        ))
        sup_mult = self.get_support_multiplier(SupportLevel(profile.support_level))
        factors.append(PricingFactor(
            name="Support Level",
            description=SupportLevel(profile.support_level).value.title(),
            value=sup_mult,
            unit="x",
            category="multiplier",
        ))
        tier_adj = self.get_tier_adjustment(PricingTier(profile.pricing_tier))
        factors.append(PricingFactor(
            name="Pricing Tier",
            description=PricingTier(profile.pricing_tier).value.title(),
            value=tier_adj,
            unit="%" if tier_adj >= 0 else "% discount",
            category="adjustment",
        ))
        ind_mult = self.get_industry_multiplier(profile.industry)
        factors.append(PricingFactor(
            name="Industry Risk",
            description=profile.industry.title(),
            value=ind_mult,
            unit="x",
            category="multiplier",
        ))
        mat_adj = self.maturity_adjustment(profile.compliance_maturity)
        factors.append(PricingFactor(
            name="Compliance Maturity",
            description=f"Maturity score: {profile.compliance_maturity}/10",
            value=mat_adj,
            unit="x",
            category="adjustment",
        ))
        return factors

    def compute_breakdown(self, profile: OrganizationProfile) -> PricingBreakdown:
        base_costs = self.compute_base_costs(profile)
        factors = self.compute_all_factors(profile)

        subtotal = sum(base_costs.values())
        vol_disc = self.get_volume_discount(profile.agents)
        vol_disc_amount = subtotal * (vol_disc / 100)

        dep_mult = self.get_deployment_multiplier(DeploymentModel(profile.deployment_model))
        sup_mult = self.get_support_multiplier(SupportLevel(profile.support_level))
        tier_adj = self.get_tier_adjustment(PricingTier(profile.pricing_tier))
        ind_mult = self.get_industry_multiplier(profile.industry)
        mat_adj = self.maturity_adjustment(profile.compliance_maturity)

        total_multiplier = dep_mult * sup_mult * ind_mult * mat_adj
        if tier_adj != 0:
            total_multiplier *= (1 + tier_adj)

        after_discount = subtotal - vol_disc_amount
        final_cost = after_discount * total_multiplier

        return PricingBreakdown(
            base_costs=base_costs,
            factors=factors,
            volume_discount_pct=vol_disc,
            volume_discount_amount=round(vol_disc_amount, 2),
            subtotal=round(subtotal, 2),
            total_multiplier=round(total_multiplier, 4),
            final_cost=round(final_cost, 2),
        )


# ── Quote Calculator ──────────────────────────────────────────────────────

class QuoteCalculator:
    """Generates quotes from organization profiles."""

    def __init__(self, engine: PricingEngine = None):
        self.engine = engine or PricingEngine()

    def calculate(self, profile: OrganizationProfile) -> Quote:
        breakdown = self.engine.compute_breakdown(profile)
        line_items = self._build_line_items(profile, breakdown)
        quote = self._assemble_quote(profile, line_items, breakdown)
        return quote

    def _build_line_items(self, profile: OrganizationProfile, breakdown: PricingBreakdown) -> list:
        items = []

        items.append(QuoteLineItem(
            description=f"GRC Agent License ({profile.agents} agents)",
            quantity=float(profile.agents),
            unit_price=self.engine.base_prices["agent_base"],
            unit="agent/year",
            category="license",
        ))

        items.append(QuoteLineItem(
            description=f"AI Model License ({profile.models} models)",
            quantity=float(profile.models),
            unit_price=self.engine.base_prices["model_base"],
            unit="model/year",
            category="license",
        ))

        items.append(QuoteLineItem(
            description=f"Policy Management ({profile.policies} policies)",
            quantity=float(profile.policies),
            unit_price=self.engine.base_prices["policy_base"],
            unit="policy/year",
            category="management",
        ))

        if profile.evidence_volume_gb > 0:
            items.append(QuoteLineItem(
                description=f"Evidence Storage ({profile.evidence_volume_gb:.0f} GB)",
                quantity=profile.evidence_volume_gb,
                unit_price=self.engine.base_prices["evidence_base"],
                unit="GB/year",
                category="storage",
            ))

        for fw in profile.frameworks:
            items.append(QuoteLineItem(
                description=f"Framework Compliance: {fw}",
                quantity=1.0,
                unit_price=self.engine.base_prices["framework_base"],
                unit="framework/year",
                category="compliance",
            ))

        support_cost = breakdown.subtotal * (
            self.engine.get_support_multiplier(SupportLevel(profile.support_level)) - 1.0
        )
        if support_cost > 0:
            items.append(QuoteLineItem(
                description=f"Support: {SupportLevel(profile.support_level).value.title()}",
                quantity=1.0,
                unit_price=round(support_cost, 2),
                unit="package",
                category="support",
            ))

        if profile.deployment_model != DeploymentModel.CLOUD_SAAS.value:
            dep_cost = breakdown.subtotal * (
                self.engine.get_deployment_multiplier(DeploymentModel(profile.deployment_model)) - 1.0
            )
            if dep_cost > 0:
                items.append(QuoteLineItem(
                    description=f"Deployment: {DeploymentModel(profile.deployment_model).value.replace('_', ' ').title()}",
                    quantity=1.0,
                    unit_price=round(dep_cost, 2),
                    unit="infrastructure",
                    category="infrastructure",
                ))

        # Calculate totals for each line item
        for item in items:
            item.subtotal = round(item.quantity * item.unit_price, 2)
            item.discount_amount = round(item.subtotal * (breakdown.volume_discount_pct / 100), 2)
            item.total = round(item.subtotal - item.discount_amount, 2)

        return items

    def _assemble_quote(self, profile: OrganizationProfile, line_items: list,
                        breakdown: PricingBreakdown) -> Quote:
        quote_id = f"GRC-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.utcnow()
        valid_until = now + timedelta(days=30)

        subtotal = sum(item.subtotal for item in line_items)
        total_before_tax = breakdown.final_cost
        tax_rate = 0.0
        tax_amount = round(total_before_tax * tax_rate, 2)
        total = round(total_before_tax + tax_amount, 2)

        assumptions = [
            "Annual billing cycle",
            f"{DeploymentModel(profile.deployment_model).value.replace('_', ' ').title()} deployment",
            f"{SupportLevel(profile.support_level).value.title()} support included",
            f"Up to {profile.evidence_volume_gb:.0f} GB evidence storage",
            f"{len(profile.frameworks)} compliance framework(s): {', '.join(profile.frameworks) if profile.frameworks else 'None'}",
        ]

        if profile.pricing_tier == PricingTier.STARTUP.value:
            assumptions.append("Startup pricing applied (10% discount)")
        elif profile.pricing_tier == PricingTier.ENTERPRISE.value:
            assumptions.append("Enterprise tier pricing applied (15% premium for advanced features)")

        return Quote(
            quote_id=quote_id,
            created_at=now.isoformat(),
            valid_until=valid_until.isoformat(),
            organization=profile,
            line_items=line_items,
            volume_discount_pct=breakdown.volume_discount_pct,
            volume_discount_amount=breakdown.volume_discount_amount,
            support_multiplier=self.engine.get_support_multiplier(SupportLevel(profile.support_level)),
            deployment_multiplier=self.engine.get_deployment_multiplier(DeploymentModel(profile.deployment_model)),
            subtotal=round(subtotal, 2),
            total_before_tax=round(total_before_tax, 2),
            tax_rate=tax_rate,
            tax_amount=tax_amount,
            total=round(total, 2),
            annual_cost=round(total, 2),
            monthly_cost=round(total / 12, 2),
            assumptions=assumptions,
            notes=[
                "All pricing in USD",
                "Volume discounts applied automatically",
                "Custom frameworks available upon request",
            ],
        )

    def quick_quote(self, name: str, industry: str, agents: int,
                    models: int = 1, policies: int = 10,
                    evidence_volume_gb: float = 100,
                    frameworks: list = None,
                    deployment_model: str = "cloud_saas",
                    support_level: str = "standard") -> Quote:
        profile = OrganizationProfile(
            name=name,
            industry=industry,
            agents=agents,
            models=models,
            policies=policies,
            evidence_volume_gb=evidence_volume_gb,
            frameworks=frameworks or [],
            deployment_model=deployment_model,
            support_level=support_level,
        )
        return self.calculate(profile)


# ── Quote Generator ───────────────────────────────────────────────────────

class QuoteGenerator:
    """Generates quotes in multiple output formats."""

    def __init__(self, quote: Quote):
        self.quote = quote

    def to_json(self, indent: int = 2) -> str:
        data = {
            "quote_id": self.quote.quote_id,
            "created_at": self.quote.created_at,
            "valid_until": self.quote.valid_until,
            "organization": {
                "name": self.quote.organization.name,
                "industry": self.quote.organization.industry,
                "agents": self.quote.organization.agents,
                "models": self.quote.organization.models,
                "policies": self.quote.organization.policies,
                "evidence_volume_gb": self.quote.organization.evidence_volume_gb,
                "frameworks": self.quote.organization.frameworks,
                "deployment_model": self.quote.organization.deployment_model,
                "support_level": self.quote.organization.support_level,
                "pricing_tier": self.quote.organization.pricing_tier,
            },
            "line_items": [
                {
                    "description": li.description,
                    "quantity": li.quantity,
                    "unit_price": li.unit_price,
                    "unit": li.unit,
                    "category": li.category,
                    "subtotal": li.subtotal,
                    "discount_pct": li.discount_pct,
                    "discount_amount": li.discount_amount,
                    "total": li.total,
                }
                for li in self.quote.line_items
            ],
            "summary": {
                "subtotal": self.quote.subtotal,
                "volume_discount_pct": self.quote.volume_discount_pct,
                "volume_discount_amount": self.quote.volume_discount_amount,
                "support_multiplier": self.quote.support_multiplier,
                "deployment_multiplier": self.quote.deployment_multiplier,
                "total_before_tax": self.quote.total_before_tax,
                "tax_rate": self.quote.tax_rate,
                "tax_amount": self.quote.tax_amount,
                "total": self.quote.total,
                "annual_cost": self.quote.annual_cost,
                "monthly_cost": self.quote.monthly_cost,
            },
            "assumptions": self.quote.assumptions,
            "notes": self.quote.notes,
        }
        return json.dumps(data, indent=indent)

    def to_markdown(self) -> str:
        q = self.quote
        org = q.organization

        lines = [
            f"# GRC_Claw Quote — {org.name}",
            "",
            f"**Quote ID:** {q.quote_id}  ",
            f"**Generated:** {q.created_at[:10]}  ",
            f"**Valid Until:** {q.valid_until[:10]}",
            "",
            "## Organization Profile",
            "",
            "| Attribute | Value |",
            "|-----------|-------|",
            f"| Industry | {org.industry.title()} |",
            f"| Deployment | {org.deployment_model.replace('_', ' ').title()} |",
            f"| Support Level | {org.support_level.title()} |",
            f"| Pricing Tier | {org.pricing_tier.title()} |",
            f"| Agents | {org.agents:,} |",
            f"| Models | {org.models:,} |",
            f"| Policies | {org.policies:,} |",
            f"| Evidence Volume | {org.evidence_volume_gb:,.0f} GB |",
            f"| Frameworks | {', '.join(org.frameworks) if org.frameworks else 'None'} |",
            "",
            "## Line Items",
            "",
            "| Description | Qty | Unit Price | Total |",
            "|-------------|-----|------------|-------|",
        ]

        for li in q.line_items:
            lines.append(f"| {li.description} | {li.quantity:,.0f} | ${li.unit_price:,.2f} | ${li.total:,.2f} |")

        lines.extend([
            "",
            "## Summary",
            "",
            "| Item | Amount |",
            "|------|--------|",
            f"| Subtotal | ${q.subtotal:,.2f} |",
            f"| Volume Discount ({q.volume_discount_pct:.0f}%) | -${q.volume_discount_amount:,.2f} |",
            f"| Support Multiplier | {q.support_multiplier:.2f}x |",
            f"| Deployment Multiplier | {q.deployment_multiplier:.2f}x |",
            f"| Tax ({q.tax_rate:.0f}%) | ${q.tax_amount:,.2f} |",
            f"| **Total Annual Cost** | **${q.total:,.2f}** |",
            f"| Monthly Equivalent | ${q.monthly_cost:,.2f} |",
            "",
            "## Assumptions",
            "",
        ])

        for a in q.assumptions:
            lines.append(f"- {a}")

        lines.extend([
            "",
            "---",
            "*GRC_Claw — Governance, Risk & Compliance AI Agents*",
        ])

        return "\n".join(lines)

    def to_text(self) -> str:
        q = self.quote
        org = q.organization

        lines = [
            "════════════════════════════════════════════════════════════",
            "                    GRC_Claw QUOTE",
            "════════════════════════════════════════════════════════════",
            "",
            f"  Quote ID:    {q.quote_id}",
            f"  Generated:   {q.created_at[:10]}",
            f"  Valid Until: {q.valid_until[:10]}",
            "",
            "────────────────────────────────────────────────────────────",
            "  ORGANIZATION",
            "────────────────────────────────────────────────────────────",
            f"  Name:        {org.name}",
            f"  Industry:    {org.industry.title()}",
            f"  Deployment:  {org.deployment_model.replace('_', ' ').title()}",
            f"  Support:     {org.support_level.title()}",
            f"  Tier:        {org.pricing_tier.title()}",
            "",
            "────────────────────────────────────────────────────────────",
            "  LINE ITEMS",
            "────────────────────────────────────────────────────────────",
        ]

        for li in q.line_items:
            lines.append(f"  {li.description}")
            lines.append(f"    {li.quantity:,.0f} x ${li.unit_price:,.2f} = ${li.total:,.2f}")

        lines.extend([
            "",
            "────────────────────────────────────────────────────────────",
            "  SUMMARY",
            "────────────────────────────────────────────────────────────",
            f"  Subtotal:            ${q.subtotal:>12,.2f}",
            f"  Volume Discount:     -${q.volume_discount_amount:>11,.2f} ({q.volume_discount_pct:.0f}%)",
            f"  Support Multiplier:  {q.support_multiplier:>12.2f}x",
            f"  Deployment Mult.:    {q.deployment_multiplier:>12.2f}x",
            f"  Tax ({q.tax_rate:.0f}%):          ${q.tax_amount:>12,.2f}",
            "                              ────────────",
            f"  TOTAL ANNUAL:        ${q.total:>12,.2f}",
            f"  Monthly:             ${q.monthly_cost:>12,.2f}",
            "",
            "────────────────────────────────────────────────────────────",
            "  ASSUMPTIONS",
            "────────────────────────────────────────────────────────────",
        ])

        for a in q.assumptions:
            lines.append(f"  • {a}")

        lines.extend([
            "",
            "════════════════════════════════════════════════════════════",
            "  GRC_Claw — Governance, Risk & Compliance AI Agents",
            "════════════════════════════════════════════════════════════",
        ])

        return "\n".join(lines)

    def save(self, filepath: str, format: str = "json") -> str:
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)

        if format == "json":
            content = self.to_json()
            path = path.with_suffix(".json")
        elif format == "markdown" or format == "md":
            content = self.to_markdown()
            path = path.with_suffix(".md")
        elif format == "text" or format == "txt":
            content = self.to_text()
            path = path.with_suffix(".txt")
        else:
            raise ValueError(f"Unsupported format: {format}")

        path.write_text(content, encoding="utf-8")
        return str(path)


# ── Demo Runner ────────────────────────────────────────────────────────────

def print_header(title: str):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")


def print_section(title: str):
    print(f"\n--- {title} ---")


def run_demo():
    print_header("GRC_Claw Quote Generation Demo")
    print("Demonstrating: Profile → Calculate → Generate")

    engine = PricingEngine()
    calculator = QuoteCalculator(engine)

    # ════════════════════════════════════════════════════════════════════
    # SCENARIO 1: Startup
    # ════════════════════════════════════════════════════════════════════
    print_header("SCENARIO 1: Startup — TechFlow Inc.")

    startup_profile = OrganizationProfile(
        name="TechFlow Inc.",
        industry="technology",
        agents=5,
        models=2,
        policies=8,
        evidence_volume_gb=50,
        frameworks=["SOC 2", "ISO 27001"],
        deployment_model="cloud_saas",
        support_level="standard",
        pricing_tier="startup",
        compliance_maturity=3.0,
    )

    startup_quote = calculator.calculate(startup_profile)
    generator = QuoteGenerator(startup_quote)

    print_section("Organization Profile")
    print(f"  Name: {startup_profile.name}")
    print(f"  Industry: {startup_profile.industry}")
    print(f"  Agents: {startup_profile.agents}, Models: {startup_profile.models}")
    print(f"  Policies: {startup_profile.policies}, Evidence: {startup_profile.evidence_volume_gb} GB")
    print(f"  Frameworks: {', '.join(startup_profile.frameworks)}")
    print(f"  Deployment: {startup_profile.deployment_model}")
    print(f"  Support: {startup_profile.support_level}")
    print(f"  Tier: {startup_profile.pricing_tier}")
    print(f"  Maturity: {startup_profile.compliance_maturity}/10")

    print_section("Pricing Breakdown")
    breakdown = engine.compute_breakdown(startup_profile)
    print(f"  Base costs:")
    for key, value in breakdown.base_costs.items():
        print(f"    {key}: ${value:,.2f}")
    print(f"  Subtotal: ${breakdown.subtotal:,.2f}")
    print(f"  Volume discount: {breakdown.volume_discount_pct}% (-${breakdown.volume_discount_amount:,.2f})")
    print(f"  Total multiplier: {breakdown.total_multiplier:.4f}x")
    print(f"  Final cost: ${breakdown.final_cost:,.2f}")

    print_section("Pricing Factors")
    for factor in breakdown.factors:
        print(f"  • {factor.name}: {factor.value}{factor.unit} ({factor.description})")

    print_section("Quote Summary")
    print(f"  Quote ID: {startup_quote.quote_id}")
    print(f"  Subtotal: ${startup_quote.subtotal:,.2f}")
    print(f"  Volume Discount: -${startup_quote.volume_discount_amount:,.2f} ({startup_quote.volume_discount_pct}%)")
    print(f"  Support Multiplier: {startup_quote.support_multiplier:.2f}x")
    print(f"  Deployment Multiplier: {startup_quote.deployment_multiplier:.2f}x")
    print(f"  Total Annual: ${startup_quote.total:,.2f}")
    print(f"  Monthly: ${startup_quote.monthly_cost:,.2f}")

    print_section("Line Items")
    for li in startup_quote.line_items:
        print(f"  • {li.description}: {li.quantity:,.0f} x ${li.unit_price:,.2f} = ${li.total:,.2f}")

    # ════════════════════════════════════════════════════════════════════
    # SCENARIO 2: Enterprise
    # ════════════════════════════════════════════════════════════════════
    print_header("SCENARIO 2: Enterprise — GlobalBank Corp")

    enterprise_profile = OrganizationProfile(
        name="GlobalBank Corp",
        industry="banking",
        agents=200,
        models=15,
        policies=50,
        evidence_volume_gb=2000,
        frameworks=["SOC 2", "ISO 27001", "PCI DSS", "GDPR"],
        deployment_model="private_cloud",
        support_level="enterprise",
        pricing_tier="enterprise",
        compliance_maturity=7.5,
    )

    enterprise_quote = calculator.calculate(enterprise_profile)

    print_section("Organization Profile")
    print(f"  Name: {enterprise_profile.name}")
    print(f"  Industry: {enterprise_profile.industry}")
    print(f"  Agents: {enterprise_profile.agents}, Models: {enterprise_profile.models}")
    print(f"  Policies: {enterprise_profile.policies}, Evidence: {enterprise_profile.evidence_volume_gb} GB")
    print(f"  Frameworks: {', '.join(enterprise_profile.frameworks)}")
    print(f"  Deployment: {enterprise_profile.deployment_model}")
    print(f"  Support: {enterprise_profile.support_level}")
    print(f"  Tier: {enterprise_profile.pricing_tier}")
    print(f"  Maturity: {enterprise_profile.compliance_maturity}/10")

    print_section("Quote Summary")
    print(f"  Quote ID: {enterprise_quote.quote_id}")
    print(f"  Subtotal: ${enterprise_quote.subtotal:,.2f}")
    print(f"  Volume Discount: -${enterprise_quote.volume_discount_amount:,.2f} ({enterprise_quote.volume_discount_pct}%)")
    print(f"  Support Multiplier: {enterprise_quote.support_multiplier:.2f}x")
    print(f"  Deployment Multiplier: {enterprise_quote.deployment_multiplier:.2f}x")
    print(f"  Total Annual: ${enterprise_quote.total:,.2f}")
    print(f"  Monthly: ${enterprise_quote.monthly_cost:,.2f}")

    print_section("Line Items")
    for li in enterprise_quote.line_items:
        print(f"  • {li.description}: {li.quantity:,.0f} x ${li.unit_price:,.2f} = ${li.total:,.2f}")

    # ════════════════════════════════════════════════════════════════════
    # SCENARIO 3: Healthcare
    # ════════════════════════════════════════════════════════════════════
    print_header("SCENARIO 3: Healthcare — MedCare Health")

    healthcare_profile = OrganizationProfile(
        name="MedCare Health",
        industry="healthcare",
        agents=50,
        models=5,
        policies=25,
        evidence_volume_gb=500,
        frameworks=["HIPAA", "SOC 2", "ISO 27001"],
        deployment_model="hybrid",
        support_level="premium",
        pricing_tier="growth",
        compliance_maturity=6.0,
    )

    healthcare_quote = calculator.calculate(healthcare_profile)

    print_section("Quote Summary")
    print(f"  Quote ID: {healthcare_quote.quote_id}")
    print(f"  Total Annual: ${healthcare_quote.total:,.2f}")
    print(f"  Monthly: ${healthcare_quote.monthly_cost:,.2f}")

    # ════════════════════════════════════════════════════════════════════
    # GENERATE OUTPUTS
    # ════════════════════════════════════════════════════════════════════
    print_header("GENERATING OUTPUTS — Multiple Formats")

    output_dir = Path(__file__).parent / "quote_output"
    output_dir.mkdir(exist_ok=True)

    print_section("Startup Quote Outputs")
    json_path = generator.save(str(output_dir / "startup_quote"), "json")
    md_path = generator.save(str(output_dir / "startup_quote"), "md")
    txt_path = generator.save(str(output_dir / "startup_quote"), "txt")
    print(f"  ✓ JSON: {json_path}")
    print(f"  ✓ Markdown: {md_path}")
    print(f"  ✓ Text: {txt_path}")

    print_section("Enterprise Quote Outputs")
    ent_generator = QuoteGenerator(enterprise_quote)
    ent_json = ent_generator.save(str(output_dir / "enterprise_quote"), "json")
    ent_md = ent_generator.save(str(output_dir / "enterprise_quote"), "md")
    ent_txt = ent_generator.save(str(output_dir / "enterprise_quote"), "txt")
    print(f"  ✓ JSON: {ent_json}")
    print(f"  ✓ Markdown: {ent_md}")
    print(f"  ✓ Text: {ent_txt}")

    print_section("Sample Text Output (Startup)")
    print(generator.to_text())

    # ════════════════════════════════════════════════════════════════════
    # COMPARISON
    # ════════════════════════════════════════════════════════════════════
    print_header("QUOTE COMPARISON")

    print(f"{'Metric':<25} {'Startup':>15} {'Enterprise':>15} {'Healthcare':>15}")
    print(f"{'-'*70}")
    print(f"{'Agents':<25} {startup_profile.agents:>15} {enterprise_profile.agents:>15} {healthcare_profile.agents:>15}")
    print(f"{'Models':<25} {startup_profile.models:>15} {enterprise_profile.models:>15} {healthcare_profile.models:>15}")
    print(f"{'Policies':<25} {startup_profile.policies:>15} {enterprise_profile.policies:>15} {healthcare_profile.policies:>15}")
    print(f"{'Evidence (GB)':<25} {startup_profile.evidence_volume_gb:>15.0f} {enterprise_profile.evidence_volume_gb:>15.0f} {healthcare_profile.evidence_volume_gb:>15.0f}")
    print(f"{'Frameworks':<25} {len(startup_profile.frameworks):>15} {len(enterprise_profile.frameworks):>15} {len(healthcare_profile.frameworks):>15}")
    print(f"{'Volume Discount':<25} {startup_quote.volume_discount_pct:>14.0f}% {enterprise_quote.volume_discount_pct:>14.0f}% {healthcare_quote.volume_discount_pct:>14.0f}%")
    print(f"{'Support Multiplier':<25} {startup_quote.support_multiplier:>14.2f}x {enterprise_quote.support_multiplier:>14.2f}x {healthcare_quote.support_multiplier:>14.2f}x")
    print(f"{'Deployment Multiplier':<25} {startup_quote.deployment_multiplier:>14.2f}x {enterprise_quote.deployment_multiplier:>14.2f}x {healthcare_quote.deployment_multiplier:>14.2f}x")
    print(f"{'Total Annual':<25} ${startup_quote.total:>14,.0f} ${enterprise_quote.total:>14,.0f} ${healthcare_quote.total:>14,.0f}")
    print(f"{'Monthly':<25} ${startup_quote.monthly_cost:>14,.0f} ${enterprise_quote.monthly_cost:>14,.0f} ${healthcare_quote.monthly_cost:>14,.0f}")

    # ════════════════════════════════════════════════════════════════════
    # SUMMARY
    # ════════════════════════════════════════════════════════════════════
    print_header("DEMO COMPLETE")
    print(f"""
Summary:
  • Generated 3 quotes for different organization profiles
  • Startup (TechFlow): ${startup_quote.total:,.0f}/year
  • Enterprise (GlobalBank): ${enterprise_quote.total:,.0f}/year
  • Healthcare (MedCare): ${healthcare_quote.total:,.0f}/year
  • Exported to JSON, Markdown, and Text formats
  • All pricing factors transparent and documented

Key Capabilities Demonstrated:
  ✓ Organization profile definition
  ✓ Transparent pricing engine with 6 factor types
  ✓ Volume discount tiers (0-25%)
  ✓ Deployment model multipliers (1.0x-1.6x)
  ✓ Support level multipliers (1.0x-1.5x)
  ✓ Pricing tier adjustments (-10% to +15%)
  ✓ Industry risk multipliers (0.85x-1.30x)
  ✓ Compliance maturity adjustments (0.90x-1.20x)
  ✓ Multi-format output (JSON, Markdown, Text)
  ✓ Line-item breakdown with discounts
  ✓ Quote comparison across profiles
""")


if __name__ == "__main__":
    run_demo()
