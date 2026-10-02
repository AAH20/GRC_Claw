"""Event publisher for emitting events to the event bus.

Provides a high-level publisher interface with support for batching,
retry logic, and delivery guarantees.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .bus import EventBus
from .schema import Event, EventMetadata, EventPriority

logger = logging.getLogger(__name__)


@dataclass
class PublishResult:
    """Result of a publish operation.

    Attributes:
        event_id: The ID of the published event.
        success: Whether the event was successfully published.
        error: Error message if publishing failed.
    """

    event_id: str
    success: bool
    error: Optional[str] = None


class EventPublisher:
    """High-level event publisher with batching and retry support.

    Wraps the event bus with additional features like automatic retry,
    batch publishing, and delivery confirmation.

    Example:
        >>> publisher = EventPublisher(event_bus)
        >>> result = await publisher.publish(
        ...     event_type="campaign.created",
        ...     payload={"campaign_id": "123"},
        ... )
    """

    def __init__(
        self,
        event_bus: EventBus,
        *,
        default_source: str = "event-publisher",
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ) -> None:
        """Initialize the event publisher.

        Args:
            event_bus: The event bus to publish events to.
            default_source: Default source identifier for published events.
            max_retries: Maximum number of retry attempts for failed publishes.
            retry_delay: Delay in seconds between retry attempts.
        """
        self._bus = event_bus
        self._default_source = default_source
        self._max_retries = max_retries
        self._retry_delay = retry_delay
        self._published_count = 0
        self._failed_count = 0

    @property
    def published_count(self) -> int:
        """Get the total number of successfully published events."""
        return self._published_count

    @property
    def failed_count(self) -> int:
        """Get the total number of failed publish attempts."""
        return self._failed_count

    async def publish(
        self,
        event_type: str,
        payload: Optional[Dict[str, Any]] = None,
        *,
        priority: EventPriority = EventPriority.NORMAL,
        source: Optional[str] = None,
        correlation_id: Optional[str] = None,
        causation_id: Optional[str] = None,
        user_id: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
        metadata: Optional[EventMetadata] = None,
    ) -> PublishResult:
        """Publish a single event to the bus.

        Args:
            event_type: Dot-delimited event type (e.g., 'campaign.created').
            payload: Event-specific data payload.
            priority: Processing priority level.
            source: Origin service or component.
            correlation_id: ID linking related events.
            causation_id: ID of the causing event.
            user_id: Optional user associated with the event.
            tags: Arbitrary key-value tags.
            metadata: Pre-built metadata object (overrides other metadata args).

        Returns:
            A PublishResult indicating success or failure.
        """
        if metadata is None:
            metadata = EventMetadata(
                source=source or self._default_source,
                correlation_id=correlation_id,
                causation_id=causation_id,
                user_id=user_id,
                tags=tags or {},
            )

        event = Event(
            event_type=event_type,
            payload=payload or {},
            metadata=metadata,
            priority=priority,
        )

        for attempt in range(self._max_retries):
            try:
                await self._bus.publish(event)
                self._published_count += 1
                logger.debug(
                    "Published event %s (type=%s, attempt=%d)",
                    event.metadata.event_id,
                    event_type,
                    attempt + 1,
                )
                return PublishResult(event_id=event.metadata.event_id, success=True)
            except Exception as exc:
                logger.warning(
                    "Publish attempt %d failed for event %s: %s",
                    attempt + 1,
                    event.metadata.event_id,
                    exc,
                )
                if attempt < self._max_retries - 1:
                    await asyncio.sleep(self._retry_delay * (2 ** attempt))

        self._failed_count += 1
        error_msg = f"Failed to publish after {self._max_retries} attempts"
        logger.error("%s: %s", error_msg, event.metadata.event_id)
        return PublishResult(
            event_id=event.metadata.event_id,
            success=False,
            error=error_msg,
        )

    async def publish_batch(
        self,
        events: List[Event],
        *,
        continue_on_error: bool = True,
    ) -> List[PublishResult]:
        """Publish multiple events in a batch.

        Args:
            events: List of events to publish.
            continue_on_error: If True, continue publishing after failures.

        Returns:
            List of PublishResult objects, one per event.
        """
        results: List[PublishResult] = []
        for event in events:
            try:
                await self._bus.publish(event)
                self._published_count += 1
                results.append(PublishResult(event_id=event.metadata.event_id, success=True))
            except Exception as exc:
                self._failed_count += 1
                error_msg = str(exc)
                results.append(
                    PublishResult(
                        event_id=event.metadata.event_id,
                        success=False,
                        error=error_msg,
                    )
                )
                if not continue_on_error:
                    break
        return results

    def get_stats(self) -> Dict[str, int]:
        """Get publisher statistics.

        Returns:
            Dictionary with published_count and failed_count.
        """
        return {
            "published_count": self._published_count,
            "failed_count": self._failed_count,
        }
