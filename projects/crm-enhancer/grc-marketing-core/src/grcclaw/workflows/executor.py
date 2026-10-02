"""
Workflow executor for GRC_Claw.

High-level executor that provides a simplified interface for running
workflows, managing step handlers, and integrating with the GRC agent
ecosystem.
"""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Any, Callable, Optional

from .engine import WorkflowEngine
from .schema import (
    StepStatus,
    StepType,
    WorkflowDefinition,
    WorkflowRun,
    WorkflowStatus,
    StepResult,
    TriggerType,
)

logger = logging.getLogger(__name__)


class WorkflowExecutor:
    """High-level workflow executor with GRC-specific integrations."""

    def __init__(self, engine: Optional[WorkflowEngine] = None):
        self.engine = engine or WorkflowEngine()
        self._agent_handlers: dict[str, Callable] = {}
        self._tool_handlers: dict[str, Callable] = {}
        self._notification_handlers: list[Callable] = []
        self._approval_callbacks: dict[str, asyncio.Future] = {}

    def register_agent_handler(self, agent_name: str, handler: Callable) -> None:
        self._agent_handlers[agent_name] = handler
        logger.info("registered agent handler for '%s'", agent_name)

    def register_tool_handler(self, tool_name: str, handler: Callable) -> None:
        self._tool_handlers[tool_name] = handler
        logger.info("registered tool handler for '%s'", tool_name)

    def register_notification_handler(self, handler: Callable) -> None:
        self._notification_handlers.append(handler)

    async def execute(
        self,
        workflow: WorkflowDefinition,
        parameters: Optional[dict[str, Any]] = None,
        triggered_by: str = "",
        wait: bool = True,
        timeout: Optional[float] = None,
    ) -> WorkflowRun:
        if workflow.status != WorkflowStatus.ACTIVE:
            workflow.status = WorkflowStatus.ACTIVE

        self.engine.register_workflow(workflow)
        self._register_default_handlers()

        run = await self.engine.start_run(
            workflow_id=workflow.id,
            parameters=parameters,
            triggered_by=triggered_by,
        )

        if wait:
            await self._wait_for_completion(run.run_id, timeout=timeout)

        return run

    async def execute_step(
        self,
        step_type: StepType,
        step_id: str,
        run: WorkflowRun,
        definition: WorkflowDefinition,
    ) -> Any:
        step = definition.get_step(step_id)
        if step is None:
            raise KeyError(f"step '{step_id}' not found in workflow")

        if step.agent and step.agent in self._agent_handlers:
            return await self._agent_handlers[step.agent](step, run, definition)
        if step.tool and step.tool in self._tool_handlers:
            return await self._tool_handlers[step.tool](step, run, definition)

        handler = self.engine._handlers.get(step_type)
        if handler:
            return await handler(step, run, definition)

        raise RuntimeError(
            f"no handler available for step '{step_id}' "
            f"(agent={step.agent}, tool={step.tool}, type={step_type})"
        )

    async def request_approval(
        self,
        run_id: str,
        step_id: str,
        prompt: str,
        timeout: float = 3600.0,
    ) -> bool:
        future: asyncio.Future = asyncio.get_event_loop().create_future()
        key = f"{run_id}:{step_id}"
        self._approval_callbacks[key] = future

        for handler in self._notification_handlers:
            try:
                await handler(
                    type="approval_required",
                    run_id=run_id,
                    step_id=step_id,
                    prompt=prompt,
                )
            except Exception:
                logger.exception("notification handler failed")

        try:
            result = await asyncio.wait_for(future, timeout=timeout)
            return bool(result)
        except asyncio.TimeoutError:
            return False
        finally:
            self._approval_callbacks.pop(key, None)

    def resolve_approval(self, run_id: str, step_id: str, approved: bool) -> bool:
        key = f"{run_id}:{step_id}"
        future = self._approval_callbacks.get(key)
        if future and not future.done():
            future.set_result(approved)
            return True
        return False

    async def get_run_status(self, run_id: str) -> Optional[dict[str, Any]]:
        run = await self.engine.get_run(run_id)
        if run is None:
            return None
        return {
            "run_id": run.run_id,
            "workflow_id": run.workflow_id,
            "workflow_name": run.workflow_name,
            "status": run.status.value,
            "progress_pct": run.progress_pct,
            "started_at": run.started_at,
            "finished_at": run.finished_at,
            "duration_seconds": run.duration_seconds,
            "error": run.error,
            "step_results": {
                sid: {
                    "status": r.status.value,
                    "duration_seconds": r.duration_seconds,
                    "attempt": r.attempt,
                    "error": r.error,
                }
                for sid, r in run.step_results.items()
            },
        }

    async def cancel(self, run_id: str) -> bool:
        return await self.engine.cancel_run(run_id)

    async def wait(self, run_id: str, timeout: Optional[float] = None) -> WorkflowRun:
        await self._wait_for_completion(run_id, timeout=timeout)
        run = await self.engine.get_run(run_id)
        if run is None:
            raise KeyError(f"run '{run_id}' not found")
        return run

    def _register_default_handlers(self) -> None:
        if StepType.ACTION not in self.engine._handlers:
            self.engine.register_handler(StepType.ACTION, self.execute_step)
        if StepType.NOTIFICATION not in self.engine._handlers:
            self.engine.register_handler(StepType.NOTIFICATION, self._handle_notification)
        if StepType.HUMAN_APPROVAL not in self.engine._handlers:
            self.engine.register_handler(StepType.HUMAN_APPROVAL, self._handle_approval)
        if StepType.WAIT not in self.engine._handlers:
            self.engine.register_handler(StepType.WAIT, self._handle_wait)

    async def _handle_notification(self, step, run: WorkflowRun, definition: WorkflowDefinition) -> None:
        message = step.parameters.get("message", f"Step '{step.name}' completed")
        for handler in self._notification_handlers:
            try:
                await handler(
                    type="notification",
                    run_id=run.run_id,
                    step_id=step.id,
                    message=message,
                )
            except Exception:
                logger.exception("notification handler failed")

    async def _handle_approval(self, step, run: WorkflowRun, definition: WorkflowDefinition) -> None:
        prompt = step.parameters.get("prompt", f"Approval required for step '{step.name}'")
        approved = await self.request_approval(run.run_id, step.id, prompt)
        if not approved:
            raise RuntimeError(f"approval denied for step '{step.id}'")

    async def _handle_wait(self, step, run: WorkflowRun, definition: WorkflowDefinition) -> None:
        duration = step.parameters.get("duration_seconds", 1.0)
        await asyncio.sleep(duration)

    async def _wait_for_completion(
        self,
        run_id: str,
        timeout: Optional[float] = None,
    ) -> None:
        start = time.monotonic()
        while True:
            run = await self.engine.get_run(run_id)
            if run is None:
                raise KeyError(f"run '{run_id}' not found")
            if run.is_complete:
                return
            if timeout is not None and (time.monotonic() - start) > timeout:
                raise TimeoutError(f"run '{run_id}' did not complete within {timeout}s")
            await asyncio.sleep(0.1)

    # ------------------------------------------------------------------
    # Batch execution
    # ------------------------------------------------------------------

    async def execute_batch(
        self,
        workflows: list[WorkflowDefinition],
        parameters: Optional[dict[str, Any]] = None,
        triggered_by: str = "",
        max_concurrent: int = 5,
    ) -> list[WorkflowRun]:
        """
        Execute multiple workflows concurrently.

        Args:
            workflows: List of workflow definitions to execute.
            parameters: Parameters to pass to each workflow.
            triggered_by: Who/what triggered the batch.
            max_concurrent: Maximum number of concurrent executions.

        Returns:
            List of completed WorkflowRun objects.
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def run_with_semaphore(wf: WorkflowDefinition) -> WorkflowRun:
            async with semaphore:
                return await self.execute(
                    wf, parameters=parameters, triggered_by=triggered_by, wait=True
                )

        tasks = [run_with_semaphore(wf) for wf in workflows]
        return await asyncio.gather(*tasks)

    # ------------------------------------------------------------------
    # Workflow composition
    # ------------------------------------------------------------------

    async def execute_chain(
        self,
        workflows: list[WorkflowDefinition],
        parameters: Optional[dict[str, Any]] = None,
        triggered_by: str = "",
        pass_context: bool = True,
    ) -> list[WorkflowRun]:
        """
        Execute workflows in sequence, passing context from one to the next.

        Args:
            workflows: Ordered list of workflow definitions.
            parameters: Initial parameters.
            triggered_by: Who/what triggered the chain.
            pass_context: If True, merge previous run context into next run parameters.

        Returns:
            List of completed WorkflowRun objects.
        """
        runs: list[WorkflowRun] = []
        current_params = dict(parameters or {})

        for wf in workflows:
            run = await self.execute(
                wf, parameters=current_params, triggered_by=triggered_by, wait=True
            )
            runs.append(run)
            if pass_context and run.context:
                current_params.update(run.context)

        return runs

    # ------------------------------------------------------------------
    # Statistics
    # ------------------------------------------------------------------

    def get_stats(self) -> dict[str, Any]:
        """Get executor statistics."""
        return {
            "agent_handlers": list(self._agent_handlers.keys()),
            "tool_handlers": list(self._tool_handlers.keys()),
            "notification_handlers": len(self._notification_handlers),
            "pending_approvals": len(self._approval_callbacks),
            "engine_stats": self.engine.get_stats(),
        }
