"""Governance action models."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class ActionType(StrEnum):
    """Types of governance actions."""

    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    APPROVE = "approve"
    REJECT = "reject"
    FLAG = "flag"
    ESCALATE = "escalate"
    RESOLVE = "resolve"


class ActionStatus(StrEnum):
    """Status of a governance action."""

    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"
    RESOLVED = "resolved"


class GovernanceActionBase(BaseModel):
    """Base model for governance actions."""

    model_config = ConfigDict(from_attributes=True)

    action_type: ActionType = Field(..., description="Type of governance action")
    target_id: str = Field(..., description="ID of the target entity")
    target_type: str = Field(..., description="Type of the target entity")
    actor_id: str = Field(..., description="ID of the actor performing the action")
    reason: str | None = Field(default=None, description="Reason for the action")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional action metadata"
    )


class GovernanceActionCreate(GovernanceActionBase):
    """Model for creating a new governance action."""

    pass


class GovernanceActionUpdate(BaseModel):
    """Model for updating a governance action."""

    model_config = ConfigDict(from_attributes=True)

    status: ActionStatus | None = Field(default=None, description="New status")
    reason: str | None = Field(default=None, description="Updated reason")
    metadata: dict[str, Any] | None = Field(
        default=None, description="Updated metadata"
    )


class GovernanceAction(GovernanceActionBase):
    """Full governance action model."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(default_factory=uuid4, description="Unique action identifier")
    status: ActionStatus = Field(
        default=ActionStatus.PENDING, description="Action status"
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
    resolution_notes: str | None = Field(
        default=None, description="Notes about the resolution"
    )
