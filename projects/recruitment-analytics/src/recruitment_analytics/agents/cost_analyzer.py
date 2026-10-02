"""Cost Analyzer Agent - analyzes recruitment costs and ROI."""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from langchain_core.prompts import ChatPromptTemplate

from recruitment_analytics.agents.base import BaseAgent
from recruitment_analytics.integrations.hrms_client import HRMSClient
from recruitment_analytics.models.schemas import (
    CostAnalysisRequest,
    CostAnalysisResponse,
    CostBreakdown,
    CostCategory,
    CostReport,
)


class CostAnalyzerAgent(BaseAgent[CostAnalysisRequest, CostAnalysisResponse]):
    """Agent that analyzes recruitment costs, cost per hire,
    budget variance, and ROI metrics.
    """

    def __init__(self, hrms_client: HRMSClient | None = None) -> None:
        super().__init__()
        self.hrms_client = hrms_client

    @property
    def agent_name(self) -> str:
        return "Cost Analyzer"

    async def run(self, request: CostAnalysisRequest) -> CostAnalysisResponse:
        """Analyze recruitment costs and generate cost report.

        Args:
            request: Cost analysis request with date range and optional budget.

        Returns:
            Cost analysis response with report and trends.
        """
        if self.hrms_client:
            raw_data = await self.hrms_client.get_hiring_costs(
                start_date=request.start_date,
                end_date=request.end_date,
                department=request.department,
            )
        else:
            raw_data = self._generate_sample_data()

        breakdown = self._compute_cost_breakdown(raw_data)
        total_cost = sum(b.amount for b in breakdown)
        total_hires = sum(b.hires_attributed for b in breakdown)

        budget_variance = None
        if request.budget:
            budget_variance = request.budget - total_cost

        report = CostReport(
            id=str(uuid.uuid4()),
            name=f"Cost Report {request.start_date} to {request.end_date}",
            start_date=request.start_date,
            end_date=request.end_date,
            department=request.department,
            role=request.role,
            total_cost=total_cost,
            total_hires=total_hires,
            cost_per_hire=round(total_cost / total_hires, 2) if total_hires > 0 else Decimal("0"),
            breakdown=breakdown,
            budget_variance=budget_variance,
            insights=self._generate_insights(breakdown, total_cost, total_hires),
            recommendations=self._generate_recommendations(breakdown, total_cost),
        )

        trends = self._generate_trends(report)

        return CostAnalysisResponse(
            report=report,
            trends=trends,
        )

    def _compute_cost_breakdown(self, raw_data: dict) -> list[CostBreakdown]:
        """Compute cost breakdown by category."""
        breakdown: list[CostBreakdown] = []
        categories = raw_data.get("categories", {})
        total_cost = sum(Decimal(str(v.get("amount", 0))) for v in categories.values())

        for cat_name, cat_data in categories.items():
            try:
                category = CostCategory(cat_name)
            except ValueError:
                category = CostCategory.OTHER

            amount = Decimal(str(cat_data.get("amount", 0)))
            hires = cat_data.get("hires_attributed", 0)

            breakdown.append(
                CostBreakdown(
                    category=category,
                    amount=amount,
                    percentage_of_total=round(float(amount / total_cost), 4) if total_cost > 0 else 0.0,
                    hires_attributed=hires,
                    cost_per_hire=round(amount / hires, 2) if hires > 0 else Decimal("0"),
                )
            )

        return sorted(breakdown, key=lambda b: b.amount, reverse=True)

    def _generate_insights(
        self, breakdown: list[CostBreakdown], total_cost: Decimal, total_hires: int
    ) -> list[str]:
        """Generate insights from cost data."""
        insights: list[str] = []

        if not breakdown:
            return ["No cost data available for analysis"]

        # Highest cost category
        highest = breakdown[0]
        insights.append(
            f"Highest cost category: {highest.category.value} (${highest.amount:,.2f}, {highest.percentage_of_total:.1%})"
        )

        # Cost per hire analysis
        if total_hires > 0:
            cph = total_cost / total_hires
            if cph > Decimal("10000"):
                insights.append(
                    f"Cost per hire (${cph:,.2f}) exceeds $10K threshold"
                )
            elif cph < Decimal("3000"):
                insights.append(
                    f"Cost per hire (${cph:,.2f}) is excellent"
                )

        # Efficiency analysis
        efficient = [b for b in breakdown if b.cost_per_hire < Decimal("5000") and b.hires_attributed > 0]
        if efficient:
            insights.append(
                f"{len(efficient)} categories have cost per hire below $5K"
            )

        return insights

    def _generate_recommendations(
        self, breakdown: list[CostBreakdown], total_cost: Decimal
    ) -> list[str]:
        """Generate cost optimization recommendations."""
        recs: list[str] = []

        # Find expensive categories
        expensive = [b for b in breakdown if b.cost_per_hire > Decimal("8000")]
        for cat in expensive:
            recs.append(
                f"Review {cat.category.value} spending - cost per hire (${cat.cost_per_hire:,.2f}) is high"
            )

        # Find efficient categories to expand
        efficient = [b for b in breakdown if b.cost_per_hire < Decimal("4000") and b.hires_attributed > 2]
        for cat in efficient:
            recs.append(
                f"Consider increasing investment in {cat.category.value} - strong ROI"
            )

        if not recs:
            recs.append("Continue monitoring cost metrics for optimization opportunities")

        return recs

    def _generate_trends(self, report: CostReport) -> list[dict]:
        """Generate cost trend data."""
        return [
            {
                "month": (report.start_date.replace(day=1)).isoformat(),
                "total_cost": float(report.total_cost),
                "cost_per_hire": float(report.cost_per_hire),
                "total_hires": report.total_hires,
            }
        ]

    def _generate_sample_data(self) -> dict:
        """Generate sample cost data for testing/demo purposes."""
        return {
            "categories": {
                "job_board": {"amount": 15000.0, "hires_attributed": 8},
                "referral": {"amount": 7500.0, "hires_attributed": 15},
                "agency": {"amount": 30000.0, "hires_attributed": 5},
                "recruiter": {"amount": 45000.0, "hires_attributed": 10},
                "campus": {"amount": 5000.0, "hires_attributed": 3},
                "tools": {"amount": 3000.0, "hires_attributed": 0},
            }
        }
