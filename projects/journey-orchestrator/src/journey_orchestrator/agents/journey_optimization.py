"""Journey Optimization agent - recommends and applies journey improvements."""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import structlog
from pydantic import BaseModel, Field

from journey_orchestrator.agents.journey_analytics import (
    AnalyticsReport,
    AnalyticsRequest,
    JourneyAnalytics,
)
from journey_orchestrator.models.analytics import MetricType

logger = structlog.get_logger(__name__)


class OptimizationRequest(BaseModel):
    """Request for journey optimization."""

    journey_id: str = Field(..., description="The journey ID to optimize")
    target_metric: MetricType = Field(
        default=MetricType.CONVERSION_RATE,
        description="Primary metric to optimize for",
    )
    optimization_goal: str = Field(
        default="maximize",
        description="Optimization goal: maximize or minimize",
    )
    constraints: dict[str, Any] = Field(
        default_factory=dict,
        description="Optimization constraints (budget, timeline, etc.)",
    )
    auto_apply: bool = Field(
        default=False,
        description="Whether to automatically apply safe optimizations",
    )
    max_suggestions: int = Field(default=5, ge=1, le=20)


class OptimizationSuggestion(BaseModel):
    """A single optimization suggestion."""

    suggestion_id: str
    category: str
    title: str
    description: str
    expected_impact: float = Field(..., ge=0.0, le=1.0, description="Expected improvement fraction")
    confidence: float = Field(..., ge=0.0, le=1.0)
    effort: str = Field(default="medium", description="low, medium, or high")
    affected_steps: list[int] = Field(default_factory=list)
    changes: dict[str, Any] = Field(default_factory=dict)
    risk_level: str = Field(default="low", description="low, medium, or high")


class OptimizationResult(BaseModel):
    """Result of journey optimization analysis."""

    journey_id: str
    target_metric: str
    current_value: float = Field(default=0.0, ge=0.0)
    projected_value: float = Field(default=0.0, ge=0.0)
    improvement_potential: float = Field(default=0.0, ge=0.0)
    suggestions: list[OptimizationSuggestion] = Field(default_factory=list)
    applied_changes: list[dict[str, Any]] = Field(default_factory=list)
    requires_approval: list[str] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class JourneyOptimization:
    """Agent that recommends and applies journey optimizations.

    Uses analytics data, best practices, and A/B test results to
    suggest improvements to journey structure, content, timing,
    and channel mix. Can auto-apply low-risk changes.
    """

    def __init__(self, llm_client: Any | None = None) -> None:
        """Initialize the Journey Optimization agent.

        Args:
            llm_client: Optional LLM client for AI-powered optimization.
        """
        self.llm_client = llm_client
        self.logger = logger.bind(agent="journey_optimization")
        self.analytics = JourneyAnalytics(llm_client=llm_client)

    async def optimize(self, request: OptimizationRequest) -> OptimizationResult:
        """Generate optimization suggestions for a journey.

        Args:
            request: The optimization request.

        Returns:
            An optimization result with suggestions and projections.

        Raises:
            ValueError: If the request is invalid.
        """
        if not request.journey_id.strip():
            raise ValueError("journey_id must not be empty")
        if request.optimization_goal not in ("maximize", "minimize"):
            raise ValueError("optimization_goal must be 'maximize' or 'minimize'")
        if request.max_suggestions < 1:
            raise ValueError("max_suggestions must be at least 1")

        self.logger.info(
            "Optimizing journey",
            journey_id=request.journey_id,
            target_metric=request.target_metric.value,
            goal=request.optimization_goal,
        )

        # Get current analytics
        analytics_request = AnalyticsRequest(
            journey_id=request.journey_id,
            metrics=[request.target_metric],
            include_funnel=True,
            include_cohorts=True,
        )
        analytics_report = await self.analytics.analyze(analytics_request)

        # Generate suggestions based on analytics
        suggestions = await self._generate_suggestions(
            request, analytics_report
        )

        # Calculate projections
        current_value = self._get_current_value(analytics_report, request.target_metric)
        projected_value = self._project_value(current_value, suggestions)

        # Auto-apply safe suggestions if requested
        applied: list[dict[str, Any]] = []
        requires_approval: list[str] = []
        if request.auto_apply:
            for suggestion in suggestions:
                if suggestion.risk_level == "low" and suggestion.confidence > 0.7:
                    applied.append(suggestion.changes)
                else:
                    requires_approval.append(suggestion.suggestion_id)

        result = OptimizationResult(
            journey_id=request.journey_id,
            target_metric=request.target_metric.value,
            current_value=current_value,
            projected_value=projected_value,
            improvement_potential=projected_value - current_value,
            suggestions=suggestions,
            applied_changes=applied,
            requires_approval=requires_approval,
        )

        self.logger.info(
            "Optimization complete",
            journey_id=request.journey_id,
            suggestions=len(suggestions),
            improvement=result.improvement_potential,
        )
        return result

    async def apply_optimization(
        self,
        journey_id: str,
        suggestion_id: str,
    ) -> dict[str, Any]:
        """Apply a specific optimization suggestion to a journey.

        Args:
            journey_id: The journey ID.
            suggestion_id: The suggestion to apply.

        Returns:
            The result of applying the optimization.

        Raises:
            ValueError: If the journey or suggestion is not found.
        """
        if not journey_id.strip():
            raise ValueError("journey_id must not be empty")
        if not suggestion_id.strip():
            raise ValueError("suggestion_id must not be empty")

        self.logger.info(
            "Applying optimization",
            journey_id=journey_id,
            suggestion_id=suggestion_id,
        )

        # In production, this would modify the journey in the database
        return {
            "journey_id": journey_id,
            "suggestion_id": suggestion_id,
            "status": "applied",
            "applied_at": datetime.now(UTC).isoformat(),
        }

    async def _generate_suggestions(
        self,
        request: OptimizationRequest,
        analytics_report: AnalyticsReport,
    ) -> list[OptimizationSuggestion]:
        """Generate optimization suggestions from analytics data.

        Args:
            request: The optimization request.
            analytics_report: The analytics report for the journey.

        Returns:
            A list of optimization suggestions.
        """
        suggestions: list[OptimizationSuggestion] = []
        performance = analytics_report.performance

        # Suggestion based on conversion rate
        if performance.conversion_rate < 0.15:
            suggestions.append(
                OptimizationSuggestion(
                    suggestion_id=f"{request.journey_id}_conv_1",
                    category="content",
                    title="Strengthen call-to-action messaging",
                    description=(
                        "Conversion rate is below 15%. Test more compelling "
                        "CTAs with urgency and value proposition."
                    ),
                    expected_impact=0.05,
                    confidence=0.75,
                    effort="low",
                    affected_steps=[1, 2],
                    changes={"step_1_cta": "urgent_value_prop", "step_2_cta": "social_proof"},
                    risk_level="low",
                )
            )

        # Suggestion based on engagement
        if performance.engagement_rate < 0.4:
            suggestions.append(
                OptimizationSuggestion(
                    suggestion_id=f"{request.journey_id}_eng_1",
                    category="timing",
                    title="Optimize send timing",
                    description=(
                        "Engagement rate suggests suboptimal send times. "
                        "Shift to customer's local timezone peak hours."
                    ),
                    expected_impact=0.08,
                    confidence=0.7,
                    effort="low",
                    affected_steps=[],
                    changes={"send_time_strategy": "timezone_optimized"},
                    risk_level="low",
                )
            )

        # Suggestion based on funnel dropoff
        if analytics_report.funnel:
            for stage in analytics_report.funnel.stages:
                if stage.dropoff_rate > 0.5:
                    suggestions.append(
                        OptimizationSuggestion(
                            suggestion_id=f"{request.journey_id}_funnel_{stage.stage_name}",
                            category="structure",
                            title=f"Reduce dropoff at '{stage.stage_name}' stage",
                            description=(
                                f"High dropoff rate ({stage.dropoff_rate:.1%}) at "
                                f"'{stage.stage_name}'. Simplify the transition."
                            ),
                            expected_impact=0.1,
                            confidence=0.8,
                            effort="medium",
                            affected_steps=[],
                            changes={"simplify_stage": stage.stage_name},
                            risk_level="medium",
                        )
                    )

        # Suggestion based on revenue
        if performance.revenue_per_customer < 20.0:
            suggestions.append(
                OptimizationSuggestion(
                    suggestion_id=f"{request.journey_id}_rev_1",
                    category="monetization",
                    title="Add upsell step",
                    description=(
                        "Revenue per customer is low. Add a post-conversion "
                        "upsell step with a complementary offer."
                    ),
                    expected_impact=0.12,
                    confidence=0.65,
                    effort="medium",
                    affected_steps=[],
                    changes={"add_step": {"type": "upsell", "position": "post_conversion"}},
                    risk_level="medium",
                )
            )

        # Sort by expected impact and return top N
        suggestions.sort(key=lambda s: s.expected_impact * s.confidence, reverse=True)
        return suggestions[: request.max_suggestions]

    def _get_current_value(
        self,
        analytics_report: AnalyticsReport,
        target_metric: MetricType,
    ) -> float:
        """Get the current value of the target metric.

        Args:
            analytics_report: The analytics report.
            target_metric: The target metric type.

        Returns:
            The current metric value.
        """
        performance = analytics_report.performance
        if target_metric == MetricType.CONVERSION_RATE:
            return performance.conversion_rate
        if target_metric == MetricType.ENGAGEMENT_RATE:
            return performance.engagement_rate
        if target_metric == MetricType.REVENUE_PER_CUSTOMER:
            return performance.revenue_per_customer
        return 0.0

    def _project_value(
        self,
        current_value: float,
        suggestions: list[OptimizationSuggestion],
    ) -> float:
        """Project the metric value after applying suggestions.

        Args:
            current_value: The current metric value.
            suggestions: The optimization suggestions.

        Returns:
            The projected metric value.
        """
        # Simple additive projection with diminishing returns
        total_impact = sum(s.expected_impact * s.confidence for s in suggestions)
        # Apply diminishing returns: impact / (1 + impact)
        adjusted_impact = total_impact / (1.0 + total_impact) if total_impact > 0 else 0.0
        projected = current_value + adjusted_impact
        # Cap at 1.0 only for rate metrics (values between 0 and 1)
        if 0.0 <= current_value <= 1.0:
            return min(1.0, projected)
        return projected
