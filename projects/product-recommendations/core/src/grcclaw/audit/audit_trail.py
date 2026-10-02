"""
Audit trail engine — immutable, hash-chained event logging for GRC_Claw.

Every action in the system generates an AuditEvent that is cryptographically
chained to the previous event, creating a tamper-evident log suitable for
regulatory and forensic review.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import threading
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional

from .models import (
    Actor,
    AuditEvent,
    AuditEventSeverity,
    AuditEventType,
    Resource,
)


class AuditTrailEngine:
    """
    Core audit trail engine.

    Features:
    - Immutable event logging with SHA-256 hash chaining
    - Tamper detection via integrity verification
    - Event filtering and querying
    - Correlation ID tracking across distributed operations
    - Pluggable storage backends (SQLite, in-memory)
    - Event hooks for real-time monitoring
    """

    def __init__(
        self,
        storage_path: Optional[str] = None,
        tenant_id: Optional[str] = None,
    ):
        self._lock = threading.RLock()
        self._events: list[AuditEvent] = []
        self._index_by_type: dict[str, list[int]] = defaultdict(list)
        self._index_by_actor: dict[str, list[int]] = defaultdict(list)
        self._index_by_resource: dict[str, list[int]] = defaultdict(list)
        self._index_by_correlation: dict[str, list[int]] = defaultdict(list)
        self._last_hash: Optional[str] = None
        self._tenant_id = tenant_id
        self._hooks: list[Callable[[AuditEvent], None]] = []

        if storage_path:
            self._storage_path = Path(storage_path)
            self._storage_path.parent.mkdir(parents=True, exist_ok=True)
            self._init_sqlite_storage()
        else:
            self._storage_path = None
            self._conn: Optional[sqlite3.Connection] = None

    # ------------------------------------------------------------------
    # Storage
    # ------------------------------------------------------------------

    def _init_sqlite_storage(self) -> None:
        """Initialize SQLite storage with WAL mode for concurrent access."""
        self._conn = sqlite3.connect(str(self._storage_path), check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=NORMAL")
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS audit_events (
                seq INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT UNIQUE NOT NULL,
                event_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                actor_type TEXT NOT NULL,
                actor_id TEXT NOT NULL,
                actor_name TEXT,
                resource_type TEXT NOT NULL,
                resource_id TEXT NOT NULL,
                resource_name TEXT,
                timestamp TEXT NOT NULL,
                details TEXT,
                integrity_hash TEXT NOT NULL,
                previous_event_hash TEXT,
                correlation_id TEXT,
                session_id TEXT,
                tenant_id TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_audit_event_type ON audit_events(event_type);
            CREATE INDEX IF NOT EXISTS idx_audit_actor_id ON audit_events(actor_id);
            CREATE INDEX IF NOT EXISTS idx_audit_resource_id ON audit_events(resource_id);
            CREATE INDEX IF NOT EXISTS idx_audit_correlation ON audit_events(correlation_id);
            CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_events(timestamp);
            CREATE INDEX IF NOT EXISTS idx_audit_tenant ON audit_events(tenant_id);
        """)
        self._conn.commit()

        # Rebuild in-memory index and chain from persisted events
        self._rebuild_chain_from_storage()

    def _rebuild_chain_from_storage(self) -> None:
        """Rebuild the hash chain and indexes from persisted storage."""
        if not self._conn:
            return
        cursor = self._conn.execute(
            "SELECT * FROM audit_events ORDER BY seq"
        )
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        for row in rows:
            row_dict = dict(zip(columns, row))
            event = AuditEvent(
                event_id=row_dict["event_id"],
                event_type=AuditEventType(row_dict["event_type"]),
                severity=AuditEventSeverity(row_dict["severity"]),
                actor=Actor(
                    type=row_dict["actor_type"],
                    id=row_dict["actor_id"],
                    name=row_dict["actor_name"],
                ),
                resource=Resource(
                    type=row_dict["resource_type"],
                    id=row_dict["resource_id"],
                    name=row_dict["resource_name"],
                ),
                timestamp=row_dict["timestamp"],
                details=json.loads(row_dict["details"]) if row_dict["details"] else {},
                integrity_hash=row_dict["integrity_hash"],
                previous_event_hash=row_dict["previous_event_hash"],
                correlation_id=row_dict["correlation_id"],
                session_id=row_dict["session_id"],
                tenant_id=row_dict["tenant_id"],
            )
            self._events.append(event)
            self._index_event(len(self._events) - 1, event)
            self._last_hash = event.integrity_hash

    def _index_event(self, position: int, event: AuditEvent) -> None:
        """Add event to all indexes."""
        self._index_by_type[event.event_type.value].append(position)
        self._index_by_actor[event.actor.id].append(position)
        self._index_by_resource[event.resource.id].append(position)
        if event.correlation_id:
            self._index_by_correlation[event.correlation_id].append(position)

    def _persist_event(self, event: AuditEvent) -> None:
        """Persist event to SQLite storage."""
        if not self._conn:
            return
        self._conn.execute(
            """INSERT INTO audit_events
            (event_id, event_type, severity, actor_type, actor_id, actor_name,
             resource_type, resource_id, resource_name, timestamp, details,
             integrity_hash, previous_event_hash, correlation_id, session_id, tenant_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                event.event_id,
                event.event_type.value,
                event.severity.value,
                event.actor.type,
                event.actor.id,
                event.actor.name,
                event.resource.type,
                event.resource.id,
                event.resource.name,
                event.timestamp,
                json.dumps(event.details) if event.details else None,
                event.integrity_hash,
                event.previous_event_hash,
                event.correlation_id,
                event.session_id,
                event.tenant_id,
            ),
        )
        self._conn.commit()

    # ------------------------------------------------------------------
    # Event logging
    # ------------------------------------------------------------------

    def log_event(
        self,
        event_type: AuditEventType,
        actor: Actor,
        resource: Resource,
        severity: AuditEventSeverity = AuditEventSeverity.INFO,
        details: Optional[dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> AuditEvent:
        """
        Log a new audit event.

        The event is automatically chained to the previous event's hash,
        creating a tamper-evident sequence.
        """
        with self._lock:
            event = AuditEvent(
                event_type=event_type,
                severity=severity,
                actor=actor,
                resource=resource,
                details=details or {},
                previous_event_hash=self._last_hash,
                correlation_id=correlation_id,
                session_id=session_id,
                tenant_id=self._tenant_id,
            )
            # Compute hash with chain reference
            event.integrity_hash = self._compute_chained_hash(event)

            self._events.append(event)
            self._index_event(len(self._events) - 1, event)
            self._last_hash = event.integrity_hash

            self._persist_event(event)
            self._notify_hooks(event)

            return event

    def _compute_chained_hash(self, event: AuditEvent) -> str:
        """Compute hash including the previous event's hash for chain integrity."""
        data = (
            f"{event.event_id}|{event.event_type.value}|{event.actor.id}|"
            f"{event.resource.id}|{event.timestamp}|{json.dumps(event.details, sort_keys=True)}|"
            f"{event.previous_event_hash or 'GENESIS'}"
        )
        return hashlib.sha256(data.encode()).hexdigest()

    # ------------------------------------------------------------------
    # Convenience methods
    # ------------------------------------------------------------------

    def log_control_evaluated(
        self,
        actor: Actor,
        control_id: str,
        control_name: str,
        result: str,
        details: Optional[dict[str, Any]] = None,
    ) -> AuditEvent:
        """Log a control evaluation event."""
        merged = details or {}
        merged["result"] = result
        return self.log_event(
            AuditEventType.CONTROL_EVALUATED,
            actor,
            Resource(type="control", id=control_id, name=control_name),
            AuditEventSeverity.INFO,
            merged,
        )

    def log_evidence_collected(
        self,
        actor: Actor,
        evidence_id: str,
        evidence_title: str,
        evidence_type: str,
        details: Optional[dict[str, Any]] = None,
    ) -> AuditEvent:
        """Log an evidence collection event."""
        merged = details or {}
        merged["evidence_type"] = evidence_type
        return self.log_event(
            AuditEventType.EVIDENCE_COLLECTED,
            actor,
            Resource(type="evidence", id=evidence_id, name=evidence_title),
            AuditEventSeverity.INFO,
            merged,
        )

    def log_finding_raised(
        self,
        actor: Actor,
        finding_id: str,
        finding_title: str,
        severity: str,
        details: Optional[dict[str, Any]] = None,
    ) -> AuditEvent:
        """Log a finding being raised."""
        merged = details or {}
        merged["severity"] = severity
        sev = AuditEventSeverity.WARNING if severity in ("critical", "high") else AuditEventSeverity.NOTICE
        return self.log_event(
            AuditEventType.FINDING_RAISED,
            actor,
            Resource(type="finding", id=finding_id, name=finding_title),
            sev,
            merged,
        )

    def log_finding_remediated(
        self,
        actor: Actor,
        finding_id: str,
        finding_title: str,
        details: Optional[dict[str, Any]] = None,
    ) -> AuditEvent:
        """Log a finding remediation."""
        return self.log_event(
            AuditEventType.FINDING_REMEDIATED,
            actor,
            Resource(type="finding", id=finding_id, name=finding_title),
            AuditEventSeverity.INFO,
            details,
        )

    def log_access_granted(
        self,
        actor: Actor,
        resource_type: str,
        resource_id: str,
        grantee: str,
        details: Optional[dict[str, Any]] = None,
    ) -> AuditEvent:
        """Log an access grant."""
        merged = details or {}
        merged["grantee"] = grantee
        return self.log_event(
            AuditEventType.ACCESS_GRANTED,
            actor,
            Resource(type=resource_type, id=resource_id),
            AuditEventSeverity.NOTICE,
            merged,
        )

    def log_data_exported(
        self,
        actor: Actor,
        resource_type: str,
        resource_id: str,
        destination: str,
        details: Optional[dict[str, Any]] = None,
    ) -> AuditEvent:
        """Log a data export event."""
        merged = details or {}
        merged["destination"] = destination
        return self.log_event(
            AuditEventType.DATA_EXPORTED,
            actor,
            Resource(type=resource_type, id=resource_id),
            AuditEventSeverity.NOTICE,
            merged,
        )

    def log_config_changed(
        self,
        actor: Actor,
        component: str,
        change_description: str,
        old_value: Any = None,
        new_value: Any = None,
    ) -> AuditEvent:
        """Log a configuration change."""
        return self.log_event(
            AuditEventType.CONFIG_CHANGED,
            actor,
            Resource(type="config", id=component),
            AuditEventSeverity.WARNING,
            {
                "change": change_description,
                "old_value": old_value,
                "new_value": new_value,
            },
        )

    # ------------------------------------------------------------------
    # Querying
    # ------------------------------------------------------------------

    def get_events(
        self,
        event_type: Optional[AuditEventType] = None,
        actor_id: Optional[str] = None,
        resource_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        severity: Optional[AuditEventSeverity] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditEvent]:
        """Query audit events with filters."""
        with self._lock:
            # Use indexes for the most selective filter
            candidate_positions: Optional[set[int]] = None

            if correlation_id and correlation_id in self._index_by_correlation:
                candidate_positions = set(self._index_by_correlation[correlation_id])
            elif event_type and event_type.value in self._index_by_type:
                candidate_positions = set(self._index_by_type[event_type.value])
            elif actor_id and actor_id in self._index_by_actor:
                candidate_positions = set(self._index_by_actor[actor_id])
            elif resource_id and resource_id in self._index_by_resource:
                candidate_positions = set(self._index_by_resource[resource_id])

            if candidate_positions is not None:
                events = [self._events[i] for i in sorted(candidate_positions)]
            else:
                events = list(self._events)

            # Apply remaining filters
            if correlation_id and not (candidate_positions and correlation_id in self._index_by_correlation):
                events = [e for e in events if e.correlation_id == correlation_id]
            if event_type and not (candidate_positions and event_type.value in self._index_by_type):
                events = [e for e in events if e.event_type == event_type]
            if actor_id and not (candidate_positions and actor_id in self._index_by_actor):
                events = [e for e in events if e.actor.id == actor_id]
            if resource_id and not (candidate_positions and resource_id in self._index_by_resource):
                events = [e for e in events if e.resource.id == resource_id]
            if severity:
                events = [e for e in events if e.severity == severity]

            return events[offset:offset + limit]

    def get_event_by_id(self, event_id: str) -> Optional[AuditEvent]:
        """Retrieve a specific event by its ID."""
        with self._lock:
            for event in self._events:
                if event.event_id == event_id:
                    return event
            return None

    def get_event_count(self) -> int:
        """Return total number of events in the trail."""
        with self._lock:
            return len(self._events)

    def get_events_by_correlation(self, correlation_id: str) -> list[AuditEvent]:
        """Get all events in a correlated operation chain."""
        return self.get_events(correlation_id=correlation_id, limit=10000)

    # ------------------------------------------------------------------
    # Integrity verification
    # ------------------------------------------------------------------

    def verify_chain_integrity(self) -> dict[str, Any]:
        """
        Verify the integrity of the entire audit chain.

        Returns a report with:
        - chain_intact: whether all hashes match
        - events_verified: number of events checked
        - first_event_id / last_event_id
        - any tampered events
        """
        with self._lock:
            tampered = []
            previous_hash = None

            for i, event in enumerate(self._events):
                # Verify chain link
                if event.previous_event_hash != previous_hash:
                    tampered.append({
                        "event_id": event.event_id,
                        "position": i,
                        "issue": "chain_break",
                        "expected_previous": previous_hash,
                        "actual_previous": event.previous_event_hash,
                    })

                # Verify event hash
                expected_hash = self._compute_chained_hash(event)
                if event.integrity_hash != expected_hash:
                    tampered.append({
                        "event_id": event.event_id,
                        "position": i,
                        "issue": "hash_mismatch",
                        "expected_hash": expected_hash,
                        "actual_hash": event.integrity_hash,
                    })

                previous_hash = event.integrity_hash

            return {
                "chain_intact": len(tampered) == 0,
                "events_verified": len(self._events),
                "first_event_id": self._events[0].event_id if self._events else None,
                "last_event_id": self._events[-1].event_id if self._events else None,
                "tampered_events": tampered,
                "verified_at": datetime.now(timezone.utc).isoformat(),
            }

    def verify_event(self, event_id: str) -> bool:
        """Verify a single event's integrity."""
        event = self.get_event_by_id(event_id)
        if not event:
            return False
        expected = self._compute_chained_hash(event)
        return event.integrity_hash == expected

    # ------------------------------------------------------------------
    # Hooks
    # ------------------------------------------------------------------

    def register_hook(self, callback: Callable[[AuditEvent], None]) -> None:
        """Register a callback to be invoked on each new event."""
        self._hooks.append(callback)

    def unregister_hook(self, callback: Callable[[AuditEvent], None]) -> None:
        """Remove a previously registered hook."""
        if callback in self._hooks:
            self._hooks.remove(callback)

    def _notify_hooks(self, event: AuditEvent) -> None:
        """Notify all registered hooks."""
        for hook in self._hooks:
            try:
                hook(event)
            except Exception:
                pass  # Hooks must never break the audit trail

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def export_events(
        self,
        format: str = "json",
        event_type: Optional[AuditEventType] = None,
        actor_id: Optional[str] = None,
        resource_id: Optional[str] = None,
    ) -> str:
        """Export events in JSON or CSV format."""
        events = self.get_events(
            event_type=event_type,
            actor_id=actor_id,
            resource_id=resource_id,
            limit=100000,
        )

        if format == "json":
            return json.dumps(
                [self._event_to_dict(e) for e in events],
                indent=2,
                default=str,
            )
        elif format == "csv":
            import csv
            import io
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow([
                "seq", "event_id", "event_type", "severity",
                "actor_type", "actor_id", "actor_name",
                "resource_type", "resource_id", "resource_name",
                "timestamp", "integrity_hash", "previous_event_hash",
                "correlation_id",
            ])
            for i, e in enumerate(events):
                writer.writerow([
                    i, e.event_id, e.event_type.value, e.severity.value,
                    e.actor.type, e.actor.id, e.actor.name or "",
                    e.resource.type, e.resource.id, e.resource.name or "",
                    e.timestamp, e.integrity_hash, e.previous_event_hash or "",
                    e.correlation_id or "",
                ])
            return output.getvalue()
        else:
            raise ValueError(f"Unsupported export format: {format}")

    def _event_to_dict(self, event: AuditEvent) -> dict[str, Any]:
        """Convert an event to a dictionary."""
        return {
            "event_id": event.event_id,
            "event_type": event.event_type.value,
            "severity": event.severity.value,
            "actor": {
                "type": event.actor.type,
                "id": event.actor.id,
                "name": event.actor.name,
                "email": event.actor.email,
                "ip_address": event.actor.ip_address,
            },
            "resource": {
                "type": event.resource.type,
                "id": event.resource.id,
                "name": event.resource.name,
            },
            "timestamp": event.timestamp,
            "details": event.details,
            "integrity_hash": event.integrity_hash,
            "previous_event_hash": event.previous_event_hash,
            "correlation_id": event.correlation_id,
            "session_id": event.session_id,
            "tenant_id": event.tenant_id,
        }

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def close(self) -> None:
        """Close storage connections."""
        if self._conn:
            self._conn.close()
            self._conn = None

    def __enter__(self) -> AuditTrailEngine:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()
