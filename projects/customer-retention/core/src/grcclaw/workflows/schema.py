"""
Workflow definition schema for GRC_Claw.

Defines the data model for workflow definitions, steps, conditions,
retry policies, run tracking, and template metadata.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


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


class WorkflowPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


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
    condition: StepCondition | None = None
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
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    owner: str = ""
    max_concurrent_runs: int = 1
    timeout_seconds: float = 3600.0
    metadata: dict[str, Any] = field(default_factory=dict)
    priority: WorkflowPriority = WorkflowPriority.NORMAL

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

    def get_step(self, step_id: str) -> WorkflowStep | None:
        for step in self.steps:
            if step.id == step_id:
                return step
        return None

    def validate(self) -> list[str]:
        """Validate the workflow definition and return a list of error messages."""
        errors: list[str] = []
        if not self.steps:
            errors.append("workflow must have at least one step")
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

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "status": self.status.value,
            "trigger": self.trigger.value,
            "cron_expression": self.cron_expression,
            "webhook_path": self.webhook_path,
            "steps": [
                {
                    "id": s.id,
                    "name": s.name,
                    "type": s.type.value,
                    "description": s.description,
                    "agent": s.agent,
                    "tool": s.tool,
                    "parameters": s.parameters,
                    "depends_on": s.depends_on,
                    "condition": asdict(s.condition) if s.condition else None,
                    "retry_policy": asdict(s.retry_policy),
                    "timeout_seconds": s.timeout_seconds,
                    "metadata": s.metadata,
                    "next_steps": s.next_steps,
                }
                for s in self.steps
            ],
            "variables": self.variables,
            "tags": self.tags,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "owner": self.owner,
            "max_concurrent_runs": self.max_concurrent_runs,
            "timeout_seconds": self.timeout_seconds,
            "metadata": self.metadata,
            "priority": self.priority.value,
        }

    def to_json(self, indent: int = 2) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, default=str)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WorkflowDefinition:
        """Deserialize from dictionary."""
        steps = []
        for s_data in data.get("steps", []):
            cond_data = s_data.get("condition")
            condition = StepCondition(**cond_data) if cond_data else None
            retry_policy = RetryPolicy(**s_data.get("retry_policy", {}))
            steps.append(WorkflowStep(
                id=s_data["id"],
                name=s_data["name"],
                type=StepType(s_data.get("type", "action")),
                description=s_data.get("description", ""),
                agent=s_data.get("agent", ""),
                tool=s_data.get("tool", ""),
                parameters=s_data.get("parameters", {}),
                depends_on=s_data.get("depends_on", []),
                condition=condition,
                retry_policy=retry_policy,
                timeout_seconds=s_data.get("timeout_seconds", 300.0),
                metadata=s_data.get("metadata", {}),
                next_steps=s_data.get("next_steps", []),
            ))
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data["name"],
            description=data.get("description", ""),
            version=data.get("version", "1.0.0"),
            status=WorkflowStatus(data.get("status", "draft")),
            trigger=TriggerType(data.get("trigger", "manual")),
            cron_expression=data.get("cron_expression", ""),
            webhook_path=data.get("webhook_path", ""),
            steps=steps,
            variables=data.get("variables", {}),
            tags=data.get("tags", []),
            created_at=data.get("created_at", datetime.now(UTC).isoformat()),
            updated_at=data.get("updated_at", datetime.now(UTC).isoformat()),
            owner=data.get("owner", ""),
            max_concurrent_runs=data.get("max_concurrent_runs", 1),
            timeout_seconds=data.get("timeout_seconds", 3600.0),
            metadata=data.get("metadata", {}),
            priority=WorkflowPriority(data.get("priority", "normal")),
        )

    @classmethod
    def from_json(cls, json_str: str) -> WorkflowDefinition:
        """Deserialize from JSON string."""
        return cls.from_dict(json.loads(json_str))


@dataclass
class StepResult:
    step_id: str
    status: StepStatus = StepStatus.PENDING
    started_at: str | None = None
    finished_at: str | None = None
    duration_seconds: float = 0.0
    output: Any = None
    error: str | None = None
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
    started_at: str | None = None
    finished_at: str | None = None
    duration_seconds: float = 0.0
    error: str | None = None
    triggered_by: str = ""
    parent_run_id: str | None = None
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

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "workflow_id": self.workflow_id,
            "workflow_name": self.workflow_name,
            "workflow_version": self.workflow_version,
            "status": self.status.value,
            "trigger": self.trigger.value,
            "parameters": self.parameters,
            "context": self.context,
            "step_results": {
                k: {
                    "step_id": v.step_id,
                    "status": v.status.value,
                    "started_at": v.started_at,
                    "finished_at": v.finished_at,
                    "duration_seconds": v.duration_seconds,
                    "output": v.output,
                    "error": v.error,
                    "attempt": v.attempt,
                    "logs": v.logs,
                }
                for k, v in self.step_results.items()
            },
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "duration_seconds": self.duration_seconds,
            "error": self.error,
            "triggered_by": self.triggered_by,
            "parent_run_id": self.parent_run_id,
            "metadata": self.metadata,
        }


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
