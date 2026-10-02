"""Onboarding agent for partner registration and qualification."""

from __future__ import annotations

import logging
from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class PartnerTier(StrEnum):
    """Partner tier levels."""

    REGISTERED = "registered"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"


class PartnerStatus(StrEnum):
    """Partner onboarding status."""

    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    ACTIVE = "active"
    SUSPENDED = "suspended"


class PartnerProfile(BaseModel):
    """Partner profile data model."""

    id: str = Field(..., description="Unique partner identifier")
    name: str = Field(..., min_length=1, max_length=255)
    email: str = Field(..., pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$")
    tier: PartnerTier = PartnerTier.REGISTERED
    status: PartnerStatus = PartnerStatus.PENDING
    company: str = Field(default="", max_length=255)
    industry: str = Field(default="", max_length=100)
    region: str = Field(default="", max_length=100)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)


class OnboardingAgent:
    """Agent responsible for partner onboarding workflows."""

    def __init__(self) -> None:
        """Initialize the onboarding agent."""
        self._partners: dict[str, PartnerProfile] = {}
        logger.info("OnboardingAgent initialized")

    async def register_partner(self, profile: PartnerProfile) -> PartnerProfile:
        """Register a new partner.

        Args:
            profile: The partner profile to register.

        Returns:
            The registered partner profile.

        Raises:
            ValueError: If a partner with the same ID already exists.
        """
        if profile.id in self._partners:
            raise ValueError(f"Partner with ID '{profile.id}' already exists")

        profile.status = PartnerStatus.PENDING
        profile.created_at = datetime.utcnow()
        self._partners[profile.id] = profile
        logger.info("Registered new partner: %s (%s)", profile.name, profile.id)
        return profile

    async def qualify_partner(self, partner_id: str) -> PartnerProfile:
        """Qualify a partner for the next tier.

        Args:
            partner_id: The partner to qualify.

        Returns:
            The updated partner profile.

        Raises:
            KeyError: If the partner is not found.
        """
        if partner_id not in self._partners:
            raise KeyError(f"Partner '{partner_id}' not found")

        partner = self._partners[partner_id]
        partner.status = PartnerStatus.IN_REVIEW
        partner.updated_at = datetime.utcnow()
        logger.info("Partner %s moved to qualification review", partner_id)
        return partner

    async def approve_partner(self, partner_id: str) -> PartnerProfile:
        """Approve a partner for activation.

        Args:
            partner_id: The partner to approve.

        Returns:
            The updated partner profile.

        Raises:
            KeyError: If the partner is not found.
        """
        if partner_id not in self._partners:
            raise KeyError(f"Partner '{partner_id}' not found")

        partner = self._partners[partner_id]
        partner.status = PartnerStatus.APPROVED
        partner.updated_at = datetime.utcnow()
        logger.info("Partner %s approved", partner_id)
        return partner

    async def activate_partner(self, partner_id: str) -> PartnerProfile:
        """Activate an approved partner.

        Args:
            partner_id: The partner to activate.

        Returns:
            The updated partner profile.

        Raises:
            KeyError: If the partner is not found.
            ValueError: If the partner is not in approved status.
        """
        if partner_id not in self._partners:
            raise KeyError(f"Partner '{partner_id}' not found")

        partner = self._partners[partner_id]
        if partner.status != PartnerStatus.APPROVED:
            raise ValueError(
                f"Partner must be approved before activation, current: {partner.status}"
            )

        partner.status = PartnerStatus.ACTIVE
        partner.updated_at = datetime.utcnow()
        logger.info("Partner %s activated", partner_id)
        return partner

    async def get_partner(self, partner_id: str) -> PartnerProfile | None:
        """Get a partner by ID.

        Args:
            partner_id: The partner ID to look up.

        Returns:
            The partner profile or None if not found.
        """
        return self._partners.get(partner_id)

    async def list_partners(
        self,
        status: PartnerStatus | None = None,
        tier: PartnerTier | None = None,
    ) -> list[PartnerProfile]:
        """List partners with optional filtering.

        Args:
            status: Filter by status.
            tier: Filter by tier.

        Returns:
            List of matching partner profiles.
        """
        partners = list(self._partners.values())
        if status:
            partners = [p for p in partners if p.status == status]
        if tier:
            partners = [p for p in partners if p.tier == tier]
        return partners

    async def update_tier(self, partner_id: str, tier: PartnerTier) -> PartnerProfile:
        """Update a partner's tier.

        Args:
            partner_id: The partner to update.
            tier: The new tier.

        Returns:
            The updated partner profile.

        Raises:
            KeyError: If the partner is not found.
        """
        if partner_id not in self._partners:
            raise KeyError(f"Partner '{partner_id}' not found")

        partner = self._partners[partner_id]
        partner.tier = tier
        partner.updated_at = datetime.utcnow()
        logger.info("Partner %s tier updated to %s", partner_id, tier)
        return partner
