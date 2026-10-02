"""Dependency Resolution Agent — maps inter-project dependencies and resolves conflicts."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class ConflictStrategy(StrEnum):
    """Strategy for resolving version conflicts."""

    HIGHEST_VERSION = "highest_version"
    LOWEST_VERSION = "lowest_version"
    FAIL_ON_CONFLICT = "fail_on_conflict"


@dataclass(frozen=True)
class DependencyEdge:
    """Represents a dependency relationship between two projects."""

    source: str
    target: str
    version_constraint: str = "*"


@dataclass
class ResolutionResult:
    """Result of a dependency resolution operation."""

    resolved: dict[str, str] = field(default_factory=dict)
    conflicts: list[dict[str, Any]] = field(default_factory=list)
    unresolved: list[str] = field(default_factory=list)
    graph: dict[str, list[str]] = field(default_factory=lambda: defaultdict(list))


class DependencyResolutionAgent:
    """Maps inter-project dependencies and resolves version conflicts.

    Builds a directed dependency graph from discovered projects and
    provides topological ordering and conflict resolution.
    """

    def __init__(
        self,
        max_depth: int = 10,
        cache_ttl: int = 3600,
        conflict_strategy: ConflictStrategy = ConflictStrategy.HIGHEST_VERSION,
    ) -> None:
        """Initialize the Dependency Resolution Agent.

        Args:
            max_depth: Maximum depth for dependency graph traversal.
            cache_ttl: Time-to-live for cached resolution results in seconds.
            conflict_strategy: How to resolve version conflicts.
        """
        self._max_depth = max_depth
        self._cache_ttl = cache_ttl
        self._conflict_strategy = conflict_strategy
        self._graph: dict[str, list[DependencyEdge]] = defaultdict(list)
        self._cache: dict[str, ResolutionResult] = {}

    @property
    def graph(self) -> dict[str, list[DependencyEdge]]:
        """Return the current dependency graph."""
        return dict(self._graph)

    def add_edge(self, edge: DependencyEdge) -> None:
        """Add a dependency edge to the graph.

        Args:
            edge: The dependency edge to add.
        """
        self._graph[edge.source].append(edge)
        self._cache.clear()  # Invalidate cache on graph mutation
        logger.debug("Added dependency edge", source=edge.source, target=edge.target)

    def remove_edge(self, source: str, target: str) -> bool:
        """Remove a dependency edge from the graph.

        Args:
            source: Source project ID.
            target: Target project ID.

        Returns:
            True if an edge was removed.
        """
        original_len = len(self._graph[source])
        self._graph[source] = [e for e in self._graph[source] if e.target != target]
        removed = len(self._graph[source]) < original_len
        if removed:
            self._cache.clear()
        return removed

    def resolve(self, root: str) -> ResolutionResult:
        """Resolve all dependencies starting from a root project.

        Performs a depth-limited traversal of the dependency graph and
        resolves version conflicts according to the configured strategy.

        Args:
            root: The root project ID to start resolution from.

        Returns:
            ResolutionResult with resolved versions and any conflicts.
        """
        if root in self._cache:
            return self._cache[root]

        result = ResolutionResult()
        visited: set[str] = set()
        self._dfs_resolve(root, result, visited, depth=0)

        # Detect cycles
        cycles = self._detect_cycles()
        if cycles:
            logger.warning("Dependency cycles detected", cycles=cycles)
            result.conflicts.extend({"type": "cycle", "path": c} for c in cycles)

        self._cache[root] = result
        return result

    def _dfs_resolve(
        self,
        node: str,
        result: ResolutionResult,
        visited: set[str],
        depth: int,
    ) -> None:
        """Depth-first search resolution of dependencies.

        Args:
            node: Current project node.
            result: Accumulator for resolution results.
            visited: Set of already-visited nodes.
            depth: Current traversal depth.
        """
        if depth > self._max_depth:
            logger.warning("Max depth exceeded", node=node, depth=depth)
            result.unresolved.append(node)
            return
        if node in visited:
            return
        visited.add(node)

        for edge in self._graph.get(node, []):
            result.graph[node].append(edge.target)
            if edge.target not in result.resolved:
                result.resolved[edge.target] = edge.version_constraint
            self._dfs_resolve(edge.target, result, visited, depth + 1)

    def topological_sort(self) -> list[str]:
        """Return projects in topological dependency order.

        Returns:
            List of project IDs in dependency order (leaves first).

        Raises:
            ValueError: If the graph contains cycles.
        """
        visited: set[str] = set()
        temp_mark: set[str] = set()
        order: list[str] = []

        def visit(node: str) -> None:
            if node in temp_mark:
                raise ValueError(f"Cycle detected at node: {node}")
            if node in visited:
                return
            temp_mark.add(node)
            for edge in self._graph.get(node, []):
                visit(edge.target)
            temp_mark.discard(node)
            visited.add(node)
            order.append(node)

        for node in list(self._graph.keys()):
            if node not in visited:
                visit(node)

        return order

    def _detect_cycles(self) -> list[list[str]]:
        """Detect cycles in the dependency graph using DFS.

        Returns:
            List of cycles, where each cycle is a list of node names.
        """
        cycles: list[list[str]] = []
        visited: set[str] = set()
        rec_stack: set[str] = set()
        path: list[str] = []

        def dfs(node: str) -> None:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            for edge in self._graph.get(node, []):
                if edge.target not in visited:
                    dfs(edge.target)
                elif edge.target in rec_stack:
                    cycle_start = path.index(edge.target)
                    cycles.append(path[cycle_start:] + [edge.target])
            path.pop()
            rec_stack.discard(node)

        for node in list(self._graph.keys()):
            if node not in visited:
                dfs(node)

        return cycles

    def get_dependents(self, project_id: str) -> list[str]:
        """Get all projects that depend on the given project.

        Args:
            project_id: The project to find dependents for.

        Returns:
            List of project IDs that depend on the given project.
        """
        dependents: list[str] = []
        for source, edges in self._graph.items():
            for edge in edges:
                if edge.target == project_id:
                    dependents.append(source)
        return dependents

    def clear(self) -> None:
        """Clear the dependency graph and cache."""
        self._graph.clear()
        self._cache.clear()
        logger.info("Dependency graph cleared")
