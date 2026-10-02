"""Conflict models."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ConflictSeverity(str, Enum):
    """Conflict severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ConflictType(str, Enum):
    """Types of scheduling conflicts."""

    DOUBLE_BOOKING = "double_booking"
    OUTSIDE_BUSINESS_HOURS = "outside_business_hours"
    INSUFFICIENT_NOTICE = "insufficient_notice"
    BLACKOUT_DATE = "blackout_date"
    TIMEZONE_OVERLAP = "timezone_overlap"
    PARTICIPANT_UNAVAILABLE = "participant_unavailable"


class ConflictStatus(str, Enum):
    """Conflict resolution status."""

    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    IGNORED = "ignored"


class Conflict(BaseModel):
    """Represents a scheduling conflict."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique conflict ID")
    interview_id: str = Field(..., description="Associated interview ID")
    conflict_type: ConflictType
    severity: ConflictSeverity = Field(default=ConflictSeverity.MEDIUM)
    status: ConflictStatus = Field(default=ConflictStatus.OPEN)
    description: str = Field(..., description="Human-readable conflict description")
    conflicting_interview_id: str | None = Field(None, description="Conflicting interview ID")
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: datetime | None = None
    resolution: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    def model_dump(self, **kwargs: Any) -> dict[str, Any]:
        """Override to ensure datetime serialization."""
        data = super().model_dump(**kwargs)
        for key in ("detected_at", "resolved_at"):
            if data.get(key) and isinstance(data[key], datetime):
                data[key] = data[key].isoformat()
        return data


class ConflictCreate(BaseModel):
    """Model for creating a conflict."""

    model_config = ConfigDict(extra="forbid")

    interview_id: str
    conflict_type: ConflictType
    severity: ConflictSeverity = ConflictSeverity.MEDIUM
    description: str
    conflicting_interview_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ConflictResolution(BaseModel):
    """Model for resolving a conflict."""

    model_config = ConfigDict(extra="forbid")

    conflict_id: str
    resolution: str = Field(..., description="Resolution description")
    action: str = Field(..., description="Action taken (reschedule, cancel, ignore)")
    new_interview_id: str | None = None
    resolved_by: str | None = None
