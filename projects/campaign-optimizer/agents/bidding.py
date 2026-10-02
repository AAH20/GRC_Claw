"""Bidding Agent — Real-time bid optimization and budget pacing."""

from __future__ import annotations

from typing import Any

from langchain_core.language_models import BaseLanguageModel
from langchain_core.tools import BaseTool

from agents.base import AgentContext, AgentResult, BaseAgent
from core.logging import get_logger

logger = get_logger(__name__)


class BiddingAgent(BaseAgent[dict[str, Any]]):
    """Agent responsible for real-time bid optimization and budget pacing."""

    def __init__(
        self,
        llm: BaseLanguageModel | None = None,
        tools: list[BaseTool] | None = None,
    ) -> None:
        super().__init__(
            name="Bidding Agent",
            description="Real-time bid optimization, budget pacing, and ROAS maximization",
            llm=llm,
            tools=tools,
            timeout=60,
            max_iterations=10,
        )

    async def _execute(self, context: AgentContext) -> AgentResult[dict[str, Any]]:
        self._logger.info(
            "bid_optimization_started",
            campaign_id=context.campaign_id,
            task=context.task,
        )
        optimization_result = self._optimize_bids(context)
        return AgentResult(
            success=True,
            data=optimization_result,
            metadata={
                "agent": self.name,
                "campaign_id": context.campaign_id,
                "adjustments_made": len(optimization_result.get("bid_adjustments", [])),
            },
        )

    def _optimize_bids(self, context: AgentContext) -> dict[str, Any]:
        params = context.parameters
        current_bids = params.get("current_bids", {})
        performance_data = params.get("performance_data", {})
        budget = params.get("daily_budget", 0)
        target_roas = params.get("target_roas", 3.0)
        bid_adjustments = self._calculate_bid_adjustments(
            current_bids, performance_data, target_roas
        )
        pacing_plan = self._create_pacing_plan(budget, performance_data)
        budget_reallocation = self._reallocate_budget(performance_data, budget)
        return {
            "campaign_id": context.campaign_id,
            "bid_adjustments": bid_adjustments,
            "pacing_plan": pacing_plan,
            "budget_reallocation": budget_reallocation,
            "projected_roas": self._project_roas(bid_adjustments, performance_data),
            "confidence_score": 0.85,
        }

    def _calculate_bid_adjustments(
        self,
        current_bids: dict[str, float],
        performance_data: dict[str, Any],
        target_roas: float,
    ) -> list[dict[str, Any]]:
        adjustments = []
        for entity_id, current_bid in current_bids.items():
            entity_perf = performance_data.get(entity_id, {})
            current_roas = entity_perf.get("roas", 0)
            if current_roas >= target_roas * 1.2:
                new_bid = current_bid * 1.15
                action = "increase"
            elif current_roas >= target_roas * 0.8:
                new_bid = current_bid * 1.05
                action = "maintain"
            else:
                new_bid = current_bid * 0.85
                action = "decrease"
            adjustments.append({
                "entity_id": entity_id,
                "current_bid": current_bid,
                "recommended_bid": round(new_bid, 2),
                "action": action,
                "expected_roas_change": round(
                    (new_bid / current_bid - 1) * current_roas, 2
                ) if current_bid > 0 else 0,
            })
        return adjustments

    def _create_pacing_plan(
        self, daily_budget: float, performance_data: dict[str, Any]
    ) -> dict[str, Any]:
        daypart_weights = {
            "morning": 0.20,
            "afternoon": 0.30,
            "evening": 0.35,
            "night": 0.15,
        }
        pacing = {}
        for daypart, weight in daypart_weights.items():
            pacing[daypart] = {
                "budget": round(daily_budget * weight, 2),
                "weight": weight,
                "bid_modifier": 1.0 if daypart in ("afternoon", "evening") else 0.9,
            }
        return {
            "daily_budget": daily_budget,
            "daypart_distribution": pacing,
            "pacing_strategy": "even",
            "overspend_protection": True,
            "underspend_threshold": 0.10,
        }

    def _reallocate_budget(
        self, performance_data: dict[str, Any], total_budget: float
    ) -> list[dict[str, Any]]:
        reallocations = []
        channel_performance = {}
        for channel, data in performance_data.items():
            channel_performance[channel] = data.get("roas", 0)
        if not channel_performance:
            return reallocations
        avg_roas = sum(channel_performance.values()) / len(channel_performance)
        for channel, roas in channel_performance.items():
            if roas < avg_roas * 0.7:
                reallocations.append({
                    "channel": channel,
                    "action": "decrease",
                    "current_allocation_pct": 25,
                    "recommended_allocation_pct": 15,
                    "reason": f"ROAS {roas:.2f} below average {avg_roas:.2f}",
                })
            elif roas > avg_roas * 1.3:
                reallocations.append({
                    "channel": channel,
                    "action": "increase",
                    "current_allocation_pct": 25,
                    "recommended_allocation_pct": 35,
                    "reason": f"ROAS {roas:.2f} above average {avg_roas:.2f}",
                })
        return reallocations

    def _project_roas(
        self, bid_adjustments: list[dict[str, Any]], performance_data: dict[str, Any]
    ) -> float:
        if not bid_adjustments:
            return 0.0
        total_current_spend = sum(
            perf.get("spend", 0) for perf in performance_data.values()
        )
        total_current_revenue = sum(
            perf.get("revenue", 0) for perf in performance_data.values()
        )
        if total_current_spend == 0:
            return 0.0
        current_roas = total_current_revenue / total_current_spend
        avg_bid_change = sum(
            adj["recommended_bid"] / adj["current_bid"] - 1
            for adj in bid_adjustments
            if adj["current_bid"] > 0
        ) / len(bid_adjustments) if bid_adjustments else 0
        return round(current_roas * (1 + avg_bid_change * 0.5), 2)
