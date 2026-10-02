# Event-Driven Integration System

A production-grade event-driven integration system for agentic AI marketing projects. Provides event bus, schema, routing, sourcing, replay, subscriber, publisher, store, and metrics capabilities.

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Publisher  │────▶│  Event Bus  │────▶│  Subscriber │
└─────────────┘     └──────┬──────┘     └─────────────┘
                           │
                    ┌──────┴──────┐
                    │   Router    │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
        ┌─────▼─────┐ ┌───▼────┐ ┌────▼────┐
        │  Sourcing │ │ Replay │ │  Store  │
        └───────────┘ └────────┘ └─────────┘
```

## Components

### Event Bus (`bus.py`)
Central publish/subscribe messaging system. Decouples event producers from consumers with support for:
- Synchronous and asynchronous handlers
- Priority-based dispatch
- Middleware chain
- Error isolation
- Wildcard subscriptions

### Event Schema (`schema.py`)
Core event data structures with:
- Strongly-typed event metadata (correlation IDs, causation IDs, tracing)
- Priority levels (LOW, NORMAL, HIGH, CRITICAL)
- Lifecycle status tracking (PENDING → PROCESSING → COMPLETED/FAILED)
- Serialization/deserialization

### Event Router (`router.py`)
Pattern-based event routing with:
- Glob pattern matching on event types
- Content-based routing conditions
- Priority-ordered rule evaluation
- Default target fallback

### Event Sourcing (`sourcing.py`)
Aggregate state reconstruction via:
- Event stream persistence per aggregate
- Sync and async state handlers
- Snapshot support for performance
- Version tracking

### Event Replay (`replay.py`)
Historical event reprocessing with:
- Filtering by type, version, and custom predicates
- Batch processing with rate limiting
- Progress tracking and error handling
- Replay history

### Event Subscriber (`subscriber.py`)
High-level consumer interface with:
- Automatic acknowledgment
- Concurrency control (semaphores)
- Graceful shutdown
- Subscription lifecycle management

### Event Publisher (`publisher.py`)
High-level producer interface with:
- Automatic retry with exponential backoff
- Batch publishing
- Delivery confirmation
- Statistics tracking

### Event Store (`store.py`)
Persistent event storage with:
- **InMemoryEventStore**: Fast, non-persistent storage for testing
- **SQLiteEventStore**: Durable SQLite-backed storage for production
- Event querying by type, version, and time range

### Event Metrics (`metrics.py`)
Monitoring and observability with:
- Publish/processing counters
- Latency histograms (average, p99)
- Throughput measurement (events/second)
- Error rate tracking
- Breakdowns by type, priority, and status

## Quick Start

```python
import asyncio
from events import (
    EventBus, Event, EventMetadata, EventPriority,
    EventPublisher, EventSubscriber, EventRouter,
    InMemoryEventStore, EventMetrics,
)

async def main():
    # Create components
    bus = EventBus()
    publisher = EventPublisher(bus)
    subscriber = EventSubscriber(bus)
    store = InMemoryEventStore()
    metrics = EventMetrics()

    # Define a handler
    async def handle_campaign_created(event: Event) -> None:
        print(f"Campaign created: {event.payload}")
        metrics.record_processing(event, latency_ms=10.0)

    # Subscribe and start
    await subscriber.subscribe("campaign.created", handle_campaign_created)
    await subscriber.start()

    # Publish an event
    await publisher.publish(
        event_type="campaign.created",
        payload={"campaign_id": "camp_123", "name": "Summer Sale"},
        priority=EventPriority.HIGH,
    )

    # Let events process
    await asyncio.sleep(1)

    # Check metrics
    snapshot = metrics.get_snapshot()
    print(f"Processed: {snapshot.total_processed}")

    # Cleanup
    await subscriber.stop()

if __name__ == "__main__":
    asyncio.run(main())
```

## Event Sourcing Example

```python
from events import EventSourcing, Event

sourcing = EventSourcing[dict]()

# Register state handlers
sourcing.register_handler("campaign.created", lambda state, e: {**(state or {}), **e.payload})
sourcing.register_handler("campaign.updated", lambda state, e: {**(state or {}), **e.payload})

# Append events
await sourcing.append("camp_123", Event(event_type="campaign.created", payload={"name": "Summer"}))
await sourcing.append("camp_123", Event(event_type="campaign.updated", payload={"status": "active"}))

# Reconstruct state
result = await sourcing.get_state("camp_123")
print(result.state)  # {"name": "Summer", "status": "active"}
```

## Event Replay Example

```python
from events import EventReplayer

replayer = EventReplayer(store)

async def reprocess(event: Event) -> None:
    print(f"Replaying: {event.event_type}")

result = await replayer.replay(
    reprocess,
    event_types=["campaign.created"],
    batch_size=50,
    rate_limit=0.1,
)
print(f"Replayed {result.processed_events} events in {result.duration_seconds:.2f}s")
```

## Setup

Run the setup script to validate the installation:

```bash
cd ~/GRC_Claw/events
bash scripts/setup-events.sh
```

## Configuration

### Event Priorities
- `LOW`: Background tasks, non-urgent processing
- `NORMAL`: Standard business events
- `HIGH`: Time-sensitive operations
- `CRITICAL`: System-critical events requiring immediate attention

### Retry Policy
Events support configurable retry with exponential backoff:
- `max_retries`: Maximum retry attempts (default: 3)
- `retry_count`: Current attempt number
- Events exceeding max retries are marked as `DEAD_LETTER`

### Storage Backends
- **InMemoryEventStore**: Default, suitable for testing and ephemeral workloads
- **SQLiteEventStore**: Production-grade persistent storage

## Error Handling

The system provides multiple layers of error protection:
1. **Handler isolation**: Exceptions in one handler don't affect others
2. **Global error handlers**: Catch-all error callbacks on the bus
3. **Retry with backoff**: Automatic retry for transient failures
4. **Dead letter queue**: Failed events are marked for manual review

## Monitoring

Access metrics at any time:

```python
snapshot = metrics.get_snapshot()
print(f"Throughput: {snapshot.events_per_second:.1f} events/s")
print(f"P99 latency: {snapshot.p99_latency_ms:.1f}ms")
print(f"Error rate: {snapshot.total_failed / max(snapshot.total_processed, 1):.2%}")
```

## License

Part of the GRC_Claw project. See project root for license details.
