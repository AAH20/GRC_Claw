"""Verification routes."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from member_verification.api.dependencies import verify_api_key
from member_verification.models.schemas import (
    ExplanationRequest,
    VerificationExplanation,
    VerificationRequest,
    VerificationResult,
)

router = APIRouter(prefix="/verify", tags=["verification"])

# In-memory store for demo purposes — replace with database in production
_verification_store: dict[UUID, VerificationResult] = {}


@router.post("", response_model=VerificationResult, status_code=status.HTTP_201_CREATED)
async def submit_verification(
    request: VerificationRequest,
    api_key: str = Depends(verify_api_key),
) -> VerificationResult:
    """Submit a new verification request.

    Args:
        request: The verification request data.
        api_key: Verified API key.

    Returns:
        The verification result.

    Raises:
        HTTPException: If the request is invalid.
    """
    from member_verification.agents.fraud_preventor import FraudPreventorAgent
    from member_verification.agents.identity_verifier import IdentityVerifierAgent
    from member_verification.agents.trust_scorer import TrustScorerAgent

    # Run identity verification
    identity_agent = IdentityVerifierAgent()
    identity_result = await identity_agent.run(
        {
            "identity": request.identity.model_dump(),
            "documents": [doc.model_dump() for doc in request.documents],
        }
    )

    # Run trust scoring
    trust_agent = TrustScorerAgent()
    trust_result = await trust_agent.run(
        {
            "member_id": request.member_id,
            "include_history": False,
        }
    )

    # Run fraud check
    fraud_agent = FraudPreventorAgent()
    fraud_result = await fraud_agent.run(
        {
            "member_id": request.member_id,
            "identity": request.identity.model_dump(),
            "check_depth": "standard",
        }
    )

    # Combine results
    fraud_risk = fraud_result.get("risk_score", 0.0)
    trust_score = trust_result.get("score", 0.0)

    # Determine final status
    if fraud_risk >= 0.7:
        final_status = "rejected"
    elif identity_result.get("status") == "verified" and trust_score >= 0.3:
        final_status = "verified"
    elif identity_result.get("status") == "needs_review":
        final_status = "needs_review"
    else:
        final_status = "rejected"

    # Determine risk level
    if fraud_risk >= 0.8:
        risk_level = "critical"
    elif fraud_risk >= 0.6:
        risk_level = "high"
    elif fraud_risk >= 0.3:
        risk_level = "medium"
    else:
        risk_level = "low"

    result = VerificationResult(
        request_id=request.request_id,
        member_id=request.member_id,
        status=final_status,  # type: ignore[arg-type]
        confidence=identity_result.get("confidence", 0.0),
        trust_score=trust_score,
        fraud_risk=fraud_risk,
        risk_level=risk_level,  # type: ignore[arg-type]
        checks_performed=identity_result.get("checks_performed", []),
        failure_reasons=identity_result.get("failure_reasons", []),
        metadata={
            "priority": request.priority,
            "document_count": len(request.documents),
        },
    )

    _verification_store[request.request_id] = result
    return result


@router.get("/{request_id}", response_model=VerificationResult)
async def get_verification_result(
    request_id: UUID,
    api_key: str = Depends(verify_api_key),
) -> VerificationResult:
    """Get verification result by request ID.

    Args:
        request_id: The verification request ID.
        api_key: Verified API key.

    Returns:
        The verification result.

    Raises:
        HTTPException: If the result is not found.
    """
    result = _verification_store.get(request_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Verification result not found for request {request_id}",
        )
    return result


@router.post("/batch", response_model=list[VerificationResult], status_code=status.HTTP_201_CREATED)
async def batch_verification(
    requests: list[VerificationRequest],
    api_key: str = Depends(verify_api_key),
) -> list[VerificationResult]:
    """Submit multiple verification requests in batch.

    Args:
        requests: List of verification requests.
        api_key: Verified API key.

    Returns:
        List of verification results.

    Raises:
        HTTPException: If the batch size exceeds the limit.
    """
    if len(requests) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Batch size cannot exceed 100 requests",
        )

    results: list[VerificationResult] = []
    for req in requests:
        result = await submit_verification(req, api_key)
        results.append(result)
    return results


@router.post("/explain", response_model=VerificationExplanation)
async def explain_verification(
    request: ExplanationRequest,
    api_key: str = Depends(verify_api_key),
) -> VerificationExplanation:
    """Get an explanation for a verification decision.

    Args:
        request: The explanation request.
        api_key: Verified API key.

    Returns:
        The verification explanation.

    Raises:
        HTTPException: If the verification result is not found.
    """
    from member_verification.agents.explainer import VerificationExplainerAgent

    result = _verification_store.get(request.request_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Verification result not found for request {request.request_id}",
        )

    explainer = VerificationExplainerAgent()
    explanation_data = await explainer.run(
        {
            "request_id": str(request.request_id),
            "verification_result": result.model_dump(),
            "detail_level": request.detail_level,
        }
    )

    return VerificationExplanation(
        request_id=request.request_id,
        summary=explanation_data.get("summary", ""),
        factors=explanation_data.get("factors", []),
        recommendations=explanation_data.get("recommendations", []),
        appeal_process=explanation_data.get("appeal_process"),
        detail_level=request.detail_level,
    )
