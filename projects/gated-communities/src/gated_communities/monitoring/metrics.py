"""Custom Prometheus metrics for Gated Communities."""
from __future__ import annotations

import time
import logging
from typing import Any

from prometheus_client import Counter, Histogram, Gauge, Info

logger = logging.getLogger(__name__)

# Application info
app_info = Info("gated_communities", "Gated Communities application info")

# Request metrics
http_requests_total = Counter(
    "gated_communities_http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

http_request_duration_seconds = Histogram(
    "gated_communities_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

# Business metrics
active_members = Gauge(
    "gated_communities_active_members",
    "Number of active members",
    ["community_id"],
)

moderation_queue_size = Gauge(
    "gated_communities_moderation_queue_size",
    "Number of items in moderation queue",
    ["community_id", "priority"],
)

tier_subscriptions = Gauge(
    "gated_communities_tier_subscriptions",
    "Number of tier subscriptions",
    ["tier_id", "tier_level"],
)

# Agent metrics
agent_execution_total = Counter(
    "gated_communities_agent_execution_total",
    "Total agent executions",
    ["agent_type", "status"],
)

agent_execution_duration_seconds = Histogram(
    "gated_communities_agent_execution_duration_seconds",
    "Agent execution duration in seconds",
    ["agent_type"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0],
)

# Database metrics
db_query_duration_seconds = Histogram(
    "gated_communities_db_query_duration_seconds",
    "Database query duration in seconds",
    ["operation", "table"],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
)

db_connections_active = Gauge(
    "gated_communities_db_connections_active",
    "Number of active database connections",
)

# Cache metrics
cache_hits_total = Counter(
    "gated_communities_cache_hits_total",
    "Total cache hits",
    ["cache_type"],
)

cache_misses_total = Counter(
    "gated_communities_cache_misses_total",
    "Total cache misses",
    ["cache_type"],
)

# WebSocket metrics
websocket_connections_active = Gauge(
    "gated_communities_websocket_connections_active",
    "Number of active WebSocket connections",
    ["community_id"],
)

websocket_messages_total = Counter(
    "gated_communities_websocket_messages_total",
    "Total WebSocket messages",
    ["community_id", "message_type"],
)


class MetricsMiddleware:
    """Middleware to collect HTTP request metrics."""

    def __init__(self, app: Any) -> None:
        self.app = app

    async def __call__(self, scope: dict, receive: Any, send: Any) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        method = scope["method"]
        path = scope["path"]
        start_time = time.time()

        async def send_wrapper(message: dict) -> None:
            if message["type"] == "http.response.start":
                status = message["status"]
                http_requests_total.labels(
                    method=method, endpoint=path, status=status
                ).inc()
            await send(message)

        await self.app(scope, receive, send_wrapper)

        duration = time.time() - start_time
        http_request_duration_seconds.labels(
            method=method, endpoint=path
        ).observe(duration)
