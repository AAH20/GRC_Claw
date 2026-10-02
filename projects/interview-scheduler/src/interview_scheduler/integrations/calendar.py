"""Calendar integration providers."""

from __future__ import annotations

import abc
from datetime import datetime
from typing import Any

from interview_scheduler.models.timeslot import TimeSlot


class CalendarProvider(abc.ABC):
    """Abstract base class for calendar providers."""

    @abc.abstractmethod
    async def get_busy_slots(
        self,
        user_id: str,
        start: datetime,
        end: datetime,
    ) -> list[TimeSlot]:
        """Get busy time slots for a user.

        Args:
            user_id: The user identifier.
            start: Start of the time range.
            end: End of the time range.

        Returns:
            List of busy time slots.
        """
        ...

    @abc.abstractmethod
    async def create_event(
        self,
        title: str,
        start: datetime,
        end: datetime,
        attendees: list[str],
        description: str | None = None,
        timezone: str = "UTC",
    ) -> str:
        """Create a calendar event.

        Args:
            title: Event title.
            start: Event start time.
            end: Event end time.
            attendees: List of attendee emails.
            description: Optional event description.
            timezone: Event timezone.

        Returns:
            The created event ID.
        """
        ...

    @abc.abstractmethod
    async def update_event(
        self,
        event_id: str,
        title: str | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
        attendees: list[str] | None = None,
        description: str | None = None,
    ) -> None:
        """Update an existing calendar event.

        Args:
            event_id: The event to update.
            title: New title.
            start: New start time.
            end: New end time.
            attendees: New attendee list.
            description: New description.
        """
        ...

    @abc.abstractmethod
    async def delete_event(self, event_id: str) -> None:
        """Delete a calendar event.

        Args:
            event_id: The event to delete.
        """
        ...

    @abc.abstractmethod
    async def get_event(self, event_id: str) -> dict[str, Any]:
        """Get event details.

        Args:
            event_id: The event to retrieve.

        Returns:
            Event details as a dictionary.
        """
        ...


class GoogleCalendarProvider(CalendarProvider):
    """Google Calendar integration."""

    def __init__(self, credentials_path: str | None = None, token_path: str | None = None) -> None:
        """Initialize Google Calendar provider.

        Args:
            credentials_path: Path to service account credentials.
            token_path: Path to OAuth token file.
        """
        self.credentials_path = credentials_path
        self.token_path = token_path
        self._service: Any = None

    async def _get_service(self) -> Any:
        """Lazy-load the Google Calendar service."""
        if self._service is None:
            try:
                from google.oauth2 import service_account
                from googleapiclient.discovery import build

                if self.credentials_path:
                    credentials = service_account.Credentials.from_service_account_file(
                        self.credentials_path,
                        scopes=["https://www.googleapis.com/auth/calendar"],
                    )
                    self._service = build("calendar", "v3", credentials=credentials)
                else:
                    raise ValueError("Google credentials path is required")
            except ImportError as exc:
                raise RuntimeError(
                    "Google API client not installed. Install with: pip install google-api-python-client"
                ) from exc
        return self._service

    async def get_busy_slots(
        self, user_id: str, start: datetime, end: datetime
    ) -> list[TimeSlot]:
        """Get busy slots from Google Calendar."""
        service = await self._get_service()
        events_result = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=start.isoformat(),
                timeMax=end.isoformat(),
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        slots: list[TimeSlot] = []
        for event in events_result.get("items", []):
            event_start = event["start"].get("dateTime", event["start"].get("date"))
            event_end = event["end"].get("dateTime", event["end"].get("date"))
            slots.append(
                TimeSlot(
                    start_time=datetime.fromisoformat(event_start),
                    end_time=datetime.fromisoformat(event_end),
                    status="busy",
                    owner_id=user_id,
                    owner_type="google_calendar",
                )
            )
        return slots

    async def create_event(
        self,
        title: str,
        start: datetime,
        end: datetime,
        attendees: list[str],
        description: str | None = None,
        timezone: str = "UTC",
    ) -> str:
        """Create a Google Calendar event."""
        service = await self._get_service()
        event_body: dict[str, Any] = {
            "summary": title,
            "start": {"dateTime": start.isoformat(), "timeZone": timezone},
            "end": {"dateTime": end.isoformat(), "timeZone": timezone},
            "attendees": [{"email": email} for email in attendees],
        }
        if description:
            event_body["description"] = description
        event = service.events().insert(calendarId="primary", body=event_body).execute()
        return event["id"]

    async def update_event(
        self,
        event_id: str,
        title: str | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
        attendees: list[str] | None = None,
        description: str | None = None,
    ) -> None:
        """Update a Google Calendar event."""
        service = await self._get_service()
        event = service.events().get(calendarId="primary", eventId=event_id).execute()
        if title:
            event["summary"] = title
        if start:
            event["start"]["dateTime"] = start.isoformat()
        if end:
            event["end"]["dateTime"] = end.isoformat()
        if attendees:
            event["attendees"] = [{"email": email} for email in attendees]
        if description:
            event["description"] = description
        service.events().update(calendarId="primary", eventId=event_id, body=event).execute()

    async def delete_event(self, event_id: str) -> None:
        """Delete a Google Calendar event."""
        service = await self._get_service()
        service.events().delete(calendarId="primary", eventId=event_id).execute()

    async def get_event(self, event_id: str) -> dict[str, Any]:
        """Get a Google Calendar event."""
        service = await self._get_service()
        return service.events().get(calendarId="primary", eventId=event_id).execute()


class OutlookCalendarProvider(CalendarProvider):
    """Microsoft Outlook Calendar integration."""

    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
        tenant_id: str | None = None,
    ) -> None:
        """Initialize Outlook Calendar provider.

        Args:
            client_id: Azure AD application client ID.
            client_secret: Azure AD application client secret.
            tenant_id: Azure AD tenant ID.
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.tenant_id = tenant_id
        self._access_token: str | None = None

    async def _get_access_token(self) -> str:
        """Get or refresh the Microsoft Graph access token."""
        if self._access_token:
            return self._access_token
        try:
            import msal

            if not all([self.client_id, self.client_secret, self.tenant_id]):
                raise ValueError("Outlook credentials not configured")

            authority = f"https://login.microsoftonline.com/{self.tenant_id}"
            app = msal.ConfidentialClientApplication(
                self.client_id,
                authority=authority,
                client_credential=self.client_secret,
            )
            result = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
            if "access_token" not in result:
                raise RuntimeError(f"Failed to acquire token: {result.get('error_description')}")
            self._access_token = result["access_token"]
            return self._access_token
        except ImportError as exc:
            raise RuntimeError("MSAL not installed. Install with: pip install msal") from exc

    async def get_busy_slots(
        self, user_id: str, start: datetime, end: datetime
    ) -> list[TimeSlot]:
        """Get busy slots from Outlook Calendar."""
        import httpx

        token = await self._get_access_token()
        url = f"https://graph.microsoft.com/v1.0/users/{user_id}/calendarview"
        params = {"startDateTime": start.isoformat(), "endDateTime": end.isoformat()}
        headers = {"Authorization": f"Bearer {token}"}
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()
        slots: list[TimeSlot] = []
        for event in data.get("value", []):
            slots.append(
                TimeSlot(
                    start_time=datetime.fromisoformat(event["start"]["dateTime"].replace("Z", "+00:00")),
                    end_time=datetime.fromisoformat(event["end"]["dateTime"].replace("Z", "+00:00")),
                    status="busy",
                    owner_id=user_id,
                    owner_type="outlook_calendar",
                )
            )
        return slots

    async def create_event(
        self,
        title: str,
        start: datetime,
        end: datetime,
        attendees: list[str],
        description: str | None = None,
        timezone: str = "UTC",
    ) -> str:
        """Create an Outlook Calendar event."""
        import httpx

        token = await self._get_access_token()
        url = "https://graph.microsoft.com/v1.0/me/events"
        body: dict[str, Any] = {
            "subject": title,
            "start": {"dateTime": start.isoformat(), "timeZone": timezone},
            "end": {"dateTime": end.isoformat(), "timeZone": timezone},
            "attendees": [
                {"emailAddress": {"address": email}, "type": "required"} for email in attendees
            ],
        }
        if description:
            body["body"] = {"contentType": "text", "content": description}
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=body, headers=headers)
            response.raise_for_status()
            return response.json()["id"]

    async def update_event(
        self,
        event_id: str,
        title: str | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
        attendees: list[str] | None = None,
        description: str | None = None,
    ) -> None:
        """Update an Outlook Calendar event."""
        import httpx

        token = await self._get_access_token()
        url = f"https://graph.microsoft.com/v1.0/me/events/{event_id}"
        body: dict[str, Any] = {}
        if title:
            body["subject"] = title
        if start:
            body["start"] = {"dateTime": start.isoformat(), "timeZone": "UTC"}
        if end:
            body["end"] = {"dateTime": end.isoformat(), "timeZone": "UTC"}
        if attendees:
            body["attendees"] = [
                {"emailAddress": {"address": email}, "type": "required"} for email in attendees
            ]
        if description:
            body["body"] = {"contentType": "text", "content": description}
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        async with httpx.AsyncClient() as client:
            response = await client.patch(url, json=body, headers=headers)
            response.raise_for_status()

    async def delete_event(self, event_id: str) -> None:
        """Delete an Outlook Calendar event."""
        import httpx

        token = await self._get_access_token()
        url = f"https://graph.microsoft.com/v1.0/me/events/{event_id}"
        headers = {"Authorization": f"Bearer {token}"}
        async with httpx.AsyncClient() as client:
            response = await client.delete(url, headers=headers)
            response.raise_for_status()

    async def get_event(self, event_id: str) -> dict[str, Any]:
        """Get an Outlook Calendar event."""
        import httpx

        token = await self._get_access_token()
        url = f"https://graph.microsoft.com/v1.0/me/events/{event_id}"
        headers = {"Authorization": f"Bearer {token}"}
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.json()


class MockCalendarProvider(CalendarProvider):
    """Mock calendar provider for testing."""

    def __init__(self) -> None:
        """Initialize mock provider with empty state."""
        self._events: dict[str, dict[str, Any]] = {}

    async def get_busy_slots(
        self, user_id: str, start: datetime, end: datetime
    ) -> list[TimeSlot]:
        """Return mock busy slots."""
        return [
            TimeSlot(
                start_time=start.replace(hour=10, minute=0),
                end_time=start.replace(hour=11, minute=0),
                status="busy",
                owner_id=user_id,
                owner_type="mock",
            )
        ]

    async def create_event(
        self,
        title: str,
        start: datetime,
        end: datetime,
        attendees: list[str],
        description: str | None = None,
        timezone: str = "UTC",
    ) -> str:
        """Create a mock event."""
        event_id = f"mock-{len(self._events)}"
        self._events[event_id] = {
            "id": event_id,
            "title": title,
            "start": start,
            "end": end,
            "attendees": attendees,
            "description": description,
        }
        return event_id

    async def update_event(
        self,
        event_id: str,
        title: str | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
        attendees: list[str] | None = None,
        description: str | None = None,
    ) -> None:
        """Update a mock event."""
        if event_id in self._events:
            event = self._events[event_id]
            if title:
                event["title"] = title
            if start:
                event["start"] = start
            if end:
                event["end"] = end
            if attendees:
                event["attendees"] = attendees
            if description:
                event["description"] = description

    async def delete_event(self, event_id: str) -> None:
        """Delete a mock event."""
        self._events.pop(event_id, None)

    async def get_event(self, event_id: str) -> dict[str, Any]:
        """Get a mock event."""
        return self._events.get(event_id, {})
