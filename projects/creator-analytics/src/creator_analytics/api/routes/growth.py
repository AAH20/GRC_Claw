"""Growth prediction API endpoints."""

from fastapi import APIRouter, HTTPException, Depends
from typing import Any
import structlog

from creator_analytics.agents import GrowthPredictorAgent

logger = structlog.get_logger(__name__)
router = APIRouter()


def get_growth_agent() -> GrowthPredictorAgent:
    """Dependency to get growth predictor agent."""
    return GrowthPredictorAgent()


@router.post("/predict", response_model=dict[str, Any])
async def predict_growth(
    input_data: dict[str, Any],
    agent: GrowthPredictorAgent = Depends(get_growth_agent),
) -> dict[str, Any]:
    """Predict growth for a creator.

    Args:
        input_data: Input data for growth prediction.
        agent: Growth predictor agent.

    Returns:
        Growth prediction results.
    """
    try:
        result = await agent.run(input_data)
        return result
    except Exception as e:
        logger.error(f"Growth prediction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{creator_id}", response_model=dict[str, Any])
async def get_growth_prediction(
    creator_id: str,
    agent: GrowthPredictorAgent = Depends(get_growth_agent),
) -> dict[str, Any]:
    """Get growth prediction for a creator.

    Args:
        creator_id: Creator identifier.
        agent: Growth predictor agent.

    Returns:
        Growth prediction.
    """
    try:
        result = await agent.run({"creator_id": creator_id})
        return result
    except Exception as e:
        logger.error(f"Failed to get growth prediction for {creator_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{creator_id}/scenarios", response_model=dict[str, Any])
async def get_growth_scenarios(
    creator_id: str,
    agent: GrowthPredictorAgent = Depends(get_growth_agent),
) -> dict[str, Any]:
    """Get growth scenarios for a creator.

    Args:
        creator_id: Creator identifier.
        agent: Growth predictor agent.

    Returns:
        Growth scenarios.
    """
    try:
        result = await agent.run({"creator_id": creator_id})
        return {
            "creator_id": creator_id,
            "scenarios": {
                "predicted_followers": result.get("predicted_followers", {}),
                "predicted_monthly_revenue": result.get("predicted_monthly_revenue", {}),
            },
        }
    except Exception as e:
        logger.error(f"Failed to get growth scenarios for {creator_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
