"""Data models for the Journey Orchestrator."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class JourneyStatus(StrEnum):
    """Journey status enumeration."""

    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class JourneyStep(BaseModel):
    """A single step in a customer journey."""

    step_number: int
    channel: str
    action: str
    delay_hours: float = 0.0
    content_template: str = ""
    exit_conditions: list[str] = Field(default_factory=list)


class JourneyCreate(BaseModel):
    """Request model for creating a journey."""

    business_goal: str = Field(..., min_length=1, description="Business objective")
    target_audience: str = Field(..., min_length=1, description="Target audience description")
    channels: list[str] = Field(default=["email"], description="Channels to use")
    constraints: dict[str, Any] = Field(default_factory=dict, description="Design constraints")


class Journey(BaseModel):
    """Complete journey model."""

    id: str
    name: str
    description: str = ""
    business_goal: str
    target_audience: str
    channels: list[str]
    status: JourneyStatus = JourneyStatus.DRAFT
    steps: list[JourneyStep] = Field(default_factory=list)
    success_metrics: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = Field(default_factory=dict)


class CustomerEvent(BaseModel):
    """Customer event model."""

    id: str
    customer_id: str
    event_type: str
    properties: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Segment(BaseModel):
    """Customer segment model."""

    id: str
    name: str
    description: str = ""
    criteria: dict[str, Any] = Field(default_factory=dict)
    customer_count: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
