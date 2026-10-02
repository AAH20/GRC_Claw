"""Research API routes for market research operations."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from market_research.agents.analysis import AnalysisRequest, AnalysisResult, AnalysisType
from market_research.agents.data_collection import (
    CollectionRequest,
    CollectionResult,
    DataCollectionAgent,
    DataSource,
)

router = APIRouter(prefix="/api/v1/research", tags=["research"])

# In-memory store for research tasks (replace with database in production)
_research_tasks: dict[str, dict[str, Any]] = {}


class ResearchRequestSchema(BaseModel):
    """Schema for starting a new research task."""

    query: str = Field(..., min_length=1, max_length=500, description="Research query")
    sources: list[str] = Field(
        default_factory=lambda: [s.value for s in DataSource],
        description="Data sources to query",
    )
    analysis_types: list[str] = Field(
        default_factory=lambda: [t.value for t in AnalysisType],
        description="Types of analysis to perform",
    )
    date_range_start: datetime | None = None
    date_range_end: datetime | None = None
    filters: dict[str, Any] = Field(default_factory=dict)


class ResearchResponseSchema(BaseModel):
    """Schema for research task response."""

    task_id: str
    status: str
    message: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ResearchStatusResponseSchema(BaseModel):
    """Schema for research task status response."""

    task_id: str
    status: str
    progress: float = Field(ge=0.0, le=1.0)
    collection_result: CollectionResult | None = None
    analysis_result: AnalysisResult | None = None
    error: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None


@router.post("", response_model=ResearchResponseSchema, status_code=status.HTTP_202_ACCEPTED)
async def start_research(request: ResearchRequestSchema) -> ResearchResponseSchema:
    """Start a new market research task.

    Args:
        request: The research request.

    Returns:
        Research response with task ID.

    Raises:
        HTTPException: If the request is invalid.
    """
    task_id = str(uuid.uuid4())

    try:
        sources = [DataSource(s) for s in request.sources]
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid source: {exc}",
        ) from exc

    try:
        analysis_types = [AnalysisType(t) for t in request.analysis_types]
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid analysis type: {exc}",
        ) from exc

    _research_tasks[task_id] = {
        "task_id": task_id,
        "status": "pending",
        "progress": 0.0,
        "request": request,
        "sources": sources,
        "analysis_types": analysis_types,
        "collection_result": None,
        "analysis_result": None,
        "error": None,
        "created_at": datetime.utcnow(),
        "completed_at": None,
    }

    return ResearchResponseSchema(
        task_id=task_id,
        status="pending",
        message="Research task created successfully",
    )


@router.get("/{task_id}", response_model=ResearchStatusResponseSchema)
async def get_research_status(task_id: str) -> ResearchStatusResponseSchema:
    """Get the status of a research task.

    Args:
        task_id: The task identifier.

    Returns:
        Research task status.

    Raises:
        HTTPException: If the task is not found.
    """
    task = _research_tasks.get(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Research task {task_id} not found",
        )

    return ResearchStatusResponseSchema(
        task_id=task_id,
        status=task["status"],
        progress=task["progress"],
        collection_result=task.get("collection_result"),
        analysis_result=task.get("analysis_result"),
        error=task.get("error"),
        created_at=task["created_at"],
        completed_at=task.get("completed_at"),
    )


@router.post("/{task_id}/collect", response_model=CollectionResult)
async def collect_data(task_id: str) -> CollectionResult:
    """Execute data collection for a research task.

    Args:
        task_id: The task identifier.

    Returns:
        Collection result.

    Raises:
        HTTPException: If the task is not found.
    """
    task = _research_tasks.get(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Research task {task_id} not found",
        )

    task["status"] = "collecting"
    task["progress"] = 0.1

    agent = DataCollectionAgent()
    collection_request = CollectionRequest(
        query=task["request"].query,
        sources=task["sources"],
        date_range_start=task["request"].date_range_start,
        date_range_end=task["request"].date_range_end,
        filters=task["request"].filters,
    )

    result = await agent.collect(collection_request)
    task["collection_result"] = result
    task["progress"] = 0.5

    if result.status.value == "failed":
        task["status"] = "failed"
        task["error"] = "; ".join(result.errors)
    else:
        task["status"] = "collected"

    return result


@router.post("/{task_id}/analyze", response_model=AnalysisResult)
async def analyze_data(task_id: str) -> AnalysisResult:
    """Execute analysis for a research task.

    Args:
        task_id: The task identifier.

    Returns:
        Analysis result.

    Raises:
        HTTPException: If the task is not found or data not collected.
    """
    task = _research_tasks.get(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Research task {task_id} not found",
        )

    if not task.get("collection_result"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Data collection must be completed before analysis",
        )

    task["status"] = "analyzing"
    task["progress"] = 0.6

    from market_research.agents.analysis import AnalysisAgent

    agent = AnalysisAgent()
    analysis_request = AnalysisRequest(
        query=task["request"].query,
        analysis_types=task["analysis_types"],
        data_points=task["collection_result"].data_points,
        collection_result=task["collection_result"],
    )

    result = await agent.analyze(analysis_request)
    task["analysis_result"] = result
    task["progress"] = 1.0
    task["status"] = "completed"
    task["completed_at"] = datetime.utcnow()

    return result


@router.get("/tasks", response_model=list[str])
async def list_research_tasks() -> list[str]:
    """List all research task IDs.

    Returns:
        List of task IDs.
    """
    return list(_research_tasks.keys())
