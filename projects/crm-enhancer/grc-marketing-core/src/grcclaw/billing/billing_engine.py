"""
Billing Calculation Engine for GRC_Claw.

Calculates charges based on metered usage, applies pricing tiers,
discounts, and generates billing line items and cycles.
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Optional
import calendar

from .models import (
    BillingCycle,
    BillingLineItem,
    MeteringDimension,
    PricingPlan,
    PricingTierConfig,
    UsageAggregation,
)
from .usage_metering import UsageMeteringEngine


class BillingCalculationEngine:
    """
    Calculates billing charges from usage data.

    Supports multiple pricing models: flat-rate, tiered, volume-based,
    and custom enterprise pricing. Handles proration, discounts, and
    multi-currency scenarios.
    """

    # Default pricing plans
    DEFAULT_PLANS: dict[PricingPlan, dict] = {
        PricingPlan.FREE: {
            "base_monthly": 0,
            "included": {
                MeteringDimension.API_CALLS: 1000,
                MeteringDimension.AGENT_SESSIONS: 100,
                MeteringDimension.POLICY_EVALUATIONS: 500,
                MeteringDimension.EVIDENCE_PROCESSED_GB: 5,
                MeteringDimension.STORAGE_GB: 10,
            },
            "overage_rates": {
                MeteringDimension.API_CALLS: 0.001,
                MeteringDimension.AGENT_SESSIONS: 0.10,
                MeteringDimension.POLICY_EVALUATIONS: 0.005,
                MeteringDimension.EVIDENCE_PROCESSED_GB: 0.50,
                MeteringDimension.STORAGE_GB: 0.10,
            },
        },
        PricingPlan.STARTER: {
            "base_monthly": 499,
            "included": {
                MeteringDimension.API_CALLS: 50000,
                MeteringDimension.AGENT_SESSIONS: 2000,
                MeteringDimension.POLICY_EVALUATIONS: 25000,
                MeteringDimension.EVIDENCE_PROCESSED_GB: 100,
                MeteringDimension.STORAGE_GB: 500,
            },
            "overage_rates": {
                MeteringDimension.API_CALLS: 0.0008,
                MeteringDimension.AGENT_SESSIONS: 0.08,
                MeteringDimension.POLICY_EVALUATIONS: 0.004,
                MeteringDimension.EVIDENCE_PROCESSED_GB: 0.40,
                MeteringDimension.STORAGE_GB: 0.08,
            },
        },
        PricingPlan.PROFESSIONAL: {
            "base_monthly": 1999,
            "included": {
                MeteringDimension.API_CALLS: 250000,
                MeteringDimension.AGENT_SESSIONS: 10000,
                MeteringDimension.POLICY_EVALUATIONS: 100000,
                MeteringDimension.EVIDENCE_PROCESSED_GB: 500,
                MeteringDimension.STORAGE_GB: 2000,
            },
            "overage_rates": {
                MeteringDimension.API_CALLS: 0.0006,
                MeteringDimension.AGENT_SESSIONS: 0.06,
                MeteringDimension.POLICY_EVALUATIONS: 0.003,
                MeteringDimension.EVIDENCE_PROCESSED_GB: 0.30,
                MeteringDimension.STORAGE_GB: 0.06,
            },
        },
        PricingPlan.ENTERPRISE: {
            "base_monthly": 9999,
            "included": {
                MeteringDimension.API_CALLS: 1000000,
                MeteringDimension.AGENT_SESSIONS: 50000,
                MeteringDimension.POLICY_EVALUATIONS: 500000,
                MeteringDimension.EVIDENCE_PROCESSED_GB: 2000,
                MeteringDimension.STORAGE_GB: 10000,
            },
            "overage_rates": {
                MeteringDimension.API_CALLS: 0.0004,
                MeteringDimension.AGENT_SESSIONS: 0.04,
                MeteringDimension.POLICY_EVALUATIONS: 0.002,
                MeteringDimension.EVIDENCE_PROCESSED_GB: 0.20,
                MeteringDimension.STORAGE_GB: 0.04,
            },
        },
    }

    def __init__(self, metering_engine: Optional[UsageMeteringEngine] = None):
        self.metering = metering_engine or UsageMeteringEngine()
        self._custom_plans: dict[str, dict] = {}
        self._discount_rules: list[dict] = []

    def register_custom_plan(self, plan_name: str, config: dict) -> None:
        """Register a custom pricing plan."""
        self._custom_plans[plan_name] = config

    def add_discount_rule(self, rule: dict) -> None:
        """
        Add a discount rule.

        Rule format:
        {
            "name": "Annual Commitment",
            "type": "percentage" | "fixed",
            "value": 15,  # 15% or $15
            "min_commitment": 10000,  # Minimum annual commitment
            "dimensions": [MeteringDimension.API_CALLS],  # Optional: specific dimensions
            "plans": [PricingPlan.PROFESSIONAL, PricingPlan.ENTERPRISE],  # Optional: specific plans
        }
        """
        self._discount_rules.append(rule)

    def calculate_cycle(
        self,
        tenant_id: str,
        plan: PricingPlan,
        period_start: str,
        period_end: str,
        tax_rate: float = 0.0,
        currency: str = "USD",
        apply_discounts: bool = True,
    ) -> BillingCycle:
        """
        Calculate a complete billing cycle for a tenant.

        Args:
            tenant_id: The tenant identifier.
            plan: The pricing plan.
            period_start: ISO format period start.
            period_end: ISO format period end.
            tax_rate: Tax rate as percentage (e.g., 8.5 for 8.5%).
            currency: Currency code.
            apply_discounts: Whether to apply discount rules.

        Returns:
            A fully calculated BillingCycle.
        """
        cycle = BillingCycle(
            tenant_id=tenant_id,
            plan=plan,
            period_start=period_start,
            period_end=period_end,
            tax_rate=tax_rate,
            currency=currency,
        )

        # Get plan configuration
        plan_config = self._get_plan_config(plan)

        # Add base charge line item
        if plan_config["base_monthly"] > 0:
            base_item = BillingLineItem(
                description=f"{plan.value.title()} Plan - Base Subscription",
                quantity=1,
                unit="month",
                unit_price=plan_config["base_monthly"],
            )
            cycle.line_items.append(base_item)

        # Calculate usage charges for each dimension
        aggregations = self.metering.aggregate_by_dimension(
            tenant_id, period_start, period_end
        )

        for dim, agg in aggregations.items():
            included = plan_config.get("included", {}).get(dim, 0)
            overage_rate = plan_config.get("overage_rates", {}).get(dim, 0)

            if agg.total_quantity > included and overage_rate > 0:
                overage = agg.total_quantity - included
                overage_item = BillingLineItem(
                    description=f"{dim.value.replace('_', ' ').title()} - Overage",
                    dimension=dim,
                    quantity=overage,
                    unit=agg.unit,
                    unit_price=overage_rate,
                )
                cycle.line_items.append(overage_item)

        # Calculate totals
        cycle.calculate_totals()

        # Apply discounts
        if apply_discounts:
            self._apply_discounts(cycle, plan)

        # Recalculate after discounts
        cycle.calculate_totals()

        return cycle

    def calculate_prorated_charge(
        self,
        monthly_amount: float,
        days_in_period: int,
        days_used: int,
    ) -> float:
        """
        Calculate a prorated charge for partial periods.

        Args:
            monthly_amount: The full monthly amount.
            days_in_period: Total days in the billing period.
            days_used: Days actually used.

        Returns:
            The prorated amount.
        """
        if days_in_period <= 0:
            return monthly_amount
        return round(monthly_amount * (days_used / days_in_period), 2)

    def calculate_usage_charge(
        self,
        dimension: MeteringDimension,
        quantity: float,
        plan: PricingPlan = PricingPlan.STARTER,
    ) -> float:
        """
        Calculate charge for a specific usage quantity.

        Args:
            dimension: The metering dimension.
            quantity: The usage quantity.
            plan: The pricing plan.

        Returns:
            The calculated charge.
        """
        plan_config = self._get_plan_config(plan)
        included = plan_config.get("included", {}).get(dimension, 0)
        overage_rate = plan_config.get("overage_rates", {}).get(dimension, 0)

        if quantity <= included:
            return 0.0

        overage = quantity - included
        return round(overage * overage_rate, 2)

    def compare_plans(
        self,
        tenant_id: str,
        period_start: str,
        period_end: str,
    ) -> dict:
        """
        Compare costs across all available plans for a tenant's usage.

        Returns:
            Dictionary mapping plan to total cost.
        """
        results = {}
        for plan in [PricingPlan.FREE, PricingPlan.STARTER, PricingPlan.PROFESSIONAL, PricingPlan.ENTERPRISE]:
            cycle = self.calculate_cycle(
                tenant_id=tenant_id,
                plan=plan,
                period_start=period_start,
                period_end=period_end,
                apply_discounts=False,
            )
            results[plan.value] = {
                "total": cycle.total,
                "line_items": len(cycle.line_items),
                "subtotal": cycle.subtotal,
            }
        return results

    def get_plan_details(self, plan: PricingPlan) -> dict:
        """Get the details of a pricing plan."""
        return self._get_plan_config(plan)

    def _get_plan_config(self, plan: PricingPlan) -> dict:
        """Get configuration for a plan."""
        if plan == PricingPlan.CUSTOM:
            return self._custom_plans.get("default", self.DEFAULT_PLANS[PricingPlan.ENTERPRISE])
        return self.DEFAULT_PLANS.get(plan, self.DEFAULT_PLANS[PricingPlan.STARTER])

    def _apply_discounts(self, cycle: BillingCycle, plan: PricingPlan) -> None:
        """Apply discount rules to a billing cycle."""
        for rule in self._discount_rules:
            # Check if rule applies to this plan
            rule_plans = rule.get("plans")
            if rule_plans and plan not in rule_plans:
                continue

            # Check minimum commitment
            min_commitment = rule.get("min_commitment", 0)
            if cycle.subtotal < min_commitment:
                continue

            # Calculate discount
            if rule["type"] == "percentage":
                discount = cycle.subtotal * (rule["value"] / 100)
            elif rule["type"] == "fixed":
                discount = min(rule["value"], cycle.subtotal)
            else:
                continue

            cycle.discount_amount += discount
            cycle.discount_reason = rule["name"]
            cycle.notes.append(
                f"Applied discount: {rule['name']} - ${discount:.2f}"
            )
