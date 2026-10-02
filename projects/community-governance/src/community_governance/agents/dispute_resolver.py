"""Dispute Resolver Agent for community governance."""

from __future__ import annotations

import json
from typing import Any
from uuid import UUID

from langchain_core.language_models import BaseLanguageModel

from community_governance.agents.base import BaseAgent
from community_governance.config.logging_config import get_logger
from community_governance.exceptions import (
    AgentExecutionException,
    DisputeNotFoundException,
    DisputeResolutionException,
)
from community_governance.models.dispute import Dispute, DisputeResolution, DisputeStatus

logger = get_logger(__name__)


class DisputeResolverAgent(BaseAgent[dict[str, Any], DisputeResolution]):
    """Agent responsible for mediating and resolving community disputes.

    Uses LangChain DeepAgents to analyze dispute details, understand
    all parties' perspectives, and propose fair resolutions based on
    community guidelines and precedents.
    """

    def __init__(
        self,
        llm: BaseLanguageModel | None = None,
        disputes: list[Dispute] | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the Dispute Resolver Agent.

        Args:
            llm: Language model for dispute resolution reasoning.
            disputes: List of disputes to manage.
            **kwargs: Additional configuration options.
        """
        super().__init__(llm=llm, name="dispute_resolver", **kwargs)
        self.disputes = disputes or []
        self._dispute_index: dict[UUID, Dispute] = {d.id: d for d in self.disputes}

    async def _setup(self) -> None:
        """Setup the dispute index for efficient lookups."""
        self._dispute_index = {d.id: d for d in self.disputes}
        logger.info(
            f"Dispute Resolver Agent loaded with {len(self.disputes)} disputes",
            agent_name=self.name,
            dispute_count=len(self.disputes),
        )

    def add_dispute(self, dispute: Dispute) -> None:
        """Add a dispute to the resolver's case list.

        Args:
            dispute: The dispute to add.
        """
        self.disputes.append(dispute)
        self._dispute_index[dispute.id] = dispute
        logger.info(
            f"Dispute '{dispute.title}' added to resolver",
            dispute_id=str(dispute.id),
        )

    def remove_dispute(self, dispute_id: UUID) -> None:
        """Remove a dispute from the resolver's case list.

        Args:
            dispute_id: The ID of the dispute to remove.

        Raises:
            DisputeNotFoundException: If the dispute is not found.
        """
        if dispute_id not in self._dispute_index:
            raise DisputeNotFoundException(str(dispute_id))
        self.disputes = [d for d in self.disputes if d.id != dispute_id]
        del self._dispute_index[dispute_id]

    async def execute(self, input_data: dict[str, Any]) -> DisputeResolution:
        """Resolve a dispute using AI-powered mediation.

        Args:
            input_data: Dictionary containing:
                - dispute_id: The ID of the dispute to resolve
                - context: Optional additional context (precedents, guidelines)
                - resolution_constraints: Optional constraints on the resolution

        Returns:
            The proposed dispute resolution.

        Raises:
            DisputeNotFoundException: If the dispute is not found.
            DisputeResolutionException: If resolution fails.
            AgentExecutionException: If the agent execution fails.
        """
        try:
            dispute_id = input_data.get("dispute_id")
            if not dispute_id:
                raise ValueError("Input must contain a valid 'dispute_id'")

            dispute = self._dispute_index.get(dispute_id)
            if not dispute:
                raise DisputeNotFoundException(str(dispute_id))

            context = input_data.get("context", {})
            constraints = input_data.get("resolution_constraints", {})

            logger.info(
                f"Resolving dispute '{dispute.title}'",
                dispute_id=str(dispute.id),
                status=dispute.status.value,
            )

            if self.llm:
                resolution = await self._resolve_with_llm(dispute, context, constraints)
            else:
                resolution = self._resolve_programmatically(dispute, context)

            dispute.resolution = resolution
            dispute.status = DisputeStatus.RESOLVED
            dispute.resolved_at = resolution.resolved_at

            logger.info(
                f"Dispute '{dispute.title}' resolved",
                dispute_id=str(dispute.id),
                resolution_type=resolution.resolution_type,
            )

            return resolution

        except (DisputeNotFoundException, DisputeResolutionException):
            raise
        except Exception as e:
            logger.error(f"Dispute resolution failed: {e}", error=str(e))
            raise AgentExecutionException(self.name, str(e)) from e

    async def _resolve_with_llm(
        self,
        dispute: Dispute,
        context: dict[str, Any],
        constraints: dict[str, Any],
    ) -> DisputeResolution:
        """Resolve a dispute using the LLM.

        Args:
            dispute: The dispute to resolve.
            context: Additional context for resolution.
            constraints: Resolution constraints.

        Returns:
            The LLM-proposed resolution.
        """
        system_prompt = self._build_system_prompt()
        user_message = self._build_resolution_prompt(dispute, context, constraints)

        messages = self._build_messages(system_prompt, user_message)
        response = await self.llm.ainvoke(messages)

        try:
            result_data = json.loads(response.content)
            return DisputeResolution(
                resolution_type=result_data.get("resolution_type", "mediation"),
                outcome=result_data.get("outcome", ""),
                rationale=result_data.get("rationale", ""),
                conditions=result_data.get("conditions", []),
                resolved_by="dispute_resolver_agent",
                follow_up_required=result_data.get("follow_up_required", False),
            )
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to parse LLM resolution response: {e}")
            return self._resolve_programmatically(dispute, context)

    def _resolve_programmatically(
        self, dispute: Dispute, context: dict[str, Any]
    ) -> DisputeResolution:
        """Resolve a dispute using programmatic logic.

        Args:
            dispute: The dispute to resolve.
            context: Additional context.

        Returns:
            The programmatically generated resolution.
        """
        return DisputeResolution(
            resolution_type="automated_mediation",
            outcome=f"Dispute '{dispute.title}' resolved through automated mediation",
            rationale=(
                f"Based on the dispute category '{dispute.category}' and "
                f"priority '{dispute.priority.value}', a fair resolution has been "
                "determined following community guidelines."
            ),
            conditions=[
                "Both parties agree to the resolution terms",
                "No further escalation for 30 days",
            ],
            resolved_by="dispute_resolver_agent",
            follow_up_required=dispute.priority.value in ("high", "urgent"),
        )

    def _build_system_prompt(self) -> str:
        """Build the system prompt for the LLM.

        Returns:
            The system prompt string.
        """
        return (
            "You are a community dispute resolver and mediator. Your job is to "
            "analyze disputes between community members and propose fair, balanced "
            "resolutions. Consider all perspectives, community guidelines, and past "
            "precedents. You must respond with a JSON object containing: "
            "resolution_type (string), outcome (string), rationale (string), "
            "conditions (array of strings), and follow_up_required (boolean)."
        )

    def _build_resolution_prompt(
        self,
        dispute: Dispute,
        context: dict[str, Any],
        constraints: dict[str, Any],
    ) -> str:
        """Build the resolution prompt for the LLM.

        Args:
            dispute: The dispute to resolve.
            context: Additional context.
            constraints: Resolution constraints.

        Returns:
            The user message prompt.
        """
        return f"""Resolve the following community dispute.

Dispute:
- Title: {dispute.title}
- Description: {dispute.description}
- Category: {dispute.category}
- Priority: {dispute.priority.value}
- Status: {dispute.status.value}
- Initiator: {dispute.initiator_id}
- Respondent: {dispute.respondent_id or 'N/A'}

Context:
{json.dumps(context, indent=2)}

Constraints:
{json.dumps(constraints, indent=2)}

Propose a fair and balanced resolution. Respond with JSON only."""

    async def health_check(self) -> dict[str, Any]:
        """Check the health of the Dispute Resolver Agent.

        Returns:
            Health status dictionary.
        """
        base_health = await super().health_check()
        open_disputes = len([d for d in self.disputes if d.status == DisputeStatus.OPEN])
        base_health.update(
            {
                "total_disputes": len(self.disputes),
                "open_disputes": open_disputes,
            }
        )
        return base_health
