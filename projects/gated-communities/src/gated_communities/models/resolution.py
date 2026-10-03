"""Resolution models for escalation outcomes."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class ResolutionStatus(StrEnum):
    """Status of a resolution."""

    PROPOSED = "proposed"
    APPROVED = "approved"
    IN_PROGRESS = "in_progress"
    IMPLEMENTED = "implemented"
    VERIFIED = "verified"
    REJECTED = "rejected"
    ROLLED_BACK = "rolled_back"


class Resolution(BaseModel):
    """Resolution entity representing the outcome of an escalation."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(default_factory=uuid4)
    escalation_id: UUID
    title: str = Field(..., min_length=1, max_length=500)
    description: str = Field(..., min_length=1)
    status: ResolutionStatus = Field(default=ResolutionStatus.PROPOSED)
    resolution_type: str = Field(
        default="manual", description="Type: manual, automated, hybrid"
    )
    root_cause: str | None = Field(default=None)
    steps: list[str] = Field(default_factory=list, description="Resolution steps taken")
    automated: bool = Field(
        default=False, description="Whether resolution was automated"
    )
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    verified_by: str | None = Field(default=None)
    verified_at: datetime | None = Field(default=None)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime | None = Field(default=None)


class ResolutionCreate(BaseModel):
    """Schema for creating a resolution."""

    escalation_id: UUID
    title: str = Field(..., min_length=1, max_length=500)
    description: str = Field(..., min_length=1)
    resolution_type: str = Field(default="manual")
    root_cause: str | None = None
    steps: list[str] = Field(default_factory=list)
    automated: bool = False
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)
