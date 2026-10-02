"""Latency optimization system.

Provides latency profiling, optimization strategies, and real-time
performance monitoring for model routing decisions.
"""

from __future__ import annotations

import logging
import statistics
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Deque, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class LatencyTier(Enum):
    """Latency classification tiers."""

    ULTRA_LOW = "ultra_low"  # <100ms
    LOW = "low"  # <500ms
    MEDIUM = "medium"  # <2000ms
    HIGH = "high"  # <10000ms
    UNACCEPTABLE = "unacceptable"  # >=10000ms


@dataclass
class LatencyProfile:
    """Latency profile for a model.

    Attributes:
        model_name: Name of the model.
        p50_ms: 50th percentile latency.
        p95_ms: 95th percentile latency.
        p99_ms: 99th percentile latency.
        mean_ms: Mean latency.
        std_dev_ms: Standard deviation of latency.
        sample_count: Number of samples.
        last_updated: When the profile was last updated.
    """

    model_name: str
    p50_ms: float = 0.0
    p95_ms: float = 0.0
    p99_ms: float = 0.0
    mean_ms: float = 0.0
    std_dev_ms: float = 0.0
    sample_count: int = 0
    last_updated: float = 0.0

    @property
    def tier(self) -> LatencyTier:
        """Get latency tier based on p95.

        Returns:
            LatencyTier classification.
        """
        if self.p95_ms < 100:
            return LatencyTier.ULTRA_LOW
        elif self.p95_ms < 500:
            return LatencyTier.LOW
        elif self.p95_ms < 2000:
            return LatencyTier.MEDIUM
        elif self.p95_ms < 10000:
            return LatencyTier.HIGH
        else:
            return LatencyTier.UNACCEPTABLE

    @property
    def is_healthy(self) -> bool:
        """Check if latency is within acceptable bounds.

        Returns:
            True if p95 is under 2000ms.
        """
        return self.p95_ms < 2000


@dataclass
class LatencyConfig:
    """Configuration for latency optimization.

    Attributes:
        target_p95_ms: Target p95 latency in milliseconds.
        max_acceptable_ms: Maximum acceptable latency.
        optimization_strategy: Strategy for latency optimization.
        enable_prefetching: Whether to enable request prefetching.
        enable_parallel: Whether to enable parallel execution.
        max_concurrent_requests: Maximum concurrent requests.
        warmup_requests: Number of warmup requests on model switch.
    """

    target_p95_ms: float = 1000.0
    max_acceptable_ms: float = 5000.0
    optimization_strategy: str = "adaptive"
    enable_prefetching: bool = True
    enable_parallel: bool = True
    max_concurrent_requests: int = 10
    warmup_requests: int = 3


class LatencyOptimizer:
    """Latency optimizer for model routing.

    Tracks latency profiles for models and provides optimization
    recommendations based on real-time performance data.

    Example:
        >>> optimizer = LatencyOptimizer()
        >>> optimizer.record_latency("gpt-4o", 150.0)
        >>> profile = optimizer.get_profile("gpt-4o")
        >>> print(f"P95: {profile.p95_ms}ms")
    """

    def __init__(self, config: Optional[LatencyConfig] = None) -> None:
        """Initialize the latency optimizer.

        Args:
            config: Latency optimization configuration.
        """
        self._config = config or LatencyConfig()
        self._latency_data: Dict[str, Deque[float]] = {}
        self._profiles: Dict[str, LatencyProfile] = {}
        self._lock = threading.Lock()
        self._max_samples = 1000

    @property
    def config(self) -> LatencyConfig:
        """Get the latency configuration.

        Returns:
            The latency configuration.
        """
        return self._config

    def record_latency(self, model_name: str, latency_ms: float) -> None:
        """Record a latency measurement.

        Args:
            model_name: Name of the model.
            latency_ms: Measured latency in milliseconds.
        """
        with self._lock:
            if model_name not in self._latency_data:
                self._latency_data[model_name] = deque(maxlen=self._max_samples)

            self._latency_data[model_name].append(latency_ms)
            self._update_profile(model_name)

    def get_profile(self, model_name: str) -> Optional[LatencyProfile]:
        """Get the latency profile for a model.

        Args:
            model_name: Name of the model.

        Returns:
            LatencyProfile or None if no data exists.
        """
        return self._profiles.get(model_name)

    def get_all_profiles(self) -> Dict[str, LatencyProfile]:
        """Get all latency profiles.

        Returns:
            Dictionary mapping model names to profiles.
        """
        return dict(self._profiles)

    def get_fastest_model(self, candidates: List[str]) -> Optional[str]:
        """Get the fastest model from candidates.

        Args:
            candidates: List of model names to consider.

        Returns:
            Name of the fastest model, or None if no data.
        """
        best_model: Optional[str] = None
        best_p95 = float("inf")

        for model_name in candidates:
            profile = self._profiles.get(model_name)
            if profile and profile.p95_ms < best_p95:
                best_p95 = profile.p95_ms
                best_model = model_name

        return best_model

    def get_recommendation(
        self,
        prompt: str,
        candidates: List[str],
        max_latency_ms: Optional[float] = None,
    ) -> Tuple[str, str]:
        """Get a latency-optimized model recommendation.

        Args:
            prompt: The prompt to route.
            candidates: List of candidate model names.
            max_latency_ms: Maximum acceptable latency.

        Returns:
            Tuple of (recommended_model, reason).
        """
        target = max_latency_ms or self._config.target_p95_ms

        # Filter by latency constraint
        eligible = []
        for model_name in candidates:
            profile = self._profiles.get(model_name)
            if profile and profile.p95_ms <= target:
                eligible.append(model_name)

        if not eligible:
            # Fallback: pick the fastest available
            fastest = self.get_fastest_model(candidates)
            if fastest:
                return fastest, "fallback_fastest"
            return candidates[0], "no_latency_data"

        # Among eligible, pick the one with best latency
        best = min(eligible, key=lambda m: self._profiles[m].p95_ms)
        return best, "latency_optimized"

    def should_optimize(self, model_name: str) -> bool:
        """Check if a model needs latency optimization.

        Args:
            model_name: Name of the model.

        Returns:
            True if the model's latency exceeds targets.
        """
        profile = self._profiles.get(model_name)
        if not profile:
            return False
        return profile.p95_ms > self._config.target_p95_ms

    def get_optimization_suggestions(self, model_name: str) -> List[str]:
        """Get optimization suggestions for a model.

        Args:
            model_name: Name of the model.

        Returns:
            List of suggestion strings.
        """
        profile = self._profiles.get(model_name)
        if not profile:
            return ["No latency data available"]

        suggestions: List[str] = []

        if profile.p95_ms > self._config.max_acceptable_ms:
            suggestions.append(
                f"CRITICAL: P95 latency ({profile.p95_ms:.0f}ms) exceeds "
                f"maximum acceptable ({self._config.max_acceptable_ms:.0f}ms). "
                f"Consider switching to a faster model."
            )

        if profile.p95_ms > self._config.target_p95_ms:
            suggestions.append(
                f"P95 latency ({profile.p95_ms:.0f}ms) exceeds target "
                f"({self._config.target_p95_ms:.0f}ms). "
                f"Consider enabling prefetching or parallel execution."
            )

        if profile.std_dev_ms > profile.mean_ms * 0.5:
            suggestions.append(
                f"High latency variance (std={profile.std_dev_ms:.0f}ms). "
                f"Consider connection pooling or request batching."
            )

        if profile.tier == LatencyTier.UNACCEPTABLE:
            suggestions.append(
                "Model is in UNACCEPTABLE latency tier. "
                "Immediate action required."
            )

        if not suggestions:
            suggestions.append("Latency is within acceptable bounds.")

        return suggestions

    def compare_models(self, model_a: str, model_b: str) -> Dict[str, Any]:
        """Compare latency profiles of two models.

        Args:
            model_a: First model name.
            model_b: Second model name.

        Returns:
            Comparison dictionary.
        """
        profile_a = self._profiles.get(model_a)
        profile_b = self._profiles.get(model_b)

        if not profile_a or not profile_b:
            return {"error": "Insufficient data for comparison"}

        return {
            "model_a": model_a,
            "model_b": model_b,
            "p50_diff_ms": profile_a.p50_ms - profile_b.p50_ms,
            "p95_diff_ms": profile_a.p95_ms - profile_b.p95_ms,
            "faster_model": model_a if profile_a.p95_ms < profile_b.p95_ms else model_b,
            "speedup_factor": (
                max(profile_a.p95_ms, profile_b.p95_ms)
                / max(min(profile_a.p95_ms, profile_b.p95_ms), 1)
            ),
        }

    def reset(self, model_name: Optional[str] = None) -> None:
        """Reset latency data.

        Args:
            model_name: Model to reset. All models if None.
        """
        with self._lock:
            if model_name:
                self._latency_data.pop(model_name, None)
                self._profiles.pop(model_name, None)
            else:
                self._latency_data.clear()
                self._profiles.clear()
            logger.info("Latency data reset for: %s", model_name or "all models")

    def _update_profile(self, model_name: str) -> None:
        """Update the latency profile for a model.

        Args:
            model_name: Name of the model.
        """
        samples = list(self._latency_data[model_name])
        if not samples:
            return

        sorted_samples = sorted(samples)
        n = len(sorted_samples)

        def percentile(p: float) -> float:
            idx = int(p / 100.0 * (n - 1))
            return sorted_samples[idx]

        self._profiles[model_name] = LatencyProfile(
            model_name=model_name,
            p50_ms=percentile(50),
            p95_ms=percentile(95),
            p99_ms=percentile(99),
            mean_ms=statistics.mean(sorted_samples),
            std_dev_ms=statistics.stdev(sorted_samples) if n > 1 else 0.0,
            sample_count=n,
            last_updated=time.time(),
        )
