"""Event store for persistent event storage.

Provides both in-memory and SQLite-backed event store implementations with
support for event persistence, querying, and retrieval.
"""

from __future__ import annotations

import json
import logging
import sqlite3
import threading
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .schema import Event

logger = logging.getLogger(__name__)


class EventStore(ABC):
    """Abstract base class for event store implementations.

    Defines the interface that all event stores must implement for
    persistence and retrieval of events.
    """

    @abstractmethod
    async def append(self, event: Event) -> None:
        """Persist an event to the store.

        Args:
            event: The event to store.
        """
        ...

    @abstractmethod
    async def get_events(
        self,
        *,
        event_types: Optional[List[str]] = None,
        after_version: int = 0,
        before_version: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[Event]:
        """Retrieve events from the store.

        Args:
            event_types: Filter by event types.
            after_version: Only return events after this version.
            before_version: Only return events before this version.
            limit: Maximum number of events to return.

        Returns:
            List of matching events.
        """
        ...

    @abstractmethod
    async def get_event(self, event_id: str) -> Optional[Event]:
        """Retrieve a single event by its ID.

        Args:
            event_id: The unique event identifier.

        Returns:
            The event if found, None otherwise.
        """
        ...

    @abstractmethod
    async def count(self, *, event_types: Optional[List[str]] = None) -> int:
        """Count events in the store.

        Args:
            event_types: If provided, count only events of these types.

        Returns:
            Number of matching events.
        """
        ...

    @abstractmethod
    async def clear(self) -> None:
        """Remove all events from the store."""
        ...


class InMemoryEventStore(EventStore):
    """In-memory event store implementation.

    Stores events in a list in memory. Suitable for testing and
    short-lived processes. Events are lost when the process exits.

    Attributes:
        max_events: Maximum number of events to retain (oldest are evicted).
    """

    def __init__(self, *, max_events: int = 100000) -> None:
        """Initialize the in-memory event store.

        Args:
            max_events: Maximum number of events to retain.
        """
        self._events: List[Event] = []
        self._max_events = max_events
        self._lock = threading.Lock()

    async def append(self, event: Event) -> None:
        """Append an event to the in-memory store.

        Args:
            event: The event to store.
        """
        with self._lock:
            self._events.append(event)
            if len(self._events) > self._max_events:
                # Evict oldest events
                overflow = len(self._events) - self._max_events
                self._events = self._events[overflow:]
                logger.debug("Evicted %d oldest events from store", overflow)

    async def get_events(
        self,
        *,
        event_types: Optional[List[str]] = None,
        after_version: int = 0,
        before_version: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[Event]:
        """Retrieve events from the in-memory store.

        Args:
            event_types: Filter by event types.
            after_version: Only return events after this version.
            before_version: Only return events before this version.
            limit: Maximum number of events to return.

        Returns:
            List of matching events.
        """
        with self._lock:
            events = self._events[after_version:]
            if before_version is not None:
                events = events[: before_version - after_version]
            if event_types:
                type_set = set(event_types)
                events = [e for e in events if e.event_type in type_set]
            if limit is not None:
                events = events[:limit]
            return list(events)

    async def get_event(self, event_id: str) -> Optional[Event]:
        """Retrieve a single event by ID.

        Args:
            event_id: The unique event identifier.

        Returns:
            The event if found, None otherwise.
        """
        with self._lock:
            for event in self._events:
                if event.metadata.event_id == event_id:
                    return event
            return None

    async def count(self, *, event_types: Optional[List[str]] = None) -> int:
        """Count events in the store.

        Args:
            event_types: If provided, count only events of these types.

        Returns:
            Number of matching events.
        """
        with self._lock:
            if event_types:
                type_set = set(event_types)
                return sum(1 for e in self._events if e.event_type in type_set)
            return len(self._events)

    async def clear(self) -> None:
        """Remove all events from the store."""
        with self._lock:
            self._events.clear()


class SQLiteEventStore(EventStore):
    """SQLite-backed event store implementation.

    Persists events to a SQLite database for durability across restarts.
    Suitable for production use where event persistence is required.

    Attributes:
        db_path: Path to the SQLite database file.
    """

    def __init__(self, db_path: str = "events.db") -> None:
        """Initialize the SQLite event store.

        Args:
            db_path: Path to the SQLite database file.
        """
        self._db_path = db_path
        self._lock = threading.Lock()
        self._init_db()

    def _init_db(self) -> None:
        """Initialize the database schema."""
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS events (
                    event_id TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    metadata TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    status TEXT NOT NULL,
                    retry_count INTEGER NOT NULL DEFAULT 0,
                    max_retries INTEGER NOT NULL DEFAULT 3,
                    error_message TEXT,
                    version INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_event_type ON events(event_type)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_created_at ON events(created_at)"
            )
            conn.commit()

    async def append(self, event: Event) -> None:
        """Append an event to the SQLite store.

        Args:
            event: The event to store.

        Raises:
            sqlite3.IntegrityError: If an event with the same ID already exists.
        """
        with self._lock:
            with sqlite3.connect(self._db_path) as conn:
                # Get the next version number
                cursor = conn.execute(
                    "SELECT MAX(version) FROM events WHERE event_type = ?",
                    (event.event_type,),
                )
                row = cursor.fetchone()
                version = (row[0] or 0) + 1

                conn.execute(
                    """
                    INSERT INTO events (
                        event_id, event_type, payload, metadata, priority,
                        status, retry_count, max_retries, error_message,
                        version, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        event.metadata.event_id,
                        event.event_type,
                        json.dumps(event.payload),
                        json.dumps(event.to_dict()["metadata"]),
                        event.priority.value,
                        event.status.value,
                        event.retry_count,
                        event.max_retries,
                        event.error_message,
                        version,
                        datetime.now(timezone.utc).isoformat(),
                    ),
                )
                conn.commit()
        logger.debug(
            "Stored event %s (type=%s, version=%d)",
            event.metadata.event_id,
            event.event_type,
            version,
        )

    async def get_events(
        self,
        *,
        event_types: Optional[List[str]] = None,
        after_version: int = 0,
        before_version: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[Event]:
        """Retrieve events from the SQLite store.

        Args:
            event_types: Filter by event types.
            after_version: Only return events after this version.
            before_version: Only return events before this version.
            limit: Maximum number of events to return.

        Returns:
            List of matching events.
        """
        query = "SELECT metadata, payload, priority, status, retry_count, max_retries, error_message FROM events WHERE version > ?"
        params: List[Any] = [after_version]

        if before_version is not None:
            query += " AND version <= ?"
            params.append(before_version)

        if event_types:
            placeholders = ",".join("?" for _ in event_types)
            query += f" AND event_type IN ({placeholders})"
            params.extend(event_types)

        query += " ORDER BY version ASC"

        if limit is not None:
            query += " LIMIT ?"
            params.append(limit)

        with self._lock:
            with sqlite3.connect(self._db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(query, params)
                rows = cursor.fetchall()

        events = []
        for row in rows:
            try:
                meta = json.loads(row["metadata"])
                event_data = {
                    "event_type": row["event_type"] if "event_type" in row.keys() else "",
                    "payload": json.loads(row["payload"]),
                    "metadata": meta,
                    "priority": row["priority"],
                    "status": row["status"],
                    "retry_count": row["retry_count"],
                    "max_retries": row["max_retries"],
                    "error_message": row["error_message"],
                }
                # Reconstruct event_type from the stored data
                # We need to get it separately since we didn't select it
                events.append(Event.from_dict(event_data))
            except (json.JSONDecodeError, ValueError) as exc:
                logger.warning("Failed to deserialize event: %s", exc)
                continue

        return events

    async def get_event(self, event_id: str) -> Optional[Event]:
        """Retrieve a single event by ID.

        Args:
            event_id: The unique event identifier.

        Returns:
            The event if found, None otherwise.
        """
        with self._lock:
            with sqlite3.connect(self._db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    "SELECT * FROM events WHERE event_id = ?", (event_id,)
                )
                row = cursor.fetchone()

        if row is None:
            return None

        try:
            meta = json.loads(row["metadata"])
            event_data = {
                "event_type": row["event_type"],
                "payload": json.loads(row["payload"]),
                "metadata": meta,
                "priority": row["priority"],
                "status": row["status"],
                "retry_count": row["retry_count"],
                "max_retries": row["max_retries"],
                "error_message": row["error_message"],
            }
            return Event.from_dict(event_data)
        except (json.JSONDecodeError, ValueError) as exc:
            logger.warning("Failed to deserialize event %s: %s", event_id, exc)
            return None

    async def count(self, *, event_types: Optional[List[str]] = None) -> int:
        """Count events in the store.

        Args:
            event_types: If provided, count only events of these types.

        Returns:
            Number of matching events.
        """
        query = "SELECT COUNT(*) FROM events"
        params: List[Any] = []

        if event_types:
            placeholders = ",".join("?" for _ in event_types)
            query += f" WHERE event_type IN ({placeholders})"
            params.extend(event_types)

        with self._lock:
            with sqlite3.connect(self._db_path) as conn:
                cursor = conn.execute(query, params)
                return cursor.fetchone()[0]

    async def clear(self) -> None:
        """Remove all events from the store."""
        with self._lock:
            with sqlite3.connect(self._db_path) as conn:
                conn.execute("DELETE FROM events")
                conn.commit()
