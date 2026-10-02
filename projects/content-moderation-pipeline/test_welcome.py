"""Tests for the welcome message endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient

from onboarding_automator.models import EmployeeInfo, OnboardingPlanCreate, WelcomeMessageCreate


def _create_plan_with_id(client: TestClient, employee_info: EmployeeInfo) -> str:
    """Helper to create a plan and return its ID."""
    plan_data = OnboardingPlanCreate(employee=employee_info)
    response = client.post("/api/v1/plans", json=plan_data.model_dump(mode="json"))
    return response.json()["id"]


def test_generate_welcome_message(client: TestClient, employee_info: EmployeeInfo) -> None:
    """Test generating a welcome message."""
    plan_id = _create_plan_with_id(client, employee_info)
    msg_data = WelcomeMessageCreate(plan_id=plan_id)
    response = client.post(
        "/api/v1/welcome/generate", json=msg_data.model_dump(mode="json")
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


def test_list_welcome_messages(client: TestClient, employee_info: EmployeeInfo) -> None:
    """Test listing welcome messages for a plan."""
    plan_id = _create_plan_with_id(client, employee_info)
    response = client.get(f"/api/v1/welcome/{plan_id}")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
