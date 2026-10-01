#!/usr/bin/env python3
"""
GRC_Claw U-AIGMM Assessment Automation Engine
=============================================
Automated scoring, analysis, and reporting for the Unified AI Governance Maturity Model.

Usage:
    python grc_claw_assessment.py --questionnaire grc_claw_questionnaire.json --responses responses.json
    python grc_claw_assessment.py --questionnaire grc_claw_questionnaire.json --demo
    python grc_claw_assessment.py --generate-responses --output responses_template.json
"""

from __future__ import annotations

import json
import math
import argparse
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

# ─────────────────────────────────────────────────────────────────────────────
# DEFAULT CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────

DEFAULT_STREAM_WEIGHTS = {"A": 0.6, "B": 0.4}

DEFAULT_THRESHOLDS = {
    1: (1.00, 1.80),
    2: (1.81, 2.60),
    3: (2.61, 3.40),
    4: (3.41, 4.20),
    5: (4.21, 5.00),
}

LEVEL_NAMES = {
    1: "Initial",
    2: "Developing",
    3: "Defined",
    4: "Managed",
    5: "Optimizing",
}

# Industry-specific weight profiles
WEIGHT_PROFILES = {
    "default": {},
    "regulated": {
        "P2": 1.3, "P3": 1.2,
        "2.2": 1.4, "3.2": 1.3, "1.3": 1.3,
    },
    "startup": {
        "P1": 0.8, "P3": 1.3,
        "3.3": 1.4, "3.4": 1.4, "4.2": 0.7,
    },
    "enterprise": {
        "P4": 1.3, "P1": 1.2,
        "4.1": 1.3, "4.3": 1.3, "1.1": 1.2,
    },
}

# Benchmark data by industry
BENCHMARK_DATA = {
    "financial_services": {
        "1.1": 2.6, "1.2": 2.4, "1.3": 2.5,
        "2.1": 2.0, "2.2": 2.7, "2.3": 2.1,
        "3.1": 2.5, "3.2": 2.4, "3.3": 1.7, "3.4": 1.6,
        "4.1": 2.3, "4.2": 2.4, "4.3": 2.0,
    },
    "healthcare": {
        "1.1": 2.4, "1.2": 2.2, "1.3": 2.3,
        "2.1": 2.1, "2.2": 2.8, "2.3": 2.3,
        "3.1": 2.6, "3.2": 2.2, "3.3": 1.5, "3.4": 1.4,
        "4.1": 2.2, "4.2": 2.3, "4.3": 1.9,
    },
    "technology": {
        "1.1": 2.2, "1.2": 2.8, "1.3": 2.1,
        "2.1": 1.9, "2.2": 2.3, "2.3": 2.0,
        "3.1": 2.5, "3.2": 2.2, "3.3": 1.9, "3.4": 1.8,
        "4.1": 2.5, "4.2": 2.5, "4.3": 2.3,
    },
    "manufacturing": {
        "1.1": 1.8, "1.2": 2.0, "1.3": 1.9,
        "2.1": 1.6, "2.2": 2.0, "2.3": 1.7,
        "3.1": 2.2, "3.2": 1.8, "3.3": 1.3, "3.4": 1.2,
        "4.1": 1.9, "4.2": 2.0, "4.3": 1.7,
    },
    "aggregate": {
        "1.1": 2.1, "1.2": 2.3, "1.3": 2.0,
        "2.1": 1.8, "2.2": 2.2, "2.3": 1.9,
        "3.1": 2.4, "3.2": 2.0, "3.3": 1.5, "3.4": 1.4,
        "4.1": 2.1, "4.2": 2.3, "4.3": 1.9,
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# SCORING ENGINE
# ─────────────────────────────────────────────────────────────────────────────

class MaturityScoringEngine:
    """Hierarchical scoring engine for U-AIGMM assessment."""

    def __init__(self, config: Optional[dict[str, Any]] = None):
        config = config or {}
        self.stream_weights = config.get("stream_weights", DEFAULT_STREAM_WEIGHTS)
        self.thresholds = config.get("thresholds", DEFAULT_THRESHOLDS)
        self.weight_profile = config.get("weight_profile", "default")
        self.custom_weights = WEIGHT_PROFILES.get(self.weight_profile, {})

    def score_sub_dimension(
        self, questions: list[dict], responses: dict[str, int]
    ) -> dict:
        """Score a sub-dimension from question responses."""
        stream_a_scores = []
        stream_b_scores = []

        for q in questions:
            qid = q["id"]
            score = responses.get(qid, 1)
            score = max(1, min(5, score))  # Clamp to 1-5

            if q["stream"] == "A":
                stream_a_scores.append(score)
            else:
                stream_b_scores.append(score)

        stream_a_avg = (
            sum(stream_a_scores) / len(stream_a_scores) if stream_a_scores else 0
        )
        stream_b_avg = (
            sum(stream_b_scores) / len(stream_b_scores) if stream_b_scores else 0
        )

        weighted_score = (
            stream_a_avg * self.stream_weights["A"]
            + stream_b_avg * self.stream_weights["B"]
        )

        # Partial credit calculation
        partial_credit = self._calculate_partial_credit(questions, responses)

        return {
            "score": round(weighted_score, 2),
            "stream_a": round(stream_a_avg, 2),
            "stream_b": round(stream_b_avg, 2),
            "partial_credit": round(partial_credit, 2),
            "level": self.assign_level(weighted_score),
        }

    def _calculate_partial_credit(
        self, questions: list[dict], responses: dict[str, int]
    ) -> float:
        """Calculate partial credit for level progression."""
        # Find the highest level where all criteria are met
        max_full_level = 1
        for level in range(1, 6):
            all_met = True
            for q in questions:
                qid = q["id"]
                score = responses.get(qid, 1)
                if score < level:
                    all_met = False
                    break
            if all_met:
                max_full_level = level

        # Check next level partial criteria
        next_level = max_full_level + 1
        if next_level > 5:
            return float(max_full_level)

        criteria_met = 0
        criteria_total = 0
        for q in questions:
            qid = q["id"]
            score = responses.get(qid, 1)
            criteria_total += 1
            if score >= next_level:
                criteria_met += 1

        if criteria_total == 0:
            return float(max_full_level)

        partial = max_full_level + (criteria_met / criteria_total) * 0.5
        return min(partial, 5.0)

    def score_domain(
        self, sub_dimension_scores: list[dict], domain_id: str
    ) -> dict:
        """Score a domain from sub-dimension scores."""
        if not sub_dimension_scores:
            return {"score": 0, "level": 1}

        weight = self.custom_weights.get(domain_id, 1.0)
        total_weight = sum(
            self.custom_weights.get(sd.get("id", ""), 1.0)
            for sd in sub_dimension_scores
        )
        if total_weight == 0:
            total_weight = len(sub_dimension_scores)

        weighted_sum = sum(
            sd["score"] * self.custom_weights.get(sd.get("id", ""), 1.0)
            for sd in sub_dimension_scores
        )
        score = weighted_sum / total_weight

        return {
            "score": round(score, 2),
            "level": self.assign_level(score),
        }

    def score_pillar(
        self, domain_scores: list[dict], pillar_id: str
    ) -> dict:
        """Score a pillar from domain scores."""
        if not domain_scores:
            return {"score": 0, "level": 1}

        weight = self.custom_weights.get(pillar_id, 1.0)
        total_weight = sum(
            self.custom_weights.get(d.get("id", ""), 1.0) for d in domain_scores
        )
        if total_weight == 0:
            total_weight = len(domain_scores)

        weighted_sum = sum(
            d["score"] * self.custom_weights.get(d.get("id", ""), 1.0)
            for d in domain_scores
        )
        score = weighted_sum / total_weight

        return {
            "score": round(score, 2),
            "level": self.assign_level(score),
        }

    def score_overall(self, pillar_scores: list[dict]) -> dict:
        """Calculate overall maturity score."""
        if not pillar_scores:
            return {"score": 0, "level": 1}

        total_weight = sum(
            self.custom_weights.get(p.get("id", ""), 1.0) for p in pillar_scores
        )
        if total_weight == 0:
            total_weight = len(pillar_scores)

        weighted_sum = sum(
            p["score"] * self.custom_weights.get(p.get("id", ""), 1.0)
            for p in pillar_scores
        )
        score = weighted_sum / total_weight

        return {
            "score": round(score, 2),
            "level": self.assign_level(score),
            "normalized": round((score - 1) / 4 * 100, 1),
        }

    def assign_level(self, score: float, method: str = "threshold") -> int:
        """Assign maturity level based on score."""
        if method == "threshold":
            return self._threshold_based_level(score)
        elif method == "cumulative":
            return self._cumulative_gate_level(score)
        else:
            threshold_level = self._threshold_based_level(score)
            cumulative_level = self._cumulative_gate_level(score)
            return min(threshold_level, cumulative_level)

    def _threshold_based_level(self, score: float) -> int:
        """Assign level based on score thresholds."""
        for level, (low, high) in self.thresholds.items():
            if low <= score <= high:
                return level
        return 1 if score < 1.0 else 5

    def _cumulative_gate_level(self, score: float) -> int:
        """Assign level using cumulative gate method."""
        # Simplified: use threshold but require minimum coverage
        return self._threshold_based_level(score)

    def calculate_divergence(self, rater_scores: list[float]) -> float:
        """Calculate perception divergence between raters."""
        if len(rater_scores) < 2:
            return 0.0

        max_divergence = 0.0
        for i in range(len(rater_scores)):
            for j in range(i + 1, len(rater_scores)):
                divergence = abs(rater_scores[i] - rater_scores[j])
                max_divergence = max(max_divergence, divergence)

        return round(max_divergence, 2)

    def calculate_confidence_interval(
        self, rater_scores: list[float]
    ) -> dict:
        """Calculate 95% confidence interval for multi-rater scores."""
        n = len(rater_scores)
        if n < 2:
            return {"mean": rater_scores[0] if rater_scores else 0, "ci_low": 0, "ci_high": 0, "width": 0}

        mean = sum(rater_scores) / n
        variance = sum((x - mean) ** 2 for x in rater_scores) / (n - 1)
        std_dev = math.sqrt(variance)
        se = std_dev / math.sqrt(n)
        ci_low = mean - 1.96 * se
        ci_high = mean + 1.96 * se

        return {
            "mean": round(mean, 2),
            "ci_low": round(ci_low, 2),
            "ci_high": round(ci_high, 2),
            "width": round(ci_high - ci_low, 2),
        }


# ─────────────────────────────────────────────────────────────────────────────
# ASSESSMENT PROCESSOR
# ─────────────────────────────────────────────────────────────────────────────

class AssessmentProcessor:
    """Process assessment responses and generate results."""

    def __init__(self, questionnaire: dict, engine: MaturityScoringEngine):
        self.questionnaire = questionnaire
        self.engine = engine

    def process(self, responses: dict[str, int]) -> dict:
        """Process all responses and generate assessment results."""
        results = {
            "metadata": {
                "assessment_date": datetime.now().isoformat(),
                "questionnaire_version": self.questionnaire["metadata"]["version"],
                "total_questions": self.questionnaire["metadata"]["total_questions"],
                "weight_profile": self.engine.weight_profile,
            },
            "pillars": [],
            "overall": {},
            "benchmark_comparison": {},
            "gap_analysis": {},
        }

        all_domain_scores = []
        all_pillar_scores = []

        for pillar in self.questionnaire["pillars"]:
            pillar_result = {
                "id": pillar["id"],
                "name": pillar["name"],
                "domains": [],
            }

            domain_scores = []
            for domain in pillar["domains"]:
                domain_result = {
                    "id": domain["id"],
                    "name": domain["name"],
                    "sub_dimensions": [],
                }

                sub_dim_scores = []
                for sub_dim in domain["sub_dimensions"]:
                    sub_dim_result = self.engine.score_sub_dimension(
                        sub_dim["questions"], responses
                    )
                    sub_dim_result["id"] = sub_dim["id"]
                    sub_dim_result["name"] = sub_dim["name"]
                    domain_result["sub_dimensions"].append(sub_dim_result)
                    sub_dim_scores.append(sub_dim_result)

                domain_result.update(
                    self.engine.score_domain(sub_dim_scores, domain["id"])
                )
                pillar_result["domains"].append(domain_result)
                domain_scores.append(domain_result)
                all_domain_scores.append(domain_result)

            pillar_result.update(
                self.engine.score_pillar(domain_scores, pillar["id"])
            )
            results["pillars"].append(pillar_result)
            all_pillar_scores.append(pillar_result)

        results["overall"] = self.engine.score_overall(all_pillar_scores)
        results["benchmark_comparison"] = self._compare_benchmarks(all_domain_scores)
        results["gap_analysis"] = self._analyze_gaps(all_domain_scores)

        return results

    def _compare_benchmarks(self, domain_scores: list[dict]) -> dict:
        """Compare scores against industry benchmarks."""
        comparison = {}
        for industry, benchmarks in BENCHMARK_DATA.items():
            industry_comparison = {}
            for domain in domain_scores:
                domain_id = domain["id"]
                if domain_id in benchmarks:
                    benchmark = benchmarks[domain_id]
                    diff = round(domain["score"] - benchmark, 2)
                    industry_comparison[domain_id] = {
                        "score": domain["score"],
                        "benchmark": benchmark,
                        "difference": diff,
                        "percentile": self._estimate_percentile(domain["score"], benchmark),
                    }
            comparison[industry] = industry_comparison
        return comparison

    def _estimate_percentile(self, score: float, benchmark: float) -> int:
        """Estimate percentile based on score vs benchmark."""
        if score >= benchmark + 1.0:
            return 90
        elif score >= benchmark + 0.5:
            return 75
        elif score >= benchmark:
            return 50
        elif score >= benchmark - 0.5:
            return 25
        else:
            return 10

    def _analyze_gaps(self, domain_scores: list[dict]) -> dict:
        """Analyze maturity gaps and identify priorities."""
        gaps = []
        strengths = []

        for domain in domain_scores:
            if domain["score"] < 2.0:
                gaps.append({
                    "domain_id": domain["id"],
                    "domain_name": domain["name"],
                    "score": domain["score"],
                    "level": domain["level"],
                    "priority": "P1 - Critical",
                    "gap": f"Score {domain['score']} is below 2.0 threshold",
                })
            elif domain["score"] < 3.0:
                gaps.append({
                    "domain_id": domain["id"],
                    "domain_name": domain["name"],
                    "score": domain["score"],
                    "level": domain["level"],
                    "priority": "P2 - High",
                    "gap": f"Score {domain['score']} indicates developing maturity",
                })
            elif domain["score"] >= 4.0:
                strengths.append({
                    "domain_id": domain["id"],
                    "domain_name": domain["name"],
                    "score": domain["score"],
                    "level": domain["level"],
                })

        # Sort gaps by score (lowest first)
        gaps.sort(key=lambda x: x["score"])

        return {
            "critical_gaps": [g for g in gaps if g["priority"] == "P1 - Critical"],
            "high_gaps": [g for g in gaps if g["priority"] == "P2 - High"],
            "strengths": strengths,
            "total_gaps": len(gaps),
            "total_strengths": len(strengths),
        }


# ─────────────────────────────────────────────────────────────────────────────
# REPORT GENERATOR
# ─────────────────────────────────────────────────────────────────────────────

class ReportGenerator:
    """Generate assessment reports in multiple formats."""

    def __init__(self, results: dict):
        self.results = results

    def generate_text_report(self) -> str:
        """Generate a plain text assessment report."""
        lines = []
        r = self.results

        lines.append("=" * 70)
        lines.append("GRC_Claw U-AIGMM AI GOVERNANCE MATURITY ASSESSMENT REPORT")
        lines.append("=" * 70)
        lines.append("")
        lines.append(f"Assessment Date: {r['metadata']['assessment_date']}")
        lines.append(f"Questionnaire Version: {r['metadata']['questionnaire_version']}")
        lines.append(f"Weight Profile: {r['metadata']['weight_profile']}")
        lines.append("")

        # Overall Score
        lines.append("-" * 70)
        lines.append("OVERALL MATURITY SCORE")
        lines.append("-" * 70)
        overall = r["overall"]
        lines.append(f"  Score: {overall['score']} / 5.0")
        lines.append(f"  Level: {overall['level']} - {LEVEL_NAMES[overall['level']]}")
        lines.append(f"  Normalized: {overall['normalized']} / 100")
        lines.append("")

        # Pillar Summary
        lines.append("-" * 70)
        lines.append("PILLAR SUMMARY")
        lines.append("-" * 70)
        for pillar in r["pillars"]:
            lines.append(
                f"  {pillar['name']}: {pillar['score']} "
                f"(Level {pillar['level']} - {LEVEL_NAMES[pillar['level']]})"
            )
        lines.append("")

        # Domain Details
        lines.append("-" * 70)
        lines.append("DOMAIN DETAILS")
        lines.append("-" * 70)
        for pillar in r["pillars"]:
            lines.append(f"\n  {pillar['name']}:")
            for domain in pillar["domains"]:
                lines.append(
                    f"    {domain['id']} {domain['name']}: "
                    f"{domain['score']} (Level {domain['level']})"
                )
                for sd in domain["sub_dimensions"]:
                    lines.append(
                        f"      {sd['id']} {sd['name']}: "
                        f"{sd['score']} (A:{sd['stream_a']} B:{sd['stream_b']})"
                    )
        lines.append("")

        # Gap Analysis
        lines.append("-" * 70)
        lines.append("GAP ANALYSIS")
        lines.append("-" * 70)
        gaps = r["gap_analysis"]
        lines.append(f"  Critical Gaps: {len(gaps['critical_gaps'])}")
        for gap in gaps["critical_gaps"]:
            lines.append(f"    - {gap['domain_id']} {gap['domain_name']}: {gap['gap']}")
        lines.append(f"  High Priority Gaps: {len(gaps['high_gaps'])}")
        for gap in gaps["high_gaps"]:
            lines.append(f"    - {gap['domain_id']} {gap['domain_name']}: {gap['gap']}")
        lines.append(f"  Strengths: {len(gaps['strengths'])}")
        for s in gaps["strengths"]:
            lines.append(f"    - {s['domain_id']} {s['domain_name']}: {s['score']}")
        lines.append("")

        # Benchmark Comparison
        lines.append("-" * 70)
        lines.append("BENCHMARK COMPARISON (vs. Industry Aggregate)")
        lines.append("-" * 70)
        aggregate = r["benchmark_comparison"].get("aggregate", {})
        for domain_id, comp in aggregate.items():
            diff_str = f"+{comp['difference']}" if comp['difference'] >= 0 else f"{comp['difference']}"
            lines.append(
                f"  {domain_id}: Score {comp['score']} vs Benchmark {comp['benchmark']} "
                f"({diff_str}, ~P{comp['percentile']})"
            )
        lines.append("")

        # Recommendations
        lines.append("-" * 70)
        lines.append("TOP RECOMMENDATIONS")
        lines.append("-" * 70)
        recs = self._generate_recommendations()
        for i, rec in enumerate(recs, 1):
            lines.append(f"  {i}. {rec}")
        lines.append("")

        lines.append("=" * 70)
        lines.append("END OF REPORT")
        lines.append("=" * 70)

        return "\n".join(lines)

    def generate_heat_map(self) -> str:
        """Generate ASCII heat map visualization."""
        lines = []
        lines.append("")
        lines.append("MATURITY HEAT MAP")
        lines.append("=" * 80)
        lines.append("")

        # Header
        header = f"{'Domain':<35} {'L1':>4} {'L2':>4} {'L3':>4} {'L4':>4} {'L5':>4} {'Score':>7} {'Level':>6}"
        lines.append(header)
        lines.append("-" * 80)

        for pillar in self.results["pillars"]:
            for domain in pillar["domains"]:
                score = domain["score"]
                level = domain["level"]

                # Create heat map bars
                bars = []
                for l in range(1, 6):
                    if score >= l:
                        bars.append(f"{'█':>4}")
                    elif score >= l - 0.5:
                        bars.append(f"{'▓':>4}")
                    elif score >= l - 1.0:
                        bars.append(f"{'▒':>4}")
                    else:
                        bars.append(f"{'░':>4}")

                domain_label = f"{domain['id']} {domain['name'][:28]}"
                lines.append(
                    f"{domain_label:<35} {bars[0]} {bars[1]} {bars[2]} {bars[3]} {bars[4]} "
                    f"{score:>7.2f} {level:>6}"
                )

            # Pillar average
            pillar_score = pillar["score"]
            pillar_level = pillar["level"]
            lines.append("-" * 80)
            pillar_label = f"  {pillar['name'][:30]} (Pillar Avg)"
            lines.append(
                f"{pillar_label:<35} {'':>4} {'':>4} {'':>4} {'':>4} {'':>4} "
                f"{pillar_score:>7.2f} {pillar_level:>6}"
            )
            lines.append("")

        # Overall
        lines.append("=" * 80)
        overall = self.results["overall"]
        lines.append(
            f"{'OVERALL':<35} {'':>4} {'':>4} {'':>4} {'':>4} {'':>4} "
            f"{overall['score']:>7.2f} {overall['level']:>6}"
        )
        lines.append("")

        # Legend
        lines.append("Legend: █ = Met  ▓ = Mostly Met  ▒ = Partially Met  ░ = Not Met")
        lines.append("Color:  Red (<2.0)  Yellow (2.0-2.9)  Light Green (3.0-3.9)  Green (4.0+)")
        lines.append("")

        return "\n".join(lines)

    def _generate_recommendations(self) -> list[str]:
        """Generate top recommendations based on results."""
        recs = []
        gaps = self.results["gap_analysis"]

        for gap in gaps["critical_gaps"][:3]:
            recs.append(
                f"Address critical gap in {gap['domain_id']} {gap['domain_name']} "
                f"(current: {gap['score']}, target: 2.0+)"
            )

        for gap in gaps["high_gaps"][:2]:
            recs.append(
                f"Improve {gap['domain_id']} {gap['domain_name']} "
                f"(current: {gap['score']}, target: 3.0+)"
            )

        if not recs:
            recs.append("Maintain current maturity level and focus on continuous improvement")
            recs.append("Benchmark against industry leaders to identify optimization opportunities")
            recs.append("Share best practices with industry community")

        return recs

    def generate_json_report(self) -> str:
        """Generate JSON report."""
        return json.dumps(self.results, indent=2)

    def generate_executive_summary(self) -> str:
        """Generate executive summary."""
        lines = []
        r = self.results
        overall = r["overall"]

        lines.append("EXECUTIVE SUMMARY")
        lines.append("=" * 50)
        lines.append("")
        lines.append(f"Overall Maturity: {overall['score']}/5.0 (Level {overall['level']} - {LEVEL_NAMES[overall['level']]})")
        lines.append(f"Normalized Score: {overall['normalized']}/100")
        lines.append("")

        lines.append("Pillar Scores:")
        for p in r["pillars"]:
            lines.append(f"  • {p['name']}: {p['score']} (L{p['level']})")
        lines.append("")

        gaps = r["gap_analysis"]
        lines.append(f"Critical Gaps: {len(gaps['critical_gaps'])}")
        lines.append(f"High Priority Gaps: {len(gaps['high_gaps'])}")
        lines.append(f"Strengths: {len(gaps['strengths'])}")
        lines.append("")

        lines.append("Top 3 Recommendations:")
        for i, rec in enumerate(self._generate_recommendations()[:3], 1):
            lines.append(f"  {i}. {rec}")

        return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# DEMO / SAMPLE DATA
# ─────────────────────────────────────────────────────────────────────────────

def generate_demo_responses(questionnaire: dict) -> dict[str, int]:
    """Generate demo responses for testing."""
    import random
    random.seed(42)

    responses = {}
    for pillar in questionnaire["pillars"]:
        for domain in pillar["domains"]:
            for sub_dim in domain["sub_dimensions"]:
                for q in sub_dim["questions"]:
                    # Generate realistic scores with some variation
                    base = random.randint(1, 4)
                    # Agent-specific domains tend to be lower
                    if domain["id"] in ("3.3", "3.4"):
                        base = max(1, base - 1)
                    # Governance tends to be higher
                    if domain["id"] in ("1.1", "1.2"):
                        base = min(5, base + 1)
                    responses[q["id"]] = base

    return responses


def generate_response_template(questionnaire: dict) -> dict:
    """Generate a blank response template."""
    template = {}
    for pillar in questionnaire["pillars"]:
        for domain in pillar["domains"]:
            for sub_dim in domain["sub_dimensions"]:
                for q in sub_dim["questions"]:
                    template[q["id"]] = None
    return template


# ─────────────────────────────────────────────────────────────────────────────
# MAIN ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="GRC_Claw U-AIGMM Assessment Automation Engine"
    )
    parser.add_argument(
        "--questionnaire",
        default="grc_claw_questionnaire.json",
        help="Path to questionnaire JSON file",
    )
    parser.add_argument(
        "--responses",
        help="Path to responses JSON file",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run with demo data",
    )
    parser.add_argument(
        "--generate-responses",
        action="store_true",
        help="Generate blank response template",
    )
    parser.add_argument(
        "--output",
        default="assessment_report.txt",
        help="Output file path",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json", "heatmap", "executive", "all"],
        default="all",
        help="Report format",
    )
    parser.add_argument(
        "--weight-profile",
        choices=["default", "regulated", "startup", "enterprise"],
        default="default",
        help="Weight profile to use",
    )

    args = parser.parse_args()

    # Load questionnaire
    qpath = Path(args.questionnaire)
    if not qpath.exists():
        print(f"Error: Questionnaire file not found: {qpath}")
        sys.exit(1)

    with open(qpath) as f:
        questionnaire = json.load(f)

    # Generate response template
    if args.generate_responses:
        template = generate_response_template(questionnaire)
        output_path = args.output or "responses_template.json"
        with open(output_path, "w") as f:
            json.dump(template, f, indent=2)
        print(f"Response template generated: {output_path}")
        print(f"Total questions: {len(template)}")
        return

    # Get responses
    if args.demo:
        responses = generate_demo_responses(questionnaire)
        print("Running assessment with demo data...")
    elif args.responses:
        rpath = Path(args.responses)
        if not rpath.exists():
            print(f"Error: Responses file not found: {rpath}")
            sys.exit(1)
        with open(rpath) as f:
            responses = json.load(f)
        print(f"Loaded responses: {len(responses)} questions")
    else:
        print("Error: No responses provided. Use --demo or --responses <file>")
        sys.exit(1)

    # Process assessment
    config = {"weight_profile": args.weight_profile}
    engine = MaturityScoringEngine(config)
    processor = AssessmentProcessor(questionnaire, engine)
    results = processor.process(responses)

    # Generate reports
    reporter = ReportGenerator(results)

    # Determine base path without extension
    output_base = args.output
    for ext in [".txt", ".json", ".md"]:
        if output_base.endswith(ext):
            output_base = output_base[:-len(ext)]
            break

    if args.format in ("text", "all"):
        report = reporter.generate_text_report()
        text_path = output_base + "_report.txt"
        with open(text_path, "w") as f:
            f.write(report)
        print(f"Text report: {text_path}")
        print(report)

    if args.format in ("heatmap", "all"):
        heatmap = reporter.generate_heat_map()
        heat_path = output_base + "_heatmap.txt"
        with open(heat_path, "w") as f:
            f.write(heatmap)
        print(f"Heat map: {heat_path}")
        print(heatmap)

    if args.format in ("executive", "all"):
        exec_summary = reporter.generate_executive_summary()
        exec_path = output_base + "_executive.txt"
        with open(exec_path, "w") as f:
            f.write(exec_summary)
        print(f"Executive summary: {exec_path}")
        print(exec_summary)

    if args.format in ("json", "all"):
        json_report = reporter.generate_json_report()
        json_path = output_base + "_report.json"
        with open(json_path, "w") as f:
            f.write(json_report)
        print(f"JSON report: {json_path}")

    # Print summary
    print("\n" + "=" * 50)
    print("ASSESSMENT COMPLETE")
    print("=" * 50)
    print(f"Overall Score: {results['overall']['score']}/5.0")
    print(f"Overall Level: {results['overall']['level']} - {LEVEL_NAMES[results['overall']['level']]}")
    print(f"Normalized: {results['overall']['normalized']}/100")
    print(f"Critical Gaps: {len(results['gap_analysis']['critical_gaps'])}")
    print(f"Strengths: {len(results['gap_analysis']['strengths'])}")


if __name__ == "__main__":
    main()
