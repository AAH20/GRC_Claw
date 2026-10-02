"""Shared data models and types for the Sales Forecaster."""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from datetime import datetime


class DataSource(StrEnum):
    """Supported data sources."""

    SALESFORCE = "salesforce"
    HUBSPOT = "hubspot"
    SAP = "sap"


class ForecastPeriod(StrEnum):
    """Forecast time periods."""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"


class PipelineStage(StrEnum):
    """Pipeline execution stages."""

    DATA_COLLECTION = "data_collection"
    ANALYSIS = "analysis"
    PREDICTION = "prediction"
    ACTION = "action"
    PERFORMANCE_ANALYTICS = "performance_analytics"


class PipelineStatus(StrEnum):
    """Pipeline run status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class HealthStatus(StrEnum):
    """Health check status."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class SalesRecord(BaseModel):
    """A single sales record from any source."""

    id: str
    source: DataSource
    amount: float
    currency: str = "USD"
    date: datetime
    customer_id: str | None = None
    product_id: str | None = None
    region: str | None = None
    sales_rep_id: str | None = None
    stage: str | None = None
    probability: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ForecastPoint(BaseModel):
    """A single forecast data point."""

    date: datetime
    value: float
    lower_bound: float
    upper_bound: float
    confidence: float


class ForecastResult(BaseModel):
    """Complete forecast result."""

    id: str
    created_at: datetime
    period: ForecastPeriod
    horizon_days: int
    points: list[ForecastPoint]
    model_used: str
    mape: float | None = None
    rmse: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class AnalysisResult(BaseModel):
    """Result from the analysis agent."""

    trend: str
    seasonality_detected: bool
    seasonality_period: int | None = None
    anomalies: list[dict[str, Any]] = Field(default_factory=list)
    changepoints: list[datetime] = Field(default_factory=list)
    summary_statistics: dict[str, float] = Field(default_factory=dict)
    insights: list[str] = Field(default_factory=list)


class ActionRecommendation(BaseModel):
    """A recommended action from the action agent."""

    id: str
    priority: int = Field(ge=1, le=5)
    category: str
    title: str
    description: str
    expected_impact: float
    confidence: float
    due_date: datetime | None = None
    assigned_to: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class PerformanceMetrics(BaseModel):
    """Performance metrics from the analytics agent."""

    period_start: datetime
    period_end: datetime
    total_revenue: float
    forecast_accuracy: float
    bias: float
    mape: float
    rmse: float
    kpis: dict[str, float] = Field(default_factory=dict)
    alerts: list[dict[str, Any]] = Field(default_factory=list)


class PipelineRun(BaseModel):
    """A pipeline execution run."""

    id: str
    status: PipelineStatus
    started_at: datetime
    completed_at: datetime | None = None
    stages: dict[PipelineStage, dict[str, Any]] = Field(default_factory=dict)
    error: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """Standard API response wrapper."""

    success: bool
    data: T | None = None
    error: str | None = None
    request_id: str | None = None


class HealthCheck(BaseModel):
    """Health check response."""

    status: HealthStatus
    version: str
    timestamp: datetime
    checks: dict[str, bool] = Field(default_factory=dict)
    uptime_seconds: float | None = None
