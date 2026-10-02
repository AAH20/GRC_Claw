# Market Research API Reference

> Last updated: 2026-10-02 | Base URL: `https://a2zsoc.com` | Version: `0.1.0`

AI-powered market research with data collection, analysis, and competitive intelligence. Integrates with Statista and IBISWorld for comprehensive market data.

---

## Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [Endpoints](#endpoints)
  - [Research Tasks](#research-tasks)
    - [POST /api/v1/research](#post--api-v1-research)
    - [GET /api/v1/research/{task_id}](#get--api-v1-research-task_id)
    - [POST /api/v1/research/{task_id}/collect](#post--api-v1-research-task_id-collect)
    - [POST /api/v1/research/{task_id}/analyze](#post--api-v1-research-task_id-analyze)
    - [GET /api/v1/research/tasks](#get--api-v1-research-tasks)
  - [Data Sources](#data-sources)
    - [GET /api/v1/research/sources](#get--api-v1-research-sources)
- [Error Codes](#error-codes)
- [Rate Limiting](#rate-limiting)
- [Pagination](#pagination)
- [Idempotency](#idempotency)
- [Webhooks](#webhooks)

---

## Overview

The Market Research API provides programmatic access to AI-powered market research with data collection, analysis, and competitive intelligence.

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

### Research Tasks

#### POST /api/v1/research

Start a new market research task.

**Request Body:**

```json
{
  "query": "project management software market",
  "sources": ["web", "social", "news"],
  "analysis_types": ["trends", "competitors", "sentiment"],
  "date_range_start": "2026-01-01T00:00:00Z",
  "date_range_end": "2026-10-01T00:00:00Z",
  "filters": {
    "region": "global",
    "industry": "software",
    "company_size": "enterprise"
  }
}
```

**Response (202):**

```json
{
  "task_id": "research_001",
  "status": "pending",
  "message": "Research task created successfully",
  "created_at": "2026-10-01T00:00:00Z"
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/research \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -H "X-Idempotency-Key: 01J0ABC1234567890" \
  -d '{"query": "project management software market"}'
```

---

#### GET /api/v1/research/{task_id}

Get the status of a research task.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `task_id` | string | Yes | Task identifier |

**Response (200):**

```json
{
  "task_id": "research_001",
  "status": "completed",
  "progress": 1.0,
  "collection_result": {
    "data_points": 500,
    "sources": ["web", "social", "news"],
    "errors": []
  },
  "analysis_result": {
    "insights": [
      "Market growing at 15% annually",
      "Key competitors: A, B, C",
      "Mid-market segment shows highest growth"
    ],
    "recommendations": [
      "Focus on mid-market segment",
      "Differentiate on integrations"
    ],
    "trends": {
      "market_size": {"value": 5000000000, "unit": "USD", "growth_rate": 0.15},
      "adoption_rate": {"value": 0.35, "growth_rate": 0.08}
    },
    "competitors": [
      {"name": "Competitor A", "market_share": 0.30, "strengths": ["brand", "features"]}
    ],
    "sentiment": {"positive": 0.60, "neutral": 0.25, "negative": 0.15}
  },
  "error": null,
  "created_at": "2026-10-01T00:00:00Z",
  "completed_at": "2026-10-01T00:05:00Z"
}
```

**Example:**

```bash
curl -X GET https://a2zsoc.com/api/v1/research/research_001 \
  -H "Authorization: Bearer <token>"
```

---

#### POST /api/v1/research/{task_id}/collect

Execute data collection for a research task.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `task_id` | string | Yes | Task identifier |

**Response (200):**

```json
{
  "status": "collected",
  "data_points": 500,
  "sources": ["web", "social", "news"],
  "errors": [],
  "metadata": {
    "collection_duration_seconds": 120,
    "sources_queried": 3,
    "data_quality_score": 0.85
  }
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/research/research_001/collect \
  -H "Authorization: Bearer <token>"
```

---

#### POST /api/v1/research/{task_id}/analyze

Execute analysis for a research task.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `task_id` | string | Yes | Task identifier |

**Response (200):**

```json
{
  "insights": [
    "Market growing at 15% annually",
    "Key competitors: A, B, C",
    "Mid-market segment shows highest growth"
  ],
  "recommendations": [
    "Focus on mid-market segment",
    "Differentiate on integrations",
    "Invest in AI-powered features"
  ],
  "trends": {
    "market_size": {"value": 5000000000, "unit": "USD", "growth_rate": 0.15},
    "adoption_rate": {"value": 0.35, "growth_rate": 0.08},
    "average_price": {"value": 500, "unit": "USD", "growth_rate": -0.03}
  },
  "competitors": [
    {
      "name": "Competitor A",
      "market_share": 0.30,
      "strengths": ["brand recognition", "feature set"],
      "weaknesses": ["pricing", "user experience"]
    }
  ],
  "sentiment": {
    "positive": 0.60,
    "neutral": 0.25,
    "negative": 0.15,
    "key_themes": ["ease of use", "integrations", "customer support"]
  }
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/research/research_001/analyze \
  -H "Authorization: Bearer <token>"
```

---

#### GET /api/v1/research/tasks

List all research task IDs.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `status` | string | No | Filter by status: `pending`, `collecting`, `collected`, `analyzing`, `completed`, `failed` |
| `cursor` | string | No | Pagination cursor |
| `limit` | integer | No | Items per page (default: 20, max: 100) |

**Response (200):**

```json
{
  "data": [
    {
      "task_id": "research_001",
      "status": "completed",
      "query": "project management software market",
      "created_at": "2026-10-01T00:00:00Z",
      "completed_at": "2026-10-01T00:05:00Z"
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
curl -X GET "https://a2zsoc.com/api/v1/research/tasks?status=completed" \
  -H "Authorization: Bearer <token>"
```

---

### Data Sources

#### GET /api/v1/research/sources

List available data sources.

**Response (200):**

```json
{
  "sources": [
    {
      "id": "web",
      "name": "Web Search",
      "description": "General web search results",
      "status": "available"
    },
    {
      "id": "social",
      "name": "Social Media",
      "description": "Social media mentions and discussions",
      "status": "available"
    },
    {
      "id": "news",
      "name": "News API",
      "description": "News articles and press releases",
      "status": "available"
    },
    {
      "id": "statista",
      "name": "Statista",
      "description": "Market statistics and industry data",
      "status": "available"
    },
    {
      "id": "ibisworld",
      "name": "IBISWorld",
      "description": "Industry research reports",
      "status": "available"
    }
  ]
}
```

**Example:**

```bash
curl -X GET https://a2zsoc.com/api/v1/research/sources \
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

Subscribe to research task events:

| Event | Description |
|-------|-------------|
| `research.task_created` | New research task created |
| `research.collection_started` | Data collection started |
| `research.collection_completed` | Data collection completed |
| `research.analysis_started` | Analysis started |
| `research.analysis_completed` | Analysis completed |
| `research.task_failed` | Research task failed |

**Webhook Payload:**

```json
{
  "event": "research.analysis_completed",
  "timestamp": "2026-10-01T00:05:00Z",
  "data": {
    "task_id": "research_001",
    "status": "completed",
    "insights_count": 3
  }
}
```
