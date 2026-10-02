"""Service layer for interview scheduler business logic."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from interview_scheduler.agents.availability_optimizer import AvailabilityOptimizerAgent
from interview_scheduler.models.conflict import Conflict, ConflictCreate
from interview_scheduler.models.interview import Interview, InterviewCreate, InterviewUpdate
from interview_scheduler.models.reminder import Reminder
from interview_scheduler.models.schedule import Schedule, ScheduleCreate, ScheduleUpdate
from interview_scheduler.models.timeslot import TimeSlot, TimeSlotRequest, TimeSlotResponse

logger = logging.getLogger(__name__)


class InterviewService:
    """Service for managing interviews."""

    def __init__(self) -> None:
        """Initialize the interview service."""
        self._interviews: dict[str, Interview] = {}
        self._schedules: dict[str, Schedule] = {}
        self._conflicts: dict[str, Conflict] = {}
        self._reminders: dict[str, Reminder] = {}
        self._slots: dict[str, TimeSlot] = {}

    def create_interview(self, data: InterviewCreate) -> Interview:
        """Create a new interview.

        Args:
            data: Interview creation data.

        Returns:
            The created interview.
        """
        interview = Interview(**data.model_dump())
        self._interviews[interview.id] = interview
        logger.info("Created interview %s", interview.id)
        return interview

    def get_interview(self, interview_id: str) -> Interview | None:
        """Get an interview by ID.

        Args:
            interview_id: The interview ID.

        Returns:
            The interview or None if not found.
        """
        return self._interviews.get(interview_id)

    def list_interviews(
        self,
        status: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Interview]:
        """List interviews with optional filtering.

        Args:
            status: Filter by status.
            limit: Maximum results.
            offset: Pagination offset.

        Returns:
            List of interviews.
        """
        interviews = list(self._interviews.values())
        if status:
            interviews = [i for i in interviews if i.status.value == status]
        return interviews[offset : offset + limit]

    def update_interview(
        self, interview_id: str, data: InterviewUpdate
    ) -> Interview | None:
        """Update an existing interview.

        Args:
            interview_id: The interview ID.
            data: Update data.

        Returns:
            The updated interview or None if not found.
        """
        interview = self._interviews.get(interview_id)
        if not interview:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(interview, key, value)
        interview.updated_at = datetime.utcnow()
        logger.info("Updated interview %s", interview_id)
        return interview

    def delete_interview(self, interview_id: str) -> bool:
        """Delete an interview.

        Args:
            interview_id: The interview ID.

        Returns:
            True if deleted, False if not found.
        """
        if interview_id in self._interviews:
            del self._interviews[interview_id]
            logger.info("Deleted interview %s", interview_id)
            return True
        return False

    def create_schedule(self, data: ScheduleCreate) -> Schedule:
        """Create a new schedule.

        Args:
            data: Schedule creation data.

        Returns:
            The created schedule.
        """
        schedule = Schedule(**data.model_dump())
        self._schedules[schedule.id] = schedule
        logger.info("Created schedule %s", schedule.id)
        return schedule

    def get_schedule(self, schedule_id: str) -> Schedule | None:
        """Get a schedule by ID.

        Args:
            schedule_id: The schedule ID.

        Returns:
            The schedule or None if not found.
        """
        return self._schedules.get(schedule_id)

    def list_schedules(self, limit: int = 100, offset: int = 0) -> list[Schedule]:
        """List schedules.

        Args:
            limit: Maximum results.
            offset: Pagination offset.

        Returns:
            List of schedules.
        """
        return list(self._schedules.values())[offset : offset + limit]

    def update_schedule(
        self, schedule_id: str, data: ScheduleUpdate
    ) -> Schedule | None:
        """Update a schedule.

        Args:
            schedule_id: The schedule ID.
            data: Update data.

        Returns:
            The updated schedule or None if not found.
        """
        schedule = self._schedules.get(schedule_id)
        if not schedule:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(schedule, key, value)
        schedule.updated_at = datetime.utcnow()
        return schedule

    def delete_schedule(self, schedule_id: str) -> bool:
        """Delete a schedule.

        Args:
            schedule_id: The schedule ID.

        Returns:
            True if deleted, False if not found.
        """
        if schedule_id in self._schedules:
            del self._schedules[schedule_id]
            return True
        return False

    def create_conflict(self, data: ConflictCreate) -> Conflict:
        """Create a conflict record.

        Args:
            data: Conflict creation data.

        Returns:
            The created conflict.
        """
        conflict = Conflict(**data.model_dump())
        self._conflicts[conflict.id] = conflict
        return conflict

    def get_conflict(self, conflict_id: str) -> Conflict | None:
        """Get a conflict by ID.

        Args:
            conflict_id: The conflict ID.

        Returns:
            The conflict or None if not found.
        """
        return self._conflicts.get(conflict_id)

    def list_conflicts(
        self,
        interview_id: str | None = None,
        status: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Conflict]:
        """List conflicts with optional filtering.

        Args:
            interview_id: Filter by interview ID.
            status: Filter by status.
            limit: Maximum results.
            offset: Pagination offset.

        Returns:
            List of conflicts.
        """
        conflicts = list(self._conflicts.values())
        if interview_id:
            conflicts = [c for c in conflicts if c.interview_id == interview_id]
        if status:
            conflicts = [c for c in conflicts if c.status.value == status]
        return conflicts[offset : offset + limit]

    def resolve_conflict(
        self,
        conflict_id: str,
        resolution: str,
        action: str,
    ) -> Conflict | None:
        """Resolve a conflict.

        Args:
            conflict_id: The conflict ID.
            resolution: Resolution description.
            action: Action taken.

        Returns:
            The resolved conflict or None if not found.
        """
        conflict = self._conflicts.get(conflict_id)
        if not conflict:
            return None
        conflict.status = "resolved"
        conflict.resolution = resolution
        conflict.resolved_at = datetime.utcnow()
        return conflict

    def create_reminder(self, data: Any) -> Reminder:
        """Create a reminder.

        Args:
            data: Reminder creation data.

        Returns:
            The created reminder.
        """
        reminder = Reminder(**data.model_dump())
        self._reminders[reminder.id] = reminder
        return reminder

    def get_reminder(self, reminder_id: str) -> Reminder | None:
        """Get a reminder by ID.

        Args:
            reminder_id: The reminder ID.

        Returns:
            The reminder or None if not found.
        """
        return self._reminders.get(reminder_id)

    def list_reminders(
        self,
        interview_id: str | None = None,
        status: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Reminder]:
        """List reminders with optional filtering.

        Args:
            interview_id: Filter by interview ID.
            status: Filter by status.
            limit: Maximum results.
            offset: Pagination offset.

        Returns:
            List of reminders.
        """
        reminders = list(self._reminders.values())
        if interview_id:
            reminders = [r for r in reminders if r.interview_id == interview_id]
        if status:
            reminders = [r for r in reminders if r.status.value == status]
        return reminders[offset : offset + limit]

    def update_reminder(
        self, reminder_id: str, **kwargs: Any
    ) -> Reminder | None:
        """Update a reminder.

        Args:
            reminder_id: The reminder ID.
            **kwargs: Fields to update.

        Returns:
            The updated reminder or None if not found.
        """
        reminder = self._reminders.get(reminder_id)
        if not reminder:
            return None
        for key, value in kwargs.items():
            if hasattr(reminder, key):
                setattr(reminder, key, value)
        return reminder

    def delete_reminder(self, reminder_id: str) -> bool:
        """Delete a reminder.

        Args:
            reminder_id: The reminder ID.

        Returns:
            True if deleted, False if not found.
        """
        if reminder_id in self._reminders:
            del self._reminders[reminder_id]
            return True
        return False

    def find_time_slots(self, request: TimeSlotRequest) -> TimeSlotResponse:
        """Find available time slots.

        Args:
            request: Time slot search request.

        Returns:
            Time slot search response.
        """
        optimizer = AvailabilityOptimizerAgent()
        candidates = optimizer.generate_candidate_slots(
            request.start_date,
            request.end_date,
            request.duration_minutes,
        )
        if request.business_hours_only:
            candidates = optimizer.filter_business_hours(candidates)

        # Filter out past slots
        now = datetime.utcnow()
        candidates = [s for s in candidates if s.start_time > now]

        return TimeSlotResponse(
            slots=candidates[: request.max_results],
            total_found=len(candidates),
            search_window_start=request.start_date,
            search_window_end=request.end_date,
        )

    def get_all_interviews(self) -> list[Interview]:
        """Get all interviews (for conflict detection).

        Returns:
            List of all interviews.
        """
        return list(self._interviews.values())

    def get_all_reminders(self) -> list[Reminder]:
        """Get all reminders.

        Returns:
            List of all reminders.
        """
        return list(self._reminders.values())
