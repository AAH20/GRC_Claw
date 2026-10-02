"""Cost analysis endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from recruitment_analytics.agents.cost_analyzer import CostAnalyzerAgent
from recruitment_analytics.config.settings import Settings, get_settings
from recruitment_analytics.integrations.hrms_client import HRMSClient
from recruitment_analytics.models.schemas import (
    CostAnalysisRequest,
    CostAnalysisResponse,
)

router = APIRouter()


def get_cost_agent(settings: Settings = Depends(get_settings)) -> CostAnalyzerAgent:
    """Dependency to create CostAnalyzerAgent with HRMS client."""
    hrms_client = HRMSClient(
        base_url=settings.hrms_api_url,
        api_key=settings.hrms_api_key,
    )
    return CostAnalyzerAgent(hrms_client=hrms_client)


@router.post("/analyze", response_model=CostAnalysisResponse)
async def analyze_costs(
    request: CostAnalysisRequest,
    agent: CostAnalyzerAgent = Depends(get_cost_agent),
) -> CostAnalysisResponse:
    """Analyze recruitment costs for given period.

    Args:
        request: Cost analysis request with date range and optional budget.
        agent: Cost analyzer agent dependency.

    Returns:
        Cost analysis response with report and trends.

    Raises:
        HTTPException: If analysis fails.
    """
    try:
        return await agent.run(request)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cost analysis failed: {str(e)}",
        )


@router.get("/categories", response_model=list[str])
async def get_cost_categories() -> list[str]:
    """Get list of available cost categories.

    Returns:
        List of cost category names.
    """
    from recruitment_analytics.models.schemas import CostCategory

    return [cat.value for cat in CostCategory]
