"""Compliance tracking endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from licensing_engine.agents import AgentContext, ComplianceTrackerAgent
from licensing_engine.config.settings import Settings, get_settings
from licensing_engine.models import (
    ComplianceCheckCreate,
    ComplianceListResponse,
    ComplianceReport,
    ComplianceReportResponse,
)

router = APIRouter()

# In-memory store for demo purposes
_compliance_reports: dict[UUID, ComplianceReport] = {}


@router.post(
    "/check",
    response_model=ComplianceReportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Run a compliance check",
)
async def run_compliance_check(
    data: ComplianceCheckCreate,
    settings: Settings = Depends(get_settings),
) -> ComplianceReportResponse:
    """Run a compliance check using the ComplianceTrackerAgent.

    Args:
        data: The compliance check request data.
        settings: Application settings.

    Returns:
        The compliance report.
    """
    context = AgentContext(settings=settings)
    agent = ComplianceTrackerAgent(context)
    result = await agent.execute(
        {
            "license_id": str(data.license_id),
            "license_terms": data.context.get("license_terms", {}),
            "usage_data": data.context.get("usage_data", {}),
        }
    )

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.error or "Failed to run compliance check",
        )

    report = ComplianceReport(
        license_id=data.license_id,
        check_type=data.check_type,
        status=result.data.get("compliance_status", "pending_review"),
        violations=result.data.get("violations", []),
        score=result.data.get("score", 0.0),
        details=result.data,
    )
    _compliance_reports[report.id] = report
    return ComplianceReportResponse(
        report=report, message="Compliance check completed"
    )


@router.get(
    "",
    response_model=ComplianceListResponse,
    summary="List all compliance reports",
)
async def list_compliance_reports() -> ComplianceListResponse:
    """List all compliance reports.

    Returns:
        List of all compliance reports.
    """
    reports = list(_compliance_reports.values())
    return ComplianceListResponse(reports=reports, total=len(reports))


@router.get(
    "/{report_id}",
    response_model=ComplianceReportResponse,
    summary="Get a compliance report by ID",
)
async def get_compliance_report(report_id: UUID) -> ComplianceReportResponse:
    """Get a specific compliance report by its ID.

    Args:
        report_id: The report ID.

    Returns:
        The requested compliance report.

    Raises:
        HTTPException: If the report is not found.
    """
    report = _compliance_reports.get(report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Compliance report {report_id} not found",
        )
    return ComplianceReportResponse(report=report)


@router.get(
    "/license/{license_id}",
    response_model=ComplianceListResponse,
    summary="Get compliance reports for a license",
)
async def get_license_compliance_reports(license_id: UUID) -> ComplianceListResponse:
    """Get all compliance reports for a specific license.

    Args:
        license_id: The license ID.

    Returns:
        List of compliance reports for the license.
    """
    reports = [
        r for r in _compliance_reports.values() if r.license_id == license_id
    ]
    return ComplianceListResponse(reports=reports, total=len(reports))
