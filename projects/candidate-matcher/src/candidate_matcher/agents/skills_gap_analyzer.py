"""SkillsGapAnalyzerAgent for identifying and quantifying skills gaps."""

from __future__ import annotations

import json
from typing import Any

from candidate_matcher.agents.base import BaseAgent
from candidate_matcher.config.logging_config import get_logger
from candidate_matcher.models.schemas import (
    Candidate,
    JobPosting,
    JobRequirement,
    Skill,
    SkillLevel,
    SkillsGap,
)

logger = get_logger(__name__)

SKILL_LEVEL_ORDER = {
    SkillLevel.BEGINNER: 1,
    SkillLevel.INTERMEDIATE: 2,
    SkillLevel.ADVANCED: 3,
    SkillLevel.EXPERT: 4,
}


class SkillsGapAnalyzerAgent(BaseAgent[SkillsGap]):
    """Agent that analyzes skills gaps between candidates and job requirements.

    Identifies missing skills, quantifies proficiency gaps, and provides
    upskilling recommendations.
    """

    def __init__(self, llm_client: Any | None = None) -> None:
        """Initialize the skills gap analyzer agent.

        Args:
            llm_client: LLM client for generating responses.
        """
        super().__init__(
            name="SkillsGapAnalyzerAgent",
            llm_client=llm_client,
            system_prompt=(
                "You are an expert at analyzing skills gaps between candidates "
                "and job requirements. You identify missing skills, quantify "
                "proficiency differences, and recommend upskilling paths."
            ),
        )

    def _find_matching_skill(
        self,
        requirement: JobRequirement,
        candidate_skills: list[Skill],
    ) -> Skill | None:
        """Find a candidate skill that matches a job requirement.

        Args:
            requirement: The job requirement to match.
            candidate_skills: List of candidate skills.

        Returns:
            The matching skill if found, None otherwise.
        """
        req_name_lower = requirement.skill_name.lower()
        for skill in candidate_skills:
            if skill.name.lower() == req_name_lower:
                return skill
        # Fuzzy match: check if skill name contains requirement or vice versa
        for skill in candidate_skills:
            if req_name_lower in skill.name.lower() or skill.name.lower() in req_name_lower:
                return skill
        return None

    def _compute_level_gap(
        self,
        candidate_level: SkillLevel,
        required_level: SkillLevel,
    ) -> float:
        """Compute the gap between candidate and required skill levels.

        Args:
            candidate_level: Candidate's proficiency level.
            required_level: Required proficiency level.

        Returns:
            Gap score between 0 (no gap) and 1 (maximum gap).
        """
        candidate_value = SKILL_LEVEL_ORDER[candidate_level]
        required_value = SKILL_LEVEL_ORDER[required_level]
        max_gap = len(SKILL_LEVEL_ORDER) - 1
        gap = max(0, required_value - candidate_value)
        return gap / max_gap

    async def analyze_gap(
        self,
        candidate: Candidate,
        job: JobPosting,
    ) -> SkillsGap:
        """Analyze skills gap between a candidate and job.

        Args:
            candidate: The candidate profile.
            job: The job posting.

        Returns:
            Detailed skills gap analysis.
        """
        missing_skills: list[dict[str, Any]] = []
        skill_gaps: list[dict[str, Any]] = []
        matching_skills: list[dict[str, Any]] = []

        for req in job.requirements:
            matching_skill = self._find_matching_skill(req, candidate.skills)

            if matching_skill is None:
                missing_skills.append({
                    "skill_name": req.skill_name,
                    "required_level": req.minimum_level.value,
                    "preferred": req.preferred,
                    "weight": req.weight,
                    "gap_type": "missing",
                })
            else:
                level_gap = self._compute_level_gap(matching_skill.level, req.minimum_level)
                if level_gap > 0:
                    skill_gaps.append({
                        "skill_name": req.skill_name,
                        "candidate_level": matching_skill.level.value,
                        "required_level": req.minimum_level.value,
                        "level_gap": round(level_gap, 4),
                        "years_experience": matching_skill.years_experience,
                        "preferred": req.preferred,
                        "weight": req.weight,
                        "gap_type": "proficiency",
                    })
                else:
                    matching_skills.append({
                        "skill_name": req.skill_name,
                        "level": matching_skill.level.value,
                        "years_experience": matching_skill.years_experience,
                        "preferred": req.preferred,
                        "weight": req.weight,
                    })

        # Compute overall gap score
        total_weight = sum(r.weight for r in job.requirements) or 1.0
        weighted_gap = 0.0

        for ms in missing_skills:
            weighted_gap += ms["weight"] * 1.0  # Full gap for missing skills
        for sg in skill_gaps:
            weighted_gap += sg["weight"] * sg["level_gap"]

        gap_score = weighted_gap / total_weight if total_weight > 0 else 0.0

        # Compute coverage ratio
        covered = len(matching_skills) + sum(
            1 for sg in skill_gaps if sg["level_gap"] < 0.5
        )
        total_reqs = len(job.requirements)
        coverage_ratio = covered / total_reqs if total_reqs > 0 else 1.0

        # Generate recommendations using LLM
        recommendations = await self._generate_recommendations(
            candidate, job, missing_skills, skill_gaps
        )

        return SkillsGap(
            candidate_id=candidate.id,
            job_id=job.id,
            missing_skills=missing_skills,
            skill_gaps=skill_gaps,
            matching_skills=matching_skills,
            gap_score=round(gap_score, 4),
            coverage_ratio=round(coverage_ratio, 4),
            recommendations=recommendations,
        )

    async def _generate_recommendations(
        self,
        candidate: Candidate,  # noqa: ARG002
        job: JobPosting,
        missing_skills: list[dict[str, Any]],
        skill_gaps: list[dict[str, Any]],
    ) -> list[str]:
        """Generate upskilling recommendations using LLM.

        Args:
            candidate: The candidate profile.
            job: The job posting.
            missing_skills: List of missing skills.
            skill_gaps: List of proficiency gaps.

        Returns:
            List of recommendation strings.
        """
        if not missing_skills and not skill_gaps:
            return ["Candidate meets all skill requirements."]

        prompt = (
            "Based on the following skills gap analysis, provide 3-5 actionable "
            "upskilling recommendations.\n\n"
            f"Missing Skills: {json.dumps(missing_skills) if missing_skills else 'None'}\n"
            f"Proficiency Gaps: {json.dumps(skill_gaps) if skill_gaps else 'None'}\n"
            f"Job Title: {job.title}\n\n"
            "Provide recommendations as a JSON array of strings."
        )

        try:
            response = await self._generate(prompt)
            # Try to parse JSON from response
            try:
                recommendations = json.loads(response)
                if isinstance(recommendations, list):
                    return [str(r) for r in recommendations]
            except json.JSONDecodeError:
                pass
            # Fallback: split by newlines
            return [line.strip("- ").strip() for line in response.split("\n") if line.strip()]
        except Exception as e:
            logger.warning("recommendation_generation_failed", error=str(e))
            return [
                "Focus on developing the missing and below-level skills "
                "identified in the gap analysis."
            ]

    async def execute(self, **kwargs: Any) -> SkillsGap:
        """Execute skills gap analysis.

        Args:
            **kwargs: Must contain 'candidate' and 'job' keys.

        Returns:
            Skills gap analysis result.
        """
        candidate = kwargs.get("candidate")
        job = kwargs.get("job")
        if not candidate or not job:
            raise ValueError("Both 'candidate' and 'job' are required")
        return await self.analyze_gap(candidate, job)
