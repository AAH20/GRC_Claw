"""Report API routes."""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get("")
async def list_reports() -> list[dict]:
    """List all reports."""
    return []


@router.post("")
async def create_report(payload: dict) -> dict:
    """Create a new report."""
    return {"report_id": "report_1", "status": "created"}


@router.get("/{report_id}")
async def get_report(report_id: str) -> dict:
    """Get a report by ID."""
    return {"report_id": report_id, "data": {}}
