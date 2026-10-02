"""Demographic Analyzer Agent using LangChain DeepAgents."""

from __future__ import annotations

import logging
from typing import Any

from langchain_deepagents import create_deep_agent

from bias_detector.agents.base import BaseBiasAgent
from bias_detector.config import get_settings
from bias_detector.models import (
    DemographicAnalysisResult,
    DemographicData,
    DemographicDisparity,
)

logger = logging.getLogger(__name__)


class DemographicAnalyzerAgent(BaseBiasAgent[DemographicData]):
    """Agent that analyzes demographic representation and disparity metrics.

    This agent examines demographic data from hiring decisions to identify
    underrepresented groups, compute disparity ratios, and assess overall
    diversity in the hiring process.

    Attributes:
        name: Agent identifier.
        description: Agent description.
    """

    name = "demographic_analyzer"
    description = "Analyzes demographic representation and disparity in hiring data"

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the Demographic Analyzer Agent.

        Args:
            **kwargs: Additional keyword arguments.
        """
        super().__init__(**kwargs)
        self._settings = get_settings()
        self._agent = self._create_agent()

    def _create_agent(self) -> Any:
        """Create the LangChain DeepAgent for demographic analysis.

        Returns:
            Configured DeepAgent instance.
        """
        return create_deep_agent(
            name=self.name,
            description=self.description,
            system_prompt=self._get_system_prompt(),
        )

    def _get_system_prompt(self) -> str:
        """Get the system prompt for demographic analysis.

        Returns:
            System prompt string.
        """
        return (
            "You are a demographic analysis expert specializing in hiring fairness. "
            "Analyze demographic data to identify representation gaps, compute "
            "disparity ratios between groups, and assess overall diversity. "
            "Focus on gender, ethnicity, age, education, and experience dimensions. "
            "Provide actionable insights about underrepresented groups."
        )

    async def analyze(self, data: DemographicData) -> DemographicAnalysisResult:
        """Analyze demographic data for representation and disparities.

        Args:
            data: Demographic data to analyze.

        Returns:
            DemographicAnalysisResult with disparities and diversity metrics.
        """
        logger.info("Starting demographic analysis for %d candidates", data.total_candidates)

        disparities = self._compute_disparities(data)
        diversity_score = self._compute_diversity_score(data)
        underrepresented = self._identify_underrepresented(data)
        summary = self._generate_summary(data, disparities, diversity_score)

        result = DemographicAnalysisResult(
            disparities=disparities,
            overall_diversity_score=diversity_score,
            underrepresented_groups=underrepresented,
            analysis_summary=summary,
        )

        logger.info(
            "Demographic analysis complete: diversity_score=%.2f, disparities=%d",
            diversity_score,
            len(disparities),
        )
        return result

    def _compute_disparities(self, data: DemographicData) -> list[DemographicDisparity]:
        """Compute disparity ratios between demographic groups.

        Args:
            data: Demographic data.

        Returns:
            List of significant demographic disparities.
        """
        disparities: list[DemographicDisparity] = []
        threshold = self._settings.demographic_disparity_threshold

        for dimension, distribution in [
            ("gender", data.gender_distribution),
            ("ethnicity", data.ethnicity_distribution),
            ("age", data.age_distribution),
            ("education", data.education_distribution),
        ]:
            if not distribution:
                continue

            total = sum(distribution.values())
            if total == 0:
                continue

            groups = list(distribution.items())
            for i, (group_a, count_a) in enumerate(groups):
                for group_b, count_b in groups[i + 1:]:
                    rate_a = count_a / total
                    rate_b = count_b / total

                    if rate_b == 0:
                        continue

                    ratio = rate_a / rate_b
                    is_significant = abs(1.0 - ratio) > threshold

                    if is_significant:
                        disparities.append(
                            DemographicDisparity(
                                dimension=dimension,
                                group_a=group_a,
                                group_b=group_b,
                                rate_a=rate_a,
                                rate_b=rate_b,
                                disparity_ratio=ratio,
                                is_significant=True,
                            )
                        )

        return disparities

    def _compute_diversity_score(self, data: DemographicData) -> float:
        """Compute overall diversity score using Shannon entropy.

        Args:
            data: Demographic data.

        Returns:
            Diversity score between 0 and 1.
        """
        import math

        scores: list[float] = []

        for distribution in [
            data.gender_distribution,
            data.ethnicity_distribution,
            data.age_distribution,
        ]:
            if not distribution:
                continue

            total = sum(distribution.values())
            if total == 0:
                continue

            entropy = 0.0
            for count in distribution.values():
                if count > 0:
                    p = count / total
                    entropy -= p * math.log2(p)

            max_entropy = math.log2(len(distribution)) if len(distribution) > 1 else 1.0
            normalized = entropy / max_entropy if max_entropy > 0 else 0.0
            scores.append(normalized)

        return sum(scores) / len(scores) if scores else 0.0

    def _identify_underrepresented(self, data: DemographicData) -> list[str]:
        """Identify underrepresented demographic groups.

        Args:
            data: Demographic data.

        Returns:
            List of underrepresented group identifiers.
        """
        underrepresented: list[str] = []

        for dimension, distribution in [
            ("gender", data.gender_distribution),
            ("ethnicity", data.ethnicity_distribution),
        ]:
            if not distribution:
                continue

            total = sum(distribution.values())
            if total == 0:
                continue

            avg = total / len(distribution)
            for group, count in distribution.items():
                if count < avg * 0.5:
                    underrepresented.append(f"{dimension}:{group}")

        return underrepresented

    def _generate_summary(
        self,
        data: DemographicData,
        disparities: list[DemographicDisparity],
        diversity_score: float,
    ) -> str:
        """Generate a human-readable summary of demographic analysis.

        Args:
            data: Demographic data.
            disparities: Detected disparities.
            diversity_score: Overall diversity score.

        Returns:
            Summary string.
        """
        parts = [
            f"Analyzed {data.total_candidates} candidates across "
            f"{len(data.gender_distribution)} gender and "
            f"{len(data.ethnicity_distribution)} ethnicity categories.",
            f"Overall diversity score: {diversity_score:.2f}/1.0.",
        ]

        if disparities:
            parts.append(f"Found {len(disparities)} significant demographic disparities.")
        else:
            parts.append("No significant demographic disparities detected.")

        return " ".join(parts)
