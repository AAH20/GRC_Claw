"""Tests for predictive hiring endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient


class TestPredictionEndpoints:
    """Test predictive hiring endpoints."""

    def test_predict_hiring(self, test_client: TestClient) -> None:
        """Test prediction endpoint."""
        payload = {
            "candidate_id": "cand-123",
            "role": "Software Engineer",
            "features": {
                "years_experience": 5.0,
                "education_level": "bachelor",
                "skills_match_score": 0.85,
                "interview_scores": [0.8, 0.9, 0.85],
                "cultural_fit_score": 0.9,
                "referral_boost": True,
                "certifications": ["AWS"],
            },
        }
        response = test_client.post("/api/v1/prediction/analyze", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "prediction" in data
        assert "recommendations" in data
        assert data["prediction"]["candidate_id"] == "cand-123"

    def test_get_prediction_outcomes(self, test_client: TestClient) -> None:
        """Test prediction outcomes endpoint."""
        response = test_client.get("/api/v1/prediction/outcomes")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert "strong_hire" in data
        assert "no_hire" in data

