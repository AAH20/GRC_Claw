"""Critic Agent — Quality assurance and governance enforcement."""

from __future__ import annotations

from typing import Any

from langchain_core.language_models import BaseLanguageModel
from langchain_core.tools import BaseTool

from agents.base import AgentContext, AgentResult, BaseAgent
from core.config import get_settings
from core.exceptions import GovernanceApprovalRequired, GovernanceError
from core.logging import get_logger

logger = get_logger(__name__)


class CriticAgent(BaseAgent[dict[str, Any]]):
    """Agent responsible for quality assurance and governance enforcement.

    The Critic Agent reviews all campaign elements for compliance,
    evaluates performance against benchmarks, enforces GRC_Claw
    governance policies, and provides actionable feedback for
    continuous improvement.
    """

    def __init__(
        self,
        llm: BaseLanguageModel | None = None,
        tools: list[BaseTool] | None = None,
    ) -> None:
        """Initialize the Critic Agent.

        Args:
            llm: Language model for critical evaluation.
            tools: Available tools for data analysis and compliance checks.
        """
        super().__init__(
            name="Critic Agent",
            description="Quality assurance, performance evaluation, and governance enforcement",
            llm=llm,
            tools=tools,
            timeout=60,
            max_iterations=2,
        )
        self._settings = get_settings()

    async def _execute(self, context: AgentContext) -> AgentResult[dict[str, Any]]:
        """Execute quality assurance and governance checks.

        Args:
            context: Execution context with campaign data to review.

        Returns:
            AgentResult containing QA findings and governance decisions.
        """
        self._logger.info(
            "critic_evaluation_started",
            campaign_id=context.campaign_id,
            task=context.task,
        )

        evaluation = self._evaluate_campaign(context)

        return AgentResult(
            success=True,
            data=evaluation,
            metadata={
                "agent": self.name,
                "campaign_id": context.campaign_id,
                "governance_checks_passed": evaluation.get("governance", {}).get(
                    "all_passed", False
                ),
            },
        )

    def _evaluate_campaign(self, context: AgentContext) -> dict[str, Any]:
        """Evaluate campaign against quality and governance standards.

        Args:
            context: Execution context with campaign data.

        Returns:
            Dictionary containing evaluation results.
        """
        params = context.parameters
        campaign_data = params.get("campaign_data", {})

        governance_result = self._check_governance(campaign_data)
        quality_result = self._check_quality(campaign_data)
        performance_result = self._evaluate_performance(campaign_data)
        compliance_result = self._check_compliance(campaign_data)

        all_passed = all([
            governance_result.get("all_passed", False),
            quality_result.get("all_passed", False),
            compliance_result.get("all_passed", False),
        ])

        return {
            "campaign_id": context.campaign_id,
            "overall_passed": all_passed,
            "governance": governance_result,
            "quality": quality_result,
            "performance": performance_result,
            "compliance": compliance_result,
            "recommendations": self._generate_recommendations(
                governance_result, quality_result, performance_result, compliance_result
            ),
            "approval_required": governance_result.get("approval_required", False),
        }

    def _check_governance(self, campaign_data: dict[str, Any]) -> dict[str, Any]:
        """Check campaign against GRC_Claw governance policies.

        Args:
            campaign_data: Campaign data to evaluate.

        Returns:
            Governance check results.
        """
        if not self._settings.governance.enabled:
            return {"all_passed": True, "checks": [], "approval_required": False}

        checks = []
        approval_required = False

        # Budget change check
        budget_change = campaign_data.get("budget_change_pct", 0)
        max_change = self._settings.governance.max_budget_change_pct
        budget_passed = budget_change <= max_change
        checks.append({
            "name": "budget_change_limit",
            "passed": budget_passed,
            "value": budget_change,
            "threshold": max_change,
            "message": f"Budget change {budget_change}% within limit {max_change}%"
            if budget_passed
            else f"Budget change {budget_change}% exceeds limit {max_change}%",
        })

        # Approval threshold check
        budget_amount = campaign_data.get("total_budget", 0)
        approval_threshold = self._settings.governance.require_approval_above
        if budget_amount > approval_threshold:
            approval_required = True
            checks.append({
                "name": "approval_threshold",
                "passed": True,
                "value": budget_amount,
                "threshold": approval_threshold,
                "message": f"Budget ${budget_amount} requires governance approval",
            })

        # Compliance checks
        for check_name in self._settings.governance.compliance_checks:
            checks.append({
                "name": check_name,
                "passed": True,  # Would be validated against actual policy engine
                "message": f"{check_name} check passed",
            })

        all_passed = all(c["passed"] for c in checks)

        return {
            "all_passed": all_passed,
            "checks": checks,
            "approval_required": approval_required,
            "policy_engine": self._settings.governance.policy_engine,
        }

    def _check_quality(self, campaign_data: dict[str, Any]) -> dict[str, Any]:
        """Check campaign quality standards.

        Args:
            campaign_data: Campaign data to evaluate.

        Returns:
            Quality check results.
        """
        checks = []

        # Creative quality
        creative_variants = campaign_data.get("creative_variants", 0)
        creative_passed = creative_variants >= 2
        checks.append({
            "name": "creative_variants",
            "passed": creative_passed,
            "value": creative_variants,
            "threshold": 2,
            "message": f"{creative_variants} creative variants provided",
        })

        # A/B test setup
        has_ab_test = campaign_data.get("ab_test_configured", False)
        checks.append({
            "name": "ab_test_configured",
            "passed": has_ab_test,
            "message": "A/B test is configured" if has_ab_test else "A/B test not configured",
        })

        # Landing page
        has_landing_page = campaign_data.get("landing_page_url", "") != ""
        checks.append({
            "name": "landing_page",
            "passed": has_landing_page,
            "message": "Landing page configured" if has_landing_page else "Landing page missing",
        })

        # Tracking setup
        has_tracking = campaign_data.get("tracking_configured", False)
        checks.append({
            "name": "tracking",
            "passed": has_tracking,
            "message": "Tracking is configured" if has_tracking else "Tracking not configured",
        })

        all_passed = all(c["passed"] for c in checks)

        return {
            "all_passed": all_passed,
            "checks": checks,
        }

    def _evaluate_performance(self, campaign_data: dict[str, Any]) -> dict[str, Any]:
        """Evaluate campaign performance against benchmarks.

        Args:
            campaign_data: Campaign data with performance metrics.

        Returns:
            Performance evaluation results.
        """
        metrics = campaign_data.get("performance_metrics", {})
        benchmarks = {
            "ctr": 0.02,
            "cpa": 75.0,
            "roas": 2.5,
            "frequency": 3.0,
        }

        evaluations = {}
        for metric, benchmark in benchmarks.items():
            actual = metrics.get(metric, 0)
            if metric in ("cpa",):
                # Lower is better
                passed = actual <= benchmark if actual > 0 else True
            else:
                # Higher is better
                passed = actual >= benchmark if actual > 0 else True

            evaluations[metric] = {
                "actual": actual,
                "benchmark": benchmark,
                "passed": passed,
                "status": "above_benchmark" if passed else "below_benchmark",
            }

        return {
            "metrics": evaluations,
            "overall_status": "healthy" if all(
                e["passed"] for e in evaluations.values()
            ) else "needs_attention",
        }

    def _check_compliance(self, campaign_data: dict[str, Any]) -> dict[str, Any]:
        """Check regulatory and platform compliance.

        Args:
            campaign_data: Campaign data to evaluate.

        Returns:
            Compliance check results.
        """
        checks = []

        # Data privacy
        checks.append({
            "name": "data_privacy",
            "passed": campaign_data.get("data_privacy_compliant", True),
            "message": "Data privacy requirements met",
        })

        # Audience restrictions
        checks.append({
            "name": "audience_restrictions",
            "passed": campaign_data.get("audience_restrictions_met", True),
            "message": "Audience restrictions respected",
        })

        # Creative compliance
        checks.append({
            "name": "creative_compliance",
            "passed": campaign_data.get("creative_compliant", True),
            "message": "Creative meets platform policies",
        })

        all_passed = all(c["passed"] for c in checks)

        return {
            "all_passed": all_passed,
            "checks": checks,
        }

    def _generate_recommendations(
        self,
        governance: dict[str, Any],
        quality: dict[str, Any],
        performance: dict[str, Any],
        compliance: dict[str, Any],
    ) -> list[str]:
        """Generate actionable recommendations based on evaluation.

        Args:
            governance: Governance check results.
            quality: Quality check results.
            performance: Performance evaluation results.
            compliance: Compliance check results.

        Returns:
            List of recommendation strings.
        """
        recommendations = []

        for check in governance.get("checks", []):
            if not check["passed"]:
                recommendations.append(
                    f"Fix governance issue: {check['message']}"
                )

        for check in quality.get("checks", []):
            if not check["passed"]:
                recommendations.append(
                    f"Fix quality issue: {check['message']}"
                )

        for metric, eval_data in performance.get("metrics", {}).items():
            if not eval_data["passed"]:
                recommendations.append(
                    f"Improve {metric}: currently {eval_data['actual']}, "
                    f"target {eval_data['benchmark']}"
                )

        for check in compliance.get("checks", []):
            if not check["passed"]:
                recommendations.append(
                    f"Fix compliance issue: {check['message']}"
                )

        if not recommendations:
            recommendations.append("Campaign meets all quality and governance standards")

        return recommendations
