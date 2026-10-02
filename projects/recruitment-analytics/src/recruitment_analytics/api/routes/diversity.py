"""Diversity analysis endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from recruitment_analytics.agents.diversity_analyzer import DiversityAnalyzerAgent
from recruitment_analytics.config.settings import Settings, get_settings
from recruitment_analytics.integrations.ats_client import ATSClient
from recruitment_analytics.models.schemas import (
    DiversityAnalysisRequest,
    DiversityAnalysisResponse,
)

router = APIRouter()


def get_diversity_agent(settings: Settings = Depends(get_settings)) -> DiversityAnalyzerAgent:
    """Dependency to create DiversityAnalyzerAgent with ATS client."""
    ats_client = ATSClient(
        base_url=settings.ats_api_url,
        api_key=settings.ats_api_key,
    )
    return DiversityAnalyzerAgent(ats_client=ats_client)


@router.post("/analyze", response_model=DiversityAnalysisResponse)
async def analyze_diversity(
    request: DiversityAnalysisRequest,
    agent: DiversityAnalyzerAgent = Depends(get_diversity_agent)  # noqa: B008
) -> DiversityAnalysisResponse:
    """Analyze diversity metrics for given period.

    Args:
        request: Diversity analysis request with date range and dimensions.
        agent: Diversity analyzer agent dependency.

    Returns:
        Diversity analysis response with report and benchmarks.

    Raises:
        HTTPException: If analysis fails.
    """
    try:
        return await agent.run(request)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Diversity analysis failed: {str(e)}",
        ) from e


@router.get("/dimensions", response_model=list[str])
async def get_diversity_dimensions() -> list[str]:
    """Get list of available diversity dimensions.

    Returns:
        List of diversity dimension names.
    """
    return ["gender", "ethnicity", "age", "disability", "veteran_status"]
