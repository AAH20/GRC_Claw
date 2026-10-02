"""Conflict Detector Agent using LangChain DeepAgents."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

from interview_scheduler.models.conflict import Conflict, ConflictCreate, ConflictSeverity, ConflictType
from interview_scheduler.models.interview import Interview
from interview_scheduler.models.timeslot import TimeSlot

logger = logging.getLogger(__name__)


class ConflictDetectorAgent:
    """Agent responsible for detecting scheduling conflicts.

    Uses LangChain DeepAgents to intelligently detect double bookings,
    business hours violations, insufficient notice, and other conflicts.
    """

    def __init__(
        self,
        min_notice_hours: int = 24,
        business_hours_start: int = 9,
        business_hours_end: int = 17,
    ) -> None:
        """Initialize the Conflict Detector Agent.

        Args:
            min_notice_hours: Minimum hours of notice required.
            business_hours_start: Business start hour.
            business_hours_end: Business end hour.
        """
        self.min_notice_hours = min_notice_hours
        self.business_hours_start = business_hours_start
        self.business_hours_end = business_hours_end
        self._agent: Any = None

    async def _get_agent(self) -> Any:
        """Lazy-initialize the LangChain DeepAgent."""
        if self._agent is None:
            try:
                from langchain_deepagents import create_deep_agent

                self._agent = create_deep_agent(
                    tools=[self._check_overlap_tool, self._check_business_hours_tool],
                    instructions=(
                        "You are a conflict detection agent. Analyze schedules "
                        "and detect double bookings, business hours violations, "
                        "and insufficient notice periods."
                    ),
                )
            except ImportError:
                logger.warning("langchain-deepagents not available, using direct conflict detection")
                self._agent = None
        return self._agent

    async def _check_overlap_tool(
        self, start1: datetime, end1: datetime, start2: datetime, end2: datetime
    ) -> bool:
        """Tool for checking if two time ranges overlap."""
        return self._ranges_overlap(start1, end1, start2, end2)

    async def _check_business_hours_tool(
        self, dt: datetime, start_hour: int, end_hour: int
    ) -> bool:
        """Tool for checking if a time is within business hours."""
        return self._is_within_business_hours(dt, start_hour, end_hour)

    def _ranges_overlap(
        self, start1: datetime, end1: datetime, start2: datetime, end2: datetime
    ) -> bool:
        """Check if two time ranges overlap."""
        return start1 < end2 and start2 < end1

    def _is_within_business_hours(
        self, dt: datetime, start_hour: int, end_hour: int
    ) -> bool:
        """Check if a datetime falls within business hours."""
        return start_hour <= dt.hour < end_hour

    def detect_double_booking(
        self,
        interview: Interview,
        existing_interviews: list[Interview],
    ) -> list[Conflict]:
        """Detect double booking conflicts.

        Args:
            interview: The interview to check.
            existing_interviews: Existing interviews to compare against.

        Returns:
            List of detected conflicts.
        """
        conflicts: list[Conflict] = []
        if not interview.scheduled_at:
            return conflicts

        interview_end = interview.scheduled_at + timedelta(minutes=interview.duration_minutes)

        for existing in existing_interviews:
            if existing.id == interview.id or not existing.scheduled_at:
                continue
            existing_end = existing.scheduled_at + timedelta(minutes=existing.duration_minutes)
            if self._ranges_overlap(
                interview.scheduled_at, interview_end, existing.scheduled_at, existing_end
            ):
                conflicts.append(
                    Conflict(
                        interview_id=interview.id,
                        conflict_type=ConflictType.DOUBLE_BOOKING,
                        severity=ConflictSeverity.HIGH,
                        description=(
                            f"Double booking detected with interview {existing.id} "
                            f"({existing.title})"
                        ),
                        conflicting_interview_id=existing.id,
                    )
                )
        return conflicts

    def detect_business_hours_violation(
        self,
        interview: Interview,
        timezone: str = "UTC",
    ) -> list[Conflict]:
        """Detect if an interview is outside business hours.

        Args:
            interview: The interview to check.
            timezone: Timezone to check business hours in.

        Returns:
            List containing a conflict if outside business hours.
        """
        conflicts: list[Conflict] = []
        if not interview.scheduled_at:
            return conflicts

        from interview_scheduler.agents.timezone_resolver import TimezoneResolverAgent

        tz_agent = TimezoneResolverAgent()
        local_time = tz_agent.convert_time(
            interview.scheduled_at, "UTC", timezone
        )
        end_time = local_time + timedelta(minutes=interview.duration_minutes)

        if not (
            self._is_within_business_hours(local_time, self.business_hours_start, self.business_hours_end)
            and end_time.hour <= self.business_hours_end
        ):
            conflicts.append(
                Conflict(
                    interview_id=interview.id,
                    conflict_type=ConflictType.OUTSIDE_BUSINESS_HOURS,
                    severity=ConflictSeverity.MEDIUM,
                    description=(
                        f"Interview scheduled outside business hours "
                        f"({self.business_hours_start}:00-{self.business_hours_end}:00 {timezone})"
                    ),
                )
            )
        return conflicts

    def detect_insufficient_notice(
        self,
        interview: Interview,
        now: datetime | None = None,
    ) -> list[Conflict]:
        """Detect if an interview has insufficient scheduling notice.

        Args:
            interview: The interview to check.
            now: Reference time (defaults to current UTC).

        Returns:
            List containing a conflict if notice is insufficient.
        """
        conflicts: list[Conflict] = []
        if not interview.scheduled_at:
            return conflicts

        if now is None:
            now = datetime.utcnow()

        notice_period = interview.scheduled_at - now
        if notice_period < timedelta(hours=self.min_notice_hours):
            conflicts.append(
                Conflict(
                    interview_id=interview.id,
                    conflict_type=ConflictType.INSUFFICIENT_NOTICE,
                    severity=ConflictSeverity.LOW,
                    description=(
                        f"Insufficient notice: {notice_period.total_seconds() / 3600:.1f}h "
                        f"(minimum {self.min_notice_hours}h required)"
                    ),
                )
            )
        return conflicts

    def detect_all_conflicts(
        self,
        interview: Interview,
        existing_interviews: list[Interview],
        timezone: str = "UTC",
    ) -> list[Conflict]:
        """Run all conflict detection checks.

        Args:
            interview: The interview to check.
            existing_interviews: Existing interviews to compare against.
            timezone: Timezone for business hours check.

        Returns:
            List of all detected conflicts.
        """
        conflicts: list[Conflict] = []
        conflicts.extend(self.detect_double_booking(interview, existing_interviews))
        conflicts.extend(self.detect_business_hours_violation(interview, timezone))
        conflicts.extend(self.detect_insufficient_notice(interview))
        return conflicts
