"""API route registration for gated-communities."""

from fastapi import APIRouter

from gated_communities.api.routers import (
    analytics,
    comments,
    communities,
    events,
    invitations,
    members,
    messages,
    posts,
    reports,
    settings,
)

api_router = APIRouter()

api_router.include_router(
    members.router,
    prefix="/members",
    tags=["members"],
)

api_router.include_router(
    communities.router,
    prefix="/communities",
    tags=["communities"],
)

api_router.include_router(
    posts.router,
    prefix="/posts",
    tags=["posts"],
)

api_router.include_router(
    comments.router,
    prefix="/comments",
    tags=["comments"],
)

api_router.include_router(
    events.router,
    prefix="/events",
    tags=["events"],
)

api_router.include_router(
    messages.router,
    prefix="/messages",
    tags=["messages"],
)

api_router.include_router(
    analytics.router,
    prefix="/analytics",
    tags=["analytics"],
)

api_router.include_router(
    reports.router,
    prefix="/reports",
    tags=["reports"],
)

api_router.include_router(
    invitations.router,
    prefix="/invitations",
    tags=["invitations"],
)

api_router.include_router(
    settings.router,
    prefix="/settings",
    tags=["settings"],
)
