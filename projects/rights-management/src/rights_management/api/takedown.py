"""Takedown API routes."""

from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request

from rights_management.agents.takedown import TakedownAgent
from rights_management.integrations.storage import InMemoryStorage
from rights_management.models import (
    TakedownProcessRequest,
    TakedownRequest,
    TakedownRequestCreate,
    TakedownStatus,
)

router = APIRouter()


def get_storage(request: Request) -> InMemoryStorage:
    """Dependency to retrieve the storage backend from app state.

    Args:
        request: The incoming FastAPI request.

    Returns:
        The InMemoryStorage instance.
    """
    return request.app.state.storage


def get_agent(request: Request) -> TakedownAgent:
    """Dependency to retrieve the takedown agent.

    Args:
        request: The incoming FastAPI request.

    Returns:
        The TakedownAgent instance.
    """
    if not hasattr(request.app.state, "takedown_agent"):
        request.app.state.takedown_agent = TakedownAgent()
    return request.app.state.takedown_agent


@router.post("/request", response_model=TakedownRequest, status_code=201)
async def submit_takedown_request(
    payload: TakedownRequestCreate,
    storage: InMemoryStorage = Depends(get_storage),
    agent: TakedownAgent = Depends(get_agent),
) -> TakedownRequest:
    """Submit a new takedown request.

    Args:
        payload: The takedown request data.
        storage: The storage backend.
        agent: The takedown agent.

    Returns:
        The created TakedownRequest.
    """
    request_obj = await agent.run(
        {
            "id": str(uuid.uuid4()),
            "content_id": payload.content_id,
            "requester_id": payload.requester_id,
            "reason": payload.reason,
            "legal_basis": payload.legal_basis,
            "metadata": payload.metadata,
        }
    )
    await storage.save_takedown_request(request_obj)
    return request_obj


@router.get("/{request_id}", response_model=TakedownRequest)
async def get_takedown_request(
    request_id: str,
    storage: InMemoryStorage = Depends(get_storage),
) -> TakedownRequest:
    """Retrieve a specific takedown request.

    Args:
        request_id: The takedown request identifier.
        storage: The storage backend.

    Returns:
        The requested TakedownRequest.

    Raises:
        HTTPException: If the request is not found.
    """
    request_obj = await storage.get_takedown_request(request_id)
    if request_obj is None:
        raise HTTPException(status_code=404, detail="Takedown request not found")
    return request_obj


@router.post("/{request_id}/process", response_model=TakedownRequest)
async def process_takedown_request(
    request_id: str,
    payload: TakedownProcessRequest,
    storage: InMemoryStorage = Depends(get_storage),
    agent: TakedownAgent = Depends(get_agent),
) -> TakedownRequest:
    """Process a takedown request with a decision.

    Args:
        request_id: The takedown request identifier.
        payload: The processing decision.
        storage: The storage backend.
        agent: The takedown agent.

    Returns:
        The updated TakedownRequest.

    Raises:
        HTTPException: If the request is not found.
    """
    request_obj = await storage.get_takedown_request(request_id)
    if request_obj is None:
        raise HTTPException(status_code=404, detail="Takedown request not found")
    updated = await agent.process(request_obj, payload)
    await storage.save_takedown_request(updated)
    return updated


@router.get("", response_model=list[TakedownRequest])
async def list_takedown_requests(
    content_id: str | None = None,
    status: TakedownStatus | None = None,
    storage: InMemoryStorage = Depends(get_storage),
) -> list[TakedownRequest]:
    """List takedown requests, optionally filtered.

    Args:
        content_id: Filter by content identifier.
        status: Filter by request status.
        storage: The storage backend.

    Returns:
        List of matching takedown requests.
    """
    return await storage.list_takedown_requests(content_id=content_id, status=status)
