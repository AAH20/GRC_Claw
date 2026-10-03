"""API route registration for UGC Marketplace."""

from fastapi import APIRouter

from ugc_marketplace.api.routers import (
    analytics,
    categories,
    content,
    creators,
    listings,
    notifications,
    payments,
    reviews,
    tags,
    transactions,
)

api_router = APIRouter()

api_router.include_router(creators.router, prefix="/creators", tags=["creators"])
api_router.include_router(content.router, prefix="/content", tags=["content"])
api_router.include_router(listings.router, prefix="/listings", tags=["listings"])
api_router.include_router(transactions.router, prefix="/transactions", tags=["transactions"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(payments.router, prefix="/payments", tags=["payments"])
api_router.include_router(reviews.router, prefix="/reviews", tags=["reviews"])
api_router.include_router(categories.router, prefix="/categories", tags=["categories"])
api_router.include_router(tags.router, prefix="/tags", tags=["tags"])
