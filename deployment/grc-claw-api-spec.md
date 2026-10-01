# GRC_Claw API Specification

**Version:** 1.2  
**Date:** 2026-10-01  
**Status:** Draft  
**Owner:** GRC_Claw Architecture Team

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Architecture Overview](#2-architecture-overview)
3. [Authentication & Authorization](#3-authentication--authorization)
4. [Rate Limiting & Quotas](#4-rate-limiting--quotas)
5. [Versioning Strategy](#5-versioning-strategy)
6. [Error Handling](#6-error-handling)
7. [REST API](#7-rest-api)
8. [GraphQL Schema](#8-graphql-schema)
9. [gRPC Interface](#9-grpc-interface)
10. [Webhook API](#10-webhook-api)
11. [Event Catalog](#11-event-catalog)
    - 11.1–11.7: [Core Events](#11-event-catalog)
    - 11.8: [Real-Time Stream Events (Flink)](#118-real-time-stream-events-flink)
    - 11.9: [Saga Events](#119-saga-events)
12. [SDK & Client Libraries](#12-sdk--client-libraries)
13. [API Authentication & Authorization](#13-api-authentication--authorization)
14. [API Rate Limiting & Throttling](#14-api-rate-limiting--throttling)
15. [API Versioning & Deprecation](#15-api-versioning--deprecation)
16. [API Monitoring & Analytics](#16-api-monitoring--analytics)
17. [API Documentation Automation](#17-api-documentation-automation)
18. [API Testing & Quality Assurance](#18-api-testing--quality-assurance)
19. [Appendices](#19-appendices)

---

## 1. Introduction

### 1.1 Purpose

This specification defines the complete API surface for GRC_Claw — an open-source governance, risk, and compliance platform for agentic AI. It provides four complementary interfaces:

- **REST API** — CRUD operations, search, and reporting
- **GraphQL** — Complex nested queries for dashboards and analytics
- **gRPC** — High-performance enforcement decisions and streaming
- **Webhooks** — Event-driven integrations

### 1.2 Scope

This specification covers:

- Policy lifecycle management (create, update, compile, dry-run, activate, deprecate)
- Evidence collection, verification, and export
- Enforcement decisions (single, batch, streaming)
- Assessment management (risk, compliance, maturity, readiness)
- Compliance mapping across 10 frameworks
- Agent registry and identity management
- Audit trail querying and verification
- Webhook subscriptions and delivery

### 1.3 Design Principles

| Principle | Rationale |
|-----------|-----------|
| **PEP/PDP Separation** | Enforcement and decision logic scale independently |
| **Deterministic Enforcement** | No LLM in the decision path — governance cannot be influenced by the governed system |
| **Evidence-First Design** | Every action produces audit-ready evidence |
| **Multi-Framework Mapping** | Single control implementation satisfies multiple compliance frameworks |
| **Agent-as-Subject** | Agents are first-class governance subjects |
| **Cryptographic Integrity** | SHA-256 chain-hashed audit trail with RFC 3161 timestamps |

---

## 2. Architecture Overview

### 2.1 API Gateway

All external traffic flows through a unified API gateway that provides:

- Authentication (OAuth 2.1 / OIDC / mTLS)
- Rate limiting and quota enforcement
- Request routing to backend services
- Request/response transformation
- TLS termination

### 2.2 Service Topology

```
                    ┌─────────────────┐
                    │   API Gateway   │
                    │  (Kong / Envoy) │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
┌───────▼──────┐  ┌──────────▼─────────┐  ┌──────▼───────┐
│  REST API    │  │   GraphQL Server   │  │  gRPC Server │
│  (FastAPI)   │  │   (Strawberry)     │  │  (Go/Rust)   │
└───────┬──────┘  └──────────┬─────────┘  └──────┬───────┘
        │                    │                    │
        └────────────────────┼────────────────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
       ┌──────▼─────┐ ┌─────▼──────┐ ┌────▼─────┐
       │  Policy    │ │  Evidence  │ │Enforcement│
       │  Service   │ │  Service   │ │  Service  │
       └──────┬─────┘ └─────┬──────┘ └────┬──────┘
              │              │              │
       ┌──────▼─────┐ ┌─────▼──────┐ ┌────▼─────┐
       │ Assessment │ │ Compliance │ │  Agent   │
       │  Service   │ │  Service   │ │ Service  │
       └────────────┘ └────────────┘ └──────────┘
```

### 2.3 Data Flow

```
Agent Action → PEP (intercept) → PDP (decide) → PEP (enforce) → Evidence Store
                                                                    ↓
                                                          Compliance Mapping
                                                                    ↓
                                                               Audit Trail
```

---

## 3. Authentication & Authorization

### 3.1 Authentication Methods

| Method | Use Case | Token Format |
|--------|----------|-------------|
| **OAuth 2.1 / OIDC** | User-facing applications, dashboards | JWT (RS256) |
| **API Keys** | Service-to-service, CI/CD pipelines | `grc_live_...` / `grc_test_...` |
| **mTLS (SPIFFE)** | Agent-to-PEP communication | X.509 SVID |
| **Webhook Signatures** | Webhook delivery verification | HMAC-SHA256 |

### 3.2 OAuth 2.1 / OIDC

**Authorization Server:** `https://auth.grc-claw.io`

**Token Endpoint:** `POST /oauth/token`

**Supported Grant Types:**
- `authorization_code` — User authentication via browser
- `client_credentials` — Service-to-service authentication
- `refresh_token` — Token refresh

**Token Response:**
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIs...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "refresh_token": "def50200...",
  "scope": "policies:read policies:write evidence:read enforcement:decide"
}
```

### 3.3 API Key Authentication

API keys are passed via the `Authorization` header:

```
Authorization: Bearer grc_live_abc123def456...
```

**Key Prefixes:**
- `grc_live_` — Production environment
- `grc_test_` — Test environment

**Key Scopes:**

| Scope | Permissions |
|-------|-------------|
| `policies:read` | Read policies |
| `policies:write` | Create, update, delete policies |
| `evidence:read` | Read evidence |
| `evidence:write` | Submit evidence |
| `enforcement:decide` | Request enforcement decisions |
| `assessments:read` | Read assessments |
| `assessments:write` | Create, update assessments |
| `compliance:read` | Read compliance data |
| `compliance:write` | Create compliance mappings |
| `agents:read` | Read agent registry |
| `agents:write` | Register, update agents |
| `audit:read` | Read audit trail |
| `webhooks:manage` | Manage webhook subscriptions |

### 3.4 mTLS (SPIFFE) Authentication

Agents authenticate to the PEP using SPIFFE Verifiable Identity Documents (SVIDs):

```
Agent → PEP: mTLS handshake with X.509 SVID
PEP validates: SPIFFE ID, certificate chain, expiry
PEP queries: Agent Registry for capabilities and trust score
```

**SPIFFE ID Format:**
```
spiffe://grc-claw.io/ns/{namespace}/sa/{agent_id}
```

Example: `spiffe://grc-claw.io/ns/prod/sa/agent-42`

### 3.5 Authorization Model

GRC_Claw uses **RBAC + ABAC** hybrid authorization:

**Roles:**

| Role | Description | Permissions |
|------|-------------|-------------|
| `admin` | Full system access | All permissions |
| `assessor` | Conduct assessments | assessments:read, assessments:write, evidence:read |
| `auditor` | Read-only audit access | audit:read, evidence:read, compliance:read |
| `operator` | Day-to-day operations | policies:read, evidence:read, evidence:write, enforcement:decide |
| `viewer` | Read-only dashboard | policies:read, evidence:read, compliance:read |

**ABAC Attributes:**
- `tenant_id` — Organization isolation
- `resource.owner_id` — Resource ownership
- `resource.classification` — Data classification level
- `agent.risk_tier` — Agent risk classification

### 3.6 Permission Matrix

| Resource | admin | assessor | auditor | operator | viewer |
|----------|-------|----------|---------|----------|--------|
| Policy CRUD | ✅ | ❌ | ❌ | ❌ | ❌ |
| Policy Read | ✅ | ✅ | ✅ | ✅ | ✅ |
| Evidence Submit | ✅ | ✅ | ❌ | ✅ | ❌ |
| Evidence Read | ✅ | ✅ | ✅ | ✅ | ✅ |
| Enforcement Decide | ✅ | ❌ | ❌ | ✅ | ❌ |
| Assessment CRUD | ✅ | ✅ | ❌ | ❌ | ❌ |
| Assessment Read | ✅ | ✅ | ✅ | ✅ | ✅ |
| Compliance Write | ✅ | ❌ | ❌ | ❌ | ❌ |
| Compliance Read | ✅ | ✅ | ✅ | ✅ | ✅ |
| Agent CRUD | ✅ | ❌ | ❌ | ❌ | ❌ |
| Agent Read | ✅ | ✅ | ✅ | ✅ | ✅ |
| Audit Read | ✅ | ✅ | ✅ | ❌ | ❌ |
| Webhook Manage | ✅ | ❌ | ❌ | ❌ | ❌ |

---

## 4. Rate Limiting & Quotas

### 4.1 Rate Limit Headers

All API responses include rate limit headers:

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1696161600
X-RateLimit-Policy: token_bucket
```

### 4.2 Rate Limit Tiers

| Tier | Requests/Second | Requests/Day | Burst | Use Case |
|------|----------------|-------------|-------|----------|
| **Free** | 10 | 10,000 | 20 | Evaluation, development |
| **Standard** | 100 | 1,000,000 | 200 | Production workloads |
| **Enterprise** | 1,000 | 10,000,000 | 2,000 | Large-scale deployments |
| **Unlimited** | Custom | Custom | Custom | Negotiated SLA |

### 4.3 Endpoint-Specific Limits

| Endpoint Category | Rate Limit | Rationale |
|-------------------|-----------|-----------|
| `POST /v1.0/enforcement/decide` | 10,000/sec | High-frequency agent actions |
| `POST /v1.0/enforcement/decide-batch` | 1,000/sec | Batch operations |
| `GET /v1.0/policies` | 1,000/sec | Standard read |
| `POST /v1.0/policies` | 100/sec | Write operations |
| `POST /v1.0/evidence` | 5,000/sec | Evidence ingestion |
| `GET /v1.0/audit` | 500/sec | Audit queries |
| `POST /v1.0/compliance/reports` | 10/sec | Expensive report generation |
| `POST /v1.0/graphql` | 1,000/sec | GraphQL queries |

### 4.4 Rate Limit Response

When rate limit is exceeded:

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Try again in 30 seconds.",
    "details": {
      "limit": 1000,
      "remaining": 0,
      "reset_at": "2026-10-01T14:31:00Z",
      "retry_after_seconds": 30
    }
  }
}
```

**HTTP Status:** `429 Too Many Requests`

### 4.5 Quota Management

Quotas are tracked per `tenant_id` and per `api_key`:

| Quota Type | Measurement | Enforcement |
|------------|-------------|-------------|
| **Storage** | Evidence bytes stored | Hard limit — reject new evidence |
| **API Calls** | Requests per day | Hard limit — reject with 429 |
| **Compute** | Report generation time | Soft limit — queue for later |
| **Concurrent** | Active WebSocket connections | Hard limit — reject new connections |

---

## 5. Versioning Strategy

### 5.1 URL Path Versioning

All API endpoints include the version in the URL path:

```
https://api.grc-claw.io/v1.0/policies
```

**Current version:** `v1.0`

### 5.2 Version Lifecycle

| Stage | Description | Duration |
|-------|-------------|----------|
| **Alpha** | Internal testing, breaking changes allowed | 3 months |
| **Beta** | Public testing, minor breaking changes | 3 months |
| **GA** | Stable, no breaking changes | 12+ months |
| **Deprecated** | Announced deprecation, still functional | 6 months |
| **Sunset** | End of life, no longer available | — |

### 5.3 Backward Compatibility

- **Minor versions** (v1.1, v1.2) — Additive changes only, fully backward compatible
- **Major versions** (v2.0) — Breaking changes, migration guide provided
- **Deprecation notices** — Sent via webhook `api.version_deprecated` 6 months before sunset

### 5.4 Version Negotiation

Clients can request a specific version via header:

```
Accept: application/vnd.grc-claw.v1.0+json
```

Or via URL path:

```
GET /v1.0/policies
```

### 5.5 Breaking Change Policy

| Change Type | Example | Compatibility |
|-------------|---------|--------------|
| Adding optional fields | New field in response | ✅ Backward compatible |
| Adding new endpoints | New `POST /v1.0/audit/verify` | ✅ Backward compatible |
| Adding new enum value | New `PolicyStatus` value | ✅ Backward compatible |
| Removing fields | Remove field from response | ❌ Breaking change |
| Changing field types | `string` → `integer` | ❌ Breaking change |
| Renaming fields | `policy_key` → `policyKey` | ❌ Breaking change |
| Changing error codes | `404` → `410` | ❌ Breaking change |

---

## 6. Error Handling

### 6.1 Error Response Format

All errors follow RFC 7807 (Problem Details):

```json
{
  "type": "https://api.grc-claw.io/errors/policy-not-found",
  "title": "Policy Not Found",
  "status": 404,
  "detail": "Policy with ID 'pol-999' does not exist.",
  "instance": "/v1.0/policies/pol-999",
  "code": "POLICY_NOT_FOUND",
  "timestamp": "2026-10-01T14:30:00Z",
  "request_id": "req-abc123",
  "trace_id": "trace-def456"
}
```

### 6.2 Error Codes

| HTTP Status | Error Code | Description |
|-------------|------------|-------------|
| 400 | `VALIDATION_ERROR` | Request validation failed |
| 400 | `INVALID_CEDAR_SYNTAX` | Cedar policy syntax error |
| 400 | `INVALID_REGO_SYNTAX` | Rego policy syntax error |
| 401 | `UNAUTHENTICATED` | Missing or invalid credentials |
| 403 | `FORBIDDEN` | Insufficient permissions |
| 404 | `POLICY_NOT_FOUND` | Policy does not exist |
| 404 | `EVIDENCE_NOT_FOUND` | Evidence does not exist |
| 404 | `ASSESSMENT_NOT_FOUND` | Assessment does not exist |
| 404 | `AGENT_NOT_FOUND` | Agent does not exist |
| 409 | `POLICY_KEY_EXISTS` | Policy key already exists |
| 409 | `AGENT_ALREADY_REGISTERED` | Agent already registered |
| 409 | `CONFLICT` | Resource conflict |
| 422 | `POLICY_COMPILATION_FAILED` | Policy compilation failed |
| 422 | `EVIDENCE_VERIFICATION_FAILED` | Evidence verification failed |
| 429 | `RATE_LIMIT_EXCEEDED` | Rate limit exceeded |
| 500 | `INTERNAL_ERROR` | Internal server error |
| 503 | `SERVICE_UNAVAILABLE` | Service temporarily unavailable |

### 6.3 Validation Error Details

```json
{
  "type": "https://api.grc-claw.io/errors/validation-error",
  "title": "Validation Error",
  "status": 400,
  "detail": "Request validation failed with 2 errors.",
  "instance": "/v1.0/policies",
  "code": "VALIDATION_ERROR",
  "timestamp": "2026-10-01T14:30:00Z",
  "request_id": "req-abc123",
  "errors": [
    {
      "field": "policy_key",
      "message": "Field is required",
      "code": "REQUIRED"
    },
    {
      "field": "category",
      "message": "Must be one of: ethics, safety, privacy, fairness",
      "code": "INVALID_ENUM"
    }
  ]
}
```

### 6.4 Pagination

List endpoints use cursor-based pagination:

**Request:**
```
GET /v1.0/policies?limit=50&cursor=eyJpZCI6InBvbC0wMDEifQ==
```

**Response:**
```json
{
  "data": [...],
  "pagination": {
    "next_cursor": "eyJpZCI6InBvbC0wNTAifQ==",
    "has_next": true,
    "total": 1523
  }
}
```

### 6.5 Idempotency

Write operations support idempotency keys:

```
Idempotency-Key: 550e8400-e29b-41d4-a716-446655440000
```

If the same key is reused within 24 hours, the original response is returned without re-executing the operation.

---

## 7. REST API

### 7.1 Policy Management

#### 7.1.1 List Policies

```
GET /v1.0/policies
```

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `status` | string | No | Filter by status: `draft`, `review`, `active`, `deprecated`, `archived` |
| `category` | string | No | Filter by category: `ethics`, `safety`, `privacy`, `fairness` |
| `framework` | string | No | Filter by framework tag |
| `agent_id` | string | No | Filter by bound agent |
| `limit` | integer | No | Results per page (default: 50, max: 500) |
| `cursor` | string | No | Pagination cursor |

**Response:**
```json
{
  "data": [
    {
      "id": "pol-001",
      "policy_key": "AI-ETHICS-001",
      "name": "Data Access Control Policy",
      "description": "Controls agent access to data classifications",
      "category": "privacy",
      "status": "active",
      "version": "1.2.0",
      "framework_tags": ["SOC2", "ISO-27001", "GDPR"],
      "effective_date": "2026-08-15T00:00:00Z",
      "expiry_date": null,
      "owner_id": "user-001",
      "agent_bindings": ["agent-42", "agent-43"],
      "metadata": {
        "review_cycle": "quarterly",
        "approved_by": "user-002"
      },
      "created_at": "2026-08-15T10:00:00Z",
      "updated_at": "2026-09-20T14:30:00Z"
    }
  ],
  "pagination": {
    "next_cursor": "eyJpZCI6InBvbC0wMDEifQ==",
    "has_next": true,
    "total": 1523
  }
}
```

#### 7.1.2 Create Policy

```
POST /v1.0/policies
```

**Request:**
```json
{
  "policy_key": "AI-ETHICS-001",
  "name": "Data Access Control Policy",
  "description": "Controls agent access to data classifications",
  "category": "privacy",
  "framework_tags": ["SOC2", "ISO-27001", "GDPR"],
  "cedar_policy": "permit(\n  principal in Agent::\"data-analyst\",\n  action == Action::\"read\",\n  resource in DataClass::\"public\"\n) when {\n  resource.classification <= principal.clearance\n};",
  "metadata": {
    "review_cycle": "quarterly"
  }
}
```

**Response:** `201 Created`

```json
{
  "id": "pol-001",
  "policy_key": "AI-ETHICS-001",
  "name": "Data Access Control Policy",
  "description": "Controls agent access to data classifications",
  "category": "privacy",
  "status": "draft",
  "version": "1.0.0",
  "framework_tags": ["SOC2", "ISO-27001", "GDPR"],
  "effective_date": null,
  "expiry_date": null,
  "owner_id": "user-001",
  "agent_bindings": [],
  "metadata": {
    "review_cycle": "quarterly"
  },
  "created_at": "2026-10-01T14:30:00Z",
  "updated_at": "2026-10-01T14:30:00Z"
}
```

#### 7.1.3 Get Policy

```
GET /v1.0/policies/{policy_id}
```

**Response:** Full policy object including Cedar source and compiled Rego.

#### 7.1.4 Update Policy

```
PUT /v1.0/policies/{policy_id}
```

**Request:**
```json
{
  "name": "Data Access Control Policy v2",
  "description": "Updated controls for agent data access",
  "cedar_policy": "permit(\n  principal in Agent::\"data-analyst\",\n  action == Action::\"read\",\n  resource in DataClass::\"public\"\n) when {\n  resource.classification <= principal.clearance &&\n  context.time.hour >= 6 && context.time.hour <= 22\n};"
}
```

#### 7.1.5 Delete Policy

```
DELETE /v1.0/policies/{policy_id}
```

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `force` | boolean | No | Force delete even if active (default: false) |

**Response:** `204 No Content`

#### 7.1.6 Compile Policy

```
POST /v1.0/policies/{policy_id}/compile
```

Compiles Cedar policy to Rego for OPA evaluation.

**Response:**
```json
{
  "policy_id": "pol-001",
  "compilation_status": "success",
  "rego_policy": "package grc.agent.data_access\n\nimport future.keywords.if\nimport future.keywords.in\n\ndefault allow := false\n\nallow if {\n    input.principal.clearance >= input.resource.classification\n    input.action == \"read\"\n    input.resource.classification <= 2\n}",
  "warnings": [],
  "errors": [],
  "compiled_at": "2026-10-01T14:30:00Z"
}
```

#### 7.1.7 Dry-Run Policy

```
POST /v1.0/policies/{policy_id}/dry-run
```

**Request:**
```json
{
  "test_inputs": [
    {
      "principal": {"id": "agent-42", "clearance": 3},
      "action": "read",
      "resource": {"id": "dataset-001", "classification": 2},
      "context": {"time": "2026-10-01T14:30:00Z", "environment": "production"}
    },
    {
      "principal": {"id": "agent-42", "clearance": 3},
      "action": "read",
      "resource": {"id": "dataset-002", "classification": 4},
      "context": {"time": "2026-10-01T14:30:00Z", "environment": "production"}
    }
  ]
}
```

**Response:**
```json
{
  "policy_id": "pol-001",
  "dry_run_results": [
    {
      "input_index": 0,
      "decision": "ALLOW",
      "matched_rules": ["allow_read_public"],
      "evaluation_time_ms": 2.3
    },
    {
      "input_index": 1,
      "decision": "DENY",
      "matched_rules": ["deny_high_classification"],
      "reason": "Resource classification (4) exceeds principal clearance (3)",
      "evaluation_time_ms": 1.8
    }
  ],
  "summary": {
    "total": 2,
    "allowed": 1,
    "denied": 1,
    "avg_evaluation_time_ms": 2.05
  }
}
```

#### 7.1.8 Policy Version History

```
GET /v1.0/policies/{policy_id}/versions
```

**Response:**
```json
{
  "data": [
    {
      "version": "1.2.0",
      "status": "active",
      "change_summary": "Added time-based access restrictions",
      "created_at": "2026-09-20T14:30:00Z",
      "created_by": "user-002"
    },
    {
      "version": "1.1.0",
      "status": "superseded",
      "change_summary": "Added PII handling clause",
      "created_at": "2026-08-20T10:00:00Z",
      "created_by": "user-001"
    },
    {
      "version": "1.0.0",
      "status": "superseded",
      "change_summary": "Initial policy creation",
      "created_at": "2026-08-15T10:00:00Z",
      "created_by": "user-001"
    }
  ]
}
```

#### 7.1.9 Policy Dependency Graph

```
GET /v1.0/policies/{policy_id}/dependencies
```

**Response:**
```json
{
  "policy_id": "pol-001",
  "dependencies": [
    {
      "target_policy_id": "pol-000",
      "target_policy_name": "Base Agent Policy",
      "relation_type": "derives_from",
      "description": "Extends base agent policy with data access rules"
    }
  ],
  "dependents": [
    {
      "source_policy_id": "pol-003",
      "source_policy_name": "Data Export Policy",
      "relation_type": "conflicts_with",
      "description": "Export policy may conflict with access restrictions"
    }
  ]
}
```

---

### 7.2 Evidence Management

#### 7.2.1 Submit Evidence

```
POST /v1.0/evidence
```

**Request:**
```json
{
  "policy_id": "pol-001",
  "assessment_id": "asm-001",
  "source": {
    "type": "scan",
    "system": "aws-config",
    "collection_method": "api-query"
  },
  "evidence_type": "config",
  "content": {
    "format": "json",
    "data": "{\"encryption\": \"AES-256\", \"access_log\": true}"
  },
  "context": {
    "environment": "prod",
    "region": "us-east-1",
    "metadata": {
      "resource_type": "s3-bucket",
      "resource_id": "my-bucket"
    }
  },
  "control_mapping": {
    "control_id": "AC-2",
    "framework": "NIST-800-53",
    "control_title": "Account Management"
  }
}
```

**Response:** `201 Created`

```json
{
  "evidence_id": "evd-001",
  "policy_id": "pol-001",
  "assessment_id": "asm-001",
  "source": {
    "type": "scan",
    "system": "aws-config",
    "collection_method": "api-query"
  },
  "evidence_type": "config",
  "content": {
    "format": "json",
    "data": "{\"encryption\": \"AES-256\", \"access_log\": true}",
    "hash": "sha256:abc123..."
  },
  "context": {
    "environment": "prod",
    "region": "us-east-1",
    "timestamp": "2026-10-01T14:30:00Z",
    "metadata": {
      "resource_type": "s3-bucket",
      "resource_id": "my-bucket"
    }
  },
  "validation": {
    "status": "pending",
    "validated_by": null,
    "validated_at": null,
    "confidence_score": 0.0
  },
  "verification_level": "L0",
  "chain_of_custody": [
    {
      "action": "collected",
      "actor": "system",
      "timestamp": "2026-10-01T14:30:00Z",
      "hash": "sha256:abc123..."
    }
  ],
  "retention_class": "standard",
  "created_at": "2026-10-01T14:30:00Z",
  "expires_at": "2027-10-01T14:30:00Z"
}
```

#### 7.2.2 Get Evidence

```
GET /v1.0/evidence/{evidence_id}
```

**Response:** Full evidence item with chain of custody and verification status.

#### 7.2.3 Search Evidence

```
GET /v1.0/evidence
```

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `policy_id` | string | No | Filter by policy |
| `assessment_id` | string | No | Filter by assessment |
| `evidence_type` | string | No | Filter by type: `artifact`, `observation`, `interview`, `analysis`, `log` |
| `framework` | string | No | Filter by compliance framework |
| `control_id` | string | No | Filter by control ID |
| `verification_level` | string | No | Filter by verification level: `L0`-`L4` |
| `environment` | string | No | Filter by environment |
| `date_from` | string | No | Start date (ISO 8601) |
| `date_to` | string | No | End date (ISO 8601) |
| `query` | string | No | Full-text search query |

#### 7.2.4 Verify Evidence

```
POST /v1.0/evidence/{evidence_id}/verify
```

Triggers integrity verification and chain-of-custody validation.

**Response:**
```json
{
  "evidence_id": "evd-001",
  "verification_result": {
    "status": "verified",
    "verification_level": "L2",
    "hash_match": true,
    "chain_of_custody_intact": true,
    "schema_valid": true,
    "control_mapping_valid": true,
    "verified_at": "2026-10-01T14:35:00Z",
    "verified_by": "system"
  }
}
```

#### 7.2.5 Export Evidence Package

```
POST /v1.0/evidence/export
```

**Request:**
```json
{
  "framework": "NIST-800-53",
  "time_range": {
    "start": "2026-09-01T00:00:00Z",
    "end": "2026-10-01T00:00:00Z"
  },
  "format": "json",
  "include_chain_of_custody": true
}
```

**Response:** `202 Accepted` — Returns package ID for async processing.

```json
{
  "package_id": "pkg-001",
  "status": "processing",
  "estimated_completion": "2026-10-01T14:35:00Z",
  "download_url": null
}
```

#### 7.2.6 Get Export Package

```
GET /v1.0/evidence/export/{package_id}
```

**Response:** When complete, returns download URL.

```json
{
  "package_id": "pkg-001",
  "status": "completed",
  "download_url": "https://api.grc-claw.io/v1.0/evidence/export/pkg-001/download",
  "expires_at": "2026-10-08T14:35:00Z",
  "package_hash": "sha256:def456...",
  "manifest": {
    "framework": "NIST-800-53",
    "controls_assessed": 42,
    "evidence_items": 156,
    "evidence_summary": {
      "by_type": {
        "artifact": 45,
        "observation": 67,
        "interview": 12,
        "analysis": 20,
        "log": 12
      },
      "by_verification_level": {
        "L0": 0,
        "L1": 10,
        "L2": 120,
        "L3": 20,
        "L4": 6
      }
    }
  }
}
```

---

### 7.3 Enforcement Decisions

#### 7.3.1 Request Enforcement Decision

```
POST /v1.0/enforcement/decide
```

**Request:**
```json
{
  "agent_id": "agent-42",
  "action": "read",
  "resource": "s3://data/public/dataset.csv",
  "context": {
    "time": "2026-10-01T14:30:00Z",
    "environment": "production",
    "approval_ticket": null
  },
  "policy_ids": ["pol-001"],
  "include_evidence": true
}
```

**Response:**
```json
{
  "decision_id": "dec-001",
  "verdict": "ALLOW",
  "policy_id": "pol-001",
  "policy_version": "1.2.0",
  "agent_id": "agent-42",
  "action": "read",
  "resource": "s3://data/public/dataset.csv",
  "context": {
    "time": "2026-10-01T14:30:00Z",
    "environment": "production",
    "approval_ticket": null
  },
  "evidence_hash": "sha256:abc123...",
  "timestamp": "2026-10-01T14:30:00.123Z",
  "ttl": 300,
  "signature": "ecdsa-p256:def456...",
  "matched_rules": ["allow_read_public"],
  "evaluation_time_ms": 2.3
}
```

#### 7.3.2 Batch Enforcement Decisions

```
POST /v1.0/enforcement/decide-batch
```

**Request:**
```json
{
  "decisions": [
    {
      "agent_id": "agent-42",
      "action": "read",
      "resource": "s3://data/public/dataset.csv",
      "context": {"time": "2026-10-01T14:30:00Z", "environment": "production"}
    },
    {
      "agent_id": "agent-43",
      "action": "write",
      "resource": "s3://data/restricted/pii.db",
      "context": {"time": "2026-10-01T14:30:00Z", "environment": "production"}
    }
  ]
}
```

**Response:**
```json
{
  "results": [
    {
      "decision_id": "dec-001",
      "verdict": "ALLOW",
      "policy_id": "pol-001",
      "evaluation_time_ms": 2.3
    },
    {
      "decision_id": "dec-002",
      "verdict": "DENY",
      "policy_id": "pol-002",
      "reason": "PII access requires approval ticket",
      "evaluation_time_ms": 1.8
    }
  ],
  "summary": {
    "total": 2,
    "allowed": 1,
    "denied": 1,
    "avg_evaluation_time_ms": 2.05
  }
}
```

#### 7.3.3 Get Decision

```
GET /v1.0/enforcement/decisions/{decision_id}
```

**Response:** Full decision certificate with evidence.

#### 7.3.4 List Decisions

```
GET /v1.0/enforcement/decisions
```

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `agent_id` | string | No | Filter by agent |
| `policy_id` | string | No | Filter by policy |
| `verdict` | string | No | Filter by verdict |
| `date_from` | string | No | Start date |
| `date_to` | string | No | End date |

---

### 7.4 Assessment Management

#### 7.4.1 List Assessments

```
GET /v1.0/assessments
```

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `assessment_type` | string | No | `risk`, `compliance`, `maturity`, `readiness` |
| `status` | string | No | `planned`, `in_progress`, `completed`, `cancelled` |
| `target_type` | string | No | `model`, `system`, `organization`, `process` |
| `target_id` | string | No | Specific target |
| `methodology` | string | No | `NIST-AI-RMF`, `ISO-42001`, etc. |

#### 7.4.2 Get Assessment

```
GET /v1.0/assessments/{assessment_id}
```

**Response:**
```json
{
  "id": "asm-001",
  "assessment_key": "RISK-2026-Q4-001",
  "title": "Q4 2026 AI Risk Assessment",
  "description": "Quarterly risk assessment for all production AI systems",
  "assessment_type": "risk",
  "target_id": "all-production",
  "target_type": "organization",
  "status": "in_progress",
  "methodology": "NIST-AI-RMF",
  "score": 78.50,
  "risk_level": "medium",
  "started_at": "2026-10-01T09:00:00Z",
  "completed_at": null,
  "next_assessment_at": "2027-01-01T09:00:00Z",
  "lead_assessor": "user-001",
  "findings": [
    {
      "id": "fnd-001",
      "finding_key": "RISK-001",
      "title": "Insufficient training data documentation",
      "description": "Model X lacks complete training data provenance",
      "severity": "high",
      "category": "data_governance",
      "status": "open",
      "policy_id": "pol-001",
      "evidence_ids": ["evd-001", "evd-002"],
      "remediation": "Complete data card and provenance documentation",
      "remediated_by": null,
      "remediated_at": null,
      "due_date": "2026-11-01T00:00:00Z"
    }
  ],
  "metadata": {
    "assessment_period": "2026-Q4",
    "assessor_team": ["user-001", "user-002"]
  },
  "created_at": "2026-09-25T10:00:00Z",
  "updated_at": "2026-10-01T14:30:00Z"
}
```

#### 7.4.3 Create Assessment

```
POST /v1.0/assessments
```

**Request:**
```json
{
  "assessment_key": "RISK-2026-Q4-002",
  "title": "Model X Compliance Assessment",
  "description": "Compliance assessment for Model X against ISO 42001",
  "assessment_type": "compliance",
  "target_id": "model-x-v2",
  "target_type": "model",
  "methodology": "ISO-42001",
  "lead_assessor": "user-001",
  "metadata": {
    "assessment_period": "2026-Q4"
  }
}
```

#### 7.4.4 Update Assessment

```
PUT /v1.0/assessments/{assessment_id}
```

#### 7.4.5 Add Finding

```
POST /v1.0/assessments/{assessment_id}/findings
```

**Request:**
```json
{
  "finding_key": "COMP-001",
  "title": "Missing model card",
  "description": "Model X does not have a complete model card",
  "severity": "medium",
  "category": "documentation",
  "policy_id": "pol-003",
  "evidence_ids": ["evd-003"],
  "remediation": "Create and approve model card",
  "due_date": "2026-11-15T00:00:00Z"
}
```

#### 7.4.6 Generate Assessment Report

```
POST /v1.0/assessments/{assessment_id}/report
```

**Request:**
```json
{
  "format": "pdf",
  "include_evidence": true,
  "include_remediation": true
}
```

**Response:** `202 Accepted` — Returns report ID for async processing.

---

### 7.5 Compliance Mapping

#### 7.5.1 List Compliance Frameworks

```
GET /v1.0/compliance/frameworks
```

**Response:**
```json
{
  "data": [
    {
      "id": "fw-001",
      "framework_key": "NIST-800-53",
      "name": "NIST SP 800-53 Rev 5",
      "version": "5",
      "description": "Security and Privacy Controls for Information Systems",
      "authority": "NIST",
      "effective_date": "2020-09-23",
      "control_count": 1026
    },
    {
      "id": "fw-002",
      "framework_key": "SOC2",
      "name": "SOC 2 Trust Services Criteria",
      "version": "2017",
      "description": "Trust Services Criteria for Security, Availability, Processing Integrity, Confidentiality, and Privacy",
      "authority": "AICPA",
      "effective_date": "2017-04-01",
      "control_count": 64
    }
  ]
}
```

#### 7.5.2 List Controls

```
GET /v1.0/compliance/frameworks/{framework_id}/controls
```

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `category` | string | No | Filter by control family/category |
| `status` | string | No | Filter by compliance status |
| `target_id` | string | No | Filter by assessed target |

#### 7.5.3 Get Compliance Posture

```
GET /v1.0/compliance/posture
```

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `framework` | string | No | Filter by framework |
| `target_id` | string | No | Filter by target |
| `target_type` | string | No | Filter by target type |

**Response:**
```json
{
  "framework": "NIST-800-53",
  "target_id": "all-production",
  "target_type": "organization",
  "controls_assessed": 1026,
  "controls_compliant": 856,
  "controls_non_compliant": 120,
  "controls_not_assessed": 50,
  "compliance_score": 83.4,
  "gaps": [
    {
      "control_id": "AC-2",
      "control_title": "Account Management",
      "status": "non_compliant",
      "severity": "high",
      "evidence_count": 3,
      "last_assessed": "2026-09-15T10:00:00Z"
    }
  ],
  "trend": {
    "direction": "improving",
    "change": "+2.3%",
    "period": "30d"
  }
}
```

#### 7.5.4 Create Compliance Mapping

```
POST /v1.0/compliance/mappings
```

**Request:**
```json
{
  "control_id": "ctrl-001",
  "policy_id": "pol-001",
  "assessment_id": "asm-001",
  "mapping_type": "policy_satisfies",
  "coverage": "full",
  "notes": "Policy fully satisfies AC-2 control requirements"
}
```

#### 7.5.5 Generate Compliance Report

```
POST /v1.0/compliance/reports
```

**Request:**
```json
{
  "framework": "NIST-800-53",
  "time_range": {
    "start": "2026-09-01T00:00:00Z",
    "end": "2026-10-01T00:00:00Z"
  },
  "format": "json",
  "include_evidence": true,
  "include_gaps": true
}
```

**Response:** `202 Accepted` — Returns report ID for async processing.

#### 7.5.6 Crosswalk Query

```
GET /v1.0/compliance/crosswalk
```

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `control_id` | string | No | GRC_Claw control ID |
| `framework` | string | No | Source framework |
| `target_framework` | string | No | Target framework for mapping |

**Response:**
```json
{
  "grc_control_id": "ctrl-001",
  "mappings": {
    "nist_800_53": ["AC-2", "AC-3", "AC-6"],
    "soc2": ["CC6.1", "CC6.2", "CC6.3"],
    "iso_27001": ["A.12.4", "A.12.5"],
    "iso_42001": ["A.6", "A.9"],
    "gdpr": ["Art.5", "Art.25"],
    "hipaa": ["164.308(a)(1)", "164.312(b)"],
    "pci_dss": ["10.1", "10.2", "10.3"],
    "cobit": ["DSS06", "APO12"],
    "nist_ai_rmf": ["Govern", "Map", "Measure"],
    "eu_ai_act": ["Annex III", "Art.9"]
  }
}
```

---

### 7.6 Agent Registry

#### 7.6.1 List Agents

```
GET /v1.0/agents
```

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `type` | string | No | `model`, `agent`, `pipeline`, `endpoint` |
| `framework` | string | No | `langchain`, `autogen`, `crewai`, `custom`, `mcp-server` |
| `lifecycle_stage` | string | No | `proposed`, `approved`, `active`, `deprecated`, `terminated` |
| `risk_tier` | string | No | `prohibited`, `high`, `limited`, `minimal` |
| `trust_score_min` | integer | No | Minimum trust score (0-100) |

#### 7.6.2 Get Agent

```
GET /v1.0/agents/{agent_id}
```

**Response:**
```json
{
  "id": "agent-42",
  "name": "Data Analyst Agent",
  "type": "agent",
  "framework": "langchain",
  "owner": "user-001",
  "lifecycle_stage": "active",
  "risk_tier": "limited",
  "capabilities": [
    {
      "name": "read_data",
      "description": "Read data from approved sources",
      "permissions": ["read"],
      "resource_scope": "s3://data/public/*"
    }
  ],
  "identity": {
    "spiffe_id": "spiffe://grc-claw.io/ns/prod/sa/agent-42",
    "mtls_cert": "-----BEGIN CERTIFICATE-----\n...",
    "cert_expiry": "2026-10-02T14:30:00Z"
  },
  "trust_score": {
    "value": 85,
    "grade": "B",
    "last_evaluated": "2026-10-01T12:00:00Z"
  },
  "policy_bindings": ["pol-001", "pol-002"],
  "created_at": "2026-08-01T10:00:00Z",
  "updated_at": "2026-10-01T12:00:00Z"
}
```

#### 7.6.3 Register Agent

```
POST /v1.0/agents
```

**Request:**
```json
{
  "name": "New Agent",
  "type": "agent",
  "framework": "custom",
  "owner": "user-001",
  "risk_tier": "limited",
  "capabilities": [
    {
      "name": "read_data",
      "description": "Read data from approved sources",
      "permissions": ["read"],
      "resource_scope": "s3://data/public/*"
    }
  ]
}
```

#### 7.6.4 Update Agent

```
PUT /v1.0/agents/{agent_id}
```

#### 7.6.5 Update Agent Trust Score

```
POST /v1.0/agents/{agent_id}/trust-score
```

**Request:**
```json
{
  "value": 92,
  "grade": "A",
  "reason": "Consistent compliant behavior over 30 days"
}
```

#### 7.6.6 Bind Policy to Agent

```
POST /v1.0/agents/{agent_id}/policy-bindings
```

**Request:**
```json
{
  "policy_ids": ["pol-001", "pol-002"]
}
```

---

### 7.7 Audit Trail

#### 7.7.1 Query Audit Trail

```
GET /v1.0/audit
```

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `event_type` | string | No | Filter by event type |
| `actor_id` | string | No | Filter by actor |
| `resource_type` | string | No | Filter by resource type |
| `resource_id` | string | No | Filter by resource ID |
| `date_from` | string | No | Start date |
| `date_to` | string | No | End date |
| `limit` | integer | No | Max results (default: 100, max: 1000) |

**Response:**
```json
{
  "data": [
    {
      "event_id": "evt-001",
      "event_type": "policy.created",
      "actor": {
        "type": "user",
        "id": "user-001",
        "name": "John Doe"
      },
      "resource": {
        "type": "policy",
        "id": "pol-001",
        "name": "Data Access Control Policy"
      },
      "timestamp": "2026-10-01T14:30:00Z",
      "details": {
        "policy_key": "AI-ETHICS-001",
        "version": "1.0.0"
      },
      "integrity_hash": "sha256:abc123...",
      "previous_event_hash": "sha256:def456..."
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 100,
    "total": 15234
  }
}
```

#### 7.7.2 Verify Audit Chain

```
POST /v1.0/audit/verify
```

**Request:**
```json
{
  "from_event_id": "evt-001",
  "to_event_id": "evt-1000"
}
```

**Response:**
```json
{
  "verification_status": "valid",
  "events_verified": 1000,
  "chain_intact": true,
  "first_event_id": "evt-001",
  "last_event_id": "evt-1000",
  "verified_at": "2026-10-01T14:35:00Z"
}
```

---

### 7.8 Health & Monitoring

#### 7.8.1 Health Check

```
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "components": {
    "api": {"status": "up"},
    "policy_engine": {"status": "up"},
    "evidence_store": {"status": "up"},
    "database": {"status": "up"},
    "cache": {"status": "up"}
  },
  "timestamp": "2026-10-01T14:30:00Z"
}
```

#### 7.8.2 Readiness Check

```
GET /ready
```

**Response:**
```json
{
  "ready": true,
  "checks": {
    "database": {"status": "pass"},
    "policy_engine": {"status": "pass"},
    "evidence_store": {"status": "pass"}
  }
}
```

#### 7.8.3 Metrics

```
GET /metrics
```

Returns Prometheus-formatted metrics.

---

## 8. GraphQL Schema

### 8.1 Overview

The GraphQL API provides a single endpoint for complex, nested queries that would require multiple REST calls. It is optimized for dashboard rendering, compliance reporting, and cross-resource analytics.

**Endpoint:** `POST /v1.0/graphql`

**Endpoint (WebSocket subscriptions):** `wss://api.grc-claw.io/v1.0/graphql`

### 8.2 Schema Definition

```graphql
# ============================================================
# GRC_Claw GraphQL Schema
# Version: 1.0
# ============================================================

scalar DateTime
scalar JSON
scalar UUID

# ============================================================
# Enums
# ============================================================

enum PolicyStatus {
  DRAFT
  REVIEW
  ACTIVE
  DEPRECATED
  ARCHIVED
}

enum PolicyCategory {
  ETHICS
  SAFETY
  PRIVACY
  FAIRNESS
}

enum EvidenceType {
  ARTIFACT
  OBSERVATION
  INTERVIEW
  ANALYSIS
  LOG
}

enum VerificationLevel {
  L0
  L1
  L2
  L3
  L4
}

enum EnforcementVerdict {
  ALLOW
  ALLOW_WITH_REDACTION
  REQUIRE_APPROVAL
  DENY
  QUARANTINE
}

enum AssessmentType {
  RISK
  COMPLIANCE
  MATURITY
  READINESS
}

enum AssessmentStatus {
  PLANNED
  IN_PROGRESS
  COMPLETED
  CANCELLED
}

enum ComplianceStatus {
  COMPLIANT
  NON_COMPLIANT
  PARTIAL
  NOT_ASSESSED
  EXEMPT
}

enum AgentLifecycleStage {
  PROPOSED
  APPROVED
  ACTIVE
  DEPRECATED
  TERMINATED
  SUSPENDED
  QUARANTINED
}

enum RiskTier {
  PROHIBITED
  HIGH
  LIMITED
  MINIMAL
}

# ============================================================
# Interfaces
# ============================================================

interface Node {
  id: ID!
}

interface Timestamped {
  createdAt: DateTime!
  updatedAt: DateTime!
}

# ============================================================
# Types
# ============================================================

type Policy implements Node & Timestamped {
  id: ID!
  policyKey: String!
  name: String!
  description: String
  category: PolicyCategory!
  status: PolicyStatus!
  version: String!
  frameworkTags: [String!]!
  effectiveDate: DateTime
  expiryDate: DateTime
  owner: User
  agentBindings: [Agent!]!
  cedarPolicy: String
  regoPolicy: String
  metadata: JSON
  complianceMappings: [ComplianceMapping!]!
  dependencies: [Policy!]!
  dependents: [Policy!]!
  versions: [PolicyVersion!]!
  createdAt: DateTime!
  updatedAt: DateTime!
  createdBy: User!
  updatedBy: User!
}

type PolicyVersion {
  version: String!
  status: String!
  changeSummary: String
  createdAt: DateTime!
  createdBy: User!
}

type Evidence implements Node & Timestamped {
  id: ID!
  policy: Policy
  assessment: Assessment
  source: EvidenceSource!
  evidenceType: EvidenceType!
  content: EvidenceContent!
  context: EvidenceContext!
  validation: ValidationStatus!
  verificationLevel: VerificationLevel!
  chainOfCustody: [CustodyEvent!]!
  retentionClass: String!
  createdAt: DateTime!
  expiresAt: DateTime
}

type EvidenceSource {
  type: String!
  system: String!
  collectionMethod: String!
}

type EvidenceContent {
  format: String!
  data: String!
  hash: String!
}

type EvidenceContext {
  environment: String!
  region: String
  timestamp: DateTime!
  metadata: JSON
}

type ValidationStatus {
  status: String!
  validatedBy: User
  validatedAt: DateTime
  confidenceScore: Float!
}

type CustodyEvent {
  action: String!
  actor: String!
  timestamp: DateTime!
  hash: String!
}

type EnforcementDecision implements Node {
  id: ID!
  verdict: EnforcementVerdict!
  policy: Policy!
  policyVersion: String!
  agent: Agent!
  action: String!
  resource: String!
  context: JSON!
  evidenceHash: String!
  timestamp: DateTime!
  ttl: Int!
  signature: String!
  matchedRules: [String!]!
  evaluationTimeMs: Float!
}

type Assessment implements Node & Timestamped {
  id: ID!
  assessmentKey: String!
  title: String!
  description: String
  assessmentType: AssessmentType!
  targetId: String!
  targetType: String!
  status: AssessmentStatus!
  methodology: String
  score: Float
  riskLevel: String
  startedAt: DateTime
  completedAt: DateTime
  nextAssessmentAt: DateTime
  leadAssessor: User!
  findings: [AssessmentFinding!]!
  evidence: [Evidence!]!
  metadata: JSON
  createdAt: DateTime!
  updatedAt: DateTime!
}

type AssessmentFinding implements Node & Timestamped {
  id: ID!
  findingKey: String!
  title: String!
  description: String!
  severity: String!
  category: String!
  status: String!
  policy: Policy
  evidence: [Evidence!]!
  remediation: String
  remediatedBy: User
  remediatedAt: DateTime
  dueDate: DateTime
  createdAt: DateTime!
  updatedAt: DateTime!
}

type ComplianceFramework implements Node & Timestamped {
  id: ID!
  frameworkKey: String!
  name: String!
  version: String!
  description: String
  authority: String
  effectiveDate: DateTime
  controls: [ComplianceControl!]!
  controlCount: Int!
  createdAt: DateTime!
  updatedAt: DateTime!
}

type ComplianceControl implements Node & Timestamped {
  id: ID!
  framework: ComplianceFramework!
  controlKey: String!
  title: String!
  description: String!
  category: String!
  guidance: String
  mappings: [ComplianceMapping!]!
  status(targetId: String, targetType: String): ComplianceStatus!
  createdAt: DateTime!
  updatedAt: DateTime!
}

type ComplianceMapping implements Node & Timestamped {
  id: ID!
  control: ComplianceControl!
  policy: Policy
  assessment: Assessment
  mappingType: String!
  coverage: String!
  notes: String
  mappedBy: User!
  mappedAt: DateTime!
  updatedAt: DateTime!
}

type CompliancePosture {
  framework: ComplianceFramework!
  targetId: String!
  targetType: String!
  controlsAssessed: Int!
  controlsCompliant: Int!
  controlsNonCompliant: Int!
  controlsNotAssessed: Int!
  complianceScore: Float!
  gaps: [ComplianceGap!]!
  trend: ComplianceTrend!
}

type ComplianceGap {
  control: ComplianceControl!
  status: ComplianceStatus!
  severity: String!
  evidenceCount: Int!
  lastAssessed: DateTime
}

type ComplianceTrend {
  direction: String!
  change: String!
  period: String!
}

type Agent implements Node & Timestamped {
  id: ID!
  name: String!
  type: String!
  framework: String!
  owner: User!
  lifecycleStage: AgentLifecycleStage!
  riskTier: RiskTier!
  capabilities: [AgentCapability!]!
  identity: AgentIdentity!
  trustScore: TrustScore!
  policyBindings: [Policy!]!
  createdAt: DateTime!
  updatedAt: DateTime!
}

type AgentCapability {
  name: String!
  description: String!
  permissions: [String!]!
  resourceScope: String!
}

type AgentIdentity {
  spiffeId: String!
  mtlsCert: String!
  certExpiry: DateTime!
}

type TrustScore {
  value: Int!
  grade: String!
  lastEvaluated: DateTime!
}

type User implements Node {
  id: ID!
  name: String!
  email: String!
  roles: [String!]!
}

type AuditEvent implements Node {
  id: ID!
  eventType: String!
  actor: Actor!
  resource: Resource!
  timestamp: DateTime!
  details: JSON!
  integrityHash: String!
  previousEventHash: String!
}

type Actor {
  type: String!
  id: String!
  name: String
}

type Resource {
  type: String!
  id: String!
  name: String
}

# ============================================================
# Input Types
# ============================================================

input PolicyInput {
  policyKey: String!
  name: String!
  description: String
  category: PolicyCategory!
  frameworkTags: [String!]!
  cedarPolicy: String
  metadata: JSON
}

input PolicyUpdateInput {
  name: String
  description: String
  cedarPolicy: String
  metadata: JSON
}

input EvidenceInput {
  policyId: ID
  assessmentId: ID
  source: EvidenceSourceInput!
  evidenceType: EvidenceType!
  content: EvidenceContentInput!
  context: EvidenceContextInput!
  controlMapping: ControlMappingInput
}

input EvidenceSourceInput {
  type: String!
  system: String!
  collectionMethod: String!
}

input EvidenceContentInput {
  format: String!
  data: String!
}

input EvidenceContextInput {
  environment: String!
  region: String
  metadata: JSON
}

input ControlMappingInput {
  controlId: String!
  framework: String!
  controlTitle: String!
  controlFamily: String
}

input AssessmentInput {
  assessmentKey: String!
  title: String!
  description: String
  assessmentType: AssessmentType!
  targetId: String!
  targetType: String!
  methodology: String
  leadAssessor: ID!
  metadata: JSON
}

input FindingInput {
  findingKey: String!
  title: String!
  description: String!
  severity: String!
  category: String!
  policyId: ID
  evidenceIds: [ID!]
  remediation: String
  dueDate: DateTime
}

input AgentInput {
  name: String!
  type: String!
  framework: String!
  owner: ID!
  riskTier: RiskTier!
  capabilities: [AgentCapabilityInput!]!
}

input AgentCapabilityInput {
  name: String!
  description: String!
  permissions: [String!]!
  resourceScope: String!
}

input ComplianceMappingInput {
  controlId: ID!
  policyId: ID
  assessmentId: ID
  mappingType: String!
  coverage: String!
  notes: String
}

input PolicyFilter {
  status: PolicyStatus
  category: PolicyCategory
  framework: String
  agentId: ID
}

input EvidenceFilter {
  policyId: ID
  assessmentId: ID
  evidenceType: EvidenceType
  framework: String
  controlId: String
  verificationLevel: VerificationLevel
  environment: String
  dateFrom: DateTime
  dateTo: DateTime
  query: String
}

input AssessmentFilter {
  assessmentType: AssessmentType
  status: AssessmentStatus
  targetType: String
  targetId: String
  methodology: String
}

input AgentFilter {
  type: String
  framework: String
  lifecycleStage: AgentLifecycleStage
  riskTier: RiskTier
  trustScoreMin: Int
}

input AuditFilter {
  eventType: String
  actorId: ID
  resourceType: String
  resourceId: ID
  dateFrom: DateTime
  dateTo: DateTime
}

# ============================================================
# Pagination
# ============================================================

type PageInfo {
  hasNextPage: Boolean!
  hasPreviousPage: Boolean!
  startCursor: String
  endCursor: String
  totalCount: Int!
}

type PolicyConnection {
  edges: [PolicyEdge!]!
  pageInfo: PageInfo!
}

type PolicyEdge {
  node: Policy!
  cursor: String!
}

type EvidenceConnection {
  edges: [EvidenceEdge!]!
  pageInfo: PageInfo!
}

type EvidenceEdge {
  node: Evidence!
  cursor: String!
}

type AssessmentConnection {
  edges: [AssessmentEdge!]!
  pageInfo: PageInfo!
}

type AssessmentEdge {
  node: Assessment!
  cursor: String!
}

type AgentConnection {
  edges: [AgentEdge!]!
  pageInfo: PageInfo!
}

type AgentEdge {
  node: Agent!
  cursor: String!
}

type AuditConnection {
  edges: [AuditEdge!]!
  pageInfo: PageInfo!
}

type AuditEdge {
  node: AuditEvent!
  cursor: String!
}

# ============================================================
# Queries
# ============================================================

type Query {
  # Node query (Relay-style)
  node(id: ID!): Node

  # Policies
  policy(id: ID!): Policy
  policies(
    filter: PolicyFilter
    first: Int
    after: String
    last: Int
    before: String
  ): PolicyConnection!

  # Evidence
  evidence(id: ID!): Evidence
  evidences(
    filter: EvidenceFilter
    first: Int
    after: String
    last: Int
    before: String
  ): EvidenceConnection!

  # Enforcement
  enforcementDecision(id: ID!): EnforcementDecision
  enforcementDecisions(
    agentId: ID
    policyId: ID
    verdict: EnforcementVerdict
    dateFrom: DateTime
    dateTo: DateTime
    first: Int
    after: String
  ): [EnforcementDecision!]!

  # Assessments
  assessment(id: ID!): Assessment
  assessments(
    filter: AssessmentFilter
    first: Int
    after: String
    last: Int
    before: String
  ): AssessmentConnection!

  # Compliance
  complianceFramework(id: ID!): ComplianceFramework
  complianceFrameworks: [ComplianceFramework!]!
  complianceControl(id: ID!): ComplianceControl
  compliancePosture(
    frameworkId: ID!
    targetId: String!
    targetType: String!
  ): CompliancePosture!
  complianceCrosswalk(controlId: ID!): JSON!

  # Agents
  agent(id: ID!): Agent
  agents(
    filter: AgentFilter
    first: Int
    after: String
    last: Int
    before: String
  ): AgentConnection!

  # Audit
  auditEvent(id: ID!): AuditEvent
  auditEvents(
    filter: AuditFilter
    first: Int
    after: String
    last: Int
    before: String
  ): AuditConnection!

  # Users
  user(id: ID!): User
  me: User!
}

# ============================================================
# Mutations
# ============================================================

type Mutation {
  # Policies
  createPolicy(input: PolicyInput!): Policy!
  updatePolicy(id: ID!, input: PolicyUpdateInput!): Policy!
  deletePolicy(id: ID!, force: Boolean): Boolean!
  compilePolicy(id: ID!): JSON!
  dryRunPolicy(id: ID!, testInputs: [JSON!]!): JSON!
  activatePolicy(id: ID!): Policy!
  deprecatePolicy(id: ID!): Policy!

  # Evidence
  submitEvidence(input: EvidenceInput!): Evidence!
  verifyEvidence(id: ID!): JSON!
  exportEvidencePackage(
    framework: String!
    timeRange: JSON!
    format: String!
    includeChainOfCustody: Boolean!
  ): JSON!

  # Enforcement
  requestDecision(
    agentId: ID!
    action: String!
    resource: String!
    context: JSON!
    policyIds: [ID!]
    includeEvidence: Boolean!
  ): EnforcementDecision!
  requestBatchDecision(
    decisions: [DecisionInput!]!
  ): [EnforcementDecision!]!

  # Assessments
  createAssessment(input: AssessmentInput!): Assessment!
  updateAssessment(id: ID!, input: AssessmentInput!): Assessment!
  addFinding(assessmentId: ID!, input: FindingInput!): AssessmentFinding!
  updateFinding(id: ID!, input: FindingInput!): AssessmentFinding!
  generateAssessmentReport(id: ID!, format: String!): JSON!

  # Compliance
  createComplianceMapping(input: ComplianceMappingInput!): ComplianceMapping!
  deleteComplianceMapping(id: ID!): Boolean!
  generateComplianceReport(
    framework: String!
    timeRange: JSON!
    format: String!
  ): JSON!

  # Agents
  registerAgent(input: AgentInput!): Agent!
  updateAgent(id: ID!, input: AgentInput!): Agent!
  deleteAgent(id: ID!): Boolean!
  updateAgentTrustScore(agentId: ID!, value: Int!, grade: String!, reason: String): Agent!
  bindPolicyToAgent(agentId: ID!, policyIds: [ID!]!): Agent!
  unbindPolicyFromAgent(agentId: ID!, policyIds: [ID!]!): Agent!
}

input DecisionInput {
  agentId: ID!
  action: String!
  resource: String!
  context: JSON!
  policyIds: [ID!]
  includeEvidence: Boolean!
}

# ============================================================
# Subscriptions (WebSocket)
# ============================================================

type Subscription {
  # Real-time enforcement decisions for an agent
  enforcementDecisions(agentId: ID!): EnforcementDecision!

  # Real-time evidence collection events
  evidenceCollected(policyId: ID): Evidence!

  # Real-time policy changes
  policyChanged(tenantId: ID): Policy!

  # Real-time compliance posture changes
  compliancePostureChanged(frameworkId: ID!, targetId: ID!): CompliancePosture!

  # Real-time agent trust score changes
  agentTrustScoreChanged(agentId: ID!): Agent!

  # Real-time audit events
  auditEventCreated: AuditEvent!
}
```

### 8.3 Example Queries

#### 8.3.1 Complex Dashboard Query

```graphql
query DashboardOverview($tenantId: ID!) {
  # Compliance posture across all frameworks
  complianceFrameworks {
    id
    name
    controlCount
    posture: compliancePosture(frameworkId: "fw-001", targetId: "all", targetType: "organization") {
      complianceScore
      controlsCompliant
      controlsNonCompliant
      gaps {
        control { controlKey title }
        status
        severity
      }
      trend { direction change period }
    }
  }

  # Active agents with trust scores
  agents(filter: { lifecycleStage: ACTIVE }, first: 50) {
    edges {
      node {
        id
        name
        framework
        trustScore { value grade }
        policyBindings { id name status }
      }
    }
  }

  # Recent enforcement decisions
  enforcementDecisions(first: 20, dateFrom: "2026-10-01T00:00:00Z") {
    id
    verdict
    agent { id name }
    policy { id name }
    action
    resource
    timestamp
  }

  # Open assessment findings
  assessments(filter: { status: IN_PROGRESS }) {
    edges {
      node {
        id
        title
        score
        riskLevel
        findings(status: "open") {
          id
          title
          severity
          status
          dueDate
        }
      }
    }
  }
}
```

#### 8.3.2 Compliance Report Query

```graphql
query ComplianceReport($frameworkId: ID!, $timeRange: JSON!) {
  complianceFramework(id: $frameworkId) {
    id
    name
    version
    controls {
      id
      controlKey
      title
      category
      status(targetId: "all", targetType: "organization")
      mappings {
        policy { id name status version }
        assessment { id title score }
        coverage
      }
    }
  }
}
```

#### 8.3.3 Agent Governance Query

```graphql
query AgentGovernance($agentId: ID!) {
  agent(id: $agentId) {
    id
    name
    type
    framework
    lifecycleStage
    riskTier
    trustScore { value grade lastEvaluated }
    capabilities { name permissions resourceScope }
    policyBindings {
      id
      name
      status
      version
      frameworkTags
    }
    # Recent decisions for this agent
    # (resolved via dataloader)
  }
}
```

---

## 9. gRPC Interface

### 9.1 Overview

The gRPC interface provides high-performance, low-latency communication for enforcement decisions and streaming scenarios. It is the preferred interface for AI agents and enforcement proxies.

**Endpoint:** `grpc.grc-claw.io:443` (production) or `localhost:50051` (local)

**Protocol:** HTTP/2 with Protocol Buffers

**Authentication:** mTLS with SPIFFE SVIDs

### 9.2 Protocol Buffer Definition

```protobuf
syntax = "proto3";

package grcclaw.v1;

import "google/protobuf/timestamp.proto";
import "google/protobuf/struct.proto";
import "google/protobuf/duration.proto";

option go_package = "github.com/grc-claw/api/go/v1;grcclawv1";
option java_package = "io.grccLaw.api.v1";
option python_package = "grc_claw.api.v1";

// ============================================================
// Enforcement Service
// ============================================================

service EnforcementService {
  // Single enforcement decision
  rpc Decide(DecideRequest) returns (DecideResponse);

  // Batch enforcement decisions
  rpc DecideBatch(DecideBatchRequest) returns (DecideBatchResponse);

  // Streaming enforcement decisions (bidirectional)
  rpc StreamDecisions(stream DecideRequest) returns (stream DecideResponse);

  // Server-streaming: subscribe to decisions for an agent
  rpc SubscribeDecisions(SubscribeRequest) returns (stream DecideResponse);

  // Health check
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
  string strategy = 2;  // "mask", "remove", "hash", "tokenize"
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

// ============================================================
// Policy Service
// ============================================================

service PolicyService {
  // Get a policy by ID
  rpc GetPolicy(GetPolicyRequest) returns (Policy);

  // List policies with filtering
  rpc ListPolicies(ListPoliciesRequest) returns (ListPoliciesResponse);

  // Create a new policy
  rpc CreatePolicy(CreatePolicyRequest) returns (Policy);

  // Update an existing policy
  rpc UpdatePolicy(UpdatePolicyRequest) returns (Policy);

  // Delete a policy
  rpc DeletePolicy(DeletePolicyRequest) returns (DeletePolicyResponse);

  // Compile a policy (Cedar → Rego)
  rpc CompilePolicy(CompilePolicyRequest) returns (CompilePolicyResponse);

  // Dry-run a policy against test inputs
  rpc DryRunPolicy(DryRunPolicyRequest) returns (DryRunPolicyResponse);

  // Stream policy changes (server-streaming)
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

// ============================================================
// Evidence Service
// ============================================================

service EvidenceService {
  // Submit evidence
  rpc SubmitEvidence(SubmitEvidenceRequest) returns (Evidence);

  // Get evidence by ID
  rpc GetEvidence(GetEvidenceRequest) returns (Evidence);

  // Search evidence
  rpc SearchEvidence(SearchEvidenceRequest) returns (SearchEvidenceResponse);

  // Verify evidence integrity
  rpc VerifyEvidence(VerifyEvidenceRequest) returns (VerifyEvidenceResponse);

  // Stream evidence collection events
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

// ============================================================
// Agent Service
// ============================================================

service AgentService {
  // Register a new agent
  rpc RegisterAgent(RegisterAgentRequest) returns (Agent);

  // Get agent by ID
  rpc GetAgent(GetAgentRequest) returns (Agent);

  // List agents
  rpc ListAgents(ListAgentsRequest) returns (ListAgentsResponse);

  // Update agent
  rpc UpdateAgent(UpdateAgentRequest) returns (Agent);

  // Update trust score
  rpc UpdateTrustScore(UpdateTrustScoreRequest) returns (Agent);

  // Bind policies to agent
  rpc BindPolicies(BindPoliciesRequest) returns (Agent);

  // Stream agent events
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

### 9.3 gRPC Client Examples

#### 9.3.1 Python Client

```python
import grpc
from grc_claw.api.v1 import enforcement_pb2, enforcement_pb2_grpc

# Create channel with mTLS
credentials = grpc.ssl_channel_credentials(
    root_certificates=open("ca.crt", "rb").read(),
    private_key=open("client.key", "rb").read(),
    certificate_chain=open("client.crt", "rb").read(),
)

channel = grpc.secure_channel("grpc.grc-claw.io:443", credentials)
stub = enforcement_pb2_grpc.EnforcementServiceStub(channel)

# Single decision
request = enforcement_pb2.DecideRequest(
    request_id="req-001",
    agent_id="agent-42",
    action="read",
    resource="s3://data/public/dataset.csv",
    context={"time": "2026-10-01T14:30:00Z", "environment": "production"},
    tenant_id="org-acme",
)

response = stub.Decide(request)
print(f"Verdict: {response.verdict}")
print(f"Evaluation time: {response.evaluation_time_ms}ms")

# Streaming decisions
def request_generator():
    for i in range(100):
        yield enforcement_pb2.DecideRequest(
            request_id=f"req-{i}",
            agent_id="agent-42",
            action="read",
            resource=f"s3://data/public/file-{i}.csv",
            context={"time": "2026-10-01T14:30:00Z"},
            tenant_id="org-acme",
        )

for response in stub.StreamDecisions(request_generator()):
    print(f"Decision {response.decision_id}: {response.verdict}")
```

#### 9.3.2 Go Client

```go
package main

import (
    "context"
    "log"
    "time"

    "google.golang.org/grpc"
    "google.golang.org/grpc/credentials"
    pb "github.com/grc-claw/api/go/v1"
)

func main() {
    creds, err := credentials.NewClientTLSFromFile("ca.crt", "")
    if err != nil {
        log.Fatalf("Failed to create credentials: %v", err)
    }

    conn, err := grpc.Dial("grpc.grc-claw.io:443", grpc.WithTransportCredentials(creds))
    if err != nil {
        log.Fatalf("Failed to connect: %v", err)
    }
    defer conn.Close()

    client := pb.NewEnforcementServiceClient(conn)

    ctx, cancel := context.WithTimeout(context.Background(), 10*time.Millisecond)
    defer cancel()

    resp, err := client.Decide(ctx, &pb.DecideRequest{
        RequestId: "req-001",
        AgentId:   "agent-42",
        Action:    "read",
        Resource:  "s3://data/public/dataset.csv",
        Context:   map[string]interface{}{"environment": "production"},
        TenantId:  "org-acme",
    })
    if err != nil {
        log.Fatalf("Decide failed: %v", err)
    }

    log.Printf("Verdict: %v, Time: %fms", resp.Verdict, resp.EvaluationTimeMs)
}
```

### 9.4 gRPC Performance Characteristics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Decision latency (p99) | < 10ms | End-to-end gRPC round-trip |
| Throughput per instance | 50,000 decisions/sec | Single gRPC server instance |
| Connection multiplexing | 1,000 streams per connection | HTTP/2 stream multiplexing |
| Message size | < 10 KB | Average decision request/response |
| Keepalive | 30 seconds | HTTP/2 ping interval |
| Max concurrent streams | 10,000 | Per gRPC server instance |

---

## 10. Webhook API

### 10.1 Overview

Webhooks enable event-driven integrations by pushing real-time notifications to registered HTTP endpoints when governance events occur.

**Delivery model:** At-least-once delivery with exponential backoff retry

**Endpoint URL:** `POST {subscriber_url}`

**Content-Type:** `application/json`

**Signature:** `X-GRC-Signature` header with HMAC-SHA256 signature

### 10.2 Webhook Subscription Management

#### 10.2.1 Create Subscription

```
POST /v1.0/webhooks/subscriptions
```

**Request:**
```json
{
  "url": "https://example.com/webhooks/grc-claw",
  "events": [
    "policy.created",
    "policy.updated",
    "policy.status_changed",
    "enforcement.decision_made",
    "evidence.collected",
    "evidence.verified",
    "assessment.created",
    "assessment.completed",
    "compliance.posture_changed",
    "agent.registered",
    "agent.trust_score_changed",
    "audit.event_created"
  ],
  "secret": "whsec_abc123def456",
  "description": "Production webhook for compliance events",
  "active": true,
  "metadata": {
    "team": "compliance",
    "priority": "high"
  }
}
```

**Response:** `201 Created`

```json
{
  "subscription_id": "sub-001",
  "url": "https://example.com/webhooks/grc-claw",
  "events": [
    "policy.created",
    "policy.updated",
    "policy.status_changed",
    "enforcement.decision_made",
    "evidence.collected",
    "evidence.verified",
    "assessment.created",
    "assessment.completed",
    "compliance.posture_changed",
    "agent.registered",
    "agent.trust_score_changed",
    "audit.event_created"
  ],
  "secret": "whsec_abc123def456",
  "description": "Production webhook for compliance events",
  "active": true,
  "metadata": {
    "team": "compliance",
    "priority": "high"
  },
  "created_at": "2026-10-01T14:30:00Z",
  "delivery_stats": {
    "total_deliveries": 0,
    "successful_deliveries": 0,
    "failed_deliveries": 0,
    "last_delivery_at": null
  }
}
```

#### 10.2.2 List Subscriptions

```
GET /v1.0/webhooks/subscriptions
```

#### 10.2.3 Get Subscription

```
GET /v1.0/webhooks/subscriptions/{subscription_id}
```

#### 10.2.4 Update Subscription

```
PUT /v1.0/webhooks/subscriptions/{subscription_id}
```

#### 10.2.5 Delete Subscription

```
DELETE /v1.0/webhooks/subscriptions/{subscription_id}
```

#### 10.2.6 Test Subscription

```
POST /v1.0/webhooks/subscriptions/{subscription_id}/test
```

Sends a test event to the subscriber endpoint.

**Response:**
```json
{
  "subscription_id": "sub-001",
  "test_event_id": "evt-test-001",
  "delivery_status": "delivered",
  "http_status": 200,
  "response_time_ms": 45,
  "delivered_at": "2026-10-01T14:35:00Z"
}
```

#### 10.2.7 Get Delivery History

```
GET /v1.0/webhooks/subscriptions/{subscription_id}/deliveries
```

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `status` | string | No | Filter by delivery status |
| `date_from` | string | No | Start date |
| `date_to` | string | No | End date |

**Response:**
```json
{
  "data": [
    {
      "delivery_id": "del-001",
      "subscription_id": "sub-001",
      "event_id": "evt-001",
      "event_type": "policy.created",
      "status": "delivered",
      "http_status": 200,
      "response_time_ms": 45,
      "attempts": 1,
      "delivered_at": "2026-10-01T14:30:05Z",
      "next_retry_at": null
    },
    {
      "delivery_id": "del-002",
      "subscription_id": "sub-001",
      "event_id": "evt-002",
      "event_type": "enforcement.decision_made",
      "status": "retrying",
      "http_status": 503,
      "response_time_ms": 2000,
      "attempts": 3,
      "delivered_at": null,
      "next_retry_at": "2026-10-01T14:35:00Z"
    }
  ]
}
```

### 10.3 Webhook Payload Format

All webhook deliveries use a consistent envelope format:

```json
{
  "webhook_id": "wh-001",
  "event_id": "evt-001",
  "event_type": "policy.created",
  "timestamp": "2026-10-01T14:30:00Z",
  "tenant_id": "org-acme",
  "data": {
    "policy_id": "pol-001",
    "policy_key": "AI-ETHICS-001",
    "name": "Data Access Control Policy",
    "status": "draft",
    "version": "1.0.0",
    "created_by": "user-001",
    "created_at": "2026-10-01T14:30:00Z"
  },
  "metadata": {
    "delivery_attempt": 1,
    "subscription_id": "sub-001"
  }
}
```

### 10.4 Webhook Signature Verification

Each webhook delivery includes a signature for authenticity verification:

**Headers:**
```
X-GRC-Signature: t=1696161600,v1=5257a869e7ecebeda32affa62cdca3fa51cad7e77a6
X-GRC-Event-ID: evt-001
X-GRC-Event-Type: policy.created
```

**Signature computation:**
```
timestamp = "1696161600"
payload = '{"webhook_id":"wh-001",...}'
signed_payload = timestamp + "." + payload
signature = HMAC-SHA256(secret, signed_payload)
```

**Verification (Python example):**
```python
import hmac
import hashlib

def verify_webhook(payload_body, signature_header, secret):
    timestamp, signature = signature_header.split(",")
    timestamp = timestamp.split("=")[1]
    signature = signature.split("=")[1]
    
    signed_payload = f"{timestamp}.{payload_body}"
    expected = hmac.new(
        secret.encode(),
        signed_payload.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected)
```

### 10.5 Webhook Delivery Retry Policy

| Attempt | Delay | Condition |
|---------|-------|-----------|
| 1 | Immediate | Initial delivery |
| 2 | 1 minute | First retry on failure |
| 3 | 5 minutes | Second retry |
| 4 | 30 minutes | Third retry |
| 5 | 2 hours | Fourth retry |
| 6 | 8 hours | Fifth retry (final) |

**Failure conditions triggering retry:**
- HTTP 5xx responses
- HTTP 429 (rate limited)
- Connection timeout (> 10 seconds)
- Connection refused
- DNS resolution failure

**Non-retryable failures:**
- HTTP 400 (bad request)
- HTTP 401 (unauthorized)
- HTTP 403 (forbidden)
- HTTP 404 (not found)

### 10.6 Webhook Security

| Control | Implementation |
|---------|---------------|
| **Authentication** | HMAC-SHA256 signature with shared secret |
| **Transport** | TLS 1.3 required for all webhook endpoints |
| **Replay protection** | Timestamp tolerance of 5 minutes |
| **Secret rotation** | Zero-downtime dual-secret period |
| **IP allowlisting** | Optional source IP restriction |
| **Payload encryption** | Optional AES-256-GCM for sensitive payloads |

---

## 11. Event Catalog

### 11.1 Policy Events

| Event Type | Description | Payload Fields |
|------------|-------------|----------------|
| `policy.created` | New policy created | `policy_id`, `policy_key`, `name`, `status`, `version`, `created_by` |
| `policy.updated` | Policy modified | `policy_id`, `policy_key`, `name`, `version`, `change_summary`, `updated_by` |
| `policy.status_changed` | Policy status transition | `policy_id`, `old_status`, `new_status`, `changed_by` |
| `policy.deleted` | Policy deleted | `policy_id`, `policy_key`, `deleted_by` |
| `policy.compiled` | Policy compiled to Rego | `policy_id`, `compilation_status`, `warnings` |
| `policy.activated` | Policy moved to active | `policy_id`, `version`, `effective_date` |
| `policy.deprecated` | Policy deprecated | `policy_id`, `deprecated_by`, `deprecation_reason` |

### 11.2 Evidence Events

| Event Type | Description | Payload Fields |
|------------|-------------|----------------|
| `evidence.collected` | New evidence submitted | `evidence_id`, `policy_id`, `evidence_type`, `source`, `verification_level` |
| `evidence.verified` | Evidence passed verification | `evidence_id`, `verification_level`, `hash_match`, `chain_intact` |
| `evidence.exported` | Evidence package exported | `package_id`, `framework`, `controls_assessed`, `evidence_items` |
| `evidence.expired` | Evidence retention expired | `evidence_id`, `retention_class`, `expired_at` |

### 11.3 Enforcement Events

| Event Type | Description | Payload Fields |
|------------|-------------|----------------|
| `enforcement.decision_made` | Enforcement decision returned | `decision_id`, `verdict`, `agent_id`, `policy_id`, `action`, `resource` |
| `enforcement.approval_required` | Decision requires human approval | `decision_id`, `agent_id`, `action`, `resource`, `ticket_id` |
| `enforcement.agent_quarantined` | Agent quarantined | `agent_id`, `reason`, `decision_id`, `quarantine_duration` |
| `enforcement.policy_violation` | Policy violation detected | `decision_id`, `agent_id`, `policy_id`, `violation_type` |

### 11.4 Assessment Events

| Event Type | Description | Payload Fields |
|------------|-------------|----------------|
| `assessment.created` | New assessment created | `assessment_id`, `title`, `assessment_type`, `target_id` |
| `assessment.started` | Assessment started | `assessment_id`, `started_at`, `lead_assessor` |
| `assessment.completed` | Assessment completed | `assessment_id`, `score`, `risk_level`, `completed_at` |
| `assessment.finding_added` | Finding added to assessment | `assessment_id`, `finding_id`, `severity`, `status` |
| `assessment.finding_resolved` | Finding resolved | `assessment_id`, `finding_id`, `resolved_by`, `resolved_at` |

### 11.5 Compliance Events

| Event Type | Description | Payload Fields |
|------------|-------------|----------------|
| `compliance.posture_changed` | Compliance posture changed | `framework`, `target_id`, `old_score`, `new_score`, `change` |
| `compliance.control_satisfied` | Control became compliant | `control_id`, `framework`, `target_id`, `coverage` |
| `compliance.control_violated` | Control became non-compliant | `control_id`, `framework`, `target_id`, `severity` |
| `compliance.report_generated` | Compliance report generated | `report_id`, `framework`, `format`, `generated_at` |
| `compliance.mapping_created` | New compliance mapping | `mapping_id`, `control_id`, `policy_id`, `coverage` |

### 11.6 Agent Events

| Event Type | Description | Payload Fields |
|------------|-------------|----------------|
| `agent.registered` | New agent registered | `agent_id`, `name`, `type`, `framework`, `risk_tier` |
| `agent.updated` | Agent updated | `agent_id`, `changed_fields`, `updated_by` |
| `agent.lifecycle_changed` | Agent lifecycle transition | `agent_id`, `old_stage`, `new_stage`, `changed_by` |
| `agent.trust_score_changed` | Trust score updated | `agent_id`, `old_score`, `new_score`, `reason` |
| `agent.suspended` | Agent suspended | `agent_id`, `reason`, `suspended_by`, `suspension_end` |
| `agent.terminated` | Agent terminated | `agent_id`, `terminated_by`, `termination_reason` |

### 11.7 Audit Events

| Event Type | Description | Payload Fields |
|------------|-------------|----------------|
| `audit.event_created` | New audit event | `event_id`, `event_type`, `actor`, `resource`, `timestamp` |
| `audit.chain_verified` | Audit chain verified | `from_event_id`, `to_event_id`, `events_verified`, `chain_intact` |

### 11.8 Real-Time Stream Events (Flink)

| Event Type | Description | Payload Fields |
|------------|-------------|----------------|
| `stream.compliance_score_updated` | Real-time compliance score from Flink | `framework_id`, `scope_id`, `old_score`, `new_score`, `window_type` |
| `stream.risk_signal_detected` | Risk pattern detected by CEP | `signal_type`, `agent_id`, `severity`, `pattern_matched` |
| `stream.evidence_verified` | Evidence verified in real-time | `evidence_id`, `verification_level`, `hash_match` |
| `stream.agent_behavior_anomaly` | Behavioral anomaly detected | `agent_id`, `anomaly_type`, `confidence`, `window` |
| `stream.audit_merkle_root` | New Merkle root computed | `root_hash`, `event_count`, `time_window` |

### 11.9 Saga Events

| Event Type | Description | Payload Fields |
|------------|-------------|----------------|
| `saga.started` | Saga execution started | `saga_id`, `saga_name`, `input` |
| `saga.step_completed` | Saga step completed | `saga_id`, `step_id`, `result` |
| `saga.step_failed` | Saga step failed | `saga_id`, `step_id`, `error` |
| `saga.compensating` | Saga compensation started | `saga_id`, `failed_step` |
| `saga.compensated` | Saga fully compensated | `saga_id`, `compensated_steps` |
| `saga.completed` | Saga completed successfully | `saga_id`, `duration_ms` |
| `saga.compensation_failed` | Saga compensation failed | `saga_id`, `step_id`, `error` |

---

## 12. SDK & Client Libraries

### 12.1 Official SDKs

| Language | Package | Installation |
|----------|---------|-------------|
| Python | `grc-claw-sdk` | `pip install grc-claw-sdk` |
| Go | `github.com/grc-claw/sdk-go` | `go get github.com/grc-claw/sdk-go` |
| TypeScript | `@grc-claw/sdk` | `npm install @grc-claw/sdk` |
| Java | `io.grccLaw:sdk-java` | Maven/Gradle dependency |
| Rust | `grc-claw-sdk` | `cargo add grc-claw-sdk` |

### 12.2 Python SDK Example

```python
from grc_claw import GRCClawClient

# Initialize client
client = GRCClawClient(
    api_key="grc_live_abc123...",
    tenant_id="org-acme",
    environment="production"
)

# Policy management
policy = client.policies.create(
    policy_key="AI-ETHICS-001",
    name="Data Access Control Policy",
    category="privacy",
    cedar_policy='permit(principal, action, resource) when { ... }',
    framework_tags=["SOC2", "ISO-27001"]
)

# Compile and dry-run
compilation = client.policies.compile(policy.id)
dry_run = client.policies.dry_run(policy.id, test_inputs=[
    {"principal": {"id": "agent-42"}, "action": "read", "resource": {"classification": 2}}
])

# Enforcement decision
decision = client.enforcement.decide(
    agent_id="agent-42",
    action="read",
    resource="s3://data/public/dataset.csv",
    context={"environment": "production"}
)

if decision.verdict == "ALLOW":
    print("Action allowed")
elif decision.verdict == "DENY":
    print(f"Action denied: {decision.reason}")

# Evidence submission
evidence = client.evidence.submit(
    policy_id=policy.id,
    evidence_type="config",
    content={"format": "json", "data": '{"encryption": "AES-256"}'},
    control_mapping={"control_id": "AC-2", "framework": "NIST-800-53"}
)

# Compliance posture
posture = client.compliance.get_posture(
    framework="NIST-800-53",
    target_id="all-production",
    target_type="organization"
)
print(f"Compliance score: {posture.compliance_score}%")

# Webhook subscription
subscription = client.webhooks.create(
    url="https://example.com/webhooks/grc-claw",
    events=["policy.created", "enforcement.decision_made"],
    secret="whsec_abc123..."
)
```

### 12.3 Go SDK Example

```go
package main

import (
    "context"
    "log"

    "github.com/grc-claw/sdk-go"
)

func main() {
    client := grcclaw.NewClient(
        grcclaw.WithAPIKey("grc_live_abc123..."),
        grcclaw.WithTenantID("org-acme"),
        grcclaw.WithEnvironment("production"),
    )

    // Create policy
    policy, err := client.Policies.Create(context.Background(), &grcclaw.PolicyInput{
        PolicyKey:     "AI-ETHICS-001",
        Name:          "Data Access Control Policy",
        Category:      "privacy",
        CedarPolicy:   `permit(principal, action, resource) when { ... }`,
        FrameworkTags: []string{"SOC2", "ISO-27001"},
    })
    if err != nil {
        log.Fatal(err)
    }

    // Request enforcement decision
    decision, err := client.Enforcement.Decide(context.Background(), &grcclaw.DecideInput{
        AgentID:  "agent-42",
        Action:   "read",
        Resource: "s3://data/public/dataset.csv",
        Context:  map[string]interface{}{"environment": "production"},
    })
    if err != nil {
        log.Fatal(err)
    }

    log.Printf("Verdict: %s, Time: %fms", decision.Verdict, decision.EvaluationTimeMs)
}
```

---

## 13. API Authentication & Authorization

### 13.1 Authentication Methods

GRC_Claw supports four authentication methods, each suited to different client types and trust levels:

| Method | Client Type | Token Format | Rotation | Use Case |
|--------|-------------|-------------|----------|----------|
| **OAuth 2.1 / OIDC** | User-facing apps, dashboards | JWT (RS256) | 1 hour access, 30-day refresh | Browser-based admin UI, CLI tools |
| **API Keys** | Service-to-service, CI/CD | `grc_live_...` / `grc_test_...` | 90 days | Automated pipelines, backend integrations |
| **mTLS (SPIFFE)** | Agent-to-PEP, service mesh | X.509 SVID | 24 hours (auto-renewed) | Agent enforcement, internal services |
| **Webhook Signatures** | Webhook delivery verification | HMAC-SHA256 | Per-subscription secret | Event-driven integrations |

### 13.2 OAuth 2.1 / OIDC

**Authorization Server:** `https://auth.grc-claw.io`

**Token Endpoint:** `POST /oauth/token`

**Supported Grant Types:**

| Grant Type | Flow | PKCE | Use Case |
|------------|------|------|----------|
| `authorization_code` | Browser redirect | Required | User authentication via browser |
| `client_credentials` | Direct token exchange | N/A | Service-to-service authentication |
| `refresh_token` | Token refresh | N/A | Obtain new access token |
| `urn:ietf:params:oauth:grant-type:token-exchange` | Token exchange | N/A | Cross-service delegation |

**Token Response:**
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "refresh_token": "def50200...",
  "scope": "policies:read policies:write evidence:read enforcement:decide",
  "issued_token_type": "urn:ietf:params:oauth:token-type:access_token"
}
```

**Token Claims:**
```json
{
  "iss": "https://auth.grc-claw.io",
  "sub": "user-001",
  "aud": "https://api.grc-claw.io",
  "exp": 1696165200,
  "iat": 1696161600,
  "scope": "policies:read policies:write evidence:read enforcement:decide",
  "tenant_id": "org-acme",
  "roles": ["operator"],
  "mfa_verified": true,
  "auth_time": 1696161500
}
```

**Token Revocation:** `POST /oauth/revoke`

**Supported Algorithms:** RS256 (default), ES256, EdDSA

**Discovery Endpoint:** `https://auth.grc-claw.io/.well-known/openid-configuration`

### 13.3 API Key Authentication

API keys are passed via the `Authorization` header:

```
Authorization: Bearer grc_live_abc123def456...
```

**Key Prefixes:**
- `grc_live_` — Production environment
- `grc_test_` — Test environment

**Key Scopes:**

| Scope | Permissions |
|-------|-------------|
| `policies:read` | Read policies |
| `policies:write` | Create, update, delete policies |
| `evidence:read` | Read evidence |
| `evidence:write` | Submit evidence |
| `enforcement:decide` | Request enforcement decisions |
| `assessments:read` | Read assessments |
| `assessments:write` | Create, update assessments |
| `compliance:read` | Read compliance data |
| `compliance:write` | Create compliance mappings |
| `agents:read` | Read agent registry |
| `agents:write` | Register, update agents |
| `audit:read` | Read audit trail |
| `webhooks:manage` | Manage webhook subscriptions |

**Key Management:**
- Keys are created via `POST /v1.0/api-keys` (admin only)
- Keys can be scoped to specific tenants, IP ranges, and endpoint groups
- Keys support expiration dates and automatic rotation
- Key usage is logged to the audit trail

### 13.4 mTLS (SPIFFE) Authentication

Agents authenticate to the PEP using SPIFFE Verifiable Identity Documents (SVIDs):

```
Agent → PEP: mTLS handshake with X.509 SVID
PEP validates: SPIFFE ID, certificate chain, expiry
PEP queries: Agent Registry for capabilities and trust score
```

**SPIFFE ID Format:**
```
spiffe://grc-claw.io/ns/{namespace}/sa/{agent_id}
```

Example: `spiffe://grc-claw.io/ns/prod/sa/agent-42`

**SVID Fields:**
```json
{
  "spiffe_id": "spiffe://grc-claw.io/ns/prod/sa/agent-42",
  "private_key": "ecdsa-p256",
  "x509_svid": "-----BEGIN CERTIFICATE-----\n...",
  "x509_svid_key": "-----BEGIN EC PRIVATE KEY-----\n...",
  "bundle": "-----BEGIN CERTIFICATE-----\n...",
  "hint": "grc-claw-agent"
}
```

### 13.5 Authorization Model

GRC_Claw uses **RBAC + ABAC** hybrid authorization:

**Roles:**

| Role | Description | Permissions |
|------|-------------|-------------|
| `admin` | Full system access | All permissions |
| `assessor` | Conduct assessments | assessments:read, assessments:write, evidence:read |
| `auditor` | Read-only audit access | audit:read, evidence:read, compliance:read |
| `operator` | Day-to-day operations | policies:read, evidence:read, evidence:write, enforcement:decide |
| `viewer` | Read-only dashboard | policies:read, evidence:read, compliance:read |

**ABAC Attributes:**
- `tenant_id` — Organization isolation
- `resource.owner_id` — Resource ownership
- `resource.classification` — Data classification level
- `agent.risk_tier` — Agent risk classification

### 13.6 Permission Matrix

| Resource | admin | assessor | auditor | operator | viewer |
|----------|-------|----------|---------|----------|--------|
| Policy CRUD | ✅ | ❌ | ❌ | ❌ | ❌ |
| Policy Read | ✅ | ✅ | ✅ | ✅ | ✅ |
| Evidence Submit | ✅ | ✅ | ❌ | ✅ | ❌ |
| Evidence Read | ✅ | ✅ | ✅ | ✅ | ✅ |
| Enforcement Decide | ✅ | ❌ | ❌ | ✅ | ❌ |
| Assessment CRUD | ✅ | ✅ | ❌ | ❌ | ❌ |
| Assessment Read | ✅ | ✅ | ✅ | ✅ | ✅ |
| Compliance Write | ✅ | ❌ | ❌ | ❌ | ❌ |
| Compliance Read | ✅ | ✅ | ✅ | ✅ | ✅ |
| Agent CRUD | ✅ | ❌ | ❌ | ❌ | ❌ |
| Agent Read | ✅ | ✅ | ✅ | ✅ | ✅ |
| Audit Read | ✅ | ✅ | ✅ | ❌ | ❌ |
| Webhook Manage | ✅ | ❌ | ❌ | ❌ | ❌ |

### 13.7 Token Validation Flow

```
Client Request → API Gateway → Authentication Filter → Token Validation
                                                    ↓
                                            ┌───────┴───────┐
                                            │               │
                                        JWT Valid      JWT Invalid
                                            │               │
                                    Extract Claims    Return 401
                                            │
                                    Check Expiry
                                            │
                                    Check Scope
                                            │
                                    Check Tenant
                                            │
                                    Enrich Context
                                            │
                                    Route to Service
```

### 13.8 Multi-Tenant Isolation

All API requests are tenant-scoped. Tenant isolation is enforced at multiple layers:

| Layer | Mechanism | Enforcement |
|-------|-----------|-------------|
| API Gateway | JWT `tenant_id` claim | Reject if missing or invalid |
| Service Layer | Request context tenant_id | Filter all queries by tenant |
| Database | Row-Level Security (RLS) | PostgreSQL RLS policies |
| Evidence Store | Tenant-scoped collections | MongoDB collection per tenant |
| Audit Trail | Tenant-scoped event log | Separate audit chain per tenant |

### 13.9 Session Management

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Access token lifetime | 1 hour | Balance security vs. usability |
| Refresh token lifetime | 30 days | Extended session for trusted clients |
| Idle timeout | 15 minutes | Auto-logout for inactive sessions |
| Max concurrent sessions | 5 per user | Prevent session abuse |
| MFA required | Admin roles only | Protect privileged access |
| Session binding | IP + User-Agent | Prevent token theft reuse |

---

## 14. API Rate Limiting & Throttling

### 14.1 Rate Limit Headers

All API responses include rate limit headers:

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1696161600
X-RateLimit-Policy: token_bucket
```

### 14.2 Rate Limit Tiers

| Tier | Requests/Second | Requests/Day | Burst | Use Case |
|------|----------------|-------------|-------|----------|
| **Free** | 10 | 10,000 | 20 | Evaluation, development |
| **Standard** | 100 | 1,000,000 | 200 | Production workloads |
| **Enterprise** | 1,000 | 10,000,000 | 2,000 | Large-scale deployments |
| **Unlimited** | Custom | Custom | Custom | Negotiated SLA |

### 14.3 Endpoint-Specific Limits

| Endpoint Category | Rate Limit | Rationale |
|-------------------|-----------|-----------|
| `POST /v1.0/enforcement/decide` | 10,000/sec | High-frequency agent actions |
| `POST /v1.0/enforcement/decide-batch` | 1,000/sec | Batch operations |
| `GET /v1.0/policies` | 1,000/sec | Standard read |
| `POST /v1.0/policies` | 100/sec | Write operations |
| `POST /v1.0/evidence` | 5,000/sec | Evidence ingestion |
| `GET /v1.0/audit` | 500/sec | Audit queries |
| `POST /v1.0/compliance/reports` | 10/sec | Expensive report generation |
| `POST /v1.0/graphql` | 1,000/sec | GraphQL queries |

### 14.4 Rate Limit Response

When rate limit is exceeded:

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Try again in 30 seconds.",
    "details": {
      "limit": 1000,
      "remaining": 0,
      "reset_at": "2026-10-01T14:31:00Z",
      "retry_after_seconds": 30
    }
  }
}
```

**HTTP Status:** `429 Too Many Requests`

### 14.5 Quota Management

Quotas are tracked per `tenant_id` and per `api_key`:

| Quota Type | Measurement | Enforcement |
|------------|-------------|-------------|
| **Storage** | Evidence bytes stored | Hard limit — reject new evidence |
| **API Calls** | Requests per day | Hard limit — reject with 429 |
| **Compute** | Report generation time | Soft limit — queue for later |
| **Concurrent** | Active WebSocket connections | Hard limit — reject new connections |

### 14.6 Rate Limiting Algorithms

GRC_Claw uses multiple rate limiting algorithms depending on the use case:

| Algorithm | Use Case | Behavior |
|-----------|----------|----------|
| **Token Bucket** | General API requests | Smooth burst handling, refills at constant rate |
| **Sliding Window** | Accurate per-minute limits | Prevents burst at window boundaries |
| **Leaky Bucket** | Queue-based processing | Smooths traffic to constant rate |
| **Fixed Window** | Simple per-period limits | Resets at period boundary |

### 14.7 Rate Limit Configuration

Rate limits are configurable per tenant, API key, and endpoint:

```yaml
# Rate limit configuration
rate_limits:
  default:
    algorithm: token_bucket
    requests_per_second: 100
    burst_size: 200
  
  endpoints:
    /v1.0/enforcement/decide:
      requests_per_second: 10000
      burst_size: 2000
    
    /v1.0/compliance/reports:
      requests_per_second: 10
      burst_size: 20
  
  tiers:
    free:
      requests_per_second: 10
      daily_limit: 10000
    standard:
      requests_per_second: 100
      daily_limit: 1000000
    enterprise:
      requests_per_second: 1000
      daily_limit: 10000000
```

### 14.8 Rate Limit Bypass

Rate limits can be bypassed only for:

| Scenario | Mechanism | Approval |
|----------|-----------|----------|
| Emergency enforcement | Dedicated internal service account | CISO approval |
| System maintenance | Maintenance window with IP allowlist | SRE approval |
| Disaster recovery | Fail-open mode for enforcement | Automatic |

### 14.9 Throttling Strategies

| Strategy | Description | Use Case |
|----------|-------------|----------|
| **Request queuing** | Queue requests when limit reached | Non-urgent operations |
| **Graceful degradation** | Reduce response complexity under load | Dashboard queries |
| **Circuit breaker** | Fail fast when downstream is overloaded | External service calls |
| **Load shedding** | Drop non-critical requests under extreme load | System protection |

---

## 15. API Versioning & Deprecation

### 15.1 URL Path Versioning

All API endpoints include the version in the URL path:

```
https://api.grc-claw.io/v1.0/policies
```

**Current version:** `v1.0`

### 15.2 Version Lifecycle

| Stage | Description | Duration |
|-------|-------------|----------|
| **Alpha** | Internal testing, breaking changes allowed | 3 months |
| **Beta** | Public testing, minor breaking changes | 3 months |
| **GA** | Stable, no breaking changes | 12+ months |
| **Deprecated** | Announced deprecation, still functional | 6 months |
| **Sunset** | End of life, no longer available | — |

### 15.3 Backward Compatibility

- **Minor versions** (v1.1, v1.2) — Additive changes only, fully backward compatible
- **Major versions** (v2.0) — Breaking changes, migration guide provided
- **Deprecation notices** — Sent via webhook `api.version_deprecated` 6 months before sunset

### 15.4 Version Negotiation

Clients can request a specific version via header:

```
Accept: application/vnd.grc-claw.v1.0+json
```

Or via URL path:

```
GET /v1.0/policies
```

### 15.5 Breaking Change Policy

| Change Type | Example | Compatibility |
|-------------|---------|--------------|
| Adding optional fields | New field in response | ✅ Backward compatible |
| Adding new endpoints | New `POST /v1.0/audit/verify` | ✅ Backward compatible |
| Adding new enum value | New `PolicyStatus` value | ✅ Backward compatible |
| Removing fields | Remove field from response | ❌ Breaking change |
| Changing field types | `string` → `integer` | ❌ Breaking change |
| Renaming fields | `policy_key` → `policyKey` | ❌ Breaking change |
| Changing error codes | `404` → `410` | ❌ Breaking change |

### 15.6 Deprecation Timeline

| Phase | Timeframe | Action |
|-------|-----------|--------|
| **Announcement** | 6 months before sunset | Deprecation notice via webhook and email |
| **Documentation** | 6 months before sunset | Mark deprecated in OpenAPI spec |
| **Migration guide** | 6 months before sunset | Publish migration guide |
| **Sunset** | 0 | Return `410 Gone` with migration info |
| **Removal** | After sunset | Endpoint removed |

### 15.7 Deprecation Headers

Deprecated endpoints return additional headers:

```
Deprecation: true
Sunset: Sat, 01 Apr 2027 00:00:00 GMT
Link: <https://api.grc-claw.io/v2.0/policies>; rel="successor-version"
```

### 15.8 Version Sunset Response

When a version is sunset:

```json
{
  "error": {
    "code": "API_VERSION_SUNSET",
    "message": "API version v1.0 has been sunset. Please migrate to v2.0.",
    "details": {
      "sunset_date": "2027-04-01T00:00:00Z",
      "migration_guide": "https://docs.grc-claw.io/migration/v1-to-v2",
      "successor_version": "v2.0"
    }
  }
}
```

**HTTP Status:** `410 Gone`

---

## 16. API Monitoring & Analytics

### 16.1 Monitoring Architecture

GRC_Claw API monitoring follows a three-layer approach:

```
┌─────────────────────────────────────────────────────────────┐
│                    API MONITORING STACK                       │
│                                                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ Metrics  │  │ Logging  │  │ Tracing  │  │ Alerting │  │
│  │(Prometheus│  │(Structured│  │(OpenTelemetry│ │(PagerDuty│ │
│  │ + Grafana)│  │  JSON)   │  │  + Jaeger) │  │ + Slack) │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  │
│       │              │              │              │         │
│       └──────────────┴──────────────┴──────────────┘         │
│                              │                                │
│                              ▼                                │
│                    ┌──────────────────┐                      │
│                    │  Correlation &   │                      │
│                    │  Analysis        │                      │
│                    │  (Elasticsearch) │                      │
│                    └──────────────────┘                      │
└─────────────────────────────────────────────────────────────┘
```

### 16.2 Metrics

#### 16.2.1 Prometheus Metrics

All API endpoints expose Prometheus-formatted metrics at `/metrics`:

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `grc_api_requests_total` | Counter | `method`, `endpoint`, `status`, `tenant` | Total API requests |
| `grc_api_request_duration_seconds` | Histogram | `method`, `endpoint`, `tenant` | Request latency |
| `grc_api_request_size_bytes` | Histogram | `method`, `endpoint` | Request body size |
| `grc_api_response_size_bytes` | Histogram | `method`, `endpoint` | Response body size |
| `grc_api_active_requests` | Gauge | `endpoint` | Currently active requests |
| `grc_api_rate_limit_hits_total` | Counter | `tenant`, `endpoint` | Rate limit rejections |
| `grc_api_errors_total` | Counter | `method`, `endpoint`, `error_code` | Total errors |
| `grc_api_enforcement_decisions_total` | Counter | `verdict`, `policy_id` | Enforcement decisions |
| `grc_api_evidence_ingested_bytes` | Counter | `tenant`, `evidence_type` | Evidence ingestion volume |
| `grc_api_webhook_deliveries_total` | Counter | `status`, `subscription_id` | Webhook delivery attempts |

#### 16.2.2 Custom Metrics

```promql
# Request rate by endpoint
rate(grc_api_requests_total[5m])

# Error rate
rate(grc_api_errors_total[5m]) / rate(grc_api_requests_total[5m])

# P99 latency
histogram_quantile(0.99, rate(grc_api_request_duration_seconds_bucket[5m]))

# Active connections
grc_api_active_requests

# Rate limit hit rate
rate(grc_api_rate_limit_hits_total[5m])
```

### 16.3 Logging

#### 16.3.1 Structured Log Format

All API requests produce structured JSON logs:

```json
{
  "timestamp": "2026-10-01T14:30:00.123Z",
  "level": "info",
  "request_id": "req-abc123",
  "trace_id": "trace-def456",
  "span_id": "span-789",
  "method": "POST",
  "path": "/v1.0/policies",
  "status": 201,
  "duration_ms": 45,
  "tenant_id": "org-acme",
  "user_id": "user-001",
  "api_key_id": "key-001",
  "ip_address": "192.168.1.1",
  "user_agent": "grc-claw-sdk/1.0.0",
  "request_size": 1024,
  "response_size": 2048,
  "rate_limit_remaining": 999
}
```

#### 16.3.2 Log Levels

| Level | Usage | Retention |
|-------|-------|-----------|
| `DEBUG` | Detailed request/response (dev only) | 7 days |
| `INFO` | Standard request logging | 90 days |
| `WARN` | Rate limit warnings, deprecated API usage | 90 days |
| `ERROR` | Request failures, server errors | 1 year |
| `AUDIT` | Security-relevant events | 7 years |

### 16.4 Distributed Tracing

GRC_Claw uses OpenTelemetry for distributed tracing:

```
Client → API Gateway → Service A → Service B → Database
           │              │           │
           └──────────────┴───────────┘
                    Trace Context
```

**Trace Context Headers:**
```
traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01
tracestate: grc-claw=tenant:org-acme
```

**Span Attributes:**
- `http.method`, `http.url`, `http.status_code`
- `grc.tenant_id`, `grc.user_id`, `grc.api_key_id`
- `grc.policy_id`, `grc.agent_id`, `grc.decision_id`
- `db.system`, `db.operation`, `db.statement`

### 16.5 Analytics Dashboard

#### 16.5.1 Real-Time Dashboard

| Metric | Display | Alert Threshold |
|--------|---------|-----------------|
| Requests/second | Time series | > 10,000/sec |
| Error rate | Percentage | > 5% |
| P99 latency | Time series | > 500ms |
| Active connections | Gauge | > 10,000 |
| Rate limit hits | Counter | > 100/min |
| Enforcement decisions | Counter by verdict | > 20% deny |
| Evidence ingestion | Bytes/sec | > 1GB/sec |
| Webhook delivery success | Percentage | < 95% |

#### 16.5.2 Usage Analytics

| Metric | Description | Aggregation |
|--------|-------------|-------------|
| API calls by endpoint | Request count per endpoint | Hourly/Daily |
| API calls by tenant | Request count per tenant | Hourly/Daily |
| API calls by API key | Request count per key | Hourly/Daily |
| Data transfer | Bytes sent/received | Hourly/Daily |
| Top consumers | Tenants by request volume | Daily |
| Error distribution | Errors by type and endpoint | Hourly |
| Latency distribution | P50, P90, P99, P99.9 | Hourly |

### 16.6 Health & Readiness

#### 16.6.1 Health Check

```
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "components": {
    "api": {"status": "up"},
    "policy_engine": {"status": "up"},
    "evidence_store": {"status": "up"},
    "database": {"status": "up"},
    "cache": {"status": "up"}
  },
  "timestamp": "2026-10-01T14:30:00Z"
}
```

#### 16.6.2 Readiness Check

```
GET /ready
```

**Response:**
```json
{
  "ready": true,
  "checks": {
    "database": {"status": "pass"},
    "policy_engine": {"status": "pass"},
    "evidence_store": {"status": "pass"}
  }
}
```

### 16.7 Alerting

#### 16.7.1 Alert Rules

| Rule | Condition | Severity | Action |
|------|-----------|----------|--------|
| High error rate | Error rate > 5% for 5 min | P2 | Page on-call |
| High latency | P99 > 500ms for 5 min | P3 | Slack notification |
| Rate limit spike | > 1000 rate limit hits/min | P3 | Slack notification |
| Service down | Health check fails | P1 | Page on-call |
| Disk usage | > 80% disk usage | P2 | Page on-call |
| Certificate expiry | < 30 days to expiry | P3 | Slack notification |
| Webhook delivery failure | < 90% success rate | P3 | Slack notification |

#### 16.7.2 Alert Routing

| Alert Type | Primary | Secondary | Tertiary |
|------------|---------|-----------|----------|
| Service down | PagerDuty | Slack #sre | Email |
| High error rate | PagerDuty | Slack #engineering | Email |
| Security event | PagerDuty | Slack #security | Email |
| Rate limit spike | Slack #engineering | Email | — |
| Certificate expiry | Slack #sre | Email | — |

---

## 17. API Documentation Automation

### 17.1 Documentation Strategy

GRC_Claw uses a **docs-as-code** approach where API documentation is automatically generated from source code and OpenAPI specifications, ensuring documentation is always in sync with the implementation.

### 17.2 OpenAPI Specification

The complete API is documented using OpenAPI 3.1:

**Specification URL:** `https://api.grc-claw.io/v1.0/openapi.json`

**Documentation URL:** `https://docs.grc-claw.io`

### 17.3 Documentation Generation Pipeline

```
Source Code → OpenAPI Generator → Documentation Site → CDN
     ↓              ↓                    ↓
  Annotations   Schema Validation    Versioning
  Type Hints   Example Generation    Search Index
  Docstrings   SDK Generation        Changelog
```

### 17.4 Automated Documentation Components

| Component | Source | Tool | Output |
|-----------|--------|------|--------|
| REST API reference | OpenAPI spec | Redoc / Swagger UI | Interactive API docs |
| GraphQL schema | GraphQL schema | GraphQL Voyager | Visual schema explorer |
| gRPC interface | Proto files | Buf / protoc | Proto reference |
| SDK docs | Source code | Sphinx / TypeDoc / rustdoc | SDK reference |
| Changelog | Git commits | Conventional Changelog | Release notes |
| Examples | Test fixtures | Custom generator | Code samples |

### 17.5 OpenAPI Specification Structure

```yaml
openapi: 3.1.0
info:
  title: GRC_Claw API
  version: 1.0.0
  description: |
    GRC_Claw API for governance, risk, and compliance management.
  contact:
    name: GRC_Claw Team
    email: api@grc-claw.io
  license:
    name: Apache 2.0
servers:
  - url: https://api.grc-claw.io/v1.0
    description: Production
  - url: https://staging-api.grc-claw.io/v1.0
    description: Staging
tags:
  - name: Policies
    description: Policy lifecycle management
  - name: Evidence
    description: Evidence collection and verification
  - name: Enforcement
    description: Enforcement decisions
  - name: Assessments
    description: Assessment management
  - name: Compliance
    description: Compliance mapping and reporting
  - name: Agents
    description: Agent registry and identity
  - name: Audit
    description: Audit trail
  - name: Webhooks
    description: Webhook subscriptions
paths:
  /policies:
    get:
      operationId: listPolicies
      summary: List policies
      description: Returns a paginated list of policies
      tags: [Policies]
      parameters:
        - name: status
          in: query
          schema:
            type: string
            enum: [draft, review, active, deprecated, archived]
      responses:
        '200':
          description: Successful response
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PolicyList'
              example:
                data:
                  - id: pol-001
                    policy_key: AI-ETHICS-001
                    name: Data Access Control Policy
                    status: active
components:
  schemas:
    Policy:
      type: object
      required: [id, policy_key, name, status]
      properties:
        id:
          type: string
          format: uuid
        policy_key:
          type: string
          pattern: '^[A-Z0-9-]+$'
        name:
          type: string
          maxLength: 255
        status:
          type: string
          enum: [draft, review, active, deprecated, archived]
```

### 17.6 Documentation Versioning

| Version | URL | Status |
|---------|-----|--------|
| v1.0 (current) | `https://docs.grc-claw.io/v1.0` | ✅ Active |
| v1.1 (beta) | `https://docs.grc-claw.io/v1.1` | 🧪 Beta |
| v2.0 (alpha) | `https://docs.grc-claw.io/v2.0` | 🔬 Alpha |

### 17.7 SDK Documentation

SDK documentation is auto-generated from source code type hints and docstrings:

| Language | Tool | Output |
|----------|------|--------|
| Python | Sphinx + autodoc | `https://docs.grc-claw.io/sdk/python` |
| TypeScript | TypeDoc | `https://docs.grc-claw.io/sdk/typescript` |
| Go | pkg.go.dev | `https://pkg.go.dev/github.com/grc-claw/sdk-go` |
| Rust | rustdoc | `https://docs.rs/grc-claw-sdk` |
| Java | Javadoc | `https://docs.grc-claw.io/sdk/java` |

### 17.8 Documentation Quality Gates

| Gate | Criteria | Blocking |
|------|----------|----------|
| OpenAPI validation | Spec validates against OpenAPI 3.1 schema | Yes |
| Endpoint coverage | All endpoints documented | Yes |
| Example coverage | All endpoints have request/response examples | Yes |
| SDK coverage | All public SDK methods documented | Yes |
| Changelog | All changes documented | Yes |
| Broken links | No broken internal/external links | Yes |

---

## 18. API Testing & Quality Assurance

### 18.1 Testing Strategy

GRC_Claw employs a comprehensive API testing strategy across multiple layers:

```
┌─────────────────────────────────────────────────────────────────┐
│                    API TESTING PYRAMID                            │
│                                                                   │
│                        ┌─────────┐                                │
│                        │  E2E    │  Full workflow tests           │
│                        │  (Daily)│  Multi-service integration     │
│                       ┌┴─────────┴┐                               │
│                       │  Contract │  Consumer-driven contracts    │
│                       │  (Per PR) │  Pact / Schemathesis          │
│                      ┌┴───────────┴┐                              │
│                      │  Integration│  Service-level tests         │
│                      │  (Per PR)   │  API + Database + Cache      │
│                     ┌┴─────────────┴┐                             │
│                     │  Unit         │  Component-level tests      │
│                     │  (Per commit) │  Mocked dependencies        │
│                    ┌┴───────────────┴┐                            │
│                    │  Static        │  OpenAPI validation        │
│                    │  (Per commit) │  Linting, schema checks     │
│                   ┌┴─────────────────┴┐                           │
│                   │  Pre-commit       │  Secret detection         │
│                   │  (Per commit)     │  Basic linting            │
│                   └────────────────────┘                           │
└─────────────────────────────────────────────────────────────────┘
```

### 18.2 Test Types

#### 18.2.1 Unit Tests

| Component | Test Focus | Framework | Coverage Target |
|-----------|------------|-----------|-----------------|
| Authentication | Token validation, scope checking | pytest | 95% |
| Authorization | RBAC/ABAC evaluation, tenant isolation | pytest | 95% |
| Rate Limiting | Algorithm correctness, edge cases | pytest | 90% |
| Validation | Input schema validation, boundary values | pytest | 90% |
| Error Handling | Error response format, status codes | pytest | 90% |

#### 18.2.2 Integration Tests

| Component | Test Focus | Dependencies | Framework |
|-----------|------------|--------------|-----------|
| REST API | End-to-end request/response | Test DB, Mock services | pytest + httpx |
| GraphQL | Query/mutation execution | Test DB, Mock services | pytest + strawberry |
| gRPC | Service communication | Test DB, Mock services | pytest + grpcio |
| Webhooks | Delivery, retry, signature | Mock HTTP server | pytest + respx |
| Enforcement | Decision pipeline | Test policy engine | pytest |

#### 18.2.3 Contract Tests

| Consumer | Provider | Tool | Focus |
|----------|----------|------|-------|
| Web UI | REST API | Pact | API shape compatibility |
| SDK | REST API | Pact | SDK method coverage |
| Agent Framework | gRPC | grpcio | Proto compatibility |
| Webhook Consumer | Webhook API | Custom | Payload format |

#### 18.2.4 End-to-End Tests

| Scenario | Steps | Expected Result |
|----------|-------|-----------------|
| Policy lifecycle | Create → Compile → Dry-run → Activate → Deprecate | All transitions succeed |
| Evidence collection | Submit → Verify → Export | Evidence package generated |
| Enforcement flow | Register agent → Bind policy → Request decision | Correct verdict returned |
| Compliance mapping | Create mapping → Generate report | Report reflects mapping |
| Webhook delivery | Create subscription → Trigger event → Verify delivery | Event delivered with valid signature |

### 18.3 Test Data Management

| Strategy | Description | Use Case |
|----------|-------------|----------|
| **Factory pattern** | Programmatic test data creation | Unit and integration tests |
| **Fixtures** | Pre-defined test data sets | Integration and E2E tests |
| **Snapshots** | Recorded API responses | Contract tests |
| **Fuzzing** | Random/malformed input generation | Security testing |
| **Seeding** | Database seed scripts | Integration test setup |

### 18.4 Test Environments

| Environment | Purpose | Data | Access |
|-------------|---------|------|--------|
| **Local** | Development | In-memory / SQLite | Developer machine |
| **CI** | Automated testing | Ephemeral containers | CI pipeline |
| **Staging** | Pre-production validation | Anonymized production data | Internal team |
| **Production** | Smoke tests | Production data | Automated only |

### 18.5 API Quality Gates

| Gate | Criteria | Blocking |
|------|----------|----------|
| OpenAPI validation | Spec validates against OpenAPI 3.1 schema | Yes |
| Schema validation | All requests/responses match schema | Yes |
| Authentication | All endpoints require valid authentication | Yes |
| Authorization | All endpoints enforce proper authorization | Yes |
| Rate limiting | Rate limits enforced on all endpoints | Yes |
| Error handling | All errors return RFC 7807 format | Yes |
| Idempotency | Write operations support idempotency keys | Yes |
| Pagination | All list endpoints support cursor pagination | Yes |
| Deprecation | Deprecated endpoints return proper headers | Yes |
| Documentation | All endpoints documented with examples | Yes |

### 18.6 Performance Testing

#### 18.6.1 Load Testing

| Scenario | Target | Tool |
|----------|--------|------|
| Sustained load | 10,000 RPS for 1 hour | k6 / Locust |
| Spike test | 0 → 50,000 RPS in 1 minute | k6 |
| Soak test | 5,000 RPS for 24 hours | k6 |
| Stress test | Until failure | k6 |

#### 18.6.2 Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| P50 latency | < 50ms | REST API |
| P99 latency | < 200ms | REST API |
| P99.9 latency | < 500ms | REST API |
| Throughput | 10,000 RPS | Per instance |
| Error rate | < 0.1% | Under normal load |
| Availability | 99.99% | Monthly |

### 18.7 Security Testing

#### 18.7.1 API Security Tests

| Test | Description | Tool |
|------|-------------|------|
| Authentication bypass | Attempt access without valid credentials | Custom scripts |
| Authorization bypass | Attempt access to unauthorized resources | Custom scripts |
| Injection testing | SQL, NoSQL, Command, LDAP injection | OWASP ZAP |
| XSS testing | Reflected, stored, DOM-based XSS | OWASP ZAP |
| SSRF testing | Server-side request forgery | Custom scripts |
| Rate limiting bypass | Attempt to bypass rate limits | Custom scripts |
| Input validation | Malformed input handling | Fuzzing |
| Token security | JWT validation, expiration, scope | Custom scripts |

#### 18.7.2 Security Test Automation

```yaml
# Security test pipeline
security_tests:
  - name: OWASP ZAP Scan
    run: zap-baseline.py -t https://staging-api.grc-claw.io
    schedule: nightly
    
  - name: API Fuzzing
    run: schemathesis run https://staging-api.grc-claw.io/openapi.json
    schedule: per PR
    
  - name: Secret Detection
    run: gitleaks detect --source .
    schedule: per commit
    
  - name: Dependency Scan
    run: trivy fs --scanners vuln .
    schedule: per PR
```

### 18.8 Test Automation Framework

#### 18.8.1 Test Configuration

```yaml
# test-config.yaml
environments:
  local:
    base_url: http://localhost:8080
    api_key: grc_test_local
  ci:
    base_url: http://test-api:8080
    api_key: grc_test_ci
  staging:
    base_url: https://staging-api.grc-claw.io
    api_key: grc_test_staging

test_data:
  policies:
    - policy_key: TEST-POLICY-001
      name: Test Policy
      category: safety
  agents:
    - name: Test Agent
      type: agent
      risk_tier: limited

timeouts:
  default: 30s
  enforcement: 100ms
  report_generation: 60s
```

#### 18.8.2 Test Execution

```bash
# Run all tests
pytest tests/ -v

# Run specific test category
pytest tests/unit/ -v
pytest tests/integration/ -v
pytest tests/e2e/ -v

# Run with coverage
pytest tests/ --cov=grc_claw --cov-report=html

# Run security tests
pytest tests/security/ -v

# Run performance tests
k6 run tests/performance/load_test.js
```

### 18.9 Continuous Integration

#### 18.9.1 CI Pipeline

```
Commit → Lint → Unit Tests → SAST → Build → Integration Tests → DAST → Deploy
  │        │         │          │       │           │            │        │
  │        │         │          │       │           │            │        │
  │        │         │          │       │           │            │        │
  ▼        ▼         ▼          ▼       ▼           ▼            ▼        ▼
Pre-commit  Pytest   Semgrep   Docker  Pytest      ZAP Scan    Deploy
Hooks       Coverage  Trivy     Build   (staging)  (staging)   (staging)
```

#### 18.9.2 Quality Gates in CI

| Stage | Gate | Criteria | Blocking |
|-------|------|----------|----------|
| Lint | Code style | Ruff, ESLint, golangci-lint | Yes |
| Unit tests | Coverage | ≥ 80% coverage | Yes |
| SAST | Security | 0 critical/high findings | Yes |
| SCA | Dependencies | 0 critical/high vulnerabilities | Yes |
| Integration | Tests pass | All integration tests pass | Yes |
| DAST | Security | 0 critical/high findings | Yes |
| Performance | Latency | P99 < 200ms | Yes |

### 18.10 Test Reporting

#### 18.10.1 Test Report Format

```json
{
  "test_run_id": "run-20261001-001",
  "timestamp": "2026-10-01T14:30:00Z",
  "environment": "staging",
  "summary": {
    "total": 1523,
    "passed": 1500,
    "failed": 20,
    "skipped": 3,
    "duration_seconds": 300
  },
  "coverage": {
    "lines": 87.5,
    "branches": 82.3,
    "functions": 90.1
  },
  "failures": [
    {
      "test": "test_policy_creation",
      "error": "AssertionError: Expected 201, got 400",
      "duration_ms": 1.2
    }
  ]
}
```

#### 18.10.2 Test Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Test pass rate | ≥ 98% | Per test run |
| Code coverage | ≥ 80% | Per build |
| Flaky test rate | < 1% | Per week |
| Test execution time | < 10 minutes | Per PR |
| Defect escape rate | < 5% | Per release |

---

## 19. Appendices

### Appendix A: Data Model Summary

| Entity | Primary Store | Key Fields | Relationships |
|--------|--------------|------------|---------------|
| Policy | PostgreSQL | `id`, `policy_key`, `status`, `version` | → Agent (many-to-many), → ComplianceControl (many-to-many) |
| PolicyVersion | MongoDB | `policy_id`, `version`, `full_text` | → Policy (many-to-one) |
| Evidence | MongoDB | `evidence_id`, `policy_id`, `evidence_type` | → Policy (many-to-one), → Assessment (many-to-one) |
| EnforcementDecision | PostgreSQL | `decision_id`, `verdict`, `agent_id`, `policy_id` | → Agent (many-to-one), → Policy (many-to-one) |
| Assessment | PostgreSQL | `assessment_key`, `assessment_type`, `status` | → Finding (one-to-many), → Evidence (many-to-many) |
| AssessmentFinding | PostgreSQL | `finding_key`, `severity`, `status` | → Assessment (many-to-one), → Policy (many-to-one) |
| ComplianceFramework | PostgreSQL | `framework_key`, `name`, `version` | → ComplianceControl (one-to-many) |
| ComplianceControl | PostgreSQL | `control_key`, `title`, `category` | → ComplianceFramework (many-to-one), → Policy (many-to-many) |
| ComplianceStatus | PostgreSQL | `framework_id`, `control_id`, `target_id` | → ComplianceControl (many-to-one) |
| Agent | PostgreSQL | `name`, `type`, `lifecycle_stage`, `risk_tier` | → Policy (many-to-many) |
| AuditEvent | immudb | `event_id`, `event_type`, `timestamp` | → All entities (polymorphic) |

### Appendix B: API Endpoint Summary

| Category | Endpoint | Method | Description |
|----------|----------|--------|-------------|
| **Policies** | `/v1.0/policies` | GET | List policies |
| | `/v1.0/policies` | POST | Create policy |
| | `/v1.0/policies/{id}` | GET | Get policy |
| | `/v1.0/policies/{id}` | PUT | Update policy |
| | `/v1.0/policies/{id}` | DELETE | Delete policy |
| | `/v1.0/policies/{id}/compile` | POST | Compile policy |
| | `/v1.0/policies/{id}/dry-run` | POST | Dry-run policy |
| | `/v1.0/policies/{id}/versions` | GET | Policy version history |
| | `/v1.0/policies/{id}/dependencies` | GET | Policy dependency graph |
| **Evidence** | `/v1.0/evidence` | GET | Search evidence |
| | `/v1.0/evidence` | POST | Submit evidence |
| | `/v1.0/evidence/{id}` | GET | Get evidence |
| | `/v1.0/evidence/{id}/verify` | POST | Verify evidence |
| | `/v1.0/evidence/export` | POST | Export evidence package |
| | `/v1.0/evidence/export/{id}` | GET | Get export package |
| **Enforcement** | `/v1.0/enforcement/decide` | POST | Request decision |
| | `/v1.0/enforcement/decide-batch` | POST | Batch decisions |
| | `/v1.0/enforcement/decisions/{id}` | GET | Get decision |
| | `/v1.0/enforcement/decisions` | GET | List decisions |
| **Assessments** | `/v1.0/assessments` | GET | List assessments |
| | `/v1.0/assessments` | POST | Create assessment |
| | `/v1.0/assessments/{id}` | GET | Get assessment |
| | `/v1.0/assessments/{id}` | PUT | Update assessment |
| | `/v1.0/assessments/{id}/findings` | POST | Add finding |
| | `/v1.0/assessments/{id}/report` | POST | Generate report |
| **Compliance** | `/v1.0/compliance/frameworks` | GET | List frameworks |
| | `/v1.0/compliance/frameworks/{id}/controls` | GET | List controls |
| | `/v1.0/compliance/posture` | GET | Get compliance posture |
| | `/v1.0/compliance/mappings` | POST | Create mapping |
| | `/v1.0/compliance/reports` | POST | Generate report |
| | `/v1.0/compliance/crosswalk` | GET | Cross-framework mapping |
| **Agents** | `/v1.0/agents` | GET | List agents |
| | `/v1.0/agents` | POST | Register agent |
| | `/v1.0/agents/{id}` | GET | Get agent |
| | `/v1.0/agents/{id}` | PUT | Update agent |
| | `/v1.0/agents/{id}/trust-score` | POST | Update trust score |
| | `/v1.0/agents/{id}/policy-bindings` | POST | Bind policies |
| **Audit** | `/v1.0/audit` | GET | Query audit trail |
| | `/v1.0/audit/verify` | POST | Verify audit chain |
| **Webhooks** | `/v1.0/webhooks/subscriptions` | GET | List subscriptions |
| | `/v1.0/webhooks/subscriptions` | POST | Create subscription |
| | `/v1.0/webhooks/subscriptions/{id}` | GET | Get subscription |
| | `/v1.0/webhooks/subscriptions/{id}` | PUT | Update subscription |
| | `/v1.0/webhooks/subscriptions/{id}` | DELETE | Delete subscription |
| | `/v1.0/webhooks/subscriptions/{id}/test` | POST | Test subscription |
| | `/v1.0/webhooks/subscriptions/{id}/deliveries` | GET | Delivery history |
| **Composed** | `/v1.0/composed/dashboard` | GET | Dashboard overview (aggregated) |
| | `/v1.0/composed/agents/{id}/360` | GET | Agent 360° view |
| | `/v1.0/composed/compliance-report` | GET | Compliance report (aggregated) |
| | `/v1.0/composed/executive-summary` | GET | Executive summary |
| **System** | `/health` | GET | Health check |
| | `/ready` | GET | Readiness check |
| | `/metrics` | GET | Prometheus metrics |
| | `/v1.0/graphql` | POST | GraphQL endpoint |

### Appendix C: Compliance Framework Coverage

| Framework | Controls | API Support | Status |
|-----------|----------|-------------|--------|
| NIST 800-53 Rev 5 | 1,026+ | Full | ✅ |
| SOC 2 Trust Services Criteria | 64+ | Full | ✅ |
| ISO 27001:2022 | 93+ | Full | ✅ |
| ISO/IEC 42001:2023 | 38+ | Full | ✅ |
| GDPR | 30+ | Full | ✅ |
| HIPAA Security Rule | 50+ | Full | ✅ |
| PCI DSS v4.0 | 78+ | Full | ✅ |
| COBIT 2019 | 40+ | Full | ✅ |
| NIST AI RMF | 68+ | Full | ✅ |
| EU AI Act | 40+ | Full | ✅ |

### Appendix D: Glossary

| Term | Definition |
|------|------------|
| **PEP** | Policy Enforcement Point — intercepts agent actions and applies policy decisions |
| **PDP** | Policy Decision Point — evaluates policies and returns enforcement decisions |
| **Cedar** | AWS's policy language for declarative authorization |
| **Rego** | OPA's policy language for general-purpose policy evaluation |
| **OSCAL** | Open Security Controls Assessment Language (NIST standard) |
| **WORM** | Write Once Read Many — immutable storage for evidence |
| **SVID** | SPIFFE Verifiable Identity Document — cryptographic identity for workloads |
| **mTLS** | Mutual TLS — bidirectional certificate-based authentication |
| **ABAC** | Attribute-Based Access Control — access based on attributes beyond roles |
| **RBAC** | Role-Based Access Control — access based on assigned roles |
| **UCT** | Unified Control Taxonomy — hub-and-spoke compliance mapping model |
| **AIRSS** | AI Risk Scoring System — composite risk scoring methodology |
| **DLP** | Data Loss Prevention — monitoring and blocking of sensitive data exfiltration |

### Appendix E: References

| Document | Relevance |
|----------|-----------|
| GRC_Claw Reference Architecture v1.0 | System architecture and component design |
| GRC_Claw Evidence Spec v1.0 | Evidence format, collection, and verification |
| GRC_Claw Storage Spec v1.0 | Data models and storage schemas |
| GRC_Claw Performance Spec v1.0 | Latency, throughput, and scalability targets |
| GRC_Claw Data Governance Spec v1.0 | Data classification, lineage, and provenance |
| GRC_Claw Integration Layer v1.0 | COBIT, ITIL, TOGAF, ISO 42001 integration |
| GRC_Claw Gap Analysis v1.0 | Market gaps and build priorities |
| GRC_Claw Third-Party Risk Spec v1.0 | Vendor AI risk management |
| NIST SP 800-53 Rev 5 | Security and privacy controls |
| ISO/IEC 42001:2023 | AI management system standard |
| NIST AI RMF 1.0 | AI risk management framework |
| EU AI Act (2024) | European AI regulation |
| OSCAL 1.1.0 | Open Security Controls Assessment Language |

---

**Document Control**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-10-01 | GRC_Claw Architecture Team | Initial API specification |
| 1.1 | 2026-10-01 | GRC_Claw Architecture Team | Added API security, rate limiting, versioning, monitoring, documentation automation, and testing sections |
| 1.2 | 2026-10-01 | GRC_Claw Architecture Team | Added real-time stream events (Flink), saga events, composed API endpoints |

---

*End of API Specification*