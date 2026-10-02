"""Critic Agent — Quality assurance, performance evaluation, and governance."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class EvaluationGrade(StrEnum):
    """Performance evaluation grades."""

    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    NEEDS_IMPROVEMENT = "needs_improvement"
    POOR = "poor"
    CRITICAL = "critical"


class ApprovalStatus(StrEnum):
    """Approval status for campaign actions."""

    APPROVED = "approved"
    APPROVED_WITH_CHANGES = "approved_with_changes"
    REQUIRES_REVIEW = "requires_review"
    REJECTED = "rejected"


@dataclass
class PerformanceEvaluation:
    """Evaluation of campaign performance."""

    campaign_id: str
    grade: EvaluationGrade
    roas_score: float
    ctr_score: float
    cpa_score: float
    overall_score: float
    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)


@dataclass
class GovernanceDecision:
    """Governance decision for a proposed action."""

    action: str
    status: ApprovalStatus
    reason: str
    required_changes: list[str] = field(default_factory=list)
    approver: str = "critic_agent"


class CriticAgent:
    """Agent responsible for quality assurance and governance.

    The Critic Agent evaluates campaign performance, reviews
    recommendations from other agents, enforces governance policies,
    and ensures all actions meet quality and compliance standards.
    """

    def __init__(self, model: str = "gpt-4", temperature: float = 0.1) -> None:
        """Initialize the Critic Agent.

        Args:
            model: The LLM model to use for evaluation.
            temperature: Sampling temperature for the model.
        """
        self.model = model
        self.temperature = temperature
        self._evaluations: dict[str, PerformanceEvaluation] = {}
        self._decisions: list[GovernanceDecision] = []

    async def evaluate_performance(
        self,
        campaign_id: str,
        metrics: dict[str, Any],
        targets: dict[str, float],
    ) -> PerformanceEvaluation:
        """Evaluate campaign performance against targets.

        Args:
            campaign_id: Campaign identifier.
            metrics: Current performance metrics.
            targets: Target KPI values.

        Returns:
            PerformanceEvaluation with grade and recommendations.
        """
        logger.info("Evaluating campaign performance", campaign_id=campaign_id)

        # Score individual metrics (0-100 scale)
        roas_score = self._score_metric(
            metrics.get("roas", 0), targets.get("roas", 3.0), higher_is_better=True
        )
        ctr_score = self._score_metric(
            metrics.get("ctr", 0), targets.get("ctr", 0.015), higher_is_better=True
        )
        cpa_score = self._score_metric(
            metrics.get("cpa", 0), targets.get("cpa", 50.0), higher_is_better=False
        )

        # Calculate overall score
        overall_score = (roas_score + ctr_score + cpa_score) / 3

        # Determine grade
        grade = self._score_to_grade(overall_score)

        # Identify strengths and weaknesses
        strengths, weaknesses = self._identify_strengths_weaknesses(
            roas_score, ctr_score, cpa_score
        )

        # Generate recommendations
        recommendations = self._generate_recommendations(
            grade, weaknesses, metrics, targets
        )

        evaluation = PerformanceEvaluation(
            campaign_id=campaign_id,
            grade=grade,
            roas_score=roas_score,
            ctr_score=ctr_score,
            cpa_score=cpa_score,
            overall_score=overall_score,
            strengths=strengths,
            weaknesses=weaknesses,
            recommendations=recommendations,
        )

        self._evaluations[campaign_id] = evaluation
        logger.info(
            "Performance evaluation completed",
            campaign_id=campaign_id,
            grade=grade.value,
            score=overall_score,
        )
        return evaluation

    async def review_action(
        self,
        action: str,
        proposed_changes: dict[str, Any],
        governance_policies: dict[str, Any] | None = None,
    ) -> GovernanceDecision:
        """Review a proposed action against governance policies.

        Args:
            action: Description of the proposed action.
            proposed_changes: Dictionary of proposed changes.
            governance_policies: Governance policies to enforce.

        Returns:
            GovernanceDecision with approval status.
        """
        governance_policies = governance_policies or {}
        required_changes: list[str] = []

        # Check budget change limits
        max_budget_change = governance_policies.get("max_budget_change_pct", 20)
        if "budget_change_pct" in proposed_changes:
            change = abs(proposed_changes["budget_change_pct"])
            if change > max_budget_change:
                required_changes.append(
                    f"Reduce budget change from {change}% to max {max_budget_change}%"
                )

        # Check approval thresholds
        approval_threshold = governance_policies.get("require_approval_above", 1000)
        if "budget_amount" in proposed_changes:
            amount = proposed_changes["budget_amount"]
            if amount > approval_threshold:
                required_changes.append(
                    f"Budget amount ${amount} exceeds auto-approval threshold "
                    f"of ${approval_threshold} — requires human approval"
                )

        # Determine status
        if required_changes:
            status = ApprovalStatus.REQUIRES_REVIEW
            reason = "Action requires modifications to comply with governance policies"
        else:
            status = ApprovalStatus.APPROVED
            reason = "Action complies with all governance policies"

        decision = GovernanceDecision(
            action=action,
            status=status,
            reason=reason,
            required_changes=required_changes,
        )

        self._decisions.append(decision)
        logger.info(
            "Governance review completed",
            action=action,
            status=status.value,
        )
        return decision

    def _score_metric(
        self,
        actual: float,
        target: float,
        higher_is_better: bool = True,
    ) -> float:
        """Score a metric against its target.

        Args:
            actual: Actual metric value.
            target: Target metric value.
            higher_is_better: Whether higher values are better.

        Returns:
            Score from 0 to 100.
        """
        if target <= 0:
            return 50.0

        ratio = actual / target
        if not higher_is_better:
            ratio = 1 / ratio if ratio > 0 else 0

        # Score: 100 at target, scales down/up
        score = min(100.0, ratio * 100)
        return round(score, 1)

    def _score_to_grade(self, score: float) -> EvaluationGrade:
        """Convert a numeric score to a grade.

        Args:
            score: Numeric score from 0 to 100.

        Returns:
            EvaluationGrade enum value.
        """
        if score >= 90:
            return EvaluationGrade.EXCELLENT
        if score >= 75:
            return EvaluationGrade.GOOD
        if score >= 60:
            return EvaluationGrade.ACCEPTABLE
        if score >= 40:
            return EvaluationGrade.NEEDS_IMPROVEMENT
        if score >= 20:
            return EvaluationGrade.POOR
        return EvaluationGrade.CRITICAL

    def _identify_strengths_weaknesses(
        self,
        roas_score: float,
        ctr_score: float,
        cpa_score: float,
    ) -> tuple[list[str], list[str]]:
        """Identify performance strengths and weaknesses.

        Args:
            roas_score: ROAS performance score.
            ctr_score: CTR performance score.
            cpa_score: CPA performance score.

        Returns:
            Tuple of (strengths, weaknesses) lists.
        """
        scores = {
            "ROAS": roas_score,
            "CTR": ctr_score,
            "CPA": cpa_score,
        }

        strengths = [name for name, score in scores.items() if score >= 75]
        weaknesses = [name for name, score in scores.items() if score < 50]

        return strengths, weaknesses

    def _generate_recommendations(
        self,
        grade: EvaluationGrade,
        weaknesses: list[str],
        metrics: dict[str, Any],
        targets: dict[str, float],
    ) -> list[str]:
        """Generate improvement recommendations.

        Args:
            grade: Performance grade.
            weaknesses: Identified weaknesses.
            metrics: Current metrics.
            targets: Target values.

        Returns:
            List of recommendation strings.
        """
        recommendations = []

        if grade in (EvaluationGrade.POOR, EvaluationGrade.CRITICAL):
            recommendations.append(
                "Consider pausing underperforming ad sets and reallocating budget"
            )

        for weakness in weaknesses:
            if weakness == "ROAS":
                recommendations.append(
                    "Review audience targeting — ROAS below target suggests "
                    "mismatch between audience and offer"
                )
            elif weakness == "CTR":
                recommendations.append(
                    "Refresh creative assets — CTR below target indicates "
                    "creative fatigue or poor audience-creative fit"
                )
            elif weakness == "CPA":
                recommendations.append(
                    "Optimize landing page and funnel — CPA above target "
                    "suggests conversion rate issues"
                )

        if not recommendations:
            recommendations.append(
                "Performance is strong — consider scaling budget to capture "
                "additional volume"
            )

        return recommendations

    def get_evaluation(self, campaign_id: str) -> PerformanceEvaluation | None:
        """Retrieve a performance evaluation by campaign ID.

        Args:
            campaign_id: The campaign identifier.

        Returns:
            The PerformanceEvaluation or None if not found.
        """
        return self._evaluations.get(campaign_id)

    def get_decisions(self) -> list[GovernanceDecision]:
        """Get all governance decisions made by this agent.

        Returns:
            List of all GovernanceDecision objects.
        """
        return list(self._decisions)
