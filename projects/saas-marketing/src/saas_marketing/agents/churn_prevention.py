"""Churn prevention agent for identifying at-risk accounts."""

from __future__ import annotations

from enum import StrEnum

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


class ChurnRiskLevel(StrEnum):
    """Churn risk levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AccountHealth(BaseModel):
    """Account health signals for churn prediction."""

    account_id: str = Field(..., description="Unique account identifier")
    mrr: float = Field(default=0.0, description="Monthly recurring revenue")
    active_users: int = Field(default=0, description="Currently active users")
    total_seats: int = Field(default=0, description="Total purchased seats")
    days_since_last_login: int = Field(default=0, description="Days since last user login")
    support_tickets_30d: int = Field(default=0, description="Support tickets in last 30 days")
    nps_score: int | None = Field(default=None, description="Latest NPS score")
    feature_adoption_rate: float = Field(
        default=0.0, ge=0, le=1, description="Feature adoption ratio"
    )
    contract_end_days: int = Field(default=0, description="Days until contract ends")
    payment_failures: int = Field(default=0, description="Recent payment failures")
    engagement_trend: str = Field(
        default="stable", description="Engagement trend: up, down, stable"
    )


class ChurnAssessment(BaseModel):
    """Churn risk assessment result."""

    account_id: str = Field(..., description="Account identifier")
    risk_level: ChurnRiskLevel = Field(..., description="Churn risk level")
    risk_score: float = Field(..., ge=0, le=1, description="Risk score from 0 to 1")
    contributing_factors: list[str] = Field(
        default_factory=list, description="Risk factors identified"
    )
    recommended_actions: list[str] = Field(
        default_factory=list, description="Suggested interventions"
    )
    estimated_churn_probability: float = Field(..., ge=0, le=1, description="Probability of churn")


class ChurnPreventionAgent:
    """Agent that identifies at-risk accounts and recommends retention actions.

    Analyzes account health signals to predict churn risk and suggest
    proactive interventions.
    """

    RISK_THRESHOLDS = {
        ChurnRiskLevel.LOW: 0.3,
        ChurnRiskLevel.MEDIUM: 0.6,
        ChurnRiskLevel.HIGH: 0.8,
        ChurnRiskLevel.CRITICAL: 0.95,
    }

    def __init__(
        self,
        model: str = "gpt-4",
        temperature: float = 0.3,
        risk_thresholds: dict[str, float] | None = None,
    ) -> None:
        """Initialize the ChurnPreventionAgent.

        Args:
            model: LLM model identifier.
            temperature: Sampling temperature.
            risk_thresholds: Custom risk level thresholds.
        """
        self.model = model
        self.temperature = temperature
        self.risk_thresholds = risk_thresholds or {
            k.value: v for k, v in self.RISK_THRESHOLDS.items()
        }
        logger.info("churn_prevention_agent_initialized")

    async def assess(self, health: AccountHealth) -> ChurnAssessment:
        """Assess churn risk for an account.

        Args:
            health: Account health signals.

        Returns:
            Churn risk assessment with recommendations.
        """
        logger.info("assessing_churn_risk", account_id=health.account_id)

        risk_score = self._calculate_risk_score(health)
        risk_level = self._determine_risk_level(risk_score)
        factors = self._identify_risk_factors(health)
        actions = self._recommend_actions(risk_level, health)

        logger.info(
            "churn_risk_assessed",
            account_id=health.account_id,
            risk_level=risk_level.value,
            risk_score=risk_score,
        )

        return ChurnAssessment(
            account_id=health.account_id,
            risk_level=risk_level,
            risk_score=round(risk_score, 3),
            contributing_factors=factors,
            recommended_actions=actions,
            estimated_churn_probability=round(risk_score, 3),
        )

    def _calculate_risk_score(self, health: AccountHealth) -> float:
        """Calculate overall churn risk score from 0 to 1.

        Args:
            health: Account health signals.

        Returns:
            Risk score between 0 and 1.
        """
        score = 0.0

        # Inactivity risk
        if health.days_since_last_login > 14:
            score += 0.25
        elif health.days_since_last_login > 7:
            score += 0.15

        # Low seat utilization
        if health.total_seats > 0:
            utilization = health.active_users / health.total_seats
            if utilization < 0.3:
                score += 0.20
            elif utilization < 0.5:
                score += 0.10

        # Support burden
        if health.support_tickets_30d > 5:
            score += 0.15
        elif health.support_tickets_30d > 2:
            score += 0.08

        # Low NPS
        if health.nps_score is not None and health.nps_score < 6:
            score += 0.15

        # Low feature adoption
        if health.feature_adoption_rate < 0.3:
            score += 0.15
        elif health.feature_adoption_rate < 0.5:
            score += 0.08

        # Contract ending soon
        if 0 < health.contract_end_days < 30:
            score += 0.10

        # Payment issues
        if health.payment_failures > 0:
            score += 0.15

        # Declining engagement
        if health.engagement_trend == "down":
            score += 0.10

        return min(1.0, score)

    def _determine_risk_level(self, score: float) -> ChurnRiskLevel:
        """Determine risk level from score.

        Args:
            score: Calculated risk score.

        Returns:
            Churn risk level.
        """
        if score >= self.risk_thresholds[ChurnRiskLevel.CRITICAL.value]:
            return ChurnRiskLevel.CRITICAL
        if score >= self.risk_thresholds[ChurnRiskLevel.HIGH.value]:
            return ChurnRiskLevel.HIGH
        if score >= self.risk_thresholds[ChurnRiskLevel.MEDIUM.value]:
            return ChurnRiskLevel.MEDIUM
        return ChurnRiskLevel.LOW

    def _identify_risk_factors(self, health: AccountHealth) -> list[str]:
        """Identify specific risk factors from account health.

        Args:
            health: Account health signals.

        Returns:
            List of identified risk factors.
        """
        factors: list[str] = []

        if health.days_since_last_login > 14:
            factors.append("extended_inactivity")
        if health.total_seats > 0 and health.active_users / health.total_seats < 0.3:
            factors.append("low_seat_utilization")
        if health.support_tickets_30d > 5:
            factors.append("high_support_burden")
        if health.nps_score is not None and health.nps_score < 6:
            factors.append("low_nps")
        if health.feature_adoption_rate < 0.3:
            factors.append("low_feature_adoption")
        if 0 < health.contract_end_days < 30:
            factors.append("contract_ending_soon")
        if health.payment_failures > 0:
            factors.append("payment_issues")
        if health.engagement_trend == "down":
            factors.append("declining_engagement")

        return factors

    def _recommend_actions(
        self, risk_level: ChurnRiskLevel, health: AccountHealth
    ) -> list[str]:
        """Recommend retention actions based on risk level.

        Args:
            risk_level: Determined risk level.
            health: Account health signals.

        Returns:
            List of recommended actions.
        """
        actions: list[str] = []

        if risk_level in (ChurnRiskLevel.HIGH, ChurnRiskLevel.CRITICAL):
            actions.extend([
                "Schedule executive business review",
                "Assign dedicated customer success manager",
                "Offer personalized re-engagement plan",
            ])

        if health.days_since_last_login > 7:
            actions.append("Trigger re-engagement email sequence")

        if health.feature_adoption_rate < 0.5:
            actions.append("Provide guided feature walkthrough")

        if health.nps_score is not None and health.nps_score < 6:
            actions.append("Conduct follow-up NPS survey call")

        if health.contract_end_days < 60:
            actions.append("Initiate renewal conversation early")

        if health.payment_failures > 0:
            actions.append("Resolve payment method issues")

        if not actions:
            actions.append("Continue regular check-ins and monitor health signals")

        return actions
