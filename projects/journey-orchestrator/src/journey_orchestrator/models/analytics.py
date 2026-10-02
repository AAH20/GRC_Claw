"""Analytics data models for the Journey Orchestrator."""
from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class MetricType(StrEnum):
    """Types of journey metrics."""

    CONVERSION_RATE = "conversion_rate"
    ENGAGEMENT_RATE = "engagement_rate"
    OPEN_RATE = "open_rate"
    CLICK_RATE = "click_rate"
    REVENUE_PER_CUSTOMER = "revenue_per_customer"
    CHURN_RATE = "churn_rate"
    RETENTION_RATE = "retention_rate"
    CUSTOM = "custom"


class JourneyMetric(BaseModel):
    """A single metric measurement for a journey."""

    metric_type: MetricType
    value: float = Field(..., ge=0.0, description="Metric value")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(datetime.now().astimezone().tzinfo)
    )
    segment: str = "all"
    metadata: dict[str, Any] = Field(default_factory=dict)


class JourneyPerformance(BaseModel):
    """Aggregated performance data for a journey."""

    journey_id: str
    total_customers: int = Field(default=0, ge=0)
    converted_customers: int = Field(default=0, ge=0)
    engaged_customers: int = Field(default=0, ge=0)
    total_revenue: float = Field(default=0.0, ge=0.0)
    average_engagement_score: float = Field(default=0.0, ge=0.0, le=1.0)
    conversion_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    engagement_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    revenue_per_customer: float = Field(default=0.0, ge=0.0)
    metrics: list[JourneyMetric] = Field(default_factory=list)
    period_start: datetime | None = None
    period_end: datetime | None = None


class FunnelStage(BaseModel):
    """A single stage in a conversion funnel."""

    stage_name: str
    customer_count: int = Field(default=0, ge=0)
    conversion_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    dropoff_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    average_time_hours: float = Field(default=0.0, ge=0.0)


class JourneyFunnel(BaseModel):
    """Conversion funnel for a journey."""

    journey_id: str
    stages: list[FunnelStage] = Field(default_factory=list)
    overall_conversion_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    total_dropoff: int = Field(default=0, ge=0)


class CohortAnalysis(BaseModel):
    """Cohort analysis data for a journey."""

    journey_id: str
    cohort_date: datetime
    cohort_size: int = Field(default=0, ge=0)
    retained_customers: int = Field(default=0, ge=0)
    retention_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    average_revenue: float = Field(default=0.0, ge=0.0)


class AnalyticsSummary(BaseModel):
    """Summary of analytics across all journeys."""

    total_journeys: int = Field(default=0, ge=0)
    active_journeys: int = Field(default=0, ge=0)
    total_customers_reached: int = Field(default=0, ge=0)
    total_conversions: int = Field(default=0, ge=0)
    overall_conversion_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    total_revenue: float = Field(default=0.0, ge=0.0)
    top_performing_journey: str | None = None
    average_journey_score: float = Field(default=0.0, ge=0.0, le=1.0)
    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(datetime.now().astimezone().tzinfo)
    )
