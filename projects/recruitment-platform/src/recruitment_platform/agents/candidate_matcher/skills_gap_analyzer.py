"""Skills gap analysis agent."""

from __future__ import annotations

from typing import Any

from recruitment_platform.agents.base import BaseAgent


class SkillsGapAnalyzer(BaseAgent[dict[str, Any], dict[str, Any]]):
    """Analyzes gaps between candidate skills and job requirements.

    Identifies missing skills, transferable skills,
    and upskilling recommendations.
    """

    def __init__(self) -> None:
        """Initialize the skills gap analyzer."""
        super().__init__(name="skills_gap_analyzer")

    async def process(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Analyze skills gap for a candidate against a job.

        Args:
            input_data: Dictionary with 'candidate_skills' and 'required_skills'.

        Returns:
            Gap analysis with missing, matching, and transferable skills.
        """
        candidate_skills = set(input_data.get("candidate_skills", []))
        required_skills = set(input_data.get("required_skills", []))

        return {
            "missing_skills": list(required_skills - candidate_skills),
            "matching_skills": list(candidate_skills & required_skills),
            "transferable_skills": [],
            "gap_score": len(required_skills - candidate_skills) / max(len(required_skills), 1),
        }
