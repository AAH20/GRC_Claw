# GRC_Claw API Reference

> Last updated: 2026-10-01 | Base URL: `https://a2zsoc.com`

Complete REST API reference for the GRC_Claw platform. All endpoints require authentication via Bearer token and tenant scoping.

---

## Table of Contents

- [Authentication](#authentication)
- [Standard Request Format](#standard-request-format)
- [Error Model](#error-model)
- [Pagination](#pagination)
- [Compliance API](#compliance-api)
- [Evidence API](#evidence-api)
- [Agent API](#agent-api)
- [Crosswalk API](#crosswalk-api)
- [Audit API](#audit-api)
- [Marketplace API](#marketplace-api)
- [Verifier API](#verifier-api)
- [Benchmark API](#benchmark-api)
- [Procurement API](#procurement-api)
- [WebSocket API](#websocket-api)

---

## Authentication

All API requests require a Bearer token in the `Authorization` header:

```
Authorization: Bearer <jwt_token>
```

Tokens are obtained via the A2Z SOC authentication flow and contain tenant claims for multi-tenant scoping.

---

## Standard Request Format

```typescript
interface StandardRequest {
  headers: {
    'Authorization': 'Bearer <jwt>';
    'X-Tenant-Id': string;           // Tenant scoping
    'X-Idempotency-Key': string;     // ULID, mandatory for mutations
    'X-Correlation-Id'?: string;     // Distributed tracing
    'X-Schema-Version'?: number;     // API version pinning
  };
  body: unknown;                     // Validated against JSON Schema
}
```

### Idempotency

- All `POST`, `PUT`, `PATCH`, `DELETE` endpoints require `X-Idempotency-Key`
- Server stores key → response mapping for 72 hours (Redis TTL)
- Duplicate requests return cached response with `X-Idempotent-Replay: true`
- Keys are ULID-based (time-sortable, globally unique)

---

## Error Model

```typescript
interface ApiError {
  error: {
    code: string;                    // Machine-readable (e.g., EVIDENCE_CHAIN_BROKEN)
    message: string;                 // Human-readable
    details?: Record<string, unknown>;
    correlationId: string;
    timestamp: string;               // ISO 8601
    retryable: boolean;
  };
}
```

### HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 204 | No Content (delete success) |
| 400 | Validation Error |
| 401 | Authentication Required |
| 403 | Authorization Denied |
| 404 | Resource Not Found |
| 409 | Conflict (e.g., idempotency key replay with different payload) |
| 422 | Unprocessable Entity (business logic error) |
| 429 | Rate Limited (includes Retry-After header) |
| 500 | Internal Server Error |
| 503 | Service Unavailable (includes Retry-After header) |

---

## Pagination

```typescript
interface PaginatedResponse<T> {
  data: T[];
  pagination: {
    cursor: string | null;          // Cursor-based pagination
    hasMore: boolean;
    totalCount: number;             // Cached, ±1% accuracy
  };
}
```

**Usage:**
```
GET /api/v1/events?limit=50&cursor=***
```

---

## Compliance API

### List Controls

```
GET /api/v1/controls
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `framework` | string | Filter by framework (e.g., `soc2`, `iso27001`) |
| `severity` | string | Filter by severity: `low`, `medium`, `high`, `critical` |
| `status` | string | Filter by status: `passing`, `failing`, `partial` |

**Response:**
```json
{
  "data": [
    {
      "control_id": "CC6.1",
      "framework": "soc2",
      "title": "Logical Access Controls",
      "description": "...",
      "severity": "high",
      "status": "passing",
      "evidence_count": 12,
      "last_tested": "2026-06-30T10:00:00Z"
    }
  ],
  "pagination": {
    "cursor": "eyJ...",
    "hasMore": true,
    "totalCount": 42
  }
}
```

### Get Control Details

```
GET /api/v1/controls/{control_id}
```

### Test Control

```
POST /api/v1/controls/{control_id}/test
```

**Request body:**
```json
{
  "evidence_ids": ["evn_01J0...", "evn_01J1..."],
  "test_parameters": {}
}
```

### List Frameworks

```
GET /api/v1/frameworks
```

**Response:**
```json
{
  "data": [
    {
      "framework_id": "soc2",
      "name": "SOC 2",
      "version": "Type II",
      "control_count": 42,
      "mapping_count": 375,
      "installed": true
    }
  ]
}
```

---

## Evidence API

### List Evidence

```
GET /api/v1/evidence
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `framework` | string | Filter by framework |
| `type` | string | Filter by type: `log_entry`, `screenshot`, `config_export`, `scan_result`, `agent_receipt` |
| `freshness` | int | Filter by age in days |

### Attach Evidence

```
POST /api/v1/evidence/attach
```

**Request body:**
```json
{
  "control_id": "CC6.1",
  "evidence_type": "scan_result",
  "content": {},
  "metadata": {
    "source": "grc-scan",
    "version": "1.0.0"
  }
}
```

### Verify Evidence

```
POST /api/v1/evidence/verify
```

**Request body:**
```json
{
  "evidence_ids": ["evn_01J0..."],
  "verify_hash_chain": true,
  "verify_rfc3161": true
}
```

---

## Agent API

### Run Agent

```
POST /api/v1/agent/run
```

**Request body:**
```json
{
  "org": "acme-corp",
  "phases": ["plan", "act", "verify"],
  "max_actions": 50,
  "trust_threshold": 80,
  "dry_run": false
}
```

### Get Agent Status

```
GET /api/v1/agent/status/{run_id}
```

### List Agent Actions

```
GET /api/v1/agent/actions
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `agent_id` | string | Filter by agent |
| `status` | string | Filter by status: `pending`, `approved`, `denied`, `executed` |
| `trust_score` | int | Filter by minimum trust score |

### Agent Trust Score

```
GET /api/v1/agent/trust-score
```

**Response:**
```json
{
  "overall_score": 76,
  "grade": "C",
  "factors": {
    "evidence_freshness": { "score": 22, "max": 25 },
    "vulnerability_exposure": { "score": 18, "max": 25 },
    "control_test_pass_rate": { "score": 16, "max": 20 },
    "training_completion": { "score": 12, "max": 15 },
    "incident_transparency": { "score": 8, "max": 15 }
  },
  "trend": "+3 points since last assessment"
}
```

---

## Crosswalk API

### Get Crosswalk Mapping

```
GET /api/v1/crosswalk
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `source_framework` | string | Source framework ID |
| `source_control` | string | Source control ID |
| `target_framework` | string | Target framework ID |

**Response:**
```json
{
  "mappings": [
    {
      "source": { "framework": "soc2", "control": "CC6.1" },
      "target": { "framework": "iso27001", "control": "A.9.4.2" },
      "relationship": "equivalent",
      "confidence": 0.95
    },
    {
      "source": { "framework": "soc2", "control": "CC6.1" },
      "target": { "framework": "nist-csf", "control": "AC-2" },
      "relationship": "overlapping",
      "confidence": 0.88
    }
  ]
}
```

### Crosswalk Diff

```
GET /api/v1/crosswalk/diff
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `from` | string | Source git ref or framework |
| `to` | string | Target git ref or framework |

---

## Audit API

### Run Audit

```
POST /api/v1/audit/run
```

**Request body:**
```json
{
  "frameworks": ["soc2", "iso27001"],
  "include_agent_actions": true,
  "evidence_dir": ".grc/evidence"
}
```

### Get Audit Report

```
GET /api/v1/audit/report/{audit_id}
```

### Export Audit

```
GET /api/v1/audit/export/{audit_id}
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `format` | string | Export format: `json`, `pdf`, `oscal`, `ocsf`, `stix`, `sarif`, `ai-bom` |
| `signed` | boolean | Cryptographically sign report |

---

## Marketplace API

### List Packs

```
GET /api/v1/marketplace/packs
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `category` | string | Filter by category: `framework`, `connector`, `automation` |
| `search` | string | Search by name or description |

### Install Pack

```
POST /api/v1/marketplace/packs/{pack_id}/install
```

### Publish Pack

```
POST /api/v1/marketplace/packs
```

---

## Verifier API

### Create Verifier Room

```
POST /api/v1/verifier/rooms
```

**Request body:**
```json
{
  "scope": "auditor",
  "expires_days": 30,
  "evidence_ids": ["evn_01J0..."],
  "redact": true
}
```

### List Verifier Rooms

```
GET /api/v1/verifier/rooms
```

### Get Verifier Room

```
GET /api/v1/verifier/rooms/{room_id}
```

---

## Benchmark API

### Compare Benchmarks

```
GET /api/v1/benchmark/compare
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `framework` | string | Compare specific framework |
| `industry` | string | Industry cohort: `tech`, `finance`, `healthcare`, `government`, `manufacturing` |
| `size` | string | Org size: `startup`, `smb`, `mid-market`, `enterprise` |

**Response:**
```json
{
  "industry": "tech",
  "size": "mid-market",
  "peer_count": 1247,
  "frameworks": [
    {
      "framework": "soc2",
      "your_score": 72,
      "peer_median": 68,
      "percentile": 62,
      "gap": 4
    }
  ]
}
```

---

## Procurement API

### Generate Procurement Packet

```
POST /api/v1/procurement/packet
```

**Request body:**
```json
{
  "buyer": "dod",
  "frameworks": ["cmmc", "nist-800-171", "iso-42001"],
  "include": ["ssp", "poam", "sprs", "ai-bom", "sbom", "evidence", "questionnaire"],
  "format": "json"
}
```

---

## WebSocket API

### Connect

```
wss://a2zsoc.com/ws
```

**Connection headers:**
```
Authorization: Bearer <jwt>
X-GRC-Claw-Token: <token>
```

### Subscribe to SOC Events

```json
{
  "type": "subscribe",
  "channel": "soc_events"
}
```

### Subscribe to Compliance Alerts

```json
{
  "type": "subscribe",
  "channel": "compliance_alerts"
}
```

### Event Types

| Event Type | Description |
|------------|-------------|
| `security_event` | Normalized SIEM event |
| `compliance_alert` | Compliance threshold breach |
| `agent_action` | Agent action receipt |
| `evidence_update` | Evidence graph mutation |
| `trust_score_change` | Trust score update |
