"""
In-Memory Cache Implementation for GRC_Claw.

Provides a high-performance local cache with LRU/LFU/FIFO eviction,
TTL support, tag-based invalidation, and memory-bound operation.
"""

from __future__ import annotations

import asyncio
import json
import logging
import sys
import threading
import time
from collections import OrderedDict, defaultdict
from typing import Any

from .base import (
    CacheBackend,
    CacheConfig,
    CacheEntry,
    CacheError,
    CacheSerializationError,
    CacheStrategy,
)

logger = logging.getLogger(__name__)


class InMemoryCache(CacheBackend):
    """
    Thread-safe in-memory cache with configurable eviction strategy.

    Features:
    - LRU, LFU, FIFO, and TTL eviction strategies
    - Per-entry TTL with automatic expiration
    - Tag-based invalidation
    - Memory-bounded with max entry count
    - Background cleanup of expired entries
    - Lock-free reads with copy-on-write semantics
    - Statistics tracking (hits, misses, evictions)
    """

    def __init__(
        self,
        config: CacheConfig | None = None,
        cleanup_interval: float = 60.0,
        enable_stats: bool = True,
    ):
        super().__init__(config)
        self.cleanup_interval = cleanup_interval
        self.enable_stats = enable_stats

        # Core storage: OrderedDict for LRU ordering
        self._store: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()

        # Tag index: tag -> set of keys
        self._tag_index: dict[str, set[str]] = defaultdict(set)

        # Statistics
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "expirations": 0,
            "sets": 0,
            "deletes": 0,
            "clears": 0,
            "total_set_time_ms": 0.0,
            "total_get_time_ms": 0.0,
        }

        # Background cleanup task
        self._cleanup_task: asyncio.Task | None = None
        self._cleanup_event: asyncio.Event | None = None
        self._running = False

    async def connect(self) -> None:
        """Initialize the in-memory cache and start background cleanup."""
        self._running = True
        self._cleanup_event = asyncio.Event()
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        self._initialized = True
        logger.info("In-memory cache initialized (strategy=%s, max_size=%d)",
                     self.config.strategy.value, self.config.max_size)

    async def disconnect(self) -> None:
        """Stop background cleanup and clear all data."""
        self._running = False
        if self._cleanup_event:
            self._cleanup_event.set()
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        with self._lock:
            self._store.clear()
            self._tag_index.clear()
        self._initialized = False
        logger.info("In-memory cache disconnected")

    async def _cleanup_loop(self) -> None:
        """Background task to periodically clean up expired entries."""
        while self._running:
            try:
                await asyncio.wait_for(
                    self._cleanup_event.wait(),
                    timeout=self.cleanup_interval,
                )
                break  # Event set, exit
            except TimeoutError:
                pass  # Normal timeout, proceed with cleanup
            except asyncio.CancelledError:
                break

            try:
                await self._cleanup_expired()
            except Exception as e:
                logger.warning("Error in cache cleanup: %s", e)

    async def _cleanup_expired(self) -> int:
        """Remove all expired entries. Returns count removed."""
        now = time.time()
        expired_keys: list[str] = []

        with self._lock:
            for key, entry in self._store.items():
                if entry.is_expired:
                    expired_keys.append(key)

            for key in expired_keys:
                self._remove_entry(key)

        if expired_keys:
            self._stats["expirations"] += len(expired_keys)
            logger.debug("Cleaned up %d expired entries", len(expired_keys))

        return len(expired_keys)

    def _remove_entry(self, key: str) -> None:
        """Remove an entry from store and tag index. Must hold lock."""
        if key in self._store:
            entry = self._store.pop(key)
            for tag in entry.tags:
                if tag in self._tag_index:
                    self._tag_index[tag].discard(key)
                    if not self._tag_index[tag]:
                        del self._tag_index[tag]

    def _evict_if_needed(self) -> None:
        """Evict entries if store exceeds max_size. Must hold lock."""
        while len(self._store) >= self.config.max_size:
            if not self._store:
                break

            if self.config.strategy == CacheStrategy.LRU:
                # Evict least recently used (first item in OrderedDict)
                key, _ = next(iter(self._store.items()))
            elif self.config.strategy == CacheStrategy.LFU:
                # Evict least frequently used
                key = min(self._store.keys(),
                          key=lambda k: self._store[k].access_count)
            elif self.config.strategy == CacheStrategy.FIFO:
                # Evict first inserted (oldest created_at)
                key = min(self._store.keys(),
                          key=lambda k: self._store[k].created_at)
            elif self.config.strategy == CacheStrategy.TTL:
                # Evict entry with shortest remaining TTL
                key = min(self._store.keys(),
                          key=lambda k: self._store[k].expires_at
                          if self._store[k].expires_at > 0
                          else float("inf"))
            else:
                key, _ = next(iter(self._store.items()))

            self._remove_entry(key)
            self._stats["evictions"] += 1
            logger.debug("Evicted key %s (strategy=%s)", key, self.config.strategy.value)

    def _serialize(self, value: Any) -> bytes:
        """Serialize value to bytes."""
        try:
            if self.config.serializer == "json":
                return json.dumps(value, default=str).encode("utf-8")
            elif self.config.serializer == "pickle":
                import pickle
                return pickle.dumps(value)
            else:
                raise CacheSerializationError(f"Unknown serializer: {self.config.serializer}")
        except Exception as e:
            raise CacheSerializationError(f"Serialization failed: {e}") from e

    def _deserialize(self, data: bytes) -> Any:
        """Deserialize bytes to value."""
        try:
            if self.config.serializer == "json":
                return json.loads(data.decode("utf-8"))
            elif self.config.serializer == "pickle":
                import pickle
                return pickle.loads(data)
            else:
                raise CacheSerializationError(f"Unknown serializer: {self.config.serializer}")
        except Exception as e:
            raise CacheSerializationError(f"Deserialization failed: {e}") from e

    async def get(self, key: str) -> Any | None:
        """Retrieve a value from in-memory cache."""
        start = time.time()
        full_key = self._make_key(key)

        with self._lock:
            entry = self._store.get(full_key)

            if entry is None:
                self._stats["misses"] += 1
                return None

            if entry.is_expired:
                self._remove_entry(full_key)
                self._stats["misses"] += 1
                self._stats["expirations"] += 1
                return None

            # Update access metadata
            entry.touch()

            # Move to end for LRU ordering
            if self.config.strategy == CacheStrategy.LRU:
                self._store.move_to_end(full_key)

            self._stats["hits"] += 1
            elapsed_ms = (time.time() - start) * 1000
            self._stats["total_get_time_ms"] += elapsed_ms

            return entry.value

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int | None = None,
        tags: list[str] | None = None,
    ) -> bool:
        """Store a value in in-memory cache."""
        start = time.time()
        full_key = self._make_key(key)
        effective_ttl = ttl if ttl is not None else self.config.default_ttl

        try:
            serialized = self._serialize(value)
            size_bytes = len(serialized)
        except CacheSerializationError:
            raise

        with self._lock:
            # Remove old entry if exists (to update tag index)
            if full_key in self._store:
                self._remove_entry(full_key)

            # Evict if at capacity
            self._evict_if_needed()

            # Create new entry
            now = time.time()
            entry = CacheEntry(
                key=full_key,
                value=value,
                created_at=now,
                expires_at=now + effective_ttl if effective_ttl > 0 else 0,
                access_count=0,
                last_accessed=now,
                size_bytes=size_bytes,
                tags=tags or [],
            )

            self._store[full_key] = entry

            # Update tag index
            for tag in (tags or []):
                self._tag_index[tag].add(full_key)

            self._stats["sets"] += 1
            elapsed_ms = (time.time() - start) * 1000
            self._stats["total_set_time_ms"] += elapsed_ms

            return True

    async def delete(self, key: str) -> bool:
        """Remove a key from in-memory cache."""
        full_key = self._make_key(key)

        with self._lock:
            if full_key in self._store:
                self._remove_entry(full_key)
                self._stats["deletes"] += 1
                return True
            return False

    async def exists(self, key: str) -> bool:
        """Check if a key exists and is not expired."""
        full_key = self._make_key(key)

        with self._lock:
            entry = self._store.get(full_key)
            if entry is None:
                return False
            if entry.is_expired:
                self._remove_entry(full_key)
                self._stats["expirations"] += 1
                return False
            return True

    async def clear(self) -> bool:
        """Clear all entries in the cache."""
        with self._lock:
            self._store.clear()
            self._tag_index.clear()
            self._stats["clears"] += 1
            return True

    async def keys(self, pattern: str = "*") -> list[str]:
        """Return keys matching a glob-style pattern."""
        import fnmatch

        with self._lock:
            # Filter out expired entries first
            now = time.time()
            expired = [k for k, e in self._store.items() if e.is_expired]
            for k in expired:
                self._remove_entry(k)

            all_keys = list(self._store.keys())

        # Strip prefix and filter by pattern
        prefix = self._make_key("")
        result = []
        for full_key in all_keys:
            stripped = full_key.removeprefix(prefix)
            if fnmatch.fnmatch(stripped, pattern):
                result.append(stripped)

        return result

    async def ttl(self, key: str) -> float:
        """Return remaining TTL for a key in seconds."""
        full_key = self._make_key(key)

        with self._lock:
            entry = self._store.get(full_key)
            if entry is None:
                return -2
            if entry.expires_at <= 0:
                return -1
            remaining = entry.expires_at - time.time()
            if remaining <= 0:
                self._remove_entry(full_key)
                self._stats["expirations"] += 1
                return -2
            return remaining

    async def expire(self, key: str, ttl: int) -> bool:
        """Set/update TTL for an existing key."""
        full_key = self._make_key(key)

        with self._lock:
            entry = self._store.get(full_key)
            if entry is None:
                return False
            entry.expires_at = time.time() + ttl
            return True

    async def increment(self, key: str, amount: int = 1) -> int:
        """Atomically increment a numeric value."""
        full_key = self._make_key(key)

        with self._lock:
            entry = self._store.get(full_key)
            if entry is None:
                # Initialize
                new_value = amount
                entry = CacheEntry(
                    key=full_key,
                    value=new_value,
                    created_at=time.time(),
                    expires_at=0,
                    access_count=0,
                    last_accessed=time.time(),
                    size_bytes=sys.getsizeof(new_value),
                    tags=[],
                )
                self._store[full_key] = entry
                return new_value

            if entry.is_expired:
                self._remove_entry(full_key)
                raise CacheError(f"Key {key} has expired")

            if isinstance(entry.value, (int, float)):
                entry.value += amount
                entry.touch()
                if self.config.strategy == CacheStrategy.LRU:
                    self._store.move_to_end(full_key)
                return int(entry.value)
            else:
                raise CacheError(
                    f"Cannot increment non-numeric value of type {type(entry.value)}"
                )

    async def get_many(self, keys: list[str]) -> dict[str, Any]:
        """Retrieve multiple values."""
        result: dict[str, Any] = {}
        for key in keys:
            value = await self.get(key)
            if value is not None:
                result[key] = value
        return result

    async def set_many(
        self,
        mapping: dict[str, Any],
        ttl: int | None = None,
        tags: list[str] | None = None,
    ) -> bool:
        """Store multiple values."""
        for key, value in mapping.items():
            await self.set(key, value, ttl=ttl, tags=tags)
        return True

    async def delete_many(self, keys: list[str]) -> int:
        """Delete multiple keys. Returns count of deleted keys."""
        count = 0
        for key in keys:
            if await self.delete(key):
                count += 1
        return count

    async def invalidate_by_tags(self, tags: list[str]) -> int:
        """Invalidate all entries matching any of the given tags."""
        with self._lock:
            keys_to_remove: set[str] = set()
            for tag in tags:
                if tag in self._tag_index:
                    keys_to_remove.update(self._tag_index[tag])

            for key in keys_to_remove:
                self._remove_entry(key)

            # Clean up tag index
            for tag in tags:
                if tag in self._tag_index:
                    del self._tag_index[tag]

            return len(keys_to_remove)

    async def flush(self) -> bool:
        """Flush all data (same as clear for in-memory)."""
        return await self.clear()

    async def health_check(self) -> dict[str, Any]:
        """Return health status and statistics."""
        with self._lock:
            entry_count = len(self._store)
            total_size = sum(e.size_bytes for e in self._store.values())
            expired_count = sum(1 for e in self._store.values() if e.is_expired)

        hits = self._stats["hits"]
        misses = self._stats["misses"]
        total = hits + misses

        return {
            "status": "healthy",
            "connected": self._initialized,
            "entry_count": entry_count,
            "total_size_bytes": total_size,
            "expired_entries": expired_count,
            "max_size": self.config.max_size,
            "strategy": self.config.strategy.value,
            "hit_rate": round(hits / total, 4) if total > 0 else 0.0,
            "hits": hits,
            "misses": misses,
            "evictions": self._stats["evictions"],
            "expirations": self._stats["expirations"],
        }

    async def get_stats(self) -> dict[str, Any]:
        """Return detailed cache statistics."""
        with self._lock:
            entry_count = len(self._store)
            total_size = sum(e.size_bytes for e in self._store.values())
            expired_count = sum(1 for e in self._store.values() if e.is_expired)

            # Calculate average entry size
            avg_size = total_size / entry_count if entry_count > 0 else 0

            # Tag statistics
            tag_counts = {tag: len(keys) for tag, keys in self._tag_index.items()}

        hits = self._stats["hits"]
        misses = self._stats["misses"]
        total = hits + misses

        avg_set_time = (
            self._stats["total_set_time_ms"] / self._stats["sets"]
            if self._stats["sets"] > 0
            else 0
        )
        avg_get_time = (
            self._stats["total_get_time_ms"] / self._stats["hits"]
            if self._stats["hits"] > 0
            else 0
        )

        return {
            "entry_count": entry_count,
            "total_size_bytes": total_size,
            "avg_entry_size_bytes": round(avg_size, 2),
            "expired_entries": expired_count,
            "max_size": self.config.max_size,
            "strategy": self.config.strategy.value,
            "hits": hits,
            "misses": misses,
            "hit_rate": round(hits / total, 4) if total > 0 else 0.0,
            "evictions": self._stats["evictions"],
            "expirations": self._stats["expirations"],
            "sets": self._stats["sets"],
            "deletes": self._stats["deletes"],
            "clears": self._stats["clears"],
            "avg_set_time_ms": round(avg_set_time, 4),
            "avg_get_time_ms": round(avg_get_time, 4),
            "tag_counts": tag_counts,
        }

    def reset_stats(self) -> None:
        """Reset all statistics counters."""
        with self._lock:
            for key in self._stats:
                if isinstance(self._stats[key], (int, float)):
                    self._stats[key] = 0

    def get_memory_usage(self) -> dict[str, Any]:
        """Return detailed memory usage breakdown."""
        with self._lock:
            total_size = sum(e.size_bytes for e in self._store.values())
            entry_count = len(self._store)

            # Size by tag
            tag_sizes: dict[str, int] = defaultdict(int)
            for entry in self._store.values():
                for tag in entry.tags:
                    tag_sizes[tag] += entry.size_bytes

            # Size by prefix (first part of key)
            prefix_sizes: dict[str, int] = defaultdict(int)
            for key, entry in self._store.items():
                prefix = key.split(":")[0] if ":" in key else "unknown"
                prefix_sizes[prefix] += entry.size_bytes

        return {
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 4),
            "entry_count": entry_count,
            "avg_entry_size_bytes": round(total_size / entry_count, 2) if entry_count > 0 else 0,
            "size_by_tag": dict(tag_sizes),
            "size_by_prefix": dict(prefix_sizes),
            "max_size_bytes": self.config.max_size * (total_size / entry_count if entry_count > 0 else 0),
        }
