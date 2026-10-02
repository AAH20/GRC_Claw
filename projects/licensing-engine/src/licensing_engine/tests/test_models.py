"""Tests for Pydantic models."""

from __future__ import annotations

from datetime import datetime

from licensing_engine.models import (
    ComplianceStatus,
    ContentType,
    License,
    LicenseCreate,
    LicenseStatus,
    LicenseTerms,
    LicenseType,
    RiskLevel,
)


class TestLicenseModels:
    """Tests for license-related models."""

    def test_license_terms_creation(self) -> None:
        """Test creating license terms."""
        terms = LicenseTerms(
            usage_rights=["read", "display"],
            restrictions=["no_modification"],
            territory=["US", "EU"],
            duration_days=365,
            attribution_required=True,
            commercial_use=False,
        )
        assert terms.usage_rights == ["read", "display"]
        assert terms.duration_days == 365

    def test_license_create(self) -> None:
        """Test creating a license request."""
        data = LicenseCreate(
            content_id="content-123",
            content_type=ContentType.TEXT,
            license_type=LicenseType.NON_EXCLUSIVE,
            licensor_id="licensor-1",
            licensee_id="licensee-1",
            terms=LicenseTerms(usage_rights=["read"]),
        )
        assert data.content_id == "content-123"
        assert data.content_type == ContentType.TEXT

    def test_license_model(self) -> None:
        """Test the full license model."""
        license_obj = License(
            content_id="content-123",
            content_type=ContentType.TEXT,
            license_type=LicenseType.NON_EXCLUSIVE,
            licensor_id="licensor-1",
            licensee_id="licensee-1",
            terms=LicenseTerms(usage_rights=["read"]),
            status=LicenseStatus.DRAFT,
        )
        assert license_obj.status == LicenseStatus.DRAFT
        assert license_obj.id is not None
        assert isinstance(license_obj.created_at, datetime)

    def test_compliance_status_enum(self) -> None:
        """Test compliance status enum values."""
        assert ComplianceStatus.COMPLIANT == "compliant"
        assert ComplianceStatus.NON_COMPLIANT == "non_compliant"

    def test_risk_level_enum(self) -> None:
        """Test risk level enum values."""
        assert RiskLevel.LOW == "low"
        assert RiskLevel.CRITICAL == "critical"
