"""Content performance API endpoints."""

from typing import Any

import structlog
from fastapi import APIRouter, Depends, HTTPException

from creator_analytics.agents import ContentPerformanceAgent

logger = structlog.get_logger(__name__)
router = APIRouter()


def get_content_agent() -> ContentPerformanceAgent:
    """Dependency to get content performance agent."""
    return ContentPerformanceAgent()


@router.post("/analyze", response_model=dict[str, Any])
async def analyze_content(
    input_data: dict[str, Any],
    agent: ContentPerformanceAgent = Depends(get_content_agent),  # noqa: B008
) -> dict[str, Any]:
    """Analyze content performance.

    Args:
        input_data: Input data for content analysis.
        agent: Content performance agent.

    Returns:
        Content performance analysis results.
    """
    try:
        result = await agent.run(input_data)
        return result
    except Exception as e:
        logger.error(f"Content analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/{content_id}", response_model=dict[str, Any])
async def get_content_performance(
    content_id: str,
    agent: ContentPerformanceAgent = Depends(get_content_agent),  # noqa: B008
) -> dict[str, Any]:
    """Get performance data for specific content.

    Args:
        content_id: Content identifier.
        agent: Content performance agent.

    Returns:
        Content performance data.
    """
    try:
        result = await agent.run({"content_id": content_id})
        return result
    except Exception as e:
        logger.error(f"Failed to get content performance for {content_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/creator/{creator_id}", response_model=dict[str, Any])
async def get_creator_content(
    creator_id: str,
    agent: ContentPerformanceAgent = Depends(get_content_agent),  # noqa: B008
) -> dict[str, Any]:
    """Get all content performance for a creator.

    Args:
        creator_id: Creator identifier.
        agent: Content performance agent.

    Returns:
        List of content performance data.
    """
    try:
        result = await agent.run({"creator_id": creator_id})
        return {"creator_id": creator_id, "content": result}
    except Exception as e:
        logger.error(f"Failed to get content for creator {creator_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e
