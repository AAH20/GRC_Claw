"""Unit tests for the reputation system."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def reputation_service():
    """Return a fresh ReputationService instance for each test."""
    from src.reputation import ReputationService
    return ReputationService()


@pytest.fixture
def sample_user():
    """Return a sample user dict used across tests."""
    return {
        "id": "user-001",
        "username": "alice",
        "reputation": 100,
        "created_at": datetime(2024, 1, 1),
    }


@pytest.fixture
def sample_actions():
    """Return a list of sample reputation-affecting actions."""
    return [
        {"type": "post_created", "weight": 5},
        {"type": "comment_upvoted", "weight": 2},
        {"type": "post_removed", "weight": -10},
    ]


# ---------------------------------------------------------------------------
# Tests: calculate_reputation
# ---------------------------------------------------------------------------

class TestCalculateReputation:
    """Tests for ReputationService.calculate_reputation."""

    def test_calculate_reputation_returns_correct_total(
        self, reputation_service, sample_actions
    ):
        """Sum of action weights should equal the calculated reputation."""
        result = reputation_service.calculate_reputation(sample_actions)
        assert result == -3  # 5 + 2 + (-10)

    def test_calculate_reputation_empty_actions_returns_zero(
        self, reputation_service
    ):
        """No actions should yield a reputation of 0."""
        result = reputation_service.calculate_reputation([])
        assert result == 0

    def test_calculate_reputation_single_action(
        self, reputation_service
    ):
        """A single action should return its own weight."""
        actions = [{"type": "badge_earned", "weight": 25}]
        result = reputation_service.calculate_reputation(actions)
        assert result == 25

    def test_calculate_reputation_negative_result(
        self, reputation_service
    ):
        """Negative total reputation should be returned as-is."""
        actions = [
            {"type": "post_removed", "weight": -10},
            {"type": "comment_removed", "weight": -5},
        ]
        result = reputation_service.calculate_reputation(actions)
        assert result == -15

    def test_calculate_reputation_does_not_mutate_input(
        self, reputation_service, sample_actions
    ):
        """The original actions list must remain unchanged."""
        original = list(sample_actions)
        reputation_service.calculate_reputation(sample_actions)
        assert sample_actions == original


# ---------------------------------------------------------------------------
# Tests: update_reputation
# ---------------------------------------------------------------------------

class TestUpdateReputation:
    """Tests for ReputationService.update_reputation."""

    def test_update_reputation_increases_score(
        self, reputation_service, sample_user
    ):
        """Applying a positive delta should increase the user's reputation."""
        original = sample_user["reputation"]
        delta = 15
        updated = reputation_service.update_reputation(sample_user, delta)
        assert updated["reputation"] == original + delta

    def test_update_reputation_decreases_score(
        self, reputation_service, sample_user
    ):
        """Applying a negative delta should decrease the user's reputation."""
        original = sample_user["reputation"]
        delta = -30
        updated = reputation_service.update_reputation(sample_user, delta)
        assert updated["reputation"] == original + delta

    def test_update_reputation_zero_delta_no_change(
        self, reputation_service, sample_user
    ):
        """A delta of zero should leave reputation unchanged."""
        original = sample_user["reputation"]
        updated = reputation_service.update_reputation(sample_user, 0)
        assert updated["reputation"] == original

    def test_update_reputation_returns_user_object(
        self, reputation_service, sample_user
    ):
        """The method should return the updated user dict."""
        updated = reputation_service.update_reputation(sample_user, 10)
        assert isinstance(updated, dict)
        assert updated["id"] == sample_user["id"]

    def test_update_reputation_persists_to_storage(
        self, reputation_service, sample_user
    ):
        """After update, the storage layer should reflect the new value."""
        reputation_service.update_reputation(sample_user, 20)
        stored = reputation_service.get_user(sample_user["id"])
        assert stored["reputation"] == 120

    def test_update_reputation_never_goes_below_zero(
        self, reputation_service, sample_user
    ):
        """Reputation should be clamped at 0, never negative."""
        updated = reputation_service.update_reputation(sample_user, -500)
        assert updated["reputation"] >= 0


# ---------------------------------------------------------------------------
# Tests: reputation_score
# ---------------------------------------------------------------------------

class TestReputationScore:
    """Tests for ReputationService.reputation_score."""

    def test_reputation_score_returns_float(
        self, reputation_service, sample_user
    ):
        """The score should always be a float."""
        score = reputation_service.reputation_score(sample_user)
        assert isinstance(score, float)

    def test_reputation_score_positive_for_active_user(
        self, reputation_service
    ):
        """A user with positive reputation should have a positive score."""
        user = {"id": "u2", "reputation": 500, "created_at": datetime.now()}
        score = reputation_service.reputation_score(user)
        assert score > 0.0

    def test_reputation_score_zero_for_new_user(
        self, reputation_service
    ):
        """A user with zero reputation should have a score of 0.0."""
        user = {"id": "u3", "reputation": 0, "created_at": datetime.now()}
        score = reputation_service.reputation_score(user)
        assert score == 0.0

    def test_reputation_score_scales_with_reputation(
        self, reputation_service
    ):
        """Higher reputation should yield a higher score."""
        low_user = {"id": "low", "reputation": 10, "created_at": datetime.now()}
        high_user = {"id": "high", "reputation": 1000, "created_at": datetime.now()}
        assert reputation_service.reputation_score(
            high_user
        ) > reputation_service.reputation_score(low_user)

    def test_reputation_score_accounts_for_account_age(
        self, reputation_service
    ):
        """Older accounts with the same reputation should score higher."""
        now = datetime.now()
        new_user = {
            "id": "new",
            "reputation": 100,
            "created_at": now - timedelta(days=1),
        }
        old_user = {
            "id": "old",
            "reputation": 100,
            "created_at": now - timedelta(days=365),
        }
        assert reputation_service.reputation_score(
            old_user
        ) > reputation_service.reputation_score(new_user)

    def test_reputation_score_monotonic(
        self, reputation_service
    ):
        """Score must be monotonically non-decreasing with reputation."""
        now = datetime.now()
        scores = [
            reputation_service.reputation_score(
                {"id": f"u{i}", "reputation": r, "created_at": now}
            )
            for i, r in enumerate([0, 10, 50, 100, 500, 1000])
        ]
        for i in range(len(scores) - 1):
            assert scores[i] <= scores[i + 1]
