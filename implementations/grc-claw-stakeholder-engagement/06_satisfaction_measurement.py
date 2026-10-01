"""
GRC_Claw Satisfaction Measurement
==================================
Implements the stakeholder satisfaction measurement system from the GRC_Claw
Stakeholder Engagement Specification v2.0 (Section 13).

Covers:
- Multi-layer satisfaction model (Relational, Transactional, Outcome)
- 6 satisfaction dimensions with weights (Spec §13.1.2)
- Survey instruments (Semi-annual, Post-interaction, Pulse)
- Composite satisfaction scoring (Spec §13.3.1)
- Satisfaction tiers (Delighted / Satisfied / Neutral / Dissatisfied / Critical)
- NPS integration (Promoters / Passives / Detractors)
- Benchmarking (Internal + External)
- Satisfaction alerts (5 types per Spec §13.6.2)
- Integration with engagement effectiveness scoring (Spec §13.7)
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Optional
from collections import defaultdict


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class SatisfactionLayer(str, Enum):
    RELATIONAL = "relational"      # Long-term relationship health
    TRANSACTIONAL = "transactional"  # Specific interaction quality
    OUTCOME = "outcome"            # Results and impact


class SatisfactionDimension(str, Enum):
    RESPONSIVENESS = "responsiveness"
    RELEVANCE = "relevance"
    QUALITY = "quality"
    ACCESSIBILITY = "accessibility"
    TRANSPARENCY = "transparency"
    IMPACT = "impact"


class SatisfactionTier(str, Enum):
    DELIGHTED = "delighted"          # 90-100
    SATISFIED = "satisfied"          # 75-89
    NEUTRAL = "neutral"              # 60-74
    DISSATISFIED = "dissatisfied"    # 40-59
    CRITICAL = "critical"            # 0-39


class NPSCategory(str, Enum):
    PROMOTER = "promoter"    # 9-10
    PASSIVE = "passive"      # 7-8
    DETRACTOR = "detractor"  # 0-6


class AlertType(str, Enum):
    SATISFACTION_DROP = "satisfaction_drop"
    GROUP_SATISFACTION_DECLINE = "group_satisfaction_decline"
    DETRACTOR_IDENTIFIED = "detractor_identified"
    CRITICAL_SATISFACTION = "critical_satisfaction"
    IMPROVEMENT_OPPORTUNITY = "improvement_opportunity"


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

@dataclass
class SatisfactionResponse:
    """A single satisfaction survey response."""

    response_id: str
    stakeholder_id: str
    survey_type: str  # semi_annual, post_interaction, pulse
    timestamp: str
    layer: SatisfactionLayer
    # Dimension scores (1-5 Likert)
    responsiveness: float = 0.0
    relevance: float = 0.0
    quality: float = 0.0
    accessibility: float = 0.0
    transparency: float = 0.0
    impact: float = 0.0
    # NPS (0-10)
    nps_score: Optional[int] = None
    # Open feedback
    open_feedback: str = ""
    # Priority ranking (rank order of improvement areas)
    priority_ranking: list[str] = field(default_factory=list)
    # Relationship health (1-5)
    relationship_health: float = 0.0
    # Anonymity
    anonymous: bool = True

    def to_dict(self) -> dict:
        d = asdict(self)
        d["layer"] = self.layer.value
        return d


@dataclass
class SatisfactionScore:
    """Composite satisfaction score for a stakeholder."""

    stakeholder_id: str
    score: float  # 0-100
    tier: SatisfactionTier
    dimension_scores: dict[str, float] = field(default_factory=dict)
    nps_score: Optional[int] = None
    nps_category: Optional[NPSCategory] = None
    layer: SatisfactionLayer = SatisfactionLayer.RELATIONAL
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict:
        d = asdict(self)
        d["tier"] = self.tier.value
        d["layer"] = self.layer.value
        if self.nps_category:
            d["nps_category"] = self.nps_category.value
        return d


@dataclass
class SatisfactionAlert:
    """Satisfaction alert (Spec §13.6.2)."""

    alert_id: str
    alert_type: AlertType
    stakeholder_id: str
    message: str
    severity: str  # low / medium / high / critical
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    acknowledged: bool = False

    def to_dict(self) -> dict:
        d = asdict(self)
        d["alert_type"] = self.alert_type.value
        return d


# ---------------------------------------------------------------------------
# Satisfaction Measurement Engine
# ---------------------------------------------------------------------------

class SatisfactionMeasurementEngine:
    """
    Multi-layer satisfaction measurement engine (Spec §13.1).

    Layers:
    - Relational: Long-term relationship health (semi-annual survey, NPS, sentiment)
    - Transactional: Specific interaction quality (post-interaction surveys)
    - Outcome: Results and impact (quarterly business reviews)
    """

    # Dimension weights (Spec §13.1.2)
    DIMENSION_WEIGHTS = {
        SatisfactionDimension.RESPONSIVENESS: 0.20,
        SatisfactionDimension.RELEVANCE: 0.20,
        SatisfactionDimension.QUALITY: 0.15,
        SatisfactionDimension.ACCESSIBILITY: 0.15,
        SatisfactionDimension.TRANSPARENCY: 0.15,
        SatisfactionDimension.IMPACT: 0.15,
    }

    # Satisfaction tiers (Spec §13.3.2)
    TIER_THRESHOLDS = {
        SatisfactionTier.DELIGHTED: (90, 100),
        SatisfactionTier.SATISFIED: (75, 89),
        SatisfactionTier.NEUTRAL: (60, 74),
        SatisfactionTier.DISSATISFIED: (40, 59),
        SatisfactionTier.CRITICAL: (0, 39),
    }

    def __init__(self):
        self._responses: dict[str, SatisfactionResponse] = {}
        self._scores: dict[str, SatisfactionScore] = {}
        self._alerts: dict[str, SatisfactionAlert] = {}
        self._next_id = 1

    def add_response(self, response: SatisfactionResponse) -> SatisfactionResponse:
        """Add a satisfaction survey response."""
        if not response.response_id:
            response.response_id = f"RES-{self._next_id:04d}"
            self._next_id += 1
        self._responses[response.response_id] = response
        return response

    def calculate_composite_score(self, stakeholder_id: str,
                                  layer: SatisfactionLayer = SatisfactionLayer.RELATIONAL,
                                  as_of: Optional[str] = None) -> SatisfactionScore:
        """
        Calculate composite satisfaction score (Spec §13.3.1).

        Satisfaction Score = Σ (Dimension Score × Dimension Weight)
        Normalized to: 0-100 scale
        """
        # Filter responses by stakeholder and layer
        relevant = [r for r in self._responses.values()
                    if r.stakeholder_id == stakeholder_id and r.layer == layer]

        if not relevant:
            return SatisfactionScore(
                stakeholder_id=stakeholder_id,
                score=0.0,
                tier=SatisfactionTier.CRITICAL,
                layer=layer,
            )

        # Average dimension scores across responses
        dim_scores = {}
        for dim in SatisfactionDimension:
            values = []
            for r in relevant:
                val = getattr(r, dim.value, 0.0)
                if val > 0:
                    values.append(val)
            dim_scores[dim.value] = round(sum(values) / len(values), 2) if values else 0.0

        # Calculate weighted composite (1-5 scale → 0-100)
        weighted_sum = 0.0
        for dim, weight in self.DIMENSION_WEIGHTS.items():
            score = dim_scores.get(dim.value, 0.0)
            # Normalize 1-5 to 0-100: (score - 1) / 4 * 100
            normalized = (score - 1) / 4 * 100 if score > 0 else 0
            weighted_sum += normalized * weight

        composite = round(weighted_sum, 1)
        tier = self._classify_tier(composite)

        # NPS
        nps_values = [r.nps_score for r in relevant if r.nps_score is not None]
        avg_nps = round(sum(nps_values) / len(nps_values)) if nps_values else None
        nps_cat = self._classify_nps(avg_nps) if avg_nps is not None else None

        score = SatisfactionScore(
            stakeholder_id=stakeholder_id,
            score=composite,
            tier=tier,
            dimension_scores=dim_scores,
            nps_score=avg_nps,
            nps_category=nps_cat,
            layer=layer,
        )
        self._scores[stakeholder_id] = score
        return score

    def _classify_tier(self, score: float) -> SatisfactionTier:
        """Classify satisfaction tier (Spec §13.3.2)."""
        if score >= 90:
            return SatisfactionTier.DELIGHTED
        elif score >= 75:
            return SatisfactionTier.SATISFIED
        elif score >= 60:
            return SatisfactionTier.NEUTRAL
        elif score >= 40:
            return SatisfactionTier.DISSATISFIED
        else:
            return SatisfactionTier.CRITICAL

    def _classify_nps(self, score: int) -> NPSCategory:
        """Classify NPS category (Spec §13.3.3)."""
        if score >= 9:
            return NPSCategory.PROMOTER
        elif score >= 7:
            return NPSCategory.PASSIVE
        else:
            return NPSCategory.DETRACTOR

    def calculate_nps(self, stakeholder_ids: list[str]) -> dict:
        """
        Calculate Net Promoter Score for a group.

        NPS = % Promoters - % Detractors
        Range: -100 to +100
        """
        promoters = 0
        passives = 0
        detractors = 0
        total = 0

        for sid in stakeholder_ids:
            responses = [r for r in self._responses.values()
                         if r.stakeholder_id == sid and r.nps_score is not None]
            if responses:
                # Use most recent NPS
                latest = max(responses, key=lambda r: r.timestamp)
                total += 1
                if latest.nps_score >= 9:
                    promoters += 1
                elif latest.nps_score >= 7:
                    passives += 1
                else:
                    detractors += 1

        if total == 0:
            return {"nps": 0, "promoters": 0, "passives": 0, "detractors": 0, "total": 0}

        nps = round((promoters / total - detractors / total) * 100)

        return {
            "nps": nps,
            "promoters": promoters,
            "passives": passives,
            "detractors": detractors,
            "total": total,
            "promoter_pct": round(promoters / total * 100, 1),
            "passive_pct": round(passives / total * 100, 1),
            "detractor_pct": round(detractors / total * 100, 1),
        }

    # ---- Benchmarking ----

    def internal_benchmark(self, stakeholder_ids: list[str]) -> dict:
        """
        Internal benchmarking (Spec §13.4.1).

        Compare satisfaction by stakeholder group, mechanism, channel, time period.
        """
        by_layer = defaultdict(list)
        by_tier = defaultdict(int)

        for sid in stakeholder_ids:
            score = self.calculate_composite_score(sid)
            by_layer[score.layer.value].append(score.score)
            by_tier[score.tier.value] += 1

        layer_averages = {}
        for layer, scores in by_layer.items():
            layer_averages[layer] = round(sum(scores) / len(scores), 1) if scores else 0

        return {
            "by_layer": layer_averages,
            "by_tier": dict(by_tier),
            "average": round(sum(layer_averages.values()) / max(len(layer_averages), 1), 1),
        }

    def external_benchmark(self, industry_nps: float = 30.0,
                           peer_nps: float = 35.0) -> dict:
        """
        External benchmarking (Spec §13.4.2).

        Compare GRC_Claw NPS against industry averages.
        """
        # This would typically fetch external data
        return {
            "industry_nps_average": industry_nps,
            "peer_nps_average": peer_nps,
            "grc_claw_nps": "calculated separately",
            "comparison": "above_average" if peer_nps > industry_nps else "below_average",
        }

    # ---- Alerts ----

    def check_alerts(self, stakeholder_id: str,
                     current_score: float,
                     previous_score: float,
                     nps_category: Optional[NPSCategory] = None) -> list[SatisfactionAlert]:
        """Check for satisfaction alerts (Spec §13.6.2)."""
        alerts = []

        # Satisfaction drop > 1.0 point
        if previous_score - current_score > 1.0:
            alerts.append(SatisfactionAlert(
                alert_id=f"SAT-{len(self._alerts) + 1:04d}",
                alert_type=AlertType.SATISFACTION_DROP,
                stakeholder_id=stakeholder_id,
                message=f"Satisfaction dropped by {previous_score - current_score:.1f} points",
                severity="high",
            ))

        # Detractor identified
        if nps_category == NPSCategory.DETRACTOR:
            alerts.append(SatisfactionAlert(
                alert_id=f"SAT-{len(self._alerts) + 2:04d}",
                alert_type=AlertType.DETRACTOR_IDENTIFIED,
                stakeholder_id=stakeholder_id,
                message="NPS detractor identified — immediate outreach + recovery",
                severity="critical",
            ))

        # Critical satisfaction
        if current_score < 40:
            alerts.append(SatisfactionAlert(
                alert_id=f"SAT-{len(self._alerts) + 3:04d}",
                alert_type=AlertType.CRITICAL_SATISFACTION,
                stakeholder_id=stakeholder_id,
                message=f"Critical satisfaction score: {current_score}",
                severity="critical",
            ))

        for alert in alerts:
            self._alerts[alert.alert_id] = alert

        return alerts

    # ---- Dashboard Data ----

    def get_satisfaction_dashboard(self, view: str,
                                   stakeholder_ids: list[str]) -> dict:
        """
        Satisfaction dashboard data (Spec §13.6.1).

        Views: executive, program, operating
        """
        if view == "executive":
            return self._executive_view(stakeholder_ids)
        elif view == "program":
            return self._program_view(stakeholder_ids)
        elif view == "operating":
            return self._operating_view(stakeholder_ids[0] if stakeholder_ids else "")
        else:
            raise ValueError(f"Unknown view: {view}")

    def _executive_view(self, stakeholder_ids: list[str]) -> dict:
        """Executive satisfaction view."""
        nps = self.calculate_nps(stakeholder_ids)
        benchmark = self.internal_benchmark(stakeholder_ids)

        return {
            "view": "executive",
            "audience": "Exec sponsors, governance committee",
            "nps": nps,
            "average_satisfaction": benchmark["average"],
            "tier_distribution": benchmark["by_tier"],
            "alerts": [a.to_dict() for a in self._alerts.values()
                       if a.severity in ("high", "critical")],
        }

    def _program_view(self, stakeholder_ids: list[str]) -> dict:
        """Program satisfaction view."""
        by_layer = defaultdict(list)
        for sid in stakeholder_ids:
            score = self.calculate_composite_score(sid)
            by_layer[score.layer.value].append(score.score)

        return {
            "view": "program",
            "audience": "Engagement leads",
            "by_layer": {k: round(sum(v) / len(v), 1) for k, v in by_layer.items()},
            "total_alerts": len(self._alerts),
            "unacknowledged": len([a for a in self._alerts.values() if not a.acknowledged]),
        }

    def _operating_view(self, stakeholder_id: str) -> dict:
        """Operating satisfaction view."""
        score = self.calculate_composite_score(stakeholder_id)
        responses = [r.to_dict() for r in self._responses.values()
                     if r.stakeholder_id == stakeholder_id][-10:]

        return {
            "view": "operating",
            "audience": "Engagement team",
            "stakeholder_id": stakeholder_id,
            "current_score": score.to_dict(),
            "recent_responses": responses,
        }

    # ---- Integration with Effectiveness ----

    def get_effectiveness_inputs(self, stakeholder_id: str) -> dict:
        """
        Get satisfaction data for engagement effectiveness scoring (Spec §13.7).

        Maps satisfaction dimensions to effectiveness dimensions.
        """
        score = self.calculate_composite_score(stakeholder_id)

        return {
            "satisfaction_score": score.score,           # → Satisfaction (20% weight)
            "nps_score": score.nps_score,                # → Outcome (20% weight)
            "responsiveness": score.dimension_scores.get("responsiveness", 0),  # → Responsiveness (10%)
            "relevance": score.dimension_scores.get("relevance", 0),            # → Depth (15%)
            "quality": score.dimension_scores.get("quality", 0),                # → Depth (15%)
            "transparency": score.dimension_scores.get("transparency", 0),      # → Satisfaction (20%)
            "impact": score.dimension_scores.get("impact", 0),                  # → Outcome (20%)
        }


# ---------------------------------------------------------------------------
# Demo / Self-test
# ---------------------------------------------------------------------------

def _demo():
    """Demonstrate satisfaction measurement."""
    engine = SatisfactionMeasurementEngine()

    # Add satisfaction responses
    print("--- Adding Satisfaction Responses ---")
    responses = [
        SatisfactionResponse("", "STK-001", "semi_annual", "2026-09-01T10:00:00",
                             SatisfactionLayer.RELATIONAL,
                             responsiveness=4.5, relevance=4.0, quality=4.5,
                             accessibility=4.0, transparency=4.5, impact=4.0,
                             nps_score=9, open_feedback="Great platform!",
                             relationship_health=4.5),
        SatisfactionResponse("", "STK-001", "post_interaction", "2026-09-15T14:00:00",
                             SatisfactionLayer.TRANSACTIONAL,
                             responsiveness=5.0, relevance=4.5, quality=4.0,
                             accessibility=4.5, transparency=4.0, impact=4.0,
                             nps_score=9, open_feedback="Very helpful workshop"),
        SatisfactionResponse("", "STK-002", "semi_annual", "2026-09-01T10:00:00",
                             SatisfactionLayer.RELATIONAL,
                             responsiveness=3.5, relevance=3.0, quality=3.5,
                             accessibility=3.0, transparency=3.5, impact=3.0,
                             nps_score=7, open_feedback="Could be better",
                             relationship_health=3.5),
        SatisfactionResponse("", "STK-003", "semi_annual", "2026-09-01T10:00:00",
                             SatisfactionLayer.RELATIONAL,
                             responsiveness=2.0, relevance=2.5, quality=2.0,
                             accessibility=2.0, transparency=2.5, impact=2.0,
                             nps_score=4, open_feedback="Disappointed with progress",
                             relationship_health=2.0),
        SatisfactionResponse("", "STK-004", "semi_annual", "2026-09-01T10:00:00",
                             SatisfactionLayer.RELATIONAL,
                             responsiveness=4.0, relevance=3.5, quality=4.0,
                             accessibility=3.5, transparency=4.0, impact=3.5,
                             nps_score=8, open_feedback="Good overall",
                             relationship_health=4.0),
    ]

    for resp in responses:
        engine.add_response(resp)
        print(f"  Added: {resp.response_id} | {resp.stakeholder_id} | "
              f"{resp.survey_type} | NPS={resp.nps_score}")

    # Calculate composite scores
    print("\n--- Composite Satisfaction Scores ---")
    for sid in ["STK-001", "STK-002", "STK-003", "STK-004"]:
        score = engine.calculate_composite_score(sid)
        print(f"  {sid}: score={score.score} tier={score.tier.value} "
              f"NPS={score.nps_score} ({score.nps_category.value if score.nps_category else 'N/A'})")

    # NPS calculation
    print("\n--- NPS Calculation ---")
    nps = engine.calculate_nps(["STK-001", "STK-002", "STK-003", "STK-004"])
    print(f"  NPS: {nps['nps']} (Promoters: {nps['promoters']}, "
          f"Passives: {nps['passives']}, Detractors: {nps['detractors']})")

    # Internal benchmark
    print("\n--- Internal Benchmark ---")
    benchmark = engine.internal_benchmark(["STK-001", "STK-002", "STK-003", "STK-004"])
    print(f"  By layer: {benchmark['by_layer']}")
    print(f"  By tier: {benchmark['by_tier']}")
    print(f"  Average: {benchmark['average']}")

    # Alerts
    print("\n--- Satisfaction Alerts ---")
    alerts = engine.check_alerts("STK-003", 35.0, 50.0, NPSCategory.DETRACTOR)
    for alert in alerts:
        print(f"  {alert.alert_id}: {alert.alert_type.value} — {alert.message}")

    # Dashboard views
    print("\n--- Executive Dashboard ---")
    exec_view = engine.get_satisfaction_dashboard("executive",
                                                   ["STK-001", "STK-002", "STK-003", "STK-004"])
    print(f"  NPS: {exec_view['nps']['nps']}")
    print(f"  Average: {exec_view['average_satisfaction']}")
    print(f"  Alerts: {len(exec_view['alerts'])}")

    print("\n--- Program Dashboard ---")
    prog_view = engine.get_satisfaction_dashboard("program",
                                                   ["STK-001", "STK-002", "STK-003", "STK-004"])
    print(f"  By layer: {prog_view['by_layer']}")

    print("\n--- Operating Dashboard ---")
    ops_view = engine.get_satisfaction_dashboard("operating", ["STK-001"])
    print(f"  Score: {ops_view['current_score']['score']}")
    print(f"  Recent responses: {len(ops_view['recent_responses'])}")

    # Effectiveness inputs
    print("\n--- Effectiveness Inputs ---")
    inputs = engine.get_effectiveness_inputs("STK-001")
    for key, val in inputs.items():
        print(f"  {key}: {val}")

    print("\n✓ Satisfaction Measurement demo complete")


if __name__ == "__main__":
    _demo()
