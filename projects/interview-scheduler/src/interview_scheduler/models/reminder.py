"""Reminder models."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ReminderType(StrEnum):
    """Types of reminders."""

    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    WEBHOOK = "webhook"
    SLACK = "slack"


class ReminderStatus(StrEnum):
    """Reminder lifecycle status."""

    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Reminder(BaseModel):
    """Represents a reminder for an interview."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique reminder ID")
    interview_id: str = Field(..., description="Associated interview ID")
    reminder_type: ReminderType
    status: ReminderStatus = Field(default=ReminderStatus.PENDING)
    minutes_before: int = Field(..., ge=0, description="Minutes before interview to send")
    recipient: str = Field(..., description="Recipient address (email, phone, etc.)")
    subject: str | None = Field(None, description="Reminder subject")
    message: str | None = Field(None, description="Reminder message body")
    scheduled_at: datetime | None = Field(None, description="When to send the reminder (UTC)")
    sent_at: datetime | None = None
    delivered_at: datetime | None = None
    error_message: str | None = None
    retry_count: int = Field(default=0, ge=0)
    max_retries: int = Field(default=3, ge=0)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def model_dump(self, **kwargs: Any) -> dict[str, Any]:
        """Override to ensure datetime serialization."""
        data = super().model_dump(**kwargs)
        for key in ("scheduled_at", "sent_at", "delivered_at"):
            if data.get(key) and isinstance(data[key], datetime):
                data[key] = data[key].isoformat()
        return data


class ReminderCreate(BaseModel):
    """Model for creating a reminder."""

    model_config = ConfigDict(extra="forbid")

    interview_id: str
    reminder_type: ReminderType
    minutes_before: int = Field(..., ge=0)
    recipient: str
    subject: str | None = None
    message: str | None = None
    scheduled_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ReminderUpdate(BaseModel):
    """Model for updating a reminder."""

    model_config = ConfigDict(extra="forbid")

    status: ReminderStatus | None = None
    subject: str | None = None
    message: str | None = None
    scheduled_at: datetime | None = None
    metadata: dict[str, Any] | None = None
