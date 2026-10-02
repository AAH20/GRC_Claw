"""API routes for content optimization endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from seo_optimizer.agents.content_optimization import ContentOptimizationAgent
from seo_optimizer.config import get_settings

router = APIRouter()


class ContentOptimizationRequest(BaseModel):
    """Request model for content optimization.

    Attributes:
        content: The content to analyze and optimize.
        target_keywords: List of target keywords to optimize for.
        content_type: Type of content being optimized.
    """

    content: str = Field(..., description="Content to optimize", min_length=1)
    target_keywords: list[str] = Field(
        ..., description="Target keywords", min_length=1
    )
    content_type: str = Field(default="blog_post", description="Content type")


class ContentOptimizationResponse(BaseModel):
    """Response model for content optimization.

    Attributes:
        task_id: Unique task identifier.
        status: Current status of the optimization.
        result: Optimization results if completed.
    """

    task_id: str
    status: str
    result: dict[str, Any] | None = None


# In-memory task store (replace with Redis/DB in production)
_tasks: dict[str, dict[str, Any]] = {}


@router.post(
    "/optimize",
    response_model=ContentOptimizationResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def optimize_content(
    request: ContentOptimizationRequest,
) -> ContentOptimizationResponse:
    """Start a content optimization task.

    Args:
        request: Content optimization parameters.
        settings: Application settings.

    Returns:
        Task acceptance response with task ID.
    """
    import uuid

    settings = get_settings()
    task_id = str(uuid.uuid4()
    agent = ContentOptimizationAgent(config=settings.model_dump())

    _tasks[task_id] = {
        "status": "pending",
        "agent": agent,
        "request": request,
        "result": None,
    }

    return ContentOptimizationResponse(
        task_id=task_id,
        status="pending",
    )


@router.get("/{task_id}", response_model=ContentOptimizationResponse)
async def get_optimization_results(task_id: str) -> ContentOptimizationResponse:
    """Get content optimization results by task ID.

    Args:
        task_id: The task identifier.

    Returns:
        Optimization results if available.

    Raises:
        HTTPException: If task ID is not found.
    """
    if task_id not in _tasks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found",
        )

    task = _tasks[task_id]
    return ContentOptimizationResponse(
        task_id=task_id,
        status=task["status"],
        result=task.get("result"),
    )
