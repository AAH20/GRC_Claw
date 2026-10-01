"""
Trend analysis for GRC_Claw.

Statistical trend analysis with linear regression, seasonality detection,
change point detection, and volatility analysis. Provides actionable
insights for metric trajectories.
"""

from __future__ import annotations

import logging
import statistics
import math
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from .models import (
    MetricCategory,
    MetricValue,
    TrendAnalysis,
    TrendDirection,
)

logger = logging.getLogger(__name__)


@dataclass
class TrendConfig:
    """Configuration for trend analysis."""

    min_data_points: int = 5
    max_data_points: int = 365
    confidence_level: float = 0.95
    seasonality_threshold: float = 0.3
    change_point_threshold: float = 2.0
    volatility_window: int = 10
    smoothing_factor: float = 0.3
    detect_seasonality: bool = True
    detect_change_points: bool = True
    forecast_horizon: int = 5


@dataclass
class TrendSummary:
    """Summary of trend analysis across all metrics."""

    total_analyzed: int = 0
    improving_count: int = 0
    stable_count: int = 0
    degrading_count: int = 0
    volatile_count: int = 0
    seasonality_detected_count: int = 0
    change_points_detected: int = 0
    avg_r_squared: float = 0.0
    analyses: list[TrendAnalysis] = field(default_factory=list)
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_analyzed": self.total_analyzed,
            "improving_count": self.improving_count,
            "stable_count": self.stable_count,
            "degrading_count": self.degrading_count,
            "volatile_count": self.volatile_count,
            "seasonality_detected_count": self.seasonality_detected_count,
            "change_points_detected": self.change_points_detected,
            "avg_r_squared": self.avg_r_squared,
            "analyses": [a.to_dict() for a in self.analyses],
            "generated_at": self.generated_at,
        }


class TrendAnalyzer:
    """
    Statistical trend analyzer for GRC metrics.

    Capabilities:
    - Linear regression with R-squared and p-value estimation
    - Moving average smoothing
    - Seasonality detection via autocorrelation
    - Change point detection using CUSUM
    - Volatility analysis (coefficient of variation)
    - Short-term forecasting
    - Automated insight generation
    """

    def __init__(self, config: Optional[TrendConfig] = None):
        self.config = config or TrendConfig()
        self._analyses: dict[str, TrendAnalysis] = {}

    # ─── Core Analysis ──────────────────────────────────────────────────────

    def analyze(
        self,
        metric_id: str,
        metric_name: str,
        category: MetricCategory,
        values: list[MetricValue],
    ) -> Optional[TrendAnalysis]:
        """
        Perform complete trend analysis on a metric's history.

        Returns None if insufficient data points.
        """
        if len(values) < self.config.min_data_points:
            logger.debug(
                "Insufficient data for trend analysis on %s: %d points",
                metric_id,
                len(values),
            )
            return None

        # Extract numeric series
        data = [v.value for v in values[-self.config.max_data_points:]]
        timestamps = [v.timestamp for v in values[-self.config.max_data_points:]]

        # Linear regression
        slope, intercept, r_squared, p_value = self._linear_regression(data)

        # Direction classification
        direction = self._classify_direction(slope, intercept, data)

        # Change percentage
        change_pct = self._compute_change_pct(data)

        # Volatility
        volatility = self._compute_volatility(data)

        # Seasonality
        seasonality_detected = False
        seasonality_period = None
        if self.config.detect_seasonality and len(data) >= 12:
            seasonality_detected, seasonality_period = self._detect_seasonality(data)

        # Change points
        change_points = []
        if self.config.detect_change_points and len(data) >= 10:
            change_points = self._detect_change_points(data)

        # Forecast next value
        forecast_next = self._forecast_next(data, slope, intercept)

        # Confidence
        forecast_confidence = self._compute_forecast_confidence(data, r_squared)

        # Insights
        insights = self._generate_insights(
            metric_id, direction, change_pct, volatility,
            seasonality_detected, change_points, r_squared,
        )

        analysis = TrendAnalysis(
            metric_id=metric_id,
            metric_name=metric_name,
            category=category,
            direction=direction,
            slope=round(slope, 6),
            intercept=round(intercept, 4),
            r_squared=round(r_squared, 4),
            p_value=round(p_value, 6),
            data_points=len(data),
            period_start=timestamps[0] if timestamps else "",
            period_end=timestamps[-1] if timestamps else "",
            change_pct=round(change_pct, 2),
            volatility=round(volatility, 2),
            seasonality_detected=seasonality_detected,
            seasonality_period=seasonality_period,
            change_points=change_points,
            forecast_next=round(forecast_next, 4) if forecast_next is not None else None,
            forecast_confidence=round(forecast_confidence, 2),
            insights=insights,
        )

        self._analyses[metric_id] = analysis
        return analysis

    def analyze_all(
        self,
        metrics_data: dict[str, list[MetricValue]],
        metric_names: Optional[dict[str, str]] = None,
        categories: Optional[dict[str, MetricCategory]] = None,
    ) -> TrendSummary:
        """
        Analyze trends for all metrics.

        Args:
            metrics_data: Dict mapping metric_id to list of MetricValue
            metric_names: Optional dict mapping metric_id to display name
            categories: Optional dict mapping metric_id to category
        """
        metric_names = metric_names or {}
        categories = categories or {}

        analyses = []
        for metric_id, values in metrics_data.items():
            name = metric_names.get(metric_id, metric_id)
            category = categories.get(metric_id, MetricCategory.OPERATIONAL_PERFORMANCE)
            analysis = self.analyze(metric_id, name, category, values)
            if analysis:
                analyses.append(analysis)

        return self._summarize(analyses)

    # ─── Linear Regression ──────────────────────────────────────────────────

    def _linear_regression(
        self, data: list[float]
    ) -> tuple[float, float, float, float]:
        """
        Simple linear regression: y = slope * x + intercept.

        Returns (slope, intercept, r_squared, p_value).
        """
        n = len(data)
        if n < 2:
            return 0.0, data[0] if data else 0.0, 0.0, 1.0

        x_mean = (n - 1) / 2
        y_mean = statistics.mean(data)

        ss_xy = sum((i - x_mean) * (y - y_mean) for i, y in enumerate(data))
        ss_xx = sum((i - x_mean) ** 2 for i in range(n))
        ss_yy = sum((y - y_mean) ** 2 for y in data)

        if ss_xx == 0:
            return 0.0, y_mean, 0.0, 1.0

        slope = ss_xy / ss_xx
        intercept = y_mean - slope * x_mean

        # R-squared
        if ss_yy == 0:
            r_squared = 1.0
        else:
            r_squared = (ss_xy ** 2) / (ss_xx * ss_yy)

        # P-value approximation (simplified)
        if n > 2 and r_squared < 1.0:
            t_stat = abs(slope) * math.sqrt(ss_xx) / math.sqrt(ss_yy / (n - 2)) if ss_yy > 0 else 0
            # Simplified p-value from t-statistic
            p_value = max(0.001, min(1.0, 2 * (1 - self._t_cdf(t_stat, n - 2))))
        else:
            p_value = 0.0

        return slope, intercept, r_squared, p_value

    def _t_cdf(self, t: float, df: int) -> float:
        """Approximate t-distribution CDF."""
        # Simplified approximation
        if df <= 0:
            return 0.5
        x = df / (df + t * t)
        # Incomplete beta approximation
        return 1 - 0.5 * x ** (df / 2)

    # ─── Direction Classification ───────────────────────────────────────────

    def _classify_direction(
        self, slope: float, intercept: float, data: list[float]
    ) -> TrendDirection:
        """Classify the trend direction."""
        if len(data) < 2:
            return TrendDirection.STABLE

        y_mean = statistics.mean(data)
        if y_mean == 0:
            return TrendDirection.STABLE

        # Relative slope
        relative_slope = (slope * len(data)) / y_mean * 100

        # Check volatility first
        if len(data) >= 5:
            std_dev = statistics.stdev(data)
            cv = (std_dev / abs(y_mean) * 100) if y_mean != 0 else 0
            if cv > 30:
                return TrendDirection.VOLATILE

        if abs(relative_slope) < 2.0:
            return TrendDirection.STABLE
        elif relative_slope > 0:
            return TrendDirection.IMPROVING
        else:
            return TrendDirection.DEGRADING

    # ─── Change Percentage ──────────────────────────────────────────────────

    def _compute_change_pct(self, data: list[float]) -> float:
        """Compute percentage change from first to last value."""
        if len(data) < 2 or data[0] == 0:
            return 0.0
        return ((data[-1] - data[0]) / abs(data[0])) * 100

    # ─── Volatility ─────────────────────────────────────────────────────────

    def _compute_volatility(self, data: list[float]) -> float:
        """Compute coefficient of variation as volatility measure."""
        if len(data) < 2:
            return 0.0
        mean = statistics.mean(data)
        if mean == 0:
            return 0.0
        std_dev = statistics.stdev(data)
        return (std_dev / abs(mean)) * 100

    # ─── Seasonality Detection ──────────────────────────────────────────────

    def _detect_seasonality(
        self, data: list[float]
    ) -> tuple[bool, Optional[int]]:
        """
        Detect seasonality using autocorrelation.

        Returns (is_seasonal, period).
        """
        n = len(data)
        if n < 12:
            return False, None

        mean = statistics.mean(data)
        centered = [x - mean for x in data]

        # Compute autocorrelation for different lags
        max_lag = min(n // 2, 52)
        autocorrs = []

        for lag in range(1, max_lag + 1):
            c = sum(centered[i] * centered[i + lag] for i in range(n - lag))
            autocorrs.append(c)

        if not autocorrs:
            return False, None

        # Normalize
        total = sum(a * a for a in autocorrs)
        if total == 0:
            return False, None

        normalized = [a / total for a in autocorrs]

        # Find peaks
        threshold = self.config.seasonality_threshold
        peaks = []
        for i in range(1, len(normalized) - 1):
            if normalized[i] > threshold and normalized[i] > normalized[i - 1] and normalized[i] > normalized[i + 1]:
                peaks.append((i + 1, normalized[i]))

        if peaks:
            # Return the strongest peak
            best_peak = max(peaks, key=lambda x: x[1])
            return True, best_peak[0]

        return False, None

    # ─── Change Point Detection ─────────────────────────────────────────────

    def _detect_change_points(self, data: list[float]) -> list[dict[str, Any]]:
        """
        Detect change points using CUSUM (Cumulative Sum) method.

        Returns list of change point descriptions.
        """
        if len(data) < 10:
            return []

        mean = statistics.mean(data)
        std_dev = statistics.stdev(data)

        if std_dev == 0:
            return []

        # CUSUM
        cusum_pos = 0.0
        cusum_neg = 0.0
        threshold = self.config.change_point_threshold * std_dev
        change_points = []

        for i, value in enumerate(data):
            normalized = (value - mean) / std_dev
            cusum_pos = max(0, cusum_pos + normalized - 0.5)
            cusum_neg = min(0, cusum_neg + normalized + 0.5)

            if cusum_pos > threshold:
                change_points.append({
                    "index": i,
                    "type": "upward_shift",
                    "value": value,
                    "magnitude": round(cusum_pos, 2),
                })
                cusum_pos = 0.0
            elif abs(cusum_neg) > threshold:
                change_points.append({
                    "index": i,
                    "type": "downward_shift",
                    "value": value,
                    "magnitude": round(abs(cusum_neg), 2),
                })
                cusum_neg = 0.0

        return change_points

    # ─── Forecasting ────────────────────────────────────────────────────────

    def _forecast_next(
        self, data: list[float], slope: float, intercept: float
    ) -> Optional[float]:
        """Forecast the next value using linear regression."""
        if len(data) < 2:
            return None
        next_x = len(data)
        return slope * next_x + intercept

    def _compute_forecast_confidence(self, data: list[float], r_squared: float) -> float:
        """Compute confidence level for forecast."""
        if len(data) < 3:
            return 0.3

        # Base confidence on R-squared and data volume
        base_confidence = r_squared
        volume_bonus = min(0.2, len(data) / 100)
        return min(0.95, base_confidence + volume_bonus)

    # ─── Insight Generation ─────────────────────────────────────────────────

    def _generate_insights(
        self,
        metric_id: str,
        direction: TrendDirection,
        change_pct: float,
        volatility: float,
        seasonality_detected: bool,
        change_points: list[dict[str, Any]],
        r_squared: float,
    ) -> list[str]:
        """Generate human-readable insights from trend analysis."""
        insights = []

        # Direction insight
        if direction == TrendDirection.IMPROVING:
            insights.append(f"Metric is improving with {change_pct:.1f}% positive change")
        elif direction == TrendDirection.DEGRADING:
            insights.append(f"Metric is degrading with {abs(change_pct):.1f}% decline — attention required")
        elif direction == TrendDirection.VOLATILE:
            insights.append(f"Metric shows high volatility ({volatility:.1f}% CV) — investigate root causes")
        else:
            insights.append("Metric is stable with no significant trend")

        # Volatility insight
        if volatility > 25:
            insights.append(f"High volatility detected ({volatility:.1f}%) — consider smoothing or investigation")

        # Seasonality insight
        if seasonality_detected:
            insights.append("Seasonal pattern detected — consider seasonal adjustment for forecasting")

        # Change point insight
        if change_points:
            insights.append(f"{len(change_points)} significant change point(s) detected in the series")

        # Model fit insight
        if r_squared > 0.7:
            insights.append(f"Strong linear fit (R²={r_squared:.2f}) — trend is reliable")
        elif r_squared < 0.3:
            insights.append(f"Weak linear fit (R²={r_squared:.2f}) — trend may not be meaningful")

        return insights

    # ─── Summary ────────────────────────────────────────────────────────────

    def _summarize(self, analyses: list[TrendAnalysis]) -> TrendSummary:
        """Create a summary of all trend analyses."""
        if not analyses:
            return TrendSummary()

        improving = sum(1 for a in analyses if a.direction == TrendDirection.IMPROVING)
        stable = sum(1 for a in analyses if a.direction == TrendDirection.STABLE)
        degrading = sum(1 for a in analyses if a.direction == TrendDirection.DEGRADING)
        volatile = sum(1 for a in analyses if a.direction == TrendDirection.VOLATILE)
        seasonal = sum(1 for a in analyses if a.seasonality_detected)
        total_change_points = sum(len(a.change_points) for a in analyses)
        avg_r2 = statistics.mean(a.r_squared for a in analyses)

        return TrendSummary(
            total_analyzed=len(analyses),
            improving_count=improving,
            stable_count=stable,
            degrading_count=degrading,
            volatile_count=volatile,
            seasonality_detected_count=seasonal,
            change_points_detected=total_change_points,
            avg_r_squared=round(avg_r2, 4),
            analyses=analyses,
        )

    # ─── Query Methods ──────────────────────────────────────────────────────

    def get_analysis(self, metric_id: str) -> Optional[TrendAnalysis]:
        """Get the latest analysis for a metric."""
        return self._analyses.get(metric_id)

    def get_degrading_metrics(self) -> list[TrendAnalysis]:
        """Get all metrics with degrading trends."""
        return [
            a for a in self._analyses.values()
            if a.direction == TrendDirection.DEGRADING
        ]

    def get_volatile_metrics(self) -> list[TrendAnalysis]:
        """Get all metrics with volatile trends."""
        return [
            a for a in self._analyses.values()
            if a.direction == TrendDirection.VOLATILE
        ]

    def get_metrics_with_change_points(self) -> list[TrendAnalysis]:
        """Get all metrics with detected change points."""
        return [
            a for a in self._analyses.values()
            if a.change_points
        ]
