"""Report service for generating and managing recruitment reports."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any


class ReportType(str, Enum):
    """Supported report types."""

    PIPELINE = "pipeline"
    HIRING_FUNNEL = "hiring_funnel"
    TIME_TO_HIRE = "time_to_hire"
    SOURCE_EFFECTIVENESS = "source_effectiveness"
    RECRUITER_PERFORMANCE = "recruiter_performance"
    DIVERSITY = "diversity"
    COST_PER_HIRE = "cost_per_hire"
    CUSTOM = "custom"


class ReportStatus(str, Enum):
    """Report generation status."""

    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


class ReportError(Exception):
    """Base exception for report service errors."""

    pass


class ReportNotFoundError(ReportError):
    """Raised when a report is not found."""

    pass


class ReportGenerationError(ReportError):
    """Raised when report generation fails."""

    pass


class InvalidReportTypeError(ReportError):
    """Raised when an invalid report type is provided."""

    pass


class Report:
    """Represents a generated report."""

    def __init__(
        self,
        report_id: str,
        report_type: ReportType,
        params: dict[str, Any],
        status: ReportStatus = ReportStatus.PENDING,
        data: dict[str, Any] | None = None,
        error_message: str | None = None,
        created_at: datetime | None = None,
        completed_at: datetime | None = None,
    ) -> None:
        self.report_id = report_id
        self.report_type = report_type
        self.params = params
        self.status = status
        self.data = data or {}
        self.error_message = error_message
        self.created_at = created_at or datetime.utcnow()
        self.completed_at = completed_at

    def to_dict(self) -> dict[str, Any]:
        """Convert report to dictionary representation."""
        return {
            "report_id": self.report_id,
            "report_type": self.report_type.value,
            "params": self.params,
            "status": self.status.value,
            "data": self.data,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


class ReportService:
    """Service for generating and managing recruitment reports."""

    def __init__(self) -> None:
        self._reports: dict[str, Report] = {}

    def generate_report(
        self,
        report_type: ReportType | str,
        params: dict[str, Any] | None = None,
    ) -> Report:
        """Generate a new report of the specified type.

        Args:
            report_type: The type of report to generate.
            params: Optional parameters for report generation.

        Returns:
            The generated Report instance.

        Raises:
            InvalidReportTypeError: If the report type is not supported.
            ReportGenerationError: If report generation fails.
        """
        params = params or {}

        if isinstance(report_type, str):
            try:
                report_type = ReportType(report_type)
            except ValueError as exc:
                raise InvalidReportTypeError(
                    f"Unsupported report type: {report_type!r}"
                ) from exc

        if not isinstance(report_type, ReportType):
            raise InvalidReportTypeError(
                f"report_type must be a ReportType or str, got {type(report_type).__name__}"
            )

        report_id = str(uuid.uuid4())
        report = Report(
            report_id=report_id,
            report_type=report_type,
            params=params,
            status=ReportStatus.GENERATING,
        )
        self._reports[report_id] = report

        try:
            report.data = self._build_report_data(report_type, params)
            report.status = ReportStatus.COMPLETED
            report.completed_at = datetime.utcnow()
        except Exception as exc:
            report.status = ReportStatus.FAILED
            report.error_message = str(exc)
            raise ReportGenerationError(
                f"Failed to generate {report_type.value} report: {exc}"
            ) from exc

        return report

    def get_report(self, report_id: str) -> Report:
        """Retrieve a report by its ID.

        Args:
            report_id: The unique identifier of the report.

        Returns:
            The Report instance.

        Raises:
            ReportNotFoundError: If no report exists with the given ID.
        """
        if not isinstance(report_id, str) or not report_id.strip():
            raise ValueError("report_id must be a non-empty string")

        report = self._reports.get(report_id)
        if report is None:
            raise ReportNotFoundError(f"Report not found: {report_id!r}")

        return report

    def list_reports(
        self,
        report_type: ReportType | str | None = None,
        status: ReportStatus | str | None = None,
    ) -> list[Report]:
        """List available reports, optionally filtered by type and status.

        Args:
            report_type: Filter by report type.
            status: Filter by report status.

        Returns:
            List of Report instances matching the filters.
        """
        reports = list(self._reports.values())

        if report_type is not None:
            if isinstance(report_type, str):
                try:
                    report_type = ReportType(report_type)
                except ValueError:
                    return []
            reports = [r for r in reports if r.report_type == report_type]

        if status is not None:
            if isinstance(status, str):
                try:
                    status = ReportStatus(status)
                except ValueError:
                    return []
            reports = [r for r in reports if r.status == status]

        return reports

    def _build_report_data(
        self,
        report_type: ReportType,
        params: dict[str, Any],
    ) -> dict[str, Any]:
        """Build report data based on type and parameters.

        Args:
            report_type: The type of report to build data for.
            params: Parameters for report generation.

        Returns:
            Dictionary containing the report data.

        Raises:
            ReportGenerationError: If data building fails.
        """
        builders = {
            ReportType.PIPELINE: self._build_pipeline_report,
            ReportType.HIRING_FUNNEL: self._build_hiring_funnel_report,
            ReportType.TIME_TO_HIRE: self._build_time_to_hire_report,
            ReportType.SOURCE_EFFECTIVENESS: self._build_source_effectiveness_report,
            ReportType.RECRUITER_PERFORMANCE: self._build_recruiter_performance_report,
            ReportType.DIVERSITY: self._build_diversity_report,
            ReportType.COST_PER_HIRE: self._build_cost_per_hire_report,
            ReportType.CUSTOM: self._build_custom_report,
        }

        builder = builders.get(report_type)
        if builder is None:
            raise ReportGenerationError(f"No builder for report type: {report_type}")

        return builder(params)

    def _build_pipeline_report(self, params: dict[str, Any]) -> dict[str, Any]:
        """Build pipeline report data."""
        return {
            "title": "Recruitment Pipeline Report",
            "stages": [
                {"name": "applied", "count": 0},
                {"name": "screening", "count": 0},
                {"name": "interview", "count": 0},
                {"name": "offer", "count": 0},
                {"name": "hired", "count": 0},
            ],
            "filters": params,
        }

    def _build_hiring_funnel_report(self, params: dict[str, Any]) -> dict[str, Any]:
        """Build hiring funnel report data."""
        return {
            "title": "Hiring Funnel Report",
            "funnel_stages": [],
            "conversion_rates": {},
            "filters": params,
        }

    def _build_time_to_hire_report(self, params: dict[str, Any]) -> dict[str, Any]:
        """Build time-to-hire report data."""
        return {
            "title": "Time to Hire Report",
            "average_days": 0,
            "median_days": 0,
            "by_department": {},
            "filters": params,
        }

    def _build_source_effectiveness_report(self, params: dict[str, Any]) -> dict[str, Any]:
        """Build source effectiveness report data."""
        return {
            "title": "Source Effectiveness Report",
            "sources": [],
            "cost_per_source": {},
            "quality_scores": {},
            "filters": params,
        }

    def _build_recruiter_performance_report(self, params: dict[str, Any]) -> dict[str, Any]:
        """Build recruiter performance report data."""
        return {
            "title": "Recruiter Performance Report",
            "recruiters": [],
            "metrics": {},
            "filters": params,
        }

    def _build_diversity_report(self, params: dict[str, Any]) -> dict[str, Any]:
        """Build diversity report data."""
        return {
            "title": "Diversity Report",
            "demographics": {},
            "pipeline_breakdown": {},
            "filters": params,
        }

    def _build_cost_per_hire_report(self, params: dict[str, Any]) -> dict[str, Any]:
        """Build cost-per-hire report data."""
        return {
            "title": "Cost Per Hire Report",
            "total_cost": 0,
            "cost_per_hire": 0,
            "by_source": {},
            "filters": params,
        }

    def _build_custom_report(self, params: dict[str, Any]) -> dict[str, Any]:
        """Build custom report data."""
        return {
            "title": params.get("title", "Custom Report"),
            "data": params.get("data", {}),
            "filters": params,
        }
