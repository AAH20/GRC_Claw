"""
Workflow engine for GRC_Claw.

Core orchestration engine that manages workflow lifecycle, step scheduling,
dependency resolution, parallel execution, and state transitions.
"""

from __future__ import annotations

import asyncio
import copy
import logging
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from .schema import (
    StepResult,
    StepStatus,
    StepType,
    TriggerType,
    WorkflowDefinition,
    WorkflowRun,
    WorkflowStatus,
)

logger = logging.getLogger(__name__)


class WorkflowEngineError(Exception):
    """Base exception for workflow engine errors."""
    pass


class WorkflowNotFoundError(WorkflowEngineError):
    """Raised when a workflow definition is not found."""
    pass


class WorkflowValidationError(WorkflowEngineError):
    """Raised when a workflow definition fails validation."""
    pass


class WorkflowVersionError(WorkflowEngineError):
    """Raised when a workflow version conflict occurs."""
    pass


class WorkflowEngine:
    """Core workflow orchestration engine."""

    def __init__(self):
        self._workflows: dict[str, WorkflowDefinition] = {}
        self._runs: dict[str, WorkflowRun] = {}
        self._handlers: dict[str, Callable] = {}
        self._running: set[str] = set()
        self._lock = asyncio.Lock()
        self._versions: dict[str, list[WorkflowDefinition]] = {}
        self._hooks: dict[str, list[Callable]] = {
            "on_register": [],
            "on_update": [],
            "on_delete": [],
            "on_activate": [],
            "on_pause": [],
            "on_deprecate": [],
        }
        self._run_history: dict[str, list[WorkflowRun]] = {}

    # ------------------------------------------------------------------
    # Definition CRUD
    # ------------------------------------------------------------------

    def register_workflow(self, definition: WorkflowDefinition) -> None:
        errors = definition.validate()
        if errors:
            raise WorkflowValidationError(
                f"invalid workflow definition: {'; '.join(errors)}"
            )
        self._workflows[definition.id] = definition
        self._emit("on_register", definition)
        logger.info("registered workflow %s (%s)", definition.name, definition.id)

    def unregister_workflow(self, workflow_id: str) -> bool:
        if workflow_id in self._workflows:
            wf = self._workflows.pop(workflow_id)
            self._versions.pop(workflow_id, None)
            self._emit("on_delete", wf)
            return True
        return False

    def get_workflow(self, workflow_id: str) -> WorkflowDefinition | None:
        return self._workflows.get(workflow_id)

    def list_workflows(
        self,
        status: WorkflowStatus | None = None,
        tag: str | None = None,
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

    # ------------------------------------------------------------------
    # Lifecycle management
    # ------------------------------------------------------------------

    def activate(self, workflow_id: str) -> WorkflowDefinition:
        """Activate a workflow so it can be executed."""
        wf = self._workflows.get(workflow_id)
        if wf is None:
            raise WorkflowNotFoundError(f"workflow '{workflow_id}' not found")
        wf.status = WorkflowStatus.ACTIVE
        wf.updated_at = datetime.now(UTC).isoformat()
        self._emit("on_activate", wf)
        logger.info("activated workflow %s", workflow_id)
        return wf

    def pause(self, workflow_id: str) -> WorkflowDefinition:
        """Pause a workflow to prevent new runs."""
        wf = self._workflows.get(workflow_id)
        if wf is None:
            raise WorkflowNotFoundError(f"workflow '{workflow_id}' not found")
        wf.status = WorkflowStatus.PAUSED
        wf.updated_at = datetime.now(UTC).isoformat()
        self._emit("on_pause", wf)
        logger.info("paused workflow %s", workflow_id)
        return wf

    def deprecate(self, workflow_id: str) -> WorkflowDefinition:
        """Deprecate a workflow."""
        wf = self._workflows.get(workflow_id)
        if wf is None:
            raise WorkflowNotFoundError(f"workflow '{workflow_id}' not found")
        wf.status = WorkflowStatus.DEPRECATED
        wf.updated_at = datetime.now(UTC).isoformat()
        self._emit("on_deprecate", wf)
        logger.info("deprecated workflow %s", workflow_id)
        return wf

    # ------------------------------------------------------------------
    # Versioning
    # ------------------------------------------------------------------

    def list_versions(self, workflow_id: str) -> list[WorkflowDefinition]:
        """List all historical versions of a workflow."""
        return list(self._versions.get(workflow_id, []))

    def rollback(self, workflow_id: str, version: str) -> WorkflowDefinition:
        """Roll back to a previous version."""
        versions = self._versions.get(workflow_id, [])
        target = None
        for v in versions:
            if v.version == version:
                target = v
                break
        if target is None:
            raise WorkflowNotFoundError(
                f"version '{version}' not found for workflow '{workflow_id}'"
            )
        restored = copy.deepcopy(target)
        restored.status = WorkflowStatus.DRAFT
        restored.updated_at = datetime.now(UTC).isoformat()
        self._workflows[workflow_id] = restored
        logger.info("rolled back workflow %s to version %s", workflow_id, version)
        return restored

    # ------------------------------------------------------------------
    # Run management
    # ------------------------------------------------------------------

    async def start_run(
        self,
        workflow_id: str,
        parameters: dict[str, Any] | None = None,
        triggered_by: str = "",
        parent_run_id: str | None = None,
    ) -> WorkflowRun:
        definition = self._workflows.get(workflow_id)
        if definition is None:
            raise WorkflowNotFoundError(f"workflow '{workflow_id}' not found")
        if definition.status != WorkflowStatus.ACTIVE:
            raise WorkflowEngineError(
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
            started_at=datetime.now(UTC).isoformat(),
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
        run.finished_at = datetime.now(UTC).isoformat()
        async with self._lock:
            self._running.discard(run_id)
        logger.info("cancelled run %s", run_id)
        return True

    async def get_run(self, run_id: str) -> WorkflowRun | None:
        return self._runs.get(run_id)

    async def list_runs(
        self,
        workflow_id: str | None = None,
        status: StepStatus | None = None,
    ) -> list[WorkflowRun]:
        results = list(self._runs.values())
        if workflow_id is not None:
            results = [r for r in results if r.workflow_id == workflow_id]
        if status is not None:
            results = [r for r in results if r.status == status]
        return results

    def record_run(self, run: WorkflowRun) -> None:
        """Record a completed run in history."""
        self._run_history.setdefault(run.workflow_id, []).append(run)

    def get_run_history(
        self,
        workflow_id: str,
        limit: int = 100,
    ) -> list[WorkflowRun]:
        """Get recent run history for a workflow."""
        runs = self._run_history.get(workflow_id, [])
        return runs[-limit:]

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

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
            run.finished_at = datetime.now(UTC).isoformat()
            if run.started_at:
                start = datetime.fromisoformat(run.started_at)
                end = datetime.fromisoformat(run.finished_at)
                run.duration_seconds = (end - start).total_seconds()
            async with self._lock:
                self._running.discard(run_id)
            self.record_run(run)

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
        result.started_at = datetime.now(UTC).isoformat()

        handler = self._handlers.get(step.type)
        if handler is None:
            result.status = StepStatus.FAILED
            result.error = f"no handler registered for step type '{step.type}'"
            result.finished_at = datetime.now(UTC).isoformat()
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
                result.finished_at = datetime.now(UTC).isoformat()
                if result.started_at:
                    start = datetime.fromisoformat(result.started_at)
                    end = datetime.fromisoformat(result.finished_at)
                    result.duration_seconds = (end - start).total_seconds()
                run.context[f"step_{step.id}_output"] = output
                return
            except TimeoutError:
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

        result.finished_at = datetime.now(UTC).isoformat()

    async def _execute_parallel_step(
        self,
        run: WorkflowRun,
        definition: WorkflowDefinition,
        step,
    ) -> None:
        result = run.step_results[step.id]
        result.status = StepStatus.RUNNING
        result.started_at = datetime.now(UTC).isoformat()

        handler = self._handlers.get(step.type)
        if handler is None:
            result.status = StepStatus.FAILED
            result.error = f"no handler registered for step type '{step.type}'"
            result.finished_at = datetime.now(UTC).isoformat()
            return

        try:
            output = await asyncio.wait_for(
                handler(step, run, definition),
                timeout=step.timeout_seconds,
            )
            result.output = output
            result.status = StepStatus.SUCCEEDED
            run.context[f"step_{step.id}_output"] = output
        except TimeoutError:
            result.status = StepStatus.TIMED_OUT
            result.error = f"timed out after {step.timeout_seconds}s"
        except Exception as exc:
            result.status = StepStatus.FAILED
            result.error = str(exc)

        result.finished_at = datetime.now(UTC).isoformat()
        if result.started_at:
            start = datetime.fromisoformat(result.started_at)
            end = datetime.fromisoformat(result.finished_at)
            result.duration_seconds = (end - start).total_seconds()

    # ------------------------------------------------------------------
    # Event hooks
    # ------------------------------------------------------------------

    def add_hook(self, event: str, callback: Callable) -> None:
        """Register a lifecycle event hook."""
        if event not in self._hooks:
            raise ValueError(f"unknown hook event '{event}'")
        self._hooks[event].append(callback)

    def remove_hook(self, event: str, callback: Callable) -> bool:
        """Remove a previously registered hook."""
        if event in self._hooks and callback in self._hooks[event]:
            self._hooks[event].remove(callback)
            return True
        return False

    def _emit(self, event: str, *args: Any) -> None:
        """Fire all callbacks for an event."""
        for callback in self._hooks.get(event, []):
            try:
                callback(*args)
            except Exception:
                logger.exception("hook error for event '%s'", event)

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def check_readiness(self, workflow_id: str) -> tuple[bool, list[str]]:
        """Check if a workflow is ready for execution."""
        issues: list[str] = []
        try:
            wf = self._workflows.get(workflow_id)
        except Exception as exc:
            return False, [str(exc)]
        if wf is None:
            return False, [f"workflow '{workflow_id}' not found"]
        if wf.status != WorkflowStatus.ACTIVE:
            issues.append(f"workflow status is '{wf.status.value}', not 'active'")
        if not wf.steps:
            issues.append("workflow has no steps")
        step_ids = {s.id for s in wf.steps}
        for step in wf.steps:
            for nxt in step.next_steps:
                if nxt not in step_ids:
                    issues.append(f"step '{step.id}' has unknown next_step '{nxt}'")
        entry_points = [s for s in wf.steps if not s.depends_on]
        if wf.steps and not entry_points:
            issues.append("workflow has no entry-point steps")
        return len(issues) == 0, issues

    # ------------------------------------------------------------------
    # Statistics
    # ------------------------------------------------------------------

    def get_stats(self) -> dict[str, Any]:
        """Get engine statistics."""
        total = len(self._workflows)
        by_status: dict[str, int] = {}
        for wf in self._workflows.values():
            key = wf.status.value
            by_status[key] = by_status.get(key, 0) + 1
        total_runs = sum(len(runs) for runs in self._run_history.values())
        return {
            "total_definitions": total,
            "by_status": by_status,
            "total_versions_archived": sum(len(v) for v in self._versions.values()),
            "total_runs_recorded": total_runs,
            "active_runs": len(self._running),
            "registered_handlers": list(self._handlers.keys()),
            "registered_hooks": {e: len(c) for e, c in self._hooks.items()},
        }
