"""Metrics collection and monitoring utilities."""

from __future__ import annotations

import time
from collections.abc import Callable
from contextlib import contextmanager
from functools import wraps
from typing import Any, TypeVar

from prometheus_client import Counter, Gauge, Histogram

# Prometheus metrics
FORECAST_REQUESTS = Counter(
    "sales_forecaster_forecast_requests_total",
    "Total forecast requests",
    ["status", "period"],
)

FORECAST_LATENCY = Histogram(
    "sales_forecaster_forecast_latency_seconds",
    "Forecast generation latency in seconds",
    ["period"],
    buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0],
)

PIPELINE_RUNS = Counter(
    "sales_forecaster_pipeline_runs_total",
    "Total pipeline runs",
    ["status"],
)

PIPELINE_STAGE_DURATION = Histogram(
    "sales_forecaster_pipeline_stage_duration_seconds",
    "Pipeline stage duration in seconds",
    ["stage"],
    buckets=[1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0],
)

ACTIVE_PIPELINE_RUNS = Gauge(
    "sales_forecaster_active_pipeline_runs",
    "Number of currently active pipeline runs",
)

DATA_RECORDS_COLLECTED = Counter(
    "sales_forecaster_data_records_collected_total",
    "Total data records collected",
    ["source"],
)

AGENT_ERRORS = Counter(
    "sales_forecaster_agent_errors_total",
    "Total agent errors",
    ["agent"],
)

FORECAST_ACCURACY = Gauge(
    "sales_forecaster_forecast_accuracy",
    "Forecast accuracy (1 - MAPE)",
    ["model"],
)

F = TypeVar("F", bound=Callable[..., Any])


def track_forecast_request(period: str = "unknown") -> Callable[[F], F]:
    """Decorator to track forecast request metrics.

    Args:
        period: The forecast period type.

    Returns:
        Decorated function.
    """

    def decorator(func: F) -> F:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            start = time.time()
            try:
                result = await func(*args, **kwargs)
                FORECAST_REQUESTS.labels(status="success", period=period).inc()
                return result
            except Exception:
                FORECAST_REQUESTS.labels(status="error", period=period).inc()
                raise
            finally:
                FORECAST_LATENCY.labels(period=period).observe(time.time() - start)

        return wrapper  # type: ignore[return-value]

    return decorator


@contextmanager
def track_pipeline_stage(stage: str):
    """Context manager to track pipeline stage duration.

    Args:
        stage: The pipeline stage name.
    """
    start = time.time()
    try:
        yield
    finally:
        PIPELINE_STAGE_DURATION.labels(stage=stage).observe(time.time() - start)


def record_pipeline_start() -> None:
    """Record a pipeline run start."""
    PIPELINE_RUNS.labels(status="started").inc()
    ACTIVE_PIPELINE_RUNS.inc()


def record_pipeline_complete(success: bool = True) -> None:
    """Record a pipeline run completion.

    Args:
        success: Whether the pipeline completed successfully.
    """
    status = "completed" if success else "failed"
    PIPELINE_RUNS.labels(status=status).inc()
    ACTIVE_PIPELINE_RUNS.dec()


def record_data_collected(source: str, count: int = 1) -> None:
    """Record data collection metrics.

    Args:
        source: The data source name.
        count: Number of records collected.
    """
    DATA_RECORDS_COLLECTED.labels(source=source).inc(count)


def record_agent_error(agent: str) -> None:
    """Record an agent error.

    Args:
        agent: The agent name.
    """
    AGENT_ERRORS.labels(agent=agent).inc()


def record_forecast_accuracy(model: str, accuracy: float) -> None:
    """Record forecast accuracy.

    Args:
        model: The model name.
        accuracy: Accuracy value (0-1).
    """
    FORECAST_ACCURACY.labels(model=model).set(accuracy)
