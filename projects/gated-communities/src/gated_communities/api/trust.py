"""Trust score routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from member_verification.api.dependencies import verify_api_key
from member_verification.models.schemas import TrustScore, TrustScoreRequest

router = APIRouter(prefix="/trust-score", tags=["trust"])

# In-memory store for demo purposes
_trust_score_store: dict[str, TrustScore] = {}


@router.post("", response_model=TrustScore, status_code=status.HTTP_201_CREATED)
async def calculate_trust_score(
    request: TrustScoreRequest,
    api_key: str = Depends(verify_api_key),
) -> TrustScore:
    """Calculate trust score for a member.

    Args:
        request: The trust score request.
        api_key: Verified API key.

    Returns:
        The calculated trust score.
    """
    from member_verification.agents.trust_scorer import TrustScorerAgent

    agent = TrustScorerAgent()
    result = await agent.run(
        {
            "member_id": request.member_id,
            "include_history": request.include_history,
            "factors": request.factors,
        }
    )

    trust_score = TrustScore(
        member_id=request.member_id,
        score=result.get("score", 0.0),
        level=result.get("level", "medium"),  # type: ignore[arg-type]
        factors=result.get("factors", {}),
        history=result.get("history", []),
    )

    _trust_score_store[request.member_id] = trust_score
    return trust_score


@router.get("/{member_id}", response_model=TrustScore)
async def get_trust_score(
    member_id: str,
    api_key: str = Depends(verify_api_key),
) -> TrustScore:
    """Get trust score for a member.

    Args:
        member_id: The member identifier.
        api_key: Verified API key.

    Returns:
        The trust score.

    Raises:
        HTTPException: If no trust score exists for the member.
    """
    score = _trust_score_store.get(member_id)
    if not score:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No trust score found for member {member_id}",
        )
    return score
