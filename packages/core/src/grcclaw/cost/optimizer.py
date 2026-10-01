"""
Resource Optimization Engine for GRC_Claw.

Analyzes resource utilization and generates optimization recommendations
including rightsizing, scheduling, reserved capacity, and storage tiering.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime, timezone
from collections import defaultdict
import statistics

from .models import (
    CostCategory,
    CostLineItem,
    ResourceType,
    ResourceUsage,
    OptimizationAction,
    OptimizationRecommendation,
)


@dataclass
class UtilizationThresholds:
    """Thresholds for determining optimization actions."""

    underutilized_pct: float = 30.0
    overutilized_pct: float = 85.0
    idle_threshold_pct: float = 5.0
    target_utilization_pct: float = 70.0
    min_savings_threshold: float = 100.0  # Minimum monthly savings to recommend


@dataclass
class ResourceMetrics:
    """Aggregated metrics for a resource type."""

    resource_type: ResourceType
    total_quantity: float = 0.0
    total_cost: float = 0.0
    avg_utilization: float = 0.0
    peak_utilization: float = 0.0
    min_utilization: float = 0.0
    utilization_std_dev: float = 0.0
    sample_count: int = 0
    unit: str = ""
    cost_per_unit: float = 0.0
    hourly_usage: list[float] = field(default_factory=list)
    daily_costs: list[float] = field(default_factory=list)


@dataclass
class OptimizationSummary:
    """Summary of all optimization recommendations."""

    total_recommendations: int = 0
    total_potential_savings: float = 0.0
    total_potential_savings_pct: float = 0.0
    current_monthly_cost: float = 0.0
    optimized_monthly_cost: float = 0.0
    by_action: dict[str, int] = field(default_factory=dict)
    by_resource: dict[str, int] = field(default_factory=dict)
    by_effort: dict[str, int] = field(default_factory=dict)
    by_risk: dict[str, int] = field(default_factory=dict)
    recommendations: list[OptimizationRecommendation] = field(default_factory=list)


class ResourceOptimizationEngine:
    """
    Analyzes resource utilization and generates cost optimization recommendations.

    Supports:
    - Rightsizing based on utilization patterns
    - Scheduled shutdown for non-production resources
    - Reserved capacity recommendations
    - Spot instance recommendations
    - Storage tier migration
    - Auto-scaling enablement
    - Resource consolidation
    - Savings plan purchases
    """

    def __init__(self, thresholds: Optional[UtilizationThresholds] = None):
        self.thresholds = thresholds or UtilizationThresholds()
        self.resource_usage: list[ResourceUsage] = []
        self.line_items: list[CostLineItem] = []
        self.metrics: dict[ResourceType, ResourceMetrics] = {}
        self.recommendations: list[OptimizationRecommendation] = []

    def add_resource_usage(self, usage: ResourceUsage) -> None:
        """Add a resource usage measurement."""
        self.resource_usage.append(usage)

    def add_line_item(self, item: CostLineItem) -> None:
        """Add a cost line item."""
        self.line_items.append(item)

    def load_usage_data(self, usage_data: list[ResourceUsage]) -> None:
        """Load multiple usage measurements."""
        self.resource_usage.extend(usage_data)

    def compute_metrics(self) -> dict[ResourceType, ResourceMetrics]:
        """
        Compute aggregated metrics per resource type.

        Returns:
            Dictionary mapping ResourceType to ResourceMetrics.
        """
        grouped: dict[ResourceType, list[ResourceUsage]] = defaultdict(list)
        for usage in self.resource_usage:
            grouped[usage.resource_type].append(usage)

        self.metrics = {}
        for res_type, usages in grouped.items():
            quantities = [u.quantity for u in usages]
            costs = [u.total_cost for u in usages]
            utils = [u.utilization_pct for u in usages]

            total_qty = sum(quantities)
            total_cost = sum(costs)
            avg_util = statistics.mean(utils) if utils else 0.0
            peak_util = max(utils) if utils else 0.0
            min_util = min(utils) if utils else 0.0
            std_dev = statistics.stdev(utils) if len(utils) > 1 else 0.0

            self.metrics[res_type] = ResourceMetrics(
                resource_type=res_type,
                total_quantity=total_qty,
                total_cost=total_cost,
                avg_utilization=avg_util,
                peak_utilization=peak_util,
                min_utilization=min_util,
                utilization_std_dev=std_dev,
                sample_count=len(usages),
                unit=usages[0].unit if usages else "",
                cost_per_unit=usages[0].cost_per_unit if usages else 0.0,
                hourly_usage=quantities,
                daily_costs=costs,
            )

        return self.metrics

    def generate_recommendations(self) -> list[OptimizationRecommendation]:
        """
        Generate optimization recommendations based on utilization analysis.

        Returns:
            List of OptimizationRecommendation objects.
        """
        if not self.metrics:
            self.compute_metrics()

        self.recommendations = []

        for res_type, metrics in self.metrics.items():
            # Check for underutilized resources -> rightsizing
            if metrics.avg_utilization < self.thresholds.underutilized_pct:
                rec = self._recommend_rightsize(res_type, metrics)
                if rec:
                    self.recommendations.append(rec)

            # Check for idle resources -> scheduled shutdown
            if metrics.avg_utilization < self.thresholds.idle_threshold_pct:
                rec = self._recommend_scheduled_shutdown(res_type, metrics)
                if rec:
                    self.recommendations.append(rec)

            # Check for overutilized -> scale up or auto-scaling
            if metrics.peak_utilization > self.thresholds.overutilized_pct:
                rec = self._recommend_auto_scaling(res_type, metrics)
                if rec:
                    self.recommendations.append(rec)

            # Check for stable high utilization -> reserved capacity
            if (
                metrics.avg_utilization > 60
                and metrics.utilization_std_dev < 15
                and metrics.sample_count > 10
            ):
                rec = self._recommend_reserved_capacity(res_type, metrics)
                if rec:
                    self.recommendations.append(rec)

            # Check for burstable pattern -> spot instances
            if (
                metrics.peak_utilization > 80
                and metrics.avg_utilization < 50
                and metrics.utilization_std_dev > 20
            ):
                rec = self._recommend_spot_instances(res_type, metrics)
                if rec:
                    self.recommendations.append(rec)

            # Storage-specific: check for cold data -> tier migration
            if res_type in (ResourceType.STORAGE_SSD, ResourceType.STORAGE_HDD):
                if metrics.avg_utilization < 40:
                    rec = self._recommend_storage_tier_migration(res_type, metrics)
                    if rec:
                        self.recommendations.append(rec)

        # Check for consolidation opportunities
        consolidation_recs = self._recommend_consolidation()
        self.recommendations.extend(consolidation_recs)

        # Check for savings plan opportunities
        savings_rec = self._recommend_savings_plan()
        if savings_rec:
            self.recommendations.append(savings_rec)

        # Sort by savings descending
        self.recommendations.sort(key=lambda r: r.savings, reverse=True)

        return self.recommendations

    def _recommend_rightsize(
        self, res_type: ResourceType, metrics: ResourceMetrics
    ) -> Optional[OptimizationRecommendation]:
        """Recommend rightsizing an underutilized resource."""
        target_util = self.thresholds.target_utilization_pct
        current_util = metrics.avg_utilization

        if current_util <= 0:
            return None

        # Calculate optimal quantity
        optimal_quantity = metrics.total_quantity * (current_util / target_util)
        reduction = metrics.total_quantity - optimal_quantity
        savings = reduction * metrics.cost_per_unit

        if savings < self.thresholds.min_savings_threshold:
            return None

        savings_pct = (savings / metrics.total_cost * 100) if metrics.total_cost > 0 else 0

        return OptimizationRecommendation(
            action=OptimizationAction.RIGHTSIZE,
            resource_type=res_type,
            description=(
                f"Rightsize {res_type.value}: current utilization {current_util:.1f}% "
                f"is below threshold {self.thresholds.underutilized_pct}%. "
                f"Reduce from {metrics.total_quantity:.1f} to {optimal_quantity:.1f} {metrics.unit}."
            ),
            current_cost=metrics.total_cost,
            projected_cost=metrics.total_cost - savings,
            savings=savings,
            savings_pct=savings_pct,
            confidence=min(0.95, 0.7 + metrics.sample_count * 0.01),
            effort="medium",
            risk="low",
            implementation_steps=[
                f"Analyze {res_type.value} usage patterns over 30 days",
                f"Identify peak vs average utilization for {res_type.value}",
                f"Downsize {res_type.value} allocation by {reduction:.1f} {metrics.unit}",
                "Monitor for 2 weeks to validate no performance degradation",
                "Set up alerts for utilization exceeding 80%",
            ],
        )

    def _recommend_scheduled_shutdown(
        self, res_type: ResourceType, metrics: ResourceMetrics
    ) -> Optional[OptimizationRecommendation]:
        """Recommend scheduled shutdown for idle resources."""
        if metrics.avg_utilization >= self.thresholds.idle_threshold_pct:
            return None

        # Assume 12 hours/day usage for non-production
        savings = metrics.total_cost * 0.5

        if savings < self.thresholds.min_savings_threshold:
            return None

        return OptimizationRecommendation(
            action=OptimizationAction.SCHEDULE_SHUTDOWN,
            resource_type=res_type,
            description=(
                f"Schedule shutdown for {res_type.value}: average utilization "
                f"{metrics.avg_utilization:.1f}% indicates significant idle time. "
                f"Shut down during off-hours (nights/weekends)."
            ),
            current_cost=metrics.total_cost,
            projected_cost=metrics.total_cost - savings,
            savings=savings,
            savings_pct=50.0,
            confidence=0.85,
            effort="low",
            risk="low",
            implementation_steps=[
                f"Define business hours schedule for {res_type.value}",
                "Configure automated start/stop schedules",
                "Set up health checks to ensure clean shutdown/startup",
                "Monitor for 1 week to validate schedule alignment",
                "Document runbook for manual override procedures",
            ],
        )

    def _recommend_auto_scaling(
        self, res_type: ResourceType, metrics: ResourceMetrics
    ) -> Optional[OptimizationRecommendation]:
        """Recommend auto-scaling for overutilized resources."""
        if metrics.peak_utilization <= self.thresholds.overutilized_pct:
            return None

        # Auto-scaling typically saves 20-40% vs static over-provisioning
        estimated_savings = metrics.total_cost * 0.25

        return OptimizationRecommendation(
            action=OptimizationAction.ENABLE_AUTO_SCALING,
            resource_type=res_type,
            description=(
                f"Enable auto-scaling for {res_type.value}: peak utilization "
                f"{metrics.peak_utilization:.1f}% exceeds threshold "
                f"{self.thresholds.overutilized_pct}%. Auto-scale to match demand."
            ),
            current_cost=metrics.total_cost,
            projected_cost=metrics.total_cost - estimated_savings,
            savings=estimated_savings,
            savings_pct=25.0,
            confidence=0.80,
            effort="medium",
            risk="medium",
            implementation_steps=[
                f"Define scaling policies for {res_type.value} (min/max/desired)",
                "Configure CloudWatch/Monitoring alarms for scaling triggers",
                "Set cooldown periods to prevent thrashing",
                "Test scaling behavior under load",
                "Document scaling limits and cost ceilings",
            ],
        )

    def _recommend_reserved_capacity(
        self, res_type: ResourceType, metrics: ResourceMetrics
    ) -> Optional[OptimizationRecommendation]:
        """Recommend reserved capacity for stable workloads."""
        if metrics.avg_utilization < 60 or metrics.utilization_std_dev > 15:
            return None

        # Reserved instances typically save 30-60% vs on-demand
        savings = metrics.total_cost * 0.40

        if savings < self.thresholds.min_savings_threshold:
            return None

        return OptimizationRecommendation(
            action=OptimizationAction.RESERVED_CAPACITY,
            resource_type=res_type,
            description=(
                f"Purchase reserved capacity for {res_type.value}: stable utilization "
                f"at {metrics.avg_utilization:.1f}% (±{metrics.utilization_std_dev:.1f}%) "
                f"makes this ideal for 1-year or 3-year reserved pricing."
            ),
            current_cost=metrics.total_cost,
            projected_cost=metrics.total_cost - savings,
            savings=savings,
            savings_pct=40.0,
            confidence=0.90,
            effort="low",
            risk="low",
            implementation_steps=[
                f"Analyze 90-day usage history for {res_type.value}",
                "Select reservation term (1-year vs 3-year)",
                "Choose payment option (all upfront vs partial vs no upfront)",
                "Purchase reserved capacity",
                "Set up utilization monitoring to ensure reservation coverage",
            ],
        )

    def _recommend_spot_instances(
        self, res_type: ResourceType, metrics: ResourceMetrics
    ) -> Optional[OptimizationRecommendation]:
        """Recommend spot instances for burstable workloads."""
        if metrics.peak_utilization < 80 or metrics.avg_utilization > 50:
            return None

        # Spot instances save 50-90% but can be interrupted
        savings = metrics.total_cost * 0.60

        return OptimizationRecommendation(
            action=OptimizationAction.SPOT_INSTANCES,
            resource_type=res_type,
            description=(
                f"Use spot instances for {res_type.value}: burstable pattern "
                f"(avg {metrics.avg_utilization:.1f}%, peak {metrics.peak_utilization:.1f}%) "
                f"with high variance ({metrics.utilization_std_dev:.1f}%) is ideal for spot."
            ),
            current_cost=metrics.total_cost,
            projected_cost=metrics.total_cost - savings,
            savings=savings,
            savings_pct=60.0,
            confidence=0.70,
            effort="high",
            risk="medium",
            implementation_steps=[
                f"Design {res_type.value} workload for interruption tolerance",
                "Implement checkpointing and graceful shutdown handlers",
                "Configure spot fleet with diversified instance types",
                "Set up fallback to on-demand when spot unavailable",
                "Monitor spot interruption rates and adjust strategy",
            ],
        )

    def _recommend_storage_tier_migration(
        self, res_type: ResourceType, metrics: ResourceMetrics
    ) -> Optional[OptimizationRecommendation]:
        """Recommend migrating cold data to cheaper storage tiers."""
        if metrics.avg_utilization >= 40:
            return None

        # Cold storage tiers save 50-80%
        savings = metrics.total_cost * 0.60

        if savings < self.thresholds.min_savings_threshold:
            return None

        target_tier = "cold" if res_type == ResourceType.STORAGE_SSD else "archive"

        return OptimizationRecommendation(
            action=OptimizationAction.MIGRATE_STORAGE_TIER,
            resource_type=res_type,
            description=(
                f"Migrate {res_type.value} to {target_tier} tier: utilization "
                f"{metrics.avg_utilization:.1f}% indicates mostly cold data. "
                f"Move infrequently accessed data to cheaper storage."
            ),
            current_cost=metrics.total_cost,
            projected_cost=metrics.total_cost - savings,
            savings=savings,
            savings_pct=60.0,
            confidence=0.85,
            effort="medium",
            risk="low",
            implementation_steps=[
                f"Analyze access patterns for {res_type.value} data",
                "Define lifecycle policy (e.g. move to cold after 30 days)",
                "Configure automated tiering rules",
                "Test data retrieval from cold tier",
                "Monitor retrieval latency and costs",
            ],
        )

    def _recommend_consolidation(self) -> list[OptimizationRecommendation]:
        """Recommend consolidating underutilized resources."""
        recommendations = []

        # Group by resource type and find consolidation opportunities
        by_type: dict[ResourceType, list[ResourceMetrics]] = defaultdict(list)
        for res_type, metrics in self.metrics.items():
            by_type[res_type].append(metrics)

        for res_type, metrics_list in by_type.items():
            if len(metrics_list) < 2:
                continue

            # Check if multiple small resources can be consolidated
            small_resources = [
                m for m in metrics_list
                if m.avg_utilization < self.thresholds.underutilized_pct
            ]

            if len(small_resources) >= 2:
                total_cost = sum(m.total_cost for m in small_resources)
                savings = total_cost * 0.30  # 30% savings from consolidation

                if savings >= self.thresholds.min_savings_threshold:
                    recommendations.append(
                        OptimizationRecommendation(
                            action=OptimizationAction.CONSOLIDATE,
                            resource_type=res_type,
                            description=(
                                f"Consolidate {len(small_resources)} underutilized "
                                f"{res_type.value} resources into fewer, larger instances."
                            ),
                            current_cost=total_cost,
                            projected_cost=total_cost - savings,
                            savings=savings,
                            savings_pct=30.0,
                            confidence=0.75,
                            effort="high",
                            risk="medium",
                            implementation_steps=[
                                f"Inventory all {res_type.value} resources",
                                "Map dependencies and network topology",
                                "Plan migration sequence to minimize downtime",
                                "Execute consolidation in batches",
                                "Validate performance post-consolidation",
                            ],
                        )
                    )

        return recommendations

    def _recommend_savings_plan(self) -> Optional[OptimizationRecommendation]:
        """Recommend compute savings plans for consistent spend."""
        # Calculate total compute spend
        compute_cost = sum(
            m.total_cost for rt, m in self.metrics.items()
            if rt in (ResourceType.CPU, ResourceType.MEMORY, ResourceType.GPU)
        )

        if compute_cost < 1000:
            return None

        # Savings plans save 20-30% on committed spend
        savings = compute_cost * 0.25

        return OptimizationRecommendation(
            action=OptimizationAction.PURCHASE_SAVINGS_PLAN,
            resource_type=ResourceType.CPU,
            description=(
                f"Purchase Compute Savings Plan: consistent monthly compute spend of "
                f"${compute_cost:,.2f} qualifies for savings plan discounts."
            ),
            current_cost=compute_cost,
            projected_cost=compute_cost - savings,
            savings=savings,
            savings_pct=25.0,
            confidence=0.85,
            effort="low",
            risk="low",
            implementation_steps=[
                "Analyze 30-day compute spend history",
                "Select savings plan type (Compute vs EC2 Instance)",
                "Choose commitment level ($/hour)",
                "Select payment option",
                "Purchase savings plan",
                "Monitor utilization of savings plan commitment",
            ],
        )

    def get_optimization_summary(self) -> OptimizationSummary:
        """
        Get summary of all optimization recommendations.

        Returns:
            OptimizationSummary with aggregated metrics.
        """
        if not self.recommendations:
            self.generate_recommendations()

        current_cost = sum(m.total_cost for m in self.metrics.values())
        total_savings = sum(r.savings for r in self.recommendations)
        optimized_cost = current_cost - total_savings

        by_action: dict[str, int] = defaultdict(int)
        by_resource: dict[str, int] = defaultdict(int)
        by_effort: dict[str, int] = defaultdict(int)
        by_risk: dict[str, int] = defaultdict(int)

        for rec in self.recommendations:
            action_key = rec.action.value if isinstance(rec.action, OptimizationAction) else str(rec.action)
            by_action[action_key] += 1

            res_key = rec.resource_type.value if isinstance(rec.resource_type, ResourceType) else str(rec.resource_type)
            by_resource[res_key] += 1

            by_effort[rec.effort] += 1
            by_risk[rec.risk] += 1

        savings_pct = (total_savings / current_cost * 100) if current_cost > 0 else 0.0

        return OptimizationSummary(
            total_recommendations=len(self.recommendations),
            total_potential_savings=total_savings,
            total_potential_savings_pct=savings_pct,
            current_monthly_cost=current_cost,
            optimized_monthly_cost=optimized_cost,
            by_action=dict(by_action),
            by_resource=dict(by_resource),
            by_effort=dict(by_effort),
            by_risk=dict(by_risk),
            recommendations=list(self.recommendations),
        )

    def get_quick_wins(self) -> list[OptimizationRecommendation]:
        """
        Get low-effort, low-risk recommendations (quick wins).

        Returns:
            List of quick-win recommendations.
        """
        if not self.recommendations:
            self.generate_recommendations()

        return [
            r for r in self.recommendations
            if r.effort == "low" and r.risk == "low" and r.savings > 0
        ]

    def get_high_impact(self, min_savings: float = 1000) -> list[OptimizationRecommendation]:
        """
        Get high-impact recommendations above a savings threshold.

        Args:
            min_savings: Minimum monthly savings threshold.

        Returns:
            List of high-impact recommendations.
        """
        if not self.recommendations:
            self.generate_recommendations()

        return [r for r in self.recommendations if r.savings >= min_savings]
