"""Tests for the progress tracking endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient

from onboarding_automator.models import EmployeeInfo, OnboardingPlanCreate


def _create_plan_with_id(client: TestClient, employee_info: EmployeeInfo) -> str:
    """Helper to create a plan and return its ID."""
    plan_data = OnboardingPlanCreate(employee=employee_info)
    response = client.post("/api/v1/plans", json=plan_data.model_dump(mode="json"))
    return response.json()["id"]


def test_create_progress(client: TestClient, employee_info: EmployeeInfo) -> None:
    """Test creating a progress record."""
    plan_id = _create_plan_with_id(client, employee_info)
    response = client.post(f"/api/v1/progress/{plan_id}")
    assert response.status_code == 201
    data = response.json()
    assert data["plan_id"] == plan_id
    assert data["completion_percentage"] == 0.0


def test_get_progress(client: TestClient, employee_info: EmployeeInfo) -> None:
    """Test retrieving progress for a plan."""
    plan_id = _create_plan_with_id(client, employee_info)
    client.post(f"/api/v1/progress/{plan_id}")

    response = client.get(f"/api/v1/progress/{plan_id}")
    assert response.status_code == 200
    assert response.json()["plan_id"] == plan_id


def test_update_progress(client: TestClient, employee_info: EmployeeInfo) -> None:
    """Test updating progress."""
    plan_id = _create_plan_with_id(client, employee_info)
    client.post(f"/api/v1/progress/{plan_id}")

    response = client.patch(
        f"/api/v1/progress/{plan_id}",
        json={"total_tasks": 10, "completed_tasks": 5},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_tasks"] == 10
    assert data["completed_tasks"] == 5
    assert data["completion_percentage"] == 50.0


def test_progress_not_found(client: TestClient) -> None:
    """Test 404 for non-existent progress."""
    response = client.get("/api/v1/progress/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
