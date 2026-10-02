"""4-layer context management for GRC Marketing Core.

Implements a multi-layer memory system for agents:
1. Conversation Memory: Short-term dialogue context
2. Semantic Memory: Long-term knowledge and facts
3. Procedural Memory: Learned workflows and patterns
4. Episodic Memory: Historical interaction records
"""

from __future__ import annotations

import hashlib
import json
import time
import uuid
from abc import ABC, abstractmethod
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Generic, TypeVar

import structlog

logger = structlog.get_logger(__name__)

T = TypeVar("T")


class MemoryLayer(str, Enum):
    """The four memory layers."""

    CONVERSATION = "conversation"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"
    EPISODIC = "episodic"


@dataclass
class MemoryEntry:
    """A single memory entry."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    content: str = ""
    layer: MemoryLayer = MemoryLayer.CONVERSATION
    metadata: dict[str, Any] = field(default_factory=dict)
    embedding: list[float] | None = None
    importance: float = 0.5
    access_count: int = 0
    created_at: float = field(default_factory=time.time)
    last_accessed: float = field(default_factory=time.time)
    ttl_seconds: float | None = None

    @property
    def is_expired(self) -> bool:
        if self.ttl_seconds is None:
            return False
        return (time.time() - self.created_at) > self.ttl_seconds

    @property
    def age_seconds(self) -> float:
        return time.time() - self.created_at

    def touch(self) -> None:
        self.last_accessed = time.time()
        self.access_count += 1

    def compute_score(self) -> float:
        """Compute relevance score based on recency, frequency, and importance."""
        recency = 1.0 / (1.0 + self.age_seconds / 3600.0)
        frequency = min(self.access_count / 10.0, 1.0)
        return 0.4 * self.importance + 0.3 * recency + 0.3 * frequency


class BaseMemory(ABC, Generic[T]):
    """Abstract base class for memory layers."""

    def __init__(self, layer: MemoryLayer, max_entries: int = 1000) -> None:
        self.layer = layer
        self.max_entries = max_entries
        self._entries: OrderedDict[str, MemoryEntry] = OrderedDict()
        self._logger = logger.bind(memory_layer=layer.value)

    @abstractmethod
    async def store(self, content: T, **metadata: Any) -> MemoryEntry:
        """Store an entry in memory."""

    @abstractmethod
    async def retrieve(self, query: str, limit: int = 5) -> list[MemoryEntry]:
        """Retrieve relevant entries from memory."""

    async def forget(self, entry_id: str) -> bool:
        """Remove an entry from memory."""
        if entry_id in self._entries:
            del self._entries[entry_id]
            return True
        return False

    async def clear(self) -> None:
        """Clear all entries in this memory layer."""
        self._entries.clear()

    def _enforce_limit(self) -> None:
        """Evict oldest entries when over capacity."""
        while len(self._entries) > self.max_entries:
            self._entries.popitem(last=False)

    def _cleanup_expired(self) -> int:
        """Remove expired entries. Returns count removed."""
        expired = [k for k, v in self._entries.items() if v.is_expired]
        for key in expired:
            del self._entries[key]
        return len(expired)


class ConversationMemory(BaseMemory[str]):
    """Short-term conversation context with sliding window."""

    def __init__(self, max_entries: int = 50, window_size: int = 10) -> None:
        super().__init__(MemoryLayer.CONVERSATION, max_entries)
        self.window_size = window_size

    async def store(self, content: str, **metadata: Any) -> MemoryEntry:
        entry = MemoryEntry(
            content=content,
            layer=MemoryLayer.CONVERSATION,
            metadata=metadata,
            importance=metadata.get("importance", 0.5),
            ttl_seconds=metadata.get("ttl_seconds", 3600.0),
        )
        self._entries[entry.id] = entry
        self._enforce_limit()
        return entry

    async def retrieve(self, query: str, limit: int = 5) -> list[MemoryEntry]:
        self._cleanup_expired()
        # Return most recent entries within window
        entries = list(self._entries.values())[-self.window_size :]
        entries.sort(key=lambda e: e.created_at, reverse=True)
        return entries[:limit]

    async def get_window(self) -> list[MemoryEntry]:
        """Get the current conversation window."""
        entries = list(self._entries.values())[-self.window_size:]
        return sorted(entries, key=lambda e: e.created_at)


class SemanticMemory(BaseMemory[str]):
    """Long-term semantic knowledge with similarity search."""

    def __init__(self, max_entries: int = 10000, embedding_dim: int = 1536) -> None:
        super().__init__(MemoryLayer.SEMANTIC, max_entries)
        self.embedding_dim = embedding_dim

    async def store(self, content: str, **metadata: Any) -> MemoryEntry:
        entry = MemoryEntry(
            content=content,
            layer=MemoryLayer.SEMANTIC,
            metadata=metadata,
            embedding=metadata.get("embedding"),
            importance=metadata.get("importance", 0.7),
        )
        self._entries[entry.id] = entry
        self._enforce_limit()
        return entry

    async def retrieve(self, query: str, limit: int = 5) -> list[MemoryEntry]:
        self._cleanup_expired()
        # Score by importance and recency
        entries = list(self._entries.values())
        entries.sort(key=lambda e: e.compute_score(), reverse=True)
        return entries[:limit]

    async def search_by_embedding(
        self,
        query_embedding: list[float],
        limit: int = 5,
    ) -> list[MemoryEntry]:
        """Search by vector similarity (cosine)."""
        entries = [e for e in self._entries.values() if e.embedding is not None]
        scored = []
        for entry in entries:
            score = self._cosine_similarity(query_embedding, entry.embedding or [])
            scored.append((score, entry))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [e for _, e in scored[:limit]]

    @staticmethod
    def _cosine_similarity(a: list[float], b: list[float]) -> float:
        if not a or not b or len(a) != len(b):
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)


class ProceduralMemory(BaseMemory[dict[str, Any]]):
    """Learned workflows and procedural knowledge."""

    def __init__(self, max_entries: int = 500) -> None:
        super().__init__(MemoryLayer.PROCEDURAL, max_entries)

    async def store(self, content: dict[str, Any], **metadata: Any) -> MemoryEntry:
        entry = MemoryEntry(
            content=json.dumps(content),
            layer=MemoryLayer.PROCEDURAL,
            metadata=content,
            importance=metadata.get("importance", 0.8),
        )
        self._entries[entry.id] = entry
        self._enforce_limit()
        return entry

    async def retrieve(self, query: str, limit: int = 5) -> list[MemoryEntry]:
        self._cleanup_expired()
        entries = list(self._entries.values())
        entries.sort(key=lambda e: e.compute_score(), reverse=True)
        return entries[:limit]

    async def get_procedure(self, name: str) -> dict[str, Any] | None:
        """Retrieve a named procedure."""
        for entry in self._entries.values():
            meta = entry.metadata
            if meta.get("name") == name:
                entry.touch()
                return meta
        return None


class EpisodicMemory(BaseMemory[dict[str, Any]]):
    """Historical interaction records with temporal indexing."""

    def __init__(self, max_entries: int = 5000) -> None:
        super().__init__(MemoryLayer.EPISODIC, max_entries)
        self._timeline: list[tuple[float, str]] = []

    async def store(self, content: dict[str, Any], **metadata: Any) -> MemoryEntry:
        entry = MemoryEntry(
            content=json.dumps(content),
            layer=MemoryLayer.EPISODIC,
            metadata=content,
            importance=metadata.get("importance", 0.6),
        )
        self._entries[entry.id] = entry
        self._timeline.append((entry.created_at, entry.id))
        self._enforce_limit()
        return entry

    async def retrieve(self, query: str, limit: int = 5) -> list[MemoryEntry]:
        self._cleanup_expired()
        entries = list(self._entries.values())
        entries.sort(key=lambda e: e.created_at, reverse=True)
        return entries[:limit]

    async def get_timeline(
        self,
        since: float | None = None,
        until: float | None = None,
    ) -> list[MemoryEntry]:
        """Get entries within a time range."""
        results = []
        for ts, entry_id in self._timeline:
            if since and ts < since:
                continue
            if until and ts > until:
                continue
            entry = self._entries.get(entry_id)
            if entry:
                results.append(entry)
        return results


class MemoryManager:
    """Unified manager for all four memory layers."""

    def __init__(
        self,
        conversation: ConversationMemory | None = None,
        semantic: SemanticMemory | None = None,
        procedural: ProceduralMemory | None = None,
        episodic: EpisodicMemory | None = None,
    ) -> None:
        self.conversation = conversation or ConversationMemory()
        self.semantic = semantic or SemanticMemory()
        self.procedural = procedural or ProceduralMemory()
        self.episodic = episodic or EpisodicMemory()
        self._logger = logger.bind(component="memory_manager")

    async def store(
        self,
        content: str | dict[str, Any],
        layer: MemoryLayer,
        **metadata: Any,
    ) -> MemoryEntry:
        """Store content in the specified memory layer."""
        memory = self._get_layer(layer)
        if isinstance(memory, (ConversationMemory, SemanticMemory)):
            return await memory.store(str(content), **metadata)
        return await memory.store(content, **metadata)  # type: ignore[arg-type]

    async def retrieve(
        self,
        query: str,
        layer: MemoryLayer | None = None,
        limit: int = 5,
    ) -> list[MemoryEntry]:
        """Retrieve from a specific layer or all layers."""
        if layer:
            memory = self._get_layer(layer)
            return await memory.retrieve(query, limit)
        all_entries: list[MemoryEntry] = []
        for mem in (self.conversation, self.semantic, self.procedural, self.episodic):
            entries = await mem.retrieve(query, limit)
            all_entries.extend(entries)
        all_entries.sort(key=lambda e: e.compute_score(), reverse=True)
        return all_entries[:limit]

    async def consolidate(self) -> dict[str, int]:
        """Consolidate memory: promote important conversation to semantic,
        archive old episodic entries."""
        stats = {"promoted": 0, "archived": 0, "forgotten": 0}
        # Promote high-importance conversation entries to semantic
        conv_entries = list(self.conversation._entries.values())
        for entry in conv_entries:
            if entry.importance > 0.8 and entry.access_count > 2:
                await self.semantic.store(
                    entry.content,
                    importance=entry.importance,
                    promoted_from="conversation",
                )
                stats["promoted"] += 1
        # Cleanup expired
        for mem in (self.conversation, self.semantic, self.procedural, self.episodic):
            removed = mem._cleanup_expired()
            stats["forgotten"] += removed
        return stats

    def _get_layer(self, layer: MemoryLayer) -> BaseMemory[Any]:
        mapping = {
            MemoryLayer.CONVERSATION: self.conversation,
            MemoryLayer.SEMANTIC: self.semantic,
            MemoryLayer.PROCEDURAL: self.procedural,
            MemoryLayer.EPISODIC: self.episodic,
        }
        return mapping[layer]
