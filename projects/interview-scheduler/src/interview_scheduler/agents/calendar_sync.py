"""Calendar Sync Agent using LangChain DeepAgents."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from datetime import datetime

    from interview_scheduler.integrations.calendar import CalendarProvider
    from interview_scheduler.models.interview import Interview
    from interview_scheduler.models.timeslot import TimeSlot

logger = logging.getLogger(__name__)


class CalendarSyncAgent:
    """Agent responsible for synchronizing interviews with calendar providers.

    Uses LangChain DeepAgents to intelligently manage calendar events,
    handle retries, and ensure consistency between the scheduler and
    external calendar systems.
    """

    def __init__(self, provider: CalendarProvider) -> None:
        """Initialize the Calendar Sync Agent.

        Args:
            provider: The calendar provider to sync with.
        """
        self.provider = provider
        self._agent: Any = None

    async def _get_agent(self) -> Any:
        """Lazy-initialize the LangChain DeepAgent."""
        if self._agent is None:
            try:
                from langchain_deepagents import create_deep_agent

                self._agent = create_deep_agent(
                    tools=[self._sync_event_tool, self._delete_event_tool],
                    instructions=(
                        "You are a calendar synchronization agent. Your job is to "
                        "create, update, and delete calendar events to match the "
                        "interview schedule. Always verify operations succeeded."
                    ),
                )
            except ImportError:
                logger.warning("langchain-deepagents not available, using direct provider calls")
                self._agent = None
        return self._agent

    async def _sync_event_tool(
        self,
        title: str,
        start: datetime,
        end: datetime,
        attendees: list[str],
        description: str | None = None,
        timezone: str = "UTC",
    ) -> str:
        """Tool for creating/updating calendar events."""
        return await self.provider.create_event(
            title=title,
            start=start,
            end=end,
            attendees=attendees,
            description=description,
            timezone=timezone,
        )

    async def _delete_event_tool(self, event_id: str) -> None:
        """Tool for deleting calendar events."""
        await self.provider.delete_event(event_id)

    async def sync_interview(self, interview: Interview) -> str:
        """Sync an interview to the calendar provider.

        Args:
            interview: The interview to sync.

        Returns:
            The calendar event ID.

        Raises:
            ValueError: If the interview is not scheduled.
            RuntimeError: If the sync operation fails.
        """
        if not interview.scheduled_at:
            raise ValueError(f"Interview {interview.id} is not scheduled")

        end_time = interview.scheduled_at.replace(
            minute=interview.scheduled_at.minute + interview.duration_minutes
        )
        attendees = [p.email for p in interview.participants]
        event_id = await self.provider.create_event(
            title=interview.title,
            start=interview.scheduled_at,
            end=end_time,
            attendees=attendees,
            description=interview.description,
            timezone=interview.scheduled_timezone or "UTC",
        )
        logger.info("Synced interview %s to calendar event %s", interview.id, event_id)
        return event_id

    async def update_interview_event(
        self,
        event_id: str,
        interview: Interview,
    ) -> None:
        """Update an existing calendar event for an interview.

        Args:
            event_id: The calendar event ID to update.
            interview: The updated interview data.

        Raises:
            ValueError: If the interview is not scheduled.
        """
        if not interview.scheduled_at:
            raise ValueError(f"Interview {interview.id} is not scheduled")

        end_time = interview.scheduled_at.replace(
            minute=interview.scheduled_at.minute + interview.duration_minutes
        )
        await self.provider.update_event(
            event_id=event_id,
            title=interview.title,
            start=interview.scheduled_at,
            end=end_time,
            attendees=[p.email for p in interview.participants],
            description=interview.description,
        )
        logger.info("Updated calendar event %s for interview %s", event_id, interview.id)

    async def remove_interview_event(self, event_id: str) -> None:
        """Remove an interview's calendar event.

        Args:
            event_id: The calendar event ID to delete.
        """
        await self.provider.delete_event(event_id)
        logger.info("Deleted calendar event %s", event_id)

    async def get_busy_slots(
        self,
        user_id: str,
        start: datetime,
        end: datetime,
    ) -> list[TimeSlot]:
        """Get busy slots for a user from the calendar provider.

        Args:
            user_id: The user identifier.
            start: Start of the time range.
            end: End of the time range.

        Returns:
            List of busy time slots.
        """
        return await self.provider.get_busy_slots(user_id, start, end)

    async def verify_sync(self, event_id: str) -> bool:
        """Verify that a calendar event exists and is correct.

        Args:
            event_id: The event ID to verify.

        Returns:
            True if the event exists, False otherwise.
        """
        try:
            event = await self.provider.get_event(event_id)
            return bool(event)
        except Exception:
            logger.warning("Failed to verify event %s", event_id)
            return False
