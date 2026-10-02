"""Pricing API routes."""

from __future__ import annotations

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from content_marketplace.agents.pricing_optimizer import PricingOptimizerAgent
from content_marketplace.models.pricing import Pricing, PricingCreate, PricingUpdate

logger = logging.getLogger(__name__)
router = APIRouter()


def get_pricing_agent() -> PricingOptimizerAgent:
    """Dependency to get the pricing optimizer agent."""
    return PricingOptimizerAgent()


@router.post("", response_model=Pricing, status_code=status.HTTP_201_CREATED)
async def create_pricing(
    data: PricingCreate,
    agent: PricingOptimizerAgent = Depends(get_pricing_agent),
) -> Pricing:
    """Create a new pricing entry."""
    return await agent.create_pricing(data)


@router.get("/{pricing_id}", response_model=Pricing)
async def get_pricing(
    pricing_id: UUID,
    agent: PricingOptimizerAgent = Depends(get_pricing_agent),
) -> Pricing:
    """Get a pricing entry by ID."""
    try:
        return await agent.get_pricing(pricing_id)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pricing not found")


@router.put("/{pricing_id}", response_model=Pricing)
async def update_pricing(
    pricing_id: UUID,
    data: PricingUpdate,
    agent: PricingOptimizerAgent = Depends(get_pricing_agent),
) -> Pricing:
    """Update an existing pricing entry."""
    try:
        return await agent.update_pricing(pricing_id, data)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pricing not found")


@router.post("/{pricing_id}/optimize", response_model=Pricing)
async def optimize_pricing(
    pricing_id: UUID,
    agent: PricingOptimizerAgent = Depends(get_pricing_agent),
) -> Pricing:
    """Optimize a pricing entry using AI."""
    try:
        return await agent.optimize_price(pricing_id)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pricing not found")


@router.get("/listing/{listing_id}", response_model=Pricing)
async def get_pricing_for_listing(
    listing_id: UUID,
    agent: PricingOptimizerAgent = Depends(get_pricing_agent),
) -> Pricing:
    """Get pricing for a specific listing."""
    pricing = await agent.get_pricing_for_listing(listing_id)
    if pricing is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pricing not found for listing")
    return pricing


@router.post("/bulk-optimize")
async def bulk_optimize_pricing(
    category: Optional[str] = None,
    agent: PricingOptimizerAgent = Depends(get_pricing_agent),
) -> list[Pricing]:
    """Optimize prices for multiple listings."""
    return await agent.bulk_optimize(category=category)
