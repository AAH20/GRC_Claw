"""Skills assessor API endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.post("/assess")
async def assess_skills(data: dict[str, Any]) -> dict[str, Any]:
    """Assess candidate skills.

    Args:
        data: Dictionary with 'skill_assessments'.

    Returns:
        Assessment results with proficiency scores.
    """
    try:
        from recruitment_platform.agents.skills_assessor.proficiency_scorer import ProficiencyScorer

        agent = ProficiencyScorer()
        result = await agent.process(data)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/learning-path")
async def recommend_learning_path(data: dict[str, Any]) -> dict[str, Any]:
    """Recommend learning path.

    Args:
        data: Dictionary with 'skill_gaps' and 'career_goals'.

    Returns:
        Learning path recommendations.
    """
    from recruitment_platform.agents.skills_assessor.learning_path_recommender import LearningPathRecommender

    agent = LearningPathRecommender()
    result = await agent.process(data)
    return {"success": True, "data": result}


@router.post("/validate-skills")
async def validate_skills(data: dict[str, Any]) -> dict[str, Any]:
    """Validate claimed skills.

    Args:
        data: Dictionary with 'claimed_skills' and 'evidence'.

    Returns:
        Validation results.
    """
    from recruitment_platform.agents.skills_assessor.skill_validator import SkillValidator

    agent = SkillValidator()
    result = await agent.process(data)
    return {"success": True, "data": result}
