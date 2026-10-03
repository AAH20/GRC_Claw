"""Unit tests for the interview scheduler module."""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def scheduler():
    """Return a fresh InterviewScheduler instance."""
    from src.agents.interview_scheduler import InterviewScheduler

    return InterviewScheduler()


@pytest.fixture
def candidate():
    """Return a sample candidate profile."""
    return {
        "id": "cand-001",
        "name": "Alice Johnson",
        "email": "alice@example.com",
        "timezone": "UTC",
    }


@pytest.fixture
def interviewer():
    """Return a sample interviewer profile."""
    return {
        "id": "int-001",
        "name": "Bob Smith",
        "email": "bob@example.com",
        "timezone": "UTC",
    }


@pytest.fixture
def base_time():
    """Return a fixed base datetime for deterministic tests."""
    return datetime(2026, 10, 15, 9, 0, 0)


@pytest.fixture
def availability_window(base_time):
    """Return a standard availability window (9 AM – 5 PM)."""
    return {
        "start": base_time,
        "end": base_time + timedelta(hours=8),
    }


@pytest.fixture
def mock_calendar_service():
    """Return a mocked calendar service."""
    service = MagicMock()
    service.get_availability.return_value = []
    service.create_event.return_value = {"id": "evt-001", "status": "confirmed"}
    service.update_event.return_value = {"id": "evt-001", "status": "updated"}
    service.delete_event.return_value = True
    return service


# ---------------------------------------------------------------------------
# Tests: schedule_interview
# ---------------------------------------------------------------------------


class TestScheduleInterview:
    """Tests for scheduling a new interview."""

    def test_schedule_interview_success(
        self, scheduler, candidate, interviewer, base_time, mock_calendar_service
    ):
        """Successfully schedule an interview and return event details."""
        scheduler.calendar = mock_calendar_service

        result = scheduler.schedule_interview(
            candidate_id=candidate["id"],
            interviewer_id=interviewer["id"],
            start_time=base_time,
            duration_minutes=60,
        )

        assert result is not None
        assert result["candidate_id"] == candidate["id"]
        assert result["interviewer_id"] == interviewer["id"]
        assert result["start_time"] == base_time
        assert result["duration_minutes"] == 60
        assert result["status"] == "scheduled"
        mock_calendar_service.create_event.assert_called_once()

    def test_schedule_interview_with_custom_duration(
        self, scheduler, candidate, interviewer, base_time, mock_calendar_service
    ):
        """Schedule an interview with a non-default duration."""
        scheduler.calendar = mock_calendar_service

        result = scheduler.schedule_interview(
            candidate_id=candidate["id"],
            interviewer_id=interviewer["id"],
            start_time=base_time,
            duration_minutes=30,
        )

        assert result["duration_minutes"] == 30

    def test_schedule_interview_past_time_raises(
        self, scheduler, candidate, interviewer, mock_calendar_service
    ):
        """Scheduling in the past raises a ValueError."""
        scheduler.calendar = mock_calendar_service
        past_time = datetime(2020, 1, 1, 12, 0, 0)

        with pytest.raises(ValueError, match="past"):
            scheduler.schedule_interview(
                candidate_id=candidate["id"],
                interviewer_id=interviewer["id"],
                start_time=past_time,
                duration_minutes=60,
            )

    def test_schedule_interview_conflict_raises(
        self, scheduler, candidate, interviewer, base_time, mock_calendar_service
    ):
        """Scheduling over an existing event raises a conflict error."""
        scheduler.calendar = mock_calendar_service
        mock_calendar_service.get_availability.return_value = [
            {
                "start": base_time,
                "end": base_time + timedelta(hours=1),
                "event_id": "existing-001",
            }
        ]

        with pytest.raises(ValueError, match="conflict"):
            scheduler.schedule_interview(
                candidate_id=candidate["id"],
                interviewer_id=interviewer["id"],
                start_time=base_time,
                duration_minutes=60,
            )

    def test_schedule_interview_sends_invites(
        self, scheduler, candidate, interviewer, base_time, mock_calendar_service
    ):
        """Scheduling triggers calendar invites for both parties."""
        scheduler.calendar = mock_calendar_service
        scheduler.send_invite = MagicMock()

        scheduler.schedule_interview(
            candidate_id=candidate["id"],
            interviewer_id=interviewer["id"],
            start_time=base_time,
            duration_minutes=60,
        )

        scheduler.send_invite.assert_called_once()


# ---------------------------------------------------------------------------
# Tests: reschedule_interview
# ---------------------------------------------------------------------------


class TestRescheduleInterview:
    """Tests for rescheduling an existing interview."""

    def test_reschedule_interview_success(
        self, scheduler, candidate, interviewer, base_time, mock_calendar_service
    ):
        """Successfully reschedule an existing interview."""
        scheduler.calendar = mock_calendar_service
        new_time = base_time + timedelta(days=1)

        result = scheduler.reschedule_interview(
            event_id="evt-001",
            new_start_time=new_time,
        )

        assert result is not None
        assert result["event_id"] == "evt-001"
        assert result["start_time"] == new_time
        assert result["status"] == "rescheduled"
        mock_calendar_service.update_event.assert_called_once()

    def test_reschedule_interview_not_found_raises(
        self, scheduler, base_time, mock_calendar_service
    ):
        """Rescheduling a non-existent event raises an error."""
        scheduler.calendar = mock_calendar_service
        mock_calendar_service.update_event.side_effect = KeyError("evt-999")

        with pytest.raises(KeyError):
            scheduler.reschedule_interview(
                event_id="evt-999",
                new_start_time=base_time,
            )

    def test_reschedule_interview_same_time_no_op(
        self, scheduler, base_time, mock_calendar_service
    ):
        """Rescheduling to the same time is a no-op."""
        scheduler.calendar = mock_calendar_service

        result = scheduler.reschedule_interview(
            event_id="evt-001",
            new_start_time=base_time,
        )

        assert result["status"] == "unchanged"
        mock_calendar_service.update_event.assert_not_called()

    def test_reschedule_interview_notifies_parties(
        self, scheduler, base_time, mock_calendar_service
    ):
        """Rescheduling sends updated invites to all participants."""
        scheduler.calendar = mock_calendar_service
        scheduler.send_invite = MagicMock()
        new_time = base_time + timedelta(hours=2)

        scheduler.reschedule_interview(
            event_id="evt-001",
            new_start_time=new_time,
        )

        scheduler.send_invite.assert_called_once()

    def test_reschedule_interview_preserves_duration(
        self, scheduler, base_time, mock_calendar_service
    ):
        """Rescheduling preserves the original interview duration."""
        scheduler.calendar = mock_calendar_service
        original_duration = 45
        new_time = base_time + timedelta(days=2)

        result = scheduler.reschedule_interview(
            event_id="evt-001",
            new_start_time=new_time,
            duration_minutes=original_duration,
        )

        assert result["duration_minutes"] == original_duration


# ---------------------------------------------------------------------------
# Tests: find_optimal_slot
# ---------------------------------------------------------------------------


class TestFindOptimalSlot:
    """Tests for finding the optimal interview slot."""

    def test_find_optimal_slot_returns_earliest_available(
        self, scheduler, candidate, interviewer, base_time, availability_window
    ):
        """Returns the earliest slot that fits both parties."""
        busy_slots = []

        result = scheduler.find_optimal_slot(
            candidate_id=candidate["id"],
            interviewer_id=interviewer["id"],
            availability=availability_window,
            duration_minutes=60,
            busy_slots=busy_slots,
        )

        assert result is not None
        assert result["start_time"] == base_time
        assert result["end_time"] == base_time + timedelta(minutes=60)

    def test_find_optimal_slot_skips_busy_periods(
        self, scheduler, candidate, interviewer, base_time, availability_window
    ):
        """Skips over busy periods to find the next available slot."""
        busy_start = base_time
        busy_end = base_time + timedelta(hours=2)
        busy_slots = [{"start": busy_start, "end": busy_end}]

        result = scheduler.find_optimal_slot(
            candidate_id=candidate["id"],
            interviewer_id=interviewer["id"],
            availability=availability_window,
            duration_minutes=60,
            busy_slots=busy_slots,
        )

        assert result is not None
        assert result["start_time"] >= busy_end

    def test_find_optimal_slot_no_fit_returns_none(
        self, scheduler, candidate, interviewer, base_time
    ):
        """Returns None when no slot fits the required duration."""
        availability = {
            "start": base_time,
            "end": base_time + timedelta(minutes=30),
        }

        result = scheduler.find_optimal_slot(
            candidate_id=candidate["id"],
            interviewer_id=interviewer["id"],
            availability=availability,
            duration_minutes=60,
            busy_slots=[],
        )

        assert result is None

    def test_find_optimal_slot_respects_multiple_busy_slots(
        self, scheduler, candidate, interviewer, base_time, availability_window
    ):
        """Correctly handles multiple non-overlapping busy slots."""
        busy_slots = [
            {"start": base_time, "end": base_time + timedelta(hours=1)},
            {
                "start": base_time + timedelta(hours=2),
                "end": base_time + timedelta(hours=3),
            },
        ]

        result = scheduler.find_optimal_slot(
            candidate_id=candidate["id"],
            interviewer_id=interviewer["id"],
            availability=availability_window,
            duration_minutes=60,
            busy_slots=busy_slots,
        )

        assert result is not None
        # Should fit in the gap between the two busy slots
        assert result["start_time"] >= base_time + timedelta(hours=1)
        assert result["end_time"] <= base_time + timedelta(hours=2)

    def test_find_optimal_slot_with_timezone_conversion(
        self, scheduler, base_time, availability_window
    ):
        """Handles candidates and interviewers in different timezones."""
        candidate_tz = "America/New_York"
        interviewer_tz = "Europe/London"

        result = scheduler.find_optimal_slot(
            candidate_id="cand-tz",
            interviewer_id="int-tz",
            availability=availability_window,
            duration_minutes=60,
            busy_slots=[],
            candidate_timezone=candidate_tz,
            interviewer_timezone=interviewer_tz,
        )

        assert result is not None
        assert "start_time" in result
        assert "end_time" in result

    def test_find_optimal_slot_fully_booked_returns_none(
        self, scheduler, candidate, interviewer, base_time
    ):
        """Returns None when the entire window is busy."""
        availability = {
            "start": base_time,
            "end": base_time + timedelta(hours=8),
        }
        busy_slots = [{"start": base_time, "end": base_time + timedelta(hours=8)}]

        result = scheduler.find_optimal_slot(
            candidate_id=candidate["id"],
            interviewer_id=interviewer["id"],
            availability=availability,
            duration_minutes=60,
            busy_slots=busy_slots,
        )

        assert result is None
