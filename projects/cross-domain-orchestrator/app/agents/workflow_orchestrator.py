"""Workflow Orchestrator Agent.

Manages the execution of workflows, coordinating step execution,
handling dependencies, and managing workflow state.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime
from typing import Any

from app.models.workflow import (
    Workflow,
    WorkflowExecutionRequest,
    WorkflowResult,
    WorkflowState,
    WorkflowStep,
    WorkflowStepResult,
)

logger = logging.getLogger(__name__)


class WorkflowOrchestratorAgent:
    """Agent responsible for orchestrating workflow execution.

    Manages workflow lifecycle, step scheduling, dependency resolution,
    and execution monitoring.

    Attributes:
        workflows: Registry of defined workflows.
        active_executions: Currently running workflow executions.
    """

    def __init__(self) -> None:
        """Initialize the Workflow Orchestrator Agent."""
        self.workflows: dict[str, Workflow] = {}
        self.active_executions: dict[str, WorkflowResult] = {}

    def register_workflow(self, workflow: Workflow) -> None:
        """Register a workflow definition.

        Args:
            workflow: The workflow to register.
        """
        self.workflows[workflow.id] = workflow
        logger.info(
            "Registered workflow: %s (id=%s, steps=%d)",
            workflow.name,
            workflow.id,
            len(workflow.steps),
        )

    def get_workflow(self, workflow_id: str) -> Workflow | None:
        """Get a workflow by ID.

        Args:
            workflow_id: Workflow identifier.

        Returns:
            The workflow or None if not found.
        """
        return self.workflows.get(workflow_id)

    def list_workflows(self) -> list[Workflow]:
        """List all registered workflows.

        Returns:
            List of all registered workflows.
        """
        return list(self.workflows.values())

    def delete_workflow(self, workflow_id: str) -> bool:
        """Delete a workflow.

        Args:
            workflow_id: Workflow identifier.

        Returns:
            True if deleted, False if not found.
        """
        if workflow_id in self.workflows:
            del self.workflows[workflow_id]
            logger.info("Deleted workflow: %s", workflow_id)
            return True
        return False

    def execute_workflow(
        self,
        request: WorkflowExecutionRequest,
    ) -> WorkflowResult:
        """Execute a workflow.

        Args:
            request: Workflow execution request.

        Returns:
            Workflow execution result.
        """
        workflow = self.workflows.get(request.workflow_id)
        if workflow is None:
            logger.error("Workflow not found: %s", request.workflow_id)
            return WorkflowResult(
                workflow_id=request.workflow_id,
                success=False,
                error=f"Workflow '{request.workflow_id}' not found",
            )

        logger.info(
            "Starting workflow execution: %s (id=%s)",
            workflow.name,
            workflow.id,
        )

        workflow.state = WorkflowState.RUNNING
        workflow.updated_at = datetime.utcnow()

        started_at = datetime.utcnow()
        step_results: list[WorkflowStepResult] = []
        overall_success = True

        # Sort steps by order and resolve dependencies
        sorted_steps = sorted(workflow.steps, key=lambda s: s.order)
        completed_steps: set[str] = set()

        for step in sorted_steps:
            # Check dependencies
            if step.depends_on and not all(dep in completed_steps for dep in step.depends_on):
                logger.warning(
                    "Skipping step %s: dependencies not met",
                    step.id,
                )
                step_results.append(
                    WorkflowStepResult(
                        step_id=step.id,
                        success=False,
                        error="Dependencies not met",
                    ),
                )
                overall_success = False
                continue

            step_result = self._execute_step(step, request.parameters)
            step_results.append(step_result)

            if step_result.success:
                completed_steps.add(step.id)
            else:
                overall_success = False
                logger.error("Step %s failed: %s", step.id, step_result.error)

        completed_at = datetime.utcnow()
        total_duration_ms = (completed_at - started_at).total_seconds() * 1000

        workflow.state = WorkflowState.COMPLETED if overall_success else WorkflowState.FAILED
        workflow.updated_at = completed_at

        result = WorkflowResult(
            workflow_id=workflow.id,
            success=overall_success,
            step_results=step_results,
            started_at=started_at,
            completed_at=completed_at,
            total_duration_ms=total_duration_ms,
        )

        logger.info(
            "Workflow %s completed: success=%s, duration=%.2fms",
            workflow.id,
            overall_success,
            total_duration_ms,
        )

        return result

    def _execute_step(
        self,
        step: WorkflowStep,
        parameters: dict[str, Any],
    ) -> WorkflowStepResult:
        """Execute a single workflow step.

        Args:
            step: The step to execute.
            parameters: Execution parameters.

        Returns:
            Step execution result.
        """
        logger.info("Executing step: %s (action=%s)", step.name, step.action)
        started_at = datetime.utcnow()

        try:
            # Simulate step execution
            time.sleep(0.01)  # Minimal delay for simulation

            # Merge step parameters with execution parameters
            merged_params = {**step.parameters, **parameters}

            completed_at = datetime.utcnow()

            return WorkflowStepResult(
                step_id=step.id,
                success=True,
                output={
                    "step_name": step.name,
                    "domain": step.domain,
                    "action": step.action,
                    "parameters": merged_params,
                },
                started_at=started_at,
                completed_at=completed_at,
            )
        except Exception as exc:
            completed_at = datetime.utcnow()
            logger.exception("Step %s failed", step.id)
            return WorkflowStepResult(
                step_id=step.id,
                success=False,
                error=str(exc),
                started_at=started_at,
                completed_at=completed_at,
            )
