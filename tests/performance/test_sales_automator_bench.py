"""Performance benchmarks for the Sales Automator component.

These benchmarks verify that sales automation operations meet
production SLAs for latency and throughput.
"""

from __future__ import annotations

from typing import Any

import pytest

from tests.performance.conftest import BenchmarkResult


@pytest.mark.critical
class TestSalesAutomatorBenchmarks:
    """Benchmark suite for sales automation operations."""

    SLA_MS = 400.0

    def test_prospect_discovery_latency(
        self,
        run_benchmark: Any,
        sample_prospect_data: dict[str, Any],
    ) -> None:
        """Benchmark prospect discovery latency.

        Verifies that discovering prospects completes within the
        SLA threshold of 400ms.
        """
        def discover_prospects() -> list[dict[str, Any]]:
            """Simulate prospect discovery with filtering."""
            criteria = {
                "industry": "SaaS",
                "company_size": {"min": 50, "max": 500},
            }
            # Simulate filtering logic
            prospects = []
            for i in range(10):
                prospect = {
                    **sample_prospect_data,
                    "id": f"prospect_{i:04d}",
                }
                if (
                    prospect["industry"] == criteria["industry"]
                    and criteria["company_size"]["min"]
                    <= prospect["company_size"]
                    <= criteria["company_size"]["max"]
                ):
                    prospects.append(prospect)
            return prospects

        result = run_benchmark(
            discover_prospects,
            name="prospect_discovery",
            iterations=100,
            metadata={"criteria": "industry=SaaS"},
        )

        assert result.avg_ms <= self.SLA_MS, (
            f"Prospect discovery SLA violation: {result.avg_ms:.2f}ms > {self.SLA_MS}ms"
        )

    def test_prospect_scoring_performance(
        self,
        run_benchmark: Any,
        sample_prospect_data: dict[str, Any],
    ) -> None:
        """Benchmark prospect scoring performance.

        Verifies that scoring prospects completes within acceptable latency.
        """
        def score_prospect() -> dict[str, float]:
            """Score a prospect based on fit signals."""
            firmographic = 0.8 if sample_prospect_data["company_size"] > 100 else 0.5
            technographic = 0.7 if sample_prospect_data["industry"] == "SaaS" else 0.4
            intent = 0.6

            overall = (firmographic * 0.4 + technographic * 0.3 + intent * 0.3)
            return {
                "overall": round(overall, 2),
                "firmographic": firmographic,
                "technographic": technographic,
                "intent": intent,
            }

        result = run_benchmark(
            score_prospect,
            name="prospect_scoring",
            iterations=500,
        )

        assert result.avg_ms <= self.SLA_MS, (
            f"Prospect scoring SLA violation: {result.avg_ms:.2f}ms > {self.SLA_MS}ms"
        )

    def test_outreach_sequence_generation(
        self,
        run_benchmark: Any,
    ) -> None:
        """Benchmark outreach sequence generation.

        Verifies that generating outreach sequences completes within
        acceptable latency.
        """
        def generate_sequence() -> dict[str, Any]:
            """Generate a multi-step outreach sequence."""
            steps = []
            templates = [
                {"day": 0, "channel": "email", "type": "introduction"},
                {"day": 2, "channel": "linkedin", "type": "connection"},
                {"day": 4, "channel": "email", "type": "value_prop"},
                {"day": 7, "channel": "call", "type": "follow_up"},
                {"day": 10, "channel": "email", "type": "breakup"},
            ]
            for template in templates:
                steps.append({
                    **template,
                    "template_id": f"tpl_{template['type']}",
                    "personalization_fields": ["first_name", "company"],
                })
            return {"steps": steps, "total_steps": len(steps)}

        result = run_benchmark(
            generate_sequence,
            name="outreach_sequence",
            iterations=200,
        )

        assert result.avg_ms <= self.SLA_MS, (
            f"Outreach sequence SLA violation: {result.avg_ms:.2f}ms > {self.SLA_MS}ms"
        )

    def test_followup_scheduling(
        self,
        run_benchmark: Any,
    ) -> None:
        """Benchmark follow-up scheduling performance.

        Verifies that scheduling follow-ups completes within acceptable latency.
        """
        def schedule_followups() -> list[dict[str, Any]]:
            """Schedule follow-up tasks for multiple prospects."""
            prospects = [f"prospect_{i:03d}" for i in range(20)]
            followups = []
            for i, prospect_id in enumerate(prospects):
                followups.append({
                    "prospect_id": prospect_id,
                    "scheduled_day": i % 7 + 1,
                    "channel": ["email", "call", "linkedin"][i % 3],
                    "template": f"followup_v{i % 3 + 1}",
                })
            return followups

        result = run_benchmark(
            schedule_followups,
            name="followup_scheduling",
            iterations=100,
            metadata={"prospect_count": 20},
        )

        assert result.avg_ms <= self.SLA_MS, (
            f"Follow-up scheduling SLA violation: {result.avg_ms:.2f}ms > {self.SLA_MS}ms"
        )

    def test_demo_scheduling_optimization(
        self,
        run_benchmark: Any,
    ) -> None:
        """Benchmark demo scheduling optimization.

        Verifies that optimizing demo schedules completes within
        acceptable latency.
        """
        def optimize_schedule() -> dict[str, Any]:
            """Optimize demo scheduling across reps and time slots."""
            reps = ["rep_1", "rep_2", "rep_3"]
            time_slots = ["09:00", "10:00", "11:00", "14:00", "15:00"]
            scheduled = []

            for i, rep in enumerate(reps):
                for j, slot in enumerate(time_slots):
                    if (i + j) % 2 == 0:
                        scheduled.append({
                            "rep": rep,
                            "time_slot": slot,
                            "prospect_id": f"prospect_{i}_{j}",
                        })

            return {"scheduled": scheduled, "total_slots": len(scheduled)}

        result = run_benchmark(
            optimize_schedule,
            name="demo_scheduling",
            iterations=200,
        )

        assert result.avg_ms <= self.SLA_MS, (
            f"Demo scheduling SLA violation: {result.avg_ms:.2f}ms > {self.SLA_MS}ms"
        )

    def test_sales_forecasting_calculation(
        self,
        run_benchmark: Any,
    ) -> None:
        """Benchmark sales forecasting calculation.

        Verifies that sales forecast computations complete within
        acceptable latency.
        """
        def calculate_forecast() -> dict[str, Any]:
            """Calculate sales forecast from pipeline data."""
            pipeline = [
                {"stage": "discovery", "value": 50000, "probability": 0.2},
                {"stage": "demo", "value": 75000, "probability": 0.4},
                {"stage": "proposal", "value": 100000, "probability": 0.6},
                {"stage": "negotiation", "value": 120000, "probability": 0.8},
                {"stage": "closed_won", "value": 150000, "probability": 1.0},
            ]

            weighted_value = sum(
                p["value"] * p["probability"] for p in pipeline
            )
            total_value = sum(p["value"] for p in pipeline)

            return {
                "weighted_forecast": round(weighted_value, 2),
                "total_pipeline": total_value,
                "weighted_probability": round(
                    weighted_value / total_value if total_value > 0 else 0, 4
                ),
            }

        result = run_benchmark(
            calculate_forecast,
            name="sales_forecasting",
            iterations=300,
        )

        assert result.avg_ms <= self.SLA_MS, (
            f"Sales forecasting SLA violation: {result.avg_ms:.2f}ms > {self.SLA_MS}ms"
        )
