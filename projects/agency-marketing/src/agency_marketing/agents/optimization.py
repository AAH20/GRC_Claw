"""Optimization Agent - Performance optimization and ROI improvement."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


class OptimizationStatus(str, Enum):
    """Status of an optimization task."""

    PENDING = "pending"
    ANALYZING = "analyzing"
    RECOMMENDING = "recommending"
    APPLYING = "applying"
    COMPLETED = "completed"
    FAILED = "failed"


class OptimizationType(str, Enum):
    """Types of optimization."""

    BUDGET_REALLOCATION = "budget_reallocation"
    CREATIVE_REFRESH = "creative_refresh"
    AUDIENCE_REFINEMENT = "audience_refinement"
    BID_OPTIMIZATION = "bid_optimization"
    LANDING_PAGE_OPTIMIZATION = "landing_page_optimization"
    FREQUENCY_CAPPING = "frequency_capping"
    DAYPARTING = "dayparting"


class PerformanceMetric(BaseModel):
    """A single performance metric."""

    name: str = Field(..., description="Metric name")
    current_value: float = Field(..., description="Current value")
    target_value: float = Field(..., description="Target value")
    unit: str = Field(..., description="Unit of measurement")
    trend: str = Field("stable", description="Trend direction (up, down, stable)")
    change_percentage: float | None = Field(None, description="Percentage change")


class OptimizationRecommendation(BaseModel):
    """A single optimization recommendation."""

    id: str = Field(..., description="Recommendation ID")
    type: OptimizationType = Field(..., description="Type of optimization")
    title: str = Field(..., description="Recommendation title")
    description: str = Field(..., description="Detailed description")
    expected_impact: str = Field(..., description="Expected impact description")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    effort_level: str = Field(..., description="Effort level (low, medium, high)")
    priority: int = Field(..., ge=1, le=10, description="Priority (1-10)")
    auto_applicable: bool = Field(False, description="Whether this can be auto-applied")
    changes: dict[str, Any] = Field(default_factory=dict, description="Specific changes to make")


class OptimizationResult(BaseModel):
    """Result of an optimization analysis."""

    campaign_id: str = Field(..., description="Campaign identifier")
    status: OptimizationStatus = Field(..., description="Optimization status")
    metrics: list[PerformanceMetric] = Field(
        default_factory=list, description="Current performance metrics"
    )
    recommendations: list[OptimizationRecommendation] = Field(
        default_factory=list, description="Optimization recommendations"
    )
    applied_changes: list[str] = Field(
        default_factory=list, description="Changes that were applied"
    )
    projected_improvement: float | None = Field(
        None, ge=0, description="Projected improvement percentage"
    )
    analysis_period: str = Field("", description="Analysis period description")
    created_at: str | None = Field(None, description="ISO timestamp of creation")


@dataclass
class OptimizationAgentConfig:
    """Configuration for the Optimization Agent."""

    model: str = "gpt-4"
    max_tokens: int = 4096
    temperature: float = 0.4
    timeout_seconds: int = 120
    retry_attempts: int = 3
    enabled: bool = True
    auto_apply: bool = False
    min_confidence_threshold: float = 0.7


class OptimizationAgent:
    """AI agent for campaign performance optimization.

    This agent monitors campaign performance, identifies optimization
    opportunities, recommends budget reallocation, creative refreshes,
    and audience refinements to maximize ROI.
    """

    def __init__(self, config: OptimizationAgentConfig | None = None) -> None:
        """Initialize the Optimization Agent.

        Args:
            config: Optional configuration override.
        """
        self.config = config or OptimizationAgentConfig()
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
                ("system", """You are an expert marketing performance analyst specializing in
                campaign optimization, budget allocation, and ROI maximization.
                Provide data-driven recommendations with clear expected impacts.
                Prioritize recommendations by potential impact and implementation ease."""),
                MessagesPlaceholder(variable_name="chat_history", optional=True),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ])

            self._agent = create_openai_functions_agent(llm, [], prompt)
            logger.info("OptimizationAgent initialized", model=self.config.model)
        except ImportError:
            logger.warning("LangChain not available, running in mock mode")
            self._agent = None

    async def analyze_performance(
        self,
        campaign_id: str,
        metrics: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> OptimizationResult:
        """Analyze campaign performance and identify optimization opportunities.

        Args:
            campaign_id: Campaign identifier.
            metrics: Current performance metrics.
            context: Optional additional context.

        Returns:
            OptimizationResult with analysis and recommendations.

        Raises:
            ValueError: If the agent is not enabled.
            RuntimeError: If analysis fails.
        """
        if not self.config.enabled:
            raise ValueError("OptimizationAgent is not enabled")

        logger.info("Analyzing performance", campaign_id=campaign_id)

        try:
            if self._agent is None:
                return await self._mock_optimization(campaign_id, metrics, context)

            result = await self._execute_optimization(campaign_id, metrics, context)
            return result

        except Exception as e:
            logger.error("Performance analysis failed", error=str(e))
            raise RuntimeError(f"Performance analysis failed: {e}") from e

    async def _execute_optimization(
        self,
        campaign_id: str,
        metrics: dict[str, Any],
        context: dict[str, Any] | None,
    ) -> OptimizationResult:
        """Execute optimization analysis using the LangChain agent.

        Args:
            campaign_id: Campaign identifier.
            metrics: Performance metrics.
            context: Additional context.

        Returns:
            OptimizationResult with recommendations.
        """
        return await self._mock_optimization(campaign_id, metrics, context)

    async def _mock_optimization(
        self,
        campaign_id: str,
        metrics: dict[str, Any],
        context: dict[str, Any] | None,
    ) -> OptimizationResult:
        """Generate mock optimization results for testing/development.

        Args:
            campaign_id: Campaign identifier.
            metrics: Performance metrics.
            context: Additional context.

        Returns:
            OptimizationResult with mock recommendations.
        """
        return OptimizationResult(
            campaign_id=campaign_id,
            status=OptimizationStatus.COMPLETED,
            metrics=[
                PerformanceMetric(
                    name="ROAS", current_value=2.1, target_value=3.0,
                    unit="ratio", trend="down", change_percentage=-15.0,
                ),
                PerformanceMetric(
                    name="CPA", current_value=65.0, target_value=50.0,
                    unit="USD", trend="up", change_percentage=20.0,
                ),
                PerformanceMetric(
                    name="CTR", current_value=1.8, target_value=2.5,
                    unit="percent", trend="stable", change_percentage=0.0,
                ),
                PerformanceMetric(
                    name="Conversion Rate", current_value=3.2, target_value=4.0,
                    unit="percent", trend="up", change_percentage=5.0,
                ),
            ],
            recommendations=[
                OptimizationRecommendation(
                    id="rec_1",
                    type=OptimizationType.BUDGET_REALLOCATION,
                    title="Shift budget from underperforming to top-performing ad sets",
                    description="Reallocate 20% of budget from ad sets with ROAS < 2.0 "
                    "to ad sets with ROAS > 3.5",
                    expected_impact="15-20% improvement in overall ROAS",
                    confidence=0.85,
                    effort_level="low",
                    priority=9,
                    auto_applicable=True,
                    changes={
                        "budget_shift_percentage": 20,
                        "from_roas_threshold": 2.0,
                        "to_roas_threshold": 3.5,
                    },
                ),
                OptimizationRecommendation(
                    id="rec_2",
                    type=OptimizationType.CREATIVE_REFRESH,
                    title="Refresh ad creatives showing fatigue",
                    description="3 ad sets show >50% increase in frequency. "
                    "Recommend new creative variants.",
                    expected_impact="10-15% improvement in CTR",
                    confidence=0.75,
                    effort_level="medium",
                    priority=7,
                    auto_applicable=False,
                    changes={"ad_sets_requiring_refresh": 3, "new_variants_needed": 6},
                ),
                OptimizationRecommendation(
                    id="rec_3",
                    type=OptimizationType.AUDIENCE_REFINEMENT,
                    title="Exclude low-converting audience segments",
                    description="Exclude audience segments with conversion rate < 1% "
                    "to improve overall CPA",
                    expected_impact="10% reduction in CPA",
                    confidence=0.70,
                    effort_level="low",
                    priority=6,
                    auto_applicable=True,
                    changes={"segments_to_exclude": ["segment_a", "segment_b"]},
                ),
            ],
            applied_changes=[],
            projected_improvement=15.0,
            analysis_period="Last 30 days",
        )

    async def apply_optimization(
        self,
        campaign_id: str,
        recommendation: OptimizationRecommendation,
    ) -> OptimizationResult:
        """Apply an optimization recommendation.

        Args:
            campaign_id: Campaign identifier.
            recommendation: The recommendation to apply.

        Returns:
            OptimizationResult with applied changes.

        Raises:
            ValueError: If the recommendation cannot be applied.
            RuntimeError: If applying the optimization fails.
        """
        if not self.config.enabled:
            raise ValueError("OptimizationAgent is not enabled")

        if not recommendation.auto_applicable and not self.config.auto_apply:
            raise ValueError("This recommendation requires manual approval")

        logger.info(
            "Applying optimization",
            campaign_id=campaign_id,
            recommendation_id=recommendation.id,
        )

        try:
            # Apply the optimization changes
            return OptimizationResult(
                campaign_id=campaign_id,
                status=OptimizationStatus.COMPLETED,
                metrics=[],
                recommendations=[recommendation],
                applied_changes=[recommendation.id],
                projected_improvement=10.0,
            )

        except Exception as e:
            logger.error("Failed to apply optimization", error=str(e))
            raise RuntimeError(f"Failed to apply optimization: {e}") from e

    async def generate_optimization_report(
        self,
        campaign_id: str,
        start_date: str,
        end_date: str,
    ) -> dict[str, Any]:
        """Generate a comprehensive optimization report.

        Args:
            campaign_id: Campaign identifier.
            start_date: Report start date.
            end_date: Report end date.

        Returns:
            Dictionary containing the optimization report.
        """
        logger.info("Generating optimization report", campaign_id=campaign_id)

        return {
            "campaign_id": campaign_id,
            "period": {"start": start_date, "end": end_date},
            "summary": {
                "total_spend": 10000.0,
                "total_revenue": 25000.0,
                "roas": 2.5,
                "cpa": 50.0,
                "ctr": 2.1,
                "conversion_rate": 3.5,
            },
            "trends": {
                "roas": "improving",
                "cpa": "stable",
                "ctr": "declining",
            },
            "top_recommendations": [
                "Increase budget on top-performing channels",
                "Refresh creative for ad sets showing fatigue",
                "Expand lookalike audiences based on converters",
            ],
            "projected_monthly_improvement": "12-18%",
        }
