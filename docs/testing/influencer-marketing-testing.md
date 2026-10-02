# Influencer Marketing — Testing Guide

> **Project:** Influencer Marketing  
> **Version:** 1.0.0  
> **Last Updated:** 2026-10-02  
> **Owner:** GRC Claw QA Team  
> **Focus Area:** influencer discovery, campaign management, ROI tracking

---

## Table of Contents

1. [Overview](#overview)
2. [Test Strategy](#test-strategy)
3. [Unit Tests](#unit-tests)
4. [Integration Tests](#integration-tests)
5. [End-to-End Tests](#end-to-end-tests)
6. [Performance Tests](#performance-tests)
7. [Security Tests](#security-tests)
8. [Test Data Management](#test-data-management)
9. [CI/CD Integration](#cicd-integration)
10. [Test Coverage Metrics](#test-coverage-metrics)
11. [Defect Management](#defect-management)
12. [Appendices](#appendices)

---

## 1. Overview

### 1.1 Purpose

This document defines the comprehensive testing strategy for the **Influencer Marketing** module within the GRC Claw platform. It establishes testing standards, methodologies, and acceptance criteria to ensure the module meets functional, performance, security, and reliability requirements.

### 1.2 Scope

| Aspect | Details |
|--------|---------|
| **Module** | Influencer Marketing |
| **Platform** | GRC Claw |
| **Test Levels** | Unit, Integration, E2E, Performance, Security |
| **Automation Target** | >= 90% code coverage |
| **Execution Frequency** | Every commit (unit), Every PR (integration), Nightly (E2E), Weekly (performance), Per-release (security) |

### 1.3 Testing Focus Areas

The Influencer Marketing module specializes in **influencer discovery, campaign management, ROI tracking**. Testing priorities include:

- **Functional correctness** — Core algorithms and business logic
- **Data integrity** — Input validation, transformation accuracy, output consistency
- **Integration reliability** — API contracts, event-driven communication, third-party connectors
- **Performance under load** — Scalability, latency, throughput
- **Security posture** — Authentication, authorization, data protection, injection resistance

---

## 2. Test Strategy

### 2.1 Testing Pyramid

```
         /\
        /  \        E2E Tests (5%)
       /----\
      /      \      Integration Tests (25%)
     /--------\
    /          \    Unit Tests (70%)
   /------------\
```

### 2.2 Test Environment Matrix

| Environment | Purpose | Data | Trigger |
|-------------|---------|------|---------|
| **Local** | Developer testing | Synthetic/minimal | Pre-commit |
| **CI** | Automated validation | Seeded fixtures | Every push |
| **Staging** | Pre-production validation | Anonymized production-like | PR merge |
| **Production** | Smoke and monitoring | Live (read-only) | Post-deploy |

### 2.3 Tooling Stack

| Layer | Tools |
|-------|-------|
| **Unit Testing** | Jest (TS/JS), pytest (Python), JUnit (Java) |
| **Integration Testing** | Supertest, Testcontainers, Pact (contract testing) |
| **E2E Testing** | Playwright, Cypress |
| **Performance Testing** | k6, Artillery, Locust |
| **Security Testing** | OWASP ZAP, Snyk, Trivy, Semgrep |
| **Coverage** | Istanbul/nyc, Coverage.py, JaCoCo |
| **Mocking** | MSW, Sinon.js, unittest.mock, WireMock |

---

## 3. Unit Tests

### 3.1 Test Structure

```
tests/unit/
├── influencer-marketing/
│   ├── __init__.py
│   ├── test_core_logic.py
│   ├── test_data_models.py
│   ├── test_validators.py
│   ├── test_transformers.py
│   ├── test_config.py
│   └── test_exceptions.py
├── conftest.py
└── fixtures/
    ├── sample_inputs.json
    ├── expected_outputs.json
    └── mock_responses/
```

### 3.2 Core Logic Tests

```python
# tests/unit/influencer-marketing/test_core_logic.py

import pytest
from unittest.mock import Mock, patch
from grc_claw.influencer_marketing.core import InfluencerMarketingEngine


class TestInfluencerMarketingEngine:
    """Unit tests for core Influencer Marketing business logic."""

    @pytest.fixture
    def engine(self):
        """Initialize engine with test configuration."""
        config = {
            "environment": "testing",
            "max_retries": 3,
            "timeout_ms": 5000,
            "log_level": "DEBUG",
        }
        return InfluencerMarketingEngine(config)

    @pytest.fixture
    def sample_input(self):
        """Provide valid sample input data."""
        return {
            "id": "test-001",
            "name": "Test Record",
            "status": "active",
            "metadata": {"source": "unit_test"},
        }

    def test_engine_initialization(self, engine):
        """Verify engine initializes with valid configuration."""
        assert engine is not None
        assert engine.config["environment"] == "testing"
        assert engine.is_healthy() is True

    def test_engine_initialization_invalid_config(self):
        """Verify engine rejects invalid configuration."""
        with pytest.raises(ValueError, match="Invalid configuration"):
            InfluencerMarketingEngine({})

    def test_process_valid_input(self, engine, sample_input):
        """Verify processing of valid input data."""
        result = engine.process(sample_input)
        assert result is not None
        assert result["id"] == "test-001"
        assert result["status"] == "processed"
        assert "timestamp" in result

    def test_process_empty_input(self, engine):
        """Verify handling of empty input."""
        with pytest.raises(ValueError, match="Input cannot be empty"):
            engine.process({})

    def test_process_none_input(self, engine):
        """Verify handling of None input."""
        with pytest.raises(TypeError, match="Input cannot be None"):
            engine.process(None)

    def test_process_malformed_input(self, engine):
        """Verify handling of malformed input data."""
        malformed = {"invalid_key": 123, "nested": {"corrupted": True}}
        result = engine.process(malformed)
        assert result["status"] == "partial"
        assert "warnings" in result

    def test_process_large_input(self, engine):
        """Verify handling of large input payloads."""
        large_input = {
            "id": "test-large",
            "items": [{"idx": i, "data": "x" * 1000} for i in range(10000)],
        }
        result = engine.process(large_input)
        assert result["status"] == "processed"
        assert result["item_count"] == 10000
```

#### 3.2.2 Data Model Tests

```python
# tests/unit/influencer-marketing/test_data_models.py

import pytest
from datetime import datetime
from grc_claw.influencer_marketing.models import (
    InfluencerMarketingInput,
    InfluencerMarketingOutput,
    InfluencerMarketingStatus,
)


class TestInfluencerMarketingInput:
    """Unit tests for input data model."""

    def test_valid_input_creation(self):
        """Verify valid input model instantiation."""
        data = {"id": "test-001", "name": "Test", "value": 42}
        model = InfluencerMarketingInput(**data)
        assert model.id == "test-001"
        assert model.name == "Test"
        assert model.value == 42

    def test_input_validation_required_fields(self):
        """Verify required field validation."""
        with pytest.raises(ValueError):
            InfluencerMarketingInput(id="", name="", value=None)

    def test_input_serialization(self):
        """Verify input model serialization."""
        model = InfluencerMarketingInput(id="test-001", name="Test", value=42)
        serialized = model.to_dict()
        assert isinstance(serialized, dict)
        assert serialized["id"] == "test-001"

    def test_input_deserialization(self):
        """Verify input model deserialization."""
        raw = {"id": "test-001", "name": "Test", "value": 42}
        model = InfluencerMarketingInput.from_dict(raw)
        assert model.id == "test-001"


class TestInfluencerMarketingOutput:
    """Unit tests for output data model."""

    def test_output_creation(self):
        """Verify output model instantiation."""
        model = InfluencerMarketingOutput(
            id="test-001",
            status=InfluencerMarketingStatus.SUCCESS,
            result={"score": 0.95},
        )
        assert model.status == InfluencerMarketingStatus.SUCCESS

    def test_output_with_errors(self):
        """Verify output model with error information."""
        model = InfluencerMarketingOutput(
            id="test-001",
            status=InfluencerMarketingStatus.PARTIAL,
            result={},
            errors=[{"code": "WARN_001", "message": "Partial data"}],
        )
        assert len(model.errors) == 1
```

#### 3.2.3 Validator Tests

```python
# tests/unit/influencer-marketing/test_validators.py

import pytest
from grc_claw.influencer_marketing.validators import InfluencerMarketingValidator


class TestInfluencerMarketingValidator:
    """Unit tests for input/output validators."""

    @pytest.fixture
    def validator(self):
        return InfluencerMarketingValidator()

    @pytest.mark.parametrize("input_data,expected_valid", [
        ({"id": "valid-001", "name": "Test"}, True),
        ({"id": "", "name": "Test"}, False),
        ({"id": "valid-002", "name": ""}, False),
        ({"id": None, "name": "Test"}, False),
        ({}, False),
    ])
    def test_input_validation(self, validator, input_data, expected_valid):
        """Verify input validation with various inputs."""
        result = validator.validate_input(input_data)
        assert result.is_valid == expected_valid

    def test_validation_error_messages(self, validator):
        """Verify descriptive error messages."""
        result = validator.validate_input({"id": ""})
        assert not result.is_valid
        assert len(result.errors) > 0
        assert any("id" in err.field for err in result.errors)

    def test_sanitization(self, validator):
        """Verify input sanitization."""
        dirty = {"name": "  Test  ", "tags": ["  a  ", "b  "]}
        clean = validator.sanitize(dirty)
        assert clean["name"] == "Test"
        assert clean["tags"] == ["a", "b"]
```

### 3.3 Unit Test Coverage Requirements

| Component | Minimum Coverage | Target Coverage |
|-----------|-----------------|-----------------|
| Core business logic | 85% | 95% |
| Data models | 90% | 98% |
| Validators | 90% | 98% |
| Error handling | 80% | 95% |
| Configuration | 75% | 90% |
| Utility functions | 80% | 95% |

---

## 4. Integration Tests

### 4.1 Test Structure

```
tests/integration/
├── influencer-marketing/
│   ├── __init__.py
│   ├── test_api_endpoints.py
│   ├── test_database_operations.py
│   ├── test_event_handlers.py
│   ├── test_external_services.py
│   ├── test_cache_layer.py
│   ├── test_message_queue.py
│   └── test_auth_flow.py
├── conftest.py
├── docker-compose.test.yml
└── fixtures/
    ├── database_seed.sql
    ├── api_contracts/
    └── event_schemas/
```

### 4.2 API Endpoint Tests

```python
# tests/integration/influencer-marketing/test_api_endpoints.py

import pytest
import httpx
from fastapi.testclient import TestClient
from grc_claw.influencer_marketing.api import create_app


@pytest.fixture(scope="module")
def test_client():
    """Create test client with test configuration."""
    app = create_app(config={"environment": "testing", "database": "test_db"})
    with TestClient(app) as client:
        yield client


class TestInfluencerMarketingAPI:
    """Integration tests for Influencer Marketing API endpoints."""

    def test_health_check(self, test_client):
        """Verify health endpoint returns 200."""
        response = test_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data

    def test_create_resource(self, test_client):
        """Verify resource creation endpoint."""
        payload = {
            "name": "Integration Test Resource",
            "description": "Created during integration testing",
            "tags": ["test", "integration"],
        }
        response = test_client.post("/api/v1/influencer/marketing", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == payload["name"]
        assert "id" in data
        assert "created_at" in data

    def test_get_resource(self, test_client):
        """Verify resource retrieval endpoint."""
        create_resp = test_client.post("/api/v1/influencer/marketing", json={
            "name": "Get Test",
        })
        resource_id = create_resp.json()["id"]

        response = test_client.get(f"/api/v1/influencer/marketing/{resource_id}")
        assert response.status_code == 200
        assert response.json()["id"] == resource_id

    def test_update_resource(self, test_client):
        """Verify resource update endpoint."""
        create_resp = test_client.post("/api/v1/influencer/marketing", json={
            "name": "Update Test",
        })
        resource_id = create_resp.json()["id"]

        response = test_client.put(
            f"/api/v1/influencer/marketing/{resource_id}",
            json={"name": "Updated Name"},
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Updated Name"

    def test_delete_resource(self, test_client):
        """Verify resource deletion endpoint."""
        create_resp = test_client.post("/api/v1/influencer/marketing", json={
            "name": "Delete Test",
        })
        resource_id = create_resp.json()["id"]

        response = test_client.delete(f"/api/v1/influencer/marketing/{resource_id}")
        assert response.status_code == 204

        get_resp = test_client.get(f"/api/v1/influencer/marketing/{resource_id}")
        assert get_resp.status_code == 404

    def test_list_resources_pagination(self, test_client):
        """Verify paginated list endpoint."""
        for i in range(25):
            test_client.post("/api/v1/influencer/marketing", json={
                "name": f"Pagination Test {i}",
            })

        response = test_client.get("/api/v1/influencer/marketing?page=1&page_size=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 10
        assert data["page"] == 1
        assert data["total"] >= 25

        response = test_client.get("/api/v1/influencer/marketing?page=2&page_size=10")
        data = response.json()
        assert data["page"] == 2

    def test_invalid_payload_handling(self, test_client):
        """Verify API handles invalid payloads gracefully."""
        response = test_client.post(
            "/api/v1/influencer/marketing",
            json={"invalid_field": "value"},
        )
        assert response.status_code == 422
        assert "detail" in response.json()

    def test_rate_limiting(self, test_client):
        """Verify rate limiting is enforced."""
        responses = []
        for _ in range(150):
            resp = test_client.get("/health")
            responses.append(resp.status_code)

        assert 429 in responses, "Rate limiting should return 429"
```

### 4.3 Database Integration Tests

```python
# tests/integration/influencer-marketing/test_database_operations.py

import pytest
import asyncpg
from grc_claw.influencer_marketing.repository import InfluencerMarketingRepository


@pytest.fixture(scope="module")
async def db_pool():
    """Create test database connection pool."""
    pool = await asyncpg.create_pool(
        host="localhost",
        port=5432,
        database="test_grc_claw",
        user="test_user",
        password="test_pass",
        min_size=1,
        max_size=5,
    )
    yield pool
    await pool.close()


@pytest.fixture
async def repository(db_pool):
    """Create repository with test database."""
    repo = InfluencerMarketingRepository(db_pool)
    yield repo
    await db_pool.execute("TRUNCATE TABLE influencer_marketing_records CASCADE")


class TestInfluencerMarketingRepository:
    """Integration tests for database operations."""

    @pytest.mark.asyncio
    async def test_insert_and_retrieve(self, repository):
        """Verify insert and retrieve round-trip."""
        record = {
            "name": "DB Test Record",
            "data": {"key": "value"},
            "status": "active",
        }
        created = await repository.create(record)
        assert created["id"] is not None

        retrieved = await repository.get_by_id(created["id"])
        assert retrieved["name"] == record["name"]

    @pytest.mark.asyncio
    async def test_bulk_insert(self, repository):
        """Verify bulk insert operation."""
        records = [
            {"name": f"Bulk {i}", "status": "active"}
            for i in range(100)
        ]
        result = await repository.bulk_create(records)
        assert result["inserted"] == 100

    @pytest.mark.asyncio
    async def test_transaction_rollback(self, repository):
        """Verify transaction rollback on error."""
        with pytest.raises(Exception):
            async with repository.transaction() as tx:
                await tx.execute(
                    "INSERT INTO influencer_marketing_records (name) VALUES ($1)",
                    "Rollback Test",
                )
                raise Exception("Force rollback")

        result = await repository.find_by_name("Rollback Test")
        assert result is None

    @pytest.mark.asyncio
    async def test_concurrent_access(self, repository):
        """Verify concurrent read/write safety."""
        import asyncio

        async def write_record(idx):
            return await repository.create({"name": f"Concurrent {idx}"})

        tasks = [write_record(i) for i in range(20)]
        results = await asyncio.gather(*tasks)
        assert len(results) == 20
        assert len(set(r["id"] for r in results)) == 20
```

### 4.4 Event Handler Tests

```python
# tests/integration/influencer-marketing/test_event_handlers.py

import pytest
import json
from unittest.mock import AsyncMock
from grc_claw.influencer_marketing.events import InfluencerMarketingEventHandler


class TestInfluencerMarketingEventHandler:
    """Integration tests for event-driven handlers."""

    @pytest.fixture
    def handler(self):
        return InfluencerMarketingEventHandler()

    @pytest.fixture
    def event_bus(self):
        return AsyncMock()

    async def test_handle_create_event(self, handler, event_bus):
        """Verify create event processing."""
        event = {
            "type": "INFLUENCER_MARKETING_CREATED",
            "payload": {"id": "evt-001", "name": "Test"},
            "timestamp": "2026-10-02T00:00:00Z",
        }
        result = await handler.handle(event, event_bus)
        assert result["status"] == "processed"
        event_bus.publish.assert_called_once()

    async def test_handle_update_event(self, handler, event_bus):
        """Verify update event processing."""
        event = {
            "type": "INFLUENCER_MARKETING_UPDATED",
            "payload": {"id": "evt-001", "changes": {"name": "New"}},
        }
        result = await handler.handle(event, event_bus)
        assert result["status"] == "processed"

    async def test_handle_delete_event(self, handler, event_bus):
        """Verify delete event processing."""
        event = {
            "type": "INFLUENCER_MARKETING_DELETED",
            "payload": {"id": "evt-001"},
        }
        result = await handler.handle(event, event_bus)
        assert result["status"] == "processed"

    async def test_handle_invalid_event_type(self, handler, event_bus):
        """Verify graceful handling of unknown event types."""
        event = {
            "type": "UNKNOWN_EVENT",
            "payload": {},
        }
        result = await handler.handle(event, event_bus)
        assert result["status"] == "ignored"

    async def test_event_ordering(self, handler, event_bus):
        """Verify events are processed in order."""
        events = [
            {"type": "CREATED", "payload": {"seq": i}}
            for i in range(10)
        ]
        for event in events:
            await handler.handle(event, event_bus)

        call_args = [call[0][0] for call in event_bus.publish.call_args_list]
        assert len(call_args) == 10
```

### 4.5 External Service Integration Tests

```python
# tests/integration/influencer-marketing/test_external_services.py

import pytest
from unittest.mock import patch, Mock
from grc_claw.influencer_marketing.clients import ExternalServiceClient


class TestExternalServiceClient:
    """Integration tests for external service connectors."""

    @pytest.fixture
    def client(self):
        return ExternalServiceClient(
            base_url="https://api.test-service.example.com",
            api_key="test-key",
            timeout=5,
        )

    @patch("grc_claw.influencer_marketing.clients.httpx.AsyncClient")
    async def test_successful_api_call(self, mock_httpx):
        """Verify successful external API call."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "ok", "data": {}}
        mock_httpx.return_value.__aenter__.return_value.get.return_value = mock_response

        result = await client.fetch_data("/endpoint")
        assert result["status"] == "ok"

    @patch("grc_claw.influencer_marketing.clients.httpx.AsyncClient")
    async def test_retry_on_failure(self, mock_httpx):
        """Verify retry logic on transient failures."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "ok"}

        mock_httpx.return_value.__aenter__.return_value.get.side_effect = [
            Exception("Timeout"),
            Exception("Timeout"),
            mock_response,
        ]

        result = await client.fetch_data("/endpoint", retries=3)
        assert result["status"] == "ok"

    @patch("grc_claw.influencer_marketing.clients.httpx.AsyncClient")
    async def test_circuit_breaker(self, mock_httpx):
        """Verify circuit breaker opens after repeated failures."""
        mock_httpx.return_value.__aenter__.return_value.get.side_effect = Exception("Service down")

        for _ in range(5):
            with pytest.raises(Exception):
                await client.fetch_data("/endpoint")

        with pytest.raises(Exception, match="Circuit breaker open"):
            await client.fetch_data("/endpoint")
```

---

## 5. End-to-End Tests

### 5.1 Test Structure

```
tests/e2e/
├── influencer-marketing/
│   ├── __init__.py
│   ├── test_full_workflow.py
│   ├── test_user_journeys.py
│   ├── test_admin_workflows.py
│   ├── test_data_migration.py
│   └── test_disaster_recovery.py
├── conftest.py
├── playwright.config.ts
└── fixtures/
    ├── users.json
    ├── workflows/
    └── reports/
```

### 5.2 Full Workflow E2E Tests

```python
# tests/e2e/influencer-marketing/test_full_workflow.py

import pytest
import time
from playwright.sync_api import Page, expect


@pytest.fixture(autouse=True)
def setup_test_environment(page: Page):
    """Setup test environment before each E2E test."""
    page.goto("https://staging.grc-claw.example.com")
    page.fill('[data-testid="email"]', "test@example.com")
    page.fill('[data-testid="password"]', "TestPassword123!")
    page.click('[data-testid="login-button"]')
    page.wait_for_url("/dashboard")
    yield
    page.click('[data-testid="user-menu"]')
    page.click('[data-testid="logout"]')


class TestInfluencerMarketingFullWorkflow:
    """End-to-end tests for complete Influencer Marketing workflows."""

    def test_complete_creation_workflow(self, page: Page):
        """Verify complete resource creation workflow via UI."""
        page.click('[data-testid="nav-influencer-marketing"]')
        page.wait_for_selector('[data-testid="influencer-marketing-dashboard"]')

        page.click('[data-testid="create-new-button"]')
        page.wait_for_selector('[data-testid="create-form"]')

        page.fill('[data-testid="name-input"]', "E2E Test Resource")
        page.fill('[data-testid="description-input"]', "Created by E2E test")
        page.select_option('[data-testid="category-select"]', "test-category")
        page.check('[data-testid="active-checkbox"]')

        page.click('[data-testid="submit-button"]')

        expect(page.locator('[data-testid="success-toast"]')).to_be_visible()
        page.wait_for_selector('[data-testid="resource-detail"]')

        expect(page.locator('[data-testid="detail-name"]')).to_have_text("E2E Test Resource")

    def test_search_and_filter_workflow(self, page: Page):
        """Verify search and filter functionality."""
        page.click('[data-testid="nav-influencer-marketing"]')
        page.wait_for_selector('[data-testid="influencer-marketing-dashboard"]')

        page.fill('[data-testid="search-input"]', "test query")
        page.press('[data-testid="search-input"]', "Enter")
        page.wait_for_selector('[data-testid="search-results"]')

        page.click('[data-testid="filter-status"]')
        page.click('[data-testid="filter-status-active"]')
        page.wait_for_timeout(500)

        results = page.locator('[data-testid="result-item"]')
        assert results.count() > 0

    def test_bulk_operations_workflow(self, page: Page):
        """Verify bulk operations."""
        page.click('[data-testid="nav-influencer-marketing"]')
        page.wait_for_selector('[data-testid="influencer-marketing-dashboard"]')

        page.check('[data-testid="select-all-checkbox"]')
        page.click('[data-testid="bulk-actions-dropdown"]')
        page.click('[data-testid="bulk-delete"]')

        page.click('[data-testid="confirm-delete-button"]')
        expect(page.locator('[data-testid="success-toast"]')).to_be_visible()

    def test_export_workflow(self, page: Page):
        """Verify data export functionality."""
        page.click('[data-testid="nav-influencer-marketing"]')
        page.wait_for_selector('[data-testid="influencer-marketing-dashboard"]')

        with page.expect_download() as download_info:
            page.click('[data-testid="export-button"]')
        download = download_info.value

        assert download.suggested_filename.endswith(".csv")

    def test_real_time_updates(self, page: Page):
        """Verify real-time update propagation."""
        page.click('[data-testid="nav-influencer-marketing"]')
        page.wait_for_selector('[data-testid="influencer-marketing-dashboard"]')

        page.click('[data-testid="result-item"]')
        page.wait_for_selector('[data-testid="resource-detail"]')

        page.wait_for_selector('[data-testid="update-notification"]', timeout=10000)
        expect(page.locator('[data-testid="update-notification"]')).to_be_visible()
```

### 5.3 User Journey E2E Tests

```python
# tests/e2e/influencer-marketing/test_user_journeys.py

import pytest
from playwright.sync_api import Page, expect


class TestInfluencerMarketingUserJourneys:
    """End-to-end tests for common user journeys."""

    def test_new_user_onboarding_journey(self, page: Page):
        """Verify new user onboarding flow."""
        page.goto("https://staging.grc-claw.example.com/signup")
        page.fill('[data-testid="signup-email"]', "newuser_test@example.com")
        page.fill('[data-testid="signup-password"]', "SecurePass123!")
        page.click('[data-testid="signup-button"]')

        page.wait_for_selector('[data-testid="onboarding-profile"]')
        page.fill('[data-testid="company-name"]', "Test Company")
        page.select_option('[data-testid="industry-select"]', "technology")
        page.click('[data-testid="continue-button"]')

        page.wait_for_selector('[data-testid="onboarding-usecase"]')
        page.click('[data-testid="use-case-influencer-marketing"]')
        page.click('[data-testid="continue-button"]')

        page.wait_for_url("/dashboard")
        expect(page.locator('[data-testid="welcome-banner"]')).to_be_visible()

    def test_power_user_advanced_workflow(self, page: Page):
        """Verify advanced user workflow with complex operations."""
        page.goto("https://staging.grc-claw.example.com/login")
        page.fill('[data-testid="email"]', "poweruser_test@example.com")
        page.fill('[data-testid="password"]', "TestPassword123!")
        page.click('[data-testid="login-button"]')

        page.click('[data-testid="nav-influencer-marketing"]')
        page.click('[data-testid="advanced-tab"]')

        page.click('[data-testid="add-rule-button"]')
        page.fill('[data-testid="rule-name"]', "Complex Rule")
        page.select_option('[data-testid="rule-condition"]', "field_equals")
        page.fill('[data-testid="rule-value"]', "test_value")
        page.click('[data-testid="save-rule"]')

        expect(page.locator('[data-testid="rule-list-item"]')).to_contain_text("Complex Rule")

    def test_admin_configuration_journey(self, page: Page):
        """Verify admin configuration workflow."""
        page.goto("https://staging.grc-claw.example.com/login")
        page.fill('[data-testid="email"]', "admin_test@example.com")
        page.fill('[data-testid="password"]', "AdminPass123!")
        page.click('[data-testid="login-button"]')

        page.click('[data-testid="admin-menu"]')
        page.click('[data-testid="nav-influencer-marketing-settings"]')

        page.fill('[data-testid="max-items-input"]', "500")
        page.select_option('[data-testid="default-view-select"]', "grid")
        page.check('[data-testid="enable-notifications"]')

        page.click('[data-testid="save-settings"]')
        expect(page.locator('[data-testid="settings-saved-toast"]')).to_be_visible()

        page.reload()
        expect(page.locator('[data-testid="max-items-input"]')).to_have_value("500")
```

### 5.4 Cross-Browser E2E Matrix

| Browser | Versions | Priority |
|---------|----------|----------|
| Chrome | Latest, Latest-1 | P0 |
| Firefox | Latest, Latest-1 | P0 |
| Safari | Latest, Latest-1 | P1 |
| Edge | Latest | P1 |
| Mobile Chrome | Latest | P2 |
| Mobile Safari | Latest | P2 |

---

## 6. Performance Tests

### 6.1 Test Structure

```
tests/performance/
├── influencer-marketing/
│   ├── __init__.py
│   ├── test_load.py
│   ├── test_stress.py
│   ├── test_spike.py
│   ├── test_endurance.py
│   ├── test_scalability.py
│   └── test_benchmarks.py
├── k6/
│   ├── load_test.js
│   ├── stress_test.js
│   └── spike_test.js
├── locust/
│   ├── locustfile.py
│   └── custom_clients.py
└── reports/
    ├── baseline/
    └── comparisons/
```

### 6.2 Load Testing

```javascript
// tests/performance/k6/load_test.js

import http from 'k6/http';
import { check, sleep, group } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';
import { randomIntBetween } from 'https://jslib.k6.io/k6-utils/1.2.0/index.js';

const errorRate = new Rate('errors');
const latencyTrend = new Trend('latency_p95');
const throughputCounter = new Counter('requests_total');

export const options = {
  stages: [
    { duration: '2m', target: 50 },
    { duration: '5m', target: 50 },
    { duration: '2m', target: 100 },
    { duration: '5m', target: 100 },
    { duration: '2m', target: 200 },
    { duration: '5m', target: 200 },
    { duration: '2m', target: 0 },
  ],
  thresholds: {
    http_req_duration: ['p(95)<500', 'p(99)<1000'],
    http_req_failed: ['rate<0.01'],
    errors: ['rate<0.05'],
  },
};

const BASE_URL = __ENV.BASE_URL || 'https://staging.grc-claw.example.com';

export default function () {
  group('Influencer Marketing API Load Test', () => {
    const listRes = http.get(`${BASE_URL}/api/v1/influencer/marketing?page=1&page_size=20`, {
      headers: { 'Authorization': `Bearer ${__ENV.API_TOKEN}` },
    });

    check(listRes, {
      'list status is 200': (r) => r.status === 200,
      'list response time < 500ms': (r) => r.timings.duration < 500,
      'list returns items': (r) => JSON.parse(r.body).items.length > 0,
    }) || errorRate.add(1);

    latencyTrend.add(listRes.timings.duration);
    throughputCounter.add(1);

    sleep(randomIntBetween(1, 3));

    const detailId = `test-${randomIntBetween(1, 1000)}`;
    const detailRes = http.get(`${BASE_URL}/api/v1/influencer/marketing/${detailId}`, {
      headers: { 'Authorization': `Bearer ${__ENV.API_TOKEN}` },
    });

    check(detailRes, {
      'detail status is 200 or 404': (r) => r.status === 200 || r.status === 404,
      'detail response time < 300ms': (r) => r.timings.duration < 300,
    }) || errorRate.add(1);

    sleep(randomIntBetween(1, 2));
  });
}
```

### 6.3 Stress Testing

```python
# tests/performance/influencer-marketing/test_stress.py

import asyncio
import time
import statistics
from concurrent.futures import ThreadPoolExecutor
import httpx


class TestInfluencerMarketingStress:
    """Stress tests to identify breaking points."""

    BASE_URL = "https://staging.grc-claw.example.com"
    CONCURRENCY_LEVELS = [50, 100, 200, 500, 1000]
    DURATION_SECONDS = 60

    async def _make_request(self, client: httpx.AsyncClient, endpoint: str):
        """Make a single request and record metrics."""
        start = time.monotonic()
        try:
            response = await client.get(f"{self.BASE_URL}{endpoint}")
            elapsed = (time.monotonic() - start) * 1000
            return {
                "status": response.status_code,
                "latency_ms": elapsed,
                "success": response.status_code < 500,
            }
        except Exception as e:
            elapsed = (time.monotonic() - start) * 1000
            return {
                "status": 0,
                "latency_ms": elapsed,
                "success": False,
                "error": str(e),
            }

    async def _run_load(self, concurrency: int, duration: int):
        """Run load at specified concurrency for duration."""
        results = []
        start_time = time.monotonic()

        async with httpx.AsyncClient(timeout=30.0) as client:
            while time.monotonic() - start_time < duration:
                tasks = [
                    self._make_request(client, "/api/v1/influencer/marketing?page=1")
                    for _ in range(concurrency)
                ]
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                results.extend([
                    r for r in batch_results
                    if isinstance(r, dict)
                ])

        return results

    @pytest.mark.asyncio
    @pytest.mark.parametrize("concurrency", CONCURRENCY_LEVELS)
    async def test_stress_concurrency_levels(self, concurrency):
        """Test system behavior at increasing concurrency levels."""
        results = await self._run_load(concurrency, self.DURATION_SECONDS)

        total = len(results)
        successful = sum(1 for r in results if r["success"])
        failed = total - successful
        latencies = [r["latency_ms"] for r in results]

        metrics = {
            "concurrency": concurrency,
            "total_requests": total,
            "successful": successful,
            "failed": failed,
            "success_rate": successful / total if total > 0 else 0,
            "avg_latency_ms": statistics.mean(latencies) if latencies else 0,
            "p50_latency_ms": statistics.median(latencies) if latencies else 0,
            "p95_latency_ms": sorted(latencies)[int(len(latencies) * 0.95)] if latencies else 0,
            "p99_latency_ms": sorted(latencies)[int(len(latencies) * 0.99)] if latencies else 0,
            "throughput_rps": total / self.DURATION_SECONDS,
        }

        assert metrics["success_rate"] > 0.95, (
            f"Success rate {metrics['success_rate']:.2%} below 95% at concurrency {concurrency}"
        )
        assert metrics["p95_latency_ms"] < 2000, (
            f"P95 latency {metrics['p95_latency_ms']:.0f}ms exceeds 2000ms at concurrency {concurrency}"
        )

        self._store_metrics(metrics)

    def _store_metrics(self, metrics: dict):
        """Store metrics for historical comparison."""
        import json
        from pathlib import Path

        report_path = Path(f"tests/performance/reports/influencer-marketing_stress.json")
        report_path.parent.mkdir(parents=True, exist_ok=True)

        existing = []
        if report_path.exists():
            existing = json.loads(report_path.read_text())

        existing.append({
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            **metrics,
        })

        report_path.write_text(json.dumps(existing, indent=2))
```

### 6.4 Performance Benchmarks

| Metric | Target | Warning | Critical |
|--------|--------|---------|----------|
| **API Response Time (p50)** | < 100ms | 100-300ms | > 300ms |
| **API Response Time (p95)** | < 500ms | 500-1000ms | > 1000ms |
| **API Response Time (p99)** | < 1000ms | 1000-2000ms | > 2000ms |
| **Throughput** | > 1000 RPS | 500-1000 RPS | < 500 RPS |
| **Error Rate** | < 0.1% | 0.1-1% | > 1% |
| **CPU Usage** | < 60% | 60-80% | > 80% |
| **Memory Usage** | < 70% | 70-85% | > 85% |
| **Database Query Time (p95)** | < 50ms | 50-200ms | > 200ms |
| **Cache Hit Rate** | > 90% | 80-90% | < 80% |
| **Event Processing Latency** | < 500ms | 500-2000ms | > 2000ms |

### 6.5 Endurance Testing

```python
# tests/performance/influencer-marketing/test_endurance.py

import pytest
import time
import psutil
import asyncio
from datetime import datetime, timedelta


class TestInfluencerMarketingEndurance:
    """Endurance tests for sustained load over extended periods."""

    TEST_DURATION_HOURS = 4
    SAMPLE_INTERVAL_SECONDS = 30

    @pytest.mark.asyncio
    async def test_sustained_load_endurance(self):
        """Verify system stability under sustained load."""
        start_time = datetime.utcnow()
        end_time = start_time + timedelta(hours=self.TEST_DURATION_HOURS)
        samples = []

        async with httpx.AsyncClient() as client:
            while datetime.utcnow() < end_time:
                sample_start = time.monotonic()

                tasks = [
                    client.get("https://staging.grc-claw.example.com/api/v1/influencer/marketing?page=1")
                    for _ in range(20)
                ]
                responses = await asyncio.gather(*tasks)

                sample = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "elapsed_hours": (datetime.utcnow() - start_time).total_seconds() / 3600,
                    "response_times": [
                        (time.monotonic() - sample_start) * 1000 / len(responses)
                        for _ in responses
                    ],
                    "status_codes": [r.status_code for r in responses],
                    "cpu_percent": psutil.cpu_percent(),
                    "memory_percent": psutil.virtual_memory().percent,
                    "open_connections": len(psutil.net_connections()),
                }

                success_rate = sum(1 for s in sample["status_codes"] if s < 500) / len(responses)
                sample["success_rate"] = success_rate

                assert success_rate > 0.95, (
                    f"Success rate dropped to {success_rate:.2%} at "
                    f"{sample['elapsed_hours']:.1f} hours"
                )

                samples.append(sample)
                await asyncio.sleep(self.SAMPLE_INTERVAL_SECONDS)

        memory_trend = [s["memory_percent"] for s in samples]
        memory_growth = memory_trend[-1] - memory_trend[0]
        assert memory_growth < 20, (
            f"Potential memory leak: memory grew by {memory_growth:.1f}% over "
            f"{self.TEST_DURATION_HOURS} hours"
        )
```

---

## 7. Security Tests

### 7.1 Test Structure

```
tests/security/
├── influencer-marketing/
│   ├── __init__.py
│   ├── test_authentication.py
│   ├── test_authorization.py
│   ├── test_input_validation.py
│   ├── test_data_protection.py
│   ├── test_api_security.py
│   ├── test_secrets_management.py
│   ├── test_dependency_scanning.py
│   └── test_compliance.py
├── owasp_zap/
│   └── zap_scan.py
├── semgrep/
│   └── custom_rules/
└── reports/
    ├── penetration_tests/
    └── vulnerability_scans/
```

### 7.2 Authentication Tests

```python
# tests/security/influencer-marketing/test_authentication.py

import pytest
import jwt
from datetime import datetime, timedelta
from grc_claw.influencer_marketing.auth import AuthManager


class TestInfluencerMarketingAuthentication:
    """Security tests for authentication mechanisms."""

    @pytest.fixture
    def auth_manager(self):
        return AuthManager(secret_key="test-secret-key-for-testing-only")

    def test_valid_token_creation(self, auth_manager):
        """Verify valid JWT token creation."""
        token = auth_manager.create_token(
            user_id="user-001",
            roles=["user"],
            expires_in=timedelta(hours=1),
        )
        assert token is not None
        assert isinstance(token, str)

        payload = auth_manager.decode_token(token)
        assert payload["user_id"] == "user-001"
        assert "user" in payload["roles"]

    def test_expired_token_rejection(self, auth_manager):
        """Verify expired tokens are rejected."""
        token = auth_manager.create_token(
            user_id="user-001",
            expires_in=timedelta(seconds=-1),
        )
        with pytest.raises(jwt.ExpiredSignatureError):
            auth_manager.decode_token(token)

    def test_invalid_token_rejection(self, auth_manager):
        """Verify tampered tokens are rejected."""
        with pytest.raises(jwt.InvalidTokenError):
            auth_manager.decode_token("invalid.token.here")

    def test_token_signature_verification(self, auth_manager):
        """Verify token signature cannot be forged."""
        token = auth_manager.create_token(user_id="user-001")

        parts = token.split(".")
        tampered = f"{parts[0]}.{parts[1]}.fakesignature"

        with pytest.raises(jwt.InvalidSignatureError):
            auth_manager.decode_token(tampered)

    def test_brute_force_protection(self, auth_manager):
        """Verify brute force protection on login."""
        for i in range(10):
            result = auth_manager.authenticate(
                username="test_user",
                password=f"wrong_password_{i}",
            )
            assert result is None

        result = auth_manager.authenticate(
            username="test_user",
            password="correct_password",
        )
        assert result is None

    def test_password_hashing(self, auth_manager):
        """Verify passwords are properly hashed."""
        password = "MySecurePassword123!"
        hashed = auth_manager.hash_password(password)

        assert hashed != password
        assert auth_manager.verify_password(password, hashed) is True
        assert auth_manager.verify_password("wrong", hashed) is False
```

### 7.3 Authorization Tests

```python
# tests/security/influencer-marketing/test_authorization.py

import pytest
from grc_claw.influencer_marketing.auth import AuthManager, Permission


class TestInfluencerMarketingAuthorization:
    """Security tests for authorization and access control."""

    @pytest.fixture
    def auth_manager(self):
        return AuthManager(secret_key="test-secret-key")

    def test_role_based_access_control(self, auth_manager):
        """Verify RBAC enforcement."""
        admin_token = auth_manager.create_token(
            user_id="admin-001",
            roles=["admin"],
        )
        user_token = auth_manager.create_token(
            user_id="user-001",
            roles=["user"],
        )

        assert auth_manager.has_permission(admin_token, Permission.DELETE) is True
        assert auth_manager.has_permission(admin_token, Permission.ADMIN) is True

        assert auth_manager.has_permission(user_token, Permission.READ) is True
        assert auth_manager.has_permission(user_token, Permission.WRITE) is True
        assert auth_manager.has_permission(user_token, Permission.DELETE) is False
        assert auth_manager.has_permission(user_token, Permission.ADMIN) is False

    def test_resource_level_authorization(self, auth_manager):
        """Verify resource-level access control."""
        owner_token = auth_manager.create_token(
            user_id="owner-001",
            roles=["user"],
        )
        other_token = auth_manager.create_token(
            user_id="other-001",
            roles=["user"],
        )

        assert auth_manager.can_access_resource(
            owner_token, "resource-001", owner_id="owner-001"
        ) is True

        assert auth_manager.can_access_resource(
            other_token, "resource-001", owner_id="owner-001"
        ) is False

    def test_privilege_escalation_prevention(self, auth_manager):
        """Verify users cannot escalate privileges."""
        user_token = auth_manager.create_token(
            user_id="user-001",
            roles=["user"],
        )

        with pytest.raises(PermissionError):
            auth_manager.update_roles(user_token, user_id="user-001", new_roles=["admin"])

    def test_tenant_isolation(self, auth_manager):
        """Verify multi-tenant data isolation."""
        tenant_a_token = auth_manager.create_token(
            user_id="user-a",
            roles=["user"],
            tenant_id="tenant-a",
        )
        tenant_b_token = auth_manager.create_token(
            user_id="user-b",
            roles=["user"],
            tenant_id="tenant-b",
        )

        assert auth_manager.get_tenant_id(tenant_a_token) == "tenant-a"
        assert auth_manager.get_tenant_id(tenant_b_token) == "tenant-b"
```

### 7.4 Input Validation Security Tests

```python
# tests/security/influencer-marketing/test_input_validation.py

import pytest
from grc_claw.influencer_marketing.validators import SecureValidator


class TestInfluencerMarketingInputSecurity:
    """Security tests for input validation and sanitization."""

    @pytest.fixture
    def validator(self):
        return SecureValidator()

    @pytest.mark.parametrize("payload", [
        "<script>alert('xss')</script>",
        "javascript:alert('xss')",
        "<img src=x onerror=alert('xss')>",
        "'; DROP TABLE users; --",
        "1 OR 1=1",
        "{7*7}",
        "${7*7}",
        "{% import os %}{0}",
        "../../../etc/passwd",
        "..\\..\\..\\windows\\system32",
        "\x00\x00\x00",
        "A" * 10000000,
    ])
    def test_malicious_input_rejection(self, validator, payload):
        """Verify malicious inputs are rejected or sanitized."""
        result = validator.validate(payload)
        assert result.is_safe is False or result.sanitized != payload

    def test_sql_injection_prevention(self, validator):
        """Verify SQL injection attempts are blocked."""
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "1; SELECT * FROM users",
            "' UNION SELECT * FROM passwords--",
        ]
        for payload in malicious_inputs:
            result = validator.validate(payload)
            assert result.is_safe is False

    def test_xss_prevention(self, validator):
        """Verify XSS attempts are blocked."""
        xss_payloads = [
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert('xss')>",
            "<svg onload=alert('xss')>",
            "javascript:alert('xss')",
        ]
        for payload in xss_payloads:
            result = validator.validate(payload)
            assert result.is_safe is False

    def test_command_injection_prevention(self, validator):
        """Verify command injection attempts are blocked."""
        payloads = [
            "; cat /etc/passwd",
            "| whoami",
            "$(id)",
            "`id`",
            "; rm -rf /",
        ]
        for payload in payloads:
            result = validator.validate(payload)
            assert result.is_safe is False

    def test_path_traversal_prevention(self, validator):
        """Verify path traversal attempts are blocked."""
        payloads = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "/etc/shadow",
            "file:///etc/passwd",
        ]
        for payload in payloads:
            result = validator.validate(payload)
            assert result.is_safe is False
```

### 7.5 API Security Tests

```python
# tests/security/influencer-marketing/test_api_security.py

import pytest
import httpx
from fastapi.testclient import TestClient


class TestInfluencerMarketingAPISecurity:
    """Security tests for API endpoints."""

    @pytest.fixture(scope="module")
    def client(self):
        from grc_claw.influencer_marketing.api import create_app
        app = create_app(config={"environment": "testing"})
        return TestClient(app)

    def test_cors_headers(self, client):
        """Verify CORS headers are properly set."""
        response = client.options(
            "/api/v1/influencer/marketing",
            headers={"Origin": "https://evil.com"},
        )
        assert response.headers.get("access-control-allow-origin") != "*"

    def test_security_headers(self, client):
        """Verify security headers are present."""
        response = client.get("/health")
        headers = response.headers

        assert headers.get("x-content-type-options") == "nosniff"
        assert headers.get("x-frame-options") == "DENY"
        assert "strict-transport-security" in headers
        assert "content-security-policy" in headers

    def test_rate_limiting_enforcement(self, client):
        """Verify rate limiting is enforced."""
        responses = []
        for _ in range(200):
            resp = client.get("/health")
            responses.append(resp.status_code)

        assert 429 in responses

    def test_sensitive_data_exposure(self, client):
        """Verify sensitive data is not exposed in responses."""
        response = client.get("/api/v1/influencer/marketing/test-id")
        data = response.json()

        sensitive_fields = ["password", "secret", "token", "api_key", "credit_card"]
        for field in sensitive_fields:
            assert field not in str(data).lower()

    def test_error_message_information_leakage(self, client):
        """Verify error messages don't leak internal details."""
        response = client.get("/api/v1/influencer/marketing/nonexistent-id")
        assert response.status_code == 404

        data = response.json()
        assert "traceback" not in str(data).lower()
        assert "/usr/local" not in str(data)
        assert "sql" not in str(data).lower()

    def test_api_key_rotation(self, client):
        """Verify API keys can be rotated."""
        response = client.get(
            "/api/v1/influencer/marketing",
            headers={"X-API-Key": "old-key"},
        )
        assert response.status_code == 401

        response = client.get(
            "/api/v1/influencer/marketing",
            headers={"X-API-Key": "new-key"},
        )
        assert response.status_code == 200
```

### 7.6 Data Protection Tests

```python
# tests/security/influencer-marketing/test_data_protection.py

import pytest
from grc_claw.influencer_marketing.encryption import DataEncryption


class TestInfluencerMarketingDataProtection:
    """Security tests for data protection mechanisms."""

    @pytest.fixture
    def encryptor(self):
        return DataEncryption(key="test-encryption-key-32bytes-long!!")

    def test_encryption_at_rest(self, encryptor):
        """Verify data is encrypted at rest."""
        plaintext = "sensitive data: SSN 123-45-6789"
        encrypted = encryptor.encrypt(plaintext)

        assert encrypted != plaintext
        assert "123-45-6789" not in encrypted

    def test_decryption_with_valid_key(self, encryptor):
        """Verify data can be decrypted with correct key."""
        plaintext = "sensitive data"
        encrypted = encryptor.encrypt(plaintext)
        decrypted = encryptor.decrypt(encrypted)

        assert decrypted == plaintext

    def test_decryption_with_invalid_key(self, encryptor):
        """Verify decryption fails with wrong key."""
        plaintext = "sensitive data"
        encrypted = encryptor.encrypt(plaintext)

        wrong_encryptor = DataEncryption(key="wrong-key-32-bytes-long!!!")
        with pytest.raises(Exception):
            wrong_encryptor.decrypt(encrypted)

    def test_pii_masking(self, encryptor):
        """Verify PII data is properly masked."""
        pii_data = {
            "name": "John Doe",
            "email": "john@example.com",
            "ssn": "123-45-6789",
            "phone": "555-123-4567",
        }
        masked = encryptor.mask_pii(pii_data)

        assert masked["name"] == "J*** D**"
        assert masked["email"] == "j***@example.com"
        assert masked["ssn"] == "***-**-6789"
        assert masked["phone"] == "***-***-4567"

    def test_encryption_key_rotation(self, encryptor):
        """Verify encryption key rotation works."""
        plaintext = "data to preserve"
        old_encrypted = encryptor.encrypt(plaintext)

        encryptor.rotate_key("new-encryption-key-32bytes-long!!")

        decrypted = encryptor.decrypt(old_encrypted)
        assert decrypted == plaintext

        new_encrypted = encryptor.encrypt(plaintext)
        assert new_encrypted != old_encrypted
```

### 7.7 OWASP ZAP Integration

```python
# tests/security/owasp_zap/zap_scan.py

import pytest
import time
import requests
from zapv2 import ZAPv2


class TestOWASPZAPScan:
    """OWASP ZAP security scanning integration."""

    ZAP_API_URL = "http://localhost:8080"
    TARGET_URL = "https://staging.grc-claw.example.com"

    @pytest.fixture(scope="class")
    def zap(self):
        """Initialize ZAP client."""
        return ZAPv2(apikey="test-api-key", proxies={
            "http": self.ZAP_API_URL,
            "https": self.ZAP_API_URL,
        })

    @pytest.fixture(scope="class")
    def zap_scan(self, zap):
        """Run ZAP spider and active scan."""
        scan_id = zap.spider.scan(self.TARGET_URL)
        while int(zap.spider.status(scan_id)) < 100:
            time.sleep(1)

        ascan_id = zap.ascan.scan(self.TARGET_URL)
        while int(zap.ascan.status(ascan_id)) < 100:
            time.sleep(5)

        yield zap

        report = zap.core.htmlreport()
        with open(f"tests/security/reports/zap_report_influencer-marketing.html", "w") as f:
            f.write(report)

    def test_no_critical_vulnerabilities(self, zap_scan):
        """Verify no critical vulnerabilities found."""
        alerts = zap_scan.core.alerts()
        critical = [a for a in alerts if a["risk"] == "Critical"]
        assert len(critical) == 0, f"Found {len(critical)} critical vulnerabilities"

    def test_no_high_vulnerabilities(self, zap_scan):
        """Verify no high-severity vulnerabilities found."""
        alerts = zap_scan.core.alerts()
        high = [a for a in alerts if a["risk"] == "High"]
        assert len(high) == 0, f"Found {len(high)} high vulnerabilities"

    def test_vulnerability_count_baseline(self, zap_scan):
        """Verify vulnerability count is within acceptable baseline."""
        alerts = zap_scan.core.alerts()
        medium = [a for a in alerts if a["risk"] == "Medium"]
        low = [a for a in alerts if a["risk"] == "Low"]

        assert len(medium) <= 10, f"Too many medium vulnerabilities: {len(medium)}"
        assert len(low) <= 20, f"Too many low vulnerabilities: {len(low)}"
```

---

## 8. Test Data Management

### 8.1 Test Data Strategy

| Data Type | Strategy | Storage |
|-----------|----------|---------|
| **Synthetic data** | Generated per-test with Faker | In-memory |
| **Fixture data** | Version-controlled JSON/YAML | `tests/fixtures/` |
| **Seed data** | Database migration scripts | `tests/fixtures/seed/` |
| **Production-like** | Anonymized production snapshot | Staging only |
| **PII data** | Never used in testing | N/A |

### 8.2 Data Generation

```python
# tests/conftest.py

import pytest
from faker import Faker

fake = Faker()


@pytest.fixture
def fake_user():
    """Generate fake user data."""
    return {
        "id": fake.uuid4(),
        "email": fake.email(),
        "name": fake.name(),
        "company": fake.company(),
        "created_at": fake.date_time_this_year().isoformat(),
    }


@pytest.fixture
def fake_influencer_marketing_record():
    """Generate fake Influencer Marketing record."""
    return {
        "id": fake.uuid4(),
        "name": fake.catch_phrase(),
        "description": fake.text(max_nb_chars=200),
        "status": fake.random_element(["active", "inactive", "pending"]),
        "metadata": {
            "source": "test",
            "version": "1.0",
        },
        "created_at": fake.date_time_this_year().isoformat(),
        "updated_at": fake.date_time_this_year().isoformat(),
    }
```

### 8.3 Data Cleanup

```python
# tests/conftest.py

import pytest


@pytest.fixture(autouse=True)
def cleanup_test_data():
    """Automatically clean up test data after each test."""
    yield
    from grc_claw.database import get_db
    db = get_db()
    db.execute("DELETE FROM influencer_marketing_records WHERE metadata->>'source' = 'test'")
    db.commit()
```

---

## 9. CI/CD Integration

### 9.1 Pipeline Configuration

```yaml
# .github/workflows/test-influencer-marketing.yaml

name: Influencer Marketing Tests

on:
  push:
    paths:
      - 'packages/influencer_marketing/**'
      - 'tests/unit/influencer-marketing/**'
      - 'tests/integration/influencer-marketing/**'
  pull_request:
    paths:
      - 'packages/influencer_marketing/**'

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install dependencies
        run: pip install -e ".[test]"
      - name: Run unit tests
        run: pytest tests/unit/influencer-marketing/ -v --cov=grc_claw.influencer_marketing --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: coverage.xml
          flags: influencer-marketing-unit

  integration-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_DB: test_grc_claw
          POSTGRES_USER: test_user
          POSTGRES_PASSWORD: test_pass
        ports:
          - 5432:5432
      redis:
        image: redis:7
        ports:
          - 6379:6379
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install dependencies
        run: pip install -e ".[test]"
      - name: Run integration tests
        run: pytest tests/integration/influencer-marketing/ -v --tb=short
        env:
          DATABASE_URL: postgresql://test_user:test_pass@localhost:5432/test_grc_claw
          REDIS_URL: redis://localhost:6379/0

  e2e-tests:
    runs-on: ubuntu-latest
    needs: [unit-tests, integration-tests]
    if: github.event_name == 'pull_request'
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install dependencies
        run: pip install -e ".[test]"
      - name: Start staging environment
        run: docker-compose -f tests/e2e/docker-compose.yml up -d
      - name: Run E2E tests
        run: pytest tests/e2e/influencer-marketing/ -v --tb=short
        env:
          BASE_URL: http://localhost:3000
      - name: Teardown
        if: always()
        run: docker-compose -f tests/e2e/docker-compose.yml down

  performance-tests:
    runs-on: ubuntu-latest
    needs: [integration-tests]
    if: github.event_name == 'schedule' || contains(github.event.head_commit.message, '[perf]')
    steps:
      - uses: actions/checkout@v4
      - name: Run k6 load tests
        uses: grafana/k6-action@v0.3.1
        with:
          filename: tests/performance/k6/load_test.js
          flags: --env BASE_URL=https://staging.grc-claw.example.com

  security-tests:
    runs-on: ubuntu-latest
    needs: [unit-tests]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install dependencies
        run: pip install -e ".[test,security]"
      - name: Run security tests
        run: pytest tests/security/influencer-marketing/ -v --tb=short
      - name: Run Snyk scan
        uses: snyk/actions/python@master
        env:
          SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
      - name: Run Trivy scan
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: "fs"
          scan-ref: "packages/influencer_marketing"
```

### 9.2 Quality Gates

| Gate | Criteria | Enforcement |
|------|----------|-------------|
| **Unit test pass rate** | 100% | Block merge |
| **Unit test coverage** | >= 85% | Block merge |
| **Integration test pass rate** | 100% | Block merge |
| **E2E test pass rate** | >= 95% | Block merge |
| **Performance regression** | < 10% degradation | Warning |
| **Security vulnerabilities** | 0 critical, 0 high | Block merge |
| **Code quality** | SonarQube quality gate pass | Block merge |

---

## 10. Test Coverage Metrics

### 10.1 Coverage Targets

| Metric | Minimum | Target | Stretch |
|--------|---------|--------|---------|
| **Line coverage** | 80% | 90% | 95% |
| **Branch coverage** | 75% | 85% | 90% |
| **Function coverage** | 85% | 95% | 98% |
| **Statement coverage** | 80% | 90% | 95% |
| **API endpoint coverage** | 90% | 100% | 100% |
| **Error path coverage** | 70% | 85% | 90% |

### 10.2 Coverage Reporting

```bash
# Generate coverage report
pytest tests/unit/influencer-marketing/ tests/integration/influencer-marketing/ \
  --cov=grc_claw.influencer_marketing \
  --cov-report=html:tests/reports/coverage/influencer-marketing/ \
  --cov-report=xml:tests/reports/coverage/influencer-marketing.xml \
  --cov-report=term-missing \
  --cov-fail-under=85

# View HTML report
open tests/reports/coverage/influencer-marketing/index.html
```

---

## 11. Defect Management

### 11.1 Severity Classification

| Severity | Description | SLA |
|----------|-------------|-----|
| **S1 — Critical** | System down, data loss, security breach | 4 hours |
| **S2 — High** | Major feature broken, no workaround | 24 hours |
| **S3 — Medium** | Feature degraded, workaround exists | 72 hours |
| **S4 — Low** | Minor issue, cosmetic | Next sprint |

### 11.2 Defect Lifecycle

```
New -> Triaged -> In Progress -> Fixed -> Verified -> Closed
                  |
              Reopened (if fix fails verification)
```

### 11.3 Test Failure Response

1. **Detect** — Automated test failure notification (Slack/email)
2. **Triage** — Assign severity and owner within 1 hour (S1/S2)
3. **Isolate** — Identify root cause using logs, traces, and test artifacts
4. **Fix** — Implement fix with regression test
5. **Verify** — Confirm fix passes all test levels
6. **Prevent** — Add automated check to prevent recurrence

---

## 12. Appendices

### 12.1 Glossary

| Term | Definition |
|------|------------|
| **SUT** | System Under Test |
| **Test Fixture** | Fixed state used as a baseline for running tests |
| **Mock** | Object that simulates the behavior of a real object |
| **Stub** | Simplified implementation that returns pre-defined responses |
| **Spy** | Wrapper that records interactions with a real object |
| **Contract Test** | Test that verifies API consumer-provider agreements |
| **Smoke Test** | Minimal test to verify basic functionality |
| **Regression Test** | Test that verifies existing functionality after changes |

### 12.2 References

- [OWASP Testing Guide v4.2](https://owasp.org/www-project-web-security-testing-guide/)
- [ISTQB Syllabus](https://www.istqb.org/certifications/certified-tester-foundation-level)
- [Google Testing Blog](https://testing.googleblog.com/)
- [Martin Fowler — TestPyramid](https://martinfowler.com/articles/practical-test-pyramid.html)
- [GRC Claw Architecture Documentation](../architecture.md)
- [GRC Claw API Reference](../api-reference.md)

### 12.3 Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-10-02 | GRC Claw QA Team | Initial version |

---

*This document is maintained by the GRC Claw QA Team. For questions or suggestions, contact #qa-team on Slack.*
