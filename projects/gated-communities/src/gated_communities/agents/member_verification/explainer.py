"""Verification explanation agent using LangChain DeepAgents."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from member_verification.agents.base import AgentConfig, BaseAgent

if TYPE_CHECKING:
    from langchain_core.language_models import BaseLanguageModel


class VerificationExplainerAgent(BaseAgent):
    """Agent responsible for explaining verification decisions.

    Generates human-readable explanations of verification outcomes,
    including factors considered, reasons for decisions, and recommendations.
    """

    def __init__(
        self,
        llm: BaseLanguageModel | None = None,
        config: AgentConfig | None = None,
    ) -> None:
        """Initialize the verification explainer agent.

        Args:
            llm: Language model for agent reasoning.
            config: Agent configuration.
        """
        if config is None:
            config = AgentConfig(
                name="verification_explainer",
                description="Explains verification decisions in human-readable format",
            )
        super().__init__(config=config, llm=llm)
        self._capabilities = [
            "decision_explanation",
            "factor_analysis",
            "recommendation_generation",
            "appeal_guidance",
            "multi_language_support",
        ]

    async def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Generate an explanation for a verification decision.

        Args:
            input_data: Dictionary containing verification result and request details.

        Returns:
            Dictionary with explanation data.
        """
        self._status = "busy"
        self._mark_used()
        try:
            request_id = input_data.get("request_id", "")
            verification_result = input_data.get("verification_result", {})
            detail_level = input_data.get("detail_level", "detailed")

            status = verification_result.get("status", "unknown")
            confidence = verification_result.get("confidence", 0.0)
            verification_result.get("checks_performed", [])
            failures = verification_result.get("failure_reasons", [])

            # Generate summary
            summary = self._generate_summary(status, confidence, failures)

            # Generate factors
            factors = self._generate_factors(verification_result, detail_level)

            # Generate recommendations
            recommendations = self._generate_recommendations(status, failures)

            # Appeal process
            appeal_process = None
            if status in ("rejected", "needs_review"):
                appeal_process = (
                    "To appeal this decision, please submit additional supporting documents "
                    "through the member portal or contact support with your request ID. "
                    "Appeals are typically reviewed within 5-7 business days."
                )

            return {
                "request_id": request_id,
                "summary": summary,
                "factors": factors,
                "recommendations": recommendations,
                "appeal_process": appeal_process,
                "detail_level": detail_level,
                "agent": self.config.name,
            }
        finally:
            self._status = "available"

    def _generate_summary(
        self, status: str, confidence: float, failures: list[str]
    ) -> str:
        """Generate a human-readable summary.

        Args:
            status: Verification status.
            confidence: Confidence score.
            failures: List of failure reasons.

        Returns:
            Summary string.
        """
        if status == "verified":
            return (
                f"Your identity has been successfully verified with {confidence:.0%} confidence. "
                "You now have full access to community features."
            )
        elif status == "needs_review":
            reasons = (
                "; ".join(failures) if failures else "additional information required"
            )
            return (
                f"Your verification is under review. {reasons}. "
                "This typically resolves within 1-2 business days."
            )
        else:
            reasons = (
                "; ".join(failures) if failures else "verification requirements not met"
            )
            return (
                f"Unable to complete verification at this time. {reasons}. "
                "Please review the requirements and try again."
            )

    def _generate_factors(
        self, result: dict[str, Any], detail_level: str
    ) -> list[dict[str, Any]]:
        """Generate decision factors.

        Args:
            result: Verification result data.
            detail_level: Level of detail to include.

        Returns:
            List of factor dictionaries.
        """
        factors = []

        status = result.get("status", "unknown")
        factors.append(
            {
                "name": "verification_status",
                "impact": "positive" if status == "verified" else "negative",
                "weight": 0.4,
                "description": f"Overall verification status: {status}",
            }
        )

        confidence = result.get("confidence", 0.0)
        factors.append(
            {
                "name": "confidence_score",
                "impact": "positive" if confidence >= 0.7 else "negative",
                "weight": 0.3,
                "description": f"Confidence score: {confidence:.0%}",
            }
        )

        checks = result.get("checks_performed", [])
        factors.append(
            {
                "name": "checks_completed",
                "impact": "positive" if len(checks) >= 3 else "neutral",
                "weight": 0.2,
                "description": f"Completed {len(checks)} verification checks",
            }
        )

        if detail_level == "technical":
            factors.append(
                {
                    "name": "processing_metadata",
                    "impact": "neutral",
                    "weight": 0.1,
                    "description": f"Agent: {result.get('agent', 'unknown')}",
                }
            )

        return factors

    def _generate_recommendations(self, status: str, failures: list[str]) -> list[str]:
        """Generate recommendations for the member.

        Args:
            status: Verification status.
            failures: List of failure reasons.

        Returns:
            List of recommendation strings.
        """
        recommendations = []

        if status == "verified":
            recommendations.append("Keep your verification documents up to date.")
            recommendations.append(
                "Enable two-factor authentication for added security."
            )
        elif status == "needs_review":
            recommendations.append(
                "Ensure all submitted documents are clear and legible."
            )
            recommendations.append(
                "Verify that your personal information matches your documents."
            )
            recommendations.append(
                "Wait for the review process to complete before re-applying."
            )
        else:
            recommendations.append(
                "Double-check that all information entered is accurate."
            )
            recommendations.append(
                "Ensure documents are not expired and are clearly visible."
            )
            recommendations.append(
                "Use a high-quality camera or scanner for document submission."
            )
            if failures:
                recommendations.append(
                    f"Address the following issues: {'; '.join(failures)}"
                )

        return recommendations

    async def health_check(self) -> bool:
        """Check if the explainer is healthy.

        Returns:
            True if the agent is operational.
        """
        return self._status != "error"

    def get_capabilities(self) -> list[str]:
        """Get agent capabilities.

        Returns:
            List of capabilities.
        """
        return self._capabilities
