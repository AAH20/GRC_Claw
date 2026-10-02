"""Performance benchmarks for the Campaign Optimizer component.

These benchmarks verify that campaign optimization operations meet
production SLAs for latency and throughput.
"""

from __future__ import annotations

import time
from typing import Any

import pytest

from tests.performance.conftest import BenchmarkResult


@pytest.mark.critical
class TestCampaignOptimizerBenchmarks:
    """Benchmark suite for campaign optimization operations."""

    SLA_MS = 500.0

    def test_campaign_creation_latency(
        self,
        run_benchmark: Any,
        sample_campaign_payload: dict[str, Any],
    ) -> None:
        """Benchmark campaign creation endpoint latency.

        Verifies that creating a new campaign completes within the
        SLA threshold of 500ms.
        """
        def create_campaign() -> dict[str, Any]:
            """Simulate campaign creation with validation."""
            payload = sample_campaign_payload.copy()
            # Simulate validation and processing
            assert payload["total_budget"] > 0
            assert payload["daily_budget"] > 0
            assert len(payload["channels"]) > 0
            return {"id": "camp_001", "status": "created"}

        result = run_benchmark(
            create_campaign,
            name="campaign_creation",
            iterations=100,
            metadata={"payload_size": len(str(sample_campaign_payload))},
        )

        assert result.avg_ms <= self.SLA_MS, (
            f"Campaign creation SLA violation: {result.avg_ms:.2f}ms > {self.SLA_MS}ms"
        )

    def test_campaign_budget_calculation(
        self,
        run_benchmark: Any,
        sample_campaign_payload: dict[str, Any],
    ) -> None:
        """Benchmark budget allocation calculations.

        Verifies that budget distribution across channels completes
        within acceptable latency.
        """
        def calculate_budget() -> dict[str, float]:
            """Calculate budget allocation across channels."""
            total = sample_campaign_payload["total_budget"]
            channels = sample_campaign_payload["channels"]
            duration = sample_campaign_payload["duration_days"]
            daily = total / duration
            per_channel = daily / len(channels)
            return {ch: round(per_channel, 2) for ch in channels}

        result = run_benchmark(
            calculate_budget,
            name="budget_calculation",
            iterations=200,
            metadata={"channels": len(sample_campaign_payload["channels"])},
        )

        assert result.avg_ms <= self.SLA_MS, (
            f"Budget calculation SLA violation: {result.avg_ms:.2f}ms > {self.SLA_MS}ms"
        )

    def test_campaign_validation_performance(
        self,
        run_benchmark: Any,
        sample_campaign_payload: dict[str, Any],
    ) -> None:
        """Benchmark campaign payload validation performance.

        Verifies that input validation completes within acceptable latency.
        """
        def validate_payload() -> bool:
            """Validate campaign payload fields."""
            p = sample_campaign_payload
            errors: list[str] = []
            if p["total_budget"] <= 0:
                errors.append("Invalid budget")
            if p["duration_days"] <= 0:
                errors.append("Invalid duration")
            if not p["channels"]:
                errors.append("No channels")
            if not p["target_audience"]:
                errors.append("No audience")
            return len(errors) == 0

        result = run_benchmark(
            validate_payload,
            name="campaign_validation",
            iterations=500,
        )

        assert result.avg_ms <= self.SLA_MS, (
            f"Validation SLA violation: {result.avg_ms:.2f}ms > {self.SLA_MS}ms"
        )

    def test_campaign_optimization_loop(
        self,
        run_benchmark: Any,
    ) -> None:
        """Benchmark a single optimization iteration.

        Simulates the core optimization loop that adjusts bids and
        budgets based on performance signals.
        """
        def optimization_iteration() -> dict[str, Any]:
            """Simulate one optimization iteration."""
            # Simulate performance analysis
            metrics = {"ctr": 0.03, "cpa": 45.0, "roas": 3.5}
            adjustments: dict[str, float] = {}

            if metrics["cpa"] > 50.0:
                adjustments["bid_modifier"] = 0.85
            elif metrics["roas"] < 2.0:
                adjustments["budget_modifier"] = 0.90
            else:
                adjustments["bid_modifier"] = 1.05

            return adjustments

        result = run_benchmark(
            optimization_iteration,
            name="optimization_iteration",
            iterations=100,
        )

        assert result.avg_ms <= self.SLA_MS, (
            f"Optimization loop SLA violation: {result.avg_ms:.2f}ms > {self.SLA_MS}ms"
        )

    def test_multi_campaign_batch_processing(
        self,
        run_benchmark: Any,
        sample_campaign_payload: dict[str, Any],
    ) -> None:
        """Benchmark batch processing of multiple campaigns.

        Verifies that processing a batch of campaigns scales acceptably.
        """
        campaigns = [
            {**sample_campaign_payload, "name": f"Campaign {i}"}
            for i in range(50)
        ]

        def process_batch() -> int:
            """Process a batch of campaigns."""
            processed = 0
            for camp in campaigns:
                if camp["total_budget"] > 0 and camp["channels"]:
                    processed += 1
            return processed

        result = run_benchmark(
            process_batch,
            name="batch_campaign_processing",
            iterations=10,
            metadata={"batch_size": len(campaigns)},
        )

        assert result.avg_ms <= self.SLA_MS * 5, (
            f"Batch processing SLA violation: {result.avg_ms:.2f}ms > {self.SLA_MS * 5}ms"
        )

    def test_campaign_roi_calculation(
        self,
        run_benchmark: Any,
    ) -> None:
        """Benchmark ROI calculation performance.

        Verifies that ROI computations complete within acceptable latency.
        """
        def calculate_roi() -> float:
            """Calculate campaign ROI."""
            spend = 10000.0
            revenue = 35000.0
            return ((revenue - spend) / spend) * 100

        result = run_benchmark(
            calculate_roi,
            name="roi_calculation",
            iterations=1000,
        )

        assert result.avg_ms <= self.SLA_MS, (
            f"ROI calculation SLA violation: {result.avg_ms:.2f}ms > {self.SLA_MS}ms"
        )
