"""
GRC_Claw Caching System

Unified caching layer for GRC_Claw with pluggable backends,
invalidation strategies, and comprehensive monitoring.
"""

from .base import (
    CacheBackend,
    CacheConfig,
    CacheDecorator,
    CacheEntry,
    CacheError,
    CacheKeyError,
    CacheLevel,
    CacheStrategy,
    CacheConnectionError,
    CacheSerializationError,
    CacheKeyBuilder,
)
from .memory_cache import InMemoryCache
from .redis_cache import RedisCache
from .invalidation import (
    InvalidationEvent,
    InvalidationManager,
    InvalidationRule,
    InvalidationScope,
    InvalidationStrategy,
    InvalidationTrigger,
    TTLInvalidationStrategy,
    EventInvalidationStrategy,
    TagInvalidationStrategy,
    DependencyInvalidationStrategy,
    WriteThroughInvalidationStrategy,
    ScheduledInvalidationStrategy,
)
from .metrics import (
    Alert,
    AlertRule,
    AlertSeverity,
    CacheMetricsSnapshot,
    CacheMonitor,
    HealthMonitor,
    MetricType,
    MetricsCollector,
    PrometheusExporter,
)

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
