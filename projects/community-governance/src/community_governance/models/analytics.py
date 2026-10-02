"""Governance analytics models."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class GovernanceHealthScore(BaseModel):
    """Health score for governance metrics."""

    model_config = ConfigDict(from_attributes=True)

    overall_score: float = Field(
        ..., ge=0, le=100, description="Overall governance health score (0-100)"
    )
    rule_compliance_rate: float = Field(
        ..., ge=0, le=100, description="Rule compliance rate percentage"
    )
    dispute_resolution_rate: float = Field(
        ..., ge=0, le=100, description="Dispute resolution rate percentage"
    )
    policy_adherence_rate: float = Field(
        ..., ge=0, le=100, description="Policy adherence rate percentage"
    )
    average_resolution_time_hours: float = Field(
        ..., ge=0, description="Average resolution time in hours"
    )
    active_violations_count: int = Field(
        ..., ge=0, description="Number of active violations"
    )
    pending_disputes_count: int = Field(
        ..., ge=0, description="Number of pending disputes"
    )
    calculated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Calculation timestamp"
    )


class GovernanceAnalytics(BaseModel):
    """Comprehensive governance analytics model."""

    model_config = ConfigDict(from_attributes=True)

    period_start: datetime = Field(..., description="Analytics period start")
    period_end: datetime = Field(..., description="Analytics period end")
    total_actions: int = Field(default=0, ge=0, description="Total governance actions")
    total_rules: int = Field(default=0, ge=0, description="Total active rules")
    total_disputes: int = Field(default=0, ge=0, description="Total disputes")
    total_policies: int = Field(default=0, ge=0, description="Total active policies")
    violations_by_category: dict[str, int] = Field(
        default_factory=dict, description="Violations grouped by category"
    )
    disputes_by_status: dict[str, int] = Field(
        default_factory=dict, description="Disputes grouped by status"
    )
    actions_by_type: dict[str, int] = Field(
        default_factory=dict, description="Actions grouped by type"
    )
    top_violated_rules: list[dict[str, Any]] = Field(
        default_factory=list, description="Most frequently violated rules"
    )
    resolution_time_trend: list[dict[str, Any]] = Field(
        default_factory=list, description="Resolution time trend data"
    )
    health_score: GovernanceHealthScore = Field(
        ..., description="Governance health score"
    )
    recommendations: list[str] = Field(
        default_factory=list, description="AI-generated recommendations"
    )
    generated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Generation timestamp"
    )


class GovernanceSummary(BaseModel):
    """Summary of governance state."""

    model_config = ConfigDict(from_attributes=True)

    total_active_rules: int = Field(default=0, ge=0, description="Total active rules")
    total_active_policies: int = Field(
        default=0, ge=0, description="Total active policies"
    )
    open_disputes: int = Field(default=0, ge=0, description="Open disputes count")
    pending_actions: int = Field(default=0, ge=0, description="Pending actions count")
    violations_last_24h: int = Field(
        default=0, ge=0, description="Violations in the last 24 hours"
    )
    health_score: float = Field(
        default=0, ge=0, le=100, description="Current health score"
    )
    last_updated: datetime = Field(
        default_factory=datetime.utcnow, description="Last update timestamp"
    )
