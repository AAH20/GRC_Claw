"""
GRC_Claw Risk Analytics
========================
Advanced analytics for risk data:
  - Descriptive statistics
  - Trend analysis
  - Correlation analysis
  - Predictive indicators
  - Heatmap generation
  - Risk concentration analysis

References GRC-RISK-001 §8.4 (Trend Analysis) and
grc-claw-unified-metrics-layer.md §7 (Metrics Architecture).

Usage:
    from risk_analytics import RiskAnalytics

    analytics = RiskAnalytics(register)
    stats = analytics.descriptive_stats()
    heatmap = analytics.risk_heatmap()
"""

from __future__ import annotations

import json
import math
import statistics
from collections import defaultdict
from datetime import datetime, date, timedelta
from typing import Optional


# ─── Risk Analytics Engine ───────────────────────────────────────────────────

class RiskAnalytics:
    """
    Advanced analytics engine for risk register data.
    Provides statistical analysis, trend detection, and visualizations data.
    """

    def __init__(self, register):
        self.register = register

    # ── Descriptive Statistics ─────────────────────────────────────────

    def descriptive_stats(self) -> dict:
        """Calculate descriptive statistics for all risk scores."""
        scores = self._get_all_scores()
        if not scores:
            return {"count": 0}

        values = [s["mdrs"] for s in scores]
        return {
            "count": len(values),
            "mean": round(statistics.mean(values), 2),
            "median": round(statistics.median(values), 2),
            "stdev": round(statistics.stdev(values), 2) if len(values) > 1 else 0.0,
            "min": min(values),
            "max": max(values),
            "range": round(max(values) - min(values), 2),
            "percentiles": {
                "p25": round(self._percentile(values, 25), 2),
                "p50": round(self._percentile(values, 50), 2),
                "p75": round(self._percentile(values, 75), 2),
                "p90": round(self._percentile(values, 90), 2),
                "p95": round(self._percentile(values, 95), 2),
            },
        }

    def domain_statistics(self) -> dict:
        """Statistics broken down by risk domain."""
        domain_scores: dict[str, list[float]] = defaultdict(list)
        for risk in self.register.all():
            score = risk.residual_score or risk.inherent_score
            if score:
                domain_scores[risk.risk_domain].append(score.mdrs)

        result = {}
        for domain, values in domain_scores.items():
            result[domain] = {
                "count": len(values),
                "mean": round(statistics.mean(values), 2),
                "median": round(statistics.median(values), 2),
                "stdev": round(statistics.stdev(values), 2) if len(values) > 1 else 0.0,
                "min": min(values),
                "max": max(values),
            }
        return result

    def category_statistics(self) -> dict:
        """Statistics broken down by risk category."""
        cat_scores: dict[str, list[float]] = defaultdict(list)
        for risk in self.register.all():
            score = risk.residual_score or risk.inherent_score
            if score:
                cat_scores[risk.risk_category].append(score.mdrs)

        result = {}
        for cat, values in sorted(cat_scores.items()):
            result[cat] = {
                "count": len(values),
                "mean": round(statistics.mean(values), 2),
                "max": max(values),
            }
        return result

    # ── Trend Analysis ─────────────────────────────────────────────────

    def trend_analysis(self, metric: str = "mdrs", days: int = 90) -> dict:
        """
        Analyze risk score trends over time.
        Uses audit trail timestamps to reconstruct historical scores.
        """
        # Collect all score changes from audit trails
        events = []
        for risk in self.register.all():
            for event in risk.audit_trail:
                if "mdrs" in event.details.lower() or "score" in event.action.lower():
                    events.append({
                        "timestamp": event.timestamp,
                        "risk_id": risk.risk_id,
                        "details": event.details,
                    })

        if not events:
            return {"status": "insufficient_data", "points": []}

        # Sort by timestamp
        events.sort(key=lambda e: e["timestamp"])

        # Calculate daily averages
        daily_scores: dict[str, list[float]] = defaultdict(list)
        for risk in self.register.all():
            score = risk.residual_score or risk.inherent_score
            if score:
                daily_scores[risk.identified_date].append(score.mdrs)

        points = [
            {"date": d, "mean_mdrs": round(statistics.mean(v), 2), "count": len(v)}
            for d, v in sorted(daily_scores.items())
        ]

        if len(points) < 2:
            return {"status": "insufficient_data", "points": points}

        # Calculate trend
        first = points[0]["mean_mdrs"]
        last = points[-1]["mean_mdrs"]
        change = round(last - first, 2)
        change_pct = round((last - first) / first * 100, 2) if first != 0 else 0.0

        if change_pct > 5:
            direction = "increasing"
        elif change_pct < -5:
            direction = "decreasing"
        else:
            direction = "stable"

        return {
            "status": "ok",
            "points": points,
            "trend_direction": direction,
            "change": change,
            "change_pct": change_pct,
            "period_days": days,
        }

    # ── Correlation Analysis ───────────────────────────────────────────

    def correlation_analysis(self) -> dict:
        """
        Analyze correlations between risk dimensions.
        Helps identify which dimensions drive overall risk.
        """
        dimensions = ["likelihood", "impact", "detectability", "velocity", "persistence"]
        data: dict[str, list[int]] = {d: [] for d in dimensions}
        mdrs_values = []

        for risk in self.register.all():
            score = risk.residual_score or risk.inherent_score
            if score:
                for dim in dimensions:
                    data[dim].append(getattr(score, dim))
                mdrs_values.append(score.mdrs)

        if len(mdrs_values) < 3:
            return {"status": "insufficient_data"}

        correlations = {}
        for dim in dimensions:
            if len(data[dim]) >= 3:
                corr = self._pearson_correlation(data[dim], mdrs_values)
                correlations[dim] = round(corr, 3)

        # Sort by absolute correlation strength
        sorted_corrs = sorted(correlations.items(), key=lambda x: abs(x[1]), reverse=True)

        return {
            "status": "ok",
            "correlations": correlations,
            "strongest_predictors": [d for d, c in sorted_corrs[:3]],
            "interpretation": {
                "positive": "Higher dimension score increases MDRS",
                "negative": "Higher dimension score decreases MDRS",
            },
        }

    # ── Risk Heatmap ───────────────────────────────────────────────────

    def risk_heatmap(self) -> dict:
        """
        Generate risk heatmap data: domain × category matrix.
        Values represent count of risks at each intersection.
        """
        matrix: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        for risk in self.register.all():
            matrix[risk.risk_domain][risk.risk_category] += 1

        # Convert to list format for visualization
        domains = sorted(matrix.keys())
        categories = sorted(set(c for d in matrix.values() for c in d))

        heatmap = []
        for domain in domains:
            row = {"domain": domain, "categories": {}}
            for cat in categories:
                row["categories"][cat] = matrix[domain].get(cat, 0)
            row["total"] = sum(row["categories"].values())
            heatmap.append(row)

        return {
            "domains": domains,
            "categories": categories,
            "matrix": heatmap,
            "max_value": max(
                (matrix[d][c] for d in matrix for c in matrix[d]),
                default=0,
            ),
        }

    # ── Risk Concentration ─────────────────────────────────────────────

    def concentration_analysis(self) -> dict:
        """
        Analyze risk concentration using Herfindahl-Hirschman Index (HHI).
        High concentration = few categories dominate the risk landscape.
        """
        cat_counts: dict[str, int] = defaultdict(int)
        total = 0
        for risk in self.register.all():
            cat_counts[risk.risk_category] += 1
            total += 1

        if total == 0:
            return {"status": "no_data"}

        # Calculate HHI
        hhi = sum((count / total) ** 2 for count in cat_counts.values())
        hhi_pct = round(hhi * 10000, 2)  # Standard HHI scale

        # Concentration level
        if hhi_pct > 2500:
            level = "highly_concentrated"
        elif hhi_pct > 1500:
            level = "moderately_concentrated"
        else:
            level = "diversified"

        # Top categories by count
        sorted_cats = sorted(cat_counts.items(), key=lambda x: x[1], reverse=True)
        top_5 = [{"category": c, "count": n, "pct": round(n / total * 100, 1)} for c, n in sorted_cats[:5]]

        return {
            "hhi": hhi_pct,
            "concentration_level": level,
            "total_risks": total,
            "unique_categories": len(cat_counts),
            "top_5_categories": top_5,
            "interpretation": {
                "highly_concentrated": "Risk is concentrated in few categories — targeted treatment may be effective",
                "moderately_concentrated": "Moderate concentration — balanced treatment approach needed",
                "diversified": "Risk is spread across many categories — systemic controls may be more effective",
            }[level],
        }

    # ── Predictive Indicators ──────────────────────────────────────────

    def predictive_indicators(self) -> dict:
        """
        Identify early warning indicators that may predict risk escalation.
        """
        indicators = []

        # Indicator 1: Risks with high velocity + low detectability
        high_vel_low_det = []
        for risk in self.register.all():
            score = risk.residual_score or risk.inherent_score
            if score and score.velocity >= 4 and score.detectability >= 4:
                high_vel_low_det.append({
                    "risk_id": risk.risk_id,
                    "category": risk.risk_category,
                    "velocity": score.velocity,
                    "detectability": score.detectability,
                })
        if high_vel_low_det:
            indicators.append({
                "name": "High Velocity + Low Detectability",
                "description": "Risks that propagate fast and are hard to detect",
                "count": len(high_vel_low_det),
                "risks": high_vel_low_det,
                "recommendation": "Prioritize detection capabilities for these risks",
            })

        # Indicator 2: Risks with increasing residual scores
        escalating = []
        for risk in self.register.all():
            if risk.inherent_score and risk.residual_score:
                if risk.residual_score.mdrs > risk.inherent_score.mdrs:
                    escalating.append({
                        "risk_id": risk.risk_id,
                        "inherent": risk.inherent_score.mdrs,
                        "residual": risk.residual_score.mdrs,
                    })
        if escalating:
            indicators.append({
                "name": "Escalating Residual Risk",
                "description": "Risks where residual score exceeds inherent score",
                "count": len(escalating),
                "risks": escalating,
                "recommendation": "Review control effectiveness immediately",
            })

        # Indicator 3: Overdue reviews on high-tier risks
        overdue_high = []
        for risk in self.register.overdue_reviews():
            score = risk.residual_score or risk.inherent_score
            if score and score.tier.value in ("High", "Critical"):
                overdue_high.append({
                    "risk_id": risk.risk_id,
                    "tier": score.tier.value,
                    "review_date": risk.review_date,
                })
        if overdue_high:
            indicators.append({
                "name": "Overdue High-Tier Reviews",
                "description": "High/Critical risks past their review date",
                "count": len(overdue_high),
                "risks": overdue_high,
                "recommendation": "Schedule immediate reviews",
            })

        return {
            "indicator_count": len(indicators),
            "indicators": indicators,
            "overall_risk": "elevated" if len(indicators) >= 2 else "normal",
        }

    # ── Monte Carlo Simulation ─────────────────────────────────────────

    def monte_carlo_simulation(self, iterations: int = 1000) -> dict:
        """
        Simple Monte Carlo simulation to estimate probability of risk breach.
        Simulates random combinations of dimension scores.
        """
        import random

        breach_counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0, "Minimal": 0}
        total_mdrs = []

        for _ in range(iterations):
            # Random dimension scores (weighted toward observed distribution)
            l = random.randint(1, 5)
            i = random.randint(1, 5)
            d = random.randint(1, 5)
            v = random.randint(1, 5)
            p = random.randint(1, 5)

            mdrs = round(
                l * 0.25 + i * 0.30 + d * 0.15 + v * 0.15 + p * 0.15, 2
            )
            total_mdrs.append(mdrs)

            if mdrs >= 4.50:
                breach_counts["Critical"] += 1
            elif mdrs >= 3.50:
                breach_counts["High"] += 1
            elif mdrs >= 2.50:
                breach_counts["Medium"] += 1
            elif mdrs >= 1.50:
                breach_counts["Low"] += 1
            else:
                breach_counts["Minimal"] += 1

        return {
            "iterations": iterations,
            "mean_mdrs": round(statistics.mean(total_mdrs), 2),
            "stdev_mdrs": round(statistics.stdev(total_mdrs), 2) if len(total_mdrs) > 1 else 0.0,
            "tier_probabilities": {
                tier: round(count / iterations * 100, 1)
                for tier, count in breach_counts.items()
            },
            "interpretation": {
                "critical_probability": f"{round(breach_counts['Critical'] / iterations * 100, 1)}%",
                "high_or_critical_probability": f"{round((breach_counts['Critical'] + breach_counts['High']) / iterations * 100, 1)}%",
            },
        }

    # ── Helper Methods ─────────────────────────────────────────────────

    def _get_all_scores(self) -> list[dict]:
        """Get all risk scores as flat list."""
        scores = []
        for risk in self.register.all():
            s = risk.residual_score or risk.inherent_score
            if s:
                scores.append({
                    "risk_id": risk.risk_id,
                    "domain": risk.risk_domain,
                    "category": risk.risk_category,
                    "mdrs": s.mdrs,
                    "tier": s.tier.value,
                    "likelihood": s.likelihood,
                    "impact": s.impact,
                    "detectability": s.detectability,
                    "velocity": s.velocity,
                    "persistence": s.persistence,
                })
        return scores

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

    @staticmethod
    def _pearson_correlation(x: list[float], y: list[float]) -> float:
        """Calculate Pearson correlation coefficient."""
        n = len(x)
        if n < 2:
            return 0.0
        mean_x = statistics.mean(x)
        mean_y = statistics.mean(y)
        numerator = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))
        denom_x = math.sqrt(sum((xi - mean_x) ** 2 for xi in x))
        denom_y = math.sqrt(sum((yi - mean_y) ** 2 for yi in y))
        if denom_x == 0 or denom_y == 0:
            return 0.0
        return numerator / (denom_x * denom_y)


# ─── Demo / Self-Test ────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from risk_register import RiskRegister

    register = RiskRegister()

    # Create sample risks across domains
    risks_data = [
        ("SEC-02", "SEC", 3, 5, 4, 5, 3),
        ("DAT-03", "DAT", 4, 4, 3, 3, 4),
        ("TPR-03", "TPR", 3, 3, 3, 2, 3),
        ("MOD-02", "MOD", 3, 3, 3, 3, 2),
        ("SEC-01", "SEC", 4, 4, 3, 4, 3),
        ("GOV-01", "GOV", 2, 3, 2, 2, 3),
        ("OPS-01", "OPS", 3, 3, 4, 3, 2),
        ("CMP-03", "CMP", 2, 4, 3, 2, 4),
    ]

    for cat, domain, l, i, d, v, p in risks_data:
        register.create_risk(
            title=f"Risk in {cat}", domain=domain, category=cat,
            likelihood=l, impact=i, detectability=d, velocity=v, persistence=p,
        )

    analytics = RiskAnalytics(register)

    print("=== Descriptive Statistics ===")
    print(json.dumps(analytics.descriptive_stats(), indent=2))

    print("\n=== Domain Statistics ===")
    print(json.dumps(analytics.domain_statistics(), indent=2))

    print("\n=== Correlation Analysis ===")
    print(json.dumps(analytics.correlation_analysis(), indent=2))

    print("\n=== Risk Heatmap ===")
    print(json.dumps(analytics.risk_heatmap(), indent=2))

    print("\n=== Concentration Analysis ===")
    print(json.dumps(analytics.concentration_analysis(), indent=2))

    print("\n=== Predictive Indicators ===")
    print(json.dumps(analytics.predictive_indicators(), indent=2))

    print("\n=== Monte Carlo Simulation ===")
    print(json.dumps(analytics.monte_carlo_simulation(1000), indent=2))
