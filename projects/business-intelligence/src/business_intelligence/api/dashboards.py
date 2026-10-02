"""Dashboard API routes."""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get("")
async def list_dashboards() -> list[dict]:
    """List all dashboards."""
    return []


@router.get("/{dashboard_id}")
async def get_dashboard(dashboard_id: str) -> dict:
    """Get a dashboard by ID."""
    return {"dashboard_id": dashboard_id, "widgets": []}
