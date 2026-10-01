"""
Error Reporting and Analytics for GRC_Claw

Provides:
- Structured error reporting to multiple backends
- Error metrics collection and aggregation
- Error analytics and trending
- Alert rules for error thresholds
- Error dashboards data
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable

from .codes import ErrorCode, get_error_code
from .taxonomy import (
    ErrorCategory,
    ErrorClassification,
    ErrorSeverity,
    classify_error,
)

logger = logging.getLogger("grcclaw.errors.reporting")


class AlertSeverity(str, Enum):
    """Alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class ErrorEvent:
    """A single error event."""

    code: str
    message: str
    category: ErrorCategory
    severity: ErrorSeverity
    timestamp: float
    request_id: str | None = None
    trace_id: str | None = None
    tenant_id: str | None = None
    user_id: str | None = None
    agent_id: str | None = None
    workflow_id: str | None = None
    endpoint: str | None = None
    method: str | None = None
    duration_ms: float | None = None
    stack_trace: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_exception(
        cls,
        exc: Exception,
        *,
        request_id: str | None = None,
        trace_id: str | None = None,
        tenant_id: str | None = None,
        user_id: str | None = None,
        agent_id: str | None = None,
        workflow_id: str | None = None,
        endpoint: str | None = None,
        method: str | None = None,
        duration_ms: float | None = None,
        stack_trace: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ErrorEvent:
        """Create an ErrorEvent from an exception."""
        code = getattr(exc, "code", None) or _exception_to_code(exc)
        classification = classify_error(code)

        return cls(
            code=code,
            message=str(exc),
            category=classification.category,
            severity=classification.severity,
            timestamp=time.time(),
            request_id=request_id,
            trace_id=trace_id,
            tenant_id=tenant_id,
            user_id=user_id,
            agent_id=agent_id,
            workflow_id=workflow_id,
            endpoint=endpoint,
            method=method,
            duration_ms=duration_ms,
            stack_trace=stack_trace,
            metadata=metadata or {},
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "category": self.category.value,
            "severity": self.severity.value,
            "timestamp": self.timestamp,
            "request_id": self.request_id,
            "trace_id": self.trace_id,
            "tenant_id": self.tenant_id,
            "user_id": self.user_id,
            "agent_id": self.agent_id,
            "workflow_id": self.workflow_id,
            "endpoint": self.endpoint,
            "method": self.method,
            "duration_ms": self.duration_ms,
            "stack_trace": self.stack_trace,
            "metadata": self.metadata,
        }


def _exception_to_code(exc: Exception) -> str:
    """Map an exception to an error code."""
    exc_name = type(exc).__name__
    mapping: dict[str, str] = {
        "ValueError": "VALIDATION_ERROR",
        "TypeError": "VALIDATION_ERROR",
        "KeyError": "MISSING_REQUIRED_FIELD",
        "IndexError": "VALIDATION_ERROR",
        "AttributeError": "INTERNAL_ERROR",
        "NotImplementedError": "NOT_IMPLEMENTED",
        "RuntimeError": "INTERNAL_ERROR",
        "OSError": "NETWORK_ERROR",
        "IOError": "NETWORK_ERROR",
        "ConnectionError": "NETWORK_ERROR",
        "TimeoutError": "TIMEOUT",
        "FileNotFoundError": "NOT_FOUND",
        "PermissionError": "FORBIDDEN",
        "MemoryError": "MEMORY_LIMIT_EXCEEDED",
        "RecursionError": "INTERNAL_ERROR",
    }
    return mapping.get(exc_name, "INTERNAL_ERROR")


@dataclass
class ErrorMetrics:
    """Aggregated error metrics."""

    total_errors: int = 0
    errors_by_code: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    errors_by_category: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    errors_by_severity: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    errors_by_tenant: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    errors_by_endpoint: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    error_rate: float = 0.0  # errors per minute
    error_rate_5m: float = 0.0
    error_rate_1h: float = 0.0
    top_error_codes: list[tuple[str, int]] = field(default_factory=list)
    top_error_endpoints: list[tuple[str, int]] = field(default_factory=list)
    mean_time_between_failures: float = 0.0  # seconds
    last_error_timestamp: float | None = None
    first_error_timestamp: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_errors": self.total_errors,
            "errors_by_code": dict(self.errors_by_code),
            "errors_by_category": dict(self.errors_by_category),
            "errors_by_severity": dict(self.errors_by_severity),
            "errors_by_tenant": dict(self.errors_by_tenant),
            "errors_by_endpoint": dict(self.errors_by_endpoint),
            "error_rate": self.error_rate,
            "error_rate_5m": self.error_rate_5m,
            "error_rate_1h": self.error_rate_1h,
            "top_error_codes": self.top_error_codes,
            "top_error_endpoints": self.top_error_endpoints,
            "mean_time_between_failures": self.mean_time_between_failures,
            "last_error_timestamp": self.last_error_timestamp,
            "first_error_timestamp": self.first_error_timestamp,
        }


@dataclass
class ErrorTrend:
    """Error trend data point."""

    timestamp: float
    count: int
    code: str | None = None
    category: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "count": self.count,
            "code": self.code,
            "category": self.category,
        }


@dataclass
class AlertRule:
    """Alert rule for error thresholds."""

    name: str
    description: str
    severity: AlertSeverity
    # Condition: error count within time window
    error_threshold: int
    time_window_seconds: int
    # Optional filters
    error_codes: set[str] | None = None
    categories: set[ErrorCategory] | None = None
    severities: set[ErrorSeverity] | None = None
    tenants: set[str] | None = None
    endpoints: set[str] | None = None
    # Actions
    webhook_url: str | None = None
    email_recipients: list[str] = field(default_factory=list)
    slack_channel: str | None = None
    pagerduty_key: str | None = None

    def matches(self, event: ErrorEvent) -> bool:
        """Check if an error event matches this alert rule."""
        if self.error_codes and event.code not in self.error_codes:
            return False
        if self.categories and event.category not in self.categories:
            return False
        if self.severities and event.severity not in self.severities:
            return False
        if self.tenants and event.tenant_id not in self.tenants:
            return False
        if self.endpoints and event.endpoint not in self.endpoints:
            return False
        return True

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "severity": self.severity.value,
            "error_threshold": self.error_threshold,
            "time_window_seconds": self.time_window_seconds,
            "error_codes": list(self.error_codes) if self.error_codes else None,
            "categories": [c.value for c in self.categories] if self.categories else None,
            "severities": [s.value for s in self.severities] if self.severities else None,
            "tenants": list(self.tenants) if self.tenants else None,
            "endpoints": list(self.endpoints) if self.endpoints else None,
            "webhook_url": self.webhook_url,
            "email_recipients": self.email_recipients,
            "slack_channel": self.slack_channel,
            "pagerduty_key": self.pagerduty_key,
        }


class ErrorReporter:
    """Reports errors to multiple backends."""

    def __init__(self) -> None:
        self._backends: list[ErrorBackend] = []
        self._buffer: list[ErrorEvent] = []
        self._buffer_size: int = 100
        self._flush_interval_seconds: float = 10.0
        self._flush_task: asyncio.Task | None = None
        self._running = False

    def add_backend(self, backend: ErrorBackend) -> None:
        """Add a reporting backend."""
        self._backends.append(backend)

    def remove_backend(self, backend: ErrorBackend) -> None:
        """Remove a reporting backend."""
        if backend in self._backends:
            self._backends.remove(backend)

    async def start(self) -> None:
        """Start the background flush task."""
        self._running = True
        self._flush_task = asyncio.create_task(self._flush_loop())

    async def stop(self) -> None:
        """Stop the background flush task."""
        self._running = False
        if self._flush_task:
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass
        # Final flush
        await self.flush()

    async def report(self, event: ErrorEvent) -> None:
        """Report an error event."""
        self._buffer.append(event)

        if len(self._buffer) >= self._buffer_size:
            await self.flush()

    async def flush(self) -> None:
        """Flush buffered events to all backends."""
        if not self._buffer:
            return

        events = self._buffer[:]
        self._buffer.clear()

        for backend in self._backends:
            try:
                await backend.send(events)
            except Exception as exc:
                logger.error(
                    "Failed to send errors to backend %s: %s",
                    type(backend).__name__,
                    exc,
                )

    async def _flush_loop(self) -> None:
        """Background task to periodically flush events."""
        while self._running:
            try:
                await asyncio.sleep(self._flush_interval_seconds)
                await self.flush()
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error("Error in flush loop: %s", exc)


class ErrorBackend:
    """Base class for error reporting backends."""

    async def send(self, events: list[ErrorEvent]) -> None:
        """Send error events to the backend."""
        raise NotImplementedError


class LoggingBackend(ErrorBackend):
    """Backend that logs errors."""

    def __init__(self, logger_name: str = "grcclaw.errors"):
        self.logger = logging.getLogger(logger_name)

    async def send(self, events: list[ErrorEvent]) -> None:
        for event in events:
            self.logger.error(
                "Error reported: %s - %s",
                event.code,
                event.message,
                extra=event.to_dict(),
            )


class WebhookBackend(ErrorBackend):
    """Backend that sends errors to a webhook."""

    def __init__(self, url: str, headers: dict[str, str] | None = None):
        self.url = url
        self.headers = headers or {}

    async def send(self, events: list[ErrorEvent]) -> None:
        import aiohttp

        payload = {
            "events": [event.to_dict() for event in events],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.url,
                json=payload,
                headers=self.headers,
            ) as resp:
                if resp.status >= 400:
                    raise RuntimeError(
                        f"Webhook returned {resp.status}: {await resp.text()}"
                    )


class FileBackend(ErrorBackend):
    """Backend that writes errors to a file."""

    def __init__(self, filepath: str):
        self.filepath = filepath

    async def send(self, events: list[ErrorEvent]) -> None:
        import json

        lines = [json.dumps(event.to_dict()) for event in events]
        with open(self.filepath, "a") as f:
            for line in lines:
                f.write(line + "\n")


class ErrorAnalytics:
    """Error analytics and trending."""

    def __init__(self, max_events: int = 10000) -> None:
        self._events: list[ErrorEvent] = []
        self._max_events = max_events
        self._alert_rules: list[AlertRule] = []
        self._alert_history: list[dict[str, Any]] = []

    def add_event(self, event: ErrorEvent) -> None:
        """Add an error event for analytics."""
        self._events.append(event)

        # Trim old events
        if len(self._events) > self._max_events:
            self._events = self._events[-self._max_events :]

        # Check alert rules
        self._check_alerts(event)

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

    def _check_alerts(self, event: ErrorEvent) -> None:
        """Check if any alert rules are triggered."""
        for rule in self._alert_rules:
            if not rule.matches(event):
                continue

            # Count matching events in time window
            window_start = event.timestamp - rule.time_window_seconds
            count = sum(
                1
                for e in self._events
                if e.timestamp >= window_start and rule.matches(e)
            )

            if count >= rule.error_threshold:
                self._trigger_alert(rule, count, event)

    def _trigger_alert(
        self, rule: AlertRule, count: int, event: ErrorEvent
    ) -> None:
        """Trigger an alert."""
        alert = {
            "rule_name": rule.name,
            "severity": rule.severity.value,
            "error_count": count,
            "threshold": rule.error_threshold,
            "time_window_seconds": rule.time_window_seconds,
            "triggering_event": event.to_dict(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._alert_history.append(alert)

        logger.warning(
            "Alert triggered: %s (count=%d, threshold=%d)",
            rule.name,
            count,
            rule.error_threshold,
        )

        # TODO: Send notifications (webhook, email, slack, pagerduty)

    def get_metrics(
        self,
        time_window_seconds: float | None = None,
    ) -> ErrorMetrics:
        """Get error metrics for a time window.

        Args:
            time_window_seconds: Time window in seconds. None = all events.

        Returns:
            ErrorMetrics for the time window.
        """
        now = time.time()
        if time_window_seconds is not None:
            cutoff = now - time_window_seconds
            events = [e for e in self._events if e.timestamp >= cutoff]
        else:
            events = self._events[:]

        metrics = ErrorMetrics()
        metrics.total_errors = len(events)

        if not events:
            return metrics

        # Count by various dimensions
        for event in events:
            metrics.errors_by_code[event.code] += 1
            metrics.errors_by_category[event.category.value] += 1
            metrics.errors_by_severity[event.severity.value] += 1
            if event.tenant_id:
                metrics.errors_by_tenant[event.tenant_id] += 1
            if event.endpoint:
                metrics.errors_by_endpoint[event.endpoint] += 1

        # Timestamps
        metrics.first_error_timestamp = events[0].timestamp
        metrics.last_error_timestamp = events[-1].timestamp

        # Error rate (errors per minute)
        time_span = metrics.last_error_timestamp - metrics.first_error_timestamp
        if time_span > 0:
            metrics.error_rate = len(events) / (time_span / 60.0)

        # Top error codes
        metrics.top_error_codes = sorted(
            metrics.errors_by_code.items(), key=lambda x: x[1], reverse=True
        )[:10]

        # Top error endpoints
        metrics.top_error_endpoints = sorted(
            metrics.errors_by_endpoint.items(), key=lambda x: x[1], reverse=True
        )[:10]

        # Mean time between failures
        if len(events) > 1:
            metrics.mean_time_between_failures = time_span / (len(events) - 1)

        return metrics

    def get_trends(
        self,
        bucket_seconds: float = 60.0,
        time_window_seconds: float | None = None,
    ) -> list[ErrorTrend]:
        """Get error trends bucketed by time.

        Args:
            bucket_seconds: Size of each time bucket in seconds.
            time_window_seconds: Time window. None = all events.

        Returns:
            List of ErrorTrend data points.
        """
        now = time.time()
        if time_window_seconds is not None:
            cutoff = now - time_window_seconds
            events = [e for e in self._events if e.timestamp >= cutoff]
        else:
            events = self._events[:]

        if not events:
            return []

        # Bucket events
        buckets: dict[float, int] = defaultdict(int)
        for event in events:
            bucket_key = (event.timestamp // bucket_seconds) * bucket_seconds
            buckets[bucket_key] += 1

        # Convert to trends
        trends = []
        for timestamp, count in sorted(buckets.items()):
            trends.append(
                ErrorTrend(
                    timestamp=timestamp,
                    count=count,
                )
            )

        return trends

    def get_trends_by_code(
        self,
        bucket_seconds: float = 60.0,
        time_window_seconds: float | None = None,
    ) -> dict[str, list[ErrorTrend]]:
        """Get error trends grouped by error code."""
        now = time.time()
        if time_window_seconds is not None:
            cutoff = now - time_window_seconds
            events = [e for e in self._events if e.timestamp >= cutoff]
        else:
            events = self._events[:]

        if not events:
            return {}

        # Bucket events by code
        buckets: dict[str, dict[float, int]] = defaultdict(
            lambda: defaultdict(int)
        )
        for event in events:
            bucket_key = (event.timestamp // bucket_seconds) * bucket_seconds
            buckets[event.code][bucket_key] += 1

        # Convert to trends
        result: dict[str, list[ErrorTrend]] = {}
        for code, code_buckets in buckets.items():
            trends = []
            for timestamp, count in sorted(code_buckets.items()):
                trends.append(
                    ErrorTrend(
                        timestamp=timestamp,
                        count=count,
                        code=code,
                    )
                )
            result[code] = trends

        return result

    def get_error_summary(
        self,
        time_window_seconds: float | None = None,
    ) -> dict[str, Any]:
        """Get a summary of errors for dashboards."""
        metrics = self.get_metrics(time_window_seconds)
        trends = self.get_trends(
            bucket_seconds=60.0, time_window_seconds=time_window_seconds
        )

        return {
            "metrics": metrics.to_dict(),
            "trends": [t.to_dict() for t in trends],
            "alert_history": self._alert_history[-100:],
            "total_alerts": len(self._alert_history),
        }

    def get_top_errors(
        self,
        limit: int = 10,
        time_window_seconds: float | None = None,
    ) -> list[dict[str, Any]]:
        """Get the top error codes with details."""
        metrics = self.get_metrics(time_window_seconds)

        result = []
        for code, count in metrics.top_error_codes[:limit]:
            error_code = get_error_code(code)
            result.append(
                {
                    "code": code,
                    "count": count,
                    "percentage": (
                        count / metrics.total_errors * 100
                        if metrics.total_errors > 0
                        else 0
                    ),
                    "category": error_code.category.value,
                    "severity": error_code.severity.value,
                    "recoverability": error_code.recoverability.value,
                    "message": error_code.message,
                }
            )

        return result

    def clear(self) -> None:
        """Clear all events and alert history."""
        self._events.clear()
        self._alert_history.clear()


# ── Default Alert Rules ───────────────────────────────────────────────────


def create_default_alert_rules() -> list[AlertRule]:
    """Create default alert rules for common error patterns."""
    return [
        AlertRule(
            name="high_error_rate",
            description="High error rate detected",
            severity=AlertSeverity.WARNING,
            error_threshold=50,
            time_window_seconds=300,  # 5 minutes
        ),
        AlertRule(
            name="critical_errors",
            description="Critical errors detected",
            severity=AlertSeverity.CRITICAL,
            error_threshold=1,
            time_window_seconds=60,
            severities={ErrorSeverity.CRITICAL},
        ),
        AlertRule(
            name="auth_failures",
            description="Authentication failures detected",
            severity=AlertSeverity.WARNING,
            error_threshold=20,
            time_window_seconds=300,
            categories={ErrorCategory.AUTHENTICATION},
        ),
        AlertRule(
            name="rate_limit_spike",
            description="Rate limit spike detected",
            severity=AlertSeverity.WARNING,
            error_threshold=100,
            time_window_seconds=300,
            categories={ErrorCategory.RATE_LIMIT},
        ),
        AlertRule(
            name="external_service_degradation",
            description="External service degradation detected",
            severity=AlertSeverity.CRITICAL,
            error_threshold=10,
            time_window_seconds=300,
            categories={ErrorCategory.EXTERNAL_SERVICE},
        ),
        AlertRule(
            name="workflow_failures",
            description="Workflow failures detected",
            severity=AlertSeverity.WARNING,
            error_threshold=10,
            time_window_seconds=600,
            categories={ErrorCategory.WORKFLOW},
        ),
        AlertRule(
            name="security_incidents",
            description="Security incidents detected",
            severity=AlertSeverity.CRITICAL,
            error_threshold=1,
            time_window_seconds=60,
            categories={ErrorCategory.SECURITY},
        ),
    ]
