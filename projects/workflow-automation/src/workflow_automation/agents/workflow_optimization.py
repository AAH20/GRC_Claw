"""Workflow Optimization Agent - analyzes and optimizes marketing workflows."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any

import structlog
from pydantic import BaseModel, Field

from workflow_automation.agents.workflow_discovery import (
    DiscoveredWorkflow,
    WorkflowDiscoveryAgent,
)

logger = structlog.get_logger(__name__)


class OptimizationType(StrEnum):
    """Types of optimizations that can be suggested."""

    PERFORMANCE = "performance"
    COST_REDUCTION = "cost_reduction"
    RELIABILITY = "reliability"
    SCALABILITY = "scalability"
    MAINTAINABILITY = "maintainability"


class OptimizationPriority(StrEnum):
    """Priority levels for optimization suggestions."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Bottleneck(BaseModel):
    """Represents a detected bottleneck in a workflow."""

    bottleneck_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    step_name: str
    description: str
    severity: OptimizationPriority
    impact_description: str
    metrics: dict[str, float] = Field(default_factory=dict)


class OptimizationSuggestion(BaseModel):
    """A suggestion for optimizing a workflow."""

    suggestion_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workflow_id: str
    title: str
    description: str
    optimization_type: OptimizationType
    priority: OptimizationPriority
    affected_steps: list[str] = Field(default_factory=list)
    expected_improvement: str = ""
    implementation_steps: list[str] = Field(default_factory=list)
    estimated_effort: str = "medium"  # low, medium, high
    created_at: datetime = Field(default_factory=datetime.utcnow)


class OptimizationReport(BaseModel):
    """Complete optimization report for a workflow."""

    report_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workflow_id: str
    workflow_name: str
    bottlenecks: list[Bottleneck] = Field(default_factory=list)
    suggestions: list[OptimizationSuggestion] = Field(default_factory=list)
    overall_score: float = Field(default=0.0, ge=0.0, le=100.0)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class OptimizationRequest(BaseModel):
    """Request to optimize a workflow."""

    workflow_id: str = ""
    focus_areas: list[OptimizationType] = Field(default_factory=list)
    include_low_priority: bool = False
    max_suggestions: int = Field(default=10, ge=1, le=50)


@dataclass
class WorkflowOptimizationAgent:
    """Agent responsible for analyzing and optimizing marketing workflows.

    This agent uses AI to identify bottlenecks, suggest improvements,
    and optimize workflow performance, cost, and reliability.
    """

    discovery_agent: WorkflowDiscoveryAgent = field(
        default_factory=WorkflowDiscoveryAgent
    )
    _optimization_history: dict[str, list[OptimizationReport]] = field(
        default_factory=dict
    )
    _is_initialized: bool = False

    async def initialize(self) -> None:
        """Initialize the optimization agent."""
        logger.info("Initializing WorkflowOptimizationAgent")
        await self.discovery_agent.initialize()
        self._is_initialized = True

    async def optimize(self, request: OptimizationRequest) -> OptimizationReport:
        """Analyze a workflow and generate optimization suggestions.

        Args:
            request: Optimization request with parameters.

        Returns:
            OptimizationReport with bottlenecks and suggestions.

        Raises:
            RuntimeError: If the agent is not initialized.
            ValueError: If the workflow is not found.
        """
        if not self._is_initialized:
            raise RuntimeError("Agent not initialized. Call initialize() first.")

        workflow = await self.discovery_agent.get_workflow(request.workflow_id)
        if not workflow:
            raise ValueError(f"Workflow not found: {request.workflow_id}")

        logger.info(
            "Starting workflow optimization",
            workflow_id=request.workflow_id,
            focus_areas=[f.value for f in request.focus_areas],
        )

        # Analyze workflow for bottlenecks
        bottlenecks = await self._detect_bottlenecks(workflow)

        # Generate optimization suggestions
        suggestions = await self._generate_suggestions(
            workflow, bottlenecks, request
        )

        # Calculate overall score
        score = self._calculate_score(workflow, bottlenecks)

        report = OptimizationReport(
            workflow_id=workflow.workflow_id,
            workflow_name=workflow.name,
            bottlenecks=bottlenecks,
            suggestions=suggestions,
            overall_score=score,
        )

        # Store in history
        if workflow.workflow_id not in self._optimization_history:
            self._optimization_history[workflow.workflow_id] = []
        self._optimization_history[workflow.workflow_id].append(report)

        logger.info(
            "Workflow optimization completed",
            workflow_id=request.workflow_id,
            bottlenecks_found=len(bottlenecks),
            suggestions_generated=len(suggestions),
            overall_score=score,
        )

        return report

    async def _detect_bottlenecks(
        self, workflow: DiscoveredWorkflow
    ) -> list[Bottleneck]:
        """Detect bottlenecks in a workflow.

        Args:
            workflow: The workflow to analyze.

        Returns:
            List of detected bottlenecks.
        """
        bottlenecks: list[Bottleneck] = []

        # Check for sequential dependencies that could be parallelized
        steps = sorted(workflow.steps, key=lambda s: s.order)
        for _i, step in enumerate(steps):
            if step.depends_on and len(step.depends_on) > 1:
                bottlenecks.append(
                    Bottleneck(
                        step_name=step.name,
                        description=(
                            f"Step '{step.name}' has multiple dependencies"
                            " that could be parallelized"
                        ),
                        severity=OptimizationPriority.MEDIUM,
                        impact_description=(
                            "Sequential execution of dependent steps"
                            " increases total workflow duration"
                        ),
                        metrics={"dependency_count": float(len(step.depends_on))},
                    )
                )

        # Check for missing error handling
        for step in steps:
            if step.step_type == "action" and not step.config.get("error_handling"):
                bottlenecks.append(
                    Bottleneck(
                        step_name=step.name,
                        description=f"Step '{step.name}' lacks error handling configuration",
                        severity=OptimizationPriority.HIGH,
                        impact_description=(
                            "Failures in this step will halt the entire"
                            " workflow without recovery"
                        ),
                        metrics={},
                    )
                )

        # Check for long-running steps
        for step in steps:
            if step.config.get("timeout", 0) > 300:
                bottlenecks.append(
                    Bottleneck(
                        step_name=step.name,
                        description=(
                            f"Step '{step.name}' has a long timeout"
                            f" ({step.config['timeout']}s)"
                        ),
                        severity=OptimizationPriority.LOW,
                        impact_description="Long timeouts can delay failure detection and recovery",
                        metrics={"timeout_seconds": float(step.config["timeout"])},
                    )
                )

        return bottlenecks

    async def _generate_suggestions(
        self,
        workflow: DiscoveredWorkflow,
        bottlenecks: list[Bottleneck],
        request: OptimizationRequest,
    ) -> list[OptimizationSuggestion]:
        """Generate optimization suggestions based on detected bottlenecks.

        Args:
            workflow: The workflow being optimized.
            bottlenecks: Detected bottlenecks.
            request: Optimization request parameters.

        Returns:
            List of optimization suggestions.
        """
        suggestions: list[OptimizationSuggestion] = []

        for bottleneck in bottlenecks:
            if (
                not request.include_low_priority
                and bottleneck.severity == OptimizationPriority.LOW
            ):
                continue

            suggestion = OptimizationSuggestion(
                workflow_id=workflow.workflow_id,
                title=f"Resolve: {bottleneck.description[:50]}",
                description=bottleneck.impact_description,
                optimization_type=OptimizationType.PERFORMANCE,
                priority=bottleneck.severity,
                affected_steps=[bottleneck.step_name],
                expected_improvement="Improved workflow reliability and performance",
                implementation_steps=[
                    "Analyze current step configuration",
                    "Implement suggested changes",
                    "Test in staging environment",
                    "Deploy to production",
                ],
                estimated_effort="medium",
            )
            suggestions.append(suggestion)

            if len(suggestions) >= request.max_suggestions:
                break

        return suggestions

    def _calculate_score(
        self, workflow: DiscoveredWorkflow, bottlenecks: list[Bottleneck]
    ) -> float:
        """Calculate an overall health score for the workflow.

        Args:
            workflow: The workflow being scored.
            bottlenecks: Detected bottlenecks.

        Returns:
            Score between 0 and 100.
        """
        base_score = 100.0

        severity_weights = {
            OptimizationPriority.CRITICAL: 20.0,
            OptimizationPriority.HIGH: 10.0,
            OptimizationPriority.MEDIUM: 5.0,
            OptimizationPriority.LOW: 2.0,
        }

        for bottleneck in bottlenecks:
            base_score -= severity_weights.get(bottleneck.severity, 5.0)

        return max(0.0, min(100.0, base_score))

    async def get_optimization_history(
        self, workflow_id: str
    ) -> list[OptimizationReport]:
        """Get optimization history for a workflow.

        Args:
            workflow_id: The workflow identifier.

        Returns:
            List of previous optimization reports.
        """
        return self._optimization_history.get(workflow_id, [])

    async def compare_optimizations(
        self, workflow_id: str
    ) -> dict[str, Any] | None:
        """Compare optimization reports over time.

        Args:
            workflow_id: The workflow identifier.

        Returns:
            Comparison data or None if insufficient history.
        """
        history = self._optimization_history.get(workflow_id, [])
        if len(history) < 2:
            return None

        latest = history[-1]
        previous = history[-2]

        return {
            "workflow_id": workflow_id,
            "score_change": latest.overall_score - previous.overall_score,
            "bottlenecks_resolved": len(previous.bottlenecks) - len(latest.bottlenecks),
            "new_bottlenecks": len(latest.bottlenecks) - len(previous.bottlenecks),
            "suggestions_implemented": len(previous.suggestions) - len(latest.suggestions),
        }
