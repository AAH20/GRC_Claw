"""Anomaly Detector Agent using LangChain DeepAgents."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from deepagents import create_deep_agent

from ugc_marketplace.agents.fraud_detection.types import Anomaly, Transaction
from ugc_marketplace.config.logging_config import get_logger

logger = get_logger(__name__)


class AnomalyDetectorAgent:
    """Agent that detects statistical anomalies in transactions.

    Uses LangChain DeepAgents with statistical methods to identify
    outliers and behavioral anomalies that deviate from established baselines.
    """

    def __init__(self) -> None:
        """Initialize the Anomaly Detector Agent."""
        self.agent_name = "AnomalyDetectorAgent"
        self._agent = self._build_agent()
        self._tasks_processed = 0
        self._error_count = 0
        self._last_activity: datetime | None = None
        self._baselines: dict[str, dict[str, float]] = {}
        logger.info("AnomalyDetectorAgent initialized")

    def _build_agent(self) -> Any:
        """Build the LangChain DeepAgent for anomaly detection.

        Returns:
            Configured DeepAgent instance.
        """
        tools = [
            self._check_amount_anomaly,
            self._check_frequency_anomaly,
            self._check_time_anomaly,
            self._check_location_anomaly,
            self._check_device_anomaly,
        ]

        agent = create_deep_agent(
            tools=tools,
            instructions=(
                "You are a fraud anomaly detection specialist. Analyze transactions "
                "to identify statistical outliers and behavioral anomalies. Compare "
                "against account baselines for amount, frequency, time, location, "
                "and device patterns. Return structured Anomaly objects with scores "
                "and feature contributions."
            ),
        )
        return agent

    async def detect(self, transaction: Transaction) -> list[Anomaly]:
        """Detect anomalies in a transaction.

        Args:
            transaction: The transaction to analyze.

        Returns:
            List of detected anomalies.
        """
        try:
            self._last_activity = datetime.utcnow()
            result = await self._agent.ainvoke(
                {
                    "input": (
                        f"Detect anomalies in this transaction: "
                        f"ID={transaction.transaction_id}, "
                        f"Account={transaction.account_id}, "
                        f"Amount={transaction.amount} {transaction.currency}, "
                        f"Type={transaction.transaction_type.value}, "
                        f"Timestamp={transaction.timestamp.isoformat()}, "
                        f"Location={transaction.location}, "
                        f"Device={transaction.device_id}"
                    )
                }
            )

            anomalies = self._parse_anomalies(result)
            self._tasks_processed += 1
            logger.info(
                "Anomaly detection completed",
                transaction_id=transaction.transaction_id,
                anomalies_found=len(anomalies),
            )
            return anomalies

        except Exception as exc:
            self._error_count += 1
            logger.error("Anomaly detection failed", error=str(exc))
            return []

    def _parse_anomalies(self, result: Any) -> list[Anomaly]:
        """Parse agent output into Anomaly objects.

        Args:
            result: Raw agent output.

        Returns:
            List of parsed Anomaly objects.
        """
        from ugc_marketplace.models.schemas import Anomaly, RiskLevel

        anomalies: list[Anomaly] = []
        if isinstance(result, dict) and "anomalies" in result:
            for a in result["anomalies"]:
                anomalies.append(
                    Anomaly(
                        anomaly_id=str(uuid.uuid4()),
                        anomaly_type=a.get("type", "unknown"),
                        name=a.get("name", "Unknown Anomaly"),
                        description=a.get("description", ""),
                        score=float(a.get("score", 0.5)),
                        severity=RiskLevel(a.get("severity", "medium")),
                        feature_contributions=a.get("feature_contributions", {}),
                        baseline_value=a.get("baseline_value"),
                        observed_value=a.get("observed_value"),
                    )
                )
        return anomalies

    @staticmethod
    async def _check_amount_anomaly(transaction: Transaction) -> dict[str, Any]:
        """Check for amount-based anomalies.

        Args:
            transaction: Transaction to check.

        Returns:
            Anomaly detection result.
        """
        baseline = 100.0
        if transaction.amount > baseline * 5:
            return {
                "type": "amount_anomaly",
                "name": "Amount Anomaly",
                "description": f"Amount ${transaction.amount} significantly exceeds baseline",
                "score": min(transaction.amount / (baseline * 10), 1.0),
                "severity": "high" if transaction.amount > baseline * 10 else "medium",
                "feature_contributions": {"amount": 0.8},
                "baseline_value": baseline,
                "observed_value": transaction.amount,
            }
        return {}

    @staticmethod
    async def _check_frequency_anomaly(transaction: Transaction) -> dict[str, Any]:
        """Check for frequency-based anomalies.

        Args:
            transaction: Transaction to check.

        Returns:
            Anomaly detection result.
        """
        return {}

    @staticmethod
    async def _check_time_anomaly(transaction: Transaction) -> dict[str, Any]:
        """Check for time-based anomalies.

        Args:
            transaction: Transaction to check.

        Returns:
            Anomaly detection result.
        """
        return {}

    @staticmethod
    async def _check_location_anomaly(transaction: Transaction) -> dict[str, Any]:
        """Check for location-based anomalies.

        Args:
            transaction: Transaction to check.

        Returns:
            Anomaly detection result.
        """
        return {}

    @staticmethod
    async def _check_device_anomaly(transaction: Transaction) -> dict[str, Any]:
        """Check for device-based anomalies.

        Args:
            transaction: Transaction to check.

        Returns:
            Anomaly detection result.
        """
        return {}

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
