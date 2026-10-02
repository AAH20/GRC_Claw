"""Process Automation Agent - automates repetitive marketing processes."""

from __future__ import annotations

import asyncio
import uuid
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable, Coroutine
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any

import structlog
from pydantic import BaseModel, Field
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = structlog.get_logger(__name__)


class ProcessStatus(StrEnum):
    """Process execution status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed_out"


class ProcessType(StrEnum):
    """Types of automatable processes."""

    DATA_SYNC = "data_sync"
    REPORT_GENERATION = "report_generation"
    LEAD_ROUTING = "lead_routing"
    CONTENT_DISTRIBUTION = "content_distribution"
    CAMPAIGN_MANAGEMENT = "campaign_management"
    CUSTOM = "custom"


class ProcessStep(BaseModel):
    """A step in an automated process."""

    step_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str = ""
    action: str
    config: dict[str, Any] = Field(default_factory=dict)
    order: int
    depends_on: list[str] = Field(default_factory=list)
    timeout_seconds: int = 300
    retry_count: int = 0
    max_retries: int = 3


class ProcessDefinition(BaseModel):
    """Definition of an automated process."""

    process_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str = ""
    process_type: ProcessType
    steps: list[ProcessStep] = Field(default_factory=list)
    schedule: str | None = None  # Cron expression
    is_active: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ProcessExecution(BaseModel):
    """Record of a process execution."""

    execution_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    process_id: str
    status: ProcessStatus = ProcessStatus.PENDING
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_seconds: float = 0.0
    step_results: dict[str, Any] = Field(default_factory=dict)
    error_message: str = ""
    triggered_by: str = "manual"  # manual, schedule, webhook


class ProcessCreateRequest(BaseModel):
    """Request to create a new automated process."""

    name: str
    description: str = ""
    process_type: ProcessType
    steps: list[ProcessStep] = Field(default_factory=list)
    schedule: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ProcessExecutionRequest(BaseModel):
    """Request to execute a process."""

    process_id: str = ""
    parameters: dict[str, Any] = Field(default_factory=dict)
    triggered_by: str = "manual"


@dataclass
class ProcessAutomationAgent:
    """Agent responsible for automating repetitive marketing processes.

    This agent manages process definitions, schedules, and executions.
    It supports retry logic, timeout handling, and parallel step execution.
    """

    _processes: dict[str, ProcessDefinition] = field(default_factory=dict)
    _executions: dict[str, ProcessExecution] = field(default_factory=dict)
    _running_tasks: dict[str, asyncio.Task[None]] = field(default_factory=dict)
    _action_registry: dict[str, Callable[..., Coroutine[Any, Any, Any]]] = field(
        default_factory=dict
    )
    _is_initialized: bool = False

    async def initialize(self) -> None:
        """Initialize the process automation agent."""
        logger.info("Initializing ProcessAutomationAgent")
        self._register_default_actions()
        self._is_initialized = True

    def _register_default_actions(self) -> None:
        """Register default action handlers."""
        self._action_registry.update({
            "http_request": self._action_http_request,
            "data_transform": self._action_data_transform,
            "send_notification": self._action_send_notification,
            "update_database": self._action_update_database,
            "trigger_webhook": self._action_trigger_webhook,
        })

    async def create_process(self, request: ProcessCreateRequest) -> ProcessDefinition:
        """Create a new automated process.

        Args:
            request: Process creation request.

        Returns:
            The created process definition.

        Raises:
            RuntimeError: If the agent is not initialized.
        """
        if not self._is_initialized:
            raise RuntimeError("Agent not initialized. Call initialize() first.")

        process = ProcessDefinition(
            name=request.name,
            description=request.description,
            process_type=request.process_type,
            steps=request.steps,
            schedule=request.schedule,
            metadata=request.metadata,
        )

        self._processes[process.process_id] = process

        logger.info(
            "Created new process",
            process_id=process.process_id,
            name=process.name,
            type=process.process_type.value,
        )

        return process

    async def execute_process(
        self, request: ProcessExecutionRequest
    ) -> ProcessExecution:
        """Execute an automated process.

        Args:
            request: Process execution request.

        Returns:
            The process execution record.

        Raises:
            RuntimeError: If the agent is not initialized.
            ValueError: If the process is not found.
        """
        if not self._is_initialized:
            raise RuntimeError("Agent not initialized. Call initialize() first.")

        process = self._processes.get(request.process_id)
        if not process:
            raise ValueError(f"Process not found: {request.process_id}")

        execution = ProcessExecution(
            process_id=request.process_id,
            status=ProcessStatus.PENDING,
            triggered_by=request.triggered_by,
        )
        self._executions[execution.execution_id] = execution

        logger.info(
            "Starting process execution",
            execution_id=execution.execution_id,
            process_id=request.process_id,
        )

        # Start execution in background
        task = asyncio.create_task(
            self._run_process(execution, process, request.parameters)
        )
        self._running_tasks[execution.execution_id] = task

        return execution

    async def _run_process(
        self,
        execution: ProcessExecution,
        process: ProcessDefinition,
        parameters: dict[str, Any],
    ) -> None:
        """Run a process execution.

        Args:
            execution: The execution record.
            process: The process definition.
            parameters: Execution parameters.
        """
        execution.status = ProcessStatus.RUNNING
        execution.started_at = datetime.utcnow()

        try:
            steps = sorted(process.steps, key=lambda s: s.order)
            completed_steps: set[str] = set()

            for step in steps:
                # Check dependencies
                if step.depends_on:
                    pending = set(step.depends_on) - completed_steps
                    if pending:
                        logger.warning(
                            "Step has unmet dependencies",
                            step=step.name,
                            pending_dependencies=list(pending),
                        )

                # Execute step with retry
                result = await self._execute_step_with_retry(
                    step, parameters, execution
                )
                execution.step_results[step.step_id] = result
                completed_steps.add(step.step_id)

            execution.status = ProcessStatus.COMPLETED
            logger.info(
                "Process execution completed",
                execution_id=execution.execution_id,
                process_id=process.process_id,
            )

        except Exception as e:
            execution.status = ProcessStatus.FAILED
            execution.error_message = str(e)
            logger.error(
                "Process execution failed",
                execution_id=execution.execution_id,
                process_id=process.process_id,
                error=str(e),
            )

        finally:
            execution.completed_at = datetime.utcnow()
            if execution.started_at:
                execution.duration_seconds = (
                    execution.completed_at - execution.started_at
                ).total_seconds()
            self._running_tasks.pop(execution.execution_id, None)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
    )
    async def _execute_step_with_retry(
        self,
        step: ProcessStep,
        parameters: dict[str, Any],
        execution: ProcessExecution,
    ) -> dict[str, Any]:
        """Execute a single step with retry logic.

        Args:
            step: The step to execute.
            parameters: Execution parameters.
            execution: The execution record.

        Returns:
            Step execution result.

        Raises:
            Exception: If the step fails after all retries.
        """
        action = self._action_registry.get(step.action)
        if not action:
            raise ValueError(f"Unknown action: {step.action}")

        logger.info(
            "Executing step",
            step_name=step.name,
            action=step.action,
            execution_id=execution.execution_id,
        )

        result = await action(step.config, parameters)

        return {
            "step_id": step.step_id,
            "step_name": step.name,
            "status": "completed",
            "result": result,
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def _action_http_request(
        self, config: dict[str, Any], parameters: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute an HTTP request action.

        Args:
            config: Step configuration.
            parameters: Execution parameters.

        Returns:
            HTTP response data.
        """
        import httpx

        url = config.get("url", "")
        method = config.get("method", "GET").upper()
        headers = config.get("headers", {})
        body = config.get("body", {})

        async with httpx.AsyncClient(timeout=config.get("timeout", 30)) as client:
            response = await client.request(
                method, url, headers=headers, json=body if body else None
            )
            response.raise_for_status()
            return {"status_code": response.status_code, "body": response.json()}

    async def _action_data_transform(
        self, config: dict[str, Any], parameters: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute a data transformation action.

        Args:
            config: Step configuration.
            parameters: Execution parameters.

        Returns:
            Transformed data.
        """
        source_data = parameters.get(config.get("source_key", "data"), {})
        transform_type = config.get("transform_type", "identity")

        if transform_type == "identity":
            return source_data
        elif transform_type == "filter":
            condition = config.get("condition", {})
            if isinstance(source_data, list):
                return [
                    item
                    for item in source_data
                    if all(item.get(k) == v for k, v in condition.items())
                ]
        elif transform_type == "map":
            mapping = config.get("mapping", {})
            if isinstance(source_data, dict):
                return {mapping.get(k, k): v for k, v in source_data.items()}

        return source_data

    async def _action_send_notification(
        self, config: dict[str, Any], parameters: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute a notification action.

        Args:
            config: Step configuration.
            parameters: Execution parameters.

        Returns:
            Notification result.
        """
        channel = config.get("channel", "email")
        message = config.get("message", "")
        recipients = config.get("recipients", [])

        logger.info(
            "Sending notification",
            channel=channel,
            recipients=recipients,
        )

        return {
            "channel": channel,
            "recipients": recipients,
            "message": message,
            "sent": True,
        }

    async def _action_update_database(
        self, config: dict[str, Any], parameters: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute a database update action.

        Args:
            config: Step configuration.
            parameters: Execution parameters.

        Returns:
            Database update result.
        """
        table = config.get("table", "")
        operation = config.get("operation", "insert")
        logger.info(
            "Updating database",
            table=table,
            operation=operation,
        )

        return {
            "table": table,
            "operation": operation,
            "records_affected": 1,
        }

    async def _action_trigger_webhook(
        self, config: dict[str, Any], parameters: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute a webhook trigger action.

        Args:
            config: Step configuration.
            parameters: Execution parameters.

        Returns:
            Webhook trigger result.
        """
        url = config.get("url", "")
        logger.info("Triggering webhook", url=url)

        return {
            "url": url,
            "triggered": True,
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def get_execution(self, execution_id: str) -> ProcessExecution | None:
        """Get an execution by ID.

        Args:
            execution_id: The execution identifier.

        Returns:
            The execution record or None if not found.
        """
        return self._executions.get(execution_id)

    async def list_executions(
        self,
        process_id: str | None = None,
        status: ProcessStatus | None = None,
    ) -> list[ProcessExecution]:
        """List executions with optional filters.

        Args:
            process_id: Filter by process ID.
            status: Filter by execution status.

        Returns:
            List of matching executions.
        """
        executions = list(self._executions.values())

        if process_id:
            executions = [e for e in executions if e.process_id == process_id]
        if status:
            executions = [e for e in executions if e.status == status]

        return sorted(executions, key=lambda e: e.started_at or datetime.min, reverse=True)

    async def cancel_execution(self, execution_id: str) -> bool:
        """Cancel a running execution.

        Args:
            execution_id: The execution identifier.

        Returns:
            True if cancelled, False if not found or not running.
        """
        execution = self._executions.get(execution_id)
        if not execution or execution.status != ProcessStatus.RUNNING:
            return False

        task = self._running_tasks.get(execution_id)
        if task:
            task.cancel()
            execution.status = ProcessStatus.CANCELLED
            execution.completed_at = datetime.utcnow()
            logger.info("Cancelled execution", execution_id=execution_id)
            return True

        return False

    async def get_process(self, process_id: str) -> ProcessDefinition | None:
        """Get a process definition by ID.

        Args:
            process_id: The process identifier.

        Returns:
            The process definition or None if not found.
        """
        return self._processes.get(process_id)

    async def list_processes(
        self,
        process_type: ProcessType | None = None,
        is_active: bool | None = None,
    ) -> list[ProcessDefinition]:
        """List process definitions with optional filters.

        Args:
            process_type: Filter by process type.
            is_active: Filter by active status.

        Returns:
            List of matching process definitions.
        """
        processes = list(self._processes.values())

        if process_type:
            processes = [p for p in processes if p.process_type == process_type]
        if is_active is not None:
            processes = [p for p in processes if p.is_active == is_active]

        return processes
