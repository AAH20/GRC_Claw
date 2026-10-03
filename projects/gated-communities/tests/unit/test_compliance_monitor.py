"""Unit tests for the compliance monitor module."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from gated_communities.compliance_monitor import (
    ComplianceMonitor,
    ComplianceStatus,
    ComplianceReport,
)


@pytest.fixture
def monitor():
    """Return a ComplianceMonitor instance with a mock community service."""
    mock_service = MagicMock()
    return ComplianceMonitor(service=mock_service)


@pytest.fixture
def sample_compliance_data():
    """Return sample compliance data for testing."""
    return {
        "community_id": "comm-123",
        "name": "Test Community",
        "rules": [
            {"id": "rule-1", "name": "No spam", "enabled": True},
            {"id": "rule-2", "name": "Be respectful", "enabled": True},
        ],
        "violations": [],
        "last_audit": "2026-10-01T00:00:00Z",
    }


@pytest.fixture
def sample_violations():
    """Return sample violations for testing."""
    return [
        {
            "id": "viol-1",
            "rule_id": "rule-1",
            "user_id": "user-1",
            "timestamp": "2026-10-02T12:00:00Z",
            "severity": "high",
            "resolved": False,
        },
        {
            "id": "viol-2",
            "rule_id": "rule-2",
            "user_id": "user-2",
            "timestamp": "2026-10-02T13:00:00Z",
            "severity": "low",
            "resolved": True,
        },
    ]


# ---------------------------------------------------------------------------
# Tests for check_compliance
# ---------------------------------------------------------------------------


class TestCheckCompliance:
    """Tests for ComplianceMonitor.check_compliance."""

    def test_check_compliance_returns_compliant(self, monitor, sample_compliance_data):
        """A community with no violations should be compliant."""
        monitor.service.get_community_data.return_value = sample_compliance_data

        result = monitor.check_compliance("comm-123")

        assert result is True
        monitor.service.get_community_data.assert_called_once_with("comm-123")

    def test_check_compliance_returns_non_compliant(self, monitor, sample_compliance_data):
        """A community with unresolved violations should be non-compliant."""
        sample_compliance_data["violations"] = [
            {"id": "v1", "resolved": False, "severity": "high"}
        ]
        monitor.service.get_community_data.return_value = sample_compliance_data

        result = monitor.check_compliance("comm-123")

        assert result is False

    def test_check_compliance_all_violations_resolved(self, monitor, sample_compliance_data):
        """Resolved violations should not affect compliance status."""
        sample_compliance_data["violations"] = [
            {"id": "v1", "resolved": True, "severity": "high"},
            {"id": "v2", "resolved": True, "severity": "medium"},
        ]
        monitor.service.get_community_data.return_value = sample_compliance_data

        result = monitor.check_compliance("comm-123")

        assert result is True

    def test_check_compliance_service_raises(self, monitor):
        """Service errors should propagate as exceptions."""
        monitor.service.get_community_data.side_effect = ConnectionError("API down")

        with pytest.raises(ConnectionError, match="API down"):
            monitor.check_compliance("comm-123")

    def test_check_compliance_empty_community_id(self, monitor):
        """Empty community ID should raise ValueError."""
        with pytest.raises(ValueError):
            monitor.check_compliance("")


# ---------------------------------------------------------------------------
# Tests for generate_compliance_report
# ---------------------------------------------------------------------------


class TestGenerateComplianceReport:
    """Tests for ComplianceMonitor.generate_compliance_report."""

    def test_generate_compliance_report_returns_report(self, monitor, sample_compliance_data):
        """Report generation should return a ComplianceReport instance."""
        monitor.service.get_community_data.return_value = sample_compliance_data

        report = monitor.generate_compliance_report("comm-123")

        assert isinstance(report, ComplianceReport)
        assert report.community_id == "comm-123"
        assert report.compliant is True

    def test_generate_compliance_report_includes_violations(self, monitor, sample_compliance_data):
        """Report should include violation details."""
        sample_compliance_data["violations"] = [
            {"id": "v1", "rule_id": "rule-1", "severity": "high", "resolved": False}
        ]
        monitor.service.get_community_data.return_value = sample_compliance_data

        report = monitor.generate_compliance_report("comm-123")

        assert len(report.violations) == 1
        assert report.violations[0]["id"] == "v1"
        assert report.compliant is False

    def test_generate_compliance_report_sets_timestamp(self, monitor, sample_compliance_data):
        """Report should have a generated timestamp."""
        monitor.service.get_community_data.return_value = sample_compliance_data

        before = datetime.utcnow()
        report = monitor.generate_compliance_report("comm-123")
        after = datetime.utcnow()

        assert before <= report.generated_at <= after

    def test_generate_compliance_report_non_compliant(self, monitor, sample_compliance_data):
        """Non-compliant community should produce a report with compliant=False."""
        sample_compliance_data["violations"] = [
            {"id": "v1", "resolved": False, "severity": "critical"},
            {"id": "v2", "resolved": False, "severity": "high"},
        ]
        monitor.service.get_community_data.return_value = sample_compliance_data

        report = monitor.generate_compliance_report("comm-123")

        assert report.compliant is False
        assert len(report.violations) == 2

    def test_generate_compliance_report_service_error(self, monitor):
        """Service errors during report generation should propagate."""
        monitor.service.get_community_data.side_effect = TimeoutError("Request timed out")

        with pytest.raises(TimeoutError):
            monitor.generate_compliance_report("comm-123")


# ---------------------------------------------------------------------------
# Tests for compliance_status
# ---------------------------------------------------------------------------


class TestComplianceStatus:
    """Tests for ComplianceMonitor.compliance_status."""

    def test_compliance_status_returns_enum(self, monitor, sample_compliance_data):
        """Status should return a ComplianceStatus enum value."""
        monitor.service.get_community_data.return_value = sample_compliance_data

        status = monitor.compliance_status("comm-123")

        assert isinstance(status, ComplianceStatus)

    def test_compliance_status_compliant(self, monitor, sample_compliance_data):
        """Community with no violations should have COMPLIANT status."""
        monitor.service.get_community_data.return_value = sample_compliance_data

        status = monitor.compliance_status("comm-123")

        assert status == ComplianceStatus.COMPLIANT

    def test_compliance_status_non_compliant(self, monitor, sample_compliance_data):
        """Community with violations should have NON_COMPLIANT status."""
        sample_compliance_data["violations"] = [
            {"id": "v1", "resolved": False, "severity": "high"}
        ]
        monitor.service.get_community_data.return_value = sample_compliance_data

        status = monitor.compliance_status("comm-123")

        assert status == ComplianceStatus.NON_COMPLIANT

    def test_compliance_status_pending_audit(self, monitor, sample_compliance_data):
        """Community with stale audit should have PENDING status."""
        stale_date = (datetime.utcnow() - timedelta(days=90)).isoformat() + "Z"
        sample_compliance_data["last_audit"] = stale_date
        monitor.service.get_community_data.return_value = sample_compliance_data

        status = monitor.compliance_status("comm-123")

        assert status == ComplianceStatus.PENDING

    def test_compliance_status_unknown_on_error(self, monitor):
        """Service errors should result in UNKNOWN status."""
        monitor.service.get_community_data.side_effect = Exception("Unexpected error")

        status = monitor.compliance_status("comm-123")

        assert status == ComplianceStatus.UNKNOWN

    def test_compliance_status_empty_violations_list(self, monitor, sample_compliance_data):
        """Explicitly empty violations list should be COMPLIANT."""
        sample_compliance_data["violations"] = []
        monitor.service.get_community_data.return_value = sample_compliance_data

        status = monitor.compliance_status("comm-123")

        assert status == ComplianceStatus.COMPLIANT
