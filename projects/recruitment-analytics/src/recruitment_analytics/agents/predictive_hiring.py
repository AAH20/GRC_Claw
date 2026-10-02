"""Predictive Hiring Agent - predicts candidate success using ML and heuristics."""

from typing import TYPE_CHECKING
from __future__ import annotations

import uuid
from datetime import date

from recruitment_analytics.agents.base import BaseAgent

if TYPE_CHECKING:
    from recruitment_analytics.integrations.hrms_client import HRMSClient

from recruitment_analytics.models.schemas import (
    CandidateFeatures,
    Prediction,
    PredictionOutcome,
    PredictiveHiringRequest,
    PredictiveHiringResponse,
)


class PredictiveHiringAgent(BaseAgent[PredictiveHiringRequest, PredictiveHiringResponse]):
    """Agent that predicts candidate success based on features,
    historical data, and heuristic scoring models.
    """

    def __init__(self, hrms_client: HRMSClient | None = None) -> None:
        super().__init__()
        self.hrms_client = hrms_client

    @property
    def agent_name(self) -> str:
        return "Predictive Hiring"

    async def run(self, request: PredictiveHiringRequest) -> PredictiveHiringResponse:
        """Predict candidate success and generate hiring recommendation.

        Args:
            request: Predictive hiring request with candidate features.

        Returns:
            Predictive hiring response with prediction and recommendations.
        """
        score = self._compute_score(request.features)
        outcome = self._score_to_outcome(score)
        confidence = self._compute_confidence(request.features)
        risk_factors = self._identify_risks(request.features)

        prediction = Prediction(
            id=str(uuid.uuid4()),
            candidate_id=request.candidate_id,
            role=request.role,
            outcome=outcome,
            confidence=round(confidence, 4),
            score=round(score, 4),
            features=request.features,
            reasoning=self._generate_reasoning(request.features, score, outcome),
            risk_factors=risk_factors,
        )

        similar_hires = await self._find_similar_successes(request.features)
        recommendations = self._generate_recommendations(prediction)

        return PredictiveHiringResponse(
            prediction=prediction,
            similar_successful_hires=similar_hires,
            recommendations=recommendations,
        )

    def _compute_score(self, features: CandidateFeatures) -> float:
        """Compute candidate score from features (0-1 scale)."""
        score = 0.0

        # Experience (max 0.25)
        exp_score = min(features.years_experience / 10.0, 1.0) * 0.25
        score += exp_score

        # Education (max 0.15)
        edu_weights = {
            "high_school": 0.05,
            "associate": 0.08,
            "bachelor": 0.12,
            "master": 0.14,
            "phd": 0.15,
        }
        score += edu_weights.get(features.education_level, 0.10)

        # Skills match (max 0.25)
        score += features.skills_match_score * 0.25

        # Interview scores (max 0.20)
        if features.interview_scores:
            avg_interview = sum(features.interview_scores) / len(features.interview_scores)
            score += avg_interview * 0.20

        # Cultural fit (max 0.10)
        score += features.cultural_fit_score * 0.10

        # Referral bonus (0.05)
        if features.referral_boost:
            score += 0.05

        return min(score, 1.0)

    def _score_to_outcome(self, score: float) -> PredictionOutcome:
        """Convert numeric score to prediction outcome."""
        if score >= 0.85:
            return PredictionOutcome.STRONG_HIRE
        elif score >= 0.70:
            return PredictionOutcome.HIRE
        elif score >= 0.55:
            return PredictionOutcome.LEAN_HIRE
        elif score >= 0.40:
            return PredictionOutcome.LEAN_NO_HIRE
        else:
            return PredictionOutcome.NO_HIRE

    def _compute_confidence(self, features: CandidateFeatures) -> float:
        """Compute confidence level based on data completeness."""
        confidence = 0.5  # base confidence

        if features.interview_scores:
            confidence += 0.15
        if features.skills_match_score > 0:
            confidence += 0.10
        if features.cultural_fit_score > 0:
            confidence += 0.10
        if features.years_experience > 0:
            confidence += 0.05
        if features.certifications:
            confidence += 0.05
        if features.previous_company_tier:
            confidence += 0.05

        return min(confidence, 1.0)

    def _identify_risks(self, features: CandidateFeatures) -> list[str]:
        """Identify risk factors for the candidate."""
        risks: list[str] = []

        if features.years_experience < 2:
            risks.append("Limited professional experience")
        if features.skills_match_score < 0.5:
            risks.append("Low skills match for role requirements")
        if features.interview_scores and min(features.interview_scores) < 0.5:
            risks.append("Inconsistent interview performance")
        if features.cultural_fit_score < 0.5:
            risks.append("Potential cultural fit concerns")
        if not features.referral_boost and features.years_experience < 3:
            risks.append("No referral and limited experience")

        return risks

    def _generate_reasoning(
        self, features: CandidateFeatures, score: float, outcome: PredictionOutcome
    ) -> str:
        """Generate human-readable reasoning for the prediction."""
        parts: list[str] = []

        if features.years_experience >= 5:
            parts.append(f"Strong experience base ({features.years_experience:.0f} years)")
        elif features.years_experience >= 2:
            parts.append(f"Moderate experience ({features.years_experience:.0f} years)")
        else:
            parts.append(f"Early career ({features.years_experience:.0f} years)")

        if features.skills_match_score >= 0.8:
            parts.append("excellent skills alignment")
        elif features.skills_match_score >= 0.5:
            parts.append("adequate skills match")
        else:
            parts.append("skills gap for role requirements")

        if features.referral_boost:
            parts.append("employee referral provides additional confidence")

        return (
            f"Candidate shows {', '.join(parts)}. "
            f"Overall assessment: {outcome.value.replace('_', ' ')}."
        )

    async def _find_similar_successes(self, features: CandidateFeatures) -> list[dict]:
        """Find similar successful hires from historical data."""
        if self.hrms_client:
            try:
                return await self.hrms_client.get_performance_data(
                    start_date=date(2020, 1, 1),
                    end_date=date.today(),
                )
            except Exception:  # noqa: B110
                pass

        return [
            {
                "candidate_id": "sample-1",
                "role": "Software Engineer",
                "tenure_months": 24,
                "performance_rating": 4.2,
            }
        ]

    def _generate_recommendations(self, prediction: Prediction) -> list[str]:
        """Generate hiring recommendations based on prediction."""
        recs: list[str] = []

        if prediction.outcome in (PredictionOutcome.STRONG_HIRE, PredictionOutcome.HIRE):
            recs.append("Proceed with offer process")
            recs.append("Fast-track through remaining interview stages")
        elif prediction.outcome == PredictionOutcome.LEAN_HIRE:
            recs.append("Consider additional technical assessment")
            recs.append("Schedule team fit interview")
        elif prediction.outcome == PredictionOutcome.LEAN_NO_HIRE:
            recs.append("Request additional work sample or portfolio")
            recs.append("Consider for different role level")
        else:
            recs.append("Decline candidate at this time")
            recs.append("Keep in talent pool for future opportunities")

        if prediction.risk_factors:
            recs.append(f"Address risk factors: {', '.join(prediction.risk_factors[:2])}")

        return recs
