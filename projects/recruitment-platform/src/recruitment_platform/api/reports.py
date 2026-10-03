"""
Reports API endpoints for the recruitment platform.

Provides endpoints to list available reports and generate new reports.
"""

from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

router = APIRouter(prefix="/reports", tags=["reports"])


# ─── Models ──────────────────────────────────────────────────────────────────


class ReportInfo(BaseModel):
    """Metadata describing an available report."""

    id: str
    name: str
    description: str
    category: str
    format: str = "pdf"
    estimated_runtime_seconds: int = Field(default=30, ge=1)


class ReportSummary(BaseModel):
    """Summary of a generated report instance."""

    report_id: str
    name: str
    status: str
    created_at: str
    completed_at: str | None = None
    download_url: str | None = None
    format: str = "pdf"
    size_bytes: int | None = None


class GenerateReportRequest(BaseModel):
    """Request body for generating a report."""

    report_type: str = Field(..., description="Type of report to generate")
    start_date: str | None = Field(
        default=None, description="Start date (ISO 8601) for the reporting period"
    )
    end_date: str | None = Field(
        default=None, description="End date (ISO 8601) for the reporting period"
    )
    department: str | None = Field(
        default=None, description="Filter by department"
    )
    format: str = Field(default="pdf", description="Output format (pdf, csv, xlsx)")
    include_inactive: bool = Field(
        default=False, description="Include inactive records"
    )


class GenerateReportResponse(BaseModel):
    """Response returned after requesting report generation."""

    success: bool
    message: str
    report: ReportSummary


# ─── Mock Data ───────────────────────────────────────────────────────────────

AVAILABLE_REPORTS: list[dict[str, Any]] = [
    {
        "id": "pipeline-summary",
        "name": "Recruitment Pipeline Summary",
        "description": "Overview of all open requisitions, candidates in each stage, and time-to-fill metrics.",
        "category": "recruiting",
        "format": "pdf",
        "estimated_runtime_seconds": 25,
    },
    {
        "id": "time-to-hire",
        "name": "Time-to-Hire Analysis",
        "description": "Detailed breakdown of time-to-hire by department, role seniority, and recruiter.",
        "category": "metrics",
        "format": "xlsx",
        "estimated_runtime_seconds": 45,
    },
    {
        "id": "source-effectiveness",
        "name": "Source Effectiveness Report",
        "description": "Comparison of candidate sources (job boards, referrals, agencies) by volume, quality, and cost-per-hire.",
        "category": "sourcing",
        "format": "pdf",
        "estimated_runtime_seconds": 35,
    },
    {
        "id": "diversity-metrics",
        "name": "Diversity & Inclusion Metrics",
        "description": "Workforce demographic breakdown across pipeline stages and hiring outcomes.",
        "category": "compliance",
        "format": "pdf",
        "estimated_runtime_seconds": 40,
    },
    {
        "id": "interviewer-performance",
        "name": "Interviewer Performance",
        "description": "Interviewer throughput, feedback completion rates, and candidate experience scores.",
        "category": "metrics",
        "format": "csv",
        "estimated_runtime_seconds": 20,
    },
    {
        "id": "offer-acceptance",
        "name": "Offer Acceptance & Decline Analysis",
        "description": "Offer acceptance rates, decline reasons, and compensation benchmarking.",
        "category": "recruiting",
        "format": "xlsx",
        "estimated_runtime_seconds": 30,
    },
    {
        "id": "requisition-aging",
        "name": "Requisition Aging Report",
        "description": "Open requisitions sorted by days open, highlighting stale or at-risk positions.",
        "category": "recruiting",
        "format": "pdf",
        "estimated_runtime_seconds": 15,
    },
    {
        "id": "cost-per-hire",
        "name": "Cost-per-Hire Breakdown",
        "description": "Total recruiting cost per hire by channel, including agency fees and job board spend.",
        "category": "finance",
        "format": "xlsx",
        "estimated_runtime_seconds": 50,
    },
]


# ─── Helpers ─────────────────────────────────────────────────────────────────


def _generate_mock_report(
    report_type: str,
    fmt: str,
    department: str | None,
    start_date: str | None,
    end_date: str | None,
) -> dict[str, Any]:
    """Build a realistic mock report summary."""
    now = datetime.utcnow()
    created_at = now.isoformat() + "Z"
    # Simulate a short processing delay
    completed_at = (now + timedelta(seconds=12)).isoformat() + "Z"

    report_names = {
        "pipeline-summary": "Recruitment Pipeline Summary",
        "time-to-hire": "Time-to-Hire Analysis",
        "source-effectiveness": "Source Effectiveness Report",
        "diversity-metrics": "Diversity & Inclusion Metrics",
        "interviewer-performance": "Interviewer Performance",
        "offer-acceptance": "Offer Acceptance & Decline Analysis",
        "requisition-aging": "Requisition Aging Report",
        "cost-per-hire": "Cost-per-Hire Breakdown",
    }

    name = report_names.get(report_type, "Custom Report")
    report_id = f"RPT-{now.strftime('%Y%m%d')}-{abs(hash(report_type + created_at)) % 100000:05d}"

    size_map = {"pdf": 245_000, "csv": 89_000, "xlsx": 178_000}
    size_bytes = size_map.get(fmt, 150_000)

    return {
        "report_id": report_id,
        "name": name,
        "status": "completed",
        "created_at": created_at,
        "completed_at": completed_at,
        "download_url": f"/api/v1/reports/download/{report_id}.{fmt}",
        "format": fmt,
        "size_bytes": size_bytes,
    }


# ─── Endpoints ───────────────────────────────────────────────────────────────


@router.get(
    "",
    response_model=list[ReportInfo],
    summary="List available reports",
    description="Returns a list of all report types available on the platform.",
)
async def list_reports() -> list[dict[str, Any]]:
    """List all available report types."""
    return AVAILABLE_REPORTS


@router.post(
    "/generate",
    response_model=GenerateReportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate a report",
    description="Request generation of a specific report. Returns a summary with a download URL once ready.",
)
async def generate_report(request: GenerateReportRequest) -> dict[str, Any]:
    """Generate a report based on the provided parameters."""
    valid_types = {r["id"] for r in AVAILABLE_REPORTS}
    if request.report_type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown report type '{request.report_type}'. "
            f"Valid types: {', '.join(sorted(valid_types))}",
        )

    valid_formats = {"pdf", "csv", "xlsx"}
    if request.format not in valid_formats:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported format '{request.format}'. "
            f"Valid formats: {', '.join(sorted(valid_formats))}",
        )

    mock_report = _generate_mock_report(
        report_type=request.report_type,
        fmt=request.format,
        department=request.department,
        start_date=request.start_date,
        end_date=request.end_date,
    )

    return {
        "success": True,
        "message": f"Report '{mock_report['name']}' generated successfully.",
        "report": mock_report,
    }
