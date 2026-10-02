"""Cost Optimization Agent — analyzes spend patterns and recommends cost-saving measures."""

from __future__ import annotations

import asyncio
import contextlib
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class RecommendationType(StrEnum):
    """Types of cost optimization recommendations."""

    RIGHTSIZING = "rightsizing"
    SPOT_INSTANCES = "spot_instances"
    RESERVED_CAPACITY = "reserved_capacity"
    STORAGE_TIER = "storage_tier"
    IDLE_RESOURCES = "idle_resources"


@dataclass
class CostBreakdown:
    """Represents a cost breakdown for a project."""

    project_id: str
    compute_cost: float
    storage_cost: float
    network_cost: float
    api_cost: float
    total_cost: float
    period_start: datetime
    period_end: datetime


@dataclass
class CostRecommendation:
    """A cost optimization recommendation."""

    recommendation_id: str
    project_id: str
    recommendation_type: RecommendationType
    description: str
    estimated_savings: float
    confidence: float  # 0.0 to 1.0
    created_at: datetime = field(default_factory=datetime.utcnow)
    applied: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class BudgetAlert:
    """A budget threshold alert."""

    project_id: str
    threshold_percent: float
    current_spend: float
    budget_limit: float
    triggered_at: datetime = field(default_factory=datetime.utcnow)


class CostOptimizationAgent:
    """Analyzes spend patterns and recommends cost-saving measures.

    Monitors resource utilization across projects and identifies
    opportunities for rightsizing, spot instances, reserved capacity,
    and storage tier optimization.
    """

    def __init__(
        self,
        analysis_interval: int = 3600,
        budget_alert_threshold: float = 0.8,
        enabled_recommendations: list[RecommendationType] | None = None,
    ) -> None:
        """Initialize the Cost Optimization Agent.

        Args:
            analysis_interval: Seconds between cost analyses.
            budget_alert_threshold: Fraction of budget that triggers an alert.
            enabled_recommendations: Which recommendation types to enable.
        """
        self._analysis_interval = analysis_interval
        self._budget_alert_threshold = budget_alert_threshold
        self._enabled_recommendations = enabled_recommendations or list(RecommendationType)
        self._recommendations: dict[str, list[CostRecommendation]] = {}
        self._budgets: dict[str, float] = {}
        self._spend: dict[str, CostBreakdown] = {}
        self._alerts: list[BudgetAlert] = []
        self._running = False
        self._analysis_task: asyncio.Task[None] | None = None

    @property
    def is_running(self) -> bool:
        """Check if the background analysis loop is active."""
        return self._running

    async def start(self) -> None:
        """Start the background cost analysis loop."""
        if self._running:
            logger.warning("CostOptimizationAgent already running")
            return
        self._running = True
        self._analysis_task = asyncio.create_task(self._analysis_loop())
        logger.info("CostOptimizationAgent started", interval=self._analysis_interval)

    async def stop(self) -> None:
        """Stop the background cost analysis loop."""
        self._running = False
        if self._analysis_task:
            self._analysis_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._analysis_task
        logger.info("CostOptimizationAgent stopped")

    async def _analysis_loop(self) -> None:
        """Background loop that periodically analyzes costs."""
        while self._running:
            try:
                await self.analyze_all()
            except Exception as exc:
                logger.error("Cost analysis failed", error=str(exc))
            await asyncio.sleep(self._analysis_interval)

    async def analyze_all(self) -> list[CostRecommendation]:
        """Run cost analysis for all tracked projects.

        Returns:
            List of new recommendations generated.
        """
        new_recommendations: list[CostRecommendation] = []
        for project_id in list(self._spend.keys()):
            recs = await self.analyze_project(project_id)
            new_recommendations.extend(recs)
        return new_recommendations

    async def analyze_project(self, project_id: str) -> list[CostRecommendation]:
        """Analyze costs for a single project and generate recommendations.

        Args:
            project_id: The project to analyze.

        Returns:
            List of recommendations for the project.
        """
        breakdown = self._spend.get(project_id)
        if breakdown is None:
            return []

        recommendations: list[CostRecommendation] = []

        if RecommendationType.RIGHTSIZING in self._enabled_recommendations:
            rec = self._check_rightsizing(project_id, breakdown)
            if rec:
                recommendations.append(rec)

        if RecommendationType.SPOT_INSTANCES in self._enabled_recommendations:
            rec = self._check_spot_instances(project_id, breakdown)
            if rec:
                recommendations.append(rec)

        if RecommendationType.RESERVED_CAPACITY in self._enabled_recommendations:
            rec = self._check_reserved_capacity(project_id, breakdown)
            if rec:
                recommendations.append(rec)

        if RecommendationType.IDLE_RESOURCES in self._enabled_recommendations:
            rec = self._check_idle_resources(project_id, breakdown)
            if rec:
                recommendations.append(rec)

        if project_id not in self._recommendations:
            self._recommendations[project_id] = []
        self._recommendations[project_id].extend(recommendations)

        # Check budget alerts
        self._check_budget_alert(project_id, breakdown)

        logger.info(
            "Cost analysis complete",
            project_id=project_id,
            recommendations=len(recommendations),
        )
        return recommendations

    def _check_rightsizing(
        self, project_id: str, breakdown: CostBreakdown
    ) -> CostRecommendation | None:
        """Check if a project is over-provisioned.

        Args:
            project_id: The project to check.
            breakdown: Current cost breakdown.

        Returns:
            Recommendation if over-provisioned, else None.
        """
        # Placeholder: would use actual utilization metrics
        utilization = 0.3  # 30% average utilization
        if utilization < 0.4:
            savings = breakdown.compute_cost * 0.3
            return CostRecommendation(
                recommendation_id=f"rightsizing:{project_id}:{datetime.utcnow().isoformat()}",
                project_id=project_id,
                recommendation_type=RecommendationType.RIGHTSIZING,
                description=(
                    f"Project {project_id} is underutilized ({utilization:.0%}). "
                    "Consider downsizing."
                ),
                estimated_savings=savings,
                confidence=0.8,
                metadata={"current_utilization": utilization},
            )
        return None

    def _check_spot_instances(
        self, project_id: str, breakdown: CostBreakdown
    ) -> CostRecommendation | None:
        """Check if a project could benefit from spot instances.

        Args:
            project_id: The project to check.
            breakdown: Current cost breakdown.

        Returns:
            Recommendation if spot instances would help, else None.
        """
        if breakdown.compute_cost > 1000:
            savings = breakdown.compute_cost * 0.6
            return CostRecommendation(
                recommendation_id=f"spot:{project_id}:{datetime.utcnow().isoformat()}",
                project_id=project_id,
                recommendation_type=RecommendationType.SPOT_INSTANCES,
                description=(
                    f"Project {project_id} could save {savings:.2f}/month "
                    "with spot instances."
                ),
                estimated_savings=savings,
                confidence=0.7,
                metadata={"current_monthly_compute": breakdown.compute_cost},
            )
        return None

    def _check_reserved_capacity(
        self, project_id: str, breakdown: CostBreakdown
    ) -> CostRecommendation | None:
        """Check if a project should use reserved capacity.

        Args:
            project_id: The project to check.
            breakdown: Current cost breakdown.

        Returns:
            Recommendation if reserved capacity would help, else None.
        """
        if breakdown.compute_cost > 5000:
            savings = breakdown.compute_cost * 0.35
            return CostRecommendation(
                recommendation_id=f"reserved:{project_id}:{datetime.utcnow().isoformat()}",
                project_id=project_id,
                recommendation_type=RecommendationType.RESERVED_CAPACITY,
                description=(
                    f"Project {project_id} has stable workload suitable "
                    "for reserved capacity."
                ),
                estimated_savings=savings,
                confidence=0.85,
                metadata={"current_monthly_compute": breakdown.compute_cost},
            )
        return None

    def _check_idle_resources(
        self, project_id: str, breakdown: CostBreakdown
    ) -> CostRecommendation | None:
        """Check for idle resources that could be decommissioned.

        Args:
            project_id: The project to check.
            breakdown: Current cost breakdown.

        Returns:
            Recommendation if idle resources are found, else None.
        """
        if breakdown.storage_cost > 500:
            savings = breakdown.storage_cost * 0.2
            return CostRecommendation(
                recommendation_id=f"idle:{project_id}:{datetime.utcnow().isoformat()}",
                project_id=project_id,
                recommendation_type=RecommendationType.IDLE_RESOURCES,
                description=f"Project {project_id} has idle storage that could be cleaned up.",
                estimated_savings=savings,
                confidence=0.6,
                metadata={"current_monthly_storage": breakdown.storage_cost},
            )
        return None

    def _check_budget_alert(self, project_id: str, breakdown: CostBreakdown) -> None:
        """Check if a project has exceeded its budget threshold.

        Args:
            project_id: The project to check.
            breakdown: Current cost breakdown.
        """
        budget = self._budgets.get(project_id)
        if budget and breakdown.total_cost >= budget * self._budget_alert_threshold:
            alert = BudgetAlert(
                project_id=project_id,
                threshold_percent=self._budget_alert_threshold * 100,
                current_spend=breakdown.total_cost,
                budget_limit=budget,
            )
            self._alerts.append(alert)
            logger.warning(
                "Budget alert triggered",
                project_id=project_id,
                spend=breakdown.total_cost,
                budget=budget,
            )

    def set_budget(self, project_id: str, budget: float) -> None:
        """Set a budget for a project.

        Args:
            project_id: The project to set the budget for.
            budget: Monthly budget in USD.
        """
        self._budgets[project_id] = budget
        logger.info("Budget set", project_id=project_id, budget=budget)

    def record_spend(self, breakdown: CostBreakdown) -> None:
        """Record the current spend for a project.

        Args:
            breakdown: The cost breakdown to record.
        """
        self._spend[breakdown.project_id] = breakdown

    def get_recommendations(
        self, project_id: str | None = None, applied: bool | None = None
    ) -> list[CostRecommendation]:
        """Get cost recommendations with optional filtering.

        Args:
            project_id: Filter by project.
            applied: Filter by applied status.

        Returns:
            List of matching recommendations.
        """
        if project_id:
            recs = self._recommendations.get(project_id, [])
        else:
            recs = [r for sublist in self._recommendations.values() for r in sublist]
        if applied is not None:
            recs = [r for r in recs if r.applied == applied]
        return recs

    def apply_recommendation(self, recommendation_id: str) -> bool:
        """Mark a recommendation as applied.

        Args:
            recommendation_id: The recommendation to mark as applied.

        Returns:
            True if the recommendation was found and updated.
        """
        for recs in self._recommendations.values():
            for rec in recs:
                if rec.recommendation_id == recommendation_id:
                    rec.applied = True
                    logger.info("Recommendation applied", id=recommendation_id)
                    return True
        return False

    def get_total_potential_savings(self) -> float:
        """Get the total potential savings from all unapplied recommendations.

        Returns:
            Total estimated savings in USD.
        """
        return sum(
            r.estimated_savings
            for recs in self._recommendations.values()
            for r in recs
            if not r.applied
        )
