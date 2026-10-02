"""Project API routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from cross_project_orchestrator.agents.project_discovery import DiscoveredProject
from cross_project_orchestrator.main import state

router = APIRouter()


@router.get("")
async def list_projects(
    language: str | None = Query(None, description="Filter by language"),
    project_type: str | None = Query(None, description="Filter by project type"),
) -> dict[str, Any]:
    """List all discovered projects.

    Args:
        language: Optional language filter.
        project_type: Optional project type filter.

    Returns:
        List of projects and total count.
    """
    projects = state.project_discovery.list_projects(
        language=language, project_type=project_type
    )
    return {
        "projects": [_project_to_dict(p) for p in projects],
        "total": len(projects),
    }


@router.post("")
async def register_project(project: dict[str, Any]) -> dict[str, Any]:
    """Register a new project manually.

    Args:
        project: Project registration data.

    Returns:
        The registered project.

    Raises:
        HTTPException: If the project data is invalid.
    """
    if "name" not in project or "path" not in project:
        raise HTTPException(status_code=422, detail="Project requires 'name' and 'path'")

    discovered = DiscoveredProject(
        project_id=f"manual:{project['name']}",
        name=project["name"],
        path=project["path"],
        project_type=project.get("type", "unknown"),
        language=project.get("language", "unknown"),
        dependencies=project.get("dependencies", []),
        metadata=project.get("metadata", {}),
    )
    state.project_discovery.catalog[discovered.project_id] = discovered
    return _project_to_dict(discovered)


@router.get("/{project_id}")
async def get_project(project_id: str) -> dict[str, Any]:
    """Get a specific project by ID.

    Args:
        project_id: The project identifier.

    Returns:
        The project details.

    Raises:
        HTTPException: If the project is not found.
    """
    project = state.project_discovery.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail=f"Project not found: {project_id}")
    return _project_to_dict(project)


@router.post("/scan")
async def trigger_scan() -> dict[str, Any]:
    """Trigger an immediate project discovery scan.

    Returns:
        Scan results with newly discovered projects.
    """
    discovered = await state.project_discovery.scan_now()
    return {
        "discovered": len(discovered),
        "projects": [_project_to_dict(p) for p in discovered],
    }


def _project_to_dict(project: DiscoveredProject) -> dict[str, Any]:
    """Convert a DiscoveredProject to a JSON-serializable dictionary.

    Args:
        project: The project to convert.

    Returns:
        Dictionary representation.
    """
    return {
        "project_id": project.project_id,
        "name": project.name,
        "path": project.path,
        "project_type": project.project_type,
        "language": project.language,
        "dependencies": project.dependencies,
        "metadata": project.metadata,
        "discovered_at": project.discovered_at.isoformat(),
        "last_scanned": project.last_scanned.isoformat() if project.last_scanned else None,
    }
