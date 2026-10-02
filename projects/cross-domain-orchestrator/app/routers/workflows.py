"""Workflow router.

Provides endpoints for workflow management and execution.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, status

from app.agents.result_aggregator import ResultAggregatorAgent
from app.agents.workflow_orchestrator import WorkflowOrchestratorAgent
from app.models.workflow import (
    Workflow,
    WorkflowExecutionRequest,
    WorkflowResult,
    WorkflowState,
    WorkflowStep,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# Module-level agent instances (in production, use dependency injection)
_orchestrator = WorkflowOrchestratorAgent()
_aggregator = ResultAggregatorAgent()


@router.post("", response_model=Workflow, status_code=status.HTTP_201_CREATED)
async def create_workflow(workflow: Workflow) -> Workflow:
    """Create a new workflow.

    Args:
        workflow: Workflow definition to create.

    Returns:
        The created workflow.
    """
    _orchestrator.register_workflow(workflow)
    return workflow


@router.get("", response_model=list[Workflow])
async def list_workflows() -> list[Workflow]:
    """List all registered workflows.

    Returns:
        List of all workflows.
    """
    return _orchestrator.list_workflows()


@router.get("/{workflow_id}", response_model=Workflow)
async def get_workflow(workflow_id: str) -> Workflow:
    """Get a workflow by ID.

    Args:
        workflow_id: Workflow identifier.

    Returns:
        The requested workflow.

    Raises:
        HTTPException: If the workflow is not found.
    """
    workflow = _orchestrator.get_workflow(workflow_id)
    if workflow is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow '{workflow_id}' not found",
        )
    return workflow


@router.delete("/{workflow_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workflow(workflow_id: str) -> None:
    """Delete a workflow.

    Args:
        workflow_id: Workflow identifier.

    Raises:
        HTTPException: If the workflow is not found.
    """
    if not _orchestrator.delete_workflow(workflow_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow '{workflow_id}' not found",
        )


@router.post("/{workflow_id}/execute", response_model=WorkflowResult)
async def execute_workflow(
    workflow_id: str,
    request: WorkflowExecutionRequest | None = None,
) -> WorkflowResult:
    """Execute a workflow.

    Args:
        workflow_id: Workflow identifier.
        request: Optional execution request parameters.

    Returns:
        Workflow execution result.

    Raises:
        HTTPException: If the workflow is not found.
    """
    if request is None:
        request = WorkflowExecutionRequest(workflow_id=workflow_id)
    else:
        request.workflow_id = workflow_id

    result = _orchestrator.execute_workflow(request)
    if not result.success and not result.step_results:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow '{workflow_id}' not found",
        )
    return result


@router.post("/{workflow_id}/steps", response_model=Workflow)
async def add_step(workflow_id: str, step: WorkflowStep) -> Workflow:
    """Add a step to a workflow.

    Args:
        workflow_id: Workflow identifier.
        step: Step to add.

    Returns:
        Updated workflow.

    Raises:
        HTTPException: If the workflow is not found.
    """
    workflow = _orchestrator.get_workflow(workflow_id)
    if workflow is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow '{workflow_id}' not found",
        )
    workflow.steps.append(step)
    return workflow


@router.get("/{workflow_id}/summary")
async def get_workflow_summary(workflow_id: str) -> dict:
    """Get a summary of the last execution for a workflow.

    Args:
        workflow_id: Workflow identifier.

    Returns:
        Workflow execution summary.

    Raises:
        HTTPException: If the workflow is not found.
    """
    workflow = _orchestrator.get_workflow(workflow_id)
    if workflow is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow '{workflow_id}' not found",
        )
    return {
        "workflow_id": workflow.id,
        "name": workflow.name,
        "state": workflow.state.value,
        "step_count": len(workflow.steps),
    }
