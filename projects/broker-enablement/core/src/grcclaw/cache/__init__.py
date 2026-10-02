"""
GRC_Claw Caching System

Unified caching layer for GRC_Claw with pluggable backends,
invalidation strategies, and comprehensive monitoring.
"""

from .base import (
    CacheBackend,
    CacheConfig,
    CacheConnectionError,
    CacheDecorator,
    CacheEntry,
    CacheError,
    CacheKeyBuilder,
    CacheKeyError,
    CacheLevel,
    CacheSerializationError,
    CacheStrategy,
)
from .invalidation import (
    DependencyInvalidationStrategy,
    EventInvalidationStrategy,
    InvalidationEvent,
    InvalidationManager,
    InvalidationRule,
    InvalidationScope,
    InvalidationStrategy,
    InvalidationTrigger,
    ScheduledInvalidationStrategy,
    TagInvalidationStrategy,
    TTLInvalidationStrategy,
    WriteThroughInvalidationStrategy,
)
from .memory_cache import InMemoryCache
from .metrics import (
    Alert,
    AlertRule,
    AlertSeverity,
    CacheMetricsSnapshot,
    CacheMonitor,
    HealthMonitor,
    MetricsCollector,
    MetricType,
    PrometheusExporter,
)
from .redis_cache import RedisCache

__all__ = [
    # Base
    "CacheBackend",
    "CacheConfig",
    "CacheDecorator",
    "CacheEntry",
    "CacheError",
    "CacheKeyError",
    "CacheLevel",
    "CacheStrategy",
    "CacheConnectionError",
    "CacheSerializationError",
    "CacheKeyBuilder",
    # Implementations
    "InMemoryCache",
    "RedisCache",
    # Invalidation
    "InvalidationEvent",
    "InvalidationManager",
    "InvalidationRule",
    "InvalidationScope",
    "InvalidationStrategy",
    "InvalidationTrigger",
    "TTLInvalidationStrategy",
    "EventInvalidationStrategy",
    "TagInvalidationStrategy",
    "DependencyInvalidationStrategy",
    "WriteThroughInvalidationStrategy",
    "ScheduledInvalidationStrategy",
    # Metrics
    "Alert",
    "AlertRule",
    "AlertSeverity",
    "CacheMetricsSnapshot",
    "CacheMonitor",
    "HealthMonitor",
    "MetricType",
    "MetricsCollector",
    "PrometheusExporter",
]
