"""Policy Effectiveness Agent implementation."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from langchain_core.language_models import BaseLanguageModel
from langchain_core.prompts import ChatPromptTemplate

from moderation_analytics.agents import BaseAgent
from moderation_analytics.models import PolicyEffectiveness


class PolicyEffectivenessAgent(BaseAgent[list[PolicyEffectiveness]]):
    """Agent that measures policy effectiveness.

    Evaluates detection rates, false positive/negative rates,
    appeal success rates, and overall policy impact.
    """

    def __init__(self, llm: BaseLanguageModel | None = None) -> None:
        """Initialize the Policy Effectiveness Agent.

        Args:
            llm: Optional pre-configured language model.
        """
        super().__init__(name="PolicyEffectiveness", llm=llm)
        self._prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are an expert in content moderation policy analysis. Evaluate "
                    "policy effectiveness using quantitative metrics and provide "
                    "actionable recommendations for improvement.",
                ),
                (
                    "human",
                    "Assess the effectiveness of the following moderation policies:\n\n"
                    "{policy_data}\n\n"
                    "Provide effectiveness scores and recommendations.",
                ),
            ]
        )

    async def run(
        self,
        policy_data: list[dict[str, Any]],
        period_start: datetime | None = None,
        period_end: datetime | None = None,
        **kwargs: Any,
    ) -> list[PolicyEffectiveness]:
        """Assess policy effectiveness.

        Args:
            policy_data: List of policy data to assess.
            period_start: Evaluation period start. Defaults to 30 days ago.
            period_end: Evaluation period end. Defaults to now.
            **kwargs: Additional parameters.

        Returns:
            list[PolicyEffectiveness]: Effectiveness assessment for each policy.

        Raises:
            ValueError: If policy_data is empty.
        """
        self._log_start(policy_count=len(policy_data))

        if not policy_data:
            raise ValueError("Cannot assess effectiveness with empty policy data")

        start = period_start or (datetime.utcnow() - timedelta(days=30))
        end = period_end or datetime.utcnow()

        results: list[PolicyEffectiveness] = []
        for pol_data in policy_data:
            effectiveness = self._calculate_effectiveness(pol_data, start, end)
            results.append(effectiveness)

        # Use LLM for qualitative recommendations
        if self._settings.openai_api_key:
            try:
                await self._enhance_with_llm(results, policy_data)
            except Exception as e:
                self._log_error(e, fallback="using quantitative analysis only")

        self._log_complete(results)
        return results

    def _calculate_effectiveness(
        self, data: dict[str, Any], start: datetime, end: datetime
    ) -> PolicyEffectiveness:
        """Calculate effectiveness metrics for a single policy.

        Args:
            data: Raw policy data.
            start: Evaluation period start.
            end: Evaluation period end.

        Returns:
            PolicyEffectiveness: Calculated effectiveness metrics.
        """
        violations = data.get("total_violations", 0)
        enforcements = data.get("total_enforcements", 0)
        false_positives = data.get("false_positives", 0)
        false_negatives = data.get("false_negatives", 0)
        appeals = data.get("user_appeals", 0)
        successful_appeals = data.get("successful_appeals", 0)

        detection_rate = enforcements / violations if violations > 0 else 0.0
        fp_rate = false_positives / enforcements if enforcements > 0 else 0.0
        fn_rate = false_negatives / violations if violations > 0 else 0.0
        appeal_rate = appeals / enforcements if enforcements > 0 else 0.0
        appeal_success = successful_appeals / appeals if appeals > 0 else 0.0

        # Overall effectiveness score (weighted composite)
        effectiveness = (
            detection_rate * 0.3
            + (1 - fp_rate) * 0.25
            + (1 - fn_rate) * 0.25
            + (1 - appeal_success) * 0.2
        )

        return PolicyEffectiveness(
            policy_id=str(data.get("policy_id", "unknown")),
            policy_name=str(data.get("policy_name", "Unknown")),
            policy_version=str(data.get("policy_version", "1.0")),
            total_violations=violations,
            total_enforcements=enforcements,
            detection_rate=round(detection_rate, 4),
            false_positive_rate=round(fp_rate, 4),
            false_negative_rate=round(fn_rate, 4),
            user_appeal_rate=round(appeal_rate, 4),
            appeal_success_rate=round(appeal_success, 4),
            period_start=start,
            period_end=end,
            effectiveness_score=round(effectiveness, 4),
            recommendations=data.get("recommendations", []),
        )

    async def _enhance_with_llm(
        self, results: list[PolicyEffectiveness], raw_data: list[dict[str, Any]]
    ) -> None:
        """Enhance effectiveness results with LLM qualitative analysis.

        Args:
            results: Effectiveness results to enhance in-place.
            raw_data: Raw policy data for LLM context.
        """
        # In production, use structured output to parse LLM response
        pass
