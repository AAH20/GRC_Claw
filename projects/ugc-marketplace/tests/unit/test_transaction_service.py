"""Unit tests for the TransactionService."""

import pytest
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock, patch

from ugc_marketplace.services.transaction_service import TransactionService
from ugc_marketplace.models.transaction import Transaction, TransactionStatus, TransactionType


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_db():
    """Provide a mock database session."""
    db = MagicMock()
    db.add = MagicMock()
    db.commit = MagicMock()
    db.refresh = MagicMock()
    db.query = MagicMock()
    return db


@pytest.fixture
def mock_payment_gateway():
    """Provide a mock payment gateway."""
    gateway = MagicMock()
    gateway.charge = MagicMock(return_value={"id": "pay_123", "status": "succeeded"})
    gateway.refund = MagicMock(return_value={"id": "ref_456", "status": "succeeded"})
    return gateway


@pytest.fixture
def transaction_service(mock_db, mock_payment_gateway):
    """Provide a TransactionService instance with mocked dependencies."""
    return TransactionService(db=mock_db, payment_gateway=mock_payment_gateway)


@pytest.fixture
def sample_transaction_data():
    """Provide sample data for creating a transaction."""
    return {
        "buyer_id": "user-buyer-001",
        "seller_id": "user-seller-001",
        "item_id": "item-001",
        "amount": Decimal("49.99"),
        "currency": "USD",
        "transaction_type": TransactionType.PURCHASE,
    }


@pytest.fixture
def sample_transaction(mock_db, sample_transaction_data):
    """Provide a persisted Transaction instance."""
    txn = Transaction(
        id="txn-001",
        **sample_transaction_data,
        status=TransactionStatus.COMPLETED,
        created_at=datetime(2026, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
        updated_at=datetime(2026, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
    )
    # Simulate DB assigning an ID
    mock_db.refresh.side_effect = lambda obj: setattr(obj, "id", "txn-001")
    return txn


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestCreateTransaction:
    """Tests for TransactionService.create_transaction."""

    def test_create_transaction(self, transaction_service, mock_db, mock_payment_gateway, sample_transaction_data):
        """Test that a transaction is created, charged, and persisted correctly."""
        # Act
        result = transaction_service.create_transaction(**sample_transaction_data)

        # Assert — payment gateway was called with correct amount and currency
        mock_payment_gateway.charge.assert_called_once_with(
            amount=sample_transaction_data["amount"],
            currency=sample_transaction_data["currency"],
        )

        # Assert — transaction was added to the DB session and committed
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

        # Assert — returned object is a Transaction with expected fields
        assert isinstance(result, Transaction)
        assert result.id == "txn-001"
        assert result.buyer_id == sample_transaction_data["buyer_id"]
        assert result.seller_id == sample_transaction_data["seller_id"]
        assert result.item_id == sample_transaction_data["item_id"]
        assert result.amount == sample_transaction_data["amount"]
        assert result.currency == sample_transaction_data["currency"]
        assert result.status == TransactionStatus.COMPLETED
        assert result.transaction_type == TransactionType.PURCHASE

    def test_create_transaction_with_invalid_amount(self, transaction_service, mock_db, sample_transaction_data):
        """Test that creating a transaction with a non-positive amount raises ValueError."""
        sample_transaction_data["amount"] = Decimal("0.00")

        with pytest.raises(ValueError, match="Amount must be positive"):
            transaction_service.create_transaction(**sample_transaction_data)

        mock_db.add.assert_not_called()
        mock_db.commit.assert_not_called()

    def test_create_transaction_payment_failure(self, transaction_service, mock_db, mock_payment_gateway, sample_transaction_data):
        """Test that a payment failure results in a FAILED transaction, not an exception."""
        mock_payment_gateway.charge.side_effect = Exception("Card declined")

        result = transaction_service.create_transaction(**sample_transaction_data)

        assert result.status == TransactionStatus.FAILED
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()


class TestGetTransaction:
    """Tests for TransactionService.get_transaction."""

    def test_get_transaction(self, transaction_service, mock_db, sample_transaction):
        """Test that an existing transaction is retrieved by ID."""
        # Arrange — mock the DB query chain
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = sample_transaction
        mock_db.query.return_value = mock_query

        # Act
        result = transaction_service.get_transaction("txn-001")

        # Assert
        mock_db.query.assert_called_once_with(Transaction)
        assert result is not None
        assert result.id == "txn-001"
        assert result.buyer_id == "user-buyer-001"
        assert result.seller_id == "user-seller-001"
        assert result.amount == Decimal("49.99")
        assert result.status == TransactionStatus.COMPLETED

    def test_get_transaction_not_found(self, transaction_service, mock_db):
        """Test that retrieving a non-existent transaction returns None."""
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query

        result = transaction_service.get_transaction("nonexistent-id")

        assert result is None

    def test_get_transaction_invalid_id(self, transaction_service, mock_db):
        """Test that an empty or None ID returns None without hitting the DB."""
        result = transaction_service.get_transaction("")
        assert result is None
        mock_db.query.assert_not_called()

        result = transaction_service.get_transaction(None)
        assert result is None
        mock_db.query.assert_not_called()


class TestProcessRefund:
    """Tests for TransactionService.process_refund."""

    def test_process_refund(self, transaction_service, mock_db, mock_payment_gateway, sample_transaction):
        """Test that a refund is processed for a completed transaction."""
        # Arrange
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = sample_transaction
        mock_db.query.return_value = mock_query

        # Act
        result = transaction_service.process_refund("txn-001")

        # Assert — payment gateway refund was called
        mock_payment_gateway.refund.assert_called_once_with(
            payment_id="pay_123",
            amount=sample_transaction.amount,
        )

        # Assert — transaction status updated and persisted
        assert result.status == TransactionStatus.REFUNDED
        mock_db.commit.assert_called_once()

    def test_process_refund_transaction_not_found(self, transaction_service, mock_db):
        """Test that refunding a non-existent transaction raises an error."""
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query

        with pytest.raises(ValueError, match="Transaction not found"):
            transaction_service.process_refund("nonexistent-id")

        mock_db.commit.assert_not_called()

    def test_process_refund_already_refunded(self, transaction_service, mock_db, sample_transaction):
        """Test that refunding an already-refunded transaction raises an error."""
        sample_transaction.status = TransactionStatus.REFUNDED

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = sample_transaction
        mock_db.query.return_value = mock_query

        with pytest.raises(ValueError, match="Transaction already refunded"):
            transaction_service.process_refund("txn-001")

        mock_db.commit.assert_not_called()

    def test_process_refund_payment_failure(self, transaction_service, mock_db, mock_payment_gateway, sample_transaction):
        """Test that a payment gateway failure during refund marks the transaction as FAILED."""
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = sample_transaction
        mock_db.query.return_value = mock_query
        mock_payment_gateway.refund.side_effect = Exception("Gateway timeout")

        result = transaction_service.process_refund("txn-001")

        assert result.status == TransactionStatus.FAILED
        mock_db.commit.assert_called_once()
