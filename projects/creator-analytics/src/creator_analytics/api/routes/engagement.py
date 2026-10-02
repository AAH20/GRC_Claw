"""Engagement analysis API endpoints."""

from fastapi import APIRouter, HTTPException, Depends
from typing import Any
import structlog

from creator_analytics.agents import EngagementAnalyzerAgent

logger = structlog.get_logger(__name__)
router = APIRouter()


def get_engagement_agent() -> EngagementAnalyzerAgent:
    """Dependency to get engagement analyzer agent."""
    return EngagementAnalyzerAgent()


@router.post("/report", response_model=dict[str, Any])
async def generate_engagement_report(
    input_data: dict[str, Any],
    agent: EngagementAnalyzerAgent = Depends(get_engagement_agent),
) -> dict[str, Any]:
    """Generate engagement report for a creator.

    Args:
        input_data: Input data for engagement report.
        agent: Engagement analyzer agent.

    Returns:
        Engagement report.
    """
    try:
        result = await agent.run(input_data)
        return result
    except Exception as e:
        logger.error(f"Engagement report generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{creator_id}", response_model=dict[str, Any])
async def get_engagement_report(
    creator_id: str,
    agent: EngagementAnalyzerAgent = Depends(get_engagement_agent),
) -> dict[str, Any]:
    """Get engagement report for a creator.

    Args:
        creator_id: Creator identifier.
        agent: Engagement analyzer agent.

    Returns:
        Engagement report.
    """
    try:
        result = await agent.run({"creator_id": creator_id})
        return result
    except Exception as e:
        logger.error(f"Failed to get engagement report for {creator_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{creator_id}/metrics", response_model=dict[str, Any])
async def get_engagement_metrics(
    creator_id: str,
    agent: EngagementAnalyzerAgent = Depends(get_engagement_agent),
) -> dict[str, Any]:
    """Get engagement metrics for a creator.

    Args:
        creator_id: Creator identifier.
        agent: Engagement analyzer agent.

    Returns:
        Engagement metrics.
    """
    try:
        result = await agent.run({"creator_id": creator_id})
        return {"creator_id": creator_id, "metrics": result.get("metrics", {})}
    except Exception as e:
        logger.error(f"Failed to get engagement metrics for {creator_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
