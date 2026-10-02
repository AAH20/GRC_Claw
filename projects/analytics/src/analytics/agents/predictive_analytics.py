"""Predictive Analytics Agent - Revenue forecasting and churn prediction."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum
from typing import Any

import numpy as np
import structlog
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

logger = structlog.get_logger(__name__)


class ModelType(StrEnum):
    """Supported predictive model types."""

    LINEAR_REGRESSION = "linear_regression"
    RANDOM_FOREST = "random_forest"
    GRADIENT_BOOSTING = "gradient_boosting"


@dataclass
class ForecastPoint:
    """A single point in a forecast."""

    date: datetime
    predicted_value: float
    lower_bound: float
    upper_bound: float


@dataclass
class ForecastResult:
    """Result of a forecasting run."""

    model_type: ModelType
    forecast_horizon_days: int
    points: list[ForecastPoint]
    metrics: dict[str, float]
    created_at: datetime


@dataclass
class ChurnPrediction:
    """Churn prediction for a single user."""

    user_id: str
    churn_probability: float
    risk_tier: str
    top_factors: dict[str, float]


@dataclass
class ChurnPredictionResult:
    """Result of churn prediction run."""

    predictions: list[ChurnPrediction]
    model_metrics: dict[str, float]
    created_at: datetime


class PredictiveAnalyticsAgent:
    """Agent for predictive analytics including forecasting and churn prediction."""

    def __init__(self, confidence_level: float = 0.95) -> None:
        self.confidence_level = confidence_level
        self.logger = logger.bind(agent="predictive_analytics")
        self._models: dict[ModelType, Any] = {}
        self._scaler = StandardScaler()

    def _get_model(self, model_type: ModelType) -> Any:
        """Get or create a model instance."""
        if model_type not in self._models:
            if model_type == ModelType.LINEAR_REGRESSION:
                self._models[model_type] = LinearRegression()
            elif model_type == ModelType.RANDOM_FOREST:
                self._models[model_type] = RandomForestRegressor(
                    n_estimators=100,
                    max_depth=10,
                    random_state=42,
                )
            elif model_type == ModelType.GRADIENT_BOOSTING:
                self._models[model_type] = GradientBoostingRegressor(
                    n_estimators=100,
                    max_depth=5,
                    learning_rate=0.1,
                    random_state=42,
                )
            else:
                raise ValueError(f"Unsupported model type: {model_type}")
        return self._models[model_type]

    def forecast_revenue(
        self,
        historical_data: list[dict[str, Any]],
        horizon_days: int = 30,
        model_type: ModelType = ModelType.GRADIENT_BOOSTING,
    ) -> ForecastResult:
        """Generate revenue forecast based on historical data."""
        self.logger.info(
            "generating_revenue_forecast",
            model_type=model_type.value,
            horizon_days=horizon_days,
            data_points=len(historical_data),
        )

        if not historical_data:
            raise ValueError("Historical data cannot be empty")

        # Prepare features
        dates = [datetime.fromisoformat(d["date"]) for d in historical_data]
        revenues = np.array([d["revenue"] for d in historical_data])

        # Feature engineering
        x = self._engineer_features(dates)
        y = revenues

        # Split for validation
        if len(x) >= 10:
            x_train, x_test, y_train, y_test = train_test_split(
                x, y, test_size=0.2, shuffle=False
            )
        else:
            x_train, y_train = x, y
            x_test, y_test = x, y

        # Scale features
        x_train_scaled = self._scaler.fit_transform(x_train)
        x_test_scaled = self._scaler.transform(x_test)

        # Train model
        model = self._get_model(model_type)
        model.fit(x_train_scaled, y_train)

        # Evaluate
        y_pred = model.predict(x_test_scaled)
        metrics = {
            "mae": float(mean_absolute_error(y_test, y_pred)),
            "rmse": float(np.sqrt(mean_squared_error(y_test, y_pred))),
            "r2": float(r2_score(y_test, y_pred)),
        }

        # Generate future dates
        last_date = dates[-1]
        future_dates = [last_date + timedelta(days=i + 1) for i in range(horizon_days)]
        x_future = self._engineer_features(future_dates)
        x_future_scaled = self._scaler.transform(x_future)

        # Predict
        predictions = model.predict(x_future_scaled)

        # Calculate confidence intervals
        z_score = 1.96 if self.confidence_level == 0.95 else 1.645
        residuals = y_train - model.predict(x_train_scaled)
        std_residuals = np.std(residuals)

        points: list[ForecastPoint] = []
        for date, pred in zip(future_dates, predictions, strict=False):
            margin = z_score * std_residuals
            points.append(
                ForecastPoint(
                    date=date,
                    predicted_value=float(max(0, pred)),
                    lower_bound=float(max(0, pred - margin)),
                    upper_bound=float(pred + margin),
                )
            )

        return ForecastResult(
            model_type=model_type,
            forecast_horizon_days=horizon_days,
            points=points,
            metrics=metrics,
            created_at=datetime.utcnow(),
        )

    def predict_churn(
        self,
        user_features: list[dict[str, Any]],
        model_type: ModelType = ModelType.GRADIENT_BOOSTING,
    ) -> ChurnPredictionResult:
        """Predict churn probability for users."""
        self.logger.info(
            "predicting_churn",
            model_type=model_type.value,
            user_count=len(user_features),
        )

        if not user_features:
            raise ValueError("User features cannot be empty")

        # Extract features
        feature_names = [
            "days_since_last_active",
            "total_sessions",
            "avg_session_duration",
            "total_revenue",
            "support_tickets",
            "email_open_rate",
        ]

        x = np.array([[f.get(name, 0) for name in feature_names] for f in user_features])

        # For demo purposes, generate synthetic labels based on features
        # In production, this would use actual churn labels
        churn_scores = self._calculate_churn_scores(x)

        # Train model on synthetic data
        x_scaled = self._scaler.fit_transform(x)
        model = self._get_model(model_type)

        # Create synthetic binary labels
        y = (churn_scores > np.median(churn_scores)).astype(int)

        if len(x) >= 10:
            x_train, x_test, y_train, y_test = train_test_split(
                x_scaled, y, test_size=0.2, random_state=42
            )
        else:
            x_train, y_train = x_scaled, y
            x_test, y_test = x_scaled, y

        model.fit(x_train, y_train)

        # Evaluate
        y_pred = model.predict(x_test)
        metrics = {
            "mae": float(mean_absolute_error(y_test, y_pred)),
            "rmse": float(np.sqrt(mean_squared_error(y_test, y_pred))),
            "r2": float(r2_score(y_test, y_pred)),
        }

        # Predict probabilities
        if hasattr(model, "predict_proba"):
            probabilities = model.predict_proba(x_scaled)[:, 1]
        else:
            probabilities = model.predict(x_scaled)

        predictions: list[ChurnPrediction] = []
        for user_feature, prob in zip(user_features, probabilities, strict=False):
            risk_tier = self._classify_risk(float(prob))
            top_factors = self._get_top_factors(user_feature, feature_names)
            predictions.append(
                ChurnPrediction(
                    user_id=user_feature.get("user_id", ""),
                    churn_probability=float(prob),
                    risk_tier=risk_tier,
                    top_factors=top_factors,
                )
            )

        return ChurnPredictionResult(
            predictions=predictions,
            model_metrics=metrics,
            created_at=datetime.utcnow(),
        )

    def _engineer_features(self, dates: list[datetime]) -> np.ndarray:
        """Engineer time-based features from dates."""
        features: list[list[float]] = []
        for date in dates:
            features.append(
                [
                    date.weekday(),  # Day of week
                    date.day,  # Day of month
                    date.month,  # Month
                    np.sin(2 * np.pi * date.weekday() / 7),  # Cyclical day of week
                    np.cos(2 * np.pi * date.weekday() / 7),
                    np.sin(2 * np.pi * date.month / 12),  # Cyclical month
                    np.cos(2 * np.pi * date.month / 12),
                ]
            )
        return np.array(features)

    def _calculate_churn_scores(self, x: np.ndarray) -> np.ndarray:
        """Calculate synthetic churn scores based on features."""
        # Higher days_since_last_active -> higher churn risk
        # Lower total_sessions -> higher churn risk
        # Lower total_revenue -> higher churn risk
        scores = (
            0.4 * x[:, 0]  # days_since_last_active
            - 0.2 * x[:, 1]  # total_sessions (negative = protective)
            - 0.1 * x[:, 2]  # avg_session_duration
            - 0.2 * x[:, 3]  # total_revenue (negative = protective)
            + 0.1 * x[:, 4]  # support_tickets
            - 0.1 * x[:, 5]  # email_open_rate (negative = protective)
        )
        return scores

    def _classify_risk(self, probability: float) -> str:
        """Classify risk tier based on churn probability."""
        if probability >= 0.7:
            return "high"
        elif probability >= 0.4:
            return "medium"
        else:
            return "low"

    def _get_top_factors(
        self,
        user_feature: dict[str, Any],
        feature_names: list[str],
    ) -> dict[str, float]:
        """Get top contributing factors for churn prediction."""
        factors: dict[str, float] = {}
        for name in feature_names:
            value = user_feature.get(name, 0)
            # Normalize to 0-1 range for interpretability
            factors[name] = float(min(1.0, max(0.0, value / 100.0)))
        # Return top 3 factors
        return dict(sorted(factors.items(), key=lambda x: x[1], reverse=True)[:3])
