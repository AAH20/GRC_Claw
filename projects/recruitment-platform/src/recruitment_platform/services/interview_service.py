"""Interview service for the recruitment platform."""

from __future__ import annotations

from datetime import datetime
from typing import Any


class InterviewServiceError(Exception):
    """Base exception for interview service errors."""


class ValidationError(InterviewServiceError):
    """Raised when interview data fails validation."""


class InterviewNotFoundError(InterviewServiceError):
    """Raised when an interview is not found."""


class FeedbackNotFoundError(InterviewServiceError):
    """Raised when feedback for an interview is not found."""


# In-memory store for demonstration purposes.
# Replace with actual database calls in production.
_interviews: dict[str, dict[str, Any]] = {}
_feedback: dict[str, dict[str, Any]] = {}


def schedule_interview(data: dict[str, Any]) -> dict[str, Any]:
    """Schedule a new interview with validation.

    Args:
        data: Dictionary containing interview details.
            Required keys: candidate_id, interviewer_id, scheduled_time.

    Returns:
        The created interview record with an assigned interview_id.

    Raises:
        ValidationError: If required fields are missing or invalid.
    """
    required_fields = ("candidate_id", "interviewer_id", "scheduled_time")
    missing = [f for f in required_fields if f not in data or data[f] is None]
    if missing:
        raise ValidationError(f"Missing required fields: {', '.join(missing)}")

    candidate_id = data["candidate_id"]
    interviewer_id = data["interviewer_id"]
    scheduled_time = data["scheduled_time"]

    if not isinstance(candidate_id, str) or not candidate_id.strip():
        raise ValidationError("candidate_id must be a non-empty string")
    if not isinstance(interviewer_id, str) or not interviewer_id.strip():
        raise ValidationError("interviewer_id must be a non-empty string")

    if isinstance(scheduled_time, str):
        try:
            scheduled_time = datetime.fromisoformat(scheduled_time)
        except ValueError as exc:
            raise ValidationError(
                "scheduled_time must be a valid ISO format datetime string"
            ) from exc
    elif not isinstance(scheduled_time, datetime):
        raise ValidationError("scheduled_time must be a datetime or ISO format string")

    if scheduled_time < datetime.now(scheduled_time.tzinfo):
        raise ValidationError("scheduled_time must be in the future")

    interview_id = f"int_{len(_interviews) + 1:06d}"
    interview = {
        "interview_id": interview_id,
        "candidate_id": candidate_id,
        "interviewer_id": interviewer_id,
        "scheduled_time": scheduled_time,
        "status": "scheduled",
        "feedback": None,
    }
    _interviews[interview_id] = interview
    return interview


def reschedule_interview(interview_id: str, new_time: datetime | str) -> dict[str, Any]:
    """Reschedule an existing interview to a new time.

    Args:
        interview_id: The unique identifier of the interview.
        new_time: The new scheduled time (datetime or ISO format string).

    Returns:
        The updated interview record.

    Raises:
        InterviewNotFoundError: If the interview does not exist.
        ValidationError: If the new time is invalid or in the past.
    """
    if interview_id not in _interviews:
        raise InterviewNotFoundError(f"Interview '{interview_id}' not found")

    if isinstance(new_time, str):
        try:
            new_time = datetime.fromisoformat(new_time)
        except ValueError as exc:
            raise ValidationError(
                "new_time must be a valid ISO format datetime string"
            ) from exc
    elif not isinstance(new_time, datetime):
        raise ValidationError("new_time must be a datetime or ISO format string")

    if new_time < datetime.now(new_time.tzinfo):
        raise ValidationError("new_time must be in the future")

    _interviews[interview_id]["scheduled_time"] = new_time
    _interviews[interview_id]["status"] = "rescheduled"
    return _interviews[interview_id]


def get_interview_feedback(interview_id: str) -> dict[str, Any]:
    """Get feedback for a specific interview.

    Args:
        interview_id: The unique identifier of the interview.

    Returns:
        The feedback record for the interview.

    Raises:
        InterviewNotFoundError: If the interview does not exist.
        FeedbackNotFoundError: If no feedback exists for the interview.
    """
    if interview_id not in _interviews:
        raise InterviewNotFoundError(f"Interview '{interview_id}' not found")

    if interview_id not in _feedback:
        raise FeedbackNotFoundError(
            f"No feedback found for interview '{interview_id}'"
        )

    return _feedback[interview_id]
