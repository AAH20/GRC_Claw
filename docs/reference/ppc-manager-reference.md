# PPC Manager API Reference

> Last updated: 2026-10-02 | Base URL: `https://a2zsoc.com`

Manage PPC campaigns, keywords, bids, and budgets across Google Ads, Meta Ads, LinkedIn Ads, and TikTok Ads.

---

## Table of Contents

- [Overview](#overview)
- [Endpoints](#endpoints)
  - [GET /health](#get-health)
  - [GET /metrics](#get-metrics)
  - [POST /api/v1/campaigns](#post-api-v1-campaigns)
  - [GET /api/v1/campaigns](#get-api-v1-campaigns)
  - [GET /api/v1/campaigns/{campaign_id}](#get-api-v1-campaigns-campaign_id)
  - [PUT /api/v1/campaigns/{campaign_id}](#put-api-v1-campaigns-campaign_id)
  - [DELETE /api/v1/campaigns/{campaign_id}](#delete-api-v1-campaigns-campaign_id)
  - [GET /api/v1/keywords](#get-api-v1-keywords)
  - [POST /api/v1/keywords/research](#post-api-v1-keywords-research)
- [Error Codes](#error-codes)
- [Rate Limiting](#rate-limiting)
- [Pagination](#pagination)
- [Authentication](#authentication)
- [Idempotency](#idempotency)

---

## Overview

The PPC Manager API provides programmatic access to manage PPC campaigns, keywords, bids, and budgets across Google Ads, Meta Ads, LinkedIn Ads, and TikTok Ads.

**Base Path:** `/api/v1`

All endpoints require authentication via Bearer token and tenant scoping.

---

## Endpoints

### GET /health

Health check endpoint.

**Response (200):**

```json
{
  "status": "ok",
  "service": "ppc-manager"
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
http_requests_total{method="GET",endpoint="/api/v1/campaigns",status="200"} 42
```

**Example:**

```bash
curl -X GET https://a2zsoc.com/metrics
```

---

### POST /api/v1/campaigns

Create a new PPC campaign.

**Request Body:**

```json
{
  "name": "Q4 Product Launch",
  "platform": "google",
  "budget": 100.00,
  "status": "active"
}
```

**Response (201):**

```json
{
  "id": "campaign_1",
  "name": "Q4 Product Launch",
  "platform": "google",
  "budget": 100.00,
  "status": "active",
  "created_at": "2026-10-02T10:00:00Z"
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/campaigns \
  -H "Authorization: Bearer ***" \
  -H "Content-Type: application/json" \
  -H "X-Idempotency-Key: 01J0ABC1234567890" \
  -d '{"name": "Q4 Product Launch", "platform": "google", "budget": 100.00}'
```

---

### GET /api/v1/campaigns

List all campaigns.

**Response (200):**

```json
[
  {
    "id": "campaign_1",
    "name": "Q4 Product Launch",
    "platform": "google",
    "budget": 100.00,
    "status": "active",
    "created_at": "2026-10-02T10:00:00Z"
  }
]
```

**Example:**

```bash
curl -X GET https://a2zsoc.com/api/v1/campaigns \
  -H "Authorization: Bearer ***"
```

---

### GET /api/v1/campaigns/{campaign_id}

Get a campaign by ID.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `campaign_id` | string | Yes | Campaign identifier |

**Response (200):**

```json
{
  "id": "campaign_1",
  "name": "Q4 Product Launch",
  "platform": "google",
  "budget": 100.00,
  "status": "active",
  "created_at": "2026-10-02T10:00:00Z"
}
```

**Example:**

```bash
curl -X GET https://a2zsoc.com/api/v1/campaigns/campaign_1 \
  -H "Authorization: Bearer ***"
```

---

### PUT /api/v1/campaigns/{campaign_id}

Update a campaign.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `campaign_id` | string | Yes | Campaign identifier |

**Request Body:**

```json
{
  "name": "Updated Campaign Name",
  "budget": 150.00,
  "status": "paused"
}
```

**Response (200):**

```json
{
  "id": "campaign_1",
  "name": "Updated Campaign Name",
  "platform": "google",
  "budget": 150.00,
  "status": "paused",
  "created_at": "2026-10-02T10:00:00Z"
}
```

**Example:**

```bash
curl -X PUT https://a2zsoc.com/api/v1/campaigns/campaign_1 \
  -H "Authorization: Bearer ***" \
  -H "Content-Type: application/json" \
  -d '{"name": "Updated Campaign Name", "budget": 150.00}'
```

---

### DELETE /api/v1/campaigns/{campaign_id}

Delete a campaign.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `campaign_id` | string | Yes | Campaign identifier |

**Example:**

```bash
curl -X DELETE https://a2zsoc.com/api/v1/campaigns/campaign_1 \
  -H "Authorization: Bearer ***" \
  -H "X-Idempotency-Key: 01J0ABC1234567890"
```

---

### GET /api/v1/keywords

List keywords, optionally filtered by campaign.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `campaign_id` | string | No | Filter by campaign ID |

**Response (200):**

```json
[
  {
    "keyword": "ppc management software",
    "search_volume": 5000,
    "competition": "high",
    "cpc_estimate": 5.50,
    "relevance_score": 0.95,
    "intent": "commercial"
  }
]
```

**Example:**

```bash
curl -X GET "https://a2zsoc.com/api/v1/keywords?campaign_id=campaign_1" \
  -H "Authorization: Bearer ***"
```

---

### POST /api/v1/keywords/research

Run keyword research from a seed keyword.

**Request Body:**

```json
{
  "seed_keyword": "ppc management",
  "language": "en",
  "location": "US"
}
```

**Response (200):**

```json
[
  {
    "keyword": "ppc management software",
    "search_volume": 5000,
    "competition": "high",
    "cpc_estimate": 5.50,
    "relevance_score": 0.95,
    "intent": "commercial"
  },
  {
    "keyword": "best ppc tools",
    "search_volume": 3000,
    "competition": "medium",
    "cpc_estimate": 4.20,
    "relevance_score": 0.88,
    "intent": "commercial"
  }
]
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/keywords/research \
  -H "Authorization: Bearer ***" \
  -H "Content-Type: application/json" \
  -d '{"seed_keyword": "ppc management", "language": "en", "location": "US"}'
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
