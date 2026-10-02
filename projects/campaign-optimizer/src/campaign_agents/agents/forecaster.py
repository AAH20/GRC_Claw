"""Time-Series Forecaster Agent — Campaign performance forecasting with multiple methods."""
from __future__ import annotations

import math
import statistics
from datetime import datetime, timedelta

import structlog

from campaign_agents.models.optimization import (
    ForecastConfig,
    ForecastGranularity,
    ForecastMethod,
    ForecastPoint,
    ForecastResult,
    TimeSeriesPoint,
)

logger = structlog.get_logger(__name__)


class TimeSeriesForecaster:
    """Time-series forecaster for campaign performance prediction.

    Supports multiple forecasting methods including moving average,
    exponential smoothing, linear regression, and seasonal decomposition.
    """

    def __init__(self, config: ForecastConfig) -> None:
        """Initialize the forecaster.

        Args:
            config: Forecast configuration.

        Raises:
            ValueError: If config is invalid.
        """
        self._validate_config(config)
        self.config = config
        self._historical_data: list[TimeSeriesPoint] = []
        self._forecast_history: list[ForecastResult] = []

        logger.info(
            "Forecaster initialized",
            method=config.method.value,
            granularity=config.granularity.value,
            horizon=config.horizon,
        )

    def _validate_config(self, config: ForecastConfig) -> None:
        """Validate forecast configuration.

        Args:
            config: Configuration to validate.

        Raises:
            ValueError: If configuration is invalid.
        """
        if config.horizon < 1:
            raise ValueError("Horizon must be at least 1")
        if not (0 < config.confidence_level < 1):
            raise ValueError("Confidence level must be between 0 and 1")
        if config.smoothing_alpha < 0 or config.smoothing_alpha > 1:
            raise ValueError("Smoothing alpha must be between 0 and 1")

    def add_data_point(self, point: TimeSeriesPoint) -> None:
        """Add a historical data point.

        Args:
            point: The time-series data point to add.
        """
        self._historical_data.append(point)
        self._historical_data.sort(key=lambda p: p.timestamp)

    def add_data_points(self, points: list[TimeSeriesPoint]) -> None:
        """Add multiple historical data points.

        Args:
            points: List of time-series data points.
        """
        for point in points:
            self.add_data_point(point)

    def forecast(self, campaign_id: str, metric: str = "conversions") -> ForecastResult:
        """Generate a forecast for the specified metric.

        Args:
            campaign_id: Campaign identifier.
            metric: Metric name to forecast.

        Returns:
            ForecastResult with predicted values and confidence intervals.

        Raises:
            ValueError: If insufficient data is available.
        """
        if len(self._historical_data) < 3:
            raise ValueError(
                f"Need at least 3 data points for forecasting, got {len(self._historical_data)}"
            )

        values = [p.value for p in self._historical_data]

        if self.config.method == ForecastMethod.MOVING_AVERAGE:
            forecast_values = self._moving_average_forecast(values)
        elif self.config.method == ForecastMethod.EXPONENTIAL_SMOOTHING:
            forecast_values = self._exponential_smoothing_forecast(values)
        elif self.config.method == ForecastMethod.LINEAR_REGRESSION:
            forecast_values = self._linear_regression_forecast(values)
        elif self.config.method == ForecastMethod.SEASONAL_DECOMPOSITION:
            forecast_values = self._seasonal_decomposition_forecast(values)
        else:
            raise ValueError(f"Unknown forecasting method: {self.config.method}")

        forecast_points = self._build_forecast_points(forecast_values)
        mape = self._calculate_mape(values, forecast_values)
        rmse = self._calculate_rmse(values, forecast_values)
        trend = self._detect_trend(values)
        seasonality = self._detect_seasonality(values)

        result = ForecastResult(
            campaign_id=campaign_id,
            metric=metric,
            method=self.config.method,
            granularity=self.config.granularity,
            historical_points=len(values),
            forecast_points=forecast_points,
            mape=mape,
            rmse=rmse,
            trend_direction=trend,
            seasonality_detected=seasonality,
        )

        self._forecast_history.append(result)
        logger.info(
            "Forecast generated",
            campaign_id=campaign_id,
            metric=metric,
            horizon=self.config.horizon,
            mape=mape,
        )
        return result

    def _moving_average_forecast(self, values: list[float]) -> list[float]:
        """Simple moving average forecast.

        Args:
            values: Historical values.

        Returns:
            Forecasted values.
        """
        window = min(7, len(values))
        if window == 0:
            return [0.0] * self.config.horizon

        recent_avg = statistics.mean(values[-window:])
        return [recent_avg] * self.config.horizon

    def _exponential_smoothing_forecast(self, values: list[float]) -> list[float]:
        """Holt-Winters exponential smoothing forecast.

        Args:
            values: Historical values.

        Returns:
            Forecasted values.
        """
        alpha = self.config.smoothing_alpha
        beta = self.config.smoothing_beta

        if len(values) < 2:
            return [values[0] if values else 0.0] * self.config.horizon

        level = values[0]
        trend = values[1] - values[0]

        for i in range(1, len(values)):
            prev_level = level
            level = alpha * values[i] + (1 - alpha) * (level + trend)
            trend = beta * (level - prev_level) + (1 - beta) * trend

        forecasts = []
        for h in range(1, self.config.horizon + 1):
            forecasts.append(level + h * trend)

        return forecasts

    def _linear_regression_forecast(self, values: list[float]) -> list[float]:
        """Linear regression forecast.

        Args:
            values: Historical values.

        Returns:
            Forecasted values.
        """
        n = len(values)
        if n < 2:
            return [values[0] if values else 0.0] * self.config.horizon

        x_mean = (n - 1) / 2
        y_mean = statistics.mean(values)

        numerator = sum((i - x_mean) * (v - y_mean) for i, v in enumerate(values))
        denominator = sum((i - x_mean) ** 2 for i in range(n))

        slope = 0 if denominator == 0 else numerator / denominator

        intercept = y_mean - slope * x_mean

        forecasts = []
        for h in range(1, self.config.horizon + 1):
            forecasts.append(intercept + slope * (n - 1 + h))

        return forecasts

    def _seasonal_decomposition_forecast(self, values: list[float]) -> list[float]:
        """Seasonal decomposition forecast.

        Args:
            values: Historical values.

        Returns:
            Forecasted values.
        """
        period = self.config.seasonality_period or 7
        if len(values) < period * 2:
            return self._moving_average_forecast(values)

        # Calculate seasonal indices
        seasonal_averages = []
        for i in range(period):
            season_values = [values[j] for j in range(i, len(values), period)]
            seasonal_averages.append(statistics.mean(season_values) if season_values else 0)

        overall_mean = statistics.mean(seasonal_averages) if seasonal_averages else 1
        seasonal_indices = [
            s / overall_mean if overall_mean > 0 else 1.0 for s in seasonal_averages
        ]

        # Deseasonalize and trend
        deseasonalized = [
            values[i] / seasonal_indices[i % period] for i in range(len(values))
        ]

        # Fit trend on deseasonalized data
        trend_forecasts = self._linear_regression_forecast(deseasonalized)

        # Reapply seasonality
        n = len(values)
        forecasts = []
        for h in range(1, self.config.horizon + 1):
            seasonal_idx = (n - 1 + h) % period
            forecasts.append(trend_forecasts[h - 1] * seasonal_indices[seasonal_idx])

        return forecasts

    def _build_forecast_points(self, values: list[float]) -> list[ForecastPoint]:
        """Build forecast points with confidence intervals.

        Args:
            values: Forecasted values.

        Returns:
            List of ForecastPoint objects.
        """
        points = []
        last_timestamp = datetime.fromisoformat(self._historical_data[-1].timestamp)
        interval = self._get_interval_timedelta()

        # Calculate standard error from historical data
        hist_values = [p.value for p in self._historical_data]
        if len(hist_values) > 1:
            std_err = statistics.stdev(hist_values) / math.sqrt(len(hist_values))
        else:
            std_err = 0.0

        z_score = self._z_score_for_confidence(self.config.confidence_level)

        for i, value in enumerate(values):
            timestamp = last_timestamp + interval * (i + 1)
            margin = z_score * std_err * math.sqrt(i + 1)
            points.append(
                ForecastPoint(
                    timestamp=timestamp.isoformat(),
                    value=max(0.0, value),
                    lower_bound=max(0.0, value - margin),
                    upper_bound=value + margin,
                    confidence=self.config.confidence_level,
                )
            )

        return points

    def _get_interval_timedelta(self) -> timedelta:
        """Get timedelta for the configured granularity.

        Returns:
            Timedelta matching the granularity.
        """
        if self.config.granularity == ForecastGranularity.HOURLY:
            return timedelta(hours=1)
        elif self.config.granularity == ForecastGranularity.DAILY:
            return timedelta(days=1)
        elif self.config.granularity == ForecastGranularity.WEEKLY:
            return timedelta(weeks=1)
        elif self.config.granularity == ForecastGranularity.MONTHLY:
            return timedelta(days=30)
        else:
            return timedelta(days=1)

    def _z_score_for_confidence(self, confidence: float) -> float:
        """Get z-score for a confidence level.

        Args:
            confidence: Confidence level (0-1).

        Returns:
            Approximate z-score.
        """
        # Common z-scores
        z_scores = {
            0.90: 1.645,
            0.95: 1.96,
            0.99: 2.576,
        }
        return z_scores.get(confidence, 1.96)

    def _calculate_mape(self, actual: list[float], predicted: list[float]) -> float | None:
        """Calculate Mean Absolute Percentage Error.

        Args:
            actual: Actual values.
            predicted: Predicted values.

        Returns:
            MAPE value or None if not calculable.
        """
        if len(actual) != len(predicted) or not actual:
            return None

        ape_sum = 0.0
        count = 0
        for a, p in zip(actual, predicted, strict=True):
            if a > 0:
                ape_sum += abs((a - p) / a)
                count += 1

        if count == 0:
            return None
        return (ape_sum / count) * 100

    def _calculate_rmse(self, actual: list[float], predicted: list[float]) -> float | None:
        """Calculate Root Mean Squared Error.

        Args:
            actual: Actual values.
            predicted: Predicted values.

        Returns:
            RMSE value or None if not calculable.
        """
        if len(actual) != len(predicted) or not actual:
            return None

        mse = sum((a - p) ** 2 for a, p in zip(actual, predicted, strict=True)) / len(actual)
        return math.sqrt(mse)

    def _detect_trend(self, values: list[float]) -> str:
        """Detect trend direction in historical data.

        Args:
            values: Historical values.

        Returns:
            Trend direction: "increasing", "decreasing", or "stable".
        """
        if len(values) < 3:
            return "stable"

        # Simple linear regression slope
        n = len(values)
        x_mean = (n - 1) / 2
        y_mean = statistics.mean(values)

        numerator = sum((i - x_mean) * (v - y_mean) for i, v in enumerate(values))
        denominator = sum((i - x_mean) ** 2 for i in range(n))

        if denominator == 0:
            return "stable"

        slope = numerator / denominator
        threshold = y_mean * 0.05 if y_mean > 0 else 0.1

        if slope > threshold:
            return "increasing"
        elif slope < -threshold:
            return "decreasing"
        else:
            return "stable"

    def _detect_seasonality(self, values: list[float]) -> bool:
        """Detect seasonality in historical data.

        Args:
            values: Historical values.

        Returns:
            True if seasonality is detected.
        """
        period = self.config.seasonality_period or 7
        if len(values) < period * 2:
            return False

        # Check autocorrelation at seasonal lag
        n = len(values)
        mean_val = statistics.mean(values)

        numerator = sum(
            (values[i] - mean_val) * (values[i + period] - mean_val)
            for i in range(n - period)
        )
        denominator = sum((v - mean_val) ** 2 for v in values)

        if denominator == 0:
            return False

        autocorr = numerator / denominator
        return autocorr > 0.3

    def get_historical_data(self) -> list[TimeSeriesPoint]:
        """Get all historical data points.

        Returns:
            List of TimeSeriesPoint objects.
        """
        return list(self._historical_data)

    def get_forecast_history(self) -> list[ForecastResult]:
        """Get forecast history.

        Returns:
            List of ForecastResult objects.
        """
        return list(self._forecast_history)

    def clear_data(self) -> None:
        """Clear all historical data."""
        self._historical_data.clear()
        self._forecast_history.clear()
        logger.info("Forecaster data cleared")
