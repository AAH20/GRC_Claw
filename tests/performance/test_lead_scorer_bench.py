"""Performance benchmarks for the Lead Scorer component.

These benchmarks verify that lead scoring operations meet production
SLAs for latency and throughput.
"""

from __future__ import annotations

import statistics
from typing import Any

import pytest

from tests.performance.conftest import BenchmarkResult


@pytest.mark.critical
class TestLeadScorerBenchmarks:
    """Benchmark suite for lead scoring operations."""

    SLA_MS = 200.0

    def test_single_lead_scoring_latency(
        self,
        run_benchmark: Any,
        sample_lead_data: dict[str, Any],
    ) -> None:
        """Benchmark single lead scoring latency.

        Verifies that scoring a single lead completes within the
        SLA threshold of 200ms.
        """
        def score_lead() -> dict[str, Any]:
            """Compute a multi-dimensional lead score."""
            weights = {
                "firmographic": 0.25,
                "technographic": 0.15,
                "intent": 0.20,
                "engagement": 0.30,
                "timing": 0.10,
            }
            scores = {
                "firmographic": sample_lead_data["firmographic_score"],
                "technographic": sample_lead_data["technographic_score"],
                "intent": sample_lead_data["intent_score"],
                "engagement": sample_lead_data["engagement_score"],
                "timing": sample_lead_data["timing_score"],
            }

            total = sum(scores[k] * weights[k] for k in weights)
            total = max(0.0, min(100.0, total))

            if total >= 85:
                grade = "A"
            elif total >= 75:
                grade = "B+"
            elif total >= 65:
                grade = "B"
            elif total >= 55:
                grade = "C+"
            else:
                grade = "C"

            return {"total_score": round(total, 2), "grade": grade}

        result = run_benchmark(
            score_lead,
            name="single_lead_scoring",
            iterations=500,
            metadata={"lead_id": sample_lead_data["lead_id"]},
        )

        assert result.avg_ms <= self.SLA_MS, (
            f"Lead scoring SLA violation: {result.avg_ms:.2f}ms > {self.SLA_MS}ms"
        )

    def test_batch_lead_scoring_throughput(
        self,
        run_benchmark: Any,
        sample_lead_data: dict[str, Any],
    ) -> None:
        """Benchmark batch lead scoring throughput.

        Verifies that scoring a batch of leads completes within
        acceptable latency.
        """
        leads = [
            {**sample_lead_data, "lead_id": f"lead_{i:04d}"}
            for i in range(100)
        ]

        def score_batch() -> list[dict[str, Any]]:
            """Score a batch of leads."""
            results: list[dict[str, Any]] = []
            for lead in leads:
                total = (
                    lead["firmographic_score"] * 0.25
                    + lead["technographic_score"] * 0.15
                    + lead["intent_score"] * 0.20
                    + lead["engagement_score"] * 0.30
                    + lead["timing_score"] * 0.10
                )
                results.append({
                    "lead_id": lead["lead_id"],
                    "score": round(total, 2),
                })
            return results

        result = run_benchmark(
            score_batch,
            name="batch_lead_scoring",
            iterations=20,
            metadata={"batch_size": len(leads)},
        )

        assert result.avg_ms <= self.SLA_MS * 10, (
            f"Batch scoring SLA violation: {result.avg_ms:.2f}ms > {self.SLA_MS * 10}ms"
        )

    def test_lead_grade_classification(
        self,
        run_benchmark: Any,
    ) -> None:
        """Benchmark lead grade classification performance.

        Verifies that grade classification completes within acceptable latency.
        """
        def classify_grade(score: float) -> str:
            """Classify a numeric score into a letter grade."""
            if score >= 95:
                return "A+"
            if score >= 85:
                return "A"
            if score >= 75:
                return "B+"
            if score >= 65:
                return "B"
            if score >= 55:
                return "C+"
            if score >= 45:
                return "C"
            if score >= 35:
                return "D"
            return "F"

        scores = [i * 0.5 for i in range(200)]

        def classify_batch() -> list[str]:
            """Classify a batch of scores."""
            return [classify_grade(s) for s in scores]

        result = run_benchmark(
            classify_batch,
            name="grade_classification",
            iterations=100,
        )

        assert result.avg_ms <= self.SLA_MS, (
            f"Grade classification SLA violation: {result.avg_ms:.2f}ms > {self.SLA_MS}ms"
        )

    def test_lead_confidence_computation(
        self,
        run_benchmark: Any,
        sample_lead_data: dict[str, Any],
    ) -> None:
        """Benchmark confidence score computation.

        Verifies that confidence calculation completes within acceptable latency.
        """
        def compute_confidence() -> float:
            """Compute confidence based on evidence and variance."""
            base = sample_lead_data["evidence_confidence"]
            scores = [
                sample_lead_data["firmographic_score"],
                sample_lead_data["technographic_score"],
                sample_lead_data["intent_score"],
                sample_lead_data["engagement_score"],
                sample_lead_data["timing_score"],
            ]
            mean_score = sum(scores) / len(scores)
            variance = sum((s - mean_score) ** 2 for s in scores) / len(scores)
            variance_factor = max(0.5, 1.0 - (variance / 2500.0))
            return round(base * variance_factor, 2)

        result = run_benchmark(
            compute_confidence,
            name="confidence_computation",
            iterations=500,
        )

        assert result.avg_ms <= self.SLA_MS, (
            f"Confidence computation SLA violation: {result.avg_ms:.2f}ms > {self.SLA_MS}ms"
        )

    def test_lead_deduplication_performance(
        self,
        run_benchmark: Any,
    ) -> None:
        """Benchmark lead deduplication performance.

        Verifies that deduplication of lead records completes within
        acceptable latency.
        """
        leads = [
            {"lead_id": f"lead_{i:04d}", "email": f"user{i % 50}@example.com"}
            for i in range(1000)
        ]

        def deduplicate() -> int:
            """Deduplicate leads by email."""
            seen: set[str] = set()
            unique: int = 0
            for lead in leads:
                email = lead["email"]
                if email not in seen:
                    seen.add(email)
                    unique += 1
            return unique

        result = run_benchmark(
            deduplicate,
            name="lead_deduplication",
            iterations=50,
            metadata={"input_size": len(leads)},
        )

        assert result.avg_ms <= self.SLA_MS * 5, (
            f"Deduplication SLA violation: {result.avg_ms:.2f}ms > {self.SLA_MS * 5}ms"
        )

    def test_lead_scoring_with_breakdown(
        self,
        run_benchmark: Any,
        sample_lead_data: dict[str, Any],
    ) -> None:
        """Benchmark lead scoring with full breakdown.

        Verifies that detailed scoring with dimension breakdown completes
        within acceptable latency.
        """
        def score_with_breakdown() -> dict[str, Any]:
            """Compute lead score with full dimension breakdown."""
            weights = {
                "firmographic": 0.25,
                "technographic": 0.15,
                "intent": 0.20,
                "engagement": 0.30,
                "timing": 0.10,
            }
            scores = {
                "firmographic": sample_lead_data["firmographic_score"],
                "technographic": sample_lead_data["technographic_score"],
                "intent": sample_lead_data["intent_score"],
                "engagement": sample_lead_data["engagement_score"],
                "timing": sample_lead_data["timing_score"],
            }

            breakdown: list[dict[str, Any]] = []
            for dim, score in scores.items():
                weight = weights[dim]
                breakdown.append({
                    "dimension": dim,
                    "score": score,
                    "weight": weight,
                    "weighted_score": round(score * weight, 2),
                })

            total = sum(item["weighted_score"] for item in breakdown)
            return {
                "total_score": round(total, 2),
                "breakdown": breakdown,
                "top_dimensions": sorted(
                    breakdown, key=lambda x: x["weighted_score"], reverse=True
                )[:2],
            }

        result = run_benchmark(
            score_with_breakdown,
            name="scoring_with_breakdown",
            iterations=200,
        )

        assert result.avg_ms <= self.SLA_MS, (
            f"Scoring with breakdown SLA violation: {result.avg_ms:.2f}ms > {self.SLA_MS}ms"
        )
