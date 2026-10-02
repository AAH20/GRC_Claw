"""
Cost Anomaly Detection for GRC_Claw.

Detects cost anomalies using statistical methods including:
- Z-score based spike detection
- Moving average deviation
- Budget overrun detection
- Idle resource detection
- Pattern recognition for unusual spending
"""

from __future__ import annotations

import statistics
from collections import defaultdict
from dataclasses import dataclass, field

from .models import (
    Anomaly,
    AnomalySeverity,
    AnomalyType,
    CostCategory,
    CostLineItem,
    ResourceType,
)


@dataclass
class AnomalyThresholds:
    """Thresholds for anomaly detection."""

    z_score_threshold: float = 2.5
    spike_threshold_pct: float = 30.0
    budget_overrun_threshold_pct: float = 10.0
    idle_cost_threshold: float = 50.0
    idle_utilization_threshold: float = 5.0
    min_anomaly_cost: float = 25.0
    moving_average_window: int = 7
    seasonal_adjustment: bool = True


@dataclass
class CostTimeSeries:
    """Time series data for cost analysis."""

    period: str = ""
    timestamps: list[str] = field(default_factory=list)
    costs: list[float] = field(default_factory=list)
    budget: float = 0.0
    category: CostCategory = CostCategory.OTHER
    resource_type: ResourceType | None = None
    metadata: dict = field(default_factory=dict)


@dataclass
class AnomalySummary:
    """Summary of detected anomalies."""

    total_anomalies: int = 0
    by_type: dict[str, int] = field(default_factory=dict)
    by_severity: dict[str, int] = field(default_factory=dict)
    total_excess_cost: float = 0.0
    acknowledged_count: int = 0
    resolved_count: int = 0
    open_count: int = 0
    anomalies: list[Anomaly] = field(default_factory=list)


class CostAnomalyDetector:
    """
    Detects cost anomalies in GRC_Claw spending patterns.

    Uses statistical methods to identify:
    - Cost spikes (z-score based)
    - Budget overruns
    - Idle resource costs
    - Orphaned resources
    - Price increases
    - Usage surges
    - Unusual spending patterns
    """

    def __init__(self, thresholds: AnomalyThresholds | None = None):
        self.thresholds = thresholds or AnomalyThresholds()
        self.time_series: list[CostTimeSeries] = []
        self.line_items: list[CostLineItem] = []
        self.anomalies: list[Anomaly] = []
        self.budgets: dict[str, float] = {}

    def add_time_series(self, series: CostTimeSeries) -> None:
        """Add a cost time series for analysis."""
        self.time_series.append(series)

    def add_line_item(self, item: CostLineItem) -> None:
        """Add a cost line item."""
        self.line_items.append(item)

    def set_budget(self, category: str, amount: float) -> None:
        """Set a budget for a category or resource."""
        self.budgets[category] = amount

    def detect_all(self) -> list[Anomaly]:
        """
        Run all anomaly detection methods.

        Returns:
            List of detected anomalies.
        """
        self.anomalies = []

        self._detect_cost_spikes()
        self._detect_budget_overruns()
        self._detect_idle_resources()
        self._detect_orphaned_resources()
        self._detect_price_increases()
        self._detect_usage_surges()
        self._detect_unusual_patterns()

        # Sort by severity (critical first) then by deviation amount
        severity_order = {
            AnomalySeverity.CRITICAL: 0,
            AnomalySeverity.HIGH: 1,
            AnomalySeverity.MEDIUM: 2,
            AnomalySeverity.LOW: 3,
        }
        self.anomalies.sort(
            key=lambda a: (
                severity_order.get(a.severity, 4),
                -a.deviation_amount,
            )
        )

        return self.anomalies

    def _detect_cost_spikes(self) -> None:
        """Detect cost spikes using z-score analysis."""
        for series in self.time_series:
            if len(series.costs) < 3:
                continue

            mean = statistics.mean(series.costs)
            std_dev = statistics.stdev(series.costs) if len(series.costs) > 1 else 0

            if std_dev == 0:
                continue

            for i, cost in enumerate(series.costs):
                z_score = (cost - mean) / std_dev

                if z_score > self.thresholds.z_score_threshold:
                    deviation_pct = ((cost - mean) / mean * 100) if mean > 0 else 0
                    deviation_amount = cost - mean

                    if deviation_amount < self.thresholds.min_anomaly_cost:
                        continue

                    severity = self._classify_severity(z_score, deviation_pct)

                    self.anomalies.append(
                        Anomaly(
                            anomaly_type=AnomalyType.COST_SPIKE,
                            severity=severity,
                            description=(
                                f"Cost spike detected: ${cost:,.2f} vs average "
                                f"${mean:,.2f} (z-score: {z_score:.2f}, "
                                f"+{deviation_pct:.1f}%)"
                            ),
                            period=series.period,
                            expected_cost=mean,
                            actual_cost=cost,
                            deviation_pct=deviation_pct,
                            deviation_amount=deviation_amount,
                            affected_resources=[series.resource_type.value] if series.resource_type else [],
                            root_cause="Statistical outlier detected via z-score analysis",
                            recommended_action="Investigate root cause and verify if spike is legitimate",
                        )
                    )

    def _detect_budget_overruns(self) -> None:
        """Detect budget overruns."""
        for series in self.time_series:
            if series.budget <= 0:
                continue

            for i, cost in enumerate(series.costs):
                if cost > series.budget:
                    overrun_pct = ((cost - series.budget) / series.budget * 100)
                    overrun_amount = cost - series.budget

                    if overrun_pct < self.thresholds.budget_overrun_threshold_pct:
                        continue

                    severity = self._classify_severity(0, overrun_pct)

                    self.anomalies.append(
                        Anomaly(
                            anomaly_type=AnomalyType.BUDGET_OVERRUN,
                            severity=severity,
                            description=(
                                f"Budget overrun: ${cost:,.2f} exceeds budget "
                                f"${series.budget:,.2f} by {overrun_pct:.1f}% "
                                f"(${overrun_amount:,.2f})"
                            ),
                            period=series.period,
                            expected_cost=series.budget,
                            actual_cost=cost,
                            deviation_pct=overrun_pct,
                            deviation_amount=overrun_amount,
                            affected_resources=[series.resource_type.value] if series.resource_type else [],
                            root_cause="Spending exceeds allocated budget",
                            recommended_action="Review spending and adjust budget or reduce costs",
                        )
                    )

    def _detect_idle_resources(self) -> None:
        """Detect idle resources that are incurring costs."""
        # Group line items by resource
        resource_costs: dict[str, list[CostLineItem]] = defaultdict(list)
        for item in self.line_items:
            key = f"{item.category.value}:{item.description}"
            resource_costs[key].append(item)

        for resource_key, items in resource_costs.items():
            total_cost = sum(i.amount for i in items)

            # Check if resource has metadata indicating low utilization
            avg_utilization = 0
            for item in items:
                util = item.metadata.get("utilization_pct", 0)
                avg_utilization += util
            avg_utilization /= len(items) if items else 1

            if (
                total_cost > self.thresholds.idle_cost_threshold
                and avg_utilization < self.thresholds.idle_utilization_threshold
            ):
                self.anomalies.append(
                    Anomaly(
                        anomaly_type=AnomalyType.IDLE_RESOURCE,
                        severity=AnomalySeverity.MEDIUM,
                        description=(
                            f"Idle resource detected: {resource_key} costing "
                            f"${total_cost:,.2f}/period with {avg_utilization:.1f}% utilization"
                        ),
                        period=items[0].period if items else "",
                        expected_cost=0,
                        actual_cost=total_cost,
                        deviation_pct=100.0,
                        deviation_amount=total_cost,
                        affected_resources=[resource_key],
                        root_cause="Resource is running but barely utilized",
                        recommended_action="Consider shutting down or downsizing this resource",
                    )
                )

    def _detect_orphaned_resources(self) -> None:
        """Detect orphaned resources (no associated project/owner)."""
        for item in self.line_items:
            if not item.allocated_to and item.amount > self.thresholds.min_anomaly_cost:
                self.anomalies.append(
                    Anomaly(
                        anomaly_type=AnomalyType.ORPHANED_RESOURCE,
                        severity=AnomalySeverity.LOW,
                        description=(
                            f"Orphaned resource: {item.description} (${item.amount:,.2f}) "
                            f"has no assigned owner or project"
                        ),
                        period=item.period,
                        expected_cost=0,
                        actual_cost=item.amount,
                        deviation_pct=100.0,
                        deviation_amount=item.amount,
                        affected_resources=[item.description],
                        root_cause="Resource has no assigned owner or project",
                        recommended_action="Assign ownership or decommission if no longer needed",
                    )
                )

    def _detect_price_increases(self) -> None:
        """Detect price increases over time."""
        for series in self.time_series:
            if len(series.costs) < 2:
                continue

            # Compare recent average to historical average
            recent_window = min(3, len(series.costs) // 2)
            if recent_window < 1:
                continue

            recent_avg = statistics.mean(series.costs[-recent_window:])
            historical_avg = statistics.mean(series.costs[:-recent_window]) if len(series.costs) > recent_window else series.costs[0]

            if historical_avg > 0:
                increase_pct = ((recent_avg - historical_avg) / historical_avg * 100)

                if increase_pct > self.thresholds.spike_threshold_pct:
                    self.anomalies.append(
                        Anomaly(
                            anomaly_type=AnomalyType.PRICE_INCREASE,
                            severity=AnomalySeverity.MEDIUM,
                            description=(
                                f"Price increase detected: recent average ${recent_avg:,.2f} "
                                f"vs historical ${historical_avg:,.2f} (+{increase_pct:.1f}%)"
                            ),
                            period=series.period,
                            expected_cost=historical_avg,
                            actual_cost=recent_avg,
                            deviation_pct=increase_pct,
                            deviation_amount=recent_avg - historical_avg,
                            affected_resources=[series.resource_type.value] if series.resource_type else [],
                            root_cause="Unit price increase detected",
                            recommended_action="Review pricing changes and consider alternatives",
                        )
                    )

    def _detect_usage_surges(self) -> None:
        """Detect sudden usage surges."""
        for series in self.time_series:
            if len(series.costs) < 2:
                continue

            for i in range(1, len(series.costs)):
                prev_cost = series.costs[i - 1]
                curr_cost = series.costs[i]

                if prev_cost > 0:
                    surge_pct = ((curr_cost - prev_cost) / prev_cost * 100)

                    if surge_pct > self.thresholds.spike_threshold_pct * 1.5:
                        self.anomalies.append(
                            Anomaly(
                                anomaly_type=AnomalyType.USAGE_SURGE,
                                severity=AnomalySeverity.HIGH,
                                description=(
                                    f"Usage surge: ${curr_cost:,.2f} vs previous "
                                    f"${prev_cost:,.2f} (+{surge_pct:.1f}%)"
                                ),
                                period=series.period,
                                expected_cost=prev_cost,
                                actual_cost=curr_cost,
                                deviation_pct=surge_pct,
                                deviation_amount=curr_cost - prev_cost,
                                affected_resources=[series.resource_type.value] if series.resource_type else [],
                                root_cause="Sudden increase in usage detected",
                                recommended_action="Investigate cause of usage surge",
                            )
                        )

    def _detect_unusual_patterns(self) -> None:
        """Detect unusual spending patterns using coefficient of variation."""
        for series in self.time_series:
            if len(series.costs) < 5:
                continue

            mean = statistics.mean(series.costs)
            std_dev = statistics.stdev(series.costs)

            if mean > 0:
                cv = std_dev / mean

                # High coefficient of variation indicates erratic spending
                if cv > 0.5:
                    self.anomalies.append(
                        Anomaly(
                            anomaly_type=AnomalyType.UNUSUAL_PATTERN,
                            severity=AnomalySeverity.LOW,
                            description=(
                                f"Unusual spending pattern: high variability "
                                f"(CV: {cv:.2f}) in {series.period}"
                            ),
                            period=series.period,
                            expected_cost=mean,
                            actual_cost=max(series.costs),
                            deviation_pct=(max(series.costs) - mean) / mean * 100,
                            deviation_amount=max(series.costs) - mean,
                            affected_resources=[series.resource_type.value] if series.resource_type else [],
                            root_cause="Erratic spending pattern detected",
                            recommended_action="Review spending consistency and identify causes of variability",
                        )
                    )

    def _classify_severity(self, z_score: float, deviation_pct: float) -> AnomalySeverity:
        """Classify anomaly severity based on z-score and deviation."""
        if z_score > 4 or deviation_pct > 100:
            return AnomalySeverity.CRITICAL
        elif z_score > 3 or deviation_pct > 50:
            return AnomalySeverity.HIGH
        elif z_score > 2 or deviation_pct > 25:
            return AnomalySeverity.MEDIUM
        else:
            return AnomalySeverity.LOW

    def get_anomaly_summary(self) -> AnomalySummary:
        """
        Get summary of detected anomalies.

        Returns:
            AnomalySummary with aggregated metrics.
        """
        if not self.anomalies:
            self.detect_all()

        by_type: dict[str, int] = defaultdict(int)
        by_severity: dict[str, int] = defaultdict(int)
        total_excess = 0.0
        acknowledged = 0
        resolved = 0

        for anomaly in self.anomalies:
            type_key = anomaly.anomaly_type.value if isinstance(anomaly.anomaly_type, AnomalyType) else str(anomaly.anomaly_type)
            by_type[type_key] += 1

            sev_key = anomaly.severity.value if isinstance(anomaly.severity, AnomalySeverity) else str(anomaly.severity)
            by_severity[sev_key] += 1

            total_excess += anomaly.deviation_amount

            if anomaly.acknowledged:
                acknowledged += 1
            if anomaly.resolved:
                resolved += 1

        return AnomalySummary(
            total_anomalies=len(self.anomalies),
            by_type=dict(by_type),
            by_severity=dict(by_severity),
            total_excess_cost=total_excess,
            acknowledged_count=acknowledged,
            resolved_count=resolved,
            open_count=len(self.anomalies) - resolved,
            anomalies=list(self.anomalies),
        )

    def get_open_anomalies(self) -> list[Anomaly]:
        """Get all unresolved anomalies."""
        return [a for a in self.anomalies if not a.resolved]

    def get_critical_anomalies(self) -> list[Anomaly]:
        """Get all critical and high severity anomalies."""
        return [
            a for a in self.anomalies
            if a.severity in (AnomalySeverity.CRITICAL, AnomalySeverity.HIGH)
        ]

    def acknowledge_anomaly(self, anomaly_id: str) -> bool:
        """Acknowledge an anomaly by ID."""
        for anomaly in self.anomalies:
            if anomaly.anomaly_id == anomaly_id:
                anomaly.acknowledged = True
                return True
        return False

    def resolve_anomaly(self, anomaly_id: str) -> bool:
        """Mark an anomaly as resolved."""
        for anomaly in self.anomalies:
            if anomaly.anomaly_id == anomaly_id:
                anomaly.resolved = True
                anomaly.acknowledged = True
                return True
        return False
