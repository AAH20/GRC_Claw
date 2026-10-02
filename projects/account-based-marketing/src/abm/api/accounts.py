"""API routes for account management."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query, status

from abm.agents.account_identification import AccountIdentificationAgent
from abm.agents.buying_committee_mapper import BuyingCommitteeMapperAgent
from abm.agents.intent_scoring import IntentScoringAgent

router = APIRouter()

# Agent instances (would use dependency injection in production)
account_agent = AccountIdentificationAgent()
intent_agent = IntentScoringAgent()
committee_agent = BuyingCommitteeMapperAgent()


@router.get("/", response_model=list[dict[str, Any]])
async def list_accounts(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[dict[str, Any]]:
    """List target accounts with pagination.

    Args:
        limit: Maximum number of accounts to return.
        offset: Number of accounts to skip.

    Returns:
        List of account summaries.
    """
    return [
        {
            "id": f"acc_{i:03d}",
            "name": f"Company {i}",
            "domain": f"company{i}.com",
            "score": 0.9 - (i * 0.01),
            "industry": "Technology",
            "employee_count": 500 + i * 10,
        }
        for i in range(offset, min(offset + limit, 100))
    ]


@router.post("/identify", response_model=list[dict[str, Any]])
async def identify_accounts(criteria: dict[str, Any]) -> list[dict[str, Any]]:
    """Identify new target accounts based on ICP criteria.

    Args:
        criteria: ICP criteria including industry, size, geography, etc.

    Returns:
        List of identified accounts with scores.

    Raises:
        HTTPException: If criteria is invalid.
    """
    try:
        accounts = await account_agent.identify_accounts(criteria)
        return [
            {
                "account_id": a.account_id,
                "name": a.name,
                "domain": a.domain,
                "score": a.score,
                "firmographic_match": a.firmographic_match,
                "technographic_match": a.technographic_match,
                "engagement_level": a.engagement_level,
                "signals": a.signals,
            }
            for a in accounts
        ]
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get("/{account_id}", response_model=dict[str, Any])
async def get_account(account_id: str) -> dict[str, Any]:
    """Get detailed information about a specific account.

    Args:
        account_id: The account identifier.

    Returns:
        Account details.

    Raises:
        HTTPException: If account is not found.
    """
    if not account_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="account_id is required",
        )

    enriched = await account_agent.enrich_account(account_id)
    return enriched


@router.get("/{account_id}/intent", response_model=dict[str, Any])
async def get_account_intent(account_id: str) -> dict[str, Any]:
    """Get intent score and signals for an account.

    Args:
        account_id: The account identifier.

    Returns:
        Intent score details.

    Raises:
        HTTPException: If account_id is invalid.
    """
    try:
        score = await intent_agent.score_account(account_id)
        return {
            "account_id": score.account_id,
            "total_score": score.total_score,
            "normalized_score": score.normalized_score,
            "trend": score.trend,
            "last_activity": score.last_activity.isoformat() if score.last_activity else None,
            "signals": [
                {
                    "type": s.signal_type.value,
                    "timestamp": s.timestamp.isoformat(),
                    "weight": s.weight,
                    "metadata": s.metadata,
                }
                for s in score.signals
            ],
        }
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get("/{account_id}/committee", response_model=dict[str, Any])
async def get_account_committee(account_id: str) -> dict[str, Any]:
    """Get buying committee map for an account.

    Args:
        account_id: The account identifier.

    Returns:
        Buying committee details.

    Raises:
        HTTPException: If account_id is invalid.
    """
    try:
        committee = await committee_agent.map_committee(account_id)
        return {
            "account_id": committee.account_id,
            "completeness_score": committee.completeness_score,
            "identified_gaps": committee.identified_gaps,
            "members": [
                {
                    "contact_id": m.contact_id,
                    "name": m.name,
                    "title": m.title,
                    "role": m.role.value,
                    "influence_score": m.influence_score,
                    "engagement_level": m.engagement_level,
                    "email": m.email,
                    "linkedin_url": m.linkedin_url,
                    "notes": m.notes,
                }
                for m in committee.members
            ],
        }
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
