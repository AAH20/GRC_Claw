"""Pydantic data models for the Customer Segmentation platform."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class SegmentType(StrEnum):
    """Types of customer segments."""
    RFM = "rfm"
    BEHAVIORAL = "behavioral"
    DEMOGRAPHIC = "demographic"
    PREDICTIVE = "predictive"
    CUSTOM = "custom"


class SegmentStatus(StrEnum):
    """Status of a customer segment."""
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"
    PROCESSING = "processing"


class Customer(BaseModel):
    """Customer data model."""
    model_config = ConfigDict(extra="allow")

    id: str
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    company: str | None = None
    industry: str | None = None
    job_title: str | None = None
    country: str | None = None
    city: str | None = None
    total_revenue: float = 0.0
    total_orders: int = 0
    last_order_date: datetime | None = None
    first_order_date: datetime | None = None
    lifetime_value: float = 0.0
    churn_risk: float | None = Field(default=None, ge=0.0, le=1.0)
    engagement_score: float | None = Field(default=None, ge=0.0, le=100.0)
    segment_ids: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Segment(BaseModel):
    """Customer segment data model."""
    model_config = ConfigDict(extra="allow")

    id: str
    name: str
    description: str = ""
    segment_type: SegmentType = SegmentType.CUSTOM
    status: SegmentStatus = SegmentStatus.DRAFT
    size: int = 0
    criteria: dict[str, Any] = Field(default_factory=dict)
    customer_ids: list[str] = Field(default_factory=list)
    rfm_profile: dict[str, Any] | None = None
    behavioral_profile: dict[str, Any] | None = None
    strategies: list[dict[str, Any]] = Field(default_factory=list)
    performance_metrics: dict[str, Any] | None = None
    quality_score: float | None = Field(default=None, ge=0.0, le=1.0)
    bias_report: dict[str, Any] | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class SegmentCreate(BaseModel):
    """Model for creating a new segment."""
    name: str = Field(min_length=1, max_length=200)
    description: str = ""
    segment_type: SegmentType = SegmentType.CUSTOM
    criteria: dict[str, Any] = Field(default_factory=dict)


class SegmentUpdate(BaseModel):
    """Model for updating an existing segment."""
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    status: SegmentStatus | None = None
    criteria: dict[str, Any] | None = None


class RFMProfile(BaseModel):
    """RFM (Recency, Frequency, Monetary) profile."""
    recency_days: int
    frequency: int
    monetary_value: float
    r_score: int = Field(ge=1, le=5)
    f_score: int = Field(ge=1, le=5)
    m_score: int = Field(ge=1, le=5)
    rfm_segment: str


class PerformanceMetrics(BaseModel):
    """Segment performance metrics."""
    segment_id: str
    period_start: datetime
    period_end: datetime
    total_customers: int
    active_customers: int
    conversion_rate: float = Field(ge=0.0, le=1.0)
    churn_rate: float = Field(ge=0.0, le=1.0)
    average_order_value: float
    total_revenue: float
    roi: float
    engagement_rate: float = Field(ge=0.0, le=1.0)
    metrics: dict[str, Any] = Field(default_factory=dict)


class AnalysisResult(BaseModel):
    """Result of a segment analysis pipeline run."""
    segment_id: str
    status: Literal["completed", "failed", "partial"]
    agents_executed: list[str]
    insights: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    quality_score: float | None = None
    bias_detected: bool = False
    errors: list[str] = Field(default_factory=list)
    started_at: datetime
    completed_at: datetime | None = None


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    version: str
    timestamp: datetime
    checks: dict[str, bool] = Field(default_factory=dict)


class CustomerEnrichmentRequest(BaseModel):
    """Request model for customer data enrichment."""
    customer_ids: list[str] = Field(min_length=1, max_length=1000)
    sources: list[Literal["salesforce", "hubspot", "google_analytics"]] = Field(
        default_factory=lambda: ["salesforce", "hubspot", "google_analytics"]
    )


class CustomerEnrichmentResponse(BaseModel):
    """Response model for customer data enrichment."""
    enriched_count: int
    failed_count: int
    results: dict[str, Any] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)
