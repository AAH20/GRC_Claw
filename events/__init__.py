"""Event-driven integration system for agentic AI marketing projects.

Provides event bus, schema, routing, sourcing, replay, subscriber, publisher,
store, and metrics capabilities.
"""

from .bus import EventBus
from .schema import Event, EventMetadata, EventPriority, EventStatus
from .router import EventRouter, RouteRule
from .sourcing import EventSourcing, AggregateState
from .replay import EventReplayer, ReplayResult
from .subscriber import EventSubscriber, Subscription
from .publisher import EventPublisher
from .store import EventStore, InMemoryEventStore, SQLiteEventStore
from .metrics import EventMetrics, MetricsSnapshot

__all__ = [
    "EventBus",
    "Event",
    "EventMetadata",
    "EventPriority",
    "EventStatus",
    "EventRouter",
    "RouteRule",
    "EventSourcing",
    "AggregateState",
    "EventReplayer",
    "ReplayResult",
    "EventSubscriber",
    "Subscription",
    "EventPublisher",
    "EventStore",
    "InMemoryEventStore",
    "SQLiteEventStore",
    "EventMetrics",
    "MetricsSnapshot",
]

__version__ = "1.0.0"
