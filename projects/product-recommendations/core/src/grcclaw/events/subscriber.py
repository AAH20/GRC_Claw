"""
Event subscriber for GRC_Claw.

Provides decorator-based and class-based subscriber patterns for
consuming events from the event bus.
"""

from __future__ import annotations

import asyncio
import functools
import inspect
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Coroutine, Optional, Type, Union

from .schema import Event, EventCategory, EventStatus
from .publisher import EventPublisher

logger = logging.getLogger(__name__)


# ─── Handler Result ─────────────────────────────────────────────────────────

class HandlerResult(str, Enum):
    """Result of event handler execution."""

    SUCCESS = "success"
    RETRY = "retry"
    SKIP = "skip"
    DEAD_LETTER = "dead_letter"


# ─── Handler Context ────────────────────────────────────────────────────────

@dataclass
class HandlerContext:
    """Context passed to event handlers with execution metadata."""

    event: Event
    handler_id: str
    attempt: int = 1
    started_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def duration_seconds(self) -> float:
        start = datetime.fromisoformat(self.started_at)
        now = datetime.now(timezone.utc)
        return (now - start).total_seconds()


# ─── Decorator-based Subscriber ─────────────────────────────────────────────

def on_event(
    event_type: str,
    *,
    category: Optional[EventCategory] = None,
    severity: Optional[str] = None,
    source: Optional[str] = None,
    tags: Optional[list[str]] = None,
    tenant_id: Optional[str] = None,
):
    """
    Decorator to mark a function as an event handler.

    Args:
        event_type: The event type to subscribe to.
        category: Optional category filter.
        severity: Optional severity filter.
        source: Optional source filter.
        tags: Optional tag filter (all must match).
        tenant_id: Optional tenant filter.

    Usage:
        @on_event("compliance.violation.detected")
        def handle_violation(event: Event) -> None:
            print(f"Violation: {event.data}")
    """
    def decorator(func: Callable) -> Callable:
        func._event_subscription = {  # type: ignore[attr-defined]
            "event_type": event_type,
            "category": category,
            "severity": severity,
            "source": source,
            "tags": tags or [],
            "tenant_id": tenant_id,
            "handler": func,
        }
        return func
    return decorator


def on_category(
    category: EventCategory,
    *,
    severity: Optional[str] = None,
    source: Optional[str] = None,
):
    """
    Decorator to subscribe a function to all events in a category.

    Usage:
        @on_category(EventCategory.COMPLIANCE)
        def handle_compliance(event: Event) -> None:
            print(f"Compliance event: {event.type}")
    """
    def decorator(func: Callable) -> Callable:
        func._event_subscription = {  # type: ignore[attr-defined]
            "event_type": "*",
            "category": category,
            "severity": severity,
            "source": source,
            "tags": [],
            "tenant_id": None,
            "handler": func,
        }
        return func
    return decorator


# ─── Subscriber Registration ────────────────────────────────────────────────

class SubscriberRegistrar:
    """
    Registers decorated handlers with an EventPublisher.

    Scans classes or modules for decorated functions and registers them
    as event handlers.
    """

    def __init__(self, publisher: EventPublisher) -> None:
        self._publisher = publisher
        self._handlers: dict[str, str] = {}  # handler_id -> event_type

    def register_function(self, func: Callable) -> Optional[str]:
        """
        Register a single decorated function.

        Returns the subscription ID if registered, None otherwise.
        """
        sub_meta = getattr(func, "_event_subscription", None)
        if sub_meta is None:
            return None

        event_type = sub_meta["event_type"]
        category = sub_meta.get("category")
        severity = sub_meta.get("severity")
        source = sub_meta.get("source")
        tags = sub_meta.get("tags", [])
        tenant_id = sub_meta.get("tenant_id")
        handler = sub_meta["handler"]

        # Wrap handler with filters
        wrapped = self._wrap_with_filters(
            handler, severity=severity, source=source, tags=tags, tenant_id=tenant_id
        )

        if event_type == "*":
            sub_id = self._publisher.subscribe_category(category or EventCategory.CUSTOM, wrapped)
        else:
            sub_id = self._publisher.subscribe(event_type, wrapped)

        self._handlers[sub_id] = event_type
        return sub_id

    def register_instance(self, instance: Any) -> list[str]:
        """
        Register all decorated methods on a class instance.

        Returns list of subscription IDs.
        """
        sub_ids: list[str] = []
        for attr_name in dir(instance):
            if attr_name.startswith("_"):
                continue
            try:
                attr = getattr(instance, attr_name)
            except Exception:
                continue
            if callable(attr) and hasattr(attr, "_event_subscription"):
                sub_id = self.register_function(attr)
                if sub_id:
                    sub_ids.append(sub_id)
        return sub_ids

    def register_module(self, module: Any) -> list[str]:
        """
        Register all decorated functions in a module.

        Returns list of subscription IDs.
        """
        sub_ids: list[str] = []
        for attr_name in dir(module):
            if attr_name.startswith("_"):
                continue
            try:
                attr = getattr(module, attr_name)
            except Exception:
                continue
            if callable(attr) and hasattr(attr, "_event_subscription"):
                sub_id = self.register_function(attr)
                if sub_id:
                    sub_ids.append(sub_id)
        return sub_ids

    def unregister_all(self) -> int:
        """Unregister all handlers registered through this registrar."""
        count = 0
        for sub_id in list(self._handlers.keys()):
            if self._publisher.unsubscribe(sub_id):
                count += 1
                del self._handlers[sub_id]
        return count

    def _wrap_with_filters(
        self,
        handler: Callable,
        severity: Optional[str] = None,
        source: Optional[str] = None,
        tags: Optional[list[str]] = None,
        tenant_id: Optional[str] = None,
    ) -> Callable:
        """Wrap a handler with filter checks."""
        @functools.wraps(handler)
        def filtered_handler(event: Event) -> Any:
            if severity is not None and event.severity.value != severity:
                return None
            if source is not None and event.source != source:
                return None
            if tags and not all(t in event.tags for t in tags):
                return None
            if tenant_id is not None and event.tenant_id != tenant_id:
                return None
            return handler(event)
        return filtered_handler


# ─── Class-based Subscriber ─────────────────────────────────────────────────

class EventSubscriber:
    """
    Base class for class-based event subscribers.

    Subclass this and use the @on_event decorator on methods.
    The register() method wires everything up.

    Usage:
        class MySubscriber(EventSubscriber):
            @on_event("compliance.violation.detected")
            def handle_violation(self, event: Event) -> None:
                print(f"Violation: {event.data}")

        subscriber = MySubscriber()
        subscriber.register(publisher)
    """

    def __init__(self) -> None:
        self._registrar = SubscriberRegistrar(getattr(self, "_publisher", None) or _get_default_publisher())
        self._subscription_ids: list[str] = []

    def register(self, publisher: EventPublisher) -> list[str]:
        """Register all decorated handlers with the given publisher."""
        self._registrar = SubscriberRegistrar(publisher)
        self._subscription_ids = self._registrar.register_instance(self)
        return self._subscription_ids

    def unregister(self) -> int:
        """Unregister all handlers."""
        count = self._registrar.unregister_all()
        self._subscription_ids.clear()
        return count


# ─── Async Handler Support ──────────────────────────────────────────────────

class AsyncEventSubscriber:
    """
    Base class for async event handlers.

    Supports both sync and async handler methods.
    """

    def __init__(self) -> None:
        self._publisher: Optional[EventPublisher] = None
        self._subscription_ids: list[str] = []

    def register(self, publisher: EventPublisher) -> list[str]:
        """Register all decorated handlers, wrapping async ones."""
        self._publisher = publisher
        sub_ids: list[str] = []
        for attr_name in dir(self):
            if attr_name.startswith("_"):
                continue
            try:
                attr = getattr(self, attr_name)
            except Exception:
                continue
            if callable(attr) and hasattr(attr, "_event_subscription"):
                sub_meta = attr._event_subscription
                handler = sub_meta["handler"]
                event_type = sub_meta["event_type"]
                category = sub_meta.get("category")

                if inspect.iscoroutinefunction(handler):
                    wrapped = self._wrap_async(handler)
                else:
                    wrapped = handler

                if event_type == "*":
                    sub_id = publisher.subscribe_category(
                        category or EventCategory.CUSTOM, wrapped
                    )
                else:
                    sub_id = publisher.subscribe(event_type, wrapped)
                sub_ids.append(sub_id)
        self._subscription_ids = sub_ids
        return sub_ids

    def _wrap_async(self, handler: Callable) -> Callable:
        """Wrap an async handler for sync invocation."""
        @functools.wraps(handler)
        def sync_wrapper(event: Event) -> Any:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Schedule as task if loop is already running
                    asyncio.ensure_future(handler(event))
                    return None
                return loop.run_until_complete(handler(event))
            except RuntimeError:
                # No event loop, create one
                return asyncio.run(handler(event))
        return sync_wrapper


# ─── Default Publisher Singleton ────────────────────────────────────────────

_default_publisher: Optional[EventPublisher] = None


def get_default_publisher() -> EventPublisher:
    """Get or create the default global event publisher."""
    global _default_publisher
    if _default_publisher is None:
        _default_publisher = EventPublisher()
    return _default_publisher


def _get_default_publisher() -> EventPublisher:
    return get_default_publisher()


def set_default_publisher(publisher: EventPublisher) -> None:
    """Set the default global event publisher."""
    global _default_publisher
    _default_publisher = publisher