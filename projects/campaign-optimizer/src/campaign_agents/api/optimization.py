"""Optimization API routes — Multi-armed bandit optimization endpoints."""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from campaign_agents.agents.optimizer import MultiArmedBanditOptimizer
from campaign_agents.models.optimization import (
    ArmConfig,
    BanditAlgorithm,
    BanditConfig,
    OptimizationResult,
    OptimizationStrategy,
)

logger = structlog.get_logger(__name__)

router = APIRouter()


# ─── Request/Response Models ────────────────────────────────────────


class OptimizeRequest(BaseModel):
    """Request model for optimization."""

    campaign_id: str = Field(..., min_length=1)
    strategy: OptimizationStrategy = Field(default=OptimizationStrategy.MULTI_ARMED_BANDIT)
    algorithm: BanditAlgorithm = Field(default=BanditAlgorithm.UCB1)
    arms: list[dict[str, Any]] = Field(..., min_length=2)
    reward_metric: str = Field(default="conversion_rate")
    epsilon: float = Field(default=0.1, ge=0.0, le=1.0)
    exploration_factor: float = Field(default=1.414, gt=0.0)


class BanditArmUpdateRequest(BaseModel):
    """Request model for updating bandit arm rewards."""

    arm_id: str = Field(..., min_length=1)
    reward: float = Field(...)


class BanditStatusResponse(BaseModel):
    """Response model for bandit status."""

    campaign_id: str
    algorithm: str
    total_pulls: int
    total_reward: float
    arms: list[dict[str, Any]]
    history_count: int


# ─── In-Memory Store ────────────────────────────────────────────────

_optimizers: dict[str, MultiArmedBanditOptimizer] = {}


# ─── Routes ─────────────────────────────────────────────────────────


@router.post("/bandit/optimize", response_model=OptimizationResult)
async def run_bandit_optimization(request: OptimizeRequest) -> OptimizationResult:
    """Run a multi-armed bandit optimization cycle.

    Args:
        request: Optimization request with bandit configuration.

    Returns:
        OptimizationResult with recommendations.

    Raises:
        HTTPException: If optimization fails.
    """
    try:
        arm_configs = [
            ArmConfig(
                arm_id=arm.get("arm_id", f"arm_{i}"),
                name=arm.get("name", f"Arm {i}"),
                initial_reward=arm.get("initial_reward", 0.0),
                initial_pulls=arm.get("initial_pulls", 0),
                metadata=arm.get("metadata", {}),
            )
            for i, arm in enumerate(request.arms)
        ]

        config = BanditConfig(
            algorithm=request.algorithm,
            epsilon=request.epsilon,
            exploration_factor=request.exploration_factor,
            arms=arm_configs,
            reward_metric=request.reward_metric,
        )

        optimizer = MultiArmedBanditOptimizer(config)
        result = optimizer.optimize(request.campaign_id)
        _optimizers[request.campaign_id] = optimizer

        logger.info(
            "Bandit optimization completed",
            campaign_id=request.campaign_id,
            algorithm=request.algorithm.value,
        )
        return result

    except Exception as e:
        logger.error("Bandit optimization failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Optimization failed: {str(e)}",
        ) from e


@router.post("/bandit/{campaign_id}/update")
async def update_bandit_reward(
    campaign_id: str, request: BanditArmUpdateRequest
) -> dict[str, Any]:
    """Update the reward for a bandit arm.

    Args:
        campaign_id: The campaign identifier.
        request: Arm update with reward value.

    Returns:
        Updated bandit status.

    Raises:
        HTTPException: If campaign or arm not found.
    """
    optimizer = _optimizers.get(campaign_id)
    if not optimizer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No optimizer found for campaign {campaign_id}",
        )

    try:
        optimizer.update_reward(request.arm_id, request.reward)
        return {
            "status": "updated",
            "campaign_id": campaign_id,
            "arm_id": request.arm_id,
            "reward": request.reward,
            "timestamp": datetime.now(UTC).isoformat(),
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.get("/bandit/{campaign_id}/status", response_model=BanditStatusResponse)
async def get_bandit_status(campaign_id: str) -> BanditStatusResponse:
    """Get the current status of a bandit optimizer.

    Args:
        campaign_id: The campaign identifier.

    Returns:
        Current bandit status.

    Raises:
        HTTPException: If campaign not found.
    """
    optimizer = _optimizers.get(campaign_id)
    if not optimizer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No optimizer found for campaign {campaign_id}",
        )

    states = optimizer.get_state()
    return BanditStatusResponse(
        campaign_id=campaign_id,
        algorithm=optimizer.config.algorithm.value,
        total_pulls=optimizer._total_pulls,
        total_reward=optimizer._total_reward,
        arms=[s.model_dump() for s in states],
        history_count=len(optimizer.get_history()),
    )


@router.post("/bandit/{campaign_id}/reset")
async def reset_bandit(campaign_id: str) -> dict[str, str]:
    """Reset a bandit optimizer to initial state.

    Args:
        campaign_id: The campaign identifier.

    Returns:
        Reset confirmation.

    Raises:
        HTTPException: If campaign not found.
    """
    optimizer = _optimizers.get(campaign_id)
    if not optimizer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No optimizer found for campaign {campaign_id}",
        )

    optimizer.reset()
    return {"status": "reset", "campaign_id": campaign_id}
