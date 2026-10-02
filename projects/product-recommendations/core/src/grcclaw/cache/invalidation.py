"""
Cache Invalidation Strategies for GRC_Claw.

Provides multiple invalidation strategies including time-based (TTL),
event-based, tag-based, dependency-based, and write-through patterns.
"""

from __future__ import annotations

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .base import CacheBackend, CacheConfig

logger = logging.getLogger(__name__)


class InvalidationTrigger(str, Enum):
    """Types of invalidation triggers."""

    TTL = "ttl"
    EVENT = "event"
    TAG = "tag"
    DEPENDENCY = "dependency"
    WRITE = "write"
    MANUAL = "manual"
    SCHEDULED = "scheduled"


class InvalidationScope(str, Enum):
    """Scope of invalidation."""

    SINGLE = "single"
    PREFIX = "prefix"
    TAG = "tag"
    PATTERN = "pattern"
    ALL = "all"


@dataclass
class InvalidationEvent:
    """Represents a cache invalidation event."""

    trigger: InvalidationTrigger
    scope: InvalidationScope
    target: str  # key, prefix, tag, or pattern
    timestamp: float = field(default_factory=time.time)
    source: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    cascade: bool = False  # Whether to invalidate dependent entries


@dataclass
class InvalidationRule:
    """A rule that defines when and how to invalidate cache entries."""

    name: str
    trigger: InvalidationTrigger
    scope: InvalidationScope
    target: str
    condition: Callable[[Any], bool] | None = None
    cascade_targets: list[str] = field(default_factory=list)
    priority: int = 0  # Higher = evaluated first
    enabled: bool = True
    ttl_override: int | None = None  # Override TTL for matching entries


class InvalidationStrategy(ABC):
    """Abstract base class for invalidation strategies."""

    def __init__(self, cache: CacheBackend):
        self.cache = cache

    @abstractmethod
    async def invalidate(self, event: InvalidationEvent) -> int:
        """Execute invalidation. Returns count of invalidated entries."""
        ...

    @abstractmethod
    async def setup(self) -> None:
        """Initialize the strategy."""
        ...

    @abstractmethod
    async def teardown(self) -> None:
        """Clean up resources."""
        ...


class TTLInvalidationStrategy(InvalidationStrategy):
    """
    Time-based invalidation using TTL.

    Entries automatically expire after their TTL. This strategy
    also provides proactive expiration and TTL jitter to prevent
    cache stampedes.
    """

    def __init__(
        self,
        cache: CacheConfig,
        default_ttl: int = 300,
        jitter_pct: float = 0.1,
        proactive_expiry: bool = True,
        proactive_threshold: float = 0.8,
    ):
        # Note: cache here is actually a CacheBackend, but we accept it
        # as CacheConfig for the base class signature
        if isinstance(cache, CacheBackend):
            super().__init__(cache)
        else:
            # This shouldn't happen in practice
            raise TypeError("TTLInvalidationStrategy requires a CacheBackend")

        self.default_ttl = default_ttl
        self.jitter_pct = jitter_pct
        self.proactive_expiry = proactive_expiry
        self.proactive_threshold = proactive_threshold
        self._ttl_tracker: dict[str, float] = {}

    async def setup(self) -> None:
        logger.info("TTL invalidation strategy initialized (default_ttl=%ds, jitter=%.0f%%)",
                     self.default_ttl, self.jitter_pct * 100)

    async def teardown(self) -> None:
        self._ttl_tracker.clear()

    def compute_ttl(self, base_ttl: int | None = None) -> int:
        """Compute TTL with jitter to prevent cache stampedes."""
        import random

        ttl = base_ttl if base_ttl is not None else self.default_ttl
        if ttl <= 0:
            return 0

        jitter = int(ttl * self.jitter_pct * random.uniform(-1, 1))
        return max(1, ttl + jitter)

    async def invalidate(self, event: InvalidationEvent) -> int:
        """Invalidate entries based on TTL rules."""
        if event.trigger != InvalidationTrigger.TTL:
            return 0

        if event.scope == InvalidationScope.SINGLE:
            deleted = await self.cache.delete(event.target)
            return 1 if deleted else 0

        elif event.scope == InvalidationScope.PATTERN:
            keys = await self.cache.keys(event.target)
            if keys:
                return await self.cache.delete_many(keys)
            return 0

        elif event.scope == InvalidationScope.ALL:
            await self.cache.clear()
            return -1  # Unknown count

        return 0

    async def get_remaining_ttl(self, key: str) -> float:
        """Get remaining TTL for a key."""
        return await self.cache.ttl(key)

    async def is_near_expiry(self, key: str, threshold: float | None = None) -> bool:
        """Check if a key is near its expiration time."""
        threshold = threshold or self.proactive_threshold
        remaining = await self.cache.ttl(key)

        if remaining < 0:  # No expiry or doesn't exist
            return False

        # Get the original TTL from the entry metadata
        # For simplicity, we use the default TTL as reference
        original_ttl = self.default_ttl
        return remaining < (original_ttl * threshold)


class EventInvalidationStrategy(InvalidationStrategy):
    """
    Event-based invalidation.

    Listens for domain events and invalidates cache entries
    based on configurable rules.
    """

    def __init__(self, cache: CacheBackend):
        super().__init__(cache)
        self._rules: list[InvalidationRule] = []
        self._event_queue: asyncio.Queue[InvalidationEvent] = asyncio.Queue()
        self._worker_task: asyncio.Task | None = None
        self._running = False

    async def setup(self) -> None:
        """Start the event processing worker."""
        self._running = True
        self._worker_task = asyncio.create_task(self._process_events())
        logger.info("Event invalidation strategy initialized")

    async def teardown(self) -> None:
        """Stop the event processing worker."""
        self._running = False
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass

    def add_rule(self, rule: InvalidationRule) -> None:
        """Add an invalidation rule."""
        self._rules.append(rule)
        self._rules.sort(key=lambda r: r.priority, reverse=True)
        logger.debug("Added invalidation rule: %s", rule.name)

    def remove_rule(self, name: str) -> bool:
        """Remove an invalidation rule by name."""
        for i, rule in enumerate(self._rules):
            if rule.name == name:
                self._rules.pop(i)
                return True
        return False

    async def emit(self, event: InvalidationEvent) -> None:
        """Emit an invalidation event."""
        await self._event_queue.put(event)
        logger.debug("Emitted invalidation event: %s/%s for %s",
                      event.trigger.value, event.scope.value, event.target)

    async def _process_events(self) -> None:
        """Background worker to process invalidation events."""
        while self._running:
            try:
                event = await asyncio.wait_for(
                    self._event_queue.get(),
                    timeout=1.0,
                )
                await self._handle_event(event)
            except TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error processing invalidation event: %s", e)

    async def _handle_event(self, event: InvalidationEvent) -> int:
        """Handle a single invalidation event."""
        total_invalidated = 0

        # Find matching rules
        matching_rules = [
            r for r in self._rules
            if r.enabled and r.trigger == event.trigger
        ]

        for rule in matching_rules:
            if rule.condition and not rule.condition(event):
                continue

            # Invalidate based on rule scope
            count = await self._invalidate_by_scope(event, rule.scope, rule.target)
            total_invalidated += count

            # Cascade invalidation
            if event.cascade and rule.cascade_targets:
                for cascade_target in rule.cascade_targets:
                    cascade_event = InvalidationEvent(
                        trigger=InvalidationTrigger.CASCADE,
                        scope=InvalidationScope.TAG,
                        target=cascade_target,
                        source=event.source,
                        cascade=False,
                    )
                    count = await self._invalidate_by_scope(
                        cascade_event, InvalidationScope.TAG, cascade_target
                    )
                    total_invalidated += count

        return total_invalidated

    async def _invalidate_by_scope(
        self, event: InvalidationEvent, scope: InvalidationScope, target: str
    ) -> int:
        """Invalidate entries based on scope."""
        if scope == InvalidationScope.SINGLE:
            deleted = await self.cache.delete(target)
            return 1 if deleted else 0

        elif scope == InvalidationScope.PREFIX:
            keys = await self.cache.keys(f"{target}*")
            if keys:
                return await self.cache.delete_many(keys)
            return 0

        elif scope == InvalidationScope.TAG:
            return await self.cache.invalidate_by_tags([target])

        elif scope == InvalidationScope.PATTERN:
            keys = await self.cache.keys(target)
            if keys:
                return await self.cache.delete_many(keys)
            return 0

        elif scope == InvalidationScope.ALL:
            await self.cache.clear()
            return -1

        return 0

    async def invalidate(self, event: InvalidationEvent) -> int:
        """Directly invalidate based on an event."""
        return await self._invalidate_by_scope(event, event.scope, event.target)


class TagInvalidationStrategy(InvalidationStrategy):
    """
    Tag-based invalidation.

    Entries are tagged with one or more tags, and can be
    invalidated by tag. Supports tag hierarchies and
    bulk tag operations.
    """

    def __init__(self, cache: CacheBackend):
        super().__init__(cache)
        self._tag_dependencies: dict[str, set[str]] = {}  # tag -> dependent tags

    async def setup(self) -> None:
        logger.info("Tag invalidation strategy initialized")

    async def teardown(self) -> None:
        self._tag_dependencies.clear()

    def add_tag_dependency(self, tag: str, depends_on: str) -> None:
        """Define that invalidating `depends_on` should also invalidate `tag`."""
        if tag not in self._tag_dependencies:
            self._tag_dependencies[tag] = set()
        self._tag_dependencies[tag].add(depends_on)

    async def invalidate(self, event: InvalidationEvent) -> int:
        """Invalidate entries by tags."""
        if event.scope == InvalidationScope.TAG:
            tags = [event.target]
        elif event.scope == InvalidationScope.SINGLE:
            # For single key, we need to find its tags
            # This is a simplified version
            return 0
        else:
            return 0

        # Include dependent tags
        all_tags = set(tags)
        for tag in tags:
            if tag in self._tag_dependencies:
                all_tags.update(self._tag_dependencies[tag])

        return await self.cache.invalidate_by_tags(list(all_tags))

    async def invalidate_tags(self, tags: list[str], cascade: bool = True) -> int:
        """Invalidate all entries with any of the given tags."""
        all_tags = set(tags)
        if cascade:
            for tag in tags:
                if tag in self._tag_dependencies:
                    all_tags.update(self._tag_dependencies[tag])

        return await self.cache.invalidate_by_tags(list(all_tags))

    async def get_tags_for_key(self, key: str) -> list[str]:
        """Get all tags associated with a key."""
        # This would need cache backend support for tag retrieval
        # For now, return empty list
        return []


class DependencyInvalidationStrategy(InvalidationStrategy):
    """
    Dependency-based invalidation.

    Tracks dependencies between cache entries and invalidates
    dependents when a source entry changes.
    """

    def __init__(self, cache: CacheBackend):
        super().__init__(cache)
        self._dependencies: dict[str, set[str]] = {}  # source_key -> set of dependent keys
        self._reverse_deps: dict[str, set[str]] = {}  # dependent_key -> set of source keys

    async def setup(self) -> None:
        logger.info("Dependency invalidation strategy initialized")

    async def teardown(self) -> None:
        self._dependencies.clear()
        self._reverse_deps.clear()

    def add_dependency(self, source_key: str, dependent_key: str) -> None:
        """Register that `dependent_key` depends on `source_key`."""
        if source_key not in self._dependencies:
            self._dependencies[source_key] = set()
        self._dependencies[source_key].add(dependent_key)

        if dependent_key not in self._reverse_deps:
            self._reverse_deps[dependent_key] = set()
        self._reverse_deps[dependent_key].add(source_key)

    def remove_dependency(self, source_key: str, dependent_key: str) -> None:
        """Remove a dependency relationship."""
        if source_key in self._dependencies:
            self._dependencies[source_key].discard(dependent_key)
        if dependent_key in self._reverse_deps:
            self._reverse_deps[dependent_key].discard(source_key)

    async def invalidate(self, event: InvalidationEvent) -> int:
        """Invalidate entries based on dependency graph."""
        if event.scope != InvalidationScope.SINGLE:
            return 0

        source_key = event.target
        if source_key not in self._dependencies:
            return 0

        # Get all direct dependents
        dependents = list(self._dependencies[source_key])

        # Get transitive dependents
        all_dependents = set(dependents)
        queue = list(dependents)
        while queue:
            current = queue.pop(0)
            if current in self._dependencies:
                for dep in self._dependencies[current]:
                    if dep not in all_dependents:
                        all_dependents.add(dep)
                        queue.append(dep)

        # Delete the source and all dependents
        keys_to_delete = [source_key] + list(all_dependents)
        deleted = await self.cache.delete_many(keys_to_delete)

        # Clean up dependency tracking
        for key in keys_to_delete:
            if key in self._dependencies:
                del self._dependencies[key]
            if key in self._reverse_deps:
                del self._reverse_deps[key]

        return deleted

    async def invalidate_dependents(self, source_key: str) -> int:
        """Invalidate all entries that depend on the given key."""
        event = InvalidationEvent(
            trigger=InvalidationTrigger.DEPENDENCY,
            scope=InvalidationScope.SINGLE,
            target=source_key,
        )
        return await self.invalidate(event)


class WriteThroughInvalidationStrategy(InvalidationStrategy):
    """
    Write-through invalidation.

    Automatically invalidates cache entries when the underlying
    data source is updated. Supports write-through and
    write-behind patterns.
    """

    def __init__(self, cache: CacheBackend):
        super().__init__(cache)
        self._write_handlers: dict[str, Callable] = {}
        self._pending_writes: dict[str, Any] = {}

    async def setup(self) -> None:
        logger.info("Write-through invalidation strategy initialized")

    async def teardown(self) -> None:
        self._write_handlers.clear()
        self._pending_writes.clear()

    def register_write_handler(self, prefix: str, handler: Callable) -> None:
        """Register a handler for write operations on a key prefix."""
        self._write_handlers[prefix] = handler

    async def invalidate(self, event: InvalidationEvent) -> int:
        """Invalidate entries affected by a write operation."""
        if event.trigger != InvalidationTrigger.WRITE:
            return 0

        target = event.target

        # Find matching write handlers
        for prefix, handler in self._write_handlers.items():
            if target.startswith(prefix):
                # Get keys to invalidate from handler
                keys_to_invalidate = await handler(target)
                if keys_to_invalidate:
                    return await self.cache.delete_many(keys_to_invalidate)

        # Default: invalidate the target key and pattern matches
        deleted = await self.cache.delete(target)
        count = 1 if deleted else 0

        # Also invalidate pattern matches
        keys = await self.cache.keys(f"{target}*")
        if keys:
            count += await self.cache.delete_many(keys)

        return count

    async def write_through(self, key: str, value: Any, ttl: int | None = None) -> bool:
        """Write to cache and invalidate related entries."""
        # Write to cache
        success = await self.cache.set(key, value, ttl=ttl)
        if not success:
            return False

        # Invalidate related entries
        event = InvalidationEvent(
            trigger=InvalidationTrigger.WRITE,
            scope=InvalidationScope.SINGLE,
            target=key,
        )
        await self.invalidate(event)

        return True


class ScheduledInvalidationStrategy(InvalidationStrategy):
    """
    Scheduled/timed invalidation.

    Invalidates cache entries on a schedule (e.g., every N minutes,
    at specific times). Useful for data that needs periodic refresh.
    """

    def __init__(self, cache: CacheBackend):
        super().__init__(cache)
        self._schedules: list[dict[str, Any]] = []
        self._task: asyncio.Task | None = None
        self._running = False

    async def setup(self) -> None:
        """Start the scheduled invalidation worker."""
        self._running = True
        self._task = asyncio.create_task(self._run_schedules())
        logger.info("Scheduled invalidation strategy initialized")

    async def teardown(self) -> None:
        """Stop the scheduled invalidation worker."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    def add_schedule(
        self,
        name: str,
        interval_seconds: float,
        scope: InvalidationScope,
        target: str,
        last_run: float | None = None,
    ) -> None:
        """Add a scheduled invalidation."""
        self._schedules.append({
            "name": name,
            "interval_seconds": interval_seconds,
            "scope": scope,
            "target": target,
            "last_run": last_run or 0,
        })

    def remove_schedule(self, name: str) -> bool:
        """Remove a scheduled invalidation."""
        for i, sched in enumerate(self._schedules):
            if sched["name"] == name:
                self._schedules.pop(i)
                return True
        return False

    async def _run_schedules(self) -> None:
        """Background worker to execute scheduled invalidations."""
        while self._running:
            try:
                await asyncio.sleep(1.0)  # Check every second

                now = time.time()
                for sched in self._schedules:
                    if now - sched["last_run"] >= sched["interval_seconds"]:
                        event = InvalidationEvent(
                            trigger=InvalidationTrigger.SCHEDULED,
                            scope=sched["scope"],
                            target=sched["target"],
                        )
                        await self.invalidate(event)
                        sched["last_run"] = now
                        logger.debug("Executed scheduled invalidation: %s", sched["name"])

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in scheduled invalidation: %s", e)

    async def invalidate(self, event: InvalidationEvent) -> int:
        """Invalidate based on schedule."""
        if event.scope == InvalidationScope.SINGLE:
            deleted = await self.cache.delete(event.target)
            return 1 if deleted else 0
        elif event.scope == InvalidationScope.PATTERN:
            keys = await self.cache.keys(event.target)
            if keys:
                return await self.cache.delete_many(keys)
            return 0
        elif event.scope == InvalidationScope.TAG:
            return await self.cache.invalidate_by_tags([event.target])
        elif event.scope == InvalidationScope.ALL:
            await self.cache.clear()
            return -1
        return 0


class InvalidationManager:
    """
    Central manager for all invalidation strategies.

    Coordinates multiple invalidation strategies and provides
    a unified interface for cache invalidation.
    """

    def __init__(self, cache: CacheBackend):
        self.cache = cache
        self._strategies: dict[str, InvalidationStrategy] = {}
        self._history: list[InvalidationEvent] = []
        self._max_history = 1000

    def register_strategy(self, name: str, strategy: InvalidationStrategy) -> None:
        """Register an invalidation strategy."""
        self._strategies[name] = strategy
        logger.info("Registered invalidation strategy: %s", name)

    def unregister_strategy(self, name: str) -> bool:
        """Unregister an invalidation strategy."""
        if name in self._strategies:
            del self._strategies[name]
            return True
        return False

    async def setup_all(self) -> None:
        """Initialize all registered strategies."""
        for name, strategy in self._strategies.items():
            try:
                await strategy.setup()
            except Exception as e:
                logger.error("Failed to setup strategy %s: %s", name, e)

    async def teardown_all(self) -> None:
        """Clean up all registered strategies."""
        for name, strategy in self._strategies.items():
            try:
                await strategy.teardown()
            except Exception as e:
                logger.error("Failed to teardown strategy %s: %s", name, e)

    async def invalidate(
        self,
        trigger: InvalidationTrigger,
        scope: InvalidationScope,
        target: str,
        source: str = "",
        cascade: bool = False,
    ) -> int:
        """Execute invalidation across all applicable strategies."""
        event = InvalidationEvent(
            trigger=trigger,
            scope=scope,
            target=target,
            source=source,
            cascade=cascade,
        )

        # Record in history
        self._history.append(event)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]

        total = 0
        for name, strategy in self._strategies.items():
            try:
                count = await strategy.invalidate(event)
                if count > 0:
                    total += count
                    logger.debug("Strategy %s invalidated %d entries", name, count)
            except Exception as e:
                logger.error("Strategy %s failed to invalidate: %s", name, e)

        return total

    async def invalidate_key(self, key: str, cascade: bool = True) -> int:
        """Invalidate a single key."""
        return await self.invalidate(
            trigger=InvalidationTrigger.MANUAL,
            scope=InvalidationScope.SINGLE,
            target=key,
            cascade=cascade,
        )

    async def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all keys matching a pattern."""
        return await self.invalidate(
            trigger=InvalidationTrigger.MANUAL,
            scope=InvalidationScope.PATTERN,
            target=pattern,
        )

    async def invalidate_tags(self, tags: list[str]) -> int:
        """Invalidate all entries with any of the given tags."""
        return await self.invalidate(
            trigger=InvalidationTrigger.TAG,
            scope=InvalidationScope.TAG,
            target=tags[0] if tags else "",
        )

    async def invalidate_all(self) -> int:
        """Invalidate all cache entries."""
        return await self.invalidate(
            trigger=InvalidationTrigger.MANUAL,
            scope=InvalidationScope.ALL,
            target="*",
        )

    def get_history(
        self,
        limit: int = 100,
        trigger: InvalidationTrigger | None = None,
    ) -> list[InvalidationEvent]:
        """Get invalidation history."""
        history = self._history
        if trigger:
            history = [e for e in history if e.trigger == trigger]
        return history[-limit:]

    def clear_history(self) -> None:
        """Clear invalidation history."""
        self._history.clear()
