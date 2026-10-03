"""
Gated Communities - API Routes.

Consolidated router that includes all sub-project API routes.
"""

from typing import Any

from fastapi import APIRouter

router = APIRouter()

# Import and include all sub-project routers
# These are populated from the consolidated agent modules


@router.get("/status")
async def get_status() -> dict[str, Any]:
    """Get overall API status."""
    return {
        "status": "operational",
        "modules": [
            "tier-management",
            "moderation-queue",
            "access-control",
            "community-health-scorer",
            "member-verification",
            "escalation-workflow",
            "reputation-system",
            "compliance-monitor",
            "moderation-analytics",
            "community-governance",
        ],
    }
