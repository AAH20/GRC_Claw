"""Metrics middleware for UGC Marketplace."""

from __future__ import annotations

import time
from collections import defaultdict
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from ugc_marketplace.config.logging_config import get_logger

logger = get_logger(__name__)


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to collect application metrics.

    Tracks request count, latency, and error rates.
    Exposes metrics in Prometheus format at /metrics endpoint.
    """

    def __init__(self, app: Any) -> None:
        """Initialize metrics middleware.

        Args:
            app: The ASGI application.
        """
        super().__init__(app)
        self.request_count: dict[str, int] = defaultdict(int)
        self.request_latency: dict[str, list[float]] = defaultdict(list)
        self.error_count: dict[str, int] = defaultdict(int)
        self.status_codes: dict[str, int] = defaultdict(int)

    def _get_route_key(self, request: Request) -> str:
        """Get route key for metrics.

        Args:
            request: The incoming request.

        Returns:
            Route key string.
        """
        path = request.url.path
        # Normalize path by replacing IDs with placeholders
        # e.g., /api/v1/listings/123 -> /api/v1/listings/{id}
        parts = path.split("/")
        normalized = []
        for part in parts:
            if part.isdigit() or (len(part) > 20 and "-" in part):
                normalized.append("{id}")
            else:
                normalized.append(part)
        return "/".join(normalized)

    async def dispatch(self, request: Request, call_next: Any) -> Any:
        """Process request with metrics collection.

        Args:
            request: The incoming request.
            call_next: The next handler in the chain.

        Returns:
            Response from next handler.
        """
        start_time = time.monotonic()
        route = self._get_route_key(request)
        method = request.method

        try:
            response = await call_next(request)
            duration = time.monotonic() - start_time

            # Record metrics
            self.request_count[f"{method}:{route}"] += 1
            self.request_latency[f"{method}:{route}"].append(duration)
            self.status_codes[f"{response.status_code}"] += 1

            if response.status_code >= 400:
                self.error_count[f"{method}:{route}"] += 1

            # Add metrics headers
            response.headers["X-Request-Duration-Ms"] = str(round(duration * 1000, 2))

            return response

        except Exception:
            duration = time.monotonic() - start_time
            self.request_count[f"{method}:{route}"] += 1
            self.request_latency[f"{method}:{route}"].append(duration)
            self.error_count[f"{method}:{route}"] += 1
            self.status_codes["500"] += 1
            raise

    def get_metrics(self) -> dict[str, Any]:
        """Get current metrics.

        Returns:
            Dictionary of metrics.
        """
        metrics: dict[str, Any] = {
            "request_count": dict(self.request_count),
            "error_count": dict(self.error_count),
            "status_codes": dict(self.status_codes),
            "latency": {},
        }

        # Calculate latency percentiles
        for key, latencies in self.request_latency.items():
            if latencies:
                sorted_latencies = sorted(latencies)
                metrics["latency"][key] = {
                    "count": len(sorted_latencies),
                    "min": round(min(sorted_latencies) * 1000, 2),
                    "max": round(max(sorted_latencies) * 1000, 2),
                    "mean": round(
                        (sum(sorted_latencies) / len(sorted_latencies)) * 1000, 2
                    ),
                    "p50": round(
                        sorted_latencies[int(len(sorted_latencies) * 0.5)] * 1000, 2
                    ),
                    "p95": round(
                        sorted_latencies[int(len(sorted_latencies) * 0.95)] * 1000, 2
                    ),
                    "p99": round(
                        sorted_latencies[int(len(sorted_latencies) * 0.99)] * 1000, 2
                    ),
                }

        return metrics

    def get_prometheus_format(self) -> str:
        """Get metrics in Prometheus exposition format.

        Returns:
            Prometheus-formatted metrics string.
        """
        lines: list[str] = []

        # Request count
        lines.append("# HELP http_requests_total Total number of HTTP requests.")
        lines.append("# TYPE http_requests_total counter")
        for key, count in self.request_count.items():
            method, route = key.split(":", 1)
            lines.append(
                f'http_requests_total{{method="{method}",route="{route}"}} {count}'
            )

        # Error count
        lines.append("# HELP http_errors_total Total number of HTTP errors.")
        lines.append("# TYPE http_errors_total counter")
        for key, count in self.error_count.items():
            method, route = key.split(":", 1)
            lines.append(
                f'http_errors_total{{method="{method}",route="{route}"}} {count}'
            )

        # Status codes
        lines.append(
            "# HELP http_responses_total Total number of HTTP responses by status code."
        )
        lines.append("# TYPE http_responses_total counter")
        for code, count in self.status_codes.items():
            lines.append(f'http_responses_total{{status_code="{code}"}} {count}')

        # Latency
        lines.append(
            "# HELP http_request_duration_ms HTTP request duration in milliseconds."
        )
        lines.append("# TYPE http_request_duration_ms summary")
        for key, latency in self.get_metrics()["latency"].items():
            method, route = key.split(":", 1)
            for stat, value in latency.items():
                lines.append(
                    f'http_request_duration_ms{{method="{method}",route="{route}",stat="{stat}"}} {value}'
                )

        return "\n".join(lines)
