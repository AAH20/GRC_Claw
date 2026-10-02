"""Tests for member verification models."""

from __future__ import annotations

from datetime import datetime

import pytest
from pydantic import ValidationError

from member_verification.models.schemas import (
    DocumentData,
    DocumentType,
    FraudCheckRequest,
    IdentityData,
    RiskLevel,
    TrustScoreRequest,
    VerificationRequest,
    VerificationStatus,
)


class TestIdentityData:
    """Tests for IdentityData model."""

    def test_valid_identity(self) -> None:
        """Test creating valid identity data."""
        identity = IdentityData(
            full_name="John Doe",
            date_of_birth="1990-01-15",
            email="john@example.com",
        )
        assert identity.full_name == "John Doe"
        assert identity.phone is None

    def test_invalid_dob_format(self) -> None:
        """Test invalid date of birth format."""
        with pytest.raises(ValidationError):
            IdentityData(
                full_name="John Doe",
                date_of_birth="01-15-1990",
                email="john@example.com",
            )

    def test_empty_name(self) -> None:
        """Test empty name validation."""
        with pytest.raises(ValidationError):
            IdentityData(
                full_name="",
                date_of_birth="1990-01-15",
                email="john@example.com",
            )


class TestDocumentData:
    """Tests for DocumentData model."""

    def test_valid_document(self) -> None:
        """Test creating valid document data."""
        doc = DocumentData(
            document_type=DocumentType.PASSPORT,
            document_number="P12345678",
            issuing_country="US",
        )
        assert doc.document_type == DocumentType.PASSPORT
        assert doc.expiry_date is None

    def test_invalid_country_code(self) -> None:
        """Test invalid country code."""
        with pytest.raises(ValidationError):
            DocumentData(
                document_type=DocumentType.PASSPORT,
                document_number="P123",
                issuing_country="USA",
            )


class TestVerificationRequest:
    """Tests for VerificationRequest model."""

    def test_valid_request(self) -> None:
        """Test creating valid verification request."""
        request = VerificationRequest(
            member_id="test-001",
            identity=IdentityData(
                full_name="John Doe",
                date_of_birth="1990-01-15",
                email="john@example.com",
            ),
        )
        assert request.member_id == "test-001"
        assert request.priority == "normal"
        assert len(request.documents) == 0

    def test_with_documents(self) -> None:
        """Test request with documents."""
        request = VerificationRequest(
            member_id="test-001",
            identity=IdentityData(
                full_name="John Doe",
                date_of_birth="1990-01-15",
                email="john@example.com",
            ),
            documents=[
                DocumentData(
                    document_type=DocumentType.PASSPORT,
                    document_number="P123",
                    issuing_country="US",
                )
            ],
        )
        assert len(request.documents) == 1


class TestTrustScoreRequest:
    """Tests for TrustScoreRequest model."""

    def test_valid_request(self) -> None:
        """Test creating valid trust score request."""
        request = TrustScoreRequest(member_id="test-001")
        assert request.member_id == "test-001"
        assert request.include_history is True


class TestFraudCheckRequest:
    """Tests for FraudCheckRequest model."""

    def test_valid_request(self) -> None:
        """Test creating valid fraud check request."""
        request = FraudCheckRequest(
            member_id="test-001",
            identity=IdentityData(
                full_name="John Doe",
                date_of_birth="1990-01-15",
                email="john@example.com",
            ),
        )
        assert request.check_depth == "standard"
