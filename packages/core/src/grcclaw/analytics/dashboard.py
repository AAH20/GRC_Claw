"""
KPI Dashboard — three-layer dashboard for GRC_Claw analytics.

Implements the Executive, Program, and Operating dashboard layers
with real-time metric aggregation, RAG status visualization,
and drill-through capability.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from .models import (
    DashboardLayer,
    KPISummary,
    MetricSnapshot,
    RAGStatus,
    MetricCategory,
)
from .engine import AnalyticsEngine
from .metrics_registry import (
    get_executive_metrics,
    get_program_metrics,
    get_operating_metrics,
    get_metrics_by_layer,
    get_metrics_by_category,
)


class DashboardWidget:
    """A single dashboard widget/panel."""

    def __init__(
        self,
        widget_id: str,
        title: str,
        widget_type: str,
        layer: DashboardLayer,
    ):
        self.widget_id = widget_id
        self.title = title
        self.widget_type = widget_type
        self.layer = layer
        self.data: dict[str, Any] = {}
        self.position: tuple[int, int] = (0, 0)  # row, col
        self.size: tuple[int, int] = (1, 1)  # width, height

    def set_data(self, data: dict[str, Any]) -> None:
        self.data = data

    def to_dict(self) -> dict[str, Any]:
        return {
            "widget_id": self.widget_id,
            "title": self.title,
            "widget_type": self.widget_type,
            "layer": self.layer.value,
            "data": self.data,
            "position": self.position,
            "size": self.size,
        }


class ExecutiveDashboard:
    """
    Executive dashboard — one-page principle for Board and C-Suite.

    Shows: overall compliance score, score by framework, top 5 material risks,
    decisions awaiting, incident summary, key metrics with RAG status.
    """

    def __init__(self, engine: AnalyticsEngine):
        self.engine = engine
        self.layer = DashboardLayer.EXECUTIVE
        self.widgets: list[DashboardWidget] = []
        self._build_widgets()

    def _build_widgets(self) -> None:
        """Build default executive dashboard widgets."""
        self.widgets = [
            DashboardWidget("exec-overall-score", "Overall Compliance Score", "gauge", self.layer),
            DashboardWidget("exec-framework-scores", "Compliance Score by Framework", "bar_chart", self.layer),
            DashboardWidget("exec-top-risks", "Top 5 Material Risks", "risk_list", self.layer),
            DashboardWidget("exec-decisions", "Decisions Required", "decision_list", self.layer),
            DashboardWidget("exec-incident-summary", "Incident Summary", "summary_table", self.layer),
            DashboardWidget("exec-kpi-trends", "Key Metric Trends", "trend_chart", self.layer),
            DashboardWidget("exec-rag-overview", "RAG Status Overview", "rag_summary", self.layer),
            DashboardWidget("exec-category-breakdown", "Score by Category", "category_chart", self.layer),
        ]

    def render(
        self,
        snapshots: list[MetricSnapshot],
        period: str = "",
    ) -> dict[str, Any]:
        """Render the executive dashboard."""
        kpi = self.engine.compute_kpi_summary(self.layer, snapshots, period)

        # Overall score widget
        self.widgets[0].set_data({
            "score": kpi.overall_score,
            "health_pct": kpi.health_pct,
            "total_metrics": kpi.total_metrics,
        })

        # Framework scores widget
        framework_scores = self._compute_framework_scores(snapshots)
        self.widgets[1].set_data({"frameworks": framework_scores})

        # Top risks widget
        self.widgets[2].set_data({"risks": kpi.top_risks})

        # Decisions widget
        self.widgets[3].set_data({"decisions": kpi.decisions_required})

        # Incident summary widget
        incident_summary = self._compute_incident_summary(snapshots)
        self.widgets[4].set_data(incident_summary)

        # KPI trends widget
        self.widgets[5].set_data({
            "metrics": [
                {
                    "metric_id": s.metric_id,
                    "name": s.name,
                    "current": s.current_value,
                    "previous": s.previous_value,
                    "trend": s.trend_direction.value,
                    "rag_status": s.rag_status.value,
                }
                for s in snapshots
                if s.dashboard_layers and self.layer in s.dashboard_layers
            ]
        })

        # RAG overview widget
        self.widgets[6].set_data({
            "green": kpi.green_count,
            "amber": kpi.amber_count,
            "red": kpi.red_count,
            "critical": kpi.critical_count,
        })

        # Category breakdown widget
        category_scores = self._compute_category_scores(snapshots)
        self.widgets[7].set_data({"categories": category_scores})

        return {
            "layer": self.layer.value,
            "title": "Executive Dashboard",
            "period": period,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "kpi_summary": kpi.to_dict(),
            "widgets": [w.to_dict() for w in self.widgets],
        }

    def _compute_framework_scores(
        self, snapshots: list[MetricSnapshot]
    ) -> list[dict[str, Any]]:
        """Compute compliance scores by framework."""
        frameworks: dict[str, list[float]] = {}
        for s in snapshots:
            # Map metrics to frameworks based on category
            fw = self._metric_to_framework(s.metric_id)
            if fw:
                frameworks.setdefault(fw, []).append(s.current_value)

        result = []
        for fw, values in frameworks.items():
            avg = round(sum(values) / len(values), 1) if values else 0.0
            result.append({
                "framework": fw,
                "score": avg,
                "metric_count": len(values),
            })
        return sorted(result, key=lambda x: x["score"], reverse=True)

    def _metric_to_framework(self, metric_id: str) -> Optional[str]:
        """Map a metric ID to its primary framework."""
        mapping = {
            "UC1-001": "ISO 42001", "UC1-002": "NIST AI RMF", "UC1-003": "NIST AI RMF",
            "UC1-004": "ISO 42001", "UC1-005": "EU AI Act",
            "UC2-001": "NIST AI RMF", "UC2-002": "NIST AI RMF", "UC2-003": "EU AI Act",
            "UC2-004": "NIST AI RMF", "UC2-005": "ISO 42001", "UC2-006": "ISO 42001",
            "UC3-001": "EU AI Act", "UC3-002": "EU AI Act", "UC3-003": "EU AI Act",
            "UC3-004": "EU AI Act", "UC3-005": "EU AI Act",
            "UC4-001": "EU AI Act", "UC4-002": "EU AI Act", "UC4-003": "EU AI Act",
            "UC4-004": "EU AI Act", "UC4-005": "NIST AI RMF", "UC4-006": "NIST AI RMF",
            "UC5-001": "NIST AI RMF", "UC5-002": "NIST AI RMF", "UC5-003": "ISO 42001",
            "UC5-004": "ISO 42001", "UC5-005": "ISO 42001",
            "UC6-001": "EU AI Act", "UC6-002": "EU AI Act", "UC6-003": "EU AI Act",
            "UC6-004": "EU AI Act",
            "UC7-001": "NIST AI RMF", "UC7-002": "NIST AI RMF", "UC7-003": "NIST AI RMF",
            "UC7-004": "NIST AI RMF", "UC7-005": "ISO 42001",
            "UC8-001": "EU AI Act", "UC8-002": "EU AI Act", "UC8-003": "EU AI Act",
            "UC8-004": "NIST AI RMF",
        }
        return mapping.get(metric_id)

    def _compute_incident_summary(
        self, snapshots: list[MetricSnapshot]
    ) -> dict[str, Any]:
        """Compute incident summary for executive view."""
        incident_metrics = [s for s in snapshots if s.category == MetricCategory.INCIDENT_MANAGEMENT]
        return {
            "total_incident_metrics": len(incident_metrics),
            "open_high_risk": sum(
                1 for s in incident_metrics if s.rag_status in (RAGStatus.RED, RAGStatus.CRITICAL)
            ),
            "metrics": [
                {
                    "metric_id": s.metric_id,
                    "name": s.name,
                    "value": s.current_value,
                    "rag_status": s.rag_status.value,
                }
                for s in incident_metrics
            ],
        }

    def _compute_category_scores(
        self, snapshots: list[MetricSnapshot]
    ) -> list[dict[str, Any]]:
        """Compute average score by metric category."""
        cat_values: dict[str, list[float]] = {}
        for s in snapshots:
            cat = s.category.value
            cat_values.setdefault(cat, []).append(s.current_value)

        result = []
        for cat, values in cat_values.items():
            avg = round(sum(values) / len(values), 1) if values else 0.0
            result.append({"category": cat, "score": avg, "count": len(values)})
        return sorted(result, key=lambda x: x["score"], reverse=True)


class ProgramDashboard:
    """
    Program dashboard — for governance leaders and risk officers.

    Shows: breakdown by risk tier, control family status, exception exposure,
    review currency, monitoring coverage, decision speed metrics.
    """

    def __init__(self, engine: AnalyticsEngine):
        self.engine = engine
        self.layer = DashboardLayer.PROGRAM
        self.widgets: list[DashboardWidget] = []
        self._build_widgets()

    def _build_widgets(self) -> None:
        """Build default program dashboard widgets."""
        self.widgets = [
            DashboardWidget("prog-risk-posture", "Risk Posture by Tier", "risk_matrix", self.layer),
            DashboardWidget("prog-control-status", "Control Family Status", "control_table", self.layer),
            DashboardWidget("prog-exception-exposure", "Exception Exposure", "exception_list", self.layer),
            DashboardWidget("prog-review-currency", "Review Currency", "currency_chart", self.layer),
            DashboardWidget("prog-monitoring-coverage", "Monitoring Coverage", "coverage_chart", self.layer),
            DashboardWidget("prog-decision-speed", "Decision Speed Metrics", "speed_chart", self.layer),
            DashboardWidget("prog-remediation-progress", "Remediation Progress", "progress_chart", self.layer),
            DashboardWidget("prog-vendor-risk", "Vendor Risk Overview", "vendor_table", self.layer),
        ]

    def render(
        self,
        snapshots: list[MetricSnapshot],
        period: str = "",
    ) -> dict[str, Any]:
        """Render the program dashboard."""
        kpi = self.engine.compute_kpi_summary(self.layer, snapshots, period)

        self.widgets[0].set_data({
            "risk_tiers": self._compute_risk_tiers(snapshots),
        })
        self.widgets[1].set_data({
            "controls": self._compute_control_status(snapshots),
        })
        self.widgets[2].set_data({
            "exceptions": [
                {"metric_id": s.metric_id, "name": s.name, "status": s.rag_status.value}
                for s in snapshots if s.rag_status != RAGStatus.GREEN
            ],
        })
        self.widgets[3].set_data({
            "review_currency": self._compute_review_currency(snapshots),
        })
        self.widgets[4].set_data({
            "monitoring": self._compute_monitoring_coverage(snapshots),
        })
        self.widgets[5].set_data({
            "decision_speed": self._compute_decision_speed(snapshots),
        })
        self.widgets[6].set_data({
            "remediation": self._compute_remediation_progress(snapshots),
        })
        self.widgets[7].set_data({
            "vendors": self._compute_vendor_risk(snapshots),
        })

        return {
            "layer": self.layer.value,
            "title": "Program Dashboard",
            "period": period,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "kpi_summary": kpi.to_dict(),
            "widgets": [w.to_dict() for w in self.widgets],
        }

    def _compute_risk_tiers(self, snapshots: list[MetricSnapshot]) -> list[dict[str, Any]]:
        """Compute risk posture by tier."""
        tiers: dict[str, list[MetricSnapshot]] = {}
        for s in snapshots:
            tier = s.tier.value
            tiers.setdefault(tier, []).append(s)

        return [
            {
                "tier": tier,
                "count": len(items),
                "red_count": sum(1 for s in items if s.rag_status == RAGStatus.RED),
                "critical_count": sum(1 for s in items if s.rag_status == RAGStatus.CRITICAL),
            }
            for tier, items in sorted(tiers.items())
        ]

    def _compute_control_status(self, snapshots: list[MetricSnapshot]) -> list[dict[str, Any]]:
        """Compute control family status."""
        return [
            {
                "metric_id": s.metric_id,
                "name": s.name,
                "status": s.rag_status.value,
                "value": s.current_value,
                "target": s.target,
            }
            for s in snapshots
        ]

    def _compute_review_currency(self, snapshots: list[MetricSnapshot]) -> dict[str, Any]:
        """Compute review currency metrics."""
        overdue = [s for s in snapshots if s.rag_status in (RAGStatus.RED, RAGStatus.CRITICAL)]
        return {
            "overdue_count": len(overdue),
            "overdue_metrics": [{"metric_id": s.metric_id, "name": s.name} for s in overdue],
        }

    def _compute_monitoring_coverage(self, snapshots: list[MetricSnapshot]) -> dict[str, Any]:
        """Compute monitoring coverage."""
        monitored = [s for s in snapshots if s.rag_status == RAGStatus.GREEN]
        return {
            "monitored_count": len(monitored),
            "total_count": len(snapshots),
            "coverage_pct": round(len(monitored) / len(snapshots) * 100, 1) if snapshots else 0,
        }

    def _compute_decision_speed(self, snapshots: list[MetricSnapshot]) -> list[dict[str, Any]]:
        """Compute decision speed metrics."""
        return [
            {
                "metric_id": s.metric_id,
                "name": s.name,
                "value": s.current_value,
                "trend": s.trend_direction.value,
            }
            for s in snapshots
            if s.category in (MetricCategory.RISK_COMPLIANCE, MetricCategory.REMEDIATION_IMPROVEMENT)
        ]

    def _compute_remediation_progress(self, snapshots: list[MetricSnapshot]) -> list[dict[str, Any]]:
        """Compute remediation progress."""
        return [
            {
                "metric_id": s.metric_id,
                "name": s.name,
                "value": s.current_value,
                "target": s.target,
                "status": s.rag_status.value,
            }
            for s in snapshots
            if s.category == MetricCategory.REMEDIATION_IMPROVEMENT
        ]

    def _compute_vendor_risk(self, snapshots: list[MetricSnapshot]) -> list[dict[str, Any]]:
        """Compute vendor risk overview."""
        return [
            {
                "metric_id": s.metric_id,
                "name": s.name,
                "value": s.current_value,
                "status": s.rag_status.value,
            }
            for s in snapshots
            if s.category == MetricCategory.THIRD_PARTY_RISK
        ]


class OperatingDashboard:
    """
    Operating dashboard — for engineers and compliance ops.

    Shows: system inventory with status, evidence freshness, open findings,
    incident register, change log, access review status.
    """

    def __init__(self, engine: AnalyticsEngine):
        self.engine = engine
        self.layer = DashboardLayer.OPERATING
        self.widgets: list[DashboardWidget] = []
        self._build_widgets()

    def _build_widgets(self) -> None:
        """Build default operating dashboard widgets."""
        self.widgets = [
            DashboardWidget("ops-system-inventory", "System Inventory", "inventory_table", self.layer),
            DashboardWidget("ops-evidence-freshness", "Evidence Freshness", "freshness_chart", self.layer),
            DashboardWidget("ops-open-findings", "Open Findings", "findings_table", self.layer),
            DashboardWidget("ops-incident-register", "Incident Register", "incident_table", self.layer),
            DashboardWidget("ops-change-log", "Change Log", "change_table", self.layer),
            DashboardWidget("ops-access-review", "Access Review Status", "access_table", self.layer),
            DashboardWidget("ops-agent-metrics", "Agent Metrics", "agent_table", self.layer),
            DashboardWidget("ops-model-performance", "Model Performance", "model_table", self.layer),
        ]

    def render(
        self,
        snapshots: list[MetricSnapshot],
        period: str = "",
    ) -> dict[str, Any]:
        """Render the operating dashboard."""
        kpi = self.engine.compute_kpi_summary(self.layer, snapshots, period)

        self.widgets[0].set_data({
            "inventory": [
                {"metric_id": s.metric_id, "name": s.name, "status": s.rag_status.value}
                for s in snapshots if s.category == MetricCategory.ASSET_INVENTORY
            ],
        })
        self.widgets[1].set_data({
            "freshness": self._compute_evidence_freshness(snapshots),
        })
        self.widgets[2].set_data({
            "findings": [
                {"metric_id": s.metric_id, "name": s.name, "value": s.current_value, "status": s.rag_status.value}
                for s in snapshots if s.rag_status in (RAGStatus.RED, RAGStatus.CRITICAL)
            ],
        })
        self.widgets[3].set_data({
            "incidents": [
                {"metric_id": s.metric_id, "name": s.name, "value": s.current_value}
                for s in snapshots if s.category == MetricCategory.INCIDENT_MANAGEMENT
            ],
        })
        self.widgets[4].set_data({
            "changes": self._compute_change_log(snapshots),
        })
        self.widgets[5].set_data({
            "access": self._compute_access_review(snapshots),
        })
        self.widgets[6].set_data({
            "agents": [
                {"metric_id": s.metric_id, "name": s.name, "value": s.current_value, "status": s.rag_status.value}
                for s in snapshots if s.category == MetricCategory.AGENTIC_AI
            ],
        })
        self.widgets[7].set_data({
            "models": [
                {"metric_id": s.metric_id, "name": s.name, "value": s.current_value, "target": s.target}
                for s in snapshots if s.category == MetricCategory.OPERATIONAL_PERFORMANCE
            ],
        })

        return {
            "layer": self.layer.value,
            "title": "Operating Dashboard",
            "period": period,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "kpi_summary": kpi.to_dict(),
            "widgets": [w.to_dict() for w in self.widgets],
        }

    def _compute_evidence_freshness(self, snapshots: list[MetricSnapshot]) -> dict[str, Any]:
        """Compute evidence freshness metrics."""
        stale = [s for s in snapshots if s.rag_status in (RAGStatus.RED, RAGStatus.CRITICAL)]
        return {
            "stale_count": len(stale),
            "stale_metrics": [{"metric_id": s.metric_id, "name": s.name} for s in stale],
        }

    def _compute_change_log(self, snapshots: list[MetricSnapshot]) -> list[dict[str, Any]]:
        """Compute change log from metric trends."""
        return [
            {
                "metric_id": s.metric_id,
                "name": s.name,
                "previous": s.previous_value,
                "current": s.current_value,
                "change_pct": s.trend_pct,
            }
            for s in snapshots
            if abs(s.trend_pct) > 5
        ]

    def _compute_access_review(self, snapshots: list[MetricSnapshot]) -> dict[str, Any]:
        """Compute access review status."""
        return {
            "total_metrics": len(snapshots),
            "compliant": sum(1 for s in snapshots if s.rag_status == RAGStatus.GREEN),
            "non_compliant": sum(1 for s in snapshots if s.rag_status != RAGStatus.GREEN),
        }


class DashboardManager:
    """
    Manages all three dashboard layers and provides unified access.
    """

    def __init__(self, engine: Optional[AnalyticsEngine] = None):
        self.engine = engine or AnalyticsEngine()
        self.executive = ExecutiveDashboard(self.engine)
        self.program = ProgramDashboard(self.engine)
        self.operating = OperatingDashboard(self.engine)

    def render_dashboard(
        self,
        layer: DashboardLayer,
        snapshots: list[MetricSnapshot],
        period: str = "",
    ) -> dict[str, Any]:
        """Render a specific dashboard layer."""
        if layer == DashboardLayer.EXECUTIVE:
            return self.executive.render(snapshots, period)
        elif layer == DashboardLayer.PROGRAM:
            return self.program.render(snapshots, period)
        elif layer == DashboardLayer.OPERATING:
            return self.operating.render(snapshots, period)
        else:
            raise ValueError(f"Unknown dashboard layer: {layer}")

    def render_all(
        self,
        snapshots: list[MetricSnapshot],
        period: str = "",
    ) -> dict[str, Any]:
        """Render all dashboard layers."""
        return {
            "executive": self.executive.render(snapshots, period),
            "program": self.program.render(snapshots, period),
            "operating": self.operating.render(snapshots, period),
        }

    def get_dashboard_summary(
        self,
        snapshots: list[MetricSnapshot],
        period: str = "",
    ) -> dict[str, Any]:
        """Get a summary across all dashboard layers."""
        return {
            "executive": self.engine.compute_kpi_summary(
                DashboardLayer.EXECUTIVE, snapshots, period
            ).to_dict(),
            "program": self.engine.compute_kpi_summary(
                DashboardLayer.PROGRAM, snapshots, period
            ).to_dict(),
            "operating": self.engine.compute_kpi_summary(
                DashboardLayer.OPERATING, snapshots, period
            ).to_dict(),
        }
