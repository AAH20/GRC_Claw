"""
Interview Scheduler Agent for Recruitment Platform.

Provides intelligent interview scheduling with conflict detection,
optimal slot selection, and reschedule management.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class InterviewType(str, Enum):
    PHONE_SCREEN = "phone_screen"
    TECHNICAL = "technical"
    BEHAVIORAL = "behavioral"
    PANEL = "panel"
    FINAL = "final"


class InterviewStatus(str, Enum):
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    RESCHEDULED = "rescheduled"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    NO_SHOW = "no_show"


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------


@dataclass
class TimeSlot:
    """Represents an available time slot for an interview."""

    start_time: datetime
    end_time: datetime
    interviewer_ids: List[str] = field(default_factory=list)

    def overlaps(self, other: "TimeSlot") -> bool:
        """Check if this slot overlaps with another."""
        return self.start_time < other.end_time and other.start_time < self.end_time

    def duration_minutes(self) -> int:
        """Return slot duration in minutes."""
        return int((self.end_time - self.start_time).total_seconds() / 60)


@dataclass
class Interviewer:
    """Represents an interviewer with availability and metadata."""

    id: str
    name: str
    email: str
    department: str
    role: str
    max_daily_interviews: int = 5
    unavailable_slots: List[TimeSlot] = field(default_factory=list)


@dataclass
class Interview:
    """Represents a scheduled interview."""

    id: str
    candidate_id: str
    job_id: str
    interview_type: InterviewType
    status: InterviewStatus
    scheduled_time: datetime
    duration_minutes: int
    interviewer_ids: List[str]
    location: str = "Video Call"
    notes: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Mock Data Store
# ---------------------------------------------------------------------------


class MockDataStore:
    """In-memory mock data store for interview scheduling."""

    def __init__(self) -> None:
        self.interviews: Dict[str, Interview] = {}
        self.interviewers: Dict[str, Interviewer] = {}
        self.candidate_schedules: Dict[str, List[TimeSlot]] = {}
        self._seed_data()

    def _seed_data(self) -> None:
        """Seed the store with realistic mock data."""
        # Mock interviewers
        interviewers_data = [
            ("int_001", "Sarah Chen", "sarah.chen@recruitment.io", "Engineering", "Senior Engineering Manager"),
            ("int_002", "Marcus Johnson", "marcus.j@recruitment.io", "Engineering", "Staff Engineer"),
            ("int_003", "Priya Patel", "priya.p@recruitment.io", "Product", "Product Director"),
            ("int_004", "David Kim", "david.kim@recruitment.io", "Design", "Design Lead"),
            ("int_005", "Elena Rodriguez", "elena.r@recruitment.io", "HR", "Talent Acquisition Lead"),
            ("int_006", "James Wilson", "james.w@recruitment.io", "Engineering", "Principal Engineer"),
            ("int_007", "Aisha Mohammed", "aisha.m@recruitment.io", "Data Science", "ML Engineering Manager"),
            ("int_008", "Tom Baker", "tom.b@recruitment.io", "Engineering", "DevOps Lead"),
        ]
        for iid, name, email, dept, role in interviewers_data:
            self.interviewers[iid] = Interviewer(
                id=iid, name=name, email=email, department=dept, role=role
            )

        # Mock candidate busy slots
        now = datetime.utcnow()
        self.candidate_schedules = {
            "cand_001": [
                TimeSlot(now + timedelta(hours=2), now + timedelta(hours=3)),
                TimeSlot(now + timedelta(days=1, hours=10), now + timedelta(days=1, hours=11)),
            ],
            "cand_002": [
                TimeSlot(now + timedelta(hours=4), now + timedelta(hours=5, minutes=30)),
            ],
            "cand_003": [],
        }

        # Mock existing interviews
        existing = [
            Interview(
                id="ivw_existing_001",
                candidate_id="cand_001",
                job_id="job_001",
                interview_type=InterviewType.TECHNICAL,
                status=InterviewStatus.CONFIRMED,
                scheduled_time=now + timedelta(hours=2),
                duration_minutes=60,
                interviewer_ids=["int_001", "int_002"],
            ),
            Interview(
                id="ivw_existing_002",
                candidate_id="cand_002",
                job_id="job_002",
                interview_type=InterviewType.PHONE_SCREEN,
                status=InterviewStatus.SCHEDULED,
                scheduled_time=now + timedelta(hours=4),
                duration_minutes=30,
                interviewer_ids=["int_005"],
            ),
        ]
        for ivw in existing:
            self.interviews[ivw.id] = ivw

    def get_interviewer(self, interviewer_id: str) -> Optional[Interviewer]:
        return self.interviewers.get(interviewer_id)

    def get_candidate_busy_slots(self, candidate_id: str) -> List[TimeSlot]:
        return self.candidate_schedules.get(candidate_id, [])

    def get_interviewer_busy_slots(self, interviewer_id: str) -> List[TimeSlot]:
        """Get all time slots where the interviewer is already booked."""
        busy: List[TimeSlot] = []
        for ivw in self.interviews.values():
            if interviewer_id in ivw.interviewer_ids and ivw.status not in (
                InterviewStatus.CANCELLED,
            ):
                busy.append(
                    TimeSlot(
                        start_time=ivw.scheduled_time,
                        end_time=ivw.scheduled_time + timedelta(minutes=ivw.duration_minutes),
                    )
                )
        return busy

    def add_interview(self, interview: Interview) -> None:
        self.interviews[interview.id] = interview

    def get_interview(self, interview_id: str) -> Optional[Interview]:
        return self.interviews.get(interview_id)

    def update_interview(self, interview: Interview) -> None:
        interview.updated_at = datetime.utcnow()
        self.interviews[interview.id] = interview


# ---------------------------------------------------------------------------
# Interview Scheduler Agent
# ---------------------------------------------------------------------------


class InterviewSchedulerAgent:
    """
    Agent responsible for scheduling and rescheduling interviews.

    Uses a scoring algorithm to find optimal time slots based on:
    - Interviewer availability
    - Candidate availability
    - Interviewer workload balance
    - Proximity to business hours
    """

    DEFAULT_DURATION_MINUTES: int = 60
    BUSINESS_HOURS_START: int = 9
    BUSINESS_HOURS_END: int = 17

    def __init__(self, data_store: Optional[MockDataStore] = None) -> None:
        self.data_store = data_store or MockDataStore()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def schedule_interview(
        self,
        candidate_id: str,
        job_id: str,
        interviewers: List[str],
        time_slots: List[TimeSlot],
        interview_type: InterviewType = InterviewType.TECHNICAL,
        duration_minutes: int = DEFAULT_DURATION_MINUTES,
        location: str = "Video Call",
        notes: str = "",
    ) -> Tuple[Interview, TimeSlot]:
        """
        Find the optimal time slot and schedule an interview.

        Evaluates all candidate slots against interviewer availability,
        candidate availability, workload balance, and business-hours fit.
        Returns the created Interview and the chosen TimeSlot.

        Raises:
            ValueError: If no suitable slot is found.
        """
        if not interviewers:
            raise ValueError("At least one interviewer must be provided.")
        if not time_slots:
            raise ValueError("At least one time slot must be provided.")

        # Validate all interviewers exist
        for iid in interviewers:
            if self.data_store.get_interviewer(iid) is None:
                raise ValueError(f"Unknown interviewer: {iid}")

        # Score each slot
        scored_slots: List[Tuple[float, TimeSlot]] = []
        for slot in time_slots:
            score = self._score_slot(
                slot=slot,
                candidate_id=candidate_id,
                interviewer_ids=interviewers,
                duration_minutes=duration_minutes,
            )
            if score > 0:
                scored_slots.append((score, slot))

        if not scored_slots:
            raise ValueError(
                "No suitable time slot found. All slots conflict with "
                "interviewer or candidate availability."
            )

        # Pick the highest-scoring slot
        scored_slots.sort(key=lambda x: x[0], reverse=True)
        best_score, best_slot = scored_slots[0]

        # Create the interview
        interview = Interview(
            id=f"ivw_{uuid.uuid4().hex[:12]}",
            candidate_id=candidate_id,
            job_id=job_id,
            interview_type=interview_type,
            status=InterviewStatus.SCHEDULED,
            scheduled_time=best_slot.start_time,
            duration_minutes=duration_minutes,
            interviewer_ids=list(interviewers),
            location=location,
            notes=notes,
            metadata={
                "scheduling_score": round(best_score, 2),
                "alternatives_considered": len(scored_slots),
            },
        )

        self.data_store.add_interview(interview)
        return interview, best_slot

    def reschedule_interview(
        self,
        interview_id: str,
        new_time: datetime,
        duration_minutes: Optional[int] = None,
        reason: str = "",
    ) -> Interview:
        """
        Reschedule an existing interview to a new time.

        Validates that all interviewers are available at the new time
        and that the candidate has no conflicts.

        Raises:
            ValueError: If the interview is not found or the new time
                        has conflicts.
        """
        interview = self.data_store.get_interview(interview_id)
        if interview is None:
            raise ValueError(f"Interview not found: {interview_id}")

        duration = duration_minutes or interview.duration_minutes
        new_slot = TimeSlot(
            start_time=new_time,
            end_time=new_time + timedelta(minutes=duration),
        )

        # Check interviewer availability
        for iid in interview.interviewer_ids:
            for busy in self.data_store.get_interviewer_busy_slots(iid):
                if new_slot.overlaps(busy):
                    interviewer = self.data_store.get_interviewer(iid)
                    raise ValueError(
                        f"Interviewer {interviewer.name if interviewer else iid} "
                        f"is not available at {new_time.isoformat()}"
                    )

        # Check candidate availability
        for busy in self.data_store.get_candidate_busy_slots(interview.candidate_id):
            if new_slot.overlaps(busy):
                raise ValueError(
                    f"Candidate has a conflict at {new_time.isoformat()}"
                )

        # Update the interview
        old_time = interview.scheduled_time
        interview.scheduled_time = new_time
        interview.duration_minutes = duration
        interview.status = InterviewStatus.RESCHEDULED
        interview.metadata["reschedule_reason"] = reason
        interview.metadata["previous_time"] = old_time.isoformat()
        interview.metadata["rescheduled_at"] = datetime.utcnow().isoformat()

        self.data_store.update_interview(interview)
        return interview

    # ------------------------------------------------------------------
    # Scoring & Helpers
    # ------------------------------------------------------------------

    def _score_slot(
        self,
        slot: TimeSlot,
        candidate_id: str,
        interviewer_ids: List[str],
        duration_minutes: int,
    ) -> float:
        """
        Score a time slot from 0.0 (unusable) to 100.0 (perfect).

        Returns 0.0 if the slot has any hard conflicts.
        """
        # --- Hard constraints ---

        # Slot must be long enough
        if slot.duration_minutes() < duration_minutes:
            return 0.0

        # Candidate must be free
        for busy in self.data_store.get_candidate_busy_slots(candidate_id):
            if slot.overlaps(busy):
                return 0.0

        # All interviewers must be free
        for iid in interviewer_ids:
            for busy in self.data_store.get_interviewer_busy_slots(iid):
                if slot.overlaps(busy):
                    return 0.0

        # --- Soft scoring ---

        score = 50.0  # base score for passing hard constraints

        # Business hours bonus (peak at 10:00-15:00)
        hour = slot.start_time.hour
        if self.BUSINESS_HOURS_START <= hour < self.BUSINESS_HOURS_END:
            score += 20.0
            # Peak hours bonus
            if 10 <= hour <= 15:
                score += 10.0
        else:
            score -= 15.0

        # Workload balance: prefer interviewers with fewer daily interviews
        workload_penalty = 0.0
        for iid in interviewer_ids:
            daily_count = self._count_daily_interviews(iid, slot.start_time.date())
            workload_penalty += daily_count * 3.0
        score -= workload_penalty

        # Prefer sooner slots (slight recency bias)
        hours_from_now = (slot.start_time - datetime.utcnow()).total_seconds() / 3600
        if hours_from_now < 24:
            score += 5.0
        elif hours_from_now > 72:
            score -= 5.0

        # Prefer slots with more interviewer overlap (panel efficiency)
        if len(interviewer_ids) > 1:
            score += 5.0

        return max(0.0, min(100.0, score))

    def _count_daily_interviews(self, interviewer_id: str, date: datetime.date) -> int:
        """Count how many interviews an interviewer has on a given date."""
        count = 0
        for ivw in self.data_store.interviews.values():
            if (
                interviewer_id in ivw.interviewer_ids
                and ivw.scheduled_time.date() == date
                and ivw.status != InterviewStatus.CANCELLED
            ):
                count += 1
        return count

    def get_interviewer_availability(
        self,
        interviewer_id: str,
        date: datetime.date,
    ) -> List[TimeSlot]:
        """Get free slots for an interviewer on a given date."""
        interviewer = self.data_store.get_interviewer(interviewer_id)
        if interviewer is None:
            return []

        busy = self.data_store.get_interviewer_busy_slots(interviewer_id)
        free_slots: List[TimeSlot] = []

        # Generate 1-hour slots within business hours
        for hour in range(self.BUSINESS_HOURS_START, self.BUSINESS_HOURS_END):
            slot_start = datetime(date.year, date.month, date.day, hour)
            slot_end = slot_start + timedelta(hours=1)
            candidate = TimeSlot(start_time=slot_start, end_time=slot_end)

            if not any(candidate.overlaps(b) for b in busy):
                free_slots.append(candidate)

        return free_slots


# ---------------------------------------------------------------------------
# Module-level convenience functions
# ---------------------------------------------------------------------------

_default_agent = InterviewSchedulerAgent()


def schedule_interview(
    candidate_id: str,
    job_id: str,
    interviewers: List[str],
    time_slots: List[TimeSlot],
    interview_type: InterviewType = InterviewType.TECHNICAL,
    duration_minutes: int = 60,
    location: str = "Video Call",
    notes: str = "",
) -> Tuple[Interview, TimeSlot]:
    """Schedule an interview using the default agent instance."""
    return _default_agent.schedule_interview(
        candidate_id=candidate_id,
        job_id=job_id,
        interviewers=interviewers,
        time_slots=time_slots,
        interview_type=interview_type,
        duration_minutes=duration_minutes,
        location=location,
        notes=notes,
    )


def reschedule_interview(
    interview_id: str,
    new_time: datetime,
    duration_minutes: Optional[int] = None,
    reason: str = "",
) -> Interview:
    """Reschedule an interview using the default agent instance."""
    return _default_agent.reschedule_interview(
        interview_id=interview_id,
        new_time=new_time,
        duration_minutes=duration_minutes,
        reason=reason,
    )
