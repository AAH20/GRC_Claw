"""API routes for content marketplace."""

from fastapi import APIRouter

from content_marketplace.api.listings import router as listings_router
from content_marketplace.api.pricing import router as pricing_router
from content_marketplace.api.transactions import router as transactions_router
from content_marketplace.api.analytics import router as analytics_router
from content_marketplace.api.trust import router as trust_router

api_router = APIRouter()
api_router.include_router(listings_router, prefix="/listings", tags=["listings"])
api_router.include_router(pricing_router, prefix="/pricing", tags=["pricing"])
api_router.include_router(transactions_router, prefix="/transactions", tags=["transactions"])
api_router.include_router(analytics_router, prefix="/analytics", tags=["analytics"])
api_router.include_router(trust_router, prefix="/trust", tags=["trust"])
