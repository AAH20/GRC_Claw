"""Audit API routes."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from compliance_monitor.api.dependencies import get_audit_reporter
from compliance_monitor.api.store import store
from compliance_monitor.agents import AuditReporterAgent
from compliance_monitor.models.schemas import AuditReport, AuditRequest

router = APIRouter()


@router.get("", response_model=list[AuditReport])
async def list_audits() -> list[AuditReport]:
    """List all audit reports.

    Returns:
        List of all audit reports.
    """
    return store.list_audits()


@router.post("", response_model=AuditReport, status_code=status.HTTP_201_CREATED)
async def generate_audit(
    data: AuditRequest,
    agent: AuditReporterAgent = Depends(get_audit_reporter),
) -> AuditReport:
    """Generate a new audit report.

    Args:
        data: Audit request data.
        agent: Audit reporter agent.

    Returns:
        Generated audit report.
    """
    report = await agent.run(data)
    return store.create_audit(report)


@router.get("/{audit_id}", response_model=AuditReport)
async def get_audit(audit_id: UUID) -> AuditReport:
    """Get an audit report by ID.

    Args:
        audit_id: Audit report identifier.

    Returns:
        Audit report details.

    Raises:
        HTTPException: If audit report not found.
    """
    audit = store.get_audit(audit_id)
    if not audit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audit report not found")
    return audit
