"""
GRC_Claw Engagement Optimization
=================================
Implements the engagement effectiveness scoring and continuous improvement
system from the GRC_Claw Stakeholder Engagement Specification v2.0 (Section 9, 12).

Covers:
- 7-dimension effectiveness scoring model (Spec §9.1.1)
- Composite effectiveness score calculation (Spec §9.1.3)
- 5-tier effectiveness classification (Spec §9.3.1)
- Dimension thresholds with RAG status (Spec §9.3.2)
- Continuous improvement loop (Spec §9.4)
- Scorecard generation (Spec §9.6.1)
- Integration with governance reviews (Spec §9.5)
- Feedback loop optimization metrics (Spec §12.6)
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional
from collections import defaultdict


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class EffectivenessDimension(str, Enum):
    REACH = "reach"
    FREQUENCY = "frequency"
    DEPTH = "depth"
    SATISFACTION = "satisfaction"
    OUTCOME = "outcome"
    RESPONSIVENESS = "responsiveness"
    INCLUSIVITY = "inclusivity"


class EffectivenessTier(str, Enum):
    TIER_1 = "optimized"      # 85-100
    TIER_2 = "managed"        # 70-84
    TIER_3 = "defined"        # 55-69
    TIER_4 = "initial"        # 40-54
    TIER_5 = "ad_hoc"         # 0-39


class RAGStatus(str, Enum):
    GREEN = "green"
    AMBER = "amber"
    RED = "red"


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

@dataclass
class DimensionScore:
    """Score for a single effectiveness dimension."""

    dimension: EffectivenessDimension
    score: float  # 0-100
    weight: float  # 0-1
    trend: str = "→"  # ↑ → ↓
    rag_status: RAGStatus = RAGStatus.GREEN
    raw_value: float = 0.0
    target: float = 0.0

    def to_dict(self) -> dict:
        d = asdict(self)
        d["dimension"] = self.dimension.value
        d["rag_status"] = self.rag_status.value
        return d


@dataclass
class EffectivenessScorecard:
    """Complete effectiveness scorecard (Spec §9.6.1)."""

    period: str
    composite_score: float  # 0-100
    tier: EffectivenessTier
    dimensions: list[DimensionScore] = field(default_factory=list)
    top_improvements: list[dict] = field(default_factory=list)
    benchmark: str = ""
    generated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict:
        d = asdict(self)
        d["tier"] = self.tier.value
        d["dimensions"] = [dim.to_dict() for dim in self.dimensions]
        return d


@dataclass
class ImprovementAction:
    """A tracked improvement action."""

    action_id: str
    description: str
    dimension: EffectivenessDimension
    owner: str
    due_date: str
    status: str = "planned"  # planned / in_progress / completed / cancelled
    impact_score: float = 0.0  # Measured impact after completion
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict:
        d = asdict(self)
        d["dimension"] = self.dimension.value
        return d


# ---------------------------------------------------------------------------
# Effectiveness Scoring Engine
# ---------------------------------------------------------------------------

class EffectivenessScoringEngine:
    """
    Multi-dimensional effectiveness scoring engine (Spec §9.1).

    Dimensions and weights:
    - Reach: 15%          — % of target stakeholders engaged
    - Frequency: 10%      — Engagement frequency vs. plan
    - Depth: 15%          — Quality and substance of engagement
    - Satisfaction: 20%   — Stakeholder satisfaction with engagement
    - Outcome: 20%        — Tangible results from engagement
    - Responsiveness: 10% — Speed and quality of response
    - Inclusivity: 10%    — Breadth of stakeholder groups represented
    """

    DIMENSION_WEIGHTS = {
        EffectivenessDimension.REACH: 0.15,
        EffectivenessDimension.FREQUENCY: 0.10,
        EffectivenessDimension.DEPTH: 0.15,
        EffectivenessDimension.SATISFACTION: 0.20,
        EffectivenessDimension.OUTCOME: 0.20,
        EffectivenessDimension.RESPONSIVENESS: 0.10,
        EffectivenessDimension.INCLUSIVITY: 0.10,
    }

    # RAG thresholds (Spec §9.3.2)
    RAG_THRESHOLDS = {
        EffectivenessDimension.REACH: {"green": 80, "amber": 50},
        EffectivenessDimension.FREQUENCY: {"green": 90, "amber": 70},
        EffectivenessDimension.DEPTH: {"green": 75, "amber": 50},
        EffectivenessDimension.SATISFACTION: {"green": 80, "amber": 60},  # 4.0/5.0 = 80%
        EffectivenessDimension.OUTCOME: {"green": 80, "amber": 60},
        EffectivenessDimension.RESPONSIVENESS: {"green": 95, "amber": 85},
        EffectivenessDimension.INCLUSIVITY: {"green": 85, "amber": 70},
    }

    # Tier thresholds (Spec §9.3.1)
    TIER_THRESHOLDS = {
        EffectivenessTier.TIER_1: (85, 100),
        EffectivenessTier.TIER_2: (70, 84),
        EffectivenessTier.TIER_3: (55, 69),
        EffectivenessTier.TIER_4: (40, 54),
        EffectivenessTier.TIER_5: (0, 39),
    }

    def __init__(self):
        self._scorecards: dict[str, EffectivenessScorecard] = {}
        self._improvements: dict[str, ImprovementAction] = {}
        self._next_id = 1

    def score_dimension(self, dimension: EffectivenessDimension,
                        raw_value: float, target: float,
                        trend: str = "→") -> DimensionScore:
        """
        Score a single dimension.

        raw_value: the measured metric (already normalized to 0-100)
        target: the target value for this dimension
        """
        weight = self.DIMENSION_WEIGHTS.get(dimension, 0.0)
        score = max(0, min(100, raw_value))

        # RAG status
        thresholds = self.RAG_THRESHOLDS.get(dimension, {"green": 75, "amber": 50})
        if score >= thresholds["green"]:
            rag = RAGStatus.GREEN
        elif score >= thresholds["amber"]:
            rag = RAGStatus.AMBER
        else:
            rag = RAGStatus.RED

        return DimensionScore(
            dimension=dimension,
            score=round(score, 1),
            weight=weight,
            trend=trend,
            rag_status=rag,
            raw_value=raw_value,
            target=target,
        )

    def calculate_composite(self, dimension_scores: list[DimensionScore]) -> float:
        """
        Calculate composite effectiveness score (Spec §9.1.3).

        Composite Score = Σ (Dimension Score × Dimension Weight)
        """
        weighted_sum = sum(d.score * d.weight for d in dimension_scores)
        # Weights should sum to 1.0
        total_weight = sum(d.weight for d in dimension_scores)
        if total_weight == 0:
            return 0.0
        return round(weighted_sum / total_weight, 1)

    def classify_tier(self, composite: float) -> EffectivenessTier:
        """Classify effectiveness tier (Spec §9.3.1)."""
        if composite >= 85:
            return EffectivenessTier.TIER_1
        elif composite >= 70:
            return EffectivenessTier.TIER_2
        elif composite >= 55:
            return EffectivenessTier.TIER_3
        elif composite >= 40:
            return EffectivenessTier.TIER_4
        else:
            return EffectivenessTier.TIER_5

    def generate_scorecard(self, period: str,
                           dimension_scores: list[DimensionScore],
                           benchmark: str = "") -> EffectivenessScorecard:
        """Generate a complete effectiveness scorecard (Spec §9.6.1)."""
        composite = self.calculate_composite(dimension_scores)
        tier = self.classify_tier(composite)

        # Identify top 3 improvements (lowest scoring dimensions)
        sorted_dims = sorted(dimension_scores, key=lambda d: d.score)
        top_improvements = []
        for dim in sorted_dims[:3]:
            if dim.rag_status != RAGStatus.GREEN:
                top_improvements.append({
                    "dimension": dim.dimension.value,
                    "current_score": dim.score,
                    "target": dim.target,
                    "gap": round(dim.target - dim.score, 1),
                    "action": f"Improve {dim.dimension.value} from {dim.score} to {dim.target}",
                })

        scorecard = EffectivenessScorecard(
            period=period,
            composite_score=composite,
            tier=tier,
            dimensions=dimension_scores,
            top_improvements=top_improvements,
            benchmark=benchmark,
        )
        self._scorecards[period] = scorecard
        return scorecard

    def add_improvement(self, description: str, dimension: EffectivenessDimension,
                        owner: str, due_date: str) -> ImprovementAction:
        """Add an improvement action."""
        action = ImprovementAction(
            action_id=f"IMP-{self._next_id:04d}",
            description=description,
            dimension=dimension,
            owner=owner,
            due_date=due_date,
        )
        self._next_id += 1
        self._improvements[action.action_id] = action
        return action

    def complete_improvement(self, action_id: str, impact_score: float) -> ImprovementAction:
        """Mark an improvement as completed with measured impact."""
        action = self._improvements.get(action_id)
        if not action:
            raise KeyError(f"Improvement {action_id} not found")
        action.status = "completed"
        action.impact_score = impact_score
        return action

    # ---- Continuous Improvement Loop ----

    def run_improvement_cycle(self, current_scorecard: EffectivenessScorecard) -> dict:
        """
        Run one cycle of the continuous improvement loop (Spec §9.4).

        MEASURE → ANALYZE → IMPROVE → VALIDATE
        """
        # ANALYZE: Identify gaps
        gaps = []
        for dim in current_scorecard.dimensions:
            if dim.rag_status == RAGStatus.RED:
                gaps.append({
                    "dimension": dim.dimension.value,
                    "severity": "critical",
                    "gap": round(dim.target - dim.score, 1),
                })
            elif dim.rag_status == RAGStatus.AMBER:
                gaps.append({
                    "dimension": dim.dimension.value,
                    "severity": "moderate",
                    "gap": round(dim.target - dim.score, 1),
                })

        # IMPROVE: Generate improvement actions
        actions = []
        for gap in gaps:
            action = self.add_improvement(
                description=f"Close {gap['dimension']} gap of {gap['gap']} points",
                dimension=EffectivenessDimension(gap["dimension"]),
                owner="TBD",
                due_date=(datetime.utcnow().replace(day=1) + __import__("datetime").timedelta(days=90)).isoformat(),
            )
            actions.append(action)

        return {
            "cycle_date": datetime.utcnow().isoformat(),
            "composite_score": current_scorecard.composite_score,
            "tier": current_scorecard.tier.value,
            "gaps_identified": len(gaps),
            "gaps": gaps,
            "actions_created": len(actions),
            "actions": [a.to_dict() for a in actions],
        }

    # ---- Trend Analysis ----

    def get_trend(self, periods: int = 6) -> list[dict]:
        """Get effectiveness score trend over time."""
        sorted_periods = sorted(self._scorecards.keys())[-periods:]
        trend = []
        for period in sorted_periods:
            sc = self._scorecards[period]
            trend.append({
                "period": period,
                "composite": sc.composite_score,
                "tier": sc.tier.value,
            })
        return trend

    def get_dimension_trends(self, periods: int = 6) -> dict:
        """Get trends for each dimension."""
        sorted_periods = sorted(self._scorecards.keys())[-periods:]
        trends = defaultdict(list)

        for period in sorted_periods:
            sc = self._scorecards[period]
            for dim in sc.dimensions:
                trends[dim.dimension.value].append({
                    "period": period,
                    "score": dim.score,
                    "rag": dim.rag_status.value,
                })

        return dict(trends)

    # ---- Governance Review Integration ----

    def get_review_data(self, review_type: str) -> dict:
        """
        Get effectiveness data for governance reviews (Spec §9.5).

        Review types: operational (monthly), tactical (quarterly),
                      strategic (semi-annual), annual
        """
        if not self._scorecards:
            return {"error": "No scorecards available"}

        latest = list(self._scorecards.values())[-1]

        if review_type == "operational":
            return {
                "review_type": "operational",
                "frequency": "Monthly",
                "composite": latest.composite_score,
                "tier": latest.tier.value,
                "dimension_scores": [d.to_dict() for d in latest.dimensions],
                "improvement_actions": len(self._improvements),
            }
        elif review_type == "tactical":
            return {
                "review_type": "tactical",
                "frequency": "Quarterly",
                "composite": latest.composite_score,
                "tier": latest.tier.value,
                "trend": self.get_trend(4),
                "benchmark": latest.benchmark,
            }
        elif review_type == "strategic":
            return {
                "review_type": "strategic",
                "frequency": "Semi-annually",
                "composite": latest.composite_score,
                "tier": latest.tier.value,
                "trend": self.get_trend(6),
                "dimension_trends": self.get_dimension_trends(6),
            }
        elif review_type == "annual":
            return {
                "review_type": "annual",
                "frequency": "Annually",
                "composite": latest.composite_score,
                "tier": latest.tier.value,
                "trend": self.get_trend(12),
                "improvements_completed": len([a for a in self._improvements.values()
                                                if a.status == "completed"]),
                "total_improvements": len(self._improvements),
            }
        else:
            raise ValueError(f"Unknown review type: {review_type}")

    # ---- Feedback Loop Optimization Metrics ----

    def get_optimization_metrics(self) -> dict:
        """
        Feedback loop optimization metrics (Spec §12.6).
        """
        total_improvements = len(self._improvements)
        completed = len([a for a in self._improvements.values() if a.status == "completed"])
        in_progress = len([a for a in self._improvements.values() if a.status == "in_progress"])

        return {
            "improvement_velocity": completed,  # per quarter
            "improvements_completed": completed,
            "improvements_in_progress": in_progress,
            "improvements_planned": total_improvements - completed - in_progress,
            "completion_rate": round(completed / max(total_improvements, 1) * 100, 1),
        }

    # ---- Scorecard Formatting ----

    def format_scorecard_text(self, scorecard: EffectivenessScorecard) -> str:
        """Format scorecard as text (Spec §9.6.1 template)."""
        lines = [
            f"Engagement Effectiveness Scorecard — {scorecard.period}",
            "",
            f"Composite Effectiveness Score: {scorecard.composite_score}/100 "
            f"(Tier {scorecard.tier.value})",
            "",
            f"{'Dimension':<20} {'Score':>6} {'Weight':>8} {'Weighted':>10} "
            f"{'Trend':>6} {'Status':>8}",
            "─" * 65,
        ]

        for dim in scorecard.dimensions:
            weighted = round(dim.score * dim.weight, 1)
            status_icon = {"green": "🟢", "amber": "🟡", "red": "🔴"}[dim.rag_status.value]
            lines.append(
                f"{dim.dimension.value:<20} {dim.score:>6.1f} {dim.weight:>7.0%} "
                f"{weighted:>10.1f} {dim.trend:>6} {status_icon:>8}"
            )

        lines.append("─" * 65)
        lines.append(f"{'TOTAL':<20} {'':>6} {'100%':>8} {scorecard.composite_score:>10.1f}")

        if scorecard.top_improvements:
            lines.append("")
            lines.append("Top 3 Improvements:")
            for i, imp in enumerate(scorecard.top_improvements, 1):
                lines.append(f"  {i}. {imp['action']}")

        if scorecard.benchmark:
            lines.append("")
            lines.append(f"Benchmark: {scorecard.benchmark}")

        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Demo / Self-test
# ---------------------------------------------------------------------------

def _demo():
    """Demonstrate engagement optimization."""
    engine = EffectivenessScoringEngine()

    # Score dimensions
    print("--- Scoring Dimensions ---")
    dimensions = [
        (EffectivenessDimension.REACH, 72.0, 80.0, "↑"),
        (EffectivenessDimension.FREQUENCY, 88.0, 90.0, "→"),
        (EffectivenessDimension.DEPTH, 65.0, 75.0, "↑"),
        (EffectivenessDimension.SATISFACTION, 82.0, 80.0, "↑"),
        (EffectivenessDimension.OUTCOME, 70.0, 80.0, "→"),
        (EffectivenessDimension.RESPONSIVENESS, 96.0, 95.0, "↑"),
        (EffectivenessDimension.INCLUSIVITY, 78.0, 85.0, "↑"),
    ]

    dim_scores = []
    for dim, score, target, trend in dimensions:
        ds = engine.score_dimension(dim, score, target, trend)
        dim_scores.append(ds)
        print(f"  {dim.value}: score={ds.score} weight={ds.weight:.0%} "
              f"rag={ds.rag_status.value}")

    # Generate scorecard
    print("\n--- Effectiveness Scorecard ---")
    scorecard = engine.generate_scorecard(
        period="2026-Q3",
        dimension_scores=dim_scores,
        benchmark="Industry average: 65/100",
    )
    print(f"  Composite: {scorecard.composite_score}/100")
    print(f"  Tier: {scorecard.tier.value}")
    print(f"  Top improvements: {len(scorecard.top_improvements)}")
    for imp in scorecard.top_improvements:
        print(f"    - {imp['action']}")

    # Format scorecard
    print("\n--- Formatted Scorecard ---")
    print(engine.format_scorecard_text(scorecard))

    # Run improvement cycle
    print("\n--- Improvement Cycle ---")
    cycle = engine.run_improvement_cycle(scorecard)
    print(f"  Gaps identified: {cycle['gaps_identified']}")
    for gap in cycle["gaps"]:
        print(f"    - {gap['dimension']}: {gap['severity']} (gap: {gap['gap']})")
    print(f"  Actions created: {cycle['actions_created']}")

    # Complete an improvement
    if cycle["actions"]:
        action_id = cycle["actions"][0]["action_id"]
        engine.complete_improvement(action_id, impact_score=5.0)
        print(f"  Completed: {action_id} (impact: +5.0)")

    # Trend analysis
    print("\n--- Trend Analysis ---")
    # Add a second scorecard for trend
    dim_scores_2 = []
    for dim, score, target, trend in dimensions:
        new_score = min(100, score + 5)  # Simulate improvement
        ds = engine.score_dimension(dim, new_score, target, "↑")
        dim_scores_2.append(ds)

    scorecard_2 = engine.generate_scorecard(
        period="2026-Q4",
        dimension_scores=dim_scores_2,
        benchmark="Industry average: 65/100",
    )

    trend = engine.get_trend()
    for t in trend:
        print(f"  {t['period']}: {t['composite']} ({t['tier']})")

    # Governance review data
    print("\n--- Governance Review Data ---")
    for review_type in ["operational", "tactical", "strategic", "annual"]:
        data = engine.get_review_data(review_type)
        print(f"  {review_type}: composite={data.get('composite', 'N/A')}")

    # Optimization metrics
    print("\n--- Optimization Metrics ---")
    metrics = engine.get_optimization_metrics()
    for key, val in metrics.items():
        print(f"  {key}: {val}")

    # Persistence
    print("\n--- Persistence ---")
    scorecard_data = scorecard.to_dict()
    print(f"  Scorecard dict keys: {list(scorecard_data.keys())}")

    print("\n✓ Engagement Optimization demo complete")


if __name__ == "__main__":
    _demo()
