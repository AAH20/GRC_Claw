"""Benefit Manager Agent - Manages benefits for community tiers.

Uses LangChain DeepAgents to create, update, and manage benefits
assigned to tiers, ensuring proper allocation and tracking.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from langchain_core.language_models import BaseLanguageModel
from langchain_core.tools import BaseTool

from tier_management.agents.base import BaseAgent
from tier_management.config.logging_config import get_logger
from tier_management.models.schemas import Benefit, BenefitType

logger = get_logger(__name__)


class BenefitManagerAgent(BaseAgent[dict[str, Any], Benefit]):
    """Agent that manages benefits for community tiers.

    This agent uses LangChain DeepAgents to handle benefit lifecycle
    including creation, assignment to tiers, activation/deactivation,
    and usage tracking.
    """

    def __init__(
        self,
        llm: BaseLanguageModel | None = None,
        tools: list[BaseTool] | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the Benefit Manager Agent.

        Args:
            llm: LangChain language model for benefit management reasoning.
            tools: Tools available to the agent.
            **kwargs: Additional configuration parameters.
        """
        super().__init__(name="BenefitManagerAgent", llm=llm, tools=tools, **kwargs)
        self.benefits: dict[UUID, Benefit] = {}

    async def execute(self, input_data: dict[str, Any]) -> Benefit:
        """Execute a benefit management operation.

        Args:
            input_data: Dictionary containing:
                - operation: One of 'create', 'update', 'deactivate', 'assign'
                - benefit_id: UUID (for update/deactivate/assign)
                - benefit_data: Benefit fields (for create/update)
                - tier_ids: List of tier UUIDs (for assign)

        Returns:
            The affected Benefit instance.

        Raises:
            ValueError: If operation is invalid or required fields missing.
        """
        operation = input_data.get("operation", "create")

        logger.info(
            "benefit_operation",
            operation=operation,
        )

        if operation == "create":
            return await self._create_benefit(input_data)
        elif operation == "update":
            return await self._update_benefit(input_data)
        elif operation == "deactivate":
            return await self._deactivate_benefit(input_data)
        elif operation == "assign":
            return await self._assign_benefit(input_data)
        else:
            raise ValueError(f"Unknown operation: {operation}")

    async def _create_benefit(self, input_data: dict[str, Any]) -> Benefit:
        """Create a new benefit.

        Args:
            input_data: Benefit creation data.

        Returns:
            The created Benefit.
        """
        from datetime import datetime, timezone
        from uuid import uuid4

        benefit_data = input_data.get("benefit_data", {})

        benefit = Benefit(
            id=uuid4(),
            name=benefit_data.get("name", "Unnamed Benefit"),
            benefit_type=BenefitType(benefit_data.get("benefit_type", "percentage_discount")),
            description=benefit_data.get("description"),
            value=float(benefit_data.get("value", 0.0)),
            tier_ids=[UUID(str(t)) for t in benefit_data.get("tier_ids", [])],
            active=True,
            start_date=datetime.now(timezone.utc),
            usage_limit=benefit_data.get("usage_limit"),
            metadata=benefit_data.get("metadata", {}),
        )

        self.benefits[benefit.id] = benefit
        logger.info("benefit_created", benefit_id=str(benefit.id), name=benefit.name)

        return benefit

    async def _update_benefit(self, input_data: dict[str, Any]) -> Benefit:
        """Update an existing benefit.

        Args:
            input_data: Benefit update data with benefit_id.

        Returns:
            The updated Benefit.

        Raises:
            ValueError: If benefit not found.
        """
        benefit_id = input_data.get("benefit_id")
        if not benefit_id or UUID(str(benefit_id)) not in self.benefits:
            raise ValueError(f"Benefit '{benefit_id}' not found")

        benefit = self.benefits[UUID(str(benefit_id))]
        updates = input_data.get("benefit_data", {})

        for key, value in updates.items():
            if hasattr(benefit, key):
                setattr(benefit, key, value)

        logger.info("benefit_updated", benefit_id=str(benefit.id))
        return benefit

    async def _deactivate_benefit(self, input_data: dict[str, Any]) -> Benefit:
        """Deactivate a benefit.

        Args:
            input_data: Contains benefit_id to deactivate.

        Returns:
            The deactivated Benefit.
        """
        benefit_id = input_data.get("benefit_id")
        if not benefit_id or UUID(str(benefit_id)) not in self.benefits:
            raise ValueError(f"Benefit '{benefit_id}' not found")

        benefit = self.benefits[UUID(str(benefit_id))]
        benefit.active = False

        logger.info("benefit_deactivated", benefit_id=str(benefit.id))
        return benefit

    async def _assign_benefit(self, input_data: dict[str, Any]) -> Benefit:
        """Assign a benefit to additional tiers.

        Args:
            input_data: Contains benefit_id and tier_ids to assign.

        Returns:
            The updated Benefit.
        """
        benefit_id = input_data.get("benefit_id")
        tier_ids = input_data.get("tier_ids", [])

        if not benefit_id or UUID(str(benefit_id)) not in self.benefits:
            raise ValueError(f"Benefit '{benefit_id}' not found")

        benefit = self.benefits[UUID(str(benefit_id))]
        new_tier_ids = [UUID(str(t)) for t in tier_ids]
        benefit.tier_ids = list(set(benefit.tier_ids + new_tier_ids))

        logger.info(
            "benefit_assigned",
            benefit_id=str(benefit.id),
            tier_count=len(benefit.tier_ids),
        )
        return benefit

    def get_benefits_for_tier(self, tier_id: UUID) -> list[Benefit]:
        """Get all active benefits for a specific tier.

        Args:
            tier_id: The tier identifier.

        Returns:
            List of active benefits for the tier.
        """
        return [
            b for b in self.benefits.values()
            if b.active and tier_id in b.tier_ids
        ]
