"""API routers for the compliance platform."""

from __future__ import annotations

from compliance.api.policies import router as policies_router
from compliance.api.violations import router as violations_router

__all__ = ["policies_router", "violations_router"]
