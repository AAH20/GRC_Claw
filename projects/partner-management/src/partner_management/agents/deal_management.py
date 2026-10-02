"""Deal management agent for partner deal registration and tracking."""

from __future__ import annotations

import logging
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class DealStage(StrEnum):
    """Deal pipeline stages."""

    PROSPECTING = "prospecting"
    QUALIFICATION = "qualification"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"


class Deal(BaseModel):
    """Deal data model."""

    id: str = Field(..., description="Unique deal identifier")
    partner_id: str = Field(..., description="Associated partner ID")
    name: str = Field(..., min_length=1, max_length=255)
    stage: DealStage = DealStage.PROSPECTING
    value: Decimal = Field(default=Decimal("0"), ge=0)
    currency: str = Field(default="USD", pattern=r"^[A-Z]{3}$")
    probability: float = Field(default=0.0, ge=0.0, le=1.0)
    expected_close_date: datetime | None = None
    actual_close_date: datetime | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)


class DealManagementAgent:
    """Agent responsible for partner deal lifecycle management."""

    def __init__(self) -> None:
        """Initialize the deal management agent."""
        self._deals: dict[str, Deal] = {}
        logger.info("DealManagementAgent initialized")

    async def register_deal(self, deal: Deal) -> Deal:
        """Register a new deal.

        Args:
            deal: The deal to register.

        Returns:
            The registered deal.

        Raises:
            ValueError: If a deal with the same ID already exists.
        """
        if deal.id in self._deals:
            raise ValueError(f"Deal with ID '{deal.id}' already exists")

        deal.created_at = datetime.utcnow()
        self._deals[deal.id] = deal
        logger.info("Registered new deal: %s (%s)", deal.name, deal.id)
        return deal

    async def advance_stage(self, deal_id: str, stage: DealStage) -> Deal:
        """Advance a deal to the next stage.

        Args:
            deal_id: The deal to advance.
            stage: The target stage.

        Returns:
            The updated deal.

        Raises:
            KeyError: If the deal is not found.
            ValueError: If the stage transition is invalid.
        """
        if deal_id not in self._deals:
            raise KeyError(f"Deal '{deal_id}' not found")

        deal = self._deals[deal_id]
        valid_transitions = self._get_valid_transitions(deal.stage)
        if stage not in valid_transitions:
            raise ValueError(
                f"Invalid stage transition from {deal.stage} to {stage}. "
                f"Valid: {valid_transitions}"
            )

        deal.stage = stage
        deal.updated_at = datetime.utcnow()

        if stage == DealStage.CLOSED_WON:
            deal.actual_close_date = datetime.utcnow()
            deal.probability = 1.0
        elif stage == DealStage.CLOSED_LOST:
            deal.actual_close_date = datetime.utcnow()
            deal.probability = 0.0

        logger.info("Deal %s advanced to %s", deal_id, stage)
        return deal

    async def update_value(
        self, deal_id: str, value: Decimal, currency: str = "USD"
    ) -> Deal:
        """Update a deal's value.

        Args:
            deal_id: The deal to update.
            value: The new deal value.
            currency: The currency code.

        Returns:
            The updated deal.

        Raises:
            KeyError: If the deal is not found.
        """
        if deal_id not in self._deals:
            raise KeyError(f"Deal '{deal_id}' not found")

        deal = self._deals[deal_id]
        deal.value = value
        deal.currency = currency
        deal.updated_at = datetime.utcnow()
        logger.info("Deal %s value updated to %s %s", deal_id, value, currency)
        return deal

    async def get_deal(self, deal_id: str) -> Deal | None:
        """Get a deal by ID.

        Args:
            deal_id: The deal ID to look up.

        Returns:
            The deal or None if not found.
        """
        return self._deals.get(deal_id)

    async def list_deals(
        self,
        partner_id: str | None = None,
        stage: DealStage | None = None,
    ) -> list[Deal]:
        """List deals with optional filtering.

        Args:
            partner_id: Filter by partner.
            stage: Filter by stage.

        Returns:
            List of matching deals.
        """
        deals = list(self._deals.values())
        if partner_id:
            deals = [d for d in deals if d.partner_id == partner_id]
        if stage:
            deals = [d for d in deals if d.stage == stage]
        return deals

    async def forecast_revenue(
        self, partner_id: str | None = None
    ) -> dict[str, Decimal]:
        """Forecast revenue from open deals.

        Args:
            partner_id: Optional partner filter.

        Returns:
            Dictionary with total and weighted forecast values.
        """
        deals = await self.list_deals(partner_id=partner_id)
        open_deals = [d for d in deals if d.stage not in (
            DealStage.CLOSED_WON, DealStage.CLOSED_LOST
        )]

        total = sum(d.value for d in open_deals)
        weighted = sum(d.value * Decimal(str(d.probability)) for d in open_deals)

        return {
            "total": total,
            "weighted": weighted,
            "count": Decimal(len(open_deals)),
        }

    def _get_valid_transitions(self, current: DealStage) -> list[DealStage]:
        """Get valid stage transitions from the current stage.

        Args:
            current: The current deal stage.

        Returns:
            List of valid next stages.
        """
        transitions: dict[DealStage, list[DealStage]] = {
            DealStage.PROSPECTING: [
                DealStage.QUALIFICATION,
                DealStage.CLOSED_LOST,
            ],
            DealStage.QUALIFICATION: [
                DealStage.PROPOSAL,
                DealStage.CLOSED_LOST,
            ],
            DealStage.PROPOSAL: [
                DealStage.NEGOTIATION,
                DealStage.CLOSED_LOST,
            ],
            DealStage.NEGOTIATION: [
                DealStage.CLOSED_WON,
                DealStage.CLOSED_LOST,
            ],
            DealStage.CLOSED_WON: [],
            DealStage.CLOSED_LOST: [],
        }
        return transitions.get(current, [])
