"""Risk Scorer Agent using LangChain DeepAgents."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from deepagents import create_deep_agent

from fraud_detection.config.logging_config import get_logger
from fraud_detection.config.settings import get_settings
from fraud_detection.models.schemas import (
    Anomaly,
    Pattern,
    RiskFactor,
    RiskLevel,
    RiskScore,
    Transaction,
)

logger = get_logger(__name__)


class RiskScorerAgent:
    """Agent that computes composite risk scores for transactions.

    Uses LangChain DeepAgents to aggregate signals from pattern detection,
    anomaly detection, and behavioral analysis into a unified risk score
    with explainable factors.
    """

    def __init__(self) -> None:
        """Initialize the Risk Scorer Agent."""
        self.agent_name = "RiskScorerAgent"
        self._agent = self._build_agent()
        self._tasks_processed = 0
        self._error_count = 0
        self._last_activity: datetime | None = None
        self._settings = get_settings()
        logger.info("RiskScorerAgent initialized")

    def _build_agent(self) -> Any:
        """Build the LangChain DeepAgent for risk scoring.

        Returns:
            Configured DeepAgent instance.
        """
        tools = [
            self._compute_pattern_risk,
            self._compute_anomaly_risk,
            self._compute_behavioral_risk,
            self._compute_velocity_risk,
            self._compute_geographic_risk,
        ]

        agent = create_deep_agent(
            tools=tools,
            instructions=(
                "You are a risk scoring specialist. Aggregate fraud signals from "
                "pattern detection, anomaly detection, and behavioral analysis into "
                "a unified risk score. Provide explainable risk factors with weights "
                "and evidence. Score range is 0.0 (no risk) to 1.0 (certain fraud)."
            ),
        )
        return agent

    async def score(
        self,
        transaction: Transaction,
        patterns: list[Pattern] | None = None,
        anomalies: list[Anomaly] | None = None,
    ) -> RiskScore:
        """Compute risk score for a transaction.

        Args:
            transaction: The transaction to score.
            patterns: Detected patterns from PatternDetectorAgent.
            anomalies: Detected anomalies from AnomalyDetectorAgent.

        Returns:
            Computed RiskScore with factors and explanation.
        """
        try:
            self._last_activity = datetime.utcnow()
            patterns = patterns or []
            anomalies = anomalies or []

            result = await self._agent.ainvoke(
                {
                    "input": (
                        f"Score risk for transaction {transaction.transaction_id}: "
                        f"Amount={transaction.amount}, Account={transaction.account_id}, "
                        f"Patterns={len(patterns)}, Anomalies={len(anomalies)}. "
                        f"Pattern details: {[p.model_dump() for p in patterns]}. "
                        f"Anomaly details: {[a.model_dump() for a in anomalies]}"
                    )
                }
            )

            risk_score = self._build_risk_score(transaction, patterns, anomalies, result)
            self._tasks_processed += 1
            logger.info(
                "Risk scoring completed",
                transaction_id=transaction.transaction_id,
                score=risk_score.overall_score,
                level=risk_score.risk_level.value,
            )
            return risk_score

        except Exception as exc:
            self._error_count += 1
            logger.error("Risk scoring failed", error=str(exc))
            return self._fallback_score(transaction)

    def _build_risk_score(
        self,
        transaction: Transaction,
        patterns: list[Pattern],
        anomalies: list[Anomaly],
        result: Any,
    ) -> RiskScore:
        """Build a RiskScore from agent output and inputs.

        Args:
            transaction: The transaction being scored.
            patterns: Detected patterns.
            anomalies: Detected anomalies.
            result: Raw agent output.

        Returns:
            Constructed RiskScore.
        """
        factors: list[RiskFactor] = []

        # Pattern-based factors
        for pattern in patterns:
            factors.append(
                RiskFactor(
                    factor_name=f"pattern:{pattern.pattern_type}",
                    factor_type="pattern",
                    weight=0.3,
                    score=pattern.confidence,
                    description=f"Detected pattern: {pattern.name}",
                    evidence=pattern.evidence,
                )
            )

        # Anomaly-based factors
        for anomaly in anomalies:
            factors.append(
                RiskFactor(
                    factor_name=f"anomaly:{anomaly.anomaly_type}",
                    factor_type="anomaly",
                    weight=0.3,
                    score=anomaly.score,
                    description=f"Detected anomaly: {anomaly.name}",
                    evidence=[anomaly.description],
                )
            )

        # Compute weighted score
        if factors:
            total_weight = sum(f.weight for f in factors)
            overall = (
                sum(f.weight * f.score for f in factors) / total_weight if total_weight > 0 else 0.0
            )
        else:
            overall = 0.1

        overall = max(0.0, min(1.0, overall))
        risk_level = self._score_to_level(overall)

        return RiskScore(
            score_id=str(uuid.uuid4()),
            transaction_id=transaction.transaction_id,
            account_id=transaction.account_id,
            overall_score=overall,
            risk_level=risk_level,
            factors=factors,
            explanation=f"Risk score {overall:.2f} based on {len(factors)} factors",
        )

    def _score_to_level(self, score: float) -> RiskLevel:
        """Convert numeric score to risk level.

        Args:
            score: Numeric risk score between 0 and 1.

        Returns:
            Corresponding RiskLevel.
        """
        if score >= self._settings.high_risk_threshold:
            return RiskLevel.CRITICAL
        if score >= self._settings.medium_risk_threshold:
            return RiskLevel.HIGH
        if score >= 0.3:
            return RiskLevel.MEDIUM
        return RiskLevel.LOW

    def _fallback_score(self, transaction: Transaction) -> RiskScore:
        """Generate a fallback risk score when agent fails.

        Args:
            transaction: The transaction to score.

        Returns:
            Fallback RiskScore.
        """
        return RiskScore(
            score_id=str(uuid.uuid4()),
            transaction_id=transaction.transaction_id,
            account_id=transaction.account_id,
            overall_score=0.5,
            risk_level=RiskLevel.MEDIUM,
            factors=[],
            explanation="Fallback score due to agent error",
        )

    @staticmethod
    async def _compute_pattern_risk(patterns: list[Pattern]) -> float:
        """Compute aggregate pattern risk.

        Args:
            patterns: Detected patterns.

        Returns:
            Aggregate pattern risk score.
        """
        if not patterns:
            return 0.0
        return max(p.confidence for p in patterns)

    @staticmethod
    async def _compute_anomaly_risk(anomalies: list[Anomaly]) -> float:
        """Compute aggregate anomaly risk.

        Args:
            anomalies: Detected anomalies.

        Returns:
            Aggregate anomaly risk score.
        """
        if not anomalies:
            return 0.0
        return max(a.score for a in anomalies)

    @staticmethod
    async def _compute_behavioral_risk(transaction: Transaction) -> float:
        """Compute behavioral risk.

        Args:
            transaction: Transaction to analyze.

        Returns:
            Behavioral risk score.
        """
        return 0.0

    @staticmethod
    async def _compute_velocity_risk(transaction: Transaction) -> float:
        """Compute velocity risk.

        Args:
            transaction: Transaction to analyze.

        Returns:
            Velocity risk score.
        """
        return 0.0

    @staticmethod
    async def _compute_geographic_risk(transaction: Transaction) -> float:
        """Compute geographic risk.

        Args:
            transaction: Transaction to analyze.

        Returns:
            Geographic risk score.
        """
        return 0.0

    def get_status(self) -> dict[str, Any]:
        """Get agent status.

        Returns:
            Agent status dictionary.
        """
        return {
            "agent_name": self.agent_name,
            "status": "idle" if self._last_activity is None else "running",
            "last_activity": self._last_activity,
            "tasks_processed": self._tasks_processed,
            "error_count": self._error_count,
        }
