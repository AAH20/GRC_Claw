"""Transaction API routes."""

from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from content_marketplace.agents.transaction_processor import TransactionProcessorAgent
from content_marketplace.models.transaction import (
    Transaction,
    TransactionCreate,
    TransactionStatus,
)

logger = logging.getLogger(__name__)
router = APIRouter()


_transaction_agent_instance: TransactionProcessorAgent | None = None


def get_transaction_agent() -> TransactionProcessorAgent:
    """Dependency to get the transaction processor agent (singleton)."""
    global _transaction_agent_instance
    if _transaction_agent_instance is None:
        _transaction_agent_instance = TransactionProcessorAgent()
    return _transaction_agent_instance


@router.post("", response_model=Transaction, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    data: TransactionCreate,
    agent: TransactionProcessorAgent = Depends(get_transaction_agent),  # noqa: B008
) -> Transaction:
    """Create a new transaction."""
    try:
        return await agent.create_transaction(data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{transaction_id}", response_model=Transaction)
async def get_transaction(
    transaction_id: UUID,
    agent: TransactionProcessorAgent = Depends(get_transaction_agent),  # noqa: B008
) -> Transaction:
    """Get a transaction by ID."""
    try:
        return await agent.get_transaction(transaction_id)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")


@router.post("/{transaction_id}/process", response_model=Transaction)
async def process_transaction(
    transaction_id: UUID,
    agent: TransactionProcessorAgent = Depends(get_transaction_agent),  # noqa: B008
) -> Transaction:
    """Process a pending transaction."""
    try:
        return await agent.process_transaction(transaction_id)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{transaction_id}/complete", response_model=Transaction)
async def complete_transaction(
    transaction_id: UUID,
    agent: TransactionProcessorAgent = Depends(get_transaction_agent),  # noqa: B008
) -> Transaction:
    """Mark a transaction as completed."""
    try:
        return await agent.complete_transaction(transaction_id)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")


@router.post("/{transaction_id}/refund", response_model=Transaction)
async def refund_transaction(
    transaction_id: UUID,
    reason: str = "",
    agent: TransactionProcessorAgent = Depends(get_transaction_agent),  # noqa: B008
) -> Transaction:
    """Refund a transaction."""
    try:
        return await agent.refund_transaction(transaction_id, reason)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")


@router.get("", response_model=list[Transaction])
async def list_transactions(
    buyer_id: str | None = Query(None),
    seller_id: str | None = Query(None),
    status: TransactionStatus | None = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    agent: TransactionProcessorAgent = Depends(get_transaction_agent),  # noqa: B008
) -> list[Transaction]:
    """List transactions with optional filters."""
    return await agent.list_transactions(
        buyer_id=buyer_id, seller_id=seller_id, status=status, limit=limit, offset=offset
    )


@router.get("/stats/summary")
async def get_transaction_stats(
    agent: TransactionProcessorAgent = Depends(get_transaction_agent),  # noqa: B008
) -> dict:
    """Get transaction statistics."""
    return await agent.get_transaction_stats()
