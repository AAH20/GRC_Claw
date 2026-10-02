"""Benchmark testing framework for marketing systems.

This module provides benchmarking capabilities including:
- Baseline performance measurement
- Comparative benchmarking
- Regression detection
- Benchmark reporting and trending
- Performance scoring
"""

from __future__ import annotations

import json
import statistics
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable


class BenchmarkCategory(Enum):
    """Categories of benchmarks."""

    LATENCY = "latency"
    THROUGHPUT = "throughput"
    ACCURACY = "accuracy"
    RELIABILITY = "reliability"
    SCALABILITY = "scalability"
    RESOURCE = "resource"


@dataclass
class BenchmarkMetric:
    """A single benchmark metric measurement.

    Attributes:
        name: Metric name.
        value: Measured value.
        unit: Unit of measurement (e.g., "ms", "rps", "percent").
        category: Benchmark category.
        timestamp: When the measurement was taken.
        metadata: Additional metric metadata.
    """

    name: str
    value: float
    unit: str
    category: BenchmarkCategory
    timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class BenchmarkResult:
    """Result of a benchmark run.

    Attributes:
        benchmark_id: Unique benchmark identifier.
        name: Benchmark name.
        description: Benchmark description.
        metrics: List of measured metrics.
        total_score: Overall benchmark score.
        duration_seconds: Total benchmark duration.
        timestamp: When the benchmark was run.
        metadata: Additional result metadata.
    """

    benchmark_id: str
    name: str
    description: str = ""
    metrics: list[BenchmarkMetric] = field(default_factory=list)
    total_score: float = 0.0
    duration_seconds: float = 0.0
    timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def get_metric(self, name: str) -> BenchmarkMetric | None:
        """Get a metric by name.

        Args:
            name: The metric name.

        Returns:
            The metric, or None if not found.
        """
        for metric in self.metrics:
            if metric.name == name:
                return metric
        return None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation.
        """
        return {
            "benchmark_id": self.benchmark_id,
            "name": self.name,
            "description": self.description,
            "metrics": [
                {
                    "name": m.name,
                    "value": m.value,
                    "unit": m.unit,
                    "category": m.category.value,
                    "timestamp": m.timestamp,
                    "metadata": m.metadata,
                }
                for m in self.metrics
            ],
            "total_score": self.total_score,
            "duration_seconds": self.duration_seconds,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }


class BenchmarkTarget(ABC):
    """Abstract base class for benchmark targets."""

    @abstractmethod
    async def setup(self) -> None:
        """Set up the target for benchmarking."""
        ...

    @abstractmethod
    async def execute(self) -> list[BenchmarkMetric]:
        """Execute the benchmark and return metrics.

        Returns:
            List of measured metrics.
        """
        ...

    @abstractmethod
    async def teardown(self) -> None:
        """Tear down the target after benchmarking."""
        ...


class BenchmarkRunner:
    """Runs benchmarks and collects results."""

    def __init__(self, warmup_iterations: int = 3, measured_iterations: int = 10) -> None:
        """Initialize BenchmarkRunner.

        Args:
            warmup_iterations: Number of warmup iterations.
            measured_iterations: Number of measured iterations.
        """
        self.warmup_iterations = warmup_iterations
        self.measured_iterations = measured_iterations
        self._results: list[BenchmarkResult] = []

    async def run(
        self,
        target: BenchmarkTarget,
        benchmark_id: str,
        name: str,
        description: str = "",
    ) -> BenchmarkResult:
        """Run a benchmark.

        Args:
            target: The benchmark target.
            benchmark_id: Unique benchmark identifier.
            name: Benchmark name.
            description: Benchmark description.

        Returns:
            The benchmark result.
        """
        await target.setup()

        try:
            for _ in range(self.warmup_iterations):
                await target.execute()

            all_metrics: list[list[BenchmarkMetric]] = []
            start_time = time.monotonic()

            for _ in range(self.measured_iterations):
                metrics = await target.execute()
                all_metrics.append(metrics)

            duration = time.monotonic() - start_time

            aggregated = self._aggregate_metrics(all_metrics)
            score = self._compute_score(aggregated)

            result = BenchmarkResult(
                benchmark_id=benchmark_id,
                name=name,
                description=description,
                metrics=aggregated,
                total_score=score,
                duration_seconds=duration,
                timestamp=time.time(),
            )

            self._results.append(result)
            return result

        finally:
            await target.teardown()

    def _aggregate_metrics(
        self, all_metrics: list[list[BenchmarkMetric]]
    ) -> list[BenchmarkMetric]:
        """Aggregate metrics across iterations.

        Args:
            all_metrics: List of metric lists from each iteration.

        Returns:
            List of aggregated metrics.
        """
        if not all_metrics:
            return []

        metric_groups: dict[str, list[BenchmarkMetric]] = {}
        for iteration_metrics in all_metrics:
            for metric in iteration_metrics:
                if metric.name not in metric_groups:
                    metric_groups[metric.name] = []
                metric_groups[metric.name].append(metric)

        aggregated: list[BenchmarkMetric] = []
        for name, metrics in metric_groups.items():
            values = [m.value for m in metrics]
            aggregated.append(
                BenchmarkMetric(
                    name=name,
                    value=statistics.mean(values),
                    unit=metrics[0].unit,
                    category=metrics[0].category,
                    timestamp=time.time(),
                    metadata={
                        "min": min(values),
                        "max": max(values),
                        "std_dev": statistics.stdev(values) if len(values) > 1 else 0,
                        "iterations": len(values),
                    },
                )
            )

        return aggregated

    def _compute_score(self, metrics: list[BenchmarkMetric]) -> float:
        """Compute overall benchmark score.

        Args:
            metrics: Aggregated metrics.

        Returns:
            Overall score (higher is better).
        """
        if not metrics:
            return 0.0

        scores: list[float] = []
        for metric in metrics:
            if metric.category == BenchmarkCategory.LATENCY:
                score = max(0, 100 - metric.value)
            elif metric.category == BenchmarkCategory.THROUGHPUT:
                score = min(100, metric.value / 100)
            elif metric.category == BenchmarkCategory.ACCURACY:
                score = metric.value
            else:
                score = metric.value
            scores.append(score)

        return statistics.mean(scores) if scores else 0.0

    def get_results(self) -> list[BenchmarkResult]:
        """Get all benchmark results.

        Returns:
            List of benchmark results.
        """
        return self._results.copy()


class BenchmarkComparator:
    """Compares benchmark results to detect regressions."""

    def __init__(self, regression_threshold: float = 0.10) -> None:
        """Initialize BenchmarkComparator.

        Args:
            regression_threshold: Fractional change that constitutes a regression.
        """
        self.regression_threshold = regression_threshold

    def compare(
        self, baseline: BenchmarkResult, current: BenchmarkResult
    ) -> dict[str, Any]:
        """Compare two benchmark results.

        Args:
            baseline: The baseline result.
            current: The current result.

        Returns:
            Dictionary with comparison results.
        """
        regressions: list[dict[str, Any]] = []
        improvements: list[dict[str, Any]] = []
        unchanged: list[dict[str, Any]] = []

        baseline_metrics = {m.name: m for m in baseline.metrics}
        current_metrics = {m.name: m for m in current.metrics}

        all_names = set(baseline_metrics.keys()) | set(current_metrics.keys())

        for name in all_names:
            base_metric = baseline_metrics.get(name)
            curr_metric = current_metrics.get(name)

            if base_metric is None or curr_metric is None:
                continue

            if base_metric.value == 0:
                change_pct = 0.0
            else:
                change_pct = (curr_metric.value - base_metric.value) / abs(base_metric.value)

            comparison = {
                "metric": name,
                "baseline": base_metric.value,
                "current": curr_metric.value,
                "change": curr_metric.value - base_metric.value,
                "change_percent": change_pct,
            }

            if abs(change_pct) > self.regression_threshold:
                if change_pct > 0:
                    if base_metric.category in (
                        BenchmarkCategory.LATENCY,
                        BenchmarkCategory.RESOURCE,
                    ):
                        regressions.append(comparison)
                    else:
                        improvements.append(comparison)
                else:
                    if base_metric.category in (
                        BenchmarkCategory.LATENCY,
                        BenchmarkCategory.RESOURCE,
                    ):
                        improvements.append(comparison)
                    else:
                        regressions.append(comparison)
            else:
                unchanged.append(comparison)

        return {
            "has_regressions": len(regressions) > 0,
            "regressions": regressions,
            "improvements": improvements,
            "unchanged": unchanged,
            "total_compared": len(all_names),
        }


class BenchmarkReporter:
    """Generates benchmark reports."""

    @staticmethod
    def generate_report(result: BenchmarkResult) -> str:
        """Generate a text report for a benchmark result.

        Args:
            result: The benchmark result.

        Returns:
            Formatted report string.
        """
        lines = [
            f"Benchmark: {result.name}",
            f"ID: {result.benchmark_id}",
            f"Description: {result.description}",
            f"Duration: {result.duration_seconds:.2f}s",
            f"Overall Score: {result.total_score:.1f}",
            "",
            "Metrics:",
            "-" * 60,
        ]

        for metric in result.metrics:
            lines.append(
                f"  {metric.name:30s} {metric.value:10.2f} {metric.unit:10s} "
                f"({metric.category.value})"
            )
            if metric.metadata:
                for key, value in metric.metadata.items():
                    lines.append(f"    {key}: {value}")

        return "\n".join(lines)

    @staticmethod
    def export_json(result: BenchmarkResult, filepath: str) -> None:
        """Export benchmark result to JSON.

        Args:
            result: The benchmark result.
            filepath: Output file path.
        """
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(result.to_dict(), f, indent=2, default=str)
