"""
Integration Engine — Orchestrates multi-step integration pipelines.
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional
from datetime import datetime, timezone

from ..sdk import BaseConnector, ConnectorConfig, ConnectorStatus
from ..transformation import TransformationResult

logger = logging.getLogger(__name__)


class IntegrationState(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


@dataclass
class PipelineStep:
    """A single step in an integration pipeline."""

    name: str
    connector: str
    operation: str
    config: dict[str, Any] = field(default_factory=dict)
    depends_on: list[str] = field(default_factory=list)
    condition: Optional[str] = None
    timeout_seconds: float = 300.0
    retry_count: int = 0
    max_retries: int = 3
    on_failure: str = "abort"  # abort, skip, continue
    transform_input: Optional[str] = None
    transform_output: Optional[str] = None


@dataclass
class PipelineResult:
    """Result of executing a pipeline step."""

    step_name: str
    success: bool
    state: IntegrationState
    started_at: str = ""
    completed_at: str = ""
    duration_ms: float = 0.0
    input_data: Any = None
    output_data: Any = None
    error_message: str = ""
    error_type: str = ""
    retry_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class PipelineExecution:
    """Result of executing an entire pipeline."""

    execution_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    pipeline_name: str = ""
    state: IntegrationState = IntegrationState.PENDING
    started_at: str = ""
    completed_at: str = ""
    duration_ms: float = 0.0
    steps: list[PipelineResult] = field(default_factory=list)
    final_output: Any = None
    error_message: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


class IntegrationPipeline:
    """
    A multi-step integration pipeline.

    Steps are executed sequentially or based on dependency graph.
    Each step uses a connector to perform an operation.
    """

    def __init__(
        self,
        name: str,
        steps: list[PipelineStep],
        description: str = "",
        tags: list[str] | None = None,
    ):
        self.name = name
        self.steps = steps
        self.description = description
        self.tags = tags or []
        self._step_map = {s.name: s for s in steps}
        self._results: dict[str, PipelineResult] = {}

    def validate(self) -> list[str]:
        """Validate pipeline configuration. Returns list of errors."""
        errors = []
        step_names = set()

        for step in self.steps:
            if step.name in step_names:
                errors.append(f"Duplicate step name: {step.name}")
            step_names.add(step.name)

            for dep in step.depends_on:
                if dep not in self._step_map:
                    errors.append(f"Step '{step.name}' depends on unknown step '{dep}'")

        # Check for circular dependencies
        visited = set()
        rec_stack = set()

        def has_cycle(name: str) -> bool:
            visited.add(name)
            rec_stack.add(name)
            step = self._step_map.get(name)
            if step:
                for dep in step.depends_on:
                    if dep not in visited:
                        if has_cycle(dep):
                            return True
                    elif dep in rec_stack:
                        return True
            rec_stack.discard(name)
            return False

        for step in self.steps:
            if step.name not in visited:
                if has_cycle(step.name):
                    errors.append(f"Circular dependency detected involving step '{step.name}'")
                    break

        return errors

    def get_execution_order(self) -> list[list[PipelineStep]]:
        """
        Return steps grouped by execution level (topological sort).
        Steps in the same level can be executed in parallel.
        """
        levels: list[list[PipelineStep]] = []
        completed: set[str] = set()
        remaining = list(self.steps)

        while remaining:
            level = []
            next_remaining = []
            for step in remaining:
                if all(dep in completed for dep in step.depends_on):
                    level.append(step)
                else:
                    next_remaining.append(step)

            if not level:
                # Circular dependency or missing dependency
                break

            levels.append(level)
            for step in level:
                completed.add(step.name)
            remaining = next_remaining

        return levels

    async def execute(
        self,
        connectors: dict[str, BaseConnector],
        initial_input: Any = None,
        context: dict[str, Any] | None = None,
    ) -> PipelineExecution:
        """Execute the pipeline."""
        execution = PipelineExecution(
            pipeline_name=self.name,
            state=IntegrationState.RUNNING,
            started_at=datetime.now(timezone.utc).isoformat(),
            metadata=context or {},
        )

        errors = self.validate()
        if errors:
            execution.state = IntegrationState.FAILED
            execution.error_message = "; ".join(errors)
            execution.completed_at = datetime.now(timezone.utc).isoformat()
            return execution

        current_data = initial_input
        levels = self.get_execution_order()

        for level in levels:
            level_results = await asyncio.gather(
                *[
                    self._execute_step(step, connectors, current_data, execution)
                    for step in level
                ],
                return_exceptions=True,
            )

            for result in level_results:
                if isinstance(result, Exception):
                    step_result = PipelineResult(
                        step_name="unknown",
                        success=False,
                        state=IntegrationState.FAILED,
                        error_message=str(result),
                        error_type=type(result).__name__,
                    )
                    execution.steps.append(step_result)
                else:
                    execution.steps.append(result)
                    self._results[result.step_name] = result
                    if result.success and result.output_data is not None:
                        current_data = result.output_data

        # Determine final state
        failed_steps = [s for s in execution.steps if not s.success]
        if failed_steps:
            execution.state = IntegrationState.FAILED
            execution.error_message = f"Failed steps: {', '.join(s.step_name for s in failed_steps)}"
        else:
            execution.state = IntegrationState.COMPLETED

        execution.final_output = current_data
        execution.completed_at = datetime.now(timezone.utc).isoformat()
        if execution.started_at:
            start = datetime.fromisoformat(execution.started_at)
            end = datetime.fromisoformat(execution.completed_at)
            execution.duration_ms = (end - start).total_seconds() * 1000

        return execution

    async def _execute_step(
        self,
        step: PipelineStep,
        connectors: dict[str, BaseConnector],
        input_data: Any,
        execution: PipelineExecution,
    ) -> PipelineResult:
        """Execute a single pipeline step."""
        result = PipelineResult(
            step_name=step.name,
            state=IntegrationState.RUNNING,
            started_at=datetime.now(timezone.utc).isoformat(),
            input_data=input_data,
        )

        connector = connectors.get(step.connector)
        if not connector:
            result.success = False
            result.state = IntegrationState.FAILED
            result.error_message = f"Connector '{step.connector}' not found"
            result.error_type = "ConnectorNotFound"
            result.completed_at = datetime.now(timezone.utc).isoformat()
            return result

        try:
            # Apply input transformation if specified
            step_input = input_data
            if step.transform_input:
                from ..transformation import SchemaMapper
                mapper = SchemaMapper(step.transform_input)
                transform_result = mapper.transform(input_data)
                if transform_result.success:
                    step_input = transform_result.data

            # Execute the connector operation
            method = getattr(connector, step.operation, None)
            if not method:
                raise AttributeError(f"Connector has no operation '{step.operation}'")

            output = method(**step.config) if step.config else method()

            # Apply output transformation if specified
            if step.transform_output:
                from ..transformation import SchemaMapper
                mapper = SchemaMapper(step.transform_output)
                transform_result = mapper.transform(output)
                if transform_result.success:
                    output = transform_result.data

            result.success = True
            result.state = IntegrationState.COMPLETED
            result.output_data = output

        except Exception as e:
            result.success = False
            result.state = IntegrationState.FAILED
            result.error_message = str(e)
            result.error_type = type(e).__name__

            if step.on_failure == "abort":
                raise

        result.completed_at = datetime.now(timezone.utc).isoformat()
        if result.started_at:
            start = datetime.fromisoformat(result.started_at)
            end = datetime.fromisoformat(result.completed_at)
            result.duration_ms = (end - start).total_seconds() * 1000

        return result


class IntegrationOrchestrator:
    """
    Orchestrates multiple integration pipelines.

    Provides:
    - Pipeline registration and execution
    - Scheduled execution
    - Event-driven triggers
    - Execution history and monitoring
    """

    def __init__(self):
        self._pipelines: dict[str, IntegrationPipeline] = {}
        self._connectors: dict[str, BaseConnector] = {}
        self._executions: dict[str, PipelineExecution] = {}
        self._schedules: dict[str, dict[str, Any]] = {}
        self._event_handlers: dict[str, list[Callable]] = {}

    def register_pipeline(self, pipeline: IntegrationPipeline) -> None:
        """Register a pipeline."""
        errors = pipeline.validate()
        if errors:
            raise ValueError(f"Pipeline validation failed: {'; '.join(errors)}")
        self._pipelines[pipeline.name] = pipeline
        logger.info("Registered pipeline: %s", pipeline.name)

    def unregister_pipeline(self, name: str) -> None:
        """Unregister a pipeline."""
        self._pipelines.pop(name, None)

    def register_connector(self, name: str, connector: BaseConnector) -> None:
        """Register a connector for use in pipelines."""
        self._connectors[name] = connector

    def get_connector(self, name: str) -> Optional[BaseConnector]:
        """Get a registered connector."""
        return self._connectors.get(name)

    async def execute_pipeline(
        self,
        name: str,
        initial_input: Any = None,
        context: dict[str, Any] | None = None,
    ) -> PipelineExecution:
        """Execute a registered pipeline by name."""
        pipeline = self._pipelines.get(name)
        if not pipeline:
            raise KeyError(f"Pipeline '{name}' not found")

        execution = await pipeline.execute(self._connectors, initial_input, context)
        self._executions[execution.execution_id] = execution

        # Emit event
        await self._emit_event("pipeline_completed", execution)

        return execution

    async def execute_pipeline_sync(
        self,
        name: str,
        initial_input: Any = None,
        context: dict[str, Any] | None = None,
    ) -> PipelineExecution:
        """Synchronous wrapper for execute_pipeline."""
        return await self.execute_pipeline(name, initial_input, context)

    def schedule_pipeline(
        self,
        name: str,
        cron_expression: str,
        initial_input: Any = None,
        context: dict[str, Any] | None = None,
    ) -> str:
        """Schedule a pipeline for recurring execution."""
        schedule_id = str(uuid.uuid4())[:12]
        self._schedules[schedule_id] = {
            "pipeline_name": name,
            "cron_expression": cron_expression,
            "initial_input": initial_input,
            "context": context or {},
            "enabled": True,
            "last_run": None,
            "next_run": None,
        }
        return schedule_id

    def unschedule_pipeline(self, schedule_id: str) -> None:
        """Remove a scheduled pipeline."""
        self._schedules.pop(schedule_id, None)

    def on_event(self, event_type: str, handler: Callable) -> None:
        """Register an event handler."""
        self._event_handlers.setdefault(event_type, []).append(handler)

    async def _emit_event(self, event_type: str, data: Any) -> None:
        """Emit an event to registered handlers."""
        handlers = self._event_handlers.get(event_type, [])
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(data)
                else:
                    handler(data)
            except Exception as e:
                logger.error("Event handler error: %s", e)

    def get_execution(self, execution_id: str) -> Optional[PipelineExecution]:
        """Get execution result by ID."""
        return self._executions.get(execution_id)

    def list_executions(
        self,
        pipeline_name: str | None = None,
        state: IntegrationState | None = None,
    ) -> list[PipelineExecution]:
        """List executions, optionally filtered."""
        results = list(self._executions.values())
        if pipeline_name:
            results = [e for e in results if e.pipeline_name == pipeline_name]
        if state:
            results = [e for e in results if e.state == state]
        return results

    def get_pipeline(self, name: str) -> Optional[IntegrationPipeline]:
        """Get a registered pipeline."""
        return self._pipelines.get(name)

    def list_pipelines(self) -> list[str]:
        """List all registered pipeline names."""
        return list(self._pipelines.keys())

    def health_check(self) -> dict[str, Any]:
        """Health check for the orchestrator."""
        connector_health = {}
        for name, connector in self._connectors.items():
            try:
                connector_health[name] = connector.health_check()
            except Exception as e:
                connector_health[name] = {"name": name, "status": "error", "error": str(e)}

        return {
            "orchestrator": "healthy",
            "pipelines": len(self._pipelines),
            "connectors": len(self._connectors),
            "executions": len(self._executions),
            "schedules": len(self._schedules),
            "connector_health": connector_health,
        }


class IntegrationScheduler:
    """
    Schedules and runs integration pipelines on a cron-like schedule.
    """

    def __init__(self, orchestrator: IntegrationOrchestrator):
        self.orchestrator = orchestrator
        self._running = False
        self._task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """Start the scheduler loop."""
        self._running = True
        self._task = asyncio.create_task(self._run_loop())

    async def stop(self) -> None:
        """Stop the scheduler loop."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _run_loop(self) -> None:
        """Main scheduler loop."""
        while self._running:
            try:
                now = datetime.now(timezone.utc)
                for schedule_id, schedule in list(self.orchestrator._schedules.items()):
                    if not schedule.get("enabled"):
                        continue
                    # Simple cron check — in production use a proper cron parser
                    # This is a placeholder for the scheduling logic
                    pass
                await asyncio.sleep(60)  # Check every minute
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Scheduler error: %s", e)
                await asyncio.sleep(60)
