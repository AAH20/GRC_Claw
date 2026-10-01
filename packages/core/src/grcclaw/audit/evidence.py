"""
Evidence management — collect, store, review, and manage audit evidence
with full chain of custody tracking.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, BinaryIO, Optional, Union

from .models import (
    Actor,
    ChainOfCustodyStatus,
    Evidence,
    EvidenceStatus,
    EvidenceType,
)


class EvidenceManager:
    """
    Manages audit evidence with chain of custody tracking.

    Features:
    - Evidence collection with metadata
    - File storage with SHA-256 hashing
    - Chain of custody tracking (collection → review → acceptance)
    - Evidence lifecycle management (pending → collected → reviewed → accepted)
    - Retention period and expiry management
    - Linkage to controls, findings, and audits
    - SQLite persistence
    """

    def __init__(
        self,
        storage_path: Optional[str] = None,
        file_storage_path: Optional[str] = None,
    ):
        self._lock = threading.RLock()
        self._evidence: dict[str, Evidence] = {}
        self._index_by_type: dict[str, list[str]] = defaultdict(list)
        self._index_by_status: dict[str, list[str]] = defaultdict(list)
        self._index_by_control: dict[str, list[str]] = defaultdict(list)
        self._index_by_finding: dict[str, list[str]] = defaultdict(list)
        self._index_by_audit: dict[str, list[str]] = defaultdict(list)

        if storage_path:
            self._storage_path = Path(storage_path)
            self._storage_path.parent.mkdir(parents=True, exist_ok=True)
            self._init_storage()
        else:
            self._storage_path = None
            self._conn: Optional[sqlite3.Connection] = None

        # File storage for evidence binaries
        if file_storage_path:
            self._file_storage = Path(file_storage_path)
            self._file_storage.mkdir(parents=True, exist_ok=True)
        else:
            self._file_storage = None

    # ------------------------------------------------------------------
    # Storage
    # ------------------------------------------------------------------

    def _init_storage(self) -> None:
        """Initialize SQLite storage."""
        self._conn = sqlite3.connect(str(self._storage_path), check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS evidence (
                evidence_id TEXT PRIMARY KEY,
                evidence_type TEXT NOT NULL,
                status TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                source TEXT,
                collector TEXT,
                collection_date TEXT,
                storage_location TEXT,
                file_hash TEXT,
                file_size_bytes INTEGER,
                mime_type TEXT,
                retention_period_days INTEGER,
                expiry_date TEXT,
                control_ids TEXT,
                finding_ids TEXT,
                audit_ids TEXT,
                chain_of_custody TEXT,
                tags TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                metadata TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_evidence_type ON evidence(evidence_type);
            CREATE INDEX IF NOT EXISTS idx_evidence_status ON evidence(status);
            CREATE INDEX IF NOT EXISTS idx_evidence_expiry ON evidence(expiry_date);
        """)
        self._conn.commit()
        self._load_from_storage()

    def _load_from_storage(self) -> None:
        """Load evidence from SQLite storage."""
        if not self._conn:
            return
        cursor = self._conn.execute("SELECT * FROM evidence")
        columns = [desc[0] for desc in cursor.description]
        for row in cursor.fetchall():
            d = dict(zip(columns, row))
            ev = Evidence(
                evidence_id=d["evidence_id"],
                evidence_type=EvidenceType(d["evidence_type"]),
                status=EvidenceStatus(d["status"]),
                title=d["title"],
                description=d["description"],
                source=d["source"],
                collector=d["collector"],
                collection_date=d["collection_date"],
                storage_location=d["storage_location"],
                file_hash=d["file_hash"],
                file_size_bytes=d["file_size_bytes"],
                mime_type=d["mime_type"],
                retention_period_days=d["retention_period_days"],
                expiry_date=d["expiry_date"],
                control_ids=json.loads(d["control_ids"]) if d["control_ids"] else [],
                finding_ids=json.loads(d["finding_ids"]) if d["finding_ids"] else [],
                audit_ids=json.loads(d["audit_ids"]) if d["audit_ids"] else [],
                chain_of_custody=json.loads(d["chain_of_custody"]) if d["chain_of_custody"] else [],
                tags=json.loads(d["tags"]) if d["tags"] else [],
                created_at=d["created_at"],
                updated_at=d["updated_at"],
                metadata=json.loads(d["metadata"]) if d["metadata"] else {},
            )
            self._evidence[ev.evidence_id] = ev
            self._index_evidence(ev)

    def _index_evidence(self, ev: Evidence) -> None:
        """Add evidence to indexes."""
        self._index_by_type[ev.evidence_type.value].append(ev.evidence_id)
        self._index_by_status[ev.status.value].append(ev.evidence_id)
        for cid in ev.control_ids:
            self._index_by_control[cid].append(ev.evidence_id)
        for fid in ev.finding_ids:
            self._index_by_finding[fid].append(ev.evidence_id)
        for aid in ev.audit_ids:
            self._index_by_audit[aid].append(ev.evidence_id)

    def _persist_evidence(self, ev: Evidence) -> None:
        """Persist evidence to storage."""
        if not self._conn:
            return
        self._conn.execute(
            """INSERT OR REPLACE INTO evidence VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                ev.evidence_id,
                ev.evidence_type.value,
                ev.status.value,
                ev.title,
                ev.description,
                ev.source,
                ev.collector,
                ev.collection_date,
                ev.storage_location,
                ev.file_hash,
                ev.file_size_bytes,
                ev.mime_type,
                ev.retention_period_days,
                ev.expiry_date,
                json.dumps(ev.control_ids),
                json.dumps(ev.finding_ids),
                json.dumps(ev.audit_ids),
                json.dumps(ev.chain_of_custody),
                json.dumps(ev.tags),
                ev.created_at,
                ev.updated_at,
                json.dumps(ev.metadata),
            ),
        )
        self._conn.commit()

    # ------------------------------------------------------------------
    # Evidence creation
    # ------------------------------------------------------------------

    def register_evidence(
        self,
        title: str,
        evidence_type: EvidenceType,
        description: Optional[str] = None,
        source: Optional[str] = None,
        collector: Optional[str] = None,
        retention_period_days: Optional[int] = None,
        tags: Optional[list[str]] = None,
        control_ids: Optional[list[str]] = None,
        finding_ids: Optional[list[str]] = None,
        audit_ids: Optional[list[str]] = None,
    ) -> Evidence:
        """Register a new evidence item (without file upload)."""
        with self._lock:
            now = datetime.now(timezone.utc)
            ev = Evidence(
                title=title,
                evidence_type=evidence_type,
                status=EvidenceStatus.PENDING,
                description=description,
                source=source,
                collector=collector,
                collection_date=now.isoformat(),
                retention_period_days=retention_period_days,
                control_ids=control_ids or [],
                finding_ids=finding_ids or [],
                audit_ids=audit_ids or [],
                tags=tags or [],
                chain_of_custody=[{
                    "action": "registered",
                    "actor": collector or "system",
                    "timestamp": now.isoformat(),
                    "status": ChainOfCustodyStatus.INTACT.value,
                }],
            )
            if retention_period_days:
                from datetime import timedelta
                ev.expiry_date = (now + timedelta(days=retention_period_days)).isoformat()

            self._evidence[ev.evidence_id] = ev
            self._index_evidence(ev)
            self._persist_evidence(ev)
            return ev

    def collect_evidence(
        self,
        title: str,
        evidence_type: EvidenceType,
        file_data: Union[bytes, BinaryIO, str, Path],
        description: Optional[str] = None,
        source: Optional[str] = None,
        collector: Optional[str] = None,
        mime_type: Optional[str] = None,
        retention_period_days: Optional[int] = None,
        tags: Optional[list[str]] = None,
        control_ids: Optional[list[str]] = None,
        finding_ids: Optional[list[str]] = None,
        audit_ids: Optional[list[str]] = None,
    ) -> Evidence:
        """
        Collect evidence with file data.

        Stores the file in the file storage path, computes SHA-256 hash,
        and creates the evidence record with chain of custody.
        """
        with self._lock:
            now = datetime.now(timezone.utc)

            # Read file data
            if isinstance(file_data, (str, Path)):
                file_path = Path(file_data)
                file_bytes = file_path.read_bytes()
                if not mime_type:
                    mime_type = self._guess_mime_type(file_path.suffix)
            elif hasattr(file_data, "read"):
                file_bytes = file_data.read()
                if isinstance(file_bytes, str):
                    file_bytes = file_bytes.encode()
            else:
                file_bytes = file_data

            # Compute hash
            file_hash = hashlib.sha256(file_bytes).hexdigest()
            file_size = len(file_bytes)

            # Store file
            storage_location = None
            if self._file_storage:
                # Organize by date
                date_dir = self._file_storage / now.strftime("%Y/%m/%d")
                date_dir.mkdir(parents=True, exist_ok=True)
                ext = ""
                if mime_type:
                    ext = self._mime_to_ext(mime_type)
                filename = f"{ev_id_prefix()}{ext}" if False else f"{file_hash[:16]}{ext}"
                file_path = date_dir / filename
                file_path.write_bytes(file_bytes)
                storage_location = str(file_path)

            ev = Evidence(
                title=title,
                evidence_type=evidence_type,
                status=EvidenceStatus.COLLECTED,
                description=description,
                source=source,
                collector=collector,
                collection_date=now.isoformat(),
                storage_location=storage_location,
                file_hash=file_hash,
                file_size_bytes=file_size,
                mime_type=mime_type,
                retention_period_days=retention_period_days,
                control_ids=control_ids or [],
                finding_ids=finding_ids or [],
                audit_ids=audit_ids or [],
                tags=tags or [],
                chain_of_custody=[{
                    "action": "collected",
                    "actor": collector or "system",
                    "timestamp": now.isoformat(),
                    "status": ChainOfCustodyStatus.INTACT.value,
                    "file_hash": file_hash,
                }],
            )
            if retention_period_days:
                from datetime import timedelta
                ev.expiry_date = (now + timedelta(days=retention_period_days)).isoformat()

            self._evidence[ev.evidence_id] = ev
            self._index_evidence(ev)
            self._persist_evidence(ev)
            return ev

    # ------------------------------------------------------------------
    # Evidence retrieval
    # ------------------------------------------------------------------

    def get_evidence(self, evidence_id: str) -> Optional[Evidence]:
        """Get evidence by ID."""
        return self._evidence.get(evidence_id)

    def list_evidence(
        self,
        evidence_type: Optional[EvidenceType] = None,
        status: Optional[EvidenceStatus] = None,
        control_id: Optional[str] = None,
        finding_id: Optional[str] = None,
        audit_id: Optional[str] = None,
        tags: Optional[list[str]] = None,
    ) -> list[Evidence]:
        """List evidence with optional filters."""
        # Use indexes for the most selective filter
        candidate_ids: Optional[set[str]] = None

        if control_id and control_id in self._index_by_control:
            candidate_ids = set(self._index_by_control[control_id])
        elif finding_id and finding_id in self._index_by_finding:
            candidate_ids = set(self._index_by_finding[finding_id])
        elif audit_id and audit_id in self._index_by_audit:
            candidate_ids = set(self._index_by_audit[audit_id])
        elif status and status.value in self._index_by_status:
            candidate_ids = set(self._index_by_status[status.value])
        elif evidence_type and evidence_type.value in self._index_by_type:
            candidate_ids = set(self._index_by_type[evidence_type.value])

        if candidate_ids is not None:
            evidence_list = [self._evidence[eid] for eid in candidate_ids if eid in self._evidence]
        else:
            evidence_list = list(self._evidence.values())

        # Apply remaining filters
        if control_id and not (candidate_ids and control_id in self._index_by_control):
            evidence_list = [e for e in evidence_list if control_id in e.control_ids]
        if finding_id and not (candidate_ids and finding_id in self._index_by_finding):
            evidence_list = [e for e in evidence_list if finding_id in e.finding_ids]
        if audit_id and not (candidate_ids and audit_id in self._index_by_audit):
            evidence_list = [e for e in evidence_list if audit_id in e.audit_ids]
        if status and not (candidate_ids and status.value in self._index_by_status):
            evidence_list = [e for e in evidence_list if e.status == status]
        if evidence_type and not (candidate_ids and evidence_type.value in self._index_by_type):
            evidence_list = [e for e in evidence_list if e.evidence_type == evidence_type]
        if tags:
            evidence_list = [
                e for e in evidence_list
                if any(tag in e.tags for tag in tags)
            ]

        return evidence_list

    def get_evidence_file(self, evidence_id: str) -> Optional[bytes]:
        """Retrieve the file content of an evidence item."""
        ev = self._evidence.get(evidence_id)
        if not ev or not ev.storage_location:
            return None
        try:
            return Path(ev.storage_location).read_bytes()
        except (FileNotFoundError, OSError):
            return None

    def verify_evidence_integrity(self, evidence_id: str) -> dict[str, Any]:
        """Verify the integrity of an evidence file by checking its hash."""
        ev = self._evidence.get(evidence_id)
        if not ev:
            return {"valid": False, "reason": "evidence_not_found"}
        if not ev.storage_location:
            return {"valid": False, "reason": "no_file"}
        if not ev.file_hash:
            return {"valid": False, "reason": "no_hash"}

        try:
            file_bytes = Path(ev.storage_location).read_bytes()
            actual_hash = hashlib.sha256(file_bytes).hexdigest()
            return {
                "valid": actual_hash == ev.file_hash,
                "expected_hash": ev.file_hash,
                "actual_hash": actual_hash,
                "evidence_id": evidence_id,
            }
        except (FileNotFoundError, OSError) as e:
            return {"valid": False, "reason": str(e), "evidence_id": evidence_id}

    # ------------------------------------------------------------------
    # Evidence lifecycle
    # ------------------------------------------------------------------

    def update_evidence_status(
        self,
        evidence_id: str,
        new_status: EvidenceStatus,
        actor: str,
        notes: Optional[str] = None,
    ) -> Optional[Evidence]:
        """Update evidence status with chain of custody entry."""
        with self._lock:
            ev = self._evidence.get(evidence_id)
            if not ev:
                return None

            old_status = ev.status
            ev.status = new_status
            ev.updated_at = datetime.now(timezone.utc).isoformat()

            # Add chain of custody entry
            ev.chain_of_custody.append({
                "action": "status_change",
                "from_status": old_status.value,
                "to_status": new_status.value,
                "actor": actor,
                "timestamp": ev.updated_at,
                "status": ChainOfCustodyStatus.INTACT.value,
                "notes": notes,
            })

            self._persist_evidence(ev)
            return ev

    def review_evidence(
        self,
        evidence_id: str,
        reviewer: str,
        accepted: bool,
        notes: Optional[str] = None,
    ) -> Optional[Evidence]:
        """Review evidence and accept or reject it."""
        new_status = EvidenceStatus.ACCEPTED if accepted else EvidenceStatus.REJECTED
        return self.update_evidence_status(evidence_id, new_status, reviewer, notes)

    def transfer_custody(
        self,
        evidence_id: str,
        from_actor: str,
        to_actor: str,
        reason: Optional[str] = None,
    ) -> Optional[Evidence]:
        """Transfer evidence custody."""
        with self._lock:
            ev = self._evidence.get(evidence_id)
            if not ev:
                return None

            ev.updated_at = datetime.now(timezone.utc).isoformat()
            ev.chain_of_custody.append({
                "action": "custody_transfer",
                "from": from_actor,
                "to": to_actor,
                "timestamp": ev.updated_at,
                "status": ChainOfCustodyStatus.TRANSFERRED.value,
                "reason": reason,
            })

            self._persist_evidence(ev)
            return ev

    def access_evidence(
        self,
        evidence_id: str,
        accessor: str,
        purpose: Optional[str] = None,
    ) -> Optional[Evidence]:
        """Record an evidence access event."""
        with self._lock:
            ev = self._evidence.get(evidence_id)
            if not ev:
                return None

            ev.chain_of_custody.append({
                "action": "accessed",
                "actor": accessor,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "status": ChainOfCustodyStatus.ACCESSED.value,
                "purpose": purpose,
            })

            self._persist_evidence(ev)
            return ev

    def dispose_evidence(
        self,
        evidence_id: str,
        disposer: str,
        reason: Optional[str] = None,
    ) -> Optional[Evidence]:
        """Dispose of evidence (retain record, remove file)."""
        with self._lock:
            ev = self._evidence.get(evidence_id)
            if not ev:
                return None

            # Remove file if exists
            if ev.storage_location:
                try:
                    Path(ev.storage_location).unlink(missing_ok=True)
                except OSError:
                    pass
                ev.storage_location = None

            ev.status = EvidenceStatus.EXPIRED
            ev.updated_at = datetime.now(timezone.utc).isoformat()
            ev.chain_of_custody.append({
                "action": "disposed",
                "actor": disposer,
                "timestamp": ev.updated_at,
                "status": ChainOfCustodyStatus.DISPOSED.value,
                "reason": reason,
            })

            self._persist_evidence(ev)
            return ev

    # ------------------------------------------------------------------
    # Linkage
    # ------------------------------------------------------------------

    def link_to_control(self, evidence_id: str, control_id: str) -> bool:
        """Link evidence to a control."""
        with self._lock:
            ev = self._evidence.get(evidence_id)
            if not ev:
                return False
            if control_id not in ev.control_ids:
                ev.control_ids.append(control_id)
                ev.updated_at = datetime.now(timezone.utc).isoformat()
                self._persist_evidence(ev)
            return True

    def link_to_finding(self, evidence_id: str, finding_id: str) -> bool:
        """Link evidence to a finding."""
        with self._lock:
            ev = self._evidence.get(evidence_id)
            if not ev:
                return False
            if finding_id not in ev.finding_ids:
                ev.finding_ids.append(finding_id)
                ev.updated_at = datetime.now(timezone.utc).isoformat()
                self._persist_evidence(ev)
            return True

    def link_to_audit(self, evidence_id: str, audit_id: str) -> bool:
        """Link evidence to an audit."""
        with self._lock:
            ev = self._evidence.get(evidence_id)
            if not ev:
                return False
            if audit_id not in ev.audit_ids:
                ev.audit_ids.append(audit_id)
                ev.updated_at = datetime.now(timezone.utc).isoformat()
                self._persist_evidence(ev)
            return True

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_expired_evidence(self) -> list[Evidence]:
        """Get all expired evidence."""
        now = datetime.now(timezone.utc)
        expired = []
        for ev in self._evidence.values():
            if ev.expiry_date:
                try:
                    expiry = datetime.fromisoformat(ev.expiry_date)
                    if expiry < now:
                        expired.append(ev)
                except (ValueError, TypeError):
                    pass
        return expired

    def get_pending_review(self) -> list[Evidence]:
        """Get all evidence pending review."""
        return self.list_evidence(status=EvidenceStatus.UNDER_REVIEW)

    def get_chain_of_custody(self, evidence_id: str) -> list[dict[str, Any]]:
        """Get the full chain of custody for an evidence item."""
        ev = self._evidence.get(evidence_id)
        if not ev:
            return []
        return ev.chain_of_custody

    def get_evidence_summary(self) -> dict[str, Any]:
        """Get a summary of all evidence."""
        by_type: dict[str, int] = defaultdict(int)
        by_status: dict[str, int] = defaultdict(int)
        total_size = 0
        for ev in self._evidence.values():
            by_type[ev.evidence_type.value] += 1
            by_status[ev.status.value] += 1
            if ev.file_size_bytes:
                total_size += ev.file_size_bytes

        return {
            "total_evidence": len(self._evidence),
            "by_type": dict(by_type),
            "by_status": dict(by_status),
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "expired_count": len(self.get_expired_evidence()),
            "pending_review_count": len(self.get_pending_review()),
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _guess_mime_type(self, extension: str) -> str:
        """Guess MIME type from file extension."""
        mime_types = {
            ".pdf": "application/pdf",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".txt": "text/plain",
            ".csv": "text/csv",
            ".json": "application/json",
            ".xml": "application/xml",
            ".zip": "application/zip",
            ".doc": "application/msword",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".xls": "application/vnd.ms-excel",
            ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".log": "text/plain",
            ".conf": "text/plain",
            ".cfg": "text/plain",
        }
        return mime_types.get(extension.lower(), "application/octet-stream")

    def _mime_to_ext(self, mime_type: str) -> str:
        """Convert MIME type to file extension."""
        ext_map = {
            "application/pdf": ".pdf",
            "image/png": ".png",
            "image/jpeg": ".jpg",
            "image/gif": ".gif",
            "text/plain": ".txt",
            "text/csv": ".csv",
            "application/json": ".json",
            "application/xml": ".xml",
            "application/zip": ".zip",
        }
        return ext_map.get(mime_type, "")

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def close(self) -> None:
        """Close storage connections."""
        if self._conn:
            self._conn.close()
            self._conn = None

    def __enter__(self) -> EvidenceManager:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()


def ev_id_prefix() -> str:
    """Generate a short prefix for evidence file names."""
    import uuid
    return str(uuid.uuid4())[:8]
