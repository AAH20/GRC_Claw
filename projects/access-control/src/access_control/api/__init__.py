"""API layer for the access control service."""

from access_control.api.dependencies import get_settings
from access_control.api.routes import router

__all__ = ["get_settings", "router"]
