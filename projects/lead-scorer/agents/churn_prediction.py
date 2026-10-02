"""Churn Prediction agent — predicts churn risk for existing customers."""

from __future__ import annotations

from langchain_core.language_models import BaseLanguageModel
from pydantic import BaseModel, Field

from agents.base import AgentConfig, AgentContext, AgentResult, BaseAgent


class ChurnPredictionInput(BaseModel):
    """Input for the Churn Prediction agent."""

    customer_id: str = Field(..., description="Customer identifier")
    company_name: str = Field(..., description="Company name")
    tenure_months: int = Field(..., ge=0, description="Customer tenure in months")
    contract_value: float = Field(..., ge=0.0, description="Annual contract value")
    usage_trend: str = Field(
        default="stable",
        description="Usage trend: increasing, stable, or decreasing",
    )
    support_tickets_90d: int = Field(
        default=0, ge=0,
        description="Support tickets in last 90 days",
    )
    nps_score: float | None = Field(
        None, ge=0.0, le=10.0,
        description="Net Promoter Score",
    )
    engagement_score: float = Field(
        default=50.0, ge=0.0, le=100.0,
        description="Product engagement score",
    )
    last_login_days: int = Field(
        default=0, ge=0,
        description="Days since last login",
    )
    feature_adoption_rate: float = Field(
        default=0.5, ge=0.0, le=1.0,
        description="Percentage of features adopted",
    )
    stakeholder_changes: int = Field(
        default=0, ge=0,
        description="Number of stakeholder changes in last 6 months",
    )
    contract_renewal_date: str | None = Field(
        None,
        description="Contract renewal date (ISO format)",
    )
    competitor_mentions: int = Field(
        default=0, ge=0,
        description="Mentions of competitors in conversations",
    )


class ChurnRiskFactor(BaseModel):
    """A single churn risk factor."""

    factor: str
    severity: str = Field(..., description="high, medium, or low")
    impact: float = Field(ge=0.0, le=1.0)
    description: str = ""


class ChurnPredictionOutput(BaseModel):
    """Output from the Churn Prediction agent."""

    customer_id: str
    churn_probability: float = Field(ge=0.0, le=1.0)
    risk_level: str = Field(..., description="high, medium, or low")
    risk_factors: list[ChurnRiskFactor] = Field(default_factory=list)
    protective_factors: list[str] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    prediction_window_days: int = 90
    summary: str = ""


class ChurnPredictionAgent(BaseAgent[ChurnPredictionInput, ChurnPredictionOutput]):
    """Predicts churn risk for existing customers.

    Analyzes usage patterns, engagement, support interactions, and
    relationship health to predict likelihood of churn.
    """

    name = "churn_prediction"
    description = "Predicts churn risk for existing customers"

    HIGH_RISK_THRESHOLD: float = 0.7
    MEDIUM_RISK_THRESHOLD: float = 0.4

    def __init__(
        self,
        llm: BaseLanguageModel | None = None,
        config: AgentConfig | None = None,
    ) -> None:
        default_config = AgentConfig(
            enabled=True,
            timeout_seconds=30.0,
            max_retries=2,
        )
        if config:
            default_config = config
        super().__init__(llm=llm, config=default_config)

    @property
    def input_model(self) -> type[ChurnPredictionInput]:
        return ChurnPredictionInput

    @property
    def output_model(self) -> type[ChurnPredictionOutput]:
        return ChurnPredictionOutput

    async def run(
        self, input_data: ChurnPredictionInput, context: AgentContext
    ) -> AgentResult[ChurnPredictionOutput]:
        """Predict churn risk for the customer.

        Args:
            input_data: Customer health data.
            context: Execution context.

        Returns:
            Churn prediction with probability, risk level, and factors.
        """
        try:
            risk_factors = self._identify_risk_factors(input_data)
            protective_factors = self._identify_protective_factors(input_data)

            # Compute churn probability
            base_prob = 0.15  # Base churn rate
            risk_impact = sum(f.impact for f in risk_factors) * 0.1
            protective_impact = len(protective_factors) * 0.03

            churn_prob = base_prob + risk_impact - protective_impact
            churn_prob = max(0.0, min(1.0, churn_prob))

            risk_level = self._probability_to_risk_level(churn_prob)
            actions = self._recommend_actions(risk_factors, risk_level)
            confidence = self._compute_confidence(input_data)

            output = ChurnPredictionOutput(
                customer_id=input_data.customer_id,
                churn_probability=round(churn_prob, 2),
                risk_level=risk_level,
                risk_factors=risk_factors,
                protective_factors=protective_factors,
                recommended_actions=actions,
                confidence=round(confidence, 2),
                prediction_window_days=90,
                summary=self._build_summary(churn_prob, risk_level, risk_factors),
            )
            return AgentResult(success=True, data=output)

        except Exception as exc:
            return AgentResult(
                success=False,
                error=f"Churn prediction failed: {exc}",
            )

    def _identify_risk_factors(
        self, data: ChurnPredictionInput
    ) -> list[ChurnRiskFactor]:
        """Identify churn risk factors.

        Args:
            data: Customer health data.

        Returns:
            List of risk factors.
        """
        factors: list[ChurnRiskFactor] = []

        if data.usage_trend == "decreasing":
            factors.append(
                ChurnRiskFactor(
                    factor="declining_usage",
                    severity="high",
                    impact=0.25,
                    description="Usage trend is decreasing over time",
                )
            )

        if data.last_login_days > 14:
            factors.append(
                ChurnRiskFactor(
                    factor="low_engagement",
                    severity="high" if data.last_login_days > 30 else "medium",
                    impact=0.20 if data.last_login_days > 30 else 0.10,
                    description=f"Last login was {data.last_login_days} days ago",
                )
            )

        if data.support_tickets_90d > 5:
            factors.append(
                ChurnRiskFactor(
                    factor="high_support_burden",
                    severity="medium",
                    impact=0.15,
                    description=f"{data.support_tickets_90d} support tickets in 90 days",
                )
            )

        if data.nps_score is not None and data.nps_score < 6:
            factors.append(
                ChurnRiskFactor(
                    factor="low_nps",
                    severity="high",
                    impact=0.20,
                    description=f"NPS score of {data.nps_score} indicates detractor",
                )
            )

        if data.stakeholder_changes > 2:
            factors.append(
                ChurnRiskFactor(
                    factor="stakeholder_turnover",
                    severity="medium",
                    impact=0.15,
                    description=f"{data.stakeholder_changes} stakeholder changes in 6 months",
                )
            )

        if data.competitor_mentions > 0:
            factors.append(
                ChurnRiskFactor(
                    factor="competitor_mentions",
                    severity="medium",
                    impact=0.10 * min(data.competitor_mentions, 3),
                    description=f"Competitor mentioned {data.competitor_mentions} times",
                )
            )

        if data.feature_adoption_rate < 0.3:
            factors.append(
                ChurnRiskFactor(
                    factor="low_feature_adoption",
                    severity="medium",
                    impact=0.10,
                    description=f"Only {data.feature_adoption_rate:.0%} of features adopted",
                )
            )

        return factors

    def _identify_protective_factors(
        self, data: ChurnPredictionInput
    ) -> list[str]:
        """Identify factors that reduce churn risk.

        Args:
            data: Customer health data.

        Returns:
            List of protective factor descriptions.
        """
        factors: list[str] = []

        if data.usage_trend == "increasing":
            factors.append("Usage is increasing")
        if data.tenure_months > 12:
            factors.append(f"Long tenure ({data.tenure_months} months)")
        if data.nps_score is not None and data.nps_score >= 9:
            factors.append(f"High NPS score ({data.nps_score})")
        if data.feature_adoption_rate > 0.7:
            factors.append("High feature adoption")
        if data.engagement_score > 70:
            factors.append("Strong product engagement")

        return factors

    def _probability_to_risk_level(self, prob: float) -> str:
        """Convert probability to risk level.

        Args:
            prob: Churn probability (0-1).

        Returns:
            Risk level string.
        """
        if prob >= self.HIGH_RISK_THRESHOLD:
            return "high"
        if prob >= self.MEDIUM_RISK_THRESHOLD:
            return "medium"
        return "low"

    def _recommend_actions(
        self, risk_factors: list[ChurnRiskFactor], risk_level: str
    ) -> list[str]:
        """Generate recommended retention actions.

        Args:
            risk_factors: Identified risk factors.
            risk_level: Overall risk level.

        Returns:
            List of recommended actions.
        """
        actions: list[str] = []

        if risk_level == "high":
            actions.append("Schedule executive business review within 7 days")
            actions.append("Assign dedicated customer success manager")

        for factor in risk_factors:
            if factor.factor == "declining_usage":
                actions.append("Conduct product usage workshop")
            elif factor.factor == "low_engagement":
                actions.append("Send re-engagement email campaign")
            elif factor.factor == "high_support_burden":
                actions.append("Escalate to support leadership for root cause analysis")
            elif factor.factor == "low_nps":
                actions.append("Schedule NPS follow-up call")
            elif factor.factor == "stakeholder_turnover":
                actions.append("Map new stakeholders and rebuild relationships")
            elif factor.factor == "competitor_mentions":
                actions.append("Prepare competitive battle card and value proposition")

        if not actions:
            actions.append("Continue regular check-ins and monitor health metrics")

        return actions

    def _compute_confidence(self, data: ChurnPredictionInput) -> float:
        """Compute prediction confidence.

        Args:
            data: Customer data.

        Returns:
            Confidence score between 0 and 1.
        """
        # More data points = higher confidence
        data_points = 3  # Always have tenure, contract, usage
        if data.nps_score is not None:
            data_points += 1
        if data.contract_renewal_date:
            data_points += 1

        return min(0.95, 0.5 + (data_points * 0.1))

    def _build_summary(
        self, prob: float, risk_level: str, factors: list[ChurnRiskFactor]
    ) -> str:
        """Build prediction summary.

        Args:
            prob: Churn probability.
            risk_level: Risk level.
            factors: Risk factors.

        Returns:
            Summary string.
        """
        return (
            f"Churn probability: {prob:.0%} ({risk_level} risk). "
            f"{len(factors)} risk factors identified. "
            f"Prediction window: 90 days."
        )
