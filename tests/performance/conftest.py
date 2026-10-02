"""Shared fixtures and configuration for performance benchmarks.

This module provides pytest fixtures used across all performance benchmark
test suites in the GRC_Claw project. It includes utilities for timing,
memory profiling, and SLA threshold validation.
"""

from __future__ import annotations

import statistics
import time
from dataclasses import dataclass, field
from typing import Any, Callable, TypeVar

import pytest

# ---------------------------------------------------------------------------
# SLA Thresholds (milliseconds) — production-grade performance budgets
# ---------------------------------------------------------------------------

SLA_THRESHOLDS_MS: dict[str, float] = {
    "campaign_optimizer": 500.0,
    "lead_scorer": 200.0,
    "journey_orchestrator": 800.0,
    "content_generator": 1000.0,
    "sales_automator": 400.0,
    "analytics": 600.0,
    "social_media": 300.0,
    "email_marketing": 350.0,
    "ppc_manager": 450.0,
}

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class BenchmarkResult:
    """Container for a single benchmark measurement.

    Attributes:
        name: Human-readable benchmark identifier.
        duration_ms: Wall-clock execution time in milliseconds.
        iterations: Number of iterations performed.
        metadata: Arbitrary extra context (e.g., payload size, model used).
    """

    name: str
    duration_ms: float
    iterations: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def avg_ms(self) -> float:
        """Average time per iteration in milliseconds."""
        return self.duration_ms / max(self.iterations, 1)


@dataclass
class BenchmarkSuite:
    """Aggregated results from a collection of benchmarks.

    Attributes:
        suite_name: Name of the benchmark suite.
        results: List of individual benchmark results.
    """

    suite_name: str
    results: list[BenchmarkResult] = field(default_factory=list)

    def add(self, result: BenchmarkResult) -> None:
        """Add a benchmark result to the suite."""
        self.results.append(result)

    @property
    def total_duration_ms(self) -> float:
        """Total wall-clock time for all benchmarks in the suite."""
        return sum(r.duration_ms for r in self.results)

    @property
    def avg_duration_ms(self) -> float:
        """Mean duration across all benchmarks."""
        if not self.results:
            return 0.0
        return statistics.mean(r.duration_ms for r in self.results)

    @property
    def p95_duration_ms(self) -> float:
        """95th-percentile duration across all benchmarks."""
        if not self.results:
            return 0.0
        sorted_durations = sorted(r.duration_ms for r in self.results)
        idx = int(len(sorted_durations) * 0.95)
        idx = min(idx, len(sorted_durations) - 1)
        return sorted_durations[idx]

    def to_dict(self) -> dict[str, Any]:
        """Serialize the suite to a plain dictionary."""
        return {
            "suite_name": self.suite_name,
            "total_duration_ms": round(self.total_duration_ms, 3),
            "avg_duration_ms": round(self.avg_duration_ms, 3),
            "p95_duration_ms": round(self.p95_duration_ms, 3),
            "benchmark_count": len(self.results),
            "results": [
                {
                    "name": r.name,
                    "duration_ms": round(r.duration_ms, 3),
                    "iterations": r.iterations,
                    "avg_ms": round(r.avg_ms, 3),
                    "metadata": r.metadata,
                }
                for r in self.results
            ],
        }


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def benchmark_timer() -> Callable[[], float]:
    """Return a high-resolution timer function.

    Returns:
        A callable that returns the current monotonic time in seconds.
    """
    return time.monotonic


@pytest.fixture
def run_benchmark() -> Callable[..., BenchmarkResult]:
    """Factory fixture that produces a benchmark runner.

    The returned callable executes a function *iterations* times and
    returns a :class:`BenchmarkResult` with timing metadata.

    Returns:
        A callable ``run_benchmark(func, name, iterations=1, **kwargs)``
        that produces a :class:`BenchmarkResult`.
    """

    def _run(
        func: Callable[..., Any],
        *,
        name: str,
        iterations: int = 1,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> BenchmarkResult:
        """Execute *func* and measure wall-clock time.

        Args:
            func: The callable to benchmark.
            name: Human-readable benchmark name.
            iterations: Number of times to call *func*.
            metadata: Extra context to attach to the result.
            **kwargs: Keyword arguments forwarded to *func*.

        Returns:
            A :class:`BenchmarkResult` with timing data.

        Raises:
            ValueError: If *iterations* is less than 1.
        """
        if iterations < 1:
            raise ValueError("iterations must be >= 1")

        start = time.perf_counter()
        for _ in range(iterations):
            func(**kwargs)
        elapsed_ms = (time.perf_counter() - start) * 1000

        return BenchmarkResult(
            name=name,
            duration_ms=elapsed_ms,
            iterations=iterations,
            metadata=metadata or {},
        )

    return _run


@pytest.fixture
def benchmark_suite() -> BenchmarkSuite:
    """Create an empty benchmark suite for aggregating results.

    Returns:
        A new :class:`BenchmarkSuite` instance.
    """
    return BenchmarkSuite(suite_name="default")


@pytest.fixture
def sla_threshold() -> Callable[[str], float]:
    """Return a callable that looks up SLA thresholds by component name.

    Returns:
        A callable ``sla_threshold(component) -> float`` that returns the
        SLA budget in milliseconds for the given component.
    """

    def _get(component: str) -> float:
        """Return the SLA threshold for *component*.

        Args:
            component: Component identifier (e.g., ``"lead_scorer"``).

        Returns:
            SLA threshold in milliseconds. Defaults to ``1000.0`` if the
            component is not found.
        """
        return SLA_THRESHOLDS_MS.get(component, 1000.0)

    return _get


@pytest.fixture
def assert_sla() -> Callable[[BenchmarkResult, str], None]:
    """Return a callable that asserts a benchmark meets its SLA.

    Returns:
        A callable ``assert_sla(result, component)`` that raises
        :class:`AssertionError` if the benchmark exceeds the SLA threshold.
    """

    def _assert(result: BenchmarkResult, component: str) -> None:
        """Assert that *result* meets the SLA for *component*.

        Args:
            result: The benchmark result to check.
            component: Component identifier used to look up the SLA.

        Raises:
            AssertionError: If the benchmark's average duration exceeds
                the SLA threshold.
        """
        threshold = SLA_THRESHOLDS_MS.get(component, 1000.0)
        assert result.avg_ms <= threshold, (
            f"SLA violation: {result.name} took {result.avg_ms:.2f}ms "
            f"(threshold: {threshold:.2f}ms)"
        )

    return _assert


# ---------------------------------------------------------------------------
# Sample data fixtures — reused across benchmark suites
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_campaign_payload() -> dict[str, Any]:
    """Return a representative campaign payload for benchmarking.

    Returns:
        Dictionary with realistic campaign creation data.
    """
    return {
        "name": "Q4 Product Launch",
        "description": "Enterprise product launch campaign for Q4 2026",
        "goals": ["awareness", "conversion", "retention"],
        "total_budget": 50000.0,
        "daily_budget": 1666.67,
        "channels": ["search", "social", "display", "email"],
        "duration_days": 30,
        "target_audience": {
            "demographics": {
                "age_ranges": ["25-34", "35-44"],
                "locations": ["US", "CA", "UK"],
            },
            "interests": ["technology", "SaaS", "productivity"],
        },
        "brand_voice": "professional",
        "key_message": "Transform your workflow with AI-powered automation",
        "industry": "technology",
    }


@pytest.fixture
def sample_lead_data() -> dict[str, Any]:
    """Return a representative lead payload for benchmarking.

    Returns:
        Dictionary with realistic lead scoring input data.
    """
    return {
        "lead_id": "lead_001",
        "company_name": "Acme Corp",
        "firmographic_score": 85.0,
        "technographic_score": 72.0,
        "intent_score": 91.0,
        "engagement_score": 68.0,
        "timing_score": 77.0,
        "evidence_confidence": 0.85,
    }


@pytest.fixture
def sample_journey_input() -> dict[str, Any]:
    """Return a representative journey design input for benchmarking.

    Returns:
        Dictionary with realistic journey design parameters.
    """
    return {
        "business_goal": "Increase trial-to-paid conversion by 25%",
        "target_audience": "B2B SaaS decision makers at mid-market companies",
        "constraints": {
            "max_stages": 5,
            "preferred_channels": ["email", "in sms", "push"],
            "brand_voice": "helpful and authoritative",
        },
        "existing_journeys": ["onboarding_v2", "trial_expiry"],
    }


@pytest.fixture
def sample_content_strategy() -> dict[str, Any]:
    """Return a representative content strategy for benchmarking.

    Returns:
        Dictionary with realistic content generation parameters.
    """
    return {
        "content_type": "blog_post",
        "topic": "AI in marketing",
        "target_audience": "Marketing managers at B2B companies",
        "tone": "professional yet approachable",
        "angle": "Practical applications of AI in daily marketing workflows",
        "key_messages": [
            "AI reduces manual work by 40%",
            "Personalization at scale is achievable",
            "ROI is measurable within 30 days",
        ],
        "word_count_target": 1500,
        "seo_recommendations": {
            "primary_keyword": "AI marketing tools",
            "secondary_keywords": ["AI automation", "marketing AI"],
            "meta_description": "Discover how AI transforms marketing operations.",
        },
        "content_outline": [
            {"heading": "Introduction", "word_count": 200},
            {"heading": "The State of AI in Marketing", "word_count": 400},
            {"heading": "Practical Applications", "word_count": 500},
            {"heading": "Measuring ROI", "word_count": 300},
            {"heading": "Conclusion", "word_count": 100},
        ],
    }


@pytest.fixture
def sample_prospect_data() -> dict[str, Any]:
    """Return a representative sales prospect for benchmarking.

    Returns:
        Dictionary with realistic prospect data.
    """
    return {
        "id": "prospect_001",
        "name": "Jane Smith",
        "company": "TechStart Inc",
        "title": "VP of Marketing",
        "email": "jane@techstart.com",
        "linkedin_url": "https://linkedin.com/in/janesmith",
        "company_size": 150,
        "industry": "SaaS",
        "source": "linkedin",
    }


@pytest.fixture
def sample_analytics_events() -> list[dict[str, Any]]:
    """Return a list of representative analytics events for benchmarking.

    Returns:
        List of event dictionaries with realistic marketing event data.
    """
    return [
        {
            "event_id": f"evt_{i:04d}",
            "source": "google_analytics",
            "event_type": "page_view" if i % 3 == 0 else "click",
            "timestamp": f"2026-10-01T{i % 24:02d}:00:00Z",
            "user_id": f"user_{i % 50:03d}",
            "campaign_id": f"campaign_{i % 5}",
            "channel": ["organic", "paid_search", "social", "email", "direct"][i % 5],
            "revenue": 99.99 if i % 7 == 0 else 0.0,
        }
        for i in range(100)
    ]


@pytest.fixture
def sample_social_payload() -> dict[str, Any]:
    """Return a representative social media payload for benchmarking.

    Returns:
        Dictionary with realistic social media scheduling data.
    """
    return {
        "platforms": ["twitter", "instagram", "linkedin"],
        "start_date": "2026-10-01T00:00:00Z",
        "posts_per_day": 2,
        "posts": [
            {"id": f"post_{i:03d}", "text": f"Sample post content {i}"}
            for i in range(10)
        ],
    }


@pytest.fixture
def sample_email_campaign() -> dict[str, Any]:
    """Return a representative email campaign for benchmarking.

    Returns:
        Dictionary with realistic email campaign data.
    """
    return {
        "campaign_id": "email_001",
        "subject": "Welcome to GRC_Claw",
        "template": "welcome_v2",
        "recipient_count": 5000,
        "segments": ["new_users", "trial_users"],
        "personalization": {
            "first_name": True,
            "company": True,
            "last_active": True,
        },
        "schedule": {"send_at": "2026-10-01T09:00:00Z", "timezone": "US/Eastern"},
    }


@pytest.fixture
def sample_ppc_campaigns() -> list[dict[str, Any]]:
    """Return a list of representative PPC campaigns for benchmarking.

    Returns:
        List of campaign dictionaries with realistic PPC data.
    """
    return [
        {
            "campaign_id": f"ppc_{i:03d}",
            "name": f"Campaign {i}",
            "current_bid": 1.50 + i * 0.10,
            "ctr": 0.02 + i * 0.005,
            "conversion_rate": 0.03 + i * 0.002,
            "cpa": 45.0 + i * 2.0,
            "target_cpa": 40.0,
            "budget": 1000.0 + i * 100,
            "spend": 500.0 + i * 50,
        }
        for i in range(10)
    ]


# ---------------------------------------------------------------------------
# Pytest hooks
# ---------------------------------------------------------------------------


def pytest_configure(config: Any) -> None:
    """Register custom markers for benchmark categorization."""
    config.addinivalue_line(
        "markers",
        "slow: marks benchmarks that take longer than 1 second to run",
    )
    config.addinivalue_line(
        "markers",
        "critical: marks benchmarks for critical-path components",
    )
