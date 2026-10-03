"""Unit tests for fraud detection, investigation, and scoring."""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def fraud_detector():
    """Return a fresh FraudDetector instance."""
    from ugc_marketplace.fraud import FraudDetector
    return FraudDetector()


@pytest.fixture
def sample_transaction():
    """Return a normal-looking transaction dict."""
    return {
        "id": "txn_001",
        "user_id": "user_42",
        "amount": 29.99,
        "currency": "USD",
        "timestamp": datetime(2026, 10, 3, 12, 0, 0),
        "ip_address": "192.168.1.10",
        "device_id": "device_abc",
        "payment_method": "card_visa_4242",
    }


@pytest.fixture
def suspicious_transaction():
    """Return a transaction that should trigger fraud signals."""
    return {
        "id": "txn_002",
        "user_id": "user_99",
        "amount": 9999.99,
        "currency": "USD",
        "timestamp": datetime(2026, 10, 3, 3, 15, 0),
        "ip_address": "10.0.0.99",
        "device_id": "device_xyz",
        "payment_method": "card_unknown",
    }


@pytest.fixture
def mock_fraud_service():
    """Return a mocked external fraud service."""
    service = MagicMock()
    service.check.return_value = {"risk_level": "low", "score": 10}
    return service


# ---------------------------------------------------------------------------
# Tests — detect_fraud
# ---------------------------------------------------------------------------

class TestDetectFraud:
    """Tests for fraud detection logic."""

    def test_detect_fraud_returns_dict(self, fraud_detector, sample_transaction):
        """detect_fraud should return a dict with expected keys."""
        result = fraud_detector.detect(sample_transaction)
        assert isinstance(result, dict)
        assert "is_fraud" in result
        assert "risk_score" in result
        assert "reasons" in result

    def test_detect_fraud_flags_normal_transaction_as_safe(
        self, fraud_detector, sample_transaction
    ):
        """A normal transaction should not be flagged as fraud."""
        result = fraud_detector.detect(sample_transaction)
        assert result["is_fraud"] is False
        assert result["risk_score"] < 50

    def test_detect_fraud_flags_suspicious_transaction(
        self, fraud_detector, suspicious_transaction
    ):
        """A suspicious transaction should be flagged as fraud."""
        result = fraud_detector.detect(suspicious_transaction)
        assert result["is_fraud"] is True
        assert result["risk_score"] >= 50
        assert len(result["reasons"]) > 0

    def test_detect_fraud_handles_missing_fields(self, fraud_detector):
        """detect_fraud should handle transactions with missing fields."""
        incomplete = {"id": "txn_003", "user_id": "user_1"}
        result = fraud_detector.detect(incomplete)
        assert isinstance(result, dict)
        assert "is_fraud" in result

    def test_detect_fraud_empty_transaction(self, fraud_detector):
        """detect_fraud should handle an empty transaction dict."""
        result = fraud_detector.detect({})
        assert isinstance(result, dict)
        assert "is_fraud" in result

    def test_detect_fraud_uses_external_service(
        self, fraud_detector, sample_transaction, mock_fraud_service
    ):
        """detect_fraud should integrate with external fraud service."""
        fraud_detector.external_service = mock_fraud_service
        fraud_detector.detect(sample_transaction)
        mock_fraud_service.check.assert_called_once()

    def test_detect_fraud_high_amount_triggers_flag(self, fraud_detector):
        """Transactions with very high amounts should be flagged."""
        high_amount_txn = {
            "id": "txn_004",
            "user_id": "user_7",
            "amount": 50000.00,
            "currency": "USD",
            "timestamp": datetime.now(),
            "ip_address": "1.2.3.4",
            "device_id": "dev_1",
            "payment_method": "card_visa",
        }
        result = fraud_detector.detect(high_amount_txn)
        assert result["is_fraud"] is True
        assert "high_amount" in result["reasons"]


# ---------------------------------------------------------------------------
# Tests — investigate_fraud
# ---------------------------------------------------------------------------

class TestInvestigateFraud:
    """Tests for fraud investigation workflow."""

    def test_investigate_fraud_returns_report(self, fraud_detector, suspicious_transaction):
        """investigate_fraud should return an investigation report."""
        report = fraud_detector.investigate(suspicious_transaction)
        assert isinstance(report, dict)
        assert "transaction_id" in report
        assert "verdict" in report
        assert "evidence" in report
        assert "recommended_action" in report

    def test_investigate_fraud_confirms_fraud(self, fraud_detector, suspicious_transaction):
        """Investigation of a suspicious transaction should confirm fraud."""
        report = fraud_detector.investigate(suspicious_transaction)
        assert report["verdict"] == "confirmed_fraud"
        assert report["recommended_action"] == "block_and_review"

    def test_investigate_fraud_clears_legitimate(
        self, fraud_detector, sample_transaction
    ):
        """Investigation of a legitimate transaction should clear it."""
        report = fraud_detector.investigate(sample_transaction)
        assert report["verdict"] == "cleared"
        assert report["recommended_action"] == "allow"

    def test_investigate_fraud_collects_evidence(
        self, fraud_detector, suspicious_transaction
    ):
        """Investigation should collect multiple pieces of evidence."""
        report = fraud_detector.investigate(suspicious_transaction)
        assert len(report["evidence"]) >= 2

    def test_investigate_fraud_includes_timestamp(self, fraud_detector, sample_transaction):
        """Investigation report should include an investigation timestamp."""
        report = fraud_detector.investigate(sample_transaction)
        assert "investigated_at" in report
        assert isinstance(report["investigated_at"], datetime)

    def test_investigate_fraud_handles_unknown_transaction(self, fraud_detector):
        """Investigation should handle transactions not in the system."""
        unknown = {"id": "txn_unknown", "user_id": "user_0"}
        report = fraud_detector.investigate(unknown)
        assert report["verdict"] == "insufficient_data"
        assert report["recommended_action"] == "manual_review"

    @patch("ugc_marketplace.fraud.FraudDetector._query_user_history")
    def test_investigate_fraud_uses_user_history(
        self, mock_history, fraud_detector, suspicious_transaction
    ):
        """Investigation should query user history as part of evidence."""
        mock_history.return_value = {"previous_frauds": 2, "account_age_days": 5}
        report = fraud_detector.investigate(suspicious_transaction)
        mock_history.assert_called_once_with(suspicious_transaction["user_id"])
        assert report["verdict"] == "confirmed_fraud"


# ---------------------------------------------------------------------------
# Tests — fraud_score
# ---------------------------------------------------------------------------

class TestFraudScore:
    """Tests for fraud scoring algorithm."""

    def test_fraud_score_returns_numeric(self, fraud_detector, sample_transaction):
        """fraud_score should return a numeric value."""
        score = fraud_detector.score(sample_transaction)
        assert isinstance(score, (int, float))
        assert 0 <= score <= 100

    def test_fraud_score_normal_transaction_low(self, fraud_detector, sample_transaction):
        """Normal transactions should receive a low fraud score."""
        score = fraud_detector.score(sample_transaction)
        assert score < 30

    def test_fraud_score_suspicious_transaction_high(
        self, fraud_detector, suspicious_transaction
    ):
        """Suspicious transactions should receive a high fraud score."""
        score = fraud_detector.score(suspicious_transaction)
        assert score >= 70

    def test_fraud_score_monotonic_with_amount(self, fraud_detector):
        """Higher amounts should not decrease the fraud score."""
        low_txn = {
            "id": "txn_low",
            "user_id": "user_1",
            "amount": 10.00,
            "currency": "USD",
            "timestamp": datetime.now(),
            "ip_address": "1.1.1.1",
            "device_id": "dev_1",
            "payment_method": "card_visa",
        }
        high_txn = {**low_txn, "id": "txn_high", "amount": 10000.00}
        low_score = fraud_detector.score(low_txn)
        high_score = fraud_detector.score(high_txn)
        assert high_score >= low_score

    def test_fraud_score_consistency(self, fraud_detector, sample_transaction):
        """Same transaction should produce the same score on repeated calls."""
        score1 = fraud_detector.score(sample_transaction)
        score2 = fraud_detector.score(sample_transaction)
        assert score1 == score2

    def test_fraud_score_boundary_zero(self, fraud_detector):
        """A perfectly clean transaction should score near zero."""
        clean_txn = {
            "id": "txn_clean",
            "user_id": "user_trusted",
            "amount": 5.00,
            "currency": "USD",
            "timestamp": datetime.now(),
            "ip_address": "192.168.1.1",
            "device_id": "device_trusted",
            "payment_method": "card_visa_4242",
        }
        score = fraud_detector.score(clean_txn)
        assert score <= 10

    def test_fraud_score_boundary_max(self, fraud_detector):
        """A maximally suspicious transaction should score near 100."""
        dirty_txn = {
            "id": "txn_dirty",
            "user_id": "user_flagged",
            "amount": 999999.99,
            "currency": "USD",
            "timestamp": datetime.now() - timedelta(minutes=1),
            "ip_address": "0.0.0.0",
            "device_id": "device_blacklisted",
            "payment_method": "card_blacklisted",
        }
        score = fraud_detector.score(dirty_txn)
        assert score >= 90

    def test_fraud_score_uses_external_service(
        self, fraud_detector, sample_transaction, mock_fraud_service
    ):
        """fraud_score should incorporate external service signals."""
        fraud_detector.external_service = mock_fraud_service
        fraud_detector.score(sample_transaction)
        mock_fraud_service.check.assert_called_once()
