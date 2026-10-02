"""
Dashboard engine — core rendering, data fetching, and management.
"""

from __future__ import annotations

import json
import time
from collections import defaultdict
from datetime import UTC, datetime
from typing import Any

from .analytics import (
    ComplianceAggregator,
    GovernanceScorer,
    MetricCalculator,
    RiskAggregator,
    TrendAnalyzer,
)
from .models import (
    ChartType,
    DashboardConfig,
    DashboardSnapshot,
    DashboardWidget,
    DataSourceType,
    FilterCriteria,
    GovernanceScore,
    TrendDirection,
    WidgetType,
)


class DashboardEngine:
    """
    Core engine for dashboard data fetching, caching, and rendering.
    Orchestrates data sources, applies filters, and produces widget data.
    """

    def __init__(self):
        self._cache: dict[str, tuple[float, Any]] = {}
        self._data_providers: dict[DataSourceType, Any] = {}
        self.metric_calculator = MetricCalculator()
        self.trend_analyzer = TrendAnalyzer()
        self.compliance_aggregator = ComplianceAggregator()
        self.risk_aggregator = RiskAggregator()
        self.governance_scorer = GovernanceScorer()

    def register_data_provider(self, source_type: DataSourceType, provider: Any) -> None:
        """Register a data provider for a specific source type."""
        self._data_providers[source_type] = provider

    def fetch_widget_data(
        self,
        widget: DashboardWidget,
        filters: list[FilterCriteria] | None = None,
        force_refresh: bool = False,
    ) -> Any:
        """Fetch data for a single widget with caching."""
        cache_key = f"{widget.id}:{hash(str(widget.data_query))}"
        now = time.time()

        if not force_refresh and cache_key in self._cache:
            cached_time, cached_data = self._cache[cache_key]
            if now - cached_time < widget.cache_ttl_seconds:
                return cached_data

        provider = self._data_providers.get(widget.data_source)
        if provider is None:
            data = self._generate_sample_data(widget)
        else:
            data = provider.fetch(widget.data_query, filters or widget.filters)

        self._cache[cache_key] = (now, data)
        widget.last_refreshed = datetime.now(UTC).isoformat()
        widget.cached_data = data
        return data

    def render_dashboard(
        self,
        config: DashboardConfig,
        filters: list[FilterCriteria] | None = None,
    ) -> dict[str, Any]:
        """Render a complete dashboard with all widget data."""
        effective_filters = filters or config.filters
        widget_results = {}

        for widget in config.widgets:
            if not widget.enabled:
                continue
            try:
                data = self.fetch_widget_data(widget, effective_filters)
                widget_results[widget.id] = {
                    "widget": widget.to_dict(),
                    "data": data,
                    "status": "ok",
                }
            except Exception as e:
                widget_results[widget.id] = {
                    "widget": widget.to_dict(),
                    "data": None,
                    "status": "error",
                    "error": str(e),
                }

        governance_score = self.governance_scorer.calculate(
            config, widget_results, effective_filters
        )

        return {
            "dashboard": config.to_dict(),
            "widgets": widget_results,
            "governance_score": {
                "overall": governance_score.overall,
                "governance": governance_score.governance,
                "risk": governance_score.risk,
                "compliance": governance_score.compliance,
                "operational": governance_score.operational,
                "security": governance_score.security,
                "trend": governance_score.trend.value,
                "change_pct": governance_score.change_pct,
                "breakdown": governance_score.breakdown,
                "recommendations": governance_score.recommendations,
            },
            "rendered_at": datetime.now(UTC).isoformat(),
        }

    def create_snapshot(
        self,
        config: DashboardConfig,
        filters: list[FilterCriteria] | None = None,
    ) -> DashboardSnapshot:
        """Create a point-in-time snapshot of the dashboard."""
        rendered = self.render_dashboard(config, filters)
        return DashboardSnapshot(
            dashboard_id=config.id,
            dashboard_name=config.name,
            widget_data={
                wid: wdata["data"]
                for wid, wdata in rendered["widgets"].items()
            },
            governance_score=GovernanceScore(
                overall=rendered["governance_score"]["overall"],
                governance=rendered["governance_score"]["governance"],
                risk=rendered["governance_score"]["risk"],
                compliance=rendered["governance_score"]["compliance"],
                operational=rendered["governance_score"]["operational"],
                security=rendered["governance_score"]["security"],
                trend=TrendDirection(rendered["governance_score"]["trend"]),
                change_pct=rendered["governance_score"]["change_pct"],
                breakdown=rendered["governance_score"]["breakdown"],
                recommendations=rendered["governance_score"]["recommendations"],
            ),
            summary={
                "total_widgets": len(config.widgets),
                "active_widgets": sum(1 for w in config.widgets if w.enabled),
                "data_sources": list(set(w.data_source.value for w in config.widgets)),
            },
        )

    def invalidate_cache(self, widget_id: str | None = None) -> None:
        """Invalidate cache for a specific widget or all widgets."""
        if widget_id:
            keys_to_remove = [k for k in self._cache if k.startswith(f"{widget_id}:")]
            for k in keys_to_remove:
                del self._cache[k]
        else:
            self._cache.clear()

    def _generate_sample_data(self, widget: DashboardWidget) -> Any:
        """Generate sample data for demo/testing purposes."""
        if widget.widget_type == WidgetType.KPI:
            return self._sample_kpi_data(widget)
        elif widget.widget_type == WidgetType.CHART:
            return self._sample_chart_data(widget)
        elif widget.widget_type == WidgetType.TABLE:
            return self._sample_table_data(widget)
        elif widget.widget_type == WidgetType.ALERT:
            return self._sample_alert_data(widget)
        elif widget.widget_type == WidgetType.HEATMAP:
            return self._sample_heatmap_data(widget)
        elif widget.widget_type == WidgetType.GAUGE:
            return self._sample_gauge_data(widget)
        elif widget.widget_type == WidgetType.SPARKLINE:
            return self._sample_sparkline_data(widget)
        elif widget.widget_type == WidgetType.TEXT:
            return {"content": f"Sample text for {widget.name}"}
        return {}

    def _sample_kpi_data(self, widget: DashboardWidget) -> dict:
        return {
            "value": 42,
            "previous_value": 38,
            "change": 4,
            "change_pct": 10.5,
            "trend": "up",
            "target": 50,
            "unit": "",
            "label": widget.name,
        }

    def _sample_chart_data(self, widget: DashboardWidget) -> dict:
        chart_type = widget.chart_type or ChartType.LINE
        labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]
        if chart_type in (ChartType.PIE, ChartType.DOUGHNUT):
            return {
                "labels": ["Compliant", "Partial", "Non-Compliant", "Not Assessed"],
                "values": [65, 20, 10, 5],
                "colors": ["#22c55e", "#f59e0b", "#ef4444", "#6b7280"],
            }
        return {
            "labels": labels,
            "datasets": [
                {
                    "label": "Current Period",
                    "data": [12, 19, 15, 22, 18, 25],
                    "color": "#3b82f6",
                },
                {
                    "label": "Previous Period",
                    "data": [10, 15, 14, 18, 16, 20],
                    "color": "#94a3b8",
                },
            ],
        }

    def _sample_table_data(self, widget: DashboardWidget) -> dict:
        return {
            "columns": ["ID", "Name", "Status", "Risk Level", "Last Updated"],
            "rows": [
                ["R-001", "Agent goal hijacking", "Active", "Critical", "2026-09-15"],
                ["R-002", "Bias in loan approval", "Mitigated", "High", "2026-09-10"],
                ["R-003", "Vendor model update", "Monitoring", "Medium", "2026-09-08"],
                ["R-004", "Data poisoning", "Identified", "High", "2026-09-05"],
                ["R-005", "Prompt injection", "Closed", "Low", "2026-08-28"],
            ],
            "total_count": 5,
            "page": 1,
            "page_size": 25,
        }

    def _sample_alert_data(self, widget: DashboardWidget) -> dict:
        return {
            "alerts": [
                {
                    "id": "A-001",
                    "severity": "critical",
                    "title": "Critical risk threshold breached",
                    "source": "risk_monitor",
                    "timestamp": "2026-10-01T10:30:00Z",
                    "acknowledged": False,
                },
                {
                    "id": "A-002",
                    "severity": "high",
                    "title": "Compliance deadline approaching",
                    "source": "compliance_engine",
                    "timestamp": "2026-10-01T09:15:00Z",
                    "acknowledged": True,
                },
                {
                    "id": "A-003",
                    "severity": "medium",
                    "title": "Evidence collection overdue",
                    "source": "evidence_store",
                    "timestamp": "2026-10-01T08:00:00Z",
                    "acknowledged": False,
                },
            ],
            "total_count": 3,
            "unacknowledged_count": 2,
        }

    def _sample_heatmap_data(self, widget: DashboardWidget) -> dict:
        domains = ["SEC", "DAT", "TPR", "MOD", "GOV", "OPS", "CMP"]
        categories = ["SEC-01", "SEC-02", "DAT-01", "DAT-02", "TPR-01", "MOD-01", "GOV-01", "OPS-01", "CMP-01"]
        matrix = []
        for d in domains:
            row = {"domain": d, "categories": {}}
            for c in categories:
                row["categories"][c] = (hash(d + c) % 10) + 1
            row["total"] = sum(row["categories"].values())
            matrix.append(row)
        return {
            "domains": domains,
            "categories": categories,
            "matrix": matrix,
            "max_value": 10,
        }

    def _sample_gauge_data(self, widget: DashboardWidget) -> dict:
        return {
            "value": 72,
            "min": 0,
            "max": 100,
            "zones": [
                {"min": 0, "max": 40, "color": "#ef4444", "label": "Poor"},
                {"min": 40, "max": 70, "color": "#f59e0b", "label": "Fair"},
                {"min": 70, "max": 90, "color": "#22c55e", "label": "Good"},
                {"min": 90, "max": 100, "color": "#3b82f6", "label": "Excellent"},
            ],
        }

    def _sample_sparkline_data(self, widget: DashboardWidget) -> dict:
        return {
            "values": [12, 15, 14, 18, 22, 20, 25, 23, 28, 30, 27, 32],
            "labels": ["W1", "W2", "W3", "W4", "W5", "W6", "W7", "W8", "W9", "W10", "W11", "W12"],
            "trend": "up",
        }


class DashboardRenderer:
    """
    Renders dashboard data into various output formats.
    Supports JSON, HTML, and Markdown rendering.
    """

    def __init__(self, engine: DashboardEngine | None = None):
        self.engine = engine or DashboardEngine()

    def render_json(self, rendered_dashboard: dict[str, Any]) -> str:
        """Render dashboard as JSON."""
        return json.dumps(rendered_dashboard, indent=2, default=str)

    def render_markdown(self, rendered_dashboard: dict[str, Any]) -> str:
        """Render dashboard as Markdown."""
        dashboard = rendered_dashboard.get("dashboard", {})
        score = rendered_dashboard.get("governance_score", {})
        widgets = rendered_dashboard.get("widgets", {})

        lines = [
            f"# {dashboard.get('name', 'Dashboard')}",
            "",
            f"_{dashboard.get('description', '')}_",
            "",
            f"**Overall Governance Score:** {score.get('overall', 0):.1f}/100",
            "",
            "## Score Breakdown",
            "",
            "| Dimension | Score |",
            "|-----------|-------|",
            f"| Governance | {score.get('governance', 0):.1f} |",
            f"| Risk | {score.get('risk', 0):.1f} |",
            f"| Compliance | {score.get('compliance', 0):.1f} |",
            f"| Operational | {score.get('operational', 0):.1f} |",
            f"| Security | {score.get('security', 0):.1f} |",
            "",
            "## Widgets",
            "",
        ]

        for wid, wdata in widgets.items():
            widget = wdata.get("widget", {})
            status = wdata.get("status", "unknown")
            lines.append(f"### {widget.get('name', wid)}")
            lines.append("")
            lines.append(f"- **Type:** {widget.get('widget_type', 'unknown')}")
            lines.append(f"- **Status:** {status}")
            if status == "ok":
                data = wdata.get("data", {})
                if isinstance(data, dict) and "value" in data:
                    lines.append(f"- **Value:** {data['value']}")
            lines.append("")

        recs = score.get("recommendations", [])
        if recs:
            lines.append("## Recommendations")
            lines.append("")
            for rec in recs:
                lines.append(f"- {rec}")
            lines.append("")

        lines.append(f"_Rendered at {rendered_dashboard.get('rendered_at', '')}_")
        return "\n".join(lines)

    def render_html(self, rendered_dashboard: dict[str, Any]) -> str:
        """Render dashboard as a self-contained HTML page."""
        dashboard = rendered_dashboard.get("dashboard", {})
        score = rendered_dashboard.get("governance_score", {})
        widgets = rendered_dashboard.get("widgets", {})

        widget_cards = []
        for wid, wdata in widgets.items():
            widget = wdata.get("widget", {})
            status = wdata.get("status", "unknown")
            data = wdata.get("data", {})

            value_html = ""
            if isinstance(data, dict) and "value" in data:
                value_html = f'<div class="kpi-value">{data["value"]}</div>'
            elif isinstance(data, dict) and "alerts" in data:
                value_html = f'<div class="kpi-value">{len(data["alerts"])}</div>'
            elif isinstance(data, dict) and "rows" in data:
                value_html = f'<div class="kpi-value">{data.get("total_count", 0)}</div>'

            widget_cards.append(f"""
            <div class="widget-card">
                <h3>{widget.get('name', wid)}</h3>
                <div class="widget-type">{widget.get('widget_type', 'unknown')}</div>
                {value_html}
                <div class="widget-status {status}">{status}</div>
            </div>""")

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{dashboard.get('name', 'GRC Dashboard')}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f8fafc; color: #1e293b; padding: 24px; }}
        .dashboard-header {{ margin-bottom: 32px; }}
        .dashboard-header h1 {{ font-size: 28px; font-weight: 700; margin-bottom: 8px; }}
        .dashboard-header p {{ color: #64748b; font-size: 14px; }}
        .score-overview {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: 16px; margin-bottom: 32px; }}
        .score-card {{ background: white; border-radius: 12px; padding: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); text-align: center; }}
        .score-card .label {{ font-size: 12px; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px; }}
        .score-card .value {{ font-size: 32px; font-weight: 700; }}
        .score-card.overall .value {{ color: #3b82f6; }}
        .score-card.governance .value {{ color: #8b5cf6; }}
        .score-card.risk .value {{ color: #ef4444; }}
        .score-card.compliance .value {{ color: #22c55e; }}
        .score-card.operational .value {{ color: #f59e0b; }}
        .widgets-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; }}
        .widget-card {{ background: white; border-radius: 12px; padding: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
        .widget-card h3 {{ font-size: 16px; font-weight: 600; margin-bottom: 4px; }}
        .widget-type {{ font-size: 12px; color: #94a3b8; text-transform: uppercase; margin-bottom: 12px; }}
        .kpi-value {{ font-size: 36px; font-weight: 700; color: #1e293b; }}
        .widget-status {{ font-size: 12px; margin-top: 8px; padding: 4px 8px; border-radius: 4px; display: inline-block; }}
        .widget-status.ok {{ background: #dcfce7; color: #166534; }}
        .widget-status.error {{ background: #fee2e2; color: #991b1b; }}
        .recommendations {{ margin-top: 32px; background: white; border-radius: 12px; padding: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
        .recommendations h2 {{ font-size: 18px; margin-bottom: 12px; }}
        .recommendations ul {{ padding-left: 20px; }}
        .recommendations li {{ margin-bottom: 8px; color: #475569; }}
    </style>
</head>
<body>
    <div class="dashboard-header">
        <h1>{dashboard.get('name', 'GRC Dashboard')}</h1>
        <p>{dashboard.get('description', '')}</p>
    </div>
    <div class="score-overview">
        <div class="score-card overall"><div class="label">Overall</div><div class="value">{score.get('overall', 0):.0f}</div></div>
        <div class="score-card governance"><div class="label">Governance</div><div class="value">{score.get('governance', 0):.0f}</div></div>
        <div class="score-card risk"><div class="label">Risk</div><div class="value">{score.get('risk', 0):.0f}</div></div>
        <div class="score-card compliance"><div class="label">Compliance</div><div class="value">{score.get('compliance', 0):.0f}</div></div>
        <div class="score-card operational"><div class="label">Operational</div><div class="value">{score.get('operational', 0):.0f}</div></div>
    </div>
    <div class="widgets-grid">
        {''.join(widget_cards)}
    </div>
    {self._render_recommendations_html(score.get('recommendations', []))}
</body>
</html>"""
        return html

    def _render_recommendations_html(self, recommendations: list[str]) -> str:
        if not recommendations:
            return ""
        items = "".join(f"<li>{r}</li>" for r in recommendations)
        return f"""
    <div class="recommendations">
        <h2>Recommendations</h2>
        <ul>{items}</ul>
    </div>"""


class DashboardManager:
    """
    Manages dashboard lifecycle: CRUD, versioning, access control.
    """

    def __init__(self):
        self._dashboards: dict[str, DashboardConfig] = {}
        self._snapshots: dict[str, list[DashboardSnapshot]] = defaultdict(list)
        self._engine = DashboardEngine()
        self._renderer = DashboardRenderer(self._engine)

    def create_dashboard(self, config: DashboardConfig) -> DashboardConfig:
        """Create a new dashboard."""
        self._dashboards[config.id] = config
        return config

    def get_dashboard(self, dashboard_id: str) -> DashboardConfig | None:
        """Retrieve a dashboard by ID."""
        dashboard = self._dashboards.get(dashboard_id)
        if dashboard:
            dashboard.last_accessed = datetime.now(UTC).isoformat()
            dashboard.access_count += 1
        return dashboard

    def update_dashboard(self, dashboard_id: str, updates: dict[str, Any]) -> DashboardConfig | None:
        """Update an existing dashboard."""
        dashboard = self._dashboards.get(dashboard_id)
        if not dashboard:
            return None
        for key, value in updates.items():
            if hasattr(dashboard, key):
                setattr(dashboard, key, value)
        dashboard.version += 1
        dashboard.updated_at = datetime.now(UTC).isoformat()
        return dashboard

    def delete_dashboard(self, dashboard_id: str) -> bool:
        """Delete a dashboard."""
        if dashboard_id in self._dashboards:
            del self._dashboards[dashboard_id]
            self._snapshots.pop(dashboard_id, None)
            return True
        return False

    def list_dashboards(
        self,
        category: str | None = None,
        tag: str | None = None,
        owner: str | None = None,
    ) -> list[DashboardConfig]:
        """List dashboards with optional filtering."""
        results = list(self._dashboards.values())
        if category:
            results = [d for d in results if d.category == category]
        if tag:
            results = [d for d in results if tag in d.tags]
        if owner:
            results = [d for d in results if d.owner == owner]
        return results

    def clone_dashboard(self, dashboard_id: str, new_name: str) -> DashboardConfig | None:
        """Clone an existing dashboard."""
        source = self._dashboards.get(dashboard_id)
        if not source:
            return None
        import copy
        cloned = copy.deepcopy(source)
        cloned.id = str(__import__("uuid").uuid4())[:12]
        cloned.name = new_name
        cloned.version = 1
        cloned.is_default = False
        cloned.created_at = datetime.now(UTC).isoformat()
        cloned.updated_at = datetime.now(UTC).isoformat()
        cloned.access_count = 0
        self._dashboards[cloned.id] = cloned
        return cloned

    def save_snapshot(self, snapshot: DashboardSnapshot) -> None:
        """Save a dashboard snapshot."""
        self._snapshots[snapshot.dashboard_id].append(snapshot)

    def get_snapshots(self, dashboard_id: str, limit: int = 10) -> list[DashboardSnapshot]:
        """Get recent snapshots for a dashboard."""
        return self._snapshots.get(dashboard_id, [])[-limit:]

    def render_dashboard(
        self,
        dashboard_id: str,
        output_format: str = "json",
        filters: list[FilterCriteria] | None = None,
    ) -> str | None:
        """Render a dashboard in the specified format."""
        dashboard = self._dashboards.get(dashboard_id)
        if not dashboard:
            return None
        rendered = self._engine.render_dashboard(dashboard, filters)
        if output_format == "json":
            return self._renderer.render_json(rendered)
        elif output_format == "markdown":
            return self._renderer.render_markdown(rendered)
        elif output_format == "html":
            return self._renderer.render_html(rendered)
        return None
