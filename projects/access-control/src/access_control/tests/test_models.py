"""Tests for Pydantic models and schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from access_control.models.enums import AccessDecision, AuditSeverity, PolicyEffect, RoleStatus
from access_control.models.schemas import (
    AccessAudit,
    AccessRecommendation,
    AccessRequest,
    AccessResult,
    PaginatedResponse,
    Permission,
    Policy,
    Role,
    RoleCreate,
    RoleUpdate,
)


class TestModels:
    """Test suite for Pydantic models."""

    def test_permission_creation(self) -> None:
        """Test creating a permission."""
        perm = Permission(resource="documents", action="read")
        assert perm.resource == "documents"
        assert perm.action == "read"
        assert perm.effect == PolicyEffect.ALLOW
        assert perm.conditions == {}

    def test_permission_with_conditions(self) -> None:
        """Test creating a permission with conditions."""
        perm = Permission(
            resource="documents",
            action="write",
            conditions={"time_range": "09:00-17:00"},
        )
        assert perm.conditions["time_range"] == "09:00-17:00"

    def test_role_creation(self) -> None:
        """Test creating a role."""
        role = Role(name="admin", description="Administrator role")
        assert role.name == "admin"
        assert role.status == RoleStatus.ACTIVE
        assert role.permissions == []

    def test_role_with_permissions(self) -> None:
        """Test creating a role with permissions."""
        perms = [
            Permission(resource="documents", action="read"),
            Permission(resource="documents", action="write"),
        ]
        role = Role(name="editor", permissions=perms)
        assert len(role.permissions) == 2

    def test_role_create_payload(self) -> None:
        """Test role creation payload."""
        payload = RoleCreate(
            name="viewer",
            permissions=[Permission(resource="documents", action="read")],
        )
        assert payload.name == "viewer"
        assert len(payload.permissions) == 1

    def test_role_update_payload(self) -> None:
        """Test role update payload."""
        payload = RoleUpdate(name="new-name", status=RoleStatus.INACTIVE)
        assert payload.name == "new-name"
        assert payload.status == RoleStatus.INACTIVE
        assert payload.description is None

    def test_access_request_creation(self) -> None:
        """Test creating an access request."""
        req = AccessRequest(
            principal_id="user-1",
            resource="documents",
            action="read",
        )
        assert req.principal_id == "user-1"
        assert req.context == {}
        assert req.roles == []

    def test_access_result_creation(self) -> None:
        """Test creating an access result."""
        req = AccessRequest(principal_id="user-1", resource="documents", action="read")
        result = AccessResult(request=req, decision=AccessDecision.ALLOW)
        assert result.decision == AccessDecision.ALLOW
        assert result.confidence == 1.0

    def test_access_audit_creation(self) -> None:
        """Test creating an audit entry."""
        audit = AccessAudit(
            principal_id="user-1",
            action="read",
            resource="documents",
            decision=AccessDecision.ALLOW,
        )
        assert audit.severity == AuditSeverity.INFO
        assert audit.details == {}

    def test_access_recommendation_creation(self) -> None:
        """Test creating an access recommendation."""
        rec = AccessRecommendation(
            principal_id="user-1",
            resource="documents",
            action="read",
            recommendation="grant",
        )
        assert rec.recommendation == "grant"
        assert rec.confidence == 0.5

    def test_policy_creation(self) -> None:
        """Test creating a policy."""
        policy = Policy(
            name="test-policy",
            rules=[Permission(resource="documents", action="read")],
        )
        assert policy.name == "test-policy"
        assert policy.enabled is True
        assert policy.priority == 0

    def test_paginated_response(self) -> None:
        """Test paginated response."""
        resp = PaginatedResponse[str](
            items=["a", "b", "c"],
            total=3,
            page=1,
            page_size=10,
            pages=1,
        )
        assert resp.total == 3
        assert len(resp.items) == 3

    def test_invalid_access_decision(self) -> None:
        """Test that invalid access decision raises error."""
        with pytest.raises(ValidationError):
            AccessResult(
                request=AccessRequest(principal_id="u", resource="r", action="a"),
                decision="invalid",  # type: ignore
            )

    def test_invalid_confidence(self) -> None:
        """Test that invalid confidence raises error."""
        with pytest.raises(ValidationError):
            AccessResult(
                request=AccessRequest(principal_id="u", resource="r", action="a"),
                decision=AccessDecision.ALLOW,
                confidence=1.5,
            )

    def test_invalid_role_name(self) -> None:
        """Test that empty role name raises error."""
        with pytest.raises(ValidationError):
            RoleCreate(name="")

    def test_invalid_recommendation_type(self) -> None:
        """Test that invalid recommendation type raises error."""
        with pytest.raises(ValidationError):
            AccessRecommendation(
                principal_id="u",
                resource="r",
                action="a",
                recommendation="invalid",  # type: ignore
            )
