"""
Data models for the GRC_Claw governance dashboard and reporting system.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
import uuid


# ─── Enums ───────────────────────────────────────────────────────────────────

class WidgetType(str, Enum):
    KPI = "kpi"
    CHART = "chart"
    TABLE = "table"
    ALERT = "alert"
    TEXT = "text"
    HEATMAP = "heatmap"
    GAUGE = "gauge"
    SPARKLINE = "sparkline"
    TIMELINE = "timeline"
    TREEMAP = "treemap"


class WidgetSize(str, Enum):
    SMALL = "small"       # 1x1 grid
    MEDIUM = "medium"     # 2x1 grid
    LARGE = "large"       # 2x2 grid
    FULL = "full"         # 4x1 grid
    WIDE = "wide"         # 4x2 grid


class ChartType(str, Enum):
    LINE = "line"
    BAR = "bar"
    PIE = "pie"
    DOUGHNUT = "doughnut"
    AREA = "area"
    SCATTER = "scatter"
    RADAR = "radar"
    BUBBLE = "bubble"
    FUNNEL = "funnel"


class ReportFormat(str, Enum):
    JSON = "json"
    CSV = "csv"
    MARKDOWN = "markdown"
    HTML = "html"
    PDF = "pdf"
    EXCEL = "excel"


class ReportFrequency(str, Enum):
    REALTIME = "realtime"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"
    ON_DEMAND = "on_demand"


class DataSourceType(str, Enum):
    RISK_REGISTER = "risk_register"
    COMPLIANCE_FRAMEWORK = "compliance_framework"
    POLICY_ENGINE = "policy_engine"
    EVIDENCE_STORE = "evidence_store"
    AUDIT_LOG = "audit_log"
    ASSESSMENT = "assessment"
    INCIDENT = "incident"
    WORKFLOW = "workflow"
    COST = "cost"
    NOTIFICATION = "notification"
    CUSTOM = "custom"


class AlertLevel(str, Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TimeRange(str, Enum):
    LAST_1H = "last_1h"
    LAST_6H = "last_6h"
    LAST_24H = "last_24h"
    LAST_7D = "last_7d"
    LAST_30D = "last_30d"
    LAST_90D = "last_90d"
    LAST_6M = "last_6m"
    LAST_1Y = "last_1y"
    YTD = "ytd"
    ALL_TIME = "all_time"
    CUSTOM = "custom"


class MetricAggregation(str, Enum):
    COUNT = "count"
    SUM = "sum"
    AVG = "avg"
    MIN = "min"
    MAX = "max"
    MEDIAN = "median"
    P95 = "p95"
    P99 = "p99"
    RATE = "rate"
    RATIO = "ratio"
    DISTINCT = "distinct"


class TrendDirection(str, Enum):
    UP = "up"
    DOWN = "down"
    FLAT = "flat"
    UNKNOWN = "unknown"


class ComplianceStatus(str, Enum):
    COMPLIANT = "compliant"
    PARTIALLY_COMPLIANT = "partially_compliant"
    NON_COMPLIANT = "non_compliant"
    NOT_ASSESSED = "not_assessed"
    EXEMPT = "exempt"


class RiskLevel(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    MINIMAL = "minimal"


# ─── Core Models ─────────────────────────────────────────────────────────────

@dataclass
class FilterCriteria:
    """Filter criteria for dashboard data queries."""

    field: str = ""
    operator: str = "eq"  # eq, neq, gt, gte, lt, lte, in, nin, contains, starts_with, ends_with
    value: Any = None
    values: list[Any] = field(default_factory=list)
    time_range: TimeRange = TimeRange.LAST_30D
    custom_start: Optional[str] = None
    custom_end: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    frameworks: list[str] = field(default_factory=list)
    domains: list[str] = field(default_factory=list)
    categories: list[str] = field(default_factory=list)
    statuses: list[str] = field(default_factory=list)
    owners: list[str] = field(default_factory=list)
    severity_levels: list[AlertLevel] = field(default_factory=list)


@dataclass
class GovernanceScore:
    """Overall governance health score."""

    overall: float = 0.0
    governance: float = 0.0
    risk: float = 0.0
    compliance: float = 0.0
    operational: float = 0.0
    security: float = 0.0
    trend: TrendDirection = TrendDirection.UNKNOWN
    change_pct: float = 0.0
    period: str = ""
    calculated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    breakdown: dict[str, float] = field(default_factory=dict)
    recommendations: list[str] = field(default_factory=list)


@dataclass
class DashboardWidget:
    """A single widget on the dashboard."""

    id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    name: str = ""
    description: str = ""
    widget_type: WidgetType = WidgetType.KPI
    size: WidgetSize = WidgetSize.MEDIUM
    chart_type: Optional[ChartType] = None
    data_source: DataSourceType = DataSourceType.CUSTOM
    data_query: dict[str, Any] = field(default_factory=dict)
    filters: list[FilterCriteria] = field(default_factory=list)
    aggregation: MetricAggregation = MetricAggregation.COUNT
    refresh_interval_seconds: int = 300
    position_x: int = 0
    position_y: int = 0
    width: int = 2
    height: int = 1
    config: dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    tags: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_refreshed: Optional[str] = None
    cached_data: Any = None
    cache_ttl_seconds: int = 60

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "widget_type": self.widget_type.value,
            "size": self.size.value,
            "chart_type": self.chart_type.value if self.chart_type else None,
            "data_source": self.data_source.value,
            "data_query": self.data_query,
            "filters": [
                {
                    "field": f.field,
                    "operator": f.operator,
                    "value": f.value,
                    "time_range": f.time_range.value,
                }
                for f in self.filters
            ],
            "aggregation": self.aggregation.value,
            "refresh_interval_seconds": self.refresh_interval_seconds,
            "position": {"x": self.position_x, "y": self.position_y},
            "dimensions": {"width": self.width, "height": self.height},
            "config": self.config,
            "enabled": self.enabled,
            "tags": self.tags,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "last_refreshed": self.last_refreshed,
        }


@dataclass
class KPIWidget:
    """Key Performance Indicator widget configuration."""

    widget: DashboardWidget = field(default_factory=DashboardWidget)
    metric_name: str = ""
    metric_unit: str = ""
    target_value: Optional[float] = None
    warning_threshold: Optional[float] = None
    critical_threshold: Optional[float] = None
    comparison_mode: str = "none"  # none, previous_period, target, baseline
    show_sparkline: bool = True
    show_trend: bool = True
    format_string: str = "{:,.0f}"
    color_positive: str = "#22c55e"
    color_negative: str = "#ef4444"
    color_neutral: str = "#6b7280"


@dataclass
class ChartWidget:
    """Chart widget configuration."""

    widget: DashboardWidget = field(default_factory=DashboardWidget)
    chart_type: ChartType = ChartType.LINE
    x_axis_field: str = ""
    y_axis_field: str = ""
    series_field: str = ""
    stacked: bool = False
    show_legend: bool = True
    show_tooltips: bool = True
    show_grid: bool = True
    color_palette: list[str] = field(default_factory=lambda: [
        "#3b82f6", "#22c55e", "#f59e0b", "#ef4444", "#8b5cf6",
        "#06b6d4", "#ec4899", "#f97316", "#14b8a6", "#6366f1",
    ])
    y_axis_min: Optional[float] = None
    y_axis_max: Optional[float] = None
    smooth_lines: bool = True
    fill_area: bool = False


@dataclass
class TableWidget:
    """Table widget configuration."""

    widget: DashboardWidget = field(default_factory=DashboardWidget)
    columns: list[dict[str, Any]] = field(default_factory=list)
    sortable: bool = True
    filterable: bool = True
    paginated: bool = True
    page_size: int = 25
    show_row_numbers: bool = True
    sticky_header: bool = True
    column_widths: dict[str, int] = field(default_factory=dict)
    row_actions: list[dict[str, Any]] = field(default_factory=list)
    conditional_formatting: list[dict[str, Any]] = field(default_factory=list)
    export_enabled: bool = True
    group_by: str = ""
    sort_by: str = ""
    sort_order: str = "desc"


@dataclass
class AlertWidget:
    """Alert/notification widget configuration."""

    widget: DashboardWidget = field(default_factory=DashboardWidget)
    alert_levels: list[AlertLevel] = field(default_factory=lambda: [
        AlertLevel.HIGH, AlertLevel.CRITICAL
    ])
    show_acknowledged: bool = False
    show_resolved: bool = False
    group_by: str = "severity"
    max_items: int = 50
    auto_refresh: bool = True
    sound_enabled: bool = False
    color_map: dict[str, str] = field(default_factory=lambda: {
        "critical": "#ef4444",
        "high": "#f97316",
        "medium": "#f59e0b",
        "low": "#3b82f6",
        "info": "#6b7280",
    })


@dataclass
class TextWidget:
    """Text/markdown content widget."""

    widget: DashboardWidget = field(default_factory=DashboardWidget)
    content: str = ""
    content_type: str = "markdown"  # markdown, html, plain
    auto_scroll: bool = False
    font_size: str = "medium"  # small, medium, large
    text_align: str = "left"  # left, center, right


@dataclass
class DashboardLayout:
    """Layout configuration for a dashboard."""

    columns: int = 12
    row_height: int = 80
    gutter: int = 16
    padding: int = 24
    responsive_breakpoints: dict[str, int] = field(default_factory=lambda: {
        "xs": 1,
        "sm": 2,
        "md": 4,
        "lg": 6,
        "xl": 8,
        "xxl": 12,
    })
    theme: str = "light"  # light, dark, auto
    custom_css: str = ""
    header_config: dict[str, Any] = field(default_factory=dict)
    footer_config: dict[str, Any] = field(default_factory=dict)


@dataclass
class DashboardConfig:
    """Complete dashboard configuration."""

    id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    name: str = ""
    description: str = ""
    category: str = "general"  # general, risk, compliance, operational, executive
    layout: DashboardLayout = field(default_factory=DashboardLayout)
    widgets: list[DashboardWidget] = field(default_factory=list)
    filters: list[FilterCriteria] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    owner: str = ""
    is_public: bool = False
    is_default: bool = False
    parent_dashboard_id: Optional[str] = None
    version: int = 1
    enabled: bool = True
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_accessed: Optional[str] = None
    access_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
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
            "widgets": [w.to_dict() for w in self.widgets],
            "filters": [
                {
                    "field": f.field,
                    "operator": f.operator,
                    "value": f.value,
                    "time_range": f.time_range.value,
                }
                for f in self.filters
            ],
            "tags": self.tags,
            "owner": self.owner,
            "is_public": self.is_public,
            "is_default": self.is_default,
            "version": self.version,
            "enabled": self.enabled,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "access_count": self.access_count,
        }


@dataclass
class DashboardSnapshot:
    """Point-in-time snapshot of dashboard data."""

    snapshot_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    dashboard_id: str = ""
    dashboard_name: str = ""
    captured_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    widget_data: dict[str, Any] = field(default_factory=dict)
    governance_score: Optional[GovernanceScore] = None
    summary: dict[str, Any] = field(default_factory=dict)
    alerts: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ReportDefinition:
    """Definition of a report."""

    id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    name: str = ""
    description: str = ""
    category: str = "general"
    report_format: ReportFormat = ReportFormat.MARKDOWN
    frequency: ReportFrequency = ReportFrequency.ON_DEMAND
    data_sources: list[DataSourceType] = field(default_factory=list)
    sections: list[dict[str, Any]] = field(default_factory=list)
    filters: list[FilterCriteria] = field(default_factory=list)
    parameters: dict[str, Any] = field(default_factory=dict)
    template: str = ""
    output_path: str = ""
    recipients: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    owner: str = ""
    enabled: bool = True
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_generated: Optional[str] = None
    generation_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "report_format": self.report_format.value,
            "frequency": self.frequency.value,
            "data_sources": [ds.value for ds in self.data_sources],
            "sections": self.sections,
            "parameters": self.parameters,
            "template": self.template,
            "output_path": self.output_path,
            "recipients": self.recipients,
            "tags": self.tags,
            "owner": self.owner,
            "enabled": self.enabled,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "last_generated": self.last_generated,
            "generation_count": self.generation_count,
        }


@dataclass
class ReportSchedule:
    """Schedule configuration for automated report generation."""

    id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    report_id: str = ""
    report_name: str = ""
    frequency: ReportFrequency = ReportFrequency.WEEKLY
    cron_expression: str = ""
    next_run: Optional[str] = None
    last_run: Optional[str] = None
    last_status: str = ""  # pending, running, success, failed
    last_error: Optional[str] = None
    enabled: bool = True
    recipients: list[str] = field(default_factory=list)
    output_formats: list[ReportFormat] = field(default_factory=lambda: [ReportFormat.MARKDOWN])
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class ReportOutput:
    """Generated report output."""

    output_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    report_id: str = ""
    report_name: str = ""
    format: ReportFormat = ReportFormat.MARKDOWN
    content: str = ""
    file_path: Optional[str] = None
    file_size: int = 0
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    generated_by: str = ""
    parameters: dict[str, Any] = field(default_factory=dict)
    execution_time_ms: float = 0.0
    success: bool = True
    error: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)
