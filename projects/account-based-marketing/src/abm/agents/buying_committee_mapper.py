"""Buying Committee Mapper Agent for identifying decision-makers within accounts."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import ClassVar

import structlog

logger = structlog.get_logger(__name__)


class CommitteeRole(str, Enum):
    """Roles within a buying committee."""

    CHAMPION = "champion"
    DECISION_MAKER = "decision_maker"
    INFLUENCER = "influencer"
    BLOCKER = "blocker"
    USER = "user"
    ECONOMIC_BUYER = "economic_buyer"
    TECHNICAL_EVALUATOR = "technical_evaluator"


@dataclass
class CommitteeMember:
    """Represents a member of the buying committee."""

    contact_id: str
    name: str
    title: str
    role: CommitteeRole
    influence_score: float
    engagement_level: float
    email: str | None = None
    linkedin_url: str | None = None
    notes: str = ""


@dataclass
class BuyingCommittee:
    """Represents the complete buying committee for an account."""

    account_id: str
    members: list[CommitteeMember] = field(default_factory=list)
    completeness_score: float = 0.0
    identified_gaps: list[str] = field(default_factory=list)


class BuyingCommitteeMapperAgent:
    """Maps the buying committee within target accounts.

    This agent uses CRM data, LinkedIn, and engagement data to identify
    key stakeholders, their roles, and influence levels within the
    decision-making unit.
    """

    # Ideal committee composition by role
    IDEAL_COMPOSITION: ClassVar[dict[CommitteeRole, int]] = {
        CommitteeRole.CHAMPION: 1,
        CommitteeRole.DECISION_MAKER: 1,
        CommitteeRole.ECONOMIC_BUYER: 1,
        CommitteeRole.INFLUENCER: 2,
        CommitteeRole.TECHNICAL_EVALUATOR: 1,
        CommitteeRole.USER: 2,
    }

    def __init__(self, max_contacts_per_account: int = 20) -> None:
        """Initialize the Buying Committee Mapper Agent.

        Args:
            max_contacts_per_account: Maximum contacts to analyze per account.
        """
        self.max_contacts_per_account = max_contacts_per_account
        logger.info(
            "BuyingCommitteeMapperAgent initialized",
            max_contacts=max_contacts_per_account,
        )

    async def map_committee(self, account_id: str) -> BuyingCommittee:
        """Map the buying committee for a target account.

        Args:
            account_id: The unique identifier for the account.

        Returns:
            BuyingCommittee object with identified members and gaps.

        Raises:
            ValueError: If account_id is empty.
        """
        if not account_id:
            raise ValueError("account_id cannot be empty")

        logger.info("Mapping buying committee", account_id=account_id)

        # In production, this would query CRM and LinkedIn
        members = self._identify_members(account_id)
        completeness = self._compute_completeness(members)
        gaps = self._identify_gaps(members)

        committee = BuyingCommittee(
            account_id=account_id,
            members=members,
            completeness_score=completeness,
            identified_gaps=gaps,
        )

        logger.info(
            "Committee mapping complete",
            account_id=account_id,
            member_count=len(members),
            completeness=completeness,
        )
        return committee

    async def find_champion(self, account_id: str) -> CommitteeMember | None:
        """Find the champion within an account's buying committee.

        Args:
            account_id: The account to search.

        Returns:
            The champion CommitteeMember if found, None otherwise.
        """
        committee = await self.map_committee(account_id)
        for member in committee.members:
            if member.role == CommitteeRole.CHAMPION:
                return member
        return None

    def _identify_members(self, account_id: str) -> list[CommitteeMember]:
        """Identify committee members from CRM and engagement data.

        Args:
            account_id: The account to identify members for.

        Returns:
            List of CommitteeMember objects.
        """
        return [
            CommitteeMember(
                contact_id="contact_001",
                name="Sarah Johnson",
                title="VP of Marketing",
                role=CommitteeRole.CHAMPION,
                influence_score=0.85,
                engagement_level=0.90,
                email="sarah.j@techcorp.com",
                linkedin_url="https://linkedin.com/in/sarahjohnson",
                notes="Active in evaluations, strong internal advocate",
            ),
            CommitteeMember(
                contact_id="contact_002",
                name="Michael Chen",
                title="CFO",
                role=CommitteeRole.ECONOMIC_BUYER,
                influence_score=0.95,
                engagement_level=0.30,
                email="m.chen@techcorp.com",
                notes="Final budget authority, low engagement so far",
            ),
            CommitteeMember(
                contact_id="contact_003",
                name="David Park",
                title="Director of IT",
                role=CommitteeRole.TECHNICAL_EVALUATOR,
                influence_score=0.70,
                engagement_level=0.65,
                email="d.park@techcorp.com",
                notes="Evaluating technical requirements",
            ),
            CommitteeMember(
                contact_id="contact_004",
                name="Lisa Martinez",
                title="Marketing Manager",
                role=CommitteeRole.USER,
                influence_score=0.50,
                engagement_level=0.80,
                email="lisa.m@techcorp.com",
                notes="Primary user, very engaged with content",
            ),
        ]

    def _compute_completeness(self, members: list[CommitteeMember]) -> float:
        """Compute committee completeness score.

        Args:
            members: Identified committee members.

        Returns:
            Completeness score between 0 and 1.
        """
        if not members:
            return 0.0

        identified_roles = {m.role for m in members}
        ideal_roles = set(self.IDEAL_COMPOSITION.keys())

        coverage = len(identified_roles & ideal_roles) / len(ideal_roles)
        return round(coverage, 2)

    def _identify_gaps(self, members: list[CommitteeMember]) -> list[str]:
        """Identify gaps in the buying committee mapping.

        Args:
            members: Identified committee members.

        Returns:
            List of gap descriptions.
        """
        gaps: list[str] = []

        for role, ideal_count in self.IDEAL_COMPOSITION.items():
            actual_count = sum(1 for m in members if m.role == role)
            if actual_count < ideal_count:
                gaps.append(
                    f"Missing {ideal_count - actual_count} {role.value}(s) "
                    f"(found {actual_count}, need {ideal_count})"
                )

        return gaps
