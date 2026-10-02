"""Transaction Monitor Agent using LangChain DeepAgents."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from deepagents import create_deep_agent

from fraud_detection.config.logging_config import get_logger
from fraud_detection.models.schemas import MonitoringSession, Transaction

logger = get_logger(__name__)


class TransactionMonitorAgent:
    """Agent that monitors transaction streams in real-time.

    Uses LangChain DeepAgents to watch for suspicious activity patterns
    across transaction streams and generate alerts when thresholds are breached.
    """

    def __init__(self) -> None:
        """Initialize the Transaction Monitor Agent."""
        self.agent_name = "TransactionMonitorAgent"
        self._agent = self._build_agent()
        self._tasks_processed = 0
        self._error_count = 0
        self._last_activity: datetime | None = None
        self._active_sessions: dict[str, MonitoringSession] = {}
        logger.info("TransactionMonitorAgent initialized")

    def _build_agent(self) -> Any:
        """Build the LangChain DeepAgent for transaction monitoring.

        Returns:
            Configured DeepAgent instance.
        """
        tools = [
            self._monitor_account_stream,
            self._detect_stream_anomalies,
            self._generate_alert,
            self._update_session,
        ]

        agent = create_deep_agent(
            tools=tools,
            instructions=(
                "You are a real-time transaction monitoring specialist. Watch "
                "transaction streams for suspicious activity, detect anomalies "
                "in real-time, generate alerts when risk thresholds are breached, "
                "and maintain monitoring session state."
            ),
        )
        return agent

    async def start_monitoring(self, account_id: str) -> MonitoringSession:
        """Start monitoring an account's transaction stream.

        Args:
            account_id: The account to monitor.

        Returns:
            MonitoringSession for the new session.
        """
        try:
            self._last_activity = datetime.utcnow()
            session_id = str(uuid.uuid4())

            await self._agent.ainvoke(
                {
                    "input": (
                        f"Start monitoring account {account_id}. "
                        f"Set up real-time transaction stream analysis."
                    )
                }
            )

            session = MonitoringSession(
                session_id=session_id,
                account_id=account_id,
                status="active",
            )
            self._active_sessions[session_id] = session
            self._tasks_processed += 1
            logger.info("Monitoring session started", session_id=session_id, account_id=account_id)
            return session

        except Exception as exc:
            self._error_count += 1
            logger.error("Failed to start monitoring", error=str(exc))
            raise

    async def stop_monitoring(self, session_id: str) -> MonitoringSession:
        """Stop a monitoring session.

        Args:
            session_id: The session to stop.

        Returns:
            Updated MonitoringSession.

        Raises:
            ValueError: If session_id is not found.
        """
        if session_id not in self._active_sessions:
            raise ValueError(f"Monitoring session {session_id} not found")

        session = self._active_sessions[session_id]
        session.status = "stopped"
        self._last_activity = datetime.utcnow()
        self._tasks_processed += 1
        logger.info("Monitoring session stopped", session_id=session_id)
        return session

    async def process_transaction(
        self,
        session_id: str,
        transaction: Transaction,
    ) -> dict[str, Any]:
        """Process a transaction within a monitoring session.

        Args:
            session_id: Active monitoring session ID.
            transaction: Transaction to process.

        Returns:
            Processing result with alerts if any.

        Raises:
            ValueError: If session_id is not found.
        """
        if session_id not in self._active_sessions:
            raise ValueError(f"Monitoring session {session_id} not found")

        try:
            self._last_activity = datetime.utcnow()
            result = await self._agent.ainvoke(
                {
                    "input": (
                        f"Process transaction {transaction.transaction_id} "
                        f"for account {transaction.account_id}: "
                        f"Amount={transaction.amount}, Type={transaction.transaction_type.value}"
                    )
                }
            )

            self._tasks_processed += 1
            return result if isinstance(result, dict) else {"status": "processed"}

        except Exception as exc:
            self._error_count += 1
            logger.error("Transaction processing failed", error=str(exc))
            return {"status": "error", "error": str(exc)}

    def get_session(self, session_id: str) -> MonitoringSession | None:
        """Get a monitoring session by ID.

        Args:
            session_id: Session identifier.

        Returns:
            MonitoringSession if found, None otherwise.
        """
        return self._active_sessions.get(session_id)

    def list_sessions(self) -> list[MonitoringSession]:
        """List all monitoring sessions.

        Returns:
            List of all monitoring sessions.
        """
        return list(self._active_sessions.values())

    @staticmethod
    async def _monitor_account_stream(account_id: str) -> dict[str, Any]:
        """Monitor an account's transaction stream.

        Args:
            account_id: Account to monitor.

        Returns:
            Stream monitoring status.
        """
        return {"account_id": account_id, "status": "monitoring"}

    @staticmethod
    async def _detect_stream_anomalies(transactions: list[Transaction]) -> list[dict[str, Any]]:
        """Detect anomalies in a stream of transactions.

        Args:
            transactions: Transactions to analyze.

        Returns:
            List of detected anomalies.
        """
        return []

    @staticmethod
    async def _generate_alert(account_id: str, reason: str) -> dict[str, Any]:
        """Generate a fraud alert.

        Args:
            account_id: Account identifier.
            reason: Alert reason.

        Returns:
            Alert data.
        """
        return {
            "alert_id": str(uuid.uuid4()),
            "account_id": account_id,
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat(),
        }

    @staticmethod
    async def _update_session(session_id: str, status: str) -> dict[str, Any]:
        """Update monitoring session status.

        Args:
            session_id: Session identifier.
            status: New status.

        Returns:
            Updated session data.
        """
        return {"session_id": session_id, "status": status}

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
