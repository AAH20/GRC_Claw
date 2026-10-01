"""
Unit Economics Dashboard — cost per agent, policy, evidence, framework.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
from .models import OrganizationProfile, Quote


@dataclass
class UnitEconomics:
    """Complete unit economics breakdown."""

    # Per-agent economics
    cost_per_agent: float = 0.0
    cost_per_agent_monthly: float = 0.0
    agents_per_framework: float = 0.0
    policies_per_agent: float = 0.0

    # Per-policy economics
    cost_per_policy: float = 0.0
    cost_per_policy_monthly: float = 0.0
    evidence_gb_per_policy: float = 0.0

    # Per-evidence economics
    cost_per_evidence_gb: float = 0.0
    cost_per_evidence_gb_monthly: float = 0.0
    evidence_gb_per_agent: float = 0.0

    # Per-framework economics
    cost_per_framework: float = 0.0
    cost_per_framework_monthly: float = 0.0
    agents_per_framework: float = 0.0

    # Model economics
    cost_per_model: float = 0.0
    cost_per_model_monthly: float = 0.0
    models_per_agent: float = 0.0

    # Marginal costs
    marginal_cost_per_additional_agent: float = 0.0
    marginal_cost_per_additional_policy: float = 0.0
    marginal_cost_per_additional_evidence_gb: float = 0.0
    marginal_cost_per_additional_framework: float = 0.0

    # Scale metrics
    total_agents: int = 0
    total_policies: int = 0
    total_evidence_gb: float = 0.0
    total_frameworks: int = 0
    total_models: int = 0
    total_annual_cost: float = 0.0


class UnitEconomicsDashboard:
    """
    Compute and display unit economics for GRC_Claw deployment.
    
    Shows cost per agent, cost per policy, cost per evidence GB,
    cost per compliance framework, and marginal costs for scaling.
    """

    def __init__(self, quote: Quote, profile: OrganizationProfile):
        self.quote = quote
        self.profile = profile
        self.economics = self._compute()

    def _compute(self) -> UnitEconomics:
        """Compute all unit economics metrics."""
        ue = UnitEconomics()
        q = self.quote
        p = self.profile

        ue.total_agents = p.agents
        ue.total_policies = p.policies
        ue.total_evidence_gb = p.evidence_volume_gb
        ue.total_frameworks = len(p.frameworks)
        ue.total_models = p.models
        ue.total_annual_cost = q.annual_cost

        # Per-agent
        if p.agents > 0:
            ue.cost_per_agent = q.annual_cost / p.agents
            ue.cost_per_agent_monthly = ue.cost_per_agent / 12
            ue.policies_per_agent = p.policies / p.agents
            ue.evidence_gb_per_agent = p.evidence_volume_gb / p.agents
            ue.models_per_agent = p.models / p.agents

        # Per-policy
        if p.policies > 0:
            ue.cost_per_policy = q.annual_cost / p.policies
            ue.cost_per_policy_monthly = ue.cost_per_policy / 12
            ue.evidence_gb_per_policy = p.evidence_volume_gb / p.policies

        # Per-evidence
        if p.evidence_volume_gb > 0:
            ue.cost_per_evidence_gb = q.annual_cost / p.evidence_volume_gb
            ue.cost_per_evidence_gb_monthly = ue.cost_per_evidence_gb / 12

        # Per-framework
        if p.frameworks:
            ue.cost_per_framework = q.annual_cost / len(p.frameworks)
            ue.cost_per_framework_monthly = ue.cost_per_framework / 12
            ue.agents_per_framework = p.agents / len(p.frameworks)

        # Per-model
        if p.models > 0:
            ue.cost_per_model = q.annual_cost / p.models
            ue.cost_per_model_monthly = ue.cost_per_model / 12

        # Marginal costs (using base prices from pricing engine)
        from .pricing_engine import PricingEngine
        engine = PricingEngine()
        ue.marginal_cost_per_additional_agent = engine.base_prices["agent_base"]
        ue.marginal_cost_per_additional_policy = engine.base_prices["policy_base"]
        ue.marginal_cost_per_additional_evidence_gb = engine.base_prices["evidence_base"]
        ue.marginal_cost_per_additional_framework = engine.base_prices["framework_base"]

        return ue

    def summary(self) -> str:
        """Generate a formatted summary of unit economics."""
        ue = self.economics
        lines = [
            "═══ GRC_Claw Unit Economics Dashboard ═══",
            "",
            f"Organization: {self.profile.name}",
            f"Industry: {self.profile.industry}",
            f"Deployment: {self.profile.deployment_model.value.replace('_', ' ').title()}",
            "",
            "── Scale ──",
            f"  Agents:          {ue.total_agents:>8,}",
            f"  Models:          {ue.total_models:>8,}",
            f"  Policies:        {ue.total_policies:>8,}",
            f"  Evidence:        {ue.total_evidence_gb:>8,.0f} GB",
            f"  Frameworks:      {ue.total_frameworks:>8,}",
            f"  Annual Cost:     ${ue.total_annual_cost:>12,.0f}",
            "",
            "── Per-Agent Economics ──",
            f"  Cost per Agent (annual):    ${ue.cost_per_agent:>10,.0f}",
            f"  Cost per Agent (monthly):   ${ue.cost_per_agent_monthly:>10,.0f}",
            f"  Policies per Agent:         {ue.policies_per_agent:>10.1f}",
            f"  Evidence GB per Agent:      {ue.evidence_gb_per_agent:>10.1f}",
            f"  Models per Agent:           {ue.models_per_agent:>10.2f}",
            "",
            "── Per-Policy Economics ──",
            f"  Cost per Policy (annual):   ${ue.cost_per_policy:>10,.0f}",
            f"  Cost per Policy (monthly):  ${ue.cost_per_policy_monthly:>10,.0f}",
            f"  Evidence GB per Policy:     {ue.evidence_gb_per_policy:>10.1f}",
            "",
            "── Per-Evidence Economics ──",
            f"  Cost per GB (annual):       ${ue.cost_per_evidence_gb:>10,.2f}",
            f"  Cost per GB (monthly):      ${ue.cost_per_evidence_gb_monthly:>10,.2f}",
            "",
            "── Per-Framework Economics ──",
            f"  Cost per Framework (annual):  ${ue.cost_per_framework:>10,.0f}",
            f"  Cost per Framework (monthly): ${ue.cost_per_framework_monthly:>10,.0f}",
            f"  Agents per Framework:         {ue.agents_per_framework:>10.1f}",
            "",
            "── Per-Model Economics ──",
            f"  Cost per Model (annual):    ${ue.cost_per_model:>10,.0f}",
            f"  Cost per Model (monthly):   ${ue.cost_per_model_monthly:>10,.0f}",
            "",
            "── Marginal Costs (Scaling) ──",
            f"  Additional Agent:      ${ue.marginal_cost_per_additional_agent:>10,.0f}/year",
            f"  Additional Policy:     ${ue.marginal_cost_per_additional_policy:>10,.0f}/year",
            f"  Additional Evidence:   ${ue.marginal_cost_per_additional_evidence_gb:>10,.2f}/GB/year",
            f"  Additional Framework:  ${ue.marginal_cost_per_additional_framework:>10,.0f}/year",
        ]
        return "\n".join(lines)

    def to_dict(self) -> dict:
        """Export unit economics as a dictionary."""
        ue = self.economics
        return {
            "scale": {
                "agents": ue.total_agents,
                "models": ue.total_models,
                "policies": ue.total_policies,
                "evidence_gb": ue.total_evidence_gb,
                "frameworks": ue.total_frameworks,
                "annual_cost": ue.total_annual_cost,
            },
            "per_agent": {
                "annual": ue.cost_per_agent,
                "monthly": ue.cost_per_agent_monthly,
                "policies_per_agent": ue.policies_per_agent,
                "evidence_gb_per_agent": ue.evidence_gb_per_agent,
                "models_per_agent": ue.models_per_agent,
            },
            "per_policy": {
                "annual": ue.cost_per_policy,
                "monthly": ue.cost_per_policy_monthly,
                "evidence_gb_per_policy": ue.evidence_gb_per_policy,
            },
            "per_evidence": {
                "annual_per_gb": ue.cost_per_evidence_gb,
                "monthly_per_gb": ue.cost_per_evidence_gb_monthly,
            },
            "per_framework": {
                "annual": ue.cost_per_framework,
                "monthly": ue.cost_per_framework_monthly,
                "agents_per_framework": ue.agents_per_framework,
            },
            "per_model": {
                "annual": ue.cost_per_model,
                "monthly": ue.cost_per_model_monthly,
            },
            "marginal_costs": {
                "per_agent": ue.marginal_cost_per_additional_agent,
                "per_policy": ue.marginal_cost_per_additional_policy,
                "per_evidence_gb": ue.marginal_cost_per_additional_evidence_gb,
                "per_framework": ue.marginal_cost_per_additional_framework,
            },
        }
