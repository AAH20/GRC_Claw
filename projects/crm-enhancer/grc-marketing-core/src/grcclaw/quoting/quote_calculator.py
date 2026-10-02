"""
Quote Calculator — generates custom quotes from organization profiles.
"""

from __future__ import annotations

from typing import Optional
from .models import (
    OrganizationProfile,
    Quote,
    QuoteLineItem,
    DeploymentModel,
    SupportLevel,
)
from .pricing_engine import PricingEngine


class QuoteCalculator:
    """
    Main quote calculator. Takes an OrganizationProfile and produces
    a fully itemized Quote with transparent pricing.
    """

    def __init__(self, engine: Optional[PricingEngine] = None):
        self.engine = engine or PricingEngine()

    def calculate(self, profile: OrganizationProfile) -> Quote:
        """Generate a complete quote for the given organization profile."""
        breakdown = self.engine.compute_breakdown(profile)

        line_items = self._build_line_items(profile, breakdown)
        quote = self._assemble_quote(profile, line_items, breakdown)
        return quote

    def _build_line_items(
        self, profile: OrganizationProfile, breakdown
    ) -> list[QuoteLineItem]:
        """Build itemized line items from pricing breakdown."""
        items = []

        # Agent licenses
        items.append(QuoteLineItem(
            description=f"GRC Agent License ({profile.agents} agents)",
            quantity=float(profile.agents),
            unit_price=self.engine.base_prices["agent_base"],
            unit="agent/year",
            category="license",
        ))

        # Model licenses
        items.append(QuoteLineItem(
            description=f"AI Model License ({profile.models} models)",
            quantity=float(profile.models),
            unit_price=self.engine.base_prices["model_base"],
            unit="model/year",
            category="license",
        ))

        # Policy management
        items.append(QuoteLineItem(
            description=f"Policy Management ({profile.policies} policies)",
            quantity=float(profile.policies),
            unit_price=self.engine.base_prices["policy_base"],
            unit="policy/year",
            category="management",
        ))

        # Evidence storage
        if profile.evidence_volume_gb > 0:
            items.append(QuoteLineItem(
                description=f"Evidence Storage ({profile.evidence_volume_gb:.0f} GB)",
                quantity=profile.evidence_volume_gb,
                unit_price=self.engine.base_prices["evidence_base"],
                unit="GB/year",
                category="storage",
            ))

        # Framework compliance
        for fw in profile.frameworks:
            items.append(QuoteLineItem(
                description=f"Framework Compliance: {fw}",
                quantity=1.0,
                unit_price=self.engine.base_prices["framework_base"],
                unit="framework/year",
                category="compliance",
            ))

        # Support package
        support_desc = f"Support: {profile.support_level.value.title()}"
        support_cost = breakdown.subtotal * (
            self.engine.get_support_multiplier(profile.support_level) - 1.0
        )
        if support_cost > 0:
            items.append(QuoteLineItem(
                description=support_desc,
                quantity=1.0,
                unit_price=support_cost,
                unit="package",
                category="support",
            ))

        # Deployment infrastructure
        if profile.deployment_model != DeploymentModel.CLOUD_SAAS:
            dep_desc = f"Deployment: {profile.deployment_model.value.replace('_', ' ').title()}"
            dep_cost = breakdown.subtotal * (
                self.engine.get_deployment_multiplier(profile.deployment_model) - 1.0
            )
            if dep_cost > 0:
                items.append(QuoteLineItem(
                    description=dep_desc,
                    quantity=1.0,
                    unit_price=dep_cost,
                    unit="infrastructure",
                    category="infrastructure",
                ))

        return items

    def _assemble_quote(
        self,
        profile: OrganizationProfile,
        line_items: list[QuoteLineItem],
        breakdown,
    ) -> Quote:
        """Assemble final quote from line items and breakdown."""
        quote = Quote(
            organization=profile,
            line_items=line_items,
            volume_discount_pct=breakdown.volume_discount_pct,
            support_multiplier=self.engine.get_support_multiplier(profile.support_level),
            deployment_multiplier=self.engine.get_deployment_multiplier(profile.deployment_model),
        )

        # Add assumptions
        quote.assumptions = [
            f"Annual billing cycle",
            f"{profile.deployment_model.value.replace('_', ' ').title()} deployment",
            f"{profile.support_level.value.title()} support included",
            f"Up to {profile.evidence_volume_gb:.0f} GB evidence storage",
            f"{len(profile.frameworks)} compliance framework(s): {', '.join(profile.frameworks) if profile.frameworks else 'None'}",
        ]

        if profile.pricing_tier.value == "startup":
            quote.assumptions.append("Startup pricing applied (10% discount)")
        elif profile.pricing_tier.value == "enterprise":
            quote.assumptions.append("Enterprise tier pricing applied (15% premium for advanced features)")

        quote.calculate_totals()
        return quote

    def quick_quote(
        self,
        name: str,
        industry: str,
        agents: int,
        models: int = 1,
        policies: int = 10,
        evidence_volume_gb: float = 100,
        frameworks: Optional[list[str]] = None,
        deployment_model: DeploymentModel = DeploymentModel.CLOUD_SAAS,
        support_level: SupportLevel = SupportLevel.STANDARD,
    ) -> Quote:
        """Convenience method for quick quotes without building a full profile."""
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
