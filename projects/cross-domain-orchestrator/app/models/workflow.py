"""Workflow-related Pydantic models.

Defines the data structures for workflows, steps, and execution results.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class WorkflowState(str, Enum):
    """Enumeration of possible workflow states."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowStep(BaseModel):
    """Represents a single step within a workflow.

    Attributes:
        id: Unique step identifier.
        name: Human-readable step name.
        domain: Target domain for this step.
        action: Action to perform.
        parameters: Step-specific parameters.
        depends_on: List of step IDs this step depends on.
        order: Execution order within the workflow.
    """

    id: str = Field(default_factory=lambda: str(uuid4()), description="Step unique identifier")
    name: str = Field(..., min_length=1, max_length=256, description="Step name")
    domain: str = Field(..., min_length=1, max_length=128, description="Target domain")
    action: str = Field(..., min_length=1, max_length=128, description="Action to perform")
    parameters: dict[str, Any] = Field(
        default_factory=dict,
        description="Step-specific parameters",
    )
    depends_on: list[str] = Field(
        default_factory=list,
        description="IDs of steps this step depends on",
    )
    order: int = Field(default=0, ge=0, description="Execution order")


class Workflow(BaseModel):
    """Represents a complete workflow definition.

    Attributes:
        id: Unique workflow identifier.
        name: Human-readable workflow name.
        description: Optional workflow description.
        steps: Ordered list of workflow steps.
        state: Current workflow state.
        created_at: Creation timestamp.
        updated_at: Last update timestamp.
        metadata: Additional workflow metadata.
    """

    id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Workflow unique identifier",
    )
    name: str = Field(..., min_length=1, max_length=256, description="Workflow name")
    description: str = Field(default="", description="Workflow description")
    steps: list[WorkflowStep] = Field(
        default_factory=list,
        description="Workflow steps",
    )
    state: WorkflowState = Field(
        default=WorkflowState.PENDING,
        description="Current workflow state",
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Creation timestamp",
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Last update timestamp",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional workflow metadata",
    )


class WorkflowStepResult(BaseModel):
    """Result of executing a single workflow step.

    Attributes:
        step_id: ID of the step that was executed.
        success: Whether the step succeeded.
        output: Step output data.
        error: Error message if the step failed.
        started_at: Execution start timestamp.
        completed_at: Execution completion timestamp.
    """

    step_id: str = Field(..., description="Step identifier")
    success: bool = Field(..., description="Whether the step succeeded")
    output: dict[str, Any] = Field(
        default_factory=dict,
        description="Step output data",
    )
    error: str | None = Field(default=None, description="Error message if failed")
    started_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Execution start timestamp",
    )
    completed_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Execution completion timestamp",
    )


class WorkflowResult(BaseModel):
    """Complete result of a workflow execution.

    Attributes:
        workflow_id: ID of the executed workflow.
        success: Whether the overall workflow succeeded.
        step_results: Results from each step.
        started_at: Execution start timestamp.
        completed_at: Execution completion timestamp.
        total_duration_ms: Total execution duration in milliseconds.
    """

    workflow_id: str = Field(..., description="Workflow identifier")
    success: bool = Field(..., description="Whether the workflow succeeded")
    step_results: list[WorkflowStepResult] = Field(
        default_factory=list,
        description="Results from each step",
    )
    started_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Execution start timestamp",
    )
    completed_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Execution completion timestamp",
    )
    total_duration_ms: float = Field(
        default=0.0,
        ge=0,
        description="Total execution duration in milliseconds",
    )


class WorkflowExecutionRequest(BaseModel):
    """Request to execute a workflow.

    Attributes:
        workflow_id: ID of the workflow to execute.
        parameters: Override parameters for execution.
        async_execution: Whether to execute asynchronously.
    """

    workflow_id: str = Field(..., description="Workflow identifier")
    parameters: dict[str, Any] = Field(
        default_factory=dict,
        description="Override parameters",
    )
    async_execution: bool = Field(
        default=False,
        description="Execute asynchronously",
    )
