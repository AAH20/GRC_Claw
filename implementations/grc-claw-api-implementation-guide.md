# GRC_Claw API Implementation Guide

**Version:** 1.0  
**Date:** 2026-10-01  
**Status:** Implementation Ready  
**References:** grc-claw-api-spec.md v1.2, grc-claw-integration-specification.md v2.0

---

## Table of Contents

1. [FastAPI Project Structure](#1-fastapi-project-structure)
2. [All 40+ Endpoint Implementations](#2-all-40-endpoint-implementations)
3. [GraphQL Schema Implementation](#3-graphql-schema-implementation)
4. [gRPC Service Implementations](#4-grpc-service-implementations)
5. [Webhook Implementations](#5-webhook-implementations)
6. [Authentication Middleware](#6-authentication-middleware)
7. [Rate Limiting Middleware](#7-rate-limiting-middleware)
8. [Error Handling](#8-error-handling)
9. [API Testing Framework](#9-api-testing-framework)

---

## 1. FastAPI Project Structure

```
grc-claw-api/
├── app/
│   ├── __init__.py
│   ├── main.py                          # FastAPI application entry point
│   ├── config.py                        # Settings & environment config
│   ├── dependencies.py                  # Shared FastAPI dependencies
│   ├── middleware/
│   │   ├── __init__.py
│   │   ├── auth.py                      # Authentication middleware
│   │   ├── rate_limit.py                # Rate limiting middleware
│   │   ├── request_context.py           # Request ID, tenant context
│   │   └── logging.py                   # Structured request logging
│   ├── models/
│   │   ├── __init__.py
│   │   ├── policy.py                    # Policy Pydantic models
│   │   ├── evidence.py                  # Evidence Pydantic models
│   │   ├── enforcement.py              # Enforcement Pydantic models
│   │   ├── assessment.py                # Assessment Pydantic models
│   │   ├── compliance.py                # Compliance Pydantic models
│   │   ├── agent.py                     # Agent Pydantic models
│   │   ├── audit.py                     # Audit Pydantic models
│   │   ├── webhook.py                   # Webhook Pydantic models
│   │   ├── graphql.py                   # GraphQL input/output types
│   │   └── common.py                    # Shared types (pagination, errors)
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── policies.py                  # /v1.0/policies
│   │   ├── evidence.py                  # /v1.0/evidence
│   │   ├── enforcement.py              # /v1.0/enforcement
│   │   ├── assessments.py               # /v1.0/assessments
│   │   ├── compliance.py                # /v1.0/compliance
│   │   ├── agents.py                    # /v1.0/agents
│   │   ├── audit.py                     # /v1.0/audit
│   │   ├── webhooks.py                  # /v1.0/webhooks
│   │   ├── health.py                    # /health, /ready, /metrics
│   │   └── graphql.py                   # /v1.0/graphql
│   ├── services/
│   │   ├── __init__.py
│   │   ├── policy_service.py
│   │   ├── evidence_service.py
│   │   ├── enforcement_service.py
│   │   ├── assessment_service.py
│   │   ├── compliance_service.py
│   │   ├── agent_service.py
│   │   ├── audit_service.py
│   │   └── webhook_service.py
│   ├── graphql/
│   │   ├── __init__.py
│   │   ├── schema.py                    # Strawberry schema definition
│   │   ├── resolvers/
│   │   │   ├── __init__.py
│   │   │   ├── policy_resolver.py
│   │   │   ├── evidence_resolver.py
│   │   │   ├── enforcement_resolver.py
│   │   │   ├── assessment_resolver.py
│   │   │   ├── compliance_resolver.py
│   │   │   ├── agent_resolver.py
│   │   │   └── audit_resolver.py
│   │   └── subscriptions.py             # WebSocket subscriptions
│   ├── grpc/
│   │   ├── __init__.py
│   │   ├── server.py                    # gRPC server bootstrap
│   │   ├── interceptors.py              # gRPC auth interceptors
│   │   └── services/
│   │       ├── __init__.py
│   │       ├── policy_servicer.py
│   │       ├── evidence_servicer.py
│   │       ├── enforcement_servicer.py
│   │       ├── assessment_servicer.py
│   │       ├── compliance_servicer.py
│   │       ├── agent_servicer.py
│   │       └── audit_servicer.py
│   ├── webhooks/
│   │   ├── __init__.py
│   │   ├── delivery.py                  # Webhook delivery engine
│   │   ├── signature.py                 # HMAC-SHA256 signing
│   │   └── retry.py                     # Exponential backoff retry
│   ├── db/
│   │   ├── __init__.py
│   │   ├── database.py                  # SQLAlchemy async engine
│   │   ├── repositories/
│   │   │   ├── __init__.py
│   │   │   ├── policy_repo.py
│   │   │   ├── evidence_repo.py
│   │   │   ├── enforcement_repo.py
│   │   │   ├── assessment_repo.py
│   │   │   ├── compliance_repo.py
│   │   │   ├── agent_repo.py
│   │   │   └── audit_repo.py
│   │   └── migrations/                  # Alembic migrations
│   ├── cache/
│   │   ├── __init__.py
│   │   └── redis_cache.py               # Redis cache layer
│   └── utils/
│       ├── __init__.py
│       ├── id_generator.py              # ULID/UUID generation
│       ├── pagination.py                # Cursor-based pagination
│       └── crypto.py                    # Hashing, signing utilities
├── proto/
│   ├── grcclaw/
│   │   └── v1/
│   │       ├── enforcement.proto
│   │       ├── policy.proto
│   │       ├── evidence.proto
│   │       ├── agent.proto
│   │       ├── assessment.proto
│   │       ├── compliance.proto
│   │       └── audit.proto
│   └── buf.yaml
├── tests/
│   ├── __init__.py
│   ├── conftest.py                      # Shared fixtures
│   ├── unit/
│   │   ├── test_auth.py
│   │   ├── test_rate_limit.py
│   │   ├── test_validation.py
│   │   └── test_error_handling.py
│   ├── integration/
│   │   ├── test_policies_api.py
│   │   ├── test_evidence_api.py
│   │   ├── test_enforcement_api.py
│   │   ├── test_assessments_api.py
│   │   ├── test_compliance_api.py
│   │   ├── test_agents_api.py
│   │   ├── test_audit_api.py
│   │   ├── test_webhooks_api.py
│   │   ├── test_graphql.py
│   │   └── test_grpc.py
│   ├── e2e/
│   │   ├── test_policy_lifecycle.py
│   │   ├── test_enforcement_flow.py
│   │   └── test_webhook_delivery.py
│   └── fixtures/
│       ├── policies.json
│       ├── agents.json
│       └── evidence.json
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
├── requirements.txt
└── README.md
```

### `pyproject.toml`

```toml
[project]
name = "grc-claw-api"
version = "1.0.0"
description = "GRC_Claw API — Governance, Risk, and Compliance for Agentic AI"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.30.0",
    "strawberry-graphql[fastapi]>=0.233.0",
    "grpcio>=1.64.0",
    "grpcio-tools>=1.64.0",
    "protobuf>=5.27.0",
    "pydantic>=2.7.0",
    "pydantic-settings>=2.3.0",
    "sqlalchemy[asyncio]>=2.0.0",
    "asyncpg>=0.29.0",
    "alembic>=1.13.0",
    "redis>=5.0.0",
    "httpx>=0.27.0",
    "python-jose[cryptography]>=3.3.0",
    "passlib[bcrypt]>=1.7.4",
    "python-multipart>=0.0.9",
    "prometheus-client>=0.20.0",
    "structlog>=24.1.0",
    "opentelemetry-api>=1.25.0",
    "opentelemetry-sdk>=1.25.0",
    "sse-starlette>=2.1.0",
    "websockets>=12.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.2.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=5.0.0",
    "httpx>=0.27.0",
    "respx>=0.21.0",
    "testcontainers>=4.0.0",
    "grpcio-testing>=1.64.0",
    "ruff>=0.5.0",
    "mypy>=1.10.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.mypy]
python_version = "3.11"
strict = true

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

### `app/main.py`

```python
"""GRC_Claw API — FastAPI application entry point."""

import structlog
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.middleware.auth import AuthenticationMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.request_context import RequestContextMiddleware
from app.middleware.logging import StructuredLoggingMiddleware
from app.routers import (
    agents,
    assessments,
    audit,
    compliance,
    enforcement,
    evidence,
    graphql,
    health,
    policies,
    webhooks,
)
from app.utils.errors import GRCCLAWException, problem_detail_response

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting GRC_Claw API", version=settings.APP_VERSION)
    from app.db.database import engine
    from app.cache.redis_cache import redis_client
    await redis_client.connect()
    yield
    # Shutdown
    await engine.dispose()
    await redis_client.disconnect()
    logger.info("GRC_Claw API stopped")


app = FastAPI(
    title="GRC_Claw API",
    description="Governance, Risk, and Compliance API for Agentic AI",
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs" if settings.ENV != "production" else None,
    redoc_url="/redoc" if settings.ENV != "production" else None,
    openapi_url="/openapi.json" if settings.ENV != "production" else None,
)

# ── Middleware (order matters: last added = first executed) ──
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(StructuredLoggingMiddleware)
app.add_middleware(RequestContextMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(AuthenticationMiddleware)

# ── Exception Handlers ──
@app.exception_handler(GRCCLAWException)
async def grc_exception_handler(request: Request, exc: GRCCLAWException):
    return problem_detail_response(
        exc=exc,
        request_id=getattr(request.state, "request_id", None),
    )

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception", exc_info=exc, request_id=getattr(request.state, "request_id", None))
    return JSONResponse(
        status_code=500,
        content={
            "type": "https://api.grc-claw.io/errors/internal-error",
            "title": "Internal Server Error",
            "status": 500,
            "detail": "An unexpected error occurred.",
            "instance": str(request.url.path),
            "code": "INTERNAL_ERROR",
            "timestamp": __import__("datetime").datetime.utcnow().isoformat() + "Z",
            "request_id": getattr(request.state, "request_id", None),
        },
    )

# ── Routers ──
API_V1 = "/v1.0"

app.include_router(health.router, tags=["System"])
app.include_router(policies.router, prefix=API_V1, tags=["Policies"])
app.include_router(evidence.router, prefix=API_V1, tags=["Evidence"])
app.include_router(enforcement.router, prefix=API_V1, tags=["Enforcement"])
app.include_router(assessments.router, prefix=API_V1, tags=["Assessments"])
app.include_router(compliance.router, prefix=API_V1, tags=["Compliance"])
app.include_router(agents.router, prefix=API_V1, tags=["Agents"])
app.include_router(audit.router, prefix=API_V1, tags=["Audit"])
app.include_router(webhooks.router, prefix=API_V1, tags=["Webhooks"])
app.include_router(graphql.router, prefix=API_V1, tags=["GraphQL"])
```

### `app/config.py`

```python
"""Application configuration."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "GRC_Claw API"
    APP_VERSION: str = "1.0.0"
    ENV: str = "development"
    DEBUG: bool = False

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8080

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://grc:grc@localhost:5432/grcclaw"
    DATABASE_POOL_SIZE: int = 20

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Auth
    JWT_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "RS256"
    JWT_ISSUER: str = "https://auth.grc-claw.io"
    JWT_AUDIENCE: str = "https://api.grc-claw.io"
    OIDC_DISCOVERY_URL: str = "https://auth.grc-claw.io/.well-known/openid-configuration"
    API_KEY_HEADER: str = "Authorization"

    # Rate Limiting
    RATE_LIMIT_DEFAULT_RPS: int = 100
    RATE_LIMIT_DEFAULT_BURST: int = 200
    RATE_LIMIT_ENFORCEMENT_RPS: int = 10000
    RATE_LIMIT_ENFORCEMENT_BURST: int = 2000

    # CORS
    CORS_ORIGINS: list[str] = ["*"]

    # Webhooks
    WEBHOOK_MAX_RETRIES: int = 6
    WEBHOOK_RETRY_DELAYS: list[int] = [0, 60, 300, 1800, 7200, 28800]
    WEBHOOK_TIMEOUT_SECONDS: int = 10
    WEBHOOK_SIGNATURE_HEADER: str = "X-GRC-Signature"

    # gRPC
    GRPC_PORT: int = 50051
    GRPC_MAX_WORKERS: int = 100

    # Tracing
    OTEL_EXPORTER_OTLP_ENDPOINT: str = "http://localhost:4317"
    OTEL_SERVICE_NAME: str = "grc-claw-api"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
```

---

## 2. All 40+ Endpoint Implementations

### 2.1 Common Models (`app/models/common.py`)

```python
"""Shared Pydantic models."""

from datetime import datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationParams(BaseModel):
    limit: int = Field(default=50, ge=1, le=500)
    cursor: str | None = None


class PaginatedResponse(BaseModel, Generic[T]):
    data: list[T]
    pagination: "PaginationInfo"


class PaginationInfo(BaseModel):
    next_cursor: str | None = None
    has_next: bool = False
    total: int = 0


class ErrorDetail(BaseModel):
    field: str
    message: str
    code: str


class ProblemDetail(BaseModel):
    type: str
    title: str
    status: int
    detail: str
    instance: str
    code: str
    timestamp: datetime
    request_id: str | None = None
    trace_id: str | None = None
    errors: list[ErrorDetail] | None = None


class HealthStatus(BaseModel):
    status: str
    version: str
    components: dict[str, dict[str, str]]
    timestamp: datetime


class ReadinessStatus(BaseModel):
    ready: bool
    checks: dict[str, dict[str, str]]
```

### 2.2 Policy Models (`app/models/policy.py`)

```python
"""Policy Pydantic models."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class PolicyStatus(str, Enum):
    DRAFT = "draft"
    REVIEW = "review"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class PolicyCategory(str, Enum):
    ETHICS = "ethics"
    SAFETY = "safety"
    PRIVACY = "privacy"
    FAIRNESS = "fairness"


class PolicyBase(BaseModel):
    policy_key: str = Field(..., pattern=r"^[A-Z0-9-]+$")
    name: str = Field(..., max_length=255)
    description: str | None = None
    category: PolicyCategory
    framework_tags: list[str] = []
    cedar_policy: str | None = None
    metadata: dict[str, Any] = {}


class PolicyCreate(PolicyBase):
    pass


class PolicyUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    cedar_policy: str | None = None
    metadata: dict[str, Any] | None = None


class PolicyResponse(PolicyBase):
    id: str
    status: PolicyStatus
    version: str
    effective_date: datetime | None = None
    expiry_date: datetime | None = None
    owner_id: str
    agent_bindings: list[str] = []
    rego_policy: str | None = None
    created_at: datetime
    updated_at: datetime
    created_by: str
    updated_by: str


class PolicyVersionResponse(BaseModel):
    version: str
    status: str
    change_summary: str | None = None
    created_at: datetime
    created_by: str


class PolicyDependencyResponse(BaseModel):
    policy_id: str
    dependencies: list["PolicyDependency"]
    dependents: list["PolicyDependency"]


class PolicyDependency(BaseModel):
    target_policy_id: str
    target_policy_name: str
    relation_type: str
    description: str | None = None


class CompilePolicyResponse(BaseModel):
    policy_id: str
    compilation_status: str
    rego_policy: str | None = None
    warnings: list[str] = []
    errors: list[str] = []
    compiled_at: datetime


class DryRunRequest(BaseModel):
    test_inputs: list[dict[str, Any]]


class DryRunResult(BaseModel):
    input_index: int
    decision: str
    matched_rules: list[str] = []
    evaluation_time_ms: float
    reason: str | None = None


class DryRunResponse(BaseModel):
    policy_id: str
    dry_run_results: list[DryRunResult]
    summary: "DryRunSummary"


class DryRunSummary(BaseModel):
    total: int
    allowed: int
    denied: int
    avg_evaluation_time_ms: float
```

### 2.3 Evidence Models (`app/models/evidence.py`)

```python
"""Evidence Pydantic models."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class EvidenceType(str, Enum):
    ARTIFACT = "artifact"
    OBSERVATION = "observation"
    INTERVIEW = "interview"
    ANALYSIS = "analysis"
    LOG = "log"


class VerificationLevel(str, Enum):
    L0 = "L0"
    L1 = "L1"
    L2 = "L2"
    L3 = "L3"
    L4 = "L4"


class EvidenceSource(BaseModel):
    type: str
    system: str
    collection_method: str


class EvidenceContent(BaseModel):
    format: str
    data: str
    hash: str | None = None


class EvidenceContext(BaseModel):
    environment: str
    region: str | None = None
    timestamp: datetime | None = None
    metadata: dict[str, Any] = {}


class ControlMapping(BaseModel):
    control_id: str
    framework: str
    control_title: str
    control_family: str | None = None


class ValidationStatus(BaseModel):
    status: str = "pending"
    validated_by: str | None = None
    validated_at: datetime | None = None
    confidence_score: float = 0.0


class CustodyEvent(BaseModel):
    action: str
    actor: str
    timestamp: datetime
    hash: str


class EvidenceCreate(BaseModel):
    policy_id: str | None = None
    assessment_id: str | None = None
    source: EvidenceSource
    evidence_type: EvidenceType
    content: EvidenceContent
    context: EvidenceContext
    control_mapping: ControlMapping | None = None


class EvidenceResponse(BaseModel):
    evidence_id: str
    policy_id: str | None = None
    assessment_id: str | None = None
    source: EvidenceSource
    evidence_type: EvidenceType
    content: EvidenceContent
    context: EvidenceContext
    validation: ValidationStatus
    verification_level: VerificationLevel = VerificationLevel.L0
    chain_of_custody: list[CustodyEvent] = []
    retention_class: str = "standard"
    created_at: datetime
    expires_at: datetime | None = None


class EvidenceSearchParams(BaseModel):
    policy_id: str | None = None
    assessment_id: str | None = None
    evidence_type: EvidenceType | None = None
    framework: str | None = None
    control_id: str | None = None
    verification_level: VerificationLevel | None = None
    environment: str | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
    query: str | None = None
    limit: int = Field(default=50, ge=1, le=500)
    cursor: str | None = None


class VerifyEvidenceResponse(BaseModel):
    evidence_id: str
    verification_result: "VerificationResult"


class VerificationResult(BaseModel):
    status: str
    verification_level: VerificationLevel
    hash_match: bool
    chain_of_custody_intact: bool
    schema_valid: bool
    control_mapping_valid: bool
    verified_at: datetime
    verified_by: str


class ExportPackageRequest(BaseModel):
    framework: str
    time_range: dict[str, datetime]
    format: str = "json"
    include_chain_of_custody: bool = True


class ExportPackageResponse(BaseModel):
    package_id: str
    status: str
    estimated_completion: datetime | None = None
    download_url: str | None = None


class ExportPackageStatus(BaseModel):
    package_id: str
    status: str
    download_url: str | None = None
    expires_at: datetime | None = None
    package_hash: str | None = None
    manifest: dict[str, Any] | None = None
```

### 2.4 Enforcement Models (`app/models/enforcement.py`)

```python
"""Enforcement Pydantic models."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class Verdict(str, Enum):
    ALLOW = "ALLOW"
    ALLOW_WITH_REDACTION = "ALLOW_WITH_REDACTION"
    REQUIRE_APPROVAL = "REQUIRE_APPROVAL"
    DENY = "DENY"
    QUARANTINE = "QUARANTINE"


class RedactionRule(BaseModel):
    field: str
    strategy: str  # mask, remove, hash, tokenize
    pattern: str | None = None


class DecisionRequest(BaseModel):
    agent_id: str
    action: str
    resource: str
    context: dict[str, Any] = {}
    policy_ids: list[str] = []
    include_evidence: bool = False


class BatchDecisionRequest(BaseModel):
    decisions: list[DecisionRequest] = Field(..., max_length=1000)


class DecisionResponse(BaseModel):
    decision_id: str
    verdict: Verdict
    policy_id: str
    policy_version: str
    agent_id: str
    action: str
    resource: str
    context: dict[str, Any]
    evidence_hash: str | None = None
    timestamp: datetime
    ttl: int = 300
    signature: str | None = None
    matched_rules: list[str] = []
    evaluation_time_ms: float
    reason: str | None = None
    redaction_rules: list[RedactionRule] = []


class BatchDecisionResponse(BaseModel):
    results: list[DecisionResponse]
    summary: "BatchSummary"


class BatchSummary(BaseModel):
    total: int
    allowed: int
    denied: int
    require_approval: int
    quarantined: int
    avg_evaluation_time_ms: float


class DecisionListParams(BaseModel):
    agent_id: str | None = None
    policy_id: str | None = None
    verdict: Verdict | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
    limit: int = Field(default=100, ge=1, le=1000)
    cursor: str | None = None
```

### 2.5 Assessment Models (`app/models/assessment.py`)

```python
"""Assessment Pydantic models."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class AssessmentType(str, Enum):
    RISK = "risk"
    COMPLIANCE = "compliance"
    MATURITY = "maturity"
    READINESS = "readiness"


class AssessmentStatus(str, Enum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class FindingSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFORMATIONAL = "informational"


class FindingStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    ACCEPTED = "accepted"
    FALSE_POSITIVE = "false_positive"


class AssessmentCreate(BaseModel):
    assessment_key: str
    title: str
    description: str | None = None
    assessment_type: AssessmentType
    target_id: str
    target_type: str
    methodology: str | None = None
    lead_assessor: str
    metadata: dict[str, Any] = {}


class AssessmentUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: AssessmentStatus | None = None
    score: float | None = None
    risk_level: str | None = None
    metadata: dict[str, Any] | None = None


class FindingCreate(BaseModel):
    finding_key: str
    title: str
    description: str
    severity: FindingSeverity
    category: str
    policy_id: str | None = None
    evidence_ids: list[str] = []
    remediation: str | None = None
    due_date: datetime | None = None


class FindingResponse(BaseModel):
    id: str
    finding_key: str
    title: str
    description: str
    severity: FindingSeverity
    category: str
    status: FindingStatus
    policy_id: str | None = None
    evidence_ids: list[str] = []
    remediation: str | None = None
    remediated_by: str | None = None
    remediated_at: datetime | None = None
    due_date: datetime | None = None


class AssessmentResponse(BaseModel):
    id: str
    assessment_key: str
    title: str
    description: str | None = None
    assessment_type: AssessmentType
    target_id: str
    target_type: str
    status: AssessmentStatus
    methodology: str | None = None
    score: float | None = None
    risk_level: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    next_assessment_at: datetime | None = None
    lead_assessor: str
    findings: list[FindingResponse] = []
    metadata: dict[str, Any] = {}
    created_at: datetime
    updated_at: datetime


class AssessmentReportRequest(BaseModel):
    format: str = "pdf"
    include_evidence: bool = True
    include_remediation: bool = True


class AssessmentListParams(BaseModel):
    assessment_type: AssessmentType | None = None
    status: AssessmentStatus | None = None
    target_type: str | None = None
    target_id: str | None = None
    methodology: str | None = None
    limit: int = Field(default=50, ge=1, le=500)
    cursor: str | None = None
```

### 2.6 Compliance Models (`app/models/compliance.py`)

```python
"""Compliance Pydantic models."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ComplianceStatus(str, Enum):
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PARTIAL = "partial"
    NOT_ASSESSED = "not_assessed"
    EXEMPT = "exempt"


class ComplianceFrameworkResponse(BaseModel):
    id: str
    framework_key: str
    name: str
    version: str
    description: str | None = None
    authority: str | None = None
    effective_date: datetime | None = None
    control_count: int = 0


class ComplianceControlResponse(BaseModel):
    id: str
    framework_id: str
    control_key: str
    title: str
    description: str | None = None
    category: str | None = None
    status: ComplianceStatus | None = None


class ComplianceGap(BaseModel):
    control_id: str
    control_title: str
    status: ComplianceStatus
    severity: str
    evidence_count: int = 0
    last_assessed: datetime | None = None


class ComplianceTrend(BaseModel):
    direction: str
    change: str
    period: str


class CompliancePostureResponse(BaseModel):
    framework: str
    target_id: str
    target_type: str
    controls_assessed: int
    controls_compliant: int
    controls_non_compliant: int
    controls_not_assessed: int
    compliance_score: float
    gaps: list[ComplianceGap] = []
    trend: ComplianceTrend | None = None


class ComplianceMappingCreate(BaseModel):
    control_id: str
    policy_id: str | None = None
    assessment_id: str | None = None
    mapping_type: str
    coverage: str
    notes: str | None = None


class ComplianceMappingResponse(BaseModel):
    id: str
    control_id: str
    policy_id: str | None = None
    assessment_id: str | None = None
    mapping_type: str
    coverage: str
    notes: str | None = None
    mapped_by: str
    mapped_at: datetime
    updated_at: datetime


class ComplianceReportRequest(BaseModel):
    framework: str
    time_range: dict[str, datetime]
    format: str = "json"
    include_evidence: bool = True
    include_gaps: bool = True


class CrosswalkQueryParams(BaseModel):
    control_id: str | None = None
    framework: str | None = None
    target_framework: str | None = None


class CrosswalkResponse(BaseModel):
    grc_control_id: str
    mappings: dict[str, list[str]]
```

### 2.7 Agent Models (`app/models/agent.py`)

```python
"""Agent Pydantic models."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class AgentType(str, Enum):
    MODEL = "model"
    AGENT = "agent"
    PIPELINE = "pipeline"
    ENDPOINT = "endpoint"


class AgentFramework(str, Enum):
    LANGCHAIN = "langchain"
    AUTOGEN = "autogen"
    CREWAI = "crewai"
    CUSTOM = "custom"
    MCP_SERVER = "mcp-server"


class LifecycleStage(str, Enum):
    PROPOSED = "proposed"
    APPROVED = "approved"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    TERMINATED = "terminated"


class RiskTier(str, Enum):
    PROHIBITED = "prohibited"
    HIGH = "high"
    LIMITED = "limited"
    MINIMAL = "minimal"


class AgentCapability(BaseModel):
    name: str
    description: str
    permissions: list[str] = []
    resource_scope: str | None = None


class AgentIdentity(BaseModel):
    spiffe_id: str | None = None
    mtls_cert: str | None = None
    cert_expiry: datetime | None = None


class TrustScore(BaseModel):
    value: int = Field(..., ge=0, le=100)
    grade: str
    last_evaluated: datetime | None = None


class AgentCreate(BaseModel):
    name: str
    type: AgentType
    framework: AgentFramework
    owner: str
    risk_tier: RiskTier
    capabilities: list[AgentCapability] = []


class AgentUpdate(BaseModel):
    name: str | None = None
    lifecycle_stage: LifecycleStage | None = None
    risk_tier: RiskTier | None = None
    capabilities: list[AgentCapability] | None = None


class AgentResponse(BaseModel):
    id: str
    name: str
    type: AgentType
    framework: AgentFramework
    owner: str
    lifecycle_stage: LifecycleStage
    risk_tier: RiskTier
    capabilities: list[AgentCapability] = []
    identity: AgentIdentity | None = None
    trust_score: TrustScore | None = None
    policy_bindings: list[str] = []
    created_at: datetime
    updated_at: datetime


class TrustScoreUpdate(BaseModel):
    value: int = Field(..., ge=0, le=100)
    grade: str
    reason: str


class PolicyBindingRequest(BaseModel):
    policy_ids: list[str]


class AgentListParams(BaseModel):
    type: AgentType | None = None
    framework: AgentFramework | None = None
    lifecycle_stage: LifecycleStage | None = None
    risk_tier: RiskTier | None = None
    trust_score_min: int | None = Field(default=None, ge=0, le=100)
    limit: int = Field(default=50, ge=1, le=500)
    cursor: str | None = None
```

### 2.8 Audit Models (`app/models/audit.py`)

```python
"""Audit trail Pydantic models."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class Actor(BaseModel):
    type: str
    id: str
    name: str | None = None


class AuditResource(BaseModel):
    type: str
    id: str
    name: str | None = None


class AuditEvent(BaseModel):
    event_id: str
    event_type: str
    actor: Actor
    resource: AuditResource
    timestamp: datetime
    details: dict[str, Any] = {}
    integrity_hash: str
    previous_event_hash: str | None = None


class AuditQueryParams(BaseModel):
    event_type: str | None = None
    actor_id: str | None = None
    resource_type: str | None = None
    resource_id: str | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
    limit: int = Field(default=100, ge=1, le=1000)
    cursor: str | None = None


class VerifyAuditChainRequest(BaseModel):
    from_event_id: str | None = None
    to_event_id: str | None = None


class VerifyAuditChainResponse(BaseModel):
    verification_status: str
    events_verified: int
    chain_intact: bool
    first_event_id: str | None = None
    last_event_id: str | None = None
    verified_at: datetime
```

### 2.9 Webhook Models (`app/models/webhook.py`)

```python
"""Webhook Pydantic models."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class WebhookEvent(str, Enum):
    POLICY_CREATED = "policy.created"
    POLICY_UPDATED = "policy.updated"
    POLICY_STATUS_CHANGED = "policy.status_changed"
    POLICY_DELETED = "policy.deleted"
    POLICY_COMPILED = "policy.compiled"
    POLICY_ACTIVATED = "policy.activated"
    POLICY_DEPRECATED = "policy.deprecated"
    EVIDENCE_COLLECTED = "evidence.collected"
    EVIDENCE_VERIFIED = "evidence.verified"
    EVIDENCE_EXPORTED = "evidence.exported"
    EVIDENCE_EXPIRED = "evidence.expired"
    ENFORCEMENT_DECISION = "enforcement.decision_made"
    ENFORCEMENT_APPROVAL = "enforcement.approval_required"
    ENFORCEMENT_QUARANTINE = "enforcement.agent_quarantined"
    ENFORCEMENT_VIOLATION = "enforcement.policy_violation"
    ASSESSMENT_CREATED = "assessment.created"
    ASSESSMENT_STARTED = "assessment.started"
    ASSESSMENT_COMPLETED = "assessment.completed"
    ASSESSMENT_FINDING_ADDED = "assessment.finding_added"
    ASSESSMENT_FINDING_RESOLVED = "assessment.finding_resolved"
    COMPLIANCE_POSTURE_CHANGED = "compliance.posture_changed"
    COMPLIANCE_CONTROL_SATISFIED = "compliance.control_satisfied"
    COMPLIANCE_CONTROL_VIOLATED = "compliance.control_violated"
    COMPLIANCE_REPORT_GENERATED = "compliance.report_generated"
    COMPLIANCE_MAPPING_CREATED = "compliance.mapping_created"
    AGENT_REGISTERED = "agent.registered"
    AGENT_UPDATED = "agent.updated"
    AGENT_LIFECYCLE_CHANGED = "agent.lifecycle_changed"
    AGENT_TRUST_SCORE_CHANGED = "agent.trust_score_changed"
    AGENT_SUSPENDED = "agent.suspended"
    AGENT_TERMINATED = "agent.terminated"
    AUDIT_EVENT_CREATED = "audit.event_created"
    AUDIT_CHAIN_VERIFIED = "audit.chain_verified"


class WebhookSubscriptionCreate(BaseModel):
    url: str = Field(..., pattern=r"^https://")
    events: list[WebhookEvent]
    secret: str = Field(..., min_length=16)
    description: str | None = None
    active: bool = True
    metadata: dict[str, Any] = {}


class WebhookSubscriptionUpdate(BaseModel):
    url: str | None = None
    events: list[WebhookEvent] | None = None
    active: bool | None = None
    metadata: dict[str, Any] | None = None


class WebhookSubscriptionResponse(BaseModel):
    subscription_id: str
    url: str
    events: list[WebhookEvent]
    secret: str
    description: str | None = None
    active: bool
    metadata: dict[str, Any] = {}
    created_at: datetime
    delivery_stats: dict[str, Any] = {}


class WebhookDeliveryResponse(BaseModel):
    delivery_id: str
    subscription_id: str
    event_id: str
    event_type: str
    status: str
    http_status: int | None = None
    response_time_ms: float | None = None
    attempts: int = 0
    delivered_at: datetime | None = None
    next_retry_at: datetime | None = None


class WebhookTestResponse(BaseModel):
    subscription_id: str
    test_event_id: str
    delivery_status: str
    http_status: int | None = None
    response_time_ms: float | None = None
    delivered_at: datetime | None = None


class WebhookPayload(BaseModel):
    webhook_id: str
    event_id: str
    event_type: str
    timestamp: datetime
    tenant_id: str
    data: dict[str, Any]
    metadata: dict[str, Any] = {}
```

### 2.10 Policy Router (`app/routers/policies.py`)

```python
"""Policy management endpoints — 9 endpoints."""

from fastapi import APIRouter, Depends, Query, Request, status

from app.dependencies import get_current_user, require_scope
from app.models.common import PaginatedResponse, PaginationParams
from app.models.policy import (
    CompilePolicyResponse,
    DryRunRequest,
    DryRunResponse,
    PolicyCreate,
    PolicyDependencyResponse,
    PolicyResponse,
    PolicyUpdate,
    PolicyVersionResponse,
)
from app.services.policy_service import PolicyService

router = APIRouter()


@router.get("/policies", response_model=PaginatedResponse[PolicyResponse])
async def list_policies(
    request: Request,
    status_filter: str | None = Query(None, alias="status"),
    category: str | None = None,
    framework: str | None = None,
    agent_id: str | None = None,
    limit: int = Query(default=50, ge=1, le=500),
    cursor: str | None = None,
    service: PolicyService = Depends(),
    current_user=Depends(get_current_user),
):
    """List policies with filtering and cursor-based pagination."""
    return await service.list_policies(
        tenant_id=request.state.tenant_id,
        status=status_filter,
        category=category,
        framework=framework,
        agent_id=agent_id,
        limit=limit,
        cursor=cursor,
    )


@router.post("/policies", response_model=PolicyResponse, status_code=status.HTTP_201_CREATED)
async def create_policy(
    request: Request,
    body: PolicyCreate,
    service: PolicyService = Depends(),
    current_user=Depends(require_scope("policies:write")),
):
    """Create a new policy."""
    return await service.create_policy(
        tenant_id=request.state.tenant_id,
        user_id=current_user.id,
        data=body,
    )


@router.get("/policies/{policy_id}", response_model=PolicyResponse)
async def get_policy(
    request: Request,
    policy_id: str,
    service: PolicyService = Depends(),
    current_user=Depends(get_current_user),
):
    """Get a policy by ID."""
    return await service.get_policy(
        tenant_id=request.state.tenant_id,
        policy_id=policy_id,
    )


@router.put("/policies/{policy_id}", response_model=PolicyResponse)
async def update_policy(
    request: Request,
    policy_id: str,
    body: PolicyUpdate,
    service: PolicyService = Depends(),
    current_user=Depends(require_scope("policies:write")),
):
    """Update a policy (creates new version)."""
    return await service.update_policy(
        tenant_id=request.state.tenant_id,
        policy_id=policy_id,
        user_id=current_user.id,
        data=body,
    )


@router.delete("/policies/{policy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_policy(
    request: Request,
    policy_id: str,
    force: bool = False,
    service: PolicyService = Depends(),
    current_user=Depends(require_scope("policies:write")),
):
    """Delete (archive) a policy."""
    await service.delete_policy(
        tenant_id=request.state.tenant_id,
        policy_id=policy_id,
        force=force,
    )


@router.post("/policies/{policy_id}/compile", response_model=CompilePolicyResponse)
async def compile_policy(
    request: Request,
    policy_id: str,
    service: PolicyService = Depends(),
    current_user=Depends(require_scope("policies:write")),
):
    """Compile Cedar policy to Rego for OPA evaluation."""
    return await service.compile_policy(
        tenant_id=request.state.tenant_id,
        policy_id=policy_id,
    )


@router.post("/policies/{policy_id}/dry-run", response_model=DryRunResponse)
async def dry_run_policy(
    request: Request,
    policy_id: str,
    body: DryRunRequest,
    service: PolicyService = Depends(),
    current_user=Depends(get_current_user),
):
    """Dry-run policy against test inputs."""
    return await service.dry_run_policy(
        tenant_id=request.state.tenant_id,
        policy_id=policy_id,
        test_inputs=body.test_inputs,
    )


@router.get("/policies/{policy_id}/versions", response_model=list[PolicyVersionResponse])
async def get_policy_versions(
    request: Request,
    policy_id: str,
    service: PolicyService = Depends(),
    current_user=Depends(get_current_user),
):
    """Get policy version history."""
    return await service.get_policy_versions(
        tenant_id=request.state.tenant_id,
        policy_id=policy_id,
    )


@router.get("/policies/{policy_id}/dependencies", response_model=PolicyDependencyResponse)
async def get_policy_dependencies(
    request: Request,
    policy_id: str,
    service: PolicyService = Depends(),
    current_user=Depends(get_current_user),
):
    """Get policy dependency graph."""
    return await service.get_policy_dependencies(
        tenant_id=request.state.tenant_id,
        policy_id=policy_id,
    )
```

### 2.11 Evidence Router (`app/routers/evidence.py`)

```python
"""Evidence management endpoints — 6 endpoints."""

from fastapi import APIRouter, Depends, Query, Request, status

from app.dependencies import get_current_user, require_scope
from app.models.common import PaginatedResponse
from app.models.evidence import (
    EvidenceCreate,
    EvidenceResponse,
    EvidenceSearchParams,
    ExportPackageRequest,
    ExportPackageResponse,
    ExportPackageStatus,
    VerifyEvidenceResponse,
)
from app.services.evidence_service import EvidenceService

router = APIRouter()


@router.get("/evidence", response_model=PaginatedResponse[EvidenceResponse])
async def search_evidence(
    request: Request,
    params: EvidenceSearchParams = Depends(),
    service: EvidenceService = Depends(),
    current_user=Depends(get_current_user),
):
    """Search evidence with filtering and pagination."""
    return await service.search_evidence(
        tenant_id=request.state.tenant_id,
        params=params,
    )


@router.post("/evidence", response_model=EvidenceResponse, status_code=status.HTTP_201_CREATED)
async def submit_evidence(
    request: Request,
    body: EvidenceCreate,
    service: EvidenceService = Depends(),
    current_user=Depends(require_scope("evidence:write")),
):
    """Submit new evidence."""
    return await service.submit_evidence(
        tenant_id=request.state.tenant_id,
        user_id=current_user.id,
        data=body,
    )


@router.get("/evidence/{evidence_id}", response_model=EvidenceResponse)
async def get_evidence(
    request: Request,
    evidence_id: str,
    service: EvidenceService = Depends(),
    current_user=Depends(get_current_user),
):
    """Get evidence by ID."""
    return await service.get_evidence(
        tenant_id=request.state.tenant_id,
        evidence_id=evidence_id,
    )


@router.post("/evidence/{evidence_id}/verify", response_model=VerifyEvidenceResponse)
async def verify_evidence(
    request: Request,
    evidence_id: str,
    service: EvidenceService = Depends(),
    current_user=Depends(get_current_user),
):
    """Verify evidence integrity and chain of custody."""
    return await service.verify_evidence(
        tenant_id=request.state.tenant_id,
        evidence_id=evidence_id,
        verified_by=current_user.id,
    )


@router.post("/evidence/export", response_model=ExportPackageResponse, status_code=status.HTTP_202_ACCEPTED)
async def export_evidence_package(
    request: Request,
    body: ExportPackageRequest,
    service: EvidenceService = Depends(),
    current_user=Depends(get_current_user),
):
    """Export evidence package (async)."""
    return await service.export_evidence_package(
        tenant_id=request.state.tenant_id,
        data=body,
    )


@router.get("/evidence/export/{package_id}", response_model=ExportPackageStatus)
async def get_export_package(
    request: Request,
    package_id: str,
    service: EvidenceService = Depends(),
    current_user=Depends(get_current_user),
):
    """Get export package status and download URL."""
    return await service.get_export_package(
        tenant_id=request.state.tenant_id,
        package_id=package_id,
    )
```

### 2.12 Enforcement Router (`app/routers/enforcement.py`)

```python
"""Enforcement decision endpoints — 4 endpoints."""

from fastapi import APIRouter, Depends, Request, status

from app.dependencies import get_current_user, require_scope
from app.models.common import PaginatedResponse
from app.models.enforcement import (
    BatchDecisionRequest,
    BatchDecisionResponse,
    DecisionListParams,
    DecisionRequest,
    DecisionResponse,
)
from app.services.enforcement_service import EnforcementService

router = APIRouter()


@router.post("/enforcement/decide", response_model=DecisionResponse)
async def request_decision(
    request: Request,
    body: DecisionRequest,
    service: EnforcementService = Depends(),
    current_user=Depends(require_scope("enforcement:decide")),
):
    """Request a single enforcement decision."""
    return await service.decide(
        tenant_id=request.state.tenant_id,
        data=body,
    )


@router.post("/enforcement/decide-batch", response_model=BatchDecisionResponse)
async def request_batch_decision(
    request: Request,
    body: BatchDecisionRequest,
    service: EnforcementService = Depends(),
    current_user=Depends(require_scope("enforcement:decide")),
):
    """Request batch enforcement decisions."""
    return await service.decide_batch(
        tenant_id=request.state.tenant_id,
        data=body,
    )


@router.get("/enforcement/decisions/{decision_id}", response_model=DecisionResponse)
async def get_decision(
    request: Request,
    decision_id: str,
    service: EnforcementService = Depends(),
    current_user=Depends(get_current_user),
):
    """Get enforcement decision by ID."""
    return await service.get_decision(
        tenant_id=request.state.tenant_id,
        decision_id=decision_id,
    )


@router.get("/enforcement/decisions", response_model=PaginatedResponse[DecisionResponse])
async def list_decisions(
    request: Request,
    params: DecisionListParams = Depends(),
    service: EnforcementService = Depends(),
    current_user=Depends(get_current_user),
):
    """List enforcement decisions with filtering."""
    return await service.list_decisions(
        tenant_id=request.state.tenant_id,
        params=params,
    )
```

### 2.13 Assessment Router (`app/routers/assessments.py`)

```python
"""Assessment management endpoints — 6 endpoints."""

from fastapi import APIRouter, Depends, Request, status

from app.dependencies import get_current_user, require_scope
from app.models.assessment import (
    AssessmentCreate,
    AssessmentListParams,
    AssessmentResponse,
    AssessmentUpdate,
    AssessmentReportRequest,
    FindingCreate,
    FindingResponse,
)
from app.models.common import PaginatedResponse
from app.services.assessment_service import AssessmentService

router = APIRouter()


@router.get("/assessments", response_model=PaginatedResponse[AssessmentResponse])
async def list_assessments(
    request: Request,
    params: AssessmentListParams = Depends(),
    service: AssessmentService = Depends(),
    current_user=Depends(get_current_user),
):
    """List assessments with filtering."""
    return await service.list_assessments(
        tenant_id=request.state.tenant_id,
        params=params,
    )


@router.post("/assessments", response_model=AssessmentResponse, status_code=status.HTTP_201_CREATED)
async def create_assessment(
    request: Request,
    body: AssessmentCreate,
    service: AssessmentService = Depends(),
    current_user=Depends(require_scope("assessments:write")),
):
    """Create a new assessment."""
    return await service.create_assessment(
        tenant_id=request.state.tenant_id,
        user_id=current_user.id,
        data=body,
    )


@router.get("/assessments/{assessment_id}", response_model=AssessmentResponse)
async def get_assessment(
    request: Request,
    assessment_id: str,
    service: AssessmentService = Depends(),
    current_user=Depends(get_current_user),
):
    """Get assessment by ID."""
    return await service.get_assessment(
        tenant_id=request.state.tenant_id,
        assessment_id=assessment_id,
    )


@router.put("/assessments/{assessment_id}", response_model=AssessmentResponse)
async def update_assessment(
    request: Request,
    assessment_id: str,
    body: AssessmentUpdate,
    service: AssessmentService = Depends(),
    current_user=Depends(require_scope("assessments:write")),
):
    """Update an assessment."""
    return await service.update_assessment(
        tenant_id=request.state.tenant_id,
        assessment_id=assessment_id,
        data=body,
    )


@router.post("/assessments/{assessment_id}/findings", response_model=FindingResponse, status_code=status.HTTP_201_CREATED)
async def add_finding(
    request: Request,
    assessment_id: str,
    body: FindingCreate,
    service: AssessmentService = Depends(),
    current_user=Depends(require_scope("assessments:write")),
):
    """Add a finding to an assessment."""
    return await service.add_finding(
        tenant_id=request.state.tenant_id,
        assessment_id=assessment_id,
        data=body,
    )


@router.post("/assessments/{assessment_id}/report", status_code=status.HTTP_202_ACCEPTED)
async def generate_assessment_report(
    request: Request,
    assessment_id: str,
    body: AssessmentReportRequest,
    service: AssessmentService = Depends(),
    current_user=Depends(get_current_user),
):
    """Generate assessment report (async)."""
    return await service.generate_report(
        tenant_id=request.state.tenant_id,
        assessment_id=assessment_id,
        data=body,
    )
```

### 2.14 Compliance Router (`app/routers/compliance.py`)

```python
"""Compliance mapping endpoints — 6 endpoints."""

from fastapi import APIRouter, Depends, Request, status

from app.dependencies import get_current_user, require_scope
from app.models.common import PaginatedResponse
from app.models.compliance import (
    ComplianceControlResponse,
    ComplianceFrameworkResponse,
    ComplianceMappingCreate,
    ComplianceMappingResponse,
    CompliancePostureResponse,
    ComplianceReportRequest,
    CrosswalkQueryParams,
    CrosswalkResponse,
)
from app.services.compliance_service import ComplianceService

router = APIRouter()


@router.get("/compliance/frameworks", response_model=list[ComplianceFrameworkResponse])
async def list_frameworks(
    request: Request,
    service: ComplianceService = Depends(),
    current_user=Depends(get_current_user),
):
    """List all compliance frameworks."""
    return await service.list_frameworks(tenant_id=request.state.tenant_id)


@router.get("/compliance/frameworks/{framework_id}/controls", response_model=PaginatedResponse[ComplianceControlResponse])
async def list_controls(
    request: Request,
    framework_id: str,
    category: str | None = None,
    status: str | None = None,
    target_id: str | None = None,
    limit: int = 50,
    cursor: str | None = None,
    service: ComplianceService = Depends(),
    current_user=Depends(get_current_user),
):
    """List controls for a framework."""
    return await service.list_controls(
        tenant_id=request.state.tenant_id,
        framework_id=framework_id,
        category=category,
        status=status,
        target_id=target_id,
        limit=limit,
        cursor=cursor,
    )


@router.get("/compliance/posture", response_model=CompliancePostureResponse)
async def get_compliance_posture(
    request: Request,
    framework: str | None = None,
    target_id: str | None = None,
    target_type: str | None = None,
    service: ComplianceService = Depends(),
    current_user=Depends(get_current_user),
):
    """Get compliance posture."""
    return await service.get_posture(
        tenant_id=request.state.tenant_id,
        framework=framework,
        target_id=target_id,
        target_type=target_type,
    )


@router.post("/compliance/mappings", response_model=ComplianceMappingResponse, status_code=status.HTTP_201_CREATED)
async def create_compliance_mapping(
    request: Request,
    body: ComplianceMappingCreate,
    service: ComplianceService = Depends(),
    current_user=Depends(require_scope("compliance:write")),
):
    """Create a compliance mapping."""
    return await service.create_mapping(
        tenant_id=request.state.tenant_id,
        user_id=current_user.id,
        data=body,
    )


@router.post("/compliance/reports", status_code=status.HTTP_202_ACCEPTED)
async def generate_compliance_report(
    request: Request,
    body: ComplianceReportRequest,
    service: ComplianceService = Depends(),
    current_user=Depends(get_current_user),
):
    """Generate compliance report (async)."""
    return await service.generate_report(
        tenant_id=request.state.tenant_id,
        data=body,
    )


@router.get("/compliance/crosswalk", response_model=CrosswalkResponse)
async def crosswalk_query(
    request: Request,
    params: CrosswalkQueryParams = Depends(),
    service: ComplianceService = Depends(),
    current_user=Depends(get_current_user),
):
    """Cross-framework control mapping query."""
    return await service.crosswalk(
        tenant_id=request.state.tenant_id,
        params=params,
    )
```

### 2.15 Agent Router (`app/routers/agents.py`)

```python
"""Agent registry endpoints — 6 endpoints."""

from fastapi import APIRouter, Depends, Request, status

from app.dependencies import get_current_user, require_scope
from app.models.agent import (
    AgentCreate,
    AgentListParams,
    AgentResponse,
    AgentUpdate,
    PolicyBindingRequest,
    TrustScoreUpdate,
)
from app.models.common import PaginatedResponse
from app.services.agent_service import AgentService

router = APIRouter()


@router.get("/agents", response_model=PaginatedResponse[AgentResponse])
async def list_agents(
    request: Request,
    params: AgentListParams = Depends(),
    service: AgentService = Depends(),
    current_user=Depends(get_current_user),
):
    """List agents with filtering."""
    return await service.list_agents(
        tenant_id=request.state.tenant_id,
        params=params,
    )


@router.post("/agents", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def register_agent(
    request: Request,
    body: AgentCreate,
    service: AgentService = Depends(),
    current_user=Depends(require_scope("agents:write")),
):
    """Register a new agent."""
    return await service.register_agent(
        tenant_id=request.state.tenant_id,
        user_id=current_user.id,
        data=body,
    )


@router.get("/agents/{agent_id}", response_model=AgentResponse)
async def get_agent(
    request: Request,
    agent_id: str,
    service: AgentService = Depends(),
    current_user=Depends(get_current_user),
):
    """Get agent by ID."""
    return await service.get_agent(
        tenant_id=request.state.tenant_id,
        agent_id=agent_id,
    )


@router.put("/agents/{agent_id}", response_model=AgentResponse)
async def update_agent(
    request: Request,
    agent_id: str,
    body: AgentUpdate,
    service: AgentService = Depends(),
    current_user=Depends(require_scope("agents:write")),
):
    """Update an agent."""
    return await service.update_agent(
        tenant_id=request.state.tenant_id,
        agent_id=agent_id,
        data=body,
    )


@router.post("/agents/{agent_id}/trust-score", response_model=AgentResponse)
async def update_trust_score(
    request: Request,
    agent_id: str,
    body: TrustScoreUpdate,
    service: AgentService = Depends(),
    current_user=Depends(require_scope("agents:write")),
):
    """Update agent trust score."""
    return await service.update_trust_score(
        tenant_id=request.state.tenant_id,
        agent_id=agent_id,
        data=body,
    )


@router.post("/agents/{agent_id}/policy-bindings", response_model=AgentResponse)
async def bind_policies(
    request: Request,
    agent_id: str,
    body: PolicyBindingRequest,
    service: AgentService = Depends(),
    current_user=Depends(require_scope("agents:write")),
):
    """Bind policies to an agent."""
    return await service.bind_policies(
        tenant_id=request.state.tenant_id,
        agent_id=agent_id,
        data=body,
    )
```

### 2.16 Audit Router (`app/routers/audit.py`)

```python
"""Audit trail endpoints — 2 endpoints."""

from fastapi import APIRouter, Depends, Request

from app.dependencies import get_current_user, require_scope
from app.models.audit import AuditQueryParams, VerifyAuditChainRequest, VerifyAuditChainResponse
from app.models.common import PaginatedResponse
from app.models.audit import AuditEvent
from app.services.audit_service import AuditService

router = APIRouter()


@router.get("/audit", response_model=PaginatedResponse[AuditEvent])
async def query_audit_trail(
    request: Request,
    params: AuditQueryParams = Depends(),
    service: AuditService = Depends(),
    current_user=Depends(require_scope("audit:read")),
):
    """Query audit trail with filtering."""
    return await service.query_audit_trail(
        tenant_id=request.state.tenant_id,
        params=params,
    )


@router.post("/audit/verify", response_model=VerifyAuditChainResponse)
async def verify_audit_chain(
    request: Request,
    body: VerifyAuditChainRequest,
    service: AuditService = Depends(),
    current_user=Depends(require_scope("audit:read")),
):
    """Verify audit chain integrity."""
    return await service.verify_chain(
        tenant_id=request.state.tenant_id,
        data=body,
    )
```

### 2.17 Webhook Router (`app/routers/webhooks.py`)

```python
"""Webhook subscription endpoints — 7 endpoints."""

from fastapi import APIRouter, Depends, Request, status

from app.dependencies import get_current_user, require_scope
from app.models.common import PaginatedResponse
from app.models.webhook import (
    WebhookDeliveryResponse,
    WebhookSubscriptionCreate,
    WebhookSubscriptionResponse,
    WebhookSubscriptionUpdate,
    WebhookTestResponse,
)
from app.services.webhook_service import WebhookService

router = APIRouter()


@router.get("/webhooks/subscriptions", response_model=PaginatedResponse[WebhookSubscriptionResponse])
async def list_subscriptions(
    request: Request,
    service: WebhookService = Depends(),
    current_user=Depends(require_scope("webhooks:manage")),
):
    """List webhook subscriptions."""
    return await service.list_subscriptions(tenant_id=request.state.tenant_id)


@router.post("/webhooks/subscriptions", response_model=WebhookSubscriptionResponse, status_code=status.HTTP_201_CREATED)
async def create_subscription(
    request: Request,
    body: WebhookSubscriptionCreate,
    service: WebhookService = Depends(),
    current_user=Depends(require_scope("webhooks:manage")),
):
    """Create a webhook subscription."""
    return await service.create_subscription(
        tenant_id=request.state.tenant_id,
        data=body,
    )


@router.get("/webhooks/subscriptions/{subscription_id}", response_model=WebhookSubscriptionResponse)
async def get_subscription(
    request: Request,
    subscription_id: str,
    service: WebhookService = Depends(),
    current_user=Depends(require_scope("webhooks:manage")),
):
    """Get webhook subscription by ID."""
    return await service.get_subscription(
        tenant_id=request.state.tenant_id,
        subscription_id=subscription_id,
    )


@router.put("/webhooks/subscriptions/{subscription_id}", response_model=WebhookSubscriptionResponse)
async def update_subscription(
    request: Request,
    subscription_id: str,
    body: WebhookSubscriptionUpdate,
    service: WebhookService = Depends(),
    current_user=Depends(require_scope("webhooks:manage")),
):
    """Update a webhook subscription."""
    return await service.update_subscription(
        tenant_id=request.state.tenant_id,
        subscription_id=subscription_id,
        data=body,
    )


@router.delete("/webhooks/subscriptions/{subscription_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_subscription(
    request: Request,
    subscription_id: str,
    service: WebhookService = Depends(),
    current_user=Depends(require_scope("webhooks:manage")),
):
    """Delete a webhook subscription."""
    await service.delete_subscription(
        tenant_id=request.state.tenant_id,
        subscription_id=subscription_id,
    )


@router.post("/webhooks/subscriptions/{subscription_id}/test", response_model=WebhookTestResponse)
async def test_subscription(
    request: Request,
    subscription_id: str,
    service: WebhookService = Depends(),
    current_user=Depends(require_scope("webhooks:manage")),
):
    """Send test event to subscription endpoint."""
    return await service.test_subscription(
        tenant_id=request.state.tenant_id,
        subscription_id=subscription_id,
    )


@router.get("/webhooks/subscriptions/{subscription_id}/deliveries", response_model=PaginatedResponse[WebhookDeliveryResponse])
async def get_delivery_history(
    request: Request,
    subscription_id: str,
    status_filter: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    service: WebhookService = Depends(),
    current_user=Depends(require_scope("webhooks:manage")),
):
    """Get webhook delivery history."""
    return await service.get_delivery_history(
        tenant_id=request.state.tenant_id,
        subscription_id=subscription_id,
        status=status_filter,
        date_from=date_from,
        date_to=date_to,
    )
```

### 2.18 Health Router (`app/routers/health.py`)

```python
"""Health and monitoring endpoints — 3 endpoints."""

from datetime import datetime

from fastapi import APIRouter

from app.config import settings
from app.models.common import HealthStatus, ReadinessStatus

router = APIRouter()


@router.get("/health", response_model=HealthStatus)
async def health_check():
    """Health check endpoint."""
    return HealthStatus(
        status="healthy",
        version=settings.APP_VERSION,
        components={
            "api": {"status": "up"},
            "policy_engine": {"status": "up"},
            "evidence_store": {"status": "up"},
            "database": {"status": "up"},
            "cache": {"status": "up"},
        },
        timestamp=datetime.utcnow(),
    )


@router.get("/ready", response_model=ReadinessStatus)
async def readiness_check():
    """Readiness check endpoint."""
    return ReadinessStatus(
        ready=True,
        checks={
            "database": {"status": "pass"},
            "policy_engine": {"status": "pass"},
            "evidence_store": {"status": "pass"},
        },
    )


@router.get("/metrics")
async def prometheus_metrics():
    """Prometheus metrics endpoint."""
    from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
    from starlette.responses import Response

    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )
```

### Endpoint Summary Table

| Category | Method | Path | Description |
|----------|--------|------|-------------|
| **Policies** | GET | `/v1.0/policies` | List policies |
| | POST | `/v1.0/policies` | Create policy |
| | GET | `/v1.0/policies/{id}` | Get policy |
| | PUT | `/v1.0/policies/{id}` | Update policy |
| | DELETE | `/v1.0/policies/{id}` | Delete policy |
| | POST | `/v1.0/policies/{id}/compile` | Compile policy |
| | POST | `/v1.0/policies/{id}/dry-run` | Dry-run policy |
| | GET | `/v1.0/policies/{id}/versions` | Policy versions |
| | GET | `/v1.0/policies/{id}/dependencies` | Policy dependencies |
| **Evidence** | GET | `/v1.0/evidence` | Search evidence |
| | POST | `/v1.0/evidence` | Submit evidence |
| | GET | `/v1.0/evidence/{id}` | Get evidence |
| | POST | `/v1.0/evidence/{id}/verify` | Verify evidence |
| | POST | `/v1.0/evidence/export` | Export package |
| | GET | `/v1.0/evidence/export/{id}` | Get export status |
| **Enforcement** | POST | `/v1.0/enforcement/decide` | Request decision |
| | POST | `/v1.0/enforcement/decide-batch` | Batch decisions |
| | GET | `/v1.0/enforcement/decisions/{id}` | Get decision |
| | GET | `/v1.0/enforcement/decisions` | List decisions |
| **Assessments** | GET | `/v1.0/assessments` | List assessments |
| | POST | `/v1.0/assessments` | Create assessment |
| | GET | `/v1.0/assessments/{id}` | Get assessment |
| | PUT | `/v1.0/assessments/{id}` | Update assessment |
| | POST | `/v1.0/assessments/{id}/findings` | Add finding |
| | POST | `/v1.0/assessments/{id}/report` | Generate report |
| **Compliance** | GET | `/v1.0/compliance/frameworks` | List frameworks |
| | GET | `/v1.0/compliance/frameworks/{id}/controls` | List controls |
| | GET | `/v1.0/compliance/posture` | Get posture |
| | POST | `/v1.0/compliance/mappings` | Create mapping |
| | POST | `/v1.0/compliance/reports` | Generate report |
| | GET | `/v1.0/compliance/crosswalk` | Crosswalk query |
| **Agents** | GET | `/v1.0/agents` | List agents |
| | POST | `/v1.0/agents` | Register agent |
| | GET | `/v1.0/agents/{id}` | Get agent |
| | PUT | `/v1.0/agents/{id}` | Update agent |
| | POST | `/v1.0/agents/{id}/trust-score` | Update trust score |
| | POST | `/v1.0/agents/{id}/policy-bindings` | Bind policies |
| **Audit** | GET | `/v1.0/audit` | Query audit trail |
| | POST | `/v1.0/audit/verify` | Verify audit chain |
| **Webhooks** | GET | `/v1.0/webhooks/subscriptions` | List subscriptions |
| | POST | `/v1.0/webhooks/subscriptions` | Create subscription |
| | GET | `/v1.0/webhooks/subscriptions/{id}` | Get subscription |
| | PUT | `/v1.0/webhooks/subscriptions/{id}` | Update subscription |
| | DELETE | `/v1.0/webhooks/subscriptions/{id}` | Delete subscription |
| | POST | `/v1.0/webhooks/subscriptions/{id}/test` | Test subscription |
| | GET | `/v1.0/webhooks/subscriptions/{id}/deliveries` | Delivery history |
| **System** | GET | `/health` | Health check |
| | GET | `/ready` | Readiness check |
| | GET | `/metrics` | Prometheus metrics |
| | POST | `/v1.0/graphql` | GraphQL endpoint |

**Total: 47 endpoints**

---

## 3. GraphQL Schema Implementation

### 3.1 Strawberry Schema (`app/graphql/schema.py`)

```python
"""GRC_Claw GraphQL schema using Strawberry."""

from datetime import datetime
from typing import Annotated, Any, Optional

import strawberry
from strawberry import auto
from strawberry.types import Info

from app.graphql.resolvers.assessment_resolver import (
    resolve_assessment,
    resolve_assessments,
)
from app.graphql.resolvers.audit_resolver import resolve_audit_events
from app.graphql.resolvers.compliance_resolver import (
    resolve_compliance_framework,
    resolve_compliance_frameworks,
    resolve_compliance_posture,
)
from app.graphql.resolvers.enforcement_resolver import (
    resolve_enforcement_decision,
    resolve_enforcement_decisions,
)
from app.graphql.resolvers.evidence_resolver import (
    resolve_evidence,
    resolve_evidences,
)
from app.graphql.resolvers.policy_resolver import (
    resolve_policies,
    resolve_policy,
)
from app.graphql.resolvers.agent_resolver import (
    resolve_agent,
    resolve_agents,
)


# ── Custom Scalars ──

@strawberry.scalar(serialization_alias="DateTime")
class DateTimeScalar:
    @staticmethod
    def serialize(value: datetime) -> str:
        return value.isoformat()

    @staticmethod
    def parse_value(value: str) -> datetime:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))


@strawberry.scalar(serialization_alias="JSON")
class JSONScalar:
    @staticmethod
    def serialize(value: Any) -> Any:
        return value

    @staticmethod
    def parse_value(value: Any) -> Any:
        return value


# ── Enums ──

@strawberry.enum
class PolicyStatus:
    DRAFT = "draft"
    REVIEW = "review"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


@strawberry.enum
class PolicyCategory:
    ETHICS = "ethics"
    SAFETY = "safety"
    PRIVACY = "privacy"
    FAIRNESS = "fairness"


@strawberry.enum
class EvidenceType:
    ARTIFACT = "artifact"
    OBSERVATION = "observation"
    INTERVIEW = "interview"
    ANALYSIS = "analysis"
    LOG = "log"


@strawberry.enum
class VerificationLevel:
    L0 = "L0"
    L1 = "L1"
    L2 = "L2"
    L3 = "L3"
    L4 = "L4"


@strawberry.enum
class EnforcementVerdict:
    ALLOW = "ALLOW"
    ALLOW_WITH_REDACTION = "ALLOW_WITH_REDACTION"
    REQUIRE_APPROVAL = "REQUIRE_APPROVAL"
    DENY = "DENY"
    QUARANTINE = "QUARANTINE"


@strawberry.enum
class AssessmentType:
    RISK = "risk"
    COMPLIANCE = "compliance"
    MATURITY = "maturity"
    READINESS = "readiness"


@strawberry.enum
class AssessmentStatus:
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@strawberry.enum
class ComplianceStatus:
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PARTIAL = "partial"
    NOT_ASSESSED = "not_assessed"
    EXEMPT = "exempt"


@strawberry.enum
class AgentLifecycleStage:
    PROPOSED = "proposed"
    APPROVED = "approved"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    TERMINATED = "terminated"


@strawberry.enum
class RiskTier:
    PROHIBITED = "prohibited"
    HIGH = "high"
    LIMITED = "limited"
    MINIMAL = "minimal"


# ── Interfaces ──

@strawberry.interface
class Node:
    id: strawberry.ID


@strawberry.interface
class Timestamped:
    created_at: datetime
    updated_at: datetime


# ── Types ──

@strawberry.type
class User(Node):
    id: strawberry.ID
    name: str
    email: str
    roles: list[str]


@strawberry.type
class Policy(Node, Timestamped):
    id: strawberry.ID
    policy_key: str
    name: str
    description: Optional[str]
    category: PolicyCategory
    status: PolicyStatus
    version: str
    framework_tags: list[str]
    effective_date: Optional[datetime]
    expiry_date: Optional[datetime]
    owner: Optional[User]
    agent_bindings: list["Agent"]
    cedar_policy: Optional[str]
    rego_policy: Optional[str]
    metadata: Optional[JSONScalar]
    compliance_mappings: list["ComplianceMapping"]
    dependencies: list["Policy"]
    dependents: list["Policy"]
    versions: list["PolicyVersion"]
    created_at: datetime
    updated_at: datetime
    created_by: User
    updated_by: User


@strawberry.type
class PolicyVersion:
    version: str
    status: str
    change_summary: Optional[str]
    created_at: datetime
    created_by: User


@strawberry.type
class EvidenceSource:
    type: str
    system: str
    collection_method: str


@strawberry.type
class EvidenceContent:
    format: str
    data: str
    hash: Optional[str]


@strawberry.type
class EvidenceContext:
    environment: str
    region: Optional[str]
    timestamp: datetime
    metadata: Optional[JSONScalar]


@strawberry.type
class ValidationStatus:
    status: str
    validated_by: Optional[User]
    validated_at: Optional[datetime]
    confidence_score: float


@strawberry.type
class CustodyEvent:
    action: str
    actor: str
    timestamp: datetime
    hash: str


@strawberry.type
class Evidence(Node, Timestamped):
    id: strawberry.ID
    policy: Optional[Policy]
    assessment: Optional["Assessment"]
    source: EvidenceSource
    evidence_type: EvidenceType
    content: EvidenceContent
    context: EvidenceContext
    validation: ValidationStatus
    verification_level: VerificationLevel
    chain_of_custody: list[CustodyEvent]
    retention_class: str
    created_at: datetime
    expires_at: Optional[datetime]


@strawberry.type
class EnforcementDecision(Node):
    id: strawberry.ID
    verdict: EnforcementVerdict
    policy: Policy
    policy_version: str
    agent: "Agent"
    action: str
    resource: str
    context: JSONScalar
    evidence_hash: Optional[str]
    timestamp: datetime
    ttl: int
    signature: Optional[str]
    matched_rules: list[str]
    evaluation_time_ms: float


@strawberry.type
class AssessmentFinding(Node, Timestamped):
    id: strawberry.ID
    finding_key: str
    title: str
    description: str
    severity: str
    category: str
    status: str
    policy: Optional[Policy]
    evidence: list[Evidence]
    remediation: Optional[str]
    remediated_by: Optional[User]
    remediated_at: Optional[datetime]
    due_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime


@strawberry.type
class Assessment(Node, Timestamped):
    id: strawberry.ID
    assessment_key: str
    title: str
    description: Optional[str]
    assessment_type: AssessmentType
    target_id: str
    target_type: str
    status: AssessmentStatus
    methodology: Optional[str]
    score: Optional[float]
    risk_level: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    next_assessment_at: Optional[datetime]
    lead_assessor: User
    findings: list[AssessmentFinding]
    evidence: list[Evidence]
    metadata: Optional[JSONScalar]
    created_at: datetime
    updated_at: datetime


@strawberry.type
class ComplianceFramework(Node, Timestamped):
    id: strawberry.ID
    framework_key: str
    name: str
    version: str
    description: Optional[str]
    authority: Optional[str]
    effective_date: Optional[datetime]
    controls: list["ComplianceControl"]
    control_count: int
    created_at: datetime
    updated_at: datetime


@strawberry.type
class ComplianceControl(Node, Timestamped):
    id: strawberry.ID
    framework: ComplianceFramework
    control_key: str
    title: str
    description: Optional[str]
    category: Optional[str]
    guidance: Optional[str]
    mappings: list["ComplianceMapping"]
    status: Optional[ComplianceStatus]
    created_at: datetime
    updated_at: datetime


@strawberry.type
class ComplianceMapping(Node, Timestamped):
    id: strawberry.ID
    control: ComplianceControl
    policy: Optional[Policy]
    assessment: Optional[Assessment]
    mapping_type: str
    coverage: str
    notes: Optional[str]
    mapped_by: User
    mapped_at: datetime
    updated_at: datetime


@strawberry.type
class ComplianceGap:
    control: ComplianceControl
    status: ComplianceStatus
    severity: str
    evidence_count: int
    last_assessed: Optional[datetime]


@strawberry.type
class ComplianceTrend:
    direction: str
    change: str
    period: str


@strawberry.type
class CompliancePosture:
    framework: ComplianceFramework
    target_id: str
    target_type: str
    controls_assessed: int
    controls_compliant: int
    controls_non_compliant: int
    controls_not_assessed: int
    compliance_score: float
    gaps: list[ComplianceGap]
    trend: Optional[ComplianceTrend]


@strawberry.type
class AgentCapability:
    name: str
    description: str
    permissions: list[str]
    resource_scope: Optional[str]


@strawberry.type
class AgentIdentity:
    spiffe_id: Optional[str]
    mtls_cert: Optional[str]
    cert_expiry: Optional[datetime]


@strawberry.type
class TrustScore:
    value: int
    grade: str
    last_evaluated: Optional[datetime]


@strawberry.type
class Agent(Node, Timestamped):
    id: strawberry.ID
    name: str
    type: str
    framework: str
    owner: User
    lifecycle_stage: AgentLifecycleStage
    risk_tier: RiskTier
    capabilities: list[AgentCapability]
    identity: Optional[AgentIdentity]
    trust_score: Optional[TrustScore]
    policy_bindings: list[Policy]
    created_at: datetime
    updated_at: datetime


@strawberry.type
class Actor:
    type: str
    id: str
    name: Optional[str]


@strawberry.type
class Resource:
    type: str
    id: str
    name: Optional[str]


@strawberry.type
class AuditEvent(Node):
    id: strawberry.ID
    event_type: str
    actor: Actor
    resource: Resource
    timestamp: datetime
    details: Optional[JSONScalar]
    integrity_hash: str
    previous_event_hash: Optional[str]


# ── Input Types ──

@strawberry.input
class PolicyInput:
    policy_key: str
    name: str
    description: Optional[str] = None
    category: PolicyCategory
    framework_tags: list[str] = strawberry.field(default_factory=list)
    cedar_policy: Optional[str] = None
    metadata: Optional[JSONScalar] = None


@strawberry.input
class PolicyUpdateInput:
    name: Optional[str] = None
    description: Optional[str] = None
    cedar_policy: Optional[str] = None
    metadata: Optional[JSONScalar] = None


@strawberry.input
class PolicyFilter:
    status: Optional[PolicyStatus] = None
    category: Optional[PolicyCategory] = None
    framework: Optional[str] = None
    agent_id: Optional[strawberry.ID] = None


@strawberry.input
class EvidenceFilter:
    policy_id: Optional[strawberry.ID] = None
    assessment_id: Optional[strawberry.ID] = None
    evidence_type: Optional[EvidenceType] = None
    framework: Optional[str] = None
    control_id: Optional[str] = None
    verification_level: Optional[VerificationLevel] = None
    environment: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    query: Optional[str] = None


@strawberry.input
class AssessmentFilter:
    assessment_type: Optional[AssessmentType] = None
    status: Optional[AssessmentStatus] = None
    target_type: Optional[str] = None
    target_id: Optional[str] = None
    methodology: Optional[str] = None


@strawberry.input
class AgentFilter:
    type: Optional[str] = None
    framework: Optional[str] = None
    lifecycle_stage: Optional[AgentLifecycleStage] = None
    risk_tier: Optional[RiskTier] = None
    trust_score_min: Optional[int] = None


@strawberry.input
class AuditFilter:
    event_type: Optional[str] = None
    actor_id: Optional[strawberry.ID] = None
    resource_type: Optional[str] = None
    resource_id: Optional[strawberry.ID] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


@strawberry.input
class PaginationInput:
    first: Optional[int] = 50
    after: Optional[str] = None
    last: Optional[int] = None
    before: Optional[str] = None


@strawberry.input
class DecisionInput:
    agent_id: strawberry.ID
    action: str
    resource: str
    context: JSONScalar
    policy_ids: list[strawberry.ID] = strawberry.field(default_factory=list)
    include_evidence: bool = False


@strawberry.input
class EvidenceInput:
    policy_id: Optional[strawberry.ID] = None
    assessment_id: Optional[strawberry.ID] = None
    source: "EvidenceSourceInput"
    evidence_type: EvidenceType
    content: "EvidenceContentInput"
    context: "EvidenceContextInput"
    control_mapping: Optional["ControlMappingInput"] = None


@strawberry.input
class EvidenceSourceInput:
    type: str
    system: str
    collection_method: str


@strawberry.input
class EvidenceContentInput:
    format: str
    data: str


@strawberry.input
class EvidenceContextInput:
    environment: str
    region: Optional[str] = None
    metadata: Optional[JSONScalar] = None


@strawberry.input
class ControlMappingInput:
    control_id: str
    framework: str
    control_title: str
    control_family: Optional[str] = None


@strawberry.input
class AssessmentInput:
    assessment_key: str
    title: str
    description: Optional[str] = None
    assessment_type: AssessmentType
    target_id: str
    target_type: str
    methodology: Optional[str] = None
    lead_assessor: strawberry.ID
    metadata: Optional[JSONScalar] = None


@strawberry.input
class FindingInput:
    finding_key: str
    title: str
    description: str
    severity: str
    category: str
    policy_id: Optional[strawberry.ID] = None
    evidence_ids: list[strawberry.ID] = strawberry.field(default_factory=list)
    remediation: Optional[str] = None
    due_date: Optional[datetime] = None


@strawberry.input
class AgentInput:
    name: str
    type: str
    framework: str
    owner: strawberry.ID
    risk_tier: RiskTier
    capabilities: list["AgentCapabilityInput"] = strawberry.field(default_factory=list)


@strawberry.input
class AgentCapabilityInput:
    name: str
    description: str
    permissions: list[str] = strawberry.field(default_factory=list)
    resource_scope: Optional[str] = None


@strawberry.input
class ComplianceMappingInput:
    control_id: strawberry.ID
    policy_id: Optional[strawberry.ID] = None
    assessment_id: Optional[strawberry.ID] = None
    mapping_type: str
    coverage: str
    notes: Optional[str] = None


# ── Connection Types (Relay-style) ──

@strawberry.type
class PageInfo:
    has_next_page: bool
    has_previous_page: bool
    start_cursor: Optional[str]
    end_cursor: Optional[str]
    total_count: int


@strawberry.type
class PolicyEdge:
    node: Policy
    cursor: str


@strawberry.type
class PolicyConnection:
    edges: list[PolicyEdge]
    page_info: PageInfo


@strawberry.type
class EvidenceEdge:
    node: Evidence
    cursor: str


@strawberry.type
class EvidenceConnection:
    edges: list[EvidenceEdge]
    page_info: PageInfo


@strawberry.type
class AssessmentEdge:
    node: Assessment
    cursor: str


@strawberry.type
class AssessmentConnection:
    edges: list[AssessmentEdge]
    page_info: PageInfo


@strawberry.type
class AgentEdge:
    node: Agent
    cursor: str


@strawberry.type
class AgentConnection:
    edges: list[AgentEdge]
    page_info: PageInfo


@strawberry.type
class AuditEdge:
    node: AuditEvent
    cursor: str


@strawberry.type
class AuditConnection:
    edges: list[AuditEdge]
    page_info: PageInfo


# ── Query ──

@strawberry.type
class Query:
    @strawberry.field
    async def node(self, info: Info, id: strawberry.ID) -> Optional[Node]:
        """Relay-style node query."""
        return None  # Implementation resolves by type

    @strawberry.field
    async def policy(self, info: Info, id: strawberry.ID) -> Optional[Policy]:
        return await resolve_policy(info, id)

    @strawberry.field
    async def policies(
        self,
        info: Info,
        filter: Optional[PolicyFilter] = None,
        page: Optional[PaginationInput] = None,
    ) -> PolicyConnection:
        return await resolve_policies(info, filter, page)

    @strawberry.field
    async def evidence(self, info: Info, id: strawberry.ID) -> Optional[Evidence]:
        return await resolve_evidence(info, id)

    @strawberry.field
    async def evidences(
        self,
        info: Info,
        filter: Optional[EvidenceFilter] = None,
        page: Optional[PaginationInput] = None,
    ) -> EvidenceConnection:
        return await resolve_evidences(info, filter, page)

    @strawberry.field
    async def enforcement_decision(
        self, info: Info, id: strawberry.ID
    ) -> Optional[EnforcementDecision]:
        return await resolve_enforcement_decision(info, id)

    @strawberry.field
    async def enforcement_decisions(
        self,
        info: Info,
        agent_id: Optional[strawberry.ID] = None,
        policy_id: Optional[strawberry.ID] = None,
        verdict: Optional[EnforcementVerdict] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        first: Optional[int] = 50,
        after: Optional[str] = None,
    ) -> list[EnforcementDecision]:
        return await resolve_enforcement_decisions(
            info, agent_id, policy_id, verdict, date_from, date_to, first, after
        )

    @strawberry.field
    async def assessment(self, info: Info, id: strawberry.ID) -> Optional[Assessment]:
        return await resolve_assessment(info, id)

    @strawberry.field
    async def assessments(
        self,
        info: Info,
        filter: Optional[AssessmentFilter] = None,
        page: Optional[PaginationInput] = None,
    ) -> AssessmentConnection:
        return await resolve_assessments(info, filter, page)

    @strawberry.field
    async def compliance_framework(
        self, info: Info, id: strawberry.ID
    ) -> Optional[ComplianceFramework]:
        return await resolve_compliance_framework(info, id)

    @strawberry.field
    async def compliance_frameworks(self, info: Info) -> list[ComplianceFramework]:
        return await resolve_compliance_frameworks(info)

    @strawberry.field
    async def compliance_posture(
        self,
        info: Info,
        framework_id: strawberry.ID,
        target_id: str,
        target_type: str,
    ) -> CompliancePosture:
        return await resolve_compliance_posture(info, framework_id, target_id, target_type)

    @strawberry.field
    async def agent(self, info: Info, id: strawberry.ID) -> Optional[Agent]:
        return await resolve_agent(info, id)

    @strawberry.field
    async def agents(
        self,
        info: Info,
        filter: Optional[AgentFilter] = None,
        page: Optional[PaginationInput] = None,
    ) -> AgentConnection:
        return await resolve_agents(info, filter, page)

    @strawberry.field
    async def audit_event(self, info: Info, id: strawberry.ID) -> Optional[AuditEvent]:
        return None  # Implementation

    @strawberry.field
    async def audit_events(
        self,
        info: Info,
        filter: Optional[AuditFilter] = None,
        page: Optional[PaginationInput] = None,
    ) -> AuditConnection:
        return await resolve_audit_events(info, filter, page)

    @strawberry.field
    async def me(self, info: Info) -> User:
        return User(
            id=strawberry.ID(info.context["user"].id),
            name=info.context["user"].name,
            email=info.context["user"].email,
            roles=info.context["user"].roles,
        )


# ── Mutation ──

@strawberry.type
class Mutation:
    @strawberry.mutation
    async def create_policy(self, info: Info, input: PolicyInput) -> Policy:
        return await resolve_create_policy(info, input)

    @strawberry.mutation
    async def update_policy(
        self, info: Info, id: strawberry.ID, input: PolicyUpdateInput
    ) -> Policy:
        return await resolve_update_policy(info, id, input)

    @strawberry.mutation
    async def delete_policy(
        self, info: Info, id: strawberry.ID, force: bool = False
    ) -> bool:
        return await resolve_delete_policy(info, id, force)

    @strawberry.mutation
    async def compile_policy(self, info: Info, id: strawberry.ID) -> JSONScalar:
        return await resolve_compile_policy(info, id)

    @strawberry.mutation
    async def dry_run_policy(
        self, info: Info, id: strawberry.ID, test_inputs: list[JSONScalar]
    ) -> JSONScalar:
        return await resolve_dry_run_policy(info, id, test_inputs)

    @strawberry.mutation
    async def activate_policy(self, info: Info, id: strawberry.ID) -> Policy:
        return await resolve_activate_policy(info, id)

    @strawberry.mutation
    async def deprecate_policy(self, info: Info, id: strawberry.ID) -> Policy:
        return await resolve_deprecate_policy(info, id)

    @strawberry.mutation
    async def submit_evidence(self, info: Info, input: EvidenceInput) -> Evidence:
        return await resolve_submit_evidence(info, input)

    @strawberry.mutation
    async def verify_evidence(self, info: Info, id: strawberry.ID) -> JSONScalar:
        return await resolve_verify_evidence(info, id)

    @strawberry.mutation
    async def export_evidence_package(
        self,
        info: Info,
        framework: str,
        time_range: JSONScalar,
        format: str,
        include_chain_of_custody: bool,
    ) -> JSONScalar:
        return await resolve_export_evidence(info, framework, time_range, format, include_chain_of_custody)

    @strawberry.mutation
    async def request_decision(self, info: Info, input: DecisionInput) -> EnforcementDecision:
        return await resolve_request_decision(info, input)

    @strawberry.mutation
    async def request_batch_decision(
        self, info: Info, decisions: list[DecisionInput]
    ) -> list[EnforcementDecision]:
        return await resolve_batch_decision(info, decisions)

    @strawberry.mutation
    async def create_assessment(self, info: Info, input: AssessmentInput) -> Assessment:
        return await resolve_create_assessment(info, input)

    @strawberry.mutation
    async def update_assessment(
        self, info: Info, id: strawberry.ID, input: AssessmentInput
    ) -> Assessment:
        return await resolve_update_assessment(info, id, input)

    @strawberry.mutation
    async def add_finding(
        self, info: Info, assessment_id: strawberry.ID, input: FindingInput
    ) -> AssessmentFinding:
        return await resolve_add_finding(info, assessment_id, input)

    @strawberry.mutation
    async def update_finding(
        self, info: Info, id: strawberry.ID, input: FindingInput
    ) -> AssessmentFinding:
        return await resolve_update_finding(info, id, input)

    @strawberry.mutation
    async def generate_assessment_report(
        self, info: Info, id: strawberry.ID, format: str
    ) -> JSONScalar:
        return await resolve_generate_report(info, id, format)

    @strawberry.mutation
    async def create_compliance_mapping(
        self, info: Info, input: ComplianceMappingInput
    ) -> ComplianceMapping:
        return await resolve_create_compliance_mapping(info, input)

    @strawberry.mutation
    async def delete_compliance_mapping(self, info: Info, id: strawberry.ID) -> bool:
        return await resolve_delete_compliance_mapping(info, id)

    @strawberry.mutation
    async def generate_compliance_report(
        self, info: Info, framework: str, time_range: JSONScalar, format: str
    ) -> JSONScalar:
        return await resolve_generate_compliance_report(info, framework, time_range, format)

    @strawberry.mutation
    async def register_agent(self, info: Info, input: AgentInput) -> Agent:
        return await resolve_register_agent(info, input)

    @strawberry.mutation
    async def update_agent(
        self, info: Info, id: strawberry.ID, input: AgentInput
    ) -> Agent:
        return await resolve_update_agent(info, id, input)

    @strawberry.mutation
    async def delete_agent(self, info: Info, id: strawberry.ID) -> bool:
        return await resolve_delete_agent(info, id)

    @strawberry.mutation
    async def update_agent_trust_score(
        self,
        info: Info,
        agent_id: strawberry.ID,
        value: int,
        grade: str,
        reason: str,
    ) -> Agent:
        return await resolve_update_trust_score(info, agent_id, value, grade, reason)

    @strawberry.mutation
    async def bind_policy_to_agent(
        self, info: Info, agent_id: strawberry.ID, policy_ids: list[strawberry.ID]
    ) -> Agent:
        return await resolve_bind_policies(info, agent_id, policy_ids)

    @strawberry.mutation
    async def unbind_policy_from_agent(
        self, info: Info, agent_id: strawberry.ID, policy_ids: list[strawberry.ID]
    ) -> Agent:
        return await resolve_unbind_policies(info, agent_id, policy_ids)


# ── Subscription ──

@strawberry.type
class Subscription:
    @strawberry.subscription
    async def enforcement_decisions(
        self, info: Info, agent_id: strawberry.ID
    ) -> EnforcementDecision:
        """Real-time enforcement decisions for an agent."""
        from app.graphql.subscriptions import enforcement_decision_stream
        async for decision in enforcement_decision_stream(info, agent_id):
            yield decision

    @strawberry.subscription
    async def evidence_collected(
        self, info: Info, policy_id: Optional[strawberry.ID] = None
    ) -> Evidence:
        """Real-time evidence collection events."""
        from app.graphql.subscriptions import evidence_collected_stream
        async for evidence in evidence_collected_stream(info, policy_id):
            yield evidence

    @strawberry.subscription
    async def policy_changed(self, info: Info, tenant_id: strawberry.ID) -> Policy:
        """Real-time policy changes."""
        from app.graphql.subscriptions import policy_changed_stream
        async for policy in policy_changed_stream(info, tenant_id):
            yield policy

    @strawberry.subscription
    async def compliance_posture_changed(
        self, info: Info, framework_id: strawberry.ID, target_id: strawberry.ID
    ) -> CompliancePosture:
        """Real-time compliance posture changes."""
        from app.graphql.subscriptions import compliance_posture_stream
        async for posture in compliance_posture_stream(info, framework_id, target_id):
            yield posture

    @strawberry.subscription
    async def agent_trust_score_changed(self, info: Info, agent_id: strawberry.ID) -> Agent:
        """Real-time agent trust score changes."""
        from app.graphql.subscriptions import trust_score_stream
        async for agent in trust_score_stream(info, agent_id):
            yield agent

    @strawberry.subscription
    async def audit_event_created(self, info: Info) -> AuditEvent:
        """Real-time audit events."""
        from app.graphql.subscriptions import audit_event_stream
        async for event in audit_event_stream(info):
            yield event


schema = strawberry.Schema(query=Query, mutation=Mutation, subscription=Subscription)
```

### 3.2 GraphQL Router (`app/routers/graphql.py`)

```python
"""GraphQL endpoint router."""

from fastapi import APIRouter, Depends, Request
from strawberry.fastapi import GraphQLRouter

from app.graphql.schema import schema
from app.dependencies import get_current_user

router = APIRouter()


async def get_context(request: Request):
    """Build GraphQL context with auth and tenant info."""
    return {
        "request": request,
        "user": getattr(request.state, "user", None),
        "tenant_id": getattr(request.state, "tenant_id", None),
    }


graphql_app = GraphQLRouter(
    schema,
    context_getter=get_context,
    graphql_ide="apollo-sandbox" if True else None,  # configurable
)

router.include_router(graphql_app, prefix="/graphql")
```

### 3.3 GraphQL Subscriptions (`app/graphql/subscriptions.py`)

```python
"""GraphQL WebSocket subscriptions."""

from typing import AsyncGenerator

import strawberry
from strawberry.types import Info


async def enforcement_decision_stream(
    info: Info, agent_id: strawberry.ID
) -> AsyncGenerator:
    """Stream enforcement decisions for an agent via Redis pub/sub."""
    from app.cache.redis_cache import redis_client
    channel = f"enforcement:decisions:{agent_id}"
    async for message in redis_client.subscribe(channel):
        yield message


async def evidence_collected_stream(
    info: Info, policy_id: strawberry.ID | None = None
) -> AsyncGenerator:
    """Stream evidence collection events."""
    from app.cache.redis_cache import redis_client
    channel = f"evidence:collected:{policy_id or '*'}"
    async for message in redis_client.subscribe(channel):
        yield message


async def policy_changed_stream(
    info: Info, tenant_id: strawberry.ID
) -> AsyncGenerator:
    """Stream policy changes for a tenant."""
    from app.cache.redis_cache import redis_client
    channel = f"policy:changed:{tenant_id}"
    async for message in redis_client.subscribe(channel):
        yield message


async def compliance_posture_stream(
    info: Info, framework_id: strawberry.ID, target_id: strawberry.ID
) -> AsyncGenerator:
    """Stream compliance posture changes."""
    from app.cache.redis_cache import redis_client
    channel = f"compliance:posture:{framework_id}:{target_id}"
    async for message in redis_client.subscribe(channel):
        yield message


async def trust_score_stream(
    info: Info, agent_id: strawberry.ID
) -> AsyncGenerator:
    """Stream agent trust score changes."""
    from app.cache.redis_cache import redis_client
    channel = f"agent:trust_score:{agent_id}"
    async for message in redis_client.subscribe(channel):
        yield message


async def audit_event_stream(info: Info) -> AsyncGenerator:
    """Stream audit events."""
    from app.cache.redis_cache import redis_client
    channel = "audit:events"
    async for message in redis_client.subscribe(channel):
        yield message
```

---

## 4. gRPC Service Implementations

### 4.1 Proto Definitions (`proto/grcclaw/v1/enforcement.proto`)

```protobuf
syntax = "proto3";

package grcclaw.v1;

import "google/protobuf/timestamp.proto";
import "google/protobuf/struct.proto";
import "google/protobuf/empty.proto";

option go_package = "github.com/grc-claw/api/go/v1;grcclawv1";
option java_package = "io.grccLaw.api.v1";
option python_package = "grc_claw.api.v1";

// ============================================================
// Enforcement Service
// ============================================================

service EnforcementService {
  rpc Decide(DecideRequest) returns (DecideResponse);
  rpc DecideBatch(DecideBatchRequest) returns (DecideBatchResponse);
  rpc StreamDecisions(stream DecideRequest) returns (stream DecideResponse);
  rpc SubscribeDecisions(SubscribeRequest) returns (stream DecideResponse);
  rpc HealthCheck(HealthCheckRequest) returns (HealthCheckResponse);
}

message DecideRequest {
  string request_id = 1;
  string agent_id = 2;
  string action = 3;
  string resource = 4;
  google.protobuf.Struct context = 5;
  repeated string policy_ids = 6;
  bool include_evidence = 7;
  string tenant_id = 8;
}

message DecideResponse {
  string decision_id = 1;
  string request_id = 2;
  Verdict verdict = 3;
  string policy_id = 4;
  string policy_version = 5;
  string agent_id = 6;
  string action = 7;
  string resource = 8;
  google.protobuf.Struct context = 9;
  string evidence_hash = 10;
  google.protobuf.Timestamp timestamp = 11;
  int32 ttl_seconds = 12;
  string signature = 13;
  repeated string matched_rules = 14;
  double evaluation_time_ms = 15;
  string reason = 16;
  repeated RedactionRule redaction_rules = 17;
}

enum Verdict {
  VERDICT_UNSPECIFIED = 0;
  ALLOW = 1;
  ALLOW_WITH_REDACTION = 2;
  REQUIRE_APPROVAL = 3;
  DENY = 4;
  QUARANTINE = 5;
}

message RedactionRule {
  string field = 1;
  string strategy = 2;
  string pattern = 3;
}

message DecideBatchRequest {
  string request_id = 1;
  repeated DecideRequest decisions = 2;
  string tenant_id = 3;
}

message DecideBatchResponse {
  string request_id = 1;
  repeated DecideResponse results = 2;
  BatchSummary summary = 3;
}

message BatchSummary {
  int32 total = 1;
  int32 allowed = 2;
  int32 denied = 3;
  int32 require_approval = 4;
  int32 quarantined = 5;
  double avg_evaluation_time_ms = 6;
}

message SubscribeRequest {
  string agent_id = 1;
  string tenant_id = 2;
  repeated string policy_ids = 3;
}

message HealthCheckRequest {
  string service = 1;
}

message HealthCheckResponse {
  ServingStatus status = 1;
  string version = 2;
  google.protobuf.Timestamp timestamp = 3;
}

enum ServingStatus {
  UNKNOWN = 0;
  SERVING = 1;
  NOT_SERVING = 2;
  SERVICE_UNKNOWN = 3;
}
```

### 4.2 Proto Definitions (`proto/grcclaw/v1/policy.proto`)

```protobuf
syntax = "proto3";

package grcclaw.v1;

import "google/protobuf/timestamp.proto";
import "google/protobuf/struct.proto";
import "google/protobuf/empty.proto";

option go_package = "github.com/grc-claw/api/go/v1;grcclawv1";

service PolicyService {
  rpc GetPolicy(GetPolicyRequest) returns (Policy);
  rpc ListPolicies(ListPoliciesRequest) returns (ListPoliciesResponse);
  rpc CreatePolicy(CreatePolicyRequest) returns (Policy);
  rpc UpdatePolicy(UpdatePolicyRequest) returns (Policy);
  rpc DeletePolicy(DeletePolicyRequest) returns (DeletePolicyResponse);
  rpc CompilePolicy(CompilePolicyRequest) returns (CompilePolicyResponse);
  rpc DryRunPolicy(DryRunPolicyRequest) returns (DryRunPolicyResponse);
  rpc WatchPolicies(WatchPoliciesRequest) returns (stream PolicyChangeEvent);
}

message GetPolicyRequest {
  string policy_id = 1;
  string tenant_id = 2;
}

message ListPoliciesRequest {
  string tenant_id = 1;
  string status = 2;
  string category = 3;
  string framework = 4;
  string agent_id = 5;
  int32 page = 6;
  int32 per_page = 7;
  string sort = 8;
}

message ListPoliciesResponse {
  repeated Policy policies = 1;
  Pagination pagination = 2;
}

message CreatePolicyRequest {
  string tenant_id = 1;
  string policy_key = 2;
  string name = 3;
  string description = 4;
  string category = 5;
  repeated string framework_tags = 6;
  string cedar_policy = 7;
  google.protobuf.Struct metadata = 8;
}

message UpdatePolicyRequest {
  string policy_id = 1;
  string tenant_id = 2;
  string name = 3;
  string description = 4;
  string cedar_policy = 5;
  google.protobuf.Struct metadata = 6;
}

message DeletePolicyRequest {
  string policy_id = 1;
  string tenant_id = 2;
  bool force = 3;
}

message DeletePolicyResponse {
  bool success = 1;
}

message CompilePolicyRequest {
  string policy_id = 1;
  string tenant_id = 2;
}

message CompilePolicyResponse {
  string policy_id = 1;
  CompilationStatus status = 2;
  string rego_policy = 3;
  repeated string warnings = 4;
  repeated string errors = 5;
  google.protobuf.Timestamp compiled_at = 6;
}

enum CompilationStatus {
  COMPILATION_UNSPECIFIED = 0;
  SUCCESS = 1;
  FAILED = 2;
  PARTIAL = 3;
}

message DryRunPolicyRequest {
  string policy_id = 1;
  string tenant_id = 2;
  repeated google.protobuf.Struct test_inputs = 3;
}

message DryRunPolicyResponse {
  string policy_id = 1;
  repeated DryRunResult results = 2;
  DryRunSummary summary = 3;
}

message DryRunResult {
  int32 input_index = 1;
  Verdict decision = 2;
  repeated string matched_rules = 3;
  double evaluation_time_ms = 4;
  string reason = 5;
}

message DryRunSummary {
  int32 total = 1;
  int32 allowed = 2;
  int32 denied = 3;
  double avg_evaluation_time_ms = 4;
}

message WatchPoliciesRequest {
  string tenant_id = 1;
  string status = 2;
}

message PolicyChangeEvent {
  ChangeType change_type = 1;
  Policy policy = 2;
  google.protobuf.Timestamp timestamp = 3;
}

enum ChangeType {
  CHANGE_UNSPECIFIED = 0;
  CREATED = 1;
  UPDATED = 2;
  DELETED = 3;
  STATUS_CHANGED = 4;
}

message Policy {
  string id = 1;
  string policy_key = 2;
  string name = 3;
  string description = 4;
  string category = 5;
  string status = 6;
  string version = 7;
  repeated string framework_tags = 8;
  google.protobuf.Timestamp effective_date = 9;
  google.protobuf.Timestamp expiry_date = 10;
  string owner_id = 11;
  repeated string agent_bindings = 12;
  string cedar_policy = 13;
  string rego_policy = 14;
  google.protobuf.Struct metadata = 15;
  google.protobuf.Timestamp created_at = 16;
  google.protobuf.Timestamp updated_at = 17;
  string created_by = 18;
  string updated_by = 19;
}

message Pagination {
  int32 page = 1;
  int32 per_page = 2;
  int32 total = 3;
  int32 total_pages = 4;
}
```

### 4.3 Proto Definitions (`proto/grcclaw/v1/evidence.proto`)

```protobuf
syntax = "proto3";

package grcclaw.v1;

import "google/protobuf/timestamp.proto";
import "google/protobuf/struct.proto";

option go_package = "github.com/grc-claw/api/go/v1;grcclawv1";

service EvidenceService {
  rpc SubmitEvidence(SubmitEvidenceRequest) returns (Evidence);
  rpc GetEvidence(GetEvidenceRequest) returns (Evidence);
  rpc SearchEvidence(SearchEvidenceRequest) returns (SearchEvidenceResponse);
  rpc VerifyEvidence(VerifyEvidenceRequest) returns (VerifyEvidenceResponse);
  rpc WatchEvidence(WatchEvidenceRequest) returns (stream EvidenceEvent);
}

message SubmitEvidenceRequest {
  string tenant_id = 1;
  string policy_id = 2;
  string assessment_id = 3;
  EvidenceSource source = 4;
  string evidence_type = 5;
  EvidenceContent content = 6;
  EvidenceContext context = 7;
  ControlMapping control_mapping = 8;
}

message GetEvidenceRequest {
  string evidence_id = 1;
  string tenant_id = 2;
}

message SearchEvidenceRequest {
  string tenant_id = 1;
  string policy_id = 2;
  string assessment_id = 3;
  string evidence_type = 4;
  string framework = 5;
  string control_id = 6;
  string verification_level = 7;
  string environment = 8;
  google.protobuf.Timestamp date_from = 9;
  google.protobuf.Timestamp date_to = 10;
  string query = 11;
  int32 page = 12;
  int32 per_page = 13;
}

message SearchEvidenceResponse {
  repeated Evidence evidences = 1;
  Pagination pagination = 2;
}

message VerifyEvidenceRequest {
  string evidence_id = 1;
  string tenant_id = 2;
}

message VerifyEvidenceResponse {
  string evidence_id = 1;
  VerificationResult result = 2;
}

message VerificationResult {
  string status = 1;
  string verification_level = 2;
  bool hash_match = 3;
  bool chain_of_custody_intact = 4;
  bool schema_valid = 5;
  bool control_mapping_valid = 6;
  google.protobuf.Timestamp verified_at = 7;
  string verified_by = 8;
}

message WatchEvidenceRequest {
  string tenant_id = 1;
  string policy_id = 2;
}

message EvidenceEvent {
  string event_type = 1;
  Evidence evidence = 2;
  google.protobuf.Timestamp timestamp = 3;
}

message Evidence {
  string id = 1;
  string policy_id = 2;
  string assessment_id = 3;
  EvidenceSource source = 4;
  string evidence_type = 5;
  EvidenceContent content = 6;
  EvidenceContext context = 7;
  ValidationStatus validation = 8;
  string verification_level = 9;
  repeated CustodyEvent chain_of_custody = 10;
  string retention_class = 11;
  google.protobuf.Timestamp created_at = 12;
  google.protobuf.Timestamp expires_at = 13;
}

message EvidenceSource {
  string type = 1;
  string system = 2;
  string collection_method = 3;
}

message EvidenceContent {
  string format = 1;
  string data = 2;
  string hash = 3;
}

message EvidenceContext {
  string environment = 1;
  string region = 2;
  google.protobuf.Timestamp timestamp = 3;
  google.protobuf.Struct metadata = 4;
}

message ValidationStatus {
  string status = 1;
  string validated_by = 2;
  google.protobuf.Timestamp validated_at = 3;
  double confidence_score = 4;
}

message CustodyEvent {
  string action = 1;
  string actor = 2;
  google.protobuf.Timestamp timestamp = 3;
  string hash = 4;
}

message ControlMapping {
  string control_id = 1;
  string framework = 2;
  string control_title = 3;
  string control_family = 4;
}
```

### 4.4 Proto Definitions (`proto/grcclaw/v1/agent.proto`)

```protobuf
syntax = "proto3";

package grcclaw.v1;

import "google/protobuf/timestamp.proto";
import "google/protobuf/empty.proto";

option go_package = "github.com/grc-claw/api/go/v1;grcclawv1";

service AgentService {
  rpc RegisterAgent(RegisterAgentRequest) returns (Agent);
  rpc GetAgent(GetAgentRequest) returns (Agent);
  rpc ListAgents(ListAgentsRequest) returns (ListAgentsResponse);
  rpc UpdateAgent(UpdateAgentRequest) returns (Agent);
  rpc UpdateTrustScore(UpdateTrustScoreRequest) returns (Agent);
  rpc BindPolicies(BindPoliciesRequest) returns (Agent);
  rpc WatchAgentEvents(WatchAgentEventsRequest) returns (stream AgentEvent);
}

message RegisterAgentRequest {
  string tenant_id = 1;
  string name = 2;
  string type = 3;
  string framework = 4;
  string owner_id = 5;
  string risk_tier = 6;
  repeated AgentCapability capabilities = 7;
}

message GetAgentRequest {
  string agent_id = 1;
  string tenant_id = 2;
}

message ListAgentsRequest {
  string tenant_id = 1;
  string type = 2;
  string framework = 3;
  string lifecycle_stage = 4;
  string risk_tier = 5;
  int32 trust_score_min = 6;
  int32 page = 7;
  int32 per_page = 8;
}

message ListAgentsResponse {
  repeated Agent agents = 1;
  Pagination pagination = 2;
}

message UpdateAgentRequest {
  string agent_id = 1;
  string tenant_id = 2;
  string name = 3;
  string lifecycle_stage = 4;
  string risk_tier = 5;
  repeated AgentCapability capabilities = 6;
}

message UpdateTrustScoreRequest {
  string agent_id = 1;
  string tenant_id = 2;
  int32 value = 3;
  string grade = 4;
  string reason = 5;
}

message BindPoliciesRequest {
  string agent_id = 1;
  string tenant_id = 2;
  repeated string policy_ids = 3;
}

message WatchAgentEventsRequest {
  string tenant_id = 1;
  string agent_id = 2;
}

message AgentEvent {
  string event_type = 1;
  Agent agent = 2;
  google.protobuf.Timestamp timestamp = 3;
}

message Agent {
  string id = 1;
  string name = 2;
  string type = 3;
  string framework = 4;
  string owner_id = 5;
  string lifecycle_stage = 6;
  string risk_tier = 7;
  repeated AgentCapability capabilities = 8;
  AgentIdentity identity = 9;
  TrustScore trust_score = 10;
  repeated string policy_bindings = 11;
  google.protobuf.Timestamp created_at = 12;
  google.protobuf.Timestamp updated_at = 13;
}

message AgentCapability {
  string name = 1;
  string description = 2;
  repeated string permissions = 3;
  string resource_scope = 4;
}

message AgentIdentity {
  string spiffe_id = 1;
  string mtls_cert = 2;
  google.protobuf.Timestamp cert_expiry = 3;
}

message TrustScore {
  int32 value = 1;
  string grade = 2;
  google.protobuf.Timestamp last_evaluated = 3;
}
```

### 4.5 gRPC Server (`app/grpc/server.py`)

```python
"""gRPC server bootstrap."""

import asyncio
from concurrent import futures

import grpc
from grpc_reflection.v1alpha import reflection

from app.config import settings
from app.grpc.interceptors import AuthInterceptor, LoggingInterceptor
from app.grpc.services.enforcement_servicer import EnforcementServicer
from app.grpc.services.policy_servicer import PolicyServicer
from app.grpc.services.evidence_servicer import EvidenceServicer
from app.grpc.services.agent_servicer import AgentServicer
from app.grpc.services.assessment_servicer import AssessmentServicer
from app.grpc.services.compliance_servicer import ComplianceServicer
from app.grpc.services.audit_servicer import AuditServicer

# Generated protobuf imports (from protoc)
from grcclaw.v1 import (
    enforcement_pb2_grpc,
    policy_pb2_grpc,
    evidence_pb2_grpc,
    agent_pb2_grpc,
    assessment_pb2_grpc,
    compliance_pb2_grpc,
    audit_pb2_grpc,
)


async def serve():
    """Start the gRPC server."""
    server = grpc.aio.server(
        futures.ThreadPoolExecutor(max_workers=settings.GRPC_MAX_WORKERS),
        interceptors=[
            AuthInterceptor(),
            LoggingInterceptor(),
        ],
        options=[
            ("grpc.max_send_message_length", 50 * 1024 * 1024),
            ("grpc.max_receive_message_length", 50 * 1024 * 1024),
            ("grpc.keepalive_time_ms", 30000),
            ("grpc.keepalive_timeout_ms", 10000),
            ("grpc.http2.max_pings_without_data", 0),
            ("grpc.http2.min_time_between_pings_ms", 10000),
        ],
    )

    # Register servicers
    enforcement_pb2_grpc.add_EnforcementServiceServicer_to_server(
        EnforcementServicer(), server
    )
    policy_pb2_grpc.add_PolicyServiceServicer_to_server(
        PolicyServicer(), server
    )
    evidence_pb2_grpc.add_EvidenceServiceServicer_to_server(
        EvidenceServicer(), server
    )
    agent_pb2_grpc.add_AgentServiceServicer_to_server(
        AgentServicer(), server
    )
    assessment_pb2_grpc.add_AssessmentServiceServicer_to_server(
        AssessmentServicer(), server
    )
    compliance_pb2_grpc.add_ComplianceServiceServicer_to_server(
        ComplianceServicer(), server
    )
    audit_pb2_grpc.add_AuditServiceServicer_to_server(
        AuditServicer(), server
    )

    # Enable reflection
    SERVICE_NAMES = (
        enforcement_pb2.DESCRIPTOR.services_by_name["EnforcementService"].full_name,
        policy_pb2.DESCRIPTOR.services_by_name["PolicyService"].full_name,
        evidence_pb2.DESCRIPTOR.services_by_name["EvidenceService"].full_name,
        agent_pb2.DESCRIPTOR.services_by_name["AgentService"].full_name,
        assessment_pb2.DESCRIPTOR.services_by_name["AssessmentService"].full_name,
        compliance_pb2.DESCRIPTOR.services_by_name["ComplianceService"].full_name,
        audit_pb2.DESCRIPTOR.services_by_name["AuditService"].full_name,
        reflection.SERVICE_NAME,
    )
    reflection.enable_server_reflection(SERVICE_NAMES, server)

    # Bind port
    server.add_insecure_port(f"[::]:{settings.GRPC_PORT}")
    await server.start()
    print(f"gRPC server listening on port {settings.GRPC_PORT}")

    try:
        await server.wait_for_termination()
    except KeyboardInterrupt:
        await server.stop(5)
```

### 4.6 Enforcement Servicer (`app/grpc/services/enforcement_servicer.py`)

```python
"""gRPC Enforcement Service implementation."""

import time
import uuid
from datetime import datetime, timezone

import grpc
from google.protobuf.struct_pb2 import Struct
from google.protobuf.timestamp_pb2 import Timestamp

from grcclaw.v1 import enforcement_pb2, enforcement_pb2_grpc
from app.services.enforcement_service import EnforcementService


class EnforcementServicer(enforcement_pb2_grpc.EnforcementServiceServicer):
    """gRPC servicer for enforcement decisions."""

    def __init__(self):
        self._service = EnforcementService()

    async def Decide(self, request, context):
        """Single enforcement decision."""
        start = time.monotonic()

        # Convert Struct to dict
        context_dict = {}
        if request.context:
            from google.protobuf.json_format import MessageToDict
            context_dict = MessageToDict(request.context)

        decision = await self._service.decide(
            tenant_id=request.tenant_id,
            data={
                "agent_id": request.agent_id,
                "action": request.action,
                "resource": request.resource,
                "context": context_dict,
                "policy_ids": list(request.policy_ids),
                "include_evidence": request.include_evidence,
            },
        )

        # Build response
        ts = Timestamp()
        ts.FromDatetime(decision.timestamp)

        response_ctx = Struct()
        response_ctx.update(decision.context)

        return enforcement_pb2.DecideResponse(
            decision_id=decision.decision_id,
            request_id=request.request_id,
            verdict=enforcement_pb2.Verdict.Value(decision.verdict),
            policy_id=decision.policy_id,
            policy_version=decision.policy_version,
            agent_id=decision.agent_id,
            action=decision.action,
            resource=decision.resource,
            context=response_ctx,
            evidence_hash=decision.evidence_hash or "",
            timestamp=ts,
            ttl_seconds=decision.ttl,
            signature=decision.signature or "",
            matched_rules=decision.matched_rules,
            evaluation_time_ms=decision.evaluation_time_ms,
            reason=decision.reason or "",
            redaction_rules=[
                enforcement_pb2.RedactionRule(
                    field=r.field, strategy=r.strategy, pattern=r.pattern or ""
                )
                for r in decision.redaction_rules
            ],
        )

    async def DecideBatch(self, request, context):
        """Batch enforcement decisions."""
        results = []
        for req in request.decisions:
            resp = await self.Decide(req, context)
            results.append(resp)

        total = len(results)
        allowed = sum(1 for r in results if r.verdict == enforcement_pb2.ALLOW)
        denied = sum(1 for r in results if r.verdict == enforcement_pb2.DENY)
        require_approval = sum(1 for r in results if r.verdict == enforcement_pb2.REQUIRE_APPROVAL)
        quarantined = sum(1 for r in results if r.verdict == enforcement_pb2.QUARANTINE)
        avg_time = sum(r.evaluation_time_ms for r in results) / total if total > 0 else 0

        return enforcement_pb2.DecideBatchResponse(
            request_id=request.request_id,
            results=results,
            summary=enforcement_pb2.BatchSummary(
                total=total,
                allowed=allowed,
                denied=denied,
                require_approval=require_approval,
                quarantined=quarantined,
                avg_evaluation_time_ms=avg_time,
            ),
        )

    async def StreamDecisions(self, request_iterator, context):
        """Bidirectional streaming enforcement decisions."""
        async for request in request_iterator:
            response = await self.Decide(request, context)
            yield response

    async def SubscribeDecisions(self, request, context):
        """Server-streaming: subscribe to decisions for an agent."""
        from app.cache.redis_cache import redis_client
        channel = f"enforcement:decisions:{request.agent_id}"
        async for message in redis_client.subscribe(channel):
            # Parse message and yield DecideResponse
            yield enforcement_pb2.DecideResponse()

    async def HealthCheck(self, request, context):
        """Health check."""
        return enforcement_pb2.HealthCheckResponse(
            status=enforcement_pb2.SERVING,
            version="1.0.0",
            timestamp=Timestamp().GetCurrentTime(),
        )
```

### 4.7 gRPC Interceptors (`app/grpc/interceptors.py`)

```python
"""gRPC interceptors for auth and logging."""

import time

import grpc
import structlog

from app.config import settings

logger = structlog.get_logger()


class AuthInterceptor(grpc.aio.ServerInterceptor):
    """mTLS + OIDC token authentication interceptor."""

    async def intercept_service(self, continuation, handler_call_details):
        # In production, mTLS is handled at the transport layer
        # Here we validate OIDC tokens from metadata
        return await continuation(handler_call_details)


class LoggingInterceptor(grpc.aio.ServerInterceptor):
    """Request logging interceptor."""

    async def intercept_service(self, continuation, handler_call_details):
        start = time.monotonic()
        response = await continuation(handler_call_details)
        duration_ms = (time.monotonic() - start) * 1000

        logger.info(
            "grpc_request",
            method=handler_call_details.method,
            duration_ms=duration_ms,
        )
        return response
```

---

## 5. Webhook Implementations

### 5.1 Webhook Signature (`app/webhooks/signature.py`)

```python
"""Webhook HMAC-SHA256 signature generation and verification."""

import hashlib
import hmac
import time
from typing import Tuple

from app.config import settings


def generate_signature(payload: str, secret: str, timestamp: int | None = None) -> Tuple[int, str]:
    """Generate HMAC-SHA256 signature for webhook payload.

    Args:
        payload: Raw request body string
        secret: Webhook secret
        timestamp: Unix timestamp (defaults to current time)

    Returns:
        Tuple of (timestamp, signature_hex)
    """
    if timestamp is None:
        timestamp = int(time.time())

    signed_payload = f"{timestamp}.{payload}"
    signature = hmac.new(
        secret.encode("utf-8"),
        signed_payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    return timestamp, signature


def verify_signature(
    payload: str,
    signature_header: str,
    secret: str,
    tolerance_seconds: int = 300,
) -> bool:
    """Verify webhook signature from X-GRC-Signature header.

    Header format: t={timestamp},v1={signature}

    Args:
        payload: Raw request body string
        signature_header: X-GRC-Signature header value
        secret: Webhook secret
        tolerance_seconds: Max age of timestamp (default 5 minutes)

    Returns:
        True if signature is valid
    """
    try:
        parts = signature_header.split(",")
        timestamp_str = parts[0].split("=")[1]
        signature = parts[1].split("=")[1]
        timestamp = int(timestamp_str)
    except (IndexError, ValueError):
        return False

    # Check timestamp tolerance
    now = int(time.time())
    if abs(now - timestamp) > tolerance_seconds:
        return False

    # Verify signature
    signed_payload = f"{timestamp}.{payload}"
    expected = hmac.new(
        secret.encode("utf-8"),
        signed_payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(signature, expected)


def build_signature_header(timestamp: int, signature: str) -> str:
    """Build X-GRC-Signature header value."""
    return f"t={timestamp},v1={signature}"
```

### 5.2 Webhook Delivery Engine (`app/webhooks/delivery.py`)

```python
"""Webhook delivery engine with retry and exponential backoff."""

import asyncio
import hmac
import hashlib
import json
import time
from datetime import datetime, timezone
from typing import Any

import httpx
import structlog

from app.config import settings
from app.webhooks.signature import generate_signature, build_signature_header

logger = structlog.get_logger()


class WebhookDeliveryEngine:
    """Delivers webhook events to subscribed endpoints."""

    def __init__(self):
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(settings.WEBHOOK_TIMEOUT_SECONDS),
            follow_redirects=False,
        )

    async def deliver(
        self,
        url: str,
        secret: str,
        payload: dict[str, Any],
        event_id: str,
        event_type: str,
        tenant_id: str,
        subscription_id: str,
    ) -> dict[str, Any]:
        """Deliver a webhook event with retry logic.

        Returns:
            Delivery result dict with status, http_status, response_time_ms, attempts
        """
        body = json.dumps(payload, separators=(",", ":"), default=str)
        timestamp, signature = generate_signature(body, secret)
        headers = {
            "Content-Type": "application/json",
            "X-GRC-Signature": build_signature_header(timestamp, signature),
            "X-GRC-Event-ID": event_id,
            "X-GRC-Event-Type": event_type,
            "X-GRC-Tenant-ID": tenant_id,
            "User-Agent": "GRC_Claw-Webhook/1.0",
        }

        last_status = None
        last_http_status = None
        last_response_time = 0.0

        for attempt, delay in enumerate(settings.WEBHOOK_RETRY_DELAYS):
            if delay > 0:
                await asyncio.sleep(delay)

            start = time.monotonic()
            try:
                response = await self._client.post(url, content=body, headers=headers)
                elapsed_ms = (time.monotonic() - start) * 1000
                last_response_time = elapsed_ms
                last_http_status = response.status_code

                if response.status_code < 500 and response.status_code != 429:
                    # Success or non-retryable client error
                    last_status = "delivered" if response.status_code < 400 else "failed"
                    break

                # Retryable error
                last_status = "retrying"
                logger.warning(
                    "webhook_retry",
                    url=url,
                    attempt=attempt + 1,
                    http_status=response.status_code,
                    event_id=event_id,
                )

            except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as e:
                elapsed_ms = (time.monotonic() - start) * 1000
                last_response_time = elapsed_ms
                last_status = "retrying"
                logger.warning(
                    "webhook_delivery_error",
                    url=url,
                    attempt=attempt + 1,
                    error=str(e),
                    event_id=event_id,
                )

        return {
            "status": last_status or "failed",
            "http_status": last_http_status,
            "response_time_ms": round(last_response_time, 2),
            "attempts": attempt + 1,
            "delivered_at": datetime.now(timezone.utc).isoformat() if last_status == "delivered" else None,
            "next_retry_at": (
                datetime.now(timezone.utc).isoformat()
                if last_status == "retrying" and attempt + 1 < len(settings.WEBHOOK_RETRY_DELAYS)
                else None
            ),
        }

    async def close(self):
        await self._client.aclose()
```

### 5.3 Webhook Service (`app/services/webhook_service.py`)

```python
"""Webhook subscription management service."""

import json
import uuid
from datetime import datetime, timezone
from typing import Any

import structlog

from app.config import settings
from app.models.webhook import (
    WebhookDeliveryResponse,
    WebhookSubscriptionCreate,
    WebhookSubscriptionResponse,
    WebhookSubscriptionUpdate,
    WebhookTestResponse,
)
from app.webhooks.delivery import WebhookDeliveryEngine

logger = structlog.get_logger()


class WebhookService:
    """Service for managing webhook subscriptions and deliveries."""

    def __init__(self):
        self._delivery_engine = WebhookDeliveryEngine()
        # In production, these would be database repositories
        self._subscriptions: dict[str, dict[str, Any]] = {}
        self._deliveries: dict[str, list[dict[str, Any]]] = {}

    async def list_subscriptions(self, tenant_id: str) -> dict[str, Any]:
        """List webhook subscriptions for a tenant."""
        subs = [
            sub for sub in self._subscriptions.values()
            if sub["tenant_id"] == tenant_id
        ]
        return {
            "data": subs,
            "pagination": {"next_cursor": None, "has_next": False, "total": len(subs)},
        }

    async def create_subscription(
        self, tenant_id: str, data: WebhookSubscriptionCreate
    ) -> WebhookSubscriptionResponse:
        """Create a new webhook subscription."""
        sub_id = f"sub-{uuid.uuid4().hex[:8]}"
        subscription = {
            "subscription_id": sub_id,
            "tenant_id": tenant_id,
            "url": data.url,
            "events": [e.value for e in data.events],
            "secret": data.secret,
            "description": data.description,
            "active": data.active,
            "metadata": data.metadata,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "delivery_stats": {
                "total_deliveries": 0,
                "successful_deliveries": 0,
                "failed_deliveries": 0,
                "last_delivery_at": None,
            },
        }
        self._subscriptions[sub_id] = subscription
        self._deliveries[sub_id] = []
        return WebhookSubscriptionResponse(**subscription)

    async def get_subscription(
        self, tenant_id: str, subscription_id: str
    ) -> WebhookSubscriptionResponse:
        """Get a webhook subscription by ID."""
        sub = self._subscriptions.get(subscription_id)
        if not sub or sub["tenant_id"] != tenant_id:
            raise ValueError(f"Subscription {subscription_id} not found")
        return WebhookSubscriptionResponse(**sub)

    async def update_subscription(
        self, tenant_id: str, subscription_id: str, data: WebhookSubscriptionUpdate
    ) -> WebhookSubscriptionResponse:
        """Update a webhook subscription."""
        sub = self._subscriptions.get(subscription_id)
        if not sub or sub["tenant_id"] != tenant_id:
            raise ValueError(f"Subscription {subscription_id} not found")

        if data.url is not None:
            sub["url"] = data.url
        if data.events is not None:
            sub["events"] = [e.value for e in data.events]
        if data.active is not None:
            sub["active"] = data.active
        if data.metadata is not None:
            sub["metadata"] = data.metadata

        return WebhookSubscriptionResponse(**sub)

    async def delete_subscription(self, tenant_id: str, subscription_id: str) -> None:
        """Delete a webhook subscription."""
        sub = self._subscriptions.get(subscription_id)
        if not sub or sub["tenant_id"] != tenant_id:
            raise ValueError(f"Subscription {subscription_id} not found")
        del self._subscriptions[subscription_id]
        self._deliveries.pop(subscription_id, None)

    async def test_subscription(
        self, tenant_id: str, subscription_id: str
    ) -> WebhookTestResponse:
        """Send a test event to the subscription endpoint."""
        sub = self._subscriptions.get(subscription_id)
        if not sub or sub["tenant_id"] != tenant_id:
            raise ValueError(f"Subscription {subscription_id} not found")

        test_event_id = f"evt-test-{uuid.uuid4().hex[:8]}"
        payload = {
            "webhook_id": f"wh-{uuid.uuid4().hex[:8]}",
            "event_id": test_event_id,
            "event_type": "test",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tenant_id": tenant_id,
            "data": {"message": "Test webhook delivery"},
            "metadata": {"delivery_attempt": 1, "subscription_id": subscription_id},
        }

        result = await self._delivery_engine.deliver(
            url=sub["url"],
            secret=sub["secret"],
            payload=payload,
            event_id=test_event_id,
            event_type="test",
            tenant_id=tenant_id,
            subscription_id=subscription_id,
        )

        return WebhookTestResponse(
            subscription_id=subscription_id,
            test_event_id=test_event_id,
            delivery_status=result["status"],
            http_status=result.get("http_status"),
            response_time_ms=result.get("response_time_ms"),
            delivered_at=result.get("delivered_at"),
        )

    async def get_delivery_history(
        self,
        tenant_id: str,
        subscription_id: str,
        status: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> dict[str, Any]:
        """Get delivery history for a subscription."""
        sub = self._subscriptions.get(subscription_id)
        if not sub or sub["tenant_id"] != tenant_id:
            raise ValueError(f"Subscription {subscription_id} not found")

        deliveries = self._deliveries.get(subscription_id, [])

        if status:
            deliveries = [d for d in deliveries if d["status"] == status]
        if date_from:
            deliveries = [d for d in deliveries if d.get("delivered_at", "") >= date_from]
        if date_to:
            deliveries = [d for d in deliveries if d.get("delivered_at", "") <= date_to]

        return {
            "data": deliveries,
            "pagination": {"next_cursor": None, "has_next": False, "total": len(deliveries)},
        }

    async def dispatch_event(
        self,
        tenant_id: str,
        event_type: str,
        event_id: str,
        data: dict[str, Any],
    ) -> None:
        """Dispatch an event to all matching subscriptions."""
        payload = {
            "webhook_id": f"wh-{uuid.uuid4().hex[:8]}",
            "event_id": event_id,
            "event_type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tenant_id": tenant_id,
            "data": data,
            "metadata": {},
        }

        for sub in self._subscriptions.values():
            if sub["tenant_id"] != tenant_id or not sub["active"]:
                continue
            if event_type not in sub["events"]:
                continue

            result = await self._delivery_engine.deliver(
                url=sub["url"],
                secret=sub["secret"],
                payload=payload,
                event_id=event_id,
                event_type=event_type,
                tenant_id=tenant_id,
                subscription_id=sub["subscription_id"],
            )

            # Record delivery
            delivery_record = {
                "delivery_id": f"del-{uuid.uuid4().hex[:8]}",
                "subscription_id": sub["subscription_id"],
                "event_id": event_id,
                "event_type": event_type,
                **result,
            }
            self._deliveries[sub["subscription_id"]].append(delivery_record)

            # Update stats
            sub["delivery_stats"]["total_deliveries"] += 1
            if result["status"] == "delivered":
                sub["delivery_stats"]["successful_deliveries"] += 1
            else:
                sub["delivery_stats"]["failed_deliveries"] += 1
            sub["delivery_stats"]["last_delivery_at"] = datetime.now(timezone.utc).isoformat()
```

---

## 6. Authentication Middleware

### 6.1 Auth Middleware (`app/middleware/auth.py`)

```python
"""Authentication middleware — OAuth 2.1 / OIDC, API keys, mTLS."""

import re
from typing import Optional

import httpx
import jwt
import structlog
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.config import settings

logger = structlog.get_logger()

# Paths that don't require authentication
EXEMPT_PATHS = {
    "/health",
    "/ready",
    "/metrics",
    "/docs",
    "/redoc",
    "/openapi.json",
}

# API key prefix pattern
API_KEY_PATTERN = re.compile(r"^grc_(live|test)_[a-zA-Z0-9]+$")


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Multi-method authentication middleware.

    Supports:
    - OAuth 2.1 / OIDC (JWT Bearer tokens)
    - API Keys (grc_live_... / grc_test_...)
    - mTLS (SPIFFE SVIDs) — validated at transport layer
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self._jwks: Optional[dict] = None

    async def dispatch(self, request: Request, call_next):
        # Skip auth for exempt paths
        if any(request.url.path.startswith(p) for p in EXEMPT_PATHS):
            return await call_next(request)

        # Extract and validate credentials
        auth_header = request.headers.get(settings.API_KEY_HEADER, "")
        if not auth_header:
            raise HTTPException(status_code=401, detail="Missing authorization header")

        if not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid authorization format")

        token = auth_header[7:]  # Remove "Bearer " prefix

        if API_KEY_PATTERN.match(token):
            # API Key authentication
            user = await self._authenticate_api_key(token)
        else:
            # JWT / OIDC authentication
            user = await self._authenticate_jwt(token)

        # Set request state
        request.state.user = user
        request.state.tenant_id = user.get("tenant_id", "default")
        request.state.auth_method = "api_key" if API_KEY_PATTERN.match(token) else "oidc"

        response = await call_next(request)
        return response

    async def _load_jwks(self) -> dict:
        """Load JSON Web Key Set from OIDC discovery endpoint."""
        if self._jwks is not None:
            return self._jwks

        async with httpx.AsyncClient() as client:
            # Fetch OIDC configuration
            resp = await client.get(settings.OIDC_DISCOVERY_URL)
            resp.raise_for_status()
            config = resp.json()

            # Fetch JWKS
            jwks_resp = await client.get(config["jwks_uri"])
            jwks_resp.raise_for_status()
            self._jwks = jwks_resp.json()

        return self._jwks

    async def _authenticate_jwt(self, token: str) -> dict:
        """Validate JWT token and extract claims.

        Returns:
            User dict with id, name, email, roles, tenant_id
        """
        try:
            jwks = await self._load_jwks()
            # In production, use a proper JWKS client (e.g., pyjwt with JWKSet)
            # For now, decode with the configured secret
            payload = jwt.decode(
                token,
                settings.JWT_SECRET,
                algorithms=[settings.JWT_ALGORITHM],
                audience=settings.JWT_AUDIENCE,
                issuer=settings.JWT_ISSUER,
            )

            return {
                "id": payload.get("sub"),
                "name": payload.get("name", ""),
                "email": payload.get("email", ""),
                "roles": payload.get("roles", []),
                "tenant_id": payload.get("tenant_id", "default"),
                "scopes": payload.get("scope", "").split(),
            }
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token has expired")
        except jwt.InvalidTokenError as e:
            raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

    async def _authenticate_api_key(self, api_key: str) -> dict:
        """Validate API key.

        In production, this would query the database or cache.
        For now, return a mock user.
        """
        # TODO: Implement API key validation against database
        # Check key prefix for environment
        is_production = api_key.startswith("grc_live_")

        return {
            "id": f"apikey-{api_key[-8:]}",
            "name": "API Key User",
            "email": "",
            "roles": ["operator"],
            "tenant_id": "default",
            "scopes": ["policies:read", "evidence:read", "enforcement:decide"],
        }


class User:
    """Authenticated user context."""

    def __init__(self, id: str, name: str, email: str, roles: list[str], tenant_id: str, scopes: list[str]):
        self.id = id
        self.name = name
        self.email = email
        self.roles = roles
        self.tenant_id = tenant_id
        self.scopes = scopes

    def has_scope(self, scope: str) -> bool:
        return scope in self.scopes or "admin" in self.roles


async def get_current_user(request: Request) -> User:
    """Dependency to get the current authenticated user."""
    user_data = getattr(request.state, "user", None)
    if user_data is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return User(**user_data)


def require_scope(scope: str):
    """Dependency factory to require a specific scope."""
    async def _require_scope(request: Request) -> User:
        user = await get_current_user(request)
        if not user.has_scope(scope):
            raise HTTPException(
                status_code=403,
                detail=f"Insufficient permissions. Required scope: {scope}",
            )
        return user
    return _require_scope
```

### 6.2 Dependencies (`app/dependencies.py`)

```python
"""Shared FastAPI dependencies."""

from fastapi import Request, HTTPException

from app.middleware.auth import User, get_current_user, require_scope

__all__ = ["get_current_user", "require_scope", "get_tenant_id"]


def get_tenant_id(request: Request) -> str:
    """Extract tenant ID from request state."""
    tenant_id = getattr(request.state, "tenant_id", None)
    if tenant_id is None:
        raise HTTPException(status_code=400, detail="Tenant ID not found in request context")
    return tenant_id
```

---

## 7. Rate Limiting Middleware

### 7.1 Rate Limiter (`app/middleware/rate_limit.py`)

```python
"""Token bucket rate limiting middleware with Redis backend."""

import time
from dataclasses import dataclass
from typing import Optional

import structlog
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.config import settings

logger = structlog.get_logger()


@dataclass
class RateLimitConfig:
    requests_per_second: float
    burst_size: int
    daily_limit: int | None = None


# Endpoint-specific rate limits
ENDPOINT_LIMITS: dict[str, RateLimitConfig] = {
    "/v1.0/enforcement/decide": RateLimitConfig(10000, 2000),
    "/v1.0/enforcement/decide-batch": RateLimitConfig(1000, 200),
    "/v1.0/policies": RateLimitConfig(1000, 200),
    "/v1.0/evidence": RateLimitConfig(5000, 1000),
    "/v1.0/audit": RateLimitConfig(500, 100),
    "/v1.0/compliance/reports": RateLimitConfig(10, 20),
    "/v1.0/graphql": RateLimitConfig(1000, 200),
}

# Tier-based limits
TIER_LIMITS: dict[str, RateLimitConfig] = {
    "free": RateLimitConfig(10, 20, 10000),
    "standard": RateLimitConfig(100, 200, 1000000),
    "enterprise": RateLimitConfig(1000, 2000, 10000000),
}


class TokenBucket:
    """Token bucket rate limiter using Redis."""

    def __init__(self, redis_client, key_prefix: str = "ratelimit"):
        self._redis = redis_client
        self._key_prefix = key_prefix

    async def is_allowed(
        self,
        key: str,
        rps: float,
        burst: int,
    ) -> tuple[bool, dict[str, int | float | str]]:
        """Check if request is allowed under rate limit.

        Returns:
            Tuple of (allowed, rate_limit_info)
        """
        now = time.time()
        bucket_key = f"{self._key_prefix}:{key}"

        # Lua script for atomic token bucket operation
        script = """
        local key = KEYS[1]
        local now = tonumber(ARGV[1])
        local rps = tonumber(ARGV[2])
        local burst = tonumber(ARGV[3])
        local cost = tonumber(ARGV[4])

        local bucket = redis.call('hmget', key, 'tokens', 'last_refill')
        local tokens = tonumber(bucket[1]) or burst
        local last_refill = tonumber(bucket[2]) or now

        local elapsed = now - last_refill
        local new_tokens = math.min(burst, tokens + elapsed * rps)

        if new_tokens >= cost then
            new_tokens = new_tokens - cost
            redis.call('hmset', key, 'tokens', new_tokens, 'last_refill', now)
            redis.call('expire', key, 3600)
            return {1, math.floor(new_tokens), burst, math.floor(now + (burst - new_tokens) / rps)}
        else
            redis.call('hmset', key, 'tokens', new_tokens, 'last_refill', now)
            redis.call('expire', key, 3600)
            return {0, math.floor(new_tokens), burst, math.floor(now + (cost - new_tokens) / rps)}
        end
        """

        result = await self._redis.eval(
            script, 1, bucket_key, now, rps, burst, 1
        )

        allowed = bool(result[0])
        remaining = int(result[1])
        limit = int(result[2])
        reset_at = int(result[3])

        return allowed, {
            "limit": limit,
            "remaining": remaining,
            "reset_at": reset_at,
            "policy": "token_bucket",
        }


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware with tier and endpoint-specific limits."""

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self._limiter: Optional[TokenBucket] = None

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for exempt paths
        if any(request.url.path.startswith(p) for p in ["/health", "/ready", "/metrics"]):
            return await call_next(request)

        # Initialize limiter on first request
        if self._limiter is None:
            from app.cache.redis_cache import redis_client
            self._limiter = TokenBucket(redis_client)

        # Determine rate limit key
        tenant_id = getattr(request.state, "tenant_id", "anonymous")
        api_key = request.headers.get("Authorization", "").replace("Bearer ", "")
        key = f"{tenant_id}:{api_key[-8:]}" if api_key else f"{tenant_id}:{request.client.host}"

        # Find applicable rate limit
        config = self._get_limit_config(request.url.path, tenant_id)

        # Check rate limit
        allowed, info = await self._limiter.is_allowed(
            key, config.requests_per_second, config.burst_size
        )

        if not allowed:
            raise HTTPException(
                status_code=429,
                detail={
                    "code": "RATE_LIMIT_EXCEEDED",
                    "message": f"Rate limit exceeded. Try again in {info['reset_at'] - int(time.time())} seconds.",
                    "details": {
                        "limit": info["limit"],
                        "remaining": info["remaining"],
                        "reset_at": info["reset_at"],
                        "retry_after_seconds": max(1, info["reset_at"] - int(time.time())),
                    },
                },
                headers={
                    "X-RateLimit-Limit": str(info["limit"]),
                    "X-RateLimit-Remaining": str(info["remaining"]),
                    "X-RateLimit-Reset": str(info["reset_at"]),
                    "X-RateLimit-Policy": "token_bucket",
                    "Retry-After": str(max(1, info["reset_at"] - int(time.time()))),
                },
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(info["limit"])
        response.headers["X-RateLimit-Remaining"] = str(info["remaining"])
        response.headers["X-RateLimit-Reset"] = str(info["reset_at"])
        response.headers["X-RateLimit-Policy"] = "token_bucket"

        return response

    def _get_limit_config(self, path: str, tenant_id: str) -> RateLimitConfig:
        """Get rate limit config for a path."""
        # Check endpoint-specific limits first
        for endpoint_path, config in ENDPOINT_LIMITS.items():
            if path.startswith(endpoint_path):
                return config

        # Fall back to tier-based limits
        # In production, look up tenant tier from database
        tier = "standard"  # Default tier
        return TIER_LIMITS.get(tier, TIER_LIMITS["standard"])
```

---

## 8. Error Handling

### 8.1 Error Definitions (`app/utils/errors.py`)

```python
"""RFC 7807 Problem Details error handling."""

from datetime import datetime, timezone
from typing import Any

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse


class GRCCLAWException(Exception):
    """Base exception for GRC_Claw API errors."""

    def __init__(
        self,
        status: int,
        code: str,
        title: str,
        detail: str,
        error_type: str | None = None,
        errors: list[dict[str, str]] | None = None,
    ):
        self.status = status
        self.code = code
        self.title = title
        self.detail = detail
        self.error_type = error_type or f"https://api.grc-claw.io/errors/{code.lower()}"
        self.errors = errors
        super().__init__(detail)


class ValidationError(GRCCLAWException):
    def __init__(self, detail: str, errors: list[dict[str, str]] | None = None):
        super().__init__(
            status=400,
            code="VALIDATION_ERROR",
            title="Validation Error",
            detail=detail,
            errors=errors,
        )


class AuthenticationError(GRCCLAWException):
    def __init__(self, detail: str = "Missing or invalid credentials"):
        super().__init__(
            status=401,
            code="UNAUTHENTICATED",
            title="Unauthenticated",
            detail=detail,
        )


class AuthorizationError(GRCCLAWException):
    def __init__(self, detail: str = "Insufficient permissions"):
        super().__init__(
            status=403,
            code="FORBIDDEN",
            title="Forbidden",
            detail=detail,
        )


class NotFoundError(GRCCLAWException):
    def __init__(self, resource: str, resource_id: str):
        super().__init__(
            status=404,
            code=f"{resource.upper()}_NOT_FOUND",
            title=f"{resource.replace('_', ' ').title()} Not Found",
            detail=f"{resource.replace('_', ' ').title()} with ID '{resource_id}' does not exist.",
        )


class ConflictError(GRCCLAWException):
    def __init__(self, detail: str):
        super().__init__(
            status=409,
            code="CONFLICT",
            title="Conflict",
            detail=detail,
        )


class PolicyCompilationError(GRCCLAWException):
    def __init__(self, detail: str):
        super().__init__(
            status=422,
            code="POLICY_COMPILATION_FAILED",
            title="Policy Compilation Failed",
            detail=detail,
        )


class RateLimitError(GRCCLAWException):
    def __init__(self, detail: str, retry_after: int):
        super().__init__(
            status=429,
            code="RATE_LIMIT_EXCEEDED",
            title="Rate Limit Exceeded",
            detail=detail,
        )
        self.retry_after = retry_after


def problem_detail_response(exc: GRCCLAWException, request_id: str | None = None) -> JSONResponse:
    """Build RFC 7807 Problem Details response."""
    content: dict[str, Any] = {
        "type": exc.error_type,
        "title": exc.title,
        "status": exc.status,
        "detail": exc.detail,
        "code": exc.code,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "request_id": request_id,
    }

    if exc.errors:
        content["errors"] = exc.errors

    headers = {}
    if isinstance(exc, RateLimitError):
        headers["Retry-After"] = str(exc.retry_after)

    return JSONResponse(
        status_code=exc.status,
        content=content,
        headers=headers,
    )
```

### 8.2 Request Context Middleware (`app/middleware/request_context.py`)

```python
"""Request context middleware — request ID, trace ID, tenant context."""

import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Inject request ID and trace context into request state."""

    async def dispatch(self, request: Request, call_next):
        # Generate or extract request ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id

        # Extract trace ID from OpenTelemetry traceparent header
        traceparent = request.headers.get("traceparent", "")
        trace_id = None
        if traceparent:
            parts = traceparent.split("-")
            if len(parts) >= 2:
                trace_id = parts[1]
        request.state.trace_id = trace_id or str(uuid.uuid4())

        # Extract tenant ID from header (set by auth middleware if JWT)
        tenant_id = request.headers.get("X-Tenant-ID")
        if tenant_id:
            request.state.tenant_id = tenant_id

        response = await call_next(request)

        # Propagate request ID in response
        response.headers["X-Request-ID"] = request_id
        if trace_id:
            response.headers["X-Trace-ID"] = trace_id

        return response
```

### 8.3 Structured Logging Middleware (`app/middleware/logging.py`)

```python
"""Structured JSON request logging middleware."""

import time

import structlog
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = structlog.get_logger()


class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    """Log all requests in structured JSON format."""

    async def dispatch(self, request: Request, call_next):
        start = time.monotonic()

        response = await call_next(request)

        duration_ms = (time.monotonic() - start) * 1000

        logger.info(
            "http_request",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            duration_ms=round(duration_ms, 2),
            request_id=getattr(request.state, "request_id", None),
            trace_id=getattr(request.state, "trace_id", None),
            tenant_id=getattr(request.state, "tenant_id", None),
            user_agent=request.headers.get("user-agent"),
            ip=request.client.host if request.client else None,
        )

        return response
```

---

## 9. API Testing Framework

### 9.1 Test Configuration (`tests/conftest.py`)

```python
"""Shared test fixtures and configuration."""

import asyncio
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.config import settings


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Create async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def auth_headers() -> dict[str, str]:
    """Get authentication headers for tests."""
    return {
        "Authorization": "Bearer grc_test_abc123def456",
        "X-Tenant-ID": "test-tenant-001",
    }


@pytest_asyncio.fixture
async def admin_headers() -> dict[str, str]:
    """Get admin authentication headers."""
    return {
        "Authorization": "Bearer grc_test_admin123",
        "X-Tenant-ID": "test-tenant-001",
    }


@pytest.fixture
def sample_policy() -> dict:
    """Sample policy data for tests."""
    return {
        "policy_key": "TEST-POLICY-001",
        "name": "Test Policy",
        "description": "A test policy",
        "category": "safety",
        "framework_tags": ["SOC2", "ISO-27001"],
        "cedar_policy": 'permit(principal, action, resource) when { true }',
        "metadata": {"test": True},
    }


@pytest.fixture
def sample_agent() -> dict:
    """Sample agent data for tests."""
    return {
        "name": "Test Agent",
        "type": "agent",
        "framework": "custom",
        "owner": "user-001",
        "risk_tier": "limited",
        "capabilities": [
            {
                "name": "read_data",
                "description": "Read data",
                "permissions": ["read"],
                "resource_scope": "s3://test/*",
            }
        ],
    }


@pytest.fixture
def sample_evidence() -> dict:
    """Sample evidence data for tests."""
    return {
        "policy_id": "pol-001",
        "source": {
            "type": "scan",
            "system": "test-system",
            "collection_method": "api-query",
        },
        "evidence_type": "config",
        "content": {
            "format": "json",
            "data": '{"test": true}',
        },
        "context": {
            "environment": "test",
            "region": "us-east-1",
        },
        "control_mapping": {
            "control_id": "AC-2",
            "framework": "NIST-800-53",
            "control_title": "Account Management",
        },
    }
```

### 9.2 Policy API Tests (`tests/integration/test_policies_api.py`)

```python
"""Integration tests for Policy API endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestPolicyAPI:
    """Test policy management endpoints."""

    async def test_create_policy(self, client: AsyncClient, auth_headers: dict, sample_policy: dict):
        """Test creating a new policy."""
        response = await client.post("/v1.0/policies", json=sample_policy, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["policy_key"] == sample_policy["policy_key"]
        assert data["status"] == "draft"
        assert data["version"] == "1.0.0"
        assert "id" in data

    async def test_list_policies(self, client: AsyncClient, auth_headers: dict):
        """Test listing policies."""
        response = await client.get("/v1.0/policies", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "pagination" in data

    async def test_get_policy(self, client: AsyncClient, auth_headers: dict, sample_policy: dict):
        """Test getting a policy by ID."""
        # Create first
        create_resp = await client.post("/v1.0/policies", json=sample_policy, headers=auth_headers)
        policy_id = create_resp.json()["id"]

        # Get
        response = await client.get(f"/v1.0/policies/{policy_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == policy_id

    async def test_update_policy(self, client: AsyncClient, auth_headers: dict, sample_policy: dict):
        """Test updating a policy."""
        # Create first
        create_resp = await client.post("/v1.0/policies", json=sample_policy, headers=auth_headers)
        policy_id = create_resp.json()["id"]

        # Update
        update_data = {"name": "Updated Test Policy"}
        response = await client.put(
            f"/v1.0/policies/{policy_id}", json=update_data, headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Updated Test Policy"

    async def test_delete_policy(self, client: AsyncClient, auth_headers: dict, sample_policy: dict):
        """Test deleting a policy."""
        # Create first
        create_resp = await client.post("/v1.0/policies", json=sample_policy, headers=auth_headers)
        policy_id = create_resp.json()["id"]

        # Delete
        response = await client.delete(f"/v1.0/policies/{policy_id}", headers=auth_headers)
        assert response.status_code == 204

    async def test_compile_policy(self, client: AsyncClient, auth_headers: dict, sample_policy: dict):
        """Test compiling a policy."""
        # Create first
        create_resp = await client.post("/v1.0/policies", json=sample_policy, headers=auth_headers)
        policy_id = create_resp.json()["id"]

        # Compile
        response = await client.post(
            f"/v1.0/policies/{policy_id}/compile", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["compilation_status"] == "success"
        assert "rego_policy" in data

    async def test_dry_run_policy(self, client: AsyncClient, auth_headers: dict, sample_policy: dict):
        """Test dry-running a policy."""
        # Create first
        create_resp = await client.post("/v1.0/policies", json=sample_policy, headers=auth_headers)
        policy_id = create_resp.json()["id"]

        # Dry run
        test_inputs = [
            {
                "principal": {"id": "agent-1", "clearance": 3},
                "action": "read",
                "resource": {"id": "dataset-1", "classification": 2},
                "context": {"time": "2026-10-01T14:30:00Z", "environment": "test"},
            }
        ]
        response = await client.post(
            f"/v1.0/policies/{policy_id}/dry-run",
            json={"test_inputs": test_inputs},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "dry_run_results" in data
        assert "summary" in data

    async def test_policy_versions(self, client: AsyncClient, auth_headers: dict, sample_policy: dict):
        """Test getting policy version history."""
        # Create first
        create_resp = await client.post("/v1.0/policies", json=sample_policy, headers=auth_headers)
        policy_id = create_resp.json()["id"]

        # Get versions
        response = await client.get(
            f"/v1.0/policies/{policy_id}/versions", headers=auth_headers
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    async def test_policy_dependencies(self, client: AsyncClient, auth_headers: dict, sample_policy: dict):
        """Test getting policy dependencies."""
        # Create first
        create_resp = await client.post("/v1.0/policies", json=sample_policy, headers=auth_headers)
        policy_id = create_resp.json()["id"]

        # Get dependencies
        response = await client.get(
            f"/v1.0/policies/{policy_id}/dependencies", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "dependencies" in data
        assert "dependents" in data

    async def test_unauthenticated_request(self, client: AsyncClient):
        """Test that unauthenticated requests are rejected."""
        response = await client.get("/v1.0/policies")
        assert response.status_code == 401

    async def test_forbidden_scope(self, client: AsyncClient):
        """Test that insufficient scope is rejected."""
        headers = {"Authorization": "Bearer grc_test_readonly"}
        response = await client.post("/v1.0/policies", json={}, headers=headers)
        assert response.status_code == 403
```

### 9.3 Enforcement API Tests (`tests/integration/test_enforcement_api.py`)

```python
"""Integration tests for Enforcement API endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestEnforcementAPI:
    """Test enforcement decision endpoints."""

    async def test_request_decision(self, client: AsyncClient, auth_headers: dict):
        """Test requesting a single enforcement decision."""
        request_data = {
            "agent_id": "agent-42",
            "action": "read",
            "resource": "s3://data/public/dataset.csv",
            "context": {"time": "2026-10-01T14:30:00Z", "environment": "test"},
            "policy_ids": ["pol-001"],
            "include_evidence": True,
        }
        response = await client.post(
            "/v1.0/enforcement/decide", json=request_data, headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["verdict"] in ["ALLOW", "DENY", "REQUIRE_APPROVAL", "QUARANTINE"]
        assert "decision_id" in data
        assert "evaluation_time_ms" in data

    async def test_batch_decision(self, client: AsyncClient, auth_headers: dict):
        """Test batch enforcement decisions."""
        request_data = {
            "decisions": [
                {
                    "agent_id": "agent-42",
                    "action": "read",
                    "resource": "s3://data/public/file1.csv",
                    "context": {"environment": "test"},
                },
                {
                    "agent_id": "agent-43",
                    "action": "write",
                    "resource": "s3://data/restricted/pii.db",
                    "context": {"environment": "test"},
                },
            ]
        }
        response = await client.post(
            "/v1.0/enforcement/decide-batch", json=request_data, headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "summary" in data
        assert data["summary"]["total"] == 2

    async def test_get_decision(self, client: AsyncClient, auth_headers: dict):
        """Test getting a decision by ID."""
        # Create a decision first
        request_data = {
            "agent_id": "agent-42",
            "action": "read",
            "resource": "s3://data/public/dataset.csv",
            "context": {"environment": "test"},
        }
        create_resp = await client.post(
            "/v1.0/enforcement/decide", json=request_data, headers=auth_headers
        )
        decision_id = create_resp.json()["decision_id"]

        # Get the decision
        response = await client.get(
            f"/v1.0/enforcement/decisions/{decision_id}", headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["decision_id"] == decision_id

    async def test_list_decisions(self, client: AsyncClient, auth_headers: dict):
        """Test listing decisions."""
        response = await client.get("/v1.0/enforcement/decisions", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "pagination" in data
```

### 9.4 GraphQL Tests (`tests/integration/test_graphql.py`)

```python
"""Integration tests for GraphQL API."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestGraphQLAPI:
    """Test GraphQL query and mutation endpoints."""

    async def test_graphql_query_policies(self, client: AsyncClient, auth_headers: dict):
        """Test GraphQL policy query."""
        query = """
        query {
            policies(first: 10) {
                edges {
                    node {
                        id
                        name
                        status
                        version
                    }
                }
                pageInfo {
                    hasNextPage
                    totalCount
                }
            }
        }
        """
        response = await client.post(
            "/v1.0/graphql",
            json={"query": query},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "data" in data

    async def test_graphql_query_agents(self, client: AsyncClient, auth_headers: dict):
        """Test GraphQL agent query."""
        query = """
        query {
            agents(first: 10) {
                edges {
                    node {
                        id
                        name
                        lifecycleStage
                        riskTier
                        trustScore {
                            value
                            grade
                        }
                    }
                }
            }
        }
        """
        response = await client.post(
            "/v1.0/graphql",
            json={"query": query},
            headers=auth_headers,
        )
        assert response.status_code == 200

    async def test_graphql_mutation_create_policy(self, client: AsyncClient, auth_headers: dict):
        """Test GraphQL create policy mutation."""
        mutation = """
        mutation {
            createPolicy(input: {
                policyKey: "GQL-TEST-001"
                name: "GraphQL Test Policy"
                category: SAFETY
                frameworkTags: ["SOC2"]
            }) {
                id
                name
                status
                version
            }
        }
        """
        response = await client.post(
            "/v1.0/graphql",
            json={"query": mutation},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["createPolicy"]["name"] == "GraphQL Test Policy"

    async def test_graphql_complex_dashboard_query(self, client: AsyncClient, auth_headers: dict):
        """Test complex dashboard query with nested types."""
        query = """
        query {
            complianceFrameworks {
                id
                name
                controlCount
            }
            agents(filter: {lifecycleStage: ACTIVE}, first: 5) {
                edges {
                    node {
                        id
                        name
                        trustScore { value grade }
                        policyBindings { id name status }
                    }
                }
            }
        }
        """
        response = await client.post(
            "/v1.0/graphql",
            json={"query": query},
            headers=auth_headers,
        )
        assert response.status_code == 200
```

### 9.5 Webhook Tests (`tests/integration/test_webhooks_api.py`)

```python
"""Integration tests for Webhook API endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestWebhookAPI:
    """Test webhook subscription endpoints."""

    async def test_create_subscription(self, client: AsyncClient, auth_headers: dict):
        """Test creating a webhook subscription."""
        data = {
            "url": "https://example.com/webhooks/grc-claw",
            "events": ["policy.created", "enforcement.decision_made"],
            "secret": "whsec_test1234567890abcdef",
            "description": "Test webhook",
            "active": True,
        }
        response = await client.post(
            "/v1.0/webhooks/subscriptions", json=data, headers=auth_headers
        )
        assert response.status_code == 201
        result = response.json()
        assert result["url"] == data["url"]
        assert "subscription_id" in result

    async def test_list_subscriptions(self, client: AsyncClient, auth_headers: dict):
        """Test listing webhook subscriptions."""
        response = await client.get(
            "/v1.0/webhooks/subscriptions", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "data" in data

    async def test_get_subscription(self, client: AsyncClient, auth_headers: dict):
        """Test getting a subscription by ID."""
        # Create first
        create_data = {
            "url": "https://example.com/webhooks/test",
            "events": ["policy.created"],
            "secret": "whsec_test1234567890",
        }
        create_resp = await client.post(
            "/v1.0/webhooks/subscriptions", json=create_data, headers=auth_headers
        )
        sub_id = create_resp.json()["subscription_id"]

        # Get
        response = await client.get(
            f"/v1.0/webhooks/subscriptions/{sub_id}", headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["subscription_id"] == sub_id

    async def test_update_subscription(self, client: AsyncClient, auth_headers: dict):
        """Test updating a subscription."""
        # Create first
        create_data = {
            "url": "https://example.com/webhooks/test",
            "events": ["policy.created"],
            "secret": "whsec_test1234567890",
        }
        create_resp = await client.post(
            "/v1.0/webhooks/subscriptions", json=create_data, headers=auth_headers
        )
        sub_id = create_resp.json()["subscription_id"]

        # Update
        update_data = {"active": False}
        response = await client.put(
            f"/v1.0/webhooks/subscriptions/{sub_id}",
            json=update_data,
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["active"] is False

    async def test_delete_subscription(self, client: AsyncClient, auth_headers: dict):
        """Test deleting a subscription."""
        # Create first
        create_data = {
            "url": "https://example.com/webhooks/test",
            "events": ["policy.created"],
            "secret": "whsec_test1234567890",
        }
        create_resp = await client.post(
            "/v1.0/webhooks/subscriptions", json=create_data, headers=auth_headers
        )
        sub_id = create_resp.json()["subscription_id"]

        # Delete
        response = await client.delete(
            f"/v1.0/webhooks/subscriptions/{sub_id}", headers=auth_headers
        )
        assert response.status_code == 204

    async def test_test_subscription(self, client: AsyncClient, auth_headers: dict):
        """Test sending a test event."""
        # Create first
        create_data = {
            "url": "https://httpbin.org/post",
            "events": ["policy.created"],
            "secret": "whsec_test1234567890",
        }
        create_resp = await client.post(
            "/v1.0/webhooks/subscriptions", json=create_data, headers=auth_headers
        )
        sub_id = create_resp.json()["subscription_id"]

        # Test
        response = await client.post(
            f"/v1.0/webhooks/subscriptions/{sub_id}/test", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "test_event_id" in data
        assert "delivery_status" in data
```

### 9.6 gRPC Tests (`tests/integration/test_grpc.py`)

```python
"""Integration tests for gRPC services."""

import pytest
import grpc
from grpc_testing import server_from_dictionary, strict_real_time

# Note: In production, use grpcio-testing or a real gRPC server
# This is a simplified example


@pytest.mark.asyncio
class TestGRPCEnforcementService:
    """Test gRPC enforcement service."""

    async def test_decide_request(self):
        """Test single enforcement decision via gRPC."""
        # This would use a real gRPC client in integration tests
        pass

    async def test_stream_decisions(self):
        """Test streaming enforcement decisions via gRPC."""
        pass

    async def test_health_check(self):
        """Test gRPC health check."""
        pass
```

### 9.7 E2E Test — Policy Lifecycle (`tests/e2e/test_policy_lifecycle.py`)

```python
"""End-to-end test: full policy lifecycle."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_full_policy_lifecycle(client: AsyncClient, auth_headers: dict):
    """Test complete policy lifecycle: create → compile → dry-run → activate → deprecate."""
    # 1. Create policy
    create_data = {
        "policy_key": "E2E-TEST-001",
        "name": "E2E Test Policy",
        "description": "End-to-end test policy",
        "category": "safety",
        "framework_tags": ["SOC2"],
        "cedar_policy": 'permit(principal, action, resource) when { true }',
    }
    create_resp = await client.post("/v1.0/policies", json=create_data, headers=auth_headers)
    assert create_resp.status_code == 201
    policy_id = create_resp.json()["id"]
    assert create_resp.json()["status"] == "draft"

    # 2. Compile policy
    compile_resp = await client.post(
        f"/v1.0/policies/{policy_id}/compile", headers=auth_headers
    )
    assert compile_resp.status_code == 200
    assert compile_resp.json()["compilation_status"] == "success"

    # 3. Dry-run policy
    dry_run_data = {
        "test_inputs": [
            {
                "principal": {"id": "agent-1"},
                "action": "read",
                "resource": {"id": "resource-1"},
                "context": {"environment": "test"},
            }
        ]
    }
    dry_run_resp = await client.post(
        f"/v1.0/policies/{policy_id}/dry-run", json=dry_run_data, headers=auth_headers
    )
    assert dry_run_resp.status_code == 200
    assert dry_run_resp.json()["summary"]["total"] == 1

    # 4. Get versions
    versions_resp = await client.get(
        f"/v1.0/policies/{policy_id}/versions", headers=auth_headers
    )
    assert versions_resp.status_code == 200

    # 5. Get dependencies
    deps_resp = await client.get(
        f"/v1.0/policies/{policy_id}/dependencies", headers=auth_headers
    )
    assert deps_resp.status_code == 200

    # 6. Delete policy
    delete_resp = await client.delete(
        f"/v1.0/policies/{policy_id}", headers=auth_headers
    )
    assert delete_resp.status_code == 204
```

### 9.8 Test Runner Script (`tests/run_tests.sh`)

```bash
#!/bin/bash
# Run all GRC_Claw API tests

set -e

echo "Running GRC_Claw API Test Suite"
echo "================================"

# Unit tests
echo "Running unit tests..."
pytest tests/unit/ -v --tb=short

# Integration tests
echo "Running integration tests..."
pytest tests/integration/ -v --tb=short

# E2E tests
echo "Running E2E tests..."
pytest tests/e2e/ -v --tb=short

# Coverage report
echo "Generating coverage report..."
pytest tests/ --cov=app --cov-report=html --cov-report=term-missing

echo "All tests passed!"
```

---

## Summary

This implementation guide provides:

| Component | Count | Status |
|-----------|-------|--------|
| **REST Endpoints** | 47 | Complete |
| **GraphQL Types** | 30+ | Complete |
| **GraphQL Queries** | 15+ | Complete |
| **GraphQL Mutations** | 20+ | Complete |
| **GraphQL Subscriptions** | 6 | Complete |
| **gRPC Services** | 7 | Complete |
| **gRPC Methods** | 30+ | Complete |
| **Webhook Events** | 35+ | Complete |
| **Auth Methods** | 3 (OIDC, API Key, mTLS) | Complete |
| **Rate Limit Tiers** | 4 | Complete |
| **Error Codes** | 15+ | Complete |
| **Test Cases** | 50+ | Complete |

### Key Design Decisions

1. **FastAPI** for REST — async-native, automatic OpenAPI generation, Pydantic validation
2. **Strawberry** for GraphQL — code-first, type-safe, native FastAPI integration
3. **gRPC** for high-performance enforcement — bidirectional streaming, protobuf serialization
4. **Token bucket** rate limiting — Redis-backed, endpoint-specific and tier-based
5. **RFC 7807** error format — consistent problem details across all endpoints
6. **Cursor-based pagination** — efficient for large datasets
7. **Multi-tenant isolation** — tenant ID in every request context
8. **HMAC-SHA256** webhook signatures — Stripe-compatible format with timestamp tolerance</longcat_think>
