"""Revenue tracking API endpoints."""

from fastapi import APIRouter, HTTPException, Depends
from typing import Any
import structlog

from creator_analytics.agents import RevenueTrackerAgent

logger = structlog.get_logger(__name__)
router = APIRouter()


def get_revenue_agent() -> RevenueTrackerAgent:
    """Dependency to get revenue tracker agent."""
    return RevenueTrackerAgent()


@router.post("/report", response_model=dict[str, Any])
async def generate_revenue_report(
    input_data: dict[str, Any],
    agent: RevenueTrackerAgent = Depends(get_revenue_agent),
) -> dict[str, Any]:
    """Generate revenue report for a creator.

    Args:
        input_data: Input data for revenue report.
        agent: Revenue tracker agent.

    Returns:
        Revenue report.
    """
    try:
        result = await agent.run(input_data)
        return result
    except Exception as e:
        logger.error(f"Revenue report generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{creator_id}", response_model=dict[str, Any])
async def get_revenue_report(
    creator_id: str,
    agent: RevenueTrackerAgent = Depends(get_revenue_agent),
) -> dict[str, Any]:
    """Get revenue report for a creator.

    Args:
        creator_id: Creator identifier.
        agent: Revenue tracker agent.

    Returns:
        Revenue report.
    """
    try:
        result = await agent.run({"creator_id": creator_id})
        return result
    except Exception as e:
        logger.error(f"Failed to get revenue report for {creator_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{creator_id}/breakdown", response_model=dict[str, Any])
async def get_revenue_breakdown(
    creator_id: str,
    agent: RevenueTrackerAgent = Depends(get_revenue_agent),
) -> dict[str, Any]:
    """Get revenue breakdown by stream for a creator.

    Args:
        creator_id: Creator identifier.
        agent: Revenue tracker agent.

    Returns:
        Revenue breakdown.
    """
    try:
        result = await agent.run({"creator_id": creator_id})
        return {"creator_id": creator_id, "breakdown": result.get("breakdown", [])}
    except Exception as e:
        logger.error(f"Failed to get revenue breakdown for {creator_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
