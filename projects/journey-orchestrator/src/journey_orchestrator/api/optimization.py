"""Optimization API routes."""
from __future__ import annotations

from datetime import UTC, datetime

import structlog
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from journey_orchestrator.agents.journey_optimization import (
    JourneyOptimization,
    OptimizationRequest,
)
from journey_orchestrator.models.analytics import MetricType

logger = structlog.get_logger(__name__)
router = APIRouter()

# In-memory store for optimization results (replace with database in production)
_optimization_results: dict[str, dict] = {}


class OptimizationRequestSchema(BaseModel):
    """API request schema for optimization."""

    journey_id: str = Field(..., description="The journey ID to optimize")
    target_metric: str = Field(default="conversion_rate", description="Metric to optimize for")
    optimization_goal: str = Field(default="maximize", description="maximize or minimize")
    constraints: dict = Field(default_factory=dict, description="Optimization constraints")
    auto_apply: bool = Field(default=False, description="Auto-apply safe optimizations")
    max_suggestions: int = Field(default=5, ge=1, le=20)


class OptimizationResponse(BaseModel):
    """API response schema for optimization."""

    journey_id: str
    target_metric: str
    current_value: float
    projected_value: float
    improvement_potential: float
    suggestions_count: int
    applied_count: int
    requires_approval_count: int
    generated_at: datetime


class ApplyOptimizationRequest(BaseModel):
    """API request to apply an optimization."""

    journey_id: str = Field(..., description="The journey ID")
    suggestion_id: str = Field(..., description="The suggestion to apply")


@router.post("", response_model=OptimizationResponse, status_code=200)
async def optimize_journey(request: OptimizationRequestSchema) -> OptimizationResponse:
    """Get optimization suggestions for a journey.

    Args:
        request: The optimization request.

    Returns:
        The optimization response with suggestions.

    Raises:
        HTTPException: If optimization fails.
    """
    if not request.journey_id.strip():
        raise HTTPException(status_code=400, detail="journey_id must not be empty")

    try:
        metric_type = MetricType(request.target_metric)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid target_metric: {e}") from e

    optimization_request = OptimizationRequest(
        journey_id=request.journey_id,
        target_metric=metric_type,
        optimization_goal=request.optimization_goal,
        constraints=request.constraints,
        auto_apply=request.auto_apply,
        max_suggestions=request.max_suggestions,
    )

    agent = JourneyOptimization()
    try:
        result = await agent.optimize(optimization_request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    # Store result
    _optimization_results[request.journey_id] = result.model_dump()

    logger.info(
        "Optimization computed via API",
        journey_id=request.journey_id,
        suggestions=len(result.suggestions),
        improvement=result.improvement_potential,
    )

    return OptimizationResponse(
        journey_id=result.journey_id,
        target_metric=result.target_metric,
        current_value=result.current_value,
        projected_value=result.projected_value,
        improvement_potential=result.improvement_potential,
        suggestions_count=len(result.suggestions),
        applied_count=len(result.applied_changes),
        requires_approval_count=len(result.requires_approval),
        generated_at=result.generated_at,
    )


@router.post("/apply", response_model=dict)
async def apply_optimization(request: ApplyOptimizationRequest) -> dict:
    """Apply an optimization suggestion to a journey.

    Args:
        request: The apply optimization request.

    Returns:
        The result of applying the optimization.

    Raises:
        HTTPException: If the optimization cannot be applied.
    """
    if not request.journey_id.strip():
        raise HTTPException(status_code=400, detail="journey_id must not be empty")
    if not request.suggestion_id.strip():
        raise HTTPException(status_code=400, detail="suggestion_id must not be empty")

    agent = JourneyOptimization()
    try:
        result = await agent.apply_optimization(
            journey_id=request.journey_id,
            suggestion_id=request.suggestion_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e

    logger.info(
        "Optimization applied via API",
        journey_id=request.journey_id,
        suggestion_id=request.suggestion_id,
    )
    return result


@router.get("/{journey_id}", response_model=OptimizationResponse)
async def get_optimization_result(journey_id: str) -> OptimizationResponse:
    """Get cached optimization result for a journey.

    Args:
        journey_id: The journey ID.

    Returns:
        The cached optimization response.

    Raises:
        HTTPException: If no optimization result found.
    """
    result = _optimization_results.get(journey_id)
    if not result:
        raise HTTPException(
            status_code=404,
            detail="No optimization result found. Run POST /optimization first.",
        )

    return OptimizationResponse(
        journey_id=result["journey_id"],
        target_metric=result["target_metric"],
        current_value=result["current_value"],
        projected_value=result["projected_value"],
        improvement_potential=result["improvement_potential"],
        suggestions_count=len(result.get("suggestions", [])),
        applied_count=len(result.get("applied_changes", [])),
        requires_approval_count=len(result.get("requires_approval", [])),
        generated_at=datetime.now(UTC),
    )
