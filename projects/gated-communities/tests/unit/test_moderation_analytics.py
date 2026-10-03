"""Unit tests for gated-communities moderation analytics module."""

from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_db():
    """Provide a mock database connection/cursor."""
    db = MagicMock()
    cursor = MagicMock()
    db.cursor.return_value = cursor
    return db


@pytest.fixture
def sample_moderation_metrics():
    """Return a representative moderation metrics payload."""
    return {
        "total_actions": 150,
        "actions_by_type": {
            "warn": 60,
            "mute": 40,
            "ban": 30,
            "kick": 20,
        },
        "actions_by_moderator": {
            "mod_alice": 70,
            "mod_bob": 50,
            "mod_carol": 30,
        },
        "period_start": "2025-01-01T00:00:00Z",
        "period_end": "2025-01-31T23:59:59Z",
    }


@pytest.fixture
def sample_trend_data():
    """Return a representative trend-analysis payload."""
    return {
        "daily_counts": [
            {"date": "2025-01-01", "count": 5},
            {"date": "2025-01-02", "count": 8},
            {"date": "2025-01-03", "count": 3},
            {"date": "2025-01-04", "count": 12},
            {"date": "2025-01-05", "count": 7},
        ],
        "peak_day": "2025-01-04",
        "peak_count": 12,
        "average_daily": 7.0,
        "trend_direction": "increasing",
    }


@pytest.fixture
def sample_moderation_stats():
    """Return a representative moderation statistics payload."""
    return {
        "total_members": 5000,
        "active_moderators": 12,
        "actions_last_24h": 23,
        "actions_last_7d": 145,
        "actions_last_30d": 512,
        "most_active_moderator": "mod_alice",
        "most_common_action": "warn",
        "ban_rate": 0.06,
        "appeal_rate": 0.15,
        "appeal_success_rate": 0.30,
    }


@pytest.fixture
def mock_analytics_module():
    """Patch the moderation_analytics module for isolated testing."""
    with patch(
        "gated_communities.analytics.moderation_analytics"
    ) as mock_mod:
        yield mock_mod


# ---------------------------------------------------------------------------
# Tests — get_moderation_metrics
# ---------------------------------------------------------------------------


class TestGetModerationMetrics:
    """Tests for the get_moderation_metrics function."""

    def test_returns_expected_keys(
        self, mock_db, sample_moderation_metrics
    ):
        """get_moderation_metrics should return a dict with expected top-level keys."""
        from gated_communities.analytics.moderation_analytics import (
            get_moderation_metrics,
        )

        with patch(
            "gated_communities.analytics.moderation_analytics._query_db",
            return_value=sample_moderation_metrics,
        ):
            result = get_moderation_metrics(mock_db)

        assert isinstance(result, dict)
        assert "total_actions" in result
        assert "actions_by_type" in result
        assert "actions_by_moderator" in result
        assert "period_start" in result
        assert "period_end" in result

    def test_total_actions_is_integer(
        self, mock_db, sample_moderation_metrics
    ):
        """total_actions should be an integer."""
        from gated_communities.analytics.moderation_analytics import (
            get_moderation_metrics,
        )

        with patch(
            "gated_communities.analytics.moderation_analytics._query_db",
            return_value=sample_moderation_metrics,
        ):
            result = get_moderation_metrics(mock_db)

        assert isinstance(result["total_actions"], int)
        assert result["total_actions"] == 150

    def test_actions_by_type_sums_to_total(
        self, mock_db, sample_moderation_metrics
    ):
        """Sum of actions_by_type values should equal total_actions."""
        from gated_communities.analytics.moderation_analytics import (
            get_moderation_metrics,
        )

        with patch(
            "gated_communities.analytics.moderation_analytics._query_db",
            return_value=sample_moderation_metrics,
        ):
            result = get_moderation_metrics(mock_db)

        type_sum = sum(result["actions_by_type"].values())
        assert type_sum == result["total_actions"]

    def test_empty_metrics(self, mock_db):
        """get_moderation_metrics should handle empty result gracefully."""
        from gated_communities.analytics.moderation_analytics import (
            get_moderation_metrics,
        )

        empty = {
            "total_actions": 0,
            "actions_by_type": {},
            "actions_by_moderator": {},
            "period_start": None,
            "period_end": None,
        }

        with patch(
            "gated_communities.analytics.moderation_analytics._query_db",
            return_value=empty,
        ):
            result = get_moderation_metrics(mock_db)

        assert result["total_actions"] == 0
        assert result["actions_by_type"] == {}

    def test_period_dates_are_valid(
        self, mock_db, sample_moderation_metrics
    ):
        """period_start and period_end should be parseable ISO dates."""
        from gated_communities.analytics.moderation_analytics import (
            get_moderation_metrics,
        )

        with patch(
            "gated_communities.analytics.moderation_analytics._query_db",
            return_value=sample_moderation_metrics,
        ):
            result = get_moderation_metrics(mock_db)

        start = datetime.fromisoformat(
            result["period_start"].replace("Z", "+00:00")
        )
        end = datetime.fromisoformat(
            result["period_end"].replace("Z", "+00:00")
        )
        assert start < end


# ---------------------------------------------------------------------------
# Tests — analyze_moderation_trends
# ---------------------------------------------------------------------------


class TestAnalyzeModerationTrends:
    """Tests for the analyze_moderation_trends function."""

    def test_returns_expected_keys(self, mock_db, sample_trend_data):
        """analyze_moderation_trends should return a dict with expected keys."""
        from gated_communities.analytics.moderation_analytics import (
            analyze_moderation_trends,
        )

        with patch(
            "gated_communities.analytics.moderation_analytics._query_db",
            return_value=sample_trend_data,
        ):
            result = analyze_moderation_trends(mock_db)

        assert isinstance(result, dict)
        assert "daily_counts" in result
        assert "peak_day" in result
        assert "peak_count" in result
        assert "average_daily" in result
        assert "trend_direction" in result

    def test_daily_counts_is_list_of_dicts(
        self, mock_db, sample_trend_data
    ):
        """daily_counts should be a list of dicts with date and count keys."""
        from gated_communities.analytics.moderation_analytics import (
            analyze_moderation_trends,
        )

        with patch(
            "gated_communities.analytics.moderation_analytics._query_db",
            return_value=sample_trend_data,
        ):
            result = analyze_moderation_trends(mock_db)

        assert isinstance(result["daily_counts"], list)
        assert len(result["daily_counts"]) > 0
        for entry in result["daily_counts"]:
            assert "date" in entry
            assert "count" in entry
            assert isinstance(entry["count"], int)

    def test_peak_day_matches_max_count(
        self, mock_db, sample_trend_data
    ):
        """peak_day should correspond to the day with the highest count."""
        from gated_communities.analytics.moderation_analytics import (
            analyze_moderation_trends,
        )

        with patch(
            "gated_communities.analytics.moderation_analytics._query_db",
            return_value=sample_trend_data,
        ):
            result = analyze_moderation_trends(mock_db)

        max_entry = max(result["daily_counts"], key=lambda x: x["count"])
        assert result["peak_day"] == max_entry["date"]
        assert result["peak_count"] == max_entry["count"]

    def test_average_daily_is_correct(
        self, mock_db, sample_trend_data
    ):
        """average_daily should equal the mean of daily counts."""
        from gated_communities.analytics.moderation_analytics import (
            analyze_moderation_trends,
        )

        with patch(
            "gated_communities.analytics.moderation_analytics._query_db",
            return_value=sample_trend_data,
        ):
            result = analyze_moderation_trends(mock_db)

        counts = [entry["count"] for entry in result["daily_counts"]]
        expected_avg = sum(counts) / len(counts)
        assert result["average_daily"] == pytest.approx(expected_avg)

    def test_trend_direction_valid_value(
        self, mock_db, sample_trend_data
    ):
        """trend_direction should be one of the allowed values."""
        from gated_communities.analytics.moderation_analytics import (
            analyze_moderation_trends,
        )

        with patch(
            "gated_communities.analytics.moderation_analytics._query_db",
            return_value=sample_trend_data,
        ):
            result = analyze_moderation_trends(mock_db)

        assert result["trend_direction"] in {
            "increasing",
            "decreasing",
            "stable",
        }

    def test_empty_trend_data(self, mock_db):
        """analyze_moderation_trends should handle empty data gracefully."""
        from gated_communities.analytics.moderation_analytics import (
            analyze_moderation_trends,
        )

        empty = {
            "daily_counts": [],
            "peak_day": None,
            "peak_count": 0,
            "average_daily": 0.0,
            "trend_direction": "stable",
        }

        with patch(
            "gated_communities.analytics.moderation_analytics._query_db",
            return_value=empty,
        ):
            result = analyze_moderation_trends(mock_db)

        assert result["daily_counts"] == []
        assert result["peak_day"] is None
        assert result["trend_direction"] == "stable"


# ---------------------------------------------------------------------------
# Tests — moderation_stats
# ---------------------------------------------------------------------------


class TestModerationStats:
    """Tests for the moderation_stats function."""

    def test_returns_expected_keys(
        self, mock_db, sample_moderation_stats
    ):
        """moderation_stats should return a dict with expected top-level keys."""
        from gated_communities.analytics.moderation_analytics import (
            moderation_stats,
        )

        with patch(
            "gated_communities.analytics.moderation_analytics._query_db",
            return_value=sample_moderation_stats,
        ):
            result = moderation_stats(mock_db)

        assert isinstance(result, dict)
        assert "total_members" in result
        assert "active_moderators" in result
        assert "actions_last_24h" in result
        assert "actions_last_7d" in result
        assert "actions_last_30d" in result
        assert "most_active_moderator" in result
        assert "most_common_action" in result
        assert "ban_rate" in result
        assert "appeal_rate" in result
        assert "appeal_success_rate" in result

    def test_total_members_is_positive_integer(
        self, mock_db, sample_moderation_stats
    ):
        """total_members should be a positive integer."""
        from gated_communities.analytics.moderation_analytics import (
            moderation_stats,
        )

        with patch(
            "gated_communities.analytics.moderation_analytics._query_db",
            return_value=sample_moderation_stats,
        ):
            result = moderation_stats(mock_db)

        assert isinstance(result["total_members"], int)
        assert result["total_members"] > 0

    def test_active_moderators_is_positive_integer(
        self, mock_db, sample_moderation_stats
    ):
        """active_moderators should be a positive integer."""
        from gated_communities.analytics.moderation_analytics import (
            moderation_stats,
        )

        with patch(
            "gated_communities.analytics.moderation_analytics._query_db",
            return_value=sample_moderation_stats,
        ):
            result = moderation_stats(mock_db)

        assert isinstance(result["active_moderators"], int)
        assert result["active_moderators"] > 0

    def test_action_counts_are_non_negative(
        self, mock_db, sample_moderation_stats
    ):
        """All action count fields should be non-negative integers."""
        from gated_communities.analytics.moderation_analytics import (
            moderation_stats,
        )

        with patch(
            "gated_communities.analytics.moderation_analytics._query_db",
            return_value=sample_moderation_stats,
        ):
            result = moderation_stats(mock_db)

        for key in (
            "actions_last_24h",
            "actions_last_7d",
            "actions_last_30d",
        ):
            assert isinstance(result[key], int)
            assert result[key] >= 0

    def test_24h_less_than_or_equal_7d(
        self, mock_db, sample_moderation_stats
    ):
        """actions_last_24h should be <= actions_last_7d."""
        from gated_communities.analytics.moderation_analytics import (
            moderation_stats,
        )

        with patch(
            "gated_communities.analytics.moderation_analytics._query_db",
            return_value=sample_moderation_stats,
        ):
            result = moderation_stats(mock_db)

        assert result["actions_last_24h"] <= result["actions_last_7d"]

    def test_7d_less_than_or_equal_30d(
        self, mock_db, sample_moderation_stats
    ):
        """actions_last_7d should be <= actions_last_30d."""
        from gated_communities.analytics.moderation_analytics import (
            moderation_stats,
        )

        with patch(
            "gated_communities.analytics.moderation_analytics._query_db",
            return_value=sample_moderation_stats,
        ):
            result = moderation_stats(mock_db)

        assert result["actions_last_7d"] <= result["actions_last_30d"]

    def test_rates_are_between_zero_and_one(
        self, mock_db, sample_moderation_stats
    ):
        """Rate fields should be floats between 0 and 1."""
        from gated_communities.analytics.moderation_analytics import (
            moderation_stats,
        )

        with patch(
            "gated_communities.analytics.moderation_analytics._query_db",
            return_value=sample_moderation_stats,
        ):
            result = moderation_stats(mock_db)

        for key in ("ban_rate", "appeal_rate", "appeal_success_rate"):
            assert isinstance(result[key], float)
            assert 0.0 <= result[key] <= 1.0

    def test_most_active_moderator_is_string(
        self, mock_db, sample_moderation_stats
    ):
        """most_active_moderator should be a non-empty string."""
        from gated_communities.analytics.moderation_analytics import (
            moderation_stats,
        )

        with patch(
            "gated_communities.analytics.moderation_analytics._query_db",
            return_value=sample_moderation_stats,
        ):
            result = moderation_stats(mock_db)

        assert isinstance(result["most_active_moderator"], str)
        assert len(result["most_active_moderator"]) > 0

    def test_most_common_action_is_valid(
        self, mock_db, sample_moderation_stats
    ):
        """most_common_action should be one of the known action types."""
        from gated_communities.analytics.moderation_analytics import (
            moderation_stats,
        )

        with patch(
            "gated_communities.analytics.moderation_analytics._query_db",
            return_value=sample_moderation_stats,
        ):
            result = moderation_stats(mock_db)

        assert result["most_common_action"] in {
            "warn",
            "mute",
            "ban",
            "kick",
            "note",
        }

    def test_empty_stats(self, mock_db):
        """moderation_stats should handle empty/zeroed data gracefully."""
        from gated_communities.analytics.moderation_analytics import (
            moderation_stats,
        )

        empty = {
            "total_members": 0,
            "active_moderators": 0,
            "actions_last_24h": 0,
            "actions_last_7d": 0,
            "actions_last_30d": 0,
            "most_active_moderator": None,
            "most_common_action": None,
            "ban_rate": 0.0,
            "appeal_rate": 0.0,
            "appeal_success_rate": 0.0,
        }

        with patch(
            "gated_communities.analytics.moderation_analytics._query_db",
            return_value=empty,
        ):
            result = moderation_stats(mock_db)

        assert result["total_members"] == 0
        assert result["actions_last_24h"] == 0
        assert result["ban_rate"] == 0.0
