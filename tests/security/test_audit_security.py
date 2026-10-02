"""Audit security tests for GRC_Claw.

Tests audit event creation, schema validation, tamper-evident hash chains,
and event integrity verification to ensure comprehensive audit trail
security across the platform.
"""

from __future__ import annotations

import hashlib
import json
import time
import uuid
from dataclasses import asdict
from typing import Any, Dict, List, Optional, Tuple
from unittest.mock import MagicMock, patch

import pytest

from audit.events import (
    Action,
    Actor,
    AuditEvent,
    AuditEventBuilder,
    AuditEventSchema,
    AuditEventType,
    AuditOutcome,
    AuditSeverity,
    Context,
    Resource,
)
from audit.hashchain import (
    ChainEntry,
    ChainIntegrityError,
    ChainVerificationError,
    HashChain,
    HashChainError,
    HashChainManager,
)


# ===========================================================================
# Audit Event Creation Tests
# ===========================================================================


class TestAuditEventCreation:
    """Tests for audit event creation and structure."""

    def test_create_minimal_event(self) -> None:
        """Verify creation of a minimal audit event."""
        event = AuditEvent()
        assert event.id is not None
        assert event.timestamp is not None
        assert event.type == AuditEventType.SYSTEM_EVENT
        assert event.severity == AuditSeverity.INFO
        assert event.outcome == AuditOutcome.SUCCESS
        assert event.event_hash is not None

    def test_create_event_with_all_fields(self) -> None:
        """Verify creation of a fully-specified audit event."""
        event = AuditEvent(
            type=AuditEventType.AUTHENTICATION,
            severity=AuditSeverity.WARNING,
            outcome=AuditOutcome.FAILURE,
            actor=Actor(
                id="user-123",
                type="user",
                name="Test User",
                ip_address="192.168.1.100",
                user_agent="TestAgent/1.0",
                session_id="sess-456",
            ),
            resource=Resource(
                id="res-789",
                type="api_endpoint",
                name="/api/v1/data",
                uri="https://api.test.local/v1/data",
            ),
            action=Action(
                name="login",
                type="authentication",
                parameters={"method": "password"},
                result="failure",
            ),
            context=Context(
                request_id=str(uuid.uuid4()),
                trace_id="trace-123",
                environment="testing",
                service="test-service",
                version="1.0.0",
            ),
            message="Authentication failed",
            details={"reason": "invalid_credentials", "attempt": 3},
            tags=["auth", "failure"],
            compliance=["SOC2", "ISO27001"],
        )
        assert event.type == AuditEventType.AUTHENTICATION
        assert event.severity == AuditSeverity.WARNING
        assert event.outcome == AuditOutcome.FAILURE
        assert event.actor is not None
        assert event.actor.id == "user-123"
        assert event.resource is not None
        assert event.resource.id == "res-789"
        assert event.action is not None
        assert event.action.name == "login"
        assert event.message == "Authentication failed"
        assert event.details["reason"] == "invalid_credentials"
        assert "SOC2" in event.compliance

    def test_event_hash_is_deterministic(self) -> None:
        """Verify that event hash is deterministic for same data."""
        event1 = AuditEvent(
            id="test-id",
            timestamp=1000.0,
            type=AuditEventType.SYSTEM_EVENT,
            message="Test",
        )
        event2 = AuditEvent(
            id="test-id",
            timestamp=1000.0,
            type=AuditEventType.SYSTEM_EVENT,
            message="Test",
        )
        assert event1.event_hash == event2.event_hash

    def test_event_hash_changes_with_different_data(self) -> None:
        """Verify that event hash changes when data changes."""
        event1 = AuditEvent(message="Message A")
        event2 = AuditEvent(message="Message B")
        assert event1.event_hash != event2.event_hash

    def test_event_to_dict_contains_all_fields(self) -> None:
        """Verify that to_dict includes all required fields."""
        event = AuditEvent()
        data = event.to_dict()
        required_fields = {
            "id", "timestamp", "type", "severity", "outcome",
            "actor", "resource", "action", "context",
            "message", "details", "tags", "compliance",
            "previous_hash", "event_hash",
        }
        assert required_fields.issubset(set(data.keys()))

    def test_event_to_json_is_valid_json(self) -> None:
        """Verify that to_json produces valid JSON."""
        event = AuditEvent(
            type=AuditEventType.AUTHENTICATION,
            message="Test event",
        )
        json_str = event.to_json()
        parsed = json.loads(json_str)
        assert parsed["type"] == "authentication"
        assert parsed["message"] == "Test event"

    def test_event_from_dict_roundtrip(self) -> None:
        """Verify that from_dict(to_dict()) preserves all data."""
        original = AuditEvent(
            type=AuditEventType.AUTHENTICATION,
            severity=AuditSeverity.WARNING,
            outcome=AuditOutcome.FAILURE,
            actor=Actor(id="user-1", type="user"),
            resource=Resource(id="res-1", type="file"),
            action=Action(name="read", type="access"),
            message="Test message",
            details={"key": "value"},
            tags=["test"],
        )
        data = original.to_dict()
        restored = AuditEvent.from_dict(data)
        assert restored.type == original.type
        assert restored.severity == original.severity
        assert restored.outcome == original.outcome
        assert restored.message == original.message
        assert restored.details == original.details
        assert restored.tags == original.tags

    def test_event_integrity_verification(self) -> None:
        """Verify that event integrity check passes for unmodified events."""
        event = AuditEvent(message="Test")
        assert event.verify_integrity() is True

    def test_event_integrity_fails_after_modification(self) -> None:
        """Verify that event integrity check fails after modification."""
        event = AuditEvent(message="Original")
        object.__setattr__(event, "message", "Modified")
        assert event.event_hash != event._compute_hash()


# ===========================================================================
# Audit Event Builder Tests
# ===========================================================================


class TestAuditEventBuilder:
    """Tests for the audit event builder pattern."""

    def test_builder_creates_event(self) -> None:
        """Verify that builder creates a valid event."""
        event = (
            AuditEventBuilder()
            .with_type(AuditEventType.AUTHENTICATION)
            .with_severity(AuditSeverity.INFO)
            .with_outcome(AuditOutcome.SUCCESS)
            .with_message("User logged in")
            .build()
        )
        assert event.type == AuditEventType.AUTHENTICATION
        assert event.severity == AuditSeverity.INFO
        assert event.outcome == AuditOutcome.SUCCESS
        assert event.message == "User logged in"

    def test_builder_with_actor(self) -> None:
        """Verify builder with actor."""
        actor = Actor(id="user-1", type="user", name="Test User")
        event = AuditEventBuilder().with_actor(actor).with_message("Test").build()
        assert event.actor is not None
        assert event.actor.id == "user-1"

    def test_builder_with_resource(self) -> None:
        """Verify builder with resource."""
        resource = Resource(id="res-1", type="file", name="test.txt")
        event = AuditEventBuilder().with_resource(resource).with_message("Test").build()
        assert event.resource is not None
        assert event.resource.id == "res-1"

    def test_builder_with_action(self) -> None:
        """Verify builder with action."""
        action = Action(name="read", type="access", result="success")
        event = AuditEventBuilder().with_action(action).with_message("Test").build()
        assert event.action is not None
        assert event.action.name == "read"

    def test_builder_with_context(self) -> None:
        """Verify builder with context."""
        context = Context(environment="production", service="api")
        event = AuditEventBuilder().with_context(context).with_message("Test").build()
        assert event.context.environment == "production"
        assert event.context.service == "api"

    def test_builder_with_details(self) -> None:
        """Verify builder with details."""
        details = {"ip": "10.0.0.1", "user_agent": "TestAgent"}
        event = AuditEventBuilder().with_details(details).with_message("Test").build()
        assert event.details == details

    def test_builder_with_tags(self) -> None:
        """Verify builder with tags."""
        event = (
            AuditEventBuilder()
            .with_tags(["auth", "security"])
            .with_message("Test")
            .build()
        )
        assert event.tags == ["auth", "security"]

    def test_builder_with_compliance(self) -> None:
        """Verify builder with compliance frameworks."""
        event = (
            AuditEventBuilder()
            .with_compliance(["SOC2", "GDPR", "HIPAA"])
            .with_message("Test")
            .build()
        )
        assert event.compliance == ["SOC2", "GDPR", "HIPAA"]

    def test_builder_with_previous_hash(self) -> None:
        """Verify builder with previous hash for chain linking."""
        event = (
            AuditEventBuilder()
            .with_previous_hash("abc123hash")
            .with_message("Test")
            .build()
        )
        assert event.previous_hash == "abc123hash"

    def test_builder_chaining(self) -> None:
        """Verify that builder methods can be chained."""
        event = (
            AuditEventBuilder()
            .with_type(AuditEventType.SECURITY_ALERT)
            .with_severity(AuditSeverity.CRITICAL)
            .with_outcome(AuditOutcome.FAILURE)
            .with_actor(Actor(id="user-1", type="user"))
            .with_resource(Resource(id="res-1", type="file"))
            .with_action(Action(name="breach", type="security"))
            .with_message("Security breach detected")
            .with_details({"severity": "high"})
            .with_tags(["security", "breach"])
            .with_compliance(["SOC2"])
            .build()
        )
        assert event.type == AuditEventType.SECURITY_ALERT
        assert event.severity == AuditSeverity.CRITICAL
        assert event.outcome == AuditOutcome.FAILURE
        assert event.actor is not None
        assert event.resource is not None
        assert event.action is not None
        assert event.message == "Security breach detected"


# ===========================================================================
# Audit Event Schema Validation Tests
# ===========================================================================


class TestAuditEventSchemaValidation:
    """Tests for audit event schema validation."""

    def test_validate_valid_event(self) -> None:
        """Verify that valid events pass schema validation."""
        event = AuditEvent()
        assert AuditEventSchema.validate(event) is True

    def test_validate_valid_dict(self) -> None:
        """Verify that valid dict passes schema validation."""
        event = AuditEvent()
        data = event.to_dict()
        assert AuditEventSchema.validate(data) is True

    def test_validate_missing_required_fields(self) -> None:
        """Verify that missing required fields fail validation."""
        data = {"id": "test", "timestamp": 1000.0}
        with pytest.raises(ValueError, match="Missing required fields"):
            AuditEventSchema.validate(data)

    def test_validate_invalid_event_type(self) -> None:
        """Verify that invalid event type fails validation."""
        event = AuditEvent()
        data = event.to_dict()
        data["type"] = "invalid_type"
        with pytest.raises(ValueError, match="Invalid event type"):
            AuditEventSchema.validate(data)

    def test_validate_invalid_severity(self) -> None:
        """Verify that invalid severity fails validation."""
        event = AuditEvent()
        data = event.to_dict()
        data["severity"] = "invalid_severity"
        with pytest.raises(ValueError, match="Invalid severity"):
            AuditEventSchema.validate(data)

    def test_validate_invalid_outcome(self) -> None:
        """Verify that invalid outcome fails validation."""
        event = AuditEvent()
        data = event.to_dict()
        data["outcome"] = "invalid_outcome"
        with pytest.raises(ValueError, match="Invalid outcome"):
            AuditEventSchema.validate(data)

    def test_validate_non_numeric_timestamp(self) -> None:
        """Verify that non-numeric timestamp fails validation."""
        event = AuditEvent()
        data = event.to_dict()
        data["timestamp"] = "not-a-number"
        with pytest.raises(ValueError, match="Timestamp must be numeric"):
            AuditEventSchema.validate(data)

    def test_all_event_types_valid(self) -> None:
        """Verify that all event types are valid."""
        for event_type in AuditEventType:
            event = AuditEvent(type=event_type)
            assert AuditEventSchema.validate(event) is True

    def test_all_severities_valid(self) -> None:
        """Verify that all severities are valid."""
        for severity in AuditSeverity:
            event = AuditEvent(severity=severity)
            assert AuditEventSchema.validate(event) is True

    def test_all_outcomes_valid(self) -> None:
        """Verify that all outcomes are valid."""
        for outcome in AuditOutcome:
            event = AuditEvent(outcome=outcome)
            assert AuditEventSchema.validate(event) is True


# ===========================================================================
# Hash Chain Tests
# ===========================================================================


class TestHashChain:
    """Tests for tamper-evident hash chain."""

    def test_create_chain(self) -> None:
        """Verify chain creation."""
        chain = HashChain(chain_id="test-chain")
        assert chain.chain_id == "test-chain"
        assert len(chain) == 0

    def test_append_event(self) -> None:
        """Verify appending events to the chain."""
        chain = HashChain()
        event = AuditEvent(message="Test event")
        entry = chain.append(event)
        assert len(chain) == 1
        assert entry.sequence_number == 1
        assert entry.event == event

    def test_append_multiple_events(self) -> None:
        """Verify appending multiple events."""
        chain = HashChain()
        for i in range(5):
            chain.append(AuditEvent(message=f"Event {i}"))
        assert len(chain) == 5

    def test_sequence_numbers_increment(self) -> None:
        """Verify that sequence numbers increment correctly."""
        chain = HashChain()
        for i in range(5):
            entry = chain.append(AuditEvent(message=f"Event {i}"))
            assert entry.sequence_number == i + 1

    def test_chain_verification_empty(self) -> None:
        """Verify that empty chain passes verification."""
        chain = HashChain()
        valid, error = chain.verify()
        assert valid is True
        assert error is None

    def test_chain_verification_valid(self) -> None:
        """Verify that valid chain passes verification."""
        chain = HashChain()
        for i in range(5):
            chain.append(AuditEvent(message=f"Event {i}"))
        valid, error = chain.verify()
        assert valid is True
        assert error is None

    def test_chain_verification_detects_tampering(self) -> None:
        """Verify that chain verification detects tampering."""
        chain = HashChain()
        for i in range(5):
            chain.append(AuditEvent(message=f"Event {i}"))
        chain._entries[2].event.message = "Tampered"
        valid, error = chain.verify()
        assert valid is False
        assert error is not None

    def test_chain_verification_detects_sequence_mismatch(self) -> None:
        """Verify that chain verification detects sequence number mismatch."""
        chain = HashChain()
        for i in range(5):
            chain.append(AuditEvent(message=f"Event {i}"))
        chain._entries[2].sequence_number = 99
        valid, error = chain.verify()
        assert valid is False
        assert "Sequence mismatch" in error

    def test_chain_verification_detects_hash_linkage_break(self) -> None:
        """Verify that chain verification detects broken hash linkage."""
        chain = HashChain()
        for i in range(5):
            chain.append(AuditEvent(message=f"Event {i}"))
        chain._entries[2].previous_entry_hash = "broken_hash"
        valid, error = chain.verify()
        assert valid is False
        assert "Hash linkage broken" in error

    def test_chain_verification_detects_entry_hash_mismatch(self) -> None:
        """Verify that chain verification detects entry hash mismatch."""
        chain = HashChain()
        for i in range(5):
            chain.append(AuditEvent(message=f"Event {i}"))
        chain._entries[2].entry_hash = "tampered_hash"
        valid, error = chain.verify()
        assert valid is False
        assert "Entry hash mismatch" in error

    def test_chain_verification_detects_event_integrity_failure(self) -> None:
        """Verify that chain verification detects event integrity failure."""
        chain = HashChain()
        for i in range(5):
            chain.append(AuditEvent(message=f"Event {i}"))
        object.__setattr__(chain._entries[2].event, "message", "Tampered")
        valid, error = chain.verify()
        assert valid is False
        assert "Event integrity check failed" in error

    def test_verify_up_to_valid(self) -> None:
        """Verify chain up to a specific sequence number."""
        chain = HashChain()
        for i in range(10):
            chain.append(AuditEvent(message=f"Event {i}"))
        valid, error = chain.verify_up_to(5)
        assert valid is True
        assert error is None

    def test_verify_up_to_exceeds_length(self) -> None:
        """Verify that verify_up_to fails when exceeding chain length."""
        chain = HashChain()
        chain.append(AuditEvent(message="Event 0"))
        valid, error = chain.verify_up_to(10)
        assert valid is False
        assert "exceeds chain length" in error

    def test_get_entries(self) -> None:
        """Verify getting entries from the chain."""
        chain = HashChain()
        for i in range(5):
            chain.append(AuditEvent(message=f"Event {i}"))
        entries = chain.get_entries(1, 3)
        assert len(entries) == 2
        assert entries[0].sequence_number == 2
        assert entries[1].sequence_number == 3

    def test_get_entry_by_sequence(self) -> None:
        """Verify getting a specific entry by sequence number."""
        chain = HashChain()
        for i in range(5):
            chain.append(AuditEvent(message=f"Event {i}"))
        entry = chain.get_entry(3)
        assert entry is not None
        assert entry.sequence_number == 3

    def test_get_nonexistent_entry(self) -> None:
        """Verify that getting a non-existent entry returns None."""
        chain = HashChain()
        chain.append(AuditEvent(message="Event 0"))
        assert chain.get_entry(99) is None

    def test_get_last_hash(self) -> None:
        """Verify getting the last entry hash."""
        chain = HashChain()
        assert chain.get_last_hash() is None
        chain.append(AuditEvent(message="Event 0"))
        assert chain.get_last_hash() is not None

    def test_get_chain_id(self) -> None:
        """Verify getting the chain ID."""
        chain = HashChain(chain_id="my-chain")
        assert chain.get_chain_id() == "my-chain"

    def test_chain_to_list(self) -> None:
        """Verify exporting chain as list."""
        chain = HashChain()
        for i in range(3):
            chain.append(AuditEvent(message=f"Event {i}"))
        data = chain.to_list()
        assert len(data) == 3
        assert data[0]["sequence_number"] == 1

    def test_merkle_root_empty_chain(self) -> None:
        """Verify Merkle root of empty chain is None."""
        chain = HashChain()
        assert chain.get_merkle_root() is None

    def test_merkle_root_single_entry(self) -> None:
        """Verify Merkle root with single entry."""
        chain = HashChain()
        chain.append(AuditEvent(message="Event 0"))
        root = chain.get_merkle_root()
        assert root is not None
        assert len(root) == 64

    def test_merkle_root_multiple_entries(self) -> None:
        """Verify Merkle root with multiple entries."""
        chain = HashChain()
        for i in range(4):
            chain.append(AuditEvent(message=f"Event {i}"))
        root = chain.get_merkle_root()
        assert root is not None
        assert len(root) == 64

    def test_chain_entry_to_dict(self) -> None:
        """Verify ChainEntry serialization."""
        chain = HashChain()
        event = AuditEvent(message="Test")
        entry = chain.append(event)
        data = entry.to_dict()
        assert "event" in data
        assert "sequence_number" in data
        assert "entry_hash" in data
        assert "previous_entry_hash" in data

    def test_chain_entry_from_dict(self) -> None:
        """Verify ChainEntry deserialization."""
        chain = HashChain()
        event = AuditEvent(message="Test")
        entry = chain.append(event)
        data = entry.to_dict()
        restored = ChainEntry.from_dict(data)
        assert restored.sequence_number == entry.sequence_number
        assert restored.entry_hash == entry.entry_hash


# ===========================================================================
# Hash Chain Manager Tests
# ===========================================================================


class TestHashChainManager:
    """Tests for hash chain manager."""

    def test_create_chain(self) -> None:
        """Verify creating a chain via manager."""
        manager = HashChainManager()
        chain = manager.create_chain("chain-1")
        assert chain.chain_id == "chain-1"
        assert manager.get_chain("chain-1") is not None

    def test_get_nonexistent_chain(self) -> None:
        """Verify that getting a non-existent chain returns None."""
        manager = HashChainManager()
        assert manager.get_chain("nonexistent") is None

    def test_append_to_chain(self) -> None:
        """Verify appending to a chain via manager."""
        manager = HashChainManager()
        chain = manager.create_chain("chain-1")
        event = AuditEvent(message="Test")
        entry = manager.append_to_chain("chain-1", event)
        assert entry is not None
        assert len(chain) == 1

    def test_append_to_nonexistent_chain_raises(self) -> None:
        """Verify that appending to non-existent chain raises an error."""
        manager = HashChainManager()
        event = AuditEvent(message="Test")
        with pytest.raises(HashChainError, match="not found"):
            manager.append_to_chain("nonexistent", event)

    def test_verify_chain(self) -> None:
        """Verify a specific chain via manager."""
        manager = HashChainManager()
        chain = manager.create_chain("chain-1")
        for i in range(3):
            chain.append(AuditEvent(message=f"Event {i}"))
        valid, error = manager.verify_chain("chain-1")
        assert valid is True
        assert error is None

    def test_verify_nonexistent_chain(self) -> None:
        """Verify that verifying non-existent chain returns error."""
        manager = HashChainManager()
        valid, error = manager.verify_chain("nonexistent")
        assert valid is False
        assert "not found" in error

    def test_verify_all_chains(self) -> None:
        """Verify all chains via manager."""
        manager = HashChainManager()
        chain1 = manager.create_chain("chain-1")
        chain2 = manager.create_chain("chain-2")
        chain1.append(AuditEvent(message="Event 1"))
        chain2.append(AuditEvent(message="Event 2"))
        results = manager.verify_all_chains()
        assert len(results) == 2
        assert results["chain-1"][0] is True
        assert results["chain-2"][0] is True


# ===========================================================================
# Audit Security Edge Cases
# ===========================================================================


class TestAuditEdgeCases:
    """Tests for audit security edge cases."""

    def test_event_with_unicode_content(self) -> None:
        """Verify events with unicode content."""
        event = AuditEvent(message="Unicode: \u00e9\u00e8\u00ea \u4e2d\u6587 \U0001f600")
        assert event.verify_integrity() is True
        json_str = event.to_json()
        parsed = json.loads(json_str)
        assert parsed["message"] == "Unicode: \u00e9\u00e8\u00ea \u4e2d\u6587 \U0001f600"

    def test_event_with_large_details(self) -> None:
        """Verify events with large details payload."""
        large_details = {f"key_{i}": f"value_{i}" for i in range(1000)}
        event = AuditEvent(message="Large event", details=large_details)
        assert event.verify_integrity() is True
        data = event.to_dict()
        assert len(data["details"]) == 1000

    def test_chain_with_many_events(self) -> None:
        """Verify chain with many events."""
        chain = HashChain()
        for i in range(100):
            chain.append(AuditEvent(message=f"Event {i}"))
        assert len(chain) == 100
        valid, error = chain.verify()
        assert valid is True

    def test_event_enum_values(self) -> None:
        """Verify all audit event type enum values."""
        expected = {
            "authentication", "authorization", "access", "data_access",
            "data_modification", "configuration_change", "security_alert",
            "agent_action", "policy_violation", "encryption_operation",
            "secret_access", "network_access", "compliance_event", "system_event",
        }
        actual = {e.value for e in AuditEventType}
        assert actual == expected

    def test_severity_enum_values(self) -> None:
        """Verify all severity enum values."""
        expected = {"debug", "info", "notice", "warning", "error", "critical", "alert", "emergency"}
        actual = {s.value for s in AuditSeverity}
        assert actual == expected

    def test_outcome_enum_values(self) -> None:
        """Verify all outcome enum values."""
        expected = {"success", "failure", "unknown", "partial"}
        actual = {o.value for o in AuditOutcome}
        assert actual == expected
