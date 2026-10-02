"""E2E tests for the full Analytics & Reporting workflow.

Tests the complete lifecycle of analytics and reporting through the
Analytics API: attribution analysis, model comparison, revenue forecasting,
and churn prediction.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient

from conftest import (
    assert_health_check,
    assert_response_error,
    assert_response_success,
    generate_unique_id,
)


class TestAnalyticsReportingE2E:
    """End-to-end test suite for analytics and reporting workflow."""

    def test_health_check(self, analytics_client: TestClient) -> None:
        """Verify the Analytics service is healthy.

        Args:
            analytics_client: Test client for the Analytics API.
        """
        assert_health_check(analytics_client)

    def test_attribution_analysis_full_workflow(
        self, analytics_client: TestClient
    ) -> None:
        """Test the complete attribution analysis workflow.

        Steps:
            1. List available attribution models.
            2. Run attribution analysis with default model.
            3. Run attribution with specific model.
            4. Compare all attribution models.

        Args:
            analytics_client: Test client for the Analytics API.
        """
        # Step 1: List models
        models_response = analytics_client.get("/api/v1/attribution/models")
        models = assert_response_success(models_response)
        assert "models" in models
        assert len(models["models"]) > 0
        assert "default" in models

        # Step 2: Run attribution with default model
        run_response = analytics_client.post("/api/v1/attribution/run")
        result = assert_response_success(run_response)

        assert "model" in result
        assert "period" in result
        assert "summary" in result
        assert "channel_attributions" in result
        assert "channel_percentages" in result

        summary = result["summary"]
        assert "total_revenue" in summary
        assert "journey_count" in summary
        assert "converted_journeys" in summary

        # Step 3: Run attribution with specific model
        specific_response = analytics_client.post(
            "/api/v1/attribution/run?model=first_touch"
        )
        specific_result = assert_response_success(specific_response)
        assert specific_result["model"] == "first_touch"

        # Step 4: Compare models
        compare_response = analytics_client.post("/api/v1/attribution/compare")
        comparison = assert_response_success(compare_response)
        assert "period" in comparison
        assert "models" in comparison
        assert len(comparison["models"]) > 0

    def test_attribution_with_date_range(
        self, analytics_client: TestClient
    ) -> None:
        """Test attribution analysis with custom date range.

        Args:
            analytics_client: Test client for the Analytics API.
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=60)

        response = analytics_client.post(
            f"/api/v1/attribution/run?start_date={start_date.isoformat()}&end_date={end_date.isoformat()}"
        )
        result = assert_response_success(response)

        assert result["period"]["start"] is not None
        assert result["period"]["end"] is not None
        assert result["summary"]["journey_count"] > 0

    def test_revenue_forecasting_workflow(
        self, analytics_client: TestClient
    ) -> None:
        """Test the revenue forecasting workflow.

        Args:
            analytics_client: Test client for the Analytics API.
        """
        response = analytics_client.post(
            "/api/v1/forecasting/revenue?horizon_days=30"
        )
        result = assert_response_success(response)

        assert "model_type" in result
        assert "horizon_days" in result
        assert result["horizon_days"] == 30
        assert "metrics" in result
        assert "forecast" in result
        assert "summary" in result

        forecast = result["forecast"]
        assert len(forecast) == 30

        for point in forecast:
            assert "date" in point
            assert "predicted_value" in point
            assert "lower_bound" in point
            assert "upper_bound" in point

        summary = result["summary"]
        assert "total_predicted" in summary
        assert "average_daily" in summary

    def test_churn_prediction_workflow(
        self, analytics_client: TestClient
    ) -> None:
        """Test the churn prediction workflow.

        Args:
            analytics_client: Test client for the Analytics API.
        """
        response = analytics_client.post("/api/v1/forecasting/churn")
        result = assert_response_success(response)

        assert "model_metrics" in result
        assert "predictions" in result
        assert "summary" in result

        predictions = result["predictions"]
        assert len(predictions) > 0

        for pred in predictions:
            assert "user_id" in pred
            assert "churn_probability" in pred
            assert "risk_tier" in pred
            assert "top_factors" in pred

        summary = result["summary"]
        assert "total_users" in summary
        assert "high_risk" in summary
        assert "medium_risk" in summary
        assert "low_risk" in summary

    def test_forecast_models_list(self, analytics_client: TestClient) -> None:
        """Test listing available forecasting models.

        Args:
            analytics_client: Test client for the Analytics API.
        """
        response = analytics_client.get("/api/v1/forecasting/models")
        result = assert_response_success(response)

        assert "models" in result
        assert len(result["models"]) > 0

        for model in result["models"]:
            assert "id" in model
            assert "name" in model
            assert "description" in model

    def test_attribution_model_comparison(
        self, analytics_client: TestClient
    ) -> None:
        """Test comparing different attribution models.

        Args:
            analytics_client: Test client for the Analytics API.
        """
        response = analytics_client.post("/api/v1/attribution/compare")
        result = assert_response_success(response)

        assert "models" in result
        models = result["models"]

        # Verify each model has expected fields
        for model_name, model_data in models.items():
            assert "channel_totals" in model_data
            assert "channel_percentages" in model_data
            assert "total_revenue" in model_data

    def test_revenue_forecast_different_models(
        self, analytics_client: TestClient
    ) -> None:
        """Test revenue forecasting with different model types.

        Args:
            analytics_client: Test client for the Analytics API.
        """
        model_types = ["linear_regression", "random_forest", "gradient_boosting"]
        for model_type in model_types:
            response = analytics_client.post(
                f"/api/v1/forecasting/revenue?horizon_days=14&model_type={model_type}"
            )
            result = assert_response_success(response)
            assert result["model_type"] == model_type
            assert len(result["forecast"]) == 14

    def test_full_analytics_integration(
        self, analytics_client: TestClient
    ) -> None:
        """Test the full analytics integration workflow.

        Steps:
            1. Run attribution analysis.
            2. Compare attribution models.
            3. Generate revenue forecast.
            4. Predict churn.

        Args:
            analytics_client: Test client for the Analytics API.
        """
        # Step 1: Attribution
        attribution_response = analytics_client.post("/api/v1/attribution/run")
        attribution = assert_response_success(attribution_response)
        assert attribution["summary"]["journey_count"] > 0

        # Step 2: Model comparison
        compare_response = analytics_client.post("/api/v1/attribution/compare")
        comparison = assert_response_success(compare_response)
        assert len(comparison["models"]) > 0

        # Step 3: Revenue forecast
        forecast_response = analytics_client.post(
            "/api/v1/forecasting/revenue?horizon_days=30"
        )
        forecast = assert_response_success(forecast_response)
        assert len(forecast["forecast"]) == 30

        # Step 4: Churn prediction
        churn_response = analytics_client.post("/api/v1/forecasting/churn")
        churn = assert_response_success(churn_response)
        assert len(churn["predictions"]) > 0
        assert churn["summary"]["total_users"] > 0
