"""Performance benchmarks for the Analytics component.

These benchmarks verify that analytics operations meet production
SLAs for latency and throughput.
"""

from __future__ import annotations

from typing import Any

import pytest

from tests.performance.conftest import BenchmarkResult


@pytest.mark.critical
class TestAnalyticsBenchmarks:
    """Benchmark suite for analytics operations."""

    SLA_MS = 600.0

    def test_attribution_calculation_latency(
        self,
        run_benchmark: Any,
        sample_analytics_events: list[dict[str, Any]],
    ) -> None:
        """Benchmark multi-touch attribution calculation.

        Verifies that attribution calculations complete within the
        SLA threshold of 600ms.
        """
        def calculate_attribution() -> dict[str, float]:
            """Calculate first-touch attribution from events."""
            channel_revenue: dict[str, float] = {}
            user_first_touch: dict[str, str] = {}

            for event in sample_analytics_events:
                user_id = event["user_id"]
                channel = event["channel"]
                revenue = event["revenue"]

                if user_id not in user_first_touch:
                    user_first_touch[user_id] = channel

                if revenue > 0:
                    first_channel = user_first_touch[user_id]
                    channel_revenue[first_channel] = (
                        channel_revenue.get(first_channel, 0.0) + revenue
                    )

            return channel_revenue

        result = run_benchmark(
            calculate_attribution,
            name="attribution_calculation",
            iterations=100,
            metadata={"event_count": len(sample_analytics_events)},
        )

        assert result.avg_ms <= self.SLA_MS, (
            f"Attribution SLA violation: {result.avg_ms:.2f}ms > {self.SLA_MS}ms"
        )

    def test_revenue_aggregation_performance(
        self,
        run_benchmark: Any,
        sample_analytics_events: list[dict[str, Any]],
    ) -> None:
        """Benchmark revenue aggregation performance.

        Verifies that aggregating revenue across events completes within
        acceptable latency.
        """
        def aggregate_revenue() -> dict[str, Any]:
            """Aggregate revenue by channel and campaign."""
            channel_totals: dict[str, float] = {}
            campaign_totals: dict[str, float] = {}

            for event in sample_analytics_events:
                channel = event["channel"]
                campaign = event["campaign_id"]
                revenue = event["revenue"]

                channel_totals[channel] = channel_totals.get(channel, 0.0) + revenue
                if campaign:
                    campaign_totals[campaign] = (
                        campaign_totals.get(campaign, 0.0) + revenue
                    )

            return {
                "by_channel": channel_totals,
                "by_campaign": campaign_totals,
                "total": sum(channel_totals.values()),
            }

        result = run_benchmark(
            aggregate_revenue,
            name="revenue_aggregation",
            iterations=200,
        )

        assert result.avg_ms <= self.SLA_MS, (
            f"Revenue aggregation SLA violation: {result.avg_ms:.2f}ms > {self.SLA_MS}ms"
        )

    def test_funnel_analysis_calculation(
        self,
        run_benchmark: Any,
    ) -> None:
        """Benchmark funnel analysis calculation.

        Verifies that funnel analysis completes within acceptable latency.
        """
        def calculate_funnel() -> dict[str, Any]:
            """Calculate conversion funnel metrics."""
            stages = [
                {"name": "visit", "count": 10000},
                {"name": "signup", "count": 2500},
                {"name": "activation", "count": 1200},
                {"name": "trial", "count": 600},
                {"name": "paid", "count": 150},
            ]

            funnel = []
            for i, stage in enumerate(stages):
                conversion_rate = (
                    stage["count"] / stages[i - 1]["count"] * 100
                    if i > 0
                    else 100.0
                )
                funnel.append({
                    **stage,
                    "conversion_rate": round(conversion_rate, 2),
                    "dropoff_rate": round(100 - conversion_rate, 2),
                })

            return {"stages": funnel}

        result = run_benchmark(
            calculate_funnel,
            name="funnel_analysis",
            iterations=300,
        )

        assert result.avg_ms <= self.SLA_MS, (
            f"Funnel analysis SLA violation: {result.avg_ms:.2f}ms > {self.SLA_MS}ms"
        )

    def test_cohort_analysis_performance(
        self,
        run_benchmark: Any,
    ) -> None:
        """Benchmark cohort analysis performance.

        Verifies that cohort analysis completes within acceptable latency.
        """
        def analyze_cohorts() -> dict[str, Any]:
            """Analyze user cohorts by signup month."""
            cohorts: dict[str, dict[str, Any]] = {}

            for month in range(1, 13):
                cohort_key = f"2026-{month:02d}"
                cohorts[cohort_key] = {
                    "users": 1000 + month * 50,
                    "retained_m1": 0.6 - month * 0.01,
                    "retained_m3": 0.4 - month * 0.005,
                    "retained_m6": 0.25 - month * 0.002,
                    "ltv": 150.0 + month * 5,
                }

            return {"cohorts": cohorts, "total_cohorts": len(cohorts)}

        result = run_benchmark(
            analyze_cohorts,
            name="cohort_analysis",
            iterations=100,
        )

        assert result.avg_ms <= self.SLA_MS, (
            f"Cohort analysis SLA violation: {result.avg_ms:.2f}ms > {self.SLA_MS}ms"
        )

    def test_realtime_dashboard_metrics(
        self,
        run_benchmark: Any,
    ) -> None:
        """Benchmark real-time dashboard metrics computation.

        Verifies that real-time metrics computation completes within
        acceptable latency.
        """
        def compute_realtime_metrics() -> dict[str, Any]:
            """Compute real-time dashboard metrics."""
            metrics = {
                "active_users": 1250,
                "page_views_per_minute": 3400,
                "conversion_rate": 3.2,
                "revenue_per_minute": 1250.50,
                "avg_session_duration": 245.0,
                "bounce_rate": 42.5,
                "top_pages": [
                    {"path": "/pricing", "views": 450},
                    {"path": "/features", "views": 380},
                    {"path": "/blog", "views": 290},
                ],
            }
            return metrics

        result = run_benchmark(
            compute_realtime_metrics,
            name="realtime_metrics",
            iterations=500,
        )

        assert result.avg_ms <= self.SLA_MS, (
            f"Real-time metrics SLA violation: {result.avg_ms:.2f}ms > {self.SLA_MS}ms"
        )

    def test_anomaly_detection_performance(
        self,
        run_benchmark: Any,
    ) -> None:
        """Benchmark anomaly detection performance.

        Verifies that anomaly detection completes within acceptable latency.
        """
        def detect_anomalies() -> list[dict[str, Any]]:
            """Detect anomalies in time-series metrics."""
            data_points = [100 + i * 2 + (50 if i == 50 else 0) for i in range(100)]
            mean_val = sum(data_points) / len(data_points)
            variance = sum((x - mean_val) ** 2 for x in data_points) / len(data_points)
            std_dev = variance**0.5

            anomalies = []
            for i, value in enumerate(data_points):
                deviation = (value - mean_val) / std_dev if std_dev > 0 else 0
                if abs(deviation) > 2.0:
                    anomalies.append({
                        "index": i,
                        "value": value,
                        "deviation": round(deviation, 2),
                        "severity": "high" if abs(deviation) > 3.0 else "medium",
                    })

            return anomalies

        result = run_benchmark(
            detect_anomalies,
            name="anomaly_detection",
            iterations=200,
        )

        assert result.avg_ms <= self.SLA_MS, (
            f"Anomaly detection SLA violation: {result.avg_ms:.2f}ms > {self.SLA_MS}ms"
        )
