"""Event bus implementation for publish/subscribe messaging.

Provides a central event bus that decouples event producers from consumers,
supporting both synchronous and asynchronous handlers with priority-based
dispatch and error isolation.
"""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Dict, List, Optional, Set, Union

from .schema import Event, EventPriority, EventStatus

logger = logging.getLogger(__name__)

# Type alias for event handlers
EventHandler = Union[Callable[[Event], None], Callable[[Event], Awaitable[None]]]


@dataclass
class HandlerRegistration:
    """Internal record of a registered event handler.

    Attributes:
        handler: The callback function to invoke.
        event_type: The event type pattern this handler subscribes to.
        priority: Handler execution priority (higher = earlier).
        filter_fn: Optional predicate to filter events before handling.
    """

    handler: EventHandler
    event_type: str
    priority: int = 0
    filter_fn: Optional[Callable[[Event], bool]] = None


class EventBus:
    """Central event bus for publish/subscribe messaging.

    The event bus decouples event producers from consumers. Publishers emit
    events to the bus, and subscribers register handlers for specific event
    types. Handlers are invoked in priority order with error isolation.

    Example:
        >>> bus = EventBus()
        >>> bus.subscribe("campaign.created", my_handler)
        >>> await bus.publish(Event(event_type="campaign.created", payload={...}))
    """

    def __init__(self, *, max_queue_size: int = 10000) -> None:
        """Initialize the event bus.

        Args:
            max_queue_size: Maximum number of events allowed in the internal queue.
        """
        self._handlers: Dict[str, List[HandlerRegistration]] = defaultdict(list)
        self._wildcard_handlers: List[HandlerRegistration] = []
        self._max_queue_size = max_queue_size
        self._event_queue: asyncio.Queue[Event] = asyncio.Queue(maxsize=max_queue_size)
        self._running = False
        self._dispatch_task: Optional[asyncio.Task[None]] = None
        self._middleware: List[Callable[[Event], Event]] = []
        self._error_handlers: List[Callable[[Event, Exception], None]] = []

    @property
    def is_running(self) -> bool:
        """Check if the event bus dispatch loop is running."""
        return self._running

    def subscribe(
        self,
        event_type: str,
        handler: EventHandler,
        *,
        priority: int = 0,
        filter_fn: Optional[Callable[[Event], bool]] = None,
    ) -> None:
        """Register a handler for a specific event type.

        Args:
            event_type: Dot-delimited event type (e.g., 'campaign.created').
                Use '*' to subscribe to all events.
            handler: Callback function invoked when matching events arrive.
            priority: Execution priority; higher values execute first.
            filter_fn: Optional predicate; handler is only called if this
                returns True for the event.

        Raises:
            ValueError: If event_type is empty or handler is not callable.
        """
        if not event_type:
            raise ValueError("event_type must not be empty")
        if not callable(handler):
            raise ValueError("handler must be callable")

        registration = HandlerRegistration(
            handler=handler,
            event_type=event_type,
            priority=priority,
            filter_fn=filter_fn,
        )

        if event_type == "*":
            self._wildcard_handlers.append(registration)
            self._wildcard_handlers.sort(key=lambda r: r.priority, reverse=True)
        else:
            self._handlers[event_type].append(registration)
            self._handlers[event_type].sort(key=lambda r: r.priority, reverse=True)

        logger.debug("Subscribed handler for event type '%s'", event_type)

    def unsubscribe(self, event_type: str, handler: EventHandler) -> bool:
        """Remove a handler registration.

        Args:
            event_type: The event type the handler was registered for.
            handler: The handler function to remove.

        Returns:
            True if the handler was found and removed, False otherwise.
        """
        if event_type == "*":
            for i, reg in enumerate(self._wildcard_handlers):
                if reg.handler == handler:
                    self._wildcard_handlers.pop(i)
                    return True
            return False

        handlers = self._handlers.get(event_type, [])
        for i, reg in enumerate(handlers):
            if reg.handler == handler:
                handlers.pop(i)
                return True
        return False

    def add_middleware(self, middleware: Callable[[Event], Event]) -> None:
        """Add middleware that transforms events before dispatch.

        Args:
            middleware: Function that takes an Event and returns a (possibly
                modified) Event.
        """
        self._middleware.append(middleware)

    def add_error_handler(self, handler: Callable[[Event, Exception], None]) -> None:
        """Add a global error handler for dispatch failures.

        Args:
            handler: Callback invoked with (event, exception) on handler failure.
        """
        self._error_handlers.append(handler)

    async def publish(self, event: Event) -> None:
        """Publish an event to the bus.

        The event is placed on the internal queue for asynchronous dispatch.
        If the queue is full, the event is dropped and logged.

        Args:
            event: The event to publish.
        """
        try:
            self._event_queue.put_nowait(event)
        except asyncio.QueueFull:
            logger.error(
                "Event queue full (max_size=%d); dropping event %s",
                self._max_queue_size,
                event.metadata.event_id,
            )

    async def publish_and_wait(self, event: Event) -> None:
        """Publish an event and wait for all handlers to complete.

        Args:
            event: The event to publish.
        """
        await self._dispatch_event(event)

    async def start(self) -> None:
        """Start the asynchronous dispatch loop."""
        if self._running:
            return
        self._running = True
        self._dispatch_task = asyncio.create_task(self._dispatch_loop())
        logger.info("Event bus started")

    async def stop(self) -> None:
        """Stop the dispatch loop and wait for pending events to be processed."""
        if not self._running:
            return
        self._running = False
        if self._dispatch_task:
            self._dispatch_task.cancel()
            try:
                await self._dispatch_task
            except asyncio.CancelledError:
                pass
            self._dispatch_task = None
        logger.info("Event bus stopped")

    async def _dispatch_loop(self) -> None:
        """Main dispatch loop that processes events from the queue."""
        while self._running:
            try:
                event = await asyncio.wait_for(self._event_queue.get(), timeout=1.0)
                await self._dispatch_event(event)
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("Unexpected error in dispatch loop")

    async def _dispatch_event(self, event: Event) -> None:
        """Dispatch a single event to all matching handlers.

        Handlers are invoked in priority order. Each handler is isolated;
        exceptions in one handler do not prevent others from running.

        Args:
            event: The event to dispatch.
        """
        # Apply middleware chain
        for mw in self._middleware:
            try:
                event = mw(event)
            except Exception:
                logger.exception("Middleware failed for event %s", event.metadata.event_id)
                return

        # Collect all matching handlers
        handlers: List[HandlerRegistration] = []
        handlers.extend(self._handlers.get(event.event_type, []))
        handlers.extend(self._wildcard_handlers)
        handlers.sort(key=lambda r: r.priority, reverse=True)

        for registration in handlers:
            # Apply filter if present
            if registration.filter_fn and not registration.filter_fn(event):
                continue

            try:
                result = registration.handler(event)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as exc:
                logger.exception(
                    "Handler failed for event %s (type=%s)",
                    event.metadata.event_id,
                    event.event_type,
                )
                for error_handler in self._error_handlers:
                    try:
                        error_handler(event, exc)
                    except Exception:
                        logger.exception("Error handler failed")

    def handler_count(self, event_type: Optional[str] = None) -> int:
        """Get the number of registered handlers.

        Args:
            event_type: If provided, count handlers for this type only.
                If None, count all handlers including wildcards.

        Returns:
            Number of registered handlers.
        """
        if event_type:
            return len(self._handlers.get(event_type, []))
        total = len(self._wildcard_handlers)
        for handlers in self._handlers.values():
            total += len(handlers)
        return total

    def registered_types(self) -> Set[str]:
        """Get all event types that have registered handlers.

        Returns:
            Set of event type strings.
        """
        return set(self._handlers.keys())
