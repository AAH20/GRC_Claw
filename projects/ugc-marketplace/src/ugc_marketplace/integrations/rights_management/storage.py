"""In-memory storage for rights management."""

from __future__ import annotations

from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class InMemoryStorage:
    """In-memory storage backend for rights management data."""

    def __init__(self) -> None:
        """Initialize in-memory storage."""
        self._licenses: dict[str, Any] = {}
        self._usage_records: dict[str, list[Any]] = {}
        self._infringement_reports: dict[str, Any] = {}
        self._validations: dict[str, Any] = {}
        self._takedown_requests: dict[str, Any] = {}

    async def close(self) -> None:
        """Close storage and cleanup resources."""
        logger.info("Closing in-memory storage")

    async def save_license(self, license_obj: Any) -> None:
        """Save a license.

        Args:
            license_obj: License to save.
        """
        self._licenses[license_obj.license_id] = license_obj

    async def get_license(self, license_id: str) -> Any | None:
        """Get a license by ID.

        Args:
            license_id: License identifier.

        Returns:
            License or None.
        """
        return self._licenses.get(license_id)

    async def list_licenses(self, content_id: str | None = None) -> list[Any]:
        """List licenses.

        Args:
            content_id: Optional content filter.

        Returns:
            List of licenses.
        """
        licenses = list(self._licenses.values())
        if content_id:
            licenses = [l for l in licenses if getattr(l, "content_id", None) == content_id]
        return licenses

    async def save_usage_record(self, record: Any) -> None:
        """Save a usage record.

        Args:
            record: Usage record to save.
        """
        content_id = getattr(record, "content_id", "unknown")
        if content_id not in self._usage_records:
            self._usage_records[content_id] = []
        self._usage_records[content_id].append(record)

    async def list_usage_records(self, content_id: str) -> list[Any]:
        """List usage records for content.

        Args:
            content_id: Content identifier.

        Returns:
            List of usage records.
        """
        return self._usage_records.get(content_id, [])

    async def save_infringement_report(self, report: Any) -> None:
        """Save an infringement report.

        Args:
            report: Report to save.
        """
        self._infringement_reports[report.report_id] = report

    async def get_infringement_report(self, report_id: str) -> Any | None:
        """Get an infringement report.

        Args:
            report_id: Report identifier.

        Returns:
            Report or None.
        """
        return self._infringement_reports.get(report_id)

    async def list_infringement_reports(self, content_id: str) -> list[Any]:
        """List infringement reports for content.

        Args:
            content_id: Content identifier.

        Returns:
            List of reports.
        """
        return [
            r for r in self._infringement_reports.values()
            if getattr(r, "content_id", None) == content_id
        ]

    async def save_validation(self, validation: Any) -> None:
        """Save a rights validation.

        Args:
            validation: Validation to save.
        """
        self._validations[validation.validation_id] = validation

    async def get_validation(self, validation_id: str) -> Any | None:
        """Get a validation.

        Args:
            validation_id: Validation identifier.

        Returns:
            Validation or None.
        """
        return self._validations.get(validation_id)

    async def list_validations(self, content_id: str) -> list[Any]:
        """List validations for content.

        Args:
            content_id: Content identifier.

        Returns:
            List of validations.
        """
        return [
            v for v in self._validations.values()
            if getattr(v, "content_id", None) == content_id
        ]

    async def save_takedown_request(self, request: Any) -> None:
        """Save a takedown request.

        Args:
            request: Request to save.
        """
        self._takedown_requests[request.request_id] = request

    async def get_takedown_request(self, request_id: str) -> Any | None:
        """Get a takedown request.

        Args:
            request_id: Request identifier.

        Returns:
            Request or None.
        """
        return self._takedown_requests.get(request_id)

    async def list_takedown_requests(self, status: str | None = None) -> list[Any]:
        """List takedown requests.

        Args:
            status: Optional status filter.

        Returns:
            List of requests.
        """
        requests = list(self._takedown_requests.values())
        if status:
            requests = [r for r in requests if getattr(r, "status", None) == status]
        return requests
