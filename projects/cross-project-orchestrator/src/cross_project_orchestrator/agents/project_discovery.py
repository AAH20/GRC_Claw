"""Project Discovery Agent — discovers and catalogs AI marketing projects."""

from __future__ import annotations

import asyncio
import contextlib
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class DiscoveredProject:
    """Represents a discovered project."""

    project_id: str
    name: str
    path: str
    project_type: str
    language: str
    dependencies: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    discovered_at: datetime = field(default_factory=datetime.utcnow)
    last_scanned: datetime | None = None


class ProjectDiscoveryAgent:
    """Discovers and catalogs all AI marketing projects across the organization.

    Scans configured project roots for recognizable project structures
    (pyproject.toml, package.json, etc.) and maintains an in-memory catalog.
    """

    PROJECT_MARKERS: dict[str, str] = {
        "pyproject.toml": "python",
        "package.json": "node",
        "Cargo.toml": "rust",
        "go.mod": "go",
        "pom.xml": "java",
        "Gemfile": "ruby",
    }

    def __init__(
        self,
        project_roots: list[str] | None = None,
        exclude_patterns: list[str] | None = None,
        scan_interval: int = 300,
    ) -> None:
        """Initialize the Project Discovery Agent.

        Args:
            project_roots: List of root directories to scan for projects.
            exclude_patterns: Glob patterns to exclude from scanning.
            scan_interval: Seconds between automatic re-scans.
        """
        self._project_roots = project_roots or ["/projects"]
        self._exclude_patterns = exclude_patterns or ["*.tmp", "*.cache", "__pycache__"]
        self._scan_interval = scan_interval
        self._catalog: dict[str, DiscoveredProject] = {}
        self._running = False
        self._scan_task: asyncio.Task[None] | None = None

    @property
    def catalog(self) -> dict[str, DiscoveredProject]:
        """Return the current project catalog."""
        return dict(self._catalog)

    @property
    def is_running(self) -> bool:
        """Check if the background scan loop is active."""
        return self._running

    async def start(self) -> None:
        """Start the background discovery scan loop."""
        if self._running:
            logger.warning("ProjectDiscoveryAgent already running")
            return
        self._running = True
        self._scan_task = asyncio.create_task(self._scan_loop())
        logger.info("ProjectDiscoveryAgent started", roots=self._project_roots)

    async def stop(self) -> None:
        """Stop the background discovery scan loop."""
        self._running = False
        if self._scan_task:
            self._scan_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._scan_task
        logger.info("ProjectDiscoveryAgent stopped")

    async def _scan_loop(self) -> None:
        """Background loop that periodically scans for projects."""
        while self._running:
            try:
                await self.scan_now()
            except Exception as exc:
                logger.error("Scan failed", error=str(exc))
            await asyncio.sleep(self._scan_interval)

    async def scan_now(self) -> list[DiscoveredProject]:
        """Perform an immediate scan of all project roots.

        Returns:
            List of newly discovered or updated projects.
        """
        discovered: list[DiscoveredProject] = []
        for root_path in self._project_roots:
            path = Path(root_path).expanduser()
            if not path.exists():
                logger.warning("Project root does not exist", path=str(path))
                continue
            for project in self._scan_directory(path):
                existing = self._catalog.get(project.project_id)
                if existing is None or self._is_newer(project, existing):
                    self._catalog[project.project_id] = project
                    discovered.append(project)
                    logger.info(
                        "Project discovered",
                        project_id=project.project_id,
                        name=project.name,
                        type=project.project_type,
                    )
        return discovered

    def _scan_directory(self, root: Path) -> list[DiscoveredProject]:
        """Scan a directory tree for project markers.

        Args:
            root: Root directory to scan.

        Returns:
            List of discovered projects.
        """
        projects: list[DiscoveredProject] = []
        for dirpath, dirnames, filenames in os.walk(root):
            # Prune excluded directories
            dirnames[:] = [
                d for d in dirnames
                if not any(
                    self._matches_pattern(d, pat) for pat in self._exclude_patterns
                )
            ]
            for marker, lang in self.PROJECT_MARKERS.items():
                if marker in filenames:
                    project = self._parse_project(Path(dirpath), marker, lang)
                    if project:
                        projects.append(project)
                    break  # One project per directory
        return projects

    def _parse_project(
        self, path: Path, marker: str, language: str
    ) -> DiscoveredProject | None:
        """Parse a project directory into a DiscoveredProject.

        Args:
            path: Project root directory.
            marker: The marker file that was found.
            language: Detected project language.

        Returns:
            DiscoveredProject or None if parsing fails.
        """
        try:
            project_id = f"{language}:{path.name}:{str(path.resolve())}"
            dependencies = self._extract_dependencies(path, marker)
            return DiscoveredProject(
                project_id=project_id,
                name=path.name,
                path=str(path.resolve()),
                project_type=self._classify_project_type(path),
                language=language,
                dependencies=dependencies,
                metadata={"marker_file": marker},
                last_scanned=datetime.utcnow(),
            )
        except Exception as exc:
            logger.warning("Failed to parse project", path=str(path), error=str(exc))
            return None

    def _extract_dependencies(self, path: Path, marker: str) -> list[str]:
        """Extract dependency names from a project's manifest file.

        Args:
            path: Project root directory.
            marker: The manifest file name.

        Returns:
            List of dependency names.
        """
        deps: list[str] = []
        manifest = path / marker
        try:
            content = manifest.read_text(encoding="utf-8")
            if marker == "pyproject.toml":
                deps = self._parse_pyproject_deps(content)
            elif marker == "package.json":
                deps = self._parse_package_json_deps(content)
        except (OSError, ValueError) as exc:
            logger.debug("Could not read dependencies", path=str(manifest), error=str(exc))
        return deps

    @staticmethod
    def _parse_pyproject_deps(content: str) -> list[str]:
        """Parse dependencies from pyproject.toml content."""
        import tomllib

        try:
            data = tomllib.loads(content)
            project_deps = data.get("project", {}).get("dependencies", [])
            deps_list: list[str] = []
            for dep in project_deps:
                name = dep.split(">=")[0].split("==")[0].split("<")[0].strip()
                if name:
                    deps_list.append(name)
            return deps_list
        except Exception:
            return []

    @staticmethod
    def _parse_package_json_deps(content: str) -> list[str]:
        """Parse dependencies from package.json content."""
        import json

        try:
            data = json.loads(content)
            deps = list(data.get("dependencies", {}).keys())
            deps.extend(data.get("devDependencies", {}).keys())
            return deps
        except Exception:
            return []

    @staticmethod
    def _classify_project_type(path: Path) -> str:
        """Classify the type of project based on directory contents.

        Args:
            path: Project root directory.

        Returns:
            Project type string.
        """
        if (path / "src").is_dir():
            return "library"
        if (path / "app").is_dir() or (path / "main.py").exists():
            return "application"
        if (path / "notebooks").is_dir():
            return "research"
        return "unknown"

    @staticmethod
    def _matches_pattern(name: str, pattern: str) -> bool:
        """Check if a name matches a glob pattern.

        Args:
            name: The name to check.
            pattern: Glob pattern.

        Returns:
            True if the name matches.
        """
        import fnmatch

        return fnmatch.fnmatch(name, pattern)

    @staticmethod
    def _is_newer(candidate: DiscoveredProject, existing: DiscoveredProject) -> bool:
        """Check if a candidate project is newer than the existing entry.

        Args:
            candidate: Newly discovered project.
            existing: Existing catalog entry.

        Returns:
            True if the candidate should replace the existing entry.
        """
        return (
            candidate.last_scanned is not None
            and (existing.last_scanned is None or candidate.last_scanned > existing.last_scanned)
        )

    def get_project(self, project_id: str) -> DiscoveredProject | None:
        """Get a project by its ID.

        Args:
            project_id: The project identifier.

        Returns:
            The discovered project or None.
        """
        return self._catalog.get(project_id)

    def list_projects(
        self, language: str | None = None, project_type: str | None = None
    ) -> list[DiscoveredProject]:
        """List discovered projects with optional filtering.

        Args:
            language: Filter by language.
            project_type: Filter by project type.

        Returns:
            Filtered list of projects.
        """
        projects = list(self._catalog.values())
        if language:
            projects = [p for p in projects if p.language == language]
        if project_type:
            projects = [p for p in projects if p.project_type == project_type]
        return projects
