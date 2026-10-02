"""Interview models."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class InterviewStatus(StrEnum):
    """Interview lifecycle status."""

    PENDING = "pending"
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    RESCHEDULED = "rescheduled"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    NO_SHOW = "no_show"


class InterviewType(StrEnum):
    """Type of interview."""

    PHONE = "phone"
    VIDEO = "video"
    IN_PERSON = "in_person"
    TECHNICAL = "technical"
    BEHAVIORAL = "behavioral"
    PANEL = "panel"


class Participant(BaseModel):
    """Interview participant."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1, max_length=200, description="Participant full name")
    email: str = Field(..., description="Participant email address")
    role: str = Field(..., description="Role (e.g., interviewer, candidate)")
    timezone: str | None = Field(None, description="IANA timezone identifier")


class InterviewBase(BaseModel):
    """Base interview model with common fields."""

    model_config = ConfigDict(extra="forbid")

    title: str = Field(..., min_length=1, max_length=300, description="Interview title")
    description: str | None = Field(None, max_length=2000, description="Interview description")
    interview_type: InterviewType = Field(default=InterviewType.VIDEO)
    participants: list[Participant] = Field(..., min_length=1, description="Interview participants")
    duration_minutes: int = Field(default=60, ge=15, le=480, description="Duration in minutes")
    preferred_timezones: list[str] = Field(default_factory=list, description="Preferred timezones")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class InterviewCreate(InterviewBase):
    """Model for creating a new interview."""

    proposed_slot_ids: list[str] = Field(default_factory=list, description="Proposed time slot IDs")


class InterviewUpdate(BaseModel):
    """Model for updating an existing interview."""

    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(None, min_length=1, max_length=300)
    description: str | None = Field(None, max_length=2000)
    interview_type: InterviewType | None = None
    participants: list[Participant] | None = None
    duration_minutes: int | None = Field(None, ge=15, le=480)
    preferred_timezones: list[str] | None = None
    status: InterviewStatus | None = None
    scheduled_at: datetime | None = None
    metadata: dict[str, Any] | None = None


class Interview(InterviewBase):
    """Full interview model with system fields."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique interview ID")
    status: InterviewStatus = Field(default=InterviewStatus.PENDING)
    proposed_slot_ids: list[str] = Field(default_factory=list, description="Proposed time slot IDs")
    scheduled_at: datetime | None = Field(None, description="Scheduled start time (UTC)")
    scheduled_timezone: str | None = Field(None, description="Timezone of scheduled time")
    schedule_id: str | None = Field(None, description="Associated schedule ID")
    conflict_ids: list[str] = Field(default_factory=list, description="Associated conflict IDs")
    reminder_ids: list[str] = Field(default_factory=list, description="Associated reminder IDs")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str | None = Field(None, description="Creator identifier")

    def model_dump(self, **kwargs: Any) -> dict[str, Any]:
        """Override to ensure datetime serialization."""
        data = super().model_dump(**kwargs)
        for key in ("scheduled_at", "created_at", "updated_at"):
            if data.get(key) and isinstance(data[key], datetime):
                data[key] = data[key].isoformat()
        return data
