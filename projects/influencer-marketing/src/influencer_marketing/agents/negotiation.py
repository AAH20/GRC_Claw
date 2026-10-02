"""Negotiation agent for handling contract terms and pricing."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum

import structlog

from influencer_marketing.agents.base import AgentConfig, AgentResult, BaseAgent
from influencer_marketing.agents.outreach import OutreachResult, OutreachStatus

logger = structlog.get_logger(__name__)


class NegotiationStatus(StrEnum):
    """Status of a negotiation."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COUNTER_OFFER = "counter_offer"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"


@dataclass
class ContractTerms:
    """Contract terms for an influencer agreement."""

    deliverables: list[str] = field(default_factory=list)
    compensation: float = 0.0
    currency: str = "USD"
    usage_rights: str = "6_months"
    exclusivity: bool = False
    exclusivity_scope: str = ""
    content_approval_required: bool = True
    revision_rounds: int = 2
    timeline_days: int = 30
    payment_terms: str = "net_30"
    performance_bonus: float = 0.0


@dataclass
class NegotiationRound:
    """A single round of negotiation."""

    round_number: int
    proposed_by: str
    terms: ContractTerms
    message: str
    timestamp: datetime
    status: NegotiationStatus


@dataclass
class NegotiationResult:
    """Result of a negotiation process."""

    influencer_id: str
    status: NegotiationStatus
    rounds: list[NegotiationRound] = field(default_factory=list)
    final_terms: ContractTerms | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    auto_approved: bool = False
    notes: str = ""


class NegotiationAgent(BaseAgent[tuple[OutreachResult, ContractTerms], NegotiationResult]):
    """Agent responsible for negotiating contracts with influencers."""

    def __init__(self) -> None:
        config = AgentConfig(
            name="negotiation",
            description="Handles contract terms, pricing, and deliverable agreements",
            max_retries=3,
            timeout_seconds=120,
        )
        super().__init__(config)
        self.max_rounds = 5
        self.auto_approve_below = 500.0

    async def validate_input(
        self, input_data: tuple[OutreachResult, ContractTerms]
    ) -> bool:
        """Validate negotiation input."""
        outreach, terms = input_data
        if outreach.status not in (OutreachStatus.REPLIED, OutreachStatus.INTERESTED):
            self.logger.warning("Influencer not interested in negotiation")
            return False
        if terms.compensation < 0:
            self.logger.warning("Invalid compensation amount")
            return False
        return True

    async def execute(
        self, input_data: tuple[OutreachResult, ContractTerms]
    ) -> AgentResult[NegotiationResult]:
        """Execute negotiation with an influencer."""
        outreach, initial_terms = input_data
        self.logger.info("Starting negotiation", influencer_id=outreach.influencer_id)

        try:
            result = NegotiationResult(
                influencer_id=outreach.influencer_id,
                status=NegotiationStatus.IN_PROGRESS,
                started_at=datetime.utcnow(),
            )

            # Auto-approve if below threshold
            if initial_terms.compensation <= self.auto_approve_below:
                result.status = NegotiationStatus.ACCEPTED
                result.final_terms = initial_terms
                result.auto_approved = True
                result.completed_at = datetime.utcnow()
                result.notes = "Auto-approved: below threshold"
                self.logger.info("Negotiation auto-approved", influencer_id=outreach.influencer_id)
                return AgentResult(success=True, data=result)

            # Simulate negotiation rounds
            current_terms = initial_terms
            for round_num in range(1, self.max_rounds + 1):
                round_result = await self._conduct_round(
                    outreach.influencer_id, round_num, current_terms
                )
                result.rounds.append(round_result)

                if round_result.status == NegotiationStatus.ACCEPTED:
                    result.status = NegotiationStatus.ACCEPTED
                    result.final_terms = round_result.terms
                    result.completed_at = datetime.utcnow()
                    break
                elif round_result.status == NegotiationStatus.REJECTED:
                    result.status = NegotiationStatus.REJECTED
                    result.completed_at = datetime.utcnow()
                    break

                current_terms = round_result.terms

            if result.status == NegotiationStatus.IN_PROGRESS:
                result.status = NegotiationStatus.EXPIRED
                result.completed_at = datetime.utcnow()

            self.logger.info(
                "Negotiation completed",
                influencer_id=outreach.influencer_id,
                status=result.status.value,
                rounds=len(result.rounds),
            )
            return AgentResult(success=True, data=result)

        except Exception as exc:
            self.logger.error("Negotiation failed", error=str(exc))
            return AgentResult(success=False, error=str(exc))

    async def _conduct_round(
        self, influencer_id: str, round_number: int, current_terms: ContractTerms
    ) -> NegotiationRound:
        """Conduct a single negotiation round."""
        self.logger.info(
            "Conducting negotiation round",
            influencer_id=influencer_id,
            round=round_number,
        )

        # Placeholder: In production, this would send messages via LLM
        # and parse influencer responses
        return NegotiationRound(
            round_number=round_number,
            proposed_by="brand",
            terms=current_terms,
            message=f"Round {round_number} proposal",
            timestamp=datetime.utcnow(),
            status=NegotiationStatus.COUNTER_OFFER,
        )
