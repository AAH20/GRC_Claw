"""Compliance Scorer Agent - computes compliance scores per policy/domain."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from compliance_monitor.agents.base import BaseComplianceAgent
from compliance_monitor.models.schemas import ComplianceScore, ScoreRequest

if TYPE_CHECKING:
    from uuid import UUID


class ComplianceScorerAgent(BaseComplianceAgent[ScoreRequest, ComplianceScore]):
    """Agent responsible for computing compliance scores.

    Uses LangChain DeepAgents to evaluate compliance posture,
    compute scores, and identify improvement areas.
    """

    def __init__(self, model: str = "gpt-4o") -> None:
        """Initialize the Compliance Scorer Agent.

        Args:
            model: LLM model to use for scoring.
        """
        super().__init__(name="ComplianceScorerAgent", model=model)

    async def run(self, input_data: ScoreRequest) -> ComplianceScore:
        """Compute a compliance score.

        Args:
            input_data: Score request data.

        Returns:
            Computed ComplianceScore instance.
        """
        factors = input_data.factors or {}
        total_weight = sum(factors.values()) if factors else 1.0
        score = (total_weight / max(len(factors), 1)) * 100 if factors else 50.0
        score = max(0.0, min(100.0, score))

        return ComplianceScore(
            policy_id=input_data.policy_id,
            domain=input_data.domain,
            score=score,
            factors=factors,
        )

    async def evaluate_compliance_posture(
        self,
        policy_id: UUID,
        violations: list[dict[str, Any]],
        controls: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Evaluate overall compliance posture for a policy.

        Args:
            policy_id: Policy identifier.
            violations: List of violations.
            controls: List of compliance controls.

        Returns:
            Compliance posture evaluation.
        """
        prompt = f"""Evaluate the compliance posture for policy {policy_id}:

Violations:
{violations}

Controls:
{controls}

Provide:
1. Overall compliance score (0-100)
2. Key risk areas
3. Strengths
4. Improvement recommendations
"""
        result = await self.agent.ainvoke(
            {"messages": [{"role": "user", "content": prompt}]}
        )
        return {
            "evaluation": result,
            "policy_id": str(policy_id),
            "timestamp": datetime.now(tz=UTC).isoformat(),
        }

    async def compute_trend(
        self,
        current_score: float,
        previous_score: float | None,
    ) -> str:
        """Compute score trend direction.

        Args:
            current_score: Current compliance score.
            previous_score: Previous compliance score.

        Returns:
            Trend direction: improving, declining, or stable.
        """
        if previous_score is None:
            return "stable"
        diff = current_score - previous_score
        if diff > 5:
            return "improving"
        if diff < -5:
            return "declining"
        return "stable"

    async def generate_score_breakdown(self, score: ComplianceScore) -> dict[str, Any]:
        """Generate a detailed breakdown of a compliance score.

        Args:
            score: Compliance score to break down.

        Returns:
            Score breakdown with factor details.
        """
        return {
            "total_score": score.score,
            "max_score": score.max_score,
            "factors": score.factors,
            "trend": score.trend,
            "computed_at": score.computed_at.isoformat(),
        }
