"""Analysis Agent - analyzes sales data for trends, seasonality, and anomalies."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np
import pandas as pd
import structlog

from sales_forecaster.core.exceptions import AnalysisError
from sales_forecaster.core.metrics import record_agent_error
from sales_forecaster.core.models import AnalysisResult, SalesRecord

if TYPE_CHECKING:
    from datetime import datetime

logger = structlog.get_logger(__name__)


class AnalysisAgent:
    """Agent responsible for analyzing collected sales data.

    Performs trend analysis, seasonality detection, anomaly detection,
    and generates summary statistics and insights.
    """

    def __init__(
        self,
        seasonality_mode: str = "multiplicative",
        changepoint_prior_scale: float = 0.05,
        anomaly_threshold: float = 2.5,
    ) -> None:
        """Initialize the Analysis Agent.

        Args:
            seasonality_mode: Seasonality mode ('additive' or 'multiplicative').
            changepoint_prior_scale: Prior scale for changepoint detection.
            anomaly_threshold: Z-score threshold for anomaly detection.
        """
        self.seasonality_mode = seasonality_mode
        self.changepoint_prior_scale = changepoint_prior_scale
        self.anomaly_threshold = anomaly_threshold

    async def analyze(
        self,
        records: list[SalesRecord],
        period: str = "monthly",
    ) -> AnalysisResult:
        """Analyze sales records and produce insights.

        Args:
            records: List of sales records to analyze.
            period: Aggregation period ('daily', 'weekly', 'monthly').

        Returns:
            AnalysisResult with trends, seasonality, anomalies, and insights.

        Raises:
            AnalysisError: If analysis fails.
        """
        if not records:
            raise AnalysisError("No records provided for analysis")

        logger.info(
            "Starting analysis",
            record_count=len(records),
            period=period,
        )

        try:
            df = self._prepare_dataframe(records, period)
            trend = self._detect_trend(df)
            seasonality_detected, seasonality_period = self._detect_seasonality(df)
            anomalies = self._detect_anomalies(df)
            changepoints = self._detect_changepoints(df)
            summary_stats = self._compute_summary_statistics(df)
            insights = self._generate_insights(
                df, trend, seasonality_detected, anomalies, changepoints
            )

            result = AnalysisResult(
                trend=trend,
                seasonality_detected=seasonality_detected,
                seasonality_period=seasonality_period,
                anomalies=anomalies,
                changepoints=changepoints,
                summary_statistics=summary_stats,
                insights=insights,
            )

            logger.info(
                "Analysis complete",
                trend=trend,
                seasonality_detected=seasonality_detected,
                anomaly_count=len(anomalies),
            )
            return result

        except AnalysisError:
            raise
        except Exception as exc:
            record_agent_error("analysis")
            logger.error("Analysis failed", error=str(exc), exc_info=True)
            raise AnalysisError(f"Analysis failed: {exc}") from exc

    def _prepare_dataframe(
        self, records: list[SalesRecord], period: str
    ) -> pd.DataFrame:
        """Convert sales records to a time-series DataFrame.

        Args:
            records: List of sales records.
            period: Aggregation period.

        Returns:
            DataFrame with 'ds' (date) and 'y' (value) columns.
        """
        data = [
            {"ds": r.date, "y": r.amount, "source": r.source.value}
            for r in records
        ]
        df = pd.DataFrame(data)
        df["ds"] = pd.to_datetime(df["ds"])
        df = df.sort_values("ds")

        freq_map = {"daily": "D", "weekly": "W", "monthly": "ME"}
        freq = freq_map.get(period, "ME")

        df = df.set_index("ds").resample(freq)["y"].sum().reset_index()
        df = df.fillna(0)

        return df

    def _detect_trend(self, df: pd.DataFrame) -> str:
        """Detect the overall trend direction.

        Args:
            df: Time-series DataFrame.

        Returns:
            Trend direction: 'increasing', 'decreasing', or 'stable'.
        """
        if len(df) < 3:
            return "stable"

        values = df["y"].values
        x = np.arange(len(values))
        slope = np.polyfit(x, values, 1)[0]

        mean_val = np.mean(values)
        if mean_val == 0:
            return "stable"

        relative_slope = slope / mean_val
        if relative_slope > 0.02:
            return "increasing"
        elif relative_slope < -0.02:
            return "decreasing"
        return "stable"

    def _detect_seasonality(
        self, df: pd.DataFrame
    ) -> tuple[bool, int | None]:
        """Detect seasonality in the time series.

        Args:
            df: Time-series DataFrame.

        Returns:
            Tuple of (seasonality_detected, period_length).
        """
        if len(df) < 12:
            return False, None

        values = df["y"].values
        if np.std(values) == 0:
            return False, None

        # Autocorrelation-based seasonality detection
        autocorr = np.correlate(values - np.mean(values), values - np.mean(values), mode="full")
        autocorr = autocorr[len(autocorr) // 2 :]
        autocorr = autocorr / autocorr[0]

        # Find peaks in autocorrelation (excluding lag 0)
        for lag in range(2, min(len(autocorr) // 2, 24)):
            if (
                autocorr[lag] > 0.3
                and autocorr[lag] > autocorr[lag - 1]
                and autocorr[lag] > autocorr[lag + 1]
            ):
                return True, lag

        return False, None

    def _detect_anomalies(self, df: pd.DataFrame) -> list[dict[str, Any]]:
        """Detect anomalies using Z-score method.

        Args:
            df: Time-series DataFrame.

        Returns:
            List of anomaly records with date, value, and z-score.
        """
        if len(df) < 3:
            return []

        values = df["y"].values
        mean = np.mean(values)
        std = np.std(values)

        if std == 0:
            return []

        z_scores = np.abs((values - mean) / std)
        anomaly_mask = z_scores > self.anomaly_threshold

        anomalies: list[dict[str, Any]] = []
        for idx in np.where(anomaly_mask)[0]:
            anomalies.append(
                {
                    "date": df.iloc[idx]["ds"].isoformat(),
                    "value": float(values[idx]),
                    "z_score": float(z_scores[idx]),
                }
            )

        return anomalies

    def _detect_changepoints(self, df: pd.DataFrame) -> list[datetime]:
        """Detect significant changepoints in the time series.

        Args:
            df: Time-series DataFrame.

        Returns:
            List of changepoint dates.
        """
        if len(df) < 6:
            return []

        values = df["y"].values
        changepoints: list[datetime] = []

        # Simple changepoint detection using rolling mean shift
        window = max(3, len(values) // 6)
        for i in range(window, len(values) - window):
            before = np.mean(values[max(0, i - window) : i])
            after = np.mean(values[i : i + window])
            if before > 0 and abs(after - before) / before > 0.5:
                changepoints.append(df.iloc[i]["ds"])

        return changepoints

    def _compute_summary_statistics(self, df: pd.DataFrame) -> dict[str, float]:
        """Compute summary statistics for the time series.

        Args:
            df: Time-series DataFrame.

        Returns:
            Dictionary of summary statistics.
        """
        values = df["y"].values
        return {
            "mean": float(np.mean(values)),
            "median": float(np.median(values)),
            "std": float(np.std(values)),
            "min": float(np.min(values)),
            "max": float(np.max(values)),
            "total": float(np.sum(values)),
            "count": float(len(values)),
        }

    def _generate_insights(
        self,
        df: pd.DataFrame,
        trend: str,
        seasonality_detected: bool,
        anomalies: list[dict[str, Any]],
        changepoints: list[datetime],
    ) -> list[str]:
        """Generate human-readable insights from the analysis.

        Args:
            df: Time-series DataFrame.
            trend: Detected trend direction.
            seasonality_detected: Whether seasonality was detected.
            anomalies: List of detected anomalies.
            changepoints: List of detected changepoints.

        Returns:
            List of insight strings.
        """
        insights: list[str] = []
        stats = self._compute_summary_statistics(df)

        insights.append(
            f"Overall trend is {trend} with total revenue of ${stats['total']:,.2f}"
            f" over {int(stats['count'])} periods."
        )

        if seasonality_detected:
            insights.append(
                "Seasonality detected in the data. Consider seasonal adjustments"
                " in forecasting."
            )

        if anomalies:
            insights.append(
                f"Found {len(anomalies)} anomalous data points that may indicate"
                " special events or data quality issues."
            )

        if changepoints:
            insights.append(
                f"Detected {len(changepoints)} significant changepoints suggesting"
                " shifts in sales patterns."
            )

        if stats["std"] / stats["mean"] > 0.5 if stats["mean"] > 0 else False:
            insights.append(
                "High volatility detected in sales data. Forecasts may have"
                " wider confidence intervals."
            )

        return insights
