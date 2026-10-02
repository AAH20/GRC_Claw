"""Budget Allocation Agent — distributes budget across campaigns based on ROI."""

from __future__ import annotations

from typing import Any

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


class BudgetAllocation(BaseModel):
    """A budget allocation for a specific campaign.

    Attributes:
        campaign_id: The campaign identifier.
        current_budget: Current daily budget in USD.
        recommended_budget: Recommended daily budget in USD.
        reason: Human-readable explanation.
        expected_roi: Expected return on investment (ratio).
    """

    campaign_id: str
    current_budget: float = 0.0
    recommended_budget: float = 0.0
    reason: str = ""
    expected_roi: float = 0.0


class BudgetAllocationResult(BaseModel):
    """Result of a budget allocation operation.

    Attributes:
        total_budget: Total budget to allocate.
        allocations: List of budget allocations.
        total_allocated: Sum of all recommended budgets.
    """

    total_budget: float
    allocations: list[BudgetAllocation] = Field(default_factory=list)
    total_allocated: float = 0.0


class BudgetAllocationAgent:
    """Agent responsible for budget distribution across campaigns.

    Analyzes campaign performance and ROI to recommend optimal budget
    allocation that maximizes overall return on ad spend.
    """

    def __init__(
        self,
        model: str = "gpt-4o",
        min_budget: float = 1.0,
    ) -> None:
        """Initialize the Budget Allocation Agent.

        Args:
            model: The LLM model to use for budget analysis.
            min_budget: Minimum daily budget per campaign in USD.
        """
        self.model = model
        self.min_budget = min_budget
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

    async def allocate(
        self,
        total_budget: float,
        campaign_ids: list[str],
        performance_data: dict[str, Any] | None = None,
    ) -> BudgetAllocationResult:
        """Allocate budget across campaigns.

        Args:
            total_budget: Total daily budget to allocate in USD.
            campaign_ids: List of campaign IDs to allocate budget for.
            performance_data: Optional performance metrics per campaign.

        Returns:
            A BudgetAllocationResult with per-campaign allocations.

        Raises:
            ValueError: If total_budget is negative or campaign_ids is empty.
        """
        if total_budget < 0:
            raise ValueError("Total budget cannot be negative")
        if not campaign_ids:
            raise ValueError("At least one campaign ID is required")

        logger.info(
            "Starting budget allocation",
            total_budget=total_budget,
            campaign_count=len(campaign_ids),
        )

        data = performance_data or {}
        allocations: list[BudgetAllocation] = []

        # Compute ROI scores for weighting
        roi_scores: dict[str, float] = {}
        for cid in campaign_ids:
            campaign_data = data.get(cid, {})
            revenue = float(campaign_data.get("revenue", 0))
            spend = float(campaign_data.get("spend", 0))
            roi_scores[cid] = revenue / spend if spend > 0 else 1.0

        total_roi = sum(roi_scores.values()) or 1.0

        for cid in campaign_ids:
            weight = roi_scores[cid] / total_roi
            recommended = max(self.min_budget, round(total_budget * weight, 2))
            current = float(data.get(cid, {}).get("current_budget", 0))

            allocations.append(
                BudgetAllocation(
                    campaign_id=cid,
                    current_budget=current,
                    recommended_budget=recommended,
                    reason=self._build_reason(roi_scores[cid], weight),
                    expected_roi=round(roi_scores[cid], 2),
                )
            )

        # Normalize to ensure total doesn't exceed budget
        total_allocated = sum(a.recommended_budget for a in allocations)
        if total_allocated > total_budget:
            scale = total_budget / total_allocated
            for a in allocations:
                a.recommended_budget = max(self.min_budget, round(a.recommended_budget * scale, 2))
            total_allocated = sum(a.recommended_budget for a in allocations)

        result = BudgetAllocationResult(
            total_budget=total_budget,
            allocations=allocations,
            total_allocated=round(total_allocated, 2),
        )

        logger.info("Budget allocation complete", total_allocated=total_allocated)
        return result

    def _build_reason(self, roi: float, weight: float) -> str:
        """Build a human-readable reason for the budget allocation.

        Args:
            roi: The campaign's ROI ratio.
            weight: The allocation weight.

        Returns:
            A reason string.
        """
        if roi > 3.0:
            return f"Strong ROI ({roi:.1f}x) — allocating {weight:.0%} of budget"
        if roi > 1.5:
            return f"Positive ROI ({roi:.1f}x) — maintaining allocation at {weight:.0%}"
        if roi > 0:
            return f"Low ROI ({roi:.1f}x) — reducing allocation to {weight:.0%}"
        return "No conversion data — allocating minimum budget for testing"
