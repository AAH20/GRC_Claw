"""
Trend Analysis — statistical trend detection and forecasting for GRC_Claw metrics.

Provides linear regression, moving average, exponential smoothing,
seasonal decomposition, change point detection, and volatility analysis.
"""

from __future__ import annotations

import statistics
from typing import Any

from .metrics_registry import get_metric
from .models import (
    ForecastMethod,
    MetricValue,
    Prediction,
    PredictionConfidence,
    PredictiveModel,
    TrendAnalysis,
    TrendDirection,
)


class LinearRegression:
    """Simple linear regression for trend fitting."""

    @staticmethod
    def fit(x: list[float], y: list[float]) -> tuple[float, float, float]:
        """
        Fit y = slope * x + intercept.

        Returns (slope, intercept, r_squared).
        """
        n = len(x)
        if n < 2:
            return 0.0, y[0] if y else 0.0, 0.0

        mean_x = statistics.mean(x)
        mean_y = statistics.mean(y)

        ss_xx = sum((xi - mean_x) ** 2 for xi in x)
        ss_yy = sum((yi - mean_y) ** 2 for yi in y)
        ss_xy = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))

        if ss_xx == 0:
            return 0.0, mean_y, 0.0

        slope = ss_xy / ss_xx
        intercept = mean_y - slope * mean_x

        # R-squared
        if ss_yy == 0:
            r_squared = 1.0
        else:
            r_squared = (ss_xy ** 2) / (ss_xx * ss_yy)

        return slope, intercept, round(max(0.0, min(1.0, r_squared)), 4)

    @staticmethod
    def predict(slope: float, intercept: float, x: float) -> float:
        """Predict y for a given x."""
        return slope * x + intercept


class MovingAverage:
    """Moving average forecasting."""

    @staticmethod
    def compute(values: list[float], window: int = 7) -> list[float]:
        """Compute moving average series."""
        if not values or window <= 0:
            return []
        result = []
        for i in range(len(values)):
            start = max(0, i - window + 1)
            result.append(round(statistics.mean(values[start:i + 1]), 4))
        return result

    @staticmethod
    def forecast(values: list[float], window: int = 7, periods: int = 1) -> list[float]:
        """Forecast future values using moving average."""
        if not values:
            return [0.0] * periods
        ma = MovingAverage.compute(values, window)
        last_ma = ma[-1] if ma else values[-1]
        return [round(last_ma, 4)] * periods


class ExponentialSmoothing:
    """Exponential smoothing forecasting (Holt-Winters simplified)."""

    @staticmethod
    def compute(values: list[float], alpha: float = 0.3) -> list[float]:
        """Compute exponentially smoothed series."""
        if not values:
            return []
        result = [values[0]]
        for i in range(1, len(values)):
            smoothed = alpha * values[i] + (1 - alpha) * result[-1]
            result.append(round(smoothed, 4))
        return result

    @staticmethod
    def forecast(values: list[float], alpha: float = 0.3, periods: int = 1) -> list[float]:
        """Forecast future values using exponential smoothing."""
        if not values:
            return [0.0] * periods
        smoothed = ExponentialSmoothing.compute(values, alpha)
        last = smoothed[-1] if smoothed else values[-1]
        return [round(last, 4)] * periods


class SeasonalDecomposition:
    """Simple seasonal decomposition."""

    @staticmethod
    def detect_seasonality(values: list[float], max_period: int = 12) -> tuple[bool, int | None]:
        """
        Detect seasonality using autocorrelation.

        Returns (has_seasonality, period).
        """
        if len(values) < 4:
            return False, None

        mean_val = statistics.mean(values)
        n = len(values)

        best_period = None
        best_correlation = 0.0

        for period in range(2, min(max_period + 1, n // 2)):
            # Compute autocorrelation at lag=period
            numerator = sum(
                (values[i] - mean_val) * (values[i - period] - mean_val)
                for i in range(period, n)
            )
            denominator = sum((v - mean_val) ** 2 for v in values)

            if denominator == 0:
                continue

            correlation = numerator / denominator
            if correlation > best_correlation and correlation > 0.3:
                best_correlation = correlation
                best_period = period

        return (best_period is not None, best_period)


class ChangePointDetector:
    """Detect significant change points in time series."""

    @staticmethod
    def detect(values: list[float], threshold_std: float = 2.0) -> list[dict[str, Any]]:
        """
        Detect change points using cumulative sum (CUSUM) approach.

        Returns list of change point descriptions.
        """
        if len(values) < 5:
            return []

        mean_val = statistics.mean(values)
        std_dev = statistics.stdev(values) if len(values) >= 2 else 0.0

        if std_dev == 0:
            return []

        change_points = []
        cusum_pos = 0.0
        cusum_neg = 0.0
        k = 0.5 * std_dev  # reference value

        for i, val in enumerate(values):
            normalized = (val - mean_val) / std_dev
            cusum_pos = max(0, cusum_pos + normalized - k)
            cusum_neg = min(0, cusum_neg + normalized + k)

            if cusum_pos > threshold_std or abs(cusum_neg) > threshold_std:
                change_points.append({
                    "index": i,
                    "value": val,
                    "direction": "up" if cusum_pos > threshold_std else "down",
                    "magnitude": round(normalized, 2),
                })
                cusum_pos = 0.0
                cusum_neg = 0.0

        return change_points


class TrendAnalyzer:
    """
    Main trend analysis engine. Analyzes metric time series for trends,
    seasonality, change points, and generates forecasts.
    """

    def __init__(self):
        self.regression = LinearRegression()
        self.moving_avg = MovingAverage()
        self.exp_smoothing = ExponentialSmoothing()
        self.seasonal = SeasonalDecomposition()
        self.change_detector = ChangePointDetector()

    def analyze(
        self,
        metric_id: str,
        values: list[MetricValue],
        forecast_periods: int = 3,
    ) -> TrendAnalysis | None:
        """
        Perform complete trend analysis on a metric's time series.
        """
        metric_def = get_metric(metric_id)
        if not metric_def or len(values) < 2:
            return None

        raw_values = [v.value for v in values]
        x = list(range(len(raw_values)))

        # Linear regression
        slope, intercept, r_squared = self.regression.fit(x, raw_values)

        # Trend direction
        direction = self._classify_trend(slope, r_squared, raw_values)

        # Change points
        change_points = self.change_detector.detect(raw_values)

        # Seasonality
        has_season, season_period = self.seasonal.detect_seasonality(raw_values)

        # Volatility
        volatility = self._compute_volatility(raw_values)

        # Change percentage
        if len(raw_values) >= 2 and raw_values[0] != 0:
            change_pct = round(
                ((raw_values[-1] - raw_values[0]) / abs(raw_values[0])) * 100, 2
            )
        else:
            change_pct = 0.0

        # Forecast next value
        forecast_next = self.regression.predict(slope, intercept, len(raw_values))
        forecast_confidence = r_squared

        # Generate insights
        insights = self._generate_insights(
            metric_id, metric_def.name, direction, slope, r_squared,
            volatility, change_points, has_season, season_period, raw_values,
        )

        return TrendAnalysis(
            metric_id=metric_id,
            metric_name=metric_def.name,
            category=metric_def.category,
            direction=direction,
            slope=round(slope, 6),
            intercept=round(intercept, 4),
            r_squared=r_squared,
            p_value=0.0,  # Would need proper statistical test
            data_points=len(raw_values),
            period_start=values[0].timestamp if values else "",
            period_end=values[-1].timestamp if values else "",
            change_pct=change_pct,
            volatility=volatility,
            seasonality_detected=has_season,
            seasonality_period=season_period,
            change_points=change_points,
            forecast_next=round(forecast_next, 4) if forecast_next is not None else None,
            forecast_confidence=round(forecast_confidence, 4),
            insights=insights,
        )

    def _classify_trend(
        self, slope: float, r_squared: float, values: list[float]
    ) -> TrendDirection:
        """Classify trend direction from regression results."""
        if len(values) < 3:
            return TrendDirection.STABLE

        # Check volatility first
        if len(values) >= 2:
            mean_val = statistics.mean(values)
            if mean_val != 0:
                cv = statistics.stdev(values) / abs(mean_val)
                if cv > 0.3:
                    return TrendDirection.VOLATILE

        # Use R-squared to determine if trend is significant
        if r_squared < 0.1:
            return TrendDirection.STABLE

        # Classify based on slope direction
        if slope > 0:
            return TrendDirection.IMPROVING
        elif slope < 0:
            return TrendDirection.DEGRADING
        else:
            return TrendDirection.STABLE

    def _compute_volatility(self, values: list[float]) -> float:
        """Compute coefficient of variation as volatility."""
        if len(values) < 2:
            return 0.0
        mean_val = statistics.mean(values)
        if mean_val == 0:
            return 0.0
        return round((statistics.stdev(values) / abs(mean_val)) * 100, 2)

    def _generate_insights(
        self,
        metric_id: str,
        metric_name: str,
        direction: TrendDirection,
        slope: float,
        r_squared: float,
        volatility: float,
        change_points: list[dict[str, Any]],
        has_season: bool,
        season_period: int | None,
        values: list[float],
    ) -> list[str]:
        """Generate human-readable insights from trend analysis."""
        insights: list[str] = []

        if direction == TrendDirection.IMPROVING:
            insights.append(f"{metric_name} is improving (slope: {slope:.4f})")
        elif direction == TrendDirection.DEGRADING:
            insights.append(f"{metric_name} is degrading (slope: {slope:.4f})")
        elif direction == TrendDirection.VOLATILE:
            insights.append(f"{metric_name} shows high volatility ({volatility}%)")
        else:
            insights.append(f"{metric_name} is stable")

        if r_squared > 0.7:
            insights.append(f"Strong trend fit (R²={r_squared:.2f})")
        elif r_squared > 0.3:
            insights.append(f"Moderate trend fit (R²={r_squared:.2f})")
        else:
            insights.append(f"Weak trend fit (R²={r_squared:.2f}) — trend may not be significant")

        if change_points:
            insights.append(f"{len(change_points)} significant change point(s) detected")

        if has_season and season_period:
            insights.append(f"Seasonal pattern detected with period={season_period}")

        if volatility > 30:
            insights.append(f"High volatility ({volatility}%) — consider investigating root causes")

        # Compare last value to mean
        if values:
            mean_val = statistics.mean(values)
            last_val = values[-1]
            if mean_val != 0:
                deviation = ((last_val - mean_val) / abs(mean_val)) * 100
                if abs(deviation) > 20:
                    direction_word = "above" if deviation > 0 else "below"
                    insights.append(
                        f"Current value is {abs(deviation):.1f}% {direction_word} mean"
                    )

        return insights

    def forecast(
        self,
        metric_id: str,
        values: list[MetricValue],
        method: ForecastMethod = ForecastMethod.LINEAR_REGRESSION,
        periods: int = 3,
        confidence: float = 0.95,
    ) -> PredictiveModel | None:
        """
        Generate a predictive model for a metric.
        """
        metric_def = get_metric(metric_id)
        if not metric_def or len(values) < 2:
            return None

        raw_values = [v.value for v in values]
        x = list(range(len(raw_values)))

        # Fit model based on method
        if method == ForecastMethod.LINEAR_REGRESSION:
            slope, intercept, r_squared = self.regression.fit(x, raw_values)
            predictions = []
            for i in range(periods):
                pred = self.regression.predict(slope, intercept, len(raw_values) + i)
                # Confidence interval based on residual std
                residuals = [
                    raw_values[j] - self.regression.predict(slope, intercept, j)
                    for j in range(len(raw_values))
                ]
                residual_std = statistics.stdev(residuals) if len(residuals) >= 2 else 0.0
                z_score = 1.96 if confidence >= 0.95 else 1.645  # 95% or 90%
                margin = z_score * residual_std

                period_label = f"period_{i + 1}"
                predictions.append(Prediction(
                    period=period_label,
                    predicted_value=round(pred, 4),
                    lower_bound=round(pred - margin, 4),
                    upper_bound=round(pred + margin, 4),
                    confidence=confidence,
                    method=method,
                ))

            model_accuracy = r_squared

        elif method == ForecastMethod.MOVING_AVG:
            ma_preds = self.moving_avg.forecast(raw_values, window=min(7, len(raw_values)), periods=periods)
            predictions = []
            for i, pred in enumerate(ma_preds):
                predictions.append(Prediction(
                    period=f"period_{i + 1}",
                    predicted_value=round(pred, 4),
                    lower_bound=round(pred * 0.9, 4),
                    upper_bound=round(pred * 1.1, 4),
                    confidence=confidence,
                    method=method,
                ))
            model_accuracy = 0.7  # Moving average baseline

        elif method == ForecastMethod.EXPONENTIAL_SMOOTHING:
            es_preds = self.exp_smoothing.forecast(raw_values, alpha=0.3, periods=periods)
            predictions = []
            for i, pred in enumerate(es_preds):
                predictions.append(Prediction(
                    period=f"period_{i + 1}",
                    predicted_value=round(pred, 4),
                    lower_bound=round(pred * 0.85, 4),
                    upper_bound=round(pred * 1.15, 4),
                    confidence=confidence,
                    method=method,
                ))
            model_accuracy = 0.75  # Exponential smoothing baseline

        else:
            # Default to linear regression
            return self.forecast(metric_id, values, ForecastMethod.LINEAR_REGRESSION, periods, confidence)

        # Determine confidence level
        if model_accuracy >= 0.8:
            conf_level = PredictionConfidence.HIGH
        elif model_accuracy >= 0.5:
            conf_level = PredictionConfidence.MEDIUM
        else:
            conf_level = PredictionConfidence.LOW

        return PredictiveModel(
            metric_id=metric_id,
            metric_name=metric_def.name,
            category=metric_def.category,
            method=method,
            confidence_level=conf_level,
            model_accuracy=round(model_accuracy, 4),
            training_data_points=len(raw_values),
            predictions=predictions,
            model_metadata={
                "slope": slope if method == ForecastMethod.LINEAR_REGRESSION else None,
                "intercept": intercept if method == ForecastMethod.LINEAR_REGRESSION else None,
                "r_squared": r_squared if method == ForecastMethod.LINEAR_REGRESSION else None,
                "data_points": len(raw_values),
            },
        )
