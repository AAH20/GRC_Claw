"""Tests for the storage backend."""

from __future__ import annotations

import pytest

from rights_management.integrations.storage import InMemoryStorage
from rights_management.models import (
    InfringementReport,
    InfringementSeverity,
    InfringementStatus,
    License,
    LicenseStatus,
    LicenseType,
    RightsValidation,
    TakedownRequest,
    TakedownStatus,
    UsageRecord,
    UsageType,
    ValidationStatus,
)


@pytest.fixture
async def storage() -> InMemoryStorage:
    """Create a fresh InMemoryStorage instance.

    Returns:
        An InMemoryStorage instance.
    """
    store = InMemoryStorage()
    yield store
    await store.close()


class TestLicenseStorage:
    """Tests for license storage operations."""

    @pytest.mark.asyncio
    async def test_save_and_get_license(self, storage: InMemoryStorage) -> None:
        """Test saving and retrieving a license."""
        license_obj = License(
            id="lic-1",
            content_id="content-1",
            license_type=LicenseType.CC_BY,
            holder="Holder",
        )
        await storage.save_license(license_obj)
        retrieved = await storage.get_license("lic-1")
        assert retrieved is not None
        assert retrieved.id == "lic-1"

    @pytest.mark.asyncio
    async def test_list_licenses(self, storage: InMemoryStorage) -> None:
        """Test listing licenses."""
        await storage.save_license(
            License(
                id="lic-1",
                content_id="content-1",
                license_type=LicenseType.CC_BY,
                holder="Holder",
            )
        )
        await storage.save_license(
            License(
                id="lic-2",
                content_id="content-2",
                license_type=LicenseType.CC0,
                holder="Holder2",
            )
        )
        results = await storage.list_licenses()
        assert len(results) == 2


class TestUsageStorage:
    """Tests for usage record storage operations."""

    @pytest.mark.asyncio
    async def test_save_and_list_usage_records(self, storage: InMemoryStorage) -> None:
        """Test saving and listing usage records."""
        record = UsageRecord(
            id="usage-1",
            content_id="content-1",
            usage_type=UsageType.VIEW,
            user_id="user-1",
        )
        await storage.save_usage_record(record)
        results = await storage.list_usage_records("content-1")
        assert len(results) == 1
        assert results[0].id == "usage-1"


class TestInfringementStorage:
    """Tests for infringement report storage operations."""

    @pytest.mark.asyncio
    async def test_save_and_get_report(self, storage: InMemoryStorage) -> None:
        """Test saving and retrieving an infringement report."""
        report = InfringementReport(
            id="report-1",
            content_id="content-1",
            reporter_id="reporter-1",
            description="Test",
            severity=InfringementSeverity.MEDIUM,
        )
        await storage.save_infringement_report(report)
        retrieved = await storage.get_infringement_report("report-1")
        assert retrieved is not None
        assert retrieved.id == "report-1"


class TestValidationStorage:
    """Tests for validation storage operations."""

    @pytest.mark.asyncio
    async def test_save_and_get_validation(self, storage: InMemoryStorage) -> None:
        """Test saving and retrieving a validation result."""
        validation = RightsValidation(
            id="val-1",
            content_id="content-1",
            usage_type=UsageType.VIEW,
            status=ValidationStatus.VALID,
        )
        await storage.save_validation(validation)
        retrieved = await storage.get_validation("val-1")
        assert retrieved is not None
        assert retrieved.id == "val-1"


class TestTakedownStorage:
    """Tests for takedown request storage operations."""

    @pytest.mark.asyncio
    async def test_save_and_get_takedown_request(self, storage: InMemoryStorage) -> None:
        """Test saving and retrieving a takedown request."""
        request = TakedownRequest(
            id="td-1",
            content_id="content-1",
            requester_id="requester-1",
            reason="Test",
        )
        await storage.save_takedown_request(request)
        retrieved = await storage.get_takedown_request("td-1")
        assert retrieved is not None
        assert retrieved.id == "td-1"
