"""Export functionality for data."""
from __future__ import annotations

import csv
import io
import json
import logging

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/export/members")
async def export_members(
    format: str = Query("csv", regex="^(csv|json)$"),  # noqa: A002
    community_id: str | None = None,
) -> StreamingResponse:
    """Export members data in CSV or JSON format."""
    # Sample data - replace with actual database query
    members = [
        {"id": "1", "name": "Alice", "email": "alice@example.com", "role": "admin"},
        {"id": "2", "name": "Bob", "email": "bob@example.com", "role": "member"},
    ]

    if format == "json":
        content = json.dumps(members, indent=2)
        return StreamingResponse(
            io.StringIO(content),
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=members.json"},
        )

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["id", "name", "email", "role"])
    writer.writeheader()
    writer.writerows(members)
    output.seek(0)
    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=members.csv"},
    )


@router.get("/export/analytics")
async def export_analytics(
    format: str = Query("csv", regex="^(csv|json)$"),  # noqa: A002
    days: int = Query(30, ge=1, le=365),
) -> StreamingResponse:
    """Export analytics data in CSV or JSON format."""
    analytics = [
        {"date": "2024-01-01", "active_users": 100, "new_members": 10},
        {"date": "2024-01-02", "active_users": 120, "new_members": 15},
    ]

    if format == "json":
        content = json.dumps(analytics, indent=2)
        return StreamingResponse(
            io.StringIO(content),
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=analytics.json"},
        )

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["date", "active_users", "new_members"])
    writer.writeheader()
    writer.writerows(analytics)
    output.seek(0)
    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=analytics.csv"},
    )
