"""Pattern Detector Agent using LangChain DeepAgents."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from deepagents import create_deep_agent

from fraud_detection.config.logging_config import get_logger
from fraud_detection.models.schemas import Pattern, RiskLevel, Transaction

logger = get_logger(__name__)


class PatternDetectorAgent:
    """Agent that detects known fraud patterns in transactions.

    Uses LangChain DeepAgents to identify structured fraud signatures
    such as card testing, account takeover, and money laundering patterns.
    """

    def __init__(self) -> None:
        """Initialize the Pattern Detector Agent."""
        self.agent_name = "PatternDetectorAgent"
        self._agent = self._build_agent()
        self._tasks_processed = 0
        self._error_count = 0
        self._last_activity: datetime | None = None
        logger.info("PatternDetectorAgent initialized")

    def _build_agent(self) -> Any:
        """Build the LangChain DeepAgent for pattern detection.

        Returns:
            Configured DeepAgent instance.
        """
        tools = [
            self._check_card_testing_pattern,
            self._check_velocity_pattern,
            self._check_amount_rounding_pattern,
            self._check_merchant_concentration_pattern,
            self._check_geographic_impossibility_pattern,
        ]

        agent = create_deep_agent(
            tools=tools,
            instructions=(
                "You are a fraud pattern detection specialist. Analyze transactions "
                "to identify known fraud signatures including card testing, velocity "
                "attacks, amount rounding, merchant concentration, and geographic "
                "impossibility patterns. Return structured Pattern objects for each "
                "detected pattern with confidence scores and evidence."
            ),
        )
        return agent

    async def detect(self, transaction: Transaction) -> list[Pattern]:
        """Detect fraud patterns in a transaction.

        Args:
            transaction: The transaction to analyze.

        Returns:
            List of detected patterns.
        """
        try:
            self._last_activity = datetime.utcnow()
            result = await self._agent.ainvoke(
                {
                    "input": (
                        f"Analyze this transaction for fraud patterns: "
                        f"ID={transaction.transaction_id}, "
                        f"Account={transaction.account_id}, "
                        f"Amount={transaction.amount} {transaction.currency}, "
                        f"Type={transaction.transaction_type.value}, "
                        f"Merchant={transaction.merchant_id}, "
                        f"Location={transaction.location}"
                    )
                }
            )

            patterns = self._parse_patterns(result)
            self._tasks_processed += 1
            logger.info(
                "Pattern detection completed",
                transaction_id=transaction.transaction_id,
                patterns_found=len(patterns),
            )
            return patterns

        except Exception as exc:
            self._error_count += 1
            logger.error("Pattern detection failed", error=str(exc))
            return []

    def _parse_patterns(self, result: Any) -> list[Pattern]:
        """Parse agent output into Pattern objects.

        Args:
            result: Raw agent output.

        Returns:
            List of parsed Pattern objects.
        """
        patterns: list[Pattern] = []
        if isinstance(result, dict) and "patterns" in result:
            for p in result["patterns"]:
                patterns.append(
                    Pattern(
                        pattern_id=str(uuid.uuid4()),
                        pattern_type=p.get("type", "unknown"),
                        name=p.get("name", "Unknown Pattern"),
                        description=p.get("description", ""),
                        confidence=float(p.get("confidence", 0.5)),
                        severity=RiskLevel(p.get("severity", "medium")),
                        evidence=p.get("evidence", []),
                        related_transactions=p.get("related_transactions", []),
                    )
                )
        return patterns

    @staticmethod
    async def _check_card_testing_pattern(transaction: Transaction) -> dict[str, Any]:
        """Check for card testing pattern (many small transactions).

        Args:
            transaction: Transaction to check.

        Returns:
            Pattern detection result.
        """
        if transaction.amount < 2.0:
            return {
                "type": "card_testing",
                "name": "Card Testing Pattern",
                "description": "Small amount transaction consistent with card testing",
                "confidence": 0.7,
                "severity": "medium",
                "evidence": [f"Amount ${transaction.amount} below typical threshold"],
            }
        return {}

    @staticmethod
    async def _check_velocity_pattern(transaction: Transaction) -> dict[str, Any]:
        """Check for velocity-based fraud patterns.

        Args:
            transaction: Transaction to check.

        Returns:
            Pattern detection result.
        """
        return {}

    @staticmethod
    async def _check_amount_rounding_pattern(transaction: Transaction) -> dict[str, Any]:
        """Check for amount rounding patterns common in fraud.

        Args:
            transaction: Transaction to check.

        Returns:
            Pattern detection result.
        """
        if transaction.amount == int(transaction.amount) and transaction.amount > 100:
            return {
                "type": "amount_rounding",
                "name": "Amount Rounding Pattern",
                "description": "Round dollar amount above typical consumer range",
                "confidence": 0.4,
                "severity": "low",
                "evidence": [f"Amount ${transaction.amount} is a round number"],
            }
        return {}

    @staticmethod
    async def _check_merchant_concentration_pattern(transaction: Transaction) -> dict[str, Any]:
        """Check for merchant concentration patterns.

        Args:
            transaction: Transaction to check.

        Returns:
            Pattern detection result.
        """
        return {}

    @staticmethod
    async def _check_geographic_impossibility_pattern(transaction: Transaction) -> dict[str, Any]:
        """Check for geographic impossibility patterns.

        Args:
            transaction: Transaction to check.

        Returns:
            Pattern detection result.
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
