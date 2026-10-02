"""Bid Management Agent — optimizes CPC/CPM bids using performance signals."""

from __future__ import annotations

from typing import Any

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


class BidRecommendation(BaseModel):
    """A bid recommendation for a specific campaign or ad group.

    Attributes:
        campaign_id: The campaign identifier.
        ad_group_id: The ad group identifier (optional).
        current_bid: The current bid amount in USD.
        recommended_bid: The recommended bid amount in USD.
        reason: Human-readable explanation for the recommendation.
        confidence: Confidence level (0.0–1.0).
    """

    campaign_id: str
    ad_group_id: str | None = None
    current_bid: float = 0.0
    recommended_bid: float = 0.0
    reason: str = ""
    confidence: float = 0.0


class BidManagementResult(BaseModel):
    """Result of a bid management operation.

    Attributes:
        recommendations: List of bid recommendations.
        total_recommendations: Total number of recommendations.
    """

    recommendations: list[BidRecommendation] = Field(default_factory=list)
    total_recommendations: int = 0


class BidManagementAgent:
    """Agent responsible for bid optimization across ad platforms.

    Analyzes performance metrics (CTR, conversion rate, CPA) and recommends
    bid adjustments to maximize ROI while staying within budget constraints.
    """

    def __init__(
        self,
        model: str = "gpt-4o",
        min_bid: float = 0.01,
        max_bid: float = 100.0,
    ) -> None:
        """Initialize the Bid Management Agent.

        Args:
            model: The LLM model to use for bid analysis.
            min_bid: Minimum allowed bid in USD.
            max_bid: Maximum allowed bid in USD.
        """
        self.model = model
        self.min_bid = min_bid
        self.max_bid = max_bid
        self._llm: Any = None

    def _get_llm(self) -> Any:
        """Lazy-load the LLM client.

        Returns:
            The LangChain LLM instance.
        """
        if self._llm is None:
            from langchain_openai import ChatOpenAI

            self._llm = ChatOpenAI(model=self.model, temperature=0.2)
        return self._llm

    async def optimize_bids(
        self,
        campaign_ids: list[str],
        performance_data: dict[str, Any] | None = None,
    ) -> BidManagementResult:
        """Optimize bids for the given campaigns.

        Args:
            campaign_ids: List of campaign IDs to optimize.
            performance_data: Optional performance metrics per campaign.

        Returns:
            A BidManagementResult with recommendations.

        Raises:
            ValueError: If campaign_ids is empty.
        """
        if not campaign_ids:
            raise ValueError("At least one campaign ID is required")

        logger.info("Starting bid optimization", campaign_count=len(campaign_ids))

        recommendations: list[BidRecommendation] = []

        for campaign_id in campaign_ids:
            rec = await self._analyze_campaign(campaign_id, performance_data)
            if rec:
                recommendations.append(rec)

        result = BidManagementResult(
            recommendations=recommendations,
            total_recommendations=len(recommendations),
        )

        logger.info("Bid optimization complete", count=len(recommendations))
        return result

    async def _analyze_campaign(
        self,
        campaign_id: str,
        performance_data: dict[str, Any] | None,
    ) -> BidRecommendation | None:
        """Analyze a single campaign and generate a bid recommendation.

        Args:
            campaign_id: The campaign to analyze.
            performance_data: Optional performance metrics.

        Returns:
            A BidRecommendation or None if analysis fails.
        """
        data = (performance_data or {}).get(campaign_id, {})
        current_bid = float(data.get("current_bid", 1.0))
        ctr = float(data.get("ctr", 0.02))
        conversion_rate = float(data.get("conversion_rate", 0.03))
        cpa = float(data.get("cpa", 50.0))
        target_cpa = float(data.get("target_cpa", 40.0))

        # Simple heuristic-based bid adjustment
        if cpa > 0 and target_cpa > 0:
            ratio = target_cpa / cpa
            recommended = current_bid * ratio
        elif ctr > 0.05:
            recommended = current_bid * 1.1
        elif ctr < 0.01:
            recommended = current_bid * 0.85
        else:
            recommended = current_bid

        recommended = max(self.min_bid, min(self.max_bid, round(recommended, 2)))

        reason = self._build_reason(ctr, conversion_rate, cpa, target_cpa)
        confidence = self._compute_confidence(data)

        return BidRecommendation(
            campaign_id=campaign_id,
            current_bid=current_bid,
            recommended_bid=recommended,
            reason=reason,
            confidence=confidence,
        )

    def _build_reason(
        self,
        ctr: float,
        conversion_rate: float,
        cpa: float,
        target_cpa: float,
    ) -> str:
        """Build a human-readable reason for the bid change.

        Args:
            ctr: Click-through rate.
            conversion_rate: Conversion rate.
            cpa: Current cost per acquisition.
            target_cpa: Target cost per acquisition.

        Returns:
            A reason string.
        """
        if cpa > target_cpa * 1.2:
            return f"CPA (${cpa:.2f}) exceeds target (${target_cpa:.2f}) — reducing bid"
        if cpa < target_cpa * 0.8:
            return (
                f"CPA (${cpa:.2f}) below target (${target_cpa:.2f}) — "
                f"increasing bid to capture more volume"
            )
        if ctr > 0.05:
            return f"Strong CTR ({ctr:.1%}) — increasing bid to improve ad position"
        if ctr < 0.01:
            return f"Low CTR ({ctr:.1%}) — reducing bid to cut waste"
        return "Performance within target range — maintaining current bid"

    def _compute_confidence(self, data: dict[str, Any]) -> float:
        """Compute confidence score based on data completeness.

        Args:
            data: Performance data dictionary.

        Returns:
            A confidence score between 0.0 and 1.0.
        """
        required_keys = {"ctr", "conversion_rate", "cpa", "current_bid"}
        present = sum(1 for k in required_keys if k in data)
        return round(present / len(required_keys), 2)
