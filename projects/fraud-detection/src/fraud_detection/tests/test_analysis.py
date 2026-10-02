"""Analysis endpoint tests."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_analyze_transaction(client: TestClient, sample_transaction: dict) -> None:
    """Test single transaction analysis.

    Args:
        client: Test client fixture.
        sample_transaction: Sample transaction fixture.
    """
    response = client.post(
        "/v1/analyze",
        json=sample_transaction,
        headers={"X-API-Key": "dev-api-key-change-in-production"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "report_id" in data
    assert "risk_score" in data
    assert "final_decision" in data


def test_analyze_batch(client: TestClient, sample_transaction: dict) -> None:
    """Test batch transaction analysis.

    Args:
        client: Test client fixture.
        sample_transaction: Sample transaction fixture.
    """
    response = client.post(
        "/v1/analyze/batch",
        json={"transactions": [sample_transaction, sample_transaction]},
        headers={"X-API-Key": "dev-api-key-change-in-production"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "batch_id" in data
    assert "reports" in data
    assert len(data["reports"]) == 2


def test_detect_patterns(client: TestClient, sample_transaction: dict) -> None:
    """Test pattern detection endpoint.

    Args:
        client: Test client fixture.
        sample_transaction: Sample transaction fixture.
    """
    response = client.post(
        "/v1/patterns/detect",
        json=sample_transaction,
        headers={"X-API-Key": "dev-api-key-change-in-production"},
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_detect_anomalies(client: TestClient, sample_transaction: dict) -> None:
    """Test anomaly detection endpoint.

    Args:
        client: Test client fixture.
        sample_transaction: Sample transaction fixture.
    """
    response = client.post(
        "/v1/anomalies/detect",
        json=sample_transaction,
        headers={"X-API-Key": "dev-api-key-change-in-production"},
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_score_risk(client: TestClient, sample_transaction: dict) -> None:
    """Test risk scoring endpoint.

    Args:
        client: Test client fixture.
        sample_transaction: Sample transaction fixture.
    """
    response = client.post(
        "/v1/risk/score",
        json=sample_transaction,
        headers={"X-API-Key": "dev-api-key-change-in-production"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "overall_score" in data
    assert "risk_level" in data
