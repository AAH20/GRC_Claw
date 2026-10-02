"""Shared fixtures for GRC Claw integration tests.

This module provides common fixtures used across all integration test modules,
including test clients, sample data factories, and utility helpers for testing
multi-project integrations within the GRC Claw ecosystem.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, AsyncGenerator, Dict, List, Optional

import pytest
import pytest_asyncio


# ── Sample Data Factories ────────────────────────────────────────────────────


@pytest.fixture
def sample_campaign_data() -> Dict[str, Any]:
    """Provide sample campaign creation data.

    Returns:
        Dictionary with valid campaign creation payload.
    """
    return {
        "name": "Integration Test Campaign",
        "description": "Campaign created during integration testing",
        "goals": ["awareness", "conversion"],
        "total_budget": 25000.0,
        "daily_budget": 833.33,
        "channels": ["search", "social", "display"],
        "duration_days": 30,
        "target_audience": {
            "demographics": {
                "age_ranges": ["25-34", "35-44"],
                "locations": ["US", "UK"],
            },
            "interests": ["technology", "marketing"],
        },
        "brand_voice": "professional",
        "key_message": "The future of marketing is here",
        "industry": "technology",
    }


@pytest.fixture
def sample_lead_data() -> Dict[str, Any]:
    """Provide sample lead scoring data.

    Returns:
        Dictionary with valid lead scoring payload.
    """
    return {
        "lead_id": f"lead_{uuid.uuid4().hex[:8]}",
        "company_name": "Acme Corp",
        "domain": "acme.com",
        "industry": "technology",
        "company_size": "50-200",
        "location": "US",
        "firmographic_score": 75.0,
        "technographic_score": 60.0,
        "intent_score": 85.0,
        "engagement_score": 70.0,
        "timing_score": 90.0,
        "evidence_confidence": 0.8,
    }


@pytest.fixture
def sample_journey_data() -> Dict[str, Any]:
    """Provide sample journey creation data.

    Returns:
        Dictionary with valid journey creation payload.
    """
    return {
        "name": "Integration Test Journey",
        "description": "Journey created during integration testing",
        "target_audience": "high_value_prospects",
        "business_goal": "conversion",
        "channels": ["email", "push"],
        "metadata": {"source": "integration_test", "version": "1.0"},
    }


@pytest.fixture
def sample_social_post_data() -> Dict[str, Any]:
    """Provide sample social media post data.

    Returns:
        Dictionary with valid social post creation payload.
    """
    return {
        "platform": "twitter",
        "content": "Integration test post content #testing",
        "hashtags": ["testing", "integration"],
        "metadata": {"impressions": 1000, "likes": 50, "comments": 10, "shares": 5},
    }


@pytest.fixture
def sample_ppc_campaign_data() -> Dict[str, Any]:
    """Provide sample PPC campaign data.

    Returns:
        Dictionary with valid PPC campaign creation payload.
    """
    return {
        "name": "Integration Test PPC Campaign",
        "platform": "google",
        "budget": 500.0,
        "status": "active",
    }


@pytest.fixture
def sample_deal_data() -> Dict[str, Any]:
    """Provide sample deal scoring data.

    Returns:
        Dictionary with valid deal scoring payload.
    """
    return {
        "deal_id": f"deal_{uuid.uuid4().hex[:8]}",
        "title": "Integration Test Deal",
        "value": 50000.0,
        "stage": "qualification",
        "contact_email": "buyer@acme.com",
        "company": "Acme Corp",
        "days_in_stage": 5,
        "activities_count": 3,
        "last_activity_days": 1,
        "source": "inbound",
    }


@pytest.fixture
def sample_content_generation_request() -> Dict[str, Any]:
    """Provide sample content generation request data.

    Returns:
        Dictionary with valid content generation payload.
    """
    return {
        "query": "AI marketing automation",
        "content_type": "article",
        "language": "en",
        "location": "us",
        "platforms": ["twitter", "linkedin"],
    }


@pytest.fixture
def sample_seo_optimization_request() -> Dict[str, Any]:
    """Provide sample SEO optimization request data.

    Returns:
        Dictionary with valid SEO optimization payload.
    """
    return {
        "content": "AI marketing automation is transforming how businesses reach customers.",
        "target_keywords": ["AI marketing", "marketing automation", "AI tools"],
        "content_type": "blog_post",
    }


@pytest.fixture
def sample_product_data() -> Dict[str, Any]:
    """Provide sample product data.

    Returns:
        Dictionary with valid product payload.
    """
    return {
        "id": f"prod_{uuid.uuid4().hex[:8]}",
        "name": "Integration Test Product",
        "description": "A product for integration testing",
        "price": 99.99,
        "category": "Electronics",
        "tags": ["test", "integration"],
        "in_stock": True,
    }


@pytest.fixture
def sample_partner_data() -> Dict[str, Any]:
    """Provide sample partner registration data.

    Returns:
        Dictionary with valid partner registration payload.
    """
    return {
        "id": f"partner_{uuid.uuid4().hex[:8]}",
        "name": "Integration Test Partner",
        "email": "partner@test.com",
        "company": "Test Partner Co",
        "industry": "technology",
        "region": "US",
    }


@pytest.fixture
def sample_prospect_data() -> Dict[str, Any]:
    """Provide sample prospect creation data.

    Returns:
        Dictionary with valid prospect creation payload.
    """
    return {
        "name": "Jane Prospect",
        "company": "Prospect Corp",
        "title": "VP of Marketing",
        "email": "jane@prospectcorp.com",
        "linkedin_url": "https://linkedin.com/in/janeprospect",
        "company_size": 200,
        "industry": "technology",
        "source": "integration_test",
    }


@pytest.fixture
def sample_attribution_request() -> Dict[str, Any]:
    """Provide sample attribution request data.

    Returns:
        Dictionary with valid attribution request payload.
    """
    return {
        "model": "data_driven",
        "start_date": "2024-01-01T00:00:00",
        "end_date": "2024-01-31T23:59:59",
    }


# ── Utility Fixtures ─────────────────────────────────────────────────────────


@pytest.fixture
def unique_id() -> str:
    """Generate a unique identifier for test isolation.

    Returns:
        A unique hex string.
    """
    return uuid.uuid4().hex[:12]


@pytest.fixture
def timestamp() -> str:
    """Provide a consistent timestamp for test data.

    Returns:
        ISO format UTC timestamp string.
    """
    return datetime.now(timezone.utc).isoformat()


@pytest.fixture
def mock_agent_response() -> Dict[str, Any]:
    """Provide a standard mock agent response.

    Returns:
        Dictionary representing a successful agent response.
    """
    return {
        "success": True,
        "data": {"result": "mocked"},
        "error": None,
        "duration_ms": 100.0,
    }


@pytest.fixture
def mock_agent_error_response() -> Dict[str, Any]:
    """Provide a standard mock agent error response.

    Returns:
        Dictionary representing a failed agent response.
    """
    return {
        "success": False,
        "data": None,
        "error": "Mock agent error",
        "duration_ms": 50.0,
    }


# ── Async Fixtures ───────────────────────────────────────────────────────────


@pytest_asyncio.fixture
async def async_test_client() -> AsyncGenerator[Any, None]:
    """Create an async test client for async endpoint testing.

    Yields:
        Async test client instance.
    """
    try:
        from httpx import AsyncClient

        # This is a generic async client; specific test modules will create
        # their own clients bound to specific app instances.
        async with AsyncClient(base_url="http://test") as client:
            yield client
    except ImportError:
        pytest.skip("httpx not available for async testing")


# ── Configuration Fixtures ───────────────────────────────────────────────────


@pytest.fixture
def integration_test_config() -> Dict[str, Any]:
    """Provide integration test configuration.

    Returns:
        Dictionary with test configuration parameters.
    """
    return {
        "timeout_seconds": 30,
        "max_retries": 3,
        "retry_delay_seconds": 1.0,
        "test_environment": "integration",
    }


@pytest.fixture
def project_paths() -> Dict[str, str]:
    """Provide paths to all GRC Claw projects for integration testing.

    Returns:
        Dictionary mapping project names to their filesystem paths.
    """
    base = "/Users/ahmedhassan/GRC_Claw/projects"
    return {
        "campaign-optimizer": f"{base}/campaign-optimizer",
        "lead-scorer": f"{base}/lead-scorer",
        "journey-orchestrator": f"{base}/journey-orchestrator",
        "analytics": f"{base}/analytics",
        "social-media-manager": f"{base}/social-media-manager",
        "email-marketing": f"{base}/email-marketing",
        "ppc-manager": f"{base}/ppc-manager",
        "marketing-attribution": f"{base}/marketing-attribution",
        "crm-enhancer": f"{base}/crm-enhancer",
        "sales-automator": f"{base}/sales-automator",
        "content-generator": f"{base}/content-generator",
        "seo-optimizer": f"{base}/seo-optimizer",
        "ecommerce-marketing": f"{base}/ecommerce-marketing",
        "product-recommendations": f"{base}/product-recommendations",
        "broker-enablement": f"{base}/broker-enablement",
        "partner-management": f"{base}/partner-management",
    }
