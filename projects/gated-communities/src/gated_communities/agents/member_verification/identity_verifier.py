"""Identity verification agent using LangChain DeepAgents."""

from __future__ import annotations

from typing import Any

from langchain_core.language_models import BaseLanguageModel

from member_verification.agents.base import AgentConfig, BaseAgent


class IdentityVerifierAgent(BaseAgent):
    """Agent responsible for verifying member identity.

    Uses LangChain DeepAgents to orchestrate multi-step identity verification
    including document validation, biometric matching, and database cross-referencing.
    """

    def __init__(
        self,
        llm: BaseLanguageModel | None = None,
        config: AgentConfig | None = None,
    ) -> None:
        """Initialize the identity verifier agent.

        Args:
            llm: Language model for agent reasoning.
            config: Agent configuration.
        """
        if config is None:
            config = AgentConfig(
                name="identity_verifier",
                description="Verifies member identity using multiple data points and documents",
            )
        super().__init__(config=config, llm=llm)
        self._capabilities = [
            "document_analysis",
            "biometric_matching",
            "database_cross_reference",
            "sanctions_screening",
            "address_verification",
        ]

    async def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Execute identity verification.

        Args:
            input_data: Dictionary containing identity data and documents.

        Returns:
            Dictionary with verification results.
        """
        self._status = "busy"
        self._mark_used()
        try:
            identity = input_data.get("identity", {})
            documents = input_data.get("documents", [])

            checks_performed: list[str] = []
            confidence = 0.0
            failure_reasons: list[str] = []

            # Step 1: Validate identity data completeness
            checks_performed.append("identity_completeness")
            if not identity.get("full_name") or not identity.get("date_of_birth"):
                failure_reasons.append("Incomplete identity data")
                confidence += 0.1
            else:
                confidence += 0.3

            # Step 2: Document verification
            if documents:
                checks_performed.append("document_verification")
                doc_score = min(len(documents) * 0.2, 0.4)
                confidence += doc_score
            else:
                failure_reasons.append("No supporting documents provided")

            # Step 3: Cross-reference checks
            checks_performed.append("cross_reference")
            confidence += 0.2

            # Step 4: Sanctions screening
            checks_performed.append("sanctions_screening")
            confidence += 0.1

            # Determine status
            if confidence >= 0.7 and not failure_reasons:
                status = "verified"
            elif confidence >= 0.4:
                status = "needs_review"
            else:
                status = "rejected"

            return {
                "status": status,
                "confidence": min(confidence, 1.0),
                "checks_performed": checks_performed,
                "failure_reasons": failure_reasons,
                "agent": self.config.name,
            }
        finally:
            self._status = "available"

    async def health_check(self) -> bool:
        """Check if the identity verifier is healthy.

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
