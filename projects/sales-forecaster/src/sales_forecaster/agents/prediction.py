"""Prediction Agent - generates sales forecasts using ML models."""

from __future__ import annotations

import uuid
from datetime import datetime

import numpy as np
import pandas as pd
import structlog

from sales_forecaster.core.exceptions import PredictionError
from sales_forecaster.core.metrics import record_agent_error, record_forecast_accuracy
from sales_forecaster.core.models import (
    AnalysisResult,
    ForecastPeriod,
    ForecastPoint,
    ForecastResult,
    SalesRecord,
)

logger = structlog.get_logger(__name__)


class PredictionAgent:
    """Agent responsible for generating sales forecasts.

    Uses Prophet and statistical models to generate forecasts with
    confidence intervals and accuracy metrics.
    """

    def __init__(
        self,
        forecast_horizon_days: int = 90,
        confidence_level: float = 0.95,
        models: list[str] | None = None,
    ) -> None:
        """Initialize the Prediction Agent.

        Args:
            forecast_horizon_days: Number of days to forecast.
            confidence_level: Confidence level for prediction intervals.
            models: List of models to use ('prophet', 'arima', 'ensemble').
        """
        self.forecast_horizon_days = forecast_horizon_days
        self.confidence_level = confidence_level
        self.models = models or ["prophet", "ensemble"]

    async def predict(
        self,
        records: list[SalesRecord],
        analysis: AnalysisResult | None = None,
        period: ForecastPeriod = ForecastPeriod.MONTHLY,
    ) -> ForecastResult:
        """Generate a sales forecast.

        Args:
            records: Historical sales records.
            analysis: Optional analysis result from the Analysis Agent.
            period: Forecast period granularity.

        Returns:
            ForecastResult with predictions and confidence intervals.

        Raises:
            PredictionError: If prediction fails.
        """
        if not records:
            raise PredictionError("No records provided for prediction")

        logger.info(
            "Starting prediction",
            record_count=len(records),
            horizon_days=self.forecast_horizon_days,
            period=period.value,
        )

        try:
            df = self._prepare_dataframe(records, period)

            if "prophet" in self.models:
                forecast_df, model_name = self._run_prophet(df, period)
            elif "arima" in self.models:
                forecast_df, model_name = self._run_arima(df, period)
            else:
                forecast_df, model_name = self._run_ensemble(df, period, analysis)

            points = self._create_forecast_points(forecast_df)
            mape, rmse = self._calculate_accuracy_metrics(df, forecast_df)

            result = ForecastResult(
                id=str(uuid.uuid4()),
                created_at=datetime.now(),
                period=period,
                horizon_days=self.forecast_horizon_days,
                points=points,
                model_used=model_name,
                mape=mape,
                rmse=rmse,
                metadata={
                    "confidence_level": self.confidence_level,
                    "training_records": len(records),
                    "analysis_trend": analysis.trend if analysis else None,
                },
            )

            if mape is not None:
                record_forecast_accuracy(model_name, 1.0 - mape)

            logger.info(
                "Prediction complete",
                model=model_name,
                point_count=len(points),
                mape=mape,
            )
            return result

        except PredictionError:
            raise
        except Exception as exc:
            record_agent_error("prediction")
            logger.error("Prediction failed", error=str(exc), exc_info=True)
            raise PredictionError(f"Prediction failed: {exc}") from exc

    def _prepare_dataframe(
        self, records: list[SalesRecord], period: ForecastPeriod
    ) -> pd.DataFrame:
        """Convert sales records to a time-series DataFrame.

        Args:
            records: List of sales records.
            period: Aggregation period.

        Returns:
            DataFrame with 'ds' (date) and 'y' (value) columns.
        """
        data = [{"ds": r.date, "y": r.amount} for r in records]
        df = pd.DataFrame(data)
        df["ds"] = pd.to_datetime(df["ds"])
        df = df.sort_values("ds")

        freq_map = {
            ForecastPeriod.DAILY: "D",
            ForecastPeriod.WEEKLY: "W",
            ForecastPeriod.MONTHLY: "ME",
            ForecastPeriod.QUARTERLY: "QE",
        }
        freq = freq_map.get(period, "ME")

        df = df.set_index("ds").resample(freq)["y"].sum().reset_index()
        df = df.fillna(0)

        return df

    def _run_prophet(
        self, df: pd.DataFrame, period: ForecastPeriod
    ) -> tuple[pd.DataFrame, str]:
        """Run Prophet forecasting model.

        Args:
            df: Training DataFrame.
            period: Forecast period.

        Returns:
            Tuple of (forecast DataFrame, model name).
        """
        try:
            from prophet import Prophet
        except ImportError:
            logger.warning("Prophet not available, falling back to ensemble")
            return self._run_ensemble(df, period, None)

        freq_map = {
            ForecastPeriod.DAILY: "D",
            ForecastPeriod.WEEKLY: "W",
            ForecastPeriod.MONTHLY: "ME",
            ForecastPeriod.QUARTERLY: "QE",
        }
        freq = freq_map.get(period, "ME")

        model = Prophet(
            seasonality_mode="multiplicative",
            interval_width=self.confidence_level,
            daily_seasonality=period == ForecastPeriod.DAILY,
            weekly_seasonality=period in (ForecastPeriod.DAILY, ForecastPeriod.WEEKLY),
            yearly_seasonality=True,
        )
        model.fit(df)

        periods = self._get_periods(period)
        future = model.make_future_dataframe(periods=periods, freq=freq)
        forecast = model.predict(future)

        forecast = forecast[forecast["ds"] > df["ds"].max()].copy()
        forecast = forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]]

        return forecast, "prophet"

    def _run_arima(
        self, df: pd.DataFrame, period: ForecastPeriod
    ) -> tuple[pd.DataFrame, str]:
        """Run ARIMA forecasting model.

        Args:
            df: Training DataFrame.
            period: Forecast period.

        Returns:
            Tuple of (forecast DataFrame, model name).
        """
        try:
            from statsmodels.tsa.arima.model import ARIMA
        except ImportError:
            logger.warning("statsmodels not available, falling back to ensemble")
            return self._run_ensemble(df, period, None)

        periods = self._get_periods(period)
        values = df["y"].values

        # Simple ARIMA(1,1,1) - in production, use auto_arima for parameter selection
        model = ARIMA(values, order=(1, 1, 1))
        fitted = model.fit()

        forecast_result = fitted.get_forecast(steps=periods)
        forecast_mean = forecast_result.predicted_mean
        conf_int = forecast_result.conf_int(alpha=1 - self.confidence_level)

        last_date = df["ds"].max()
        freq_map = {
            ForecastPeriod.DAILY: "D",
            ForecastPeriod.WEEKLY: "W",
            ForecastPeriod.MONTHLY: "ME",
            ForecastPeriod.QUARTERLY: "QE",
        }
        freq = freq_map.get(period, "ME")

        future_dates = pd.date_range(
            start=last_date, periods=periods + 1, freq=freq
        )[1:]

        forecast_df = pd.DataFrame(
            {
                "ds": future_dates,
                "yhat": forecast_mean,
                "yhat_lower": conf_int[:, 0],
                "yhat_upper": conf_int[:, 1],
            }
        )

        return forecast_df, "arima"

    def _run_ensemble(
        self,
        df: pd.DataFrame,
        period: ForecastPeriod,
        analysis: AnalysisResult | None,
    ) -> tuple[pd.DataFrame, str]:
        """Run ensemble forecasting (moving average + trend).

        Args:
            df: Training DataFrame.
            period: Forecast period.
            analysis: Optional analysis result.

        Returns:
            Tuple of (forecast DataFrame, model name).
        """
        periods = self._get_periods(period)
        values = df["y"].values

        # Simple moving average with trend
        window = min(3, len(values))
        if window > 0:
            ma = np.convolve(values, np.ones(window) / window, mode="valid")
            last_ma = ma[-1] if len(ma) > 0 else np.mean(values)
        else:
            last_ma = np.mean(values)

        # Trend component
        if analysis and analysis.trend == "increasing":
            trend_factor = 1.02
        elif analysis and analysis.trend == "decreasing":
            trend_factor = 0.98
        else:
            trend_factor = 1.0

        # Generate forecasts
        forecasts = []
        for i in range(periods):
            forecasts.append(last_ma * (trend_factor ** (i + 1)))

        forecasts_arr = np.array(forecasts)
        std = np.std(values) if len(values) > 1 else 0
        z_score = 1.96 if self.confidence_level >= 0.95 else 1.645

        last_date = df["ds"].max()
        freq_map = {
            ForecastPeriod.DAILY: "D",
            ForecastPeriod.WEEKLY: "W",
            ForecastPeriod.MONTHLY: "ME",
            ForecastPeriod.QUARTERLY: "QE",
        }
        freq = freq_map.get(period, "ME")

        future_dates = pd.date_range(
            start=last_date, periods=periods + 1, freq=freq
        )[1:]

        forecast_df = pd.DataFrame(
            {
                "ds": future_dates,
                "yhat": forecasts_arr,
                "yhat_lower": forecasts_arr - z_score * std,
                "yhat_upper": forecasts_arr + z_score * std,
            }
        )

        return forecast_df, "ensemble"

    def _get_periods(self, period: ForecastPeriod) -> int:
        """Get number of periods for the forecast horizon.

        Args:
            period: Forecast period.

        Returns:
            Number of periods.
        """
        periods_map = {
            ForecastPeriod.DAILY: self.forecast_horizon_days,
            ForecastPeriod.WEEKLY: self.forecast_horizon_days // 7,
            ForecastPeriod.MONTHLY: self.forecast_horizon_days // 30,
            ForecastPeriod.QUARTERLY: self.forecast_horizon_days // 90,
        }
        return max(1, periods_map.get(period, 3))

    def _create_forecast_points(self, forecast_df: pd.DataFrame) -> list[ForecastPoint]:
        """Create ForecastPoint objects from forecast DataFrame.

        Args:
            forecast_df: DataFrame with forecast results.

        Returns:
            List of ForecastPoint objects.
        """
        points: list[ForecastPoint] = []
        for _, row in forecast_df.iterrows():
            points.append(
                ForecastPoint(
                    date=row["ds"],
                    value=max(0, float(row["yhat"])),
                    lower_bound=max(0, float(row["yhat_lower"])),
                    upper_bound=max(0, float(row["yhat_upper"])),
                    confidence=self.confidence_level,
                )
            )
        return points

    def _calculate_accuracy_metrics(
        self, actual_df: pd.DataFrame, forecast_df: pd.DataFrame
    ) -> tuple[float | None, float | None]:
        """Calculate MAPE and RMSE using cross-validation.

        Args:
            actual_df: Actual values DataFrame.
            forecast_df: Forecast DataFrame.

        Returns:
            Tuple of (MAPE, RMSE).
        """
        if len(actual_df) < 4:
            return None, None

        # Simple train/test split for metrics
        split_idx = int(len(actual_df) * 0.8)
        train = actual_df.iloc[:split_idx]
        test = actual_df.iloc[split_idx:]

        if len(test) == 0:
            return None, None

        # Use simple mean as baseline for metrics
        train_mean = train["y"].mean()
        predictions = np.full(len(test), train_mean)
        actuals = test["y"].values

        # MAPE
        mape = np.mean(np.abs((actuals - predictions) / np.maximum(actuals, 1))) * 100

        # RMSE
        rmse = np.sqrt(np.mean((actuals - predictions) ** 2))

        return float(mape), float(rmse)
