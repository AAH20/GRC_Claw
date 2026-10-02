"""Source tracking endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from recruitment_analytics.agents.source_tracker import SourceTrackerAgent
from recruitment_analytics.config.settings import Settings, get_settings
from recruitment_analytics.integrations.ats_client import ATSClient
from recruitment_analytics.models.schemas import (
    SourceTrackingRequest,
    SourceTrackingResponse,
)

router = APIRouter()


def get_source_agent(settings: Settings = Depends(get_settings)) -> SourceTrackerAgent:
    """Dependency to create SourceTrackerAgent with ATS client."""
    ats_client = ATSClient(
        base_url=settings.ats_api_url,
        api_key=settings.ats_api_key,
    )
    return SourceTrackerAgent(ats_client=ats_client)


@router.post("/analyze", response_model=SourceTrackingResponse)
async def analyze_sources(
    request: SourceTrackingRequest,
    agent: SourceTrackerAgent = Depends(get_source_agent),
) -> SourceTrackingResponse:
    """Analyze recruitment sources for given period.

    Args:
        request: Source tracking request with date range and optional filters.
        agent: Source tracker agent dependency.

    Returns:
        Source tracking response with metrics and insights.

    Raises:
        HTTPException: If analysis fails.
    """
    try:
        return await agent.run(request)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Source analysis failed: {str(e)}",
        )


@router.get("/types", response_model=list[str])
async def get_source_types() -> list[str]:
    """Get list of available source types.

    Returns:
        List of source type names.
    """
    from recruitment_analytics.models.schemas import SourceType

    return [source.value for source in SourceType]
