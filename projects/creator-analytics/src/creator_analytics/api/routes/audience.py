"""Audience analysis API endpoints."""

from fastapi import APIRouter, HTTPException, Depends
from typing import Any
import structlog

from creator_analytics.agents import AudienceAnalyzerAgent
from creator_analytics.models.audience import Audience

logger = structlog.get_logger(__name__)
router = APIRouter()


def get_audience_agent() -> AudienceAnalyzerAgent:
    """Dependency to get audience analyzer agent."""
    return AudienceAnalyzerAgent()


@router.post("/analyze", response_model=dict[str, Any])
async def analyze_audience(
    input_data: dict[str, Any],
    agent: AudienceAnalyzerAgent = Depends(get_audience_agent),
) -> dict[str, Any]:
    """Analyze audience for a creator.

    Args:
        input_data: Input data for audience analysis.
        agent: Audience analyzer agent.

    Returns:
        Audience analysis results.
    """
    try:
        result = await agent.run(input_data)
        return result
    except Exception as e:
        logger.error(f"Audience analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{creator_id}", response_model=dict[str, Any])
async def get_audience(
    creator_id: str,
    agent: AudienceAnalyzerAgent = Depends(get_audience_agent),
) -> dict[str, Any]:
    """Get audience analysis for a creator.

    Args:
        creator_id: Creator identifier.
        agent: Audience analyzer agent.

    Returns:
        Audience analysis results.
    """
    try:
        result = await agent.run({"creator_id": creator_id})
        return result
    except Exception as e:
        logger.error(f"Failed to get audience for {creator_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{creator_id}/segments", response_model=dict[str, Any])
async def get_audience_segments(
    creator_id: str,
    agent: AudienceAnalyzerAgent = Depends(get_audience_agent),
) -> dict[str, Any]:
    """Get audience segments for a creator.

    Args:
        creator_id: Creator identifier.
        agent: Audience analyzer agent.

    Returns:
        Audience segments.
    """
    try:
        result = await agent.run({"creator_id": creator_id})
        return {"creator_id": creator_id, "segments": result.get("segments", [])}
    except Exception as e:
        logger.error(f"Failed to get audience segments for {creator_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
