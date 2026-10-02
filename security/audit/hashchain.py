"""Tamper-evident hash chain for audit events.

Provides a cryptographically linked chain of audit events where each
event's hash includes the previous event's hash, making tampering
detectable.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from audit.events import AuditEvent


class HashChainError(Exception):
    """Base exception for hash chain errors."""


class ChainIntegrityError(HashChainError):
    """Raised when chain integrity is violated."""


class ChainVerificationError(HashChainError):
    """Raised when chain verification fails."""


@dataclass(frozen=True)
class ChainEntry:
    """A single entry in the hash chain."""

    event: AuditEvent
    sequence_number: int
    timestamp: float
    entry_hash: str
    previous_entry_hash: Optional[str]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "event": self.event.to_dict(),
            "sequence_number": self.sequence_number,
            "timestamp": self.timestamp,
            "entry_hash": self.entry_hash,
            "previous_entry_hash": self.previous_entry_hash,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ChainEntry":
        """Create from dictionary."""
        return cls(
            event=AuditEvent.from_dict(data["event"]),
            sequence_number=data["sequence_number"],
            timestamp=data["timestamp"],
            entry_hash=data["entry_hash"],
            previous_entry_hash=data.get("previous_entry_hash"),
        )


class HashChain:
    """Tamper-evident hash chain for audit events."""

    def __init__(self, chain_id: Optional[str] = None) -> None:
        self.chain_id = chain_id or self._generate_chain_id()
        self._entries: List[ChainEntry] = []
        self._last_hash: Optional[str] = None
        self._sequence: int = 0

    @staticmethod
    def _generate_chain_id() -> str:
        """Generate a unique chain ID."""
        return hashlib.sha256(
            f"{time.time()}-{id(object())}".encode()
        ).hexdigest()[:16]

    def _compute_entry_hash(
        self,
        event: AuditEvent,
        sequence_number: int,
        timestamp: float,
        previous_hash: Optional[str],
    ) -> str:
        """Compute the hash for a chain entry."""
        data = {
            "chain_id": self.chain_id,
            "event_hash": event.event_hash,
            "sequence_number": sequence_number,
            "timestamp": timestamp,
            "previous_hash": previous_hash,
        }
        canonical = json.dumps(data, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def append(self, event: AuditEvent) -> ChainEntry:
        """Append an event to the chain."""
        self._sequence += 1
        timestamp = time.time()

        entry_hash = self._compute_entry_hash(
            event=event,
            sequence_number=self._sequence,
            timestamp=timestamp,
            previous_hash=self._last_hash,
        )

        entry = ChainEntry(
            event=event,
            sequence_number=self._sequence,
            timestamp=timestamp,
            entry_hash=entry_hash,
            previous_entry_hash=self._last_hash,
        )

        self._entries.append(entry)
        self._last_hash = entry_hash
        return entry

    def verify(self) -> Tuple[bool, Optional[str]]:
        """Verify the integrity of the entire chain.

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not self._entries:
            return True, None

        previous_hash: Optional[str] = None

        for i, entry in enumerate(self._entries):
            # Check sequence number
            if entry.sequence_number != i + 1:
                return False, f"Sequence mismatch at entry {i}: expected {i+1}, got {entry.sequence_number}"

            # Check previous hash linkage
            if entry.previous_entry_hash != previous_hash:
                return False, f"Hash linkage broken at entry {i}"

            # Recompute and verify entry hash
            computed_hash = self._compute_entry_hash(
                event=entry.event,
                sequence_number=entry.sequence_number,
                timestamp=entry.timestamp,
                previous_hash=entry.previous_entry_hash,
            )
            if computed_hash != entry.entry_hash:
                return False, f"Entry hash mismatch at entry {i}"

            # Verify event integrity
            if not entry.event.verify_integrity():
                return False, f"Event integrity check failed at entry {i}"

            previous_hash = entry.entry_hash

        return True, None

    def verify_up_to(self, sequence_number: int) -> Tuple[bool, Optional[str]]:
        """Verify chain integrity up to a specific sequence number."""
        if sequence_number > len(self._entries):
            return False, f"Sequence number {sequence_number} exceeds chain length {len(self._entries)}"

        previous_hash: Optional[str] = None

        for i in range(sequence_number):
            entry = self._entries[i]

            if entry.sequence_number != i + 1:
                return False, f"Sequence mismatch at entry {i}"

            if entry.previous_entry_hash != previous_hash:
                return False, f"Hash linkage broken at entry {i}"

            computed_hash = self._compute_entry_hash(
                event=entry.event,
                sequence_number=entry.sequence_number,
                timestamp=entry.timestamp,
                previous_hash=entry.previous_entry_hash,
            )
            if computed_hash != entry.entry_hash:
                return False, f"Entry hash mismatch at entry {i}"

            if not entry.event.verify_integrity():
                return False, f"Event integrity check failed at entry {i}"

            previous_hash = entry.entry_hash

        return True, None

    def get_entries(
        self,
        start: int = 0,
        end: Optional[int] = None,
    ) -> List[ChainEntry]:
        """Get entries from the chain."""
        return self._entries[start:end]

    def get_entry(self, sequence_number: int) -> Optional[ChainEntry]:
        """Get a specific entry by sequence number."""
        if sequence_number < 1 or sequence_number > len(self._entries):
            return None
        return self._entries[sequence_number - 1]

    def get_last_hash(self) -> Optional[str]:
        """Get the last entry hash."""
        return self._last_hash

    def get_chain_id(self) -> str:
        """Get the chain ID."""
        return self.chain_id

    def __len__(self) -> int:
        return len(self._entries)

    def to_list(self) -> List[Dict[str, Any]]:
        """Export chain as list of dictionaries."""
        return [entry.to_dict() for entry in self._entries]

    def get_merkle_root(self) -> Optional[str]:
        """Compute Merkle root of the chain for efficient verification."""
        if not self._entries:
            return None

        hashes = [entry.entry_hash for entry in self._entries]

        while len(hashes) > 1:
            new_hashes = []
            for i in range(0, len(hashes), 2):
                left = hashes[i]
                right = hashes[i + 1] if i + 1 < len(hashes) else left
                combined = hashlib.sha256(
                    (left + right).encode("utf-8")
                ).hexdigest()
                new_hashes.append(combined)
            hashes = new_hashes

        return hashes[0]


class HashChainManager:
    """Manager for multiple hash chains."""

    def __init__(self) -> None:
        self._chains: Dict[str, HashChain] = {}

    def create_chain(self, chain_id: Optional[str] = None) -> HashChain:
        """Create a new hash chain."""
        chain = HashChain(chain_id=chain_id)
        self._chains[chain.chain_id] = chain
        return chain

    def get_chain(self, chain_id: str) -> Optional[HashChain]:
        """Get a chain by ID."""
        return self._chains.get(chain_id)

    def append_to_chain(self, chain_id: str, event: AuditEvent) -> ChainEntry:
        """Append an event to a specific chain."""
        chain = self._chains.get(chain_id)
        if not chain:
            raise HashChainError(f"Chain '{chain_id}' not found")
        return chain.append(event)

    def verify_chain(self, chain_id: str) -> Tuple[bool, Optional[str]]:
        """Verify a specific chain."""
        chain = self._chains.get(chain_id)
        if not chain:
            return False, f"Chain '{chain_id}' not found"
        return chain.verify()

    def verify_all_chains(self) -> Dict[str, Tuple[bool, Optional[str]]]:
        """Verify all chains."""
        results = {}
        for chain_id, chain in self._chains.items():
            results[chain_id] = chain.verify()
        return results
