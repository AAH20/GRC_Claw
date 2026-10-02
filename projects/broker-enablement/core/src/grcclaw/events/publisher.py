"""
Event publisher for GRC_Claw.

Provides the publish/subscribe infrastructure for emitting events to
subscribers with support for filtering, middleware, and delivery guarantees.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from .schema import (
    Event,
    EventCategory,
    EventSchemaRegistry,
    EventSeverity,
    EventStatus,
    create_default_registry,
)

logger = logging.getLogger(__name__)


# ─── Delivery Guarantees ────────────────────────────────────────────────────

class DeliveryGuarantee(str, Enum):
    """Delivery guarantee levels for published events."""

    AT_MOST_ONCE = "at_most_once"
    AT_LEAST_ONCE = "at_least_once"
    EXACTLY_ONCE = "exactly_once"


# ─── Publish Result ─────────────────────────────────────────────────────────

@dataclass
class PublishResult:
    """Result of publishing an event."""

    event_id: str
    success: bool
    subscriber_count: int = 0
    delivered_count: int = 0
    failed_count: int = 0
    errors: list[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    @property
    def all_delivered(self) -> bool:
        return self.failed_count == 0 and self.delivered_count == self.subscriber_count


# ─── Event Publisher ────────────────────────────────────────────────────────

class EventPublisher:
    """
    Central event publisher for GRC_Claw.

    Manages subscriber registration, event filtering, middleware execution,
    and event delivery with configurable delivery guarantees.
    """

    def __init__(
        self,
        schema_registry: EventSchemaRegistry | None = None,
        delivery_guarantee: DeliveryGuarantee = DeliveryGuarantee.AT_LEAST_ONCE,
    ) -> None:
        self._registry = schema_registry or create_default_registry()
        self._delivery_guarantee = delivery_guarantee
        self._subscribers: dict[str, list[Callable]] = defaultdict(list)
        self._category_subscribers: dict[EventCategory, list[Callable]] = defaultdict(list)
        self._global_subscribers: list[Callable] = []
        self._middleware: list[Callable] = []
        self._event_store: Any | None = None
        self._published_count: int = 0
        self._failed_count: int = 0

    @property
    def registry(self) -> EventSchemaRegistry:
        return self._registry

    @property
    def published_count(self) -> int:
        return self._published_count

    @property
    def failed_count(self) -> int:
        return self._failed_count

    def set_event_store(self, event_store: Any) -> None:
        """Attach an event store for persistence before publishing."""
        self._event_store = event_store

    def use(self, middleware: Callable) -> None:
        """Register middleware that runs before event delivery."""
        self._middleware.append(middleware)

    def subscribe(
        self,
        event_type: str,
        handler: Callable[[Event], Any],
    ) -> str:
        """
        Subscribe a handler to a specific event type.

        Returns a subscription ID that can be used to unsubscribe.
        """
        sub_id = str(uuid.uuid4())
        wrapped = _Subscription(sub_id, event_type, handler)
        self._subscribers[event_type].append(wrapped)
        return sub_id

    def subscribe_category(
        self,
        category: EventCategory,
        handler: Callable[[Event], Any],
    ) -> str:
        """Subscribe a handler to all events in a category."""
        sub_id = str(uuid.uuid4())
        wrapped = _Subscription(sub_id, f"category:{category.value}", handler)
        self._category_subscribers[category].append(wrapped)
        return sub_id

    def subscribe_all(self, handler: Callable[[Event], Any]) -> str:
        """Subscribe a handler to all events."""
        sub_id = str(uuid.uuid4())
        wrapped = _Subscription(sub_id, "*", handler)
        self._global_subscribers.append(wrapped)
        return sub_id

    def unsubscribe(self, subscription_id: str) -> bool:
        """Remove a subscription by ID. Returns True if found and removed."""
        for subs in self._subscribers.values():
            for i, sub in enumerate(subs):
                if sub.id == subscription_id:
                    subs.pop(i)
                    return True
        for subs in self._category_subscribers.values():
            for i, sub in enumerate(subs):
                if sub.id == subscription_id:
                    subs.pop(i)
                    return True
        for i, sub in enumerate(self._global_subscribers):
            if sub.id == subscription_id:
                self._global_subscribers.pop(i)
                return True
        return False

    def publish(self, event: Event) -> PublishResult:
        """
        Publish an event to all matching subscribers.

        Runs middleware, validates against schema, persists to event store,
        and delivers to all matching subscribers.
        """
        result = PublishResult(event_id=event.id, success=True)

        # Validate against schema
        validation_errors = self._registry.validate_event(event)
        if validation_errors:
            result.success = False
            result.errors.extend(validation_errors)
            self._failed_count += 1
            return result

        # Run middleware
        for mw in self._middleware:
            try:
                event = mw(event) or event
            except Exception as exc:
                logger.warning("middleware error: %s", exc)

        # Persist to event store
        if self._event_store is not None:
            try:
                self._event_store.append(event)
            except Exception as exc:
                logger.error("event store append failed: %s", exc)
                if self._delivery_guarantee == DeliveryGuarantee.EXACTLY_ONCE:
                    result.success = False
                    result.errors.append(f"event store error: {exc}")
                    self._failed_count += 1
                    return result

        # Collect matching subscribers
        matching: list[_Subscription] = []
        matching.extend(self._subscribers.get(event.type, []))
        matching.extend(self._category_subscribers.get(event.category, []))
        matching.extend(self._global_subscribers)

        result.subscriber_count = len(matching)

        # Deliver to each subscriber
        for sub in matching:
            try:
                sub.handler(event)
                result.delivered_count += 1
            except Exception as exc:
                logger.error(
                    "subscriber %s failed for event %s: %s",
                    sub.id, event.id, exc,
                )
                result.failed_count += 1
                result.errors.append(f"subscriber {sub.id}: {exc}")

        if result.failed_count > 0:
            result.success = False
            event.status = EventStatus.FAILED
            event.error = "; ".join(result.errors)
        else:
            event.status = EventStatus.PROCESSED
            event.processed_at = datetime.now(UTC).isoformat()

        self._published_count += 1
        return result

    async def publish_async(self, event: Event) -> PublishResult:
        """Async version of publish for non-blocking event emission."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.publish, event)

    def create_event(
        self,
        event_type: str,
        data: dict[str, Any],
        category: EventCategory = EventCategory.CUSTOM,
        severity: EventSeverity = EventSeverity.INFO,
        source: str = "",
        correlation_id: str | None = None,
        causation_id: str | None = None,
        trace_id: str | None = None,
        tags: list[str] | None = None,
        tenant_id: str | None = None,
        agent_id: str | None = None,
    ) -> Event:
        """Convenience method to create and return an Event (without publishing)."""
        return Event(
            type=event_type,
            category=category,
            severity=severity,
            source=source,
            data=data,
            correlation_id=correlation_id,
            causation_id=causation_id,
            trace_id=trace_id,
            tags=tags or [],
            tenant_id=tenant_id,
            agent_id=agent_id,
        )

    def get_stats(self) -> dict[str, Any]:
        """Return publisher statistics."""
        return {
            "published_count": self._published_count,
            "failed_count": self._failed_count,
            "subscriber_count": sum(
                len(subs) for subs in self._subscribers.values()
            ),
            "category_subscriber_count": sum(
                len(subs) for subs in self._category_subscribers.values()
            ),
            "global_subscriber_count": len(self._global_subscribers),
            "middleware_count": len(self._middleware),
            "delivery_guarantee": self._delivery_guarantee.value,
        }


# ─── Subscription Wrapper ───────────────────────────────────────────────────

@dataclass
class _Subscription:
    """Internal wrapper for subscriber metadata."""

    id: str
    event_type: str
    handler: Callable[[Event], Any]


# ─── Typed Event Builders ───────────────────────────────────────────────────

class EventBuilder:
    """
    Fluent builder for constructing well-formed events.

    Example:
        event = EventBuilder("compliance.violation.detected") \\
            .with_data(framework="SOC2", control_id="CC6.1") \\
            .with_severity(EventSeverity.HIGH) \\
            .with_source("compliance-monitor") \\
            .with_tag("production") \\
            .build()
    """

    def __init__(self, event_type: str) -> None:
        self._type = event_type
        self._category = EventCategory.CUSTOM
        self._severity = EventSeverity.INFO
        self._source = ""
        self._data: dict[str, Any] = {}
        self._metadata: dict[str, Any] = {}
        self._correlation_id: str | None = None
        self._causation_id: str | None = None
        self._trace_id: str | None = None
        self._tags: list[str] = []
        self._tenant_id: str | None = None
        self._agent_id: str | None = None

    def with_category(self, category: EventCategory) -> EventBuilder:
        self._category = category
        return self

    def with_severity(self, severity: EventSeverity) -> EventBuilder:
        self._severity = severity
        return self

    def with_source(self, source: str) -> EventBuilder:
        self._source = source
        return self

    def with_data(self, **kwargs: Any) -> EventBuilder:
        self._data.update(kwargs)
        return self

    def with_metadata(self, **kwargs: Any) -> EventBuilder:
        self._metadata.update(kwargs)
        return self

    def with_correlation(self, correlation_id: str) -> EventBuilder:
        self._correlation_id = correlation_id
        return self

    def with_causation(self, causation_id: str) -> EventBuilder:
        self._causation_id = causation_id
        return self

    def with_trace(self, trace_id: str) -> EventBuilder:
        self._trace_id = trace_id
        return self

    def with_tag(self, tag: str) -> EventBuilder:
        self._tags.append(tag)
        return self

    def with_tenant(self, tenant_id: str) -> EventBuilder:
        self._tenant_id = tenant_id
        return self

    def with_agent(self, agent_id: str) -> EventBuilder:
        self._agent_id = agent_id
        return self

    def build(self) -> Event:
        return Event(
            type=self._type,
            category=self._category,
            severity=self._severity,
            source=self._source,
            data=self._data,
            metadata=self._metadata,
            correlation_id=self._correlation_id,
            causation_id=self._causation_id,
            trace_id=self._trace_id,
            tags=self._tags,
            tenant_id=self._tenant_id,
            agent_id=self._agent_id,
        )
