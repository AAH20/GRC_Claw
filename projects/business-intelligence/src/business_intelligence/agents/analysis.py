"""Analysis Agent for statistical analysis and insights generation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd
import structlog
from scipy import stats

logger = structlog.get_logger(__name__)


@dataclass
class AnalysisResult:
    """Result of an analysis operation."""

    success: bool
    summary_statistics: dict[str, Any] = field(default_factory=dict)
    trends: dict[str, Any] = field(default_factory=dict)
    anomalies: list[dict[str, Any]] = field(default_factory=list)
    correlations: dict[str, Any] = field(default_factory=dict)
    insights: list[str] = field(default_factory=list)
    error_message: str | None = None


class AnalysisAgent:
    """Agent responsible for performing statistical analysis on data.

    Provides summary statistics, trend detection, anomaly identification,
    and correlation analysis.
    """

    def __init__(self, confidence_level: float = 0.95) -> None:
        """Initialize the Analysis Agent.

        Args:
            confidence_level: Confidence level for statistical tests (0-1).
        """
        self.confidence_level = confidence_level

    def analyze(self, df: pd.DataFrame) -> AnalysisResult:
        """Perform comprehensive analysis on a DataFrame.

        Args:
            df: Input data to analyze.

        Returns:
            AnalysisResult containing statistics, trends, anomalies, and insights.
        """
        logger.info("starting_analysis", rows=len(df), columns=len(df.columns))

        try:
            if df.empty:
                return AnalysisResult(
                    success=False,
                    error_message="Cannot analyze empty dataset",
                )

            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            categorical_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
            datetime_cols = df.select_dtypes(include=["datetime64"]).columns.tolist()

            summary_stats = self._compute_summary_statistics(df, numeric_cols)
            trends = self._detect_trends(df, numeric_cols, datetime_cols)
            anomalies = self._detect_anomalies(df, numeric_cols)
            correlations = self._compute_correlations(df, numeric_cols)
            insights = self._generate_insights(
                df, numeric_cols, categorical_cols, summary_stats, anomalies
            )

            logger.info("analysis_complete", insights_count=len(insights))

            return AnalysisResult(
                success=True,
                summary_statistics=summary_stats,
                trends=trends,
                anomalies=anomalies,
                correlations=correlations,
                insights=insights,
            )

        except Exception as e:
            logger.error("analysis_error", error=str(e))
            return AnalysisResult(success=False, error_message=str(e))

    def _compute_summary_statistics(
        self, df: pd.DataFrame, numeric_cols: list[str]
    ) -> dict[str, Any]:
        """Compute summary statistics for numeric columns.

        Args:
            df: Input DataFrame.
            numeric_cols: List of numeric column names.

        Returns:
            Dictionary of summary statistics per column.
        """
        stats_dict: dict[str, Any] = {}

        for col in numeric_cols:
            series = df[col].dropna()
            if series.empty:
                continue

            stats_dict[col] = {
                "count": int(series.count()),
                "mean": float(series.mean()),
                "median": float(series.median()),
                "std": float(series.std()),
                "min": float(series.min()),
                "max": float(series.max()),
                "q25": float(series.quantile(0.25)),
                "q75": float(series.quantile(0.75)),
                "skewness": float(series.skew()),
                "kurtosis": float(series.kurtosis()),
                "missing_pct": float(df[col].isna().mean() * 100),
            }

        return stats_dict

    def _detect_trends(
        self,
        df: pd.DataFrame,
        numeric_cols: list[str],
        datetime_cols: list[str],
    ) -> dict[str, Any]:
        """Detect trends in time-series data.

        Args:
            df: Input DataFrame.
            numeric_cols: List of numeric column names.
            datetime_cols: List of datetime column names.

        Returns:
            Dictionary of trend analysis results.
        """
        trends: dict[str, Any] = {}

        if not datetime_cols:
            return trends

        time_col = datetime_cols[0]
        df_sorted = df.sort_values(by=time_col)

        for col in numeric_cols:
            series = df_sorted[col].dropna()
            if len(series) < 3:
                continue

            x = np.arange(len(series))
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, series)

            trends[col] = {
                "slope": float(slope),
                "r_squared": float(r_value**2),
                "p_value": float(p_value),
                "direction": "increasing" if slope > 0 else "decreasing",
                "significant": p_value < (1 - self.confidence_level),
            }

        return trends

    def _detect_anomalies(
        self, df: pd.DataFrame, numeric_cols: list[str]
    ) -> list[dict[str, Any]]:
        """Detect anomalies using the IQR method.

        Args:
            df: Input DataFrame.
            numeric_cols: List of numeric column names.

        Returns:
            List of detected anomalies with details.
        """
        anomalies: list[dict[str, Any]] = []

        for col in numeric_cols:
            series = df[col].dropna()
            if series.empty:
                continue

            q1 = series.quantile(0.25)
            q3 = series.quantile(0.75)
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr

            outlier_mask = (series < lower_bound) | (series > upper_bound)
            outlier_indices = series[outlier_mask].index.tolist()

            for idx in outlier_indices[:10]:  # Limit to top 10 per column
                anomalies.append(
                    {
                        "column": col,
                        "index": int(idx),
                        "value": float(series[idx]),
                        "lower_bound": float(lower_bound),
                        "upper_bound": float(upper_bound),
                    }
                )

        return anomalies

    def _compute_correlations(
        self, df: pd.DataFrame, numeric_cols: list[str]
    ) -> dict[str, Any]:
        """Compute correlation matrix for numeric columns.

        Args:
            df: Input DataFrame.
            numeric_cols: List of numeric column names.

        Returns:
            Dictionary with correlation matrix and top correlations.
        """
        if len(numeric_cols) < 2:
            return {"matrix": {}, "top_pairs": []}

        corr_matrix = df[numeric_cols].corr()

        # Extract top correlated pairs
        pairs: list[dict[str, Any]] = []
        for i, col1 in enumerate(numeric_cols):
            for j, col2 in enumerate(numeric_cols):
                if i < j:
                    pairs.append(
                        {
                            "column_1": col1,
                            "column_2": col2,
                            "correlation": float(corr_matrix.loc[col1, col2]),
                        }
                    )

        pairs.sort(key=lambda x: abs(x["correlation"]), reverse=True)

        return {
            "matrix": corr_matrix.to_dict(),
            "top_pairs": pairs[:10],
        }

    def _generate_insights(
        self,
        df: pd.DataFrame,
        numeric_cols: list[str],
        categorical_cols: list[str],
        summary_stats: dict[str, Any],
        anomalies: list[dict[str, Any]],
    ) -> list[str]:
        """Generate human-readable insights from the analysis.

        Args:
            df: Input DataFrame.
            numeric_cols: List of numeric column names.
            categorical_cols: List of categorical column names.
            summary_stats: Computed summary statistics.
            anomalies: Detected anomalies.

        Returns:
            List of insight strings.
        """
        insights: list[str] = []

        # Dataset overview
        insights.append(
            f"Dataset contains {len(df)} rows and {len(df.columns)} columns "
            f"({len(numeric_cols)} numeric, {len(categorical_cols)} categorical)."
        )

        # High missing data
        for col, stat in summary_stats.items():
            if stat["missing_pct"] > 20:
                insights.append(
                    f"Column '{col}' has {stat['missing_pct']:.1f}% missing values."
                )

        # Skewness
        for col, stat in summary_stats.items():
            if abs(stat["skewness"]) > 2:
                direction = "right" if stat["skewness"] > 0 else "left"
                insights.append(
                    f"Column '{col}' is highly skewed to the {direction} "
                    f"(skewness: {stat['skewness']:.2f})."
                )

        # Anomalies
        if anomalies:
            cols_with_anomalies = set(a["column"] for a in anomalies)
            insights.append(
                f"Detected {len(anomalies)} anomalies across "
                f"{len(cols_with_anomalies)} columns."
            )

        return insights
