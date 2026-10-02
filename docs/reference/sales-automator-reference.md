# Sales Automator API Reference

> Last updated: 2026-10-02 | Base URL: `https://a2zsoc.com`

Automate sales outreach, manage prospect sequences, score leads, and schedule demos.

---

## Table of Contents

- [Overview](#overview)
- [Endpoints](#endpoints)
  - [GET /health](#get-health)
  - [GET /metrics](#get-metrics)
  - [POST /api/v1/prospects](#post-api-v1-prospects)
  - [GET /api/v1/prospects](#get-api-v1-prospects)
  - [GET /api/v1/prospects/{prospect_id}](#get-api-v1-prospects-prospect_id)
  - [POST /api/v1/prospects/{prospect_id}/score](#post-api-v1-prospects-prospect_id-score)
  - [POST /api/v1/sequences](#post-api-v1-sequences)
  - [GET /api/v1/sequences](#get-api-v1-sequences)
  - [GET /api/v1/sequences/{sequence_id}](#get-api-v1-sequences-sequence_id)
  - [POST /api/v1/sequences/{sequence_id}/enroll](#post-api-v1-sequences-sequence_id-enroll)
- [Error Codes](#error-codes)
- [Rate Limiting](#rate-limiting)
- [Pagination](#pagination)
- [Authentication](#authentication)
- [Idempotency](#idempotency)

---

## Overview

The Sales Automator API provides programmatic access to automate sales outreach, manage prospect sequences, score leads, and schedule demos.

**Base Path:** `/api/v1`

All endpoints require authentication via Bearer token and tenant scoping.

---

## Endpoints

### GET /health

Health check endpoint.

**Response (200):**

```json
{
  "status": "healthy",
  "version": "0.1.0"
}
```

**Example:**

```bash
curl -X GET https://a2zsoc.com/health
```

---

### GET /metrics

Prometheus metrics endpoint.

**Response (200):**

```
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{method="POST",endpoint="/api/v1/prospects",status="201"} 5
```

**Example:**

```bash
curl -X GET https://a2zsoc.com/metrics
```

---

### POST /api/v1/prospects

Create a new prospect.

**Request Body:**

```json
{
  "name": "Jane Smith",
  "company": "TechCorp",
  "title": "VP of Engineering",
  "email": "jane.smith@techcorp.com",
  "linkedin_url": "https://linkedin.com/in/janesmith",
  "company_size": 500,
  "industry": "Technology",
  "source": "linkedin",
  "metadata": {"campaign": "q4_outreach"}
}
```

**Response (201):**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Jane Smith",
  "company": "TechCorp",
  "title": "VP of Engineering",
  "email": "jane.smith@techcorp.com",
  "linkedin_url": "https://linkedin.com/in/janesmith",
  "company_size": 500,
  "industry": "Technology",
  "source": "linkedin",
  "score": null,
  "metadata": {"campaign": "q4_outreach"}
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/prospects \
  -H "Authorization: Bearer ***" \
  -H "Content-Type: application/json" \
  -H "X-Idempotency-Key: 01J0ABC1234567890" \
  -d '{"name": "Jane Smith", "company": "TechCorp", "email": "jane.smith@techcorp.com"}'
```

---

### GET /api/v1/prospects

List all prospects.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `skip` | integer | No | Number of prospects to skip (default: 0) |
| `limit` | integer | No | Maximum number to return (default: 100) |

**Response (200):**

```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Jane Smith",
    "company": "TechCorp",
    "title": "VP of Engineering",
    "email": "jane.smith@techcorp.com",
    "source": "linkedin"
  }
]
```

**Example:**

```bash
curl -X GET "https://a2zsoc.com/api/v1/prospects?skip=0&limit=50" \
  -H "Authorization: Bearer ***"
```

---

### GET /api/v1/prospects/{prospect_id}

Get a prospect by ID.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `prospect_id` | string | Yes | Prospect identifier |

**Response (200):**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Jane Smith",
  "company": "TechCorp",
  "title": "VP of Engineering",
  "email": "jane.smith@techcorp.com",
  "source": "linkedin"
}
```

**Example:**

```bash
curl -X GET https://a2zsoc.com/api/v1/prospects/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer ***"
```

---

### POST /api/v1/prospects/{prospect_id}/score

Score a prospect.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `prospect_id` | string | Yes | Prospect identifier |

**Response (200):**

```json
{
  "prospect_id": "550e8400-e29b-41d4-a716-446655440000",
  "total_score": 78.5,
  "factors": [
    {"name": "company_size", "weight": 0.3, "score": 85},
    {"name": "title_seniority", "weight": 0.4, "score": 90},
    {"name": "industry_fit", "weight": 0.3, "score": 60}
  ],
  "priority": "high",
  "recommendation": "Priority follow-up within 24 hours"
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/prospects/550e8400-e29b-41d4-a716-446655440000/score \
  -H "Authorization: Bearer ***" \
  -H "X-Idempotency-Key: 01J0ABC1234567890"
```

---

### POST /api/v1/sequences

Create a new outreach sequence.

**Request Body:**

```json
{
  "name": "Q4 Outreach Sequence",
  "prospect_id": "550e8400-e29b-41d4-a716-446655440000",
  "steps": 5,
  "context": {"campaign": "q4_product_launch", "product": "enterprise_plan"}
}
```

**Response (201):**

```json
{
  "id": "seq_001",
  "name": "Q4 Outreach Sequence",
  "steps": [
    {"step": 1, "type": "email", "delay_days": 0},
    {"step": 2, "type": "email", "delay_days": 2},
    {"step": 3, "type": "call", "delay_days": 4},
    {"step": 4, "type": "email", "delay_days": 7},
    {"step": 5, "type": "linkedin", "delay_days": 10}
  ],
  "target_prospect_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "draft",
  "metadata": {"campaign": "q4_product_launch"}
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/sequences \
  -H "Authorization: Bearer ***" \
  -H "Content-Type: application/json" \
  -H "X-Idempotency-Key: 01J0ABC1234567890" \
  -d '{"name": "Q4 Outreach Sequence", "prospect_id": "550e8400-e29b-41d4-a716-446655440000", "steps": 5}'
```

---

### GET /api/v1/sequences

List all outreach sequences.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `skip` | integer | No | Number of sequences to skip (default: 0) |
| `limit` | integer | No | Maximum number to return (default: 100) |

**Response (200):**

```json
[
  {
    "id": "seq_001",
    "name": "Q4 Outreach Sequence",
    "status": "draft",
    "target_prospect_id": "550e8400-e29b-41d4-a716-446655440000"
  }
]
```

**Example:**

```bash
curl -X GET "https://a2zsoc.com/api/v1/sequences?skip=0&limit=50" \
  -H "Authorization: Bearer ***"
```

---

### GET /api/v1/sequences/{sequence_id}

Get a sequence by ID.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `sequence_id` | string | Yes | Sequence identifier |

**Response (200):**

```json
{
  "id": "seq_001",
  "name": "Q4 Outreach Sequence",
  "steps": [
    {"step": 1, "type": "email", "delay_days": 0},
    {"step": 2, "type": "email", "delay_days": 2}
  ],
  "target_prospect_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "draft"
}
```

**Example:**

```bash
curl -X GET https://a2zsoc.com/api/v1/sequences/seq_001 \
  -H "Authorization: Bearer ***"
```

---

### POST /api/v1/sequences/{sequence_id}/enroll

Enroll a prospect in a sequence.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `sequence_id` | string | Yes | Sequence identifier |

**Request Body:**

```json
{
  "prospect_id": "550e8400-e29b-41d4-a716-446655440000",
  "start_step": 1
}
```

**Response (200):**

```json
{
  "sequence_id": "seq_001",
  "prospect_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "enrolled",
  "started_at": "2026-10-01T00:00:00Z"
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/sequences/seq_001/enroll \
  -H "Authorization: Bearer ***" \
  -H "Content-Type: application/json" \
  -H "X-Idempotency-Key: 01J0ABC1234567890" \
  -d '{"prospect_id": "550e8400-e29b-41d4-a716-446655440000", "start_step": 1}'
```

---

## Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Request validation failed |
| `AUTHENTICATION_REQUIRED` | 401 | Missing or invalid authentication |
| `AUTHORIZATION_DENIED` | 403 | Insufficient permissions |
| `RESOURCE_NOT_FOUND` | 404 | Resource does not exist |
| `CONFLICT` | 409 | Resource conflict (e.g., duplicate) |
| `UNPROCESSABLE_ENTITY` | 422 | Business logic validation failed |
| `RATE_LIMITED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Internal server error |
| `SERVICE_UNAVAILABLE` | 503 | Service temporarily unavailable |

## Rate Limiting

All API endpoints are subject to rate limiting:

- **Standard tier**: 100 requests/minute
- **Professional tier**: 500 requests/minute
- **Enterprise tier**: 2000 requests/minute

Rate limit headers are included in all responses:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1696123200
```

## Pagination

List endpoints support cursor-based pagination:

```typescript
interface PaginatedResponse<T> {
  data: T[];
  pagination: {
    cursor: string | null;
    hasMore: boolean;
    totalCount: number;
  };
}
```

## Authentication

All endpoints require Bearer token authentication:

```
Authorization: Bearer ***
```

## Idempotency

All `POST`, `PUT`, `PATCH`, and `DELETE` endpoints require an `X-Idempotency-Key` header:

```
X-Idempotency-Key: <ulid>
```

Duplicate requests with the same key return the cached response with `X-Idempotent-Replay: true`.
