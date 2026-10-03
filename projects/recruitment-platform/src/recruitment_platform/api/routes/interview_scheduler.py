"""Interview scheduler API endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.post("/optimize-slots")
async def optimize_slots(data: dict[str, Any]) -> dict[str, Any]:
    """Find optimal interview time slots.

    Args:
        data: Dictionary with 'participants' and their availabilities.

    Returns:
        Optimal time slots.
    """
    try:
        from recruitment_platform.agents.interview_scheduler.availability_optimizer import AvailabilityOptimizer

        agent = AvailabilityOptimizer()
        result = await agent.process(data)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/detect-conflicts")
async def detect_conflicts(data: dict[str, Any]) -> dict[str, Any]:
    """Detect scheduling conflicts.

    Args:
        data: Dictionary with 'proposed_slot' and 'existing_events'.

    Returns:
        Detected conflicts.
    """
    from recruitment_platform.agents.interview_scheduler.conflict_detector import ConflictDetector

    agent = ConflictDetector()
    result = await agent.process(data)
    return {"success": True, "data": result}


@router.post("/send-reminder")
async def send_reminder(data: dict[str, Any]) -> dict[str, Any]:
    """Send interview reminder.

    Args:
        data: Dictionary with 'interview' and 'reminder_type'.

    Returns:
        Reminder delivery status.
    """
    from recruitment_platform.agents.interview_scheduler.reminder import Reminder

    agent = Reminder()
    result = await agent.process(data)
    return {"success": True, "data": result}
