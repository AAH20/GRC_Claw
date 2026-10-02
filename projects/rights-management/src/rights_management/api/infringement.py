"""Infringement API routes."""

from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request

from rights_management.agents.infringement_detector import InfringementDetectorAgent
from rights_management.integrations.storage import InMemoryStorage
from rights_management.models import (
    InfringementDetectionRequest,
    InfringementDetectionResult,
    InfringementReport,
    InfringementReportCreate,
    InfringementStatus,
)

router = APIRouter()


def get_storage(request: Request) -> InMemoryStorage:
    """Dependency to retrieve the storage backend from app state.

    Args:
        request: The incoming FastAPI request.

    Returns:
        The InMemoryStorage instance.
    """
    return request.app.state.storage


def get_agent(request: Request) -> InfringementDetectorAgent:
    """Dependency to retrieve the infringement detector agent.

    Args:
        request: The incoming FastAPI request.

    Returns:
        The InfringementDetectorAgent instance.
    """
    if not hasattr(request.app.state, "infringement_detector_agent"):
        request.app.state.infringement_detector_agent = InfringementDetectorAgent()
    return request.app.state.infringement_detector_agent


@router.post("/report", response_model=InfringementReport, status_code=201)
async def file_infringement_report(
    payload: InfringementReportCreate,
    storage: InMemoryStorage = Depends(get_storage),
) -> InfringementReport:
    """File a new infringement report.

    Args:
        payload: The report data.
        storage: The storage backend.

    Returns:
        The created InfringementReport.
    """
    report = InfringementReport(
        id=str(uuid.uuid4()),
        content_id=payload.content_id,
        reporter_id=payload.reporter_id,
        description=payload.description,
        severity=payload.severity,
        status=InfringementStatus.OPEN,
        evidence_urls=payload.evidence_urls,
        created_at=datetime.utcnow(),
        metadata=payload.metadata,
    )
    await storage.save_infringement_report(report)
    return report


@router.get("/reports/{content_id}", response_model=list[InfringementReport])
async def list_infringement_reports(
    content_id: str,
    storage: InMemoryStorage = Depends(get_storage),
) -> list[InfringementReport]:
    """List infringement reports for a piece of content.

    Args:
        content_id: The content identifier.
        storage: The storage backend.

    Returns:
        List of infringement reports.
    """
    return await storage.list_infringement_reports(content_id=content_id)


@router.post("/detect", response_model=InfringementDetectionResult)
async def detect_infringement(
    payload: InfringementDetectionRequest,
    agent: InfringementDetectorAgent = Depends(get_agent),
) -> InfringementDetectionResult:
    """Run automated infringement detection on content.

    Args:
        payload: The detection request.
        agent: The infringement detector agent.

    Returns:
        The detection result.
    """
    return await agent.run(payload)


@router.patch("/reports/{report_id}/status", response_model=InfringementReport)
async def update_report_status(
    report_id: str,
    status: InfringementStatus,
    storage: InMemoryStorage = Depends(get_storage),
) -> InfringementReport:
    """Update the status of an infringement report.

    Args:
        report_id: The report identifier.
        status: The new status.
        storage: The storage backend.

    Returns:
        The updated InfringementReport.

    Raises:
        HTTPException: If the report is not found.
    """
    report = await storage.get_infringement_report(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    report.status = status
    if status == InfringementStatus.RESOLVED:
        report.resolved_at = datetime.utcnow()
    await storage.save_infringement_report(report)
    return report
