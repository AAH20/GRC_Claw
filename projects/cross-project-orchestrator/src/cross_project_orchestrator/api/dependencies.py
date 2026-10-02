"""Dependency API routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from cross_project_orchestrator.agents.dependency_resolution import DependencyEdge
from cross_project_orchestrator.main import state

router = APIRouter()


@router.get("")
async def list_dependencies() -> dict[str, Any]:
    """List all known dependency edges.

    Returns:
        List of dependency edges.
    """
    graph = state.dependency_resolution.graph
    edges: list[dict[str, str]] = []
    for _source, edge_list in graph.items():
        for edge in edge_list:
            edges.append(
                {
                    "source": edge.source,
                    "target": edge.target,
                    "version_constraint": edge.version_constraint,
                }
            )
    return {"edges": edges, "total": len(edges)}


@router.post("/resolve")
async def resolve_dependencies(request: dict[str, Any]) -> dict[str, Any]:
    """Resolve dependencies starting from a root project.

    Args:
        request: Resolution request with 'root' project ID.

    Returns:
        Resolution result with resolved versions and conflicts.

    Raises:
        HTTPException: If the request is invalid or resolution fails.
    """
    root = request.get("root")
    if not root:
        raise HTTPException(status_code=422, detail="Request requires 'root' project ID")

    try:
        result = state.dependency_resolution.resolve(root)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return {
        "resolved": result.resolved,
        "conflicts": result.conflicts,
        "unresolved": result.unresolved,
        "graph": {k: v for k, v in result.graph.items()},
    }


@router.post("/edges")
async def add_edge(request: dict[str, Any]) -> dict[str, Any]:
    """Add a dependency edge.

    Args:
        request: Edge data with 'source', 'target', and optional 'version_constraint'.

    Returns:
        Success confirmation.

    Raises:
        HTTPException: If the request is invalid.
    """
    source = request.get("source")
    target = request.get("target")
    if not source or not target:
        raise HTTPException(status_code=422, detail="Edge requires 'source' and 'target'")

    edge = DependencyEdge(
        source=source,
        target=target,
        version_constraint=request.get("version_constraint", "*"),
    )
    state.dependency_resolution.add_edge(edge)
    return {"status": "added", "edge": {"source": source, "target": target}}


@router.delete("/edges/{source}/{target}")
async def remove_edge(source: str, target: str) -> dict[str, Any]:
    """Remove a dependency edge.

    Args:
        source: Source project ID.
        target: Target project ID.

    Returns:
        Success confirmation.

    Raises:
        HTTPException: If the edge is not found.
    """
    removed = state.dependency_resolution.remove_edge(source, target)
    if not removed:
        raise HTTPException(status_code=404, detail=f"Edge not found: {source} -> {target}")
    return {"status": "removed"}


@router.get("/topology")
async def topological_order() -> dict[str, Any]:
    """Get the topological ordering of the dependency graph.

    Returns:
        Ordered list of project IDs.

    Raises:
        HTTPException: If the graph contains cycles.
    """
    try:
        order = state.dependency_resolution.topological_sort()
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {"order": order}


@router.get("/dependents/{project_id}")
async def get_dependents(project_id: str) -> dict[str, Any]:
    """Get all projects that depend on the given project.

    Args:
        project_id: The project to find dependents for.

    Returns:
        List of dependent project IDs.
    """
    dependents = state.dependency_resolution.get_dependents(project_id)
    return {"project_id": project_id, "dependents": dependents}
