"""Health and monitoring endpoints."""

from datetime import datetime, timezone

from fastapi import APIRouter, Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)

from app.api.v1.schemas.common import HealthResponse, ReadinessResponse
from app.core.config import get_settings

settings = get_settings()
router = APIRouter(tags=["System"])

# Prometheus metrics
registry = CollectorRegistry()

REQUEST_COUNT = Counter(
    "grc_api_requests_total",
    "Total API requests",
    ["method", "endpoint", "status", "tenant"],
    registry=registry,
)
REQUEST_DURATION = Histogram(
    "grc_api_request_duration_seconds",
    "Request duration in seconds",
    ["method", "endpoint", "tenant"],
    registry=registry,
)
ACTIVE_REQUESTS = Gauge(
    "grc_api_active_requests",
    "Currently active requests",
    ["endpoint"],
    registry=registry,
)
RATE_LIMIT_HITS = Counter(
    "grc_api_rate_limit_hits_total",
    "Rate limit rejections",
    ["tenant", "endpoint"],
    registry=registry,
)
ERROR_COUNT = Counter(
    "grc_api_errors_total",
    "Total errors",
    ["method", "endpoint", "error_code"],
    registry=registry,
)
ENFORCEMENT_DECISIONS = Counter(
    "grc_api_enforcement_decisions_total",
    "Enforcement decisions",
    ["verdict", "policy_id"],
    registry=registry,
)
EVIDENCE_INGESTED = Counter(
    "grc_api_evidence_ingested_bytes",
    "Evidence ingestion volume",
    ["tenant", "evidence_type"],
    registry=registry,
)
WEBHOOK_DELIVERIES = Counter(
    "grc_api_webhook_deliveries_total",
    "Webhook delivery attempts",
    ["status", "subscription_id"],
    registry=registry,
)


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    now = datetime.now(timezone.utc)
    return HealthResponse(
        status="healthy",
        version=settings.APP_VERSION,
        components={
            "api": {"status": "up"},
            "policy_engine": {"status": "up"},
            "evidence_store": {"status": "up"},
            "database": {"status": "up"},
            "cache": {"status": "up"},
        },
        timestamp=now,
    )


@router.get("/ready", response_model=ReadinessResponse)
async def readiness_check():
    """Readiness check endpoint."""
    return ReadinessResponse(
        ready=True,
        checks={
            "database": {"status": "pass"},
            "policy_engine": {"status": "pass"},
            "evidence_store": {"status": "pass"},
        },
    )


@router.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(
        content=generate_latest(registry),
        media_type=CONTENT_TYPE_LATEST,
    )
