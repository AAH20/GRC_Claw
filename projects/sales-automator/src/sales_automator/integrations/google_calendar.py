"""Google Calendar integration client."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from sales_automator.config import get_settings

logger = structlog.get_logger(__name__)


class GoogleCalendarError(Exception):
    """Google Calendar API error."""


class GoogleCalendarClient:
    """Client for Google Calendar API."""

    def __init__(self) -> None:
        settings = get_settings()
        self.credentials_path = settings.google_calendar_credentials_path
        self.token_path = settings.google_calendar_token_path
        self.primary_calendar_id = settings.google_calendar_primary_calendar_id
        self.base_url = "https://www.googleapis.com/calendar/v3"
        self.access_token: str | None = None
        self.logger = logger.bind(integration="google_calendar")

    async def _get_access_token(self) -> str:
        """Get or refresh access token.

        Returns:
            Valid access token.

        Raises:
            GoogleCalendarError: If token cannot be obtained.
        """
        if not self.access_token:
            raise GoogleCalendarError("No access token available. Run OAuth flow first.")
        return self.access_token

    def _headers(self) -> dict[str, str]:
        """Get request headers."""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def _request(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Make an authenticated request to Google Calendar API.

        Args:
            method: HTTP method.
            path: API path.
            **kwargs: Additional request arguments.

        Returns:
            Response data.

        Raises:
            GoogleCalendarError: If the request fails.
        """
        if not self.access_token:
            self.access_token = await self._get_access_token()

        url = f"{self.base_url}{path}"
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method,
                url,
                headers=self._headers(),
                timeout=30.0,
                **kwargs,
            )
            if response.status_code >= 400:
                raise GoogleCalendarError(f"API error {response.status_code}: {response.text}")
            return response.json() if response.content else {}

    async def list_calendars(self) -> list[dict[str, Any]]:
        """List available calendars.

        Returns:
            List of calendars.
        """
        self.logger.info("Listing calendars")
        result = await self._request("GET", "/users/me/calendarList")
        return result.get("items", [])

    async def get_events(
        self,
        calendar_id: str | None = None,
        time_min: datetime | None = None,
        time_max: datetime | None = None,
        max_results: int = 100,
    ) -> list[dict[str, Any]]:
        """Get events from a calendar.

        Args:
            calendar_id: Calendar ID (defaults to primary).
            time_min: Start time filter.
            time_max: End time filter.
            max_results: Maximum number of events.

        Returns:
            List of events.
        """
        cal_id = calendar_id or self.primary_calendar_id
        self.logger.info("Getting events", calendar_id=cal_id)
        params: dict[str, Any] = {"maxResults": max_results}
        if time_min:
            params["timeMin"] = time_min.isoformat()
        if time_max:
            params["timeMax"] = time_max.isoformat()
        result = await self._request("GET", f"/calendars/{cal_id}/events", params=params)
        return result.get("items", [])

    async def create_event(
        self,
        summary: str,
        start: datetime,
        end: datetime,
        description: str | None = None,
        attendees: list[str] | None = None,
        calendar_id: str | None = None,
    ) -> dict[str, Any]:
        """Create a calendar event.

        Args:
            summary: Event title.
            start: Start time.
            end: End time.
            description: Event description.
            attendees: List of attendee emails.
            calendar_id: Calendar ID (defaults to primary).

        Returns:
            Created event.
        """
        cal_id = calendar_id or self.primary_calendar_id
        self.logger.info("Creating event", summary=summary, start=start)
        event_body: dict[str, Any] = {
            "summary": summary,
            "start": {"dateTime": start.isoformat()},
            "end": {"dateTime": end.isoformat()},
        }
        if description:
            event_body["description"] = description
        if attendees:
            event_body["attendees"] = [{"email": e} for e in attendees]
        return await self._request("POST", f"/calendars/{cal_id}/events", json=event_body)

    async def update_event(
        self,
        event_id: str,
        updates: dict[str, Any],
        calendar_id: str | None = None,
    ) -> dict[str, Any]:
        """Update an existing event.

        Args:
            event_id: Event ID.
            updates: Fields to update.
            calendar_id: Calendar ID (defaults to primary).

        Returns:
            Updated event.
        """
        cal_id = calendar_id or self.primary_calendar_id
        self.logger.info("Updating event", event_id=event_id)
        return await self._request(
            "PATCH",
            f"/calendars/{cal_id}/events/{event_id}",
            json=updates,
        )

    async def delete_event(
        self,
        event_id: str,
        calendar_id: str | None = None,
    ) -> bool:
        """Delete a calendar event.

        Args:
            event_id: Event ID.
            calendar_id: Calendar ID (defaults to primary).

        Returns:
            True if deleted.
        """
        cal_id = calendar_id or self.primary_calendar_id
        self.logger.info("Deleting event", event_id=event_id)
        await self._request("DELETE", f"/calendars/{cal_id}/events/{event_id}")
        return True

    async def get_free_busy(
        self,
        time_min: datetime,
        time_max: datetime,
        calendar_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        """Get free/busy information.

        Args:
            time_min: Start time.
            time_max: End time.
            calendar_ids: Calendar IDs to check.

        Returns:
            Free/busy information.
        """
        self.logger.info("Getting free/busy", time_min=time_min, time_max=time_max)
        cal_ids = calendar_ids or [self.primary_calendar_id]
        payload = {
            "timeMin": time_min.isoformat(),
            "timeMax": time_max.isoformat(),
            "items": [{"id": cal_id} for cal_id in cal_ids],
        }
        return await self._request("POST", "/freeBusy", json=payload)

    async def find_available_slots(
        self,
        duration_minutes: int,
        time_min: datetime,
        time_max: datetime,
        calendar_id: str | None = None,
    ) -> list[dict[str, datetime]]:
        """Find available time slots.

        Args:
            duration_minutes: Required duration in minutes.
            time_min: Search window start.
            time_max: Search window end.
            calendar_id: Calendar ID (defaults to primary).

        Returns:
            List of available slots with start/end times.
        """
        self.logger.info(
            "Finding available slots",
            duration=duration_minutes,
            time_min=time_min,
            time_max=time_max,
        )
        return []
