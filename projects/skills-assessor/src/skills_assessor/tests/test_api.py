"""Tests for API endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi.testclient import TestClient


class TestHealthAPI:
    """Test suite for health endpoints."""

    def test_health_check(self, test_client: TestClient) -> None:
        """Test health check endpoint."""
        response = test_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "timestamp" in data

    def test_readiness_check(self, test_client: TestClient) -> None:
        """Test readiness check endpoint."""
        response = test_client.get("/ready")
        assert response.status_code == 200
        data = response.json()
        assert "ready" in data
        assert "checks" in data


class TestAssessmentsAPI:
    """Test suite for assessment endpoints."""

    def test_create_assessment(self, test_client: TestClient) -> None:
        """Test creating an assessment."""
        response = test_client.post(
            "/assessments",
            json={
                "candidate_id": "candidate-123",
                "candidate_name": "John Doe",
                "target_role": "Software Engineer",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["candidate_id"] == "candidate-123"
        assert data["status"] == "pending"
        assert "id" in data

    def test_list_assessments(self, test_client: TestClient) -> None:
        """Test listing assessments."""
        # Create one first
        test_client.post(
            "/assessments",
            json={"candidate_id": "candidate-123"},
        )
        response = test_client.get("/assessments")
        assert response.status_code == 200
        data = response.json()
        assert "assessments" in data
        assert "total" in data

    def test_get_assessment_not_found(self, test_client: TestClient) -> None:
        """Test getting non-existent assessment."""
        response = test_client.get("/assessments/123e4567-e89b-12d3-a456-426614174000")
        assert response.status_code == 404

    def test_delete_assessment_not_found(self, test_client: TestClient) -> None:
        """Test deleting non-existent assessment."""
        response = test_client.delete("/assessments/123e4567-e89b-12d3-a456-426614174000")
        assert response.status_code == 404

    def test_complete_assessment_not_found(self, test_client: TestClient) -> None:
        """Test completing non-existent assessment."""
        response = test_client.post("/assessments/123e4567-e89b-12d3-a456-426614174000/complete")
        assert response.status_code == 404

    def test_get_assessment_summary_not_found(self, test_client: TestClient) -> None:
        """Test getting summary of non-existent assessment."""
        response = test_client.get("/assessments/123e4567-e89b-12d3-a456-426614174000/summary")
        assert response.status_code == 404

    def test_extract_skills_not_found(self, test_client: TestClient) -> None:
        """Test extracting skills from non-existent assessment."""
        response = test_client.post(
            "/assessments/123e4567-e89b-12d3-a456-426614174000/extract-skills",
            json={"text": "Python developer"},
        )
        assert response.status_code == 404

    def test_score_skills_not_found(self, test_client: TestClient) -> None:
        """Test scoring skills for non-existent assessment."""
        response = test_client.post(
            "/assessments/123e4567-e89b-12d3-a456-426614174000/score",
            json={"skills": [{"name": "python"}]},
        )
        assert response.status_code == 404

    def test_analyze_gaps_not_found(self, test_client: TestClient) -> None:
        """Test analyzing gaps for non-existent assessment."""
        response = test_client.post(
            "/assessments/123e4567-e89b-12d3-a456-426614174000/analyze-gaps",
            json={"assessment_id": "123e4567-e89b-12d3-a456-426614174000", "target_role": "Engineer"},
        )
        assert response.status_code == 404

    def test_validate_skills_not_found(self, test_client: TestClient) -> None:
        """Test validating skills for non-existent assessment."""
        response = test_client.post(
            "/assessments/123e4567-e89b-12d3-a456-426614174000/validate",
            json={"skills": [{"name": "python"}]},
        )
        assert response.status_code == 404

    def test_generate_learning_path_not_found(self, test_client: TestClient) -> None:
        """Test generating learning path for non-existent assessment."""
        response = test_client.post(
            "/assessments/123e4567-e89b-12d3-a456-426614174000/learning-path",
            json={"assessment_id": "123e4567-e89b-12d3-a456-426614174000", "target_role": "Engineer"},
        )
        assert response.status_code == 404


class TestSkillsAPI:
    """Test suite for skills endpoints."""

    def test_list_skills(self, test_client: TestClient) -> None:
        """Test listing skills."""
        response = test_client.get("/skills")
        assert response.status_code == 200
        data = response.json()
        assert "skills" in data
        assert "total" in data

    def test_get_skill_not_found(self, test_client: TestClient) -> None:
        """Test getting non-existent skill."""
        response = test_client.get("/skills/123e4567-e89b-12d3-a456-426614174000")
        assert response.status_code == 404

    def test_create_skill(self, test_client: TestClient) -> None:
        """Test creating a skill."""
        response = test_client.post(
            "/skills",
            json={"name": "Python", "category": "technical"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "python"
        assert "id" in data

    def test_delete_skill_not_found(self, test_client: TestClient) -> None:
        """Test deleting non-existent skill."""
        response = test_client.delete("/skills/123e4567-e89b-12d3-a456-426614174000")
        assert response.status_code == 404
