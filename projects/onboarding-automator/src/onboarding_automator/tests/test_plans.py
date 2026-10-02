"""Tests for the onboarding plan endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient

from onboarding_automator.models import EmployeeInfo, OnboardingPlanCreate


def test_create_plan(client: TestClient, employee_info: EmployeeInfo) -> None:
    """Test creating a new onboarding plan."""
    plan_data = OnboardingPlanCreate(employee=employee_info)
    response = client.post("/api/v1/plans", json=plan_data.model_dump(mode="json"))
    assert response.status_code == 201
    data = response.json()
    assert data["employee"]["employee_id"] == "EMP-001"
    assert data["status"] == "not_started"
    assert "id" in data


def test_list_plans(client: TestClient, employee_info: EmployeeInfo) -> None:
    """Test listing onboarding plans."""
    plan_data = OnboardingPlanCreate(employee=employee_info)
    client.post("/api/v1/plans", json=plan_data.model_dump(mode="json"))

    response = client.get("/api/v1/plans")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1


def test_get_plan(client: TestClient, employee_info: EmployeeInfo) -> None:
    """Test retrieving a specific plan."""
    plan_data = OnboardingPlanCreate(employee=employee_info)
    create_response = client.post(
        "/api/v1/plans", json=plan_data.model_dump(mode="json")
    )
    plan_id = create_response.json()["id"]

    response = client.get(f"/api/v1/plans/{plan_id}")
    assert response.status_code == 200
    assert response.json()["id"] == plan_id


def test_get_plan_not_found(client: TestClient) -> None:
    """Test 404 for non-existent plan."""
    response = client.get("/api/v1/plans/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


def test_update_plan(client: TestClient, employee_info: EmployeeInfo) -> None:
    """Test updating a plan's status."""
    plan_data = OnboardingPlanCreate(employee=employee_info)
    create_response = client.post(
        "/api/v1/plans", json=plan_data.model_dump(mode="json")
    )
    plan_id = create_response.json()["id"]

    response = client.patch(
        f"/api/v1/plans/{plan_id}", json={"status": "in_progress"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "in_progress"


def test_delete_plan(client: TestClient, employee_info: EmployeeInfo) -> None:
    """Test deleting a plan."""
    plan_data = OnboardingPlanCreate(employee=employee_info)
    create_response = client.post(
        "/api/v1/plans", json=plan_data.model_dump(mode="json")
    )
    plan_id = create_response.json()["id"]

    response = client.delete(f"/api/v1/plans/{plan_id}")
    assert response.status_code == 204

    get_response = client.get(f"/api/v1/plans/{plan_id}")
    assert get_response.status_code == 404
