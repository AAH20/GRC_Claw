"""Escalation analysis models for pattern detection and insights."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class EscalationPattern(StrEnum):
    """Types of patterns detected in escalations."""

    RECURRING = "recurring"
    SEASONAL = "seasonal"
    DEPENDENCY = "dependency"
    CAPACITY = "capacity"
    CONFIGURATION = "configuration"
    EXTERNAL = "external"


class EscalationAnalysis(BaseModel):
    """Comprehensive analysis of an escalation or set of escalations."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(default_factory=uuid4)
    escalation_id: UUID | None = Field(default=None)
    analysis_type: str = Field(default="single", description="single, batch, or trend")
    summary: str = Field(default="")
    patterns: list[EscalationPattern] = Field(default_factory=list)
    risk_score: float = Field(default=0.0, ge=0.0, le=1.0)
    impact_assessment: str = Field(default="")
    recommendations: list[str] = Field(default_factory=list)
    related_escalations: list[UUID] = Field(default_factory=list)
    metrics: dict[str, float] = Field(default_factory=dict)
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class TrendReport(BaseModel):
    """Trend analysis report over a time period."""

    period_start: datetime
    period_end: datetime
    total_escalations: int = Field(default=0, ge=0)
    resolved_count: int = Field(default=0, ge=0)
    breached_count: int = Field(default=0, ge=0)
    avg_resolution_minutes: float = Field(default=0.0, ge=0)
    top_categories: dict[str, int] = Field(default_factory=dict)
    priority_distribution: dict[str, int] = Field(default_factory=dict)
    pattern_summary: dict[str, int] = Field(default_factory=dict)
