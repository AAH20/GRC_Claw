"""In-memory storage backend for rights-management data."""

from __future__ import annotations

from rights_management.models import (
    InfringementReport,
    License,
    LicenseStatus,
    RightsValidation,
    TakedownRequest,
    TakedownStatus,
    UsageRecord,
)


class InMemoryStorage:
    """Simple in-memory storage backend.

    This backend stores all data in dictionaries and is suitable for
    development and testing. For production use, replace with a
    persistent backend (e.g., PostgreSQL, Redis).
    """

    def __init__(self) -> None:
        """Initialize empty storage dictionaries."""
        self._licenses: dict[str, License] = {}
        self._usage_records: dict[str, UsageRecord] = {}
        self._infringement_reports: dict[str, InfringementReport] = {}
        self._validations: dict[str, RightsValidation] = {}
        self._takedown_requests: dict[str, TakedownRequest] = {}

    async def close(self) -> None:
        """Release any resources held by the storage backend."""

    # License operations

    async def save_license(self, license_obj: License) -> None:
        """Store a license.

        Args:
            license_obj: The license to store.
        """
        self._licenses[license_obj.id] = license_obj

    async def get_license(self, license_id: str) -> License | None:
        """Retrieve a license by ID.

        Args:
            license_id: The license identifier.

        Returns:
            The license if found, None otherwise.
        """
        return self._licenses.get(license_id)

    async def list_licenses(
        self,
        content_id: str | None = None,
        status: LicenseStatus | None = None,
    ) -> list[License]:
        """List licenses with optional filtering.

        Args:
            content_id: Filter by content identifier.
            status: Filter by license status.

        Returns:
            List of matching licenses.
        """
        results = list(self._licenses.values())
        if content_id is not None:
            results = [lic for lic in results if lic.content_id == content_id]
        if status is not None:
            results = [lic for lic in results if lic.status == status]
        return results

    # Usage record operations

    async def save_usage_record(self, record: UsageRecord) -> None:
        """Store a usage record.

        Args:
            record: The usage record to store.
        """
        self._usage_records[record.id] = record

    async def list_usage_records(self, content_id: str) -> list[UsageRecord]:
        """List usage records for a piece of content.

        Args:
            content_id: The content identifier.

        Returns:
            List of matching usage records.
        """
        return [r for r in self._usage_records.values() if r.content_id == content_id]

    # Infringement report operations

    async def save_infringement_report(self, report: InfringementReport) -> None:
        """Store an infringement report.

        Args:
            report: The report to store.
        """
        self._infringement_reports[report.id] = report

    async def get_infringement_report(self, report_id: str) -> InfringementReport | None:
        """Retrieve an infringement report by ID.

        Args:
            report_id: The report identifier.

        Returns:
            The report if found, None otherwise.
        """
        return self._infringement_reports.get(report_id)

    async def list_infringement_reports(self, content_id: str) -> list[InfringementReport]:
        """List infringement reports for a piece of content.

        Args:
            content_id: The content identifier.

        Returns:
            List of matching reports.
        """
        return [r for r in self._infringement_reports.values() if r.content_id == content_id]

    # Validation operations

    async def save_validation(self, validation: RightsValidation) -> None:
        """Store a validation result.

        Args:
            validation: The validation result to store.
        """
        self._validations[validation.id] = validation

    async def get_validation(self, validation_id: str) -> RightsValidation | None:
        """Retrieve a validation result by ID.

        Args:
            validation_id: The validation identifier.

        Returns:
            The validation result if found, None otherwise.
        """
        return self._validations.get(validation_id)

    async def list_validations(self, content_id: str) -> list[RightsValidation]:
        """List validation results for a piece of content.

        Args:
            content_id: The content identifier.

        Returns:
            List of matching validation results.
        """
        return [v for v in self._validations.values() if v.content_id == content_id]

    # Takedown request operations

    async def save_takedown_request(self, request: TakedownRequest) -> None:
        """Store a takedown request.

        Args:
            request: The takedown request to store.
        """
        self._takedown_requests[request.id] = request

    async def get_takedown_request(self, request_id: str) -> TakedownRequest | None:
        """Retrieve a takedown request by ID.

        Args:
            request_id: The takedown request identifier.

        Returns:
            The takedown request if found, None otherwise.
        """
        return self._takedown_requests.get(request_id)

    async def list_takedown_requests(
        self,
        content_id: str | None = None,
        status: TakedownStatus | None = None,
    ) -> list[TakedownRequest]:
        """List takedown requests with optional filtering.

        Args:
            content_id: Filter by content identifier.
            status: Filter by request status.

        Returns:
            List of matching takedown requests.
        """
        results = list(self._takedown_requests.values())
        if content_id is not None:
            results = [r for r in results if r.content_id == content_id]
        if status is not None:
            results = [r for r in results if r.status == status]
        return results
