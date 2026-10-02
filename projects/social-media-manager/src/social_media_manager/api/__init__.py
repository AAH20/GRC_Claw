"""FastAPI routers and request/response schemas."""

from __future__ import annotations

from social_media_manager.api.analytics import router as analytics_router
from social_media_manager.api.posts import router as posts_router

__all__ = ["analytics_router", "posts_router"]
