"""
Cache Metrics and Monitoring for GRC_Claw.

Provides comprehensive metrics collection, health monitoring,
alerting, and Prometheus-compatible export for cache operations.
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .base import CacheBackend

logger = logging.getLogger(__name__)


class MetricType(str, Enum):
    """Types of cache metrics."""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"
    RATE = "rate"


class AlertSeverity(str, Enum):
    """Alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class MetricValue:
    """A single metric data point."""

    name: str
    value: float
    timestamp: float = field(default_factory=time.time)
    labels: dict[str, str] = field(default_factory=dict)
    type: MetricType = MetricType.GAUGE


@dataclass
class CacheMetricsSnapshot:
    """A snapshot of all cache metrics at a point in time."""

    timestamp: float
    hits: int = 0
    misses: int = 0
    hit_rate: float = 0.0
    sets: int = 0
    deletes: int = 0
    evictions: int = 0
    expirations: int = 0
    total_entries: int = 0
    memory_usage_bytes: int = 0
    avg_get_time_ms: float = 0.0
    avg_set_time_ms: float = 0.0
    operations_per_second: float = 0.0
    error_count: int = 0
    error_rate: float = 0.0
    connection_status: str = "unknown"
    custom_metrics: dict[str, float] = field(default_factory=dict)


@dataclass
class Alert:
    """A cache alert."""

    alert_id: str
    name: str
    severity: AlertSeverity
    message: str
    timestamp: float = field(default_factory=time.time)
    metric_name: str = ""
    threshold: float = 0.0
    current_value: float = 0.0
    acknowledged: bool = False


@dataclass
class AlertRule:
    """A rule for generating alerts."""

    name: str
    metric_name: str
    condition: str  # ">", "<", ">=", "<=", "=="
    threshold: float
    severity: AlertSeverity
    message: str
    cooldown_seconds: float = 300.0
    enabled: bool = True
    _last_triggered: float = 0.0

    def evaluate(self, value: float) -> bool:
        """Evaluate the rule against a metric value."""
        if not self.enabled:
            return False

        ops = {
            ">": lambda a, b: a > b,
            "<": lambda a, b: a < b,
            ">=": lambda a, b: a >= b,
            "<=": lambda a, b: a <= b,
            "==": lambda a, b: a == b,
        }

        op = ops.get(self.condition)
        if op is None:
            return False

        return op(value, self.threshold)

    def can_trigger(self) -> bool:
        """Check if enough time has passed since last trigger."""
        return (time.time() - self._last_triggered) >= self.cooldown_seconds

    def mark_triggered(self) -> None:
        """Mark the rule as triggered."""
        self._last_triggered = time.time()


class MetricsCollector:
    """
    Collects and aggregates cache metrics.

    Tracks operation counts, latencies, error rates, and
    provides real-time and historical metric data.
    """

    def __init__(
        self,
        cache: CacheBackend,
        collection_interval: float = 10.0,
        max_history: int = 1000,
    ):
        self.cache = cache
        self.collection_interval = collection_interval
        self.max_history = max_history

        # Counters
        self._hits = 0
        self._misses = 0
        self._sets = 0
        self._deletes = 0
        self._errors = 0
        self._evictions = 0
        self._expirations = 0

        # Latency tracking
        self._get_times: list[float] = []
        self._set_times: list[float] = []
        self._max_latency_samples = 1000

        # History
        self._snapshots: list[CacheMetricsSnapshot] = []

        # Custom metrics
        self._custom_counters: dict[str, int] = defaultdict(int)
        self._custom_gauges: dict[str, float] = {}
        self._custom_histograms: dict[str, list[float]] = defaultdict(list)

        # Background task
        self._task: asyncio.Task | None = None
        self._running = False

    async def start(self) -> None:
        """Start background metrics collection."""
        self._running = True
        self._task = asyncio.create_task(self._collection_loop())
        logger.info("Metrics collector started (interval=%.1fs)", self.collection_interval)

    async def stop(self) -> None:
        """Stop background metrics collection."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Metrics collector stopped")

    async def _collection_loop(self) -> None:
        """Background loop to collect metrics periodically."""
        while self._running:
            try:
                await asyncio.sleep(self.collection_interval)
                snapshot = await self.collect_snapshot()
                self._snapshots.append(snapshot)
                if len(self._snapshots) > self.max_history:
                    self._snapshots = self._snapshots[-self.max_history:]
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error collecting metrics: %s", e)

    async def collect_snapshot(self) -> CacheMetricsSnapshot:
        """Collect a metrics snapshot from the cache backend."""
        try:
            stats = await self.cache.get_stats()
        except Exception:
            stats = {}

        total_ops = self._hits + self._misses
        hit_rate = self._hits / total_ops if total_ops > 0 else 0.0

        avg_get = (
            sum(self._get_times) / len(self._get_times)
            if self._get_times
            else 0.0
        )
        avg_set = (
            sum(self._set_times) / len(self._set_times)
            if self._set_times
            else 0.0
        )

        # Calculate operations per second
        ops_per_sec = 0.0
        if len(self._snapshots) >= 2:
            time_diff = self._snapshots[-1].timestamp - self._snapshots[-2].timestamp
            if time_diff > 0:
                ops_diff = total_ops - (
                    self._snapshots[-1].hits + self._snapshots[-1].misses
                )
                ops_per_sec = ops_diff / time_diff

        error_rate = self._errors / total_ops if total_ops > 0 else 0.0

        return CacheMetricsSnapshot(
            timestamp=time.time(),
            hits=self._hits,
            misses=self._misses,
            hit_rate=hit_rate,
            sets=self._sets,
            deletes=self._deletes,
            evictions=self._evictions,
            expirations=self._expirations,
            total_entries=stats.get("entry_count", 0),
            memory_usage_bytes=stats.get("total_size_bytes", 0),
            avg_get_time_ms=avg_get,
            avg_set_time_ms=avg_set,
            operations_per_second=ops_per_sec,
            error_count=self._errors,
            error_rate=error_rate,
            connection_status="connected" if self.cache._is_connected() else "disconnected",
            custom_metrics=dict(self._custom_gauges),
        )

    def record_hit(self) -> None:
        """Record a cache hit."""
        self._hits += 1

    def record_miss(self) -> None:
        """Record a cache miss."""
        self._misses += 1

    def record_set(self) -> None:
        """Record a cache set operation."""
        self._sets += 1

    def record_delete(self) -> None:
        """Record a cache delete operation."""
        self._deletes += 1

    def record_error(self) -> None:
        """Record a cache error."""
        self._errors += 1

    def record_eviction(self) -> None:
        """Record a cache eviction."""
        self._evictions += 1

    def record_expiration(self) -> None:
        """Record a cache expiration."""
        self._expirations += 1

    def record_get_time(self, duration_ms: float) -> None:
        """Record a get operation latency."""
        self._get_times.append(duration_ms)
        if len(self._get_times) > self._max_latency_samples:
            self._get_times = self._get_times[-self._max_latency_samples:]

    def record_set_time(self, duration_ms: float) -> None:
        """Record a set operation latency."""
        self._set_times.append(duration_ms)
        if len(self._set_times) > self._max_latency_samples:
            self._set_times = self._set_times[-self._max_latency_samples:]

    def increment_counter(self, name: str, value: int = 1) -> None:
        """Increment a custom counter."""
        self._custom_counters[name] += value

    def set_gauge(self, name: str, value: float) -> None:
        """Set a custom gauge value."""
        self._custom_gauges[name] = value

    def record_histogram(self, name: str, value: float) -> None:
        """Record a value in a custom histogram."""
        self._custom_histograms[name].append(value)
        if len(self._custom_histograms[name]) > self._max_latency_samples:
            self._custom_histograms[name] = self._custom_histograms[name][-self._max_latency_samples:]

    def get_latency_percentiles(self, operation: str = "get") -> dict[str, float]:
        """Calculate latency percentiles."""
        times = self._get_times if operation == "get" else self._set_times
        if not times:
            return {"p50": 0, "p90": 0, "p95": 0, "p99": 0, "p999": 0}

        sorted_times = sorted(times)
        n = len(sorted_times)

        def percentile(p: float) -> float:
            idx = int(n * p / 100)
            return sorted_times[min(idx, n - 1)]

        return {
            "p50": percentile(50),
            "p90": percentile(90),
            "p95": percentile(95),
            "p99": percentile(99),
            "p999": percentile(99.9),
        }

    def get_snapshot(self) -> CacheMetricsSnapshot | None:
        """Get the most recent metrics snapshot."""
        return self._snapshots[-1] if self._snapshots else None

    def get_history(
        self,
        limit: int = 100,
        since: float | None = None,
    ) -> list[CacheMetricsSnapshot]:
        """Get historical metrics snapshots."""
        snapshots = self._snapshots
        if since:
            snapshots = [s for s in snapshots if s.timestamp >= since]
        return snapshots[-limit:]

    def reset(self) -> None:
        """Reset all metrics."""
        self._hits = 0
        self._misses = 0
        self._sets = 0
        self._deletes = 0
        self._errors = 0
        self._evictions = 0
        self._expirations = 0
        self._get_times.clear()
        self._set_times.clear()
        self._custom_counters.clear()
        self._custom_gauges.clear()
        self._custom_histograms.clear()


class HealthMonitor:
    """
    Monitors cache health and generates alerts.

    Tracks connection status, hit rates, memory usage,
    and other health indicators with configurable thresholds.
    """

    def __init__(
        self,
        cache: CacheBackend,
        check_interval: float = 30.0,
    ):
        self.cache = cache
        self.check_interval = check_interval
        self._alert_rules: list[AlertRule] = []
        self._alerts: list[Alert] = []
        self._max_alerts = 1000
        self._task: asyncio.Task | None = None
        self._running = False
        self._alert_handlers: list[Callable[[Alert], None]] = []

        # Default alert rules
        self._setup_default_rules()

    def _setup_default_rules(self) -> None:
        """Set up default alert rules."""
        self.add_alert_rule(AlertRule(
            name="low_hit_rate",
            metric_name="hit_rate",
            condition="<",
            threshold=0.5,
            severity=AlertSeverity.WARNING,
            message="Cache hit rate is below 50%",
        ))
        self.add_alert_rule(AlertRule(
            name="high_error_rate",
            metric_name="error_rate",
            condition=">",
            threshold=0.1,
            severity=AlertSeverity.CRITICAL,
            message="Cache error rate is above 10%",
        ))
        self.add_alert_rule(AlertRule(
            name="high_eviction_rate",
            metric_name="evictions",
            condition=">",
            threshold=100,
            severity=AlertSeverity.WARNING,
            message="High cache eviction rate detected",
        ))
        self.add_alert_rule(AlertRule(
            name="high_latency",
            metric_name="avg_get_time_ms",
            condition=">",
            threshold=100.0,
            severity=AlertSeverity.WARNING,
            message="Cache get latency is above 100ms",
        ))
        self.add_alert_rule(AlertRule(
            name="cache_disconnected",
            metric_name="connection_status",
            condition="==",
            threshold=0,  # Will compare as string
            severity=AlertSeverity.CRITICAL,
            message="Cache is disconnected",
        ))

    async def start(self) -> None:
        """Start health monitoring."""
        self._running = True
        self._task = asyncio.create_task(self._monitoring_loop())
        logger.info("Health monitor started (interval=%.1fs)", self.check_interval)

    async def stop(self) -> None:
        """Stop health monitoring."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Health monitor stopped")

    async def _monitoring_loop(self) -> None:
        """Background loop to check cache health."""
        while self._running:
            try:
                await asyncio.sleep(self.check_interval)
                await self._check_health()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in health monitoring: %s", e)

    async def _check_health(self) -> None:
        """Check cache health and evaluate alert rules."""
        try:
            health = await self.cache.health_check()
        except Exception as e:
            logger.error("Health check failed: %s", e)
            health = {"status": "error", "error": str(e)}

        # Build metrics dict for rule evaluation
        metrics: dict[str, float] = {
            "hit_rate": health.get("hit_rate", 0.0),
            "error_rate": health.get("error_rate", 0.0),
            "evictions": float(health.get("evictions", 0)),
            "avg_get_time_ms": health.get("avg_get_time_ms", 0.0),
            "avg_set_time_ms": health.get("avg_set_time_ms", 0.0),
            "memory_usage_bytes": float(health.get("used_memory_human", "0")
                                        .replace("M", "000000")
                                        .replace("G", "000000000")
                                        .replace("K", "000")
                                        .replace("B", "")
                                        or 0),
        }

        # Evaluate alert rules
        for rule in self._alert_rules:
            if not rule.enabled:
                continue

            value = metrics.get(rule.metric_name)
            if value is None:
                continue

            if rule.evaluate(value) and rule.can_trigger():
                alert = Alert(
                    alert_id=f"{rule.name}_{int(time.time())}",
                    name=rule.name,
                    severity=rule.severity,
                    message=rule.message,
                    metric_name=rule.metric_name,
                    threshold=rule.threshold,
                    current_value=value,
                )
                self._alerts.append(alert)
                if len(self._alerts) > self._max_alerts:
                    self._alerts = self._alerts[-self._max_alerts:]

                rule.mark_triggered()
                logger.warning("Alert triggered: %s (value=%.2f, threshold=%.2f)",
                              rule.name, value, rule.threshold)

                # Notify handlers
                for handler in self._alert_handlers:
                    try:
                        handler(alert)
                    except Exception as e:
                        logger.error("Alert handler error: %s", e)

    def add_alert_rule(self, rule: AlertRule) -> None:
        """Add an alert rule."""
        self._alert_rules.append(rule)

    def remove_alert_rule(self, name: str) -> bool:
        """Remove an alert rule by name."""
        for i, rule in enumerate(self._alert_rules):
            if rule.name == name:
                self._alert_rules.pop(i)
                return True
        return False

    def add_alert_handler(self, handler: Callable[[Alert], None]) -> None:
        """Add an alert handler callback."""
        self._alert_handlers.append(handler)

    def get_alerts(
        self,
        limit: int = 100,
        severity: AlertSeverity | None = None,
        acknowledged: bool | None = None,
    ) -> list[Alert]:
        """Get alerts with optional filtering."""
        alerts = self._alerts
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        if acknowledged is not None:
            alerts = [a for a in alerts if a.acknowledged == acknowledged]
        return alerts[-limit:]

    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert."""
        for alert in self._alerts:
            if alert.alert_id == alert_id:
                alert.acknowledged = True
                return True
        return False

    def clear_alerts(self) -> None:
        """Clear all alerts."""
        self._alerts.clear()

    async def get_health_status(self) -> dict[str, Any]:
        """Get current health status."""
        try:
            return await self.cache.health_check()
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "connected": False,
            }


class PrometheusExporter:
    """
    Exports cache metrics in Prometheus format.

    Generates text-based metrics output compatible with
    Prometheus scraping.
    """

    def __init__(self, collector: MetricsCollector):
        self.collector = collector

    def export(self) -> str:
        """Export metrics in Prometheus text format."""
        snapshot = self.collector.get_snapshot()
        if snapshot is None:
            return "# No metrics available\n"

        lines: list[str] = []

        # Hit rate
        lines.append("# HELP grcclaw_cache_hit_rate Cache hit rate")
        lines.append("# TYPE grcclaw_cache_hit_rate gauge")
        lines.append(f"grcclaw_cache_hit_rate {snapshot.hit_rate:.4f}")

        # Hits
        lines.append("# HELP grcclaw_cache_hits_total Total cache hits")
        lines.append("# TYPE grcclaw_cache_hits_total counter")
        lines.append(f"grcclaw_cache_hits_total {snapshot.hits}")

        # Misses
        lines.append("# HELP grcclaw_cache_misses_total Total cache misses")
        lines.append("# TYPE grcclaw_cache_misses_total counter")
        lines.append(f"grcclaw_cache_misses_total {snapshot.misses}")

        # Sets
        lines.append("# HELP grcclaw_cache_sets_total Total cache sets")
        lines.append("# TYPE grcclaw_cache_sets_total counter")
        lines.append(f"grcclaw_cache_sets_total {snapshot.sets}")

        # Deletes
        lines.append("# HELP grcclaw_cache_deletes_total Total cache deletes")
        lines.append("# TYPE grcclaw_cache_deletes_total counter")
        lines.append(f"grcclaw_cache_deletes_total {snapshot.deletes}")

        # Evictions
        lines.append("# HELP grcclaw_cache_evictions_total Total cache evictions")
        lines.append("# TYPE grcclaw_cache_evictions_total counter")
        lines.append(f"grcclaw_cache_evictions_total {snapshot.evictions}")

        # Expirations
        lines.append("# HELP grcclaw_cache_expirations_total Total cache expirations")
        lines.append("# TYPE grcclaw_cache_expirations_total counter")
        lines.append(f"grcclaw_cache_expirations_total {snapshot.expirations}")

        # Total entries
        lines.append("# HELP grcclaw_cache_entries Current number of cache entries")
        lines.append("# TYPE grcclaw_cache_entries gauge")
        lines.append(f"grcclaw_cache_entries {snapshot.total_entries}")

        # Memory usage
        lines.append("# HELP grcclaw_cache_memory_usage_bytes Cache memory usage in bytes")
        lines.append("# TYPE grcclaw_cache_memory_usage_bytes gauge")
        lines.append(f"grcclaw_cache_memory_usage_bytes {snapshot.memory_usage_bytes}")

        # Average get time
        lines.append("# HELP grcclaw_cache_avg_get_time_ms Average get operation time in ms")
        lines.append("# TYPE grcclaw_cache_avg_get_time_ms gauge")
        lines.append(f"grcclaw_cache_avg_get_time_ms {snapshot.avg_get_time_ms:.4f}")

        # Average set time
        lines.append("# HELP grcclaw_cache_avg_set_time_ms Average set operation time in ms")
        lines.append("# TYPE grcclaw_cache_avg_set_time_ms gauge")
        lines.append(f"grcclaw_cache_avg_set_time_ms {snapshot.avg_set_time_ms:.4f}")

        # Operations per second
        lines.append("# HELP grcclaw_cache_operations_per_second Cache operations per second")
        lines.append("# TYPE grcclaw_cache_operations_per_second gauge")
        lines.append(f"grcclaw_cache_operations_per_second {snapshot.operations_per_second:.4f}")

        # Error count
        lines.append("# HELP grcclaw_cache_errors_total Total cache errors")
        lines.append("# TYPE grcclaw_cache_errors_total counter")
        lines.append(f"grcclaw_cache_errors_total {snapshot.error_count}")

        # Error rate
        lines.append("# HELP grcclaw_cache_error_rate Cache error rate")
        lines.append("# TYPE grcclaw_cache_error_rate gauge")
        lines.append(f"grcclaw_cache_error_rate {snapshot.error_rate:.4f}")

        # Connection status
        lines.append("# HELP grcclaw_cache_connected Cache connection status (1=connected, 0=disconnected)")
        lines.append("# TYPE grcclaw_cache_connected gauge")
        connected = 1 if snapshot.connection_status == "connected" else 0
        lines.append(f"grcclaw_cache_connected {connected}")

        # Latency percentiles
        for op in ["get", "set"]:
            percentiles = self.collector.get_latency_percentiles(op)
            for pct, value in percentiles.items():
                lines.append(f"# HELP grcclaw_cache_{op}_latency_{pct}_ms {op} latency {pct} percentile in ms")
                lines.append(f"# TYPE grcclaw_cache_{op}_latency_{pct}_ms gauge")
                lines.append(f"grcclaw_cache_{op}_latency_{pct}_ms {value:.4f}")

        # Custom metrics
        for name, value in snapshot.custom_metrics.items():
            safe_name = name.replace(".", "_").replace("-", "_")
            lines.append(f"# HELP grcclaw_cache_custom_{safe_name} Custom metric: {name}")
            lines.append(f"# TYPE grcclaw_cache_custom_{safe_name} gauge")
            lines.append(f"grcclaw_cache_custom_{safe_name} {value}")

        return "\n".join(lines) + "\n"

    def export_json(self) -> dict[str, Any]:
        """Export metrics as a JSON-compatible dict."""
        snapshot = self.collector.get_snapshot()
        if snapshot is None:
            return {}

        return {
            "timestamp": snapshot.timestamp,
            "hit_rate": snapshot.hit_rate,
            "hits": snapshot.hits,
            "misses": snapshot.misses,
            "sets": snapshot.sets,
            "deletes": snapshot.deletes,
            "evictions": snapshot.evictions,
            "expirations": snapshot.expirations,
            "total_entries": snapshot.total_entries,
            "memory_usage_bytes": snapshot.memory_usage_bytes,
            "avg_get_time_ms": snapshot.avg_get_time_ms,
            "avg_set_time_ms": snapshot.avg_set_time_ms,
            "operations_per_second": snapshot.operations_per_second,
            "error_count": snapshot.error_count,
            "error_rate": snapshot.error_rate,
            "connection_status": snapshot.connection_status,
            "custom_metrics": snapshot.custom_metrics,
            "latency_percentiles": {
                "get": self.collector.get_latency_percentiles("get"),
                "set": self.collector.get_latency_percentiles("set"),
            },
        }


class CacheMonitor:
    """
    Unified cache monitoring facade.

    Combines metrics collection, health monitoring, and
    alerting into a single easy-to-use interface.
    """

    def __init__(
        self,
        cache: CacheBackend,
        collection_interval: float = 10.0,
        health_check_interval: float = 30.0,
        enable_prometheus: bool = True,
    ):
        self.cache = cache
        self.metrics = MetricsCollector(cache, collection_interval)
        self.health = HealthMonitor(cache, health_check_interval)
        self.prometheus = PrometheusExporter(self.metrics) if enable_prometheus else None

    async def start(self) -> None:
        """Start all monitoring components."""
        await self.metrics.start()
        await self.health.start()
        logger.info("Cache monitor started")

    async def stop(self) -> None:
        """Stop all monitoring components."""
        await self.metrics.stop()
        await self.health.stop()
        logger.info("Cache monitor stopped")

    async def get_status(self) -> dict[str, Any]:
        """Get comprehensive cache status."""
        health = await self.health.get_health_status()
        snapshot = self.metrics.get_snapshot()

        return {
            "health": health,
            "metrics": {
                "hit_rate": snapshot.hit_rate if snapshot else 0.0,
                "total_entries": snapshot.total_entries if snapshot else 0,
                "memory_usage_bytes": snapshot.memory_usage_bytes if snapshot else 0,
                "operations_per_second": snapshot.operations_per_second if snapshot else 0.0,
                "error_rate": snapshot.error_rate if snapshot else 0.0,
            },
            "alerts": {
                "total": len(self.health.get_alerts(limit=1000)),
                "unacknowledged": len(self.health.get_alerts(limit=1000, acknowledged=False)),
                "critical": len(self.health.get_alerts(limit=1000, severity=AlertSeverity.CRITICAL)),
            },
        }

    def record_hit(self) -> None:
        self.metrics.record_hit()

    def record_miss(self) -> None:
        self.metrics.record_miss()

    def record_set(self) -> None:
        self.metrics.record_set()

    def record_delete(self) -> None:
        self.metrics.record_delete()

    def record_error(self) -> None:
        self.metrics.record_error()

    def record_get_time(self, duration_ms: float) -> None:
        self.metrics.record_get_time(duration_ms)

    def record_set_time(self, duration_ms: float) -> None:
        self.metrics.record_set_time(duration_ms)

    def increment_counter(self, name: str, value: int = 1) -> None:
        self.metrics.increment_counter(name, value)

    def set_gauge(self, name: str, value: float) -> None:
        self.metrics.set_gauge(name, value)

    def get_prometheus_metrics(self) -> str:
        """Get Prometheus-formatted metrics."""
        if self.prometheus:
            return self.prometheus.export()
        return "# Prometheus export not enabled\n"

    def get_json_metrics(self) -> dict[str, Any]:
        """Get JSON-formatted metrics."""
        if self.prometheus:
            return self.prometheus.export_json()
        return {}
