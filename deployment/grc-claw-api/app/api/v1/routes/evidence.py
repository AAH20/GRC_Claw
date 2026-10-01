"""Evidence management endpoints."""

import hashlib
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status

from app.api.v1.schemas.common import PaginatedResponse, PaginationParams
from app.api.v1.schemas.evidence import (
    EvidenceCreate,
    EvidenceFilter,
    EvidenceResponse,
    ExportEvidenceRequest,
    ExportPackageResponse,
    ExportPackageStatus,
    VerifyEvidenceResponse,
)
from app.core.exceptions import NotFoundException
from app.middleware.auth import AuthContext, get_current_auth, require_scope

router = APIRouter(prefix="/evidence", tags=["Evidence"])

_evidence: dict[str, dict] = {}
_export_packages: dict[str, dict] = {}


@router.get("", response_model=PaginatedResponse[EvidenceResponse])
async def search_evidence(
    request: Request,
    auth: Annotated[AuthContext, Depends(get_current_auth)],
    filter: Annotated[EvidenceFilter, Depends()],
    pagination: Annotated[PaginationParams, Depends()],
) -> PaginatedResponse[EvidenceResponse]:
    """Search evidence with filtering and pagination."""
    results = list(_evidence.values())

    if filter.policy_id:
        results = [e for e in results if e.get("policy_id") == filter.policy_id]
    if filter.evidence_type:
        results = [e for e in results if e["evidence_type"] == filter.evidence_type.value]
    if filter.framework:
        results = [e for e in results if e.get("control_mapping", {}).get("framework") == filter.framework]
    if filter.verification_level:
        results = [e for e in results if e["verification_level"] == filter.verification_level.value]
    if filter.environment:
        results = [e for e in results if e["context"]["environment"] == filter.environment]

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
        data=[EvidenceResponse(**e) for e in page],
        pagination={
            "next_cursor": next_cursor,
            "has_next": next_cursor is not None,
            "total": total,
        },
    )


@router.post("", response_model=EvidenceResponse, status_code=status.HTTP_201_CREATED)
async def submit_evidence(
    request: Request,
    auth: Annotated[AuthContext, Depends(require_scope("evidence:write"))],
    body: EvidenceCreate,
) -> EvidenceResponse:
    """Submit new evidence."""
    evidence_id = f"evd-{len(_evidence) + 1:03d}"
    now = datetime.now(timezone.utc)

    # Compute content hash
    content_hash = hashlib.sha256(body.content.data.encode()).hexdigest()

    evidence = {
        "evidence_id": evidence_id,
        "policy_id": body.policy_id,
        "assessment_id": body.assessment_id,
        "source": body.source.model_dump(),
        "evidence_type": body.evidence_type.value,
        "content": {
            "format": body.content.format,
            "data": body.content.data,
            "hash": f"sha256:{content_hash}",
        },
        "context": {
            "environment": body.context.environment,
            "region": body.context.region,
            "timestamp": now.isoformat(),
            "metadata": body.context.metadata or {},
        },
        "validation": {
            "status": "pending",
            "validated_by": None,
            "validated_at": None,
            "confidence_score": 0.0,
        },
        "verification_level": "L0",
        "chain_of_custody": [
            {
                "action": "collected",
                "actor": auth.subject,
                "timestamp": now.isoformat(),
                "hash": f"sha256:{content_hash}",
            }
        ],
        "retention_class": "standard",
        "created_at": now,
        "expires_at": now + timedelta(days=365),
    }

    if body.control_mapping:
        evidence["control_mapping"] = body.control_mapping.model_dump()

    _evidence[evidence_id] = evidence
    return EvidenceResponse(**evidence)


@router.get("/{evidence_id}", response_model=EvidenceResponse)
async def get_evidence(
    request: Request,
    auth: Annotated[AuthContext, Depends(get_current_auth)],
    evidence_id: str,
) -> EvidenceResponse:
    """Get evidence by ID."""
    if evidence_id not in _evidence:
        raise NotFoundException("Evidence", evidence_id)
    return EvidenceResponse(**_evidence[evidence_id])


@router.post("/{evidence_id}/verify", response_model=VerifyEvidenceResponse)
async def verify_evidence(
    request: Request,
    auth: Annotated[AuthContext, Depends(require_scope("evidence:write"))],
    evidence_id: str,
) -> VerifyEvidenceResponse:
    """Verify evidence integrity."""
    if evidence_id not in _evidence:
        raise NotFoundException("Evidence", evidence_id)

    evidence = _evidence[evidence_id]
    now = datetime.now(timezone.utc)

    # In production, this would perform actual hash verification,
    # chain-of-custody validation, and schema validation
    evidence["validation"] = {
        "status": "verified",
        "validated_by": auth.subject,
        "validated_at": now.isoformat(),
        "confidence_score": 0.95,
    }
    evidence["verification_level"] = "L2"

    return VerifyEvidenceResponse(
        evidence_id=evidence_id,
        verification_result={
            "status": "verified",
            "verification_level": "L2",
            "hash_match": True,
            "chain_of_custody_intact": True,
            "schema_valid": True,
            "control_mapping_valid": True,
            "verified_at": now.isoformat(),
            "verified_by": auth.subject,
        },
    )


@router.post("/export", response_model=ExportPackageResponse, status_code=status.HTTP_202_ACCEPTED)
async def export_evidence_package(
    request: Request,
    auth: Annotated[AuthContext, Depends(require_scope("evidence:read"))],
    body: ExportEvidenceRequest,
) -> ExportPackageResponse:
    """Export evidence package (async)."""
    package_id = f"pkg-{len(_export_packages) + 1:03d}"
    now = datetime.now(timezone.utc)

    _export_packages[package_id] = {
        "package_id": package_id,
        "status": "processing",
        "estimated_completion": now + timedelta(minutes=5),
        "download_url": None,
    }

    return ExportPackageResponse(
        package_id=package_id,
        status="processing",
        estimated_completion=now + timedelta(minutes=5),
    )


@router.get("/export/{package_id}", response_model=ExportPackageStatus)
async def get_export_package(
    request: Request,
    auth: Annotated[AuthContext, Depends(get_current_auth)],
    package_id: str,
) -> ExportPackageStatus:
    """Get export package status."""
    if package_id not in _export_packages:
        raise NotFoundException("Export package", package_id)

    pkg = _export_packages[package_id]

    # Simulate completion
    if pkg["status"] == "processing":
        pkg["status"] = "completed"
        pkg["download_url"] = f"/v1.0/evidence/export/{package_id}/download"
        pkg["expires_at"] = datetime.now(timezone.utc) + timedelta(days=7)
        pkg["package_hash"] = f"sha256:{hashlib.sha256(package_id.encode()).hexdigest()}"
        pkg["manifest"] = {
            "framework": "NIST-800-53",
            "controls_assessed": 42,
            "evidence_items": 156,
        }

    return ExportPackageStatus(**pkg)
