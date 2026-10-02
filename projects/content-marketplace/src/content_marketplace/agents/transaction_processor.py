"""Transaction Processor Agent using LangChain DeepAgents."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage

from content_marketplace.models.transaction import (
    Transaction,
    TransactionCreate,
    TransactionStatus,
    TransactionUpdate,
)

logger = logging.getLogger(__name__)

PLATFORM_FEE_RATE = 0.10  # 10% platform fee


class TransactionProcessorAgent:
    """Agent responsible for processing marketplace transactions.

    Uses LangChain DeepAgents to handle payment processing,
    fraud detection, and transaction lifecycle management.
    """

    def __init__(self, llm: Optional[BaseChatModel] = None) -> None:
        """Initialize the TransactionProcessorAgent.

        Args:
            llm: Optional LangChain chat model for AI-powered fraud detection.
        """
        self.llm = llm
        self._transactions: dict[UUID, Transaction] = {}

    def _compute_fees(self, amount: float) -> tuple[float, float]:
        """Compute platform fee and net amount.

        Args:
            amount: The transaction amount.

        Returns:
            Tuple of (platform_fee, net_amount).
        """
        fee = round(amount * PLATFORM_FEE_RATE, 2)
        net = round(amount - fee, 2)
        return fee, net

    async def create_transaction(self, data: TransactionCreate) -> Transaction:
        """Create a new transaction.

        Args:
            data: Transaction creation data.

        Returns:
            The newly created transaction.

        Raises:
            ValueError: If transaction data is invalid.
        """
        if data.amount <= 0:
            raise ValueError("Transaction amount must be positive")

        fee, net = self._compute_fees(data.amount)

        transaction = Transaction(
            listing_id=data.listing_id,
            buyer_id=data.buyer_id,
            seller_id=data.seller_id,
            amount=data.amount,
            currency=data.currency,
            payment_method=data.payment_method,
            status=TransactionStatus.PENDING,
            platform_fee=fee,
            net_amount=net,
            metadata=data.metadata,
        )
        self._transactions[transaction.id] = transaction
        logger.info("Created transaction %s for listing %s", transaction.id, data.listing_id)
        return transaction

    async def process_transaction(self, transaction_id: UUID) -> Transaction:
        """Process a pending transaction.

        Args:
            transaction_id: The transaction UUID to process.

        Returns:
            The processed transaction.

        Raises:
            KeyError: If transaction not found.
            ValueError: If transaction is not in PENDING status.
        """
        if transaction_id not in self._transactions:
            raise KeyError(f"Transaction {transaction_id} not found")

        transaction = self._transactions[transaction_id]

        if transaction.status != TransactionStatus.PENDING:
            raise ValueError(f"Transaction {transaction_id} is not pending")

        # AI-powered fraud check
        fraud_result = await self._check_fraud(transaction)
        if fraud_result.get("is_fraudulent", False):
            transaction.status = TransactionStatus.FAILED
            transaction.metadata["fraud_reasons"] = str(fraud_result.get("reasons", []))
            logger.warning("Transaction %s flagged as fraudulent", transaction_id)
            return transaction

        transaction.status = TransactionStatus.PROCESSING
        logger.info("Processing transaction %s", transaction_id)
        return transaction

    async def complete_transaction(self, transaction_id: UUID) -> Transaction:
        """Mark a transaction as completed.

        Args:
            transaction_id: The transaction UUID to complete.

        Returns:
            The completed transaction.

        Raises:
            KeyError: If transaction not found.
        """
        if transaction_id not in self._transactions:
            raise KeyError(f"Transaction {transaction_id} not found")

        transaction = self._transactions[transaction_id]
        transaction.status = TransactionStatus.COMPLETED
        transaction.completed_at = datetime.utcnow()
        transaction.updated_at = datetime.utcnow()
        logger.info("Completed transaction %s", transaction_id)
        return transaction

    async def refund_transaction(self, transaction_id: UUID, reason: str = "") -> Transaction:
        """Refund a transaction.

        Args:
            transaction_id: The transaction UUID to refund.
            reason: Reason for refund.

        Returns:
            The refunded transaction.

        Raises:
            KeyError: If transaction not found.
        """
        if transaction_id not in self._transactions:
            raise KeyError(f"Transaction {transaction_id} not found")

        transaction = self._transactions[transaction_id]
        transaction.status = TransactionStatus.REFUNDED
        transaction.updated_at = datetime.utcnow()
        transaction.metadata["refund_reason"] = reason
        logger.info("Refunded transaction %s: %s", transaction_id, reason)
        return transaction

    async def get_transaction(self, transaction_id: UUID) -> Transaction:
        """Retrieve a transaction by ID.

        Args:
            transaction_id: The transaction UUID.

        Returns:
            The transaction.

        Raises:
            KeyError: If transaction not found.
        """
        if transaction_id not in self._transactions:
            raise KeyError(f"Transaction {transaction_id} not found")
        return self._transactions[transaction_id]

    async def list_transactions(
        self,
        buyer_id: Optional[str] = None,
        seller_id: Optional[str] = None,
        status: Optional[TransactionStatus] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Transaction]:
        """List transactions with optional filters.

        Args:
            buyer_id: Filter by buyer.
            seller_id: Filter by seller.
            status: Filter by status.
            limit: Maximum results.
            offset: Pagination offset.

        Returns:
            Filtered list of transactions.
        """
        results = list(self._transactions.values())

        if buyer_id:
            results = [t for t in results if t.buyer_id == buyer_id]
        if seller_id:
            results = [t for t in results if t.seller_id == seller_id]
        if status:
            results = [t for t in results if t.status == status]

        return results[offset : offset + limit]

    async def _check_fraud(self, transaction: Transaction) -> dict[str, Any]:
        """Use AI to check for fraudulent transactions.

        Args:
            transaction: The transaction to check.

        Returns:
            Dictionary with is_fraudulent flag and reasons.
        """
        if self.llm is None:
            return {"is_fraudulent": False, "reasons": []}

        prompt = (
            f"Check this transaction for fraud indicators:\n"
            f"Amount: {transaction.amount} {transaction.currency}\n"
            f"Buyer: {transaction.buyer_id}\n"
            f"Seller: {transaction.seller_id}\n"
            f"Payment method: {transaction.payment_method}\n"
            f"Respond with JSON: {{\"is_fraudulent\": true/false, \"reasons\": [\"...\"]}}"
        )

        response = await self.llm.ainvoke([HumanMessage(content=prompt)])
        import json
        try:
            result = json.loads(response.content)
            return result
        except (json.JSONDecodeError, TypeError):
            return {"is_fraudulent": False, "reasons": []}

    async def get_transaction_stats(self) -> dict[str, Any]:
        """Get transaction statistics.

        Returns:
            Dictionary with transaction counts and volume.
        """
        total = len(self._transactions)
        completed = sum(1 for t in self._transactions.values() if t.status == TransactionStatus.COMPLETED)
        pending = sum(1 for t in self._transactions.values() if t.status == TransactionStatus.PENDING)
        failed = sum(1 for t in self._transactions.values() if t.status == TransactionStatus.FAILED)
        total_volume = sum(t.amount for t in self._transactions.values() if t.status == TransactionStatus.COMPLETED)

        return {
            "total": total,
            "completed": completed,
            "pending": pending,
            "failed": failed,
            "total_volume": total_volume,
        }
