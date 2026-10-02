"""Ensemble lead scoring agent (v2).

Combines multiple scoring models using weighted ensemble approach
to produce more accurate and robust lead scores with confidence
intervals and model explainability.
"""
from __future__ import annotations

import math
import time
from datetime import UTC, datetime
from enum import StrEnum
from typing import TYPE_CHECKING, Any

import structlog
from pydantic import BaseModel, Field

from lead_scorer.agents.scoring import LeadGrade, ScoringResult

if TYPE_CHECKING:
    from lead_scorer.agents.evidence import EvidenceResult
    from lead_scorer.agents.research import ResearchResult

logger = structlog.get_logger(__name__)


class ModelWeight(BaseModel):
    """Weight configuration for an ensemble model."""

    model_name: str
    weight: float = Field(ge=0.0, le=1.0)
    enabled: bool = True


class EnsembleComponent(BaseModel):
    """A single component from the ensemble scoring."""

    name: str
    model_scores: dict[str, float] = Field(default_factory=dict)
    ensemble_score: float = Field(ge=0.0, le=1.0)
    weight: float = Field(ge=0.0, le=1.0)
    weighted_score: float = Field(ge=0.0, le=1.0)
    variance: float = Field(ge=0.0, default=0.0)
    confidence_interval: tuple[float, float] = (0.0, 0.0)


class EnsembleScoringResult(BaseModel):
    """Result from the ensemble scoring agent."""

    lead_id: str
    total_score: float = Field(ge=0.0, le=100.0)
    grade: LeadGrade
    components: list[EnsembleComponent] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    score_std_dev: float = Field(ge=0.0, default=0.0)
    model_contributions: dict[str, float] = Field(default_factory=dict)
    scored_at: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class ScoringModelType(StrEnum):
    """Types of scoring models in the ensemble."""

    FIRMOGRAPHIC = "firmographic"
    TECHNOGRAPHIC = "technographic"
    ENGAGEMENT = "engagement"
    INTENT = "intent"
    TIMING = "timing"
    BEHAVIORAL = "behavioral"
    PREDICTIVE = "predictive"


class LeadScoringV2Agent:
    """Ensemble scoring agent that combines multiple scoring models.

    Uses a weighted ensemble approach where each model contributes
    a score, and the final score is a weighted combination. Provides
    confidence intervals and model explainability.
    """

    def __init__(
        self,
        model_weights: dict[str, float] | None = None,
        thresholds: dict[str, int] | None = None,
        timeout_seconds: int = 45,
        max_retries: int = 1,
        min_models: int = 2,
    ) -> None:
        """Initialize the ensemble scoring agent.

        Args:
            model_weights: Weights for each model in the ensemble.
            thresholds: Grade thresholds (hot, warm, cold).
            timeout_seconds: Maximum time allowed for scoring.
            max_retries: Number of retry attempts on failure.
            min_models: Minimum number of models required for ensemble.
        """
        self.model_weights = model_weights or {
            "firmographic": 0.20,
            "technographic": 0.10,
            "engagement": 0.25,
            "intent": 0.20,
            "timing": 0.10,
            "behavioral": 0.10,
            "predictive": 0.05,
        }
        self.thresholds = thresholds or {"hot": 80, "warm": 50, "cold": 0}
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.min_models = min_models
        self._validate_weights()

    def _validate_weights(self) -> None:
        """Validate that model weights sum to approximately 1.0."""
        total = sum(self.model_weights.values())
        if not 0.99 <= total <= 1.01:
            raise ValueError(f"Model weights must sum to 1.0, got {total}")

    async def score(
        self,
        lead_id: str,
        research: ResearchResult | None = None,
        evidence: EvidenceResult | None = None,
        behavioral_signals: dict[str, Any] | None = None,
        predictive_features: dict[str, Any] | None = None,
    ) -> EnsembleScoringResult:
        """Compute an ensemble lead score.

        Args:
            lead_id: Unique identifier for the lead.
            research: Optional research result for firmographic/technographic data.
            evidence: Optional evidence result for engagement/intent data.
            behavioral_signals: Optional behavioral signals.
            predictive_features: Optional predictive model features.

        Returns:
            EnsembleScoringResult with total score, grade, and component breakdown.

        Raises:
            ValueError: If lead_id is empty.
            TimeoutError: If scoring exceeds timeout.
        """
        if not lead_id:
            raise ValueError("lead_id is required")

        logger.info("ensemble_scoring_started", lead_id=lead_id)
        start_time = time.monotonic()

        try:
            # Compute individual model scores
            model_scores = self._compute_model_scores(
                research, evidence, behavioral_signals, predictive_features
            )

            # Build ensemble components
            components = self._build_components(model_scores)

            # Compute total score
            total_score = sum(c.weighted_score * 100 for c in components)
            total_score = round(min(max(total_score, 0.0), 100.0), 2)

            # Compute grade
            grade = self._determine_grade(total_score)

            # Compute confidence and variance
            confidence = self._compute_confidence(model_scores, components)
            score_std_dev = self._compute_std_dev(components)

            # Compute model contributions
            model_contributions = self._compute_model_contributions(components)

            elapsed = time.monotonic() - start_time
            if elapsed > self.timeout_seconds:
                raise TimeoutError(f"Ensemble scoring timed out after {elapsed:.1f}s")

            result = EnsembleScoringResult(
                lead_id=lead_id,
                total_score=total_score,
                grade=grade,
                components=components,
                confidence=confidence,
                score_std_dev=score_std_dev,
                model_contributions=model_contributions,
                scored_at=datetime.now(UTC).isoformat(),
                metadata={
                    "elapsed_seconds": elapsed,
                    "models_used": list(model_scores.keys()),
                    "ensemble_method": "weighted_average",
                },
            )

            logger.info(
                "ensemble_lead_scored",
                lead_id=lead_id,
                score=total_score,
                grade=grade.value,
                confidence=confidence,
                std_dev=score_std_dev,
            )
            return result

        except Exception as exc:
            logger.error("ensemble_scoring_failed", lead_id=lead_id, error=str(exc))
            raise

    def _compute_model_scores(
        self,
        research: ResearchResult | None,
        evidence: EvidenceResult | None,
        behavioral_signals: dict[str, Any] | None,
        predictive_features: dict[str, Any] | None,
    ) -> dict[str, float]:
        """Compute scores from each individual model.

        Returns:
            Dictionary mapping model name to its raw score (0-1).
        """
        scores: dict[str, float] = {}

        # Firmographic model
        firm_score = 0.0
        if research:
            firm = research.firmographic
            if firm.company_size > 0:
                firm_score += min(firm.company_size / 500, 1.0) * 0.4
            if firm.industry:
                firm_score += 0.3
            if firm.revenue_range:
                firm_score += 0.3
        scores["firmographic"] = min(firm_score, 1.0)

        # Technographic model
        tech_score = 0.0
        if research:
            tech = research.technographic
            if tech.technologies:
                tech_score += min(len(tech.technologies) / 5, 1.0) * 0.5
            if tech.ssl_enabled:
                tech_score += 0.2
            if tech.hosting_provider:
                tech_score += 0.3
        scores["technographic"] = min(tech_score, 1.0)

        # Engagement model
        eng_score = 0.0
        if evidence:
            eng_score = evidence.engagement_score
        scores["engagement"] = eng_score

        # Intent model
        intent_score = 0.0
        if evidence:
            intent_score = evidence.intent_score
        scores["intent"] = intent_score

        # Timing model
        timing_score = 0.5  # Default
        if evidence and evidence.recency_score > 0:
            timing_score = evidence.recency_score
        scores["timing"] = timing_score

        # Behavioral model
        behavioral_score = 0.0
        if behavioral_signals:
            behavioral_score = self._compute_behavioral_score(behavioral_signals)
        scores["behavioral"] = behavioral_score

        # Predictive model
        predictive_score = 0.0
        if predictive_features:
            predictive_score = self._compute_predictive_score(predictive_features)
        scores["predictive"] = predictive_score

        return scores

    def _compute_behavioral_score(self, signals: dict[str, Any]) -> float:
        """Compute behavioral score from signals.

        Args:
            signals: Dictionary of behavioral signals.

        Returns:
            Behavioral score between 0.0 and 1.0.
        """
        score = 0.0

        # Page views
        page_views = signals.get("page_views_7d", 0)
        score += min(page_views / 20, 1.0) * 0.2

        # Content downloads
        downloads = signals.get("content_downloads_30d", 0)
        score += min(downloads / 3, 1.0) * 0.3

        # Email engagement
        email_opens = signals.get("email_opens_30d", 0)
        email_clicks = signals.get("email_clicks_30d", 0)
        score += min(email_opens / 10, 1.0) * 0.15
        score += min(email_clicks / 5, 1.0) * 0.2

        # Social engagement
        social = signals.get("social_engagements_30d", 0)
        score += min(social / 10, 1.0) * 0.15

        return min(score, 1.0)

    def _compute_predictive_score(self, features: dict[str, Any]) -> float:
        """Compute predictive score from features.

        In production, this would use a trained ML model (e.g., XGBoost,
        logistic regression) to predict conversion probability.

        Args:
            features: Dictionary of predictive features.

        Returns:
            Predictive score between 0.0 and 1.0.
        """
        score = 0.0

        # Historical conversion rate for similar leads
        historical_rate = features.get("historical_conversion_rate", 0.0)
        score += historical_rate * 0.3

        # Lead source quality
        source_quality = features.get("source_quality_score", 0.5)
        score += source_quality * 0.2

        # Company fit score
        company_fit = features.get("company_fit_score", 0.5)
        score += company_fit * 0.3

        # Engagement velocity
        velocity = features.get("engagement_velocity", 0.0)
        score += min(velocity, 1.0) * 0.2

        return min(score, 1.0)

    def _build_components(
        self, model_scores: dict[str, float]
    ) -> list[EnsembleComponent]:
        """Build ensemble components from individual model scores.

        Args:
            model_scores: Dictionary mapping model name to raw score.

        Returns:
            List of EnsembleComponent objects.
        """
        components: list[EnsembleComponent] = []

        for model_name, raw_score in model_scores.items():
            weight = self.model_weights.get(model_name, 0.0)
            if weight == 0.0:
                continue

            # Compute variance across models (simplified)
            variance = self._compute_model_variance(model_name, model_scores)

            # Compute confidence interval (95%)
            std_err = math.sqrt(variance) if variance > 0 else 0.05
            ci_lower = max(0.0, raw_score - 1.96 * std_err)
            ci_upper = min(1.0, raw_score + 1.96 * std_err)

            component = EnsembleComponent(
                name=model_name,
                model_scores={model_name: raw_score},
                ensemble_score=raw_score,
                weight=weight,
                weighted_score=raw_score * weight,
                variance=round(variance, 4),
                confidence_interval=(round(ci_lower, 4), round(ci_upper, 4)),
            )
            components.append(component)

        return components

    def _compute_model_variance(
        self, model_name: str, all_scores: dict[str, float]
    ) -> float:
        """Compute variance for a model's score.

        Uses the spread of all model scores as a proxy for uncertainty.

        Args:
            model_name: The model name.
            all_scores: All model scores.

        Returns:
            Variance value.
        """
        if len(all_scores) < 2:
            return 0.0

        values = list(all_scores.values())
        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        return variance

    def _determine_grade(self, score: float) -> LeadGrade:
        """Determine lead grade from total score."""
        if score >= self.thresholds["hot"]:
            return LeadGrade.HOT
        if score >= self.thresholds["warm"]:
            return LeadGrade.WARM
        return LeadGrade.COLD

    def _compute_confidence(
        self, model_scores: dict[str, float], components: list[EnsembleComponent]
    ) -> float:
        """Compute overall confidence in the ensemble score.

        Based on:
        - Number of models that contributed
        - Agreement between models (low variance = high confidence)
        - Data completeness

        Returns:
            Confidence score between 0.0 and 1.0.
        """
        if not model_scores:
            return 0.0

        # Factor 1: Number of models (more models = higher confidence)
        model_count_factor = min(len(model_scores) / len(self.model_weights), 1.0)

        # Factor 2: Model agreement (low variance = high confidence)
        if components:
            avg_variance = sum(c.variance for c in components) / len(components)
            agreement_factor = max(0.0, 1.0 - avg_variance * 10)
        else:
            agreement_factor = 0.0

        # Factor 3: Data completeness (non-zero scores)
        non_zero = sum(1 for s in model_scores.values() if s > 0)
        completeness_factor = non_zero / len(model_scores)

        # Weighted combination
        confidence = (
            model_count_factor * 0.3
            + agreement_factor * 0.4
            + completeness_factor * 0.3
        )
        return round(min(max(confidence, 0.0), 1.0), 2)

    def _compute_std_dev(self, components: list[EnsembleComponent]) -> float:
        """Compute standard deviation of the ensemble score.

        Args:
            components: List of ensemble components.

        Returns:
            Standard deviation value.
        """
        if not components:
            return 0.0

        # Weighted variance
        total_weight = sum(c.weight for c in components)
        if total_weight == 0:
            return 0.0

        weighted_mean = sum(c.ensemble_score * c.weight for c in components) / total_weight
        weighted_var = (
            sum(
                c.weight * (c.ensemble_score - weighted_mean) ** 2
                for c in components
            )
            / total_weight
        )
        return round(math.sqrt(weighted_var), 4)

    def _compute_model_contributions(
        self, components: list[EnsembleComponent]
    ) -> dict[str, float]:
        """Compute each model's contribution to the final score.

        Args:
            components: List of ensemble components.

        Returns:
            Dictionary mapping model name to its contribution percentage.
        """
        total = sum(c.weighted_score for c in components)
        if total == 0:
            return {c.name: 0.0 for c in components}

        return {
            c.name: round(c.weighted_score / total, 4) for c in components
        }

    def compare_with_v1(
        self, v1_result: ScoringResult, v2_result: EnsembleScoringResult
    ) -> dict[str, Any]:
        """Compare v1 and v2 scoring results.

        Args:
            v1_result: Result from the v1 scoring agent.
            v2_result: Result from the v2 ensemble scoring agent.

        Returns:
            Dictionary with comparison metrics.
        """
        score_diff = v2_result.total_score - v1_result.total_score
        grade_changed = v1_result.grade != v2_result.grade

        return {
            "v1_score": v1_result.total_score,
            "v2_score": v2_result.total_score,
            "score_difference": round(score_diff, 2),
            "grade_changed": grade_changed,
            "v1_grade": v1_result.grade.value,
            "v2_grade": v2_result.grade.value,
            "v2_confidence": v2_result.confidence,
            "v2_std_dev": v2_result.score_std_dev,
        }
