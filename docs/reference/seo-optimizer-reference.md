# SEO Optimizer API Reference

> Last updated: 2026-10-02 | Base URL: `https://a2zsoc.com`

Optimize content for search engines, research keywords, audit technical SEO, and track rankings.

---

## Table of Contents

- [Overview](#overview)
- [Endpoints](#endpoints)
  - [GET /health](#get-health)
  - [GET /metrics](#get-metrics)
  - [POST /api/v1/keywords/research](#post-api-v1-keywords-research)
  - [GET /api/v1/keywords/{task_id}](#get-api-v1-keywords-task_id)
  - [POST /api/v1/content/optimize](#post-api-v1-content-optimize)
  - [GET /api/v1/content/{task_id}](#get-api-v1-content-task_id)
- [Error Codes](#error-codes)
- [Rate Limiting](#rate-limiting)
- [Pagination](#pagination)
- [Authentication](#authentication)
- [Idempotency](#idempotency)

---

## Overview

The SEO Optimizer API provides programmatic access to optimize content for search engines, research keywords, audit technical SEO, and track rankings.

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
# HELP seo_optimizer_requests_total Total HTTP requests
# TYPE seo_optimizer_requests_total counter
seo_optimizer_requests_total{method="GET",endpoint="/api/v1/keywords",status="200"} 42
```

**Example:**

```bash
curl -X GET https://a2zsoc.com/metrics
```

---

### POST /api/v1/keywords/research

Start a keyword research task.

**Request Body:**

```json
{
  "domain": "example.com",
  "seed_keywords": ["seo tools", "keyword research"],
  "country": "us",
  "max_results": 50,
  "min_search_volume": 100,
  "max_difficulty": 70
}
```

**Response (202):**

```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "result": null
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/keywords/research \
  -H "Authorization: Bearer ***" \
  -H "Content-Type: application/json" \
  -H "X-Idempotency-Key: 01J0ABC1234567890" \
  -d '{"domain": "example.com", "seed_keywords": ["seo tools"]}'
```

---

### GET /api/v1/keywords/{task_id}

Get keyword research results by task ID.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `task_id` | string | Yes | Task identifier |

**Response (200):**

```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "result": {
    "keywords": [
      {
        "keyword": "seo tools",
        "search_volume": 12000,
        "difficulty": 45,
        "cpc": 3.50
      }
    ]
  }
}
```

**Example:**

```bash
curl -X GET https://a2zsoc.com/api/v1/keywords/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer ***"
```

---

### POST /api/v1/content/optimize

Start a content optimization task.

**Request Body:**

```json
{
  "content": "Your article content here...",
  "target_keywords": ["seo optimization", "content marketing"],
  "content_type": "blog_post"
}
```

**Response (202):**

```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440001",
  "status": "pending",
  "result": null
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/content/optimize \
  -H "Authorization: Bearer ***" \
  -H "Content-Type: application/json" \
  -H "X-Idempotency-Key: 01J0ABC1234567890" \
  -d '{"content": "Your article content here...", "target_keywords": ["seo optimization"]}'
```

---

### GET /api/v1/content/{task_id}

Get content optimization results by task ID.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `task_id` | string | Yes | Task identifier |

**Response (200):**

```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440001",
  "status": "completed",
  "result": {
    "score": 85,
    "suggestions": [
      "Add more internal links",
      "Include target keyword in first paragraph"
    ],
    "optimized_content": "..."
  }
}
```

**Example:**

```bash
curl -X GET https://a2zsoc.com/api/v1/content/550e8400-e29b-41d4-a716-446655440001 \
  -H "Authorization: Bearer ***"
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
