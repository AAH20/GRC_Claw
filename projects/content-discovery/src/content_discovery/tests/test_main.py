"""Tests for the main application factory."""

from __future__ import annotations

from fastapi.testclient import TestClient

from content_discovery.config import Settings
from content_discovery.main import create_app


def test_create_app_returns_fastapi() -> None:
    """Test that create_app returns a FastAPI instance."""
    from fastapi import FastAPI

    app = create_app()
    assert isinstance(app, FastAPI)


def test_create_app_with_custom_settings() -> None:
    """Test create_app with custom settings."""
    settings = Settings(
        app_name="custom-app",
        version="1.2.3",
        debug=True,
    )
    app = create_app(settings=settings)
    assert app.title == "custom-app"
    assert app.version == "1.2.3"


def test_app_has_routes() -> None:
    """Test that app has expected routes."""
    app = create_app()
    routes = [route.path for route in app.routes]

    assert "/health" in routes
    assert "/ready" in routes
    assert "/api/v1/search" in routes
    assert "/api/v1/recommendations" in routes
    assert "/api/v1/trends" in routes


def test_app_cors_middleware() -> None:
    """Test that CORS middleware is configured."""
    app = create_app()
    middleware_classes = [m.cls.__name__ for m in app.user_middleware]
    assert "CORSMiddleware" in middleware_classes


def test_app_exception_handler() -> None:
    """Test that exception handler is configured."""
    app = create_app()
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
