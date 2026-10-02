"""E2E tests for the Unified Platform workflow.

Tests the complete lifecycle of the Cross-Project Orchestrator:
project discovery, registration, dependency management,
and agent status monitoring.
"""
from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient

from conftest import (
    assert_health_check,
    assert_response_error,
    assert_response_success,
    generate_unique_id,
)


class TestUnifiedPlatformE2E:
    """End-to-end test suite for unified platform workflow."""

    def test_health_check(self, orchestrator_client: TestClient) -> None:
        """Verify the Cross-Project Orchestrator service is healthy.

        Args:
            orchestrator_client: Test client for the Cross-Project Orchestrator API.
        """
        assert_health_check(orchestrator_client)

    def test_project_discovery_full_workflow(
        self, orchestrator_client: TestClient, sample_project_data: dict[str, Any]
    ) -> None:
        """Test the complete project discovery and registration workflow.

        Steps:
            1. List all projects.
            2. Register a new project.
            3. Get project by ID.
            4. Trigger a scan.
            5. List projects with filters.

        Args:
            orchestrator_client: Test client for the Cross-Project Orchestrator API.
            sample_project_data: Sample project registration payload.
        """
        # Step 1: List projects
        list_response = orchestrator_client.get("/api/v1/projects")
        projects = assert_response_success(list_response)
        assert "projects" in projects
        assert "total" in projects

        # Step 2: Register project
        register_response = orchestrator_client.post(
            "/api/v1/projects", json=sample_project_data
        )
        registered = assert_response_success(register_response)

        project_id = registered["project_id"]
        assert project_id is not None
        assert registered["name"] == sample_project_data["name"]
        assert registered["path"] == sample_project_data["path"]
        assert registered["language"] == sample_project_data["language"]

        # Step 3: Get project by ID
        get_response = orchestrator_client.get(
            f"/api/v1/projects/{project_id}"
        )
        retrieved = assert_response_success(get_response)
        assert retrieved["project_id"] == project_id
        assert retrieved["name"] == sample_project_data["name"]

        # Step 4: Trigger scan
        scan_response = orchestrator_client.post("/api/v1/projects/scan")
        scan = assert_response_success(scan_response)
        assert "discovered" in scan
        assert "projects" in scan

        # Step 5: List with language filter
        filtered_response = orchestrator_client.get(
            "/api/v1/projects?language=python"
        )
        filtered = assert_response_success(filtered_response)
        assert "projects" in filtered

    def test_dependency_management_full_workflow(
        self, orchestrator_client: TestClient
    ) -> None:
        """Test the complete dependency management workflow.

        Steps:
            1. Add a dependency edge.
            2. List all dependencies.
            3. Resolve dependencies from a root.
            4. Get topological ordering.
            5. Get dependents of a project.
            6. Remove a dependency edge.

        Args:
            orchestrator_client: Test client for the Cross-Project Orchestrator API.
        """
        source = generate_unique_id("proj")
        target = generate_unique_id("proj")

        # Step 1: Add edge
        edge_request: dict[str, Any] = {
            "source": source,
            "target": target,
            "version_constraint": ">=1.0.0",
        }
        add_response = orchestrator_client.post(
            "/api/v1/dependencies/edges", json=edge_request
        )
        added = assert_response_success(add_response)
        assert added["status"] == "added"
        assert added["edge"]["source"] == source
        assert added["edge"]["target"] == target

        # Step 2: List dependencies
        list_response = orchestrator_client.get("/api/v1/dependencies")
        deps = assert_response_success(list_response)
        assert "edges" in deps
        assert "total" in deps
        assert deps["total"] >= 1

        # Step 3: Resolve dependencies
        resolve_request: dict[str, Any] = {"root": source}
        resolve_response = orchestrator_client.post(
            "/api/v1/dependencies/resolve", json=resolve_request
        )
        resolved = assert_response_success(resolve_response)
        assert "resolved" in resolved
        assert "conflicts" in resolved
        assert "unresolved" in resolved

        # Step 4: Topological order
        topo_response = orchestrator_client.get(
            "/api/v1/dependencies/topology"
        )
        topo = assert_response_success(topo_response)
        assert "order" in topo

        # Step 5: Get dependents
        dependents_response = orchestrator_client.get(
            f"/api/v1/dependencies/dependents/{target}"
        )
        dependents = assert_response_success(dependents_response)
        assert "project_id" in dependents
        assert "dependents" in dependents

        # Step 6: Remove edge
        remove_response = orchestrator_client.delete(
            f"/api/v1/dependencies/edges/{source}/{target}"
        )
        removed = assert_response_success(remove_response)
        assert removed["status"] == "removed"

    def test_agent_status_monitoring(
        self, orchestrator_client: TestClient
    ) -> None:
        """Test agent status monitoring.

        Args:
            orchestrator_client: Test client for the Cross-Project Orchestrator API.
        """
        agent_ids = [
            "project_discovery",
            "dependency_resolution",
            "resource_allocation",
            "health_monitoring",
            "cost_optimization",
        ]
        for agent_id in agent_ids:
            response = orchestrator_client.get(
                f"/api/v1/agents/{agent_id}/status"
            )
            result = assert_response_success(response)
            assert result["agent_id"] == agent_id
            assert "running" in result

    def test_project_registration_validation_error(
        self, orchestrator_client: TestClient
    ) -> None:
        """Test that project registration validates required fields.

        Args:
            orchestrator_client: Test client for the Cross-Project Orchestrator API.
        """
        invalid_data: dict[str, Any] = {
            "type": "python",
        }
        response = orchestrator_client.post(
            "/api/v1/projects", json=invalid_data
        )
        assert_response_error(response, expected_status=422)

    def test_project_not_found_error(
        self, orchestrator_client: TestClient
    ) -> None:
        """Test that accessing a non-existent project returns 404.

        Args:
            orchestrator_client: Test client for the Cross-Project Orchestrator API.
        """
        fake_id = "nonexistent-project-id"
        response = orchestrator_client.get(f"/api/v1/projects/{fake_id}")
        assert_response_error(response, expected_status=404)

    def test_dependency_edge_validation_error(
        self, orchestrator_client: TestClient
    ) -> None:
        """Test that dependency edge creation validates required fields.

        Args:
            orchestrator_client: Test client for the Cross-Project Orchestrator API.
        """
        invalid_request: dict[str, Any] = {
            "source": "",
            "target": "",
        }
        response = orchestrator_client.post(
            "/api/v1/dependencies/edges", json=invalid_request
        )
        assert_response_error(response, expected_status=422)

    def test_dependency_resolution_validation_error(
        self, orchestrator_client: TestClient
    ) -> None:
        """Test that dependency resolution validates required fields.

        Args:
            orchestrator_client: Test client for the Cross-Project Orchestrator API.
        """
        invalid_request: dict[str, Any] = {}
        response = orchestrator_client.post(
            "/api/v1/dependencies/resolve", json=invalid_request
        )
        assert_response_error(response, expected_status=422)

    def test_unknown_agent_status_error(
        self, orchestrator_client: TestClient
    ) -> None:
        """Test that accessing an unknown agent returns 404.

        Args:
            orchestrator_client: Test client for the Cross-Project Orchestrator API.
        """
        response = orchestrator_client.get("/api/v1/agents/unknown_agent/status")
        assert_response_error(response, expected_status=404)

    def test_full_unified_platform_integration(
        self, orchestrator_client: TestClient, sample_project_data: dict[str, Any]
    ) -> None:
        """Test the full unified platform integration workflow.

        Steps:
            1. Register a project.
            2. Add dependency edges.
            3. Resolve dependencies.
            4. Check agent statuses.
            5. Trigger project scan.
            6. Verify project appears in listing.

        Args:
            orchestrator_client: Test client for the Cross-Project Orchestrator API.
            sample_project_data: Sample project registration payload.
        """
        # Step 1: Register project
        register_response = orchestrator_client.post(
            "/api/v1/projects", json=sample_project_data
        )
        registered = assert_response_success(register_response)
        project_id = registered["project_id"]

        # Step 2: Add dependency edges
        dep_source = generate_unique_id("proj")
        edge_request: dict[str, Any] = {
            "source": dep_source,
            "target": project_id,
            "version_constraint": "*",
        }
        edge_response = orchestrator_client.post(
            "/api/v1/dependencies/edges", json=edge_request
        )
        assert_response_success(edge_response)

        # Step 3: Resolve dependencies
        resolve_request: dict[str, Any] = {"root": dep_source}
        resolve_response = orchestrator_client.post(
            "/api/v1/dependencies/resolve", json=resolve_request
        )
        resolved = assert_response_success(resolve_response)
        assert "resolved" in resolved

        # Step 4: Check agent statuses
        for agent_id in ["project_discovery", "health_monitoring"]:
            status_response = orchestrator_client.get(
                f"/api/v1/agents/{agent_id}/status"
            )
            status = assert_response_success(status_response)
            assert status["agent_id"] == agent_id

        # Step 5: Trigger scan
        scan_response = orchestrator_client.post("/api/v1/projects/scan")
        scan = assert_response_success(scan_response)
        assert "discovered" in scan

        # Step 6: Verify project in listing
        list_response = orchestrator_client.get("/api/v1/projects")
        projects = assert_response_success(list_response)
        project_ids = [p["project_id"] for p in projects["projects"]]
        assert project_id in project_ids

        # Cleanup: remove edge
        orchestrator_client.delete(
            f"/api/v1/dependencies/edges/{dep_source}/{project_id}"
        )
