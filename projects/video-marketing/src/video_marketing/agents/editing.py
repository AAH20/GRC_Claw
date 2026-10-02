"""Editing Agent.

Handles video editing workflows including rough cuts, fine cuts,
color grading, audio mixing, and export management.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

logger = logging.getLogger(__name__)


class EditingStatus(StrEnum):
    """Editing workflow status."""

    PENDING = "pending"
    INGESTING = "ingesting"
    ROUGH_CUT = "rough_cut"
    FINE_CUT = "fine_cut"
    COLOR_GRADING = "color_grading"
    AUDIO_MIXING = "audio_mixing"
    GRAPHICS = "graphics"
    FINAL_REVIEW = "final_review"
    EXPORTING = "exporting"
    COMPLETED = "completed"
    REVISIONS = "revisions"


class ExportFormat(StrEnum):
    """Supported export formats."""

    MP4_H264 = "mp4_h264"
    MP4_H265 = "mp4_h265"
    PRORES = "prores"
    WEBM = "webm"
    GIF = "gif"


class Resolution(StrEnum):
    """Export resolutions."""

    SD_480P = "480p"
    HD_720P = "720p"
    FHD_1080P = "1080p"
    QHD_1440P = "1440p"
    UHD_4K = "4k"
    UHD_8K = "8k"


@dataclass
class EditDecision:
    """An edit decision (cut, transition, effect)."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = 0.0  # Time in source footage
    duration: float = 0.0
    edit_type: str = ""  # cut, transition, effect, audio
    description: str = ""
    source_clip: str = ""
    destination_clip: str = ""
    parameters: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExportPreset:
    """Export configuration preset."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    format: ExportFormat = ExportFormat.MP4_H264
    resolution: Resolution = Resolution.FHD_1080P
    fps: float = 30.0
    video_bitrate_mbps: float = 8.0
    audio_bitrate_kbps: int = 192
    audio_codec: str = "aac"
    video_codec: str = "libx264"
    additional_params: dict[str, Any] = field(default_factory=dict)


@dataclass
class EditingProject:
    """A video editing project."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    production_id: str = ""
    status: EditingStatus = EditingStatus.PENDING
    edit_decisions: list[EditDecision] = field(default_factory=list)
    export_presets: list[ExportPreset] = field(default_factory=list)
    timeline_duration_seconds: float = 0.0
    source_footage: list[str] = field(default_factory=list)
    exports: list[dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None
    editor: str = ""
    notes: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def edit_count(self) -> int:
        """Number of edit decisions."""
        return len(self.edit_decisions)

    @property
    def export_count(self) -> int:
        """Number of completed exports."""
        return len(self.exports)

    def to_dict(self) -> dict[str, Any]:
        """Convert editing project to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "production_id": self.production_id,
            "status": self.status.value,
            "edit_count": self.edit_count,
            "export_count": self.export_count,
            "timeline_duration_seconds": self.timeline_duration_seconds,
            "source_footage_count": len(self.source_footage),
            "editor": self.editor,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "notes": self.notes,
            "metadata": self.metadata,
        }


class EditingError(Exception):
    """Raised when an editing operation fails."""

    def __init__(self, message: str, project_id: str | None = None) -> None:
        super().__init__(message)
        self.project_id = project_id


class EditingAgent:
    """Agent responsible for video editing workflows.

    Manages the editing pipeline from ingest through rough cut,
    fine cut, color grading, audio mixing, and final export.
    """

    def __init__(self, storage_backend: Any | None = None) -> None:
        """Initialize the Editing Agent.

        Args:
            storage_backend: Optional storage backend for persistence.
        """
        self._storage = storage_backend
        self._projects: dict[str, EditingProject] = {}
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    async def create_project(
        self,
        title: str,
        production_id: str = "",
        editor: str = "",
        source_footage: list[str] | None = None,
        notes: str = "",
    ) -> EditingProject:
        """Create a new editing project.

        Args:
            title: Project title.
            production_id: Associated production ID.
            editor: Assigned editor name.
            source_footage: List of source footage file paths/URLs.
            notes: Additional notes.

        Returns:
            The created EditingProject.

        Raises:
            EditingError: If creation fails.
        """
        if not title or not title.strip():
            raise EditingError("Editing project title is required")

        project = EditingProject(
            title=title,
            production_id=production_id,
            editor=editor,
            source_footage=source_footage or [],
            notes=notes,
        )

        self._projects[project.id] = project
        self._logger.info(
            "Editing project created",
            extra={"project_id": project.id, "title": title},
        )
        return project

    async def get_project(self, project_id: str) -> EditingProject:
        """Get an editing project by ID.

        Args:
            project_id: The project ID.

        Returns:
            The EditingProject.

        Raises:
            EditingError: If project not found.
        """
        if project_id not in self._projects:
            raise EditingError(
                f"Editing project '{project_id}' not found",
                project_id=project_id,
            )
        return self._projects[project_id]

    async def update_status(
        self,
        project_id: str,
        status: EditingStatus,
    ) -> EditingProject:
        """Update editing project status.

        Args:
            project_id: The project ID.
            status: New status.

        Returns:
            Updated EditingProject.

        Raises:
            EditingError: If project not found or invalid transition.
        """
        project = await self.get_project(project_id)

        valid_transitions = self._get_valid_transitions(project.status)
        if status not in valid_transitions:
            raise EditingError(
                f"Invalid status transition from {project.status.value} to {status.value}",
                project_id=project_id,
            )

        project.status = status
        project.updated_at = datetime.now(UTC)

        if status == EditingStatus.COMPLETED:
            project.completed_at = datetime.now(UTC)

        self._logger.info(
            "Editing status updated",
            extra={"project_id": project_id, "status": status.value},
        )
        return project

    def _get_valid_transitions(self, current: EditingStatus) -> list[EditingStatus]:
        """Get valid status transitions."""
        transitions: dict[EditingStatus, list[EditingStatus]] = {
            EditingStatus.PENDING: [EditingStatus.INGESTING],
            EditingStatus.INGESTING: [EditingStatus.ROUGH_CUT],
            EditingStatus.ROUGH_CUT: [EditingStatus.FINE_CUT, EditingStatus.REVISIONS],
            EditingStatus.FINE_CUT: [EditingStatus.COLOR_GRADING, EditingStatus.REVISIONS],
            EditingStatus.COLOR_GRADING: [EditingStatus.AUDIO_MIXING, EditingStatus.REVISIONS],
            EditingStatus.AUDIO_MIXING: [EditingStatus.GRAPHICS, EditingStatus.REVISIONS],
            EditingStatus.GRAPHICS: [EditingStatus.FINAL_REVIEW, EditingStatus.REVISIONS],
            EditingStatus.FINAL_REVIEW: [EditingStatus.EXPORTING, EditingStatus.REVISIONS],
            EditingStatus.EXPORTING: [EditingStatus.COMPLETED, EditingStatus.REVISIONS],
            EditingStatus.REVISIONS: [
                EditingStatus.ROUGH_CUT,
                EditingStatus.FINE_CUT,
                EditingStatus.COLOR_GRADING,
                EditingStatus.AUDIO_MIXING,
                EditingStatus.GRAPHICS,
                EditingStatus.FINAL_REVIEW,
            ],
            EditingStatus.COMPLETED: [],
        }
        return transitions.get(current, [])

    async def add_edit_decision(
        self,
        project_id: str,
        timestamp: float,
        duration: float,
        edit_type: str,
        description: str = "",
        source_clip: str = "",
        destination_clip: str = "",
        parameters: dict[str, Any] | None = None,
    ) -> EditDecision:
        """Add an edit decision to the timeline.

        Args:
            project_id: The project ID.
            timestamp: Time in source footage (seconds).
            duration: Duration of the edit (seconds).
            edit_type: Type of edit (cut, transition, effect, audio).
            description: Edit description.
            source_clip: Source clip identifier.
            destination_clip: Destination clip identifier.
            parameters: Additional edit parameters.

        Returns:
            The created EditDecision.

        Raises:
            EditingError: If project not found.
        """
        project = await self.get_project(project_id)

        decision = EditDecision(
            timestamp=timestamp,
            duration=duration,
            edit_type=edit_type,
            description=description,
            source_clip=source_clip,
            destination_clip=destination_clip,
            parameters=parameters or {},
        )

        project.edit_decisions.append(decision)
        project.updated_at = datetime.now(UTC)

        self._logger.info(
            "Edit decision added",
            extra={"project_id": project_id, "decision_id": decision.id, "type": edit_type},
        )
        return decision

    async def add_export_preset(
        self,
        project_id: str,
        name: str,
        format: ExportFormat = ExportFormat.MP4_H264,
        resolution: Resolution = Resolution.FHD_1080P,
        fps: float = 30.0,
        video_bitrate_mbps: float = 8.0,
        audio_bitrate_kbps: int = 192,
    ) -> ExportPreset:
        """Add an export preset to the project.

        Args:
            project_id: The project ID.
            name: Preset name.
            format: Export format.
            resolution: Export resolution.
            fps: Frames per second.
            video_bitrate_mbps: Video bitrate in Mbps.
            audio_bitrate_kbps: Audio bitrate in kbps.

        Returns:
            The created ExportPreset.

        Raises:
            EditingError: If project not found.
        """
        project = await self.get_project(project_id)

        preset = ExportPreset(
            name=name,
            format=format,
            resolution=resolution,
            fps=fps,
            video_bitrate_mbps=video_bitrate_mbps,
            audio_bitrate_kbps=audio_bitrate_kbps,
        )

        project.export_presets.append(preset)
        project.updated_at = datetime.now(UTC)

        self._logger.info(
            "Export preset added",
            extra={"project_id": project_id, "preset_id": preset.id, "name": name},
        )
        return preset

    async def add_export(
        self,
        project_id: str,
        preset_id: str,
        output_url: str,
        file_size_bytes: int = 0,
    ) -> dict[str, Any]:
        """Record a completed export.

        Args:
            project_id: The project ID.
            preset_id: The export preset used.
            output_url: URL/path to the exported file.
            file_size_bytes: File size in bytes.

        Returns:
            Export record dictionary.

        Raises:
            EditingError: If project not found.
        """
        project = await self.get_project(project_id)

        export_record = {
            "id": str(uuid.uuid4()),
            "preset_id": preset_id,
            "output_url": output_url,
            "file_size_bytes": file_size_bytes,
            "created_at": datetime.now(UTC).isoformat(),
        }

        project.exports.append(export_record)
        project.updated_at = datetime.now(UTC)

        self._logger.info(
            "Export recorded",
            extra={"project_id": project_id, "export_id": export_record["id"]},
        )
        return export_record

    async def list_projects(
        self,
        status: EditingStatus | None = None,
    ) -> list[EditingProject]:
        """List editing projects, optionally filtered by status.

        Args:
            status: Filter by status.

        Returns:
            List of EditingProject objects.
        """
        projects = list(self._projects.values())
        if status is not None:
            projects = [p for p in projects if p.status == status]
        return sorted(projects, key=lambda p: p.created_at, reverse=True)

    async def generate_edl(self, project_id: str) -> list[dict[str, Any]]:
        """Generate an Edit Decision List (EDL) for the project.

        Args:
            project_id: The project ID.

        Returns:
            List of edit decision dictionaries.

        Raises:
            EditingError: If project not found.
        """
        project = await self.get_project(project_id)
        return [
            {
                "event_number": i + 1,
                "timestamp": d.timestamp,
                "duration": d.duration,
                "type": d.edit_type,
                "description": d.description,
                "source_clip": d.source_clip,
                "destination_clip": d.destination_clip,
                "parameters": d.parameters,
            }
            for i, d in enumerate(project.edit_decisions)
        ]
