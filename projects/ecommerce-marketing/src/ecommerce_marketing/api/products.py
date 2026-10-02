"""API routes for product and recommendation endpoints."""

from __future__ import annotations

from typing import Any

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from ecommerce_marketing.agents.product_recommendations import (
    Product,
    ProductRecommendationsAgent,
    RecommendationRequest,
)

logger = structlog.get_logger(__name__)

router = APIRouter()


class ProductResponse(BaseModel):
    """Response model for a product."""

    id: str = Field(..., description="Product identifier")
    name: str = Field(..., description="Product name")
    description: str = Field(default="", description="Product description")
    price: float = Field(..., description="Product price")
    category: str = Field(default="", description="Product category")
    tags: list[str] = Field(default_factory=list, description="Product tags")
    in_stock: bool = Field(default=True, description="Whether product is in stock")


class ProductListResponse(BaseModel):
    """Response model for listing products."""

    products: list[ProductResponse] = Field(..., description="List of products")
    total: int = Field(..., description="Total number of products")


class RecommendationResponse(BaseModel):
    """Response model for product recommendations."""

    customer_id: str = Field(..., description="Customer identifier")
    recommendations: list[dict[str, Any]] = Field(..., description="List of recommendations")
    generated_at: str = Field(..., description="Generation timestamp")


# In-memory product catalog for demo purposes — replace with database in production
_products: dict[str, Product] = {}


def _get_demo_products() -> list[Product]:
    """Get demo products for testing.

    Returns:
        List of demo products.
    """
    return [
        Product(
            id="prod_001",
            name="Wireless Noise-Cancelling Headphones",
            description="Premium over-ear headphones with active noise cancellation",
            price=299.99,
            category="Electronics",
            tags=["wireless", "noise-cancelling", "premium"],
            in_stock=True,
        ),
        Product(
            id="prod_002",
            name="Organic Cotton T-Shirt",
            description="Soft, sustainable organic cotton t-shirt",
            price=29.99,
            category="Clothing",
            tags=["organic", "sustainable", "casual"],
            in_stock=True,
        ),
        Product(
            id="prod_003",
            name="Smart Home Hub",
            description="Central control for all your smart home devices",
            price=149.99,
            category="Electronics",
            tags=["smart-home", "automation", "wifi"],
            in_stock=True,
        ),
        Product(
            id="prod_004",
            name="Running Shoes Pro",
            description="Lightweight performance running shoes",
            price=119.99,
            category="Sports",
            tags=["running", "lightweight", "performance"],
            in_stock=True,
        ),
        Product(
            id="prod_005",
            name="Stainless Steel Water Bottle",
            description="Insulated 750ml water bottle, keeps drinks cold for 24h",
            price=34.99,
            category="Lifestyle",
            tags=["insulated", "eco-friendly", "fitness"],
            in_stock=True,
        ),
    ]


@router.get("/products", response_model=ProductListResponse)
async def list_products() -> ProductListResponse:
    """List all available products.

    Returns:
        List of all products in the catalog.
    """
    products = _get_demo_products()
    return ProductListResponse(
        products=[ProductResponse(**p.model_dump()) for p in products],
        total=len(products),
    )


@router.get("/products/{product_id}", response_model=ProductResponse)
async def get_product(product_id: str) -> ProductResponse:
    """Get a specific product by ID.

    Args:
        product_id: Product identifier.

    Returns:
        Product details.

    Raises:
        HTTPException: If product is not found.
    """
    products = _get_demo_products()
    product = next((p for p in products if p.id == product_id), None)

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product {product_id} not found",
        )

    return ProductResponse(**product.model_dump())


@router.post("/recommendations", response_model=RecommendationResponse)
async def get_recommendations(request: RecommendationRequest) -> RecommendationResponse:
    """Get personalized product recommendations for a customer.

    Args:
        request: Recommendation request with customer context.

    Returns:
        Personalized product recommendations.

    Raises:
        HTTPException: If recommendation generation fails.
    """
    try:
        agent = ProductRecommendationsAgent()
        products = _get_demo_products()

        response = await agent.get_recommendations(request, products)

        return RecommendationResponse(
            customer_id=response.customer_id,
            recommendations=[r.model_dump() for r in response.recommendations],
            generated_at=response.generated_at,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.error("Failed to generate recommendations", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate recommendations: {exc}",
        ) from exc
