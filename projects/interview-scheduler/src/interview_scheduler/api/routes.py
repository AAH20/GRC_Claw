"""API routes for interview scheduler."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status

from interview_scheduler.models.conflict import Conflict, ConflictCreate, ConflictResolution
from interview_scheduler.models.interview import Interview, InterviewCreate, InterviewUpdate
from interview_scheduler.models.reminder import Reminder, ReminderCreate, ReminderUpdate
from interview_scheduler.models.schedule import Schedule, ScheduleCreate, ScheduleUpdate
from interview_scheduler.models.timeslot import TimeSlotRequest, TimeSlotResponse
from interview_scheduler.services.interview_service import InterviewService

logger = logging.getLogger(__name__)

router = APIRouter()


def get_interview_service() -> InterviewService:
    """Dependency to get the interview service.

    Returns:
        InterviewService instance.
    """
    return InterviewService()


# Health check
@router.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    """Health check endpoint.

    Returns:
        Health status.
    """
    return {"status": "healthy", "service": "interview-scheduler"}


# Interview routes
@router.get("/api/v1/interviews", response_model=list[Interview], tags=["interviews"])
async def list_interviews(
    status_filter: str | None = Query(None, alias="status"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    service: Annotated[InterviewService, Depends(get_interview_service)] = None,
) -> list[Interview]:
    """List interviews.

    Args:
        status_filter: Filter by status.
        limit: Maximum results.
        offset: Pagination offset.
        service: Interview service.

    Returns:
        List of interviews.
    """
    return service.list_interviews(status=status_filter, limit=limit, offset=offset)


@router.post(
    "/api/v1/interviews",
    response_model=Interview,
    status_code=status.HTTP_201_CREATED,
    tags=["interviews"],
)
async def create_interview(
    data: InterviewCreate,
    service: Annotated[InterviewService, Depends(get_interview_service)] = None,
) -> Interview:
    """Create a new interview.

    Args:
        data: Interview creation data.
        service: Interview service.

    Returns:
        The created interview.
    """
    return service.create_interview(data)


@router.get("/api/v1/interviews/{interview_id}", response_model=Interview, tags=["interviews"])
async def get_interview(
    interview_id: str,
    service: Annotated[InterviewService, Depends(get_interview_service)] = None,
) -> Interview:
    """Get an interview by ID.

    Args:
        interview_id: The interview ID.
        service: Interview service.

    Returns:
        The interview.

    Raises:
        HTTPException: If interview not found.
    """
    interview = service.get_interview(interview_id)
    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Interview {interview_id} not found",
        )
    return interview


@router.put("/api/v1/interviews/{interview_id}", response_model=Interview, tags=["interviews"])
async def update_interview(
    interview_id: str,
    data: InterviewUpdate,
    service: Annotated[InterviewService, Depends(get_interview_service)] = None,
) -> Interview:
    """Update an interview.

    Args:
        interview_id: The interview ID.
        data: Update data.
        service: Interview service.

    Returns:
        The updated interview.

    Raises:
        HTTPException: If interview not found.
    """
    interview = service.update_interview(interview_id, data)
    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Interview {interview_id} not found",
        )
    return interview


@router.delete(
    "/api/v1/interviews/{interview_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["interviews"],
)
async def delete_interview(
    interview_id: str,
    service: Annotated[InterviewService, Depends(get_interview_service)] = None,
) -> None:
    """Delete an interview.

    Args:
        interview_id: The interview ID.
        service: Interview service.

    Raises:
        HTTPException: If interview not found.
    """
    if not service.delete_interview(interview_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Interview {interview_id} not found",
        )


# Schedule routes
@router.get("/api/v1/schedules", response_model=list[Schedule], tags=["schedules"])
async def list_schedules(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    service: Annotated[InterviewService, Depends(get_interview_service)] = None,
) -> list[Schedule]:
    """List schedules.

    Args:
        limit: Maximum results.
        offset: Pagination offset.
        service: Interview service.

    Returns:
        List of schedules.
    """
    return service.list_schedules(limit=limit, offset=offset)


@router.post(
    "/api/v1/schedules",
    response_model=Schedule,
    status_code=status.HTTP_201_CREATED,
    tags=["schedules"],
)
async def create_schedule(
    data: ScheduleCreate,
    service: Annotated[InterviewService, Depends(get_interview_service)] = None,
) -> Schedule:
    """Create a new schedule.

    Args:
        data: Schedule creation data.
        service: Interview service.

    Returns:
        The created schedule.
    """
    return service.create_schedule(data)


@router.get("/api/v1/schedules/{schedule_id}", response_model=Schedule, tags=["schedules"])
async def get_schedule(
    schedule_id: str,
    service: Annotated[InterviewService, Depends(get_interview_service)] = None,
) -> Schedule:
    """Get a schedule by ID.

    Args:
        schedule_id: The schedule ID.
        service: Interview service.

    Returns:
        The schedule.

    Raises:
        HTTPException: If schedule not found.
    """
    schedule = service.get_schedule(schedule_id)
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Schedule {schedule_id} not found",
        )
    return schedule


@router.put("/api/v1/schedules/{schedule_id}", response_model=Schedule, tags=["schedules"])
async def update_schedule(
    schedule_id: str,
    data: ScheduleUpdate,
    service: Annotated[InterviewService, Depends(get_interview_service)] = None,
) -> Schedule:
    """Update a schedule.

    Args:
        schedule_id: The schedule ID.
        data: Update data.
        service: Interview service.

    Returns:
        The updated schedule.

    Raises:
        HTTPException: If schedule not found.
    """
    schedule = service.update_schedule(schedule_id, data)
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Schedule {schedule_id} not found",
        )
    return schedule


@router.delete(
    "/api/v1/schedules/{schedule_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["schedules"],
)
async def delete_schedule(
    schedule_id: str,
    service: Annotated[InterviewService, Depends(get_interview_service)] = None,
) -> None:
    """Delete a schedule.

    Args:
        schedule_id: The schedule ID.
        service: Interview service.

    Raises:
        HTTPException: If schedule not found.
    """
    if not service.delete_schedule(schedule_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Schedule {schedule_id} not found",
        )


# Time slot routes
@router.post("/api/v1/timeslots/find", response_model=TimeSlotResponse, tags=["timeslots"])
async def find_time_slots(
    request: TimeSlotRequest,
    service: Annotated[InterviewService, Depends(get_interview_service)] = None,
) -> TimeSlotResponse:
    """Find available time slots.

    Args:
        request: Time slot search request.
        service: Interview service.

    Returns:
        Available time slots.
    """
    return service.find_time_slots(request)


# Conflict routes
@router.get("/api/v1/conflicts", response_model=list[Conflict], tags=["conflicts"])
async def list_conflicts(
    interview_id: str | None = None,
    status_filter: str | None = Query(None, alias="status"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    service: Annotated[InterviewService, Depends(get_interview_service)] = None,
) -> list[Conflict]:
    """List conflicts.

    Args:
        interview_id: Filter by interview ID.
        status_filter: Filter by status.
        limit: Maximum results.
        offset: Pagination offset.
        service: Interview service.

    Returns:
        List of conflicts.
    """
    return service.list_conflicts(
        interview_id=interview_id, status=status_filter, limit=limit, offset=offset
    )


@router.post(
    "/api/v1/conflicts/detect",
    response_model=list[Conflict],
    status_code=status.HTTP_201_CREATED,
    tags=["conflicts"],
)
async def detect_conflicts(
    interview_id: str,
    service: Annotated[InterviewService, Depends(get_interview_service)] = None,
) -> list[Conflict]:
    """Detect conflicts for an interview.

    Args:
        interview_id: The interview ID.
        service: Interview service.

    Returns:
        List of detected conflicts.

    Raises:
        HTTPException: If interview not found.
    """
    from interview_scheduler.agents.conflict_detector import ConflictDetectorAgent

    interview = service.get_interview(interview_id)
    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Interview {interview_id} not found",
        )

    existing = service.get_all_interviews()
    detector = ConflictDetectorAgent()
    conflicts = detector.detect_all_conflicts(interview, existing)

    stored: list[Conflict] = []
    for conflict in conflicts:
        stored.append(service.create_conflict(ConflictCreate(**conflict.model_dump())))

    return stored


@router.post(
    "/api/v1/conflicts/{conflict_id}/resolve",
    response_model=Conflict,
    tags=["conflicts"],
)
async def resolve_conflict(
    conflict_id: str,
    data: ConflictResolution,
    service: Annotated[InterviewService, Depends(get_interview_service)] = None,
) -> Conflict:
    """Resolve a conflict.

    Args:
        conflict_id: The conflict ID.
        data: Resolution data.
        service: Interview service.

    Returns:
        The resolved conflict.

    Raises:
        HTTPException: If conflict not found.
    """
    conflict = service.resolve_conflict(conflict_id, data.resolution, data.action)
    if not conflict:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conflict {conflict_id} not found",
        )
    return conflict


# Reminder routes
@router.get("/api/v1/reminders", response_model=list[Reminder], tags=["reminders"])
async def list_reminders(
    interview_id: str | None = None,
    status_filter: str | None = Query(None, alias="status"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    service: Annotated[InterviewService, Depends(get_interview_service)] = None,
) -> list[Reminder]:
    """List reminders.

    Args:
        interview_id: Filter by interview ID.
        status_filter: Filter by status.
        limit: Maximum results.
        offset: Pagination offset.
        service: Interview service.

    Returns:
        List of reminders.
    """
    return service.list_reminders(
        interview_id=interview_id, status=status_filter, limit=limit, offset=offset
    )


@router.post(
    "/api/v1/reminders",
    response_model=Reminder,
    status_code=status.HTTP_201_CREATED,
    tags=["reminders"],
)
async def create_reminder(
    data: ReminderCreate,
    service: Annotated[InterviewService, Depends(get_interview_service)] = None,
) -> Reminder:
    """Create a reminder.

    Args:
        data: Reminder creation data.
        service: Interview service.

    Returns:
        The created reminder.
    """
    return service.create_reminder(data)


@router.get("/api/v1/reminders/{reminder_id}", response_model=Reminder, tags=["reminders"])
async def get_reminder(
    reminder_id: str,
    service: Annotated[InterviewService, Depends(get_interview_service)] = None,
) -> Reminder:
    """Get a reminder by ID.

    Args:
        reminder_id: The reminder ID.
        service: Interview service.

    Returns:
        The reminder.

    Raises:
        HTTPException: If reminder not found.
    """
    reminder = service.get_reminder(reminder_id)
    if not reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reminder {reminder_id} not found",
        )
    return reminder


@router.put("/api/v1/reminders/{reminder_id}", response_model=Reminder, tags=["reminders"])
async def update_reminder(
    reminder_id: str,
    data: ReminderUpdate,
    service: Annotated[InterviewService, Depends(get_interview_service)] = None,
) -> Reminder:
    """Update a reminder.

    Args:
        reminder_id: The reminder ID.
        data: Update data.
        service: Interview service.

    Returns:
        The updated reminder.

    Raises:
        HTTPException: If reminder not found.
    """
    reminder = service.update_reminder(reminder_id, **data.model_dump(exclude_unset=True))
    if not reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reminder {reminder_id} not found",
        )
    return reminder


@router.delete(
    "/api/v1/reminders/{reminder_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["reminders"],
)
async def delete_reminder(
    reminder_id: str,
    service: Annotated[InterviewService, Depends(get_interview_service)] = None,
) -> None:
    """Delete a reminder.

    Args:
        reminder_id: The reminder ID.
        service: Interview service.

    Raises:
        HTTPException: If reminder not found.
    """
    if not service.delete_reminder(reminder_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reminder {reminder_id} not found",
        )


# Agent pipeline route
@router.post(
    "/api/v1/agents/schedule",
    response_model=dict[str, Any],
    status_code=status.HTTP_201_CREATED,
    tags=["agents"],
)
async def run_scheduling_pipeline(
    interview_id: str,
    service: Annotated[InterviewService, Depends(get_interview_service)] = None,
) -> dict[str, Any]:
    """Run the full scheduling pipeline for an interview.

    Args:
        interview_id: The interview ID.
        service: Interview service.

    Returns:
        Pipeline results.

    Raises:
        HTTPException: If interview not found.
    """
    from interview_scheduler.agents.availability_optimizer import AvailabilityOptimizerAgent
    from interview_scheduler.agents.conflict_detector import ConflictDetectorAgent
    from interview_scheduler.agents.reminder import ReminderAgent
    from interview_scheduler.agents.timezone_resolver import TimezoneResolverAgent

    interview = service.get_interview(interview_id)
    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Interview {interview_id} not found",
        )

    tz_agent = TimezoneResolverAgent()
    conflict_agent = ConflictDetectorAgent()
    optimizer_agent = AvailabilityOptimizerAgent()
    reminder_agent = ReminderAgent()

    existing = service.get_all_interviews()
    conflicts = conflict_agent.detect_all_conflicts(interview, existing)

    slots: list[Any] = []
    if not interview.scheduled_at:
        from datetime import timedelta

        candidates = optimizer_agent.generate_candidate_slots(
            datetime.utcnow(),
            datetime.utcnow() + timedelta(days=7),
            interview.duration_minutes,
        )
        slots = optimizer_agent.find_optimal_slots(candidates, [], interview.duration_minutes)

    reminders = reminder_agent.create_default_reminders(interview)

    return {
        "interview_id": interview_id,
        "conflicts_detected": len(conflicts),
        "optimal_slots_found": len(slots),
        "reminders_created": len(reminders),
        "timezone_resolved": tz_agent.resolve_participant_timezone(
            interview.preferred_timezones
        ),
    }
