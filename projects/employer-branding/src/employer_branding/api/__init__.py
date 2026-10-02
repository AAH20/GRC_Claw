"""API routes for employer branding platform."""

from employer_branding.api.health import router as health_router
from employer_branding.api.content import router as content_router
from employer_branding.api.sentiment import router as sentiment_router
from employer_branding.api.reputation import router as reputation_router
from employer_branding.api.reviews import router as reviews_router
from employer_branding.api.strategy import router as strategy_router

__all__ = [
    "health_router",
    "content_router",
    "sentiment_router",
    "reputation_router",
    "reviews_router",
    "strategy_router",
]
