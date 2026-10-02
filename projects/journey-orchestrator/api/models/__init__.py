"""Pydantic request/response models for the API layer."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class JourneyStatus(str, Enum):
    """Journey execution status."""

    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class ChannelType(str, Enum):
    """Supported channel types."""

    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    WEB = "web"
    ADS = "ads"


class JourneyCreateRequest(BaseModel):
    """Request model for creating a journey."""

    name: str = Field(..., min_length=1, max_length=200, description="Journey name")
    description: str = Field(default="", description="Journey description")
    target_audience: str = Field(..., description="Target audience segment")
    business_goal: str = Field(..., description="Primary business goal")
    channels: list[ChannelType] = Field(default_factory=list, description="Channels to use")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class JourneyUpdateRequest(BaseModel):
    """Request model for updating a journey."""

    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    target_audience: str | None = None
    business_goal: str | None = None
    channels: list[ChannelType] | None = None
    status: JourneyStatus | None = None
    metadata: dict[str, Any] | None = None


class JourneyResponse(BaseModel):
    """Response model for a journey."""

    id: str = Field(..., description="Journey identifier")
    name: str
    description: str = ""
    target_audience: str
    business_goal: str
    channels: list[str] = Field(default_factory=list)
    status: JourneyStatus = JourneyStatus.DRAFT
    stages: list[dict[str, Any]] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)


class JourneyListResponse(BaseModel):
    """Response model for listing journeys."""

    journeys: list[JourneyResponse]
    total: int
    page: int = 1
    page_size: int = 20


class JourneyExecuteRequest(BaseModel):
    """Request model for executing a journey."""

    customer_ids: list[str] = Field(default_factory=list, description="Specific customers to target")
    segment_id: str | None = Field(default=None, description="Segment to target")
    scheduled_time: datetime | None = Field(default=None, description="When to start execution")
    metadata: dict[str, Any] = Field(default_factory=dict)


class JourneyExecuteResponse(BaseModel):
    """Response model for journey execution."""

    execution_id: str
    journey_id: str
    status: JourneyStatus
    started_at: datetime = Field(default_factory=datetime.utcnow)
    estimated_completion: datetime | None = None
    message: str = ""


class JourneyStatusResponse(BaseModel):
    """Response model for journey status."""

    journey_id: str
    execution_id: str | None = None
    status: JourneyStatus
    progress: float = Field(default=0.0, ge=0.0, le=1.0, description="Progress percentage")
    current_stage: str | None = None
    customers_processed: int = 0
    customers_total: int = 0
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error: str | None = None


class PersonalizeRequest(BaseModel):
    """Request model for personalization."""

    customer_id: str = Field(..., description="Customer identifier")
    customer_profile: dict[str, Any] = Field(default_factory=dict, description="Customer attributes")
    channel: ChannelType | None = Field(default=None, description="Target channel")
    context: dict[str, Any] = Field(default_factory=dict, description="Additional context")


class PersonalizeResponse(BaseModel):
    """Response model for personalization."""

    customer_id: str
    contents: list[dict[str, Any]] = Field(default_factory=list)
    recommended_offers: list[str] = Field(default_factory=list)
    next_best_action: str = ""
    confidence_score: float = 0.0


class OptimizeTimingRequest(BaseModel):
    """Request model for timing optimization."""

    customer_id: str = Field(..., description="Customer identifier")
    channels: list[ChannelType] = Field(default_factory=list, description="Channels to optimize")
    timezone: str | None = Field(default=None, description="Customer timezone")


class OptimizeTimingResponse(BaseModel):
    """Response model for timing optimization."""

    customer_id: str
    timezone: str = "UTC"
    channel_timings: list[dict[str, Any]] = Field(default_factory=list)
    best_overall_time: str = ""
    global_frequency_cap: int = 5


class ExperimentCreateRequest(BaseModel):
    """Request model for creating an experiment."""

    name: str = Field(..., min_length=1, max_length=200)
    hypothesis: str = Field(..., description="Experiment hypothesis")
    experiment_type: str = Field(default="ab_test")
    variants: list[dict[str, Any]] = Field(default_factory=list)
    primary_metric: str = Field(default="conversion_rate")
    secondary_metrics: list[str] = Field(default_factory=list)
    minimum_sample_size: int = Field(default=1000, ge=100)
    confidence_level: float = Field(default=0.95, ge=0.8, le=0.99)
    max_duration_days: int = Field(default=14, ge=1, le=90)


class ExperimentResponse(BaseModel):
    """Response model for an experiment."""

    id: str
    name: str
    hypothesis: str
    status: str = "draft"
    variants: list[dict[str, Any]] = Field(default_factory=list)
    primary_metric: str = "conversion_rate"
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ExperimentResultsResponse(BaseModel):
    """Response model for experiment results."""

    experiment_id: str
    status: str
    winner: str | None = None
    confidence: float = 0.0
    sample_size: int = 0
    metrics: dict[str, float] = Field(default_factory=dict)
    recommendation: str = ""


class HealthResponse(BaseModel):
    """Response model for health check."""

    status: str = "healthy"
    version: str = "0.1.0"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    services: dict[str, str] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    """Standard error response model."""

    error: str
    code: str | None = None
    details: dict[str, Any] | None = None
