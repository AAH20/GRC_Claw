"""Payment service for processing payments, payouts, and retrieving payment history."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


class PaymentError(Exception):
    """Base exception for payment-related errors."""

    def __init__(self, message: str, code: str = "PAYMENT_ERROR") -> None:
        super().__init__(message)
        self.message = message
        self.code = code


class InsufficientFundsError(PaymentError):
    """Raised when a user has insufficient funds for a transaction."""

    def __init__(self, message: str = "Insufficient funds") -> None:
        super().__init__(message, code="INSUFFICIENT_FUNDS")


class InvalidPaymentDataError(PaymentError):
    """Raised when payment data is invalid or incomplete."""

    def __init__(self, message: str = "Invalid payment data") -> None:
        super().__init__(message, code="INVALID_PAYMENT_DATA")


class PayoutError(PaymentError):
    """Raised when a payout cannot be processed."""

    def __init__(self, message: str = "Payout processing failed") -> None:
        super().__init__(message, code="PAYOUT_ERROR")


class PaymentNotFoundError(PaymentError):
    """Raised when a payment record cannot be found."""

    def __init__(self, message: str = "Payment not found") -> None:
        super().__init__(message, code="PAYMENT_NOT_FOUND")


# In-memory store for demonstration purposes.
# In production, replace with actual database calls.
_payments_store: Dict[str, Dict[str, Any]] = {}
_user_balances: Dict[str, float] = {}


def _validate_payment_data(data: Dict[str, Any]) -> None:
    """Validate payment data before processing.

    Args:
        data: Dictionary containing payment information.

    Raises:
        InvalidPaymentDataError: If required fields are missing or invalid.
    """
    required_fields = ["user_id", "amount", "currency", "payment_method"]
    missing_fields = [field for field in required_fields if field not in data]

    if missing_fields:
        raise InvalidPaymentDataError(
            f"Missing required fields: {', '.join(missing_fields)}"
        )

    if not isinstance(data["amount"], (int, float)) or data["amount"] <= 0:
        raise InvalidPaymentDataError("Amount must be a positive number")

    if not isinstance(data["user_id"], str) or not data["user_id"].strip():
        raise InvalidPaymentDataError("user_id must be a non-empty string")

    if not isinstance(data["currency"], str) or len(data["currency"]) != 3:
        raise InvalidPaymentDataError("currency must be a valid 3-letter ISO code")

    if not isinstance(data["payment_method"], str) or not data["payment_method"].strip():
        raise InvalidPaymentDataError("payment_method must be a non-empty string")


def process_payment(data: Dict[str, Any]) -> Dict[str, Any]:
    """Process a payment transaction.

    Args:
        data: Dictionary containing payment details:
            - user_id (str): The ID of the user making the payment.
            - amount (float): The payment amount.
            - currency (str): 3-letter ISO currency code (e.g., 'USD').
            - payment_method (str): Payment method identifier.
            - description (Optional[str]): Optional payment description.
            - metadata (Optional[Dict[str, Any]]): Optional additional metadata.

    Returns:
        Dict[str, Any]: Payment result containing:
            - payment_id (str): Unique payment identifier.
            - status (str): Payment status ('completed', 'pending', 'failed').
            - user_id (str): The user who made the payment.
            - amount (float): The payment amount.
            - currency (str): The currency code.
            - created_at (str): ISO 8601 timestamp of the transaction.

    Raises:
        InvalidPaymentDataError: If payment data is invalid or incomplete.
        PaymentError: If the payment processing fails.
    """
    try:
        _validate_payment_data(data)

        user_id: str = data["user_id"]
        amount: float = float(data["amount"])
        currency: str = data["currency"].upper()
        payment_method: str = data["payment_method"]
        description: Optional[str] = data.get("description")
        metadata: Optional[Dict[str, Any]] = data.get("metadata")

        payment_id: str = str(uuid4())
        created_at: str = datetime.now(timezone.utc).isoformat()

        # Simulate payment processing logic
        # In production, integrate with a payment gateway (Stripe, PayPal, etc.)
        payment_record: Dict[str, Any] = {
            "payment_id": payment_id,
            "user_id": user_id,
            "amount": amount,
            "currency": currency,
            "payment_method": payment_method,
            "status": "completed",
            "description": description,
            "metadata": metadata or {},
            "created_at": created_at,
        }

        # Store payment record
        _payments_store[payment_id] = payment_record

        # Update user balance
        _user_balances[user_id] = _user_balances.get(user_id, 0.0) + amount

        logger.info(
            "Payment processed successfully: payment_id=%s, user_id=%s, amount=%.2f %s",
            payment_id,
            user_id,
            amount,
            currency,
        )

        return payment_record

    except InvalidPaymentDataError:
        raise
    except Exception as exc:
        logger.error("Payment processing failed: %s", exc)
        raise PaymentError(f"Payment processing failed: {exc}") from exc


def initiate_payout(creator_id: str, amount: float) -> Dict[str, Any]:
    """Initiate a payout to a creator.

    Args:
        creator_id: The unique identifier of the creator receiving the payout.
        amount: The payout amount in the creator's currency.

    Returns:
        Dict[str, Any]: Payout result containing:
            - payout_id (str): Unique payout identifier.
            - creator_id (str): The creator receiving the payout.
            - amount (float): The payout amount.
            - status (str): Payout status ('initiated', 'processing', 'completed').
            - created_at (str): ISO 8601 timestamp of the payout initiation.

    Raises:
        InvalidPaymentDataError: If creator_id is empty or amount is not positive.
        InsufficientFundsError: If the creator has insufficient balance.
        PayoutError: If the payout cannot be initiated.
    """
    try:
        if not isinstance(creator_id, str) or not creator_id.strip():
            raise InvalidPaymentDataError("creator_id must be a non-empty string")

        if not isinstance(amount, (int, float)) or amount <= 0:
            raise InvalidPaymentDataError("amount must be a positive number")

        amount = float(amount)

        # Check creator's available balance
        available_balance: float = _user_balances.get(creator_id, 0.0)
        if available_balance < amount:
            raise InsufficientFundsError(
                f"Insufficient balance: available={available_balance:.2f}, requested={amount:.2f}"
            )

        payout_id: str = str(uuid4())
        created_at: str = datetime.now(timezone.utc).isoformat()

        # Deduct from balance
        _user_balances[creator_id] = available_balance - amount

        payout_record: Dict[str, Any] = {
            "payout_id": payout_id,
            "creator_id": creator_id,
            "amount": amount,
            "status": "initiated",
            "created_at": created_at,
        }

        # Store payout record
        _payments_store[payout_id] = payout_record

        logger.info(
            "Payout initiated: payout_id=%s, creator_id=%s, amount=%.2f",
            payout_id,
            creator_id,
            amount,
        )

        return payout_record

    except (InvalidPaymentDataError, InsufficientFundsError):
        raise
    except Exception as exc:
        logger.error("Payout initiation failed: %s", exc)
        raise PayoutError(f"Payout initiation failed: {exc}") from exc


def get_payment_history(user_id: str) -> List[Dict[str, Any]]:
    """Retrieve the payment history for a given user.

    Args:
        user_id: The unique identifier of the user.

    Returns:
        List[Dict[str, Any]]: A list of payment records for the user,
            sorted by creation date in descending order (most recent first).
            Each record contains payment_id, amount, currency, status,
            payment_method, and created_at fields.

    Raises:
        InvalidPaymentDataError: If user_id is empty or not a string.
    """
    try:
        if not isinstance(user_id, str) or not user_id.strip():
            raise InvalidPaymentDataError("user_id must be a non-empty string")

        user_payments: List[Dict[str, Any]] = [
            record
            for record in _payments_store.values()
            if record.get("user_id") == user_id or record.get("creator_id") == user_id
        ]

        # Sort by created_at descending (most recent first)
        user_payments.sort(key=lambda x: x.get("created_at", ""), reverse=True)

        logger.info(
            "Retrieved payment history for user_id=%s: %d records found",
            user_id,
            len(user_payments),
        )

        return user_payments

    except InvalidPaymentDataError:
        raise
    except Exception as exc:
        logger.error("Failed to retrieve payment history: %s", exc)
        raise PaymentError(f"Failed to retrieve payment history: {exc}") from exc
