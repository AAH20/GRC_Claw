"""
Workflow definition schema for GRC_Claw.

Defines the data model for workflow definitions, steps, conditions,
retry policies, run tracking, and template metadata.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
import uuid


class WorkflowStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    DEPRECATED = "deprecated"


class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    SKIPPED = "skipped"
    RETRYING = "retrying"
    TIMED_OUT = "timed_out"
    CANCELLED = "cancelled"


class StepType(str, Enum):
    ACTION = "action"
    DECISION = "decision"
    PARALLEL = "parallel"
    SUB_WORKFLOW = "sub_workflow"
    WAIT = "wait"
    HUMAN_APPROVAL = "human_approval"
    NOTIFICATION = "notification"


class TriggerType(str, Enum):
    MANUAL = "manual"
    SCHEDULED = "scheduled"
    EVENT = "event"
    WEBHOOK = "webhook"


@dataclass
class RetryPolicy:
    max_attempts: int = 3
    backoff_seconds: float = 1.0
    max_backoff_seconds: float = 300.0
    backoff_multiplier: float = 2.0
    retryable_exceptions: list[str] = field(default_factory=lambda: ["TimeoutError", "ConnectionError"])


@dataclass
class StepCondition:
    expression: str = ""
    on_success: bool = True
    variables: dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowStep:
    id: str
    name: str
    type: StepType = StepType.ACTION
    description: str = ""
    agent: str = ""
    tool: str = ""
    parameters: dict[str, Any] = field(default_factory=dict)
    depends_on: list[str] = field(default_factory=list)
    condition: Optional[StepCondition] = None
    retry_policy: RetryPolicy = field(default_factory=RetryPolicy)
    timeout_seconds: float = 300.0
    metadata: dict[str, Any] = field(default_factory=dict)
    next_steps: list[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.id:
            raise ValueError("step id must not be empty")
        if not self.name:
            raise ValueError("step name must not be empty")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be > 0")
        if self.retry_policy.max_attempts < 1:
            raise ValueError("retry_policy.max_attempts must be >= 1")


@dataclass
class WorkflowDefinition:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    version: str = "1.0.0"
    status: WorkflowStatus = WorkflowStatus.DRAFT
    trigger: TriggerType = TriggerType.MANUAL
    cron_expression: str = ""
    webhook_path: str = ""
    steps: list[WorkflowStep] = field(default_factory=list)
    variables: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    owner: str = ""
    max_concurrent_runs: int = 1
    timeout_seconds: float = 3600.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.name:
            raise ValueError("workflow name must not be empty")
        if self.max_concurrent_runs < 1:
            raise ValueError("max_concurrent_runs must be >= 1")
        step_ids = [s.id for s in self.steps]
        if len(step_ids) != len(set(step_ids)):
            raise ValueError("step ids must be unique within a workflow")
        for step in self.steps:
            for dep in step.depends_on:
                if dep not in step_ids:
                    raise ValueError(
                        f"step '{step.id}' depends on unknown step '{dep}'"
                    )

    def get_step(self, step_id: str) -> Optional[WorkflowStep]:
        for step in self.steps:
            if step.id == step_id:
                return step
        return None

    def validate(self) -> list[str]:
        """Validate the workflow definition and return a list of error messages."""
        errors: list[str] = []
        if not self.steps:
            errors.append("workflow must have at least step")
        step_ids = {s.id for s in self.steps}
        for step in self.steps:
            for dep in step.depends_on:
                if dep not in step_ids:
                    errors.append(
                        f"step '{step.id}' has unknown dependency '{dep}'"
                    )
            if step.type == StepType.PARALLEL and not step.next_steps:
                errors.append(
                    f"parallel step '{step.id}' should define next_steps"
                )
        visited: set[str] = set()
        temp_mark: set[str] = set()

        def dfs(node_id: str) -> None:
            if node_id in temp_mark:
                errors.append(f"cycle detected involving step '{node_id}'")
                return
            if node_id in visited:
                return
            temp_mark.add(node_id)
            step = self.get_step(node_id)
            if step:
                for nxt in step.next_steps:
                    if nxt in step_ids:
                        dfs(nxt)
            temp_mark.discard(node_id)
            visited.add(node_id)

        for step in self.steps:
            dfs(step.id)
        return errors


@dataclass
class StepResult:
    step_id: str
    status: StepStatus = StepStatus.PENDING
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    duration_seconds: float = 0.0
    output: Any = None
    error: Optional[str] = None
    attempt: int = 1
    logs: list[str] = field(default_factory=list)

    @property
    def is_terminal(self) -> bool:
        return self.status in {
            StepStatus.SUCCEEDED,
            StepStatus.FAILED,
            StepStatus.SKIPPED,
            StepStatus.CANCELLED,
            StepStatus.TIMED_OUT,
        }


@dataclass
class WorkflowRun:
    run_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    workflow_id: str = ""
    workflow_name: str = ""
    workflow_version: str = "1.0.0"
    status: StepStatus = StepStatus.PENDING
    trigger: TriggerType = TriggerType.MANUAL
    parameters: dict[str, Any] = field(default_factory=dict)
    context: dict[str, Any] = field(default_factory=dict)
    step_results: dict[str, StepResult] = field(default_factory=dict)
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    duration_seconds: float = 0.0
    error: Optional[str] = None
    triggered_by: str = ""
    parent_run_id: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_complete(self) -> bool:
        return self.status in {
            StepStatus.SUCCEEDED,
            StepStatus.FAILED,
            StepStatus.SKIPPED,
            StepStatus.CANCELLED,
            StepStatus.TIMED_OUT,
        }

    @property
    def progress_pct(self) -> float:
        if not self.step_results:
            return 0.0
        total = len(self.step_results)
        done = sum(1 for r in self.step_results.values() if r.is_terminal)
        return round((done / total) * 100, 1) if total else 0.0


@dataclass
class WorkflowTemplate:
    name: str
    description: str
    category: str
    definition_factory: Any = None  # Callable[[], WorkflowDefinition]
    default_variables: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    author: str = ""
    version: str = "1.0.0"

    def instantiate(self, name: str, **overrides: Any) -> WorkflowDefinition:
        if self.definition_factory is None:
            raise ValueError(f"template '{self.name}' has no definition_factory")
        wf = self.definition_factory()
        if name:
            wf.name = name
        for key, value in overrides.items():
            if hasattr(wf, key):
                setattr(wf, key, value)
        return wf
