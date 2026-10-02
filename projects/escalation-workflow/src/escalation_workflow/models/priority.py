"""Priority models for escalation routing."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class PriorityLevel(StrEnum):
    """Priority levels for escalations."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Priority(BaseModel):
    """Priority configuration and routing rules."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(default_factory=uuid4)
    level: PriorityLevel
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(default="")
    sla_minutes: int = Field(default=60, ge=1, description="SLA response time in minutes")
    escalation_threshold: int = Field(default=3, ge=1, description="Auto-escalate after N breaches")
    notification_channels: list[str] = Field(default_factory=list)
    routing_rules: dict[str, str] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class PriorityAssessment(BaseModel):
    """Result of priority assessment by the router agent."""

    escalation_id: UUID
    assessed_priority: PriorityLevel
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasoning: str = Field(default="")
    factors: dict[str, float] = Field(default_factory=dict)
    recommended_sla_minutes: int = Field(default=60, ge=1)
    assessed_at: datetime = Field(default_factory=datetime.utcnow)
