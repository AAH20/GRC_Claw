# Journey Orchestrator API Reference

> Last updated: 2026-10-02 | Base URL: `https://a2zsoc.com`

Design, execute, and optimize multi-channel customer journeys. Supports A/B testing, personalization, and timing optimization.

---

## Table of Contents

- [Overview](#overview)
- [Endpoints](#endpoints)
  - [POST /api/v1/journeys](#post-api-v1journeys)
  - [GET /api/v1/journeys](#get-api-v1journeys)
  - [GET /api/v1/journeys/{journey_id}](#get-api-v1journeysjourney_id)
  - [PUT /api/v1/journeys/{journey_id}](#put-api-v1journeysjourney_id)
  - [DELETE /api/v1/journeys/{journey_id}](#delete-api-v1journeysjourney_id)
  - [POST /api/v1/journeys/{journey_id}/execute](#post-api-v1journeysjourney_idexecute)
  - [GET /api/v1/journeys/{journey_id}/status](#get-api-v1journeysjourney_idstatus)
  - [POST /api/v1/journeys/experiments](#post-api-v1journeysexperiments)
  - [GET /api/v1/journeys/experiments/{experiment_id}/results](#get-api-v1journeysexperimentsexperiment_idresults)
  - [POST /api/v1/journeys/personalize](#post-api-v1journeyspersonalize)
  - [POST /api/v1/journeys/optimize-timing](#post-api-v1journeysoptimize-timing)
- [Error Codes](#error-codes)
- [Rate Limiting](#rate-limiting)
- [Pagination](#pagination)
- [Authentication](#authentication)
- [Idempotency](#idempotency)

---

## Overview

The Journey Orchestrator API provides programmatic access to design, execute, and optimize multi-channel customer journeys. Supports A/B testing, personalization, and timing optimization.

**Base Path:** `/api/v1/journeys`

All endpoints require authentication via Bearer token and tenant scoping.

---

## Endpoints

### POST /api/v1/journeys

Create a new customer journey.

**Request Body:**

```json
{
  "name": "Onboarding Journey",
  "description": "New customer onboarding sequence",
  "target_audience": {
    "segment": "new_customers"
  },
  "business_goal": "activation",
  "channels": ["email", "push", "in_app"],
  "metadata": {}
}
```

**Response (201):**

```json
{
  "id": "journey-uuid-123",
  "name": "Onboarding Journey",
  "description": "New customer onboarding sequence",
  "target_audience": {
    "segment": "new_customers"
  },
  "business_goal": "activation",
  "channels": ["email", "push", "in_app"],
  "status": "draft",
  "stages": [],
  "created_at": "2026-10-01T00:00:00Z",
  "updated_at": "2026-10-01T00:00:00Z",
  "metadata": {}
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/journeys \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -H "X-Idempotency-Key: 01J0ABC1234567890" \
  -d '{
    "name": "Onboarding Journey",
    "channels": ["email"]
  }'
```

---

### GET /api/v1/journeys

List all journeys with optional filtering.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `page` | integer | No | Page number |
| `page_size` | integer | No | Items per page |
| `status` | string | No | Filter by status: draft, active, paused, completed |

**Response (200):**

```json
{
  "journeys": [
    {
      "id": "journey-uuid-123",
      "name": "Onboarding Journey",
      "status": "draft",
      "channels": ["email"],
      "created_at": "2026-10-01T00:00:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20
}
```

**Example:**

```bash
curl -X GET "https://a2zsoc.com/api/v1/journeys?status=draft" \
  -H "Authorization: Bearer <token>"
```

---

### GET /api/v1/journeys/{journey_id}

Get a journey by ID.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `journey_id` | string | Yes | Journey identifier |

**Response (200):**

```json
{
  "id": "journey-uuid-123",
  "name": "Onboarding Journey",
  "status": "draft",
  "channels": ["email"],
  "stages": [],
  "created_at": "2026-10-01T00:00:00Z",
  "updated_at": "2026-10-01T00:00:00Z"
}
```

**Example:**

```bash
curl -X GET https://a2zsoc.com/api/v1/journeys/journey-uuid-123 \
  -H "Authorization: Bearer <token>"
```

---

### PUT /api/v1/journeys/{journey_id}

Update a journey.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `journey_id` | string | Yes | Journey identifier |

**Request Body:**

```json
{
  "name": "Updated Journey Name",
  "status": "active"
}
```

**Response (200):**

```json
{
  "id": "journey-uuid-123",
  "name": "Updated Journey Name",
  "status": "active",
  "channels": ["email"],
  "created_at": "2026-10-01T00:00:00Z",
  "updated_at": "2026-10-01T12:00:00Z"
}
```

**Example:**

```bash
curl -X PUT https://a2zsoc.com/api/v1/journeys/journey-uuid-123 \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -H "X-Idempotency-Key: 01J0ABC1234567890" \
  -d '{
    "status": "active"
  }'
```

---

### DELETE /api/v1/journeys/{journey_id}

Delete a journey.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `journey_id` | string | Yes | Journey identifier |

**Response:** 204 No Content

**Example:**

```bash
curl -X DELETE https://a2zsoc.com/api/v1/journeys/journey-uuid-123 \
  -H "Authorization: Bearer <token>" \
  -H "X-Idempotency-Key: 01J0ABC1234567890"
```

---

### POST /api/v1/journeys/{journey_id}/execute

Execute a journey.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `journey_id` | string | Yes | Journey identifier |

**Request Body:**

```json
{
  "customer_ids": ["cust_001", "cust_002"]
}
```

**Response (200):**

```json
{
  "execution_id": "exec-uuid-456",
  "journey_id": "journey-uuid-123",
  "status": "active",
  "message": "Journey execution started"
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/journeys/journey-uuid-123/execute \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -H "X-Idempotency-Key: 01J0ABC1234567890" \
  -d '{
    "customer_ids": ["cust_001"]
  }'
```

---

### GET /api/v1/journeys/{journey_id}/status

Get the execution status of a journey.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `journey_id` | string | Yes | Journey identifier |

**Response (200):**

```json
{
  "journey_id": "journey-uuid-123",
  "status": "active",
  "progress": 0.65,
  "customers_processed": 650,
  "customers_total": 1000
}
```

**Example:**

```bash
curl -X GET https://a2zsoc.com/api/v1/journeys/journey-uuid-123/status \
  -H "Authorization: Bearer <token>"
```

---

### POST /api/v1/journeys/experiments

Create a new A/B test or experiment.

**Request Body:**

```json
{
  "name": "Subject Line Test",
  "hypothesis": "Personalized subject lines increase open rates",
  "variants": [
    {
      "name": "control",
      "subject": "Check out our features"
    },
    {
      "name": "treatment",
      "subject": "John, see what's new for you"
    }
  ],
  "primary_metric": "open_rate"
}
```

**Response (201):**

```json
{
  "id": "exp-uuid-789",
  "name": "Subject Line Test",
  "hypothesis": "Personalized subject lines increase open rates",
  "status": "draft",
  "variants": [
    {
      "name": "control",
      "subject": "Check out our features"
    },
    {
      "name": "treatment",
      "subject": "John, see what's new for you"
    }
  ],
  "primary_metric": "open_rate",
  "created_at": "2026-10-01T00:00:00Z"
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/journeys/experiments \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -H "X-Idempotency-Key: 01J0ABC1234567890" \
  -d '{
    "name": "Subject Line Test",
    "variants": []
  }'
```

---

### GET /api/v1/journeys/experiments/{experiment_id}/results

Get the results of an experiment.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `experiment_id` | string | Yes | Experiment identifier |

**Response (200):**

```json
{
  "experiment_id": "exp-uuid-789",
  "status": "running",
  "sample_size": 5000,
  "metrics": {},
  "recommendation": "Experiment still in progress"
}
```

**Example:**

```bash
curl -X GET https://a2zsoc.com/api/v1/journeys/experiments/exp-uuid-789/results \
  -H "Authorization: Bearer <token>"
```

---

### POST /api/v1/journeys/personalize

Generate personalized content for a customer.

**Request Body:**

```json
{
  "customer_id": "cust_001",
  "channel": "email",
  "customer_profile": {
    "name": "John Doe",
    "preferences": ["technology", "productivity"]
  }
}
```

**Response (200):**

```json
{
  "customer_id": "cust_001",
  "contents": [
    {
      "channel": "email",
      "subject": "Your personalized recommendation",
      "body": "Hi John Doe, we have something special for you!",
      "call_to_action": "Learn More",
      "personalization_tokens": {
        "name": "John Doe"
      }
    }
  ],
  "recommended_offers": ["offer_1", "offer_2"],
  "next_best_action": "send_email",
  "confidence_score": 0.85
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/journeys/personalize \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "cust_001",
    "channel": "email"
  }'
```

---

### POST /api/v1/journeys/optimize-timing

Get optimal send times for a customer.

**Request Body:**

```json
{
  "customer_id": "cust_001",
  "channels": ["email", "push"],
  "timezone": "America/New_York"
}
```

**Response (200):**

```json
{
  "customer_id": "cust_001",
  "timezone": "America/New_York",
  "channel_timings": [
    {
      "channel": "email",
      "optimal_send_time": "10:00",
      "optimal_day": "Tuesday",
      "frequency_cap": 3,
      "min_interval_hours": 24,
      "expected_open_rate": 0.25,
      "expected_conversion_rate": 0.05
    }
  ],
  "best_overall_time": "10:00",
  "global_frequency_cap": 5
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/journeys/optimize-timing \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "cust_001",
    "channels": ["email"]
  }'
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
Authorization: Bearer <jwt_token>
```

## Idempotency

All `POST`, `PUT`, `PATCH`, and `DELETE` endpoints require an `X-Idempotency-Key` header:

```
X-Idempotency-Key: <ulid>
```

Duplicate requests with the same key return the cached response with `X-Idempotent-Replay: true`.
