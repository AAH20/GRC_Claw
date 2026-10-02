"""Onboarding plan endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status

from onboarding_automator.agents import TaskGeneratorAgent
from onboarding_automator.config.settings import Settings, get_settings
from onboarding_automator.integrations.store import InMemoryStore
from onboarding_automator.models import (
    AgentResponse,
    OnboardingPlan,
    OnboardingPlanCreate,
    OnboardingPlanUpdate,
)

__all__ = ["router"]

router = APIRouter()


def get_store(request: Request) -> InMemoryStore:
    """Dependency to get the in-memory store from app state."""
    return request.app.state.store


def get_task_agent(request: Request) -> TaskGeneratorAgent:
    """Dependency to get the task generator agent."""
    return TaskGeneratorAgent(request.app.state.settings)


@router.post("", response_model=OnboardingPlan, status_code=status.HTTP_201_CREATED)
async def create_plan(
    plan_data: OnboardingPlanCreate,
    store: InMemoryStore = Depends(get_store),
) -> OnboardingPlan:
    """Create a new onboarding plan.

    Args:
        plan_data: The plan creation data.

    Returns:
        The newly created onboarding plan.
    """
    plan = OnboardingPlan(
        employee=plan_data.employee,
        metadata=plan_data.metadata,
    )
    await store.save_plan(plan)
    return plan


@router.get("", response_model=list[OnboardingPlan])
async def list_plans(
    store: InMemoryStore = Depends(get_store),
    skip: int = 0,
    limit: int = 100,
) -> list[OnboardingPlan]:
    """List all onboarding plans with pagination.

    Args:
        skip: Number of records to skip.
        limit: Maximum number of records to return.

    Returns:
        List of onboarding plans.
    """
    plans = await store.list_plans()
    return plans[skip : skip + limit]


@router.get("/{plan_id}", response_model=OnboardingPlan)
async def get_plan(
    plan_id: UUID,
    store: InMemoryStore = Depends(get_store),
) -> OnboardingPlan:
    """Get a specific onboarding plan by ID.

    Args:
        plan_id: The plan's unique identifier.

    Returns:
        The requested onboarding plan.

    Raises:
        HTTPException: If the plan is not found.
    """
    plan = await store.get_plan(plan_id)
    if plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Onboarding plan {plan_id} not found",
        )
    return plan


@router.patch("/{plan_id}", response_model=OnboardingPlan)
async def update_plan(
    plan_id: UUID,
    update_data: OnboardingPlanUpdate,
    store: InMemoryStore = Depends(get_store),
) -> OnboardingPlan:
    """Update an existing onboarding plan.

    Args:
        plan_id: The plan's unique identifier.
        update_data: The fields to update.

    Returns:
        The updated onboarding plan.

    Raises:
        HTTPException: If the plan is not found.
    """
    plan = await store.get_plan(plan_id)
    if plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Onboarding plan {plan_id} not found",
        )

    if update_data.status is not None:
        plan.status = update_data.status
    if update_data.metadata is not None:
        plan.metadata.update(update_data.metadata)

    from datetime import datetime

    plan.updated_at = datetime.utcnow()
    await store.save_plan(plan)
    return plan


@router.delete("/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_plan(
    plan_id: UUID,
    store: InMemoryStore = Depends(get_store),
) -> None:
    """Delete an onboarding plan.

    Args:
        plan_id: The plan's unique identifier.

    Raises:
        HTTPException: If the plan is not found.
    """
    deleted = await store.delete_plan(plan_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Onboarding plan {plan_id} not found",
        )


@router.post("/{plan_id}/generate-tasks", response_model=AgentResponse)
async def generate_tasks(
    plan_id: UUID,
    request: Request,
    store: InMemoryStore = Depends(get_store),
) -> AgentResponse:
    """Trigger task generation for an onboarding plan.

    Args:
        plan_id: The plan's unique identifier.
        request: The incoming request.

    Returns:
        AgentResponse with the generation result.

    Raises:
        HTTPException: If the plan is not found.
    """
    plan = await store.get_plan(plan_id)
    if plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Onboarding plan {plan_id} not found",
        )

    agent = TaskGeneratorAgent(request.app.state.settings)
    plan_create = OnboardingPlanCreate(employee=plan.employee, metadata=plan.metadata)
    existing_tasks = await store.list_tasks(plan_id=plan_id)
    return await agent.execute(plan_create, existing_tasks)
