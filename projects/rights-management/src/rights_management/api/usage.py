"""Usage tracking API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from rights_management.agents.usage_tracker import UsageTrackerAgent
from rights_management.integrations.storage import InMemoryStorage
from rights_management.models import UsageRecord, UsageRecordCreate, UsageSummary

router = APIRouter()


def get_storage(request: Request) -> InMemoryStorage:
    """Dependency to retrieve the storage backend from app state.

    Args:
        request: The incoming FastAPI request.

    Returns:
        The InMemoryStorage instance.
    """
    return request.app.state.storage


def get_agent(request: Request) -> UsageTrackerAgent:
    """Dependency to retrieve the usage tracker agent.

    Args:
        request: The incoming FastAPI request.

    Returns:
        The UsageTrackerAgent instance.
    """
    if not hasattr(request.app.state, "usage_tracker_agent"):
        request.app.state.usage_tracker_agent = UsageTrackerAgent()
    return request.app.state.usage_tracker_agent


@router.post("/record", response_model=UsageRecord, status_code=201)
async def record_usage(
    payload: UsageRecordCreate,
    storage: InMemoryStorage = Depends(get_storage),  # noqa: B008
    agent: UsageTrackerAgent = Depends(get_agent),  # noqa: B008
) -> UsageRecord:
    """Record a content usage event.

    Args:
        payload: The usage event data.
        storage: The storage backend.
        agent: The usage tracker agent.

    Returns:
        The recorded UsageRecord.
    """
    record = await agent.run(payload.model_dump())
    await storage.save_usage_record(record)
    return record


@router.get("/summary/{content_id}", response_model=UsageSummary)
async def get_usage_summary(
    content_id: str,
    storage: InMemoryStorage = Depends(get_storage),  # noqa: B008
    agent: UsageTrackerAgent = Depends(get_agent),  # noqa: B008
) -> UsageSummary:
    """Get usage statistics for a piece of content.

    Args:
        content_id: The content identifier.
        storage: The storage backend.
        agent: The usage tracker agent.

    Returns:
        The usage summary.
    """
    records = await storage.list_usage_records(content_id=content_id)
    return await agent.summarize(content_id, records)


@router.get("/records/{content_id}", response_model=list[UsageRecord])
async def list_usage_records(
    content_id: str,
    storage: InMemoryStorage = Depends(get_storage),  # noqa: B008
) -> list[UsageRecord]:
    """List all usage records for a piece of content.

    Args:
        content_id: The content identifier.
        storage: The storage backend.

    Returns:
        List of usage records.
    """
    return await storage.list_usage_records(content_id=content_id)
