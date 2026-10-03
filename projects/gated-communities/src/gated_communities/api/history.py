"""Reputation History API routes."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from reputation_system.agents.reputation_history import (
    HistoryAnalysisInput, ReputationHistoryAgent)
from reputation_system.config.settings import Settings, get_settings
from reputation_system.models.schemas import (ReputationHistory,
                                              ReputationHistoryCreate)

router = APIRouter(prefix="/history", tags=["history"])

# In-memory store for demo purposes
_history: dict[UUID, ReputationHistory] = {}


@router.post("", response_model=ReputationHistory, status_code=status.HTTP_201_CREATED)
async def create_history_entry(
    data: ReputationHistoryCreate,
    settings: Annotated[Settings, Depends(get_settings)],
) -> ReputationHistory:
    """Create a new reputation history entry.

    Args:
        data: History entry creation data.
        settings: Application settings.

    Returns:
        Created history entry.
    """
    entry = ReputationHistory(**data.model_dump(exclude_none=True))
    _history[entry.id] = entry
    return entry


@router.get("/{entry_id}", response_model=ReputationHistory)
async def get_history_entry(
    entry_id: UUID,
    settings: Annotated[Settings, Depends(get_settings)],
) -> ReputationHistory:
    """Get a history entry by ID.

    Args:
        entry_id: History entry identifier.
        settings: Application settings.

    Returns:
        History entry details.

    Raises:
        HTTPException: If entry not found.
    """
    if entry_id not in _history:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"History entry {entry_id} not found",
        )
    return _history[entry_id]


@router.get("/member/{member_id}", response_model=list[ReputationHistory])
async def get_member_history(
    member_id: str,
    settings: Annotated[Settings, Depends(get_settings)],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=500)] = 50,
    action_filter: Annotated[str | None, Query()] = None,
) -> list[ReputationHistory]:
    """Get reputation history for a member.

    Args:
        member_id: Member identifier.
        settings: Application settings.
        skip: Number of records to skip.
        limit: Maximum number of records to return.
        action_filter: Filter by action type.

    Returns:
        List of history entries for the member.
    """
    entries = [e for e in _history.values() if e.member_id == member_id]
    if action_filter:
        entries = [e for e in entries if e.action == action_filter]
    return entries[skip : skip + limit]


@router.post("/analyze/{member_id}")
async def analyze_member_history(
    member_id: str,
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict:
    """Analyze reputation history for a member using the AI agent.

    Args:
        member_id: Member identifier.
        settings: Application settings.

    Returns:
        History analysis results with trends and insights.
    """
    entries = [e for e in _history.values() if e.member_id == member_id]
    if not entries:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No history found for member {member_id}",
        )

    agent = ReputationHistoryAgent(settings=settings)
    input_data = HistoryAnalysisInput(
        member_id=member_id,
        history_entries=[e.model_dump() for e in entries],
    )
    result = await agent.run(input_data)
    return result.model_dump()
