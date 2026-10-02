"""
Dashboard analytics — metrics calculation, trend analysis, anomaly detection,
compliance aggregation, risk aggregation, and governance scoring.
"""

from __future__ import annotations

import math
import statistics
from collections import defaultdict
from typing import Any

from .models import (
    DashboardConfig,
    FilterCriteria,
    GovernanceScore,
    MetricAggregation,
    TrendDirection,
)


class MetricCalculator:
    """
    Calculates aggregated metrics from raw data points.
    Supports count, sum, avg, min, max, median, percentiles, rates, and ratios.
    """

    def calculate(self, values: list[float], aggregation: MetricAggregation) -> float:
        """Calculate a single metric from a list of values."""
        if not values:
            return 0.0

        if aggregation == MetricAggregation.COUNT:
            return float(len(values))
        elif aggregation == MetricAggregation.SUM:
            return sum(values)
        elif aggregation == MetricAggregation.AVG:
            return statistics.mean(values)
        elif aggregation == MetricAggregation.MIN:
            return min(values)
        elif aggregation == MetricAggregation.MAX:
            return max(values)
        elif aggregation == MetricAggregation.MEDIAN:
            return statistics.median(values)
        elif aggregation == MetricAggregation.P95:
            return self._percentile(values, 95)
        elif aggregation == MetricAggregation.P99:
            return self._percentile(values, 99)
        elif aggregation == MetricAggregation.DISTINCT:
            return float(len(set(values)))
        else:
            return 0.0

    def calculate_rate(self, numerator: float, denominator: float, scale: float = 100.0) -> float:
        """Calculate a rate percentage."""
        if denominator == 0:
            return 0.0
        return round((numerator / denominator) * scale, 2)

    def calculate_ratio(self, numerator: float, denominator: float) -> float:
        """Calculate a ratio."""
        if denominator == 0:
            return 0.0
        return round(numerator / denominator, 4)

    def calculate_all(self, values: list[float]) -> dict[str, float]:
        """Calculate all supported metrics for a dataset."""
        return {
            "count": self.calculate(values, MetricAggregation.COUNT),
            "sum": self.calculate(values, MetricAggregation.SUM),
            "avg": self.calculate(values, MetricAggregation.AVG),
            "min": self.calculate(values, MetricAggregation.MIN),
            "max": self.calculate(values, MetricAggregation.MAX),
            "median": self.calculate(values, MetricAggregation.MEDIAN),
            "p95": self.calculate(values, MetricAggregation.P95),
            "p99": self.calculate(values, MetricAggregation.P99),
        }

    def compare_periods(
        self,
        current: list[float],
        previous: list[float],
    ) -> dict[str, Any]:
        """Compare two periods and return change metrics."""
        curr_avg = statistics.mean(current) if current else 0
        prev_avg = statistics.mean(previous) if previous else 0
        change = curr_avg - prev_avg
        change_pct = (change / prev_avg * 100) if prev_avg != 0 else 0

        if change_pct > 5:
            direction = TrendDirection.UP
        elif change_pct < -5:
            direction = TrendDirection.DOWN
        else:
            direction = TrendDirection.FLAT

        return {
            "current_avg": round(curr_avg, 2),
            "previous_avg": round(prev_avg, 2),
            "change": round(change, 2),
            "change_pct": round(change_pct, 2),
            "direction": direction.value,
        }

    @staticmethod
    def _percentile(values: list[float], p: float) -> float:
        """Calculate percentile using linear interpolation."""
        sorted_vals = sorted(values)
        k = (len(sorted_vals) - 1) * p / 100
        f = math.floor(k)
        c = math.ceil(k)
        if f == c:
            return sorted_vals[int(k)]
        return sorted_vals[f] * (c - k) + sorted_vals[c] * (k - f)


class TrendAnalyzer:
    """
    Analyzes trends in time-series data.
    Detects direction, momentum, seasonality, and inflection points.
    """

    def analyze(self, values: list[float], labels: list[str] | None = None) -> dict[str, Any]:
        """Perform comprehensive trend analysis."""
        if len(values) < 2:
            return {
                "direction": TrendDirection.UNKNOWN.value,
                "momentum": 0.0,
                "volatility": 0.0,
                "data_points": len(values),
            }

        # Overall direction
        first_val = values[0]
        last_val = values[-1]
        change = last_val - first_val
        change_pct = (change / first_val * 100) if first_val != 0 else 0

        if change_pct > 5:
            direction = TrendDirection.UP
        elif change_pct < -5:
            direction = TrendDirection.DOWN
        else:
            direction = TrendDirection.FLAT

        # Momentum (rate of change)
        momentum = self._calculate_momentum(values)

        # Volatility (coefficient of variation)
        volatility = self._calculate_volatility(values)

        # Moving averages
        ma_3 = self._moving_average(values, 3)
        ma_7 = self._moving_average(values, 7)

        # Linear regression slope
        slope = self._linear_regression_slope(values)

        return {
            "direction": direction.value,
            "change": round(change, 2),
            "change_pct": round(change_pct, 2),
            "momentum": round(momentum, 4),
            "volatility": round(volatility, 4),
            "slope": round(slope, 4),
            "moving_average_3": ma_3,
            "moving_average_7": ma_7,
            "data_points": len(values),
            "start_value": first_val,
            "end_value": last_val,
            "min_value": min(values),
            "max_value": max(values),
        }

    def detect_seasonality(self, values: list[float], period: int = 7) -> dict[str, Any]:
        """Detect seasonal patterns in the data."""
        if len(values) < period * 2:
            return {"detected": False, "reason": "insufficient_data"}

        # Calculate seasonal indices
        seasonal_averages = []
        for i in range(period):
            season_values = [values[j] for j in range(i, len(values), period)]
            seasonal_averages.append(statistics.mean(season_values) if season_values else 0)

        overall_avg = statistics.mean(values) if values else 1
        seasonal_indices = [
            round(avg / overall_avg, 3) if overall_avg else 1.0
            for avg in seasonal_averages
        ]

        # Detect peak and trough seasons
        peak_season = seasonal_indices.index(max(seasonal_indices))
        trough_season = seasonal_indices.index(min(seasonal_indices))

        return {
            "detected": True,
            "period": period,
            "seasonal_indices": seasonal_indices,
            "peak_season": peak_season,
            "trough_season": trough_season,
            "strength": round(max(seasonal_indices) - min(seasonal_indices), 3),
        }

    def forecast(self, values: list[float], periods: int = 7) -> list[float]:
        """Simple linear forecast for future periods."""
        if len(values) < 2:
            return [values[-1]] * periods if values else [0.0] * periods

        slope = self._linear_regression_slope(values)
        last_val = values[-1]
        forecast = []
        for i in range(1, periods + 1):
            forecast.append(round(last_val + slope * i, 2))
        return forecast

    def _calculate_momentum(self, values: list[float]) -> float:
        """Calculate momentum as the rate of change."""
        if len(values) < 2:
            return 0.0
        changes = [values[i] - values[i - 1] for i in range(1, len(values))]
        return statistics.mean(changes) if changes else 0.0

    def _calculate_volatility(self, values: list[float]) -> float:
        """Calculate volatility as coefficient of variation."""
        if len(values) < 2:
            return 0.0
        mean_val = statistics.mean(values)
        if mean_val == 0:
            return 0.0
        return statistics.stdev(values) / abs(mean_val)

    def _moving_average(self, values: list[float], window: int) -> list[float]:
        """Calculate simple moving average."""
        if window <= 1 or len(values) < window:
            return values[:]
        return [
            round(statistics.mean(values[i:i + window]), 2)
            for i in range(len(values) - window + 1)
        ]

    def _linear_regression_slope(self, values: list[float]) -> float:
        """Calculate the slope of a linear regression line."""
        n = len(values)
        if n < 2:
            return 0.0
        x_mean = (n - 1) / 2
        y_mean = statistics.mean(values)
        numerator = sum((i - x_mean) * (y - y_mean) for i, y in enumerate(values))
        denominator = sum((i - x_mean) ** 2 for i in range(n))
        return numerator / denominator if denominator != 0 else 0.0


class AnomalyDetector:
    """
    Detects anomalies in metric data using statistical methods.
    Supports Z-score, IQR, and moving average deviation methods.
    """

    def detect(self, values: list[float], method: str = "zscore", threshold: float = 2.0) -> list[dict[str, Any]]:
        """Detect anomalies in a dataset."""
        if len(values) < 3:
            return []

        if method == "zscore":
            return self._zscore_detection(values, threshold)
        elif method == "iqr":
            return self._iqr_detection(values)
        elif method == "moving_avg":
            return self._moving_avg_detection(values, threshold)
        else:
            return self._zscore_detection(values, threshold)

    def detect_in_context(
        self,
        values: list[float],
        labels: list[str],
        method: str = "zscore",
        threshold: float = 2.0,
    ) -> list[dict[str, Any]]:
        """Detect anomalies with contextual information."""
        anomalies = self.detect(values, method, threshold)
        for anomaly in anomalies:
            idx = anomaly["index"]
            anomaly["label"] = labels[idx] if idx < len(labels) else f"index_{idx}"
        return anomalies

    def _zscore_detection(self, values: list[float], threshold: float) -> list[dict[str, Any]]:
        """Z-score based anomaly detection."""
        mean_val = statistics.mean(values)
        std_val = statistics.stdev(values) if len(values) > 1 else 0

        if std_val == 0:
            return []

        anomalies = []
        for i, val in enumerate(values):
            zscore = (val - mean_val) / std_val
            if abs(zscore) > threshold:
                anomalies.append({
                    "index": i,
                    "value": val,
                    "zscore": round(zscore, 2),
                    "expected": round(mean_val, 2),
                    "deviation": round(val - mean_val, 2),
                    "severity": "high" if abs(zscore) > 3 else "medium",
                })
        return anomalies

    def _iqr_detection(self, values: list[float]) -> list[dict[str, Any]]:
        """Interquartile range based anomaly detection."""
        sorted_vals = sorted(values)
        q1 = self._percentile(sorted_vals, 25)
        q3 = self._percentile(sorted_vals, 75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr

        anomalies = []
        for i, val in enumerate(values):
            if val < lower or val > upper:
                anomalies.append({
                    "index": i,
                    "value": val,
                    "expected": round(statistics.median(values), 2),
                    "deviation": round(val - statistics.median(values), 2),
                    "severity": "high" if val < lower - iqr or val > upper + iqr else "medium",
                    "bound": "lower" if val < lower else "upper",
                })
        return anomalies

    def _moving_avg_detection(self, values: list[float], threshold: float) -> list[dict[str, Any]]:
        """Moving average deviation based anomaly detection."""
        window = min(5, len(values) // 3)
        if window < 2:
            return []

        anomalies = []
        for i in range(window, len(values)):
            window_vals = values[i - window:i]
            ma = statistics.mean(window_vals)
            std_val = statistics.stdev(window_vals) if len(window_vals) > 1 else 0

            if std_val > 0:
                zscore = (values[i] - ma) / std_val
                if abs(zscore) > threshold:
                    anomalies.append({
                        "index": i,
                        "value": values[i],
                        "zscore": round(zscore, 2),
                        "expected": round(ma, 2),
                        "deviation": round(values[i] - ma, 2),
                        "severity": "high" if abs(zscore) > 3 else "medium",
                    })
        return anomalies

    @staticmethod
    def _percentile(values: list[float], p: float) -> float:
        sorted_vals = sorted(values)
        k = (len(sorted_vals) - 1) * p / 100
        f = math.floor(k)
        c = math.ceil(k)
        if f == c:
            return sorted_vals[int(k)]
        return sorted_vals[f] * (c - k) + sorted_vals[c] * (k - f)


class ComplianceAggregator:
    """
    Aggregates compliance data across frameworks, controls, and assessments.
    """

    def aggregate(self, compliance_data: list[dict[str, Any]]) -> dict[str, Any]:
        """Aggregate compliance metrics from multiple sources."""
        if not compliance_data:
            return self._empty_result()

        total_controls = len(compliance_data)
        status_counts = defaultdict(int)
        framework_scores = defaultdict(list)
        domain_scores = defaultdict(list)

        for item in compliance_data:
            status = item.get("status", "unknown")
            status_counts[status] += 1

            framework = item.get("framework", "unknown")
            score = item.get("score", 0)
            if score is not None:
                framework_scores[framework].append(score)

            domain = item.get("domain", "unknown")
            if score is not None:
                domain_scores[domain].append(score)

        compliant = status_counts.get("compliant", 0)
        partial = status_counts.get("partially_compliant", 0)
        non_compliant = status_counts.get("non_compliant", 0)
        not_assessed = status_counts.get("not_assessed", 0)

        assessed = compliant + partial + non_compliant
        compliance_rate = (compliant / assessed * 100) if assessed > 0 else 0

        framework_summary = {}
        for fw, scores in framework_scores.items():
            framework_summary[fw] = {
                "control_count": len(scores),
                "avg_score": round(statistics.mean(scores), 2) if scores else 0,
                "min_score": min(scores) if scores else 0,
                "max_score": max(scores) if scores else 0,
            }

        domain_summary = {}
        for domain, scores in domain_scores.items():
            domain_summary[domain] = {
                "avg_score": round(statistics.mean(scores), 2) if scores else 0,
                "control_count": len(scores),
            }

        return {
            "total_controls": total_controls,
            "status_breakdown": dict(status_counts),
            "compliance_rate": round(compliance_rate, 1),
            "assessed_count": assessed,
            "not_assessed_count": not_assessed,
            "framework_summary": framework_summary,
            "domain_summary": domain_summary,
            "overall_status": self._determine_overall_status(compliance_rate, non_compliant, assessed),
        }

    def calculate_framework_score(self, controls: list[dict[str, Any]]) -> dict[str, Any]:
        """Calculate a compliance score for a single framework."""
        if not controls:
            return {"score": 0, "status": "not_assessed"}

        total = len(controls)
        passed = sum(1 for c in controls if c.get("status") == "compliant")
        failed = sum(1 for c in controls if c.get("status") == "non_compliant")
        partial = sum(1 for c in controls if c.get("status") == "partially_compliant")

        score = (passed / total * 100) if total > 0 else 0

        if score >= 90:
            status = "compliant"
        elif score >= 70:
            status = "partially_compliant"
        elif score > 0:
            status = "non_compliant"
        else:
            status = "not_assessed"

        return {
            "score": round(score, 1),
            "status": status,
            "total_controls": total,
            "passed": passed,
            "failed": failed,
            "partial": partial,
        }

    def _determine_overall_status(self, rate: float, non_compliant: int, assessed: int) -> str:
        if assessed == 0:
            return "not_assessed"
        if rate >= 90:
            return "compliant"
        elif rate >= 70:
            return "partially_compliant"
        else:
            return "non_compliant"

    def _empty_result(self) -> dict[str, Any]:
        return {
            "total_controls": 0,
            "status_breakdown": {},
            "compliance_rate": 0,
            "assessed_count": 0,
            "not_assessed_count": 0,
            "framework_summary": {},
            "domain_summary": {},
            "overall_status": "not_assessed",
        }


class RiskAggregator:
    """
    Aggregates risk data across domains, categories, and treatment plans.
    """

    def aggregate(self, risk_data: list[dict[str, Any]]) -> dict[str, Any]:
        """Aggregate risk metrics from multiple sources."""
        if not risk_data:
            return self._empty_result()

        total_risks = len(risk_data)
        tier_counts = defaultdict(int)
        domain_risks = defaultdict(list)
        category_risks = defaultdict(list)
        status_counts = defaultdict(int)
        scores = []

        for risk in risk_data:
            tier = risk.get("tier", "unknown")
            tier_counts[tier] += 1

            status = risk.get("status", "unknown")
            status_counts[status] += 1

            score = risk.get("score", 0)
            if score is not None:
                scores.append(score)

            domain = risk.get("domain", "unknown")
            domain_risks[domain].append(risk)

            category = risk.get("category", "unknown")
            category_risks[category].append(risk)

        avg_score = statistics.mean(scores) if scores else 0
        critical_count = tier_counts.get("critical", 0)
        high_count = tier_counts.get("high", 0)

        domain_summary = {}
        for domain, risks in domain_risks.items():
            domain_scores = [r.get("score", 0) for r in risks if r.get("score") is not None]
            domain_summary[domain] = {
                "count": len(risks),
                "avg_score": round(statistics.mean(domain_scores), 2) if domain_scores else 0,
                "critical": sum(1 for r in risks if r.get("tier") == "critical"),
                "high": sum(1 for r in risks if r.get("tier") == "high"),
            }

        category_summary = {}
        for cat, risks in category_risks.items():
            category_summary[cat] = {
                "count": len(risks),
                "avg_score": round(
                    statistics.mean([r.get("score", 0) for r in risks if r.get("score") is not None]), 2
                ) if any(r.get("score") is not None for r in risks) else 0,
            }

        return {
            "total_risks": total_risks,
            "tier_breakdown": dict(tier_counts),
            "status_breakdown": dict(status_counts),
            "average_score": round(avg_score, 2),
            "critical_count": critical_count,
            "high_count": critical_count + high_count,
            "domain_summary": domain_summary,
            "category_summary": category_summary,
            "risk_level": self._determine_risk_level(avg_score, critical_count, high_count),
        }

    def calculate_risk_trend(
        self,
        current_risks: list[dict[str, Any]],
        previous_risks: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Compare risk profiles between two periods."""
        current_agg = self.aggregate(current_risks)
        previous_agg = self.aggregate(previous_risks)

        score_change = current_agg["average_score"] - previous_agg["average_score"]
        count_change = current_agg["total_risks"] - previous_agg["total_risks"]

        if score_change > 0.5:
            direction = TrendDirection.UP
        elif score_change < -0.5:
            direction = TrendDirection.DOWN
        else:
            direction = TrendDirection.FLAT

        return {
            "score_change": round(score_change, 2),
            "count_change": count_change,
            "direction": direction.value,
            "current": current_agg,
            "previous": previous_agg,
        }

    def _determine_risk_level(self, avg_score: float, critical: int, high: int) -> str:
        if critical > 0 or avg_score >= 4.0:
            return "critical"
        elif high > 2 or avg_score >= 3.0:
            return "high"
        elif avg_score >= 2.0:
            return "medium"
        elif avg_score >= 1.0:
            return "low"
        else:
            return "minimal"

    def _empty_result(self) -> dict[str, Any]:
        return {
            "total_risks": 0,
            "tier_breakdown": {},
            "status_breakdown": {},
            "average_score": 0,
            "critical_count": 0,
            "high_count": 0,
            "domain_summary": {},
            "category_summary": {},
            "risk_level": "minimal",
        }


class GovernanceScorer:
    """
    Calculates overall governance health scores based on
    multiple dimensions: governance, risk, compliance, operational, security.
    """

    def __init__(self):
        self.compliance_aggregator = ComplianceAggregator()
        self.risk_aggregator = RiskAggregator()

    def calculate(
        self,
        config: DashboardConfig,
        widget_results: dict[str, Any],
        filters: list[FilterCriteria],
    ) -> GovernanceScore:
        """Calculate the overall governance score."""
        # Extract data from widget results
        compliance_data = []
        risk_data = []
        operational_data = []
        security_data = []

        for wid, wdata in widget_results.items():
            if wdata.get("status") != "ok":
                continue
            data = wdata.get("data", {})
            widget = wdata.get("widget", {})
            source = widget.get("data_source", "")

            if source == "compliance_framework":
                if isinstance(data, list):
                    compliance_data.extend(data)
                elif isinstance(data, dict) and "controls" in data:
                    compliance_data.extend(data["controls"])
            elif source == "risk_register":
                if isinstance(data, list):
                    risk_data.extend(data)
                elif isinstance(data, dict) and "risks" in data:
                    risk_data.extend(data["risks"])
            elif source == "workflow":
                if isinstance(data, list):
                    operational_data.extend(data)
            elif source == "notification":
                if isinstance(data, dict) and "alerts" in data:
                    security_data.extend(data["alerts"])

        # Calculate dimension scores
        compliance_score = self._calculate_compliance_score(compliance_data)
        risk_score = self._calculate_risk_score(risk_data)
        operational_score = self._calculate_operational_score(operational_data, widget_results)
        security_score = self._calculate_security_score(security_data)
        governance_score = self._calculate_governance_score(
            compliance_score, risk_score, operational_score, security_score
        )

        # Overall score (weighted average)
        overall = (
            governance_score * 0.25
            + risk_score * 0.25
            + compliance_score * 0.25
            + operational_score * 0.15
            + security_score * 0.10
        )

        # Determine trend
        trend = TrendDirection.FLAT
        change_pct = 0.0

        # Generate recommendations
        recommendations = self._generate_recommendations(
            compliance_score, risk_score, operational_score, security_score
        )

        return GovernanceScore(
            overall=round(overall, 1),
            governance=round(governance_score, 1),
            risk=round(risk_score, 1),
            compliance=round(compliance_score, 1),
            operational=round(operational_score, 1),
            security=round(security_score, 1),
            trend=trend,
            change_pct=change_pct,
            breakdown={
                "governance": round(governance_score, 1),
                "risk": round(risk_score, 1),
                "compliance": round(compliance_score, 1),
                "operational": round(operational_score, 1),
                "security": round(security_score, 1),
            },
            recommendations=recommendations,
        )

    def _calculate_compliance_score(self, data: list[dict]) -> float:
        if not data:
            return 50.0  # Neutral score when no data
        agg = self.compliance_aggregator.aggregate(data)
        return agg.get("compliance_rate", 50.0)

    def _calculate_risk_score(self, data: list[dict]) -> float:
        if not data:
            return 50.0
        agg = self.risk_aggregator.aggregate(data)
        avg_score = agg.get("average_score", 0)
        # Invert: lower risk score = higher governance score
        return max(0, 100 - (avg_score * 20))

    def _calculate_operational_score(self, data: list[dict], widget_results: dict) -> float:
        # Based on widget success rate and operational metrics
        total_widgets = len(widget_results)
        if total_widgets == 0:
            return 50.0
        successful = sum(1 for w in widget_results.values() if w.get("status") == "ok")
        success_rate = (successful / total_widgets) * 100
        return round(success_rate, 1)

    def _calculate_security_score(self, data: list[dict]) -> float:
        if not data:
            return 50.0
        # Based on alert severity distribution
        critical = sum(1 for d in data if d.get("severity") == "critical")
        high = sum(1 for d in data if d.get("severity") == "high")
        total = len(data)
        if total == 0:
            return 50.0
        # Fewer critical/high alerts = higher score
        penalty = (critical * 20 + high * 10) / total
        return max(0, 100 - penalty)

    def _calculate_governance_score(self, compliance: float, risk: float, operational: float, security: float) -> float:
        return round((compliance * 0.3 + risk * 0.3 + operational * 0.2 + security * 0.2), 1)

    def _generate_recommendations(
        self,
        compliance: float,
        risk: float,
        operational: float,
        security: float,
    ) -> list[str]:
        recs = []
        if compliance < 70:
            recs.append("Improve compliance posture — address non-compliant controls")
        if risk < 60:
            recs.append("Review and treat high-priority risks immediately")
        if operational < 80:
            recs.append("Investigate widget errors and improve operational reliability")
        if security < 70:
            recs.append("Address critical security alerts and strengthen controls")
        if not recs:
            recs.append("Governance posture is strong — maintain current practices")
        return recs


class DashboardAnalytics:
    """
    High-level analytics facade that combines all analytics components
    into a unified interface for dashboard consumption.
    """

    def __init__(self):
        self.metric_calculator = MetricCalculator()
        self.trend_analyzer = TrendAnalyzer()
        self.anomaly_detector = AnomalyDetector()
        self.compliance_aggregator = ComplianceAggregator()
        self.risk_aggregator = RiskAggregator()
        self.governance_scorer = GovernanceScorer()

    def analyze_dashboard(
        self,
        config: DashboardConfig,
        widget_results: dict[str, Any],
        filters: list[FilterCriteria],
    ) -> dict[str, Any]:
        """Perform comprehensive analytics on dashboard data."""
        score = self.governance_scorer.calculate(config, widget_results, filters)

        # Collect all numeric values for trend analysis
        all_values = []
        for wdata in widget_results.values():
            data = wdata.get("data", {})
            if isinstance(data, dict):
                for key in ["value", "values", "data"]:
                    val = data.get(key)
                    if isinstance(val, (int, float)):
                        all_values.append(val)
                    elif isinstance(val, list):
                        all_values.extend([v for v in val if isinstance(v, (int, float))])

        trend = self.trend_analyzer.analyze(all_values) if len(all_values) >= 2 else {}
        anomalies = self.anomaly_detector.detect(all_values) if len(all_values) >= 3 else []

        return {
            "governance_score": {
                "overall": score.overall,
                "governance": score.governance,
                "risk": score.risk,
                "compliance": score.compliance,
                "operational": score.operational,
                "security": score.security,
                "trend": score.trend.value,
                "change_pct": score.change_pct,
                "breakdown": score.breakdown,
                "recommendations": score.recommendations,
            },
            "trend_analysis": trend,
            "anomalies": anomalies,
            "summary": {
                "total_widgets": len(config.widgets),
                "active_widgets": sum(1 for w in config.widgets if w.enabled),
                "data_sources": list(set(w.data_source.value for w in config.widgets)),
                "anomaly_count": len(anomalies),
            },
        }

    def generate_executive_summary(self, analytics: dict[str, Any]) -> str:
        """Generate an executive summary from analytics data."""
        score = analytics.get("governance_score", {})
        summary = analytics.get("summary", {})
        trend = analytics.get("trend_analysis", {})

        lines = [
            "# Executive Governance Summary",
            "",
            f"**Overall Score:** {score.get('overall', 0):.1f}/100",
            f"**Trend:** {score.get('trend', 'unknown')} ({score.get('change_pct', 0):+.1f}%)",
            "",
            "## Score Breakdown",
            "",
            "| Dimension | Score |",
            "|-----------|-------|",
            f"| Governance | {score.get('governance', 0):.1f} |",
            f"| Risk | {score.get('risk', 0):.1f} |",
            f"| Compliance | {score.get('compliance', 0):.1f} |",
            f"| Operational | {score.get('operational', 0):.1f} |",
            f"| Security | {score.get('security', 0):.1f} |",
            "",
            "## Key Metrics",
            "",
            f"- Total Widgets: {summary.get('total_widgets', 0)}",
            f"- Active Widgets: {summary.get('active_widgets', 0)}",
            f"- Data Sources: {', '.join(summary.get('data_sources', []))}",
            f"- Anomalies Detected: {summary.get('anomaly_count', 0)}",
            "",
        ]

        if trend:
            lines.extend([
                "## Trend Analysis",
                "",
                f"- Direction: {trend.get('direction', 'unknown')}",
                f"- Change: {trend.get('change', 0):+.2f} ({trend.get('change_pct', 0):+.1f}%)",
                f"- Momentum: {trend.get('momentum', 0):.4f}",
                f"- Volatility: {trend.get('volatility', 0):.4f}",
                "",
            ])

        recs = score.get("recommendations", [])
        if recs:
            lines.append("## Recommendations")
            lines.append("")
            for rec in recs:
                lines.append(f"- {rec}")
            lines.append("")

        return "\n".join(lines)
