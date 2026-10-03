"""Pydantic models for UGC Marketplace API request/response schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class User(BaseModel):
    """A UGC Marketplace user."""

    id: str = Field(..., description="Unique user identifier")
    username: str = Field(..., description="User's display name")
    email: str = Field(..., description="User's email address")
    avatar_url: str | None = Field(None, description="URL to user's avatar image")
    bio: str | None = Field(None, description="User's biography")
    created_at: datetime = Field(..., description="Account creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class Category(BaseModel):
    """A product category."""

    id: str = Field(..., description="Unique category identifier")
    name: str = Field(..., description="Category name")
    slug: str = Field(..., description="URL-friendly category slug")
    description: str | None = Field(None, description="Category description")
    parent_id: str | None = Field(None, description="Parent category ID for nested categories")


class Product(BaseModel):
    """A UGC Marketplace product listing."""

    id: str = Field(..., description="Unique product identifier")
    seller_id: str = Field(..., description="ID of the seller")
    title: str = Field(..., description="Product title")
    description: str = Field(..., description="Product description")
    price: float = Field(..., ge=0, description="Product price")
    currency: str = Field(default="USD", description="ISO 4217 currency code")
    category_id: str = Field(..., description="Product category ID")
    images: list[str] = Field(default_factory=list, description="List of image URLs")
    tags: list[str] = Field(default_factory=list, description="Product tags")
    status: str = Field(default="active", description="Product status (active, draft, archived)")
    created_at: datetime = Field(..., description="Product creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class Order(BaseModel):
    """A UGC Marketplace order."""

    id: str = Field(..., description="Unique order identifier")
    buyer_id: str = Field(..., description="ID of the buyer")
    seller_id: str = Field(..., description="ID of the seller")
    product_id: str = Field(..., description="ID of the purchased product")
    quantity: int = Field(default=1, ge=1, description="Number of items purchased")
    total_amount: float = Field(..., ge=0, description="Total order amount")
    currency: str = Field(default="USD", description="ISO 4217 currency code")
    status: str = Field(default="pending", description="Order status (pending, paid, fulfilled, cancelled, refunded)")
    created_at: datetime = Field(..., description="Order creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class Review(BaseModel):
    """A product review."""

    id: str = Field(..., description="Unique review identifier")
    product_id: str = Field(..., description="ID of the reviewed product")
    reviewer_id: str = Field(..., description="ID of the reviewer")
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5")
    title: str | None = Field(None, description="Review title")
    body: str = Field(..., description="Review text content")
    created_at: datetime = Field(..., description="Review creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper."""

    items: list[T] = Field(..., description="List of result items")
    total: int = Field(..., ge=0, description="Total number of items available")
    page: int = Field(..., ge=1, description="Current page number")
    per_page: int = Field(..., ge=1, description="Number of items per page")
    has_next: bool = Field(..., description="Whether more pages are available")
    has_prev: bool = Field(..., description="Whether previous pages are available")


class CreateOrderRequest(BaseModel):
    """Request body for creating a new order."""

    product_id: str = Field(..., description="ID of the product to purchase")
    quantity: int = Field(default=1, ge=1, description="Number of items to purchase")


class CreateReviewRequest(BaseModel):
    """Request body for creating a new review."""

    product_id: str = Field(..., description="ID of the product to review")
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5")
    title: str | None = Field(None, description="Review title")
    body: str = Field(..., min_length=1, description="Review text content")


class UpdateProductRequest(BaseModel):
    """Request body for updating a product."""

    title: str | None = Field(None, description="New product title")
    description: str | None = Field(None, description="New product description")
    price: float | None = Field(None, ge=0, description="New product price")
    category_id: str | None = Field(None, description="New category ID")
    images: list[str] | None = Field(None, description="Updated list of image URLs")
    tags: list[str] | None = Field(None, description="Updated list of tags")
    status: str | None = Field(None, description="New product status")


class TokenResponse(BaseModel):
    """OAuth2 token response."""

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="Bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    refresh_token: str | None = Field(None, description="Refresh token for obtaining new access tokens")
