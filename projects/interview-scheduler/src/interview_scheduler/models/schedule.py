"""Schedule models."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ScheduleStatus(StrEnum):
    """Schedule lifecycle status."""

    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ScheduleBase(BaseModel):
    """Base schedule model."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1, max_length=200, description="Schedule name")
    description: str | None = Field(None, max_length=2000)
    timezone: str = Field(default="UTC", description="Primary timezone for this schedule")
    interview_ids: list[str] = Field(default_factory=list, description="Associated interview IDs")
    business_hours: dict[str, tuple[int, int]] = Field(
        default_factory=dict,
        description="Business hours per weekday (0=Monday)",
    )
    blackout_dates: list[str] = Field(
        default_factory=list, description="Blackout dates in ISO format"
    )
    metadata: dict[str, Any] = Field(default_factory=dict)


class ScheduleCreate(ScheduleBase):
    """Model for creating a new schedule."""


class ScheduleUpdate(BaseModel):
    """Model for updating a schedule."""

    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    timezone: str | None = None
    status: ScheduleStatus | None = None
    interview_ids: list[str] | None = None
    business_hours: dict[str, tuple[int, int]] | None = None
    blackout_dates: list[str] | None = None
    metadata: dict[str, Any] | None = None


class Schedule(ScheduleBase):
    """Full schedule model with system fields."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique schedule ID")
    status: ScheduleStatus = Field(default=ScheduleStatus.DRAFT)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str | None = None

    def model_dump(self, **kwargs: Any) -> dict[str, Any]:
        """Override to ensure datetime serialization."""
        data = super().model_dump(**kwargs)
        for key in ("created_at", "updated_at"):
            if data.get(key) and isinstance(data[key], datetime):
                data[key] = data[key].isoformat()
        return data
