"""Predictive Analytics Agent - ML-based forecasting for marketing metrics."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

import numpy as np
import structlog
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import TimeSeriesSplit, cross_val_score
from sklearn.preprocessing import StandardScaler

from attribution.agents.data_collection import RawDataPoint

logger = structlog.get_logger(__name__)


@dataclass
class ForecastResult:
    """Result of a forecast for a single metric."""

    metric_name: str
    forecast_values: list[float]
    confidence_intervals: list[tuple[float, float]]
    dates: list[datetime]
    model_name: str
    mape: float
    rmse: float


@dataclass
class PredictionMetrics:
    """Model performance metrics."""

    model_name: str
    mae: float
    rmse: float
    r2: float
    mape: float


class PredictiveAnalyticsAgent:
    """Agent for predictive analytics and forecasting of marketing metrics."""

    def __init__(self, forecast_horizon_days: int = 30, confidence_level: float = 0.95) -> None:
        self.forecast_horizon_days = forecast_horizon_days
        self.confidence_level = confidence_level
        self.models: dict[str, Any] = {}
        self.scalers: dict[str, StandardScaler] = {}
        self.logger = structlog.get_logger(__name__).bind(agent="predictive_analytics")

    def _prepare_features(self, data_points: list[RawDataPoint]) -> np.ndarray:
        """Extract features from raw data points."""
        features: list[list[float]] = []
        for dp in data_points:
            features.append([
                dp.spend,
                float(dp.impressions),
                float(dp.clicks),
                dp.conversions,
                dp.revenue,
                float(dp.timestamp.weekday()),
                float(dp.timestamp.hour),
            ])
        return np.array(features) if features else np.empty((0, 7))

    def train(
        self, data_points: list[RawDataPoint], target_metric: str = "conversions"
    ) -> PredictionMetrics:
        """Train a predictive model for the specified target metric."""
        if len(data_points) < 14:
            raise ValueError("At least 14 data points required for training")
        features = self._prepare_features(data_points)
        target_idx = {"conversions": 3, "revenue": 4, "clicks": 2, "impressions": 1, "spend": 0}
        if target_metric not in target_idx:
            raise ValueError(f"Unsupported target metric: {target_metric}")
        y = features[:, target_idx[target_metric]]
        x = np.delete(features, target_idx[target_metric], axis=1)
        scaler = StandardScaler()
        x_scaled = scaler.fit_transform(x)
        model = GradientBoostingRegressor(
            n_estimators=100, max_depth=5, learning_rate=0.1, random_state=42
        )
        tscv = TimeSeriesSplit(n_splits=3)
        cv_scores = cross_val_score(model, x_scaled, y, cv=tscv, scoring="r2")
        model.fit(x_scaled, y)
        predictions = model.predict(x_scaled)
        mae = mean_absolute_error(y, predictions)
        rmse = float(np.sqrt(mean_squared_error(y, predictions)))
        r2 = float(np.mean(cv_scores))
        mape = float(np.mean(np.abs((y - predictions) / np.maximum(y, 1))) * 100)
        self.models[target_metric] = model
        self.scalers[target_metric] = scaler
        self.logger.info("Model trained", target_metric=target_metric, r2=r2, rmse=rmse, mape=mape)
        return PredictionMetrics(
            model_name="GradientBoostingRegressor", mae=mae, rmse=rmse, r2=r2, mape=mape
        )

    def forecast(
        self, data_points: list[RawDataPoint], target_metric: str = "conversions"
    ) -> ForecastResult:
        """Generate forecast for the specified metric."""
        if target_metric not in self.models:
            self.train(data_points, target_metric)
        model = self.models[target_metric]
        scaler = self.scalers[target_metric]
        features = self._prepare_features(data_points)
        target_idx = {"conversions": 3, "revenue": 4, "clicks": 2, "impressions": 1, "spend": 0}
        x = np.delete(features, target_idx[target_metric], axis=1)
        last_date = max(dp.timestamp for dp in data_points)
        future_dates = [
            last_date + timedelta(days=i + 1) for i in range(self.forecast_horizon_days)
        ]
        last_sequence = x[-7:] if len(x) >= 7 else x
        forecast_values: list[float] = []
        confidence_intervals: list[tuple[float, float]] = []
        current_sequence = last_sequence.copy()
        for _ in range(self.forecast_horizon_days):
            seq_flat = current_sequence.flatten().reshape(1, -1)
            seq_scaled = scaler.transform(seq_flat)
            pred = float(model.predict(seq_scaled)[0])
            forecast_values.append(max(0, pred))
            std_dev = np.std(forecast_values) if forecast_values else pred * 0.1
            z_score = 1.96 if self.confidence_level >= 0.95 else 1.645
            margin = z_score * std_dev
            confidence_intervals.append((max(0, pred - margin), pred + margin))
            new_row = current_sequence[-1].copy()
            idx = target_idx[target_metric] - 1 if target_idx[target_metric] > 0 else 0
            new_row[idx] = pred
            current_sequence = np.vstack([current_sequence[1:], new_row])
        x_scaled = scaler.transform(x)
        predictions = model.predict(x_scaled)
        y = features[:, target_idx[target_metric]]
        rmse = float(np.sqrt(mean_squared_error(y, predictions)))
        mape = float(np.mean(np.abs((y - predictions) / np.maximum(y, 1))) * 100)
        self.logger.info(
            "Forecast generated",
            target_metric=target_metric,
            horizon_days=self.forecast_horizon_days,
            mape=mape,
        )
        return ForecastResult(
            metric_name=target_metric,
            forecast_values=forecast_values,
            confidence_intervals=confidence_intervals,
            dates=future_dates,
            model_name="GradientBoostingRegressor",
            mape=mape,
            rmse=rmse,
        )

    def predict_roas(self, data_points: list[RawDataPoint]) -> ForecastResult:
        """Predict Return on Ad Spend (ROAS)."""
        revenue_forecast = self.forecast(data_points, "revenue")
        spend_forecast = self.forecast(data_points, "spend")
        roas_values = [rev / spend if spend > 0 else 0.0 for rev, spend in zip(
            revenue_forecast.forecast_values, spend_forecast.forecast_values, strict=False
        )]
        return ForecastResult(
            metric_name="roas",
            forecast_values=roas_values,
            confidence_intervals=list(
                zip(
                    [
                        r[0] / s[1] if s[1] > 0 else 0
                        for r, s in zip(
                            revenue_forecast.confidence_intervals,
                            spend_forecast.confidence_intervals,
                            strict=False,
                        )
                    ],
                    [
                        r[1] / s[0] if s[0] > 0 else 0
                        for r, s in zip(
                            revenue_forecast.confidence_intervals,
                            spend_forecast.confidence_intervals,
                            strict=False,
                        )
                    ],
                    strict=False,
                )
            ),
            dates=revenue_forecast.dates,
            model_name="Derived",
            mape=revenue_forecast.mape,
            rmse=revenue_forecast.rmse,
        )

    def detect_anomalies(
        self, data_points: list[RawDataPoint], threshold_std: float = 2.0
    ) -> list[RawDataPoint]:
        """Detect anomalous data points using statistical methods."""
        if len(data_points) < 7:
            return []
        conversions = np.array([dp.conversions for dp in data_points])
        mean = np.mean(conversions)
        std = np.std(conversions)
        if std == 0:
            return []
        anomalies = [dp for dp in data_points if abs(dp.conversions - mean) > threshold_std * std]
        if anomalies:
            self.logger.warning(
                "Anomalies detected", count=len(anomalies), threshold_std=threshold_std
            )
        return anomalies
