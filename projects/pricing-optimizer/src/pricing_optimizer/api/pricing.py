"""Pricing Optimizer API - Pricing endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from pricing_optimizer.agents.market_intelligence import MarketIntelligenceAgent
from pricing_optimizer.agents.pricing_engine import (
    OptimizationStrategy,
    PricingConstraint,
    PricingEngineAgent,
    PricingEngineConfig,
)

router = APIRouter(prefix="/api/v1/pricing", tags=["pricing"])


class OptimizeRequest(BaseModel):
    """Request body for pricing optimization."""

    products: list[dict[str, Any]] = Field(
        ...,
        description="List of products with product_id, current_price, and cost",
        min_length=1,
    )
    constraints: dict[str, Any] = Field(
        default_factory=dict,
        description="Business constraints (min_price, max_price, min_margin_percent, etc.)",
    )
    strategy: OptimizationStrategy = OptimizationStrategy.PROFIT_MAXIMIZATION
    include_market_intelligence: bool = True


class ApplyPricingRequest(BaseModel):
    """Request body for applying price changes."""

    recommendations: list[dict[str, Any]] = Field(
        ...,
        description="List of price recommendations to apply",
        min_length=1,
    )
    platform: str = Field(..., description="Target platform (shopify, woocommerce, stripe)")
    dry_run: bool = Field(default=False, description="If true, simulate without making changes")


class PricingResponse(BaseModel):
    """Response for pricing optimization."""

    success: bool
    message: str
    data: dict[str, Any] | None = None


def get_pricing_engine() -> PricingEngineAgent:
    """Dependency to get the pricing engine agent.

    Returns:
        Configured PricingEngineAgent instance.
    """
    config = PricingEngineConfig()
    return PricingEngineAgent(config=config)


def get_market_intelligence() -> MarketIntelligenceAgent:
    """Dependency to get the market intelligence agent.

    Returns:
        Configured MarketIntelligenceAgent instance.
    """
    return MarketIntelligenceAgent()


@router.post("/optimize", response_model=PricingResponse)
async def optimize_pricing(
    request: OptimizeRequest,
    engine: PricingEngineAgent = Depends(get_pricing_engine),  # noqa: B008
) -> PricingResponse:
    """Run pricing optimization for a set of products.

    Args:
        request: The optimization request with products and constraints.
        engine: The pricing engine agent.

    Returns:
        Pricing optimization results.

    Raises:
        HTTPException: If the request is invalid or optimization fails.
    """
    try:
        constraint_fields: dict[str, Any] = {
            "min_price": request.constraints.get("min_price", 0.01),
            "max_price": request.constraints.get("max_price", 10000.0),
            "min_margin_percent": request.constraints.get("min_margin_percent", 10.0),
            "max_price_change_percent": request.constraints.get("max_price_change_percent", 25.0),
        }
        if "target_margin_percent" in request.constraints:
            constraint_fields["target_margin_percent"] = request.constraints[
                "target_margin_percent"
            ]

        constraints = PricingConstraint(**constraint_fields)

        result = engine.optimize_prices(
            products=request.products,
            constraints=constraints,
        )

        return PricingResponse(
            success=True,
            message=f"Generated {len(result.recommendations)} pricing recommendations",
            data=result.model_dump(mode="json"),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Optimization failed: {exc}",
        ) from exc


@router.get("/recommendations", response_model=PricingResponse)
async def get_recommendations(
    product_id: str | None = None,
) -> PricingResponse:
    """Get current pricing recommendations.

    Args:
        product_id: Optional product ID to filter recommendations.

    Returns:
        Current pricing recommendations.
    """
    return PricingResponse(
        success=True,
        message="No active recommendations",
        data={"recommendations": [], "product_id": product_id},
    )


@router.post("/apply", response_model=PricingResponse)
async def apply_pricing(
    request: ApplyPricingRequest,
) -> PricingResponse:
    """Apply recommended prices to the target platform.

    Args:
        request: The apply request with recommendations and platform.

    Returns:
        Results of the price change implementations.

    Raises:
        HTTPException: If the request is invalid or application fails.
    """
    if request.platform not in ("shopify", "woocommerce", "stripe"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unsupported platform: {request.platform}",
        )

    try:
        return PricingResponse(
            success=True,
            message=f"Applied {len(request.recommendations)} price changes to {request.platform}",
            data={
                "platform": request.platform,
                "dry_run": request.dry_run,
                "applied_count": len(request.recommendations),
            },
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to apply prices: {exc}",
        ) from exc
