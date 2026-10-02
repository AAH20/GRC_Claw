"""Trust Tier Agent for managing member trust levels."""

from typing import Any, Dict, List

from pydantic import BaseModel, Field

from reputation_system.agents.base import BaseAgent
from reputation_system.models.schemas import TrustTierLevel


class TrustTierInput(BaseModel):
    """Input for trust tier evaluation."""

    member_id: str = Field(..., description="Member identifier")
    current_score: int = Field(..., ge=0, le=1000, description="Current reputation score")
    current_tier: TrustTierLevel = Field(..., description="Current trust tier")
    account_age_days: int = Field(default=0, description="Account age in days")
    violation_count: int = Field(default=0, description="Number of violations")
    verification_status: bool = Field(default=False, description="Identity verification status")


class TrustTierOutput(BaseModel):
    """Output from trust tier evaluation."""

    member_id: str
    current_tier: TrustTierLevel
    recommended_tier: TrustTierLevel
    can_upgrade: bool
    can_downgrade: bool
    requirements_met: List[str] = Field(default_factory=list)
    requirements_pending: List[str] = Field(default_factory=list)
    benefits: List[str] = Field(default_factory=list)


class TrustTierAgent(BaseAgent[TrustTierInput, TrustTierOutput]):
    """Agent that evaluates and manages trust tier assignments."""

    def _get_system_prompt(self) -> str:
        """Get the system prompt for the trust tier agent."""
        return """You are a trust tier management agent. Your task is to evaluate
        a member's trust tier based on their reputation score, account history, and
        verification status. Determine if they qualify for a tier upgrade or downgrade,
        and list the requirements they have met or are pending."""

    async def run(self, input_data: TrustTierInput) -> TrustTierOutput:
        """Evaluate trust tier for a member.

        Args:
            input_data: Trust tier evaluation input.

        Returns:
            Trust tier evaluation results.
        """
        recommended_tier = self._calculate_recommended_tier(input_data)
        can_upgrade = self._tier_rank(recommended_tier) > self._tier_rank(input_data.current_tier)
        can_downgrade = self._tier_rank(recommended_tier) < self._tier_rank(input_data.current_tier)

        requirements_met, requirements_pending = self._evaluate_requirements(
            input_data, recommended_tier
        )
        benefits = self._get_tier_benefits(recommended_tier)

        return TrustTierOutput(
            member_id=input_data.member_id,
            current_tier=input_data.current_tier,
            recommended_tier=recommended_tier,
            can_upgrade=can_upgrade,
            can_downgrade=can_downgrade,
            requirements_met=requirements_met,
            requirements_pending=requirements_pending,
            benefits=benefits,
        )

    def _calculate_recommended_tier(self, data: TrustTierInput) -> TrustTierLevel:
        """Calculate recommended trust tier based on member data.

        Args:
            data: Trust tier input data.

        Returns:
            Recommended trust tier level.
        """
        # Violations can cap the tier
        if data.violation_count >= 5:
            return TrustTierLevel.BRONZE
        elif data.violation_count >= 3 and data.current_tier in (
            TrustTierLevel.GOLD,
            TrustTierLevel.PLATINUM,
            TrustTierLevel.DIAMOND,
        ):
            return TrustTierLevel.SILVER

        # Score-based tier
        if data.current_score >= 900 and data.verification_status:
            return TrustTierLevel.DIAMOND
        elif data.current_score >= 700 and data.verification_status:
            return TrustTierLevel.PLATINUM
        elif data.current_score >= 500:
            return TrustTierLevel.GOLD
        elif data.current_score >= 300:
            return TrustTierLevel.SILVER
        return TrustTierLevel.BRONZE

    def _tier_rank(self, tier: TrustTierLevel) -> int:
        """Get numeric rank for a trust tier.

        Args:
            tier: Trust tier level.

        Returns:
            Numeric rank (higher is better).
        """
        ranks = {
            TrustTierLevel.BRONZE: 1,
            TrustTierLevel.SILVER: 2,
            TrustTierLevel.GOLD: 3,
            TrustTierLevel.PLATINUM: 4,
            TrustTierLevel.DIAMOND: 5,
        }
        return ranks.get(tier, 0)

    def _evaluate_requirements(
        self, data: TrustTierInput, target_tier: TrustTierLevel
    ) -> tuple[List[str], List[str]]:
        """Evaluate which requirements are met or pending.

        Args:
            data: Trust tier input data.
            target_tier: Target trust tier.

        Returns:
            Tuple of (met requirements, pending requirements).
        """
        met: List[str] = []
        pending: List[str] = []

        # Score requirement
        tier_thresholds = {
            TrustTierLevel.BRONZE: 0,
            TrustTierLevel.SILVER: 300,
            TrustTierLevel.GOLD: 500,
            TrustTierLevel.PLATINUM: 700,
            TrustTierLevel.DIAMOND: 900,
        }
        threshold = tier_thresholds.get(target_tier, 0)
        if data.current_score >= threshold:
            met.append(f"Score >= {threshold}")
        else:
            pending.append(f"Score >= {threshold} (current: {data.current_score})")

        # Account age requirement
        if target_tier in (TrustTierLevel.GOLD, TrustTierLevel.PLATINUM, TrustTierLevel.DIAMOND):
            if data.account_age_days >= 90:
                met.append("Account age >= 90 days")
            else:
                pending.append(f"Account age >= 90 days (current: {data.account_age_days})")

        # Verification requirement
        if target_tier in (TrustTierLevel.PLATINUM, TrustTierLevel.DIAMOND):
            if data.verification_status:
                met.append("Identity verified")
            else:
                pending.append("Identity verification required")

        # Violation requirement
        if data.violation_count == 0:
            met.append("No violations")
        else:
            pending.append(f"Violations must be 0 (current: {data.violation_count})")

        return met, pending

    def _get_tier_benefits(self, tier: TrustTierLevel) -> List[str]:
        """Get benefits for a trust tier.

        Args:
            tier: Trust tier level.

        Returns:
            List of benefits.
        """
        benefits = {
            TrustTierLevel.BRONZE: ["Basic access", "Community participation"],
            TrustTierLevel.SILVER: ["Priority support", "Early access to features", "Reduced fees"],
            TrustTierLevel.GOLD: ["Premium support", "Exclusive content", "Fee discounts", "API access"],
            TrustTierLevel.PLATINUM: ["Dedicated account manager", "Custom integrations", "Highest limits", "SLA guarantee"],
            TrustTierLevel.DIAMOND: ["White-glove service", "Custom development", "Strategic partnership", "Maximum limits"],
        }
        return benefits.get(tier, [])
