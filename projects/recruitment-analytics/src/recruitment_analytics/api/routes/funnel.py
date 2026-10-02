"""Funnel analysis endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from recruitment_analytics.agents.funnel_analyzer import FunnelAnalyzerAgent
from recruitment_analytics.config.settings import Settings, get_settings
from recruitment_analytics.integrations.ats_client import ATSClient
from recruitment_analytics.models.schemas import (
    FunnelAnalysisRequest,
    FunnelAnalysisResponse,
)

router = APIRouter()


def get_funnel_agent(settings: Settings = Depends(get_settings)) -> FunnelAnalyzerAgent:
    """Dependency to create FunnelAnalyzerAgent with ATS client."""
    ats_client = ATSClient(
        base_url=settings.ats_api_url,
        api_key=settings.ats_api_key,
    )
    return FunnelAnalyzerAgent(ats_client=ats_client)


@router.post("/analyze", response_model=FunnelAnalysisResponse)
async def analyze_funnel(
    request: FunnelAnalysisRequest,
    agent: FunnelAnalyzerAgent = Depends(get_funnel_agent)  # noqa: B008
) -> FunnelAnalysisResponse:
    """Analyze recruitment funnel for given period and filters.

    Args:
        request: Funnel analysis request with date range and optional filters.
        agent: Funnel analyzer agent dependency.

    Returns:
        Funnel analysis response with metrics and insights.

    Raises:
        HTTPException: If analysis fails.
    """
    try:
        return await agent.run(request)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Funnel analysis failed: {str(e)}",
        ) from e


@router.get("/stages", response_model=list[str])
async def get_funnel_stages() -> list[str]:
    """Get list of available funnel stages.

    Returns:
        List of funnel stage names.
    """
    from recruitment_analytics.models.schemas import FunnelStage

    return [stage.value for stage in FunnelStage]
