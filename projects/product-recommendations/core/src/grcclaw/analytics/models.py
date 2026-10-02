"""
Data models for the GRC_Claw analytics and BI framework.

Defines the core data structures for metrics, KPIs, trends,
predictions, and executive reports across all 8 metric categories
and 12 agentic AI metrics.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

# ─── Enums ───────────────────────────────────────────────────────────────────


class MetricCategory(str, Enum):
    """Eight metric categories from the unified metrics layer."""

    ASSET_INVENTORY = "asset_inventory"
    RISK_COMPLIANCE = "risk_compliance"
    OPERATIONAL_PERFORMANCE = "operational_performance"
    INCIDENT_MANAGEMENT = "incident_management"
    REMEDIATION_IMPROVEMENT = "remediation_improvement"
    THIRD_PARTY_RISK = "third_party_risk"
    ECONOMIC_VALUE = "economic_value"
    CULTURE_TRAINING_ETHICS = "culture_training_ethics"
    AGENTIC_AI = "agentic_ai"


class MetricTier(str, Enum):
    """Three-tier escalation framework."""

    TIER_1_OPERATIONAL = "tier_1_operational"
    TIER_2_MANAGEMENT = "tier_2_management"
    TIER_3_BOARD = "tier_3_board"


class RAGStatus(str, Enum):
    """Red/Amber/Green status with critical extension."""

    GREEN = "green"
    AMBER = "amber"
    RED = "red"
    CRITICAL = "critical"


class DashboardLayer(str, Enum):
    """Three-layer dashboard architecture."""

    EXECUTIVE = "executive"
    PROGRAM = "program"
    OPERATING = "operating"


class TrendDirection(str, Enum):
    """Direction of a metric trend."""

    IMPROVING = "improving"
    STABLE = "stable"
    DEGRADING = "degrading"
    VOLATILE = "volatile"


class PredictionConfidence(str, Enum):
    """Confidence level for predictions."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ReportType(str, Enum):
    """Types of executive reports."""

    BOARD_COMPLIANCE_SUMMARY = "board_compliance_summary"
    EXECUTIVE_RISK_DASHBOARD = "executive_risk_dashboard"
    PROGRAM_STATUS_REPORT = "program_status_report"
    OPERATIONAL_COMPLIANCE_VIEW = "operational_compliance_view"
    REGULATORY_EVIDENCE_PACK = "regulatory_evidence_pack"
    INCIDENT_REPORT = "incident_report"
    TRANSPARENCY_REPORT = "transparency_report"
    VENDOR_RISK_ASSESSMENT = "vendor_risk_assessment"


class ReportFrequency(str, Enum):
    """Report delivery frequency."""

    REALTIME = "realtime"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUALLY = "annually"
    ON_DEMAND = "on_demand"


class ForecastMethod(str, Enum):
    """Forecasting methods for predictive analytics."""

    LINEAR_REGRESSION = "linear_regression"
    MOVING_AVERAGE = "moving_average"
    EXPONENTIAL_SMOOTHING = "exponential_smoothing"
    SEASONAL_DECOMPOSITION = "seasonal_decomposition"
    MONTE_CARLO = "monte_carlo"


# ─── Core Models ─────────────────────────────────────────────────────────────


@dataclass
class MetricDefinition:
    """Definition of a single metric from the unified metrics layer."""

    metric_id: str
    name: str
    category: MetricCategory
    description: str
    formula: str
    unit: str
    target: float
    tier1_threshold: float
    tier2_threshold: float
    tier3_threshold: float
    tier1_direction: str = "lte"  # lte, gte, eq
    tier2_direction: str = "lte"
    tier3_direction: str = "lte"
    measurement_frequency: str = "daily"
    dashboard_layers: list[DashboardLayer] = field(default_factory=lambda: [
        DashboardLayer.PROGRAM
    ])
    owner_role: str = ""
    data_sources: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "metric_id": self.metric_id,
            "name": self.name,
            "category": self.category.value,
            "description": self.description,
            "formula": self.formula,
            "unit": self.unit,
            "target": self.target,
            "tier1_threshold": self.tier1_threshold,
            "tier2_threshold": self.tier2_threshold,
            "tier3_threshold": self.tier3_threshold,
            "tier1_direction": self.tier1_direction,
            "tier2_direction": self.tier2_direction,
            "tier3_direction": self.tier3_direction,
            "measurement_frequency": self.measurement_frequency,
            "dashboard_layers": [layer.value for layer in self.dashboard_layers],
            "owner_role": self.owner_role,
            "data_sources": self.data_sources,
            "tags": self.tags,
        }


@dataclass
class MetricValue:
    """A measured value for a metric at a point in time."""

    metric_id: str
    value: float
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    period: str = ""
    numerator: float | None = None
    denominator: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    source: str = ""
    confidence: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "metric_id": self.metric_id,
            "value": self.value,
            "timestamp": self.timestamp,
            "period": self.period,
            "numerator": self.numerator,
            "denominator": self.denominator,
            "metadata": self.metadata,
            "source": self.source,
            "confidence": self.confidence,
        }


@dataclass
class MetricSnapshot:
    """Complete snapshot of a metric with RAG status and trend."""

    metric_id: str
    name: str
    category: MetricCategory
    current_value: float
    previous_value: float
    target: float
    rag_status: RAGStatus
    trend_direction: TrendDirection
    trend_pct: float
    tier: MetricTier
    unit: str
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    period: str = ""
    owner: str = ""
    dashboard_layers: list[DashboardLayer] = field(default_factory=list)
    history: list[MetricValue] = field(default_factory=list)
    escalation_required: bool = False
    escalation_tier: MetricTier | None = None
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "metric_id": self.metric_id,
            "name": self.name,
            "category": self.category.value,
            "current_value": self.current_value,
            "previous_value": self.previous_value,
            "target": self.target,
            "rag_status": self.rag_status.value,
            "trend_direction": self.trend_direction.value,
            "trend_pct": self.trend_pct,
            "tier": self.tier.value,
            "unit": self.unit,
            "timestamp": self.timestamp,
            "period": self.period,
            "owner": self.owner,
            "dashboard_layers": [layer.value for layer in self.dashboard_layers],
            "history": [h.to_dict() for h in self.history],
            "escalation_required": self.escalation_required,
            "escalation_tier": self.escalation_tier.value if self.escalation_tier else None,
            "notes": self.notes,
        }


@dataclass
class KPISummary:
    """Aggregated KPI summary for a dashboard layer."""

    layer: DashboardLayer
    total_metrics: int = 0
    green_count: int = 0
    amber_count: int = 0
    red_count: int = 0
    critical_count: int = 0
    overall_score: float = 0.0
    metrics: list[MetricSnapshot] = field(default_factory=list)
    top_risks: list[dict[str, Any]] = field(default_factory=list)
    decisions_required: list[dict[str, Any]] = field(default_factory=list)
    period: str = ""
    generated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    @property
    def health_pct(self) -> float:
        if self.total_metrics == 0:
            return 0.0
        return round((self.green_count / self.total_metrics) * 100, 1)

    def to_dict(self) -> dict[str, Any]:
        return {
            "layer": self.layer.value,
            "total_metrics": self.total_metrics,
            "green_count": self.green_count,
            "amber_count": self.amber_count,
            "red_count": self.red_count,
            "critical_count": self.critical_count,
            "overall_score": self.overall_score,
            "health_pct": self.health_pct,
            "metrics": [m.to_dict() for m in self.metrics],
            "top_risks": self.top_risks,
            "decisions_required": self.decisions_required,
            "period": self.period,
            "generated_at": self.generated_at,
        }


@dataclass
class TrendAnalysis:
    """Trend analysis result for a metric over time."""

    metric_id: str
    metric_name: str
    category: MetricCategory
    direction: TrendDirection
    slope: float
    intercept: float
    r_squared: float
    p_value: float
    data_points: int
    period_start: str = ""
    period_end: str = ""
    change_pct: float = 0.0
    volatility: float = 0.0
    seasonality_detected: bool = False
    seasonality_period: int | None = None
    change_points: list[dict[str, Any]] = field(default_factory=list)
    forecast_next: float | None = None
    forecast_confidence: float = 0.0
    insights: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "metric_id": self.metric_id,
            "metric_name": self.metric_name,
            "category": self.category.value,
            "direction": self.direction.value,
            "slope": self.slope,
            "intercept": self.intercept,
            "r_squared": self.r_squared,
            "p_value": self.p_value,
            "data_points": self.data_points,
            "period_start": self.period_start,
            "period_end": self.period_end,
            "change_pct": self.change_pct,
            "volatility": self.volatility,
            "seasonality_detected": self.seasonality_detected,
            "seasonality_period": self.seasonality_period,
            "change_points": self.change_points,
            "forecast_next": self.forecast_next,
            "forecast_confidence": self.forecast_confidence,
            "insights": self.insights,
        }


@dataclass
class Prediction:
    """A single prediction/forecast data point."""

    period: str
    predicted_value: float
    lower_bound: float
    upper_bound: float
    confidence: float = 0.95
    method: ForecastMethod = ForecastMethod.LINEAR_REGRESSION
    assumptions: list[str] = field(default_factory=list)
    risk_factors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "period": self.period,
            "predicted_value": self.predicted_value,
            "lower_bound": self.lower_bound,
            "upper_bound": self.upper_bound,
            "confidence": self.confidence,
            "method": self.method.value,
            "assumptions": self.assumptions,
            "risk_factors": self.risk_factors,
        }


@dataclass
class PredictiveModel:
    """Complete predictive model for a metric."""

    metric_id: str
    metric_name: str
    category: MetricCategory
    method: ForecastMethod
    confidence_level: PredictionConfidence
    model_accuracy: float
    training_data_points: int
    predictions: list[Prediction] = field(default_factory=list)
    feature_importance: dict[str, float] = field(default_factory=dict)
    model_metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    valid_until: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "metric_id": self.metric_id,
            "metric_name": self.metric_name,
            "category": self.category.value,
            "method": self.method.value,
            "confidence_level": self.confidence_level.value,
            "model_accuracy": self.model_accuracy,
            "training_data_points": self.training_data_points,
            "predictions": [p.to_dict() for p in self.predictions],
            "feature_importance": self.feature_importance,
            "model_metadata": self.model_metadata,
            "created_at": self.created_at,
            "valid_until": self.valid_until,
        }


@dataclass
class ReportSection:
    """A section within an executive report."""

    title: str
    content: str = ""
    metrics: list[MetricSnapshot] = field(default_factory=list)
    tables: list[dict[str, Any]] = field(default_factory=list)
    charts: list[dict[str, Any]] = field(default_factory=list)
    insights: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    order: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "content": self.content,
            "metrics": [m.to_dict() for m in self.metrics],
            "tables": self.tables,
            "charts": self.charts,
            "insights": self.insights,
            "recommendations": self.recommendations,
            "order": self.order,
        }


@dataclass
class ExecutiveReport:
    """Complete executive report."""

    report_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12].upper())
    report_type: ReportType = ReportType.BOARD_COMPLIANCE_SUMMARY
    title: str = ""
    frequency: ReportFrequency = ReportFrequency.QUARTERLY
    audience: list[str] = field(default_factory=list)
    period: str = ""
    generated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    valid_until: str = ""
    sections: list[ReportSection] = field(default_factory=list)
    summary: str = ""
    overall_rag_status: RAGStatus = RAGStatus.GREEN
    compliance_scores: dict[str, float] = field(default_factory=dict)
    material_risks: list[dict[str, Any]] = field(default_factory=list)
    decisions_required: list[dict[str, Any]] = field(default_factory=list)
    trend_charts: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "report_type": self.report_type.value,
            "title": self.title,
            "frequency": self.frequency.value,
            "audience": self.audience,
            "period": self.period,
            "generated_at": self.generated_at,
            "valid_until": self.valid_until,
            "sections": [s.to_dict() for s in self.sections],
            "summary": self.summary,
            "overall_rag_status": self.overall_rag_status.value,
            "compliance_scores": self.compliance_scores,
            "material_risks": self.material_risks,
            "decisions_required": self.decisions_required,
            "trend_charts": self.trend_charts,
            "metadata": self.metadata,
        }


@dataclass
class AnalyticsEvent:
    """An analytics event for real-time processing."""

    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str = ""
    metric_id: str = ""
    category: MetricCategory = MetricCategory.RISK_COMPLIANCE
    value: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    source: str = ""
    entity_id: str = ""
    entity_type: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "metric_id": self.metric_id,
            "category": self.category.value,
            "value": self.value,
            "timestamp": self.timestamp,
            "source": self.source,
            "entity_id": self.entity_id,
            "entity_type": self.entity_type,
            "metadata": self.metadata,
            "tags": self.tags,
        }


@dataclass
class BenchmarkComparison:
    """Comparison of a metric against industry benchmarks."""

    metric_id: str
    metric_name: str
    internal_value: float
    industry_avg: float
    industry_best: float
    industry_worst: float
    percentile: float
    gap_to_best: float
    gap_to_avg: float
    trend_vs_industry: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "metric_id": self.metric_id,
            "metric_name": self.metric_name,
            "internal_value": self.internal_value,
            "industry_avg": self.industry_avg,
            "industry_best": self.industry_best,
            "industry_worst": self.industry_worst,
            "percentile": self.percentile,
            "gap_to_best": self.gap_to_best,
            "gap_to_avg": self.gap_to_avg,
            "trend_vs_industry": self.trend_vs_industry,
        }
