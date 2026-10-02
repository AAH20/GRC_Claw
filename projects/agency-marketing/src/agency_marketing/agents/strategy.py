"""Strategy Agent - Campaign strategy and planning."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


class StrategyStatus(str, Enum):
    """Status of a strategy."""

    DRAFT = "draft"
    REVIEW = "in_review"
    APPROVED = "approved"
    ACTIVE = "active"
    ARCHIVED = "archived"


class ChannelType(str, Enum):
    """Marketing channel types."""

    SEO = "seo"
    PPC = "ppc"
    SOCIAL_MEDIA = "social_media"
    EMAIL = "email"
    CONTENT_MARKETING = "content_marketing"
    AFFILIATE = "affiliate"
    DISPLAY = "display"
    VIDEO = "video"
    INFLUENCER = "influencer"
    EVENTS = "events"


class CampaignObjective(str, Enum):
    """Campaign objective types."""

    BRAND_AWARENESS = "brand_awareness"
    LEAD_GENERATION = "lead_generation"
    SALES = "sales"
    CUSTOMER_RETENTION = "customer_retention"
    PRODUCT_LAUNCH = "product_launch"
    THOUGHT_LEADERSHIP = "thought_leadership"


class BudgetAllocation(BaseModel):
    """Budget allocation for a channel."""

    channel: ChannelType = Field(..., description="Marketing channel")
    amount: float = Field(..., ge=0, description="Allocated budget in USD")
    percentage: float = Field(..., ge=0, le=100, description="Percentage of total budget")
    expected_roi: float | None = Field(None, ge=0, description="Expected ROI multiplier")


class TimelineMilestone(BaseModel):
    """Campaign timeline milestone."""

    name: str = Field(..., description="Milestone name")
    description: str = Field(..., description="Milestone description")
    start_date: str = Field(..., description="Start date (ISO format)")
    end_date: str = Field(..., description="End date (ISO format)")
    deliverables: list[str] = Field(default_factory=list, description="Expected deliverables")
    status: str = Field("pending", description="Milestone status")


class KPI(BaseModel):
    """Key Performance Indicator."""

    name: str = Field(..., description="KPI name")
    description: str = Field(..., description="KPI description")
    target_value: float = Field(..., description="Target value")
    unit: str = Field(..., description="Unit of measurement")
    measurement_method: str = Field(..., description="How to measure this KPI")


class StrategyResult(BaseModel):
    """Result of strategy development."""

    objective: CampaignObjective = Field(..., description="Primary campaign objective")
    target_audience: str = Field(..., description="Target audience description")
    channels: list[ChannelType] = Field(default_factory=list, description="Selected channels")
    budget_allocations: list[BudgetAllocation] = Field(
        default_factory=list, description="Budget breakdown"
    )
    timeline: list[TimelineMilestone] = Field(default_factory=list, description="Campaign timeline")
    kpis: list[KPI] = Field(default_factory=list, description="Key performance indicators")
    messaging_pillars: list[str] = Field(default_factory=list, description="Core messaging pillars")
    creative_direction: str = Field("", description="Creative direction summary")
    risk_assessment: list[str] = Field(default_factory=list, description="Identified risks")
    created_at: str | None = Field(None, description="ISO timestamp of creation")


@dataclass
class StrategyAgentConfig:
    """Configuration for the Strategy Agent."""

    model: str = "gpt-4"
    max_tokens: int = 4096
    temperature: float = 0.5
    timeout_seconds: int = 120
    retry_attempts: int = 3
    enabled: bool = True


class StrategyAgent:
    """AI agent for campaign strategy development and planning.

    This agent creates comprehensive marketing strategies including
    channel selection, budget allocation, timeline planning, and KPI
    definition based on business objectives and market research.
    """

    def __init__(self, config: StrategyAgentConfig | None = None) -> None:
        """Initialize the Strategy Agent.

        Args:
            config: Optional configuration override.
        """
        self.config = config or StrategyAgentConfig()
        self._agent: Any = None
        self._initialize_agent()

    def _initialize_agent(self) -> None:
        """Initialize the underlying LangChain agent."""
        try:
            from langchain.agents import create_openai_functions_agent
            from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
            from langchain_openai import ChatOpenAI

            llm = ChatOpenAI(
                model=self.config.model,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
            )

            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are an expert marketing strategist with deep experience
                in digital marketing, brand strategy, and campaign planning.
                Create data-driven strategies with clear KPIs and measurable outcomes.
                Consider budget constraints, market conditions, and competitive landscape."""),
                MessagesPlaceholder(variable_name="chat_history", optional=True),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ])

            self._agent = create_openai_functions_agent(llm, [], prompt)
            logger.info("StrategyAgent initialized", model=self.config.model)
        except ImportError:
            logger.warning("LangChain not available, running in mock mode")
            self._agent = None

    async def develop_strategy(
        self,
        objective: CampaignObjective,
        budget: float,
        target_audience: str,
        industry: str,
        context: dict[str, Any] | None = None,
    ) -> StrategyResult:
        """Develop a comprehensive marketing strategy.

        Args:
            objective: Primary campaign objective.
            budget: Total campaign budget in USD.
            target_audience: Description of target audience.
            industry: Industry vertical.
            context: Optional additional context (research results, etc.).

        Returns:
            StrategyResult with complete strategy details.

        Raises:
            ValueError: If the agent is not enabled or budget is invalid.
            RuntimeError: If strategy development fails.
        """
        if not self.config.enabled:
            raise ValueError("StrategyAgent is not enabled")

        if budget <= 0:
            raise ValueError("Budget must be positive")

        logger.info(
            "Developing strategy",
            objective=objective.value,
            budget=budget,
            industry=industry,
        )

        try:
            if self._agent is None:
                return await self._mock_strategy(
                    objective, budget, target_audience, industry, context
                )

            result = await self._execute_strategy(
                objective, budget, target_audience, industry, context
            )
            return result

        except Exception as e:
            logger.error("Strategy development failed", error=str(e))
            raise RuntimeError(f"Strategy development failed: {e}") from e

    async def _execute_strategy(
        self,
        objective: CampaignObjective,
        budget: float,
        target_audience: str,
        industry: str,
        context: dict[str, Any] | None,
    ) -> StrategyResult:
        """Execute strategy development using the LangChain agent.

        Args:
            objective: Campaign objective.
            budget: Total budget.
            target_audience: Target audience.
            industry: Industry vertical.
            context: Additional context.

        Returns:
            StrategyResult with strategy details.
        """
        return await self._mock_strategy(objective, budget, target_audience, industry, context)

    async def _mock_strategy(
        self,
        objective: CampaignObjective,
        budget: float,
        target_audience: str,
        industry: str,
        context: dict[str, Any] | None,
    ) -> StrategyResult:
        """Generate mock strategy for testing/development.

        Args:
            objective: Campaign objective.
            budget: Total budget.
            target_audience: Target audience.
            industry: Industry vertical.
            context: Additional context.

        Returns:
            StrategyResult with mock strategy.
        """
        return StrategyResult(
            objective=objective,
            target_audience=target_audience,
            channels=[
                ChannelType.SEO, ChannelType.PPC,
                ChannelType.SOCIAL_MEDIA, ChannelType.EMAIL,
            ],
            budget_allocations=[
                BudgetAllocation(
                    channel=ChannelType.SEO, amount=budget * 0.3,
                    percentage=30, expected_roi=3.5,
                ),
                BudgetAllocation(
                    channel=ChannelType.PPC, amount=budget * 0.4,
                    percentage=40, expected_roi=2.8,
                ),
                BudgetAllocation(
                    channel=ChannelType.SOCIAL_MEDIA, amount=budget * 0.2,
                    percentage=20, expected_roi=2.2,
                ),
                BudgetAllocation(
                    channel=ChannelType.EMAIL, amount=budget * 0.1,
                    percentage=10, expected_roi=4.0,
                ),
            ],
            timeline=[
                TimelineMilestone(
                    name="Phase 1: Foundation",
                    description="Setup and initial content creation",
                    start_date="2024-01-01",
                    end_date="2024-01-31",
                    deliverables=["Content calendar", "Ad creatives", "Landing pages"],
                ),
                TimelineMilestone(
                    name="Phase 2: Launch",
                    description="Campaign launch across all channels",
                    start_date="2024-02-01",
                    end_date="2024-02-15",
                    deliverables=["Live campaigns", "Monitoring dashboards"],
                ),
            ],
            kpis=[
                KPI(
                    name="ROAS", description="Return on ad spend",
                    target_value=3.0, unit="ratio",
                    measurement_method="Revenue / Ad Spend",
                ),
                KPI(
                    name="CPA", description="Cost per acquisition",
                    target_value=50.0, unit="USD",
                    measurement_method="Total Spend / Conversions",
                ),
                KPI(
                    name="CTR", description="Click-through rate",
                    target_value=2.5, unit="percent",
                    measurement_method="Clicks / Impressions * 100",
                ),
            ],
            messaging_pillars=[
                "Value proposition clarity",
                "Customer pain point resolution",
                "Brand differentiation",
                "Social proof and trust",
            ],
            creative_direction=(
                f"Modern, professional creative targeting "
                f"{target_audience} in {industry}"
            ),
            risk_assessment=[
                "Budget overruns on paid channels",
                "Creative fatigue requiring frequent refreshes",
                "Seasonal fluctuations in conversion rates",
            ],
        )

    async def optimize_budget(
        self,
        current_allocations: list[BudgetAllocation],
        performance_data: dict[str, Any],
    ) -> list[BudgetAllocation]:
        """Optimize budget allocation based on performance data.

        Args:
            current_allocations: Current budget allocations.
            performance_data: Performance metrics by channel.

        Returns:
            Optimized budget allocations.
        """
        logger.info("Optimizing budget allocation")

        # Simple optimization: shift budget to higher-performing channels
        optimized: list[BudgetAllocation] = []
        for alloc in current_allocations:
            channel_perf = performance_data.get(alloc.channel.value, {})
            roi = channel_perf.get("roi", alloc.expected_roi or 1.0)

            # Adjust allocation based on performance
            adjustment = 1.0 + (roi - 2.0) * 0.1  # Simple heuristic
            new_amount = alloc.amount * max(0.5, min(1.5, adjustment))

            optimized.append(BudgetAllocation(
                channel=alloc.channel,
                amount=round(new_amount, 2),
                percentage=alloc.percentage,
                expected_roi=roi,
            ))

        return optimized
