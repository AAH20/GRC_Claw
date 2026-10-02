"""Time slot models."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SlotStatus(StrEnum):
    """Time slot availability status."""

    AVAILABLE = "available"
    BUSY = "busy"
    TENTATIVE = "tentative"
    BLOCKED = "blocked"


class TimeSlot(BaseModel):
    """Represents a single time slot."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique slot ID")
    start_time: datetime = Field(..., description="Slot start time (UTC)")
    end_time: datetime = Field(..., description="Slot end time (UTC)")
    timezone: str = Field(default="UTC", description="Timezone for display")
    status: SlotStatus = Field(default=SlotStatus.AVAILABLE)
    owner_id: str | None = Field(None, description="ID of the busy entity")
    owner_type: str | None = Field(None, description="Type of owner (interview, meeting, etc.)")
    score: float | None = Field(None, ge=0, le=1, description="Optimization score")
    metadata: dict[str, Any] = Field(default_factory=dict)

    def model_dump(self, **kwargs: Any) -> dict[str, Any]:
        """Override to ensure datetime serialization."""
        data = super().model_dump(**kwargs)
        for key in ("start_time", "end_time"):
            if data.get(key) and isinstance(data[key], datetime):
                data[key] = data[key].isoformat()
        return data


class TimeSlotRequest(BaseModel):
    """Request model for finding time slots."""

    model_config = ConfigDict(extra="forbid")

    participant_ids: list[str] = Field(..., min_length=1, description="Participant IDs")
    duration_minutes: int = Field(default=60, ge=15, le=480)
    start_date: datetime = Field(..., description="Search window start")
    end_date: datetime = Field(..., description="Search window end")
    preferred_timezones: list[str] = Field(default_factory=list)
    business_hours_only: bool = Field(default=True)
    max_results: int = Field(default=10, ge=1, le=100)


class TimeSlotResponse(BaseModel):
    """Response model for time slot queries."""

    slots: list[TimeSlot] = Field(default_factory=list)
    total_found: int = Field(default=0)
    search_window_start: datetime
    search_window_end: datetime
    timezone: str = "UTC"
