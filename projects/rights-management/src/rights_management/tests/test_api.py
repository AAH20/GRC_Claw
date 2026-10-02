"""Tests for the rights-management API."""

from __future__ import annotations

from fastapi.testclient import TestClient


class TestHealthEndpoints:
    """Tests for health check endpoints."""

    def test_health_check(self, client: TestClient) -> None:
        """Test the health endpoint returns 200."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestLicenseEndpoints:
    """Tests for license API endpoints."""

    def test_create_license(self, client: TestClient) -> None:
        """Test creating a new license."""
        response = client.post(
            "/api/v1/licenses",
            json={
                "content_id": "content-123",
                "license_type": "CC_BY",
                "holder": "Test Holder",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["content_id"] == "content-123"
        assert data["license_type"] == "CC_BY"
        assert data["holder"] == "Test Holder"
        assert data["status"] == "active"
        assert "id" in data

    def test_list_licenses(self, client: TestClient) -> None:
        """Test listing licenses."""
        # Create a license first
        client.post(
            "/api/v1/licenses",
            json={
                "content_id": "content-456",
                "license_type": "CC0",
                "holder": "Another Holder",
            },
        )
        response = client.get("/api/v1/licenses")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_get_license(self, client: TestClient) -> None:
        """Test retrieving a specific license."""
        create_response = client.post(
            "/api/v1/licenses",
            json={
                "content_id": "content-789",
                "license_type": "PROPRIETARY",
                "holder": "Owner",
            },
        )
        license_id = create_response.json()["id"]
        response = client.get(f"/api/v1/licenses/{license_id}")
        assert response.status_code == 200
        assert response.json()["id"] == license_id

    def test_get_license_not_found(self, client: TestClient) -> None:
        """Test retrieving a non-existent license returns 404."""
        response = client.get("/api/v1/licenses/nonexistent")
        assert response.status_code == 404

    def test_revoke_license(self, client: TestClient) -> None:
        """Test revoking a license."""
        create_response = client.post(
            "/api/v1/licenses",
            json={
                "content_id": "content-revoke",
                "license_type": "CC_BY_SA",
                "holder": "Revoke Test",
            },
        )
        license_id = create_response.json()["id"]
        response = client.delete(f"/api/v1/licenses/{license_id}")
        assert response.status_code == 204
        # Verify it's revoked
        get_response = client.get(f"/api/v1/licenses/{license_id}")
        assert get_response.json()["status"] == "revoked"


class TestUsageEndpoints:
    """Tests for usage tracking API endpoints."""

    def test_record_usage(self, client: TestClient) -> None:
        """Test recording a usage event."""
        response = client.post(
            "/api/v1/usage/record",
            json={
                "content_id": "content-usage-1",
                "usage_type": "view",
                "user_id": "user-1",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["content_id"] == "content-usage-1"
        assert data["usage_type"] == "view"
        assert data["user_id"] == "user-1"

    def test_get_usage_summary(self, client: TestClient) -> None:
        """Test getting usage summary for content."""
        # Record some usage first
        client.post(
            "/api/v1/usage/record",
            json={
                "content_id": "content-summary-1",
                "usage_type": "view",
                "user_id": "user-1",
            },
        )
        client.post(
            "/api/v1/usage/record",
            json={
                "content_id": "content-summary-1",
                "usage_type": "download",
                "user_id": "user-2",
            },
        )
        response = client.get("/api/v1/usage/summary/content-summary-1")
        assert response.status_code == 200
        data = response.json()
        assert data["content_id"] == "content-summary-1"
        assert data["total_uses"] >= 2

    def test_list_usage_records(self, client: TestClient) -> None:
        """Test listing usage records for content."""
        client.post(
            "/api/v1/usage/record",
            json={
                "content_id": "content-list-1",
                "usage_type": "view",
                "user_id": "user-1",
            },
        )
        response = client.get("/api/v1/usage/records/content-list-1")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1


class TestInfringementEndpoints:
    """Tests for infringement API endpoints."""

    def test_file_infringement_report(self, client: TestClient) -> None:
        """Test filing an infringement report."""
        response = client.post(
            "/api/v1/infringement/report",
            json={
                "content_id": "content-infringe-1",
                "reporter_id": "reporter-1",
                "description": "Unauthorized reproduction of copyrighted material",
                "severity": "high",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["content_id"] == "content-infringe-1"
        assert data["reporter_id"] == "reporter-1"
        assert data["status"] == "open"

    def test_list_infringement_reports(self, client: TestClient) -> None:
        """Test listing infringement reports."""
        client.post(
            "/api/v1/infringement/report",
            json={
                "content_id": "content-list-infringe",
                "reporter_id": "reporter-2",
                "description": "Test report",
                "severity": "medium",
            },
        )
        response = client.get("/api/v1/infringement/reports/content-list-infringe")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_update_report_status(self, client: TestClient) -> None:
        """Test updating infringement report status."""
        create_response = client.post(
            "/api/v1/infringement/report",
            json={
                "content_id": "content-status-update",
                "reporter_id": "reporter-3",
                "description": "Status update test",
                "severity": "low",
            },
        )
        report_id = create_response.json()["id"]
        response = client.patch(
            f"/api/v1/infringement/reports/{report_id}/status?status=resolved"
        )
        assert response.status_code == 200
        assert response.json()["status"] == "resolved"


class TestValidationEndpoints:
    """Tests for rights validation API endpoints."""

    def test_validate_rights(self, client: TestClient) -> None:
        """Test validating content usage rights."""
        response = client.post(
            "/api/v1/validation",
            json={
                "content_id": "content-validate-1",
                "usage_type": "view",
                "user_id": "user-1",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["content_id"] == "content-validate-1"
        assert data["usage_type"] == "view"
        assert "status" in data

    def test_get_validation(self, client: TestClient) -> None:
        """Test retrieving a validation result."""
        create_response = client.post(
            "/api/v1/validation",
            json={
                "content_id": "content-get-val",
                "usage_type": "download",
                "user_id": "user-2",
            },
        )
        validation_id = create_response.json()["id"]
        response = client.get(f"/api/v1/validation/{validation_id}")
        assert response.status_code == 200
        assert response.json()["id"] == validation_id

    def test_list_validations(self, client: TestClient) -> None:
        """Test listing validation results for content."""
        client.post(
            "/api/v1/validation",
            json={
                "content_id": "content-list-val",
                "usage_type": "view",
                "user_id": "user-3",
            },
        )
        response = client.get("/api/v1/validation/content/content-list-val")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestTakedownEndpoints:
    """Tests for takedown API endpoints."""

    def test_submit_takedown_request(self, client: TestClient) -> None:
        """Test submitting a takedown request."""
        response = client.post(
            "/api/v1/takedown/request",
            json={
                "content_id": "content-takedown-1",
                "requester_id": "requester-1",
                "reason": "Copyright infringement",
                "legal_basis": "DMCA",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["content_id"] == "content-takedown-1"
        assert data["requester_id"] == "requester-1"
        assert data["status"] == "pending"

    def test_get_takedown_request(self, client: TestClient) -> None:
        """Test retrieving a takedown request."""
        create_response = client.post(
            "/api/v1/takedown/request",
            json={
                "content_id": "content-get-takedown",
                "requester_id": "requester-2",
                "reason": "Test takedown",
            },
        )
        request_id = create_response.json()["id"]
        response = client.get(f"/api/v1/takedown/{request_id}")
        assert response.status_code == 200
        assert response.json()["id"] == request_id

    def test_process_takedown_request(self, client: TestClient) -> None:
        """Test processing a takedown request."""
        create_response = client.post(
            "/api/v1/takedown/request",
            json={
                "content_id": "content-process-takedown",
                "requester_id": "requester-3",
                "reason": "Process test",
            },
        )
        request_id = create_response.json()["id"]
        response = client.post(
            f"/api/v1/takedown/{request_id}/process",
            json={
                "action": "approved",
                "reviewer_id": "reviewer-1",
                "notes": "Valid claim",
            },
        )
        assert response.status_code == 200
        assert response.json()["status"] == "approved"

    def test_list_takedown_requests(self, client: TestClient) -> None:
        """Test listing takedown requests."""
        client.post(
            "/api/v1/takedown/request",
            json={
                "content_id": "content-list-takedown",
                "requester_id": "requester-4",
                "reason": "List test",
            },
        )
        response = client.get("/api/v1/takedown")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
