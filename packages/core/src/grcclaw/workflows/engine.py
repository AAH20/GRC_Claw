"""
Workflow engine for GRC_Claw.

Core orchestration engine that manages workflow lifecycle, step scheduling,
dependency resolution, parallel execution, and state transitions.
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Callable, Optional

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


class WorkflowEngine:
    """Core workflow orchestration engine."""

    def __init__(self):
        self._workflows: dict[str, WorkflowDefinition] = {}
        self._runs: dict[str, WorkflowRun] = {}
        self._handlers: dict[str, Callable] = {}
        self._running: set[str] = set()
        self._lock = asyncio.Lock()

    def register_workflow(self, definition: WorkflowDefinition) -> None:
        errors = definition.validate()
        if errors:
            raise ValueError(f"invalid workflow definition: {'; '.join(errors)}")
        self._workflows[definition.id] = definition
        logger.info("registered workflow %s (%s)", definition.name, definition.id)

    def unregister_workflow(self, workflow_id: str) -> bool:
        if workflow_id in self._workflows:
            del self._workflows[workflow_id]
            return True
        return False

    def get_workflow(self, workflow_id: str) -> Optional[WorkflowDefinition]:
        return self._workflows.get(workflow_id)

    def list_workflows(
        self,
        status: Optional[WorkflowStatus] = None,
        tag: Optional[str] = None,
    ) -> list[WorkflowDefinition]:
        results = list(self._workflows.values())
        if status is not None:
            results = [w for w in results if w.status == status]
        if tag is not None:
            results = [w for w in results if tag in w.tags]
        return results

    def register_handler(self, step_type: StepType, handler: Callable) -> None:
        self._handlers[step_type] = handler
        logger.info("registered handler for step type %s", step_type)

    async def start_run(
        self,
        workflow_id: str,
        parameters: Optional[dict[str, Any]] = None,
        triggered_by: str = "",
        parent_run_id: Optional[str] = None,
    ) -> WorkflowRun:
        definition = self._workflows.get(workflow_id)
        if definition is None:
            raise KeyError(f"workflow '{workflow_id}' not found")
        if definition.status != WorkflowStatus.ACTIVE:
            raise RuntimeError(
                f"workflow '{workflow_id}' is not active (status={definition.status})"
            )

        run = WorkflowRun(
            workflow_id=definition.id,
            workflow_name=definition.name,
            workflow_version=definition.version,
            trigger=TriggerType.MANUAL,
            parameters=parameters or {},
            triggered_by=triggered_by,
            parent_run_id=parent_run_id,
            started_at=datetime.now(timezone.utc).isoformat(),
        )

        for step in definition.steps:
            run.step_results[step.id] = StepResult(step_id=step.id)

        async with self._lock:
            self._runs[run.run_id] = run
            self._running.add(run.run_id)

        logger.info("started run %s for workflow %s", run.run_id, workflow_id)
        asyncio.create_task(self._execute_run(run.run_id))
        return run

    async def cancel_run(self, run_id: str) -> bool:
        run = self._runs.get(run_id)
        if run is None:
            return False
        if run.is_complete:
            return False
        run.status = StepStatus.CANCELLED
        run.finished_at = datetime.now(timezone.utc).isoformat()
        async with self._lock:
            self._running.discard(run_id)
        logger.info("cancelled run %s", run_id)
        return True

    async def get_run(self, run_id: str) -> Optional[WorkflowRun]:
        return self._runs.get(run_id)

    async def list_runs(
        self,
        workflow_id: Optional[str] = None,
        status: Optional[StepStatus] = None,
    ) -> list[WorkflowRun]:
        results = list(self._runs.values())
        if workflow_id is not None:
            results = [r for r in results if r.workflow_id == workflow_id]
        if status is not None:
            results = [r for r in results if r.status == status]
        return results

    async def _execute_run(self, run_id: str) -> None:
        run = self._runs.get(run_id)
        if run is None:
            return
        definition = self._workflows.get(run.workflow_id)
        if definition is None:
            return

        try:
            await self._run_steps(run, definition)
        except Exception as exc:
            logger.exception("run %s failed", run_id)
            run.status = StepStatus.FAILED
            run.error = str(exc)
        finally:
            run.finished_at = datetime.now(timezone.utc).isoformat()
            if run.started_at:
                start = datetime.fromisoformat(run.started_at)
                end = datetime.fromisoformat(run.finished_at)
                run.duration_seconds = (end - start).total_seconds()
            async with self._lock:
                self._running.discard(run_id)

    async def _run_steps(self, run: WorkflowRun, definition: WorkflowDefinition) -> None:
        completed: set[str] = set()
        failed: set[str] = set()

        while len(completed) + len(failed) < len(definition.steps):
            ready = self._get_ready_steps(definition, completed, failed, run)
            if not ready:
                if not self._has_pending(definition, completed, failed):
                    break
                await asyncio.sleep(0.1)
                continue

            parallel_tasks = []
            for step in ready:
                if step.type == StepType.PARALLEL:
                    parallel_tasks.append(self._execute_parallel_step(run, definition, step))
                else:
                    parallel_tasks.append(self._execute_step(run, definition, step))

            results = await asyncio.gather(*parallel_tasks, return_exceptions=True)
            for step, result in zip(ready, results):
                if isinstance(result, Exception):
                    failed.add(step.id)
                    run.step_results[step.id].status = StepStatus.FAILED
                    run.step_results[step.id].error = str(result)
                elif run.step_results[step.id].status == StepStatus.SUCCEEDED:
                    completed.add(step.id)
                else:
                    failed.add(step.id)

        if failed:
            run.status = StepStatus.FAILED
        elif len(completed) == len(definition.steps):
            run.status = StepStatus.SUCCEEDED
        else:
            run.status = StepStatus.SKIPPED

    def _get_ready_steps(
        self,
        definition: WorkflowDefinition,
        completed: set[str],
        failed: set[str],
        run: WorkflowRun,
    ) -> list:
        ready = []
        for step in definition.steps:
            if step.id in completed or step.id in failed:
                continue
            if run.step_results[step.id].status == StepStatus.RUNNING:
                continue
            deps_satisfied = all(
                d in completed for d in step.depends_on
            )
            if not deps_satisfied:
                continue
            deps_failed = any(d in failed for d in step.depends_on)
            if deps_failed:
                run.step_results[step.id].status = StepStatus.SKIPPED
                failed.add(step.id)
                continue
            if step.condition and not self._evaluate_condition(step.condition, run):
                run.step_results[step.id].status = StepStatus.SKIPPED
                failed.add(step.id)
                continue
            ready.append(step)
        return ready

    def _has_pending(
        self,
        definition: WorkflowDefinition,
        completed: set[str],
        failed: set[str],
    ) -> bool:
        for step in definition.steps:
            if step.id not in completed and step.id not in failed:
                return True
        return False

    def _evaluate_condition(self, condition, run: WorkflowRun) -> bool:
        if not condition.expression:
            return True
        try:
            context = {**run.parameters, **run.context}
            return bool(eval(condition.expression, {"__builtins__": {}}, context))
        except Exception:
            logger.warning("condition evaluation failed: %s", condition.expression)
            return False

    async def _execute_step(
        self,
        run: WorkflowRun,
        definition: WorkflowDefinition,
        step,
    ) -> None:
        result = run.step_results[step.id]
        result.status = StepStatus.RUNNING
        result.started_at = datetime.now(timezone.utc).isoformat()

        handler = self._handlers.get(step.type)
        if handler is None:
            result.status = StepStatus.FAILED
            result.error = f"no handler registered for step type '{step.type}'"
            result.finished_at = datetime.now(timezone.utc).isoformat()
            return

        for attempt in range(1, step.retry_policy.max_attempts + 1):
            result.attempt = attempt
            try:
                output = await asyncio.wait_for(
                    handler(step, run, definition),
                    timeout=step.timeout_seconds,
                )
                result.output = output
                result.status = StepStatus.SUCCEEDED
                result.finished_at = datetime.now(timezone.utc).isoformat()
                if result.started_at:
                    start = datetime.fromisoformat(result.started_at)
                    end = datetime.fromisoformat(result.finished_at)
                    result.duration_seconds = (end - start).total_seconds()
                run.context[f"step_{step.id}_output"] = output
                return
            except asyncio.TimeoutError:
                result.status = StepStatus.TIMED_OUT
                result.error = f"timed out after {step.timeout_seconds}s"
            except Exception as exc:
                result.status = StepStatus.FAILED
                result.error = str(exc)
                logger.warning(
                    "step %s attempt %d/%d failed: %s",
                    step.id, attempt, step.retry_policy.max_attempts, exc,
                )

            if attempt < step.retry_policy.max_attempts:
                backoff = min(
                    step.retry_policy.backoff_seconds
                    * (step.retry_policy.backoff_multiplier ** (attempt - 1)),
                    step.retry_policy.max_backoff_seconds,
                )
                result.status = StepStatus.RETRYING
                await asyncio.sleep(backoff)

        result.finished_at = datetime.now(timezone.utc).isoformat()

    async def _execute_parallel_step(
        self,
        run: WorkflowRun,
        definition: WorkflowDefinition,
        step,
    ) -> None:
        result = run.step_results[step.id]
        result.status = StepStatus.RUNNING
        result.started_at = datetime.now(timezone.utc).isoformat()

        handler = self._handlers.get(step.type)
        if handler is None:
            result.status = StepStatus.FAILED
            result.error = f"no handler registered for step type '{step.type}'"
            result.finished_at = datetime.now(timezone.utc).isoformat()
            return

        try:
            output = await asyncio.wait_for(
                handler(step, run, definition),
                timeout=step.timeout_seconds,
            )
            result.output = output
            result.status = StepStatus.SUCCEEDED
            run.context[f"step_{step.id}_output"] = output
        except asyncio.TimeoutError:
            result.status = StepStatus.TIMED_OUT
            result.error = f"timed out after {step.timeout_seconds}s"
        except Exception as exc:
            result.status = StepStatus.FAILED
            result.error = str(exc)

        result.finished_at = datetime.now(timezone.utc).isoformat()
        if result.started_at:
            start = datetime.fromisoformat(result.started_at)
            end = datetime.fromisoformat(result.finished_at)
            result.duration_seconds = (end - start).total_seconds()
