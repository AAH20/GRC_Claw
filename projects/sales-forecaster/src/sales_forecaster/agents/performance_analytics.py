"""Performance Analytics Agent - tracks KPIs and model performance."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import Any

import numpy as np
import structlog

from sales_forecaster.core.exceptions import AnalysisError
from sales_forecaster.core.metrics import record_agent_error
from sales_forecaster.core.models import (
    ForecastResult,
    PerformanceMetrics,
    SalesRecord,
)

logger = structlog.get_logger(__name__)


class PerformanceAnalyticsAgent:
    """Agent responsible for tracking performance and model accuracy.

    Monitors forecast accuracy, computes KPIs, detects model drift,
    and generates alerts for significant changes.
    """

    def __init__(
        self,
        kpi_window_days: int = 30,
        drift_threshold: float = 0.15,
        alert_channels: list[str] | None = None,
    ) -> None:
        """Initialize the Performance Analytics Agent.

        Args:
            kpi_window_days: Number of days for KPI calculation window.
            drift_threshold: Threshold for model drift detection.
            alert_channels: List of alert channels ('email', 'slack').
        """
        self.kpi_window_days = kpi_window_days
        self.drift_threshold = drift_threshold
        self.alert_channels = alert_channels or ["email"]

    async def evaluate(
        self,
        records: list[SalesRecord],
        forecast: ForecastResult | None = None,
        historical_forecasts: list[ForecastResult] | None = None,
    ) -> PerformanceMetrics:
        """Evaluate performance and generate metrics.

        Args:
            records: Actual sales records.
            forecast: Current forecast result.
            historical_forecasts: Previous forecasts for drift detection.

        Returns:
            PerformanceMetrics with KPIs, accuracy, and alerts.

        Raises:
            AnalysisError: If evaluation fails.
        """
        if not records:
            raise AnalysisError("No records provided for performance evaluation")

        logger.info(
            "Evaluating performance",
            record_count=len(records),
            has_forecast=forecast is not None,
        )

        try:
            end_date = max(r.date for r in records)
            start_date = end_date - timedelta(days=self.kpi_window_days)

            # Filter records to KPI window
            window_records = [
                r for r in records if start_date <= r.date <= end_date
            ]

            total_revenue = sum(r.amount for r in window_records)

            # Calculate forecast accuracy if forecast provided
            forecast_accuracy = 0.0
            bias = 0.0
            mape = 0.0
            rmse = 0.0

            if forecast and forecast.mape is not None:
                mape = forecast.mape
                forecast_accuracy = max(0, 1.0 - mape / 100)
                if forecast.rmse is not None:
                    rmse = forecast.rmse

            # Calculate KPIs
            kpis = self._calculate_kpis(window_records, total_revenue)

            # Detect drift
            alerts = self._detect_alerts(
                window_records, forecast, historical_forecasts, mape
            )

            metrics = PerformanceMetrics(
                period_start=start_date,
                period_end=end_date,
                total_revenue=total_revenue,
                forecast_accuracy=forecast_accuracy,
                bias=bias,
                mape=mape,
                rmse=rmse,
                kpis=kpis,
                alerts=alerts,
            )

            logger.info(
                "Performance evaluation complete",
                total_revenue=total_revenue,
                forecast_accuracy=forecast_accuracy,
                alert_count=len(alerts),
            )
            return metrics

        except Exception as exc:
            record_agent_error("performance_analytics")
            logger.error(
                "Performance evaluation failed",
                error=str(exc),
                exc_info=True,
            )
            raise AnalysisError(
                f"Performance evaluation failed: {exc}"
            ) from exc

    def _calculate_kpis(
        self, records: list[SalesRecord], total_revenue: float
    ) -> dict[str, float]:
        """Calculate key performance indicators.

        Args:
            records: Sales records in the KPI window.
            total_revenue: Total revenue in the window.

        Returns:
            Dictionary of KPI name to value.
        """
        if not records:
            return {}

        unique_customers = len(set(r.customer_id for r in records if r.customer_id))
        unique_products = len(set(r.product_id for r in records if r.product_id))

        # Average deal size
        avg_deal_size = total_revenue / len(records) if records else 0

        # Revenue per customer
        revenue_per_customer = (
            total_revenue / unique_customers if unique_customers > 0 else 0
        )

        # Win rate (if stage info available)
        closed_records = [r for r in records if r.stage and "closed" in r.stage.lower()]
        win_rate = len(closed_records) / len(records) if records else 0

        # Sales cycle (placeholder - would need created/closed dates)
        sales_cycle_days = 0.0

        return {
            "total_revenue": total_revenue,
            "deal_count": float(len(records)),
            "avg_deal_size": avg_deal_size,
            "unique_customers": float(unique_customers),
            "unique_products": float(unique_products),
            "revenue_per_customer": revenue_per_customer,
            "win_rate": win_rate,
            "sales_cycle_days": sales_cycle_days,
        }

    def _detect_alerts(
        self,
        records: list[SalesRecord],
        forecast: ForecastResult | None,
        historical_forecasts: list[ForecastResult] | None,
        current_mape: float,
    ) -> list[dict[str, Any]]:
        """Detect performance alerts and anomalies.

        Args:
            records: Current period records.
            forecast: Current forecast.
            historical_forecasts: Previous forecasts.
            current_mape: Current MAPE value.

        Returns:
            List of alert dictionaries.
        """
        alerts: list[dict[str, Any]] = []

        # Low forecast accuracy alert
        if current_mape > 30:
            alerts.append(
                {
                    "id": str(uuid.uuid4()),
                    "severity": "high",
                    "category": "model_accuracy",
                    "title": "Low forecast accuracy detected",
                    "description": (
                        f"Current MAPE is {current_mape:.1f}%, which exceeds the"
                        " 30% threshold. Consider retraining the model."
                    ),
                    "timestamp": datetime.now().isoformat(),
                }
            )

        # Model drift detection
        if historical_forecasts and len(historical_forecasts) >= 2:
            recent_mapes = [
                f.mape for f in historical_forecasts[-3:] if f.mape is not None
            ]
            if len(recent_mapes) >= 2:
                mape_change = abs(recent_mapes[-1] - recent_mapes[0]) / max(
                    recent_mapes[0], 1
                )
                if mape_change > self.drift_threshold:
                    alerts.append(
                        {
                            "id": str(uuid.uuid4()),
                            "severity": "medium",
                            "category": "model_drift",
                            "title": "Model drift detected",
                            "description": (
                                f"Forecast accuracy has changed by"
                                f" {mape_change:.1%} recently. Model retraining"
                                " recommended."
                            ),
                            "timestamp": datetime.now().isoformat(),
                        }
                    )

        # Revenue drop detection
        if len(records) >= 2:
            amounts = [r.amount for r in records]
            recent_avg = np.mean(amounts[-5:]) if len(amounts) >= 5 else np.mean(amounts)
            overall_avg = np.mean(amounts)
            if overall_avg > 0 and recent_avg < overall_avg * 0.7:
                alerts.append(
                    {
                        "id": str(uuid.uuid4()),
                        "severity": "high",
                        "category": "revenue",
                        "title": "Revenue drop detected",
                        "description": (
                            "Recent revenue is significantly below average."
                            " Immediate attention required."
                        ),
                        "timestamp": datetime.now().isoformat(),
                    }
                )

        return alerts
