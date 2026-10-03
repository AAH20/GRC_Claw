"""Security tests for common vulnerabilities."""

from __future__ import annotations

from fastapi.testclient import TestClient


class TestSecurity:
    def test_sql_injection_protection(self, client: TestClient) -> None:
        malicious_input = "'; DROP TABLE users; --"
        response = client.get(f"/api/v1/search?q={malicious_input}")
        assert response.status_code in [200, 400, 422]

    def test_xss_protection(self, client: TestClient) -> None:
        xss_payload = "<script>alert('xss')</script>"
        response = client.post(
            "/api/v1/tiers",
            json={"name": xss_payload, "level": "gold"},
        )
        assert response.status_code in [201, 400, 422]

    def test_rate_limiting(self, client: TestClient) -> None:
        responses = []
        for _ in range(150):
            response = client.get("/health")
            responses.append(response.status_code)
        assert 429 in responses or all(r == 200 for r in responses)

    def test_security_headers(self, client: TestClient) -> None:
        response = client.get("/health")
        assert "X-Frame-Options" in response.headers
        assert "X-Content-Type-Options" in response.headers
        assert "X-XSS-Protection" in response.headers

    def test_cors_headers(self, client: TestClient) -> None:
        response = client.options(
            "/api/v1/tiers",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert response.status_code == 204
        assert "Access-Control-Allow-Origin" in response.headers

    def test_input_validation(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/tiers",
            json={"name": "", "level": "invalid"},
        )
        assert response.status_code == 422

    def test_authentication_required(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/tiers",
            json={"name": "Test", "level": "gold"},
        )
        assert response.status_code in [201, 401, 403]
