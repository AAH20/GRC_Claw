"""Event schema definitions for the event-driven integration system.

Defines the core event data structures, metadata, priority levels, and status
tracking used throughout the system.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, List, Optional, Union


class EventPriority(Enum):
    """Priority levels for event processing."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class EventStatus(Enum):
    """Lifecycle status of an event."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    DEAD_LETTER = "dead_letter"


@dataclass(frozen=True)
class EventMetadata:
    """Metadata attached to every event for tracing and auditing.

    Attributes:
        event_id: Unique identifier for the event.
        correlation_id: ID linking related events in a transaction chain.
        causation_id: ID of the event that caused this event.
        timestamp: UTC timestamp when the event was created.
        source: Origin service or component that produced the event.
        version: Schema version of the event payload.
        trace_id: Distributed tracing identifier.
        user_id: Optional user associated with the event.
        tags: Arbitrary key-value tags for filtering and routing.
    """

    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    correlation_id: Optional[str] = None
    causation_id: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    source: str = "unknown"
    version: str = "1.0"
    trace_id: Optional[str] = None
    user_id: Optional[str] = None
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class Event:
    """Core event representation in the system.

    Attributes:
        event_type: Dot-delimited event type (e.g., 'campaign.created').
        payload: Event-specific data payload.
        metadata: Event metadata for tracing and auditing.
        priority: Processing priority level.
        status: Current lifecycle status.
        retry_count: Number of processing attempts made.
        max_retries: Maximum retry attempts before dead-lettering.
        error_message: Last error message if processing failed.
    """

    event_type: str
    payload: Dict[str, Any] = field(default_factory=dict)
    metadata: EventMetadata = field(default_factory=EventMetadata)
    priority: EventPriority = EventPriority.NORMAL
    status: EventStatus = EventStatus.PENDING
    retry_count: int = 0
    max_retries: int = 3
    error_message: Optional[str] = None

    def with_status(self, status: EventStatus, error: Optional[str] = None) -> Event:
        """Return a new Event with updated status and optional error.

        Args:
            status: New lifecycle status.
            error: Optional error message.

        Returns:
            A new Event instance with the updated status.
        """
        return Event(
            event_type=self.event_type,
            payload=self.payload,
            metadata=self.metadata,
            priority=self.priority,
            status=status,
            retry_count=self.retry_count,
            max_retries=self.max_retries,
            error_message=error,
        )

    def increment_retry(self) -> Event:
        """Return a new Event with incremented retry count.

        Returns:
            A new Event with retry_count incremented by 1.
        """
        return Event(
            event_type=self.event_type,
            payload=self.payload,
            metadata=self.metadata,
            priority=self.priority,
            status=EventStatus.RETRYING,
            retry_count=self.retry_count + 1,
            max_retries=self.max_retries,
            error_message=self.error_message,
        )

    def is_terminal(self) -> bool:
        """Check if the event has reached a terminal state.

        Returns:
            True if the event is completed, failed permanently, or dead-lettered.
        """
        return self.status in (
            EventStatus.COMPLETED,
            EventStatus.DEAD_LETTER,
        ) or (self.status == EventStatus.FAILED and self.retry_count >= self.max_retries)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the event to a dictionary.

        Returns:
            Dictionary representation of the event.
        """
        return {
            "event_type": self.event_type,
            "payload": self.payload,
            "metadata": {
                "event_id": self.metadata.event_id,
                "correlation_id": self.metadata.correlation_id,
                "causation_id": self.metadata.causation_id,
                "timestamp": self.metadata.timestamp.isoformat(),
                "source": self.metadata.source,
                "version": self.metadata.version,
                "trace_id": self.metadata.trace_id,
                "user_id": self.metadata.user_id,
                "tags": self.metadata.tags,
            },
            "priority": self.priority.value,
            "status": self.status.value,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "error_message": self.error_message,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Event:
        """Deserialize an event from a dictionary.

        Args:
            data: Dictionary containing event data.

        Returns:
            A new Event instance.

        Raises:
            ValueError: If required fields are missing or malformed.
        """
        try:
            meta = data.get("metadata", {})
            metadata = EventMetadata(
                event_id=meta.get("event_id", str(uuid.uuid4())),
                correlation_id=meta.get("correlation_id"),
                causation_id=meta.get("causation_id"),
                timestamp=datetime.fromisoformat(meta["timestamp"])
                if "timestamp" in meta
                else datetime.now(timezone.utc),
                source=meta.get("source", "unknown"),
                version=meta.get("version", "1.0"),
                trace_id=meta.get("trace_id"),
                user_id=meta.get("user_id"),
                tags=meta.get("tags", {}),
            )
            return cls(
                event_type=data["event_type"],
                payload=data.get("payload", {}),
                metadata=metadata,
                priority=EventPriority(data.get("priority", "normal")),
                status=EventStatus(data.get("status", "pending")),
                retry_count=data.get("retry_count", 0),
                max_retries=data.get("max_retries", 3),
                error_message=data.get("error_message"),
            )
        except (KeyError, TypeError) as exc:
            raise ValueError(f"Invalid event data: {exc}") from exc


# Type alias for event handler functions
EventHandler = Union[Callable[[Event], None], Callable[[Event], Awaitable[None]]]
