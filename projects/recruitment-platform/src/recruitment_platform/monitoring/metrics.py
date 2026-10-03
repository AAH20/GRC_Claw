"""Prometheus metrics collection for the recruitment platform."""

from __future__ import annotations

import time
from typing import Any

from fastapi import Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest
from starlette.middleware.base import BaseHTTPMiddleware

# Request metrics
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

ACTIVE_REQUESTS = Gauge(
    "http_active_requests",
    "Number of active HTTP requests",
)

# Agent metrics
AGENT_EXECUTION_COUNT = Counter(
    "agent_executions_total",
    "Total agent executions",
    ["agent_name", "status"],
)

AGENT_EXECUTION_DURATION = Histogram(
    "agent_execution_duration_seconds",
    "Agent execution duration in seconds",
    ["agent_name"],
    buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0],
)

# Database metrics
DB_CONNECTION_POOL = Gauge(
    "db_connection_pool_size",
    "Database connection pool size",
    ["state"],
)

DB_QUERY_DURATION = Histogram(
    "db_query_duration_seconds",
    "Database query duration in seconds",
    ["operation"],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0],
)

# Cache metrics
CACHE_HITS = Counter(
    "cache_hits_total",
    "Total cache hits",
    ["cache_name"],
)

CACHE_MISSES = Counter(
    "cache_misses_total",
    "Total cache misses",
    ["cache_name"],
)

CACHE_OPERATION_DURATION = Histogram(
    "cache_operation_duration_seconds",
    "Cache operation duration in seconds",
    ["operation"],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1],
)

# Queue metrics
QUEUE_SIZE = Gauge(
    "task_queue_size",
    "Current task queue size",
    ["queue_name"],
)

QUEUE_TASKS_PROCESSED = Counter(
    "tasks_processed_total",
    "Total tasks processed",
    ["queue_name", "status"],
)

# Business metrics
APPLICATIONS_CREATED = Counter(
    "applications_created_total",
    "Total job applications created",
    ["source"],
)

INTERVIEWS_SCHEDULED = Counter(
    "interviews_scheduled_total",
    "Total interviews scheduled",
    ["interview_type"],
)

RESUMES_PARSED = Counter(
    "resumes_parsed_total",
    "Total resumes parsed",
    ["status"],
)


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to collect request metrics."""

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        ACTIVE_REQUESTS.inc()
        start_time = time.time()

        try:
            response = await call_next(request)
            status_code = str(response.status_code)
        except Exception:
            status_code = "500"
            raise
        finally:
            duration = time.time() - start_time
            ACTIVE_REQUESTS.dec()

            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=request.url.path,
                status=status_code,
            ).inc()

            REQUEST_LATENCY.labels(
                method=request.method,
                endpoint=request.url.path,
            ).observe(duration)

        return response


def get_metrics() -> tuple[str, str]:
    """Get Prometheus metrics in text format."""
    return generate_latest().decode("utf-8"), CONTENT_TYPE_LATEST
