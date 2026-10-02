"""Planner-Executor-Critic pattern for GRC Marketing Core.

Implements a three-phase agent execution pattern:
1. Planner: Decomposes tasks into actionable steps
2. Executor: Runs each step with tool invocations
3. Critic: Evaluates results and provides feedback for improvement
"""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any, TypeVar

import structlog

from .base import AgentContext, AgentResult, BaseAgent, ToolError

logger = structlog.get_logger(__name__)

T = TypeVar("T")


class StepStatus(str, Enum):
    """Status of a plan step."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class PlanStep:
    """A single step in an execution plan."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    description: str = ""
    tool_name: str | None = None
    parameters: dict[str, Any] = field(default_factory=dict)
    dependencies: list[str] = field(default_factory=list)
    status: StepStatus = StepStatus.PENDING
    result: Any = None
    error: str | None = None
    retry_count: int = 0
    max_retries: int = 3
    started_at: datetime | None = None
    completed_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def duration_ms(self) -> float | None:
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds() * 1000
        return None


@dataclass
class ExecutionResult:
    """Result of executing a plan step."""

    step_id: str
    success: bool
    data: Any = None
    error: str | None = None
    execution_time_ms: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CriticFeedback:
    """Feedback from the critic phase."""

    approved: bool
    score: float = 0.0
    feedback: str = ""
    suggestions: list[str] = field(default_factory=list)
    should_retry: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


class Planner(BaseAgent[T]):
    """Agent that decomposes high-level tasks into actionable plan steps."""

    def __init__(
        self,
        name: str = "planner",
        description: str = "Plans task decomposition",
        max_steps: int = 20,
        **kwargs: Any,
    ) -> None:
        super().__init__(name=name, description=description, **kwargs)
        self.max_steps = max_steps

    async def create_plan(self, task: str, context: AgentContext) -> list[PlanStep]:
        """Create an execution plan for the given task.

        Override this method to implement custom planning logic.
        """
        result = await self.run(task, context)
        if not result.success or not result.data:
            return []
        if isinstance(result.data, list):
            return [s if isinstance(s, PlanStep) else PlanStep(**s) for s in result.data]
        return []

    async def run(self, input_data: T, context: AgentContext) -> AgentResult[list[PlanStep]]:
        """Default planning implementation — override in subclasses."""
        return AgentResult(
            success=True,
            data=[PlanStep(description=str(input_data))],
        )


class Executor(BaseAgent[T]):
    """Agent that executes plan steps using available tools."""

    def __init__(
        self,
        name: str = "executor",
        description: str = "Executes plan steps",
        **kwargs: Any,
    ) -> None:
        super().__init__(name=name, description=description, **kwargs)

    async def execute_step(
        self,
        step: PlanStep,
        context: AgentContext,
    ) -> ExecutionResult:
        """Execute a single plan step."""
        step.status = StepStatus.IN_PROGRESS
        step.started_at = datetime.now(UTC)
        start = datetime.now(UTC)
        try:
            if step.tool_name:
                data = await self.execute_tool(step.tool_name, **step.parameters)
            else:
                data = step.parameters
            step.status = StepStatus.COMPLETED
            step.result = data
            step.completed_at = datetime.now(UTC)
            elapsed = (datetime.now(UTC) - start).total_seconds() * 1000
            return ExecutionResult(
                step_id=step.id,
                success=True,
                data=data,
                execution_time_ms=elapsed,
            )
        except (ToolError, Exception) as exc:
            step.status = StepStatus.FAILED
            step.error = str(exc)
            step.completed_at = datetime.now(UTC)
            elapsed = (datetime.now(UTC) - start).total_seconds() * 1000
            return ExecutionResult(
                step_id=step.id,
                success=False,
                error=str(exc),
                execution_time_ms=elapsed,
            )

    async def execute_plan(
        self,
        steps: list[PlanStep],
        context: AgentContext,
    ) -> list[ExecutionResult]:
        """Execute all steps respecting dependencies."""
        results: list[ExecutionResult] = []
        completed: set[str] = set()
        remaining = list(steps)

        while remaining:
            ready = [
                s for s in remaining
                if all(dep in completed for dep in s.dependencies)
            ]
            if not ready:
                logger.warning("circular_dependency_detected", remaining=len(remaining))
                break
            batch = await asyncio.gather(
                *[self.execute_step(step, context) for step in ready]
            )
            for step, result in zip(ready, batch):
                results.append(result)
                if result.success:
                    completed.add(step.id)
                remaining.remove(step)
        return results

    async def run(self, input_data: T, context: AgentContext) -> AgentResult[list[ExecutionResult]]:
        """Execute a list of plan steps."""
        if not isinstance(input_data, list):
            return AgentResult(success=False, error="Expected list of PlanStep")
        steps = [s if isinstance(s, PlanStep) else PlanStep(**s) for s in input_data]
        results = await self.execute_plan(steps, context)
        return AgentResult(success=True, data=results)


class Critic(BaseAgent[T]):
    """Agent that evaluates execution results and provides feedback."""

    def __init__(
        self,
        name: str = "critic",
        description: str = "Evaluates execution results",
        approval_threshold: float = 0.7,
        **kwargs: Any,
    ) -> None:
        super().__init__(name=name, description=description, **kwargs)
        self.approval_threshold = approval_threshold

    async def evaluate(
        self,
        plan: list[PlanStep],
        results: list[ExecutionResult],
        context: AgentContext,
    ) -> CriticFeedback:
        """Evaluate execution results and provide feedback.

        Override this method to implement custom evaluation logic.
        """
        if not results:
            return CriticFeedback(approved=False, feedback="No results to evaluate")

        success_count = sum(1 for r in results if r.success)
        total = len(results)
        score = success_count / total if total > 0 else 0.0
        approved = score >= self.approval_threshold

        suggestions: list[str] = []
        if not approved:
            failed = [r for r in results if not r.success]
            suggestions.append(f"Retry {len(failed)} failed steps")
            for f in failed[:3]:
                suggestions.append(f"Step {f.step_id}: {f.error}")

        return CriticFeedback(
            approved=approved,
            score=score,
            feedback=f"Success rate: {score:.0%}",
            suggestions=suggestions,
            should_retry=not approved,
        )

    async def run(self, input_data: T, context: AgentContext) -> AgentResult[CriticFeedback]:
        """Evaluate execution results."""
        if not isinstance(input_data, dict):
            return AgentResult(success=False, error="Expected dict with 'plan' and 'results'")
        plan = input_data.get("plan", [])
        results = input_data.get("results", [])
        feedback = await self.evaluate(plan, results, context)
        return AgentResult(success=True, data=feedback)


class PlannerExecutorCritic:
    """Orchestrates the Planner-Executor-Critic pattern.

    Coordinates the three phases with retry logic and feedback loops.
    """

    def __init__(
        self,
        planner: Planner[Any],
        executor: Executor[Any],
        critic: Critic[Any],
        max_retries: int = 3,
    ) -> None:
        self.planner = planner
        self.executor = executor
        self.critic = critic
        self.max_retries = max_retries
        self._logger = logger.bind(component="pec")

    async def execute(
        self,
        task: str,
        context: AgentContext | None = None,
    ) -> AgentResult[Any]:
        """Execute a task through the full Planner-Executor-Critic pipeline."""
        ctx = context or AgentContext()
        all_results: list[ExecutionResult] = []

        for attempt in range(self.max_retries):
            self._logger.info("pec_attempt", attempt=attempt + 1)

            # Phase 1: Plan
            plan_result = await self.planner.create_plan(task, ctx)
            if not plan_result:
                return AgentResult(success=False, error="Planning failed")
            steps = plan_result if isinstance(plan_result, list) else [plan_result]

            # Phase 2: Execute
            exec_results = await self.executor.execute_plan(steps, ctx)
            all_results.extend(exec_results)

            # Phase 3: Critic
            critic_result = await self.critic.evaluate(steps, exec_results, ctx)
            if critic_result.approved:
                return AgentResult(
                    success=True,
                    data={
                        "plan": steps,
                        "results": exec_results,
                        "feedback": critic_result,
                    },
                    metadata={"attempts": attempt + 1},
                )

            if not critic_result.should_retry:
                break

            task = f"{task}\nPrevious attempt feedback: {critic_result.feedback}"

        return AgentResult(
            success=False,
            error=f"Failed after {self.max_retries} attempts",
            data={"results": all_results},
        )
