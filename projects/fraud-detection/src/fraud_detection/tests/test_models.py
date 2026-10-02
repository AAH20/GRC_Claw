"""Model validation tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from fraud_detection.models.schemas import (
    Anomaly,
    Pattern,
    RiskLevel,
    RiskScore,
    Transaction,
    TransactionType,
)


def test_transaction_valid() -> None:
    """Test valid transaction creation."""
    txn = Transaction(
        transaction_id="txn-001",
        account_id="acc-001",
        amount=100.0,
        transaction_type=TransactionType.DEBIT,
    )
    assert txn.transaction_id == "txn-001"
    assert txn.currency == "USD"


def test_transaction_invalid_amount() -> None:
    """Test transaction with invalid amount."""
    with pytest.raises(ValidationError):
        Transaction(
            transaction_id="txn-001",
            account_id="acc-001",
            amount=-10.0,
            transaction_type=TransactionType.DEBIT,
        )


def test_pattern_valid() -> None:
    """Test valid pattern creation."""
    pattern = Pattern(
        pattern_id="pat-001",
        pattern_type="card_testing",
        name="Card Testing",
        description="Small amount transactions",
        confidence=0.8,
        severity=RiskLevel.HIGH,
    )
    assert pattern.confidence == 0.8


def test_anomaly_valid() -> None:
    """Test valid anomaly creation."""
    anomaly = Anomaly(
        anomaly_id="anom-001",
        anomaly_type="amount_anomaly",
        name="Amount Anomaly",
        description="Unusually large amount",
        score=0.9,
        severity=RiskLevel.CRITICAL,
    )
    assert anomaly.score == 0.9


def test_risk_score_valid() -> None:
    """Test valid risk score creation."""
    score = RiskScore(
        score_id="score-001",
        transaction_id="txn-001",
        account_id="acc-001",
        overall_score=0.75,
        risk_level=RiskLevel.HIGH,
    )
    assert score.overall_score == 0.75
