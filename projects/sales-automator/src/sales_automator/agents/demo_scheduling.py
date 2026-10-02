"""Demo scheduling agent — coordinates calendar booking for demos."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


class TimeSlot(BaseModel):
    """An available time slot."""

    start: datetime
    end: datetime
    timezone: str = "UTC"


class DemoBooking(BaseModel):
    """A confirmed demo booking."""

    id: str
    prospect_id: str
    scheduled_at: datetime
    duration_minutes: int = 30
    meeting_url: str | None = None
    status: str = "scheduled"
    metadata: dict[str, Any] = Field(default_factory=dict)


class DemoSchedulingAgent:
    """Coordinates with Google Calendar to find available slots and book demos."""

    def __init__(
        self,
        default_duration_minutes: int = 30,
        buffer_minutes: int = 15,
    ) -> None:
        self.default_duration_minutes = default_duration_minutes
        self.buffer_minutes = buffer_minutes
        self.logger = logger.bind(agent="demo_scheduling")

    async def find_available_slots(
        self,
        prospect_id: str,
        start_date: datetime,
        end_date: datetime,
        duration_minutes: int | None = None,
    ) -> list[TimeSlot]:
        """Find available time slots for a demo.

        Args:
            prospect_id: Prospect to schedule.
            start_date: Start of the search window.
            end_date: End of the search window.
            duration_minutes: Desired duration (defaults to agent default).

        Returns:
            List of available time slots.
        """
        self.logger.info(
            "Finding available slots",
            prospect_id=prospect_id,
            start=start_date,
            end=end_date,
        )
        # In production, this would query Google Calendar API
        return []

    async def book_demo(
        self,
        prospect_id: str,
        slot: TimeSlot,
        duration_minutes: int | None = None,
    ) -> DemoBooking:
        """Book a demo at the specified time slot.

        Args:
            prospect_id: Prospect to book.
            slot: Time slot to book.
            duration_minutes: Duration in minutes.

        Returns:
            Confirmed demo booking.
        """
        self.logger.info("Booking demo", prospect_id=prospect_id, slot=slot)
        # In production, this would create a Google Calendar event
        return DemoBooking(
            id=f"demo_{prospect_id}",
            prospect_id=prospect_id,
            scheduled_at=slot.start,
            duration_minutes=duration_minutes or self.default_duration_minutes,
        )

    async def reschedule(
        self,
        booking_id: str,
        new_slot: TimeSlot,
    ) -> DemoBooking:
        """Reschedule an existing demo.

        Args:
            booking_id: Existing booking ID.
            new_slot: New time slot.

        Returns:
            Updated booking.
        """
        self.logger.info("Rescheduling demo", booking_id=booking_id, new_slot=new_slot)
        # In production, this would update the Google Calendar event
        return DemoBooking(
            id=booking_id,
            prospect_id="",
            scheduled_at=new_slot.start,
        )

    async def cancel(self, booking_id: str, reason: str | None = None) -> bool:
        """Cancel a scheduled demo.

        Args:
            booking_id: Booking to cancel.
            reason: Optional cancellation reason.

        Returns:
            True if successfully cancelled.
        """
        self.logger.info("Cancelling demo", booking_id=booking_id, reason=reason)
        return True
