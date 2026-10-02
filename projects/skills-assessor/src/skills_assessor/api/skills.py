"""Skills API routes."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException, status

from skills_assessor.config.settings import Settings, get_settings
from skills_assessor.models.schemas import Skill, SkillCategory

if TYPE_CHECKING:
    from uuid import UUID

router = APIRouter(prefix="/skills", tags=["skills"])

# In-memory store for demo purposes
_skills: dict[UUID, Skill] = {}


@router.get("")
async def list_skills(
    category: SkillCategory | None = None,
    skip: int = 0,
    limit: int = 100,
    settings: Settings = Depends(get_settings),
) -> dict:
    """List all skills with optional filtering.

    Args:
        category: Filter by skill category.
        skip: Number of records to skip.
        limit: Maximum number of records to return.
        settings: Application settings.

    Returns:
        dict: Paginated list of skills.
    """
    all_skills = list(_skills.values())
    if category:
        all_skills = [s for s in all_skills if s.category == category]
    paginated = all_skills[skip : skip + limit]
    return {"skills": paginated, "total": len(all_skills)}


@router.get("/{skill_id}")
async def get_skill(
    skill_id: UUID,
    settings: Settings = Depends(get_settings),
) -> Skill:
    """Get a skill by ID.

    Args:
        skill_id: The skill UUID.
        settings: Application settings.

    Returns:
        Skill: The requested skill.

    Raises:
        HTTPException: If skill is not found.
    """
    skill = _skills.get(skill_id)
    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skill {skill_id} not found",
        )
    return skill


@router.post("", response_model=Skill, status_code=status.HTTP_201_CREATED)
async def create_skill(
    skill: Skill,
    settings: Settings = Depends(get_settings),
) -> Skill:
    """Create a new skill.

    Args:
        skill: The skill to create.
        settings: Application settings.

    Returns:
        Skill: The newly created skill.
    """
    _skills[skill.id] = skill
    return skill


@router.delete("/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_skill(
    skill_id: UUID,
    settings: Settings = Depends(get_settings),
) -> None:
    """Delete a skill by ID.

    Args:
        skill_id: The skill UUID.
        settings: Application settings.

    Raises:
        HTTPException: If skill is not found.
    """
    if skill_id not in _skills:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skill {skill_id} not found",
        )
    del _skills[skill_id]
