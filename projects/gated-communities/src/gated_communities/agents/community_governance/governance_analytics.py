"""Governance Analytics Agent for community governance."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any

from community_governance.agents.base import BaseAgent
from community_governance.config.logging_config import get_logger
from community_governance.exceptions import AgentExecutionError
from community_governance.models.analytics import (
    GovernanceAnalytics,
    GovernanceHealthScore,
    GovernanceSummary,
)
from community_governance.models.dispute import Dispute, DisputeStatus
from community_governance.models.governance_action import ActionStatus, GovernanceAction
from community_governance.models.policy import Policy, PolicyStatus

if TYPE_CHECKING:
    from langchain_core.language_models import BaseLanguageModel

    from community_governance.models.rule import Rule


logger = get_logger(__name__)


class GovernanceAnalyticsAgent(BaseAgent[dict[str, Any], GovernanceAnalytics]):
    """Agent responsible for generating governance analytics and insights.

    Uses LangChain DeepAgents to analyze governance data, identify trends,
    calculate health scores, and provide actionable recommendations for
    improving community governance.
    """

    def __init__(
        self,
        llm: BaseLanguageModel | None = None,
        actions: list[GovernanceAction] | None = None,
        rules: list[Rule] | None = None,
        disputes: list[Dispute] | None = None,
        policies: list[Policy] | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the Governance Analytics Agent.

        Args:
            llm: Language model for analytics reasoning.
            actions: List of governance actions to analyze.
            rules: List of rules to include in analytics.
            disputes: List of disputes to include in analytics.
            policies: List of policies to include in analytics.
            **kwargs: Additional configuration options.
        """
        super().__init__(llm=llm, name="governance_analytics", **kwargs)
        self.actions = actions or []
        self.rules = rules or []
        self.disputes = disputes or []
        self.policies = policies or []

    async def _setup(self) -> None:
        """Setup analytics data indices."""
        logger.info(
            f"Governance Analytics Agent loaded with {len(self.actions)} actions, "
            f"{len(self.rules)} rules, {len(self.disputes)} disputes, "
            f"{len(self.policies)} policies",
            agent_name=self.name,
        )

    async def execute(self, input_data: dict[str, Any]) -> GovernanceAnalytics:
        """Generate comprehensive governance analytics.

        Args:
            input_data: Dictionary containing:
                - period_start: Start of analytics period (ISO format)
                - period_end: End of analytics period (ISO format)
                - focus_areas: Optional list of areas to focus on

        Returns:
            Comprehensive governance analytics.

        Raises:
            AgentExecutionError: If analytics generation fails.
        """
        try:
            period_start_str = input_data.get("period_start")
            period_end_str = input_data.get("period_end")

            if period_start_str and period_end_str:
                period_start = datetime.fromisoformat(period_start_str)
                period_end = datetime.fromisoformat(period_end_str)
            else:
                period_end = datetime.utcnow()
                period_start = period_end - timedelta(days=30)

            focus_areas = input_data.get("focus_areas", [])

            logger.info(
                f"Generating analytics for period {period_start} to {period_end}",
                agent_name=self.name,
                focus_areas=focus_areas,
            )

            period_actions = self._filter_by_period(self.actions, period_start, period_end)
            period_disputes = self._filter_by_period(self.disputes, period_start, period_end)

            violations_by_category = self._calculate_violations_by_category(period_actions)
            disputes_by_status = self._calculate_disputes_by_status(period_disputes)
            actions_by_type = self._calculate_actions_by_type(period_actions)
            top_violated_rules = self._get_top_violated_rules(period_actions)
            resolution_time_trend = self._calculate_resolution_time_trend(period_disputes)

            health_score = self._calculate_health_score(
                period_actions, period_disputes, violations_by_category
            )

            if self.llm:
                recommendations = await self._generate_recommendations_with_llm(
                    health_score, violations_by_category, focus_areas
                )
            else:
                recommendations = self._generate_recommendations(
                    health_score, violations_by_category
                )

            analytics = GovernanceAnalytics(
                period_start=period_start,
                period_end=period_end,
                total_actions=len(period_actions),
                total_rules=len([r for r in self.rules if r.is_active]),
                total_disputes=len(period_disputes),
                total_policies=len([p for p in self.policies if p.status == PolicyStatus.ACTIVE]),
                violations_by_category=violations_by_category,
                disputes_by_status=disputes_by_status,
                actions_by_type=actions_by_type,
                top_violated_rules=top_violated_rules,
                resolution_time_trend=resolution_time_trend,
                health_score=health_score,
                recommendations=recommendations,
            )

            logger.info(
                f"Analytics generated: health score {health_score.overall_score:.1f}",
                agent_name=self.name,
                health_score=health_score.overall_score,
            )

            return analytics

        except Exception as e:
            logger.error(f"Analytics generation failed: {e}", error=str(e))
            raise AgentExecutionError(self.name, str(e)) from e

    def _filter_by_period(
        self, items: list[Any], start: datetime, end: datetime
    ) -> list[Any]:
        """Filter items by creation date within the period."""
        return [
            item
            for item in items
            if hasattr(item, "created_at") and start <= item.created_at <= end
        ]

    def _calculate_violations_by_category(
        self, actions: list[GovernanceAction]
    ) -> dict[str, int]:
        """Calculate violations grouped by category."""
        violations: dict[str, int] = {}
        for action in actions:
            if action.status == ActionStatus.REJECTED:
                category = action.metadata.get("category", "unknown")
                violations[category] = violations.get(category, 0) + 1
        return violations

    def _calculate_disputes_by_status(self, disputes: list[Dispute]) -> dict[str, int]:
        """Calculate disputes grouped by status."""
        status_counts: dict[str, int] = {}
        for dispute in disputes:
            status = dispute.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        return status_counts

    def _calculate_actions_by_type(self, actions: list[GovernanceAction]) -> dict[str, int]:
        """Calculate actions grouped by type."""
        type_counts: dict[str, int] = {}
        for action in actions:
            action_type = action.action_type.value
            type_counts[action_type] = type_counts.get(action_type, 0) + 1
        return type_counts

    def _get_top_violated_rules(
        self, actions: list[GovernanceAction]
    ) -> list[dict[str, Any]]:
        """Get the most frequently violated rules."""
        rule_violations: dict[str, int] = {}
        for action in actions:
            if action.status == ActionStatus.REJECTED:
                rule_id = action.metadata.get("rule_id", "unknown")
                rule_violations[rule_id] = rule_violations.get(rule_id, 0) + 1

        sorted_rules = sorted(rule_violations.items(), key=lambda x: x[1], reverse=True)[:5]
        return [{"rule_id": rule_id, "violation_count": count} for rule_id, count in sorted_rules]

    def _calculate_resolution_time_trend(
        self, disputes: list[Dispute]
    ) -> list[dict[str, Any]]:
        """Calculate resolution time trend data."""
        resolved_disputes = [
            d for d in disputes if d.status == DisputeStatus.RESOLVED and d.resolved_at
        ]
        if not resolved_disputes:
            return []

        weekly_data: dict[str, list[float]] = {}
        for dispute in resolved_disputes:
            week_key = dispute.created_at.strftime("%Y-W%U")
            resolution_hours = (
                (dispute.resolved_at - dispute.created_at).total_seconds() / 3600
            )
            weekly_data.setdefault(week_key, []).append(resolution_hours)

        trend = []
        for week, hours_list in sorted(weekly_data.items()):
            avg_hours = sum(hours_list) / len(hours_list)
            trend.append(
                {
                    "week": week,
                    "average_resolution_hours": round(avg_hours, 2),
                    "dispute_count": len(hours_list),
                }
            )
        return trend

    def _calculate_health_score(
        self,
        actions: list[GovernanceAction],
        disputes: list[Dispute],
        violations_by_category: dict[str, int],
    ) -> GovernanceHealthScore:
        """Calculate the governance health score."""
        total_violations = sum(violations_by_category.values())
        total_actions = len(actions)

        if total_actions > 0:
            rule_compliance_rate = ((total_actions - total_violations) / total_actions) * 100
        else:
            rule_compliance_rate = 100.0

        resolved_disputes = len([d for d in disputes if d.status == DisputeStatus.RESOLVED])
        total_disputes = len(disputes)
        if total_disputes > 0:
            dispute_resolution_rate = (resolved_disputes / total_disputes) * 100
        else:
            dispute_resolution_rate = 100.0

        policy_adherence_rate = max(0, 100 - (total_violations * 2))

        resolved_with_time = [
            d for d in disputes if d.status == DisputeStatus.RESOLVED and d.resolved_at
        ]
        if resolved_with_time:
            total_hours = sum(
                (d.resolved_at - d.created_at).total_seconds() / 3600
                for d in resolved_with_time
            )
            avg_resolution_time = total_hours / len(resolved_with_time)
        else:
            avg_resolution_time = 0.0

        overall_score = (
            rule_compliance_rate * 0.35
            + dispute_resolution_rate * 0.25
            + policy_adherence_rate * 0.25
            + max(0, 100 - avg_resolution_time) * 0.15
        )

        return GovernanceHealthScore(
            overall_score=round(overall_score, 2),
            rule_compliance_rate=round(rule_compliance_rate, 2),
            dispute_resolution_rate=round(dispute_resolution_rate, 2),
            policy_adherence_rate=round(policy_adherence_rate, 2),
            average_resolution_time_hours=round(avg_resolution_time, 2),
            active_violations_count=total_violations,
            pending_disputes_count=len([d for d in disputes if d.status == DisputeStatus.OPEN]),
        )

    async def _generate_recommendations_with_llm(
        self,
        health_score: GovernanceHealthScore,
        violations_by_category: dict[str, int],
        focus_areas: list[str],
    ) -> list[str]:
        """Generate recommendations using the LLM."""
        system_prompt = (
            "You are a governance analytics expert. Based on the provided metrics, "
            "generate actionable recommendations to improve community governance. "
            "Respond with a JSON array of recommendation strings."
        )
        user_message = f"""Based on the following governance metrics, provide recommendations:

Health Score: {health_score.overall_score}
Rule Compliance Rate: {health_score.rule_compliance_rate}%
Dispute Resolution Rate: {health_score.dispute_resolution_rate}%
Policy Adherence Rate: {health_score.policy_adherence_rate}%
Average Resolution Time: {health_score.average_resolution_time_hours} hours
Active Violations: {health_score.active_violations_count}
Pending Disputes: {health_score.pending_disputes_count}

Violations by Category:
{json.dumps(violations_by_category, indent=2)}

Focus Areas: {focus_areas}

Provide 3-5 specific, actionable recommendations."""

        messages = self._build_messages(system_prompt, user_message)
        response = await self.llm.ainvoke(messages)

        try:
            result = json.loads(response.content)
            if isinstance(result, list):
                return result
            return [str(result)]
        except (json.JSONDecodeError, ValueError):
            return self._generate_recommendations(health_score, violations_by_category)

    def _generate_recommendations(
        self, health_score: GovernanceHealthScore, violations_by_category: dict[str, int]
    ) -> list[str]:
        """Generate recommendations using programmatic logic."""
        recommendations: list[str] = []

        if health_score.rule_compliance_rate < 80:
            recommendations.append(
                "Rule compliance is below 80%. Consider reviewing and clarifying "
                "community rules to improve adherence."
            )

        if health_score.dispute_resolution_rate < 70:
            recommendations.append(
                "Dispute resolution rate is low. Consider adding more mediators "
                "or implementing automated dispute resolution workflows."
            )

        if health_score.average_resolution_time_hours > 48:
            recommendations.append(
                "Average dispute resolution time exceeds 48 hours. Consider "
                "streamlining the resolution process or adding more resources."
            )

        if violations_by_category:
            top_category = max(violations_by_category, key=violations_by_category.get)
            recommendations.append(
                f"Elevated violations in '{top_category}' category. Consider "
                "targeted education campaigns or stricter enforcement."
            )

        if not recommendations:
            recommendations.append(
                "Governance health is good. Continue monitoring metrics and "
                "maintaining current policies."
            )

        return recommendations

    async def get_summary(self) -> GovernanceSummary:
        """Get a quick summary of governance state."""
        active_rules = len([r for r in self.rules if r.is_active])
        active_policies = len([p for p in self.policies if p.status == PolicyStatus.ACTIVE])
        open_disputes = len([d for d in self.disputes if d.status == DisputeStatus.OPEN])
        pending_actions = len(
            [a for a in self.actions if a.status == ActionStatus.PENDING]
        )

        day_ago = datetime.utcnow() - timedelta(hours=24)
        violations_24h = len(
            [
                a
                for a in self.actions
                if a.status == ActionStatus.REJECTED and a.created_at >= day_ago
            ]
        )

        total = len(self.actions)
        health_score = ((total - violations_24h) / total) * 100 if total > 0 else 100.0

        return GovernanceSummary(
            total_active_rules=active_rules,
            total_active_policies=active_policies,
            open_disputes=open_disputes,
            pending_actions=pending_actions,
            violations_last_24h=violations_24h,
            health_score=round(health_score, 2),
        )

    async def health_check(self) -> dict[str, Any]:
        """Check the health of the Governance Analytics Agent."""
        base_health = await super().health_check()
        base_health.update(
            {
                "total_actions": len(self.actions),
                "total_rules": len(self.rules),
                "total_disputes": len(self.disputes),
                "total_policies": len(self.policies),
            }
        )
        return base_health
