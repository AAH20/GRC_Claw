"""
Event store for GRC_Claw.

Provides persistent storage for events with support for querying,
filtering, and time-based retrieval. Includes both in-memory and
file-based backends.
"""

from __future__ import annotations

import json
import logging
import os
import threading
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Optional
import uuid

from .schema import Event, EventCategory, EventStatus, EventSeverity

logger = logging.getLogger(__name__)


# ─── Query Filters ──────────────────────────────────────────────────────────

@dataclass
class EventQuery:
    """Query parameters for filtering events in the store."""

    event_type: Optional[str] = None
    category: Optional[EventCategory] = None
    severity: Optional[EventSeverity] = None
    status: Optional[EventStatus] = None
    source: Optional[str] = None
    correlation_id: Optional[str] = None
    trace_id: Optional[str] = None
    tenant_id: Optional[str] = None
    agent_id: Optional[str] = None
    tags: Optional[list[str]] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    limit: int = 100
    offset: int = 0

    def matches(self, event: Event) -> bool:
        """Check if an event matches this query."""
        if self.event_type is not None and event.type != self.event_type:
            return False
        if self.category is not None and event.category != self.category:
            return False
        if self.severity is not None and event.severity != self.severity:
            return False
        if self.status is not None and event.status != self.status:
            return False
        if self.source is not None and event.source != self.source:
            return False
        if self.correlation_id is not None and event.correlation_id != self.correlation_id:
            return False
        if self.trace_id is not None and event.trace_id != self.trace_id:
            return False
        if self.tenant_id is not None and event.tenant_id != self.tenant_id:
            return False
        if self.agent_id is not None and event.agent_id != self.agent_id:
            return False
        if self.tags and not all(t in event.tags for t in self.tags):
            return False
        if self.start_time is not None and event.timestamp < self.start_time:
            return False
        if self.end_time is not None and event.timestamp > self.end_time:
            return False
        return True


# ─── Storage Backend ────────────────────────────────────────────────────────

class StorageBackend:
    """Abstract base class for event storage backends."""

    def append(self, event: Event) -> None:
        raise NotImplementedError

    def query(self, query: EventQuery) -> list[Event]:
        raise NotImplementedError

    def get(self, event_id: str) -> Optional[Event]:
        raise NotImplementedError

    def count(self, query: Optional[EventQuery] = None) -> int:
        raise NotImplementedError

    def clear(self) -> None:
        raise NotImplementedError


class InMemoryBackend(StorageBackend):
    """In-memory storage backend for events."""

    def __init__(self, max_size: int = 10000) -> None:
        self._events: list[Event] = []
        self._index: dict[str, Event] = {}
        self._max_size = max_size
        self._lock = threading.Lock()

    def append(self, event: Event) -> None:
        with self._lock:
            self._events.append(event)
            self._index[event.id] = event
            # Evict oldest if over capacity
            if len(self._events) > self._max_size:
                evicted = self._events.pop(0)
                self._index.pop(evicted.id, None)

    def query(self, query: EventQuery) -> list[Event]:
        with self._lock:
            results = [e for e in self._events if query.matches(e)]
            # Sort by timestamp descending
            results.sort(key=lambda e: e.timestamp, reverse=True)
            return results[query.offset : query.offset + query.limit]

    def get(self, event_id: str) -> Optional[Event]:
        return self._index.get(event_id)

    def count(self, query: Optional[EventQuery] = None) -> int:
        with self._lock:
            if query is None:
                return len(self._events)
            return sum(1 for e in self._events if query.matches(e))

    def clear(self) -> None:
        with self._lock:
            self._events.clear()
            self._index.clear()


class FileBackend(StorageBackend):
    """
    File-based storage backend using JSON lines format.

    Events are appended to a file, one JSON object per line.
    Supports time-based file rotation.
    """

    def __init__(
        self,
        base_path: str | Path,
        rotate_daily: bool = True,
        max_file_size_mb: float = 100.0,
    ) -> None:
        self._base_path = Path(base_path)
        self._base_path.mkdir(parents=True, exist_ok=True)
        self._rotate_daily = rotate_daily
        self._max_file_size_bytes = max_file_size_mb * 1024 * 1024
        self._lock = threading.Lock()
        self._current_file: Optional[Path] = None
        self._ensure_file()

    def _ensure_file(self) -> None:
        if self._rotate_daily:
            date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            self._current_file = self._base_path / f"events-{date_str}.jsonl"
        else:
            self._current_file = self._base_path / "events.jsonl"

    def _rotate_if_needed(self) -> None:
        if self._current_file is None:
            self._ensure_file()
            return
        if self._rotate_daily:
            date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            expected = self._base_path / f"events-{date_str}.jsonl"
            if self._current_file != expected:
                self._current_file = expected
        if self._current_file.exists():
            if self._current_file.stat().st_size >= self._max_file_size_bytes:
                # Add timestamp suffix for rotation
                ts = datetime.now(timezone.utc).strftime("%H%M%S")
                stem = self._current_file.stem
                self._current_file = self._base_path / f"{stem}-{ts}.jsonl"

    def append(self, event: Event) -> None:
        with self._lock:
            self._rotate_if_needed()
            assert self._current_file is not None
            with open(self._current_file, "a", encoding="utf-8") as f:
                f.write(event.to_json() + "\n")

    def query(self, query: EventQuery) -> list[Event]:
        results: list[Event] = []
        files = sorted(self._base_path.glob("events-*.jsonl"), reverse=True)
        for file_path in files:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        event = Event.from_json(line)
                        if query.matches(event):
                            results.append(event)
                    except Exception as exc:
                        logger.warning("failed to parse event from %s: %s", file_path, exc)
            if len(results) >= query.offset + query.limit:
                break
        results.sort(key=lambda e: e.timestamp, reverse=True)
        return results[query.offset : query.offset + query.limit]

    def get(self, event_id: str) -> Optional[Event]:
        files = sorted(self._base_path.glob("events-*.jsonl"), reverse=True)
        for file_path in files:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        event = Event.from_json(line)
                        if event.id == event_id:
                            return event
                    except Exception:
                        continue
        return None

    def count(self, query: Optional[EventQuery] = None) -> int:
        count = 0
        files = sorted(self._base_path.glob("events-*.jsonl"), reverse=True)
        for file_path in files:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        event = Event.from_json(line)
                        if query is None or query.matches(event):
                            count += 1
                    except Exception:
                        continue
        return count

    def clear(self) -> None:
        with self._lock:
            for file_path in self._base_path.glob("events-*.jsonl"):
                file_path.unlink(missing_ok=True)


# ─── Event Store ────────────────────────────────────────────────────────────

class EventStore:
    """
    High-level event store with indexing and aggregation.

    Wraps a storage backend and provides convenient query methods,
    statistics, and event replay capabilities.
    """

    def __init__(self, backend: Optional[StorageBackend] = None) -> None:
        self._backend = backend or InMemoryBackend()
        self._type_index: dict[str, list[str]] = defaultdict(list)
        self._correlation_index: dict[str, list[str]] = defaultdict(list)
        self._trace_index: dict[str, list[str]] = defaultdict(list)
        self._lock = threading.Lock()

    @property
    def backend(self) -> StorageBackend:
        return self._backend

    def append(self, event: Event) -> None:
        """Store an event and update indexes."""
        self._backend.append(event)
        with self._lock:
            self._type_index[event.type].append(event.id)
            if event.correlation_id:
                self._correlation_index[event.correlation_id].append(event.id)
            if event.trace_id:
                self._trace_index[event.trace_id].append(event.id)

    def get(self, event_id: str) -> Optional[Event]:
        """Retrieve a single event by ID."""
        return self._backend.get(event_id)

    def query(self, query: EventQuery) -> list[Event]:
        """Query events with filters."""
        return self._backend.query(query)

    def find_by_type(self, event_type: str, limit: int = 100) -> list[Event]:
        """Find events by type."""
        return self.query(EventQuery(event_type=event_type, limit=limit))

    def find_by_category(
        self, category: EventCategory, limit: int = 100
    ) -> list[Event]:
        """Find events by category."""
        return self.query(EventQuery(category=category, limit=limit))

    def find_by_correlation(
        self, correlation_id: str, limit: int = 100
    ) -> list[Event]:
        """Find events by correlation ID."""
        return self.query(EventQuery(correlation_id=correlation_id, limit=limit))

    def find_by_trace(self, trace_id: str, limit: int = 100) -> list[Event]:
        """Find events by trace ID."""
        return self.query(EventQuery(trace_id=trace_id, limit=limit))

    def find_by_time_range(
        self,
        start: str,
        end: str,
        event_type: Optional[str] = None,
        limit: int = 100,
    ) -> list[Event]:
        """Find events within a time range."""
        return self.query(
            EventQuery(
                event_type=event_type,
                start_time=start,
                end_time=end,
                limit=limit,
            )
        )

    def count(self, query: Optional[EventQuery] = None) -> int:
        """Count events matching a query."""
        return self._backend.count(query)

    def get_stats(self) -> dict[str, Any]:
        """Get store statistics."""
        return {
            "total_events": self._backend.count(),
            "indexed_types": len(self._type_index),
            "indexed_correlations": len(self._correlation_index),
            "indexed_traces": len(self._trace_index),
        }

    def clear(self) -> None:
        """Clear all events and indexes."""
        self._backend.clear()
        with self._lock:
            self._type_index.clear()
            self._correlation_index.clear()
            self._trace_index.clear()

    def export_to_file(self, path: str | Path, query: Optional[EventQuery] = None) -> int:
        """Export events to a JSON lines file. Returns count exported."""
        events = self._backend.query(query or EventQuery(limit=100000))
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "w", encoding="utf-8") as f:
            for event in events:
                f.write(event.to_json() + "\n")
        return len(events)

    def import_from_file(self, path: str | Path) -> int:
        """Import events from a JSON lines file. Returns count imported."""
        source = Path(path)
        if not source.exists():
            raise FileNotFoundError(f"event file not found: {source}")
        count = 0
        with open(source, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    event = Event.from_json(line)
                    self.append(event)
                    count += 1
                except Exception as exc:
                    logger.warning("failed to import event: %s", exc)
        return count