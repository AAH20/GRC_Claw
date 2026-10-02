"""Candidate profile endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status

from candidate_matcher.models.schemas import Candidate

router = APIRouter(prefix="/api/v1/candidates", tags=["candidates"])


@router.post("", response_model=Candidate, status_code=status.HTTP_201_CREATED)
async def create_candidate(
    request: Request,
    candidate: Candidate,
) -> Candidate:
    """Create a new candidate profile.

    Args:
        request: FastAPI request object.
        candidate: Candidate profile to create.

    Returns:
        The created candidate profile.
    """
    store: dict[UUID, Candidate] = request.app.state.candidate_store
    store[candidate.id] = candidate
    return candidate


@router.get("/{candidate_id}", response_model=Candidate)
async def get_candidate(
    request: Request,
    candidate_id: UUID,
) -> Candidate:
    """Get a candidate profile by ID.

    Args:
        request: FastAPI request object.
        candidate_id: Candidate identifier.

    Returns:
        The candidate profile.

    Raises:
        HTTPException: If candidate not found.
    """
    store: dict[UUID, Candidate] = request.app.state.candidate_store
    candidate = store.get(candidate_id)
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate {candidate_id} not found",
        )
    return candidate


@router.get("", response_model=list[Candidate])
async def list_candidates(
    request: Request,
    skip: int = 0,
    limit: int = 100,
) -> list[Candidate]:
    """List all candidate profiles.

    Args:
        request: FastAPI request object.
        skip: Number of records to skip.
        limit: Maximum number of records to return.

    Returns:
        List of candidate profiles.
    """
    store: dict[UUID, Candidate] = request.app.state.candidate_store
    candidates = list(store.values())
    return candidates[skip : skip + limit]
