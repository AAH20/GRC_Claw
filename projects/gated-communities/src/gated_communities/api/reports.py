"""
Reports API endpoints for gated-communities.

Provides endpoints to list available reports and generate new reports.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timedelta
import uuid

router = APIRouter()


# ─── Mock Data ───────────────────────────────────────────────────────────────

AVAILABLE_REPORTS = [
    {
        "id": "rpt_001",
        "name": "Community Activity Summary",
        "description": "Daily active users, posts, and engagement metrics for all gated communities.",
        "category": "analytics",
        "format": "pdf",
        "estimated_duration_seconds": 45,
    },
    {
        "id": "rpt_002",
        "name": "Member Growth Report",
        "description": "New member sign-ups, churn rate, and retention cohorts over a configurable period.",
        "category": "growth",
        "format": "csv",
        "estimated_duration_seconds": 20,
    },
    {
        "id": "rpt_003",
        "name": "Content Moderation Audit",
        "description": "Flagged posts, moderator actions, and policy violation trends.",
        "category": "moderation",
        "format": "pdf",
        "estimated_duration_seconds": 60,
    },
    {
        "id": "rpt_004",
        "name": "Revenue & Subscriptions",
        "description": "MRR, ARPU, subscription tier breakdown, and payment failure rates.",
        "category": "finance",
        "format": "xlsx",
        "estimated_duration_seconds": 30,
    },
    {
        "id": "rpt_005",
        "name": "Access Control Review",
        "description": "Gate configuration changes, permission escalations, and failed access attempts.",
        "category": "security",
        "format": "pdf",
        "estimated_duration_seconds": 25,
    },
]


# ─── Request / Response Models ───────────────────────────────────────────────

class GenerateReportRequest(BaseModel):
    report_id: str = Field(..., description="ID of the report to generate.")
    start_date: Optional[str] = Field(None, description="Start date (ISO 8601).")
    end_date: Optional[str] = Field(None, description="End date (ISO 8601).")
    community_id: Optional[str] = Field(None, description="Filter by community ID.")
    format: Optional[str] = Field("pdf", description="Output format: pdf, csv, xlsx.")


class GenerateReportResponse(BaseModel):
    report_instance_id: str
    report_id: str
    report_name: str
    status: str
    format: str
    created_at: str
    download_url: Optional[str] = None
    message: str


# ─── Endpoints ───────────────────────────────────────────────────────────────

@router.get("/reports", response_model=List[dict])
async def list_reports():
    """
    GET /reports — List all available report types.
    """
    return AVAILABLE_REPORTS


@router.post("/reports/generate", response_model=GenerateReportResponse)
async def generate_report(request: GenerateReportRequest):
    """
    POST /reports/generate — Generate a report instance.
    """
    # Validate report_id exists
    report = next((r for r in AVAILABLE_REPORTS if r["id"] == request.report_id), None)
    if not report:
        raise HTTPException(
            status_code=404,
            detail=f"Report with id '{request.report_id}' not found.",
        )

    # Validate format
    allowed_formats = {"pdf", "csv", "xlsx"}
    fmt = (request.format or report["format"]).lower()
    if fmt not in allowed_formats:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format '{fmt}'. Allowed: {sorted(allowed_formats)}.",
        )

    now = datetime.utcnow()
    instance_id = f"rpti_{uuid.uuid4().hex[:12]}"

    return GenerateReportResponse(
        report_instance_id=instance_id,
        report_id=report["id"],
        report_name=report["name"],
        status="completed",
        format=fmt,
        created_at=now.isoformat() + "Z",
        download_url=f"/api/v1/reports/download/{instance_id}",
        message=f"Report '{report['name']}' generated successfully.",
    )
