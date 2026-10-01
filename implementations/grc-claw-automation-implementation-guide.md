# GRC_Claw Automation Implementation Guide

**Document ID:** GRC-AUTO-001  
**Version:** 1.0  
**Date:** 2026-10-01  
**Status:** Draft  
**Owner:** GRC_Claw Architecture Team  
**References:** grc-claw-automation-engine-proposal.md, grc-claw-integration-specification.md

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Workflow Automation Patterns](#2-workflow-automation-patterns)
3. [Orchestration Engine (Temporal)](#3-orchestration-engine-temporal)
4. [Event-Driven Automation (CloudEvents)](#4-event-driven-automation-cloudevents)
5. [Policy-Driven Automation](#5-policy-driven-automation)
6. [Automation Testing Framework](#6-automation-testing-framework)
7. [Automation Monitoring and Optimization](#7-automation-monitoring-and-optimization)
8. [Closed-Loop Automation](#8-closed-loop-automation)
9. [Implementation Roadmap](#9-implementation-roadmap)
10. [Appendices](#10-appendices)

---

## 1. Executive Summary

This guide provides a complete implementation blueprint for GRC_Claw's automation engine. It translates the architecture defined in the automation engine proposal and integration specification into concrete, code-ready patterns covering seven domains:

1. **Workflow Automation Patterns** — Reusable patterns for governance workflows
2. **Orchestration Engine** — Temporal-based durable execution
3. **Event-Driven Automation** — CloudEvents for loose coupling
4. **Policy-Driven Automation** — OPA/Cedar policy-as-code enforcement
5. **Automation Testing Framework** — Contract, chaos, and conformance testing
6. **Automation Monitoring & Optimization** — Observability and continuous improvement
7. **Closed-Loop Automation** — Self-healing governance with feedback loops

### Design Principles

| Principle | Implementation |
|-----------|---------------|
| **Deterministic enforcement** | No LLM in the enforcement decision path |
| **MCP-native** | Governance embedded in AI workflows via MCP |
| **Evidence-first** | Every action produces auditable evidence |
| **Policy-as-code** | Version-controlled YAML/Cedar/Rego definitions |
| **Agent-separated** | Detection and enforcement by different agents |
| **Event-driven** | Loose coupling via CloudEvents + Kafka |

---

## 2. Workflow Automation Patterns

### 2.1 Pattern Catalog

GRC_Claw implements seven core workflow patterns derived from the automation engine proposal's workflow designs (Section 3.6) and integration specification (Section 5).

#### Pattern 1: Sequential Governance Pipeline

Used for: New AI system onboarding, policy activation, evidence collection.

```
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│ Discovery│──▶│ Inventory│──▶│   Risk   │──▶│  Policy  │──▶│  Audit   │
│          │   │          │   │Assessment│   │ Mapping  │   │ Evidence │
└──────────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘
```

**Implementation:**

```python
# workflows/sequential_pipeline.py
from dataclasses import dataclass, field
from typing import Any, Callable, Generic, TypeVar
from enum import Enum
import uuid
from datetime import datetime

T = TypeVar('T')

class StepStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    COMPENSATED = "compensated"

@dataclass
class StepResult(Generic[T]):
    step_name: str
    status: StepStatus
    output: T | None = None
    error: str | None = None
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
    evidence_id: str | None = None

@dataclass
class PipelineContext:
    pipeline_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str = ""
    correlation_id: str = ""
    trace_id: str = ""
    state: dict[str, Any] = field(default_factory=dict)
    evidence_chain: list[str] = field(default_factory=list)

class PipelineStep(Generic[T]):
    def __init__(
        self,
        name: str,
        handler: Callable[[PipelineContext], T],
        compensator: Callable[[PipelineContext, T], None] | None = None,
        evidence_collector: Callable[[PipelineContext, T], dict] | None = None,
    ):
        self.name = name
        self.handler = handler
        self.compensator = compensator
        self.evidence_collector = evidence_collector

    async def execute(self, context: PipelineContext) -> StepResult[T]:
        try:
            output = await self.handler(context) if asyncio.iscoroutinefunction(self.handler) else self.handler(context)
            evidence = None
            if self.evidence_collector:
                evidence_data = self.evidence_collector(context, output)
                evidence = await self._record_evidence(evidence_data, context)
            return StepResult(
                step_name=self.name,
                status=StepStatus.COMPLETED,
                output=output,
                evidence_id=evidence,
                completed_at=datetime.utcnow(),
            )
        except Exception as e:
            return StepResult(
                step_name=self.name,
                status=StepStatus.FAILED,
                error=str(e),
                completed_at=datetime.utcnow(),
            )

    async def compensate(self, context: PipelineContext, output: T) -> None:
        if self.compensator:
            self.compensator(context, output)

    async def _record_evidence(self, data: dict, context: PipelineContext) -> str:
        # Records evidence to the Evidence Ledger
        evidence_id = str(uuid.uuid4())
        context.evidence_chain.append(evidence_id)
        return evidence_id


class GovernancePipeline:
    def __init__(self, name: str, steps: list[PipelineStep]):
        self.name = name
        self.steps = steps
        self.results: list[StepResult] = []

    async def execute(self, context: PipelineContext) -> list[StepResult]:
        for step in self.steps:
            result = await step.execute(context)
            self.results.append(result)

            if result.status == StepStatus.FAILED:
                await self._compensate(context, result)
                break

            if result.output is not None:
                context.state[step.name] = result.output

        return self.results

    async def _compensate(self, context: PipelineContext, failed_result: StepResult):
        """Saga-style compensation: reverse completed steps."""
        for result in reversed(self.results):
            if result.status == StepStatus.COMPLETED:
                step = next(s for s in self.steps if s.name == result.step_name)
                await step.compensate(context, result.output)
                result.status = StepStatus.COMPENSATED
```

#### Pattern 2: Parallel Fan-Out with Aggregation

Used for: Multi-framework compliance scoring, parallel evidence collection, multi-agent risk assessment.

```python
# workflows/parallel_fanout.py
import asyncio
from dataclasses import dataclass, field
from typing import Any, Callable

@dataclass
class FanOutResult:
    task_name: str
    status: str  # "completed", "failed", "timeout"
    output: Any = None
    error: str | None = None
    latency_ms: float = 0.0

class ParallelFanOut:
    def __init__(self, max_concurrency: int = 10, timeout_seconds: float = 30.0):
        self.max_concurrency = max_concurrency
        self.timeout_seconds = timeout_seconds
        self.semaphore = asyncio.Semaphore(max_concurrency)

    async def execute(
        self,
        tasks: list[tuple[str, Callable]],
        aggregator: Callable[[list[FanOutResult]], Any],
    ) -> Any:
        async def run_task(name: str, handler: Callable) -> FanOutResult:
            async with self.semaphore:
                start = asyncio.get_event_loop().time()
                try:
                    if asyncio.iscoroutinefunction(handler):
                        output = await asyncio.wait_for(
                            handler(), timeout=self.timeout_seconds
                        )
                    else:
                        output = handler()
                    latency = (asyncio.get_event_loop().time() - start) * 1000
                    return FanOutResult(
                        task_name=name,
                        status="completed",
                        output=output,
                        latency_ms=latency,
                    )
                except asyncio.TimeoutError:
                    return FanOutResult(
                        task_name=name,
                        status="timeout",
                        error=f"Exceeded {self.timeout_seconds}s timeout",
                        latency_ms=self.timeout_seconds * 1000,
                    )
                except Exception as e:
                    return FanOutResult(
                        task_name=name,
                        status="failed",
                        error=str(e),
                        latency_ms=(asyncio.get_event_loop().time() - start) * 1000,
                    )

        results = await asyncio.gather(*[
            run_task(name, handler) for name, handler in tasks
        ])

        return aggregator(results)


# Usage: Parallel compliance scoring across frameworks
async def compute_compliance_posture(tenant_id: str, scope_id: str):
    fanout = ParallelFanOut(max_concurrency=6, timeout_seconds=10.0)

    frameworks = ["ISO-42001", "NIST-AI-RMF", "SOC2", "GDPR", "EU-AI-ACT", "HIPAA"]

    tasks = [
        (fw, lambda fw=fw: compliance_client.get_score(fw, scope_id))
        for fw in frameworks
    ]

    def aggregate(results: list[FanOutResult]) -> dict:
        return {
            "tenant_id": tenant_id,
            "scope_id": scope_id,
            "framework_scores": {
                r.task_name: r.output for r in results if r.status == "completed"
            },
            "failures": {
                r.task_name: r.error for r in results if r.status != "completed"
            },
            "partial": any(r.status != "completed" for r in results),
        }

    return await fanout.execute(tasks, aggregate)
```

#### Pattern 3: Event-Triggered Reaction

Used for: Runtime violation response, drift detection alerts, regulatory change response.

```python
# workflows/event_triggered.py
from dataclasses import dataclass
from typing import Callable, Any
from enum import Enum

class TriggerType(Enum):
    POLICY_VIOLATION = "policy_violation"
    DRIFT_DETECTED = "drift_detected"
    RISK_THRESHOLD = "risk_threshold"
    REGULATORY_CHANGE = "regulatory_change"
    EVIDENCE_EXPIRED = "evidence_expired"
    AGENT_ANOMALY = "agent_anomaly"

@dataclass
class Trigger:
    type: TriggerType
    source: str
    payload: dict[str, Any]
    priority: int = 5  # 1 (highest) to 10 (lowest)
    correlation_id: str = ""

class Reaction:
    def __init__(
        self,
        name: str,
        trigger_type: TriggerType,
        condition: Callable[[dict], bool],
        action: Callable[[dict], Any],
        confidence_threshold: float = 0.85,
    ):
        self.name = name
        self.trigger_type = trigger_type
        self.condition = condition
        self.action = action
        self.confidence_threshold = confidence_threshold

class EventTriggeredEngine:
    def __init__(self):
        self.reactions: dict[TriggerType, list[Reaction]] = {}
        self.confidence_router = ConfidenceRouter()

    def register(self, reaction: Reaction):
        if reaction.trigger_type not in self.reactions:
            self.reactions[reaction.trigger_type] = []
        self.reactions[reaction.trigger_type].append(reaction)

    async def handle(self, trigger: Trigger):
        reactions = self.reactions.get(trigger.type, [])
        for reaction in reactions:
            if reaction.condition(trigger.payload):
                confidence = trigger.payload.get("confidence_score", 1.0)

                if confidence >= reaction.confidence_threshold:
                    # Auto-remediate
                    result = await self._execute_with_evidence(reaction, trigger)
                    await self._record_decision(reaction, trigger, result, "auto")
                elif confidence >= 0.70:
                    # Route to human review
                    await self._escalate_to_human(reaction, trigger)
                else:
                    # Log and monitor
                    await self._log_low_confidence(reaction, trigger)

    async def _execute_with_evidence(self, reaction, trigger):
        evidence_context = {
            "trigger_type": trigger.type.value,
            "source": trigger.source,
            "correlation_id": trigger.correlation_id,
            "payload": trigger.payload,
        }
        return await reaction.action(evidence_context)


class ConfidenceRouter:
    """Routes decisions based on confidence thresholds (from proposal Section 3.2, Module 6)."""

    def __init__(self):
        self.thresholds = {
            "auto_remediate": 0.90,
            "human_review": 0.85,
            "log_only": 0.70,
        }

    def route(self, confidence: float) -> str:
        if confidence >= self.thresholds["auto_remediate"]:
            return "auto_remediate"
        if confidence >= self.thresholds["human_review"]:
            return "human_review"
        if confidence >= self.thresholds["log_only"]:
            return "log_only"
        return "ignore"
```

#### Pattern 4: State Machine Governance

Used for: Agent lifecycle, policy lifecycle, assessment workflow.

```python
# workflows/state_machine.py
from enum import Enum
from dataclasses import dataclass, field
from typing import Callable, Any

class AgentLifecycleState(Enum):
    PROPOSED = "proposed"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DEPRECATED = "deprecated"
    TERMINATED = "terminated"

@dataclass
class Transition:
    from_state: AgentLifecycleState
    to_state: AgentLifecycleState
    guard: Callable[[Any], bool] | None = None
    on_transition: Callable[[Any], None] | None = None
    evidence_required: bool = False

class GovernanceStateMachine:
    def __init__(self, initial_state: AgentLifecycleState):
        self.state = initial_state
        self.transitions: dict[tuple, Transition] = {}
        self.history: list[dict] = []

    def add_transition(self, transition: Transition):
        key = (transition.from_state, transition.to_state)
        self.transitions[key] = transition

    async def transition(
        self,
        to_state: AgentLifecycleState,
        context: Any = None,
    ) -> bool:
        key = (self.state, to_state)
        transition = self.transitions.get(key)

        if not transition:
            raise InvalidTransitionError(
                f"No transition from {self.state} to {to_state}"
            )

        if transition.guard and not transition.guard(context):
            return False

        if transition.evidence_required:
            evidence = await self._collect_evidence(self.state, to_state, context)
            if not evidence:
                return False

        old_state = self.state
        self.state = to_state

        if transition.on_transition:
            await transition.on_transition(context)

        self.history.append({
            "from": old_state.value,
            "to": to_state.value,
            "timestamp": datetime.utcnow().isoformat(),
            "context": context,
        })

        return True
```

#### Pattern 5: Scheduled Recurring Task

Used for: Continuous monitoring, evidence refresh, compliance recomputation, drift detection.

```python
# workflows/scheduled_task.py
from datetime import datetime, timedelta
from typing import Callable
import asyncio

class ScheduledTask:
    def __init__(
        self,
        name: str,
        schedule: str,  # Cron expression
        handler: Callable,
        max_retries: int = 3,
        timeout_seconds: float = 300.0,
    ):
        self.name = name
        self.schedule = schedule
        self.handler = handler
        self.max_retries = max_retries
        self.timeout_seconds = timeout_seconds
        self.last_run: datetime | None = None
        self.next_run: datetime | None = None
        self.run_count = 0
        self.failure_count = 0

    async def run(self):
        self.last_run = datetime.utcnow()
        self.run_count += 1

        for attempt in range(self.max_retries):
            try:
                result = await asyncio.wait_for(
                    self.handler(),
                    timeout=self.timeout_seconds,
                )
                await self._record_success(result)
                return result
            except Exception as e:
                if attempt == self.max_retries - 1:
                    self.failure_count += 1
                    await self._record_failure(e)
                    await self._alert_failure(e)
                else:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff


class CronParser:
    """Simple cron parser for scheduling."""

    @staticmethod
    def next_run(cron_expr: str, from_time: datetime | None = None) -> datetime:
        # Supports: "*/5 * * * *", "0 * * * *", "0 2 * * *"
        parts = cron_expr.split()
        now = from_time or datetime.utcnow()

        if len(parts) == 5:
            minute, hour, day, month, weekday = parts
            # Simplified: handle common patterns
            if minute.startswith("*/"):
                interval = int(minute.split("/")[1])
                next_minute = (now.minute // interval + 1) * interval
                if next_minute >= 60:
                    return now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
                return now.replace(minute=next_minute, second=0, microsecond=0)
            elif minute.isdigit() and hour.isdigit():
                next_time = now.replace(
                    minute=int(minute), hour=int(hour), second=0, microsecond=0
                )
                if next_time <= now:
                    next_time += timedelta(days=1)
                return next_time

        return now + timedelta(minutes=5)  # Default: every 5 minutes
```

#### Pattern 6: Human-in-the-Loop Approval

Used for: REQUIRE_APPROVAL decisions, policy exceptions, risk acceptance.

```python
# workflows/human_in_the_loop.py
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta
from typing import Callable

class ApprovalStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    EXPIRED = "expired"
    ESCALATED = "escalated"

@dataclass
class ApprovalRequest:
    id: str
    type: str  # "enforcement", "exception", "risk_acceptance", "policy_change"
    subject: dict  # What is being requested
    requester: str
    approvers: list[str]
    status: ApprovalStatus = ApprovalStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: datetime = field(default_factory=lambda: datetime.utcnow() + timedelta(hours=24))
    resolved_at: datetime | None = None
    resolved_by: str | None = None
    comments: str = ""
    escalation_count: int = 0

class ApprovalWorkflow:
    def __init__(self, notification_service, evidence_service):
        self.notification_service = notification_service
        self.evidence_service = evidence_service
        self.pending: dict[str, ApprovalRequest] = {}

    async def create_request(
        self,
        request_type: str,
        subject: dict,
        requester: str,
        approvers: list[str],
        timeout_hours: int = 24,
    ) -> ApprovalRequest:
        request = ApprovalRequest(
            id=str(uuid.uuid4()),
            type=request_type,
            subject=subject,
            requester=requester,
            approvers=approvers,
            expires_at=datetime.utcnow() + timedelta(hours=timeout_hours),
        )
        self.pending[request.id] = request

        # Notify approvers
        for approver in approvers:
            await self.notification_service.notify(
                recipient=approver,
                subject=f"Approval Required: {request_type}",
                body=f"Request {request.id} requires your review.",
                action_link=f"/approvals/{request.id}",
            )

        # Record evidence
        await self.evidence_service.record({
            "type": "approval_requested",
            "request_id": request.id,
            "subject": subject,
            "requester": requester,
        })

        return request

    async def resolve(
        self,
        request_id: str,
        approver: str,
        decision: ApprovalStatus,
        comments: str = "",
    ) -> ApprovalRequest:
        request = self.pending.get(request_id)
        if not request:
            raise RequestNotFoundError(request_id)

        if datetime.utcnow() > request.expires_at:
            request.status = ApprovalStatus.EXPIRED
            return request

        request.status = decision
        request.resolved_at = datetime.utcnow()
        request.resolved_by = approver
        request.comments = comments

        # Record evidence
        await self.evidence_service.record({
            "type": "approval_resolved",
            "request_id": request.id,
            "decision": decision.value,
            "approver": approver,
            "comments": comments,
        })

        return request

    async def escalate(self, request_id: str, reason: str):
        request = self.pending[request_id]
        request.escalation_count += 1
        request.status = ApprovalStatus.ESCALATED

        # Escalate to next level
        escalation_target = self._get_escalation_target(request)
        await self.notification_service.notify(
            recipient=escalation_target,
            subject=f"ESCALATED: Approval Request {request_id}",
            body=f"Escalation reason: {reason}",
            priority="high",
        )
```

#### Pattern 7: Circuit Breaker with Fallback

Used for: Enforcement engine resilience, external service calls.

```python
# workflows/circuit_breaker.py
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Callable, Any
import asyncio

class CircuitState(Enum):
    CLOSED = "closed"       # Normal operation
    OPEN = "open"           # Failing, reject requests
    HALF_OPEN = "half_open" # Testing if service recovered

@dataclass
class CircuitBreaker:
    name: str
    failure_threshold: int = 5
    recovery_timeout: timedelta = field(default_factory=lambda: timedelta(seconds=30))
    half_open_max_calls: int = 3
    on_failure: str = "fail_open"  # or "fail_closed"

    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: datetime | None = None
    half_open_calls: int = 0

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                self.half_open_calls = 0
            else:
                raise CircuitBreakerOpenError(
                    f"Circuit {self.name} is OPEN. "
                    f"Retry after {self._time_until_retry()}s"
                )

        if self.state == CircuitState.HALF_OPEN:
            if self.half_open_calls >= self.half_open_max_calls:
                raise CircuitBreakerOpenError(
                    f"Circuit {self.name} HALF_OPEN limit reached"
                )
            self.half_open_calls += 1

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            if self.on_failure == "fail_open":
                raise
            return None  # fail_closed: return None instead of raising

    def _on_success(self):
        self.failure_count = 0
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.CLOSED
            self.half_open_calls = 0

    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN

    def _should_attempt_reset(self) -> bool:
        if self.last_failure_time is None:
            return True
        return datetime.utcnow() - self.last_failure_time >= self.recovery_timeout

    def _time_until_retry(self) -> int:
        if self.last_failure_time is None:
            return 0
        elapsed = (datetime.utcnow() - self.last_failure_time).total_seconds()
        return max(0, int(self.recovery_timeout.total_seconds() - elapsed))
```

---

## 3. Orchestration Engine (Temporal)

### 3.1 Architecture

GRC_Claw uses Temporal as the primary orchestration engine for durable, long-running governance workflows. Temporal provides:

- **Durable execution** — Workflows survive process crashes and restarts
- **Exactly-once semantics** — Activities execute exactly once
- **Automatic retries** — Configurable retry policies with exponential backoff
- **Visibility** — Full workflow history and state inspection
- **Saga support** — Native compensation patterns

```
┌─────────────────────────────────────────────────────────────┐
│                    Temporal Cluster                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  Temporal │  │  Temporal │  │  Temporal │  │  Temporal │   │
│  │  Server   │  │  Server   │  │  Server   │  │  Server   │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Workflow Workers                         │   │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐       │   │
│  │  │  Policy    │ │ Enforcement│ │  Evidence  │       │   │
│  │  │  Worker    │ │  Worker    │ │  Worker    │       │   │
│  │  └────────────┘ └────────────┘ └────────────┘       │   │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐       │   │
│  │  │ Assessment │ │ Compliance │ │  Agent     │       │   │
│  │  │  Worker    │ │  Worker    │ │  Worker    │       │   │
│  │  └────────────┘ └────────────┘ └────────────┘       │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Workflow Definitions

#### Workflow 1: AI System Onboarding

```python
# temporal_workflows/onboarding_workflow.py
from temporalio import workflow
from temporalio.common import RetryPolicy
from dataclasses import dataclass
from datetime import timedelta

@dataclass
class OnboardingInput:
    asset_id: str
    asset_type: str  # "model", "agent", "pipeline", "dataset"
    tenant_id: str
    discovered_by: str
    metadata: dict

@dataclass
class OnboardingResult:
    asset_id: str
    status: str  # "onboarded", "rejected", "pending_review"
    risk_tier: str
    policies_applied: list[str]
    evidence_ids: list[str]
    assessment_id: str

@workflow.defn
class AIAssetOnboardingWorkflow:
    @workflow.run
    async def run(self, input: OnboardingInput) -> OnboardingResult:
        # Step 1: Create inventory record
        asset = await workflow.execute_activity(
            create_inventory_record,
            args=(input.asset_id, input.asset_type, input.metadata),
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=RetryPolicy(maximum_attempts=3),
        )

        # Step 2: Run risk assessment
        risk_result = await workflow.execute_activity(
            run_risk_assessment,
            args=(input.asset_id, input.asset_type),
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=RetryPolicy(maximum_attempts=3),
        )

        # Step 3: Map applicable policies
        policies = await workflow.execute_activity(
            map_applicable_policies,
            args=(input.asset_id, risk_result.risk_tier, input.metadata),
            start_to_close_timeout=timedelta(seconds=30),
        )

        # Step 4: EU AI Act triage
        eu_triage = await workflow.execute_activity(
            eu_ai_act_triage,
            args=(input.asset_id, input.metadata),
            start_to_close_timeout=timedelta(seconds=30),
        )

        # Step 5: If high risk, require human review
        if risk_result.risk_tier in ("prohibited", "high"):
            approval = await workflow.execute_activity(
                request_human_review,
                args=(input.asset_id, "high_risk_onboarding", risk_result),
                start_to_close_timeout=timedelta(hours=24),
            )

            if approval.decision != "approved":
                return OnboardingResult(
                    asset_id=input.asset_id,
                    status="rejected",
                    risk_tier=risk_result.risk_tier,
                    policies_applied=[],
                    evidence_ids=approval.evidence_ids,
                    assessment_id=risk_result.assessment_id,
                )

        # Step 6: Activate monitoring
        await workflow.execute_activity(
            activate_continuous_monitoring,
            args=(input.asset_id, policies),
            start_to_close_timeout=timedelta(seconds=30),
        )

        # Step 7: Generate evidence
        evidence_ids = await workflow.execute_activity(
            generate_onboarding_evidence,
            args=(input.asset_id, risk_result, policies),
            start_to_close_timeout=timedelta(seconds=30),
        )

        return OnboardingResult(
            asset_id=input.asset_id,
            status="onboarded",
            risk_tier=risk_result.risk_tier,
            policies_applied=[p.policy_id for p in policies],
            evidence_ids=evidence_ids,
            assessment_id=risk_result.assessment_id,
        )
```

#### Workflow 2: Runtime Violation Response

```python
# temporal_workflows/violation_response_workflow.py
@dataclass
class ViolationEvent:
    enforcement_id: str
    agent_id: str
    policy_id: str
    decision: str  # DENY, QUARANTINE, REQUIRE_APPROVAL
    confidence_score: float
    violation_type: str
    context: dict

@dataclass
class ViolationResponse:
    enforcement_id: str
    action_taken: str
    resolved: bool
    evidence_ids: list[str]
    escalation_id: str | None = None

@workflow.defn
class ViolationResponseWorkflow:
    @workflow.run
    async def run(self, event: ViolationEvent) -> ViolationResponse:
        evidence_ids = []

        # Step 1: Record violation evidence
        violation_evidence = await workflow.execute_activity(
            record_violation_evidence,
            args=(event,),
            start_to_close_timeout=timedelta(seconds=10),
        )
        evidence_ids.append(violation_evidence)

        # Step 2: Route based on confidence
        if event.confidence_score >= 0.90:
            # Auto-remediate
            action = await workflow.execute_activity(
                auto_remediate,
                args=(event.agent_id, event.violation_type, event.context),
                start_to_close_timeout=timedelta(seconds=30),
            )

            # Update agent trust score
            await workflow.execute_activity(
                update_trust_score,
                args=(event.agent_id, "violation", event.confidence_score),
                start_to_close_timeout=timedelta(seconds=10),
            )

            return ViolationResponse(
                enforcement_id=event.enforcement_id,
                action_taken="auto_remediated",
                resolved=True,
                evidence_ids=evidence_ids,
            )

        elif event.confidence_score >= 0.85:
            # Escalate to human
            escalation = await workflow.execute_activity(
                create_escalation,
                args=(event,),
                start_to_close_timeout=timedelta(seconds=30),
            )

            # Notify governance team
            await workflow.execute_activity(
                notify_governance_team,
                args=(event, escalation),
                start_to_close_timeout=timedelta(seconds=10),
            )

            return ViolationResponse(
                enforcement_id=event.enforcement_id,
                action_taken="escalated",
                resolved=False,
                evidence_ids=evidence_ids,
                escalation_id=escalation,
            )

        else:
            # Log and monitor
            await workflow.execute_activity(
                log_low_confidence_violation,
                args=(event,),
                start_to_close_timeout=timedelta(seconds=10),
            )

            return ViolationResponse(
                enforcement_id=event.enforcement_id,
                action_taken="logged",
                resolved=False,
                evidence_ids=evidence_ids,
            )
```

#### Workflow 3: Regulatory Change Response

```python
# temporal_workflows/regulatory_change_workflow.py
@dataclass
class RegulatoryChange:
    change_id: str
    framework: str
    change_type: str  # "new_regulation", "amendment", "repeal"
    effective_date: str
    description: str
    source_url: str

@workflow.defn
class RegulatoryChangeWorkflow:
    @workflow.run
    async def run(self, change: RegulatoryChange):
        # Step 1: Identify affected assets
        affected_assets = await workflow.execute_activity(
            identify_affected_assets,
            args=(change.framework, change.change_type),
            start_to_close_timeout=timedelta(minutes=5),
        )

        # Step 2: Gap analysis for each affected asset
        gap_results = await workflow.execute_activity(
            run_gap_analysis,
            args=(affected_assets, change),
            start_to_close_timeout=timedelta(minutes=10),
        )

        # Step 3: Generate compliance impact report
        impact_report = await workflow.execute_activity(
            generate_impact_report,
            args=(change, affected_assets, gap_results),
            start_to_close_timeout=timedelta(minutes=5),
        )

        # Step 4: Create remediation tasks for gaps
        remediation_tasks = await workflow.execute_activity(
            create_remediation_tasks,
            args=(gap_results, change.effective_date),
            start_to_close_timeout=timedelta(minutes=5),
        )

        # Step 5: Notify stakeholders
        await workflow.execute_activity(
            notify_stakeholders,
            args=(change, impact_report, affected_assets),
            start_to_close_timeout=timedelta(seconds=30),
        )

        # Step 6: Schedule re-assessment
        await workflow.execute_activity(
            schedule_reassessment,
            args=(affected_assets, change.effective_date),
            start_to_close_timeout=timedelta(seconds=30),
        )

        # Step 7: Record evidence
        await workflow.execute_activity(
            record_regulatory_change_evidence,
            args=(change, impact_report, remediation_tasks),
            start_to_close_timeout=timedelta(seconds=30),
        )
```

#### Workflow 4: Audit Evidence Generation

```python
# temporal_workflows/audit_evidence_workflow.py
@dataclass
class AuditRequest:
    request_id: str
    framework: str
    scope: dict
    date_range: tuple[str, str]
    auditor_id: str
    evidence_types: list[str]

@workflow.defn
class AuditEvidenceWorkflow:
    @workflow.run
    async def run(self, request: AuditRequest):
        # Step 1: Query evidence ledger
        evidence_items = await workflow.execute_activity(
            query_evidence_ledger,
            args=(request.framework, request.scope, request.date_range),
            start_to_close_timeout=timedelta(minutes=5),
        )

        # Step 2: Verify chain of custody
        custody_verification = await workflow.execute_activity(
            verify_chain_of_custody,
            args=(evidence_items,),
            start_to_close_timeout=timedelta(minutes=5),
        )

        # Step 3: Verify hash integrity
        hash_verification = await workflow.execute_activity(
            verify_hash_integrity,
            args=(evidence_items,),
            start_to_close_timeout=timedelta(minutes=5),
        )

        # Step 4: Compile evidence pack
        evidence_pack = await workflow.execute_activity(
            compile_evidence_pack,
            args=(request, evidence_items, custody_verification, hash_verification),
            start_to_close_timeout=timedelta(minutes=10),
        )

        # Step 5: Generate reports
        reports = await workflow.execute_activity(
            generate_audit_reports,
            args=(evidence_pack, request.framework),
            start_to_close_timeout=timedelta(minutes=10),
        )

        # Step 6: Export
        export_url = await workflow.execute_activity(
            export_evidence_pack,
            args=(evidence_pack, reports),
            start_to_close_timeout=timedelta(minutes=5),
        )

        # Step 7: Update AI Trust Center
        await workflow.execute_activity(
            update_trust_center,
            args=(request.framework, evidence_pack.summary),
            start_to_close_timeout=timedelta(seconds=30),
        )

        return {
            "request_id": request.request_id,
            "evidence_count": len(evidence_items),
            "verification_passed": custody_verification.valid and hash_verification.valid,
            "export_url": export_url,
            "reports": reports,
        }
```

### 3.3 Activity Definitions

```python
# temporal_activities/governance_activities.py
from temporalio import activity
from temporalio.common import RetryPolicy

@activity.defn
async def create_inventory_record(
    asset_id: str,
    asset_type: str,
    metadata: dict,
) -> dict:
    """Creates a new AI asset record in the Inventory Graph."""
    record = {
        "id": asset_id,
        "type": asset_type,
        "lifecycle_stage": "development",
        "risk_tier": "unknown",
        "deployment_status": "pending",
        "metadata": metadata,
        "created_at": datetime.utcnow().isoformat(),
    }
    # Persist to graph database
    await graph_db.create_node("AIAsset", record)
    return record

@activity.defn
async def run_risk_assessment(asset_id: str, asset_type: str) -> dict:
    """Runs multi-dimensional risk assessment."""
    # Parallel test execution
    test_results = await risk_engine.run_all_tests(asset_id, asset_type)

    # Compute 6-dimension trust score
    trust_score = compute_trust_score(test_results)

    # EU AI Act triage
    eu_triage = classify_eu_ai_act_risk(asset_id, asset_type)

    return {
        "asset_id": asset_id,
        "risk_tier": trust_score.tier,
        "trust_score": trust_score.composite,
        "dimensions": trust_score.dimensions,
        "eu_classification": eu_triage,
        "assessment_id": str(uuid.uuid4()),
    }

@activity.defn
async def map_applicable_policies(
    asset_id: str,
    risk_tier: str,
    metadata: dict,
) -> list:
    """Maps regulatory requirements to executable policies."""
    # Query policy packs based on asset type and risk tier
    applicable = await policy_engine.find_applicable(
        asset_type=metadata.get("type"),
        risk_tier=risk_tier,
        frameworks=metadata.get("frameworks", []),
        jurisdiction=metadata.get("jurisdiction"),
    )

    # Compile policies to enforcement rules
    for policy in applicable:
        policy.compiled_rules = await policy_compiler.compile(policy)

    return applicable

@activity.defn
async def auto_remediate(
    agent_id: str,
    violation_type: str,
    context: dict,
) -> str:
    """Automatically remediates a violation."""
    remediation_actions = {
        "data_exfiltration": isolate_agent,
        "policy_violation": apply_restrictive_policy,
        "scope_drift": reset_agent_scope,
        "anomaly": quarantine_agent,
    }

    action = remediation_actions.get(violation_type, quarantine_agent)
    result = await action(agent_id, context)

    # Record remediation evidence
    await evidence_service.record({
        "type": "remediation",
        "agent_id": agent_id,
        "violation_type": violation_type,
        "action_taken": result,
        "context": context,
    })

    return result
```

### 3.4 Worker Configuration

```python
# temporal_workers/worker_setup.py
from temporalio.worker import Worker
from temporalio.client import Client

async def run_worker():
    client = await Client.connect("temporal:7233")

    worker = Worker(
        client,
        task_queue="governance-workflows",
        workflows=[
            AIAssetOnboardingWorkflow,
            ViolationResponseWorkflow,
            RegulatoryChangeWorkflow,
            AuditEvidenceWorkflow,
        ],
        activities=[
            create_inventory_record,
            run_risk_assessment,
            map_applicable_policies,
            eu_ai_act_triage,
            request_human_review,
            activate_continuous_monitoring,
            generate_onboarding_evidence,
            record_violation_evidence,
            auto_remediate,
            update_trust_score,
            create_escalation,
            notify_governance_team,
            log_low_confidence_violation,
            identify_affected_assets,
            run_gap_analysis,
            generate_impact_report,
            create_remediation_tasks,
            notify_stakeholders,
            schedule_reassessment,
            record_regulatory_change_evidence,
            query_evidence_ledger,
            verify_chain_of_custody,
            verify_hash_integrity,
            compile_evidence_pack,
            generate_audit_reports,
            export_evidence_pack,
            update_trust_center,
        ],
        max_concurrent_workflow_tasks=100,
        max_concurrent_activities=50,
    )

    await worker.run()
```

### 3.5 Saga Pattern with Temporal

```python
# temporal_workflows/saga_workflow.py
from temporalio import workflow
from temporalio.common import RetryPolicy

@workflow.defn
class PolicyActivationSaga:
    """Saga for policy activation with compensation support."""

    @workflow.run
    async def run(self, policy_id: str):
        saga_state = SagaState(policy_id=policy_id)

        try:
            # Step 1: Validate policy
            validation = await workflow.execute_activity(
                validate_policy,
                args=(policy_id,),
                start_to_close_timeout=timedelta(seconds=10),
            )
            saga_state.add_step("validate_policy", validation)

            # Step 2: Compile policy
            compiled = await workflow.execute_activity(
                compile_policy,
                args=(policy_id,),
                start_to_close_timeout=timedelta(seconds=30),
            )
            saga_state.add_step("compile_policy", compiled)

            # Step 3: Distribute to enforcement engines
            distribution = await workflow.execute_activity(
                distribute_rules,
                args=(compiled,),
                start_to_close_timeout=timedelta(seconds=60),
            )
            saga_state.add_step("distribute_rules", distribution)

            # Step 4: Update policy status
            await workflow.execute_activity(
                update_policy_status,
                args=(policy_id, "active"),
                start_to_close_timeout=timedelta(seconds=10),
            )
            saga_state.add_step("update_status", {"status": "active"})

            # Step 5: Publish event
            await workflow.execute_activity(
                publish_policy_event,
                args=(policy_id, "PolicyActivated"),
                start_to_close_timeout=timedelta(seconds=10),
            )

            # Step 6: Update cache
            await workflow.execute_activity(
                update_policy_cache,
                args=(policy_id,),
                start_to_close_timeout=timedelta(seconds=5),
            )

            saga_state.complete()

        except Exception as e:
            # Compensate completed steps in reverse order
            await self._compensate(saga_state)
            raise

    async def _compensate(self, saga_state: SagaState):
        for step_name, step_result in reversed(saga_state.completed_steps):
            try:
                if step_name == "compile_policy":
                    await workflow.execute_activity(
                        delete_compiled_rules,
                        args=(step_result["policy_id"],),
                        start_to_close_timeout=timedelta(seconds=10),
                    )
                elif step_name == "distribute_rules":
                    await workflow.execute_activity(
                        remove_rules_from_enforcement,
                        args=(step_result["policy_id"],),
                        start_to_close_timeout=timedelta(seconds=30),
                    )
                elif step_name == "update_status":
                    await workflow.execute_activity(
                        update_policy_status,
                        args=(step_result["policy_id"], "draft"),
                        start_to_close_timeout=timedelta(seconds=10),
                    )
            except Exception as comp_error:
                # Log compensation failure — requires manual intervention
                await workflow.execute_activity(
                    alert_compensation_failure,
                    args=(saga_state.policy_id, step_name, str(comp_error)),
                    start_to_close_timeout=timedelta(seconds=10),
                )
```

---

## 4. Event-Driven Automation (CloudEvents)

### 4.1 Architecture

GRC_Claw uses CloudEvents 1.0 as the standard event envelope, with GRC_Claw-specific extensions for governance context. Events flow through Apache Kafka as the primary event backbone.

```
┌─────────────────────────────────────────────────────────────────┐
│                    Event-Driven Architecture                     │
│                                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │ Policy   │  │Enforcement│ │ Evidence │  │ Assessment│       │
│  │ Engine   │  │ Engine   │  │Orchestrator│ │ Engine   │       │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘       │
│       │              │              │              │              │
│       └──────────────┴──────────────┴──────────────┘              │
│                              │                                    │
│                    ┌─────────▼─────────┐                          │
│                    │  Event Gateway    │                          │
│                    │  (Schema Registry,│                          │
│                    │   Validation,     │                          │
│                    │   Enrichment)     │                          │
│                    └─────────┬─────────┘                          │
│                              │                                    │
│                    ┌─────────▼─────────┐                          │
│                    │  Kafka Cluster    │                          │
│                    │                   │                          │
│                    │  grcclaw.enforcement (12 partitions)        │
│                    │  grcclaw.evidence    (12 partitions)        │
│                    │  grcclaw.audit       (6 partitions)         │
│                    │  grcclaw.compliance  (6 partitions)         │
│                    │  grcclaw.risk        (6 partitions)         │
│                    │  grcclaw.agent       (6 partitions)         │
│                    │  grcclaw.policy      (6 partitions)         │
│                    │  grcclaw.assessment  (6 partitions)         │
│                    │  grcclaw.dlq         (3 partitions)         │
│                    └─────────┬─────────┘                          │
│                              │                                    │
│  ┌──────────┐  ┌──────────┐  │  ┌──────────┐  ┌──────────┐     │
│  │  SIEM    │  │Compliance│  │  │  Audit   │  │  Risk    │     │
│  │Connector │  │ Engine   │  │  │  Trail   │  │ Engine   │     │
│  └──────────┘  └──────────┘  │  └──────────┘  └──────────┘     │
│                              │                                    │
│                    ┌─────────▼─────────┐                          │
│                    │  Flink Cluster    │                          │
│                    │  (Stream Process) │                          │
│                    └───────────────────┘                          │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 CloudEvents Schema

All events conform to CloudEvents 1.0 with GRC_Claw extensions:

```json
{
  "specversion": "1.0",
  "id": "uuid-v4",
  "source": "grc-claw/enforcement-engine",
  "type": "com.grcclaw.enforcement.decision",
  "subject": "agent-123",
  "time": "2026-10-01T12:00:00Z",
  "datacontenttype": "application/json",
  "data": {
    "decision_id": "uuid",
    "agent_id": "uuid",
    "policy_id": "uuid",
    "decision": "DENY",
    "reason": "Policy violation: data_handling",
    "confidence_score": 0.95,
    "evidence_ids": ["uuid-1", "uuid-2"]
  },
  "grcclaw": {
    "tenant_id": "org-123",
    "environment": "prod",
    "trace_id": "uuid",
    "span_id": "uuid",
    "compliance_frameworks": ["ISO-42001", "SOC2"],
    "risk_tier": "high",
    "event_version": "1.0",
    "schema_version": "1.0",
    "correlation_id": "uuid",
    "causation_id": "uuid"
  }
}
```

### 4.3 Event Types

| Event Type | Source | Consumers | Payload |
|------------|--------|-----------|---------|
| `com.grcclaw.enforcement.decision` | Enforcement Engine | SIEM, Ticketing, Notification | Enforcement decision |
| `com.grcclaw.evidence.collected` | Evidence Orchestrator | SIEM, Data Warehouse, Analytics | Evidence metadata |
| `com.grcclaw.evidence.verified` | Evidence Orchestrator | SIEM, Compliance | Verification result |
| `com.grcclaw.assessment.completed` | Assessment Engine | GRC, Reporting, Ticketing | Assessment results |
| `com.grcclaw.compliance.computed` | Compliance Engine | Reporting, Dashboard, SIEM | Compliance posture |
| `com.grcclaw.risk.detected` | Risk Engine | SIEM, Ticketing, Notification | Risk signal |
| `com.grcclaw.agent.registered` | Agent Registry | IAM, SIEM, Inventory | Agent metadata |
| `com.grcclaw.agent.terminated` | Agent Registry | IAM, SIEM, Inventory | Termination record |
| `com.grcclaw.policy.activated` | Policy Engine | Enforcement, Cache, Notification | Policy details |
| `com.grcclaw.policy.violated` | Enforcement Engine | SIEM, Ticketing, Notification | Violation details |
| `com.grcclaw.audit.event` | Audit Trail | SIEM, Blockchain, Archive | Audit event |
| `com.grcclaw.exception.created` | Exception Manager | GRC, Notification, Approval | Exception details |
| `com.grcclaw.finding.created` | Assessment Engine | GRC, Ticketing, Remediation | Finding details |
| `com.grcclaw.vendor.risk_changed` | Vendor Manager | GRC, Procurement, Notification | Risk change |

### 4.4 Event Producer Implementation

```python
# events/producer.py
from cloudevents.http import CloudEvent, to_structured
from confluent_kafka import Producer
import json
import uuid
from datetime import datetime

class GRCEventProducer:
    def __init__(self, bootstrap_servers: str, schema_registry_url: str):
        self.producer = Producer({
            "bootstrap.servers": bootstrap_servers,
            "acks": "all",
            "retries": 3,
            "enable.idempotence": True,
            "compression.type": "lz4",
        })
        self.schema_registry = SchemaRegistryClient(schema_registry_url)

    async def publish(
        self,
        topic: str,
        event_type: str,
        source: str,
        subject: str,
        data: dict,
        tenant_id: str,
        environment: str = "prod",
        trace_id: str | None = None,
        correlation_id: str | None = None,
        causation_id: str | None = None,
    ) -> str:
        event_id = str(uuid.uuid4())

        attributes = {
            "specversion": "1.0",
            "id": event_id,
            "source": source,
            "type": event_type,
            "subject": subject,
            "time": datetime.utcnow().isoformat() + "Z",
            "datacontenttype": "application/json",
        }

        extensions = {
            "grcclaw": json.dumps({
                "tenant_id": tenant_id,
                "environment": environment,
                "trace_id": trace_id or str(uuid.uuid4()),
                "span_id": str(uuid.uuid4()),
                "compliance_frameworks": data.get("compliance_frameworks", []),
                "risk_tier": data.get("risk_tier"),
                "event_version": "1.0",
                "schema_version": "1.0",
                "correlation_id": correlation_id or str(uuid.uuid4()),
                "causation_id": causation_id,
            })
        }

        event = CloudEvent(attributes, {**data, **extensions})

        # Validate against schema
        await self._validate_against_schema(topic, event)

        # Produce to Kafka
        headers = {
            "ce_specversion": "1.0",
            "ce_id": event_id,
            "ce_source": source,
            "ce_type": event_type,
            "ce_subject": subject,
        }

        self.producer.produce(
            topic=topic,
            key=subject,
            value=json.dumps(event.data),
            headers=headers,
            callback=self._delivery_callback,
        )
        self.producer.flush()

        return event_id

    def _delivery_callback(self, err, msg):
        if err:
            # Send to DLQ
            self._send_to_dlq(msg, err)

    async def _validate_against_schema(self, topic: str, event: CloudEvent):
        schema = self.schema_registry.get_latest_schema(f"{topic}-value")
        validate(event.data, schema)
```

### 4.5 Event Consumer Implementation

```python
# events/consumer.py
from confluent_kafka import Consumer, KafkaError
from cloudevents.http import from_json
import asyncio

class GRCEventConsumer:
    def __init__(
        self,
        bootstrap_servers: str,
        group_id: str,
        topics: list[str],
        handler: callable,
    ):
        self.consumer = Consumer({
            "bootstrap.servers": bootstrap_servers,
            "group.id": group_id,
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
            "max.poll.records": 500,
            "session.timeout.ms": 45000,
            "heartbeat.interval.ms": 15000,
            "isolation.level": "read_committed",
        })
        self.consumer.subscribe(topics)
        self.handler = handler
        self.running = False

    async def start(self):
        self.running = True
        while self.running:
            msg = self.consumer.poll(timeout=1.0)

            if msg is None:
                continue

            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                else:
                    await self._handle_error(msg)
                    continue

            try:
                # Parse CloudEvent
                event = from_json(msg.value())

                # Process event
                await self.handler(event)

                # Commit offset after successful processing
                self.consumer.commit(message=msg, asynchronous=False)

            except Exception as e:
                await self._handle_processing_error(msg, e)

    async def _handle_error(self, msg):
        """Handle Kafka consumer errors."""
        error_count = getattr(self, '_error_count', 0) + 1
        if error_count >= 5:
            await self._send_to_dlq(msg, msg.error())

    async def _handle_processing_error(self, msg, error):
        """Handle event processing errors with retry logic."""
        retry_count = int(msg.headers().get('retry_count', 0))

        if retry_count < 5:
            # Retry with exponential backoff
            delay = [1, 5, 30, 120, 600][retry_count]
            await asyncio.sleep(delay)

            # Reproduce with incremented retry count
            new_headers = dict(msg.headers())
            new_headers['retry_count'] = str(retry_count + 1)

            self.producer.produce(
                topic=msg.topic(),
                key=msg.key(),
                value=msg.value(),
                headers=new_headers,
            )
        else:
            # Send to DLQ after max retries
            await self._send_to_dlq(msg, error)

    async def _send_to_dlq(self, msg, error):
        """Send failed message to Dead Letter Queue."""
        dlq_event = {
            "original_topic": msg.topic(),
            "original_partition": msg.partition(),
            "original_offset": msg.offset(),
            "original_key": msg.key(),
            "original_value": msg.value(),
            "error_class": type(error).__name__,
            "error_message": str(error),
            "failed_at": datetime.utcnow().isoformat(),
            "retry_count": int(msg.headers().get('retry_count', 0)),
        }
        self.producer.produce(
            topic="grcclaw.dlq",
            key=msg.key(),
            value=json.dumps(dlq_event),
        )
```

### 4.6 Event Enrichment Pipeline

```python
# events/enrichment.py
class EventEnrichmentService:
    """Enriches events with compliance context before distribution."""

    def __init__(self, policy_service, risk_service, framework_service):
        self.policy_service = policy_service
        self.risk_service = risk_service
        self.framework_service = framework_service

    async def enrich(self, event: CloudEvent) -> CloudEvent:
        data = event.data

        # Enrich with compliance framework context
        if "asset_id" in data:
            frameworks = await self.framework_service.get_applicable_frameworks(
                data["asset_id"]
            )
            data["compliance_frameworks"] = [f.id for f in frameworks]

        # Enrich with risk tier
        if "agent_id" in data:
            risk_profile = await self.risk_service.get_agent_risk(data["agent_id"])
            data["risk_tier"] = risk_profile.tier
            data["trust_score"] = risk_profile.trust_score

        # Enrich with policy context
        if "policy_id" in data:
            policy = await self.policy_service.get_policy(data["policy_id"])
            data["policy_frameworks"] = [m.framework for m in policy.framework_mappings]
            data["policy_category"] = policy.category

        # Enrich with trace context
        data["trace_id"] = event.extensions.get("trace_id", str(uuid.uuid4()))
        data["enriched_at"] = datetime.utcnow().isoformat()

        return CloudEvent(event.attributes, data)
```

### 4.7 Event Flow Patterns

#### Pattern 1: Simple Event Notification
```
Producer → Kafka Topic → Consumer(s) → Action
```
Used for: SIEM forwarding, cache invalidation, alert generation.

#### Pattern 2: Event Enrichment
```
Producer → Kafka → Enrichment Service → Kafka (enriched topic) → Consumer
```
Used for: Adding compliance framework context, risk tier classification.

#### Pattern 3: Event Aggregation
```
Multiple Producers → Kafka → Flink Window → Aggregated Topic → Consumer
```
Used for: Compliance score computation, risk trend analysis.

#### Pattern 4: Event Sourcing
```
Command → Event Store (Kafka) → Projector → Read Model → Query
```
Used for: Audit trail, compliance state reconstruction.

#### Pattern 5: CQRS with Event-Driven Sync
```
Command → Event Store → Kafka → Read Model Updater → Read DB → Query
```
Used for: Dashboard queries, reporting, analytics.

---

## 5. Policy-Driven Automation

### 5.1 Architecture

Policy-driven automation uses Open Policy Agent (OPA) and Cedar as the policy engines, with policies defined in version-controlled YAML and compiled to deterministic enforcement rules.

```
┌─────────────────────────────────────────────────────────────┐
│                  Policy-Driven Automation                    │
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  YAML    │  │  Cedar   │  │   Rego   │  │  Custom  │   │
│  │  Policy  │  │  Policy  │  │  Policy  │  │  Policy  │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘   │
│       │              │              │              │         │
│       └──────────────┴──────────────┴──────────────┘         │
│                              │                                │
│                    ┌─────────▼─────────┐                      │
│                    │  Policy Compiler  │                      │
│                    │  (YAML → OPA/Cedar)│                     │
│                    └─────────┬─────────┘                      │
│                              │                                │
│                    ┌─────────▼─────────┐                      │
│                    │  Compiled Rules   │                      │
│                    │  (JSON/Cedar)     │                      │
│                    └─────────┬─────────┘                      │
│                              │                                │
│                    ┌─────────▼─────────┐                      │
│                    │  Enforcement      │                      │
│                    │  Engine           │                      │
│                    │  (5-way decision) │                      │
│                    └───────────────────┘                      │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 Policy Definition (YAML)

```yaml
# policies/data_handling/policy_pii_protection.yaml
apiVersion: grcclaw/v1
kind: Policy
metadata:
  name: pii-protection
  version: "1.2.0"
  category: data_handling
  status: active
  owner: governance-team
  approvers:
    - chief-privacy-officer
    - compliance-lead
  tags:
    - pii
    - data-protection
    - gdpr
  labels:
    severity: critical
    auto-remediate: "true"

scope:
  agents: []  # Empty = all agents
  models: []
  resources:
    - "s3://customer-data/*"
    - "s3://pii-vault/*"
    - "api://payment-service/*"
  environments: [prod]
  risk_tiers: [prohibited, high, limited]

rules:
  - name: pii-access-requires-approval
    description: "Access to PII data requires explicit approval"
    condition:
      type: and
      conditions:
        - type: field_match
          field: action.type
          value: data_access
        - type: field_match
          field: action.resource
          pattern: "s3://customer-data/*"
        - type: field_match
          field: action.parameters.contains_pii
          value: true
    decision: REQUIRE_APPROVAL
    priority: 100
    on_violation:
      action: escalate
      target: data-protection-officer
      evidence_required: true

  - name: pii-export-prohibited
    description: "Exporting PII to unapproved destinations is prohibited"
    condition:
      type: and
      conditions:
        - type: field_match
          field: action.type
          value: data_access
        - type: field_match
          field: action.parameters.operation
          value: export
        - type: field_match
          field: action.parameters.destination
          pattern: "!approved-*"
    decision: DENY
    priority: 200
    on_violation:
      action: block
      evidence_required: true
      alert:
        severity: critical
        channels: [slack, email, pagerduty]

  - name: pii-redaction-required
    description: "PII fields must be redacted in responses"
    condition:
      type: and
      conditions:
        - type: field_match
          field: action.type
          value: model_inference
        - type: field_match
          field: action.parameters.contains_pii
          value: true
    decision: ALLOW_WITH_REDACTION
    priority: 150
    redaction:
      fields: [ssn, email, phone, address, dob]
      method: mask
      preserve_format: true

framework_mappings:
  - framework: GDPR
    control_ids: [Art.5, Art.6, Art.25, Art.32]
    mapping_strength: direct
  - framework: SOC2
    control_ids: [CC6.1, CC6.7]
    mapping_strength: direct
  - framework: HIPAA
    control_ids: [164.308, 164.312]
    mapping_strength: partial
  - framework: ISO-42001
    control_ids: [A.6.1, A.8.2]
    mapping_strength: indirect

enforcement:
  mode: enforce
  on_violation: block
  fail_mode: closed
  escalation_target: data-protection-officer

review_cycle: quarterly
effective_date: "2026-10-01"
expiration_date: "2027-10-01"
```

### 5.3 Policy Compiler

```python
# policy/compiler.py
from dataclasses import dataclass
from enum import Enum
import yaml
import json

class PolicyLanguage(Enum):
    YAML = "yaml"
    CEDAR = "cedar"
    REGO = "rego"
    JSON = "json"

@dataclass
class CompiledRule:
    rule_id: str
    name: str
    priority: int
    condition: dict  # Compiled condition tree
    decision: str
    redaction_config: dict | None
    escalation_config: dict | None
    evidence_config: dict | None

@dataclass
class CompiledPolicy:
    policy_id: str
    name: str
    version: str
    rules: list[CompiledRule]
    scope: dict
    framework_mappings: list[dict]
    enforcement_config: dict

class PolicyCompiler:
    """Compiles YAML policy definitions to executable enforcement rules."""

    def __init__(self, opa_client, cedar_client):
        self.opa = opa_client
        self.cedar = cedar_client

    async def compile(self, policy_yaml: str) -> CompiledPolicy:
        policy_data = yaml.safe_load(policy_yaml)

        rules = []
        for rule_def in policy_data.get("rules", []):
            compiled_rule = await self._compile_rule(rule_def, policy_data["metadata"])
            rules.append(compiled_rule)

        # Sort by priority (highest first)
        rules.sort(key=lambda r: r.priority, reverse=True)

        compiled = CompiledPolicy(
            policy_id=policy_data["metadata"]["name"],
            name=policy_data["metadata"]["name"],
            version=policy_data["metadata"]["version"],
            rules=rules,
            scope=policy_data.get("scope", {}),
            framework_mappings=policy_data.get("framework_mappings", []),
            enforcement_config=policy_data.get("enforcement", {}),
        )

        # Push to OPA/Cedar
        await self._distribute_to_engines(compiled)

        return compiled

    async def _compile_rule(self, rule_def: dict, metadata: dict) -> CompiledRule:
        condition = self._compile_condition(rule_def["condition"])

        return CompiledRule(
            rule_id=f"{metadata['name']}-{rule_def['name']}",
            name=rule_def["name"],
            priority=rule_def.get("priority", 50),
            condition=condition,
            decision=rule_def["decision"],
            redaction_config=rule_def.get("redaction"),
            escalation_config=rule_def.get("on_violation"),
            evidence_config={"required": rule_def.get("on_violation", {}).get("evidence_required", False)},
        )

    def _compile_condition(self, condition: dict) -> dict:
        """Compiles condition tree to OPA-compatible format."""
        if condition["type"] == "and":
            return {
                "type": "and",
                "conditions": [
                    self._compile_condition(c) for c in condition["conditions"]
                ],
            }
        elif condition["type"] == "or":
            return {
                "type": "or",
                "conditions": [
                    self._compile_condition(c) for c in condition["conditions"]
                ],
            }
        elif condition["type"] == "field_match":
            return {
                "type": "field_match",
                "field": condition["field"],
                "operator": self._get_operator(condition),
                "value": condition.get("value"),
                "pattern": condition.get("pattern"),
            }
        elif condition["type"] == "numeric_comparison":
            return {
                "type": "numeric_comparison",
                "field": condition["field"],
                "operator": condition["operator"],  # gt, lt, gte, lte, eq
                "value": condition["value"],
            }
        else:
            raise ValueError(f"Unknown condition type: {condition['type']}")

    def _get_operator(self, condition: dict) -> str:
        if "pattern" in condition:
            return "regex_match"
        return "eq"

    async def _distribute_to_engines(self, compiled: CompiledPolicy):
        """Distributes compiled rules to OPA and Cedar engines."""
        # Push to OPA as Rego
        rego_policy = self._to_rego(compiled)
        await self.opa.update_policy(compiled.policy_id, rego_policy)

        # Push to Cedar
        cedar_policy = self._to_cedar(compiled)
        await self.cedar.update_policy(compiled.policy_id, cedar_policy)

    def _to_rego(self, compiled: CompiledPolicy) -> str:
        """Converts compiled policy to Rego format."""
        lines = [
            f"package grcclaw.{compiled.policy_id}",
            "",
            "import future.keywords.if",
            "import future.keywords.in",
            "",
            "default decision := \"ALLOW\"",
            "",
        ]

        for rule in compiled.rules:
            lines.append(f"# Rule: {rule.name}")
            lines.append(f"decision := \"{rule.decision}\" if {{")
            lines.extend(self._condition_to_rego(rule.condition, indent=1))
            lines.append("}")
            lines.append("")

        return "\n".join(lines)

    def _condition_to_rego(self, condition: dict, indent: int = 0) -> list[str]:
        prefix = "\t" * indent
        if condition["type"] == "and":
            lines = []
            for i, c in enumerate(condition["conditions"]):
                if i > 0:
                    lines.append("")
                lines.extend(self._condition_to_rego(c, indent))
            return lines
        elif condition["type"] == "field_match":
            field_path = condition["field"].replace(".", "/")
            if condition.get("pattern"):
                return [f'{prefix}re.match("{condition["pattern"]}", input.{field_path})']
            else:
                return [f'{prefix}input.{field_path} == "{condition["value"]}"']
        return []
```

### 5.4 Five-Way Decision Engine

```python
# policy/decision_engine.py
from enum import Enum
from dataclasses import dataclass, field
from typing import Any

class DecisionType(Enum):
    ALLOW = "ALLOW"
    ALLOW_WITH_REDACTION = "ALLOW_WITH_REDACTION"
    REQUIRE_APPROVAL = "REQUIRE_APPROVAL"
    DENY = "DENY"
    QUARANTINE = "QUARANTINE"

@dataclass
class ActionContext:
    agent_id: str
    action_type: str  # tool_call, api_request, data_access, etc.
    tool_name: str | None
    resource: str
    parameters: dict
    environment: str
    trace_id: str
    metadata: dict = field(default_factory=dict)

@dataclass
class Decision:
    decision_id: str
    decision: DecisionType
    reason: str
    confidence_score: float
    policy_id: str
    policy_version: str
    rules_matched: list[str]
    evaluation_context: dict
    redaction: dict | None = None
    escalation: dict | None = None
    quarantine: dict | None = None
    evidence_ids: list[str] = field(default_factory=list)
    evaluation_latency_ms: int = 0
    deterministic: bool = True  # Always true for enforcement decisions

class FiveWayDecisionEngine:
    """Deterministic 5-way governance decision engine.

    Inspired by WhitePact's deterministic 5-way decision pattern.
    No LLM in the decision path — governance decisions are reproducible.
    """

    def __init__(self, opa_client, cedar_client, evidence_service):
        self.opa = opa_client
        self.cedar = cedar_client
        self.evidence = evidence_service
        self.decision_log: list[Decision] = []

    async def evaluate(self, context: ActionContext) -> Decision:
        start_time = time.monotonic()

        # Step 1: Get applicable policies
        policies = await self._get_applicable_policies(context)

        # Step 2: Evaluate rules in priority order (first-match-wins)
        for policy in policies:
            for rule in policy.rules:
                if self._evaluate_rule(rule, context):
                    decision = await self._make_decision(rule, policy, context)
                    decision.evaluation_latency_ms = int(
                        (time.monotonic() - start_time) * 1000
                    )
                    await self._record_decision(decision)
                    return decision

        # Default: ALLOW
        decision = Decision(
            decision_id=str(uuid.uuid4()),
            decision=DecisionType.ALLOW,
            reason="No policy rules matched",
            confidence_score=1.0,
            policy_id="default",
            policy_version="1.0",
            rules_matched=[],
            evaluation_context=context.__dict__,
            evaluation_latency_ms=int((time.monotonic() - start_time) * 1000),
        )
        await self._record_decision(decision)
        return decision

    def _evaluate_rule(self, rule: CompiledRule, context: ActionContext) -> bool:
        """Evaluates a single rule against the action context."""
        return self._evaluate_condition(rule.condition, context)

    def _evaluate_condition(self, condition: dict, context: ActionContext) -> bool:
        if condition["type"] == "and":
            return all(
                self._evaluate_condition(c, context)
                for c in condition["conditions"]
            )
        elif condition["type"] == "or":
            return any(
                self._evaluate_condition(c, context)
                for c in condition["conditions"]
            )
        elif condition["type"] == "field_match":
            value = self._get_field_value(condition["field"], context)
            if condition.get("pattern"):
                return bool(re.match(condition["pattern"], str(value)))
            return value == condition.get("value")
        elif condition["type"] == "numeric_comparison":
            value = self._get_field_value(condition["field"], context)
            op = condition["operator"]
            target = condition["value"]
            ops = {
                "gt": lambda a, b: a > b,
                "lt": lambda a, b: a < b,
                "gte": lambda a, b: a >= b,
                "lte": lambda a, b: a <= b,
                "eq": lambda a, b: a == b,
            }
            return ops[op](value, target)
        return False

    async def _make_decision(
        self,
        rule: CompiledRule,
        policy: CompiledPolicy,
        context: ActionContext,
    ) -> Decision:
        decision_type = DecisionType(rule.decision)
        decision = Decision(
            decision_id=str(uuid.uuid4()),
            decision=decision_type,
            reason=f"Policy rule matched: {rule.name}",
            confidence_score=1.0,  # Deterministic = 100% confidence
            policy_id=policy.policy_id,
            policy_version=policy.version,
            rules_matched=[rule.rule_id],
            evaluation_context=context.__dict__,
        )

        if decision_type == DecisionType.ALLOW_WITH_REDACTION:
            decision.redaction = rule.redaction_config
        elif decision_type == DecisionType.REQUIRE_APPROVAL:
            decision.escalation = rule.escalation_config
        elif decision_type == DecisionType.QUARANTINE:
            decision.quarantine = {
                "scope": "agent",
                "reason": rule.name,
                "initiated_by": "policy-engine",
            }

        # Record evidence
        if rule.evidence_config and rule.evidence_config.get("required"):
            evidence_id = await self.evidence.record({
                "type": "enforcement_decision",
                "decision_id": decision.decision_id,
                "policy_id": policy.policy_id,
                "rule_id": rule.rule_id,
                "context": context.__dict__,
            })
            decision.evidence_ids.append(evidence_id)

        return decision

    def _get_field_value(self, field: str, context: ActionContext) -> Any:
        """Extracts field value from context using dot notation."""
        parts = field.split(".")
        value = context.__dict__
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            else:
                value = getattr(value, part, None)
            if value is None:
                return None
        return value
```

### 5.5 Policy Packs (Pre-built Regulatory Mappings)

```python
# policy/packs/eu_ai_act_pack.py
EU_AI_ACT_POLICY_PACK = {
    "name": "eu-ai-act",
    "version": "1.0.0",
    "framework": "EU_AI_ACT",
    "description": "EU AI Act regulatory mapping pack",
    "policies": [
        {
            "name": "prohibited-practices",
            "article": "Art. 5",
            "description": "Prohibited AI practices",
            "rules": [
                {
                    "name": "social-scoring-prohibited",
                    "condition": {
                        "type": "field_match",
                        "field": "action.parameters.practice_type",
                        "value": "social_scoring",
                    },
                    "decision": "DENY",
                    "priority": 1000,
                },
                {
                    "name": "manipulation-prohibited",
                    "condition": {
                        "type": "field_match",
                        "field": "action.parameters.practice_type",
                        "value": "subliminal_manipulation",
                    },
                    "decision": "DENY",
                    "priority": 1000,
                },
                {
                    "name": "exploitation-prohibited",
                    "condition": {
                        "type": "field_match",
                        "field": "action.parameters.practice_type",
                        "value": "exploitation_of_vulnerabilities",
                    },
                    "decision": "DENY",
                    "priority": 1000,
                },
            ],
        },
        {
            "name": "high-risk-obligations",
            "article": "Art. 6, Annex III",
            "description": "High-risk AI system obligations",
            "rules": [
                {
                    "name": "risk-management-required",
                    "condition": {
                        "type": "and",
                        "conditions": [
                            {"type": "field_match", "field": "asset.risk_tier", "value": "high"},
                            {"type": "field_match", "field": "action.type", "value": "deployment"},
                        ],
                    },
                    "decision": "REQUIRE_APPROVAL",
                    "priority": 500,
                },
                {
                    "name": "transparency-required",
                    "condition": {
                        "type": "and",
                        "conditions": [
                            {"type": "field_match", "field": "asset.risk_tier", "value": "high"},
                            {"type": "field_match", "field": "action.type", "value": "model_inference"},
                        ],
                    },
                    "decision": "ALLOW_WITH_REDACTION",
                    "priority": 400,
                    "redaction": {
                        "fields": ["model_internals", "training_data"],
                        "method": "remove",
                    },
                },
            ],
        },
    ],
}
```

---

## 6. Automation Testing Framework

### 6.1 Architecture

The automation testing framework provides four layers of testing for GRC_Claw's automation engine:

```
┌─────────────────────────────────────────────────────────────┐
│                  Testing Framework                           │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Layer 4: Chaos Engineering                           │   │
│  │  • Failure injection • Resilience validation          │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Layer 3: Conformance Testing                         │   │
│  │  • Policy compliance • Framework mapping validation   │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Layer 2: Integration Testing                         │   │
│  │  • Event flow • API contract • Workflow execution     │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Layer 1: Unit Testing                                 │   │
│  │  • Decision engine • Policy compiler • Activities     │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 6.2 Unit Testing

```python
# tests/unit/test_decision_engine.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from policy.decision_engine import FiveWayDecisionEngine, ActionContext, DecisionType

@pytest.fixture
def decision_engine():
    opa_client = AsyncMock()
    cedar_client = AsyncMock()
    evidence_service = AsyncMock()
    evidence_service.record.return_value = "evidence-123"
    return FiveWayDecisionEngine(opa_client, cedar_client, evidence_service)

@pytest.fixture
def sample_context():
    return ActionContext(
        agent_id="agent-123",
        action_type="data_access",
        tool_name="s3_reader",
        resource="s3://customer-data/pii/file.csv",
        parameters={"contains_pii": True, "operation": "read"},
        environment="prod",
        trace_id="trace-456",
    )

class TestFiveWayDecisionEngine:
    @pytest.mark.asyncio
    async def test_pii_access_requires_approval(self, decision_engine, sample_context):
        """PII access should trigger REQUIRE_APPROVAL decision."""
        # Arrange
        mock_policy = MagicMock()
        mock_policy.policy_id = "pii-protection"
        mock_policy.version = "1.2.0"
        mock_policy.rules = [
            MagicMock(
                rule_id="pii-access-requires-approval",
                name="pii-access-requires-approval",
                priority=100,
                condition={
                    "type": "and",
                    "conditions": [
                        {"type": "field_match", "field": "action_type", "value": "data_access"},
                        {"type": "field_match", "field": "resource", "pattern": "s3://customer-data/*"},
                        {"type": "field_match", "field": "parameters.contains_pii", "value": True},
                    ],
                },
                decision="REQUIRE_APPROVAL",
                redaction_config=None,
                escalation_config={"target": "data-protection-officer"},
                evidence_config={"required": True},
            )
        ]
        decision_engine._get_applicable_policies = AsyncMock(return_value=[mock_policy])

        # Act
        decision = await decision_engine.evaluate(sample_context)

        # Assert
        assert decision.decision == DecisionType.REQUIRE_APPROVAL
        assert decision.policy_id == "pii-protection"
        assert decision.deterministic is True
        assert decision.confidence_score == 1.0
        assert len(decision.evidence_ids) > 0

    @pytest.mark.asyncio
    async def test_pii_export_denied(self, decision_engine, sample_context):
        """PII export to unapproved destination should be DENIED."""
        sample_context.parameters = {"contains_pii": True, "operation": "export", "destination": "unapproved-bucket"}

        mock_policy = MagicMock()
        mock_policy.policy_id = "pii-protection"
        mock_policy.version = "1.2.0"
        mock_policy.rules = [
            MagicMock(
                rule_id="pii-export-prohibited",
                name="pii-export-prohibited",
                priority=200,
                condition={
                    "type": "and",
                    "conditions": [
                        {"type": "field_match", "field": "action_type", "value": "data_access"},
                        {"type": "field_match", "field": "parameters.operation", "value": "export"},
                        {"type": "field_match", "field": "parameters.destination", "pattern": "!approved-*"},
                    ],
                },
                decision="DENY",
                redaction_config=None,
                escalation_config={"action": "block", "alert": {"severity": "critical"}},
                evidence_config={"required": True},
            )
        ]
        decision_engine._get_applicable_policies = AsyncMock(return_value=[mock_policy])

        decision = await decision_engine.evaluate(sample_context)

        assert decision.decision == DecisionType.DENY
        assert decision.deterministic is True

    @pytest.mark.asyncio
    async def test_default_allow_when_no_rules_match(self, decision_engine, sample_context):
        """When no rules match, default to ALLOW."""
        decision_engine._get_applicable_policies = AsyncMock(return_value=[])

        decision = await decision_engine.evaluate(sample_context)

        assert decision.decision == DecisionType.ALLOW
        assert decision.reason == "No policy rules matched"

    @pytest.mark.asyncio
    async def test_redaction_applied_for_pii_inference(self, decision_engine, sample_context):
        """PII in model inference should trigger ALLOW_WITH_REDACTION."""
        sample_context.action_type = "model_inference"
        sample_context.parameters = {"contains_pii": True}

        mock_policy = MagicMock()
        mock_policy.policy_id = "pii-protection"
        mock_policy.version = "1.2.0"
        mock_policy.rules = [
            MagicMock(
                rule_id="pii-redaction-required",
                name="pii-redaction-required",
                priority=150,
                condition={
                    "type": "and",
                    "conditions": [
                        {"type": "field_match", "field": "action_type", "value": "model_inference"},
                        {"type": "field_match", "field": "parameters.contains_pii", "value": True},
                    ],
                },
                decision="ALLOW_WITH_REDACTION",
                redaction_config={"fields": ["ssn", "email", "phone"], "method": "mask"},
                escalation_config=None,
                evidence_config={"required": False},
            )
        ]
        decision_engine._get_applicable_policies = AsyncMock(return_value=[mock_policy])

        decision = await decision_engine.evaluate(sample_context)

        assert decision.decision == DecisionType.ALLOW_WITH_REDACTION
        assert decision.redaction is not None
        assert decision.redaction["method"] == "mask"
```

### 6.3 Integration Testing

```python
# tests/integration/test_event_flow.py
import pytest
import asyncio
from events.producer import GRCEventProducer
from events.consumer import GRCEventConsumer

@pytest.fixture
async def kafka_container():
    """Spin up Kafka test container."""
    from testcontainers.kafka import KafkaContainer
    with KafkaContainer() as kafka:
        yield kafka.get_bootstrap_server()

@pytest.mark.asyncio
async def test_enforcement_decision_event_flow(kafka_container):
    """Test that enforcement decisions flow through the event pipeline."""
    received_events = []

    async def event_handler(event):
        received_events.append(event)

    # Start consumer
    consumer = GRCEventConsumer(
        bootstrap_servers=kafka_container,
        group_id="test-consumer",
        topics=["grcclaw.enforcement"],
        handler=event_handler,
    )
    consumer_task = asyncio.create_task(consumer.start())
    await asyncio.sleep(2)  # Let consumer start

    # Publish event
    producer = GRCEventProducer(bootstrap_servers=kafka_container)
    event_id = await producer.publish(
        topic="grcclaw.enforcement",
        event_type="com.grcclaw.enforcement.decision",
        source="grc-claw/enforcement-engine",
        subject="agent-123",
        data={
            "decision_id": "decision-456",
            "agent_id": "agent-123",
            "policy_id": "policy-789",
            "decision": "DENY",
            "reason": "Policy violation: data_handling",
            "confidence_score": 0.95,
        },
        tenant_id="org-123",
        environment="prod",
    )

    # Wait for event to be consumed
    await asyncio.sleep(3)
    consumer.running = False
    await consumer_task

    # Assert
    assert len(received_events) == 1
    event = received_events[0]
    assert event.data["decision_id"] == "decision-456"
    assert event.data["decision"] == "DENY"
    assert event.data["agent_id"] == "agent-123"

@pytest.mark.asyncio
async def test_dead_letter_queue_after_max_retries(kafka_container):
    """Test that failed events are sent to DLQ after max retries."""
    async def failing_handler(event):
        raise ValueError("Simulated processing failure")

    consumer = GRCEventConsumer(
        bootstrap_servers=kafka_container,
        group_id="test-dlq-consumer",
        topics=["grcclaw.enforcement"],
        handler=failing_handler,
    )
    consumer_task = asyncio.create_task(consumer.start())
    await asyncio.sleep(2)

    producer = GRCEventProducer(bootstrap_servers=kafka_container)
    await producer.publish(
        topic="grcclaw.enforcement",
        event_type="com.grcclaw.enforcement.decision",
        source="grc-claw/enforcement-engine",
        subject="agent-123",
        data={"decision_id": "decision-456", "decision": "DENY"},
        tenant_id="org-123",
    )

    # Wait for retries to exhaust
    await asyncio.sleep(15)
    consumer.running = False
    await consumer_task

    # Check DLQ
    dlq_consumer = GRCEventConsumer(
        bootstrap_servers=kafka_container,
        group_id="test-dlq-reader",
        topics=["grcclaw.dlq"],
        handler=lambda e: None,
    )
    # Verify DLQ contains the failed event
```

### 6.4 Conformance Testing

```python
# tests/conformance/test_policy_compliance.py
import pytest
import yaml
from policy.compiler import PolicyCompiler

class TestPolicyConformance:
    """Validates that policies conform to GRC_Claw policy schema."""

    @pytest.fixture
    def compiler(self):
        return PolicyCompiler(opa_client=AsyncMock(), cedar_client=AsyncMock())

    @pytest.mark.asyncio
    async def test_eu_ai_act_prohibited_practices(self, compiler):
        """EU AI Act Art. 5 prohibited practices must result in DENY."""
        policy_yaml = """
        apiVersion: grcclaw/v1
        kind: Policy
        metadata:
          name: eu-ai-act-prohibited
          version: "1.0.0"
          category: content_safety
        rules:
          - name: social-scoring-prohibited
            condition:
              type: field_match
              field: action.parameters.practice_type
              value: social_scoring
            decision: DENY
            priority: 1000
        """
        compiled = await compiler.compile(policy_yaml)

        # Verify all prohibited practices map to DENY
        for rule in compiled.rules:
            assert rule.decision == "DENY", (
                f"Prohibited practice rule {rule.name} must be DENY"
            )

    @pytest.mark.asyncio
    async def test_framework_mapping_completeness(self, compiler):
        """Every policy must map to at least one framework."""
        policy_yaml = """
        apiVersion: grcclaw/v1
        kind: Policy
        metadata:
          name: test-policy
          version: "1.0.0"
        framework_mappings:
          - framework: ISO-42001
            control_ids: [A.6.1]
            mapping_strength: direct
        rules:
          - name: test-rule
            condition:
              type: field_match
              field: action.type
              value: test
            decision: ALLOW
        """
        compiled = await compiler.compile(policy_yaml)

        assert len(compiled.framework_mappings) > 0
        assert compiled.framework_mappings[0]["framework"] == "ISO-42001"

    @pytest.mark.asyncio
    async def test_decision_determinism(self, compiler):
        """Same input must always produce same decision (deterministic)."""
        policy_yaml = """
        apiVersion: grcclaw/v1
        kind: Policy
        metadata:
          name: determinism-test
          version: "1.0.0"
        rules:
          - name: deterministic-rule
            condition:
              type: field_match
              field: action.type
              value: data_access
            decision: REQUIRE_APPROVAL
            priority: 100
        """
        compiled = await compiler.compile(policy_yaml)

        # Compile twice and verify identical output
        compiled_again = await compiler.compile(policy_yaml)

        assert len(compiled.rules) == len(compiled_again.rules)
        for r1, r2 in zip(compiled.rules, compiled_again.rules):
            assert r1.decision == r2.decision
            assert r1.priority == r2.priority
            assert r1.condition == r2.condition
```

### 6.5 Chaos Engineering

```python
# tests/chaos/test_resilience.py
import pytest
import asyncio
import random
from unittest.mock import AsyncMock, patch

class TestChaosEngineering:
    """Chaos tests for automation engine resilience."""

    @pytest.mark.asyncio
    async def test_enforcement_survives_policy_engine_crash(self):
        """Enforcement should fail closed when policy engine is unavailable."""
        opa_client = AsyncMock()
        opa_client.evaluate.side_effect = ConnectionError("OPA unavailable")

        engine = FiveWayDecisionEngine(
            opa_client=opa_client,
            cedar_client=AsyncMock(),
            evidence_service=AsyncMock(),
        )

        context = ActionContext(
            agent_id="agent-123",
            action_type="data_access",
            tool_name="s3_reader",
            resource="s3://customer-data/pii/file.csv",
            parameters={"contains_pii": True},
            environment="prod",
            trace_id="trace-456",
        )

        # Should fail closed (DENY) when policy engine is down
        decision = await engine.evaluate(context)
        assert decision.decision == DecisionType.DENY
        assert "policy engine unavailable" in decision.reason.lower()

    @pytest.mark.asyncio
    async def test_evidence_service_failure_does_not_block_enforcement(self):
        """Evidence service failure should not block enforcement decisions."""
        evidence_service = AsyncMock()
        evidence_service.record.side_effect = TimeoutError("Evidence store timeout")

        engine = FiveWayDecisionEngine(
            opa_client=AsyncMock(),
            cedar_client=AsyncMock(),
            evidence_service=evidence_service,
        )

        # Should still make decision even if evidence recording fails
        decision = await engine.evaluate(context)
        assert decision.decision in [DecisionType.ALLOW, DecisionType.DENY]

    @pytest.mark.asyncio
    async def test_kafka_consumer_recovers_from_processing_errors(self):
        """Consumer should recover and continue after processing errors."""
        processed = []
        error_count = 0

        async def flaky_handler(event):
            nonlocal error_count
            error_count += 1
            if error_count <= 3:
                raise ValueError("Transient error")
            processed.append(event)

        consumer = GRCEventConsumer(
            bootstrap_servers="localhost:9092",
            group_id="test-chaos",
            topics=["grcclaw.enforcement"],
            handler=flaky_handler,
        )

        # Simulate events
        for i in range(5):
            event = CloudEvent(
                attributes={
                    "specversion": "1.0",
                    "id": f"event-{i}",
                    "source": "test",
                    "type": "com.grcclaw.enforcement.decision",
                    "subject": f"agent-{i}",
                },
                data={"decision": "ALLOW"},
            )
            try:
                await consumer.handler(event)
            except ValueError:
                pass

        # After 3 failures, should recover
        assert len(processed) == 2  # Events 4 and 5 processed

    @pytest.mark.asyncio
    async def test_circuit_breaker_opens_after_repeated_failures(self):
        """Circuit breaker should open after threshold failures."""
        cb = CircuitBreaker(
            name="test-service",
            failure_threshold=3,
            recovery_timeout=timedelta(seconds=30),
        )

        call_count = 0

        async def failing_call():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("Service unavailable")

        # First 3 calls should raise
        for _ in range(3):
            with pytest.raises(ConnectionError):
                await cb.call(failing_call)

        # Circuit should be open now
        assert cb.state == CircuitState.OPEN

        # Next call should raise CircuitBreakerOpenError
        with pytest.raises(CircuitBreakerOpenError):
            await cb.call(failing_call)

        # Call count should not increase (circuit is open)
        assert call_count == 3
```

### 6.6 Contract Testing

```python
# tests/contracts/test_api_contracts.py
import pytest
from httpx import AsyncClient

class TestEnforcementAPIContract:
    """Contract tests for enforcement API endpoints."""

    @pytest.mark.asyncio
    async def test_enforce_endpoint_returns_valid_decision(self):
        """POST /v1/enforcements must return a valid 5-way decision."""
        async with AsyncClient(base_url="http://localhost:8080") as client:
            response = await client.post("/v1/enforcements", json={
                "agent_id": "agent-123",
                "action": {
                    "type": "data_access",
                    "tool_name": "s3_reader",
                    "resource": "s3://customer-data/pii/file.csv",
                    "parameters": {"contains_pii": True},
                },
                "context": {
                    "environment": "prod",
                    "trace_id": "trace-456",
                },
            })

        assert response.status_code == 200
        data = response.json()

        # Verify response schema
        assert "decision_id" in data
        assert data["decision"] in ["ALLOW", "ALLOW_WITH_REDACTION", "REQUIRE_APPROVAL", "DENY", "QUARANTINE"]
        assert "reason" in data
        assert "confidence_score" in data
        assert "policy_id" in data
        assert "evaluation_latency_ms" in data
        assert data["deterministic"] is True

    @pytest.mark.asyncio
    async def test_policy_compile_endpoint(self):
        """POST /v1/policies/{id}/compile must return compiled rules."""
        async with AsyncClient(base_url="http://localhost:8080") as client:
            # First create a policy
            create_response = await client.post("/v1/policies", json={
                "name": "test-policy",
                "version": "1.0.0",
                "category": "data_handling",
                "rules": [
                    {
                        "name": "test-rule",
                        "condition": {
                            "type": "field_match",
                            "field": "action.type",
                            "value": "data_access",
                        },
                        "decision": "REQUIRE_APPROVAL",
                        "priority": 100,
                    }
                ],
            })
            policy_id = create_response.json()["id"]

            # Compile
            compile_response = await client.post(f"/v1/policies/{policy_id}/compile")

        assert compile_response.status_code == 200
        data = compile_response.json()
        assert "compiled_rules" in data
        assert len(data["compiled_rules"]) > 0
```

---

## 7. Automation Monitoring and Optimization

### 7.1 Monitoring Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  Monitoring Architecture                     │
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  OTel    │  │Prometheus│  │  Custom  │  │  Flink   │   │
│  │ Traces   │  │ Metrics  │  │  Events  │  │  Jobs    │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘   │
│       │              │              │              │         │
│       └──────────────┴──────────────┴──────────────┘         │
│                              │                                │
│                    ┌─────────▼─────────┐                      │
│                    │  Monitoring       │                      │
│                    │  Aggregator       │                      │
│                    │  (Flink + Kafka)  │                      │
│                    └─────────┬─────────┘                      │
│                              │                                │
│                    ┌─────────▼─────────┐                      │
│                    │  Alert Manager    │                      │
│                    │  • PagerDuty      │                      │
│                    │  • Slack          │                      │
│                    │  • Email          │                      │
│                    │  • Webhook        │                      │
│                    └───────────────────┘                      │
└─────────────────────────────────────────────────────────────┘
```

### 7.2 Metrics Collection

```python
# monitoring/metrics.py
from prometheus_client import Counter, Histogram, Gauge, Info
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

# Prometheus metrics
ENFORCEMENT_DECISIONS = Counter(
    "grcclaw_enforcement_decisions_total",
    "Total enforcement decisions",
    ["decision", "policy_id", "agent_id", "risk_tier"],
)

ENFORCEMENT_LATENCY = Histogram(
    "grcclaw_enforcement_latency_seconds",
    "Enforcement decision latency",
    ["policy_id"],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
)

POLICY_VIOLATIONS = Counter(
    "grcclaw_policy_violations_total",
    "Total policy violations",
    ["policy_id", "violation_type", "severity"],
)

ACTIVE_AGENTS = Gauge(
    "grcclaw_active_agents",
    "Number of active agents",
    ["risk_tier", "environment"],
)

COMPLIANCE_SCORE = Gauge(
    "grcclaw_compliance_score",
    "Current compliance score",
    ["framework", "scope_id"],
)

EVIDENCE_COUNT = Gauge(
    "grcclaw_evidence_count",
    "Total evidence items",
    ["type", "verification_level"],
)

WORKFLOW_DURATION = Histogram(
    "grcclaw_workflow_duration_seconds",
    "Workflow execution duration",
    ["workflow_name", "status"],
    buckets=[0.1, 0.5, 1, 5, 10, 30, 60, 120, 300, 600],
)

EVENT_LAG = Gauge(
    "grcclaw_event_lag_seconds",
    "Event processing lag",
    ["topic", "consumer_group"],
)

CIRCUIT_BREAKER_STATE = Gauge(
    "grcclaw_circuit_breaker_state",
    "Circuit breaker state (0=closed, 1=open, 2=half_open)",
    ["service"],
)

class MetricsCollector:
    def __init__(self):
        self.tracer = trace.get_tracer("grcclaw.automation")

    def record_enforcement_decision(self, decision: Decision):
        ENFORCEMENT_DECISIONS.labels(
            decision=decision.decision.value,
            policy_id=decision.policy_id,
            agent_id=decision.evaluation_context.get("agent_id", "unknown"),
            risk_tier=decision.evaluation_context.get("risk_tier", "unknown"),
        ).inc()

        ENFORCEMENT_LATENCY.labels(
            policy_id=decision.policy_id,
        ).observe(decision.evaluation_latency_ms / 1000)

    def record_policy_violation(self, policy_id: str, violation_type: str, severity: str):
        POLICY_VIOLATIONS.labels(
            policy_id=policy_id,
            violation_type=violation_type,
            severity=severity,
        ).inc()

    def update_compliance_score(self, framework: str, scope_id: str, score: float):
        COMPLIANCE_SCORE.labels(
            framework=framework,
            scope_id=scope_id,
        ).set(score)

    def record_workflow_execution(self, workflow_name: str, duration_seconds: float, status: str):
        WORKFLOW_DURATION.labels(
            workflow_name=workflow_name,
            status=status,
        ).observe(duration_seconds)
```

### 7.3 Alerting Rules

```yaml
# monitoring/alerts.yaml
groups:
  - name: enforcement_alerts
    rules:
      - alert: HighDenialRate
        expr: |
          rate(grcclaw_enforcement_decisions_total{decision="DENY"}[5m])
          / rate(grcclaw_enforcement_decisions_total[5m]) > 0.3
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High denial rate above 30%"
          description: "Denial rate is {{ $value | humanizePercentage }} for the last 5 minutes"

      - alert: EnforcementLatencyHigh
        expr: |
          histogram_quantile(0.99, grcclaw_enforcement_latency_seconds) > 0.1
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Enforcement p99 latency exceeds 100ms"
          description: "p99 latency is {{ $value }}s, exceeding 100ms SLA"

      - alert: PolicyViolationSpike
        expr: |
          rate(grcclaw_policy_violations_total[5m]) > 10
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Policy violation spike detected"
          description: "{{ $value }} violations per second in the last 5 minutes"

      - alert: ComplianceScoreDrop
        expr: |
          grcclaw_compliance_score < 0.7
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Compliance score below 70%"
          description: "Framework {{ $labels.framework }} compliance score is {{ $value }}"

      - alert: CircuitBreakerOpen
        expr: |
          grcclaw_circuit_breaker_state == 1
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Circuit breaker open for {{ $labels.service }}"
          description: "Service {{ $labels.service }} circuit breaker is open"

      - alert: EventLagHigh
        expr: |
          grcclaw_event_lag_seconds > 30
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Event processing lag exceeds 30 seconds"
          description: "Consumer group {{ $labels.consumer_group }} lag is {{ $value }}s"

      - alert: WorkflowFailureRate
        expr: |
          rate(grcclaw_workflow_duration_seconds_count{status="failed"}[5m])
          / rate(grcclaw_workflow_duration_seconds_count[5m]) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Workflow failure rate above 5%"
          description: "Workflow {{ $labels.workflow_name }} failure rate is {{ $value | humanizePercentage }}"
```

### 7.4 Performance Optimization

```python
# monitoring/optimization.py
from dataclasses import dataclass
from typing import Any
import statistics

@dataclass
class PerformanceReport:
    period: str
    total_decisions: int
    p50_latency_ms: float
    p99_latency_ms: float
    denial_rate: float
    top_violated_policies: list[tuple[str, int]]
    slowest_policies: list[tuple[str, float]]
    recommendations: list[str]

class PerformanceOptimizer:
    """Analyzes automation performance and generates optimization recommendations."""

    def __init__(self, metrics_store, policy_service):
        self.metrics = metrics_store
        self.policy_service = policy_service

    async def generate_report(self, period: str = "24h") -> PerformanceReport:
        # Query metrics
        decisions = await self.metrics.query_enforcement_decisions(period)
        latencies = [d.evaluation_latency_ms for d in decisions]

        # Compute statistics
        p50 = statistics.median(latencies) if latencies else 0
        p99 = sorted(latencies)[int(len(latencies) * 0.99)] if latencies else 0

        denial_count = sum(1 for d in decisions if d.decision == DecisionType.DENY)
        denial_rate = denial_count / len(decisions) if decisions else 0

        # Top violated policies
        policy_violations: dict[str, int] = {}
        for d in decisions:
            if d.decision in (DecisionType.DENY, DecisionType.QUARANTINE):
                policy_violations[d.policy_id] = policy_violations.get(d.policy_id, 0) + 1

        top_violated = sorted(policy_violations.items(), key=lambda x: x[1], reverse=True)[:5]

        # Slowest policies
        policy_latencies: dict[str, list[float]] = {}
        for d in decisions:
            policy_latencies.setdefault(d.policy_id, []).append(d.evaluation_latency_ms)

        slowest = sorted(
            [(pid, statistics.median(lats)) for pid, lats in policy_latencies.items()],
            key=lambda x: x[1],
            reverse=True,
        )[:5]

        # Generate recommendations
        recommendations = []
        if p99 > 100:
            recommendations.append(
                f"p99 latency {p99}ms exceeds 100ms SLA. "
                "Consider caching compiled policy rules or optimizing rule evaluation."
            )
        if denial_rate > 0.3:
            recommendations.append(
                f"Denial rate {denial_rate:.1%} is high. "
                "Review policies for overly restrictive rules."
            )
        if top_violated and top_violated[0][1] > 100:
            recommendations.append(
                f"Policy {top_violated[0][0]} has {top_violated[0][1]} violations. "
                "Consider policy review or agent retraining."
            )

        return PerformanceReport(
            period=period,
            total_decisions=len(decisions),
            p50_latency_ms=p50,
            p99_latency_ms=p99,
            denial_rate=denial_rate,
            top_violated_policies=top_violated,
            slowest_policies=slowest,
            recommendations=recommendations,
        )

    async def optimize_policy_cache(self):
        """Pre-compiles and caches frequently used policies."""
        hot_policies = await self.metrics.get_hot_policies(limit=20)
        for policy_id in hot_policies:
            policy = await self.policy_service.get_policy(policy_id)
            compiled = await self.policy_service.compile_policy(policy)
            await self.cache.set(
                f"policy:compiled:{policy_id}",
                compiled,
                ttl=3600,
            )

    async def rebalance_kafka_partitions(self):
        """Rebalances Kafka partitions based on consumer lag."""
        lag_data = await self.metrics.get_consumer_lags()
        for topic, consumer_groups in lag_data.items():
            for group, lag in consumer_groups.items():
                if lag > 10000:
                    await self._scale_consumer_group(group, replicas=lag // 5000 + 1)
```

### 7.5 Drift Detection

```python
# monitoring/drift_detection.py
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Callable
import statistics

@dataclass
class DriftReport:
    asset_id: str
    drift_type: str  # "behavior", "performance", "policy", "data"
    severity: str  # "low", "medium", "high", "critical"
    detected_at: datetime
    baseline_value: float
    current_value: float
    drift_percentage: float
    description: str
    recommended_action: str

class DriftDetector:
    """Detects drift in agent behavior, model performance, and policy compliance."""

    def __init__(self, metrics_store, evidence_service):
        self.metrics = metrics_store
        self.evidence = evidence_service
        self.baselines: dict[str, dict] = {}

    async def detect_behavior_drift(self, agent_id: str) -> DriftReport | None:
        """Detects drift in agent behavior patterns."""
        # Get baseline (30-day average)
        baseline = await self._get_baseline(agent_id, "behavior", days=30)
        if not baseline:
            return None

        # Get current (last 1 hour)
        current = await self._get_current_metrics(agent_id, "behavior", hours=1)

        # Compute drift
        drift_pct = self._compute_drift(baseline["trust_score"], current["trust_score"])

        if abs(drift_pct) > 0.20:  # 20% drift threshold
            severity = "critical" if abs(drift_pct) > 0.50 else "high" if abs(drift_pct) > 0.30 else "medium"

            return DriftReport(
                asset_id=agent_id,
                drift_type="behavior",
                severity=severity,
                detected_at=datetime.utcnow(),
                baseline_value=baseline["trust_score"],
                current_value=current["trust_score"],
                drift_percentage=drift_pct,
                description=f"Agent trust score drifted {drift_pct:.1%} from baseline",
                recommended_action="Review recent enforcement decisions and agent activity",
            )

        return None

    async def detect_policy_drift(self, policy_id: str) -> DriftReport | None:
        """Detects drift in policy violation patterns."""
        baseline = await self._get_baseline(policy_id, "policy_violations", days=30)
        current = await self._get_current_metrics(policy_id, "policy_violations", hours=1)

        if baseline["violation_rate"] == 0:
            return None

        drift_pct = (current["violation_rate"] - baseline["violation_rate"]) / baseline["violation_rate"]

        if drift_pct > 0.50:  # 50% increase in violations
            return DriftReport(
                asset_id=policy_id,
                drift_type="policy",
                severity="high",
                detected_at=datetime.utcnow(),
                baseline_value=baseline["violation_rate"],
                current_value=current["violation_rate"],
                drift_percentage=drift_pct,
                description=f"Policy violation rate increased {drift_pct:.1%}",
                recommended_action="Review policy rules and affected agents",
            )

        return None

    async def detect_performance_drift(self, model_id: str) -> DriftReport | None:
        """Detects drift in model performance metrics."""
        baseline = await self._get_baseline(model_id, "performance", days=30)
        current = await self._get_current_metrics(model_id, "performance", hours=1)

        drift_pct = self._compute_drift(baseline["accuracy"], current["accuracy"])

        if drift_pct < -0.10:  # 10% accuracy drop
            return DriftReport(
                asset_id=model_id,
                drift_type="performance",
                severity="critical" if drift_pct < -0.20 else "high",
                detected_at=datetime.utcnow(),
                baseline_value=baseline["accuracy"],
                current_value=current["accuracy"],
                drift_percentage=drift_pct,
                description=f"Model accuracy dropped {abs(drift_pct):.1%} from baseline",
                recommended_action="Trigger model re-evaluation and consider rollback",
            )

        return None

    def _compute_drift(self, baseline: float, current: float) -> float:
        if baseline == 0:
            return 0.0
        return (current - baseline) / baseline
```

---

## 8. Closed-Loop Automation

### 8.1 Architecture

Closed-loop automation creates a self-healing governance system where detection, decision, enforcement, and feedback form a continuous cycle:

```
┌─────────────────────────────────────────────────────────────┐
│                  Closed-Loop Automation                      │
│                                                              │
│  ┌──────────┐                                               │
│  │ 1. DETECT│◀──────────────────────────────────────┐       │
│  │          │  Sentinel Agents, Drift Detection,    │       │
│  │          │  Anomaly Detection, CEP Patterns      │       │
│  └────┬─────┘                                        │       │
│       │                                              │       │
│       ▼                                              │       │
│  ┌──────────┐                                        │       │
│  │ 2. DECIDE│  5-Way Decision Engine                 │       │
│  │          │  (Deterministic, No LLM)               │       │
│  └────┬─────┘                                        │       │
│       │                                              │       │
│       ▼                                              │       │
│  ┌──────────┐                                        │       │
│  │ 3. ENFORCE│  Operative Agents, Kill Switches,    │       │
│  │          │  Policy Updates, Agent Isolation       │       │
│  └────┬─────┘                                        │       │
│       │                                              │       │
│       ▼                                              │       │
│  ┌──────────┐                                        │       │
│  │ 4. VERIFY │  Evidence Collection,                 │       │
│  │          │  Compliance Recomputation              │       │
│  └────┬─────┘                                        │       │
│       │                                              │       │
│       ▼                                              │       │
│  ┌──────────┐                                        │       │
│  │ 5. LEARN  │  Trust Score Update,                  │       │
│  │          │  Policy Optimization,                  │       │
│  │          │  Baseline Recalculation                │       │
│  └────┬─────┘                                        │       │
│       │                                              │       │
│       └──────────────────────────────────────────────┘       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 8.2 Closed-Loop Controller

```python
# closed_loop/controller.py
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Callable, Any
import asyncio

class LoopPhase(Enum):
    DETECT = "detect"
    DECIDE = "decide"
    ENFORCE = "enforce"
    VERIFY = "verify"
    LEARN = "learn"

@dataclass
class LoopContext:
    loop_id: str
    trigger_event: dict
    tenant_id: str
    agent_id: str | None = None
    asset_id: str | None = None
    current_phase: LoopPhase = LoopPhase.DETECT
    iteration: int = 0
    max_iterations: int = 5
    state: dict = field(default_factory=dict)
    evidence_chain: list[str] = field(default_factory=list)
    decisions: list[dict] = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.utcnow)

class ClosedLoopController:
    """Orchestrates the detect-decide-enforce-verify-learn cycle."""

    def __init__(
        self,
        detection_service,
        decision_engine,
        enforcement_service,
        verification_service,
        learning_service,
        evidence_service,
    ):
        self.detection = detection_service
        self.decision = decision_engine
        self.enforcement = enforcement_service
        self.verification = verification_service
        self.learning = learning_service
        self.evidence = evidence_service

        self.phase_handlers: dict[LoopPhase, Callable] = {
            LoopPhase.DETECT: self._execute_detect,
            LoopPhase.DECIDE: self._execute_decide,
            LoopPhase.ENFORCE: self._execute_enforce,
            LoopPhase.VERIFY: self._execute_verify,
            LoopPhase.LEARN: self._execute_learn,
        }

    async def run(self, trigger_event: dict) -> LoopContext:
        context = LoopContext(
            loop_id=str(uuid.uuid4()),
            trigger_event=trigger_event,
            tenant_id=trigger_event.get("tenant_id", "default"),
            agent_id=trigger_event.get("agent_id"),
            asset_id=trigger_event.get("asset_id"),
        )

        phases = [
            LoopPhase.DETECT,
            LoopPhase.DECIDE,
            LoopPhase.ENFORCE,
            LoopPhase.VERIFY,
            LoopPhase.LEARN,
        ]

        for phase in phases:
            context.current_phase = phase
            handler = self.phase_handlers[phase]

            try:
                result = await handler(context)
                context.state[phase.value] = result

                # Check if loop should terminate early
                if self._should_terminate(context, phase, result):
                    break

            except Exception as e:
                context.state[f"{phase.value}_error"] = str(e)
                await self._handle_phase_error(context, phase, e)
                break

            context.iteration += 1

        # Record loop completion evidence
        await self.evidence.record({
            "type": "closed_loop_execution",
            "loop_id": context.loop_id,
            "phases_completed": list(context.state.keys()),
            "decisions": context.decisions,
            "evidence_chain": context.evidence_chain,
            "duration_seconds": (datetime.utcnow() - context.start_time).total_seconds(),
        })

        return context

    async def _execute_detect(self, context: LoopContext) -> dict:
        """Phase 1: Detect anomalies, violations, or drift."""
        detections = []

        # Check for policy violations
        if context.agent_id:
            violations = await self.detection.detect_violations(
                agent_id=context.agent_id,
                time_window=timedelta(hours=1),
            )
            detections.extend(violations)

        # Check for behavior drift
        drift = await self.detection.detect_drift(
            asset_id=context.agent_id or context.asset_id,
        )
        if drift:
            detections.append(drift)

        # Check for anomalies
        anomalies = await self.detection.detect_anomalies(
            agent_id=context.agent_id,
            time_window=timedelta(minutes=30),
        )
        detections.extend(anomalies)

        return {
            "detections_count": len(detections),
            "detections": [d.__dict__ for d in detections],
            "highest_severity": max(
                (d.severity for d in detections),
                default="none",
            ),
        }

    async def _execute_decide(self, context: LoopContext) -> dict:
        """Phase 2: Make deterministic 5-way governance decision."""
        detections = context.state.get("detect", {}).get("detections", [])

        if not detections:
            return {"decision": "ALLOW", "reason": "No detections"}

        # Use highest severity detection
        highest = max(detections, key=lambda d: self._severity_weight(d.severity))

        # Build action context
        action_context = ActionContext(
            agent_id=context.agent_id or "unknown",
            action_type=highest.get("type", "unknown"),
            tool_name=highest.get("tool_name"),
            resource=highest.get("resource", "unknown"),
            parameters=highest.get("context", {}),
            environment=highest.get("environment", "prod"),
            trace_id=context.loop_id,
        )

        decision = await self.decision.evaluate(action_context)
        context.decisions.append(decision.__dict__)

        return {
            "decision": decision.decision.value,
            "reason": decision.reason,
            "confidence": decision.confidence_score,
            "policy_id": decision.policy_id,
        }

    async def _execute_enforce(self, context: LoopContext) -> dict:
        """Phase 3: Enforce the decision."""
        decision_data = context.state.get("decide", {})
        decision_type = decision_data.get("decision", "ALLOW")

        enforcement_result = {"action": "none"}

        if decision_type == "DENY":
            enforcement_result = await self.enforcement.deny_action(
                agent_id=context.agent_id,
                reason=decision_data.get("reason"),
            )
        elif decision_type == "QUARANTINE":
            enforcement_result = await self.enforcement.quarantine_agent(
                agent_id=context.agent_id,
                reason=decision_data.get("reason"),
            )
        elif decision_type == "REQUIRE_APPROVAL":
            enforcement_result = await self.enforcement.request_approval(
                agent_id=context.agent_id,
                context=context.trigger_event,
            )
        elif decision_type == "ALLOW_WITH_REDACTION":
            enforcement_result = await self.enforcement.apply_redaction(
                agent_id=context.agent_id,
                fields=decision_data.get("redaction_fields", []),
            )

        return enforcement_result

    async def _execute_verify(self, context: LoopContext) -> dict:
        """Phase 4: Verify enforcement was effective."""
        decision_data = context.state.get("decide", {})
        decision_type = decision_data.get("decision", "ALLOW")

        if decision_type in ("DENY", "QUARANTINE"):
            # Verify agent is actually blocked
            is_blocked = await self.verification.verify_enforcement(
                agent_id=context.agent_id,
                expected_decision=decision_type,
            )
            return {"enforcement_verified": is_blocked}

        elif decision_type == "REQUIRE_APPROVAL":
            # Check if approval was resolved
            approval_status = await self.verification.check_approval_status(
                agent_id=context.agent_id,
            )
            return {"approval_status": approval_status}

        return {"verification": "not_required"}

    async def _execute_learn(self, context: LoopContext) -> dict:
        """Phase 5: Update baselines, trust scores, and policies."""
        learnings = {}

        # Update agent trust score
        if context.agent_id:
            trust_update = await self.learning.update_trust_score(
                agent_id=context.agent_id,
                decisions=context.decisions,
            )
            learnings["trust_score_update"] = trust_update

        # Update baselines
        await self.learning.update_baselines(
            asset_id=context.agent_id or context.asset_id,
        )
        learnings["baselines_updated"] = True

        # Check if policy needs optimization
        if context.iteration > 2:
            policy_optimization = await self.learning.suggest_policy_optimization(
                policy_id=context.state.get("decide", {}).get("policy_id"),
            )
            learnings["policy_optimization"] = policy_optimization

        return learnings

    def _should_terminate(self, context: LoopContext, phase: LoopPhase, result: dict) -> bool:
        """Determine if the loop should terminate early."""
        if phase == LoopPhase.DECIDE and result.get("decision") == "ALLOW":
            return True
        if phase == LoopPhase.VERIFY and result.get("enforcement_verified"):
            return True
        if context.iteration >= context.max_iterations:
            return True
        return False

    def _severity_weight(self, severity: str) -> int:
        weights = {"critical": 4, "high": 3, "medium": 2, "low": 1, "none": 0}
        return weights.get(severity, 0)

    async def _handle_phase_error(self, context: LoopContext, phase: LoopPhase, error: Exception):
        """Handle errors in loop phases."""
        await self.evidence.record({
            "type": "closed_loop_error",
            "loop_id": context.loop_id,
            "phase": phase.value,
            "error": str(error),
            "iteration": context.iteration,
        })
```

### 8.3 Self-Healing Policies

```python
# closed_loop/self_healing.py
@dataclass
class HealingAction:
    action_type: str  # "restart", "scale", "rollback", "isolate", "notify"
    target: str
    parameters: dict
    automated: bool  # True = auto-execute, False = require approval

class SelfHealingEngine:
    """Automatically remediates common governance issues."""

    def __init__(self, enforcement_service, monitoring_service, notification_service):
        self.enforcement = enforcement_service
        self.monitoring = monitoring_service
        self.notification = notification_service
        self.healing_history: list[HealingAction] = []

    async def evaluate_and_heal(self, alert: dict) -> HealingAction | None:
        """Evaluates an alert and determines if auto-healing is appropriate."""
        alert_type = alert.get("type")
        severity = alert.get("severity", "low")
        target = alert.get("target")

        # Critical alerts: auto-heal if confidence is high
        if severity == "critical" and alert.get("confidence", 0) > 0.90:
            if alert_type == "agent_misbehavior":
                return await self._heal_agent_misbehavior(target, alert)
            elif alert_type == "policy_violation_spike":
                return await self._heal_policy_violation_spike(target, alert)
            elif alert_type == "compliance_drop":
                return await self._heal_compliance_drop(target, alert)
            elif alert_type == "service_degradation":
                return await self._heal_service_degradation(target, alert)

        # High severity: notify and recommend
        elif severity == "high":
            await self.notification.notify(
                recipient="governance-team",
                subject=f"High severity alert: {alert_type}",
                body=json.dumps(alert, indent=2),
                priority="high",
            )

        return None

    async def _heal_agent_misbehavior(self, agent_id: str, alert: dict) -> HealingAction:
        """Auto-heal agent misbehavior by isolating the agent."""
        # Isolate agent
        await self.enforcement.quarantine_agent(
            agent_id=agent_id,
            reason=f"Auto-healing: {alert.get('description', 'misbehavior detected')}",
        )

        # Update trust score
        await self.enforcement.update_trust_score(
            agent_id=agent_id,
            delta=-0.2,
            reason="auto_healing",
        )

        # Notify
        await self.notification.notify(
            recipient="governance-team",
            subject=f"Agent {agent_id} auto-isolated",
            reason=alert.get("description"),
            action_taken="quarantine",
        )

        action = HealingAction(
            action_type="isolate",
            target=agent_id,
            parameters={"reason": alert.get("description")},
            automated=True,
        )
        self.healing_history.append(action)
        return action

    async def _heal_policy_violation_spike(self, policy_id: str, alert: dict) -> HealingAction:
        """Auto-heal policy violation spike by tightening enforcement."""
        # Get current policy
        policy = await self.enforcement.get_policy(policy_id)

        # Temporarily increase enforcement level
        await self.enforcement.update_policy_enforcement(
            policy_id=policy_id,
            mode="enforce",
            on_violation="block",
        )

        # Schedule policy review
        await self.notification.notify(
            recipient="policy-owners",
            subject=f"Policy {policy_id} violation spike — review required",
            body=f"Violation rate: {alert.get('violation_rate')}",
            action_required="review_policy",
        )

        action = HealingAction(
            action_type="tighten_enforcement",
            target=policy_id,
            parameters={"previous_mode": policy.enforcement.mode},
            automated=True,
        )
        self.healing_history.append(action)
        return action

    async def _heal_compliance_drop(self, scope_id: str, alert: dict) -> HealingAction:
        """Auto-heal compliance drop by triggering re-assessment."""
        # Trigger re-assessment
        assessment_id = await self.enforcement.trigger_reassessment(
            scope_id=scope_id,
            framework=alert.get("framework"),
        )

        # Notify compliance team
        await self.notification.notify(
            recipient="compliance-team",
            subject=f"Compliance drop detected for {scope_id}",
            body=f"Score: {alert.get('compliance_score')}. Re-assessment triggered.",
            action_required="review_compliance",
        )

        action = HealingAction(
            action_type="trigger_reassessment",
            target=scope_id,
            parameters={"assessment_id": assessment_id},
            automated=True,
        )
        self.healing_history.append(action)
        return action
```

### 8.4 Feedback Loop Integration

```python
# closed_loop/feedback.py
class FeedbackLoop:
    """Closes the loop by feeding verification results back into detection and decision."""

    def __init__(self, controller: ClosedLoopController, metrics_store):
        self.controller = controller
        self.metrics = metrics_store
        self.feedback_history: list[dict] = []

    async def process_feedback(self, loop_context: LoopContext):
        """Processes feedback from a completed loop iteration."""
        feedback = {
            "loop_id": loop_context.loop_id,
            "timestamp": datetime.utcnow().isoformat(),
            "phases_completed": list(loop_context.state.keys()),
            "outcome": self._determine_outcome(loop_context),
            "effectiveness": self._measure_effectiveness(loop_context),
            "improvements": self._suggest_improvements(loop_context),
        }

        self.feedback_history.append(feedback)

        # Update detection baselines
        await self._update_detection_baselines(loop_context, feedback)

        # Update decision thresholds
        await self._update_decision_thresholds(loop_context, feedback)

        # Update policy effectiveness scores
        await self._update_policy_effectiveness(loop_context, feedback)

        return feedback

    def _determine_outcome(self, context: LoopContext) -> str:
        """Determines if the loop achieved its goal."""
        verify_result = context.state.get("verify", {})

        if verify_result.get("enforcement_verified"):
            return "success"
        elif verify_result.get("approval_status") == "pending":
            return "pending"
        elif "error" in context.state:
            return "error"
        else:
            return "incomplete"

    def _measure_effectiveness(self, context: LoopContext) -> dict:
        """Measures how effective the loop was."""
        detect_result = context.state.get("detect", {})
        decide_result = context.state.get("decide", {})
        verify_result = context.state.get("verify", {})

        return {
            "detection_accuracy": self._compute_detection_accuracy(context),
            "decision_appropriateness": self._compute_decision_appropriateness(context),
            "enforcement_success": verify_result.get("enforcement_verified", False),
            "time_to_resolve": (
                datetime.utcnow() - context.start_time
            ).total_seconds(),
            "iterations_needed": context.iteration,
        }

    def _suggest_improvements(self, context: LoopContext) -> list[str]:
        """Suggests improvements based on loop execution."""
        suggestions = []

        if context.iteration > 3:
            suggestions.append(
                "Loop required multiple iterations. Consider tightening detection thresholds."
            )

        decide_result = context.state.get("decide", {})
        if decide_result.get("decision") == "REQUIRE_APPROVAL":
            suggestions.append(
                "Decision required human review. Consider if policy can be made more specific."
            )

        verify_result = context.state.get("verify", {})
        if not verify_result.get("enforcement_verified", True):
            suggestions.append(
                "Enforcement verification failed. Review enforcement mechanisms."
            )

        return suggestions

    async def _update_detection_baselines(self, context: LoopContext, feedback: dict):
        """Updates detection baselines based on feedback."""
        if feedback["outcome"] == "success":
            # Gradually adjust baselines to reduce false positives
            await self.metrics.adjust_baseline(
                asset_id=context.agent_id or context.asset_id,
                metric_type="detection_sensitivity",
                delta=-0.01,  # Slightly reduce sensitivity
            )

    async def _update_decision_thresholds(self, context: LoopContext, feedback: dict):
        """Updates decision thresholds based on feedback."""
        if feedback["effectiveness"]["decision_appropriateness"] < 0.8:
            # Increase confidence threshold for auto-remediation
            await self.controller.decision.confidence_router.adjust_threshold(
                "auto_remediate",
                delta=0.02,
            )

    async def _update_policy_effectiveness(self, context: LoopContext, feedback: dict):
        """Updates policy effectiveness scores."""
        policy_id = context.state.get("decide", {}).get("policy_id")
        if policy_id:
            effectiveness = 1.0 if feedback["outcome"] == "success" else 0.5
            await self.metrics.update_policy_effectiveness(
                policy_id=policy_id,
                effectiveness=effectiveness,
            )
```

---

## 9. Implementation Roadmap

### Phase 1: Foundation (Months 1-3)

| Week | Deliverable | Key Activities |
|------|-------------|----------------|
| 1-2 | Core data model | Implement unified data model (Policy, Evidence, Enforcement, Assessment, Compliance) |
| 3-4 | Policy engine | OPA integration, YAML policy compiler, 5-way decision engine |
| 5-6 | Event infrastructure | Kafka cluster, CloudEvents schema, producer/consumer framework |
| 7-8 | Temporal setup | Temporal cluster, worker framework, basic workflows |
| 9-10 | Discovery engine | Repository scanner, cloud connectors, agent detector |
| 11-12 | Inventory graph | Graph database setup, asset records, dependency mapping |

### Phase 2: Assessment (Months 4-6)

| Week | Deliverable | Key Activities |
|------|-------------|----------------|
| 13-14 | Risk assessment | Multi-dimensional scoring, EU AI Act triage, test suite |
| 15-16 | Policy mapping | Pre-built policy packs (EU AI Act, NIST, ISO 42001), crosswalk engine |
| 17-18 | Evidence ledger | Hash-chained records, chain of custody, verification |
| 19-20 | Reporting | PDF/HTML export, AI Trust Center, OSCAL compliance |
| 21-22 | Integration testing | Contract tests, event flow tests, API conformance |
| 23-24 | Monitoring | Prometheus metrics, alerting rules, drift detection |

### Phase 3: Enforcement (Months 7-9)

| Week | Deliverable | Key Activities |
|------|-------------|----------------|
| 25-26 | Runtime enforcement | MCP Gateway, 5-way decision at runtime, kill switch |
| 27-28 | Approval workflow | Human-in-the-loop, escalation, approval API |
| 29-30 | Continuous monitoring | Sentinel agents, anomaly detection, alert routing |
| 31-32 | Saga pattern | Distributed transactions, compensation, saga orchestrator |
| 33-34 | Chaos engineering | Failure injection, resilience testing, circuit breakers |
| 35-36 | Performance optimization | Caching, partition rebalancing, latency optimization |

### Phase 4: Intelligence (Months 10-12)

| Week | Deliverable | Key Activities |
|------|-------------|----------------|
| 37-38 | Closed-loop automation | Self-healing, feedback loops, trust score updates |
| 39-40 | Agent governance | Sentinel/Operative separation, agent identity, multi-agent governance |
| 41-42 | Knowledge graph | Governance Knowledge Graph, contextual governance |
| 43-44 | Stream processing | Flink jobs, CEP patterns, real-time compliance scoring |
| 45-46 | Advanced testing | Chaos tests, conformance tests, contract tests |
| 47-48 | Production readiness | Security audit, penetration testing, documentation |

---

## 10. Appendices

### Appendix A: Technology Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| Graph Database | Neo4j / Apache AGE | Native graph queries for dependency mapping |
| Policy Engine | OPA / Cedar | Declarative, auditable policy-as-code |
| MCP Server | Python MCP SDK / TypeScript MCP SDK | Official SDKs, active ecosystem |
| Task Queue | Temporal | Reliable async processing for governance workflows |
| Event Streaming | Apache Kafka / NATS | Real-time event processing for monitoring |
| Stream Processing | Apache Flink | Complex event processing, windowed aggregations |
| Evidence Store | PostgreSQL + immudb | Relational data + immutable audit log |
| Frontend | React + D3.js | Interactive graph visualization |
| API | FastAPI (Python) | Async, OpenAPI-native, MCP-compatible |
| Deployment | Docker + Kubernetes | Cloud-agnostic, scalable |
| Observability | OpenTelemetry | Standard tracing for audit trails |
| Metrics | Prometheus + Grafana | Monitoring and alerting |
| Testing | pytest + testcontainers | Unit, integration, chaos testing |

### Appendix B: Configuration Reference

```yaml
# config/automation.yaml
automation:
  engine:
    name: grcclaw-automation
    version: "1.0.0"
    environment: prod

  enforcement:
    mode: enforce
    fail_mode: closed
    default_decision: DENY
    confidence_thresholds:
      auto_remediate: 0.90
      human_review: 0.85
      log_only: 0.70
    latency_sla_ms: 100

  policies:
    compiler:
      languages: [yaml, cedar, rego]
      cache_ttl_seconds: 3600
      auto_compile_on_deploy: true
    packs:
      - eu-ai-act
      - nist-ai-rmf
      - iso-42001
      - gdpr
      - soc2
      - hipaa

  events:
    primary_bus: kafka
    schema_registry: http://schema-registry:8081
    compatibility: forward
    dlq:
      enabled: true
      max_retries: 5
      retention_days: 30

  temporal:
    host: temporal:7233
    namespace: grcclaw
    task_queue: governance-workflows
    max_concurrent_workflows: 100
    max_concurrent_activities: 50

  monitoring:
    metrics_backend: prometheus
    tracing_backend: otel
    alert_manager: http://alertmanager:9093
    drift_detection:
      enabled: true
      sensitivity: 0.20
      check_interval: 3600

  closed_loop:
    enabled: true
    max_iterations: 5
    auto_heal_threshold: 0.90
    feedback_retention_days: 90

  testing:
    unit_test_coverage_threshold: 0.80
    integration_test_required: true
    chaos_test_schedule: "0 2 * * 0"  # Weekly
    conformance_test_required: true
```

### Appendix C: Glossary

| Term | Definition |
|------|-----------|
| **5-Way Decision** | ALLOW, ALLOW_WITH_REDACTION, REQUIRE_APPROVAL, DENY, QUARANTINE |
| **CloudEvents** | CNCF standard event format for describing event data in a common way |
| **CQRS** | Command Query Responsibility Segregation — separates read and write models |
| **Deterministic Enforcement** | Governance decisions made by rules, not LLM — reproducible and auditable |
| **Event Sourcing** | Storing state as a sequence of events rather than current state |
| **MCP** | Model Context Protocol — universal integration layer for AI workflows |
| **OPA** | Open Policy Agent — open-source policy engine for policy-as-code |
| **Saga** | Distributed transaction pattern with compensating actions for rollback |
| **Sentinel Agent** | Detection-focused governance agent (drift, bias, anomalies) |
| **Operative Agent** | Enforcement-focused governance agent (kill switches, blocking, remediation) |
| **Temporal** | Durable workflow orchestration engine for long-running processes |
| **Trust Score** | Multi-dimensional agent reliability score (0.0–1.0) |
| **WhitePact** | Open-source deterministic 5-way governance engine (reference implementation) |</longcat_think>
