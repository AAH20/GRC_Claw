"""
GRC_Claw Incident Severity Auto-Classification (§14 of GRC-AIM-001)

Implements the multi-factor auto-classification system:
    • Weighted severity scoring (§14.3)
    • Auto-classification decision matrix (§14.4)
    • Override rules for regulatory/business-critical conditions (§14.5)
    • Feedback loop for model improvement (§14.7)
    • Rule-based impact × likelihood classification (§4.2)

Scoring formula:
    Severity_Score = Σ(Factor_i × Weight_i × Normalized_Value_i)

    Score ≥ 0.85 → S1 (Critical)
    Score 0.70–0.84 → S2 (High)
    Score 0.50–0.69 → S3 (Medium)
    Score 0.30–0.49 → S4 (Low)
    Score < 0.30 → S5 (Informational)
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Optional

from .models import DetectionSignal, Incident
from .taxonomy import (
    IncidentCategory,
    Severity,
    MINIMUM_SEVERITY,
    CATEGORY_MINIMUM_SEVERITY,
)


# ═══════════════════════════════════════════════════════════════════════════════
# Classification Factors (§14.2)
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class ClassificationFactor:
    """A single classification factor with weight and normalized value."""
    name: str
    weight: float  # 0.0–1.0, all weights sum to 1.0
    value: float   # normalized 0.0–1.0
    description: str = ""

    @property
    def weighted_score(self) -> float:
        return self.weight * self.value


@dataclass
class ClassificationResult:
    """Result of severity auto-classification."""
    incident_id: str
    severity: Severity
    confidence: float
    score: float
    factors: list[ClassificationFactor] = field(default_factory=list)
    overrides_applied: list[str] = field(default_factory=list)
    auto_apply: bool = False
    requires_human_review: bool = False
    explanation: str = ""
    timestamp: str = ""


# ═══════════════════════════════════════════════════════════════════════════════
# Severity Classification Engine
# ═══════════════════════════════════════════════════════════════════════════════

class SeverityClassificationEngine:
    """
    Multi-factor auto-classification engine (§14.1).

    Combines signal-based, asset-based, and historical factors to produce
    a weighted severity score with confidence calibration.
    """

    # Category base severity scores (normalized 0.0–1.0)
    CATEGORY_BASE_SEVERITY: dict[IncidentCategory, float] = {
        IncidentCategory.DATA_LEAKAGE: 0.75,
        IncidentCategory.HARMFUL_OUTPUT: 0.75,
        IncidentCategory.WRONG_ACTION: 0.70,
        IncidentCategory.HALLUCINATION: 0.50,
        IncidentCategory.PROMPT_INJECTION: 0.80,
        IncidentCategory.MODEL_POISONING: 0.85,
        IncidentCategory.SUPPLY_CHAIN: 0.55,
        IncidentCategory.AGENT_MISBEHAVIOR: 0.85,
    }

    # Override rules (§14.5)
    OVERRIDE_RULES: list[dict[str, Any]] = [
        {"name": "Regulatory Trigger", "condition": "pii_breach_gt_1000", "min_severity": Severity.S2_HIGH},
        {"name": "Active Exploitation", "condition": "active_attack_production", "min_severity": Severity.S2_HIGH},
        {"name": "Physical Harm", "condition": "physical_harm", "min_severity": Severity.S1_CRITICAL},
        {"name": "Critical Infrastructure", "condition": "critical_infrastructure", "min_severity": Severity.S1_CRITICAL},
        {"name": "Mass Impact", "condition": "mass_impact_10000", "min_severity": Severity.S1_CRITICAL},
        {"name": "Media Attention", "condition": "media_attention", "min_severity": Severity.S2_HIGH},
        {"name": "Executive Involvement", "condition": "executive_notified", "min_severity": Severity.S2_HIGH},
        {"name": "Cross-Border", "condition": "cross_border", "min_severity": Severity.S2_HIGH},
    ]

    def __init__(self) -> None:
        self._historical_incidents: list[dict[str, Any]] = []
        self._custom_scorers: dict[str, Callable[[DetectionSignal, Optional[Incident]], float]] = {}

    def register_historical_incident(self, incident_data: dict[str, Any]) -> None:
        self._historical_incidents.append(incident_data)

    def register_custom_scorer(
        self, factor_name: str,
        scorer: Callable[[DetectionSignal, Optional[Incident]], float]
    ) -> None:
        self._custom_scorers[factor_name] = scorer

    def classify(
        self,
        signal: DetectionSignal,
        incident: Optional[Incident] = None,
    ) -> ClassificationResult:
        """
        Run full multi-factor classification on a detection signal.

        Returns a ClassificationResult with severity, confidence, and explanation.
        """
        factors = self._compute_factors(signal, incident)
        raw_score = sum(f.weighted_score for f in factors)

        # Apply minimum severity from taxonomy
        min_sev = self._get_minimum_severity(signal)
        if min_sev:
            min_score = self._severity_to_score(min_sev)
            if raw_score < min_score:
                raw_score = min_score

        # Apply override rules
        overrides = self._apply_overrides(signal, incident)
        for override in overrides:
            override_score = self._severity_to_score(override["min_severity"])
            if raw_score < override_score:
                raw_score = override_score

        # Map score to severity
        severity = self._score_to_severity(raw_score)

        # Compute confidence based on factor agreement
        confidence = self._compute_confidence(factors, signal)

        # Determine auto-apply vs human review (§14.4)
        auto_apply, requires_review = self._decision_matrix(confidence, severity, signal)

        # Generate explanation
        explanation = self._generate_explanation(factors, severity, overrides)

        return ClassificationResult(
            incident_id=incident.incident_id if incident else signal.signal_id,
            severity=severity,
            confidence=confidence,
            score=raw_score,
            factors=factors,
            overrides_applied=[o["name"] for o in overrides],
            auto_apply=auto_apply,
            requires_human_review=requires_review,
            explanation=explanation,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    def _compute_factors(
        self, signal: DetectionSignal, incident: Optional[Incident]
    ) -> list[ClassificationFactor]:
        """Compute all 12 classification factors (§14.2)."""
        factors: list[ClassificationFactor] = []

        # ── Signal-Based Factors (§14.2.1) ──

        # 1. Incident Category (20%)
        cat_score = 0.5
        if signal.category:
            cat_score = self.CATEGORY_BASE_SEVERITY.get(signal.category, 0.5)
        factors.append(ClassificationFactor(
            "incident_category", 0.20, cat_score,
            f"Category: {signal.category.value if signal.category else 'unknown'}"
        ))

        # 2. Detection Confidence (15%)
        factors.append(ClassificationFactor(
            "detection_confidence", 0.15, signal.confidence,
            f"Signal confidence: {signal.confidence:.2f}"
        ))

        # 3. Signal Velocity (10%)
        velocity = signal.raw_data.get("signal_velocity", 0.5)
        factors.append(ClassificationFactor(
            "signal_velocity", 0.10, min(1.0, velocity),
            f"Signal velocity: {velocity:.2f}"
        ))

        # 4. Signal Diversity (10%)
        diversity = signal.raw_data.get("signal_diversity", 0.5)
        factors.append(ClassificationFactor(
            "signal_diversity", 0.10, min(1.0, diversity),
            f"Signal diversity: {diversity:.2f}"
        ))

        # 5. Corroboration (15%)
        corroboration = signal.raw_data.get("corroboration", 0.5)
        factors.append(ClassificationFactor(
            "corroboration", 0.15, min(1.0, corroboration),
            f"Corroboration: {corroboration:.2f}"
        ))

        # ── Asset-Based Factors (§14.2.2) ──

        # 6. Asset Criticality (15%)
        criticality = signal.raw_data.get("asset_criticality", 0.5)
        factors.append(ClassificationFactor(
            "asset_criticality", 0.15, min(1.0, criticality),
            f"Asset criticality: {criticality:.2f}"
        ))

        # 7. User Impact (10%)
        user_impact = signal.raw_data.get("user_impact", 0.5)
        factors.append(ClassificationFactor(
            "user_impact", 0.10, min(1.0, user_impact),
            f"User impact: {user_impact:.2f}"
        ))

        # 8. Data Sensitivity (10%)
        sensitivity = signal.raw_data.get("data_sensitivity", 0.5)
        factors.append(ClassificationFactor(
            "data_sensitivity", 0.10, min(1.0, sensitivity),
            f"Data sensitivity: {sensitivity:.2f}"
        ))

        # 9. Environment (5%)
        env_score = {"production": 1.0, "staging": 0.6, "development": 0.3, "edge": 0.8}.get(
            signal.environment, 0.5
        )
        factors.append(ClassificationFactor(
            "environment", 0.05, env_score,
            f"Environment: {signal.environment}"
        ))

        # ── Historical Factors (§14.2.3) ──

        # 10. Similar Incidents (10%)
        similar_score = self._score_similar_incidents(signal)
        factors.append(ClassificationFactor(
            "similar_incidents", 0.10, similar_score,
            f"Similar incidents score: {similar_score:.2f}"
        ))

        # 11. Recurrence (5%)
        recurrence = signal.raw_data.get("recurrence", 0.0)
        factors.append(ClassificationFactor(
            "recurrence", 0.05, min(1.0, recurrence),
            f"Recurrence: {recurrence:.2f}"
        ))

        # 12. Trend (5%)
        trend = signal.raw_data.get("trend", 0.5)
        factors.append(ClassificationFactor(
            "trend", 0.05, min(1.0, trend),
            f"Trend: {trend:.2f}"
        ))

        return factors

    def _get_minimum_severity(self, signal: DetectionSignal) -> Optional[Severity]:
        """Get minimum severity from taxonomy (§4.4)."""
        if signal.subcategory_code:
            return MINIMUM_SEVERITY.get(signal.subcategory_code)
        if signal.category:
            return CATEGORY_MINIMUM_SEVERITY.get(signal.category)
        return None

    def _apply_overrides(
        self, signal: DetectionSignal, incident: Optional[Incident]
    ) -> list[dict[str, Any]]:
        """Apply override rules (§14.5)."""
        applied = []
        raw = signal.raw_data

        if raw.get("pii_breach_gt_1000", False):
            applied.append(self.OVERRIDE_RULES[0])
        if raw.get("active_attack_production", False):
            applied.append(self.OVERRIDE_RULES[1])
        if raw.get("physical_harm", False):
            applied.append(self.OVERRIDE_RULES[2])
        if raw.get("critical_infrastructure", False):
            applied.append(self.OVERRIDE_RULES[3])
        if raw.get("mass_impact_10000", False):
            applied.append(self.OVERRIDE_RULES[4])
        if raw.get("media_attention", False):
            applied.append(self.OVERRIDE_RULES[5])
        if raw.get("executive_notified", False):
            applied.append(self.OVERRIDE_RULES[6])
        if raw.get("cross_border", False):
            applied.append(self.OVERRIDE_RULES[7])

        return applied

    def _score_similar_incidents(self, signal: DetectionSignal) -> float:
        """Score based on historically similar incidents."""
        if not self._historical_incidents or not signal.category:
            return 0.5

        similar = [
            i for i in self._historical_incidents
            if i.get("category") == signal.category.value
        ]
        if not similar:
            return 0.5

        # Average severity of similar incidents
        severity_scores = []
        for inc in similar:
            sev = inc.get("severity", "S3")
            try:
                severity_scores.append(self._severity_to_score(Severity(sev)))
            except ValueError:
                pass

        return statistics.mean(severity_scores) if severity_scores else 0.5

    def _compute_confidence(
        self, factors: list[ClassificationFactor], signal: DetectionSignal
    ) -> float:
        """Compute classification confidence based on factor agreement."""
        if not factors:
            return 0.5

        # Confidence is higher when factors agree (low variance)
        scores = [f.weighted_score for f in factors]
        if len(scores) > 1:
            variance = statistics.variance(scores)
            agreement = max(0.0, 1.0 - variance * 10)
        else:
            agreement = 0.5

        # Blend with signal confidence
        return 0.6 * signal.confidence + 0.4 * agreement

    def _decision_matrix(
        self, confidence: float, severity: Severity, signal: DetectionSignal
    ) -> tuple[bool, bool]:
        """
        Auto-classification decision matrix (§14.4).

        Returns (auto_apply, requires_human_review).
        """
        if confidence >= 0.95:
            return True, False  # Auto-apply, no human review
        elif confidence >= 0.80:
            return True, True   # Auto-apply, notify human for confirmation
        elif confidence >= 0.60:
            return False, True  # Queue for human triage
        else:
            return False, False  # Log for pattern analysis

    def _generate_explanation(
        self, factors: list[ClassificationFactor], severity: Severity,
        overrides: list[dict[str, Any]]
    ) -> str:
        """Generate human-readable explanation."""
        top_factors = sorted(factors, key=lambda f: f.weighted_score, reverse=True)[:3]
        parts = [f"Severity {severity.value} based on:"]
        for f in top_factors:
            parts.append(f"  • {f.description} (weight: {f.weight:.0%})")
        if overrides:
            parts.append(f"Overrides applied: {', '.join(o['name'] for o in overrides)}")
        return "\n".join(parts)

    @staticmethod
    def _score_to_severity(score: float) -> Severity:
        """Map normalized score to severity level (§14.3)."""
        if score >= 0.85:
            return Severity.S1_CRITICAL
        elif score >= 0.70:
            return Severity.S2_HIGH
        elif score >= 0.50:
            return Severity.S3_MEDIUM
        elif score >= 0.30:
            return Severity.S4_LOW
        else:
            return Severity.S5_INFORMATIONAL

    @staticmethod
    def _severity_to_score(severity: Severity) -> float:
        """Convert severity to normalized score."""
        mapping = {
            Severity.S1_CRITICAL: 0.90,
            Severity.S2_HIGH: 0.75,
            Severity.S3_MEDIUM: 0.55,
            Severity.S4_LOW: 0.35,
            Severity.S5_INFORMATIONAL: 0.15,
        }
        return mapping.get(severity, 0.5)


# ═══════════════════════════════════════════════════════════════════════════════
# Rule-Based Classification (§4.2)
# ═══════════════════════════════════════════════════════════════════════════════

class RuleBasedClassifier:
    """
    Rule-based impact × likelihood classification (§4.2).

    Used as a fallback or cross-check for the ML-based classifier.
    """

    # Impact × Likelihood matrix (§4.2)
    MATRIX: dict[tuple[str, str], Severity] = {
        ("severe", "certain"): Severity.S1_CRITICAL,
        ("severe", "likely"): Severity.S1_CRITICAL,
        ("severe", "possible"): Severity.S2_HIGH,
        ("severe", "unlikely"): Severity.S3_MEDIUM,
        ("major", "certain"): Severity.S1_CRITICAL,
        ("major", "likely"): Severity.S2_HIGH,
        ("major", "possible"): Severity.S3_MEDIUM,
        ("major", "unlikely"): Severity.S4_LOW,
        ("moderate", "certain"): Severity.S2_HIGH,
        ("moderate", "likely"): Severity.S3_MEDIUM,
        ("moderate", "possible"): Severity.S4_LOW,
        ("moderate", "unlikely"): Severity.S4_LOW,
        ("minor", "certain"): Severity.S3_MEDIUM,
        ("minor", "likely"): Severity.S4_LOW,
        ("minor", "possible"): Severity.S4_LOW,
        ("minor", "unlikely"): Severity.S5_INFORMATIONAL,
        ("negligible", "certain"): Severity.S4_LOW,
        ("negligible", "likely"): Severity.S4_LOW,
        ("negligible", "possible"): Severity.S5_INFORMATIONAL,
        ("negligible", "unlikely"): Severity.S5_INFORMATIONAL,
    }

    @classmethod
    def classify(cls, impact: str, likelihood: str) -> Severity:
        """Classify based on impact and likelihood."""
        return cls.MATRIX.get((impact.lower(), likelihood.lower()), Severity.S3_MEDIUM)

    @classmethod
    def assess_impact(
        cls,
        individuals_affected: int = 0,
        records_affected: int = 0,
        financial_loss_usd: float = 0.0,
        system_compromise: str = "none",
    ) -> str:
        """Assess impact level based on criteria (§4.3)."""
        if (individuals_affected > 0 and financial_loss_usd > 10_000_000) or records_affected > 10_000:
            return "severe"
        elif financial_loss_usd > 1_000_000 or records_affected > 1_000:
            return "major"
        elif financial_loss_usd > 100_000 or records_affected > 100:
            return "moderate"
        elif financial_loss_usd > 10_000 or records_affected > 0:
            return "minor"
        else:
            return "negligible"


# ═══════════════════════════════════════════════════════════════════════════════
# Feedback Loop (§14.7)
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class ClassificationFeedback:
    """Feedback record for model improvement."""
    incident_id: str
    auto_classified_severity: Severity
    human_assigned_severity: Severity
    timestamp: str = ""
    analyst_notes: str = ""


class ClassificationFeedbackLoop:
    """
    Severity classification feedback loop (§14.7).

    Records discrepancies between auto-classified and human-assigned severity
    for model retraining.
    """

    def __init__(self) -> None:
        self._feedback_records: list[ClassificationFeedback] = []

    def record_feedback(
        self,
        incident_id: str,
        auto_severity: Severity,
        human_severity: Severity,
        analyst_notes: str = "",
    ) -> ClassificationFeedback:
        """Record a feedback entry."""
        fb = ClassificationFeedback(
            incident_id=incident_id,
            auto_classified_severity=auto_severity,
            human_assigned_severity=human_severity,
            timestamp=datetime.now(timezone.utc).isoformat(),
            analyst_notes=analyst_notes,
        )
        self._feedback_records.append(fb)
        return fb

    def get_discrepancies(self) -> list[ClassificationFeedback]:
        """Get all cases where auto-classification differed from human assignment."""
        return [
            fb for fb in self._feedback_records
            if fb.auto_classified_severity != fb.human_assigned_severity
        ]

    def get_accuracy(self) -> dict[str, float]:
        """Compute classification accuracy metrics."""
        if not self._feedback_records:
            return {"exact_match": 0.0, "within_one_level": 0.0, "total": 0}

        exact = sum(
            1 for fb in self._feedback_records
            if fb.auto_classified_severity == fb.human_assigned_severity
        )
        within_one = sum(
            1 for fb in self._feedback_records
            if abs(
                int(fb.auto_classified_severity.value[1]) - int(fb.human_assigned_severity.value[1])
            ) <= 1
        )
        total = len(self._feedback_records)
        return {
            "exact_match": exact / total,
            "within_one_level": within_one / total,
            "total": total,
        }

    def get_retraining_data(self) -> list[dict[str, Any]]:
        """Export feedback data for model retraining."""
        return [
            {
                "incident_id": fb.incident_id,
                "auto_severity": fb.auto_classified_severity.value,
                "human_severity": fb.human_assigned_severity.value,
                "timestamp": fb.timestamp,
                "notes": fb.analyst_notes,
            }
            for fb in self._feedback_records
        ]
