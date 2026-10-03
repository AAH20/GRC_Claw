"""Custom metrics for UGC Marketplace."""

from __future__ import annotations

import time
from collections import defaultdict
from typing import Any

from ugc_marketplace.config.logging_config import get_logger

logger = get_logger(__name__)
_counters: dict[str, int] = defaultdict(int)
_gauges: dict[str, float] = {}
_histograms: dict[str, list[float]] = defaultdict(list)


def record_metric(name: str, value: float, metric_type: str = "counter") -> None:
    """Record a custom metric."""
    if metric_type == "counter":
        _counters[name] += int(value)
    elif metric_type == "gauge":
        _gauges[name] = value
    elif metric_type == "histogram":
        _histograms[name].append(value)


def increment_counter(name: str, value: int = 1) -> None:
    """Increment a counter metric."""
    _counters[name] += value


def set_gauge(name: str, value: float) -> None:
    """Set a gauge metric."""
    _gauges[name] = value


def record_histogram(name: str, value: float) -> None:
    """Record a histogram observation."""
    _histograms[name].append(value)


def get_metrics() -> dict[str, Any]:
    """Get all metrics."""
    return {
        "counters": dict(_counters),
        "gauges": dict(_gauges),
        "histograms": {
            name: {
                "count": len(values),
                "min": min(values) if values else 0,
                "max": max(values) if values else 0,
                "avg": sum(values) / len(values) if values else 0,
            }
            for name, values in _histograms.items()
        },
    }


def timer(name: str):
    """Context manager for timing operations."""

    class Timer:
        def __enter__(self):
            self.start = time.monotonic()
            return self

        def __exit__(self, *args):
            duration = time.monotonic() - self.start
            record_histogram(name, duration)

    return Timer()
