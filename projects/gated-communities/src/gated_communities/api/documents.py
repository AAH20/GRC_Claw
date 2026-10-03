"""Document verification routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from member_verification.api.dependencies import verify_api_key
from member_verification.models.schemas import (DocumentVerificationResult,
                                                DocumentVerifyRequest)

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post(
    "/verify",
    response_model=DocumentVerificationResult,
    status_code=status.HTTP_201_CREATED,
)
async def verify_document(
    request: DocumentVerifyRequest,
    api_key: str = Depends(verify_api_key),
) -> DocumentVerificationResult:
    """Verify an identity document.

    Args:
        request: The document verification request.
        api_key: Verified API key.

    Returns:
        The document verification result.
    """
    from member_verification.agents.document_checker import \
        DocumentCheckerAgent

    agent = DocumentCheckerAgent()
    result = await agent.run(
        {
            "document": request.document.model_dump(),
            "identity": (
                {"government_id": request.member_id} if request.cross_reference else {}
            ),
            "cross_reference": request.cross_reference,
        }
    )

    return DocumentVerificationResult(
        document_type=request.document.model_dump().get("document_type", "passport"),  # type: ignore[arg-type]
        is_authentic=result.get("is_authentic", False),
        confidence=result.get("confidence", 0.0),
        tampering_detected=result.get("tampering_detected", False),
        expiry_status=result.get("expiry_status", "unknown"),  # type: ignore[arg-type]
        cross_reference_match=result.get("cross_reference_match"),
        issues=result.get("issues", []),
    )
