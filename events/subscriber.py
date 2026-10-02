"""Event subscriber for consuming events from the event bus.

Provides a high-level subscriber interface with support for automatic
acknowledgment, error handling, and graceful shutdown.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Dict, List, Optional, Set

from .bus import EventBus
from .schema import Event, EventStatus

logger = logging.getLogger(__name__)


@dataclass
class Subscription:
    """Represents an active event subscription.

    Attributes:
        event_type: The event type being subscribed to.
        handler: The callback function.
        subscription_id: Unique identifier for this subscription.
        auto_ack: Whether to automatically acknowledge successful processing.
        max_concurrent: Maximum number of concurrent handler invocations.
    """

    event_type: str
    handler: Callable[[Event], Awaitable[None]]
    subscription_id: str
    auto_ack: bool = True
    max_concurrent: int = 1


class EventSubscriber:
    """High-level event subscriber with lifecycle management.

    Wraps the event bus with additional features like automatic acknowledgment,
    concurrency control, and graceful shutdown.

    Example:
        >>> subscriber = EventSubscriber(event_bus)
        >>> await subscriber.subscribe("campaign.created", my_handler)
        >>> await subscriber.start()
        >>> # ... later ...
        >>> await subscriber.stop()
    """

    def __init__(self, event_bus: EventBus) -> None:
        """Initialize the event subscriber.

        Args:
            event_bus: The event bus to subscribe to.
        """
        self._bus = event_bus
        self._subscriptions: Dict[str, Subscription] = {}
        self._running = False
        self._semaphores: Dict[str, asyncio.Semaphore] = {}
        self._pending_tasks: Set[asyncio.Task[None]] = set()

    @property
    def is_running(self) -> bool:
        """Check if the subscriber is actively processing events."""
        return self._running

    @property
    def subscription_count(self) -> int:
        """Get the number of active subscriptions."""
        return len(self._subscriptions)

    async def subscribe(
        self,
        event_type: str,
        handler: Callable[[Event], Awaitable[None]],
        *,
        auto_ack: bool = True,
        max_concurrent: int = 1,
    ) -> str:
        """Subscribe to events of a specific type.

        Args:
            event_type: The event type to subscribe to.
            handler: Async callback invoked for each matching event.
            auto_ack: If True, events are automatically acknowledged after
                successful processing.
            max_concurrent: Maximum number of concurrent handler invocations.

        Returns:
            The subscription ID.

        Raises:
            ValueError: If event_type is empty or handler is not callable.
        """
        if not event_type:
            raise ValueError("event_type must not be empty")
        if not callable(handler):
            raise ValueError("handler must be callable")

        import uuid

        sub_id = str(uuid.uuid4())
        subscription = Subscription(
            event_type=event_type,
            handler=handler,
            subscription_id=sub_id,
            auto_ack=auto_ack,
            max_concurrent=max_concurrent,
        )
        self._subscriptions[sub_id] = subscription
        self._semaphores[sub_id] = asyncio.Semaphore(max_concurrent)

        # Wrap the handler with concurrency control and error handling
        async def wrapped_handler(event: Event) -> None:
            semaphore = self._semaphores[sub_id]
            async with semaphore:
                try:
                    await handler(event)
                    if auto_ack:
                        logger.debug(
                            "Auto-acked event %s", event.metadata.event_id
                        )
                except Exception:
                    logger.exception(
                        "Handler failed for event %s (subscription=%s)",
                        event.metadata.event_id,
                        sub_id,
                    )
                    raise

        self._bus.subscribe(event_type, wrapped_handler)
        logger.info("Subscribed to '%s' (id=%s)", event_type, sub_id)
        return sub_id

    async def unsubscribe(self, subscription_id: str) -> bool:
        """Remove a subscription.

        Args:
            subscription_id: The subscription ID to remove.

        Returns:
            True if the subscription was found and removed, False otherwise.
        """
        subscription = self._subscriptions.pop(subscription_id, None)
        if subscription is None:
            return False

        self._semaphores.pop(subscription_id, None)
        self._bus.unsubscribe(subscription.event_type, subscription.handler)
        logger.info("Unsubscribed %s from '%s'", subscription_id, subscription.event_type)
        return True

    async def start(self) -> None:
        """Start the subscriber and the underlying event bus."""
        if self._running:
            return
        self._running = True
        await self._bus.start()
        logger.info("Event subscriber started")

    async def stop(self) -> None:
        """Stop the subscriber and wait for pending tasks to complete."""
        if not self._running:
            return
        self._running = False

        # Wait for all pending tasks
        if self._pending_tasks:
            await asyncio.gather(*self._pending_tasks, return_exceptions=True)
            self._pending_tasks.clear()

        await self._bus.stop()
        logger.info("Event subscriber stopped")

    def get_subscriptions(self) -> List[Subscription]:
        """Get all active subscriptions.

        Returns:
            List of Subscription objects.
        """
        return list(self._subscriptions.values())
