"""Data export API endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response

from recruitment_platform.export.export_service import export_service

router = APIRouter()


@router.get("/export/csv")
async def export_csv(
    data: str = Query(..., description="JSON-encoded data to export"),
    fields: str = Query("", description="Comma-separated field names"),
) -> Response:
    """Export data as CSV."""
    import json
    try:
        parsed_data = json.loads(data)
        field_list = fields.split(",") if fields else None
        csv_content = await export_service.export_to_csv(parsed_data, field_list)
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=export.csv"},
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/export/json")
async def export_json(
    data: str = Query(..., description="JSON-encoded data to export"),
) -> Response:
    """Export data as JSON."""
    import json
    try:
        parsed_data = json.loads(data)
        json_content = await export_service.export_to_json(parsed_data)
        return Response(
            content=json_content,
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=export.json"},
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/export/xml")
async def export_xml(
    data: str = Query(..., description="JSON-encoded data to export"),
    root_element: str = Query("records", description="Root XML element name"),
) -> Response:
    """Export data as XML."""
    import json
    try:
        parsed_data = json.loads(data)
        xml_content = await export_service.export_to_xml(parsed_data, root_element)
        return Response(
            content=xml_content,
            media_type="application/xml",
            headers={"Content-Disposition": "attachment; filename=export.xml"},
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
