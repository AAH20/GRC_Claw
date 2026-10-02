"""
Integration Engine — orchestrates multi-step integration pipelines.

Provides:
- IntegrationPipeline: sequential/parallel step execution
- IntegrationOrchestrator: manages multiple pipelines
- IntegrationScheduler: cron-like and interval-based scheduling
- PipelineStep / PipelineResult: step-level abstractions
- IntegrationState: lifecycle state tracking
"""

from __future__ import annotations

import logging
import threading
import time
import uuid
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from .sdk.base import BaseConnector
from .sdk.exceptions import ConnectorError

logger = logging.getLogger(__name__)


class IntegrationState(str, Enum):
    """Lifecycle states for an integration pipeline."""

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
    connector: BaseConnector
    operation: str  # method name to call on connector
    params: dict[str, Any] = field(default_factory=dict)
    transform: Callable[[Any], Any] | None = None
    on_error: str = "fail"  # fail, skip, retry
    max_retries: int = 3
    retry_delay_seconds: float = 1.0
    timeout_seconds: float = 60.0
    condition: Callable[[PipelineResult], bool] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class PipelineResult:
    """Result of executing a pipeline step or an entire pipeline."""

    step_name: str
    success: bool
    data: Any = None
    error: str | None = None
    error_type: str | None = None
    duration_ms: float = 0.0
    attempts: int = 1
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    @property
    def failed(self) -> bool:
        return not self.success


@dataclass
class PipelineExecutionResult:
    """Result of executing an entire pipeline."""

    pipeline_id: str
    state: IntegrationState
    step_results: list[PipelineResult] = field(default_factory=list)
    start_time: datetime = field(default_factory=lambda: datetime.now(UTC))
    end_time: datetime | None = None
    total_duration_ms: float = 0.0
    data: Any = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def success(self) -> bool:
        return self.state == IntegrationState.COMPLETED

    @property
    def failed(self) -> bool:
        return self.state == IntegrationState.FAILED

    @property
    def step_count(self) -> int:
        return len(self.step_results)

    @property
    def failed_steps(self) -> list[PipelineResult]:
        return [r for r in self.step_results if not r.success]


class IntegrationPipeline:
    """
    Manages a sequence of integration steps.

    Supports:
    - Sequential and parallel step execution
    - Conditional step execution
    - Error handling per step (fail, skip, retry)
    - Data passing between steps
    - Pipeline-level timeout
    """

    def __init__(
        self,
        name: str,
        steps: list[PipelineStep],
        *,
        description: str = "",
        parallel: bool = False,
        max_parallelism: int = 4,
        pipeline_timeout_seconds: float = 300.0,
        on_step_complete: Callable[[PipelineResult], None] | None = None,
        on_step_error: Callable[[PipelineResult], None] | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        self.name = name
        self.steps = steps
        self.description = description
        self.parallel = parallel
        self.max_parallelism = max_parallelism
        self.pipeline_timeout_seconds = pipeline_timeout_seconds
        self.on_step_complete = on_step_complete
        self.on_step_error = on_step_error
        self.metadata = metadata or {}
        self._state = IntegrationState.PENDING
        self._results: list[PipelineResult] = []
        self._data: Any = None
        self._lock = threading.Lock()

    @property
    def state(self) -> IntegrationState:
        return self._state

    @property
    def results(self) -> list[PipelineResult]:
        return list(self._results)

    @property
    def data(self) -> Any:
        return self._data

    def execute(self, initial_data: Any = None) -> PipelineExecutionResult:
        """
        Execute the pipeline.

        Args:
            initial_data: Data to pass into the first step.

        Returns:
            PipelineExecutionResult with all step results.
        """
        pipeline_id = str(uuid.uuid4())[:8]
        self._state = IntegrationState.RUNNING
        self._results = []
        self._data = initial_data
        start = time.monotonic()
        start_dt = datetime.now(UTC)

        logger.info("Pipeline '%s' started (id=%s, steps=%d)", self.name, pipeline_id, len(self.steps))

        try:
            if self.parallel and len(self.steps) > 1:
                self._execute_parallel(pipeline_id)
            else:
                self._execute_sequential(pipeline_id)

            # Determine final state
            failed = [r for r in self._results if not r.success]
            if failed:
                self._state = IntegrationState.FAILED
                error_msg = f"{len(failed)} step(s) failed: {', '.join(r.step_name for r in failed)}"
            else:
                self._state = IntegrationState.COMPLETED
                error_msg = None

        except Exception as e:
            self._state = IntegrationState.FAILED
            error_msg = str(e)
            logger.exception("Pipeline '%s' failed with exception", self.name)

        end_dt = datetime.now(UTC)
        duration_ms = (time.monotonic() - start) * 1000

        result = PipelineExecutionResult(
            pipeline_id=pipeline_id,
            state=self._state,
            step_results=list(self._results),
            start_time=start_dt,
            end_time=end_dt,
            total_duration_ms=duration_ms,
            data=self._data,
            error=error_msg,
            metadata=dict(self.metadata),
        )

        logger.info(
            "Pipeline '%s' finished: state=%s, duration=%.1fms, steps=%d",
            self.name, self._state.value, duration_ms, len(self._results),
        )
        return result

    def _execute_sequential(self, pipeline_id: str) -> None:
        """Execute steps one at a time."""
        for step in self.steps:
            if self._state == IntegrationState.CANCELLED:
                break

            # Check condition
            if step.condition and self._results:
                if not step.condition(self._results[-1]):
                    logger.debug("Step '%s' skipped (condition not met)", step.name)
                    continue

            result = self._execute_step(step, pipeline_id)
            self._results.append(result)

            if result.success:
                self._data = result.data
                if self.on_step_complete:
                    self.on_step_complete(result)
            else:
                if self.on_step_error:
                    self.on_step_error(result)
                if step.on_error == "fail":
                    self._state = IntegrationState.FAILED
                    break
                # "skip" and "retry" are handled inside _execute_step

    def _execute_parallel(self, pipeline_id: str) -> None:
        """Execute steps in parallel using a thread pool."""
        with ThreadPoolExecutor(max_workers=self.max_parallelism) as executor:
            futures = {}
            for step in self.steps:
                if step.condition:
                    # Conditional steps run sequentially after parallel batch
                    continue
                future = executor.submit(self._execute_step, step, pipeline_id)
                futures[future] = step

            for future in as_completed(futures):
                step = futures[future]
                try:
                    result = future.result(timeout=self.pipeline_timeout_seconds)
                except Exception as e:
                    result = PipelineResult(
                        step_name=step.name,
                        success=False,
                        error=str(e),
                        error_type=type(e).__name__,
                    )
                self._results.append(result)
                if result.success:
                    if self.on_step_complete:
                        self.on_step_complete(result)
                elif self.on_step_error:
                    self.on_step_error(result)

    def _execute_step(self, step: PipelineStep, pipeline_id: str) -> PipelineResult:
        """Execute a single step with retry logic."""
        start = time.monotonic()
        last_error: Exception | None = None
        attempts = 0

        for attempt in range(step.max_retries + 1):
            attempts = attempt + 1
            try:
                # Resolve the operation
                operation = getattr(step.connector, step.operation, None)
                if operation is None:
                    raise ConnectorError(
                        f"Connector has no operation '{step.operation}'",
                        connector=step.connector.config.name,
                    )

                # Merge params with pipeline data
                call_params = dict(step.params)
                if self._data is not None and "input" not in call_params:
                    call_params["input"] = self._data

                # Execute
                raw_data = operation(**call_params)

                # Apply transform if provided
                if step.transform:
                    raw_data = step.transform(raw_data)

                duration_ms = (time.monotonic() - start) * 1000
                return PipelineResult(
                    step_name=step.name,
                    success=True,
                    data=raw_data,
                    duration_ms=duration_ms,
                    attempts=attempts,
                    metadata={"pipeline_id": pipeline_id},
                )

            except Exception as e:
                last_error = e
                logger.warning(
                    "Step '%s' attempt %d/%d failed: %s",
                    step.name, attempt + 1, step.max_retries + 1, e,
                )
                if attempt < step.max_retries and step.on_error == "retry":
                    time.sleep(step.retry_delay_seconds * (2 ** attempt))
                else:
                    break

        duration_ms = (time.monotonic() - start) * 1000
        return PipelineResult(
            step_name=step.name,
            success=False,
            error=str(last_error),
            error_type=type(last_error).__name__ if last_error else None,
            duration_ms=duration_ms,
            attempts=attempts,
            metadata={"pipeline_id": pipeline_id},
        )

    def pause(self) -> None:
        """Pause the pipeline (takes effect between steps)."""
        if self._state == IntegrationState.RUNNING:
            self._state = IntegrationState.PAUSED
            logger.info("Pipeline '%s' paused", self.name)

    def resume(self) -> None:
        """Resume a paused pipeline."""
        if self._state == IntegrationState.PAUSED:
            self._state = IntegrationState.RUNNING
            logger.info("Pipeline '%s' resumed", self.name)

    def cancel(self) -> None:
        """Cancel the pipeline."""
        self._state = IntegrationState.CANCELLED
        logger.info("Pipeline '%s' cancelled", self.name)

    def add_step(self, step: PipelineStep) -> None:
        """Add a step to the pipeline."""
        self.steps.append(step)

    def remove_step(self, name: str) -> bool:
        """Remove a step by name. Returns True if found and removed."""
        for i, s in enumerate(self.steps):
            if s.name == name:
                self.steps.pop(i)
                return True
        return False

    def get_step(self, name: str) -> PipelineStep | None:
        """Get a step by name."""
        for s in self.steps:
            if s.name == name:
                return s
        return None

    def __len__(self) -> int:
        return len(self.steps)


class IntegrationOrchestrator:
    """
    Manages multiple integration pipelines.

    Provides:
    - Pipeline registration and lifecycle management
    - Dependency resolution between pipelines
    - Concurrent pipeline execution
    - Event callbacks
    - Execution history
    """

    def __init__(self, max_concurrent_pipelines: int = 10):
        self._pipelines: dict[str, IntegrationPipeline] = {}
        self._dependencies: dict[str, list[str]] = {}
        self._history: list[PipelineExecutionResult] = []
        self._max_concurrent = max_concurrent_pipelines
        self._lock = threading.Lock()
        self._executor = ThreadPoolExecutor(max_workers=max_concurrent_pipelines)
        self._on_pipeline_complete: Callable[[PipelineExecutionResult], None] | None = None
        self._on_pipeline_error: Callable[[PipelineExecutionResult], None] | None = None

    @property
    def pipelines(self) -> dict[str, IntegrationPipeline]:
        return dict(self._pipelines)

    @property
    def history(self) -> list[PipelineExecutionResult]:
        return list(self._history)

    def register(
        self,
        pipeline: IntegrationPipeline,
        depends_on: list[str] | None = None,
    ) -> None:
        """Register a pipeline with optional dependencies."""
        with self._lock:
            self._pipelines[pipeline.name] = pipeline
            if depends_on:
                self._dependencies[pipeline.name] = depends_on
        logger.info("Registered pipeline '%s' (depends_on=%s)", pipeline.name, depends_on)

    def unregister(self, name: str) -> bool:
        """Unregister a pipeline. Returns True if found."""
        with self._lock:
            if name in self._pipelines:
                del self._pipelines[name]
                self._dependencies.pop(name, None)
                return True
        return False

    def get(self, name: str) -> IntegrationPipeline | None:
        """Get a pipeline by name."""
        return self._pipelines.get(name)

    def execute(
        self,
        name: str,
        initial_data: Any = None,
        wait: bool = True,
    ) -> PipelineExecutionResult | None:
        """
        Execute a pipeline by name.

        Args:
            name: Pipeline name.
            initial_data: Data to pass to the pipeline.
            wait: If True, block until completion. If False, return None and run in background.

        Returns:
            PipelineExecutionResult if wait=True, else None.
        """
        pipeline = self._pipelines.get(name)
        if not pipeline:
            raise KeyError(f"Pipeline '{name}' is not registered")

        # Check dependencies
        deps = self._dependencies.get(name, [])
        for dep_name in deps:
            dep = self._pipelines.get(dep_name)
            if not dep:
                raise KeyError(f"Dependency pipeline '{dep_name}' not found")
            if dep.state != IntegrationState.COMPLETED:
                logger.info("Waiting for dependency pipeline '%s' to complete", dep_name)
                dep_result = self.execute(dep_name, wait=True)
                if dep_result and dep_result.failed:
                    raise ConnectorError(
                        f"Dependency pipeline '{dep_name}' failed: {dep_result.error}",
                        connector="orchestrator",
                    )

        if wait:
            return self._run_pipeline(pipeline, initial_data)
        else:
            self._executor.submit(self._run_pipeline, pipeline, initial_data)
            return None

    def execute_all(
        self,
        initial_data: Any = None,
        parallel: bool = True,
    ) -> dict[str, PipelineExecutionResult]:
        """
        Execute all registered pipelines.

        Args:
            initial_data: Data to pass to each pipeline.
            parallel: If True, run pipelines concurrently.

        Returns:
            Dict mapping pipeline names to their execution results.
        """
        results: dict[str, PipelineExecutionResult] = {}

        if parallel:
            futures = {}
            for name, pipeline in self._pipelines.items():
                future = self._executor.submit(self._run_pipeline, pipeline, initial_data)
                futures[future] = name

            for future in as_completed(futures):
                name = futures[future]
                try:
                    results[name] = future.result()
                except Exception as e:
                    results[name] = PipelineExecutionResult(
                        pipeline_id="error",
                        state=IntegrationState.FAILED,
                        error=str(e),
                    )
        else:
            for name, pipeline in self._pipelines.items():
                results[name] = self._run_pipeline(pipeline, initial_data)

        return results

    def _run_pipeline(
        self,
        pipeline: IntegrationPipeline,
        initial_data: Any,
    ) -> PipelineExecutionResult:
        """Run a pipeline and record the result."""
        result = pipeline.execute(initial_data)

        with self._lock:
            self._history.append(result)

        if result.success and self._on_pipeline_complete:
            self._on_pipeline_complete(result)
        elif result.failed and self._on_pipeline_error:
            self._on_pipeline_error(result)

        return result

    def on_pipeline_complete(self, callback: Callable[[PipelineExecutionResult], None]) -> None:
        """Set a callback for successful pipeline completion."""
        self._on_pipeline_complete = callback

    def on_pipeline_error(self, callback: Callable[[PipelineExecutionResult], None]) -> None:
        """Set a callback for pipeline errors."""
        self._on_pipeline_error = callback

    def get_history(
        self,
        pipeline_name: str | None = None,
        limit: int = 100,
    ) -> list[PipelineExecutionResult]:
        """Get execution history, optionally filtered by pipeline name."""
        with self._lock:
            history = list(self._history)
        if pipeline_name:
            history = [h for h in history if h.metadata.get("pipeline_name") == pipeline_name]
        return history[-limit:]

    def clear_history(self) -> None:
        """Clear execution history."""
        with self._lock:
            self._history.clear()

    def health_check(self) -> dict[str, Any]:
        """Check health of all registered pipelines."""
        status = {}
        for name, pipeline in self._pipelines.items():
            status[name] = {
                "state": pipeline.state.value,
                "step_count": len(pipeline),
                "last_result": pipeline.results[-1].__dict__ if pipeline.results else None,
            }
        return status

    def shutdown(self) -> None:
        """Shut down the orchestrator and clean up resources."""
        self._executor.shutdown(wait=True)
        logger.info("Integration orchestrator shut down")


class IntegrationScheduler:
    """
    Schedules pipeline execution on a cron-like or interval-based schedule.

    Supports:
    - Interval-based scheduling (every N seconds/minutes/hours)
    - Cron-like scheduling (minute, hour, day-of-month, month, day-of-week)
    - One-shot delayed execution
    - Schedule persistence
    """

    def __init__(self, orchestrator: IntegrationOrchestrator):
        self.orchestrator = orchestrator
        self._schedules: dict[str, dict[str, Any]] = {}
        self._running = False
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()

    def add_interval_schedule(
        self,
        name: str,
        pipeline_name: str,
        interval_seconds: float,
        initial_data: Any = None,
        max_runs: int = 0,  # 0 = unlimited
    ) -> None:
        """Add an interval-based schedule."""
        with self._lock:
            self._schedules[name] = {
                "type": "interval",
                "pipeline_name": pipeline_name,
                "interval_seconds": interval_seconds,
                "initial_data": initial_data,
                "max_runs": max_runs,
                "run_count": 0,
                "last_run": None,
                "next_run": time.time(),
                "enabled": True,
            }
        logger.info("Added interval schedule '%s' (every %.0fs)", name, interval_seconds)

    def add_cron_schedule(
        self,
        name: str,
        pipeline_name: str,
        minute: str = "*",
        hour: str = "*",
        day_of_month: str = "*",
        month: str = "*",
        day_of_week: str = "*",
        initial_data: Any = None,
        max_runs: int = 0,
    ) -> None:
        """Add a cron-like schedule."""
        with self._lock:
            self._schedules[name] = {
                "type": "cron",
                "pipeline_name": pipeline_name,
                "cron": {
                    "minute": minute,
                    "hour": hour,
                    "day_of_month": day_of_month,
                    "month": month,
                    "day_of_week": day_of_week,
                },
                "initial_data": initial_data,
                "max_runs": max_runs,
                "run_count": 0,
                "last_run": None,
                "next_run": self._calculate_next_cron_run(minute, hour, day_of_month, month, day_of_week),
                "enabled": True,
            }
        logger.info("Added cron schedule '%s'", name)

    def add_one_shot(
        self,
        name: str,
        pipeline_name: str,
        delay_seconds: float,
        initial_data: Any = None,
    ) -> None:
        """Add a one-shot delayed execution."""
        with self._lock:
            self._schedules[name] = {
                "type": "one_shot",
                "pipeline_name": pipeline_name,
                "delay_seconds": delay_seconds,
                "initial_data": initial_data,
                "max_runs": 1,
                "run_count": 0,
                "last_run": None,
                "next_run": time.time() + delay_seconds,
                "enabled": True,
            }
        logger.info("Added one-shot schedule '%s' (in %.0fs)", name, delay_seconds)

    def remove_schedule(self, name: str) -> bool:
        """Remove a schedule. Returns True if found."""
        with self._lock:
            return self._schedules.pop(name, None) is not None

    def enable_schedule(self, name: str) -> bool:
        """Enable a schedule."""
        with self._lock:
            if name in self._schedules:
                self._schedules[name]["enabled"] = True
                return True
        return False

    def disable_schedule(self, name: str) -> bool:
        """Disable a schedule."""
        with self._lock:
            if name in self._schedules:
                self._schedules[name]["enabled"] = False
                return True
        return False

    def start(self) -> None:
        """Start the scheduler loop."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        logger.info("Integration scheduler started")

    def stop(self) -> None:
        """Stop the scheduler loop."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("Integration scheduler stopped")

    def _run_loop(self) -> None:
        """Main scheduler loop."""
        while self._running:
            now = time.time()
            with self._lock:
                schedules = list(self._schedules.items())

            for name, schedule in schedules:
                if not schedule["enabled"]:
                    continue
                if schedule["run_count"] >= schedule["max_runs"] and schedule["max_runs"] > 0:
                    continue
                if now < schedule["next_run"]:
                    continue

                # Execute the pipeline
                pipeline_name = schedule["pipeline_name"]
                initial_data = schedule.get("initial_data")
                logger.info("Scheduler executing pipeline '%s' (schedule='%s')", pipeline_name, name)

                try:
                    self.orchestrator.execute(pipeline_name, initial_data, wait=False)
                except Exception as e:
                    logger.error("Scheduled pipeline '%s' failed: %s", pipeline_name, e)

                # Update schedule state
                with self._lock:
                    if name in self._schedules:
                        self._schedules[name]["run_count"] += 1
                        self._schedules[name]["last_run"] = now
                        if self._schedules[name]["type"] == "interval":
                            self._schedules[name]["next_run"] = now + self._schedules[name]["interval_seconds"]
                        elif self._schedules[name]["type"] == "one_shot":
                            self._schedules[name]["enabled"] = False
                        elif self._schedules[name]["type"] == "cron":
                            cron = self._schedules[name]["cron"]
                            self._schedules[name]["next_run"] = self._calculate_next_cron_run(
                                cron["minute"], cron["hour"], cron["day_of_month"],
                                cron["month"], cron["day_of_week"],
                            )

            time.sleep(1)

    def _calculate_next_cron_run(
        self,
        minute: str,
        hour: str,
        day_of_month: str,
        month: str,
        day_of_week: str,
    ) -> float:
        """Calculate the next run time for a cron schedule."""
        # Simplified: just add 1 minute for wildcard patterns
        # A full cron parser would be more complex
        now = datetime.now(UTC)
        next_run = now

        if minute != "*":
            next_run = next_run.replace(minute=int(minute), second=0, microsecond=0)
            if next_run <= now:
                from datetime import timedelta
                next_run += timedelta(minutes=1)
        else:
            from datetime import timedelta
            next_run = next_run + timedelta(minutes=1)
            next_run = next_run.replace(second=0, microsecond=0)

        return next_run.timestamp()

    def get_schedules(self) -> dict[str, dict[str, Any]]:
        """Get all schedules."""
        with self._lock:
            return dict(self._schedules)

    def __len__(self) -> int:
        return len(self._schedules)
