"""SLA (Service Level Agreement) tracking models."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class SLAStatus(str, Enum):
    """Status of an SLA."""

    ACTIVE = "active"
    AT_RISK = "at_risk"
    BREACHED = "breached"
    MET = "met"
    PAUSED = "paused"


class SLABreach(BaseModel):
    """Record of an SLA breach event."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(default_factory=uuid4)
    sla_id: UUID
    escalation_id: UUID
    breached_at: datetime = Field(default_factory=datetime.utcnow)
    minutes_overdue: float = Field(..., ge=0)
    severity: str = Field(default="high")
    acknowledged: bool = Field(default=False)
    acknowledged_by: str | None = Field(default=None)
    acknowledged_at: datetime | None = Field(default=None)
    notes: str = Field(default="")


class SLA(BaseModel):
    """Service Level Agreement tracking entity."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(default_factory=uuid4)
    escalation_id: UUID
    priority: str = Field(..., description="Priority level this SLA applies to")
    response_time_minutes: int = Field(..., ge=1, description="Allowed response time")
    resolution_time_minutes: int = Field(..., ge=1, description="Allowed resolution time")
    status: SLAStatus = Field(default=SLAStatus.ACTIVE)
    started_at: datetime = Field(default_factory=datetime.utcnow)
    response_deadline: datetime = Field(..., description="Deadline for initial response")
    resolution_deadline: datetime = Field(..., description="Deadline for resolution")
    responded_at: datetime | None = Field(default=None)
    resolved_at: datetime | None = Field(default=None)
    elapsed_minutes: float = Field(default=0.0, ge=0)
    remaining_minutes: float = Field(default=0.0)
    breach_count: int = Field(default=0, ge=0)
    breaches: list[SLABreach] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
