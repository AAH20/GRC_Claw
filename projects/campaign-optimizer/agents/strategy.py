"""Strategy Agent — High-level campaign planning and goal decomposition."""

from __future__ import annotations

from typing import Any

from langchain_core.language_models import BaseLanguageModel
from langchain_core.tools import BaseTool

from agents.base import AgentContext, AgentResult, BaseAgent
from core.logging import get_logger

logger = get_logger(__name__)


class StrategyAgent(BaseAgent[dict[str, Any]]):
    """Agent responsible for high-level campaign planning."""

    def __init__(
        self,
        llm: BaseLanguageModel | None = None,
        tools: list[BaseTool] | None = None,
    ) -> None:
        super().__init__(
            name="Strategy Agent",
            description="High-level campaign planning, goal decomposition, and budget allocation",
            llm=llm,
            tools=tools,
            timeout=120,
            max_iterations=5,
        )

    async def _execute(self, context: AgentContext) -> AgentResult[dict[str, Any]]:
        self._logger.info(
            "strategy_planning_started",
            campaign_id=context.campaign_id,
            task=context.task,
        )
        plan = self._build_strategic_plan(context)
        return AgentResult(
            success=True,
            data=plan,
            metadata={
                "agent": self.name,
                "campaign_id": context.campaign_id,
                "plan_version": "1.0",
            },
        )

    def _build_strategic_plan(self, context: AgentContext) -> dict[str, Any]:
        params = context.parameters
        goals = params.get("goals", [])
        budget = params.get("total_budget", 0)
        channels = params.get("channels", ["search", "social", "display"])
        duration_days = params.get("duration_days", 30)
        budget_allocation = self._allocate_budget(budget, channels)
        kpis = self._define_kpis(goals)
        timeline = self._create_timeline(duration_days)
        return {
            "campaign_id": context.campaign_id,
            "goals": goals,
            "budget_allocation": budget_allocation,
            "kpis": kpis,
            "timeline": timeline,
            "channels": channels,
            "risk_assessment": self._assess_risks(params),
        }

    def _allocate_budget(
        self, total_budget: float, channels: list[str]
    ) -> dict[str, float]:
        if not channels or total_budget <= 0:
            return {}
        weights = {
            "search": 0.35,
            "social": 0.30,
            "display": 0.20,
            "email": 0.10,
            "video": 0.05,
        }
        total_weight = sum(weights.get(ch, 0.1) for ch in channels)
        allocation = {}
        for channel in channels:
            weight = weights.get(channel, 0.1)
            allocation[channel] = round(total_budget * (weight / total_weight), 2)
        return allocation

    def _define_kpis(self, goals: list[str]) -> list[dict[str, Any]]:
        kpi_templates = {
            "awareness": {"metric": "impressions", "target": 1000000},
            "engagement": {"metric": "ctr", "target": 0.03},
            "conversion": {"metric": "cpa", "target": 50.0},
            "retention": {"metric": "roas", "target": 4.0},
            "reach": {"metric": "unique_reach", "target": 500000},
        }
        kpis = []
        for goal in goals:
            template = kpi_templates.get(goal.lower(), {"metric": goal, "target": 0})
            kpis.append({
                "goal": goal,
                "metric": template["metric"],
                "target": template["target"],
                "measurement": "daily",
            })
        return kpis

    def _create_timeline(self, duration_days: int) -> list[dict[str, Any]]:
        phases = [
            {
                "phase": "research",
                "duration_days": max(1, int(duration_days * 0.15)),
                "activities": ["market_research", "audience_analysis", "competitor_benchmark"],
            },
            {
                "phase": "creative",
                "duration_days": max(1, int(duration_days * 0.20)),
                "activities": ["copywriting", "asset_creation", "ab_test_setup"],
            },
            {
                "phase": "launch",
                "duration_days": max(1, int(duration_days * 0.10)),
                "activities": ["campaign_launch", "initial_monitoring", "quick_optimizations"],
            },
            {
                "phase": "optimize",
                "duration_days": max(1, int(duration_days * 0.40)),
                "activities": ["performance_monitoring", "bid_optimization", "budget_reallocation"],
            },
            {
                "phase": "scale",
                "duration_days": max(1, int(duration_days * 0.15)),
                "activities": ["scale_winners", "expand_audiences", "final_reporting"],
            },
        ]
        return phases

    def _assess_risks(self, params: dict[str, Any]) -> list[dict[str, Any]]:
        risks = []
        budget = params.get("total_budget", 0)
        duration = params.get("duration_days", 30)
        if budget > 100000:
            risks.append({
                "type": "high_budget",
                "severity": "medium",
                "mitigation": "Implement daily budget caps and real-time monitoring",
            })
        if duration < 14:
            risks.append({
                "type": "short_duration",
                "severity": "low",
                "mitigation": "Focus on proven audiences and creative variants",
            })
        return risks
