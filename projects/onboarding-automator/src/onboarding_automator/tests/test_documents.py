"""Tests for the document management endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi.testclient import TestClient



from onboarding_automator.models import DocumentCreate, EmployeeInfo, OnboardingPlanCreate


def _create_plan_with_id(client: TestClient, employee_info: EmployeeInfo) -> str:
    """Helper to create a plan and return its ID."""
    plan_data = OnboardingPlanCreate(employee=employee_info)
    response = client.post("/api/v1/plans", json=plan_data.model_dump(mode="json"))
    return response.json()["id"]


def test_create_document(client: TestClient, employee_info: EmployeeInfo) -> None:
    """Test registering a new document."""
    plan_id = _create_plan_with_id(client, employee_info)
    doc_data = DocumentCreate(
        plan_id=plan_id,
        name="Passport Scan",
        document_type="id_proof",
    )
    response = client.post("/api/v1/documents", json=doc_data.model_dump(mode="json"))
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Passport Scan"
    assert data["status"] == "pending"


def test_list_documents(client: TestClient, employee_info: EmployeeInfo) -> None:
    """Test listing documents."""
    plan_id = _create_plan_with_id(client, employee_info)
    doc_data = DocumentCreate(
        plan_id=plan_id,
        name="Test Document",
        document_type="contract",
    )
    client.post("/api/v1/documents", json=doc_data.model_dump(mode="json"))

    response = client.get("/api/v1/documents", params={"plan_id": plan_id})
    assert response.status_code == 200
    assert len(response.json()) >= 1


def test_get_document(client: TestClient, employee_info: EmployeeInfo) -> None:
    """Test retrieving a specific document."""
    plan_id = _create_plan_with_id(client, employee_info)
    doc_data = DocumentCreate(
        plan_id=plan_id,
        name="Test Document",
        document_type="contract",
    )
    create_response = client.post(
        "/api/v1/documents", json=doc_data.model_dump(mode="json")
    )
    doc_id = create_response.json()["id"]

    response = client.get(f"/api/v1/documents/{doc_id}")
    assert response.status_code == 200
    assert response.json()["id"] == doc_id


def test_update_document(client: TestClient, employee_info: EmployeeInfo) -> None:
    """Test updating document status."""
    plan_id = _create_plan_with_id(client, employee_info)
    doc_data = DocumentCreate(
        plan_id=plan_id,
        name="Test Document",
        document_type="contract",
    )
    create_response = client.post(
        "/api/v1/documents", json=doc_data.model_dump(mode="json")
    )
    doc_id = create_response.json()["id"]

    response = client.patch(
        f"/api/v1/documents/{doc_id}", json={"status": "verified"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "verified"


def test_delete_document(client: TestClient, employee_info: EmployeeInfo) -> None:
    """Test deleting a document."""
    plan_id = _create_plan_with_id(client, employee_info)
    doc_data = DocumentCreate(
        plan_id=plan_id,
        name="Test Document",
        document_type="contract",
    )
    create_response = client.post(
        "/api/v1/documents", json=doc_data.model_dump(mode="json")
    )
    doc_id = create_response.json()["id"]

    response = client.delete(f"/api/v1/documents/{doc_id}")
    assert response.status_code == 204
