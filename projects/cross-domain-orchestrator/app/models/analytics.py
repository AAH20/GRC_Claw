"""Analytics-related Pydantic models.

Defines the data structures for analytics events and cross-domain metrics.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class AnalyticsEvent(BaseModel):
    """Represents a single analytics event.

    Attributes:
        id: Unique event identifier.
        event_type: Type of event.
        domain: Domain that generated the event.
        agent: Agent that generated the event.
        timestamp: Event timestamp.
        data: Event-specific data.
    """

    id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Event unique identifier",
    )
    event_type: str = Field(..., min_length=1, max_length=128, description="Event type")
    domain: str = Field(..., min_length=1, max_length=128, description="Source domain")
    agent: str = Field(..., min_length=1, max_length=128, description="Source agent")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Event timestamp",
    )
    data: dict[str, Any] = Field(
        default_factory=dict,
        description="Event-specific data",
    )


class DomainMetrics(BaseModel):
    """Metrics for a single domain.

    Attributes:
        domain: Domain name.
        total_requests: Total number of requests.
        successful_requests: Number of successful requests.
        failed_requests: Number of failed requests.
        average_latency_ms: Average request latency in milliseconds.
        last_activity: Last activity timestamp.
    """

    domain: str = Field(..., description="Domain name")
    total_requests: int = Field(default=0, ge=0, description="Total requests")
    successful_requests: int = Field(default=0, ge=0, description="Successful requests")
    failed_requests: int = Field(default=0, ge=0, description="Failed requests")
    average_latency_ms: float = Field(
        default=0.0,
        ge=0,
        description="Average latency in milliseconds",
    )
    last_activity: datetime = Field(
        default_factory=datetime.utcnow,
        description="Last activity timestamp",
    )


class CrossDomainAnalytics(BaseModel):
    """Aggregated analytics across all domains.

    Attributes:
        total_events: Total number of events.
        domain_metrics: Per-domain metrics.
        agent_metrics: Per-agent metrics.
        period_start: Analytics period start.
        period_end: Analytics period end.
        summary: Summary statistics.
    """

    total_events: int = Field(default=0, ge=0, description="Total events")
    domain_metrics: dict[str, DomainMetrics] = Field(
        default_factory=dict,
        description="Per-domain metrics",
    )
    agent_metrics: dict[str, int] = Field(
        default_factory=dict,
        description="Per-agent event counts",
    )
    period_start: datetime = Field(
        default_factory=datetime.utcnow,
        description="Analytics period start",
    )
    period_end: datetime = Field(
        default_factory=datetime.utcnow,
        description="Analytics period end",
    )
    summary: dict[str, Any] = Field(
        default_factory=dict,
        description="Summary statistics",
    )
