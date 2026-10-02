"""
Cost Model Calculator for GRC_Claw.

Computes Total Cost of Ownership (TCO), unit economics, and cost breakdowns
across all GRC_Claw deployment dimensions.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from .models import (
    CostBreakdown,
    CostCategory,
    CostLineItem,
    ResourceType,
    ResourceUsage,
    TCOSummary,
)


@dataclass
class InfrastructureCost:
    """Infrastructure cost components."""

    compute_monthly: float = 0.0
    storage_monthly: float = 0.0
    network_monthly: float = 0.0
    gpu_monthly: float = 0.0
    backup_monthly: float = 0.0
    monitoring_monthly: float = 0.0

    @property
    def total_monthly(self) -> float:
        return (
            self.compute_monthly
            + self.storage_monthly
            + self.network_monthly
            + self.gpu_monthly
            + self.backup_monthly
            + self.monitoring_monthly
        )


@dataclass
class LicensingCost:
    """Licensing cost components."""

    platform_license_monthly: float = 0.0
    model_api_costs_monthly: float = 0.0
    third_party_integrations_monthly: float = 0.0
    security_tools_monthly: float = 0.0
    compliance_tools_monthly: float = 0.0

    @property
    def total_monthly(self) -> float:
        return (
            self.platform_license_monthly
            + self.model_api_costs_monthly
            + self.third_party_integrations_monthly
            + self.security_tools_monthly
            + self.compliance_tools_monthly
        )


@dataclass
class PersonnelCost:
    """Personnel cost components."""

    engineering_monthly: float = 0.0
    operations_monthly: float = 0.0
    compliance_officers_monthly: float = 0.0
    security_analysts_monthly: float = 0.0
    management_overhead_monthly: float = 0.0

    @property
    def total_monthly(self) -> float:
        return (
            self.engineering_monthly
            + self.operations_monthly
            + self.compliance_officers_monthly
            + self.security_analysts_monthly
            + self.management_overhead_monthly
        )


@dataclass
class OperationalCost:
    """Operational cost components."""

    incident_response_monthly: float = 0.0
    audit_remediation_monthly: float = 0.0
    training_monthly: float = 0.0
    support_monthly: float = 0.0
    contingency_monthly: float = 0.0

    @property
    def total_monthly(self) -> float:
        return (
            self.incident_response_monthly
            + self.audit_remediation_monthly
            + self.training_monthly
            + self.support_monthly
            + self.contingency_monthly
        )


class CostModelCalculator:
    """
    Comprehensive cost model calculator for GRC_Claw deployments.

    Calculates TCO, unit economics, cost breakdowns, and per-unit costs
    across all dimensions of the platform.
    """

    def __init__(self):
        self.infrastructure = InfrastructureCost()
        self.licensing = LicensingCost()
        self.personnel = PersonnelCost()
        self.operational = OperationalCost()
        self.line_items: list[CostLineItem] = []
        self.resource_usage: list[ResourceUsage] = []
        self.currency: str = "USD"

    def set_infrastructure_costs(
        self,
        compute_monthly: float = 0,
        storage_monthly: float = 0,
        network_monthly: float = 0,
        gpu_monthly: float = 0,
        backup_monthly: float = 0,
        monitoring_monthly: float = 0,
    ) -> None:
        """Set infrastructure cost components."""
        self.infrastructure = InfrastructureCost(
            compute_monthly=compute_monthly,
            storage_monthly=storage_monthly,
            network_monthly=network_monthly,
            gpu_monthly=gpu_monthly,
            backup_monthly=backup_monthly,
            monitoring_monthly=monitoring_monthly,
        )

    def set_licensing_costs(
        self,
        platform_license_monthly: float = 0,
        model_api_costs_monthly: float = 0,
        third_party_integrations_monthly: float = 0,
        security_tools_monthly: float = 0,
        compliance_tools_monthly: float = 0,
    ) -> None:
        """Set licensing cost components."""
        self.licensing = LicensingCost(
            platform_license_monthly=platform_license_monthly,
            model_api_costs_monthly=model_api_costs_monthly,
            third_party_integrations_monthly=third_party_integrations_monthly,
            security_tools_monthly=security_tools_monthly,
            compliance_tools_monthly=compliance_tools_monthly,
        )

    def set_personnel_costs(
        self,
        engineering_monthly: float = 0,
        operations_monthly: float = 0,
        compliance_officers_monthly: float = 0,
        security_analysts_monthly: float = 0,
        management_overhead_monthly: float = 0,
    ) -> None:
        """Set personnel cost components."""
        self.personnel = PersonnelCost(
            engineering_monthly=engineering_monthly,
            operations_monthly=operations_monthly,
            compliance_officers_monthly=compliance_officers_monthly,
            security_analysts_monthly=security_analysts_monthly,
            management_overhead_monthly=management_overhead_monthly,
        )

    def set_operational_costs(
        self,
        incident_response_monthly: float = 0,
        audit_remediation_monthly: float = 0,
        training_monthly: float = 0,
        support_monthly: float = 0,
        contingency_monthly: float = 0,
    ) -> None:
        """Set operational cost components."""
        self.operational = OperationalCost(
            incident_response_monthly=incident_response_monthly,
            audit_remediation_monthly=audit_remediation_monthly,
            training_monthly=training_monthly,
            support_monthly=support_monthly,
            contingency_monthly=contingency_monthly,
        )

    def add_line_item(self, item: CostLineItem) -> None:
        """Add a cost line item."""
        self.line_items.append(item)

    def add_resource_usage(self, usage: ResourceUsage) -> None:
        """Add a resource usage measurement."""
        self.resource_usage.append(usage)

    @property
    def total_monthly_cost(self) -> float:
        """Total monthly cost across all categories."""
        return (
            self.infrastructure.total_monthly
            + self.licensing.total_monthly
            + self.personnel.total_monthly
            + self.operational.total_monthly
        )

    @property
    def total_annual_cost(self) -> float:
        """Total annual cost."""
        return self.total_monthly_cost * 12

    def calculate_tco(
        self,
        period: str = "",
        agents: int = 1,
        policies: int = 1,
        evidence_volume_gb: float = 0,
        api_calls_monthly: int = 0,
        period_months: int = 12,
    ) -> TCOSummary:
        """
        Calculate Total Cost of Ownership.

        Args:
            period: Reporting period label (e.g. "2024-Q1").
            agents: Number of GRC agents deployed.
            policies: Number of compliance policies managed.
            evidence_volume_gb: Evidence data volume in GB.
            api_calls_monthly: Monthly API call volume.
            period_months: Number of months in the period.

        Returns:
            TCOSummary with all TCO components and per-unit costs.
        """
        infra_total = self.infrastructure.total_monthly * period_months
        lic_total = self.licensing.total_monthly * period_months
        pers_total = self.personnel.total_monthly * period_months
        ops_total = self.operational.total_monthly * period_months

        total = infra_total + lic_total + pers_total + ops_total

        cost_per_agent = total / agents if agents > 0 else 0.0
        cost_per_policy = total / policies if policies > 0 else 0.0
        cost_per_gb = total / evidence_volume_gb if evidence_volume_gb > 0 else 0.0
        cost_per_api = total / (api_calls_monthly * period_months) if api_calls_monthly > 0 else 0.0

        return TCOSummary(
            period=period,
            infrastructure_cost=infra_total,
            licensing_cost=lic_total,
            personnel_cost=pers_total,
            operational_cost=ops_total,
            compliance_cost=self.operational.audit_remediation_monthly * period_months,
            training_cost=self.operational.training_monthly * period_months,
            support_cost=self.operational.support_monthly * period_months,
            total_tco=total,
            cost_per_agent=cost_per_agent,
            cost_per_policy=cost_per_policy,
            cost_per_gb_stored=cost_per_gb,
            cost_per_api_call=cost_per_api,
            period_months=period_months,
            currency=self.currency,
        )

    def get_cost_breakdown(self, period: str = "") -> CostBreakdown:
        """
        Get aggregated cost breakdown by category, resource, and department.

        Args:
            period: Reporting period label.

        Returns:
            CostBreakdown with all aggregations.
        """
        by_category: dict[str, float] = defaultdict(float)
        by_resource: dict[str, float] = defaultdict(float)
        by_department: dict[str, float] = defaultdict(float)

        for item in self.line_items:
            cat_key = item.category.value if isinstance(item.category, CostCategory) else str(item.category)
            by_category[cat_key] += item.amount

            if item.resource_type:
                res_key = item.resource_type.value if isinstance(item.resource_type, ResourceType) else str(item.resource_type)
                by_resource[res_key] += item.amount

            dept = item.allocated_to or "unallocated"
            by_department[dept] += item.amount

        # Add resource usage costs
        for usage in self.resource_usage:
            res_key = usage.resource_type.value if isinstance(usage.resource_type, ResourceType) else str(usage.resource_type)
            by_resource[res_key] += usage.total_cost

        total = sum(by_category.values()) + sum(
            u.total_cost for u in self.resource_usage
        )

        return CostBreakdown(
            period=period,
            total_cost=total,
            by_category=dict(by_category),
            by_resource=dict(by_resource),
            by_department=dict(by_department),
            line_items=list(self.line_items),
            currency=self.currency,
        )

    def get_unit_economics(
        self,
        agents: int = 1,
        policies: int = 1,
        evidence_volume_gb: float = 0,
        api_calls_monthly: int = 0,
    ) -> dict[str, float]:
        """
        Calculate unit economics metrics.

        Returns:
            Dictionary of per-unit cost metrics.
        """
        monthly = self.total_monthly_cost
        annual = self.total_annual_cost

        return {
            "monthly_total": monthly,
            "annual_total": annual,
            "cost_per_agent_monthly": monthly / agents if agents > 0 else 0.0,
            "cost_per_agent_annual": annual / agents if agents > 0 else 0.0,
            "cost_per_policy_monthly": monthly / policies if policies > 0 else 0.0,
            "cost_per_policy_annual": annual / policies if policies > 0 else 0.0,
            "cost_per_gb_monthly": monthly / evidence_volume_gb if evidence_volume_gb > 0 else 0.0,
            "cost_per_gb_annual": annual / evidence_volume_gb if evidence_volume_gb > 0 else 0.0,
            "cost_per_1k_api_calls": monthly / (api_calls_monthly / 1000) if api_calls_monthly > 0 else 0.0,
            "infrastructure_pct": (self.infrastructure.total_monthly / monthly * 100) if monthly > 0 else 0.0,
            "licensing_pct": (self.licensing.total_monthly / monthly * 100) if monthly > 0 else 0.0,
            "personnel_pct": (self.personnel.total_monthly / monthly * 100) if monthly > 0 else 0.0,
            "operational_pct": (self.operational.total_monthly / monthly * 100) if monthly > 0 else 0.0,
        }

    def compare_scenarios(
        self,
        baseline: CostModelCalculator,
        scenario_name: str = "optimized",
    ) -> dict:
        """
        Compare this cost model against a baseline scenario.

        Args:
            baseline: The baseline CostModelCalculator to compare against.
            scenario_name: Name for this scenario.

        Returns:
            Dictionary with comparison metrics.
        """
        base_monthly = baseline.total_monthly_cost
        scen_monthly = self.total_monthly_cost
        delta = scen_monthly - base_monthly
        delta_pct = (delta / base_monthly * 100) if base_monthly > 0 else 0.0

        base_annual = baseline.total_annual_cost
        scen_annual = self.total_annual_cost
        annual_delta = scen_annual - base_annual

        return {
            "scenario_name": scenario_name,
            "baseline_monthly": base_monthly,
            "scenario_monthly": scen_monthly,
            "monthly_delta": delta,
            "monthly_delta_pct": delta_pct,
            "baseline_annual": base_annual,
            "scenario_annual": scen_annual,
            "annual_delta": annual_delta,
            "annual_savings": -annual_delta if annual_delta < 0 else 0.0,
            "is_cheaper": scen_monthly < base_monthly,
        }

    def project_growth(
        self,
        months: int = 12,
        monthly_growth_rate: float = 0.02,
        seasonality: list[float] | None = None,
    ) -> list[dict]:
        """
        Project costs forward with optional growth and seasonality.

        Args:
            months: Number of months to project.
            monthly_growth_rate: Monthly cost growth rate (e.g. 0.02 = 2%).
            seasonality: Optional list of 12 monthly seasonality multipliers.

        Returns:
            List of monthly projection dictionaries.
        """
        projections = []
        current_monthly = self.total_monthly_cost

        for m in range(1, months + 1):
            growth_factor = (1 + monthly_growth_rate) ** m
            seasonal_factor = 1.0
            if seasonality and len(seasonality) == 12:
                seasonal_factor = seasonality[(m - 1) % 12]

            projected = current_monthly * growth_factor * seasonal_factor

            projections.append({
                "month": m,
                "projected_monthly": round(projected, 2),
                "projected_cumulative": round(current_monthly * growth_factor * seasonal_factor * m, 2),
                "growth_factor": round(growth_factor, 4),
                "seasonality_factor": round(seasonal_factor, 4),
            })

        return projections
