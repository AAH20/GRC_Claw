"""MatchExplainerAgent for generating human-readable match explanations."""

from __future__ import annotations

from typing import Any, Optional

from candidate_matcher.agents.base import BaseAgent
from candidate_matcher.config.logging_config import get_logger
from candidate_matcher.models.schemas import (
    Candidate,
    JobPosting,
    MatchExplanation,
    MatchResult,
    SkillsGap,
)

logger = get_logger(__name__)


class MatchExplainerAgent(BaseAgent[MatchExplanation]):
    """Agent that generates human-readable explanations for match results.

    Creates detailed, actionable explanations of why a candidate was scored
    a particular way, including strengths, weaknesses, and suggestions.
    """

    def __init__(self, llm_client: Optional[Any] = None) -> None:
        """Initialize the match explainer agent.

        Args:
            llm_client: LLM client for generating responses.
        """
        super().__init__(
            name="MatchExplainerAgent",
            llm_client=llm_client,
            system_prompt=(
                "You are an expert at explaining candidate-job match results in clear, "
                "human-readable language. You provide actionable feedback that helps "
                "candidates understand their fit and recruiters make informed decisions."
            ),
        )

    async def explain(
        self,
        candidate: Candidate,
        job: JobPosting,
        match_result: MatchResult,
        skills_gap: Optional[SkillsGap] = None,
    ) -> MatchExplanation:
        """Generate an explanation for a match result.

        Args:
            candidate: The candidate profile.
            job: The job posting.
            match_result: The match result to explain.
            skills_gap: Optional skills gap analysis.

        Returns:
            Detailed match explanation.
        """
        context = self._build_context(candidate, job, match_result, skills_gap)

        prompt = f"""Explain the following candidate-job match result in clear, actionable language.

{context}

Provide a JSON response with:
- "summary": 2-3 sentence summary of the overall match
- "strengths": list of 3-5 key strengths the candidate brings
- "weaknesses": list of 2-4 areas where the candidate could improve
- "key_factors": list of objects with "factor" and "impact" fields explaining score components
- "suggestions": list of 2-4 actionable suggestions for the candidate
- "confidence": float (0-1) your confidence in this explanation"""

        try:
            llm_response = await self._generate_structured(
                prompt,
                schema={
                    "type": "object",
                    "properties": {
                        "summary": {"type": "string"},
                        "strengths": {"type": "array", "items": {"type": "string"}},
                        "weaknesses": {"type": "array", "items": {"type": "string"}},
                        "key_factors": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "factor": {"type": "string"},
                                    "impact": {"type": "string"},
                                },
                                "required": ["factor", "impact"],
                            },
                        },
                        "suggestions": {"type": "array", "items": {"type": "string"}},
                        "confidence": {"type": "number"},
                    },
                    "required": ["summary", "strengths", "weaknesses", "key_factors", "suggestions", "confidence"],
                },
            )
        except Exception as e:
            logger.warning("llm_explanation_failed", error=str(e))
            llm_response = self._generate_fallback_explanation(match_result, skills_gap)

        return MatchExplanation(
            match_id=match_result.match_id,
            summary=llm_response.get("summary", ""),
            strengths=llm_response.get("strengths", []),
            weaknesses=llm_response.get("weaknesses", []),
            key_factors=llm_response.get("key_factors", []),
            suggestions=llm_response.get("suggestions", []),
            confidence=llm_response.get("confidence", 0.5),
        )

    def _build_context(
        self,
        candidate: Candidate,
        job: JobPosting,
        match_result: MatchResult,
        skills_gap: Optional[SkillsGap],
    ) -> str:
        """Build context string for the LLM prompt.

        Args:
            candidate: The candidate profile.
            job: The job posting.
            match_result: The match result.
            skills_gap: Optional skills gap analysis.

        Returns:
            Formatted context string.
        """
        parts = [
            f"Candidate: {candidate.name}",
            f"Job: {job.title} at {job.company}",
            f"Overall Match Score: {match_result.overall_score:.2f}",
            f"Semantic Similarity: {match_result.semantic_score:.2f}",
            f"Skills Match: {match_result.skills_score:.2f}",
            f"Experience Match: {match_result.experience_score:.2f}",
            f"Culture Fit: {match_result.culture_score:.2f}",
        ]

        if match_result.bias_adjusted:
            parts.append(f"Bias Adjustment Applied: -{match_result.bias_penalty:.2f}")

        if skills_gap:
            parts.append(f"Skills Gap Score: {skills_gap.gap_score:.2f}")
            parts.append(f"Skills Coverage: {skills_gap.coverage_ratio:.2f}")
            if skills_gap.missing_skills:
                missing = ", ".join(s["skill_name"] for s in skills_gap.missing_skills)
                parts.append(f"Missing Skills: {missing}")
            if skills_gap.recommendations:
                parts.append(f"Recommendations: {'; '.join(skills_gap.recommendations)}")

        return "\n".join(parts)

    def _generate_fallback_explanation(
        self,
        match_result: MatchResult,
        skills_gap: Optional[SkillsGap],
    ) -> dict[str, Any]:
        """Generate a fallback explanation when LLM fails.

        Args:
            match_result: The match result.
            skills_gap: Optional skills gap analysis.

        Returns:
            Fallback explanation dictionary.
        """
        score = match_result.overall_score
        if score >= 0.8:
            summary = "Strong match with high alignment across all dimensions."
        elif score >= 0.6:
            summary = "Good match with some areas for development."
        elif score >= 0.4:
            summary = "Moderate match with notable gaps to address."
        else:
            summary = "Weak match with significant gaps."

        strengths = []
        if match_result.semantic_score >= 0.7:
            strengths.append("Strong semantic alignment with job requirements")
        if match_result.skills_score >= 0.7:
            strengths.append("Good skills match for the role")
        if match_result.experience_score >= 0.7:
            strengths.append("Relevant experience level")
        if match_result.culture_score >= 0.7:
            strengths.append("Good cultural fit")
        if not strengths:
            strengths.append("Some transferable skills and potential for growth")

        weaknesses = []
        if match_result.skills_score < 0.5:
            weaknesses.append("Skills gap in key areas")
        if match_result.experience_score < 0.5:
            weaknesses.append("Experience level below requirements")
        if match_result.culture_score < 0.5:
            weaknesses.append("Potential cultural misalignment")
        if skills_gap and skills_gap.missing_skills:
            weaknesses.append(f"Missing skills: {', '.join(s['skill_name'] for s in skills_gap.missing_skills[:3])}")
        if not weaknesses:
            weaknesses.append("Minor areas for development")

        return {
            "summary": summary,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "key_factors": [
                {"factor": "Semantic Similarity", "impact": f"Score: {match_result.semantic_score:.2f}"},
                {"factor": "Skills Match", "impact": f"Score: {match_result.skills_score:.2f}"},
                {"factor": "Experience", "impact": f"Score: {match_result.experience_score:.2f}"},
                {"factor": "Culture Fit", "impact": f"Score: {match_result.culture_score:.2f}"},
            ],
            "suggestions": [
                "Review job requirements and align profile accordingly",
                "Develop skills identified in the gap analysis",
            ],
            "confidence": 0.5,
        }

    async def execute(self, **kwargs: Any) -> MatchExplanation:
        """Execute match explanation generation.

        Args:
            **kwargs: Must contain 'candidate', 'job', and 'match_result' keys.
                     Optionally accepts 'skills_gap'.

        Returns:
            Match explanation result.
        """
        candidate = kwargs.get("candidate")
        job = kwargs.get("job")
        match_result = kwargs.get("match_result")
        skills_gap = kwargs.get("skills_gap")

        if not candidate or not job or not match_result:
            raise ValueError("'candidate', 'job', and 'match_result' are required")

        return await self.explain(candidate, job, match_result, skills_gap)
