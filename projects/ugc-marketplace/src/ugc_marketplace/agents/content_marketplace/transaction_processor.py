"""Transaction Processor Agent for content marketplace."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage

from ugc_marketplace.models.schemas import Transaction, TransactionCreate, TransactionStatus

logger = logging.getLogger(__name__)


class TransactionProcessorAgent:
    """Agent that processes marketplace transactions.

    Handles transaction lifecycle from creation through
    completion, including refunds.
    """

    def __init__(self, model: BaseChatModel | None = None) -> None:
        """Initialize the transaction processor agent.

        Args:
            model: Optional pre-configured chat model.
        """
        self._model = model
        self._transactions: dict[str, Transaction] = {}

    async def create_transaction(self, data: TransactionCreate) -> Transaction:
        """Create a new transaction.

        Args:
            data: Transaction creation data.

        Returns:
            Created transaction.
        """
        tx = Transaction(
            transaction_id=str(UUID(int=0)),
            listing_id=data.listing_id,
            buyer_id=data.buyer_id,
            seller_id=data.seller_id,
            amount=data.amount,
            currency=data.currency,
            status=TransactionStatus.PENDING,
        )
        self._transactions[tx.transaction_id] = tx
        logger.info("Transaction created", transaction_id=tx.transaction_id)
        return tx

    async def process_transaction(self, transaction_id: str) -> Transaction:
        """Process a pending transaction.

        Args:
            transaction_id: Transaction identifier.

        Returns:
            Updated transaction.

        Raises:
            ValueError: If transaction not found.
        """
        if transaction_id not in self._transactions:
            raise ValueError(f"Transaction {transaction_id} not found")

        tx = self._transactions[transaction_id]
        tx.status = TransactionStatus.PROCESSING
        logger.info("Transaction processing", transaction_id=transaction_id)
        return tx

    async def complete_transaction(self, transaction_id: str) -> Transaction:
        """Complete a transaction.

        Args:
            transaction_id: Transaction identifier.

        Returns:
            Updated transaction.

        Raises:
            ValueError: If transaction not found.
        """
        if transaction_id not in self._transactions:
            raise ValueError(f"Transaction {transaction_id} not found")

        tx = self._transactions[transaction_id]
        tx.status = TransactionStatus.COMPLETED
        tx.completed_at = datetime.now(UTC)
        logger.info("Transaction completed", transaction_id=transaction_id)
        return tx

    async def refund_transaction(self, transaction_id: str) -> Transaction:
        """Refund a transaction.

        Args:
            transaction_id: Transaction identifier.

        Returns:
            Updated transaction.

        Raises:
            ValueError: If transaction not found.
        """
        if transaction_id not in self._transactions:
            raise ValueError(f"Transaction {transaction_id} not found")

        tx = self._transactions[transaction_id]
        tx.status = TransactionStatus.REFUNDED
        logger.info("Transaction refunded", transaction_id=transaction_id)
        return tx

    def get_transaction(self, transaction_id: str) -> Transaction | None:
        """Get a transaction by ID.

        Args:
            transaction_id: Transaction identifier.

        Returns:
            Transaction or None.
        """
        return self._transactions.get(transaction_id)

    def get_stats(self) -> dict[str, Any]:
        """Get transaction statistics.

        Returns:
            Transaction statistics.
        """
        total = len(self._transactions)
        by_status: dict[str, int] = {}
        for tx in self._transactions.values():
            by_status[tx.status.value] = by_status.get(tx.status.value, 0) + 1

        return {
            "total": total,
            "by_status": by_status,
        }
