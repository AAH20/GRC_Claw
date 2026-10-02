"""Pricing Optimizer API - Products endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1/products", tags=["products"])


class ProductResponse(BaseModel):
    """Product response model."""

    product_id: str
    name: str
    current_price: float
    cost: float
    category: str | None = None
    platform: str | None = None
    variant_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ProductListResponse(BaseModel):
    """Response for product list endpoint."""

    products: list[ProductResponse]
    total: int
    page: int = 1
    page_size: int = 50


_PRODUCTS: dict[str, ProductResponse] = {
    "prod_001": ProductResponse(
        product_id="prod_001",
        name="Premium Widget",
        current_price=49.99,
        cost=25.00,
        category="widgets",
        platform="shopify",
    ),
    "prod_002": ProductResponse(
        product_id="prod_002",
        name="Standard Gadget",
        current_price=29.99,
        cost=15.00,
        category="gadgets",
        platform="woocommerce",
    ),
    "prod_003": ProductResponse(
        product_id="prod_003",
        name="Deluxe Thingamajig",
        current_price=99.99,
        cost=50.00,
        category="deluxe",
        platform="stripe",
    ),
}


@router.get("", response_model=ProductListResponse)
async def list_products(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=50, ge=1, le=200, description="Items per page"),
    category: str | None = Query(default=None, description="Filter by category"),
    platform: str | None = Query(default=None, description="Filter by platform"),
) -> ProductListResponse:
    """List all products with optional filtering and pagination.

    Args:
        page: Page number (1-indexed).
        page_size: Number of items per page.
        category: Optional category filter.
        platform: Optional platform filter.

    Returns:
        Paginated list of products.
    """
    products = list(_PRODUCTS.values())

    if category:
        products = [p for p in products if p.category == category]
    if platform:
        products = [p for p in products if p.platform == platform]

    total = len(products)
    start = (page - 1) * page_size
    end = start + page_size
    paginated = products[start:end]

    return ProductListResponse(
        products=paginated,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: str) -> ProductResponse:
    """Get a single product by ID.

    Args:
        product_id: The product identifier.

    Returns:
        The product details.

    Raises:
        HTTPException: If the product is not found.
    """
    product = _PRODUCTS.get(product_id)
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product {product_id} not found",
        )
    return product
