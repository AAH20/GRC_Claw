"""Event Management API package."""

from event_management.api.attendees import router as attendees_router
from event_management.api.events import router as events_router

__all__ = ["events_router", "attendees_router"]
