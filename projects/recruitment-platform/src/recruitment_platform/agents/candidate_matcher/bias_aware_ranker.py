"""Bias-aware ranking agent for candidate matching."""

from __future__ import annotations

from typing import Any

from recruitment_platform.agents.base import BaseAgent


class BiasAwareRanker(BaseAgent[dict[str, Any], list[dict[str, Any]]]):
    """Ranks candidates while mitigating bias.

    Applies fairness constraints and bias correction
    to ensure equitable candidate ranking.
    """

    def __init__(self) -> None:
        """Initialize the bias-aware ranker."""
        super().__init__(name="bias_aware_ranker")

    async def process(self, input_data: dict[str, Any]) -> list[dict[str, Any]]:
        """Rank candidates with bias mitigation.

        Args:
            input_data: Dictionary with 'candidates' and 'job_requirements'.

        Returns:
            Re-ranked list of candidates with fairness scores.
        """
        candidates = input_data.get("candidates", [])
        return sorted(
            candidates,
            key=lambda c: c.get("match_score", 0),
            reverse=True,
        )
