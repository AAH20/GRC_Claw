"""Progress tracking endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status

from onboarding_automator.agents import ProgressTrackerAgent
from onboarding_automator.integrations.store import InMemoryStore
from onboarding_automator.models import AgentResponse, Progress, ProgressUpdate

__all__ = ["router"]

router = APIRouter()


def get_store(request: Request) -> InMemoryStore:
    """Dependency to get the in-memory store from app state."""
    return request.app.state.store


@router.get("/{plan_id}", response_model=Progress)
async def get_progress(
    plan_id: UUID,
    store: InMemoryStore = Depends(get_store)  # noqa: B008
) -> Progress:
    """Get progress for a specific onboarding plan.

    Args:
        plan_id: The plan's unique identifier.

    Returns:
        The progress record for the plan.

    Raises:
        HTTPException: If no progress record exists.
    """
    progress = await store.get_progress(plan_id)
    if progress is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No progress record found for plan {plan_id}",
        )
    return progress


@router.post("/{plan_id}", response_model=Progress, status_code=status.HTTP_201_CREATED)
async def create_progress(
    plan_id: UUID,
    store: InMemoryStore = Depends(get_store)  # noqa: B008
) -> Progress:
    """Create a new progress record for a plan.

    Args:
        plan_id: The plan's unique identifier.

    Returns:
        The newly created progress record.
    """
    progress = Progress(plan_id=plan_id)
    await store.save_progress(progress)

    # Link progress to plan
    plan = await store.get_plan(plan_id)
    if plan:
        plan.progress = progress.id
        await store.save_plan(plan)

    return progress


@router.patch("/{plan_id}", response_model=Progress)
async def update_progress(
    plan_id: UUID,
    update_data: ProgressUpdate,
    store: InMemoryStore = Depends(get_store)  # noqa: B008
) -> Progress:
    """Update progress for a plan.

    Args:
        plan_id: The plan's unique identifier.
        update_data: The fields to update.

    Returns:
        The updated progress record.

    Raises:
        HTTPException: If no progress record exists.
    """
    progress = await store.get_progress(plan_id)
    if progress is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No progress record found for plan {plan_id}",
        )

    if update_data.total_tasks is not None:
        progress.total_tasks = update_data.total_tasks
    if update_data.completed_tasks is not None:
        progress.completed_tasks = update_data.completed_tasks
    if update_data.blocked_tasks is not None:
        progress.blocked_tasks = update_data.blocked_tasks
    if update_data.pending_tasks is not None:
        progress.pending_tasks = update_data.pending_tasks
    if update_data.risk_assessment is not None:
        progress.risk_assessment = update_data.risk_assessment
    if update_data.estimated_completion is not None:
        progress.estimated_completion = update_data.estimated_completion

    # Recalculate completion percentage
    if progress.total_tasks > 0:
        progress.completion_percentage = round(
            progress.completed_tasks / progress.total_tasks * 100, 1
        )

    from datetime import datetime

    progress.updated_at = datetime.utcnow()
    await store.save_progress(progress)
    return progress


@router.post("/{plan_id}/recalculate", response_model=AgentResponse)
async def recalculate_progress(
    plan_id: UUID,
    request: Request,
    store: InMemoryStore = Depends(get_store)  # noqa: B008
) -> AgentResponse:
    """Trigger progress recalculation via the ProgressTrackerAgent.

    Args:
        plan_id: The plan's unique identifier.
        request: The incoming request.

    Returns:
        AgentResponse with the recalculation result.

    Raises:
        HTTPException: If the plan is not found.
    """
    plan = await store.get_plan(plan_id)
    if plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Onboarding plan {plan_id} not found",
        )

    tasks = await store.list_tasks(plan_id=plan_id)
    progress = await store.get_progress(plan_id)

    agent = ProgressTrackerAgent(request.app.state.settings)
    return await agent.execute(plan, tasks, progress)


@router.get("/{plan_id}/report", response_model=AgentResponse)
async def generate_report(
    plan_id: UUID,
    request: Request,
    store: InMemoryStore = Depends(get_store)  # noqa: B008
) -> AgentResponse:
    """Generate a detailed progress report.

    Args:
        plan_id: The plan's unique identifier.
        request: The incoming request.

    Returns:
        AgentResponse with the generated report.

    Raises:
        HTTPException: If the plan or progress is not found.
    """
    plan = await store.get_plan(plan_id)
    if plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Onboarding plan {plan_id} not found",
        )

    progress = await store.get_progress(plan_id)
    if progress is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No progress record found for plan {plan_id}",
        )

    tasks = await store.list_tasks(plan_id=plan_id)
    agent = ProgressTrackerAgent(request.app.state.settings)
    return await agent.generate_progress_report(plan, tasks, progress)
