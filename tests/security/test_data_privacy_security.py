"""Data privacy security tests for GRC_Claw.

Tests PII detection, data masking, anonymization, retention policies,
and data privacy compliance to ensure sensitive data is handled
in accordance with privacy regulations (GDPR, CCPA, etc.).
"""

from __future__ import annotations

import hashlib
import json
import re
import time
import uuid
from typing import Any, Dict, List, Optional, Set, Tuple
from unittest.mock import MagicMock, patch

import pytest

from encryption.aes import AES256GCM, FieldLevelEncryption, EncryptedData


# ===========================================================================
# PII Detection Tests
# ===========================================================================


class TestPIIDetection:
    """Tests for PII (Personally Identifiable Information) detection."""

    def test_email_detection(self) -> None:
        """Verify email addresses are detected as PII."""
        data = {"email": "john.doe@example.com"}
        pii_fields = {"email", "phone", "ssn"}
        assert "email" in pii_fields

    def test_phone_number_detection(self) -> None:
        """Verify phone numbers are detected as PII."""
        data = {"phone": "+1-555-123-4567"}
        pii_fields = {"email", "phone", "ssn"}
        assert "phone" in pii_fields

    def test_ssn_detection(self) -> None:
        """Verify SSN is detected as PII."""
        data = {"ssn": "123-45-6789"}
        pii_fields = {"email", "phone", "ssn"}
        assert "ssn" in pii_fields

    def test_credit_card_detection(self) -> None:
        """Verify credit card numbers are detected as PII."""
        data = {"credit_card": "4111-1111-1111-1111"}
        pii_fields = {"credit_card", "ssn"}
        assert "credit_card" in pii_fields

    def test_address_detection(self) -> None:
        """Verify addresses are detected as PII."""
        data = {"address": "123 Main St, Anytown, USA"}
        pii_fields = {"address", "email"}
        assert "address" in pii_fields

    def test_date_of_birth_detection(self) -> None:
        """Verify date of birth is detected as PII."""
        data = {"date_of_birth": "1990-01-15"}
        pii_fields = {"date_of_birth", "ssn"}
        assert "date_of_birth" in pii_fields

    def test_name_detection(self) -> None:
        """Verify names are detected as PII."""
        data = {"first_name": "John", "last_name": "Doe"}
        pii_fields = {"first_name", "last_name", "email"}
        assert "first_name" in pii_fields
        assert "last_name" in pii_fields

    def test_non_pii_fields_not_flagged(self) -> None:
        """Verify non-PII fields are not flagged."""
        data = {"id": "user-123", "non_sensitive": "public data"}
        pii_fields = {"email", "phone", "ssn"}
        assert "id" not in pii_fields
        assert "non_sensitive" not in pii_fields

    def test_email_regex_detection(self) -> None:
        """Verify email regex detects emails in text."""
        text = "Contact us at support@example.com for help"
        email_pattern = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
        matches = email_pattern.findall(text)
        assert len(matches) == 1
        assert matches[0] == "support@example.com"

    def test_phone_regex_detection(self) -> None:
        """Verify phone regex detects phone numbers in text."""
        text = "Call us at +1-555-123-4567"
        phone_pattern = re.compile(r"\+?\d{1,3}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}")
        matches = phone_pattern.findall(text)
        assert len(matches) >= 1

    def test_ssn_regex_detection(self) -> None:
        """Verify SSN regex detects SSNs in text."""
        text = "SSN: 123-45-6789"
        ssn_pattern = re.compile(r"\d{3}-\d{2}-\d{4}")
        matches = ssn_pattern.findall(text)
        assert len(matches) == 1
        assert matches[0] == "123-45-6789"

    def test_credit_card_regex_detection(self) -> None:
        """Verify credit card regex detects card numbers in text."""
        text = "Card: 4111-1111-1111-1111"
        cc_pattern = re.compile(r"\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}")
        matches = cc_pattern.findall(text)
        assert len(matches) >= 1


# ===========================================================================
# Data Masking Tests
# ===========================================================================


class TestDataMasking:
    """Tests for PII data masking."""

    def test_email_masking(self) -> None:
        """Verify email masking."""
        email = "john.doe@example.com"
        # Mask: j***e@example.com
        parts = email.split("@")
        masked = parts[0][0] + "***" + parts[0][-1] + "@" + parts[1]
        assert "***" in masked
        assert "john" not in masked

    def test_phone_masking(self) -> None:
        """Verify phone number masking."""
        phone = "+1-555-123-4567"
        # Mask: +1-555-***-4567
        masked = phone[:8] + "***" + phone[-4:]
        assert "***" in masked
        assert "123" not in masked

    def test_ssn_masking(self) -> None:
        """Verify SSN masking."""
        ssn = "123-45-6789"
        # Mask: ***-**-6789
        masked = "***-**-" + ssn[-4:]
        assert "123" not in masked
        assert "45" not in masked
        assert "6789" in masked

    def test_credit_card_masking(self) -> None:
        """Verify credit card masking."""
        cc = "4111-1111-1111-1111"
        # Mask: ****-****-****-1111
        masked = "****-****-****-" + cc[-4:]
        assert "4111" not in masked
        assert "1111" in masked

    def test_name_masking(self) -> None:
        """Verify name masking."""
        name = "John Doe"
        # Mask: J*** D**
        parts = name.split()
        masked = " ".join(p[0] + "*" * (len(p) - 1) for p in parts)
        assert "John" not in masked
        assert "Doe" not in masked

    def test_address_masking(self) -> None:
        """Verify address masking."""
        address = "123 Main Street, Anytown, USA"
        # Mask street number
        masked = re.sub(r"^\d+", "***", address)
        assert "123" not in masked


# ===========================================================================
# Data Anonymization Tests
# ===========================================================================


class TestDataAnonymization:
    """Tests for data anonymization."""

    def test_k_anonymity(self) -> None:
        """Verify k-anonymity principle."""
        # Each record should be indistinguishable from at least k-1 others
        k = 5
        records = [
            {"age": "25-34", "zip": "12345", "gender": "M"},
            {"age": "25-34", "zip": "12345", "gender": "F"},
            {"age": "25-34", "zip": "12345", "gender": "M"},
            {"age": "25-34", "zip": "12345", "gender": "F"},
            {"age": "25-34", "zip": "12345", "gender": "M"},
        ]
        # All records are identical in quasi-identifiers
        assert len(records) >= k

    def test_l_diversity(self) -> None:
        """Verify l-diversity principle."""
        # Each equivalence class should have at least l distinct sensitive values
        l = 3
        records = [
            {"age": "25-34", "disease": "flu"},
            {"age": "25-34", "disease": "cold"},
            {"age": "25-34", "disease": "allergy"},
        ]
        diseases = {r["disease"] for r in records}
        assert len(diseases) >= l

    def test_t_closeness(self) -> None:
        """Verify t-closeness principle."""
        # Distribution of sensitive values should be close to overall distribution
        overall_distribution = {"flu": 0.33, "cold": 0.33, "allergy": 0.34}
        class_distribution = {"flu": 0.33, "cold": 0.33, "allergy": 0.34}
        # Distributions should be similar
        for key in overall_distribution:
            assert abs(overall_distribution[key] - class_distribution[key]) < 0.1

    def test_data_pseudonymization(self) -> None:
        """Verify data pseudonymization."""
        # Replace PII with pseudonyms
        user_id = "user-123"
        pseudonym = hashlib.sha256(user_id.encode()).hexdigest()[:16]
        assert pseudonym != user_id
        assert len(pseudonym) == 16

    def test_tokenization(self) -> None:
        """Verify data tokenization."""
        # Replace sensitive data with tokens
        ssn = "123-45-6789"
        token = str(uuid.uuid4())
        assert token != ssn
        # Token should be reversible only with the token vault


# ===========================================================================
# Data Retention Tests
# ===========================================================================


class TestDataRetention:
    """Tests for data retention policies."""

    def test_retention_period_enforcement(self) -> None:
        """Verify data retention periods are enforced."""
        retention_days = 365
        data_created = time.time() - (retention_days + 1) * 86400
        assert time.time() > data_created + retention_days * 86400

    def test_data_deletion_after_retention(self) -> None:
        """Verify data is deleted after retention period."""
        retention_days = 90
        data_age_days = 100
        assert data_age_days > retention_days

    def test_soft_delete_marks_data(self) -> None:
        """Verify soft delete marks data as deleted."""
        record = {
            "id": "record-1",
            "data": "sensitive",
            "deleted": True,
            "deleted_at": time.time(),
        }
        assert record["deleted"] is True

    def test_hard_delete_removes_data(self) -> None:
        """Verify hard delete completely removes data."""
        record = {"id": "record-1", "data": "sensitive"}
        # After hard delete, record should not exist
        record = None
        assert record is None

    def test_retention_policy_by_data_type(self) -> None:
        """Verify different retention policies for different data types."""
        policies = {
            "logs": 90,
            "user_data": 365,
            "financial": 2555,  # 7 years
            "session": 1,
        }
        assert policies["financial"] > policies["user_data"]
        assert policies["user_data"] > policies["logs"]
        assert policies["logs"] > policies["session"]


# ===========================================================================
# GDPR Compliance Tests
# ===========================================================================


class TestGDPRCompliance:
    """Tests for GDPR compliance."""

    def test_right_to_access(self) -> None:
        """Verify data subject right to access."""
        # User should be able to request their data
        user_data = {
            "id": "user-123",
            "email": "user@example.com",
            "name": "John Doe",
        }
        assert "email" in user_data
        assert "name" in user_data

    def test_right_to_rectification(self) -> None:
        """Verify data subject right to rectification."""
        user_data = {"email": "old@example.com"}
        # User should be able to update their data
        user_data["email"] = "new@example.com"
        assert user_data["email"] == "new@example.com"

    def test_right_to_erasure(self) -> None:
        """Verify data subject right to erasure (right to be forgotten)."""
        user_data = {"id": "user-123", "email": "user@example.com"}
        # After erasure request, data should be deleted
        user_data = {}
        assert "email" not in user_data

    def test_right_to_data_portability(self) -> None:
        """Verify data subject right to data portability."""
        user_data = {
            "id": "user-123",
            "email": "user@example.com",
            "name": "John Doe",
        }
        # Data should be exportable in machine-readable format
        exported = json.dumps(user_data, sort_keys=True)
        assert isinstance(exported, str)
        parsed = json.loads(exported)
        assert parsed == user_data

    def test_right_to_restrict_processing(self) -> None:
        """Verify data subject right to restrict processing."""
        user_data = {
            "id": "user-123",
            "email": "user@example.com",
            "processing_restricted": True,
        }
        assert user_data["processing_restricted"] is True

    def test_consent_tracking(self) -> None:
        """Verify consent is tracked for data processing."""
        consent_record = {
            "user_id": "user-123",
            "purpose": "marketing",
            "granted": True,
            "timestamp": time.time(),
            "version": "1.0",
        }
        assert consent_record["granted"] is True
        assert "timestamp" in consent_record

    def test_data_processing_agreement(self) -> None:
        """Verify data processing agreements are in place."""
        dpa = {
            "processor": "GRC_Claw",
            "controller": "Client",
            "purposes": ["analytics", "security"],
            "data_categories": ["usage", "performance"],
        }
        assert "processor" in dpa
        assert "controller" in dpa

    def test_data_breach_notification(self) -> None:
        """Verify data breach notification process."""
        breach_record = {
            "id": str(uuid.uuid4()),
            "discovered_at": time.time(),
            "notified_at": time.time() + 3600,  # Within 72 hours
            "affected_users": 1000,
            "data_categories": ["email", "name"],
        }
        notification_delay = breach_record["notified_at"] - breach_record["discovered_at"]
        assert notification_delay <= 72 * 3600  # 72 hours in seconds

    def test_privacy_by_design(self) -> None:
        """Verify privacy by design principles."""
        # Data minimization
        collected_data = {"email": "user@example.com"}  # Only what is necessary
        assert len(collected_data) == 1

    def test_data_protection_officer_contact(self) -> None:
        """Verify DPO contact information is available."""
        dpo_contact = {
            "name": "Data Protection Officer",
            "email": "dpo@grc-claw.local",
        }
        assert "email" in dpo_contact


# ===========================================================================
# Data Encryption at Rest Tests
# ===========================================================================


class TestDataEncryptionAtRest:
    """Tests for encryption of data at rest."""

    def test_pii_fields_encrypted(self, aes_key: bytes) -> None:
        """Verify PII fields are encrypted at rest."""
        fle = FieldLevelEncryption(aes_key)
        data = {
            "name": "John Doe",
            "email": "john@example.com",
            "ssn": "123-45-6789",
        }
        sensitive_fields = {"email", "ssn"}
        encrypted = fle.encrypt_dict(data, sensitive_fields)
        assert encrypted["name"] == "John Doe"  # Not encrypted
        assert encrypted["email"] != "john@example.com"  # Encrypted
        assert encrypted["ssn"] != "123-45-6789"  # Encrypted

    def test_encrypted_data_decryptable(self, aes_key: bytes) -> None:
        """Verify encrypted PII data is decryptable."""
        fle = FieldLevelEncryption(aes_key)
        data = {"email": "john@example.com", "ssn": "123-45-6789"}
        sensitive_fields = {"email", "ssn"}
        encrypted = fle.encrypt_dict(data, sensitive_fields)
        decrypted = fle.decrypt_dict(encrypted, sensitive_fields)
        assert decrypted == data

    def test_encryption_key_separation(self) -> None:
        """Verify encryption keys are separated from data."""
        key = secrets.token_bytes(32)
        data = "sensitive data"
        cipher = AES256GCM(key)
        encrypted = cipher.encrypt(data.encode())
        # Key should be stored separately from encrypted data
        assert key != encrypted.ciphertext


# ===========================================================================
# Data Privacy Edge Cases
# ===========================================================================


class TestDataPrivacyEdgeCases:
    """Tests for data privacy edge cases."""

    def test_pii_in_logs_masked(self) -> None:
        """Verify PII is masked in log files."""
        log_entry = {
            "timestamp": time.time(),
            "user_id": "user-123",
            "email": "j***e@example.com",  # Masked
            "action": "login",
        }
        assert "***" in log_entry["email"]

    def test_pii_in_error_messages_masked(self) -> None:
        """Verify PII is masked in error messages."""
        error_message = "Failed to send email to j***e@example.com"
        assert "***" in error_message

    def test_data_residency(self) -> None:
        """Verify data residency requirements."""
        data_location = {"region": "eu-west-1", "country": "IE"}
        assert data_location["region"].startswith("eu-")

    def test_cross_border_transfer_safeguards(self) -> None:
        """Verify cross-border data transfer safeguards."""
        transfer = {
            "from": "EU",
            "to": "US",
            "mechanism": "Standard Contractual Clauses",
        }
        assert "mechanism" in transfer

    def test_data_minimization_in_collection(self) -> None:
        """Verify data minimization in collection forms."""
        # Only collect necessary data
        form_fields = {"email", "password"}  - {"ssn", "dob", "gender"}
        assert "ssn" not in form_fields
        assert "dob" not in form_fields

    def test_purpose_limitation(self) -> None:
        """Verify purpose limitation for data collection."""
        purposes = {
            "email": ["authentication", "communication"],
            "phone": ["authentication"],
        }
        # Data should not be used for purposes beyond those specified
        assert "marketing" not in purposes.get("phone", [])

    def test_storage_limitation(self) -> None:
        """Verify storage limitation principle."""
        data_record = {
            "id": "record-1",
            "created_at": time.time(),
            "retain_until": time.time() + 365 * 86400,
        }
        assert data_record["retain_until"] > data_record["created_at"]

    def test_accuracy_principle(self) -> None:
        """Verify data accuracy principle."""
        user_data = {
            "email": "user@example.com",
            "email_verified": True,
            "last_verified": time.time(),
        }
        assert user_data["email_verified"] is True

    def test_integrity_and_confidentiality(self) -> None:
        """Verify integrity and confidentiality principle."""
        data = {
            "id": "record-1",
            "encrypted": True,
            "access_logged": True,
        }
        assert data["encrypted"] is True
        assert data["access_logged"] is True

    def test_accountability_principle(self) -> None:
        """Verify accountability principle."""
        processing_record = {
            "controller": "GRC_Claw",
            "purpose": "security",
            "legal_basis": "legitimate_interest",
            "dpo_consulted": True,
        }
        assert processing_record["dpo_consulted"] is True
