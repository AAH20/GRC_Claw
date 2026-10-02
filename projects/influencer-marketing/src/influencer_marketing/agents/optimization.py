"""Optimization agent for data-driven campaign optimization."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import structlog

from influencer_marketing.agents.base import AgentConfig, AgentResult, BaseAgent
from influencer_marketing.agents.performance import PerformanceReport

logger = structlog.get_logger(__name__)


@dataclass
class OptimizationAction:
    """A recommended optimization action."""

    action_type: str  # e.g., "increase_budget", "pause_content", "adjust_targeting"
    target: str  # e.g., content_id, campaign_id, influencer_id
    description: str
    expected_impact: str
    priority: int  # 1 = highest
    estimated_improvement: float  # percentage improvement estimate
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class OptimizationResult:
    """Result of an optimization analysis."""

    campaign_id: str
    actions: list[OptimizationAction] = field(default_factory=list)
    analysis_timestamp: datetime | None = None
    summary: str = ""
    total_estimated_improvement: float = 0.0


class OptimizationAgent(BaseAgent[list[PerformanceReport], OptimizationResult]):
    """Agent responsible for optimizing campaign performance through data-driven adjustments."""

    def __init__(self) -> None:
        config = AgentConfig(
            name="optimization",
            description="Optimizes campaign performance through data-driven adjustments",
            max_retries=3,
            timeout_seconds=120,
        )
        super().__init__(config)
        self.min_data_points = 100

    async def validate_input(self, input_data: list[PerformanceReport]) -> bool:
        """Validate optimization input."""
        if not input_data:
            self.logger.warning("No performance reports provided")
            return False
        if len(input_data) < self.min_data_points:
            self.logger.warning(
                "Insufficient data points for optimization",
                required=self.min_data_points,
                provided=len(input_data),
            )
            return False
        return True

    async def execute(
        self, input_data: list[PerformanceReport]
    ) -> AgentResult[OptimizationResult]:
        """Execute optimization analysis on performance reports."""
        self.logger.info(
            "Starting optimization analysis",
            report_count=len(input_data),
        )

        try:
            campaign_id = input_data[0].campaign_id
            actions: list[OptimizationAction] = []

            # Analyze each report for optimization opportunities
            for report in input_data:
                report_actions = self._analyze_report(report)
                actions.extend(report_actions)

            # Sort by priority
            actions.sort(key=lambda x: x.priority)

            # Calculate total estimated improvement
            total_improvement = sum(a.estimated_improvement for a in actions)

            result = OptimizationResult(
                campaign_id=campaign_id,
                actions=actions,
                analysis_timestamp=datetime.utcnow(),
                summary=self._generate_summary(actions),
                total_estimated_improvement=total_improvement,
            )

            self.logger.info(
                "Optimization analysis completed",
                campaign_id=campaign_id,
                actions_count=len(actions),
                total_improvement=total_improvement,
            )
            return AgentResult(success=True, data=result)

        except Exception as exc:
            self.logger.error("Optimization analysis failed", error=str(exc))
            return AgentResult(success=False, error=str(exc))

    def _analyze_report(self, report: PerformanceReport) -> list[OptimizationAction]:
        """Analyze a single performance report for optimization opportunities."""
        actions: list[OptimizationAction] = []
        metrics = report.metrics

        # Low engagement optimization
        if metrics.engagement_rate < 0.02:
            actions.append(
                OptimizationAction(
                    action_type="content_refresh",
                    target=report.content_id or "",
                    description="Content engagement is below threshold - recommend content refresh",
                    expected_impact="Increase engagement rate by 20-30%",
                    priority=1,
                    estimated_improvement=0.25,
                )
            )

        # High ROAS scaling opportunity
        if metrics.roas > 3.0:
            actions.append(
                OptimizationAction(
                    action_type="increase_budget",
                    target=report.influencer_id or "",
                    description="High ROAS detected - recommend budget increase",
                    expected_impact="Scale successful content for higher revenue",
                    priority=2,
                    estimated_improvement=0.4,
                )
            )

        # Negative ROAS mitigation
        if metrics.roas < 1.0 and metrics.spend > 0:
            actions.append(
                OptimizationAction(
                    action_type="pause_content",
                    target=report.content_id or "",
                    description="Negative ROAS - recommend pausing underperforming content",
                    expected_impact="Prevent further budget waste",
                    priority=1,
                    estimated_improvement=0.15,
                )
            )

        # Low CTR optimization
        if metrics.ctr < 0.01 and metrics.impressions > 1000:
            actions.append(
                OptimizationAction(
                    action_type="improve_cta",
                    target=report.content_id or "",
                    description="Low click-through rate - improve call-to-action",
                    expected_impact="Increase CTR by 15-25%",
                    priority=3,
                    estimated_improvement=0.2,
                )
            )

        return actions

    def _generate_summary(self, actions: list[OptimizationAction]) -> str:
        """Generate a summary of optimization actions."""
        if not actions:
            return "No optimization actions recommended at this time."

        high_priority = sum(1 for a in actions if a.priority == 1)
        return (
            f"Generated {len(actions)} optimization actions "
            f"({high_priority} high priority). "
            f"Estimated total improvement: "
            f"{sum(a.estimated_improvement for a in actions):.0%}"
        )
