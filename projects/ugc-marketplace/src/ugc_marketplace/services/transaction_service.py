"""Transaction service for UGC marketplace.

Handles creation, retrieval, and refund processing of marketplace transactions.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class TransactionError(Exception):
    """Base exception for transaction-related errors."""


class TransactionNotFoundError(TransactionError):
    """Raised when a transaction cannot be found."""


class TransactionValidationError(TransactionError):
    """Raised when transaction data fails validation."""


class TransactionStateError(TransactionError):
    """Raised when an operation is invalid for the current transaction state."""


class TransactionStatus(str, Enum):
    """Possible statuses for a transaction."""

    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"


class RefundReason(str, Enum):
    """Valid reasons for processing a refund."""

    BUYER_REMORSE = "buyer_remorse"
    SELLER_CANCELLED = "seller_cancelled"
    FRAUD = "fraud"
    DUPLICATE = "duplicate"
    OTHER = "other"


@dataclass
class Transaction:
    """Represents a marketplace transaction."""

    id: str
    buyer_id: str
    seller_id: str
    amount: float
    currency: str
    status: TransactionStatus
    created_at: datetime
    updated_at: datetime
    description: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    refunds: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def refunded_amount(self) -> float:
        """Total amount refunded so far."""
        return sum(r["amount"] for r in self.refunds)

    @property
    def remaining_amount(self) -> float:
        """Amount still eligible for refund."""
        return self.amount - self.refunded_amount

    def to_dict(self) -> Dict[str, Any]:
        """Serialize transaction to dictionary."""
        return {
            "id": self.id,
            "buyer_id": self.buyer_id,
            "seller_id": self.seller_id,
            "amount": self.amount,
            "currency": self.currency,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "description": self.description,
            "metadata": self.metadata,
            "refunds": self.refunds,
            "refunded_amount": self.refunded_amount,
            "remaining_amount": self.remaining_amount,
        }


# In-memory store — replace with database integration in production
_transactions: Dict[str, Transaction] = {}


def _validate_transaction_data(data: Dict[str, Any]) -> None:
    """Validate transaction creation data.

    Raises:
        TransactionValidationError: If required fields are missing or invalid.
    """
    required_fields = ["buyer_id", "seller_id", "amount", "currency"]
    missing = [f for f in required_fields if f not in data]
    if missing:
        raise TransactionValidationError(
            f"Missing required fields: {', '.join(missing)}"
        )

    if not isinstance(data["buyer_id"], str) or not data["buyer_id"].strip():
        raise TransactionValidationError("buyer_id must be a non-empty string")

    if not isinstance(data["seller_id"], str) or not data["seller_id"].strip():
        raise TransactionValidationError("seller_id must be a non-empty string")

    if data["buyer_id"] == data["seller_id"]:
        raise TransactionValidationError("buyer_id and seller_id must differ")

    if not isinstance(data["amount"], (int, float)) or data["amount"] <= 0:
        raise TransactionValidationError("amount must be a positive number")

    if not isinstance(data["currency"], str) or len(data["currency"]) != 3:
        raise TransactionValidationError("currency must be a 3-letter ISO code")


def create_transaction(data: Dict[str, Any]) -> Transaction:
    """Create a new transaction with validation.

    Args:
        data: Dictionary containing transaction fields:
            - buyer_id (str): ID of the buyer
            - seller_id (str): ID of the seller
            - amount (float): Transaction amount
            - currency (str): 3-letter ISO currency code
            - description (str, optional): Transaction description
            - metadata (dict, optional): Additional metadata

    Returns:
        The created Transaction object.

    Raises:
        TransactionValidationError: If data fails validation.
    """
    _validate_transaction_data(data)

    now = datetime.now(timezone.utc)
    transaction = Transaction(
        id=str(uuid.uuid4()),
        buyer_id=data["buyer_id"],
        seller_id=data["seller_id"],
        amount=float(data["amount"]),
        currency=data["currency"].upper(),
        status=TransactionStatus.PENDING,
        created_at=now,
        updated_at=now,
        description=data.get("description"),
        metadata=data.get("metadata", {}),
    )

    _transactions[transaction.id] = transaction
    return transaction


def get_transaction(transaction_id: str) -> Transaction:
    """Retrieve a transaction by its ID.

    Args:
        transaction_id: The unique transaction identifier.

    Returns:
        The matching Transaction object.

    Raises:
        TransactionNotFoundError: If no transaction exists with the given ID.
        TransactionValidationError: If transaction_id is empty or invalid.
    """
    if not transaction_id or not isinstance(transaction_id, str):
        raise TransactionValidationError("transaction_id must be a non-empty string")

    transaction = _transactions.get(transaction_id)
    if transaction is None:
        raise TransactionNotFoundError(
            f"Transaction not found: {transaction_id}"
        )
    return transaction


def process_refund(
    transaction_id: str,
    amount: Optional[float] = None,
    reason: RefundReason = RefundReason.OTHER,
) -> Transaction:
    """Process a refund for a transaction.

    If no amount is provided, refunds the full remaining eligible amount.

    Args:
        transaction_id: The transaction to refund.
        amount: Amount to refund. Defaults to full remaining amount.
        reason: Reason for the refund.

    Returns:
        The updated Transaction object.

    Raises:
        TransactionNotFoundError: If the transaction does not exist.
        TransactionStateError: If the transaction cannot be refunded.
        TransactionValidationError: If the refund amount is invalid.
    """
    transaction = get_transaction(transaction_id)

    if transaction.status == TransactionStatus.REFUNDED:
        raise TransactionStateError(
            f"Transaction {transaction_id} has already been fully refunded"
        )

    if transaction.status == TransactionStatus.FAILED:
        raise TransactionStateError(
            f"Cannot refund failed transaction {transaction_id}"
        )

    if transaction.status == TransactionStatus.PENDING:
        raise TransactionStateError(
            f"Cannot refund pending transaction {transaction_id} — "
            "complete or cancel it first"
        )

    refund_amount = amount if amount is not None else transaction.remaining_amount

    if refund_amount <= 0:
        raise TransactionValidationError("Refund amount must be positive")

    if refund_amount > transaction.remaining_amount:
        raise TransactionValidationError(
            f"Refund amount {refund_amount} exceeds remaining "
            f"eligible amount {transaction.remaining_amount}"
        )

    now = datetime.now(timezone.utc)
    transaction.refunds.append({
        "amount": refund_amount,
        "reason": reason.value,
        "processed_at": now.isoformat(),
    })
    transaction.updated_at = now

    if transaction.refunded_amount >= transaction.amount:
        transaction.status = TransactionStatus.REFUNDED
    else:
        transaction.status = TransactionStatus.PARTIALLY_REFUNDED

    return transaction


def list_transactions(
    buyer_id: Optional[str] = None,
    seller_id: Optional[str] = None,
    status: Optional[TransactionStatus] = None,
) -> List[Transaction]:
    """List transactions with optional filtering.

    Args:
        buyer_id: Filter by buyer.
        seller_id: Filter by seller.
        status: Filter by status.

    Returns:
        List of matching Transaction objects.
    """
    results = list(_transactions.values())

    if buyer_id is not None:
        results = [t for t in results if t.buyer_id == buyer_id]
    if seller_id is not None:
        results = [t for t in results if t.seller_id == seller_id]
    if status is not None:
        results = [t for t in results if t.status == status]

    return results


def cancel_transaction(transaction_id: str) -> Transaction:
    """Cancel a pending transaction.

    Args:
        transaction_id: The transaction to cancel.

    Returns:
        The updated Transaction object.

    Raises:
        TransactionNotFoundError: If the transaction does not exist.
        TransactionStateError: If the transaction is not in a cancellable state.
    """
    transaction = get_transaction(transaction_id)

    if transaction.status != TransactionStatus.PENDING:
        raise TransactionStateError(
            f"Cannot cancel transaction {transaction_id} "
            f"with status {transaction.status.value}"
        )

    transaction.status = TransactionStatus.FAILED
    transaction.updated_at = datetime.now(timezone.utc)
    return transaction


def complete_transaction(transaction_id: str) -> Transaction:
    """Mark a pending transaction as completed.

    Args:
        transaction_id: The transaction to complete.

    Returns:
        The updated Transaction object.

    Raises:
        TransactionNotFoundError: If the transaction does not exist.
        TransactionStateError: If the transaction is not pending.
    """
    transaction = get_transaction(transaction_id)

    if transaction.status != TransactionStatus.PENDING:
        raise TransactionStateError(
            f"Cannot complete transaction {transaction_id} "
            f"with status {transaction.status.value}"
        )

    transaction.status = TransactionStatus.COMPLETED
    transaction.updated_at = datetime.now(timezone.utc)
    return transaction
