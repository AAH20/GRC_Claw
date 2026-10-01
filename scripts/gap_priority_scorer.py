#!/usr/bin/env python3
"""
GRC_Claw Priority Scoring Engine

Computes dynamic priority scores for gaps using multiple factors:
- Base priority (impact × feasibility from blueprints)
- Urgency multiplier (regulatory deadlines, market windows)
- Dependency readiness (are prerequisite gaps resolved?)
- Risk exposure (severity × gap age)
- Strategic alignment (phase weighting)
- Effort-to-value ratio

Outputs a ranked list with score breakdowns and recommendations.

Usage:
    python gap_priority_scorer.py [--registry gaps.json] [--output scores.json] [--verbose]
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gap_model import (
    Gap, GapStatus, GapCategory, GapSeverity,
    load_gaps, save_gaps, initialize_gap_registry
)

DEFAULT_REGISTRY = Path(__file__).resolve().parent / "gap_registry.json"


class PriorityScorer:
    """Dynamic priority scoring engine for governance gaps."""

    # Phase weights — earlier phases get higher strategic alignment
    PHASE_WEIGHTS = {
        "GAP-008": 1.3, "GAP-005": 1.3, "GAP-015": 1.2, "GAP-010": 1.2,  # Phase 1
        "GAP-001": 1.2, "GAP-003": 1.2, "GAP-004": 1.1, "GAP-012": 1.1,  # Phase 2
        "GAP-002": 1.1, "GAP-006": 1.0, "GAP-016": 1.0, "GAP-007": 0.9, "GAP-013": 0.9,  # Phase 3
        "GAP-009": 0.8, "GAP-011": 0.8, "GAP-017": 0.8, "GAP-018": 0.7, "GAP-019": 0.7, "GAP-014": 0.7, "GAP-020": 0.7,  # Phase 4
    }

    # Category urgency multipliers
    CATEGORY_MULTIPLIERS = {
        GapCategory.STANDARD: 1.2,
        GapCategory.PLATFORM: 1.15,
        GapCategory.TOOLING: 1.1,
        GapCategory.FRAMEWORK: 1.0,
        GapCategory.LANGUAGE: 1.05,
        GapCategory.PROCESS: 0.95,
    }

    # Severity risk weights
    SEVERITY_RISK_WEIGHTS = {
        GapSeverity.CRITICAL: 2.0,
        GapSeverity.HIGH: 1.5,
        GapSeverity.MEDIUM: 1.0,
        GapSeverity.LOW: 0.6,
        GapSeverity.INFO: 0.3,
    }

    # Status-based urgency (open gaps get boosted, resolved get zeroed)
    STATUS_URGENCY = {
        GapStatus.IDENTIFIED: 1.0,
        GapStatus.ANALYZING: 1.05,
        GapStatus.PLANNED: 1.1,
        GapStatus.IN_PROGRESS: 1.15,
        GapStatus.IMPLEMENTING: 1.1,
        GapStatus.VALIDATING: 1.05,
        GapStatus.MITIGATED: 0.0,
        GapStatus.CLOSED: 0.0,
        GapStatus.DEFERRED: 0.3,
        GapStatus.ACCEPTED: 0.1,
    }

    def __init__(self, gaps: list[Gap], verbose: bool = False):
        self.gaps = gaps
        self.verbose = verbose
        self.gap_map = {g.id: g for g in gaps}
        self.scores: dict[str, dict[str, Any]] = {}

    def log(self, msg: str) -> None:
        if self.verbose:
            print(f"[scorer] {msg}")

    def compute_base_score(self, gap: Gap) -> float:
        """Base priority from impact × feasibility."""
        return gap.impact * gap.feasibility

    def compute_urgency_multiplier(self, gap: Gap) -> float:
        """Urgency based on gap age and target date proximity."""
        multiplier = 1.0
        now = datetime.now(timezone.utc)

        # Age factor — older gaps get slightly more urgent
        try:
            created = datetime.fromisoformat(gap.created_date.replace("Z", "+00:00"))
            age_days = (now - created).days
            if age_days > 90:
                multiplier += 0.1
            if age_days > 180:
                multiplier += 0.1
            if age_days > 365:
                multiplier += 0.1
        except (ValueError, AttributeError):
            pass

        # Target date proximity
        if gap.target_date:
            try:
                target = datetime.fromisoformat(gap.target_date.replace("Z", "+00:00"))
                days_to_target = (target - now).days
                if days_to_target < 0:
                    multiplier += 0.3  # Overdue!
                elif days_to_target < 30:
                    multiplier += 0.2
                elif days_to_target < 60:
                    multiplier += 0.1
            except (ValueError, AttributeError):
                pass

        return round(multiplier, 2)

    def compute_dependency_readiness(self, gap: Gap) -> float:
        """Score based on whether dependencies are resolved."""
        if not gap.dependencies:
            return 1.0  # No dependencies = full readiness

        resolved = 0
        in_progress = 0
        for dep_id in gap.dependencies:
            dep = self.gap_map.get(dep_id)
            if dep:
                if dep.status in (GapStatus.MITIGATED, GapStatus.CLOSED):
                    resolved += 1
                elif dep.status in (GapStatus.IN_PROGRESS, GapStatus.IMPLEMENTING, GapStatus.VALIDATING):
                    in_progress += 1

        total = len(gap.dependencies)
        # Full readiness = 1.0, partial = 0.5-0.9, none = 0.3
        if resolved == total:
            return 1.0
        elif resolved + in_progress == total:
            return 0.7
        elif resolved > 0:
            return 0.5
        else:
            return 0.3

    def compute_risk_exposure(self, gap: Gap) -> float:
        """Risk exposure = severity_weight × (1 + age_factor)."""
        sev_weight = self.SEVERITY_RISK_WEIGHTS.get(gap.severity, 1.0)
        age_factor = 0.0
        try:
            created = datetime.fromisoformat(gap.created_date.replace("Z", "+00:00"))
            age_days = (datetime.now(timezone.utc) - created).days
            age_factor = min(0.5, age_days / 730)  # Cap at 0.5 after 2 years
        except (ValueError, AttributeError):
            pass
        return round(sev_weight * (1 + age_factor), 2)

    def compute_strategic_alignment(self, gap: Gap) -> float:
        """Strategic alignment from phase weighting."""
        return self.PHASE_WEIGHTS.get(gap.id, 1.0)

    def compute_effort_value_ratio(self, gap: Gap) -> float:
        """Effort-to-value: higher feasibility = better ratio."""
        # Normalize feasibility to 0.5-1.5 range
        return 0.5 + (gap.feasibility / 10.0)

    def compute_status_urgency(self, gap: Gap) -> float:
        """Status-based urgency multiplier."""
        return self.STATUS_URGENCY.get(gap.status, 1.0)

    def compute_final_score(self, gap: Gap) -> dict[str, Any]:
        """Compute the final priority score with full breakdown."""
        base = self.compute_base_score(gap)
        urgency = self.compute_urgency_multiplier(gap)
        dep_readiness = self.compute_dependency_readiness(gap)
        risk = self.compute_risk_exposure(gap)
        strategic = self.compute_strategic_alignment(gap)
        effort_value = self.compute_effort_value_ratio(gap)
        status_urg = self.compute_status_urgency(gap)

        # Weighted composite
        # Base is the foundation, then multipliers adjust
        raw_score = base * urgency * dep_readiness * strategic * effort_value * status_urg
        # Risk exposure is additive (adds urgency for high-severity gaps)
        risk_bonus = risk * 5  # Up to 10 point bonus for critical old gaps
        final_score = round(raw_score + risk_bonus, 1)

        # Normalize to 0-100 scale
        normalized = min(100, max(0, final_score))

        return {
            "gap_id": gap.id,
            "gap_name": gap.name,
            "base_score": round(base, 1),
            "urgency_multiplier": urgency,
            "dependency_readiness": dep_readiness,
            "risk_exposure": risk,
            "strategic_alignment": strategic,
            "effort_value_ratio": round(effort_value, 2),
            "status_urgency": status_urg,
            "risk_bonus": round(risk_bonus, 1),
            "raw_score": round(raw_score, 1),
            "final_score": normalized,
            "severity": gap.severity.value,
            "status": gap.status.value,
            "category": gap.category.value,
        }

    def score_all(self) -> list[dict[str, Any]]:
        """Score all gaps and return sorted results."""
        self.log(f"Scoring {len(self.gaps)} gaps...")
        results = []
        for gap in self.gaps:
            score_data = self.compute_final_score(gap)
            results.append(score_data)
            self.log(f"  {gap.id}: {score_data['final_score']:.1f} (base={score_data['base_score']:.1f})")

        # Sort by final score descending
        results.sort(key=lambda x: -x["final_score"])
        return results

    def get_recommendations(self, scores: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Generate actionable recommendations based on scores."""
        recommendations = []
        for s in scores:
            gap = self.gap_map.get(s["gap_id"])
            if not gap:
                continue

            # Skip resolved gaps
            if gap.status in (GapStatus.MITIGATED, GapStatus.CLOSED):
                continue

            rec = {
                "gap_id": s["gap_id"],
                "gap_name": s["gap_name"],
                "priority_score": s["final_score"],
                "actions": [],
            }

            if s["dependency_readiness"] < 0.5:
                rec["actions"].append("Unblock dependencies before starting implementation")
            if s["urgency_multiplier"] > 1.2:
                rec["actions"].append("Accelerate — gap is overdue or approaching target date")
            if s["risk_exposure"] > 2.0:
                rec["actions"].append("High risk exposure — prioritize mitigation")
            if s["status_urgency"] == 1.0 and gap.progress == 0:
                rec["actions"].append("Not yet started — assign owner and create implementation plan")
            if s["effort_value_ratio"] > 1.2:
                rec["actions"].append("High effort-to-value ratio — good candidate for quick win")
            if s["strategic_alignment"] >= 1.2:
                rec["actions"].append("Phase 1 priority — align with foundation milestones")

            if rec["actions"]:
                recommendations.append(rec)

        return recommendations

    def run(self) -> dict[str, Any]:
        """Execute full scoring pipeline."""
        scores = self.score_all()
        recommendations = self.get_recommendations(scores)

        # Update gap priority scores in the registry
        for s in scores:
            gap = self.gap_map.get(s["gap_id"])
            if gap:
                gap.priority_score = s["final_score"]
                gap.last_updated = datetime.now(timezone.utc).isoformat()
        save_gaps(self.gaps, DEFAULT_REGISTRY)

        return {
            "scoring_timestamp": datetime.now(timezone.utc).isoformat(),
            "total_gaps_scored": len(scores),
            "scoring_methodology": {
                "base": "impact × feasibility",
                "multipliers": ["urgency", "dependency_readiness", "strategic_alignment", "effort_value", "status_urgency"],
                "additive": ["risk_exposure"],
                "normalization": "0-100 scale",
            },
            "scores": scores,
            "recommendations": recommendations,
            "summary": {
                "critical_priority": sum(1 for s in scores if s["final_score"] >= 80),
                "high_priority": sum(1 for s in scores if 60 <= s["final_score"] < 80),
                "medium_priority": sum(1 for s in scores if 40 <= s["final_score"] < 60),
                "low_priority": sum(1 for s in scores if s["final_score"] < 40),
                "avg_score": sum(s["final_score"] for s in scores) / len(scores) if scores else 0,
            }
        }


def main():
    parser = argparse.ArgumentParser(description="GRC_Claw Priority Scoring Engine")
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--output", "-o", type=Path, default=None)
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    gaps = initialize_gap_registry(args.registry)
    scorer = PriorityScorer(gaps, verbose=args.verbose)
    result = scorer.run()

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, "w") as f:
            json.dump(result, f, indent=2, default=str)
        print(f"Scores saved to {args.output}")

    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        print(f"\n{'='*70}")
        print("GRC_Claw Priority Scoring Report")
        print(f"{'='*70}")
        print(f"Scored: {result['total_gaps_scored']} gaps")
        print(f"Avg score: {result['summary']['avg_score']:.1f}")
        print(f"Critical (≥80): {result['summary']['critical_priority']}")
        print(f"High (60-79): {result['summary']['high_priority']}")
        print(f"Medium (40-59): {result['summary']['medium_priority']}")
        print(f"Low (<40): {result['summary']['low_priority']}")
        print(f"\n{'Rank':<6}{'ID':<10}{'Score':<8}{'Base':<8}{'Urgency':<10}{'Risk':<8}{'Status':<15}{'Gap'}")
        print("-" * 90)
        for i, s in enumerate(result["scores"][:20], 1):
            print(f"{i:<6}{s['gap_id']:<10}{s['final_score']:<8.1f}{s['base_score']:<8.1f}{s['urgency_multiplier']:<10.2f}{s['risk_exposure']:<8.2f}{s['status']:<15}{s['gap_name'][:35]}")

        if result["recommendations"]:
            print(f"\n--- Recommendations ---")
            for r in result["recommendations"][:10]:
                print(f"\n  {r['gap_id']} (score: {r['priority_score']:.1f}):")
                for a in r["actions"]:
                    print(f"    → {a}")


if __name__ == "__main__":
    main()
