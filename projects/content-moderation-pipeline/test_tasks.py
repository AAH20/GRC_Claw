"""Tests for the task management endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient

from onboarding_automator.models import EmployeeInfo, OnboardingPlanCreate, TaskCreate


def _create_plan_with_id(client: TestClient, employee_info: EmployeeInfo) -> str:
    """Helper to create a plan and return its ID."""
    plan_data = OnboardingPlanCreate(employee=employee_info)
    response = client.post("/api/v1/plans", json=plan_data.model_dump(mode="json"))
    return response.json()["id"]


def test_create_task(client: TestClient, employee_info: EmployeeInfo) -> None:
    """Test creating a new task."""
    plan_id = _create_plan_with_id(client, employee_info)
    task_data = TaskCreate(
        plan_id=plan_id,
        title="Complete security training",
        description="Mandatory security awareness course",
    )
    response = client.post("/api/v1/tasks", json=task_data.model_dump(mode="json"))
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Complete security training"
    assert data["status"] == "pending"


def test_list_tasks(client: TestClient, employee_info: EmployeeInfo) -> None:
    """Test listing tasks."""
    plan_id = _create_plan_with_id(client, employee_info)
    task_data = TaskCreate(plan_id=plan_id, title="Test task")
    client.post("/api/v1/tasks", json=task_data.model_dump(mode="json"))

    response = client.get("/api/v1/tasks", params={"plan_id": plan_id})
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1


def test_get_task(client: TestClient, employee_info: EmployeeInfo) -> None:
    """Test retrieving a specific task."""
    plan_id = _create_plan_with_id(client, employee_info)
    task_data = TaskCreate(plan_id=plan_id, title="Test task")
    create_response = client.post(
        "/api/v1/tasks", json=task_data.model_dump(mode="json")
    )
    task_id = create_response.json()["id"]

    response = client.get(f"/api/v1/tasks/{task_id}")
    assert response.status_code == 200
    assert response.json()["id"] == task_id


def test_update_task(client: TestClient, employee_info: EmployeeInfo) -> None:
    """Test updating a task."""
    plan_id = _create_plan_with_id(client, employee_info)
    task_data = TaskCreate(plan_id=plan_id, title="Test task")
    create_response = client.post(
        "/api/v1/tasks", json=task_data.model_dump(mode="json")
    )
    task_id = create_response.json()["id"]

    response = client.patch(
        f"/api/v1/tasks/{task_id}", json={"status": "completed"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "completed"


def test_delete_task(client: TestClient, employee_info: EmployeeInfo) -> None:
    """Test deleting a task."""
    plan_id = _create_plan_with_id(client, employee_info)
    task_data = TaskCreate(plan_id=plan_id, title="Test task")
    create_response = client.post(
        "/api/v1/tasks", json=task_data.model_dump(mode="json")
    )
    task_id = create_response.json()["id"]

    response = client.delete(f"/api/v1/tasks/{task_id}")
    assert response.status_code == 204
