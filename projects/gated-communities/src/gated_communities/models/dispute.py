"""Dispute models for community governance."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class DisputeStatus(StrEnum):
    """Status of a dispute."""

    OPEN = "open"
    UNDER_REVIEW = "under_review"
    MEDIATION = "mediation"
    RESOLVED = "resolved"
    CLOSED = "closed"
    ESCALATED = "escalated"


class DisputePriority(StrEnum):
    """Priority levels for disputes."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Dispute(BaseModel):
    """Dispute model representing a community dispute."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(default_factory=uuid4, description="Unique dispute identifier")
    title: str = Field(..., min_length=1, max_length=300, description="Dispute title")
    description: str = Field(..., min_length=1, description="Dispute description")
    status: DisputeStatus = Field(default=DisputeStatus.OPEN, description="Dispute status")
    priority: DisputePriority = Field(
        default=DisputePriority.MEDIUM, description="Dispute priority"
    )
    category: str = Field(..., description="Dispute category")
    initiator_id: str = Field(..., description="ID of the dispute initiator")
    respondent_id: str | None = Field(
        default=None, description="ID of the dispute respondent"
    )
    assigned_mediator_id: str | None = Field(
        default=None, description="ID of the assigned mediator"
    )
    related_action_id: UUID | None = Field(
        default=None, description="Related governance action ID"
    )
    resolution: DisputeResolution | None = Field(
        default=None, description="Dispute resolution details"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional dispute metadata"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Last update timestamp"
    )
    resolved_at: datetime | None = Field(
        default=None, description="Resolution timestamp"
    )


class DisputeCreate(BaseModel):
    """Model for creating a new dispute."""

    title: str = Field(..., min_length=1, max_length=300, description="Dispute title")
    description: str = Field(..., min_length=1, description="Dispute description")
    priority: DisputePriority = Field(
        default=DisputePriority.MEDIUM, description="Dispute priority"
    )
    category: str = Field(..., description="Dispute category")
    initiator_id: str = Field(..., description="ID of the dispute initiator")
    respondent_id: str | None = Field(
        default=None, description="ID of the dispute respondent"
    )
    related_action_id: UUID | None = Field(
        default=None, description="Related governance action ID"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional dispute metadata"
    )


class DisputeUpdate(BaseModel):
    """Model for updating an existing dispute."""

    title: str | None = Field(default=None, min_length=1, max_length=300)
    description: str | None = Field(default=None, min_length=1)
    status: DisputeStatus | None = None
    priority: DisputePriority | None = None
    assigned_mediator_id: str | None = None
    metadata: dict[str, Any] | None = None


class DisputeResolution(BaseModel):
    """Resolution details for a dispute."""

    model_config = ConfigDict(from_attributes=True)

    resolution_type: str = Field(..., description="Type of resolution")
    outcome: str = Field(..., description="Resolution outcome")
    rationale: str = Field(..., description="Rationale for the resolution")
    conditions: list[str] = Field(
        default_factory=list, description="Conditions of the resolution"
    )
    resolved_by: str = Field(..., description="ID of the resolver")
    resolved_at: datetime = Field(
        default_factory=datetime.utcnow, description="Resolution timestamp"
    )
    follow_up_required: bool = Field(
        default=False, description="Whether follow-up is required"
    )
    follow_up_date: datetime | None = Field(
        default=None, description="Follow-up date if required"
    )
