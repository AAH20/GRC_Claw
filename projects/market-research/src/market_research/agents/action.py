"""Action Agent for recommending actionable market strategies."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING, Any

import structlog
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from market_research.agents.analysis import AnalysisResult

logger = structlog.get_logger(__name__)


class PriorityLevel(StrEnum):
    """Priority levels for action recommendations."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ActionStatus(StrEnum):
    """Status of a recommended action."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    DEFERRED = "deferred"


class ActionItem(BaseModel):
    """A single recommended action item."""

    id: str
    title: str
    description: str
    priority: PriorityLevel
    category: str
    expected_impact: str
    effort_required: str
    timeframe: str
    dependencies: list[str] = Field(default_factory=list)
    kpis: list[str] = Field(default_factory=list)
    status: ActionStatus = ActionStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ActionPlan(BaseModel):
    """A complete action plan with multiple action items."""

    plan_id: str
    title: str
    analysis_id: str
    items: list[ActionItem] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    total_items: int = 0
    critical_items: int = 0
    high_priority_items: int = 0


class ActionRequest(BaseModel):
    """Request to generate an action plan."""

    title: str
    analysis_result: AnalysisResult
    max_recommendations: int = Field(default=10, ge=1, le=50)
    priority_filter: list[PriorityLevel] | None = None
    categories: list[str] | None = None
    timeframe_constraint: str | None = None


class ActionAgent:
    """Agent responsible for recommending actionable market strategies.

    This agent takes analysis results and generates prioritized, actionable
    recommendations with clear impact assessments and implementation guidance.
    """

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize the Action Agent.

        Args:
            config: Optional configuration dictionary for the agent.
        """
        self.config = config or {}
        self.max_recommendations = self.config.get("max_recommendations", 10)
        self.priority_levels = self.config.get(
            "priority_levels", [p.value for p in PriorityLevel]
        )
        self.validation_required = self.config.get("validation_required", True)
        logger.info("action_agent_initialized", max_recommendations=self.max_recommendations)

    async def generate_action_plan(self, request: ActionRequest) -> ActionPlan:
        """Generate an action plan based on analysis results.

        Args:
            request: The action plan request.

        Returns:
            ActionPlan with prioritized action items.

        Raises:
            ValueError: If the request is invalid.
        """
        if not request.title.strip():
            raise ValueError("Action plan title must not be empty")

        plan_id = f"ap_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{id(request)}"
        logger.info(
            "generating_action_plan",
            plan_id=plan_id,
            title=request.title,
            max_recommendations=request.max_recommendations,
        )

        items = await self._generate_action_items(request)
        items = self._prioritize_items(items)
        items = self._filter_items(items, request)
        items = items[: request.max_recommendations]

        plan = ActionPlan(
            plan_id=plan_id,
            title=request.title,
            analysis_id=request.analysis_result.analysis_id,
            items=items,
            total_items=len(items),
            critical_items=sum(1 for i in items if i.priority == PriorityLevel.CRITICAL),
            high_priority_items=sum(1 for i in items if i.priority == PriorityLevel.HIGH),
        )

        logger.info(
            "action_plan_generated",
            plan_id=plan_id,
            total_items=plan.total_items,
            critical_items=plan.critical_items,
            high_priority_items=plan.high_priority_items,
        )

        return plan

    async def _generate_action_items(self, request: ActionRequest) -> list[ActionItem]:
        """Generate action items from analysis results.

        Args:
            request: The action plan request.

        Returns:
            List of action items.
        """
        items: list[ActionItem] = []
        analysis = request.analysis_result

        if analysis.swot:
            items.extend(self._items_from_swot(analysis))

        if analysis.porters_five_forces:
            items.extend(self._items_from_porters(analysis))

        if analysis.trend_analysis:
            items.extend(self._items_from_trends(analysis))

        if analysis.recommendations:
            items.extend(self._items_from_recommendations(analysis))

        return items

    def _items_from_swot(self, analysis: AnalysisResult) -> list[ActionItem]:
        """Generate action items from SWOT analysis.

        Args:
            analysis: The analysis result.

        Returns:
            List of action items.
        """
        items: list[ActionItem] = []
        swot = analysis.swot
        if not swot:
            return items

        for idx, opportunity in enumerate(swot.opportunities[:3]):
            items.append(
                ActionItem(
                    id=f"swot_opp_{idx}",
                    title=f"Capitalize on: {opportunity}",
                    description=f"Develop strategy to leverage the opportunity: {opportunity}",
                    priority=PriorityLevel.HIGH if idx == 0 else PriorityLevel.MEDIUM,
                    category="opportunity",
                    expected_impact="Revenue growth, market share expansion",
                    effort_required="Medium",
                    timeframe="3-6 months",
                    kpis=["Revenue growth", "Market share"],
                )
            )

        for idx, threat in enumerate(swot.threats[:2]):
            items.append(
                ActionItem(
                    id=f"swot_threat_{idx}",
                    title=f"Mitigate: {threat}",
                    description=f"Develop mitigation strategy for threat: {threat}",
                    priority=PriorityLevel.CRITICAL if idx == 0 else PriorityLevel.HIGH,
                    category="risk_mitigation",
                    expected_impact="Risk reduction, business continuity",
                    effort_required="High",
                    timeframe="1-3 months",
                    kpis=["Risk exposure", "Compliance score"],
                )
            )

        return items

    def _items_from_porters(self, analysis: AnalysisResult) -> list[ActionItem]:
        """Generate action items from Porter's Five Forces.

        Args:
            analysis: The analysis result.

        Returns:
            List of action items.
        """
        items: list[ActionItem] = []
        p5f = analysis.porters_five_forces
        if not p5f:
            return items

        if p5f.competitive_rivalry > 0.6:
            items.append(
                ActionItem(
                    id="porters_rivalry",
                    title="Differentiate offerings to reduce competitive pressure",
                    description="Develop unique value propositions and product differentiation",
                    priority=PriorityLevel.HIGH,
                    category="competitive_strategy",
                    expected_impact="Reduced price pressure, improved margins",
                    effort_required="High",
                    timeframe="6-12 months",
                    kpis=["Market share", "Profit margin"],
                )
            )

        if p5f.threat_of_new_entry > 0.5:
            items.append(
                ActionItem(
                    id="porters_entry",
                    title="Build barriers to entry",
                    description=(
                        "Strengthen competitive moats through patents, partnerships, and scale"
                    ),
                    priority=PriorityLevel.MEDIUM,
                    category="competitive_strategy",
                    expected_impact="Sustained competitive advantage",
                    effort_required="Medium",
                    timeframe="6-12 months",
                    kpis=["Market position", "Entry barriers"],
                )
            )

        return items

    def _items_from_trends(self, analysis: AnalysisResult) -> list[ActionItem]:
        """Generate action items from trend analysis.

        Args:
            analysis: The analysis result.

        Returns:
            List of action items.
        """
        items: list[ActionItem] = []
        trend = analysis.trend_analysis
        if not trend:
            return items

        if trend.trend_direction == "upward":
            items.append(
                ActionItem(
                    id="trend_growth",
                    title="Invest in growth to capitalize on upward trend",
                    description="Scale operations and marketing to capture market growth",
                    priority=PriorityLevel.HIGH,
                    category="growth",
                    expected_impact="Revenue growth, market share gains",
                    effort_required="High",
                    timeframe="3-6 months",
                    kpis=["Revenue", "Customer acquisition"],
                )
            )

        for idx, driver in enumerate(trend.key_drivers[:2]):
            items.append(
                ActionItem(
                    id=f"trend_driver_{idx}",
                    title=f"Leverage key driver: {driver}",
                    description=f"Align strategy with market driver: {driver}",
                    priority=PriorityLevel.MEDIUM,
                    category="strategic_alignment",
                    expected_impact="Improved market positioning",
                    effort_required="Medium",
                    timeframe="3-9 months",
                    kpis=["Strategic alignment score"],
                )
            )

        return items

    def _items_from_recommendations(self, analysis: AnalysisResult) -> list[ActionItem]:
        """Generate action items from analysis recommendations.

        Args:
            analysis: The analysis result.

        Returns:
            List of action items.
        """
        items: list[ActionItem] = []
        for idx, rec in enumerate(analysis.recommendations[:5]):
            items.append(
                ActionItem(
                    id=f"rec_{idx}",
                    title=rec,
                    description=f"Execute recommendation: {rec}",
                    priority=PriorityLevel.MEDIUM,
                    category="general",
                    expected_impact="Improved business performance",
                    effort_required="Medium",
                    timeframe="3-6 months",
                    kpis=["Performance improvement"],
                )
            )
        return items

    def _prioritize_items(self, items: list[ActionItem]) -> list[ActionItem]:
        """Sort action items by priority.

        Args:
            items: The action items to sort.

        Returns:
            Sorted list of action items.
        """
        priority_order = {
            PriorityLevel.CRITICAL: 0,
            PriorityLevel.HIGH: 1,
            PriorityLevel.MEDIUM: 2,
            PriorityLevel.LOW: 3,
        }
        return sorted(items, key=lambda i: priority_order.get(i.priority, 99))

    def _filter_items(
        self,
        items: list[ActionItem],
        request: ActionRequest,
    ) -> list[ActionItem]:
        """Filter action items based on request criteria.

        Args:
            items: The action items to filter.
            request: The action plan request.

        Returns:
            Filtered list of action items.
        """
        filtered = items

        if request.priority_filter:
            filtered = [i for i in filtered if i.priority in request.priority_filter]

        if request.categories:
            filtered = [i for i in filtered if i.category in request.categories]

        return filtered
