"""Tests for the compliance check endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient

from onboarding_automator.models import ComplianceCheckCreate, EmployeeInfo, OnboardingPlanCreate


def _create_plan_with_id(client: TestClient, employee_info: EmployeeInfo) -> str:
    """Helper to create a plan and return its ID."""
    plan_data = OnboardingPlanCreate(employee=employee_info)
    response = client.post("/api/v1/plans", json=plan_data.model_dump(mode="json"))
    return response.json()["id"]


def test_create_compliance_check(client: TestClient, employee_info: EmployeeInfo) -> None:
    """Test creating a compliance check."""
    plan_id = _create_plan_with_id(client, employee_info)
    check_data = ComplianceCheckCreate(
        plan_id=plan_id,
        name="GDPR Compliance",
        category="data_privacy",
    )
    response = client.post(
        "/api/v1/compliance", json=check_data.model_dump(mode="json")
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "GDPR Compliance"
    assert data["status"] == "pending"


def test_list_compliance_checks(client: TestClient, employee_info: EmployeeInfo) -> None:
    """Test listing compliance checks."""
    plan_id = _create_plan_with_id(client, employee_info)
    check_data = ComplianceCheckCreate(
        plan_id=plan_id,
        name="Test Check",
        category="test_category",
    )
    client.post("/api/v1/compliance", json=check_data.model_dump(mode="json"))

    response = client.get("/api/v1/compliance", params={"plan_id": plan_id})
    assert response.status_code == 200
    assert len(response.json()) >= 1


def test_get_compliance_check(client: TestClient, employee_info: EmployeeInfo) -> None:
    """Test retrieving a specific compliance check."""
    plan_id = _create_plan_with_id(client, employee_info)
    check_data = ComplianceCheckCreate(
        plan_id=plan_id,
        name="Test Check",
        category="test_category",
    )
    create_response = client.post(
        "/api/v1/compliance", json=check_data.model_dump(mode="json")
    )
    check_id = create_response.json()["id"]

    response = client.get(f"/api/v1/compliance/{check_id}")
    assert response.status_code == 200
    assert response.json()["id"] == check_id


def test_update_compliance_check(client: TestClient, employee_info: EmployeeInfo) -> None:
    """Test updating a compliance check."""
    plan_id = _create_plan_with_id(client, employee_info)
    check_data = ComplianceCheckCreate(
        plan_id=plan_id,
        name="Test Check",
        category="test_category",
    )
    create_response = client.post(
        "/api/v1/compliance", json=check_data.model_dump(mode="json")
    )
    check_id = create_response.json()["id"]

    response = client.patch(
        f"/api/v1/compliance/{check_id}", json={"status": "pass"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "pass"


def test_delete_compliance_check(client: TestClient, employee_info: EmployeeInfo) -> None:
    """Test deleting a compliance check."""
    plan_id = _create_plan_with_id(client, employee_info)
    check_data = ComplianceCheckCreate(
        plan_id=plan_id,
        name="Test Check",
        category="test_category",
    )
    create_response = client.post(
        "/api/v1/compliance", json=check_data.model_dump(mode="json")
    )
    check_id = create_response.json()["id"]

    response = client.delete(f"/api/v1/compliance/{check_id}")
    assert response.status_code == 204
