"""
Predictive Analytics — forecasting and risk prediction for GRC_Claw.

Provides multi-method forecasting, Monte Carlo simulation, risk prediction,
anomaly detection, and what-if scenario analysis.
"""

from __future__ import annotations

import math
import random
import statistics
from datetime import datetime, timezone
from typing import Any, Optional

from .models import (
    MetricCategory,
    MetricValue,
    Prediction,
    PredictiveModel,
    ForecastMethod,
    PredictionConfidence,
    TrendDirection,
)
from .metrics_registry import get_metric
from .trend_analysis import TrendAnalyzer, LinearRegression


class MonteCarloSimulator:
    """Monte Carlo simulation for risk and cost forecasting."""

    @staticmethod
    def simulate(
        values: list[float],
        periods: int = 12,
        simulations: int = 1000,
        confidence: float = 0.95,
    ) -> dict[str, Any]:
        """
        Run Monte Carlo simulation on historical values.

        Returns distribution statistics and percentile bounds.
        """
        if not values or simulations <= 0:
            return {
                "mean": 0.0,
                "std_dev": 0.0,
                "percentile_5": 0.0,
                "percentile_95": 0.0,
                "simulations": simulations,
            }

        mean_val = statistics.mean(values)
        std_dev = statistics.stdev(values) if len(values) >= 2 else 0.0

        # Run simulations
        results = []
        for _ in range(simulations):
            # Random walk with drift
            drift = 0.0
            if len(values) >= 2:
                drift = (values[-1] - values[0]) / len(values)

            simulated = mean_val
            for _ in range(periods):
                shock = random.gauss(0, std_dev) if std_dev > 0 else 0
                simulated += drift + shock
            results.append(simulated)

        results.sort()
        p5_idx = int(len(results) * 0.05)
        p95_idx = int(len(results) * 0.95)

        return {
            "mean": round(statistics.mean(results), 4),
            "std_dev": round(statistics.stdev(results), 4) if len(results) >= 2 else 0.0,
            "percentile_5": round(results[p5_idx], 4),
            "percentile_95": round(results[p95_idx], 4),
            "min": round(results[0], 4),
            "max": round(results[-1], 4),
            "simulations": simulations,
        }

    @staticmethod
    def simulate_risk_exposure(
        probability: float,
        impact: float,
        simulations: int = 10000,
    ) -> dict[str, Any]:
        """
        Simulate risk exposure using Bernoulli trials.

        Returns expected loss and distribution.
        """
        if simulations <= 0:
            return {"expected_loss": 0.0, "percentile_95": 0.0}

        losses = []
        for _ in range(simulations):
            if random.random() < probability:
                losses.append(impact)
            else:
                losses.append(0.0)

        losses.sort()
        p95_idx = int(len(losses) * 0.95)

        return {
            "expected_loss": round(statistics.mean(losses), 2),
            "percentile_95": round(losses[p95_idx], 2),
            "percentile_99": round(losses[int(len(losses) * 0.99)], 2),
            "max_loss": round(losses[-1], 2),
            "probability": probability,
            "impact": impact,
            "simulations": simulations,
        }


class AnomalyDetector:
    """Statistical anomaly detection for metric values."""

    @staticmethod
    def detect(
        values: list[float],
        method: str = "zscore",
        threshold: float = 3.0,
    ) -> list[dict[str, Any]]:
        """
        Detect anomalies in a time series.

        Methods: 'zscore', 'iqr', 'mad'
        """
        if len(values) < 3:
            return []

        anomalies = []

        if method == "zscore":
            mean_val = statistics.mean(values)
            std_dev = statistics.stdev(values) if len(values) >= 2 else 0.0

            if std_dev == 0:
                return []

            for i, val in enumerate(values):
                z_score = (val - mean_val) / std_dev
                if abs(z_score) > threshold:
                    anomalies.append({
                        "index": i,
                        "value": val,
                        "z_score": round(z_score, 2),
                        "direction": "high" if z_score > 0 else "low",
                    })

        elif method == "iqr":
            sorted_vals = sorted(values)
            q1_idx = len(sorted_vals) // 4
            q3_idx = 3 * len(sorted_vals) // 4
            q1 = sorted_vals[q1_idx]
            q3 = sorted_vals[q3_idx]
            iqr = q3 - q1
            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr

            for i, val in enumerate(values):
                if val < lower or val > upper:
                    anomalies.append({
                        "index": i,
                        "value": val,
                        "direction": "high" if val > upper else "low",
                        "bounds": {"lower": round(lower, 4), "upper": round(upper, 4)},
                    })

        elif method == "mad":
            median_val = statistics.median(values)
            abs_deviations = [abs(v - median_val) for v in values]
            mad = statistics.median(abs_deviations)

            if mad == 0:
                return []

            for i, val in enumerate(values):
                modified_z = 0.6745 * (val - median_val) / mad
                if abs(modified_z) > threshold:
                    anomalies.append({
                        "index": i,
                        "value": val,
                        "modified_z_score": round(modified_z, 2),
                        "direction": "high" if modified_z > 0 else "low",
                    })

        return anomalies

    @staticmethod
    def detect_trend_break(
        values: list[float],
        window: int = 5,
    ) -> Optional[dict[str, Any]]:
        """
        Detect if the recent trend breaks from historical pattern.
        """
        if len(values) < window * 2:
            return None

        historical = values[:-window]
        recent = values[-window:]

        hist_mean = statistics.mean(historical)
        hist_std = statistics.stdev(historical) if len(historical) >= 2 else 0.0

        if hist_std == 0:
            return None

        recent_mean = statistics.mean(recent)
        z_score = (recent_mean - hist_mean) / hist_std

        if abs(z_score) > 2.0:
            return {
                "detected": True,
                "z_score": round(z_score, 2),
                "historical_mean": round(hist_mean, 4),
                "recent_mean": round(recent_mean, 4),
                "direction": "up" if z_score > 0 else "down",
                "severity": "high" if abs(z_score) > 3.0 else "medium",
            }

        return None


class RiskPredictor:
    """Predict future risk levels based on historical patterns."""

    @staticmethod
    def predict_risk_level(
        metric_id: str,
        values: list[MetricValue],
        forecast_periods: int = 3,
    ) -> Optional[dict[str, Any]]:
        """
        Predict risk level for a metric based on trend and thresholds.
        """
        metric_def = get_metric(metric_id)
        if not metric_def or len(values) < 3:
            return None

        raw_values = [v.value for v in values]
        x = list(range(len(raw_values)))

        slope, intercept, r_squared = LinearRegression.fit(x, raw_values)

        # Predict future values
        predictions = []
        for i in range(forecast_periods):
            pred = LinearRegression.predict(slope, intercept, len(raw_values) + i)
            predictions.append(pred)

        # Determine risk level based on predictions vs thresholds
        direction = metric_def.tier1_direction
        risk_level = "low"
        breach_period = None

        for i, pred in enumerate(predictions):
            if direction == "lte":
                if pred > metric_def.tier3_threshold:
                    risk_level = "critical"
                    breach_period = i + 1
                    break
                elif pred > metric_def.tier2_threshold and risk_level != "critical":
                    risk_level = "high"
                    breach_period = i + 1
                elif pred > metric_def.tier1_threshold and risk_level == "low":
                    risk_level = "medium"
                    breach_period = i + 1
            else:  # gte
                if pred < metric_def.tier3_threshold:
                    risk_level = "critical"
                    breach_period = i + 1
                    break
                elif pred < metric_def.tier2_threshold and risk_level != "critical":
                    risk_level = "high"
                    breach_period = i + 1
                elif pred < metric_def.tier1_threshold and risk_level == "low":
                    risk_level = "medium"
                    breach_period = i + 1

        return {
            "metric_id": metric_id,
            "metric_name": metric_def.name,
            "current_risk": risk_level,
            "predicted_risk": risk_level,
            "breach_period": breach_period,
            "predictions": [round(p, 4) for p in predictions],
            "slope": round(slope, 6),
            "r_squared": r_squared,
            "confidence": "high" if r_squared > 0.7 else "medium" if r_squared > 0.4 else "low",
        }


class WhatIfAnalyzer:
    """What-if scenario analysis for metrics."""

    @staticmethod
    def analyze(
        metric_id: str,
        current_value: float,
        target_value: float,
        historical_values: list[float],
    ) -> dict[str, Any]:
        """
        Analyze what it would take to reach a target value.
        """
        metric_def = get_metric(metric_id)
        if not metric_def:
            return {}

        gap = target_value - current_value
        gap_pct = (gap / current_value * 100) if current_value != 0 else 0.0

        # Compute required improvement rate
        if historical_values and len(historical_values) >= 2:
            recent_trend = (historical_values[-1] - historical_values[0]) / len(historical_values)
            periods_to_target = abs(gap / recent_trend) if recent_trend != 0 else float("inf")
        else:
            recent_trend = 0.0
            periods_to_target = float("inf")

        # Feasibility assessment
        if abs(gap_pct) < 5:
            feasibility = "high"
        elif abs(gap_pct) < 20:
            feasibility = "medium"
        else:
            feasibility = "low"

        return {
            "metric_id": metric_id,
            "metric_name": metric_def.name,
            "current_value": current_value,
            "target_value": target_value,
            "gap": round(gap, 4),
            "gap_pct": round(gap_pct, 2),
            "recent_trend": round(recent_trend, 6),
            "periods_to_target": round(periods_to_target, 1) if periods_to_target != float("inf") else None,
            "feasibility": feasibility,
            "recommendations": WhatIfAnalyzer._generate_recommendations(
                metric_id, gap, feasibility, metric_def.tier1_direction
            ),
        }

    @staticmethod
    def _generate_recommendations(
        metric_id: str, gap: float, feasibility: str, direction: str
    ) -> list[str]:
        """Generate recommendations for closing the gap."""
        recs = []

        if feasibility == "high":
            recs.append("Target is achievable with minor adjustments")
            recs.append("Focus on incremental improvements")
        elif feasibility == "medium":
            recs.append("Target requires moderate effort")
            recs.append("Consider process improvements and additional resources")
        else:
            recs.append("Target requires significant intervention")
            recs.append("Consider strategic initiatives and executive sponsorship")

        if direction == "lte" and gap > 0:
            recs.append(f"Need to reduce by {abs(gap):.2f} to reach target")
        elif direction == "gte" and gap < 0:
            recs.append(f"Need to increase by {abs(gap):.2f} to reach target")

        return recs


class PredictiveAnalyticsEngine:
    """
    Main predictive analytics engine. Combines forecasting, risk prediction,
    anomaly detection, and what-if analysis.
    """

    def __init__(self):
        self.trend_analyzer = TrendAnalyzer()
        self.monte_carlo = MonteCarloSimulator()
        self.anomaly_detector = AnomalyDetector()
        self.risk_predictor = RiskPredictor()
        self.what_if = WhatIfAnalyzer()

    def generate_forecast(
        self,
        metric_id: str,
        values: list[MetricValue],
        method: ForecastMethod = ForecastMethod.LINEAR_REGRESSION,
        periods: int = 6,
    ) -> Optional[PredictiveModel]:
        """Generate a forecast for a metric."""
        return self.trend_analyzer.forecast(metric_id, values, method, periods)

    def detect_anomalies(
        self,
        metric_id: str,
        values: list[MetricValue],
        method: str = "zscore",
    ) -> list[dict[str, Any]]:
        """Detect anomalies in metric values."""
        raw_values = [v.value for v in values]
        return self.anomaly_detector.detect(raw_values, method)

    def predict_risk(
        self,
        metric_id: str,
        values: list[MetricValue],
    ) -> Optional[dict[str, Any]]:
        """Predict risk level for a metric."""
        return self.risk_predictor.predict_risk_level(metric_id, values)

    def run_monte_carlo(
        self,
        metric_id: str,
        values: list[MetricValue],
        periods: int = 12,
        simulations: int = 1000,
    ) -> dict[str, Any]:
        """Run Monte Carlo simulation for a metric."""
        raw_values = [v.value for v in values]
        result = self.monte_carlo.simulate(raw_values, periods, simulations)
        metric_def = get_metric(metric_id)
        if metric_def:
            result["metric_id"] = metric_id
            result["metric_name"] = metric_def.name
        return result

    def what_if_analysis(
        self,
        metric_id: str,
        current_value: float,
        target_value: float,
        historical_values: list[float],
    ) -> dict[str, Any]:
        """Run what-if scenario analysis."""
        return self.what_if.analyze(metric_id, current_value, target_value, historical_values)

    def comprehensive_analysis(
        self,
        metric_id: str,
        values: list[MetricValue],
    ) -> dict[str, Any]:
        """
        Run comprehensive predictive analysis on a metric.

        Combines trend analysis, forecasting, anomaly detection,
        and risk prediction into a single report.
        """
        metric_def = get_metric(metric_id)
        if not metric_def or len(values) < 2:
            return {"error": f"Insufficient data for metric {metric_id}"}

        # Trend analysis
        trend = self.trend_analyzer.analyze(metric_id, values)

        # Forecast
        forecast = self.generate_forecast(metric_id, values)

        # Anomaly detection
        anomalies = self.detect_anomalies(metric_id, values)

        # Risk prediction
        risk = self.predict_risk(metric_id, values)

        # Monte Carlo
        mc = self.run_monte_carlo(metric_id, values)

        return {
            "metric_id": metric_id,
            "metric_name": metric_def.name,
            "category": metric_def.category.value,
            "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
            "trend_analysis": trend.to_dict() if trend else None,
            "forecast": forecast.to_dict() if forecast else None,
            "anomalies_detected": len(anomalies),
            "anomaly_details": anomalies[:5],  # Top 5
            "risk_prediction": risk,
            "monte_carlo": mc,
            "summary": self._generate_summary(trend, forecast, anomalies, risk),
        }

    def _generate_summary(
        self,
        trend,
        forecast,
        anomalies,
        risk,
    ) -> dict[str, Any]:
        """Generate executive summary from analysis results."""
        summary = {
            "overall_assessment": "",
            "key_findings": [],
            "recommended_actions": [],
        }

        if trend:
            summary["key_findings"].append(
                f"Trend: {trend.direction.value} (R²={trend.r_squared})"
            )
            if trend.insights:
                summary["key_findings"].extend(trend.insights[:3])

        if anomalies:
            summary["key_findings"].append(
                f"{len(anomalies)} anomaly/anomalies detected"
            )

        if risk:
            summary["overall_assessment"] = f"Risk level: {risk.get('current_risk', 'unknown')}"
            if risk.get("breach_period"):
                summary["recommended_actions"].append(
                    f"Threshold breach predicted in period {risk['breach_period']} — take preventive action"
                )

        if forecast:
            if forecast.confidence_level == PredictionConfidence.LOW:
                summary["recommended_actions"].append(
                    "Low forecast confidence — collect more data before making decisions"
                )

        return summary
