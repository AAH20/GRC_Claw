"""Compliance mapping endpoints."""

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, Request, status

from app.api.v1.schemas.common import PaginatedResponse, PaginationParams
from app.api.v1.schemas.compliance import (
    ComplianceControl,
    ComplianceFramework,
    ComplianceMappingCreate,
    CompliancePosture,
    CompliancePostureFilter,
    CrosswalkResponse,
    GenerateComplianceReportRequest,
)
from app.core.exceptions import NotFoundException
from app.middleware.auth import AuthContext, get_current_auth, require_scope

router = APIRouter(prefix="/compliance", tags=["Compliance"])

_frameworks: dict[str, dict] = {
    "fw-001": {
        "id": "fw-001",
        "framework_key": "NIST-800-53",
        "name": "NIST SP 800-53 Rev 5",
        "version": "5",
        "description": "Security and Privacy Controls for Information Systems",
        "authority": "NIST",
        "effective_date": "2020-09-23T00:00:00Z",
        "control_count": 1026,
    },
    "fw-002": {
        "id": "fw-002",
        "framework_key": "SOC2",
        "name": "SOC 2 Trust Services Criteria",
        "version": "2017",
        "description": "Trust Services Criteria for Security, Availability, Processing Integrity, Confidentiality, and Privacy",
        "authority": "AICPA",
        "effective_date": "2017-04-01T00:00:00Z",
        "control_count": 64,
    },
}

_mappings: dict[str, dict] = {}


@router.get("/frameworks", response_model=list[ComplianceFramework])
async def list_frameworks(
    request: Request,
    auth: Annotated[AuthContext, Depends(get_current_auth)],
) -> list[ComplianceFramework]:
    """List compliance frameworks."""
    return [ComplianceFramework(**fw) for fw in _frameworks.values()]


@router.get("/frameworks/{framework_id}/controls", response_model=list[ComplianceControl])
async def list_controls(
    request: Request,
    auth: Annotated[AuthContext, Depends(get_current_auth)],
    framework_id: str,
    category: str | None = None,
    status: str | None = None,
    target_id: str | None = None,
) -> list[ComplianceControl]:
    """List controls for a framework."""
    if framework_id not in _frameworks:
        raise NotFoundException("Framework", framework_id)

    # In production, this would query the controls database
    return [
        ComplianceControl(
            id=f"ctrl-{i:03d}",
            framework_id=framework_id,
            control_key=f"AC-{i}",
            title=f"Control {i}",
            description=f"Description for control {i}",
            category="Access Control",
        )
        for i in range(1, 11)
    ]


@router.get("/posture", response_model=CompliancePosture)
async def get_compliance_posture(
    request: Request,
    auth: Annotated[AuthContext, Depends(get_current_auth)],
    filter: Annotated[CompliancePostureFilter, Depends()],
) -> CompliancePosture:
    """Get compliance posture."""
    # In production, this would compute from evidence and assessments
    return CompliancePosture(
        framework=filter.framework or "NIST-800-53",
        target_id=filter.target_id or "all-production",
        target_type=filter.target_type or "organization",
        controls_assessed=1026,
        controls_compliant=856,
        controls_non_compliant=120,
        controls_not_assessed=50,
        compliance_score=83.4,
        gaps=[],
        trend={
            "direction": "improving",
            "change": "+2.3%",
            "period": "30d",
        },
    )


@router.post("/mappings", status_code=status.HTTP_201_CREATED)
async def create_compliance_mapping(
    request: Request,
    auth: Annotated[AuthContext, Depends(require_scope("compliance:write"))],
    body: ComplianceMappingCreate,
):
    """Create a compliance mapping."""
    mapping_id = f"map-{len(_mappings) + 1:03d}"
    now = datetime.now(timezone.utc)

    mapping = {
        "id": mapping_id,
        "control_id": body.control_id,
        "policy_id": body.policy_id,
        "assessment_id": body.assessment_id,
        "mapping_type": body.mapping_type,
        "coverage": body.coverage,
        "notes": body.notes,
        "mapped_by": auth.subject,
        "mapped_at": now,
        "updated_at": now,
    }

    _mappings[mapping_id] = mapping
    return mapping


@router.post("/reports")
async def generate_compliance_report(
    request: Request,
    auth: Annotated[AuthContext, Depends(require_scope("compliance:read"))],
    body: GenerateComplianceReportRequest,
):
    """Generate a compliance report (async)."""
    report_id = f"rpt-{int(datetime.now(timezone.utc).timestamp())}"

    return {
        "report_id": report_id,
        "status": "processing",
        "format": body.format,
        "estimated_completion": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/crosswalk", response_model=CrosswalkResponse)
async def get_crosswalk(
    request: Request,
    auth: Annotated[AuthContext, Depends(get_current_auth)],
    control_id: str | None = None,
    framework: str | None = None,
    target_framework: str | None = None,
) -> CrosswalkResponse:
    """Get cross-framework control mapping."""
    return CrosswalkResponse(
        grc_control_id=control_id or "ctrl-001",
        mappings={
            "nist_800_53": ["AC-2", "AC-3", "AC-6"],
            "soc2": ["CC6.1", "CC6.2", "CC6.3"],
            "iso_27001": ["A.12.4", "A.12.5"],
            "iso_42001": ["A.6", "A.9"],
            "gdpr": ["Art.5", "Art.25"],
            "hipaa": ["164.308(a)(1)", "164.312(b)"],
            "pci_dss": ["10.1", "10.2", "10.3"],
            "cobit": ["DSS06", "APO12"],
            "nist_ai_rmf": ["Govern", "Map", "Measure"],
            "eu_ai_act": ["Annex III", "Art.9"],
        },
    )
