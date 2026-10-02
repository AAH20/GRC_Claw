"""Brand strategy endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from employer_branding.agents.brand_strategy import BrandStrategyAgent
from employer_branding.models import BrandStrategy, BrandStrategyRequest

router = APIRouter(prefix="/api/v1/strategy", tags=["strategy"])

# In-memory store
_strategy_store: dict[UUID, BrandStrategy] = {}


def get_strategy_agent() -> BrandStrategyAgent:
    """Dependency to get brand strategy agent."""
    return BrandStrategyAgent()


@router.post("/create", response_model=BrandStrategy, status_code=status.HTTP_201_CREATED)
async def create_strategy(
    request: BrandStrategyRequest,
    agent: BrandStrategyAgent = Depends(get_strategy_agent),
) -> BrandStrategy:
    """Create a new employer brand strategy.

    Args:
        request: Brand strategy request.
        agent: Brand strategy agent.

    Returns:
        Created BrandStrategy.

    Raises:
        HTTPException: If creation fails.
    """
    try:
        strategy = await agent.run(request)
        _strategy_store[strategy.id] = strategy
        return strategy
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Strategy creation failed: {exc}",
        ) from exc


@router.get("/{strategy_id}", response_model=BrandStrategy)
async def get_strategy(strategy_id: UUID) -> BrandStrategy:
    """Get a brand strategy by ID.

    Args:
        strategy_id: Strategy UUID.

    Returns:
        BrandStrategy if found.

    Raises:
        HTTPException: If strategy not found.
    """
    if strategy_id not in _strategy_store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Brand strategy {strategy_id} not found",
        )
    return _strategy_store[strategy_id]


@router.get("/", response_model=list[BrandStrategy])
async def list_strategies(
    company_name: str | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[BrandStrategy]:
    """List brand strategies with optional filtering.

    Args:
        company_name: Filter by company name.
        skip: Number of items to skip.
        limit: Maximum items to return.

    Returns:
        List of BrandStrategy objects.
    """
    strategies = list(_strategy_store.values())

    if company_name:
        strategies = [
            s for s in strategies
            if s.company_name.lower() == company_name.lower()
        ]

    return strategies[skip : skip + limit]


@router.patch("/{strategy_id}", response_model=BrandStrategy)
async def update_strategy(
    strategy_id: UUID,
    updates: dict,
) -> BrandStrategy:
    """Update a brand strategy.

    Args:
        strategy_id: Strategy UUID.
        updates: Dictionary of fields to update.

    Returns:
        Updated BrandStrategy.

    Raises:
        HTTPException: If strategy not found.
    """
    if strategy_id not in _strategy_store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Brand strategy {strategy_id} not found",
        )

    strategy = _strategy_store[strategy_id]
    for key, value in updates.items():
        if hasattr(strategy, key):
            setattr(strategy, key, value)

    _strategy_store[strategy_id] = strategy
    return strategy


@router.delete("/{strategy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_strategy(strategy_id: UUID) -> None:
    """Delete a brand strategy.

    Args:
        strategy_id: Strategy UUID.

    Raises:
        HTTPException: If strategy not found.
    """
    if strategy_id not in _strategy_store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Brand strategy {strategy_id} not found",
        )
    del _strategy_store[strategy_id]


@router.post("/{strategy_id}/activate", response_model=BrandStrategy)
async def activate_strategy(strategy_id: UUID) -> BrandStrategy:
    """Activate a brand strategy.

    Args:
        strategy_id: Strategy UUID.

    Returns:
        Activated BrandStrategy.

    Raises:
        HTTPException: If strategy not found.
    """
    if strategy_id not in _strategy_store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Brand strategy {strategy_id} not found",
        )

    strategy = _strategy_store[strategy_id]
    strategy.is_active = True
    _strategy_store[strategy_id] = strategy
    return strategy
