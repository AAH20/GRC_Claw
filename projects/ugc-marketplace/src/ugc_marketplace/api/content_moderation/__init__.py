"""API routes for content moderation."""

from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, HTTPException, status
from structlog import get_logger

from ugc_marketplace.agents.content_moderation import (
    ImageModerationAgent,
    TextModerationAgent,
    VideoModerationAgent,
)
from ugc_marketplace.models.schemas import (
    BatchModerationRequest,
    BatchModerationResult,
    ContentType,
    ModerationRequest,
    ModerationResult,
)

logger = get_logger(__name__)
router = APIRouter()

_agents: dict[
    ContentType, TextModerationAgent | ImageModerationAgent | VideoModerationAgent
] = {}


def _get_agent(
    content_type: ContentType,
) -> TextModerationAgent | ImageModerationAgent | VideoModerationAgent:
    """Get or create agent for content type.

    Args:
        content_type: Content type to get agent for.

    Returns:
        Moderation agent instance.

    Raises:
        HTTPException: If content type is not supported.
    """
    if content_type not in _agents:
        agent_map = {
            ContentType.TEXT: TextModerationAgent,
            ContentType.IMAGE: ImageModerationAgent,
            ContentType.VIDEO: VideoModerationAgent,
        }
        agent_class = agent_map.get(content_type)
        if agent_class is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported content type: {content_type}",
            )
        _agents[content_type] = agent_class()
    return _agents[content_type]


@router.post("/moderate/text", response_model=ModerationResult)
async def moderate_text(request: ModerationRequest) -> ModerationResult:
    """Moderate text content."""
    request.content_type = ContentType.TEXT
    agent = _get_agent(ContentType.TEXT)
    return await agent.moderate(request.content, str(uuid4()))


@router.post("/moderate/image", response_model=ModerationResult)
async def moderate_image(request: ModerationRequest) -> ModerationResult:
    """Moderate image content."""
    request.content_type = ContentType.IMAGE
    agent = _get_agent(ContentType.IMAGE)
    return await agent.moderate(request.content, str(uuid4()))


@router.post("/moderate/video", response_model=ModerationResult)
async def moderate_video(request: ModerationRequest) -> ModerationResult:
    """Moderate video content."""
    request.content_type = ContentType.VIDEO
    agent = _get_agent(ContentType.VIDEO)
    return await agent.moderate(request.content, str(uuid4()))


@router.post("/moderate/batch", response_model=BatchModerationResult)
async def moderate_batch(request: BatchModerationRequest) -> BatchModerationResult:
    """Moderate multiple content items in batch."""
    results: list[ModerationResult] = []
    for item in request.items:
        agent = _get_agent(item.content_type)
        result = await agent.moderate(item.content, str(uuid4()))
        results.append(result)

    return BatchModerationResult(
        results=results,
        total_processed=len(results),
        total_flagged=sum(1 for r in results if r.action.value == "flag"),
        total_blocked=sum(1 for r in results if r.action.value == "block"),
    )
