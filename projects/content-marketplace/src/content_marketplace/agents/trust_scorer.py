"""Trust Scorer Agent using LangChain DeepAgents."""

from __future__ import annotations

import logging
import math
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage

from content_marketplace.models.trust import TrustLevel, TrustScore, TrustScoreCreate

logger = logging.getLogger(__name__)


class TrustScorerAgent:
    """Agent responsible for computing and managing user trust scores.

    Uses LangChain DeepAgents to analyze user behavior,
    detect anomalies, and compute trust scores.
    """

    def __init__(self, llm: Optional[BaseChatModel] = None) -> None:
        """Initialize the TrustScorerAgent.

        Args:
            llm: Optional LangChain chat model for AI-powered trust analysis.
        """
        self.llm = llm
        self._trust_scores: dict[str, TrustScore] = {}

    def _compute_score(self, data: TrustScoreCreate) -> float:
        """Compute trust score from user metrics.

        Args:
            data: Trust score creation data.

        Returns:
            Trust score between 0 and 1.
        """
        score = 0.0

        # Transaction success rate (40% weight)
        if data.transaction_count > 0:
            success_rate = data.successful_transactions / data.transaction_count
            score += success_rate * 0.40

        # Rating score (25% weight)
        rating_score = data.average_rating / 5.0
        score += rating_score * 0.25

        # Account age (15% weight) - maxes out at 2 years
        age_score = min(data.account_age_days / 730, 1.0)
        score += age_score * 0.15

        # Dispute penalty (20% weight) - fewer disputes = higher score
        if data.transaction_count > 0:
            dispute_rate = data.dispute_count / data.transaction_count
            dispute_score = max(0, 1.0 - dispute_rate)
            score += dispute_score * 0.20

        # Verification bonus
        if data.verification_status:
            score = min(score * 1.1, 1.0)

        return round(min(max(score, 0.0), 1.0), 4)

    def _classify_level(self, score: float) -> TrustLevel:
        """Classify trust score into a trust level.

        Args:
            score: The trust score.

        Returns:
            The trust level.
        """
        if score >= 0.9:
            return TrustLevel.VERIFIED
        elif score >= 0.7:
            return TrustLevel.HIGH
        elif score >= 0.5:
            return TrustLevel.MEDIUM
        elif score >= 0.3:
            return TrustLevel.LOW
        else:
            return TrustLevel.UNTRUSTED

    def _identify_risk_factors(self, data: TrustScoreCreate) -> list[str]:
        """Identify risk factors for a user.

        Args:
            data: Trust score creation data.

        Returns:
            List of risk factor descriptions.
        """
        risks = []

        if data.transaction_count > 0:
            dispute_rate = data.dispute_count / data.transaction_count
            if dispute_rate > 0.1:
                risks.append("high_dispute_rate")

        if data.average_rating < 3.0 and data.transaction_count > 5:
            risks.append("low_rating")

        if data.account_age_days < 30:
            risks.append("new_account")

        if not data.verification_status:
            risks.append("unverified")

        return risks

    async def create_trust_score(self, data: TrustScoreCreate) -> TrustScore:
        """Create a new trust score for a user.

        Args:
            data: Trust score creation data.

        Returns:
            The newly created trust score.
        """
        score_value = self._compute_score(data)
        level = self._classify_level(score_value)
        risk_factors = self._identify_risk_factors(data)

        trust_score = TrustScore(
            user_id=data.user_id,
            score=score_value,
            level=level,
            transaction_count=data.transaction_count,
            successful_transactions=data.successful_transactions,
            dispute_count=data.dispute_count,
            average_rating=data.average_rating,
            account_age_days=data.account_age_days,
            verification_status=data.verification_status,
            risk_factors=risk_factors,
        )
        self._trust_scores[data.user_id] = trust_score
        logger.info("Created trust score for user %s: %.4f (%s)", data.user_id, score_value, level)
        return trust_score

    async def update_trust_score(
        self,
        user_id: str,
        transaction_success: bool = False,
        dispute: bool = False,
        new_rating: Optional[float] = None,
    ) -> TrustScore:
        """Update a user's trust score based on new activity.

        Args:
            user_id: The user identifier.
            transaction_success: Whether a transaction was successful.
            dispute: Whether a dispute was raised.
            new_rating: Optional new rating to incorporate.

        Returns:
            The updated trust score.

        Raises:
            KeyError: If user not found.
        """
        if user_id not in self._trust_scores:
            raise KeyError(f"Trust score for user {user_id} not found")

        trust = self._trust_scores[user_id]
        trust.transaction_count += 1

        if transaction_success:
            trust.successful_transactions += 1
        if dispute:
            trust.dispute_count += 1
        if new_rating is not None:
            # Running average
            trust.average_rating = round(
                (trust.average_rating * (trust.transaction_count - 1) + new_rating)
                / trust.transaction_count,
                2,
            )

        # Recompute score
        data = TrustScoreCreate(
            user_id=user_id,
            transaction_count=trust.transaction_count,
            successful_transactions=trust.successful_transactions,
            dispute_count=trust.dispute_count,
            average_rating=trust.average_rating,
            account_age_days=trust.account_age_days,
            verification_status=trust.verification_status,
        )
        trust.score = self._compute_score(data)
        trust.level = self._classify_level(trust.score)
        trust.risk_factors = self._identify_risk_factors(data)
        trust.updated_at = datetime.utcnow()

        logger.info("Updated trust score for user %s: %.4f", user_id, trust.score)
        return trust

    async def get_trust_score(self, user_id: str) -> TrustScore:
        """Retrieve a user's trust score.

        Args:
            user_id: The user identifier.

        Returns:
            The trust score.

        Raises:
            KeyError: If user not found.
        """
        if user_id not in self._trust_scores:
            raise KeyError(f"Trust score for user {user_id} not found")
        return self._trust_scores[user_id]

    async def verify_user(self, user_id: str) -> TrustScore:
        """Mark a user as verified.

        Args:
            user_id: The user identifier.

        Returns:
            The updated trust score.

        Raises:
            KeyError: If user not found.
        """
        if user_id not in self._trust_scores:
            raise KeyError(f"Trust score for user {user_id} not found")

        trust = self._trust_scores[user_id]
        trust.verification_status = True

        data = TrustScoreCreate(
            user_id=user_id,
            transaction_count=trust.transaction_count,
            successful_transactions=trust.successful_transactions,
            dispute_count=trust.dispute_count,
            average_rating=trust.average_rating,
            account_age_days=trust.account_age_days,
            verification_status=True,
        )
        trust.score = self._compute_score(data)
        trust.level = self._classify_level(trust.score)
        trust.risk_factors = self._identify_risk_factors(data)
        trust.updated_at = datetime.utcnow()

        return trust

    async def analyze_user_behavior(self, user_id: str) -> dict[str, Any]:
        """Use AI to analyze user behavior for trust assessment.

        Args:
            user_id: The user identifier.

        Returns:
            Dictionary with behavior analysis.
        """
        trust = await self.get_trust_score(user_id)

        if self.llm is None:
            return {"risk_level": trust.level.value, "anomalies": []}

        prompt = (
            f"Analyze this user's behavior for trust assessment:\n"
            f"Trust score: {trust.score}\n"
            f"Level: {trust.level}\n"
            f"Transactions: {trust.transaction_count}\n"
            f"Success rate: {trust.successful_transactions / max(trust.transaction_count, 1)}\n"
            f"Disputes: {trust.dispute_count}\n"
            f"Rating: {trust.average_rating}\n"
            f"Account age: {trust.account_age_days} days\n"
            f"Risk factors: {trust.risk_factors}\n"
            f"Respond with JSON: {{\"risk_level\": \"...\", \"anomalies\": [\"...\"]}}"
        )

        response = await self.llm.ainvoke([HumanMessage(content=prompt)])
        import json
        try:
            result = json.loads(response.content)
            return result
        except (json.JSONDecodeError, TypeError):
            return {"risk_level": trust.level.value, "anomalies": []}

    async def get_leaderboard(self, limit: int = 10) -> list[TrustScore]:
        """Get top users by trust score.

        Args:
            limit: Maximum number of results.

        Returns:
            List of top trust scores.
        """
        sorted_scores = sorted(
            self._trust_scores.values(), key=lambda t: t.score, reverse=True
        )
        return sorted_scores[:limit]
