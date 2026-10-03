"""Match explanation agent."""

from __future__ import annotations

from typing import Any

from recruitment_platform.agents.base import BaseAgent


class MatchExplainer(BaseAgent[dict[str, Any], dict[str, Any]]):
    """Generates human-readable explanations for candidate matches.

    Provides transparency into why a candidate was scored
    at a particular match level.
    """

    def __init__(self) -> None:
        """Initialize the match explainer."""
        super().__init__(name="match_explainer")

    async def process(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Generate explanation for a candidate match.

        Args:
            input_data: Dictionary with 'candidate', 'job', and 'match_result'.

        Returns:
            Detailed explanation of the match scoring.
        """
        return {
            "summary": "",
            "strengths": [],
            "gaps": [],
            "recommendations": [],
        }
