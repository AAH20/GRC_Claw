"""
Analytics Engine — core computation engine for GRC_Claw metrics.

Processes raw metric values, computes RAG status, determines escalation
tiers, aggregates KPIs, and produces metric snapshots for dashboards.
"""

from __future__ import annotations

import statistics

from .metrics_registry import get_metric
from .models import (
    AnalyticsEvent,
    DashboardLayer,
    KPISummary,
    MetricSnapshot,
    MetricTier,
    MetricValue,
    RAGStatus,
    TrendDirection,
)


class RAGStatusEngine:
    """Computes Red/Amber/Green status for metric values."""

    @staticmethod
    def compute_status(
        value: float,
        target: float,
        tier1: float,
        tier2: float,
        tier3: float,
        direction: str = "lte",
    ) -> RAGStatus:
        """
        Compute RAG status based on thresholds.

        direction='lte': lower is better (e.g., open findings)
        direction='gte': higher is better (e.g., coverage %)
        """
        if direction == "lte":
            if value <= target:
                return RAGStatus.GREEN
            elif value <= tier1:
                return RAGStatus.AMBER
            elif value <= tier2:
                return RAGStatus.RED
            else:
                return RAGStatus.CRITICAL
        elif value >= target:
            return RAGStatus.GREEN
        elif value >= tier1:
            return RAGStatus.AMBER
        elif value >= tier2:
            return RAGStatus.RED
        else:
            return RAGStatus.CRITICAL

    @staticmethod
    def compute_tier(
        value: float,
        tier1: float,
        tier2: float,
        tier3: float,
        direction: str = "lte",
    ) -> MetricTier:
        """Determine escalation tier."""
        if direction == "lte":
            if value > tier3:
                return MetricTier.TIER_3_BOARD
            elif value > tier2:
                return MetricTier.TIER_2_MANAGEMENT
            elif value > tier1:
                return MetricTier.TIER_1_OPERATIONAL
            else:
                return MetricTier.TIER_1_OPERATIONAL
        elif value < tier3:
            return MetricTier.TIER_3_BOARD
        elif value < tier2:
            return MetricTier.TIER_2_MANAGEMENT
        elif value < tier1:
            return MetricTier.TIER_1_OPERATIONAL
        else:
            return MetricTier.TIER_1_OPERATIONAL


class TrendEngine:
    """Computes trend direction and percentage change."""

    @staticmethod
    def compute_trend(
        current: float,
        previous: float,
        threshold_pct: float = 5.0,
    ) -> tuple[TrendDirection, float]:
        """
        Compute trend direction and percentage change.

        Returns (direction, change_pct).
        """
        if previous == 0:
            if current == 0:
                return TrendDirection.STABLE, 0.0
            return TrendDirection.IMPROVING, 100.0

        change_pct = ((current - previous) / abs(previous)) * 100

        if abs(change_pct) < threshold_pct:
            return TrendDirection.STABLE, round(change_pct, 2)

        # For most metrics, increasing is improving; for some, decreasing is improving
        # This is a simplified heuristic — real implementation would use metric direction
        if change_pct > 0:
            return TrendDirection.IMPROVING, round(change_pct, 2)
        else:
            return TrendDirection.DEGRADING, round(change_pct, 2)

    @staticmethod
    def compute_volatility(values: list[float]) -> float:
        """Compute coefficient of variation as volatility measure."""
        if len(values) < 2:
            return 0.0
        mean_val = statistics.mean(values)
        if mean_val == 0:
            return 0.0
        std_dev = statistics.stdev(values)
        return round((std_dev / abs(mean_val)) * 100, 2)


class AnalyticsEngine:
    """
    Main analytics engine. Processes metric values, computes RAG status,
    determines escalation tiers, and produces dashboard-ready snapshots.
    """

    def __init__(self):
        self.rag_engine = RAGStatusEngine()
        self.trend_engine = TrendEngine()
        self._metric_history: dict[str, list[MetricValue]] = {}

    def register_metric_value(self, value: MetricValue) -> None:
        """Register a metric value for historical tracking."""
        mid = value.metric_id
        if mid not in self._metric_history:
            self._metric_history[mid] = []
        self._metric_history[mid].append(value)
        # Keep last 365 values per metric
        if len(self._metric_history[mid]) > 365:
            self._metric_history[mid] = self._metric_history[mid][-365:]

    def process_event(self, event: AnalyticsEvent) -> MetricSnapshot | None:
        """Process an analytics event and return a metric snapshot."""
        metric_def = get_metric(event.metric_id)
        if not metric_def:
            return None

        value = MetricValue(
            metric_id=event.metric_id,
            value=event.value,
            timestamp=event.timestamp,
            source=event.source,
            metadata=event.metadata,
        )
        self.register_metric_value(value)

        history = self._metric_history.get(event.metric_id, [])
        previous = history[-2].value if len(history) >= 2 else event.value

        return self._build_snapshot(metric_def, event.value, previous, history)

    def compute_snapshot(
        self,
        metric_id: str,
        current_value: float,
        previous_value: float | None = None,
        period: str = "",
    ) -> MetricSnapshot | None:
        """Compute a metric snapshot from current and previous values."""
        metric_def = get_metric(metric_id)
        if not metric_def:
            return None

        history = self._metric_history.get(metric_id, [])
        if previous_value is None and len(history) >= 2:
            previous_value = history[-2].value
        elif previous_value is None:
            previous_value = current_value

        return self._build_snapshot(metric_def, current_value, previous_value, history, period)

    def _build_snapshot(
        self,
        metric_def,
        current: float,
        previous: float,
        history: list[MetricValue],
        period: str = "",
    ) -> MetricSnapshot:
        """Build a complete metric snapshot."""
        rag_status = self.rag_engine.compute_status(
            current,
            metric_def.target,
            metric_def.tier1_threshold,
            metric_def.tier2_threshold,
            metric_def.tier3_threshold,
            metric_def.tier1_direction,
        )

        tier = self.rag_engine.compute_tier(
            current,
            metric_def.tier1_threshold,
            metric_def.tier2_threshold,
            metric_def.tier3_threshold,
            metric_def.tier1_direction,
        )

        direction, change_pct = self.trend_engine.compute_trend(current, previous)

        escalation_required = rag_status in (RAGStatus.RED, RAGStatus.CRITICAL)
        escalation_tier = tier if escalation_required else None

        volatility = self.trend_engine.compute_volatility(
            [h.value for h in history] if len(history) >= 2 else [current]
        )

        notes: list[str] = []
        if volatility > 30:
            notes.append(f"High volatility detected ({volatility}%)")
        if rag_status == RAGStatus.CRITICAL:
            notes.append("CRITICAL: Immediate board notification required")
        elif rag_status == RAGStatus.RED:
            notes.append("RED: Management escalation required")
        elif rag_status == RAGStatus.AMBER:
            notes.append("AMBER: Approaching threshold — monitor closely")

        return MetricSnapshot(
            metric_id=metric_def.metric_id,
            name=metric_def.name,
            category=metric_def.category,
            current_value=current,
            previous_value=previous,
            target=metric_def.target,
            rag_status=rag_status,
            trend_direction=direction,
            trend_pct=change_pct,
            tier=tier,
            unit=metric_def.unit,
            period=period,
            owner=metric_def.owner_role,
            dashboard_layers=metric_def.dashboard_layers,
            history=history[-30:] if history else [],
            escalation_required=escalation_required,
            escalation_tier=escalation_tier,
            notes=notes,
        )

    def compute_kpi_summary(
        self,
        layer: DashboardLayer,
        snapshots: list[MetricSnapshot],
        period: str = "",
    ) -> KPISummary:
        """Compute KPI summary for a dashboard layer."""
        total = len(snapshots)
        green = sum(1 for s in snapshots if s.rag_status == RAGStatus.GREEN)
        amber = sum(1 for s in snapshots if s.rag_status == RAGStatus.AMBER)
        red = sum(1 for s in snapshots if s.rag_status == RAGStatus.RED)
        critical = sum(1 for s in snapshots if s.rag_status == RAGStatus.CRITICAL)

        # Overall score: weighted average (green=100, amber=70, red=40, critical=10)
        if total > 0:
            overall_score = round(
                (green * 100 + amber * 70 + red * 40 + critical * 10) / total, 1
            )
        else:
            overall_score = 0.0

        # Top risks: red and critical metrics sorted by severity
        top_risks = [
            {
                "metric_id": s.metric_id,
                "name": s.name,
                "value": s.current_value,
                "target": s.target,
                "rag_status": s.rag_status.value,
                "trend": s.trend_direction.value,
            }
            for s in sorted(
                [s for s in snapshots if s.rag_status in (RAGStatus.RED, RAGStatus.CRITICAL)],
                key=lambda x: x.current_value,
                reverse=True,
            )[:5]
        ]

        # Decisions required: metrics with escalation
        decisions_required = [
            {
                "metric_id": s.metric_id,
                "name": s.name,
                "escalation_tier": s.escalation_tier.value if s.escalation_tier else None,
                "action": f"Review {s.name} — {s.rag_status.value}",
            }
            for s in snapshots
            if s.escalation_required
        ]

        return KPISummary(
            layer=layer,
            total_metrics=total,
            green_count=green,
            amber_count=amber,
            red_count=red,
            critical_count=critical,
            overall_score=overall_score,
            metrics=snapshots,
            top_risks=top_risks,
            decisions_required=decisions_required,
            period=period,
        )

    def get_metric_history(self, metric_id: str) -> list[MetricValue]:
        """Get historical values for a metric."""
        return self._metric_history.get(metric_id, [])

    def clear_history(self, metric_id: str | None = None) -> None:
        """Clear metric history (all or specific)."""
        if metric_id:
            self._metric_history.pop(metric_id, None)
        else:
            self._metric_history.clear()
