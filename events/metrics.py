"""Event metrics for monitoring and observability.

Provides counters, gauges, and histograms for tracking event processing
performance, throughput, and error rates.
"""

from __future__ import annotations

import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .schema import Event, EventPriority, EventStatus

logger = logging.getLogger(__name__)


@dataclass
class MetricsSnapshot:
    """Point-in-time snapshot of event metrics.

    Attributes:
        timestamp: When the snapshot was taken.
        total_published: Total events published.
        total_processed: Total events processed.
        total_failed: Total events failed.
        total_retried: Total events retried.
        events_per_second: Current throughput.
        average_latency_ms: Average processing latency in milliseconds.
        p99_latency_ms: 99th percentile latency in milliseconds.
        events_by_type: Breakdown of events by type.
        events_by_priority: Breakdown of events by priority.
        events_by_status: Breakdown of events by status.
        error_counts: Count of errors by error type.
    """

    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    total_published: int = 0
    total_processed: int = 0
    total_failed: int = 0
    total_retried: int = 0
    events_per_second: float = 0.0
    average_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0
    events_by_type: Dict[str, int] = field(default_factory=dict)
    events_by_priority: Dict[str, int] = field(default_factory=dict)
    events_by_status: Dict[str, int] = field(default_factory=dict)
    error_counts: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the snapshot to a dictionary.

        Returns:
            Dictionary representation of the metrics snapshot.
        """
        return {
            "timestamp": self.timestamp.isoformat(),
            "total_published": self.total_published,
            "total_processed": self.total_processed,
            "total_failed": self.total_failed,
            "total_retried": self.total_retried,
            "events_per_second": self.events_per_second,
            "average_latency_ms": self.average_latency_ms,
            "p99_latency_ms": self.p99_latency_ms,
            "events_by_type": dict(self.events_by_type),
            "events_by_priority": dict(self.events_by_priority),
            "events_by_status": dict(self.events_by_status),
            "error_counts": dict(self.error_counts),
        }


class EventMetrics:
    """Collects and reports event processing metrics.

    Tracks event lifecycle metrics including publish counts, processing
    latency, error rates, and throughput. Provides periodic snapshots
    for monitoring and alerting.

    Example:
        >>> metrics = EventMetrics()
        >>> metrics.record_publish(event)
        >>> metrics.record_processing(event, latency_ms=45.2)
        >>> snapshot = metrics.get_snapshot()
    """

    def __init__(self, *, window_size: int = 1000) -> None:
        """Initialize the event metrics collector.

        Args:
            window_size: Number of recent latency measurements to retain
                for percentile calculations.
        """
        self._total_published = 0
        self._total_processed = 0
        self._total_failed = 0
        self._total_retried = 0
        self._events_by_type: Dict[str, int] = defaultdict(int)
        self._events_by_priority: Dict[str, int] = defaultdict(int)
        self._events_by_status: Dict[str, int] = defaultdict(int)
        self._error_counts: Dict[str, int] = defaultdict(int)
        self._latency_window: List[float] = []
        self._window_size = window_size
        self._start_time = time.monotonic()
        self._last_snapshot_time = self._start_time

    def record_publish(self, event: Event) -> None:
        """Record an event publication.

        Args:
            event: The published event.
        """
        self._total_published += 1
        self._events_by_type[event.event_type] += 1
        self._events_by_priority[event.priority.value] += 1
        self._events_by_status[event.status.value] += 1

    def record_processing(self, event: Event, *, latency_ms: float) -> None:
        """Record successful event processing.

        Args:
            event: The processed event.
            latency_ms: Processing latency in milliseconds.
        """
        self._total_processed += 1
        self._latency_window.append(latency_ms)
        if len(self._latency_window) > self._window_size:
            self._latency_window = self._latency_window[-self._window_size :]

    def record_failure(self, event: Event, *, error: Optional[str] = None) -> None:
        """Record an event processing failure.

        Args:
            event: The failed event.
            error: Optional error message.
        """
        self._total_failed += 1
        error_type = error or "unknown"
        self._error_counts[error_type] += 1

    def record_retry(self, event: Event) -> None:
        """Record an event retry.

        Args:
            event: The retried event.
        """
        self._total_retried += 1

    def get_snapshot(self) -> MetricsSnapshot:
        """Get a current metrics snapshot.

        Returns:
            A MetricsSnapshot with current metrics values.
        """
        now = time.monotonic()
        elapsed = now - self._last_snapshot_time
        events_per_second = self._total_processed / elapsed if elapsed > 0 else 0.0
        self._last_snapshot_time = now

        avg_latency = 0.0
        p99_latency = 0.0
        if self._latency_window:
            sorted_latencies = sorted(self._latency_window)
            avg_latency = sum(sorted_latencies) / len(sorted_latencies)
            p99_index = int(len(sorted_latencies) * 0.99)
            p99_latency = sorted_latencies[min(p99_index, len(sorted_latencies) - 1)]

        return MetricsSnapshot(
            total_published=self._total_published,
            total_processed=self._total_processed,
            total_failed=self._total_failed,
            total_retried=self._total_retried,
            events_per_second=events_per_second,
            average_latency_ms=avg_latency,
            p99_latency_ms=p99_latency,
            events_by_type=dict(self._events_by_type),
            events_by_priority=dict(self._events_by_priority),
            events_by_status=dict(self._events_by_status),
            error_counts=dict(self._error_counts),
        )

    def reset(self) -> None:
        """Reset all metrics to zero."""
        self._total_published = 0
        self._total_processed = 0
        self._total_failed = 0
        self._total_retried = 0
        self._events_by_type.clear()
        self._events_by_priority.clear()
        self._events_by_status.clear()
        self._error_counts.clear()
        self._latency_window.clear()
        self._start_time = time.monotonic()
        self._last_snapshot_time = self._start_time
