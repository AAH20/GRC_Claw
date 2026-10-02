"""Task management endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status

from onboarding_automator.integrations.store import InMemoryStore
from onboarding_automator.models import Task, TaskCreate, TaskUpdate

__all__ = ["router"]

router = APIRouter()


def get_store(request: Request) -> InMemoryStore:
    """Dependency to get the in-memory store from app state."""
    return request.app.state.store


@router.post("", response_model=Task, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_data: TaskCreate,
    store: InMemoryStore = Depends(get_store)  # noqa: B008
) -> Task:
    """Create a new onboarding task.

    Args:
        task_data: The task creation data.

    Returns:
        The newly created task.
    """
    task = Task(
        plan_id=task_data.plan_id,
        title=task_data.title,
        description=task_data.description,
        task_type=task_data.task_type,
        priority=task_data.priority,
        due_date=task_data.due_date,
        assigned_to=task_data.assigned_to,
        metadata=task_data.metadata,
    )
    await store.save_task(task)

    # Add task to parent plan
    plan = await store.get_plan(task_data.plan_id)
    if plan:
        plan.tasks.append(task.id)
        await store.save_plan(plan)

    return task


@router.get("", response_model=list[Task])
async def list_tasks(
    store: InMemoryStore = Depends(get_store)  # noqa: B008
    plan_id: UUID | None = None,
    status_filter: str | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[Task]:
    """List tasks with optional filtering.

    Args:
        plan_id: Filter by parent plan ID.
        status_filter: Filter by task status.
        skip: Number of records to skip.
        limit: Maximum number of records to return.

    Returns:
        List of matching tasks.
    """
    tasks = await store.list_tasks(plan_id=plan_id)
    if status_filter:
        tasks = [t for t in tasks if t.status.value == status_filter]
    return tasks[skip : skip + limit]


@router.get("/{task_id}", response_model=Task)
async def get_task(
    task_id: UUID,
    store: InMemoryStore = Depends(get_store)  # noqa: B008
) -> Task:
    """Get a specific task by ID.

    Args:
        task_id: The task's unique identifier.

    Returns:
        The requested task.

    Raises:
        HTTPException: If the task is not found.
    """
    task = await store.get_task(task_id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found",
        )
    return task


@router.patch("/{task_id}", response_model=Task)
async def update_task(
    task_id: UUID,
    update_data: TaskUpdate,
    store: InMemoryStore = Depends(get_store)  # noqa: B008
) -> Task:
    """Update an existing task.

    Args:
        task_id: The task's unique identifier.
        update_data: The fields to update.

    Returns:
        The updated task.

    Raises:
        HTTPException: If the task is not found.
    """
    task = await store.get_task(task_id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found",
        )

    if update_data.title is not None:
        task.title = update_data.title
    if update_data.description is not None:
        task.description = update_data.description
    if update_data.status is not None:
        task.status = update_data.status
    if update_data.priority is not None:
        task.priority = update_data.priority
    if update_data.due_date is not None:
        task.due_date = update_data.due_date
    if update_data.assigned_to is not None:
        task.assigned_to = update_data.assigned_to
    if update_data.metadata is not None:
        task.metadata.update(update_data.metadata)

    from datetime import datetime

    task.updated_at = datetime.utcnow()
    await store.save_task(task)
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: UUID,
    store: InMemoryStore = Depends(get_store)  # noqa: B008
) -> None:
    """Delete a task.

    Args:
        task_id: The task's unique identifier.

    Raises:
        HTTPException: If the task is not found.
    """
    deleted = await store.delete_task(task_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found",
        )
