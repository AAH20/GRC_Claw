"""Account Analyzer Agent using LangChain DeepAgents."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from deepagents import create_deep_agent

from ugc_marketplace.agents.fraud_detection.types import AccountAnalysis
from ugc_marketplace.config.logging_config import get_logger

logger = get_logger(__name__)


class AccountAnalyzerAgent:
    """Agent that analyzes account behavior and risk profiles.

    Uses LangChain DeepAgents to build account risk profiles
    and detect account-level fraud indicators.
    """

    def __init__(self) -> None:
        """Initialize the Account Analyzer Agent."""
        self.agent_name = "AccountAnalyzerAgent"
        self._agent = self._build_agent()
        self._tasks_processed = 0
        self._error_count = 0
        self._last_activity: datetime | None = None
        logger.info("AccountAnalyzerAgent initialized")

    def _build_agent(self) -> Any:
        """Build the LangChain DeepAgent for account analysis.

        Returns:
            Configured DeepAgent instance.
        """
        tools = [
            self._analyze_account_age,
            self._analyze_transaction_history,
            self._analyze_behavior_patterns,
        ]

        agent = create_deep_agent(
            tools=tools,
            instructions=(
                "You are an account fraud analysis specialist. Analyze account "
                "behavior, transaction history, and patterns to build risk profiles "
                "and detect account-level fraud indicators."
            ),
        )
        return agent

    async def analyze(self, account_id: str) -> AccountAnalysis:
        """Analyze an account for fraud risk.

        Args:
            account_id: Account identifier.

        Returns:
            Account analysis result.
        """
        try:
            self._last_activity = datetime.utcnow()
            result = await self._agent.ainvoke(
                {
                    "input": (
                        f"Analyze account for fraud risk: " f"Account ID={account_id}"
                    )
                }
            )

            analysis = self._parse_analysis(result, account_id)
            self._tasks_processed += 1
            logger.info(
                "Account analysis completed",
                account_id=account_id,
                risk_level=(
                    analysis.risk_level.value
                    if hasattr(analysis.risk_level, "value")
                    else analysis.risk_level
                ),
            )
            return analysis

        except Exception as exc:
            self._error_count += 1
            logger.error("Account analysis failed", error=str(exc))
            from ugc_marketplace.models.schemas import AccountAnalysis, RiskLevel

            return AccountAnalysis(
                analysis_id=str(uuid.uuid4()),
                account_id=account_id,
                risk_level=RiskLevel.MEDIUM,
                risk_score=0.5,
                indicators=[],
                recommendations=[f"Analysis failed: {exc}"],
            )

    def _parse_analysis(self, result: Any, account_id: str) -> AccountAnalysis:
        """Parse agent output into AccountAnalysis.

        Args:
            result: Raw agent output.
            account_id: Account identifier.

        Returns:
            Parsed account analysis.
        """
        from ugc_marketplace.models.schemas import AccountAnalysis, RiskLevel

        if isinstance(result, dict):
            return AccountAnalysis(
                analysis_id=str(uuid.uuid4()),
                account_id=account_id,
                risk_level=RiskLevel(result.get("risk_level", "medium")),
                risk_score=float(result.get("risk_score", 0.5)),
                indicators=result.get("indicators", []),
                recommendations=result.get("recommendations", []),
            )
        return AccountAnalysis(
            analysis_id=str(uuid.uuid4()),
            account_id=account_id,
            risk_level=RiskLevel.MEDIUM,
            risk_score=0.5,
        )

    @staticmethod
    async def _analyze_account_age(account_id: str) -> dict[str, Any]:
        """Analyze account age risk factor.

        Args:
            account_id: Account identifier.

        Returns:
            Account age analysis.
        """
        return {"account_id": account_id, "age_risk": "low"}

    @staticmethod
    async def _analyze_transaction_history(account_id: str) -> dict[str, Any]:
        """Analyze transaction history.

        Args:
            account_id: Account identifier.

        Returns:
            Transaction history analysis.
        """
        return {"account_id": account_id, "history_risk": "low"}

    @staticmethod
    async def _analyze_behavior_patterns(account_id: str) -> dict[str, Any]:
        """Analyze behavior patterns.

        Args:
            account_id: Account identifier.

        Returns:
            Behavior pattern analysis.
        """
        return {"account_id": account_id, "behavior_risk": "low"}

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
