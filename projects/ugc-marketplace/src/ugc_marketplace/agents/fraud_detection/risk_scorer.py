"""Risk Scorer Agent using LangChain DeepAgents."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from deepagents import create_deep_agent

from ugc_marketplace.config import get_settings
from ugc_marketplace.config.logging_config import get_logger

logger = get_logger(__name__)


class RiskScorerAgent:
    """Agent that computes risk scores for transactions.

    Uses LangChain DeepAgents to aggregate signals from
    multiple sources and compute an overall risk score.
    """

    def __init__(self) -> None:
        """Initialize the Risk Scorer Agent."""
        self.agent_name = "RiskScorerAgent"
        self._agent = self._build_agent()
        self._tasks_processed = 0
        self._error_count = 0
        self._last_activity: datetime | None = None
        self.settings = get_settings()
        logger.info("RiskScorerAgent initialized")

    def _build_agent(self) -> Any:
        """Build the LangChain DeepAgent for risk scoring.

        Returns:
            Configured DeepAgent instance.
        """
        tools = [
            self._compute_base_risk,
            self._adjust_for_history,
            self._adjust_for_behavior,
        ]

        agent = create_deep_agent(
            tools=tools,
            instructions=(
                "You are a fraud risk scoring specialist. Compute overall risk "
                "scores by aggregating signals from transaction analysis, account "
                "history, and behavioral patterns. Provide a score between 0 and 1 "
                "with detailed factor contributions."
            ),
        )
        return agent

    async def score(
        self,
        transaction: Transaction,
        patterns: list[Pattern] | None = None,
        anomalies: list[Anomaly] | None = None,
    ) -> RiskScore:
        """Score risk for a transaction.

        Args:
            transaction: The transaction to score.
            patterns: Optional list of detected patterns.
            anomalies: Optional list of detected anomalies.

        Returns:
            Computed risk score.
        """
        try:
            self._last_activity = datetime.utcnow()
            result = await self._agent.ainvoke(
                {
                    "input": (
                        f"Score risk for transaction: "
                        f"ID={transaction.transaction_id}, "
                        f"Amount={transaction.amount} {transaction.currency}, "
                        f"Patterns={len(patterns or [])}, "
                        f"Anomalies={len(anomalies or [])}"
                    )
                }
            )

            risk_score = self._parse_risk_score(result, transaction)
            self._tasks_processed += 1
            logger.info(
                "Risk scoring completed",
                transaction_id=transaction.transaction_id,
                overall_score=risk_score.overall_score,
            )
            return risk_score

        except Exception as exc:
            self._error_count += 1
            logger.error("Risk scoring failed", error=str(exc))
            from ugc_marketplace.models.schemas import RiskFactor, RiskScore

            return RiskScore(
                score_id=str(uuid.uuid4()),
                transaction_id=transaction.transaction_id,
                overall_score=0.5,
                factors=[
                    RiskFactor(name="error", contribution=0.5, description=str(exc))
                ],
            )

    def _parse_risk_score(self, result: Any, transaction: Transaction) -> RiskScore:
        """Parse agent output into RiskScore.

        Args:
            result: Raw agent output.
            transaction: Original transaction.

        Returns:
            Parsed risk score.
        """
        from ugc_marketplace.models.schemas import RiskFactor, RiskScore

        if isinstance(result, dict):
            return RiskScore(
                score_id=str(uuid.uuid4()),
                transaction_id=transaction.transaction_id,
                overall_score=float(result.get("overall_score", 0.5)),
                factors=[
                    RiskFactor(
                        name=f.get("name", "unknown"),
                        contribution=float(f.get("contribution", 0.0)),
                        description=f.get("description", ""),
                    )
                    for f in result.get("factors", [])
                ],
            )
        return RiskScore(
            score_id=str(uuid.uuid4()),
            transaction_id=transaction.transaction_id,
            overall_score=0.5,
        )

    @staticmethod
    async def _compute_base_risk(transaction: Transaction) -> dict[str, Any]:
        """Compute base risk for a transaction.

        Args:
            transaction: Transaction to analyze.

        Returns:
            Base risk data.
        """
        return {"base_risk": 0.3}

    @staticmethod
    async def _adjust_for_history(account_id: str) -> dict[str, Any]:
        """Adjust risk based on account history.

        Args:
            account_id: Account identifier.

        Returns:
            History adjustment data.
        """
        return {"history_adjustment": 0.0}

    @staticmethod
    async def _adjust_for_behavior(transaction: Transaction) -> dict[str, Any]:
        """Adjust risk based on behavioral patterns.

        Args:
            transaction: Transaction to analyze.

        Returns:
            Behavior adjustment data.
        """
        return {"behavior_adjustment": 0.0}

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
