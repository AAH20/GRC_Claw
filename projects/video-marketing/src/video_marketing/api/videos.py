"""Video API endpoints.

RESTful API for video management including CRUD operations,
script generation triggers, and production workflow management.
"""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from video_marketing.agents.script_generation import ScriptFormat, Tone

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/videos", tags=["videos"])


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class VideoCreateRequest(BaseModel):
    """Request model for creating a video."""

    title: str = Field(..., min_length=1, max_length=200, description="Video title")
    description: str = Field(default="", max_length=5000, description="Video description")
    topic: str = Field(..., min_length=1, max_length=500, description="Video topic/subject")
    script_format: ScriptFormat = Field(default=ScriptFormat.TALKING_HEAD)
    tone: Tone = Field(default=Tone.PROFESSIONAL)
    target_duration_seconds: float = Field(default=60.0, gt=0, le=3600)
    target_audience: str = Field(default="", max_length=500)
    keywords: list[str] = Field(default_factory=list)
    context: str = Field(default="", max_length=10000)
    campaign_id: str = Field(default="", description="Associated campaign ID")


class VideoUpdateRequest(BaseModel):
    """Request model for updating a video."""

    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    status: str | None = None
    tags: list[str] | None = None


class VideoResponse(BaseModel):
    """Response model for video data."""

    id: str
    title: str
    description: str
    topic: str
    status: str
    script_id: str | None = None
    production_id: str | None = None
    duration_seconds: float = 0.0
    thumbnail_url: str | None = None
    video_url: str | None = None
    tags: list[str] = Field(default_factory=list)
    campaign_id: str | None = None
    created_at: str
    updated_at: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class VideoListResponse(BaseModel):
    """Response model for video list."""

    videos: list[VideoResponse]
    total: int
    page: int
    page_size: int


class ScriptGenerationResponse(BaseModel):
    """Response model for script generation."""

    video_id: str
    script: dict[str, Any]
    status: str


# ---------------------------------------------------------------------------
# In-memory store (replace with database in production)
# ---------------------------------------------------------------------------

_videos: dict[str, dict[str, Any]] = {}


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def _get_video_or_404(video_id: str) -> dict[str, Any]:
    """Get a video by ID or raise 404."""
    if video_id not in _videos:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Video '{video_id}' not found",
        )
    return _videos[video_id]


# ---------------------------------------------------------------------------
# API endpoints
# ---------------------------------------------------------------------------


@router.post("", response_model=VideoResponse, status_code=status.HTTP_201_CREATED)
async def create_video(request: VideoCreateRequest) -> VideoResponse:
    """Create a new video project.

    Creates a video entry and optionally triggers script generation.
    """
    video_id = str(uuid.uuid4())
    now = datetime.now(UTC).isoformat()

    video = {
        "id": video_id,
        "title": request.title,
        "description": request.description,
        "topic": request.topic,
        "status": "draft",
        "script_id": None,
        "production_id": None,
        "duration_seconds": request.target_duration_seconds,
        "thumbnail_url": None,
        "video_url": None,
        "tags": request.keywords,
        "campaign_id": request.campaign_id or None,
        "created_at": now,
        "updated_at": now,
        "metadata": {
            "script_format": request.script_format.value,
            "tone": request.tone.value,
            "target_audience": request.target_audience,
            "context": request.context,
        },
    }

    _videos[video_id] = video
    logger.info("Video created", extra={"video_id": video_id, "title": request.title})
    return VideoResponse(**video)


@router.get("", response_model=VideoListResponse)
async def list_videos(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status_filter: str | None = Query(default=None, alias="status"),
    campaign_id: str | None = None,
) -> VideoListResponse:
    """List videos with pagination and filtering."""
    videos = list(_videos.values())

    if status_filter:
        videos = [v for v in videos if v["status"] == status_filter]
    if campaign_id:
        videos = [v for v in videos if v.get("campaign_id") == campaign_id]

    total = len(videos)
    start = (page - 1) * page_size
    end = start + page_size
    paginated = videos[start:end]

    return VideoListResponse(
        videos=[VideoResponse(**v) for v in paginated],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{video_id}", response_model=VideoResponse)
async def get_video(video_id: str) -> VideoResponse:
    """Get a video by ID."""
    video = _get_video_or_404(video_id)
    return VideoResponse(**video)


@router.patch("/{video_id}", response_model=VideoResponse)
async def update_video(video_id: str, request: VideoUpdateRequest) -> VideoResponse:
    """Update a video."""
    video = _get_video_or_404(video_id)

    update_data = request.model_dump(exclude_unset=True)
    for field_name, value in update_data.items():
        if value is not None:
            video[field_name] = value

    video["updated_at"] = datetime.now(UTC).isoformat()
    logger.info("Video updated", extra={"video_id": video_id})
    return VideoResponse(**video)


@router.delete("/{video_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_video(video_id: str) -> None:
    """Delete a video."""
    _get_video_or_404(video_id)
    del _videos[video_id]
    logger.info("Video deleted", extra={"video_id": video_id})


@router.post("/{video_id}/generate-script", response_model=ScriptGenerationResponse)
async def generate_script(video_id: str) -> ScriptGenerationResponse:
    """Trigger script generation for a video.

    Uses the ScriptGenerationAgent to create a script from the video's
    topic and metadata.
    """
    video = _get_video_or_404(video_id)

    try:
        from video_marketing.agents.script_generation import ScriptGenerationAgent

        agent = ScriptGenerationAgent()
        script = await agent.generate_script(
            topic=video["topic"],
            format=ScriptFormat(video["metadata"].get("script_format", "talking_head")),
            tone=Tone(video["metadata"].get("tone", "professional")),
            target_duration=video["duration_seconds"],
            target_audience=video["metadata"].get("target_audience", ""),
            keywords=video.get("tags", []),
            context=video["metadata"].get("context", ""),
        )

        script_id = str(uuid.uuid4())
        video["script_id"] = script_id
        video["status"] = "scripted"
        video["updated_at"] = datetime.now(UTC).isoformat()

        return ScriptGenerationResponse(
            video_id=video_id,
            script=script.to_dict(),
            status="completed",
        )
    except Exception as exc:
        logger.error("Script generation failed", exc_info=True, extra={"video_id": video_id})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Script generation failed: {exc}",
        ) from exc


@router.post("/{video_id}/start-production")
async def start_production(video_id: str) -> dict[str, Any]:
    """Start production for a video.

    Creates a production project and transitions the video to production status.
    """
    video = _get_video_or_404(video_id)

    if not video.get("script_id"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Video must have a script before starting production",
        )

    try:
        from video_marketing.agents.production import ProductionAgent

        agent = ProductionAgent()
        production = await agent.create_production(
            title=video["title"],
            script_id=video["script_id"],
        )

        video["production_id"] = production.id
        video["status"] = "in_production"
        video["updated_at"] = datetime.now(UTC).isoformat()

        return {
            "video_id": video_id,
            "production_id": production.id,
            "status": "pending",
        }
    except Exception as exc:
        logger.error("Production start failed", exc_info=True, extra={"video_id": video_id})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start production: {exc}",
        ) from exc


@router.get("/{video_id}/status")
async def get_video_status(video_id: str) -> dict[str, Any]:
    """Get comprehensive status for a video.

    Includes script, production, editing, and distribution status.
    """
    video = _get_video_or_404(video_id)

    return {
        "video_id": video_id,
        "title": video["title"],
        "status": video["status"],
        "script_id": video.get("script_id"),
        "production_id": video.get("production_id"),
        "has_script": video.get("script_id") is not None,
        "is_in_production": video.get("production_id") is not None,
        "created_at": video["created_at"],
        "updated_at": video["updated_at"],
    }
