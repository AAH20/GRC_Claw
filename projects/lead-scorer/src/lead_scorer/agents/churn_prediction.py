"""Churn prediction agent for existing customers."""

from __future__ import annotations

import time
from datetime import UTC
from enum import StrEnum
from typing import Any

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


class ChurnRiskLevel(StrEnum):
    """Churn risk levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ChurnFactor(BaseModel):
    """A single churn risk factor."""

    name: str
    impact: float = Field(ge=0.0, le=1.0)
    description: str = ""
    weight: float = Field(ge=0.0, le=1.0, default=1.0)


class ChurnPredictionResult(BaseModel):
    """Result from the churn prediction agent."""

    customer_id: str
    churn_probability: float = Field(ge=0.0, le=1.0)
    risk_level: ChurnRiskLevel
    factors: list[ChurnFactor] = Field(default_factory=list)
    predicted_within_days: int | None = None
    recommended_actions: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    predicted_at: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class ChurnPredictionAgent:
    """Agent responsible for predicting customer churn risk.

    Analyzes usage patterns, engagement, support tickets, and other
    signals to predict likelihood of churn.
    """

    def __init__(self, timeout_seconds: int = 45, max_retries: int = 2) -> None:
        """Initialize the churn prediction agent.

        Args:
            timeout_seconds: Maximum time allowed for prediction.
            max_retries: Number of retry attempts on failure.
        """
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries

    async def predict(
        self,
        customer_id: str,
        usage_decline_pct: float | None = None,
        support_tickets_90d: int | None = None,
        nps_score: int | None = None,
        days_since_last_login: int | None = None,
        contract_renewal_days: int | None = None,
        **kwargs: Any,
    ) -> ChurnPredictionResult:
        """Predict churn risk for a customer.

        Args:
            customer_id: Unique identifier for the customer.
            usage_decline_pct: Percentage decline in usage (0-100).
            support_tickets_90d: Number of support tickets in last 90 days.
            nps_score: Net Promoter Score (-100 to 100).
            days_since_last_login: Days since last login.
            contract_renewal_days: Days until contract renewal.
            **kwargs: Additional signals.

        Returns:
            ChurnPredictionResult with probability and risk factors.

        Raises:
            ValueError: If customer_id is empty.
            TimeoutError: If prediction exceeds timeout.
        """
        if not customer_id:
            raise ValueError("customer_id is required")

        logger.info("predicting_churn", customer_id=customer_id)
        start_time = time.monotonic()

        try:
            factors = self._evaluate_factors(
                usage_decline_pct=usage_decline_pct,
                support_tickets_90d=support_tickets_90d,
                nps_score=nps_score,
                days_since_last_login=days_since_last_login,
                contract_renewal_days=contract_renewal_days,
                **kwargs,
            )

            elapsed = time.monotonic() - start_time
            if elapsed > self.timeout_seconds:
                raise TimeoutError(f"Churn prediction timed out after {elapsed:.1f}s")

            churn_probability = self._compute_probability(factors)
            risk_level = self._determine_risk_level(churn_probability)
            predicted_days = self._predict_timeline(churn_probability, factors)
            actions = self._recommend_actions(risk_level, factors)
            confidence = self._compute_confidence(factors)

            from datetime import datetime

            result = ChurnPredictionResult(
                customer_id=customer_id,
                churn_probability=churn_probability,
                risk_level=risk_level,
                factors=factors,
                predicted_within_days=predicted_days,
                recommended_actions=actions,
                confidence=confidence,
                predicted_at=datetime.now(UTC).isoformat(),
                metadata={"elapsed_seconds": elapsed},
            )

            logger.info(
                "churn_predicted",
                customer_id=customer_id,
                probability=churn_probability,
                risk_level=risk_level.value,
            )
            return result

        except Exception as exc:
            logger.error("churn_prediction_failed", customer_id=customer_id, error=str(exc))
            raise

    def _evaluate_factors(
        self,
        usage_decline_pct: float | None = None,
        support_tickets_90d: int | None = None,
        nps_score: int | None = None,
        days_since_last_login: int | None = None,
        contract_renewal_days: int | None = None,
        **kwargs: Any,
    ) -> list[ChurnFactor]:
        """Evaluate churn risk factors."""
        factors: list[ChurnFactor] = []

        # Usage decline
        if usage_decline_pct is not None:
            impact = min(usage_decline_pct / 50.0, 1.0)
            factors.append(
                ChurnFactor(
                    name="usage_decline",
                    impact=impact,
                    description=f"Usage declined {usage_decline_pct:.0f}%",
                    weight=0.30,
                )
            )

        # Support tickets
        if support_tickets_90d is not None:
            impact = min(support_tickets_90d / 10.0, 1.0)
            factors.append(
                ChurnFactor(
                    name="support_tickets",
                    impact=impact,
                    description=f"{support_tickets_90d} tickets in 90 days",
                    weight=0.20,
                )
            )

        # NPS score
        if nps_score is not None:
            # NPS: -100 to 100, lower = higher churn risk
            impact = max(0.0, (50 - nps_score) / 150.0)
            factors.append(
                ChurnFactor(
                    name="nps_score",
                    impact=impact,
                    description=f"NPS: {nps_score}",
                    weight=0.20,
                )
            )

        # Login recency
        if days_since_last_login is not None:
            impact = min(days_since_last_login / 30.0, 1.0)
            factors.append(
                ChurnFactor(
                    name="login_recency",
                    impact=impact,
                    description=f"Last login {days_since_last_login} days ago",
                    weight=0.15,
                )
            )

        # Contract renewal proximity
        if contract_renewal_days is not None:
            if contract_renewal_days <= 30:
                impact = 0.8
            elif contract_renewal_days <= 90:
                impact = 0.4
            else:
                impact = 0.1
            factors.append(
                ChurnFactor(
                    name="renewal_proximity",
                    impact=impact,
                    description=f"Renewal in {contract_renewal_days} days",
                    weight=0.15,
                )
            )

        return factors

    def _compute_probability(self, factors: list[ChurnFactor]) -> float:
        """Compute churn probability from factors."""
        if not factors:
            return 0.0
        total_weight = sum(f.weight for f in factors)
        if total_weight == 0:
            return 0.0
        weighted_sum = sum(f.impact * f.weight for f in factors)
        return round(min(weighted_sum / total_weight, 1.0), 2)

    def _determine_risk_level(self, probability: float) -> ChurnRiskLevel:
        """Determine risk level from probability."""
        if probability >= 0.8:
            return ChurnRiskLevel.CRITICAL
        if probability >= 0.6:
            return ChurnRiskLevel.HIGH
        if probability >= 0.3:
            return ChurnRiskLevel.MEDIUM
        return ChurnRiskLevel.LOW

    def _predict_timeline(
        self, probability: float, factors: list[ChurnFactor]
    ) -> int | None:
        """Predict days until churn."""
        if probability < 0.3:
            return None
        # Higher probability = sooner churn
        base_days = int(180 * (1 - probability))
        return max(base_days, 7)

    def _recommend_actions(
        self, risk_level: ChurnRiskLevel, factors: list[ChurnFactor]
    ) -> list[str]:
        """Generate recommended actions based on risk."""
        actions: list[str] = []

        if risk_level in (ChurnRiskLevel.HIGH, ChurnRiskLevel.CRITICAL):
            actions.append("Schedule executive business review")
            actions.append("Assign dedicated customer success manager")

        factor_names = {f.name for f in factors}
        if "usage_decline" in factor_names:
            actions.append("Conduct product adoption workshop")
        if "support_tickets" in factor_names:
            actions.append("Escalate support issues to engineering")
        if "nps_score" in factor_names:
            actions.append("Schedule NPS follow-up call")
        if "login_recency" in factor_names:
            actions.append("Send re-engagement email campaign")
        if "renewal_proximity" in factor_names:
            actions.append("Begin renewal conversation early")

        if not actions:
            actions.append("Continue regular check-ins")

        return actions

    def _compute_confidence(self, factors: list[ChurnFactor]) -> float:
        """Compute confidence in the prediction."""
        if not factors:
            return 0.0
        # More factors = higher confidence, capped at 0.95
        return round(min(len(factors) * 0.2, 0.95), 2)
