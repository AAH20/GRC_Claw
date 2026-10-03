"""Event service for gated communities."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


class EventServiceError(Exception):
    """Base exception for event service errors."""


class EventNotFoundError(EventServiceError):
    """Raised when an event is not found."""


class EventValidationError(EventServiceError):
    """Raised when event data fails validation."""


@dataclass
class Event:
    """Represents an event in a gated community."""

    id: str
    community_id: str
    title: str
    description: str
    start_time: datetime
    end_time: datetime
    created_by: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    location: Optional[str] = None
    max_attendees: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class EventService:
    """Service for managing events in gated communities."""

    def __init__(self, repository: Any = None) -> None:
        """Initialize the event service.

        Args:
            repository: Optional repository for event persistence.
        """
        self._repository = repository
        self._events: Dict[str, Event] = {}

    def create_event(self, data: Dict[str, Any]) -> Event:
        """Create a new event with validation.

        Args:
            data: Dictionary containing event data. Required keys:
                - id: Unique event identifier
                - community_id: Community the event belongs to
                - title: Event title
                - description: Event description
                - start_time: Event start time (ISO format string or datetime)
                - end_time: Event end time (ISO format string or datetime)
                - created_by: User ID of the creator

        Returns:
            The created Event instance.

        Raises:
            EventValidationError: If required fields are missing or invalid.
        """
        required_fields = ["id", "community_id", "title", "description", "start_time", "end_time", "created_by"]
        missing = [f for f in required_fields if f not in data or data[f] is None]
        if missing:
            raise EventValidationError(f"Missing required fields: {', '.join(missing)}")

        event_id = str(data["id"])
        if event_id in self._events:
            raise EventValidationError(f"Event with id '{event_id}' already exists")

        start_time = self._parse_datetime(data["start_time"], "start_time")
        end_time = self._parse_datetime(data["end_time"], "end_time")

        if end_time <= start_time:
            raise EventValidationError("end_time must be after start_time")

        event = Event(
            id=event_id,
            community_id=str(data["community_id"]),
            title=str(data["title"]),
            description=str(data["description"]),
            start_time=start_time,
            end_time=end_time,
            created_by=str(data["created_by"]),
            location=data.get("location"),
            max_attendees=data.get("max_attendees"),
            metadata=data.get("metadata", {}),
        )

        self._events[event_id] = event
        if self._repository:
            self._repository.save(event)

        return event

    def get_event(self, event_id: str) -> Event:
        """Get an event by its ID.

        Args:
            event_id: The unique identifier of the event.

        Returns:
            The Event instance.

        Raises:
            EventNotFoundError: If no event with the given ID exists.
            EventValidationError: If event_id is empty or None.
        """
        if not event_id:
            raise EventValidationError("event_id is required")

        event = self._events.get(event_id)
        if event is None and self._repository:
            event = self._repository.get(event_id)

        if event is None:
            raise EventNotFoundError(f"Event with id '{event_id}' not found")

        return event

    def list_events(
        self,
        community_id: str,
        pagination: Optional[Dict[str, Any]] = None,
    ) -> List[Event]:
        """List events in a community with pagination.

        Args:
            community_id: The community to list events for.
            pagination: Optional pagination parameters:
                - page: Page number (1-indexed, default 1)
                - per_page: Items per page (default 20, max 100)

        Returns:
            List of Event instances belonging to the community.

        Raises:
            EventValidationError: If community_id is empty or pagination is invalid.
        """
        if not community_id:
            raise EventValidationError("community_id is required")

        pagination = pagination or {}
        page = max(1, int(pagination.get("page", 1)))
        per_page = min(100, max(1, int(pagination.get("per_page", 20))))

        all_events = [
            e for e in self._events.values() if e.community_id == community_id
        ]

        if self._repository:
            all_events = self._repository.list_by_community(community_id)

        all_events.sort(key=lambda e: e.start_time)

        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page

        return all_events[start_idx:end_idx]

    @staticmethod
    def _parse_datetime(value: Any, field_name: str) -> datetime:
        """Parse a datetime value from string or datetime.

        Args:
            value: The value to parse.
            field_name: Name of the field for error messages.

        Returns:
            Parsed datetime.

        Raises:
            EventValidationError: If the value cannot be parsed.
        """
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError as exc:
                raise EventValidationError(
                    f"Invalid datetime format for {field_name}: {value}"
                ) from exc
        raise EventValidationError(
            f"{field_name} must be a datetime or ISO format string, got {type(value).__name__}"
        )
