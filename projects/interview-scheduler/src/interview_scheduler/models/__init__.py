"""Pydantic models for interview scheduler."""

from interview_scheduler.models.interview import (
    Interview,
    InterviewCreate,
    InterviewStatus,
    InterviewUpdate,
)
from interview_scheduler.models.schedule import Schedule, ScheduleCreate, ScheduleStatus
from interview_scheduler.models.timeslot import TimeSlot, TimeSlotRequest
from interview_scheduler.models.conflict import Conflict, ConflictCreate, ConflictResolution, ConflictSeverity
from interview_scheduler.models.reminder import Reminder, ReminderCreate, ReminderStatus, ReminderType

__all__ = [
    "Interview",
    "InterviewCreate",
    "InterviewStatus",
    "InterviewUpdate",
    "Schedule",
    "ScheduleCreate",
    "ScheduleStatus",
    "TimeSlot",
    "TimeSlotRequest",
    "Conflict",
    "ConflictCreate",
    "ConflictResolution",
    "ConflictSeverity",
    "Reminder",
    "ReminderCreate",
    "ReminderStatus",
    "ReminderType",
]
