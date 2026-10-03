"""Remediation API routes."""

from __future__ import annotations

from typing import TYPE_CHECKING

from compliance_monitor.api.dependencies import get_remediation_agent
from compliance_monitor.api.store import store
from compliance_monitor.models.schemas import RemediationAction, RemediationRequest
from fastapi import APIRouter, Depends, HTTPException, status

if TYPE_CHECKING:
    from uuid import UUID

    from compliance_monitor.agents import RemediationAgent

router = APIRouter()


@router.post("/remediate/{violation_id}", response_model=RemediationAction)
async def remediate_violation(
    violation_id: UUID,
    data: RemediationRequest,
    agent: RemediationAgent = Depends(get_remediation_agent),  # noqa: B008,
) -> RemediationAction:
    """Remediate a compliance violation.

    Args:
        violation_id: Violation identifier.
        data: Remediation request data.
        agent: Remediation agent.

    Returns:
        Remediation action result.

    Raises:
        HTTPException: If violation not found.
    """
    violation = store.get_violation(violation_id)
    if not violation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Violation not found"
        )

    action = await agent.run(data)
    action.violation_id = violation_id

    if data.auto_execute:
        action = await agent.execute_remediation(action)

    return store.create_remediation(action)


@router.get("/reports/compliance")
async def get_compliance_report() -> dict:
    """Get a comprehensive compliance report.

    Returns:
        Full compliance report with policies, violations, and scores.
    """
    policies = store.list_policies()
    violations = store.list_violations()
    scores = store.list_scores()

    total_score = sum(s.score for s in scores) / len(scores) if scores else 0.0
    open_violations = [v for v in violations if v.status.value == "open"]

    risk_level = "low"
    if len(open_violations) > 10 or total_score < 50:
        risk_level = "critical"
    elif len(open_violations) > 5 or total_score < 70:
        risk_level = "high"
    elif len(open_violations) > 0 or total_score < 85:
        risk_level = "medium"

    return {
        "overall_compliance_score": total_score,
        "risk_level": risk_level,
        "total_policies": len(policies),
        "total_violations": len(violations),
        "open_violations": len(open_violations),
        "total_scores": len(scores),
        "policies": [p.model_dump() for p in policies],
        "violations": [v.model_dump() for v in violations],
        "scores": [s.model_dump() for s in scores],
    }
