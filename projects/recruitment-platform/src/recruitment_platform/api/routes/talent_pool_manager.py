"""Talent pool manager API endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.post("/source")
async def source_candidates(data: dict[str, Any]) -> dict[str, Any]:
    """Source candidates from talent pool.

    Args:
        data: Dictionary with 'job_requirements' and 'pool_criteria'.

    Returns:
        Sourced candidates with match scores.
    """
    try:
        from recruitment_platform.agents.talent_pool_manager.candidate_sourcer import (
            CandidateSourcer,
        )

        agent = CandidateSourcer()
        result = await agent.process(data)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/analyze-pool")
async def analyze_pool(data: dict[str, Any]) -> dict[str, Any]:
    """Analyze talent pool health.

    Args:
        data: Dictionary with 'pool_data' and 'hiring_needs'.

    Returns:
        Pool analysis results.
    """
    from recruitment_platform.agents.talent_pool_manager.pool_analyzer import PoolAnalyzer

    agent = PoolAnalyzer()
    result = await agent.process(data)
    return {"success": True, "data": result}


@router.post("/recommend")
async def recommend_talent(data: dict[str, Any]) -> dict[str, Any]:
    """Recommend talent for a position.

    Args:
        data: Dictionary with 'job' and 'pool_members'.

    Returns:
        Ranked recommendations.
    """
    from recruitment_platform.agents.talent_pool_manager.talent_recommender import TalentRecommender

    agent = TalentRecommender()
    result = await agent.process(data)
    return {"success": True, "data": result}


@router.post("/track-engagement")
async def track_engagement(data: dict[str, Any]) -> dict[str, Any]:
    """Track candidate engagement.

    Args:
        data: Dictionary with 'candidate_id' and 'interactions'.

    Returns:
        Engagement metrics.
    """
    from recruitment_platform.agents.talent_pool_manager.engagement_tracker import EngagementTracker

    agent = EngagementTracker()
    result = await agent.process(data)
    return {"success": True, "data": result}
