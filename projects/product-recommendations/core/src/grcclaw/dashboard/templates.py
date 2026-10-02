"""
Dashboard templates — pre-built dashboard layouts for common GRC use cases.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from .models import (
    ChartType,
    DashboardConfig,
    DashboardLayout,
    DashboardWidget,
    DataSourceType,
    FilterCriteria,
    MetricAggregation,
    TimeRange,
    WidgetSize,
    WidgetType,
)


class DashboardTemplate:
    """
    A reusable dashboard template that can be instantiated
    with custom parameters.
    """

    def __init__(
        self,
        name: str,
        description: str,
        category: str,
        layout: DashboardLayout,
        widget_configs: list[dict[str, Any]],
        default_filters: list[FilterCriteria] | None = None,
        tags: list[str] | None = None,
        author: str = "",
        version: str = "1.0.0",
    ):
        self.name = name
        self.description = description
        self.category = category
        self.layout = layout
        self.widget_configs = widget_configs
        self.default_filters = default_filters or []
        self.tags = tags or []
        self.author = author
        self.version = version

    def instantiate(
        self,
        name: str | None = None,
        custom_filters: list[FilterCriteria] | None = None,
        **overrides: Any,
    ) -> DashboardConfig:
        """Create a dashboard configuration from this template."""
        import uuid

        widgets = []
        for wc in self.widget_configs:
            widget = DashboardWidget(
                name=wc.get("name", ""),
                description=wc.get("description", ""),
                widget_type=WidgetType(wc.get("widget_type", "kpi")),
                size=WidgetSize(wc.get("size", "medium")),
                chart_type=ChartType(wc["chart_type"]) if wc.get("chart_type") else None,
                data_source=DataSourceType(wc.get("data_source", "custom")),
                data_query=wc.get("data_query", {}),
                filters=wc.get("filters", []),
                aggregation=MetricAggregation(wc.get("aggregation", "count")),
                refresh_interval_seconds=wc.get("refresh_interval_seconds", 300),
                position_x=wc.get("position_x", 0),
                position_y=wc.get("position_y", 0),
                width=wc.get("width", 2),
                height=wc.get("height", 1),
                config=wc.get("config", {}),
                enabled=wc.get("enabled", True),
                tags=wc.get("tags", []),
            )
            widgets.append(widget)

        filters = custom_filters or self.default_filters

        config = DashboardConfig(
            id=str(uuid.uuid4())[:12],
            name=name or self.name,
            description=self.description,
            category=self.category,
            layout=self.layout,
            widgets=widgets,
            filters=filters,
            tags=self.tags.copy(),
            owner=self.author,
            is_default=False,
            version=1,
        )

        # Apply overrides
        for key, value in overrides.items():
            if hasattr(config, key):
                setattr(config, key, value)

        return config

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "layout": {
                "columns": self.layout.columns,
                "row_height": self.layout.row_height,
                "gutter": self.layout.gutter,
                "padding": self.layout.padding,
                "theme": self.layout.theme,
            },
            "widget_count": len(self.widget_configs),
            "widget_configs": self.widget_configs,
            "default_filters": [
                {"field": f.field, "operator": f.operator, "value": f.value}
                for f in self.default_filters
            ],
            "tags": self.tags,
            "author": self.author,
            "version": self.version,
        }


class TemplateLibrary:
    """
    Library of pre-built dashboard templates for common GRC scenarios.
    """

    def __init__(self):
        self._templates: dict[str, DashboardTemplate] = {}
        self._register_builtin_templates()

    def register(self, template: DashboardTemplate) -> None:
        """Register a template in the library."""
        self._templates[template.name] = template

    def get(self, name: str) -> DashboardTemplate | None:
        """Retrieve a template by name."""
        return self._templates.get(name)

    def list_templates(
        self,
        category: str | None = None,
        tag: str | None = None,
    ) -> list[DashboardTemplate]:
        """List available templates with optional filtering."""
        results = list(self._templates.values())
        if category:
            results = [t for t in results if t.category == category]
        if tag:
            results = [t for t in results if tag in t.tags]
        return results

    def categories(self) -> list[str]:
        """Get all unique template categories."""
        return sorted(set(t.category for t in self._templates.values()))

    def _register_builtin_templates(self) -> None:
        """Register all built-in dashboard templates."""
        self._templates["executive_overview"] = self._create_executive_overview()
        self._templates["risk_posture"] = self._create_risk_posture()
        self._templates["compliance_status"] = self._create_compliance_status()
        self._templates["operational_metrics"] = self._create_operational_metrics()
        self._templates["incident_response"] = self._create_incident_response()
        self._templates["cost_governance"] = self._create_cost_governance()
        self._templates["audit_readiness"] = self._create_audit_readiness()
        self._templates["framework_coverage"] = self._create_framework_coverage()

    def _create_executive_overview(self) -> DashboardTemplate:
        return DashboardTemplate(
            name="Executive Overview",
            description="High-level governance posture for C-suite and board reporting",
            category="executive",
            layout=DashboardLayout(columns=12, row_height=80, theme="light"),
            widget_configs=[
                {
                    "name": "Governance Score",
                    "description": "Overall governance health score",
                    "widget_type": "kpi",
                    "size": "medium",
                    "data_source": "custom",
                    "aggregation": "avg",
                    "position_x": 0, "position_y": 0, "width": 3, "height": 2,
                },
                {
                    "name": "Risk Level",
                    "description": "Current risk posture",
                    "widget_type": "gauge",
                    "size": "medium",
                    "data_source": "risk_register",
                    "position_x": 3, "position_y": 0, "width": 3, "height": 2,
                },
                {
                    "name": "Compliance Score",
                    "description": "Overall compliance percentage",
                    "widget_type": "kpi",
                    "size": "medium",
                    "data_source": "compliance_framework",
                    "aggregation": "avg",
                    "position_x": 6, "position_y": 0, "width": 3, "height": 2,
                },
                {
                    "name": "Active Alerts",
                    "description": "Current active alerts count",
                    "widget_type": "kpi",
                    "size": "medium",
                    "data_source": "notification",
                    "aggregation": "count",
                    "position_x": 9, "position_y": 0, "width": 3, "height": 2,
                },
                {
                    "name": "Risk Trend",
                    "description": "Risk score trend over time",
                    "widget_type": "chart",
                    "size": "large",
                    "chart_type": "line",
                    "data_source": "risk_register",
                    "position_x": 0, "position_y": 2, "width": 6, "height": 3,
                },
                {
                    "name": "Compliance by Framework",
                    "description": "Compliance breakdown by framework",
                    "widget_type": "chart",
                    "size": "large",
                    "chart_type": "doughnut",
                    "data_source": "compliance_framework",
                    "position_x": 6, "position_y": 2, "width": 6, "height": 3,
                },
                {
                    "name": "Top Risks",
                    "description": "Top 5 material risks",
                    "widget_type": "table",
                    "size": "full",
                    "data_source": "risk_register",
                    "position_x": 0, "position_y": 5, "width": 12, "height": 3,
                },
            ],
            default_filters=[
                FilterCriteria(field="time_range", value=TimeRange.LAST_30D),
            ],
            tags=["executive", "overview", "board"],
            author="GRC_Claw",
        )

    def _create_risk_posture(self) -> DashboardTemplate:
        return DashboardTemplate(
            name="Risk Posture",
            description="Comprehensive risk landscape and treatment status",
            category="risk",
            layout=DashboardLayout(columns=12, row_height=80, theme="light"),
            widget_configs=[
                {
                    "name": "Overall Risk Score",
                    "widget_type": "gauge",
                    "size": "medium",
                    "data_source": "risk_register",
                    "position_x": 0, "position_y": 0, "width": 3, "height": 2,
                },
                {
                    "name": "Critical Risks",
                    "widget_type": "kpi",
                    "size": "small",
                    "data_source": "risk_register",
                    "aggregation": "count",
                    "position_x": 3, "position_y": 0, "width": 3, "height": 1,
                },
                {
                    "name": "High Risks",
                    "widget_type": "kpi",
                    "size": "small",
                    "data_source": "risk_register",
                    "aggregation": "count",
                    "position_x": 6, "position_y": 0, "width": 3, "height": 1,
                },
                {
                    "name": "Medium Risks",
                    "widget_type": "kpi",
                    "size": "small",
                    "data_source": "risk_register",
                    "aggregation": "count",
                    "position_x": 9, "position_y": 0, "width": 3, "height": 1,
                },
                {
                    "name": "Risk Heatmap",
                    "widget_type": "heatmap",
                    "size": "wide",
                    "data_source": "risk_register",
                    "position_x": 0, "position_y": 2, "width": 8, "height": 4,
                },
                {
                    "name": "Risk Trend",
                    "widget_type": "chart",
                    "size": "large",
                    "chart_type": "area",
                    "data_source": "risk_register",
                    "position_x": 8, "position_y": 2, "width": 4, "height": 4,
                },
                {
                    "name": "Risk by Domain",
                    "widget_type": "chart",
                    "size": "medium",
                    "chart_type": "bar",
                    "data_source": "risk_register",
                    "position_x": 0, "position_y": 6, "width": 6, "height": 3,
                },
                {
                    "name": "Treatment Status",
                    "widget_type": "chart",
                    "size": "medium",
                    "chart_type": "doughnut",
                    "data_source": "risk_register",
                    "position_x": 6, "position_y": 6, "width": 6, "height": 3,
                },
            ],
            tags=["risk", "heatmap", "treatment"],
            author="GRC_Claw",
        )

    def _create_compliance_status(self) -> DashboardTemplate:
        return DashboardTemplate(
            name="Compliance Status",
            description="Real-time compliance posture across all frameworks",
            category="compliance",
            layout=DashboardLayout(columns=12, row_height=80, theme="light"),
            widget_configs=[
                {
                    "name": "Compliance Score",
                    "widget_type": "gauge",
                    "size": "medium",
                    "data_source": "compliance_framework",
                    "position_x": 0, "position_y": 0, "width": 3, "height": 2,
                },
                {
                    "name": "Compliant Controls",
                    "widget_type": "kpi",
                    "size": "small",
                    "data_source": "compliance_framework",
                    "aggregation": "count",
                    "position_x": 3, "position_y": 0, "width": 3, "height": 1,
                },
                {
                    "name": "Non-Compliant",
                    "widget_type": "kpi",
                    "size": "small",
                    "data_source": "compliance_framework",
                    "aggregation": "count",
                    "position_x": 6, "position_y": 0, "width": 3, "height": 1,
                },
                {
                    "name": "Pending Assessment",
                    "widget_type": "kpi",
                    "size": "small",
                    "data_source": "compliance_framework",
                    "aggregation": "count",
                    "position_x": 9, "position_y": 0, "width": 3, "height": 1,
                },
                {
                    "name": "Framework Coverage",
                    "widget_type": "chart",
                    "size": "large",
                    "chart_type": "radar",
                    "data_source": "compliance_framework",
                    "position_x": 0, "position_y": 2, "width": 6, "height": 4,
                },
                {
                    "name": "Compliance Trend",
                    "widget_type": "chart",
                    "size": "large",
                    "chart_type": "line",
                    "data_source": "compliance_framework",
                    "position_x": 6, "position_y": 2, "width": 6, "height": 4,
                },
                {
                    "name": "Framework Details",
                    "widget_type": "table",
                    "size": "full",
                    "data_source": "compliance_framework",
                    "position_x": 0, "position_y": 6, "width": 12, "height": 3,
                },
            ],
            tags=["compliance", "framework", "controls"],
            author="GRC_Claw",
        )

    def _create_operational_metrics(self) -> DashboardTemplate:
        return DashboardTemplate(
            name="Operational Metrics",
            description="Operational performance and efficiency metrics",
            category="operational",
            layout=DashboardLayout(columns=12, row_height=80, theme="light"),
            widget_configs=[
                {
                    "name": "Agent Uptime",
                    "widget_type": "kpi",
                    "size": "medium",
                    "data_source": "workflow",
                    "aggregation": "avg",
                    "position_x": 0, "position_y": 0, "width": 3, "height": 2,
                },
                {
                    "name": "Policy Evaluations",
                    "widget_type": "kpi",
                    "size": "medium",
                    "data_source": "policy_engine",
                    "aggregation": "count",
                    "position_x": 3, "position_y": 0, "width": 3, "height": 2,
                },
                {
                    "name": "Evidence Processed",
                    "widget_type": "kpi",
                    "size": "medium",
                    "data_source": "evidence_store",
                    "aggregation": "sum",
                    "position_x": 6, "position_y": 0, "width": 3, "height": 2,
                },
                {
                    "name": "Avg Response Time",
                    "widget_type": "kpi",
                    "size": "medium",
                    "data_source": "workflow",
                    "aggregation": "avg",
                    "position_x": 9, "position_y": 0, "width": 3, "height": 2,
                },
                {
                    "name": "Throughput Trend",
                    "widget_type": "chart",
                    "size": "large",
                    "chart_type": "area",
                    "data_source": "workflow",
                    "position_x": 0, "position_y": 2, "width": 6, "height": 3,
                },
                {
                    "name": "Error Rate",
                    "widget_type": "chart",
                    "size": "large",
                    "chart_type": "line",
                    "data_source": "workflow",
                    "position_x": 6, "position_y": 2, "width": 6, "height": 3,
                },
            ],
            tags=["operational", "performance", "efficiency"],
            author="GRC_Claw",
        )

    def _create_incident_response(self) -> DashboardTemplate:
        return DashboardTemplate(
            name="Incident Response",
            description="Active incidents and response status",
            category="operational",
            layout=DashboardLayout(columns=12, row_height=80, theme="light"),
            widget_configs=[
                {
                    "name": "Active Incidents",
                    "widget_type": "kpi",
                    "size": "medium",
                    "data_source": "incident",
                    "aggregation": "count",
                    "position_x": 0, "position_y": 0, "width": 3, "height": 2,
                },
                {
                    "name": "Critical Incidents",
                    "widget_type": "kpi",
                    "size": "medium",
                    "data_source": "incident",
                    "aggregation": "count",
                    "position_x": 3, "position_y": 0, "width": 3, "height": 2,
                },
                {
                    "name": "MTTR",
                    "widget_type": "kpi",
                    "size": "medium",
                    "data_source": "incident",
                    "aggregation": "avg",
                    "position_x": 6, "position_y": 0, "width": 3, "height": 2,
                },
                {
                    "name": "Resolved Today",
                    "widget_type": "kpi",
                    "size": "medium",
                    "data_source": "incident",
                    "aggregation": "count",
                    "position_x": 9, "position_y": 0, "width": 3, "height": 2,
                },
                {
                    "name": "Incident Feed",
                    "widget_type": "alert",
                    "size": "wide",
                    "data_source": "incident",
                    "position_x": 0, "position_y": 2, "width": 12, "height": 4,
                },
                {
                    "name": "Incident Timeline",
                    "widget_type": "chart",
                    "size": "full",
                    "chart_type": "bar",
                    "data_source": "incident",
                    "position_x": 0, "position_y": 6, "width": 12, "height": 3,
                },
            ],
            tags=["incident", "response", "operational"],
            author="GRC_Claw",
        )

    def _create_cost_governance(self) -> DashboardTemplate:
        return DashboardTemplate(
            name="Cost Governance",
            description="Cost analysis and optimization dashboard",
            category="operational",
            layout=DashboardLayout(columns=12, row_height=80, theme="light"),
            widget_configs=[
                {
                    "name": "Total Spend",
                    "widget_type": "kpi",
                    "size": "medium",
                    "data_source": "cost",
                    "aggregation": "sum",
                    "position_x": 0, "position_y": 0, "width": 3, "height": 2,
                },
                {
                    "name": "Cost per Agent",
                    "widget_type": "kpi",
                    "size": "medium",
                    "data_source": "cost",
                    "aggregation": "avg",
                    "position_x": 3, "position_y": 0, "width": 3, "height": 2,
                },
                {
                    "name": "Budget Utilization",
                    "widget_type": "gauge",
                    "size": "medium",
                    "data_source": "cost",
                    "position_x": 6, "position_y": 0, "width": 3, "height": 2,
                },
                {
                    "name": "Projected Spend",
                    "widget_type": "kpi",
                    "size": "medium",
                    "data_source": "cost",
                    "aggregation": "sum",
                    "position_x": 9, "position_y": 0, "width": 3, "height": 2,
                },
                {
                    "name": "Cost Breakdown",
                    "widget_type": "chart",
                    "size": "large",
                    "chart_type": "doughnut",
                    "data_source": "cost",
                    "position_x": 0, "position_y": 2, "width": 6, "height": 4,
                },
                {
                    "name": "Cost Trend",
                    "widget_type": "chart",
                    "size": "large",
                    "chart_type": "area",
                    "data_source": "cost",
                    "position_x": 6, "position_y": 2, "width": 6, "height": 4,
                },
            ],
            tags=["cost", "budget", "optimization"],
            author="GRC_Claw",
        )

    def _create_audit_readiness(self) -> DashboardTemplate:
        return DashboardTemplate(
            name="Audit Readiness",
            description="Audit preparation and findings tracking",
            category="compliance",
            layout=DashboardLayout(columns=12, row_height=80, theme="light"),
            widget_configs=[
                {
                    "name": "Readiness Score",
                    "widget_type": "gauge",
                    "size": "medium",
                    "data_source": "assessment",
                    "position_x": 0, "position_y": 0, "width": 3, "height": 2,
                },
                {
                    "name": "Open Findings",
                    "widget_type": "kpi",
                    "size": "medium",
                    "data_source": "assessment",
                    "aggregation": "count",
                    "position_x": 3, "position_y": 0, "width": 3, "height": 2,
                },
                {
                    "name": "Evidence Coverage",
                    "widget_type": "kpi",
                    "size": "medium",
                    "data_source": "evidence_store",
                    "aggregation": "avg",
                    "position_x": 6, "position_y": 0, "width": 3, "height": 2,
                },
                {
                    "name": "Days to Audit",
                    "widget_type": "kpi",
                    "size": "medium",
                    "data_source": "custom",
                    "position_x": 9, "position_y": 0, "width": 3, "height": 2,
                },
                {
                    "name": "Findings by Severity",
                    "widget_type": "chart",
                    "size": "large",
                    "chart_type": "bar",
                    "data_source": "assessment",
                    "position_x": 0, "position_y": 2, "width": 6, "height": 3,
                },
                {
                    "name": "Evidence Status",
                    "widget_type": "chart",
                    "size": "large",
                    "chart_type": "doughnut",
                    "data_source": "evidence_store",
                    "position_x": 6, "position_y": 2, "width": 6, "height": 3,
                },
                {
                    "name": "Recent Findings",
                    "widget_type": "table",
                    "size": "full",
                    "data_source": "assessment",
                    "position_x": 0, "position_y": 5, "width": 12, "height": 3,
                },
            ],
            tags=["audit", "readiness", "findings"],
            author="GRC_Claw",
        )

    def _create_framework_coverage(self) -> DashboardTemplate:
        return DashboardTemplate(
            name="Framework Coverage",
            description="Multi-framework compliance coverage matrix",
            category="compliance",
            layout=DashboardLayout(columns=12, row_height=80, theme="light"),
            widget_configs=[
                {
                    "name": "Overall Coverage",
                    "widget_type": "gauge",
                    "size": "medium",
                    "data_source": "compliance_framework",
                    "position_x": 0, "position_y": 0, "width": 3, "height": 2,
                },
                {
                    "name": "Frameworks Active",
                    "widget_type": "kpi",
                    "size": "small",
                    "data_source": "compliance_framework",
                    "aggregation": "count",
                    "position_x": 3, "position_y": 0, "width": 3, "height": 1,
                },
                {
                    "name": "Controls Mapped",
                    "widget_type": "kpi",
                    "size": "small",
                    "data_source": "compliance_framework",
                    "aggregation": "count",
                    "position_x": 6, "position_y": 0, "width": 3, "height": 1,
                },
                {
                    "name": "Gaps Identified",
                    "widget_type": "kpi",
                    "size": "small",
                    "data_source": "compliance_framework",
                    "aggregation": "count",
                    "position_x": 9, "position_y": 0, "width": 3, "height": 1,
                },
                {
                    "name": "Coverage Matrix",
                    "widget_type": "heatmap",
                    "size": "wide",
                    "data_source": "compliance_framework",
                    "position_x": 0, "position_y": 2, "width": 8, "height": 4,
                },
                {
                    "name": "Framework Radar",
                    "widget_type": "chart",
                    "size": "large",
                    "chart_type": "radar",
                    "data_source": "compliance_framework",
                    "position_x": 8, "position_y": 2, "width": 4, "height": 4,
                },
                {
                    "name": "Framework Details",
                    "widget_type": "table",
                    "size": "full",
                    "data_source": "compliance_framework",
                    "position_x": 0, "position_y": 6, "width": 12, "height": 3,
                },
            ],
            tags=["framework", "coverage", "compliance"],
            author="GRC_Claw",
        )


class TemplateRegistry:
    """
    Registry for managing and discovering dashboard templates.
    Supports template versioning and metadata.
    """

    def __init__(self):
        self._templates: dict[str, DashboardTemplate] = {}
        self._metadata: dict[str, dict[str, Any]] = {}

    def register(
        self,
        template: DashboardTemplate,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Register a template with optional metadata."""
        self._templates[template.name] = template
        self._metadata[template.name] = metadata or {
            "registered_at": datetime.now(UTC).isoformat(),
            "version": template.version,
            "author": template.author,
        }

    def get(self, name: str) -> DashboardTemplate | None:
        """Retrieve a template by name."""
        return self._templates.get(name)

    def get_metadata(self, name: str) -> dict[str, Any] | None:
        """Retrieve metadata for a template."""
        return self._metadata.get(name)

    def list_all(self) -> list[str]:
        """List all registered template names."""
        return list(self._templates.keys())

    def list_by_category(self, category: str) -> list[DashboardTemplate]:
        """List templates in a specific category."""
        return [t for t in self._templates.values() if t.category == category]

    def search(self, query: str) -> list[DashboardTemplate]:
        """Search templates by name, description, or tags."""
        query_lower = query.lower()
        results = []
        for template in self._templates.values():
            if (query_lower in template.name.lower()
                    or query_lower in template.description.lower()
                    or any(query_lower in tag.lower() for tag in template.tags)):
                results.append(template)
        return results

    def unregister(self, name: str) -> bool:
        """Remove a template from the registry."""
        if name in self._templates:
            del self._templates[name]
            self._metadata.pop(name, None)
            return True
        return False
