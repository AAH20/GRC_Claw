"""Policy Tracker Agent - tracks policy changes, versions, and effective dates."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from compliance_monitor.agents.base import BaseComplianceAgent
from compliance_monitor.models.schemas import Policy, PolicyCreate, PolicyStatus

if TYPE_CHECKING:
    from uuid import UUID


class PolicyTrackerAgent(BaseComplianceAgent[PolicyCreate, Policy]):
    """Agent responsible for tracking compliance policies.

    Uses LangChain DeepAgents to analyze policy documents, track changes,
    manage versions, and monitor effective dates.
    """

    def __init__(self, model: str = "gpt-4o") -> None:
        """Initialize the Policy Tracker Agent.

        Args:
            model: LLM model to use for policy analysis.
        """
        super().__init__(name="PolicyTrackerAgent", model=model)

    async def run(self, input_data: PolicyCreate) -> Policy:
        """Create and track a new policy.

        Args:
            input_data: Policy creation data.

        Returns:
            Created Policy instance.
        """
        policy = Policy(
            name=input_data.name,
            description=input_data.description,
            category=input_data.category,
            status=PolicyStatus.DRAFT,
            version=input_data.version,
            effective_date=input_data.effective_date or datetime.now(tz=UTC),
            rules=input_data.rules,
            metadata=input_data.metadata,
        )
        return policy

    async def analyze_policy_document(self, document_text: str) -> dict[str, Any]:
        """Analyze a policy document using LLM.

        Args:
            document_text: Raw policy document text.

        Returns:
            Extracted policy information.
        """
        prompt = f"""Analyze the following compliance policy document and extract:
        - Policy name
        - Category
        - Key rules and requirements
        - Effective date
        - Version information

        Document:
        {document_text}
        """
        result = await self.agent.ainvoke(
            {"messages": [{"role": "user", "content": prompt}]}
        )
        return {"analysis": result, "timestamp": datetime.now(tz=UTC).isoformat()}

    async def check_policy_expiry(self, policy: Policy) -> bool:
        """Check if a policy has expired or is nearing expiry.

        Args:
            policy: Policy to check.

        Returns:
            True if policy is expired or expiring within 30 days.
        """
        from datetime import timedelta

        now = datetime.now(tz=UTC)
        expiry_threshold = now + timedelta(days=30)
        return policy.effective_date < now or policy.effective_date <= expiry_threshold

    async def get_policy_history(self, policy_id: UUID) -> list[dict[str, Any]]:
        """Get version history for a policy.

        Args:
            policy_id: Policy identifier.

        Returns:
            List of policy version records.
        """
        return []
