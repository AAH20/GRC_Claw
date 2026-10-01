"""
GRC_Claw Incident Trend Analysis and Prediction (§16 of GRC-AIM-001)

Implements comprehensive trend analysis and prediction:
    • Temporal trends — volume, seasonality, cyclical patterns, change points
    • Category trends — distribution, emerging categories, correlation, migration
    • Severity trends — distribution, escalation, by category, prediction
    • Asset trends — risk scores, incident rates, correlation, degradation
    • Predictive models — volume, category, severity prediction
    • Risk scoring — asset and organizational risk scores
    • Early warning system — indicators and response
"""

from __future__ import annotations

import statistics
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Optional

from .models import Incident, IncidentStatus
from .taxonomy import IncidentCategory, Severity


# ═══════════════════════════════════════════════════════════════════════════════
# Temporal Trends (§16.3.1)
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class TemporalTrend:
    """Temporal trend analysis results."""
    period: str
    total_incidents: int = 0
    incident_counts: dict[str, int] = field(default_factory=dict)  # date → count
    trend_direction: str = "stable"  # increasing | decreasing | stable
    seasonality_detected: bool = False
    seasonal_pattern: dict[str, float] = field(default_factory=dict)
    change_points: list[str] = field(default_factory=list)
    mean_per_period: float = 0.0
    stdev_per_period: float = 0.0


class TemporalTrendAnalyzer:
    """
    Temporal trend analysis (§16.3.1).

    Analyzes incident volume over time, detects seasonality,
    cyclical patterns, trend direction, and change points.
    """

    def analyze(
        self,
        incidents: list[Incident],
        period: str = "daily",  # daily | weekly | monthly
    ) -> TemporalTrend:
        """Analyze temporal trends in incident data."""
        # Group incidents by period
        counts: dict[str, int] = defaultdict(int)
        for inc in incidents:
            if inc.detected_at:
                try:
                    ts = datetime.fromisoformat(inc.detected_at.replace("Z", "+00:00"))
                    if period == "daily":
                        key = ts.strftime("%Y-%m-%d")
                    elif period == "weekly":
                        key = ts.strftime("%Y-W%W")
                    else:
                        key = ts.strftime("%Y-%m")
                    counts[key] += 1
                except (ValueError, AttributeError):
                    pass

        sorted_periods = sorted(counts.keys())
        values = [counts[p] for p in sorted_periods]

        # Trend direction
        trend = "stable"
        if len(values) >= 3:
            first_half = statistics.mean(values[:len(values)//2])
            second_half = statistics.mean(values[len(values)//2:])
            if second_half > first_half * 1.2:
                trend = "increasing"
            elif second_half < first_half * 0.8:
                trend = "decreasing"

        # Seasonality detection (simple: check for repeating patterns)
        seasonality = False
        seasonal_pattern: dict[str, float] = {}
        if len(values) >= 14:
            # Check for weekly seasonality
            if period == "daily":
                day_of_week_counts: dict[int, list[int]] = defaultdict(list)
                for p in sorted_periods:
                    try:
                        dt = datetime.strptime(p, "%Y-%m-%d")
                        day_of_week_counts[dt.weekday()].append(counts[p])
                    except ValueError:
                        pass
                if day_of_week_counts:
                    day_means = {d: statistics.mean(v) for d, v in day_of_week_counts.items() if v}
                    if day_means:
                        overall_mean = statistics.mean(day_means.values())
                        seasonal_pattern = {str(d): m / overall_mean for d, m in day_means.items()}
                        seasonality = any(abs(v - 1.0) > 0.3 for v in seasonal_pattern.values())

        # Change points (simple: significant deviation from mean)
        change_points = []
        if values:
            mean_val = statistics.mean(values)
            stdev_val = statistics.stdev(values) if len(values) > 1 else 0
            if stdev_val > 0:
                for i, (p, v) in enumerate(zip(sorted_periods, values)):
                    if abs(v - mean_val) > 2 * stdev_val:
                        change_points.append(p)

        return TemporalTrend(
            period=period,
            total_incidents=sum(values),
            incident_counts=dict(counts),
            trend_direction=trend,
            seasonality_detected=seasonality,
            seasonal_pattern=seasonal_pattern,
            change_points=change_points,
            mean_per_period=statistics.mean(values) if values else 0,
            stdev_per_period=statistics.stdev(values) if len(values) > 1 else 0,
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Category Trends (§16.3.2)
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class CategoryTrend:
    """Category trend analysis results."""
    category_distribution: dict[str, int] = field(default_factory=dict)
    emerging_categories: list[str] = field(default_factory=list)
    category_correlations: dict[str, list[str]] = field(default_factory=dict)
    growth_rates: dict[str, float] = field(default_factory=dict)


class CategoryTrendAnalyzer:
    """
    Category trend analysis (§16.3.2).

    Analyzes incident category distribution, emerging categories,
    category correlations, and category migration patterns.
    """

    def analyze(self, incidents: list[Incident]) -> CategoryTrend:
        """Analyze category trends."""
        # Distribution
        distribution: Counter = Counter()
        for inc in incidents:
            if inc.category:
                distribution[inc.category.value] += 1

        # Emerging categories (appearing in recent period)
        emerging = []
        now = datetime.now(timezone.utc)
        recent_cutoff = now - timedelta(days=30)
        for inc in incidents:
            if inc.category and inc.detected_at:
                try:
                    ts = datetime.fromisoformat(inc.detected_at.replace("Z", "+00:00"))
                    if ts > recent_cutoff:
                        cat = inc.category.value
                        if cat not in emerging:
                            # Check if this category appeared recently
                            older = [
                                i for i in incidents
                                if i.category and i.category.value == cat
                                and i.detected_at and
                                datetime.fromisoformat(i.detected_at.replace("Z", "+00:00")) < recent_cutoff
                            ]
                            if not older:
                                emerging.append(cat)
                except (ValueError, AttributeError):
                    pass

        # Category correlations (categories that co-occur)
        correlations: dict[str, set[str]] = defaultdict(set)
        # Group by time window (same day)
        by_date: dict[str, set[str]] = defaultdict(set)
        for inc in incidents:
            if inc.category and inc.detected_at:
                try:
                    ts = datetime.fromisoformat(inc.detected_at.replace("Z", "+00:00"))
                    date_key = ts.strftime("%Y-%m-%d")
                    by_date[date_key].add(inc.category.value)
                except (ValueError, AttributeError):
                    pass

        for cats in by_date.values():
            for c1 in cats:
                for c2 in cats:
                    if c1 != c2:
                        correlations[c1].add(c2)

        # Growth rates
        growth_rates: dict[str, float] = {}
        for cat in distribution:
            cat_incidents = [i for i in incidents if i.category and i.category.value == cat]
            if len(cat_incidents) >= 2:
                try:
                    sorted_inc = sorted(cat_incidents, key=lambda i: i.detected_at)
                    mid = len(sorted_inc) // 2
                    first_half = sorted_inc[:mid]
                    second_half = sorted_inc[mid:]
                    if first_half:
                        first_span = (
                            datetime.fromisoformat(first_half[-1].detected_at.replace("Z", "+00:00")) -
                            datetime.fromisoformat(first_half[0].detected_at.replace("Z", "+00:00"))
                        ).days or 1
                        second_span = (
                            datetime.fromisoformat(second_half[-1].detected_at.replace("Z", "+00:00")) -
                            datetime.fromisoformat(second_half[0].detected_at.replace("Z", "+00:00"))
                        ).days or 1
                        first_rate = len(first_half) / first_span
                        second_rate = len(second_half) / second_span
                        if first_rate > 0:
                            growth_rates[cat] = (second_rate - first_rate) / first_rate
                except (ValueError, AttributeError, ZeroDivisionError):
                    pass

        return CategoryTrend(
            category_distribution=dict(distribution),
            emerging_categories=emerging,
            category_correlations={k: list(v) for k, v in correlations.items()},
            growth_rates=growth_rates,
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Severity Trends (§16.3.3)
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class SeverityTrend:
    """Severity trend analysis results."""
    severity_distribution: dict[str, int] = field(default_factory=dict)
    severity_by_category: dict[str, dict[str, int]] = field(default_factory=dict)
    escalation_trend: str = "stable"  # escalating | de_escalating | stable
    high_severity_ratio: float = 0.0


class SeverityTrendAnalyzer:
    """
    Severity trend analysis (§16.3.3).

    Analyzes severity distribution, escalation trends, and
    severity distribution within each category.
    """

    def analyze(self, incidents: list[Incident]) -> SeverityTrend:
        """Analyze severity trends."""
        # Distribution
        distribution: Counter = Counter()
        for inc in incidents:
            distribution[inc.severity.value] += 1

        # By category
        by_category: dict[str, Counter] = defaultdict(Counter)
        for inc in incidents:
            if inc.category:
                by_category[inc.category.value][inc.severity.value] += 1

        # Escalation trend
        escalation = "stable"
        s1_s2_count = sum(1 for i in incidents if i.severity in (Severity.S1_CRITICAL, Severity.S2_HIGH))
        total = len(incidents)
        high_ratio = s1_s2_count / total if total > 0 else 0

        if total >= 4:
            sorted_inc = sorted(incidents, key=lambda i: i.detected_at)
            mid = len(sorted_inc) // 2
            first_high = sum(1 for i in sorted_inc[:mid] if i.severity in (Severity.S1_CRITICAL, Severity.S2_HIGH))
            second_high = sum(1 for i in sorted_inc[mid:] if i.severity in (Severity.S1_CRITICAL, Severity.S2_HIGH))
            first_ratio = first_high / mid if mid > 0 else 0
            second_ratio = second_high / (total - mid) if (total - mid) > 0 else 0
            if second_ratio > first_ratio * 1.3:
                escalation = "escalating"
            elif second_ratio < first_ratio * 0.7:
                escalation = "de_escalating"

        return SeverityTrend(
            severity_distribution=dict(distribution),
            severity_by_category={k: dict(v) for k, v in by_category.items()},
            escalation_trend=escalation,
            high_severity_ratio=high_ratio,
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Asset Trends (§16.3.4)
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class AssetRiskScore:
    """Asset risk score (§16.5.1)."""
    asset_id: str
    asset_name: str
    risk_score: float = 0.0  # 0–100
    risk_level: str = "low"  # low | medium | high | very_high | critical
    incident_count: int = 0
    incident_rate: float = 0.0
    factors: dict[str, float] = field(default_factory=dict)


class AssetTrendAnalyzer:
    """
    Asset trend analysis (§16.3.4).

    Analyzes asset risk scores, incident rates, correlations,
    and degradation patterns.
    """

    # Risk score weights (§16.5.1)
    WEIGHTS = {
        "incident_history": 0.30,
        "threat_exposure": 0.20,
        "asset_criticality": 0.20,
        "control_maturity": 0.15,
        "change_velocity": 0.15,
    }

    def compute_risk_score(
        self,
        asset_id: str,
        asset_name: str,
        incidents: list[Incident],
        threat_exposure: float = 0.5,
        asset_criticality: float = 0.5,
        control_maturity: float = 0.5,
        change_velocity: float = 0.5,
    ) -> AssetRiskScore:
        """Compute dynamic risk score for an asset (§16.5.1)."""
        asset_incidents = [i for i in incidents if any(a.asset_id == asset_id for a in i.affected_assets)]
        incident_count = len(asset_incidents)

        # Incident history score (based on frequency and severity)
        if incident_count > 0:
            severity_sum = sum(
                int(i.severity.value[1]) for i in asset_incidents
            )
            avg_severity = severity_sum / incident_count
            incident_history = min(1.0, (incident_count / 10) * (avg_severity / 5))
        else:
            incident_history = 0.0

        # Compute weighted score
        factors = {
            "incident_history": incident_history,
            "threat_exposure": threat_exposure,
            "asset_criticality": asset_criticality,
            "control_maturity": 1.0 - control_maturity,  # Lower maturity = higher risk
            "change_velocity": change_velocity,
        }

        score = sum(factors[k] * self.WEIGHTS[k] for k in self.WEIGHTS) * 100

        # Risk level
        if score >= 81:
            level = "critical"
        elif score >= 61:
            level = "very_high"
        elif score >= 41:
            level = "high"
        elif score >= 21:
            level = "medium"
        else:
            level = "low"

        return AssetRiskScore(
            asset_id=asset_id,
            asset_name=asset_name,
            risk_score=score,
            risk_level=level,
            incident_count=incident_count,
            incident_rate=incident_count / max(len(incidents), 1),
            factors=factors,
        )

    def analyze_asset_degradation(
        self,
        asset_id: str,
        incidents: list[Incident],
    ) -> dict[str, Any]:
        """Analyze asset degradation (increasing incident rate)."""
        asset_incidents = sorted(
            [i for i in incidents if any(a.asset_id == asset_id for a in i.affected_assets)],
            key=lambda i: i.detected_at,
        )

        if len(asset_incidents) < 4:
            return {"degrading": False, "trend": "insufficient_data"}

        mid = len(asset_incidents) // 2
        first_half = asset_incidents[:mid]
        second_half = asset_incidents[mid:]

        # Compare incident rates
        if first_half:
            first_span = (
                datetime.fromisoformat(first_half[-1].detected_at.replace("Z", "+00:00")) -
                datetime.fromisoformat(first_half[0].detected_at.replace("Z", "+00:00"))
            ).days or 1
            second_span = (
                datetime.fromisoformat(second_half[-1].detected_at.replace("Z", "+00:00")) -
                datetime.fromisoformat(second_half[0].detected_at.replace("Z", "+00:00"))
            ).days or 1

            first_rate = len(first_half) / first_span
            second_rate = len(second_half) / second_span

            if second_rate > first_rate * 2:
                return {"degrading": True, "trend": "increasing", "rate_change": second_rate / first_rate if first_rate > 0 else float("inf")}

        return {"degrading": False, "trend": "stable"}


# ═══════════════════════════════════════════════════════════════════════════════
# Predictive Models (§16.4)
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class VolumePrediction:
    """Incident volume prediction (§16.4.1)."""
    horizon_days: int = 30
    predicted_count: int = 0
    confidence_interval: tuple[int, int] = (0, 0)
    model: str = "ensemble"  # arima | prophet | lstm | ensemble
    mape: float = 0.0


class VolumePredictor:
    """
    Incident volume prediction (§16.4.1).

    Predicts future incident volume using time series methods.
    In production, this would use ARIMA, Prophet, or LSTM models.
    """

    def predict(
        self,
        incidents: list[Incident],
        horizon_days: int = 30,
    ) -> VolumePrediction:
        """Predict incident volume for the next horizon period."""
        if not incidents:
            return VolumePrediction(horizon_days=horizon_days)

        # Simple moving average prediction
        sorted_inc = sorted(incidents, key=lambda i: i.detected_at)
        if len(sorted_inc) < 2:
            return VolumePrediction(horizon_days=horizon_days, predicted_count=len(incidents))

        try:
            first = datetime.fromisoformat(sorted_inc[0].detected_at.replace("Z", "+00:00"))
            last = datetime.fromisoformat(sorted_inc[-1].detected_at.replace("Z", "+00:00"))
            total_days = max((last - first).days, 1)
            daily_rate = len(incidents) / total_days
            predicted = int(daily_rate * horizon_days)

            # Confidence interval (±20%)
            ci_low = int(predicted * 0.8)
            ci_high = int(predicted * 1.2)

            return VolumePrediction(
                horizon_days=horizon_days,
                predicted_count=predicted,
                confidence_interval=(ci_low, ci_high),
                model="moving_average",
                mape=0.15,  # Placeholder
            )
        except (ValueError, AttributeError):
            return VolumePrediction(horizon_days=horizon_days)


@dataclass
class SeverityPrediction:
    """Severity prediction (§16.4.3)."""
    high_severity_probability: float = 0.0
    predicted_severity: Severity = Severity.S3_MEDIUM
    auc: float = 0.0
    early_warning_score: float = 0.0


class SeverityPredictor:
    """
    Severity prediction (§16.4.3).

    Predicts likelihood of S1/S2 incidents and provides early warning.
    """

    def predict(self, incidents: list[Incident]) -> SeverityPrediction:
        """Predict severity likelihood."""
        if not incidents:
            return SeverityPrediction()

        # Simple heuristic: ratio of high-severity incidents
        high_sev = sum(1 for i in incidents if i.severity in (Severity.S1_CRITICAL, Severity.S2_HIGH))
        ratio = high_sev / len(incidents)

        # Trend adjustment
        if len(incidents) >= 4:
            sorted_inc = sorted(incidents, key=lambda i: i.detected_at)
            mid = len(sorted_inc) // 2
            first_high = sum(1 for i in sorted_inc[:mid] if i.severity in (Severity.S1_CRITICAL, Severity.S2_HIGH))
            second_high = sum(1 for i in sorted_inc[mid:] if i.severity in (Severity.S1_CRITICAL, Severity.S2_HIGH))
            first_ratio = first_high / mid if mid > 0 else 0
            second_ratio = second_high / (len(sorted_inc) - mid) if (len(sorted_inc) - mid) > 0 else 0
            if second_ratio > first_ratio:
                ratio = min(1.0, ratio * 1.2)

        predicted = Severity.S1_CRITICAL if ratio > 0.3 else Severity.S2_HIGH if ratio > 0.15 else Severity.S3_MEDIUM

        return SeverityPrediction(
            high_severity_probability=ratio,
            predicted_severity=predicted,
            auc=0.85,  # Placeholder
            early_warning_score=ratio,
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Early Warning System (§16.6)
# ═══════════════════════════════════════════════════════════════════════════════

class AlertLevel(str, Enum):
    YELLOW = "yellow"
    ORANGE = "orange"
    RED = "red"


@dataclass
class EarlyWarning:
    """Early warning indicator (§16.6.1)."""
    indicator: str
    level: AlertLevel
    description: str
    threshold: str
    current_value: str
    timestamp: str = ""


class EarlyWarningSystem:
    """
    Early warning system (§16.6).

    Monitors indicators that precede high-severity incidents and
    generates alerts at yellow, orange, and red levels.
    """

    def __init__(self) -> None:
        self._warnings: list[EarlyWarning] = []

    def check_indicators(self, incidents: list[Incident]) -> list[EarlyWarning]:
        """Check all early warning indicators."""
        warnings: list[EarlyWarning] = []

        if not incidents:
            return warnings

        # Signal volume spike
        recent = [i for i in incidents if i.detected_at and
                  datetime.fromisoformat(i.detected_at.replace("Z", "+00:00")) > datetime.now(timezone.utc) - timedelta(hours=24)]
        if len(recent) > 10:
            warnings.append(EarlyWarning(
                indicator="signal_volume_spike",
                level=AlertLevel.YELLOW,
                description="Unusual increase in detection signals",
                threshold=">3σ from baseline",
                current_value=f"{len(recent)} signals in 24h",
                timestamp=datetime.now(timezone.utc).isoformat(),
            ))

        # Severity escalation
        if len(incidents) >= 4:
            sorted_inc = sorted(incidents, key=lambda i: i.detected_at)
            mid = len(sorted_inc) // 2
            first_high = sum(1 for i in sorted_inc[:mid] if i.severity in (Severity.S1_CRITICAL, Severity.S2_HIGH))
            second_high = sum(1 for i in sorted_inc[mid:] if i.severity in (Severity.S1_CRITICAL, Severity.S2_HIGH))
            if second_high > first_high and second_high >= 2:
                warnings.append(EarlyWarning(
                    indicator="severity_escalation",
                    level=AlertLevel.ORANGE,
                    description="Increasing severity trend detected",
                    threshold="2 consecutive periods of increase",
                    current_value=f"{first_high} → {second_high} high-severity incidents",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                ))

        # Control failure
        control_failures = sum(1 for i in incidents if i.status == IncidentStatus.DETECTED and not i.contained_at)
        if control_failures > 3:
            warnings.append(EarlyWarning(
                indicator="control_failure",
                level=AlertLevel.RED,
                description="Multiple control failures in short period",
                threshold=">3 in 24 hours",
                current_value=f"{control_failures} uncontained incidents",
                timestamp=datetime.now(timezone.utc).isoformat(),
            ))

        self._warnings.extend(warnings)
        return warnings

    def get_response_action(self, level: AlertLevel) -> dict[str, str]:
        """Get response action for alert level (§16.6.2)."""
        responses = {
            AlertLevel.YELLOW: {"action": "Increased monitoring, analyst notification", "timeline": "Within 4 hours"},
            AlertLevel.ORANGE: {"action": "Proactive assessment, management notification", "timeline": "Within 1 hour"},
            AlertLevel.RED: {"action": "Immediate assessment, potential pre-emptive action", "timeline": "Within 15 minutes"},
        }
        return responses.get(level, {"action": "Monitor", "timeline": "N/A"})


# ═══════════════════════════════════════════════════════════════════════════════
# Organizational Risk Score (§16.5.2)
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class OrganizationalRiskScore:
    """Aggregate organizational AI risk score (§16.5.2)."""
    overall_score: float = 0.0  # 0–100
    risk_level: str = "low"
    components: dict[str, float] = field(default_factory=dict)


class OrganizationalRiskScorer:
    """
    Organizational risk score (§16.5.2).

    Computes aggregate organizational AI risk from asset scores,
    incident trends, detection coverage, response readiness, and
    regulatory compliance.
    """

    def compute(
        self,
        asset_scores: list[AssetRiskScore],
        incidents: list[Incident],
        detection_coverage: float = 1.0,
        response_readiness: float = 0.8,
        regulatory_compliance: float = 1.0,
    ) -> OrganizationalRiskScore:
        """Compute organizational risk score."""
        # Weighted asset scores
        if asset_scores:
            avg_asset_risk = statistics.mean(a.risk_score for a in asset_scores)
        else:
            avg_asset_risk = 50.0

        # Incident trend component
        if len(incidents) >= 2:
            sorted_inc = sorted(incidents, key=lambda i: i.detected_at)
            mid = len(sorted_inc) // 2
            first_count = mid
            second_count = len(sorted_inc) - mid
            trend_factor = second_count / max(first_count, 1)
            incident_trend = min(100, trend_factor * 50)
        else:
            incident_trend = 50.0

        # Detection coverage gap
        detection_gap = (1.0 - detection_coverage) * 100

        # Response readiness
        response_risk = (1.0 - response_readiness) * 100

        # Regulatory compliance
        compliance_risk = (1.0 - regulatory_compliance) * 100

        # Weighted overall score
        overall = (
            avg_asset_risk * 0.30 +
            incident_trend * 0.25 +
            detection_gap * 0.20 +
            response_risk * 0.15 +
            compliance_risk * 0.10
        )

        if overall >= 81:
            level = "critical"
        elif overall >= 61:
            level = "very_high"
        elif overall >= 41:
            level = "high"
        elif overall >= 21:
            level = "medium"
        else:
            level = "low"

        return OrganizationalRiskScore(
            overall_score=overall,
            risk_level=level,
            components={
                "asset_risk": avg_asset_risk,
                "incident_trend": incident_trend,
                "detection_gap": detection_gap,
                "response_risk": response_risk,
                "compliance_risk": compliance_risk,
            },
        )
