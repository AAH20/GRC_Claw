"""
GRC_Claw Event-Driven Architecture Framework

Unified event system for GRC (Governance, Risk, Compliance) processes.
Provides event schema registry, publishing, subscription, persistent
storage, replay, and audit capabilities.

Usage:
    from grcclaw.events import (
        EventPublisher, EventStore, EventReplayer, AuditTrail,
        EventBuilder, EventSchemaRegistry, Event, EventCategory,
    )

    # Create components
    publisher = EventPublisher()
    store = EventStore()
    publisher.set_event_store(store)

    # Publish an event
    event = EventBuilder("compliance.violation.detected") \\
        .with_category(EventCategory.COMPLIANCE) \\
        .with_data(framework="SOC2", control_id="CC6.1") \\
        .build()
    publisher.publish(event)

    # Replay events
    replayer = EventReplayer(store, publisher)
    result = replayer.replay_all(event_type="compliance.violation.detected")
"""

from .publisher import (
    DeliveryGuarantee,
    EventBuilder,
    EventPublisher,
    PublishResult,
)
from .replay import (
    AuditEntry,
    AuditTrail,
    ComplianceReport,
    EventReplayer,
    ReplayMode,
    ReplayResult,
)
from .schema import (
    Event,
    EventCategory,
    EventSchema,
    EventSchemaRegistry,
    EventSeverity,
    EventStatus,
    create_audit_event_schema,
    create_compliance_event_schema,
    create_default_registry,
    create_evidence_event_schema,
    create_policy_event_schema,
    create_risk_event_schema,
    create_system_event_schema,
    create_workflow_event_schema,
)
from .store import (
    EventQuery,
    EventStore,
    FileBackend,
    InMemoryBackend,
    StorageBackend,
)
from .subscriber import (
    AsyncEventSubscriber,
    EventSubscriber,
    SubscriberRegistrar,
    get_default_publisher,
    on_category,
    on_event,
    set_default_publisher,
)

__all__ = [
    # Schema
    "Event",
    "EventCategory",
    "EventSeverity",
    "EventStatus",
    "EventSchema",
    "EventSchemaRegistry",
    "create_default_registry",
    "create_compliance_event_schema",
    "create_risk_event_schema",
    "create_workflow_event_schema",
    "create_evidence_event_schema",
    "create_audit_event_schema",
    "create_policy_event_schema",
    "create_system_event_schema",
    # Publisher
    "EventPublisher",
    "EventBuilder",
    "PublishResult",
    "DeliveryGuarantee",
    # Subscriber
    "EventSubscriber",
    "AsyncEventSubscriber",
    "SubscriberRegistrar",
    "on_event",
    "on_category",
    "get_default_publisher",
    "set_default_publisher",
    # Store
    "EventStore",
    "EventQuery",
    "StorageBackend",
    "InMemoryBackend",
    "FileBackend",
    # Replay & Audit
    "EventReplayer",
    "AuditTrail",
    "ComplianceReport",
    "ReplayResult",
    "ReplayMode",
    "AuditEntry",
]
