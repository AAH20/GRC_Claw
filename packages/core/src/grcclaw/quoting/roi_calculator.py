"""
ROI Calculator — shows cost vs risk reduction for GRC_Claw investment.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
from .models import OrganizationProfile, Quote


@dataclass
class ROIBreakdown:
    """Complete ROI analysis."""

    # Costs
    annual_grc_cost: float = 0.0
    implementation_cost: float = 0.0
    training_cost: float = 0.0
    total_first_year_cost: float = 0.0
    total_three_year_cost: float = 0.0

    # Risk Reduction
    incident_reduction_pct: float = 0.0
    audit_finding_reduction_pct: float = 0.0
    breach_probability_reduction_pct: float = 0.0
    compliance_efficiency_gain_pct: float = 0.0

    # Savings
    avoided_incident_costs_annual: float = 0.0
    avoided_audit_costs_annual: float = 0.0
    avoided_breach_costs_annual: float = 0.0
    avoided_fine_costs_annual: float = 0.0
    efficiency_savings_annual: float = 0.0
    total_annual_savings: float = 0.0

    # ROI Metrics
    net_benefit_year1: float = 0.0
    net_benefit_three_year: float = 0.0
    roi_pct_year1: float = 0.0
    roi_pct_three_year: float = 0.0
    payback_period_months: float = 0.0

    # Per-unit metrics
    cost_per_agent: float = 0.0
    cost_per_policy: float = 0.0
    cost_per_evidence_gb: float = 0.0
    cost_per_framework: float = 0.0


class ROICalculator:
    """
    Calculate return on investment for GRC_Claw deployment.
    
    Compares the cost of GRC_Claw against:
    - Avoided incident costs
    - Reduced audit remediation costs
    - Lower breach probability savings
    - Regulatory fine avoidance
    - Compliance efficiency gains
    """

    # Effectiveness rates based on industry research
    DEFAULT_INCIDENT_REDUCTION = 0.40       # 40% fewer incidents
    DEFAULT_AUDIT_REDUCTION = 0.50          # 50% fewer audit findings
    DEFAULT_BREACH_PROB_REDUCTION = 0.30    # 30% lower breach probability
    DEFAULT_FINE_REDUCTION = 0.60           # 60% fewer fines
    DEFAULT_EFFICIENCY_GAIN = 0.35          # 35% efficiency improvement

    def __init__(
        self,
        incident_reduction: float = DEFAULT_INCIDENT_REDUCTION,
        audit_reduction: float = DEFAULT_AUDIT_REDUCTION,
        breach_reduction: float = DEFAULT_BREACH_PROB_REDUCTION,
        fine_reduction: float = DEFAULT_FINE_REDUCTION,
        efficiency_gain: float = DEFAULT_EFFICIENCY_GAIN,
    ):
        self.incident_reduction = incident_reduction
        self.audit_reduction = audit_reduction
        self.breach_reduction = breach_reduction
        self.fine_reduction = fine_reduction
        self.efficiency_gain = efficiency_gain

    def calculate(
        self,
        profile: OrganizationProfile,
        quote: Quote,
        implementation_cost: float = 0,
        training_cost: float = 0,
    ) -> ROIBreakdown:
        """Calculate full ROI breakdown."""
        roi = ROIBreakdown()

        # ── Costs ─────────────────────────────────────────────────────
        roi.annual_grc_cost = quote.annual_cost
        roi.implementation_cost = implementation_cost
        roi.training_cost = training_cost
        roi.total_first_year_cost = quote.annual_cost + implementation_cost + training_cost
        roi.total_three_year_cost = (quote.annual_cost * 3) + implementation_cost + training_cost

        # ── Risk Reduction Rates ───────────────────────────────────────
        roi.incident_reduction_pct = self.incident_reduction * 100
        roi.audit_finding_reduction_pct = self.audit_reduction * 100
        roi.breach_probability_reduction_pct = self.breach_reduction * 100
        roi.compliance_efficiency_gain_pct = self.efficiency_gain * 100

        # ── Annual Savings ─────────────────────────────────────────────
        # Avoided incident costs
        annual_incident_cost = profile.incident_history_count * profile.avg_incident_cost
        roi.avoided_incident_costs_annual = annual_incident_cost * self.incident_reduction

        # Avoided audit remediation costs
        annual_audit_cost = profile.audit_findings_annual * profile.avg_audit_remediation_cost
        roi.avoided_audit_costs_annual = annual_audit_cost * self.audit_reduction

        # Avoided breach costs (probability-weighted)
        annual_breach_expected = profile.data_breach_probability_annual * profile.avg_data_breach_cost
        roi.avoided_breach_costs_annual = annual_breach_expected * self.breach_reduction

        # Avoided regulatory fines
        roi.avoided_fine_costs_annual = profile.regulatory_fine_exposure_annual * self.fine_reduction

        # Efficiency savings (based on existing tooling cost)
        if profile.existing_tooling_cost_annual:
            roi.efficiency_savings_annual = profile.existing_tooling_cost_annual * self.efficiency_gain

        roi.total_annual_savings = (
            roi.avoided_incident_costs_annual
            + roi.avoided_audit_costs_annual
            + roi.avoided_breach_costs_annual
            + roi.avoided_fine_costs_annual
            + roi.efficiency_savings_annual
        )

        # ── ROI Metrics ────────────────────────────────────────────────
        roi.net_benefit_year1 = roi.total_annual_savings - roi.total_first_year_cost
        roi.net_benefit_three_year = (roi.total_annual_savings * 3) - roi.total_three_year_cost

        if roi.total_first_year_cost > 0:
            roi.roi_pct_year1 = (roi.net_benefit_year1 / roi.total_first_year_cost) * 100
        if roi.total_three_year_cost > 0:
            roi.roi_pct_three_year = (roi.net_benefit_three_year / roi.total_three_year_cost) * 100

        # Payback period
        if roi.total_annual_savings > 0:
            monthly_savings = roi.total_annual_savings / 12
            roi.payback_period_months = roi.total_first_year_cost / monthly_savings

        # ── Per-Unit Costs ─────────────────────────────────────────────
        if profile.agents > 0:
            roi.cost_per_agent = quote.annual_cost / profile.agents
        if profile.policies > 0:
            roi.cost_per_policy = quote.annual_cost / profile.policies
        if profile.evidence_volume_gb > 0:
            roi.cost_per_evidence_gb = quote.annual_cost / profile.evidence_volume_gb
        if profile.frameworks:
            roi.cost_per_framework = quote.annual_cost / len(profile.frameworks)

        return roi

    def generate_executive_summary(self, roi: ROIBreakdown) -> str:
        """Generate a human-readable executive summary."""
        lines = [
            "═══ GRC_Claw ROI Executive Summary ═══",
            "",
            f"First Year Investment:    ${roi.total_first_year_cost:>12,.0f}",
            f"Annual Risk Reduction:    ${roi.total_annual_savings:>12,.0f}",
            f"Net Benefit (Year 1):     ${roi.net_benefit_year1:>12,.0f}",
            f"ROI (Year 1):             {roi.roi_pct_year1:>12.1f}%",
            f"ROI (3-Year):             {roi.roi_pct_three_year:>12.1f}%",
            f"Payback Period:          {roi.payback_period_months:>12.1f} months",
            "",
            "── Risk Reduction Breakdown ──",
            f"  Incident Cost Avoidance:    ${roi.avoided_incident_costs_annual:>12,.0f}/year",
            f"  Audit Cost Avoidance:       ${roi.avoided_audit_costs_annual:>12,.0f}/year",
            f"  Breach Cost Avoidance:      ${roi.avoided_breach_costs_annual:>12,.0f}/year",
            f"  Fine Avoidance:             ${roi.avoided_fine_costs_annual:>12,.0f}/year",
            f"  Efficiency Savings:         ${roi.efficiency_savings_annual:>12,.0f}/year",
            "",
            "── Per-Unit Economics ──",
            f"  Cost per Agent:        ${roi.cost_per_agent:>10,.0f}",
            f"  Cost per Policy:       ${roi.cost_per_policy:>10,.0f}",
            f"  Cost per Evidence GB:  ${roi.cost_per_evidence_gb:>10,.2f}",
            f"  Cost per Framework:    ${roi.cost_per_framework:>10,.0f}",
        ]
        return "\n".join(lines)
