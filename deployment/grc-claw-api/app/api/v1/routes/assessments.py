"""Assessment management endpoints."""

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, Request, status

from app.api.v1.schemas.assessment import (
    AssessmentCreate,
    AssessmentFilter,
    AssessmentResponse,
    AssessmentUpdate,
    FindingCreate,
    GenerateReportRequest,
)
from app.api.v1.schemas.common import PaginatedResponse, PaginationParams
from app.core.exceptions import NotFoundException
from app.middleware.auth import AuthContext, get_current_auth, require_scope

router = APIRouter(prefix="/assessments", tags=["Assessments"])

_assessments: dict[str, dict] = {}


@router.get("", response_model=PaginatedResponse[AssessmentResponse])
async def list_assessments(
    request: Request,
    auth: Annotated[AuthContext, Depends(get_current_auth)],
    filter: Annotated[AssessmentFilter, Depends()],
    pagination: Annotated[PaginationParams, Depends()],
) -> PaginatedResponse[AssessmentResponse]:
    """List assessments with filtering and pagination."""
    results = list(_assessments.values())

    if filter.assessment_type:
        results = [a for a in results if a["assessment_type"] == filter.assessment_type.value]
    if filter.status:
        results = [a for a in results if a["status"] == filter.status.value]
    if filter.target_type:
        results = [a for a in results if a["target_type"] == filter.target_type]
    if filter.target_id:
        results = [a for a in results if a["target_id"] == filter.target_id]

    total = len(results)
    start = 0
    if pagination.cursor:
        try:
            start = int(pagination.cursor)
        except ValueError:
            start = 0

    end = start + pagination.limit
    page = results[start:end]
    next_cursor = str(end) if end < total else None

    return PaginatedResponse(
        data=[AssessmentResponse(**a) for a in page],
        pagination={
            "next_cursor": next_cursor,
            "has_next": next_cursor is not None,
            "total": total,
        },
    )


@router.post("", response_model=AssessmentResponse, status_code=status.HTTP_201_CREATED)
async def create_assessment(
    request: Request,
    auth: Annotated[AuthContext, Depends(require_scope("assessments:write"))],
    body: AssessmentCreate,
) -> AssessmentResponse:
    """Create a new assessment."""
    assessment_id = f"asm-{len(_assessments) + 1:03d}"
    now = datetime.now(timezone.utc)

    assessment = {
        "id": assessment_id,
        "assessment_key": body.assessment_key,
        "title": body.title,
        "description": body.description,
        "assessment_type": body.assessment_type.value,
        "target_id": body.target_id,
        "target_type": body.target_type,
        "status": "planned",
        "methodology": body.methodology,
        "score": None,
        "risk_level": None,
        "started_at": None,
        "completed_at": None,
        "next_assessment_at": None,
        "lead_assessor": body.lead_assessor,
        "findings": [],
        "metadata": body.metadata or {},
        "created_at": now,
        "updated_at": now,
    }

    _assessments[assessment_id] = assessment
    return AssessmentResponse(**assessment)


@router.get("/{assessment_id}", response_model=AssessmentResponse)
async def get_assessment(
    request: Request,
    auth: Annotated[AuthContext, Depends(get_current_auth)],
    assessment_id: str,
) -> AssessmentResponse:
    """Get an assessment by ID."""
    if assessment_id not in _assessments:
        raise NotFoundException("Assessment", assessment_id)
    return AssessmentResponse(**_assessments[assessment_id])


@router.put("/{assessment_id}", response_model=AssessmentResponse)
async def update_assessment(
    request: Request,
    auth: Annotated[AuthContext, Depends(require_scope("assessments:write"))],
    assessment_id: str,
    body: AssessmentUpdate,
) -> AssessmentResponse:
    """Update an assessment."""
    if assessment_id not in _assessments:
        raise NotFoundException("Assessment", assessment_id)

    assessment = _assessments[assessment_id]
    now = datetime.now(timezone.utc)

    if body.title:
        assessment["title"] = body.title
    if body.description:
        assessment["description"] = body.description
    if body.status:
        assessment["status"] = body.status.value
    if body.score is not None:
        assessment["score"] = body.score
    if body.risk_level:
        assessment["risk_level"] = body.risk_level
    if body.metadata:
        assessment["metadata"] = body.metadata

    assessment["updated_at"] = now
    return AssessmentResponse(**assessment)


@router.post("/{assessment_id}/findings", response_model=AssessmentResponse)
async def add_finding(
    request: Request,
    auth: Annotated[AuthContext, Depends(require_scope("assessments:write"))],
    assessment_id: str,
    body: FindingCreate,
) -> AssessmentResponse:
    """Add a finding to an assessment."""
    if assessment_id not in _assessments:
        raise NotFoundException("Assessment", assessment_id)

    assessment = _assessments[assessment_id]
    now = datetime.now(timezone.utc)

    finding_id = f"fnd-{len(assessment['findings']) + 1:03d}"
    finding = {
        "id": finding_id,
        "finding_key": body.finding_key,
        "title": body.title,
        "description": body.description,
        "severity": body.severity.value,
        "category": body.category,
        "status": "open",
        "policy_id": body.policy_id,
        "evidence_ids": body.evidence_ids,
        "remediation": body.remediation,
        "remediated_by": None,
        "remediated_at": None,
        "due_date": body.due_date,
    }

    assessment["findings"].append(finding)
    assessment["updated_at"] = now

    return AssessmentResponse(**assessment)


@router.post("/{assessment_id}/report")
async def generate_assessment_report(
    request: Request,
    auth: Annotated[AuthContext, Depends(require_scope("assessments:read"))],
    assessment_id: str,
    body: GenerateReportRequest,
):
    """Generate an assessment report (async)."""
    if assessment_id not in _assessments:
        raise NotFoundException("Assessment", assessment_id)

    report_id = f"rpt-{assessment_id}-{int(datetime.now(timezone.utc).timestamp())}"

    return {
        "report_id": report_id,
        "status": "processing",
        "format": body.format,
        "estimated_completion": datetime.now(timezone.utc).isoformat(),
    }
