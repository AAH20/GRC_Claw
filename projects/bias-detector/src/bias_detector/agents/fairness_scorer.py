"""Fairness Scorer Agent using LangChain DeepAgents."""

from __future__ import annotations

import logging
from typing import Any

from langchain_deepagents import create_deep_agent

from bias_detector.agents.base import BaseBiasAgent
from bias_detector.config import get_settings
from bias_detector.models import (
    DemographicData,
    FairnessDimension,
    FairnessScore,
    HiringDecision,
    LanguagePattern,
)

logger = logging.getLogger(__name__)


class FairnessScorerAgent(BaseBiasAgent[dict[str, Any]]):
    """Agent that computes fairness scores across multiple dimensions.

    This agent evaluates hiring decisions across demographic parity,
    equal opportunity, treatment equality, and process fairness dimensions
    to produce a comprehensive fairness score.

    Attributes:
        name: Agent identifier.
        description: Agent description.
    """

    name = "fairness_scorer"
    description = "Computes fairness scores across multiple dimensions"

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the Fairness Scorer Agent.

        Args:
            **kwargs: Additional keyword arguments.
        """
        super().__init__(**kwargs)
        self._settings = get_settings()
        self._agent = self._create_agent()

    def _create_agent(self) -> Any:
        """Create the LangChain DeepAgent for fairness scoring.

        Returns:
            Configured DeepAgent instance.
        """
        return create_deep_agent(
            name=self.name,
            description=self.description,
            system_prompt=self._get_system_prompt(),
        )

    def _get_system_prompt(self) -> str:
        """Get the system prompt for fairness scoring.

        Returns:
            System prompt string.
        """
        return (
            "You are a fairness scoring expert. Evaluate hiring decisions across "
            "multiple fairness dimensions: demographic parity, equal opportunity, "
            "treatment equality, and process fairness. Provide weighted scores "
            "with confidence intervals."
        )

    async def analyze(self, data: dict[str, Any]) -> FairnessScore:
        """Compute fairness scores from hiring data.

        Args:
            data: Dictionary containing demographic_data, language_patterns,
                  and hiring_decisions.

        Returns:
            FairnessScore with dimension scores and overall score.
        """
        logger.info("Starting fairness scoring analysis")

        demographic_data: DemographicData = data.get("demographic_data", DemographicData())
        language_patterns: list[LanguagePattern] = data.get("language_patterns", [])
        hiring_decisions: list[HiringDecision] = data.get("hiring_decisions", [])

        dimensions = [
            self._score_demographic_parity(demographic_data, hiring_decisions),
            self._score_equal_opportunity(demographic_data, hiring_decisions),
            self._score_treatment_equality(hiring_decisions),
            self._score_process_fairness(language_patterns),
        ]

        overall = self._compute_weighted_score(dimensions)
        confidence = self._compute_confidence(dimensions, len(hiring_decisions))

        result = FairnessScore(
            overall_score=overall,
            dimensions=dimensions,
            confidence=confidence,
            methodology="Weighted multi-dimension fairness scoring with entropy-based diversity metrics",
        )

        logger.info("Fairness scoring complete: overall=%.2f, confidence=%.2f", overall, confidence)
        return result

    def _score_demographic_parity(
        self, demo: DemographicData, decisions: list[HiringDecision]
    ) -> FairnessDimension:
        """Score demographic parity across groups.

        Args:
            demo: Demographic data.
            decisions: Hiring decisions.

        Returns:
            FairnessDimension for demographic parity.
        """
        if not decisions:
            return FairnessDimension(
                name="demographic_parity", score=0.5, weight=0.3,
                details={"reason": "insufficient_data"}
            )

        hire_rates: dict[str, dict[str, float]] = {}
        for decision in decisions:
            for key, value in decision.demographic_data.items():
                if key not in hire_rates:
                    hire_rates[key] = {}
                if value not in hire_rates[key]:
                    hire_rates[key][value] = {"hired": 0, "total": 0}
                hire_rates[key][value]["total"] += 1
                if decision.decision.value == "hired":
                    hire_rates[key][value]["hired"] += 1

        rates: list[float] = []
        for dim, groups in hire_rates.items():
            for group, counts in groups.items():
                if counts["total"] > 0:
                    rates.append(counts["hired"] / counts["total"])

        if len(rates) < 2:
            score = 0.5
        else:
            avg_rate = sum(rates) / len(rates)
            variance = sum((r - avg_rate) ** 2 for r in rates) / len(rates)
            score = max(0.0, 1.0 - variance * 4)

        return FairnessDimension(
            name="demographic_parity", score=score, weight=0.3,
            details={"hire_rate_variance": variance if len(rates) >= 2 else None}
        )

    def _score_equal_opportunity(
        self, demo: DemographicData, decisions: list[HiringDecision]
    ) -> FairnessDimension:
        """Score equal opportunity across groups.

        Args:
            demo: Demographic data.
            decisions: Hiring decisions.

        Returns:
            FairnessDimension for equal opportunity.
        """
        if not decisions:
            return FairnessDimension(
                name="equal_opportunity", score=0.5, weight=0.25,
                details={"reason": "insufficient_data"}
            )

        interview_rates: dict[str, list[bool]] = {}
        for decision in decisions:
            for key, value in decision.demographic_data.items():
                group_key = f"{key}:{value}"
                if group_key not in interview_rates:
                    interview_rates[group_key] = []
                interview_rates[group_key].append(decision.decision.value in ("interviewed", "hired"))

        if len(interview_rates) < 2:
            return FairnessDimension(
                name="equal_opportunity", score=0.5, weight=0.25,
                details={"reason": "insufficient_groups"}
            )

        rates = [sum(v) / len(v) for v in interview_rates.values() if v]
        if not rates:
            return FairnessDimension(
                name="equal_opportunity", score=0.5, weight=0.25
            )

        avg = sum(rates) / len(rates)
        variance = sum((r - avg) ** 2 for r in rates) / len(rates)
        score = max(0.0, 1.0 - variance * 4)

        return FairnessDimension(
            name="equal_opportunity", score=score, weight=0.25,
            details={"interview_rate_variance": variance}
        )

    def _score_treatment_equality(self, decisions: list[HiringDecision]) -> FairnessDimension:
        """Score treatment equality in hiring decisions.

        Args:
            decisions: Hiring decisions.

        Returns:
            FairnessDimension for treatment equality.
        """
        if not decisions:
            return FairnessDimension(
                name="treatment_equality", score=0.5, weight=0.25,
                details={"reason": "insufficient_data"}
            )

        interviewer_decisions: dict[str, list[str]] = {}
        for d in decisions:
            if d.interviewer_id:
                if d.interviewer_id not in interviewer_decisions:
                    interviewer_decisions[d.interviewer_id] = []
                interviewer_decisions[d.interviewer_id].append(d.decision.value)

        if len(interviewer_decisions) < 2:
            return FairnessDimension(
                name="treatment_equality", score=0.5, weight=0.25,
                details={"reason": "insufficient_interviewers"}
            )

        from collections import Counter
        distributions = [Counter(d) for d in interviewer_decisions.values()]
        all_types = set()
        for d in distributions:
            all_types.update(d.keys())

        score = min(1.0, len(all_types) / 4.0)

        return FairnessDimension(
            name="treatment_equality", score=score, weight=0.25,
            details={"decision_types_used": len(all_types)}
        )

    def _score_process_fairness(self, patterns: list[LanguagePattern]) -> FairnessDimension:
        """Score process fairness based on language patterns.

        Args:
            patterns: Detected language patterns.

        Returns:
            FairnessDimension for process fairness.
        """
        if not patterns:
            return FairnessDimension(
                name="process_fairness", score=1.0, weight=0.2,
                details={"reason": "no_language_bias_detected"}
            )

        severity_weights = {"low": 0.1, "medium": 0.3, "high": 0.6, "critical": 1.0}
        total_penalty = sum(severity_weights.get(p.severity.value, 0.1) for p in patterns)
        score = max(0.0, 1.0 - total_penalty / 10.0)

        return FairnessDimension(
            name="process_fairness", score=score, weight=0.2,
            details={"biased_patterns_count": len(patterns)}
        )

    def _compute_weighted_score(self, dimensions: list[FairnessDimension]) -> float:
        """Compute weighted overall fairness score.

        Args:
            dimensions: List of fairness dimensions.

        Returns:
            Weighted overall score.
        """
        total_weight = sum(d.weight for d in dimensions)
        if total_weight == 0:
            return 0.0
        return sum(d.score * d.weight for d in dimensions) / total_weight

    def _compute_confidence(self, dimensions: list[FairnessDimension], n_decisions: int) -> float:
        """Compute confidence level in the fairness score.

        Args:
            dimensions: Fairness dimensions.
            n_decisions: Number of hiring decisions analyzed.

        Returns:
            Confidence score between 0 and 1.
        """
        data_confidence = min(1.0, n_decisions / 100.0)
        dims_with_data = sum(1 for d in dimensions if d.score != 0.5)
        dim_confidence = dims_with_data / len(dimensions) if dimensions else 0.0
        return (data_confidence + dim_confidence) / 2.0
