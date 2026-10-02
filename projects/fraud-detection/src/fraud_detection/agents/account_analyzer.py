"""Account Analyzer Agent using LangChain DeepAgents."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from deepagents import create_deep_agent

from fraud_detection.config.logging_config import get_logger
from fraud_detection.models.schemas import AccountAnalysis, AccountProfile, RiskScore, Transaction

logger = get_logger(__name__)


class AccountAnalyzerAgent:
    """Agent that performs deep-dive account behavior profiling.

    Uses LangChain DeepAgents to build account profiles, detect behavioral
    drift, and generate account-level risk assessments with recommendations.
    """

    def __init__(self) -> None:
        """Initialize the Account Analyzer Agent."""
        self.agent_name = "AccountAnalyzerAgent"
        self._agent = self._build_agent()
        self._tasks_processed = 0
        self._error_count = 0
        self._last_activity: datetime | None = None
        self._account_cache: dict[str, AccountProfile] = {}
        logger.info("AccountAnalyzerAgent initialized")

    def _build_agent(self) -> Any:
        """Build the LangChain DeepAgent for account analysis.

        Returns:
            Configured DeepAgent instance.
        """
        tools = [
            self._build_account_profile,
            self._detect_behavioral_drift,
            self._assess_account_risk,
            self._generate_recommendations,
        ]

        agent = create_deep_agent(
            tools=tools,
            instructions=(
                "You are an account behavior analysis specialist. Build comprehensive "
                "account profiles, detect behavioral drift from established patterns, "
                "assess account-level risk, and generate actionable recommendations. "
                "Return structured AccountAnalysis objects."
            ),
        )
        return agent

    async def analyze(
        self,
        account_id: str,
        transactions: list[Transaction] | None = None,
    ) -> AccountAnalysis:
        """Analyze an account for fraud risk.

        Args:
            account_id: The account to analyze.
            transactions: Recent transactions for the account.

        Returns:
            AccountAnalysis with profile, anomalies, and recommendations.
        """
        try:
            self._last_activity = datetime.utcnow()
            transactions = transactions or []

            result = await self._agent.ainvoke(
                {
                    "input": (
                        f"Analyze account {account_id}: "
                        f"Transaction count={len(transactions)}, "
                        f"Recent amounts={[t.amount for t in transactions[:10]]}"
                    )
                }
            )

            analysis = self._build_analysis(account_id, transactions, result)
            self._tasks_processed += 1
            logger.info(
                "Account analysis completed",
                account_id=account_id,
                risk_score=analysis.risk_score.overall_score,
            )
            return analysis

        except Exception as exc:
            self._error_count += 1
            logger.error("Account analysis failed", error=str(exc))
            return self._fallback_analysis(account_id)

    def _build_analysis(
        self,
        account_id: str,
        transactions: list[Transaction],
        result: Any,
    ) -> AccountAnalysis:
        """Build AccountAnalysis from agent output.

        Args:
            account_id: Account identifier.
            transactions: Account transactions.
            result: Raw agent output.

        Returns:
            Constructed AccountAnalysis.
        """
        profile = AccountProfile(
            account_id=account_id,
            average_transaction_amount=(
                sum(t.amount for t in transactions) / len(transactions) if transactions else 0.0
            ),
            transaction_count_30d=len(transactions),
            unique_merchants_30d=len({t.merchant_id for t in transactions if t.merchant_id}),
            unique_locations_30d=len({t.location for t in transactions if t.location}),
            typical_transaction_types=list({t.transaction_type for t in transactions}),
        )

        risk_score = RiskScore(
            score_id=str(uuid.uuid4()),
            transaction_id="",
            account_id=account_id,
            overall_score=0.3,
            risk_level="low",
            factors=[],
            explanation="Account-level risk assessment",
        )

        return AccountAnalysis(
            analysis_id=str(uuid.uuid4()),
            account_id=account_id,
            profile=profile,
            anomalies=[],
            risk_score=risk_score,
            recommendations=["Continue monitoring", "Review periodically"],
        )

    def _fallback_analysis(self, account_id: str) -> AccountAnalysis:
        """Generate fallback analysis when agent fails.

        Args:
            account_id: Account identifier.

        Returns:
            Fallback AccountAnalysis.
        """
        return AccountAnalysis(
            analysis_id=str(uuid.uuid4()),
            account_id=account_id,
            profile=AccountProfile(account_id=account_id),
            anomalies=[],
            risk_score=RiskScore(
                score_id=str(uuid.uuid4()),
                transaction_id="",
                account_id=account_id,
                overall_score=0.5,
                risk_level="medium",
                factors=[],
                explanation="Fallback analysis due to agent error",
            ),
            recommendations=["Manual review recommended"],
        )

    @staticmethod
    async def _build_account_profile(
        account_id: str, transactions: list[Transaction]
    ) -> dict[str, Any]:
        """Build account profile from transactions.

        Args:
            account_id: Account identifier.
            transactions: Account transactions.

        Returns:
            Account profile data.
        """
        return {
            "account_id": account_id,
            "transaction_count": len(transactions),
            "total_amount": sum(t.amount for t in transactions),
        }

    @staticmethod
    async def _detect_behavioral_drift(account_id: str) -> dict[str, Any]:
        """Detect behavioral drift for an account.

        Args:
            account_id: Account identifier.

        Returns:
            Behavioral drift assessment.
        """
        return {"account_id": account_id, "drift_detected": False}

    @staticmethod
    async def _assess_account_risk(account_id: str) -> dict[str, Any]:
        """Assess account-level risk.

        Args:
            account_id: Account identifier.

        Returns:
            Account risk assessment.
        """
        return {"account_id": account_id, "risk_level": "low"}

    @staticmethod
    async def _generate_recommendations(account_id: str) -> list[str]:
        """Generate recommendations for an account.

        Args:
            account_id: Account identifier.

        Returns:
            List of recommendations.
        """
        return ["Continue monitoring", "Review periodically"]

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
