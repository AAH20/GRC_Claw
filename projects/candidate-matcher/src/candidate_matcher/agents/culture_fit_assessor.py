"""CultureFitAssessorAgent for evaluating cultural alignment."""

from __future__ import annotations

from typing import Any, Optional

from candidate_matcher.agents.base import BaseAgent
from candidate_matcher.config.logging_config import get_logger
from candidate_matcher.models.schemas import Candidate, JobPosting

logger = get_logger(__name__)


class CultureFitAssessorAgent(BaseAgent[dict[str, Any]]):
    """Agent that assesses cultural fit between candidates and organizations.

    Evaluates alignment of values, work styles, and preferences between
    a candidate and the company culture described in the job posting.
    """

    def __init__(self, llm_client: Optional[Any] = None) -> None:
        """Initialize the culture fit assessor agent.

        Args:
            llm_client: LLM client for generating responses.
        """
        super().__init__(
            name="CultureFitAssessorAgent",
            llm_client=llm_client,
            system_prompt=(
                "You are an expert at assessing cultural fit between candidates and organizations. "
                "You evaluate values alignment, work style compatibility, and mutual expectations."
            ),
        )

    def _extract_culture_values(self, job: JobPosting) -> list[str]:
        """Extract culture-related values from a job posting.

        Args:
            job: The job posting.

        Returns:
            List of culture values.
        """
        values = list(job.culture_values)
        culture_keywords = [
            "collaborative", "innovative", "fast-paced", "remote-friendly",
            "work-life balance", "diverse", "inclusive", "transparent",
            "autonomous", "entrepreneurial", "customer-focused", "data-driven",
        ]
        desc_lower = job.description.lower()
        for keyword in culture_keywords:
            if keyword in desc_lower and keyword not in values:
                values.append(keyword)
        return values

    def _extract_candidate_preferences(self, candidate: Candidate) -> dict[str, Any]:
        """Extract culture-related preferences from candidate profile.

        Args:
            candidate: The candidate profile.

        Returns:
            Dictionary of candidate preferences.
        """
        prefs = candidate.preferences
        return {
            "work_style": prefs.get("work_style", "unknown"),
            "team_preference": prefs.get("team_preference", "unknown"),
            "values": prefs.get("values", []),
            "environment": prefs.get("environment", "unknown"),
            "management_style": prefs.get("management_style", "unknown"),
        }

    async def assess_fit(
        self,
        candidate: Candidate,
        job: JobPosting,
    ) -> dict[str, Any]:
        """Assess cultural fit between a candidate and job.

        Args:
            candidate: The candidate profile.
            job: The job posting.

        Returns:
            Dictionary with culture fit analysis.
        """
        job_values = self._extract_culture_values(job)
        candidate_prefs = self._extract_candidate_preferences(candidate)

        alignment_score = self._compute_alignment(candidate_prefs, job_values)

        prompt = f"""Assess the cultural fit between this candidate and company.

Candidate Preferences: {candidate_prefs}
Candidate Work History: {candidate.work_history}
Job Culture Values: {job_values}
Job Description: {job.description}
Company: {job.company}

Provide a JSON response with:
- "fit_score": float (0-1) overall cultural fit
- "aligned_values": list of values that align
- "potential_conflicts": list of potential cultural conflicts
- "work_style_compatibility": string description
- "summary": brief summary of cultural fit"""

        try:
            llm_analysis = await self._generate_structured(
                prompt,
                schema={
                    "type": "object",
                    "properties": {
                        "fit_score": {"type": "number"},
                        "aligned_values": {"type": "array", "items": {"type": "string"}},
                        "potential_conflicts": {"type": "array", "items": {"type": "string"}},
                        "work_style_compatibility": {"type": "string"},
                        "summary": {"type": "string"},
                    },
                    "required": ["fit_score", "aligned_values", "potential_conflicts", "work_style_compatibility", "summary"],
                },
            )
        except Exception as e:
            logger.warning("llm_culture_analysis_failed", error=str(e))
            llm_analysis = {
                "fit_score": alignment_score,
                "aligned_values": [],
                "potential_conflicts": [],
                "work_style_compatibility": "Analysis unavailable",
                "summary": "LLM analysis unavailable; using heuristic alignment only.",
            }

        combined_score = (alignment_score + llm_analysis.get("fit_score", alignment_score)) / 2

        return {
            "fit_score": round(combined_score, 4),
            "heuristic_score": round(alignment_score, 4),
            "llm_score": round(llm_analysis.get("fit_score", alignment_score), 4),
            "aligned_values": llm_analysis.get("aligned_values", []),
            "potential_conflicts": llm_analysis.get("potential_conflicts", []),
            "work_style_compatibility": llm_analysis.get("work_style_compatibility", ""),
            "summary": llm_analysis.get("summary", ""),
        }

    def _compute_alignment(
        self,
        candidate_prefs: dict[str, Any],
        job_values: list[str],
    ) -> float:
        """Compute heuristic alignment score.

        Args:
            candidate_prefs: Candidate preferences.
            job_values: Job culture values.

        Returns:
            Alignment score between 0 and 1.
        """
        if not job_values:
            return 0.5

        candidate_values = candidate_prefs.get("values", [])
        if not candidate_values:
            return 0.5

        candidate_set = set(v.lower() for v in candidate_values)
        job_set = set(v.lower() for v in job_values)

        if not candidate_set or not job_set:
            return 0.5

        intersection = candidate_set & job_set
        union = candidate_set | job_set

        jaccard = len(intersection) / len(union) if union else 0.5
        return jaccard

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        """Execute culture fit assessment.

        Args:
            **kwargs: Must contain 'candidate' and 'job' keys.

        Returns:
            Culture fit analysis result.
        """
        candidate = kwargs.get("candidate")
        job = kwargs.get("job")
        if not candidate or not job:
            raise ValueError("Both 'candidate' and 'job' are required")
        return await self.assess_fit(candidate, job)
