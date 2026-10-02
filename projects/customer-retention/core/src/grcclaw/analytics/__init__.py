"""
GRC_Claw Analytics & Business Intelligence Framework

Comprehensive analytics, KPI dashboards, trend analysis, predictive analytics,
and executive reporting for GRC (Governance, Risk, Compliance) AI agents.

Modules:
    models: Core data models for metrics, KPIs, trends, predictions, reports
    metrics_registry: All 40+ metrics from the unified metrics layer
    engine: Analytics engine for RAG status, escalation, and KPI computation
    dashboard: Three-layer dashboard (Executive, Program, Operating)
    trend_analysis: Statistical trend detection and forecasting
    predictive: Predictive analytics, Monte Carlo, risk prediction, anomaly detection
    reporting: Board-ready executive report generation
"""

from .models import (
    MetricCategory,
    MetricTier,
    RAGStatus,
    DashboardLayer,
    TrendDirection,
    PredictionConfidence,
    ReportType,
    ReportFrequency,
    ForecastMethod,
    MetricDefinition,
    MetricValue,
    MetricSnapshot,
    KPISummary,
    TrendAnalysis,
    Prediction,
    PredictiveModel,
    ReportSection,
    ExecutiveReport,
    AnalyticsEvent,
    BenchmarkComparison,
)
from .metrics_registry import (
    ALL_METRICS,
    METRICS_BY_ID,
    METRICS_BY_CATEGORY,
    UC1_METRICS,
    UC2_METRICS,
    UC3_METRICS,
    UC4_METRICS,
    UC5_METRICS,
    UC6_METRICS,
    UC7_METRICS,
    UC8_METRICS,
    AG_METRICS,
    get_metric,
    get_metrics_by_category,
    get_metrics_by_layer,
    get_executive_metrics,
    get_program_metrics,
    get_operating_metrics,
    get_agentic_metrics,
)
from .engine import AnalyticsEngine, RAGStatusEngine, TrendEngine
from .dashboard import (
    DashboardManager,
    ExecutiveDashboard,
    ProgramDashboard,
    OperatingDashboard,
    DashboardWidget,
)
from .trend_analysis import (
    TrendAnalyzer,
    LinearRegression,
    MovingAverage,
    ExponentialSmoothing,
    SeasonalDecomposition,
    ChangePointDetector,
)
from .predictive import (
    PredictiveAnalyticsEngine,
    MonteCarloSimulator,
    AnomalyDetector,
    RiskPredictor,
    WhatIfAnalyzer,
)
from .reporting import (
    ReportGenerator,
    BoardComplianceSummary,
    RegulatoryEvidencePack,
    ProgramStatusReport,
    TransparencyReport,
    ReportTemplate,
)

__all__ = [
    # Models
    "MetricCategory",
    "MetricTier",
    "RAGStatus",
    "DashboardLayer",
    "TrendDirection",
    "PredictionConfidence",
    "ReportType",
    "ReportFrequency",
    "ForecastMethod",
    "MetricDefinition",
    "MetricValue",
    "MetricSnapshot",
    "KPISummary",
    "TrendAnalysis",
    "Prediction",
    "PredictiveModel",
    "ReportSection",
    "ExecutiveReport",
    "AnalyticsEvent",
    "BenchmarkComparison",
    # Registry
    "ALL_METRICS",
    "METRICS_BY_ID",
    "METRICS_BY_CATEGORY",
    "UC1_METRICS",
    "UC2_METRICS",
    "UC3_METRICS",
    "UC4_METRICS",
    "UC5_METRICS",
    "UC6_METRICS",
    "UC7_METRICS",
    "UC8_METRICS",
    "AG_METRICS",
    "get_metric",
    "get_metrics_by_category",
    "get_metrics_by_layer",
    "get_executive_metrics",
    "get_program_metrics",
    "get_operating_metrics",
    "get_agentic_metrics",
    # Engine
    "AnalyticsEngine",
    "RAGStatusEngine",
    "TrendEngine",
    # Dashboard
    "DashboardManager",
    "ExecutiveDashboard",
    "ProgramDashboard",
    "OperatingDashboard",
    "DashboardWidget",
    # Trend Analysis
    "TrendAnalyzer",
    "LinearRegression",
    "MovingAverage",
    "ExponentialSmoothing",
    "SeasonalDecomposition",
    "ChangePointDetector",
    # Predictive
    "PredictiveAnalyticsEngine",
    "MonteCarloSimulator",
    "AnomalyDetector",
    "RiskPredictor",
    "WhatIfAnalyzer",
    # Reporting
    "ReportGenerator",
    "BoardComplianceSummary",
    "RegulatoryEvidencePack",
    "ProgramStatusReport",
    "TransparencyReport",
    "ReportTemplate",
]
