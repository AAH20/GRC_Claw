"""Predictive hiring endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from recruitment_analytics.agents.predictive_hiring import PredictiveHiringAgent
from recruitment_analytics.config.settings import Settings, get_settings
from recruitment_analytics.integrations.hrms_client import HRMSClient
from recruitment_analytics.models.schemas import (
    PredictiveHiringRequest,
    PredictiveHiringResponse,
)

router = APIRouter()


def get_prediction_agent(settings: Settings = Depends(get_settings)) -> PredictiveHiringAgent:
    """Dependency to create PredictiveHiringAgent with HRMS client."""
    hrms_client = HRMSClient(
        base_url=settings.hrms_api_url,
        api_key=settings.hrms_api_key,
    )
    return PredictiveHiringAgent(hrms_client=hrms_client)


@router.post("/analyze", response_model=PredictiveHiringResponse)
async def predict_hiring(
    request: PredictiveHiringRequest,
    agent: PredictiveHiringAgent = Depends(get_prediction_agent),
) -> PredictiveHiringResponse:
    """Predict candidate success for hiring decision.

    Args:
        request: Predictive hiring request with candidate features.
        agent: Predictive hiring agent dependency.

    Returns:
        Predictive hiring response with prediction and recommendations.

    Raises:
        HTTPException: If prediction fails.
    """
    try:
        return await agent.run(request)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {str(e)}",
        )


@router.get("/outcomes", response_model=list[str])
async def get_prediction_outcomes() -> list[str]:
    """Get list of possible prediction outcomes.

    Returns:
        List of prediction outcome names.
    """
    from recruitment_analytics.models.schemas import PredictionOutcome

    return [outcome.value for outcome in PredictionOutcome]
