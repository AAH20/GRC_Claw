"""API route aggregators."""

from moderation_queue.api.agents import router as agents_router
from moderation_queue.api.escalations import router as escalations_router
from moderation_queue.api.items import router as items_router
from moderation_queue.api.queues import router as queues_router
from moderation_queue.api.reviews import router as reviews_router

__all__ = [
    "agents_router",
    "escalations_router",
    "items_router",
    "queues_router",
    "reviews_router",
]
