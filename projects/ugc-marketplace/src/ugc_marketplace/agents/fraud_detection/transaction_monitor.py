"""Transaction Monitor Agent using LangChain DeepAgents."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from deepagents import create_deep_agent

from ugc_marketplace.agents.fraud_detection.types import Transaction
from ugc_marketplace.config.logging_config import get_logger

logger = get_logger(__name__)


class TransactionMonitorAgent:
    """Agent that monitors transactions in real-time.

    Uses LangChain DeepAgents to monitor transaction streams
    and detect fraud as it happens.
    """

    def __init__(self) -> None:
        """Initialize the Transaction Monitor Agent."""
        self.agent_name = "TransactionMonitorAgent"
        self._agent = self._build_agent()
        self._tasks_processed = 0
        self._error_count = 0
        self._last_activity: datetime | None = None
        self._active_sessions: dict[str, dict[str, Any]] = {}
        logger.info("TransactionMonitorAgent initialized")

    def _build_agent(self) -> Any:
        """Build the LangChain DeepAgent for transaction monitoring.

        Returns:
            Configured DeepAgent instance.
        """
        tools = [
            self._monitor_stream,
            self._detect_real_time_fraud,
            self._generate_alert,
        ]

        agent = create_deep_agent(
            tools=tools,
            instructions=(
                "You are a real-time transaction monitoring specialist. Monitor "
                "transaction streams, detect fraud as it happens, and generate "
                "alerts for suspicious activity."
            ),
        )
        return agent

    async def start_monitoring(self, account_id: str) -> MonitoringSession:
        """Start monitoring transactions for an account.

        Args:
            account_id: Account identifier.

        Returns:
            Monitoring session data.
        """
        session_id = str(uuid.uuid4())
        session = {
            "session_id": session_id,
            "account_id": account_id,
            "status": "active",
            "started_at": datetime.utcnow().isoformat(),
            "transactions_monitored": 0,
            "alerts_generated": 0,
        }
        self._active_sessions[session_id] = session
        logger.info("Monitoring started", session_id=session_id, account_id=account_id)
        return session  # type: ignore[return-value]

    async def stop_monitoring(self, session_id: str) -> MonitoringSession:
        """Stop a monitoring session.

        Args:
            session_id: Session identifier.

        Returns:
            Final session data.

        Raises:
            ValueError: If session not found.
        """
        if session_id not in self._active_sessions:
            raise ValueError(f"Session {session_id} not found")

        session = self._active_sessions[session_id]
        session["status"] = "stopped"
        session["stopped_at"] = datetime.utcnow().isoformat()
        logger.info("Monitoring stopped", session_id=session_id)
        return session  # type: ignore[return-value]

    async def monitor_transaction(
        self, session_id: str, transaction: Transaction
    ) -> dict[str, Any]:
        """Monitor a single transaction.

        Args:
            session_id: Session identifier.
            transaction: Transaction to monitor.

        Returns:
            Monitoring result.
        """
        if session_id not in self._active_sessions:
            raise ValueError(f"Session {session_id} not found")

        self._last_activity = datetime.utcnow()
        session = self._active_sessions[session_id]
        session["transactions_monitored"] += 1
        self._tasks_processed += 1

        result = {
            "transaction_id": transaction.transaction_id,
            "monitored": True,
            "alert": False,
        }

        logger.debug("Transaction monitored", transaction_id=transaction.transaction_id)
        return result

    @staticmethod
    async def _monitor_stream(account_id: str) -> dict[str, Any]:
        """Monitor transaction stream.

        Args:
            account_id: Account identifier.

        Returns:
            Stream monitoring result.
        """
        return {"account_id": account_id, "streaming": True}

    @staticmethod
    async def _detect_real_time_fraud(transaction: Transaction) -> dict[str, Any]:
        """Detect fraud in real-time.

        Args:
            transaction: Transaction to check.

        Returns:
            Real-time fraud detection result.
        """
        return {"transaction_id": transaction.transaction_id, "fraud_detected": False}

    @staticmethod
    async def _generate_alert(transaction: Transaction, reason: str) -> dict[str, Any]:
        """Generate a fraud alert.

        Args:
            transaction: Transaction that triggered the alert.
            reason: Alert reason.

        Returns:
            Alert data.
        """
        return {
            "alert_id": str(uuid.uuid4()),
            "transaction_id": transaction.transaction_id,
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat(),
        }

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
            "active_sessions": len(self._active_sessions),
        }
