"""
Integration Monitoring — health checks, metrics, alerting, and tracing.

Provides:
- HealthChecker: periodic health checks for integrations
- IntegrationMetrics: collects and aggregates metrics
- AlertManager: manages alert rules and notifications
- IntegrationTracer: traces integration execution with spans
- HealthStatus / AlertSeverity: status and severity enums
"""

from __future__ import annotations

import json
import logging
import statistics
import threading
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Optional

from .sdk.base import BaseConnector
from .sdk.types import ConnectorStatus

logger = logging.getLogger(__name__)


class HealthStatus(str, Enum):
    """Health status of an integration."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class AlertSeverity(str, Enum):
    """Severity levels for alerts."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class HealthCheckResult:
    """Result of a health check."""

    integration_name: str
    status: HealthStatus
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    response_time_ms: float = 0.0
    message: str = ""
    details: dict[str, Any] = field(default_factory=dict)
    consecutive_failures: int = 0

    @property
    def is_healthy(self) -> bool:
        return self.status == HealthStatus.HEALTHY


@dataclass
class MetricPoint:
    """A single metric data point."""

    name: str
    value: float
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    labels: dict[str, str] = field(default_factory=dict)
    unit: str = ""


@dataclass
class Alert:
    """An alert instance."""

    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    severity: AlertSeverity = AlertSeverity.WARNING
    message: str = ""
    integration_name: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    acknowledged: bool = False
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def acknowledge(self) -> None:
        self.acknowledged = True

    def resolve(self) -> None:
        self.resolved = True
        self.resolved_at = datetime.now(timezone.utc)


@dataclass
class AlertRule:
    """A rule that triggers alerts."""

    name: str
    integration_name: str
    metric: str
    condition: str  # "gt", "lt", "eq", "gte", "lte", "change_pct"
    threshold: float
    severity: AlertSeverity = AlertSeverity.WARNING
    cooldown_seconds: float = 300.0
    enabled: bool = True
    _last_triggered: float = 0.0
    _last_value: float = 0.0

    def should_trigger(self, value: float) -> bool:
        """Check if the rule should trigger for the given value."""
        if not self.enabled:
            return False

        now = time.time()
        if now - self._last_triggered < self.cooldown_seconds:
            return False

        triggered = False
        if self.condition == "gt":
            triggered = value > self.threshold
        elif self.condition == "lt":
            triggered = value < self.threshold
        elif self.condition == "eq":
            triggered = value == self.threshold
        elif self.condition == "gte":
            triggered = value >= self.threshold
        elif self.condition == "lte":
            triggered = value <= self.threshold
        elif self.condition == "change_pct":
            if self._last_value != 0:
                pct_change = abs((value - self._last_value) / self._last_value) * 100
                triggered = pct_change > self.threshold
            self._last_value = value

        if triggered:
            self._last_triggered = now

        return triggered


@dataclass
class Span:
    """A trace span."""

    trace_id: str
    span_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    parent_span_id: Optional[str] = None
    name: str = ""
    start_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    end_time: Optional[datetime] = None
    duration_ms: float = 0.0
    status: str = "ok"  # ok, error
    attributes: dict[str, Any] = field(default_factory=dict)
    events: list[dict[str, Any]] = field(default_factory=list)

    def set_attribute(self, key: str, value: Any) -> None:
        self.attributes[key] = value

    def add_event(self, name: str, attributes: dict[str, Any] | None = None) -> None:
        self.events.append({
            "name": name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "attributes": attributes or {},
        })

    def finish(self, status: str = "ok") -> None:
        self.end_time = datetime.now(timezone.utc)
        self.duration_ms = (self.end_time - self.start_time).total_seconds() * 1000
        self.status = status


@dataclass
class Trace:
    """A complete trace consisting of multiple spans."""

    trace_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    spans: list[Span] = field(default_factory=list)
    start_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    end_time: Optional[datetime] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_span(self, span: Span) -> None:
        self.spans.append(span)

    def finish(self) -> None:
        self.end_time = datetime.now(timezone.utc)

    @property
    def duration_ms(self) -> float:
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds() * 1000
        return 0.0

    @property
    def span_count(self) -> int:
        return len(self.spans)

    def to_dict(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_ms": self.duration_ms,
            "span_count": self.span_count,
            "spans": [
                {
                    "span_id": s.span_id,
                    "parent_span_id": s.parent_span_id,
                    "name": s.name,
                    "start_time": s.start_time.isoformat(),
                    "end_time": s.end_time.isoformat() if s.end_time else None,
                    "duration_ms": s.duration_ms,
                    "status": s.status,
                    "attributes": s.attributes,
                    "events": s.events,
                }
                for s in self.spans
            ],
            "metadata": self.metadata,
        }


class HealthChecker:
    """
    Periodic health checker for integrations.

    Runs health checks on a schedule and tracks consecutive failures.
    """

    def __init__(
        self,
        check_interval_seconds: float = 60.0,
        failure_threshold: int = 3,
        recovery_threshold: int = 2,
    ):
        self.check_interval_seconds = check_interval_seconds
        self.failure_threshold = failure_threshold
        self.recovery_threshold = recovery_threshold
        self._checks: dict[str, Callable[[], HealthCheckResult]] = {}
        self._results: dict[str, HealthCheckResult] = {}
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._on_status_change: Optional[Callable[[str, HealthStatus, HealthStatus], None]] = None

    def register(
        self,
        name: str,
        check_func: Callable[[], HealthCheckResult],
    ) -> None:
        """Register a health check function."""
        with self._lock:
            self._checks[name] = check_func
        logger.info("Registered health check for '%s'", name)

    def register_connector(self, connector: BaseConnector) -> None:
        """Register a connector for health checking."""
        self.register(
            connector.config.name,
            lambda: self._check_connector(connector),
        )

    def unregister(self, name: str) -> bool:
        """Unregister a health check."""
        with self._lock:
            if name in self._checks:
                del self._checks[name]
                self._results.pop(name, None)
                return True
        return False

    def check(self, name: str) -> Optional[HealthCheckResult]:
        """Run a single health check."""
        check_func = self._checks.get(name)
        if not check_func:
            return None

        start = time.monotonic()
        try:
            result = check_func()
            result.response_time_ms = (time.monotonic() - start) * 1000
        except Exception as e:
            result = HealthCheckResult(
                integration_name=name,
                status=HealthStatus.UNHEALTHY,
                response_time_ms=(time.monotonic() - start) * 1000,
                message=str(e),
            )

        with self._lock:
            previous = self._results.get(name)
            if previous and previous.status != result.status:
                if self._on_status_change:
                    self._on_status_change(name, previous.status, result.status)
            self._results[name] = result

        return result

    def check_all(self) -> dict[str, HealthCheckResult]:
        """Run all registered health checks."""
        results = {}
        with self._lock:
            names = list(self._checks.keys())
        for name in names:
            results[name] = self.check(name)
        return results

    def get_status(self, name: str) -> Optional[HealthCheckResult]:
        """Get the last health check result for an integration."""
        return self._results.get(name)

    def get_all_status(self) -> dict[str, HealthCheckResult]:
        """Get all last health check results."""
        with self._lock:
            return dict(self._results)

    def start(self) -> None:
        """Start periodic health checking."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        logger.info("Health checker started (interval=%.0fs)", self.check_interval_seconds)

    def stop(self) -> None:
        """Stop periodic health checking."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("Health checker stopped")

    def on_status_change(
        self,
        callback: Callable[[str, HealthStatus, HealthStatus], None],
    ) -> None:
        """Set a callback for status changes."""
        self._on_status_change = callback

    def _run_loop(self) -> None:
        """Main health check loop."""
        while self._running:
            self.check_all()
            time.sleep(self.check_interval_seconds)

    def _check_connector(self, connector: BaseConnector) -> HealthCheckResult:
        """Health check for a connector."""
        start = time.monotonic()
        try:
            health = connector.health_check()
            response_time_ms = (time.monotonic() - start) * 1000

            status = HealthStatus.HEALTHY if health.get("healthy") else HealthStatus.UNHEALTHY
            if health.get("error_rate", 0) > 0.1:
                status = HealthStatus.DEGRADED

            return HealthCheckResult(
                integration_name=connector.config.name,
                status=status,
                response_time_ms=response_time_ms,
                message="OK" if status == HealthStatus.HEALTHY else health.get("error", ""),
                details=health,
            )
        except Exception as e:
            return HealthCheckResult(
                integration_name=connector.config.name,
                status=HealthStatus.UNHEALTHY,
                response_time_ms=(time.monotonic() - start) * 1000,
                message=str(e),
            )


class IntegrationMetrics:
    """
    Collects and aggregates integration metrics.

    Tracks:
    - Request counts (total, success, error)
    - Latency (min, max, avg, p50, p95, p99)
    - Error rates
    - Throughput
    - Custom metrics
    """

    def __init__(self, max_history: int = 10000):
        self.max_history = max_history
        self._metrics: dict[str, list[MetricPoint]] = defaultdict(list)
        self._counters: dict[str, int] = defaultdict(int)
        self._gauges: dict[str, float] = {}
        self._lock = threading.Lock()

    def record(
        self,
        name: str,
        value: float,
        *,
        labels: dict[str, str] | None = None,
        unit: str = "",
    ) -> None:
        """Record a metric data point."""
        point = MetricPoint(
            name=name,
            value=value,
            labels=labels or {},
            unit=unit,
        )
        with self._lock:
            self._metrics[name].append(point)
            if len(self._metrics[name]) > self.max_history:
                self._metrics[name] = self._metrics[name][-self.max_history:]

    def increment(self, name: str, value: int = 1, labels: dict[str, str] | None = None) -> None:
        """Increment a counter metric."""
        with self._lock:
            self._counters[name] += value
        self.record(name, float(value), labels=labels)

    def gauge(self, name: str, value: float, labels: dict[str, str] | None = None) -> None:
        """Set a gauge metric."""
        with self._lock:
            self._gauges[name] = value
        self.record(name, value, labels=labels)

    def record_request(
        self,
        integration_name: str,
        *,
        success: bool,
        latency_ms: float,
        status_code: int | None = None,
    ) -> None:
        """Record a request metric."""
        labels = {"integration": integration_name}
        if status_code:
            labels["status_code"] = str(status_code)

        self.increment("requests_total", labels=labels)
        self.increment("requests_success" if success else "requests_error", labels=labels)
        self.record("request_latency_ms", latency_ms, labels=labels, unit="ms")

    def get_metrics(
        self,
        name: str,
        *,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> list[MetricPoint]:
        """Get metric data points, optionally filtered by time range."""
        with self._lock:
            points = list(self._metrics.get(name, []))

        if start_time:
            points = [p for p in points if p.timestamp >= start_time]
        if end_time:
            points = [p for p in points if p.timestamp <= end_time]

        return points

    def get_statistics(self, name: str) -> dict[str, float]:
        """Get statistical summary for a metric."""
        points = self.get_metrics(name)
        if not points:
            return {"count": 0, "min": 0, "max": 0, "avg": 0, "p50": 0, "p95": 0, "p99": 0}

        values = [p.value for p in points]
        sorted_values = sorted(values)

        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "avg": statistics.mean(values),
            "p50": self._percentile(sorted_values, 50),
            "p95": self._percentile(sorted_values, 95),
            "p99": self._percentile(sorted_values, 99),
        }

    def get_counter(self, name: str) -> int:
        """Get a counter value."""
        with self._lock:
            return self._counters.get(name, 0)

    def get_gauge(self, name: str) -> float:
        """Get a gauge value."""
        with self._lock:
            return self._gauges.get(name, 0.0)

    def get_all_names(self) -> list[str]:
        """Get all metric names."""
        with self._lock:
            return list(self._metrics.keys())

    def clear(self, name: str | None = None) -> None:
        """Clear metrics. If name is None, clear all."""
        with self._lock:
            if name:
                self._metrics.pop(name, None)
                self._counters.pop(name, None)
                self._gauges.pop(name, None)
            else:
                self._metrics.clear()
                self._counters.clear()
                self._gauges.clear()

    def _percentile(self, sorted_values: list[float], p: float) -> float:
        """Calculate percentile from sorted values."""
        if not sorted_values:
            return 0.0
        k = (len(sorted_values) - 1) * (p / 100.0)
        f = int(k)
        c = f + 1 if f + 1 < len(sorted_values) else f
        d = k - f
        return sorted_values[f] + d * (sorted_values[c] - sorted_values[f])


class AlertManager:
    """
    Manages alert rules and alert instances.

    Provides:
    - Alert rule registration
    - Alert triggering based on metric thresholds
    - Alert lifecycle (fire, acknowledge, resolve)
    - Notification dispatch
    """

    def __init__(self):
        self._rules: dict[str, AlertRule] = {}
        self._alerts: dict[str, Alert] = {}
        self._handlers: list[Callable[[Alert], None]] = []
        self._lock = threading.Lock()

    def add_rule(self, rule: AlertRule) -> None:
        """Add an alert rule."""
        with self._lock:
            self._rules[rule.name] = rule
        logger.info("Added alert rule '%s'", rule.name)

    def remove_rule(self, name: str) -> bool:
        """Remove an alert rule."""
        with self._lock:
            return self._rules.pop(name, None) is not None

    def enable_rule(self, name: str) -> bool:
        """Enable an alert rule."""
        with self._lock:
            if name in self._rules:
                self._rules[name].enabled = True
                return True
        return False

    def disable_rule(self, name: str) -> bool:
        """Disable an alert rule."""
        with self._lock:
            if name in self._rules:
                self._rules[name].enabled = False
                return True
        return False

    def check_metric(
        self,
        integration_name: str,
        metric_name: str,
        value: float,
    ) -> list[Alert]:
        """
        Check a metric against all applicable rules.

        Returns:
            List of triggered alerts.
        """
        triggered = []
        with self._lock:
            rules = list(self._rules.values())

        for rule in rules:
            if rule.integration_name != integration_name:
                continue
            if rule.metric != metric_name:
                continue

            if rule.should_trigger(value):
                alert = Alert(
                    name=rule.name,
                    severity=rule.severity,
                    message=f"Alert '{rule.name}': {metric_name} = {value} (threshold: {rule.condition} {rule.threshold})",
                    integration_name=integration_name,
                    metadata={
                        "metric": metric_name,
                        "value": value,
                        "condition": rule.condition,
                        "threshold": rule.threshold,
                    },
                )
                with self._lock:
                    self._alerts[alert.id] = alert
                triggered.append(alert)
                self._dispatch(alert)

        return triggered

    def fire_alert(
        self,
        name: str,
        severity: AlertSeverity,
        message: str,
        integration_name: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> Alert:
        """Manually fire an alert."""
        alert = Alert(
            name=name,
            severity=severity,
            message=message,
            integration_name=integration_name,
            metadata=metadata or {},
        )
        with self._lock:
            self._alerts[alert.id] = alert
        self._dispatch(alert)
        return alert

    def acknowledge(self, alert_id: str) -> bool:
        """Acknowledge an alert."""
        with self._lock:
            if alert_id in self._alerts:
                self._alerts[alert_id].acknowledge()
                return True
        return False

    def resolve(self, alert_id: str) -> bool:
        """Resolve an alert."""
        with self._lock:
            if alert_id in self._alerts:
                self._alerts[alert_id].resolve()
                return True
        return False

    def get_alert(
        self,
        alert_id: str,
        *,
        include_resolved: bool = True,
    ) -> Optional[Alert]:
        """Get an alert by ID."""
        with self._lock:
            alert = self._alerts.get(alert_id)
            if alert and (include_resolved or not alert.resolved):
                return alert
        return None

    def get_alerts(
        self,
        *,
        integration_name: str | None = None,
        severity: AlertSeverity | None = None,
        acknowledged: bool | None = None,
        resolved: bool | None = None,
        limit: int = 100,
    ) -> list[Alert]:
        """Get alerts with optional filters."""
        with self._lock:
            alerts = list(self._alerts.values())

        if integration_name:
            alerts = [a for a in alerts if a.integration_name == integration_name]
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        if acknowledged is not None:
            alerts = [a for a in alerts if a.acknowledged == acknowledged]
        if resolved is not None:
            alerts = [a for a in alerts if a.resolved == resolved]

        return sorted(alerts, key=lambda a: a.timestamp, reverse=True)[:limit]

    def add_handler(self, handler: Callable[[Alert], None]) -> None:
        """Add an alert notification handler."""
        self._handlers.append(handler)

    def remove_handler(self, handler: Callable[[Alert], None]) -> bool:
        """Remove an alert notification handler."""
        if handler in self._handlers:
            self._handlers.remove(handler)
            return True
        return False

    def _dispatch(self, alert: Alert) -> None:
        """Dispatch an alert to all handlers."""
        for handler in self._handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error("Alert handler failed: %s", e)

    def clear_resolved(self) -> int:
        """Clear all resolved alerts. Returns count cleared."""
        with self._lock:
            to_remove = [aid for aid, a in self._alerts.items() if a.resolved]
            for aid in to_remove:
                del self._alerts[aid]
            return len(to_remove)


class IntegrationTracer:
    """
    Traces integration execution with distributed-tracing-style spans.

    Provides:
    - Span creation and management
    - Trace context propagation
    - Trace export (JSON, in-memory)
    """

    def __init__(self, max_traces: int = 1000):
        self.max_traces = max_traces
        self._traces: dict[str, Trace] = {}
        self._active_spans: dict[str, Span] = {}
        self._lock = threading.Lock()

    def start_trace(
        self,
        name: str,
        *,
        metadata: dict[str, Any] | None = None,
    ) -> Trace:
        """Start a new trace."""
        trace = Trace(metadata=metadata or {})
        with self._lock:
            self._traces[trace.trace_id] = trace
            if len(self._traces) > self.max_traces:
                # Remove oldest
                oldest = min(self._traces.values(), key=lambda t: t.start_time)
                del self._traces[oldest.trace_id]
        return trace

    def start_span(
        self,
        name: str,
        *,
        trace_id: Optional[str] = None,
        parent_span_id: Optional[str] = None,
        attributes: dict[str, Any] | None = None,
    ) -> Span:
        """Start a new span."""
        if not trace_id:
            # Find or create a trace
            with self._lock:
                if self._traces:
                    trace_id = list(self._traces.keys())[-1]
                else:
                    trace = Trace()
                    self._traces[trace.trace_id] = trace
                    trace_id = trace.trace_id

        span = Span(
            trace_id=trace_id,
            parent_span_id=parent_span_id,
            name=name,
            attributes=attributes or {},
        )

        with self._lock:
            self._active_spans[span.span_id] = span
            trace = self._traces.get(trace_id)
            if trace:
                trace.add_span(span)

        return span

    def finish_span(
        self,
        span_id: str,
        *,
        status: str = "ok",
    ) -> Optional[Span]:
        """Finish a span."""
        with self._lock:
            span = self._active_spans.pop(span_id, None)
        if span:
            span.finish(status)
        return span

    def finish_trace(self, trace_id: str) -> Optional[Trace]:
        """Finish a trace."""
        with self._lock:
            trace = self._traces.get(trace_id)
            if trace:
                trace.finish()
            return trace

    def get_trace(self, trace_id: str) -> Optional[Trace]:
        """Get a trace by ID."""
        return self._traces.get(trace_id)

    def get_traces(
        self,
        *,
        limit: int = 100,
        include_finished: bool = True,
    ) -> list[Trace]:
        """Get traces with optional filters."""
        with self._lock:
            traces = list(self._traces.values())

        if not include_finished:
            traces = [t for t in traces if t.end_time is None]

        return sorted(traces, key=lambda t: t.start_time, reverse=True)[:limit]

    def get_active_spans(self) -> list[Span]:
        """Get all currently active spans."""
        with self._lock:
            return list(self._active_spans.values())

    def export_trace(self, trace_id: str) -> Optional[str]:
        """Export a trace as JSON."""
        trace = self._traces.get(trace_id)
        if not trace:
            return None
        return json.dumps(trace.to_dict(), indent=2, default=str)

    def clear(self) -> None:
        """Clear all traces and spans."""
        with self._lock:
            self._traces.clear()
            self._active_spans.clear()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.clear()
        return False