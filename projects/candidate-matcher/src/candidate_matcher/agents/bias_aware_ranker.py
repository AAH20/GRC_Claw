"""BiasAwareRankerAgent for ranking candidates with bias detection and mitigation."""

from __future__ import annotations

from typing import Any, Optional

from candidate_matcher.agents.base import BaseAgent
from candidate_matcher.config.logging_config import get_logger
from candidate_matcher.models.schemas import (
    BiasReport,
    Candidate,
    JobPosting,
)

logger = get_logger(__name__)

PROTECTED_ATTRIBUTES = [
    "gender",
    "age",
    "race",
    "ethnicity",
    "religion",
    "nationality",
    "disability",
    "marital_status",
    "sexual_orientation",
]


class BiasAwareRankerAgent(BaseAgent[dict[str, Any]]):
    """Agent that ranks candidates with bias detection and mitigation.

    Analyzes match results for potential biases related to protected attributes,
    applies mitigation strategies, and produces fair rankings.
    """

    def __init__(
        self,
        llm_client: Optional[Any] = None,
        bias_penalty_factor: float = 0.15,
    ) -> None:
        """Initialize the bias-aware ranker agent.

        Args:
            llm_client: LLM client for generating responses.
            bias_penalty_factor: Factor for penalizing biased scores (0-1).
        """
        super().__init__(
            name="BiasAwareRankerAgent",
            llm_client=llm_client,
            system_prompt=(
                "You are an expert at detecting and mitigating bias in candidate ranking. "
                "You ensure fair evaluation by identifying protected attributes and "
                "applying appropriate mitigation strategies."
            ),
        )
        self._bias_penalty_factor = bias_penalty_factor

    def _detect_bias_indicators(
        self,
        candidate: Candidate,
        job: JobPosting,
    ) -> list[str]:
        """Detect potential bias indicators in candidate/job data.

        Args:
            candidate: The candidate profile.
            job: The job posting.

        Returns:
            List of detected bias indicator descriptions.
        """
        indicators: list[str] = []

        gendered_terms = {
            "he": "masculine pronoun",
            "she": "feminine pronoun",
            "his": "masculine possessive",
            "her": "feminine possessive",
            "man": "masculine noun",
            "woman": "feminine noun",
            "guys": "informal masculine",
            "ninja": "coded language",
            "rockstar": "coded language",
            "aggressive": "potentially gendered",
            "dominant": "potentially gendered",
        }
        job_text = f"{job.title} {job.description}".lower()
        for term, description in gendered_terms.items():
            if term in job_text:
                indicators.append(f"Gendered language in job posting: '{term}' ({description})")

        age_terms = ["young", "energetic", "recent graduate", "digital native", "mature"]
        for term in age_terms:
            if term in job_text:
                indicators.append(f"Age-related language: '{term}'")

        culture_terms = ["culture fit", "beer", "happy hour", "ping pong"]
        for term in culture_terms:
            if term in job_text:
                indicators.append(f"Potential cultural bias: '{term}'")

        return indicators

    def _compute_bias_score(
        self,
        candidate: Candidate,
        job: JobPosting,
        indicators: list[str],
    ) -> float:
        """Compute a bias score based on detected indicators.

        Args:
            candidate: The candidate profile.
            job: The job posting.
            indicators: Detected bias indicators.

        Returns:
            Bias score between 0 (no bias) and 1 (high bias).
        """
        if not indicators:
            return 0.0

        base_score = min(len(indicators) * 0.1, 0.5)

        protected_in_metadata = [
            attr for attr in PROTECTED_ATTRIBUTES
            if attr in candidate.metadata
        ]
        if protected_in_metadata:
            base_score += 0.2

        return min(base_score, 1.0)

    def _apply_mitigation(
        self,
        original_score: float,
        bias_score: float,
    ) -> float:
        """Apply bias mitigation by adjusting the score.

        Args:
            original_score: The original match score.
            bias_score: The detected bias score.

        Returns:
            Bias-adjusted score.
        """
        penalty = bias_score * self._bias_penalty_factor
        adjusted = original_score * (1 - penalty)
        return max(0.0, adjusted)

    async def rank(
        self,
        candidate: Candidate,
        job: JobPosting,
        base_scores: dict[str, float],
    ) -> dict[str, Any]:
        """Rank a candidate with bias detection and mitigation.

        Args:
            candidate: The candidate profile.
            job: The job posting.
            base_scores: Dictionary of base scores (semantic, skills, experience, culture).

        Returns:
            Dictionary with bias analysis and adjusted scores.
        """
        indicators = self._detect_bias_indicators(candidate, job)
        bias_score = self._compute_bias_score(candidate, job, indicators)

        weights = {
            "semantic": 0.35,
            "skills": 0.30,
            "experience": 0.20,
            "culture": 0.15,
        }
        overall = sum(
            base_scores.get(key, 0.0) * weight
            for key, weight in weights.items()
        )

        adjusted_score = self._apply_mitigation(overall, bias_score)

        bias_report = BiasReport(
            bias_detected=len(indicators) > 0 or bias_score > 0.1,
            bias_types=[ind.split(":")[0] for ind in indicators] if indicators else [],
            bias_score=round(bias_score, 4),
            affected_attributes=[
                attr for attr in PROTECTED_ATTRIBUTES
                if attr in candidate.metadata
            ],
            mitigation_applied=bias_score > 0.05,
            mitigation_strategy="score_penalty" if bias_score > 0.05 else None,
            details={
                "indicators": indicators,
                "original_score": round(overall, 4),
                "adjusted_score": round(adjusted_score, 4),
                "penalty_applied": round(overall - adjusted_score, 4),
            },
            recommendations=self._generate_recommendations(indicators),
        )

        return {
            "original_score": round(overall, 4),
            "adjusted_score": round(adjusted_score, 4),
            "bias_score": round(bias_score, 4),
            "bias_detected": bias_report.bias_detected,
            "mitigation_applied": bias_report.mitigation_applied,
            "bias_report": bias_report,
        }

    def _generate_recommendations(
        self,
        indicators: list[str],
    ) -> list[str]:
        """Generate bias mitigation recommendations.

        Args:
            indicators: Detected bias indicators.

        Returns:
            List of recommendation strings.
        """
        recommendations: list[str] = []

        if any("Gendered" in ind for ind in indicators):
            recommendations.append(
                "Use gender-neutral language in job descriptions. "
                "Consider tools like Textio or Gender Decoder."
            )
        if any("Age" in ind for ind in indicators):
            recommendations.append(
                "Remove age-related language from job postings. "
                "Focus on skills and competencies rather than age proxies."
            )
        if any("cultural" in ind.lower() for ind in indicators):
            recommendations.append(
                "Replace 'culture fit' with 'culture add' language. "
                "Focus on values alignment rather than social similarity."
            )
        if not recommendations:
            recommendations.append(
                "No significant bias indicators detected. "
                "Continue monitoring for fairness in ranking."
            )

        return recommendations

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        """Execute bias-aware ranking.

        Args:
            **kwargs: Must contain 'candidate', 'job', and 'base_scores' keys.

        Returns:
            Bias analysis and adjusted ranking result.
        """
        candidate = kwargs.get("candidate")
        job = kwargs.get("job")
        base_scores = kwargs.get("base_scores", {})
        if not candidate or not job:
            raise ValueError("Both 'candidate' and 'job' are required")
        return await self.rank(candidate, job, base_scores)
