"""
Event replay and audit for GRC_Claw.

Provides event replay capabilities for debugging, recovery, and
compliance auditing. Supports replaying events to subscribers,
generating audit trails, and time-travel debugging.
"""

from __future__ import annotations

import json
import logging
import uuid
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

from .publisher import EventPublisher, PublishResult
from .schema import Event, EventCategory
from .store import EventQuery, EventStore

logger = logging.getLogger(__name__)


# ─── Replay Modes ───────────────────────────────────────────────────────────

class ReplayMode(str, Enum):
    """Modes for event replay."""

    FULL = "full"
    SELECTIVE = "selective"
    TIME_RANGE = "time_range"
    CORRELATION = "correlation"
    TRACE = "trace"


# ─── Replay Result ──────────────────────────────────────────────────────────

@dataclass
class ReplayResult:
    """Result of an event replay operation."""

    replay_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    mode: ReplayMode = ReplayMode.FULL
    total_events: int = 0
    replayed_count: int = 0
    skipped_count: int = 0
    failed_count: int = 0
    results: list[PublishResult] = field(default_factory=list)
    started_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    finished_at: str | None = None
    errors: list[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return self.failed_count == 0

    @property
    def duration_seconds(self) -> float:
        start = datetime.fromisoformat(self.started_at)
        end = (
            datetime.fromisoformat(self.finished_at)
            if self.finished_at
            else datetime.now(UTC)
        )
        return (end - start).total_seconds()

    def to_dict(self) -> dict[str, Any]:
        return {
            "replay_id": self.replay_id,
            "mode": self.mode.value,
            "total_events": self.total_events,
            "replayed_count": self.replayed_count,
            "skipped_count": self.skipped_count,
            "failed_count": self.failed_count,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "duration_seconds": self.duration_seconds,
            "success": self.success,
            "errors": self.errors,
        }


# ─── Audit Entry ────────────────────────────────────────────────────────────

@dataclass
class AuditEntry:
    """A single audit trail entry."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_id: str = ""
    action: str = ""
    actor: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    details: dict[str, Any] = field(default_factory=dict)
    event_snapshot: dict[str, Any] | None = None
    compliance_framework: str | None = None
    retention_class: str = "standard"
    hash: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "event_id": self.event_id,
            "action": self.action,
            "actor": self.actor,
            "timestamp": self.timestamp,
            "details": self.details,
            "event_snapshot": self.event_snapshot,
            "compliance_framework": self.compliance_framework,
            "retention_class": self.retention_class,
            "hash": self.hash,
        }


# ─── Event Replayer ─────────────────────────────────────────────────────────

class EventReplayer:
    """
    Replays events from the event store to subscribers.

    Supports full replay, selective replay by type/category,
    time-range replay, and correlation/trace-based replay.
    """

    def __init__(
        self,
        event_store: EventStore,
        publisher: EventPublisher | None = None,
    ) -> None:
        self._store = event_store
        self._publisher = publisher
        self._replay_history: list[ReplayResult] = []
        self._filters: list[Callable[[Event], bool]] = []

    @property
    def store(self) -> EventStore:
        return self._store

    @property
    def publisher(self) -> EventPublisher | None:
        return self._publisher

    def add_filter(self, filter_fn: Callable[[Event], bool]) -> None:
        """Add a filter function that determines which events to replay."""
        self._filters.append(filter_fn)

    def clear_filters(self) -> None:
        """Remove all replay filters."""
        self._filters.clear()

    def replay_all(
        self,
        event_type: str | None = None,
        category: EventCategory | None = None,
        limit: int = 1000,
    ) -> ReplayResult:
        """
        Replay all events matching the given criteria.

        If a publisher is attached, events are re-published to subscribers.
        Otherwise, events are returned for manual processing.
        """
        query = EventQuery(
            event_type=event_type,
            category=category,
            limit=limit,
        )
        events = self._store.query(query)
        return self._execute_replay(events, ReplayMode.FULL)

    def replay_time_range(
        self,
        start: str,
        end: str,
        event_type: str | None = None,
        limit: int = 1000,
    ) -> ReplayResult:
        """Replay events within a specific time range."""
        query = EventQuery(
            event_type=event_type,
            start_time=start,
            end_time=end,
            limit=limit,
        )
        events = self._store.query(query)
        return self._execute_replay(events, ReplayMode.TIME_RANGE)

    def replay_by_correlation(
        self, correlation_id: str, limit: int = 1000
    ) -> ReplayResult:
        """Replay all events with a specific correlation ID."""
        events = self._store.find_by_correlation(correlation_id, limit=limit)
        return self._execute_replay(events, ReplayMode.CORRELATION)

    def replay_by_trace(
        self, trace_id: str, limit: int = 1000
    ) -> ReplayResult:
        """Replay all events with a specific trace ID."""
        events = self._store.find_by_trace(trace_id, limit=limit)
        return self._execute_replay(events, ReplayMode.TRACE)

    def replay_selective(
        self,
        event_ids: list[str],
    ) -> ReplayResult:
        """Replay specific events by their IDs."""
        events: list[Event] = []
        for eid in event_ids:
            event = self._store.get(eid)
            if event:
                events.append(event)
        return self._execute_replay(events, ReplayMode.SELECTIVE)

    def dry_run(
        self,
        event_type: str | None = None,
        category: EventCategory | None = None,
        limit: int = 1000,
    ) -> list[Event]:
        """
        Preview which events would be replayed without actually replaying them.
        """
        query = EventQuery(
            event_type=event_type,
            category=category,
            limit=limit,
        )
        events = self._store.query(query)
        if self._filters:
            events = [e for e in events if all(f(e) for f in self._filters)]
        return events

    def get_replay_history(self) -> list[ReplayResult]:
        """Get history of all replay operations."""
        return list(self._replay_history)

    def _execute_replay(
        self, events: list[Event], mode: ReplayMode
    ) -> ReplayResult:
        """Execute the replay of a set of events."""
        result = ReplayResult(mode=mode, total_events=len(events))

        # Apply filters
        if self._filters:
            filtered = [e for e in events if all(f(e) for f in self._filters)]
            result.skipped_count = len(events) - len(filtered)
            events = filtered

        for event in events:
            if self._publisher is not None:
                try:
                    pub_result = self._publisher.publish(event)
                    result.results.append(pub_result)
                    if pub_result.success:
                        result.replayed_count += 1
                    else:
                        result.failed_count += 1
                        result.errors.extend(pub_result.errors)
                except Exception as exc:
                    result.failed_count += 1
                    result.errors.append(f"replay failed for {event.id}: {exc}")
            else:
                result.replayed_count += 1

        result.finished_at = datetime.now(UTC).isoformat()
        self._replay_history.append(result)
        return result


# ─── Audit Trail ────────────────────────────────────────────────────────────

class AuditTrail:
    """
    Immutable audit trail for compliance and forensic purposes.

    Records all event-related actions with tamper-evident hashing,
    retention policies, and compliance framework tagging.
    """

    def __init__(
        self,
        event_store: EventStore,
        storage_path: str | Path | None = None,
    ) -> None:
        self._store = event_store
        self._entries: list[AuditEntry] = []
        self._storage_path = Path(storage_path) if storage_path else None
        if self._storage_path:
            self._storage_path.mkdir(parents=True, exist_ok=True)
        self._action_counts: dict[str, int] = defaultdict(int)
        self._last_hash: str = ""

    @property
    def entries(self) -> list[AuditEntry]:
        return list(self._entries)

    def record(
        self,
        event: Event,
        action: str,
        actor: str = "system",
        details: dict[str, Any] | None = None,
        compliance_framework: str | None = None,
        retention_class: str = "standard",
    ) -> AuditEntry:
        """
        Record an audit entry for an event action.

        Creates a tamper-evident chain by hashing the previous entry.
        """
        entry = AuditEntry(
            event_id=event.id,
            action=action,
            actor=actor,
            details=details or {},
            event_snapshot=event.to_dict(),
            compliance_framework=compliance_framework,
            retention_class=retention_class,
        )
        # Compute hash chain
        hash_input = f"{self._last_hash}:{entry.event_id}:{entry.action}:{entry.timestamp}"
        entry.hash = self._compute_hash(hash_input)
        self._last_hash = entry.hash

        self._entries.append(entry)
        self._action_counts[action] += 1

        # Persist if storage path is set
        if self._storage_path:
            self._persist_entry(entry)

        return entry

    def record_replay(
        self,
        replay_result: ReplayResult,
        actor: str = "system",
        compliance_framework: str | None = None,
    ) -> AuditEntry:
        """Record a replay operation in the audit trail."""
        return self.record(
            event=Event(id=replay_result.replay_id, type="audit.replay"),
            action="replay",
            actor=actor,
            details=replay_result.to_dict(),
            compliance_framework=compliance_framework,
            retention_class="audit",
        )

    def query(
        self,
        event_id: str | None = None,
        action: str | None = None,
        actor: str | None = None,
        compliance_framework: str | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
        limit: int = 100,
    ) -> list[AuditEntry]:
        """Query audit entries with filters."""
        results = self._entries
        if event_id is not None:
            results = [e for e in results if e.event_id == event_id]
        if action is not None:
            results = [e for e in results if e.action == action]
        if actor is not None:
            results = [e for e in results if e.actor == actor]
        if compliance_framework is not None:
            results = [e for e in results if e.compliance_framework == compliance_framework]
        if start_time is not None:
            results = [e for e in results if e.timestamp >= start_time]
        if end_time is not None:
            results = [e for e in results if e.timestamp <= end_time]
        return results[-limit:]

    def verify_integrity(self) -> tuple[bool, list[str]]:
        """
        Verify the integrity of the audit trail hash chain.

        Returns (is_valid, list_of_errors).
        """
        errors: list[str] = []
        prev_hash = ""
        for i, entry in enumerate(self._entries):
            hash_input = f"{prev_hash}:{entry.event_id}:{entry.action}:{entry.timestamp}"
            expected_hash = self._compute_hash(hash_input)
            if entry.hash != expected_hash:
                errors.append(
                    f"entry {i} ({entry.id}): hash mismatch"
                )
            prev_hash = entry.hash
        return len(errors) == 0, errors

    def get_stats(self) -> dict[str, Any]:
        """Get audit trail statistics."""
        return {
            "total_entries": len(self._entries),
            "action_counts": dict(self._action_counts),
            "first_entry_at": self._entries[0].timestamp if self._entries else None,
            "last_entry_at": self._entries[-1].timestamp if self._entries else None,
            "integrity_verified": self.verify_integrity()[0],
        }

    def export_jsonl(self, path: str | Path) -> int:
        """Export audit trail to a JSON lines file."""
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "w", encoding="utf-8") as f:
            f.writelines(json.dumps(entry.to_dict(), default=str) + "\n" for entry in self._entries)
        return len(self._entries)

    def _compute_hash(self, data: str) -> str:
        """Compute a simple hash for the audit chain."""
        import hashlib
        return hashlib.sha256(data.encode("utf-8")).hexdigest()

    def _persist_entry(self, entry: AuditEntry) -> None:
        """Persist a single audit entry to storage."""
        if self._storage_path is None:
            return
        date_str = datetime.now(UTC).strftime("%Y-%m-%d")
        file_path = self._storage_path / f"audit-{date_str}.jsonl"
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry.to_dict(), default=str) + "\n")


# ─── Compliance Report ──────────────────────────────────────────────────────

class ComplianceReport:
    """
    Generates compliance reports from the audit trail.

    Produces summaries suitable for auditors and compliance officers.
    """

    def __init__(self, audit_trail: AuditTrail) -> None:
        self._audit = audit_trail

    def generate(
        self,
        framework: str | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
    ) -> dict[str, Any]:
        """Generate a compliance report."""
        entries = self._audit.query(
            compliance_framework=framework,
            start_time=start_time,
            end_time=end_time,
            limit=100000,
        )

        # Aggregate by action
        by_action: dict[str, int] = defaultdict(int)
        by_actor: dict[str, int] = defaultdict(int)
        by_framework: dict[str, int] = defaultdict(int)
        by_retention: dict[str, int] = defaultdict(int)

        for entry in entries:
            by_action[entry.action] += 1
            by_actor[entry.actor] += 1
            fw = entry.compliance_framework or "untagged"
            by_framework[fw] += 1
            by_retention[entry.retention_class] += 1

        integrity_ok, integrity_errors = self._audit.verify_integrity()

        return {
            "report_id": str(uuid.uuid4()),
            "generated_at": datetime.now(UTC).isoformat(),
            "framework": framework,
            "period_start": start_time,
            "period_end": end_time,
            "total_entries": len(entries),
            "by_action": dict(by_action),
            "by_actor": dict(by_actor),
            "by_framework": dict(by_framework),
            "by_retention_class": dict(by_retention),
            "integrity_verified": integrity_ok,
            "integrity_errors": integrity_errors,
        }
