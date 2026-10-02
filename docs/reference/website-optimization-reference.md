# Website Optimization API Reference

> Last updated: 2026-10-02 | Base URL: `https://a2zsoc.com` | Version: `0.1.0`

Agentic AI platform for website optimization. A/B testing, heatmaps, personalization, page analytics, and conversion rate optimization.

---

## Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [Endpoints](#endpoints)
  - [Pages](#pages)
    - [POST /api/v1/pages](#post--api-v1-pages)
    - [GET /api/v1/pages](#get--api-v1-pages)
    - [GET /api/v1/pages/{page_id}](#get--api-v1-pages-page_id)
    - [PUT /api/v1/pages/{page_id}](#put--api-v1-pages-page_id)
    - [DELETE /api/v1/pages/{page_id}](#delete--api-v1-pages-page_id)
  - [Experiments (A/B Tests)](#experiments-ab-tests)
    - [POST /api/v1/experiments](#post--api-v1-experiments)
    - [GET /api/v1/experiments](#get--api-v1-experiments)
    - [GET /api/v1/experiments/{experiment_id}](#get--api-v1-experiments-experiment_id)
    - [PUT /api/v1/experiments/{experiment_id}](#put--api-v1-experiments-experiment_id)
    - [POST /api/v1/experiments/{experiment_id}/start](#post--api-v1-experiments-experiment_id-start)
    - [POST /api/v1/experiments/{experiment_id}/stop](#post--api-v1-experiments-experiment_id-stop)
  - [Analytics](#analytics)
    - [GET /api/v1/analytics/{page_id}](#get--api-v1-analytics-page_id)
    - [GET /api/v1/analytics/{page_id}/funnel](#get--api-v1-analytics-page_id-funnel)
  - [Personalization](#personalization)
    - [POST /api/v1/personalization/rules](#post--api-v1-personalization-rules)
    - [GET /api/v1/personalization/rules](#get--api-v1-personalization-rules)
- [Error Codes](#error-codes)
- [Rate Limiting](#rate-limiting)
- [Pagination](#pagination)
- [Idempotency](#idempotency)
- [Webhooks](#webhooks)

---

## Overview

The Website Optimization API provides programmatic access to optimize website performance, conversion rates, and user experience. A/B testing, heatmaps, and personalization.

**Base Path:** `/api/v1`

All endpoints require authentication via Bearer token and tenant scoping.

---

## Authentication

All endpoints require Bearer token authentication:

```
Authorization: Bearer <token>
```

---

## Endpoints

### Pages

#### POST /api/v1/pages

Create a new page.

**Request Body:**

```json
{
  "name": "Homepage",
  "url": "https://example.com/",
  "description": "Main landing page",
  "page_type": "landing",
  "status": "active",
  "metadata": {
    "category": "marketing",
    "team": "growth"
  }
}
```

**Response (201):**

```json
{
  "page_id": "page_001",
  "name": "Homepage",
  "url": "https://example.com/",
  "page_type": "landing",
  "status": "active",
  "created_at": "2026-10-01T00:00:00Z"
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/pages \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -H "X-Idempotency-Key: 01J0ABC1234567890" \
  -d '{"name": "Homepage", "url": "https://example.com/"}'
```

---

#### GET /api/v1/pages

List all pages.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `status` | string | No | Filter by status: `active`, `inactive`, `archived` |
| `page_type` | string | No | Filter by type: `landing`, `product`, `blog`, `checkout` |
| `cursor` | string | No | Pagination cursor |
| `limit` | integer | No | Items per page (default: 20, max: 100) |

**Response (200):**

```json
{
  "data": [
    {
      "page_id": "page_001",
      "name": "Homepage",
      "url": "https://example.com/",
      "page_type": "landing",
      "status": "active",
      "created_at": "2026-10-01T00:00:00Z"
    }
  ],
  "pagination": {
    "cursor": "eyJpZCI6InBhZ2VfMDAxIn0=",
    "hasMore": false,
    "totalCount": 1
  }
}
```

**Example:**

```bash
curl -X GET "https://a2zsoc.com/api/v1/pages?status=active" \
  -H "Authorization: Bearer <token>"
```

---

#### GET /api/v1/pages/{page_id}

Get a page by ID.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `page_id` | string | Yes | Page identifier |

**Response (200):**

```json
{
  "page_id": "page_001",
  "name": "Homepage",
  "url": "https://example.com/",
  "description": "Main landing page",
  "page_type": "landing",
  "status": "active",
  "metadata": {"category": "marketing", "team": "growth"},
  "created_at": "2026-10-01T00:00:00Z",
  "updated_at": "2026-10-01T00:00:00Z"
}
```

**Example:**

```bash
curl -X GET https://a2zsoc.com/api/v1/pages/page_001 \
  -H "Authorization: Bearer <token>"
```

---

#### PUT /api/v1/pages/{page_id}

Update a page.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `page_id` | string | Yes | Page identifier |

**Request Body:**

```json
{
  "name": "Updated Homepage",
  "url": "https://example.com/new",
  "status": "active"
  "metadata": {"category": "marketing", "team": "growth", "version": "2"}
}
```

**Response (200):**

```json
{
  "page_id": "page_001",
  "name": "Updated Homepage",
  "url": "https://example.com/new",
  "status": "active",
  "updated_at": "2026-10-01T12:00:00Z"
}
```

**Example:**

```bash
curl -X PUT https://a2zsoc.com/api/v1/pages/page_001 \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "Updated Homepage"}'
```

---

#### DELETE /api/v1/pages/{page_id}

Delete a page.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `page_id` | string | Yes | Page identifier |

**Response:** `204 No Content`

**Example:**

```bash
curl -X DELETE https://a2zsoc.com/api/v1/pages/page_001 \
  -H "Authorization: Bearer <token>" \
  -H "X-Idempotency-Key: 01J0ABC1234567890"
```

---

### Experiments (A/B Tests)

#### POST /api/v1/experiments

Create an A/B test for a web page.

**Request Body:**

```json
{
  "page_id": "page_001",
  "name": "Homepage CTA Test",
  "description": "Test CTA button text variations",
  "variants": [
    {
      "name": "control",
      "cta_text": "Sign Up",
      "cta_color": "#007bff",
      "traffic_allocation": 0.5
    },
    {
      "name": "treatment",
      "cta_text": "Get Started Free",
      "cta_color": "#28a745",
      "traffic_allocation": 0.5
    }
  ],
  "primary_metric": "conversion_rate",
  "secondary_metrics": ["click_rate", "bounce_rate"],
  "minimum_sample_size": 1000,
  "confidence_level": 0.95,
  "status": "draft"
}
```

**Response (201):**

```json
{
  "experiment_id": "ab_001",
  "page_id": "page_001",
  "name": "Homepage CTA Test",
  "status": "draft",
  "variants_count": 2,
  "created_at": "2026-10-01T00:00:00Z"
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/experiments \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"page_id": "page_001", "name": "CTA Test"}'
```

---

#### GET /api/v1/experiments

List all experiments.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `status` | string | No | Filter by status: `draft`, `running`, `completed`, `stopped` |
| `page_id` | string | No | Filter by page |
| `cursor` | string | No | Pagination cursor |
| `limit` | integer | No | Items per page (default: 20, max: 100) |

**Response (200):**

```json
{
  "data": [
    {
      "experiment_id": "ab_001",
      "page_id": "page_001",
      "name": "Homepage CTA Test",
      "status": "running",
      "primary_metric": "conversion_rate",
      "created_at": "2026-10-01T00:00:00Z"
    }
  ],
  "pagination": {
    "cursor": null,
    "hasMore": false,
    "totalCount": 1
  }
}
```

**Example:**

```bash
curl -X GET "https://a2zsoc.com/api/v1/experiments?status=running" \
  -H "Authorization: Bearer <token>"
```

---

#### GET /api/v1/experiments/{experiment_id}

Get an experiment by ID.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `experiment_id` | string | Yes | Experiment identifier |

**Response (200):**

```json
{
  "experiment_id": "ab_001",
  "page_id": "page_001",
  "name": "Homepage CTA Test",
  "description": "Test CTA button text variations",
  "status": "running",
  "variants": [
    {"name": "control", "cta_text": "Sign Up", "traffic_allocation": 0.5},
    {"name": "treatment", "cta_text": "Get Started Free", "traffic_allocation": 0.5}
  ],
  "primary_metric": "conversion_rate",
  "secondary_metrics": ["click_rate", "bounce_rate"],
  "minimum_sample_size": 1000,
  "confidence_level": 0.95,
  "results": {
    "control": {"visitors": 5000, "conversions": 150, "conversion_rate": 0.03},
    "treatment": {"visitors": 5000, "conversions": 200, "conversion_rate": 0.04},
    "winner": "treatment",
    "confidence": 0.97,
    "improvement": 0.33
  },
  "created_at": "2026-10-01T00:00:00Z",
  "updated_at": "2026-10-01T00:00:00Z"
}
```

**Example:**

```bash
curl -X GET https://a2zsoc.com/api/v1/experiments/ab_001 \
  -H "Authorization: Bearer <token>"
```

---

#### PUT /api/v1/experiments/{experiment_id}

Update an experiment.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `experiment_id` | string | Yes | Experiment identifier |

**Request Body:**

```json
{
  "name": "Updated Experiment Name",
  "status": "stopped",
  "minimum_sample_size": 2000
}
```

**Response (200):**

```json
{
  "experiment_id": "ab_001",
  "name": "Updated Experiment Name",
  "status": "stopped",
  "updated_at": "2026-10-01T12:00:00Z"
}
```

**Example:**

```bash
curl -X PUT https://a2zsoc.com/api/v1/experiments/ab_001 \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"status": "stopped"}'
```

---

#### POST /api/v1/experiments/{experiment_id}/start

Start a draft experiment.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `experiment_id` | string | Yes | Experiment identifier |

**Response (200):**

```json
{
  "experiment_id": "ab_001",
  "status": "running",
  "started_at": "2026-10-01T00:00:00Z"
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/experiments/ab_001/start \
  -H "Authorization: Bearer <token>"
```

---

#### POST /api/v1/experiments/{experiment_id}/stop

Stop a running experiment.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `experiment_id` | string | Yes | Experiment identifier |

**Response (200):**

```json
{
  "experiment_id": "ab_001",
  "status": "stopped",
  "stopped_at": "2026-10-01T00:00:00Z"
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/experiments/ab_001/stop \
  -H "Authorization: Bearer <token>"
```

---

### Analytics

#### GET /api/v1/analytics/{page_id}

Get page analytics.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `page_id` | string | Yes | Page identifier |
| `start_date` | string | No | Start date (ISO 8601) |
| `end_date` | string | No | End date (ISO 8601) |

**Response (200):**

```json
{
  "page_id": "page_001",
  "pageviews": 10000,
  "unique_visitors": 8000,
  "bounce_rate": 0.35,
  "avg_time_on_page": 120,
  "conversion_rate": 0.03,
  "conversions": 300,
  "revenue": 15000,
  "top_referrers": [
    {"source": "google", "visitors": 3000},
    {"source": "direct", "visitors": 2500},
    {"source": "social", "visitors": 1500}
  ],
  "device_breakdown": [
    {"device": "desktop", "visitors": 5000, "conversion_rate": 0.035},
    {"device": "mobile", "visitors": 4000, "conversion_rate": 0.025},
    {"device": "tablet", "visitors": 1000, "conversion_rate": 0.02}
  ],
  "period": {"start": "2026-09-01", "end": "2026-09-30"}
}
```

**Example:**

```bash
curl -X GET "https://a2zsoc.com/api/v1/analytics/page_001?start_date=2026-09-01" \
  -H "Authorization: Bearer <token>"
```

---

#### GET /api/v1/analytics/{page_id}/funnel

Get conversion funnel for a page.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `page_id` | string | Yes | Page identifier |

**Response (200):**

```json
{
  "page_id": "page_001",
  "steps": [
    {"step": "page_view", "count": 10000, "conversion_rate": 1.0},
    {"step": "cta_click", "count": 3000, "conversion_rate": 0.30},
    {"step": "form_start", "count": 1500, "conversion_rate": 0.15},
    {"step": "form_submit", "count": 500, "conversion_rate": 0.05},
    {"step": "conversion", "count": 300, "conversion_rate": 0.03}
  ],
  "drop_off_points": [
    {"from": "page_view", "to": "cta_click", "drop_off_rate": 0.70},
    {"from": "cta_click", "to": "form_start", "drop_off_rate": 0.50}
  ]
}
```

**Example:**

```bash
curl -X GET https://a2zsoc.com/api/v1/analytics/page_001/funnel \
  -H "Authorization: Bearer <token>"
```

---

### Personalization

#### POST /api/v1/personalization/rules

Create a personalization rule.

**Request Body:**

```json
{
  "page_id": "page_001",
  "name": "Returning Visitor Welcome",
  "description": "Show welcome message to returning visitors",
  "conditions": [
    {
      "field": "visitor_type",
      "operator": "equals",
      "value": "returning"
    }
  ],
  "actions": [
    {
      "type": "show_banner",
      "content": "Welcome back! Here's what's new.",
      "position": "top"
    }
  ],
  "priority": 1,
  "status": "active"
  "start_date": "2026-10-01",
  "end_date": "2026-12-31"
}
```

**Response (201):**

```json
{
  "rule_id": "pers_001",
  "page_id": "page_001",
  "name": "Returning Visitor Welcome",
  "status": "active",
  "created_at": "2026-10-01T00:00:00Z"
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/personalization/rules \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"page_id": "page_001", "name": "Welcome Back"}'
```

---

#### GET /api/v1/personalization/rules

List all personalization rules.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `page_id` | string | No | Filter by page |
| `status` | string | No | Filter by status: `active`, `inactive`, `expired` |
| `cursor` | string | No | Pagination cursor |
| `limit` | integer | No | Items per page (default: 20, max: 100) |

**Response (200):**

```json
{
  "data": [
    {
      "rule_id": "pers_001",
      "page_id": "page_001",
      "name": "Returning Visitor Welcome",
      "status": "active",
      "priority": 1,
      "created_at": "2026-10-01T00:00:00Z"
    }
  ],
  "pagination": {
    "cursor": null,
    "hasMore": false,
    "totalCount": 1
  }
}
```

**Example:**

```bash
curl -X GET "https://a2zsoc.com/api/v1/personalization/rules?page_id=page_001" \
  -H "Authorization: Bearer <token>"
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

---

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

---

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

---

## Idempotency

All `POST`, `PUT`, `PATCH`, and `DELETE` endpoints require an `X-Idempotency-Key` header:

```
X-Idempotency-Key: <ulid>
```

Duplicate requests with the same key return the cached response with `X-Idempotent-Replay: true`.

---

## Webhooks

Subscribe to website optimization events:

| Event | Description |
|-------|-------------|
| `page.created` | New page created |
| `page.updated` | Page updated |
| `experiment.created` | New A/B test created |
| `experiment.started` | A/B test started |
| `experiment.completed` | A/B test completed with results |
| `experiment.winner_declared` | Winning variant declared |
| `personalization.rule_created` | New personalization rule created |
| `analytics.threshold_crossed` | Analytics threshold crossed |

**Webhook Payload:**

```json
{
  "event": "experiment.completed",
  "timestamp": "2026-10-01T00:00:00Z",
  "data": {
    "experiment_id": "ab_001",
    "winner": "treatment",
    "confidence": 0.97,
    "improvement": 0.33
  }
}
```
