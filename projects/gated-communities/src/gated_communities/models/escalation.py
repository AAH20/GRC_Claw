"""Escalation entity models."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class EscalationStatus(StrEnum):
    """Status of an escalation."""

    PENDING = "pending"
    ROUTED = "routed"
    IN_PROGRESS = "in_progress"
    WAITING = "waiting"
    RESOLVED = "resolved"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class Escalation(BaseModel):
    """Core escalation entity representing an issue requiring attention."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(default_factory=uuid4, description="Unique escalation identifier")
    title: str = Field(..., min_length=1, max_length=500, description="Escalation title")
    description: str = Field(..., min_length=1, max_length=5000, description="Detailed description")
    status: EscalationStatus = Field(default=EscalationStatus.PENDING)
    priority: str = Field(
        default="medium", description="Priority level (critical, high, medium, low)"
    )
    category: str = Field(default="general", description="Escalation category")
    source: str = Field(default="api", description="Source of the escalation")
    assignee: str | None = Field(default=None, description="Assigned agent or team")
    requester: str = Field(..., description="Person or system that created the escalation")
    tags: list[str] = Field(default_factory=list, description="Tags for categorization")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    sla_id: UUID | None = Field(default=None, description="Associated SLA identifier")
    resolution_id: UUID | None = Field(default=None, description="Associated resolution identifier")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: datetime | None = Field(default=None)
    due_at: datetime | None = Field(default=None, description="SLA deadline")


class EscalationCreate(BaseModel):
    """Schema for creating a new escalation."""

    title: str = Field(..., min_length=1, max_length=500)
    description: str = Field(..., min_length=1, max_length=5000)
    priority: str = Field(default="medium")
    category: str = Field(default="general")
    source: str = Field(default="api")
    requester: str = Field(..., min_length=1)
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class EscalationUpdate(BaseModel):
    """Schema for updating an existing escalation."""

    title: str | None = Field(default=None, min_length=1, max_length=500)
    description: str | None = Field(default=None, min_length=1, max_length=5000)
    status: EscalationStatus | None = None
    priority: str | None = None
    category: str | None = None
    assignee: str | None = None
    tags: list[str] | None = None
    metadata: dict[str, Any] | None = None
