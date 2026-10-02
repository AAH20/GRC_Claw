"""Tests for rights-management models."""

from __future__ import annotations

from rights_management.models import (
    InfringementReport,
    InfringementSeverity,
    InfringementStatus,
    License,
    LicenseCreate,
    LicenseStatus,
    LicenseType,
    RightsValidation,
    TakedownRequest,
    TakedownStatus,
    UsageRecord,
    UsageSummary,
    UsageType,
    ValidationStatus,
)


class TestLicenseModel:
    """Tests for License and related models."""

    def test_license_create(self) -> None:
        """Test creating a License instance."""
        license_obj = License(
            id="lic-1",
            content_id="content-1",
            license_type=LicenseType.CC_BY,
            holder="Test Holder",
        )
        assert license_obj.id == "lic-1"
        assert license_obj.status == LicenseStatus.ACTIVE

    def test_license_create_request(self) -> None:
        """Test LicenseCreate request model."""
        create = LicenseCreate(
            content_id="content-1",
            license_type=LicenseType.CC0,
            holder="Holder",
        )
        assert create.content_id == "content-1"


class TestUsageModels:
    """Tests for usage-related models."""

    def test_usage_record(self) -> None:
        """Test creating a UsageRecord."""
        record = UsageRecord(
            id="usage-1",
            content_id="content-1",
            usage_type=UsageType.VIEW,
            user_id="user-1",
        )
        assert record.id == "usage-1"
        assert record.usage_type == UsageType.VIEW

    def test_usage_summary(self) -> None:
        """Test UsageSummary model."""
        summary = UsageSummary(
            content_id="content-1",
            total_uses=10,
            by_type={"view": 5, "download": 5},
            unique_users=3,
        )
        assert summary.total_uses == 10
        assert summary.unique_users == 3


class TestInfringementModels:
    """Tests for infringement-related models."""

    def test_infringement_report(self) -> None:
        """Test creating an InfringementReport."""
        report = InfringementReport(
            id="report-1",
            content_id="content-1",
            reporter_id="reporter-1",
            description="Test infringement",
            severity=InfringementSeverity.HIGH,
        )
        assert report.status == InfringementStatus.OPEN
        assert report.severity == InfringementSeverity.HIGH


class TestValidationModels:
    """Tests for validation-related models."""

    def test_rights_validation(self) -> None:
        """Test creating a RightsValidation."""
        validation = RightsValidation(
            id="val-1",
            content_id="content-1",
            usage_type=UsageType.VIEW,
            status=ValidationStatus.VALID,
        )
        assert validation.status == ValidationStatus.VALID


class TestTakedownModels:
    """Tests for takedown-related models."""

    def test_takedown_request(self) -> None:
        """Test creating a TakedownRequest."""
        request = TakedownRequest(
            id="td-1",
            content_id="content-1",
            requester_id="requester-1",
            reason="Copyright violation",
        )
        assert request.status == TakedownStatus.PENDING
