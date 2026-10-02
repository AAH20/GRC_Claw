"""Fraud report routes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from fraud_detection.api.dependencies import verify_api_key
from fraud_detection.config.logging_config import get_logger
from fraud_detection.models.schemas import FraudReport

logger = get_logger(__name__)
router = APIRouter(prefix="/v1/reports", tags=["reports"])

# In-memory store for demo purposes
_reports: dict[str, FraudReport] = {}


@router.get("/{report_id}", response_model=FraudReport)
async def get_report(
    report_id: str,
    api_key: Annotated[str, Depends(verify_api_key)],
) -> FraudReport:
    """Get a fraud report by ID.

    Args:
        report_id: Report identifier.
        api_key: Verified API key.

    Returns:
        FraudReport if found.

    Raises:
        HTTPException: If report not found.
    """
    if report_id not in _reports:
        raise HTTPException(status_code=404, detail="Report not found")
    return _reports[report_id]


@router.get("", response_model=list[FraudReport])
async def list_reports(
    api_key: Annotated[str, Depends(verify_api_key)],
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[FraudReport]:
    """List fraud reports with pagination.

    Args:
        api_key: Verified API key.
        limit: Maximum number of reports to return.
        offset: Number of reports to skip.

    Returns:
        List of FraudReport objects.
    """
    all_reports = list(_reports.values())
    return all_reports[offset : offset + limit]


def store_report(report: FraudReport) -> None:
    """Store a report in the in-memory store.

    Args:
        report: FraudReport to store.
    """
    _reports[report.report_id] = report
