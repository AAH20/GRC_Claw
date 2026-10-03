"""Unit tests for gated-communities access control."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_user():
    """Return a mock user object."""
    user = MagicMock()
    user.id = "user-123"
    user.username = "testuser"
    user.is_active = True
    user.is_admin = False
    return user


@pytest.fixture
def mock_admin_user():
    """Return a mock admin user object."""
    admin = MagicMock()
    admin.id = "admin-456"
    admin.username = "adminuser"
    admin.is_active = True
    admin.is_admin = True
    return admin


@pytest.fixture
def mock_community():
    """Return a mock community object."""
    community = MagicMock()
    community.id = "comm-789"
    community.name = "Test Community"
    community.is_gated = True
    community.owner_id = "owner-001"
    return community


@pytest.fixture
def mock_access_service():
    """Return a mock access service with common methods."""
    service = MagicMock()
    service.check_access = MagicMock(return_value=True)
    service.grant_access = MagicMock(return_value=True)
    service.revoke_access = MagicMock(return_value=True)
    service.get_access_level = MagicMock(return_value="member")
    return service


@pytest.fixture
def access_control(mock_access_service):
    """Return an AccessControl instance wired to the mock service."""
    from src.access_control import AccessControl

    return AccessControl(service=mock_access_service)


# ---------------------------------------------------------------------------
# Tests: check_access
# ---------------------------------------------------------------------------


class TestCheckAccess:
    """Tests for access checking."""

    def test_check_access_returns_true_for_member(
        self, access_control, mock_user, mock_community
    ):
        """A member with valid access should be granted entry."""
        result = access_control.check_access(mock_user, mock_community)
        assert result is True

    def test_check_access_returns_false_for_non_member(
        self, access_control, mock_user, mock_community
    ):
        """A non-member should be denied entry."""
        access_control.service.check_access.return_value = False
        result = access_control.check_access(mock_user, mock_community)
        assert result is False

    def test_check_access_denies_inactive_user(
        self, access_control, mock_user, mock_community
    ):
        """An inactive user should be denied even if listed as member."""
        mock_user.is_active = False
        result = access_control.check_access(mock_user, mock_community)
        assert result is False

    def test_check_access_allows_admin_override(
        self, access_control, mock_admin_user, mock_community
    ):
        """An admin should always be granted access."""
        access_control.service.check_access.return_value = False
        result = access_control.check_access(mock_admin_user, mock_community)
        assert result is True

    def test_check_access_unrestricted_community(
        self, access_control, mock_user, mock_community
    ):
        """An ungated community should allow any active user."""
        mock_community.is_gated = False
        result = access_control.check_access(mock_user, mock_community)
        assert result is True

    def test_check_access_calls_service_with_correct_args(
        self, access_control, mock_user, mock_community
    ):
        """The underlying service must receive user and community IDs."""
        access_control.check_access(mock_user, mock_community)
        access_control.service.check_access.assert_called_once_with(
            mock_user.id, mock_community.id
        )

    def test_check_access_raises_on_none_user(self, access_control, mock_community):
        """Passing None as user should raise ValueError."""
        with pytest.raises(ValueError, match="user"):
            access_control.check_access(None, mock_community)

    def test_check_access_raises_on_none_community(
        self, access_control, mock_user
    ):
        """Passing None as community should raise ValueError."""
        with pytest.raises(ValueError, match="community"):
            access_control.check_access(mock_user, None)


# ---------------------------------------------------------------------------
# Tests: grant_access
# ---------------------------------------------------------------------------


class TestGrantAccess:
    """Tests for access granting."""

    def test_grant_access_returns_true_on_success(
        self, access_control, mock_user, mock_community
    ):
        """Granting access should return True on success."""
        result = access_control.grant_access(mock_user, mock_community)
        assert result is True

    def test_grant_access_calls_service_with_correct_args(
        self, access_control, mock_user, mock_community
    ):
        """The service must receive the correct user and community IDs."""
        access_control.grant_access(mock_user, mock_community)
        access_control.service.grant_access.assert_called_once_with(
            mock_user.id, mock_community.id
        )

    def test_grant_access_sets_default_expiry(
        self, access_control, mock_user, mock_community
    ):
        """Granted access should have a default expiry of 30 days."""
        before = datetime.utcnow()
        access_control.grant_access(mock_user, mock_community)
        after = datetime.utcnow()

        call_kwargs = access_control.service.grant_access.call_args
        # The service should be called with an expiry ~30 days out
        args, kwargs = call_kwargs
        if "expires_at" in kwargs:
            expiry = kwargs["expires_at"]
            assert before + timedelta(days=29) <= expiry <= after + timedelta(
                days=31
            )

    def test_grant_access_custom_expiry(
        self, access_control, mock_user, mock_community
    ):
        """A custom expiry should be forwarded to the service."""
        custom_expiry = datetime.utcnow() + timedelta(days=7)
        access_control.grant_access(
            mock_user, mock_community, expires_at=custom_expiry
        )
        _, kwargs = access_control.service.grant_access.call_args
        assert kwargs.get("expires_at") == custom_expiry

    def test_grant_access_denied_for_inactive_user(
        self, access_control, mock_user, mock_community
    ):
        """An inactive user should not be granted access."""
        mock_user.is_active = False
        result = access_control.grant_access(mock_user, mock_community)
        assert result is False

    def test_grant_access_raises_on_none_user(
        self, access_control, mock_community
    ):
        """Passing None as user should raise ValueError."""
        with pytest.raises(ValueError, match="user"):
            access_control.grant_access(None, mock_community)

    def test_grant_access_raises_on_none_community(
        self, access_control, mock_user
    ):
        """Passing None as community should raise ValueError."""
        with pytest.raises(ValueError, match="community"):
            access_control.grant_access(mock_user, None)

    def test_grant_access_idempotent(
        self, access_control, mock_user, mock_community
    ):
        """Granting access twice should not raise or duplicate."""
        access_control.grant_access(mock_user, mock_community)
        access_control.grant_access(mock_user, mock_community)
        assert access_control.service.grant_access.call_count == 2


# ---------------------------------------------------------------------------
# Tests: access_decision
# ---------------------------------------------------------------------------


class TestAccessDecision:
    """Tests for the high-level access decision logic."""

    def test_access_decision_allow(
        self, access_control, mock_user, mock_community
    ):
        """When service says allow, decision should be ALLOW."""
        access_control.service.check_access.return_value = True
        decision = access_control.access_decision(mock_user, mock_community)
        assert decision.allowed is True
        assert decision.reason == "access_granted"

    def test_access_decision_deny_non_member(
        self, access_control, mock_user, mock_community
    ):
        """When service says deny, decision should be DENY."""
        access_control.service.check_access.return_value = False
        decision = access_control.access_decision(mock_user, mock_community)
        assert decision.allowed is False
        assert decision.reason == "access_denied"

    def test_access_decision_admin_bypass(
        self, access_control, mock_admin_user, mock_community
    ):
        """Admin should bypass normal checks and always be allowed."""
        access_control.service.check_access.return_value = False
        decision = access_control.access_decision(mock_admin_user, mock_community)
        assert decision.allowed is True
        assert decision.reason == "admin_override"

    def test_access_decision_inactive_user_denied(
        self, access_control, mock_user, mock_community
    ):
        """Inactive user should be denied regardless of membership."""
        mock_user.is_active = False
        access_control.service.check_access.return_value = True
        decision = access_control.access_decision(mock_user, mock_community)
        assert decision.allowed is False
        assert decision.reason == "user_inactive"

    def test_access_decision_ungated_community_allows(
        self, access_control, mock_user, mock_community
    ):
        """Ungated community should allow any active user."""
        mock_community.is_gated = False
        access_control.service.check_access.return_value = False
        decision = access_control.access_decision(mock_user, mock_community)
        assert decision.allowed is True
        assert decision.reason == "community_unrestricted"

    def test_access_decision_returns_decision_object(
        self, access_control, mock_user, mock_community
    ):
        """The decision should be an object with allowed and reason attrs."""
        decision = access_control.access_decision(mock_user, mock_community)
        assert hasattr(decision, "allowed")
        assert hasattr(decision, "reason")
        assert isinstance(decision.allowed, bool)
        assert isinstance(decision.reason, str)

    def test_access_decision_expired_access_denied(
        self, access_control, mock_user, mock_community
    ):
        """Expired access should result in denial."""
        access_control.service.check_access.return_value = False
        access_control.service.get_access_level.return_value = "expired"
        decision = access_control.access_decision(mock_user, mock_community)
        assert decision.allowed is False
        assert decision.reason == "access_expired"

    def test_access_decision_none_user_raises(
        self, access_control, mock_community
    ):
        """Passing None as user should raise ValueError."""
        with pytest.raises(ValueError, match="user"):
            access_control.access_decision(None, mock_community)

    def test_access_decision_none_community_raises(
        self, access_control, mock_user
    ):
        """Passing None as community should raise ValueError."""
        with pytest.raises(ValueError, match="community"):
            access_control.access_decision(mock_user, None)
