"""Calendar integration for interview scheduling."""

from __future__ import annotations

import logging
from typing import Any

from recruitment_platform.integrations.base import BaseIntegration

logger = logging.getLogger(__name__)


class CalendarIntegration(BaseIntegration):
    """Integration with calendar services (Google, Outlook).

    Manages calendar events, availability, and scheduling
    for interviews.
    """

    def __init__(self, provider: str, api_key: str = "", base_url: str = "") -> None:
        """Initialize the calendar integration.

        Args:
            provider: Calendar provider (google, outlook).
            api_key: API key for authentication.
            base_url: Base URL for the calendar API.
        """
        super().__init__(base_url=base_url, api_key=api_key)
        self.provider = provider

    async def create_event(self, event_data: dict[str, Any]) -> dict[str, Any]:
        """Create a calendar event.

        Args:
            event_data: Event details (title, time, attendees, etc.).

        Returns:
            Created event data.
        """
        response = await self.post("/events", json=event_data)
        return response.json()

    async def get_availability(
        self,
        user_id: str,
        start_time: str,
        end_time: str,
    ) -> list[dict[str, Any]]:
        """Get user availability for a time range.

        Args:
            user_id: User identifier.
            start_time: Start of time range (ISO format).
            end_time: End of time range (ISO format).

        Returns:
            List of available time slots.
        """
        response = await self.get(
            f"/users/{user_id}/availability",
            params={"start": start_time, "end": end_time},
        )
        return response.json().get("slots", [])

    async def update_event(
        self, event_id: str, event_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Update a calendar event.

        Args:
            event_id: Event identifier.
            event_data: Updated event data.

        Returns:
            Updated event data.
        """
        response = await self.put(f"/events/{event_id}", json=event_data)
        return response.json()

    async def delete_event(self, event_id: str) -> bool:
        """Delete a calendar event.

        Args:
            event_id: Event identifier.

        Returns:
            True if deleted successfully.
        """
        await self.delete(f"/events/{event_id}")
        return True

    async def health_check(self) -> bool:
        """Check if the calendar service is available.

        Returns:
            True if the service is healthy.
        """
        try:
            await self.get("/health")
            return True
        except Exception:
            return False
