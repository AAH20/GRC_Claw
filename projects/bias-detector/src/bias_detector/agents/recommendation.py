"""Recommendation Agent using LangChain DeepAgents."""

from __future__ import annotations

import logging
from typing import Any

from deepagents import create_deep_agent

from bias_detector.agents.base import BaseBiasAgent
from bias_detector.config import get_settings
from bias_detector.models import (
    BiasRecommendation,
    DemographicAnalysisResult,
    FairnessScore,
    LanguageBiasResult,
)

logger = logging.getLogger(__name__)


class RecommendationAgent(BaseBiasAgent[dict[str, Any]]):
    """Agent that generates actionable recommendations for improvement.

    This agent synthesizes results from all other agents to produce
    prioritized, actionable recommendations for reducing bias in hiring.

    Attributes:
        name: Agent identifier.
        description: Agent description.
    """

    name = "recommendation_agent"
    description = "Generates actionable recommendations for bias reduction"

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the Recommendation Agent.

        Args:
            **kwargs: Additional keyword arguments.
        """
        super().__init__(**kwargs)
        self._settings = get_settings()
        self._agent = self._create_agent()

    def _create_agent(self) -> Any:
        """Create the LangChain DeepAgent for recommendations.

        Returns:
            Configured DeepAgent instance.
        """
        return create_deep_agent(
            name=self.name,
            system_prompt=self._get_system_prompt(),
        )

    def _get_system_prompt(self) -> str:
        """Get the system prompt for recommendations.

        Returns:
            System prompt string.
        """
        return (
            "You are a bias reduction expert. Synthesize analysis results into "
            "prioritized, actionable recommendations. Focus on practical steps "
            "that can be implemented immediately, short-term, and long-term."
        )

    async def analyze(self, data: dict[str, Any]) -> list[BiasRecommendation]:
        """Generate recommendations from analysis results.

        Args:
            data: Dictionary containing demographic_analysis, language_bias,
                  fairness_score, and patterns.

        Returns:
            List of actionable bias recommendations.
        """
        logger.info("Starting recommendation generation")

        demo_result: DemographicAnalysisResult = data.get(
            "demographic_analysis", DemographicAnalysisResult()
        )
        lang_result: LanguageBiasResult = data.get(
            "language_bias", LanguageBiasResult()
        )
        fairness: FairnessScore = data.get("fairness_score", FairnessScore())
        patterns: list[dict[str, Any]] = data.get("patterns", [])

        recommendations: list[BiasRecommendation] = []

        if demo_result.disparities:
            recommendations.append(self._create_demographic_rec(demo_result))

        if lang_result.patterns:
            recommendations.append(self._create_language_rec(lang_result))

        if fairness.overall_score < self._settings.fairness_score_threshold:
            recommendations.append(self._create_fairness_rec(fairness))

        for pattern in patterns:
            rec = self._create_pattern_rec(pattern)
            if rec:
                recommendations.append(rec)

        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        recommendations.sort(key=lambda r: priority_order.get(r.priority.value, 4))

        logger.info("Recommendation generation complete: %d recommendations", len(recommendations))
        return recommendations

    def _create_demographic_rec(self, result: DemographicAnalysisResult) -> BiasRecommendation:
        """Create recommendation from demographic analysis."""
        disparity_dims = {d.dimension for d in result.disparities}
        return BiasRecommendation(
            title="Address Demographic Disparities in Hiring",
            description=(
                f"Significant disparities detected in {', '.join(disparity_dims)}. "
                f"Overall diversity score: {result.overall_diversity_score:.2f}/1.0."
            ),
            priority="high" if result.overall_diversity_score < 0.5 else "medium",
            category="demographics",
            expected_impact="Improved diversity and reduced legal risk",
            implementation_steps=[
                "Review job posting channels to reach underrepresented groups",
                "Implement blind resume screening process",
                "Establish diversity hiring goals with accountability measures",
            ],
        )

    def _create_language_rec(self, result: LanguageBiasResult) -> BiasRecommendation:
        """Create recommendation from language bias detection."""
        categories = {p.category for p in result.patterns}
        return BiasRecommendation(
            title="Eliminate Biased Language from Hiring Materials",
            description=(
                f"Detected {result.biased_phrases_count} biased phrases across "
                f"{', '.join(categories)}."
            ),
            priority="high" if result.overall_bias_score > 0.5 else "medium",
            category="language",
            expected_impact="More inclusive candidate pool and reduced bias",
            implementation_steps=[
                "Audit all job descriptions for biased language",
                "Create inclusive language guide for hiring teams",
                "Implement automated language screening tool",
            ],
        )

    def _create_fairness_rec(self, score: FairnessScore) -> BiasRecommendation:
        """Create recommendation from fairness scoring."""
        low_dims = [d.name for d in score.dimensions if d.score < 0.5]
        return BiasRecommendation(
            title="Improve Overall Fairness in Hiring Process",
            description=(
                f"Overall fairness score: {score.overall_score:.2f}/1.0. "
                f"Below-threshold dimensions: {', '.join(low_dims)}."
            ),
            priority="critical" if score.overall_score < 0.3 else "high",
            category="fairness",
            expected_impact="Fairer outcomes and reduced discrimination risk",
            implementation_steps=[
                "Implement structured interviews with standardized questions",
                "Establish diverse interview panels",
                "Create clear, objective evaluation criteria",
            ],
        )

    def _create_pattern_rec(self, pattern: dict[str, Any]) -> BiasRecommendation | None:
        """Create recommendation from a detected pattern."""
        pattern_type = pattern.get("type", "")

        if pattern_type == "interviewer_bias":
            return BiasRecommendation(
                title="Address Interviewer Bias",
                description="Interviewer shows significant decision bias.",
                priority="high",
                category="interviewer",
                expected_impact="More consistent and fair evaluations",
                implementation_steps=[
                    "Provide bias training to identified interviewers",
                    "Implement calibration sessions for interviewers",
                ],
            )

        if pattern_type == "temporal_bias":
            return BiasRecommendation(
                title="Address Temporal Bias in Decision Making",
                description="Decisions show temporal clustering that may indicate bias.",
                priority="medium",
                category="process",
                expected_impact="More consistent decision quality",
                implementation_steps=[
                    "Implement mandatory breaks between interviews",
                    "Distribute interviews throughout the day",
                ],
            )

        if pattern_type == "demographic_clustering":
            return BiasRecommendation(
                title="Address Demographic Clustering in Rejections",
                description="Rejections cluster heavily in specific demographic groups.",
                priority="critical",
                category="demographics",
                expected_impact="Reduced discriminatory rejection patterns",
                implementation_steps=[
                    "Implement blind resume review",
                    "Require diverse rejection justification",
                ],
            )

        return None
