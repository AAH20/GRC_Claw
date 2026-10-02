"""Event sourcing implementation for aggregate state reconstruction.

Stores state as a sequence of events and reconstructs current state by
replaying those events through registered handlers.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Dict, Generic, List, Optional, TypeVar

from .schema import Event

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class AggregateState(Generic[T]):
    """Represents the state of an event-sourced aggregate.

    Attributes:
        aggregate_id: Unique identifier for the aggregate instance.
        aggregate_type: Type/class name of the aggregate.
        version: Current version (number of events applied).
        state: The reconstructed state object.
    """

    aggregate_id: str
    aggregate_type: str
    version: int = 0
    state: Optional[T] = None


# Type alias for event-sourced handlers
EventHandler = Callable[[T, Event], T]
AsyncEventHandler = Callable[[T, Event], Awaitable[T]]


class EventSourcing(Generic[T]):
    """Event sourcing repository for aggregate state management.

    Maintains a mapping of aggregate IDs to their event streams and provides
    methods to append events and reconstruct state by replaying the event
    history through registered handlers.

    Example:
        >>> sourcing = EventSourcing[MyAggregate]()
        >>> sourcing.register_handler("campaign.created", my_handler)
        >>> await sourcing.append(aggregate_id, event)
        >>> state = await sourcing.get_state(aggregate_id)
    """

    def __init__(self) -> None:
        """Initialize the event sourcing repository."""
        self._event_streams: Dict[str, List[Event]] = {}
        self._handlers: Dict[str, List[EventHandler[T]]] = {}
        self._async_handlers: Dict[str, List[AsyncEventHandler[T]]] = {}
        self._snapshots: Dict[str, AggregateState[T]] = {}

    def register_handler(self, event_type: str, handler: EventHandler[T]) -> None:
        """Register a synchronous state handler for an event type.

        Args:
            event_type: The event type this handler processes.
            handler: Function (state, event) -> new_state.
        """
        self._handlers.setdefault(event_type, []).append(handler)
        logger.debug("Registered sync handler for event type '%s'", event_type)

    def register_async_handler(self, event_type: str, handler: AsyncEventHandler[T]) -> None:
        """Register an asynchronous state handler for an event type.

        Args:
            event_type: The event type this handler processes.
            handler: Async function (state, event) -> new_state.
        """
        self._async_handlers.setdefault(event_type, []).append(handler)
        logger.debug("Registered async handler for event type '%s'", event_type)

    async def append(self, aggregate_id: str, event: Event) -> None:
        """Append an event to an aggregate's event stream.

        Args:
            aggregate_id: The aggregate instance identifier.
            event: The event to append.
        """
        if aggregate_id not in self._event_streams:
            self._event_streams[aggregate_id] = []
        self._event_streams[aggregate_id].append(event)
        logger.debug(
            "Appended event %s to aggregate %s (stream length=%d)",
            event.metadata.event_id,
            aggregate_id,
            len(self._event_streams[aggregate_id]),
        )

    async def get_state(
        self,
        aggregate_id: str,
        initial_state: Optional[T] = None,
    ) -> Optional[AggregateState[T]]:
        """Reconstruct the current state of an aggregate by replaying events.

        Args:
            aggregate_id: The aggregate instance identifier.
            initial_state: The initial state before any events are applied.

        Returns:
            The reconstructed aggregate state, or None if the aggregate
            has no events.
        """
        events = self._event_streams.get(aggregate_id, [])
        if not events:
            return None

        # Check for a snapshot to start from
        snapshot = self._snapshots.get(aggregate_id)
        if snapshot and snapshot.version <= len(events):
            state = snapshot.state
            start_version = snapshot.version
        else:
            state = initial_state
            start_version = 0

        # Replay events from the starting version
        for i in range(start_version, len(events)):
            event = events[i]
            state = await self._apply_event(state, event)

        aggregate_state = AggregateState(
            aggregate_id=aggregate_id,
            aggregate_type=type(state).__name__ if state else "unknown",
            version=len(events),
            state=state,
        )
        return aggregate_state

    async def _apply_event(self, state: Optional[T], event: Event) -> Optional[T]:
        """Apply a single event to the state using registered handlers.

        Args:
            state: The current state (may be None for initial events).
            event: The event to apply.

        Returns:
            The new state after applying the event.
        """
        new_state = state

        # Apply synchronous handlers
        for handler in self._handlers.get(event.event_type, []):
            try:
                new_state = handler(new_state, event)
            except Exception:
                logger.exception(
                    "Sync handler failed for event %s (type=%s)",
                    event.metadata.event_id,
                    event.event_type,
                )
                raise

        # Apply asynchronous handlers
        for handler in self._async_handlers.get(event.event_type, []):
            try:
                new_state = await handler(new_state, event)
            except Exception:
                logger.exception(
                    "Async handler failed for event %s (type=%s)",
                    event.metadata.event_id,
                    event.event_type,
                )
                raise

        return new_state

    def create_snapshot(self, aggregate_id: str, state: AggregateState[T]) -> None:
        """Create a snapshot of an aggregate's state for faster reconstruction.

        Args:
            aggregate_id: The aggregate instance identifier.
            state: The state to snapshot.
        """
        self._snapshots[aggregate_id] = state
        logger.debug(
            "Created snapshot for aggregate %s (version=%d)",
            aggregate_id,
            state.version,
        )

    def get_events(
        self,
        aggregate_id: str,
        *,
        after_version: int = 0,
    ) -> List[Event]:
        """Get events for an aggregate, optionally after a specific version.

        Args:
            aggregate_id: The aggregate instance identifier.
            after_version: Only return events after this version number.

        Returns:
            List of events for the aggregate.
        """
        events = self._event_streams.get(aggregate_id, [])
        return events[after_version:]

    def get_all_aggregate_ids(self) -> List[str]:
        """Get all aggregate IDs that have event streams.

        Returns:
            List of aggregate identifiers.
        """
        return list(self._event_streams.keys())

    def clear(self, aggregate_id: Optional[str] = None) -> None:
        """Clear event streams and snapshots.

        Args:
            aggregate_id: If provided, clear only this aggregate's data.
                If None, clear all data.
        """
        if aggregate_id:
            self._event_streams.pop(aggregate_id, None)
            self._snapshots.pop(aggregate_id, None)
        else:
            self._event_streams.clear()
            self._snapshots.clear()
