"""Fraud check routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from member_verification.api.dependencies import verify_api_key
from member_verification.models.schemas import FraudCheckRequest, FraudReport

router = APIRouter(prefix="/fraud", tags=["fraud"])

# In-memory store for demo purposes
_fraud_report_store: dict[str, FraudReport] = {}


@router.post("/check", response_model=FraudReport, status_code=status.HTTP_201_CREATED)
async def run_fraud_check(
    request: FraudCheckRequest,
    api_key: str = Depends(verify_api_key),
) -> FraudReport:
    """Run a fraud check on a member.

    Args:
        request: The fraud check request.
        api_key: Verified API key.

    Returns:
        The fraud report.
    """
    from member_verification.agents.fraud_preventor import FraudPreventorAgent

    agent = FraudPreventorAgent()
    result = await agent.run(
        {
            "member_id": request.member_id,
            "identity": request.identity.model_dump(),
            "check_depth": request.check_depth,
        }
    )

    report = FraudReport(
        member_id=request.member_id,
        risk_score=result.get("risk_score", 0.0),
        risk_level=result.get("risk_level", "low"),  # type: ignore[arg-type]
        flags=result.get("flags", []),
        matched_patterns=result.get("matched_patterns", []),
        recommendation=result.get("recommendation", "allow"),  # type: ignore[arg-type]
        check_depth=request.check_depth,
    )

    _fraud_report_store[request.member_id] = report
    return report


@router.get("/report/{member_id}", response_model=FraudReport)
async def get_fraud_report(
    member_id: str,
    api_key: str = Depends(verify_api_key),
) -> FraudReport:
    """Get the latest fraud report for a member.

    Args:
        member_id: The member identifier.
        api_key: Verified API key.

    Returns:
        The fraud report.

    Raises:
        HTTPException: If no fraud report exists for the member.
    """
    report = _fraud_report_store.get(member_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No fraud report found for member {member_id}",
        )
    return report
