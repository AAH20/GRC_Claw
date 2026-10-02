# Brand Monitoring API Reference

> Last updated: 2026-10-02 | Base URL: `https://a2zsoc.com` | Version: `0.1.0`

AI-powered brand monitoring with multi-agent architecture. Monitor brand mentions, sentiment, and reputation across Twitter, Reddit, and NewsAPI.

---

## Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [Endpoints](#endpoints)
  - [Mentions](#mentions)
    - [GET /api/v1/mentions](#get--api-v1-mentions)
    - [GET /api/v1/mentions/{mention_id}](#get--api-v1-mentions-mention_id)
  - [Sentiment](#sentiment)
    - [GET /api/v1/brand/sentiment](#get--api-v1-brand-sentiment)
    - [GET /api/v1/mentions/sentiment](#get--api-v1-mentions-sentiment)
  - [Reports](#reports)
    - [POST /api/v1/reports](#post--api-v1-reports)
    - [GET /api/v1/reports](#get--api-v1-reports)
    - [GET /api/v1/reports/{report_id}](#get--api-v1-reports-report_id)
  - [Reputation](#reputation)
    - [GET /api/v1/brand/reputation](#get--api-v1-brand-reputation)
  - [Health](#health)
    - [GET /api/v1/health](#get--api-v1-health)
- [Error Codes](#error-codes)
- [Rate Limiting](#rate-limiting)
- [Pagination](#pagination)
- [Idempotency](#idempotency)
- [Webhooks](#webhooks)

---

## Overview

The Brand Monitoring API provides programmatic access to monitor brand mentions, sentiment, and reputation across social media, news, and review sites.

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

### Mentions

#### GET /api/v1/mentions

Get brand mentions across platforms.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `platform` | string | No | Filter by platform: `twitter`, `reddit`, `newsapi` |
| `sentiment` | string | No | Filter by sentiment: `positive`, `negative`, `neutral` |
| `mention_type` | string | No | Filter by type: `post`, `comment`, `article`, `review` |
| `start_date` | string | No | Filter by start date (ISO 8601) |
| `end_date` | string | No | Filter by end date (ISO 8601) |
| `query` | string | No | Search query filter |
| `cursor` | string | No | Pagination cursor |
| `limit` | integer | No | Items per page (default: 20, max: 100) |

**Response (200):**

```json
{
  "data": [
    {
      "mention_id": "mention_001",
      "platform": "twitter",
      "mention_type": "post",
      "content": "Love this brand! Best product I've ever used.",
      "author": "user123",
      "url": "https://twitter.com/user123/status/123456",
      "sentiment": "positive",
      "sentiment_score": 0.92,
      "created_at": "2026-10-01T12:00:00Z",
      "metadata": {
        "followers": 5000,
        "likes": 120,
        "retweets": 45
      }
    }
  ],
  "pagination": {
    "cursor": "eyJpZCI6Im1lbnRpb25fMDAxIn0=",
    "hasMore": true,
    "totalCount": 500
  }
}
```

**Example:**

```bash
curl -X GET "https://a2zsoc.com/api/v1/mentions?platform=twitter&sentiment=positive" \
  -H "Authorization: Bearer <token>"
```

---

#### GET /api/v1/mentions/{mention_id}

Get a specific mention by ID.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `mention_id` | string | Yes | Mention identifier |

**Response (200):**

```json
{
  "mention_id": "mention_001",
  "platform": "twitter",
  "mention_type": "post",
  "content": "Love this brand! Best product I've ever used.",
  "author": "user123",
  "url": "https://twitter.com/user123/status/123456",
  "sentiment": "positive",
  "sentiment_score": 0.92,
  "created_at": "2026-10-01T12:00:00Z",
  "metadata": {
    "followers": 5000,
    "likes": 120,
    "retweets": 45,
    "replies": 12
  }
}
```

**Example:**

```bash
curl -X GET https://a2zsoc.com/api/v1/mentions/mention_001 \
  -H "Authorization: Bearer <token>"
```

---

### Sentiment

#### GET /api/v1/brand/sentiment

Get overall brand sentiment score.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `start_date` | string | No | Start date (ISO 8601) |
| `end_date` | string | No | End date (ISO 8601) |
| `platform` | string | No | Filter by platform |

**Response (200):**

```json
{
  "overall_sentiment": 0.75,
  "positive": 0.65,
  "neutral": 0.20,
  "negative": 0.15,
  "trend": "improving",
  "total_mentions": 5000,
  "period": {"start": "2026-09-01", "end": "2026-09-30"},
  "by_platform": [
    {"platform": "twitter", "sentiment": 0.78, "mentions": 3000},
    {"platform": "reddit", "sentiment": 0.70, "mentions": 1500},
    {"platform": "newsapi", "sentiment": 0.72, "mentions": 500}
  ],
  "top_positive_themes": ["customer service", "product quality", "innovation"],
  "top_negative_themes": ["pricing", "shipping delays", "bugs"]
}
```

**Example:**

```bash
curl -X GET "https://a2zsoc.com/api/v1/brand/sentiment?start_date=2026-09-01" \
  -H "Authorization: Bearer <token>"
```

---

#### GET /api/v1/mentions/sentiment

Get sentiment breakdown for mentions.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `start_date` | string | No | Start date (ISO 8601) |
| `end_date` | string | No | End date (ISO 8601) |

**Response (200):**

```json
{
  "positive": 0.65,
  "neutral": 0.25,
  "negative": 0.10,
  "total_responses": 1000,
  "average_score": 0.72,
  "sentiment_distribution": [
    {"range": "0.8-1.0", "count": 650},
    {"range": "0.6-0.8", "count": 200},
    {"range": "0.4-0.6", "count": 100},
    {"range": "0.2-0.4", "count": 30},
    {"range": "0.0-0.2", "count": 20}
  ]
}
```

**Example:**

```bash
curl -X GET https://a2zsoc.com/api/v1/mentions/sentiment \
  -H "Authorization: Bearer <token>"
```

---

### Reports

#### POST /api/v1/reports

Generate a brand monitoring report.

**Request Body:**

```json
{
  "name": "Weekly Brand Report",
  "description": "Weekly brand mention and sentiment analysis",
  "period": {"start": "2026-09-01", "end": "2026-09-30"},
  "platforms": ["twitter", "reddit", "newsapi"],
  "include_mentions": true,
  "include_sentiment": true,
  "include_reputation": true,
  "format": "pdf"
  "schedule": "weekly"
}
```

**Response (202):**

```json
{
  "report_id": "report_001",
  "name": "Weekly Brand Report",
  "status": "generating",
  "created_at": "2026-10-01T00:00:00Z"
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/reports \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "Weekly Report", "format": "pdf"}'
```

---

#### GET /api/v1/reports

List all reports.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `status` | string | No | Filter by status: `generating`, `completed`, `failed` |
| `cursor` | string | No | Pagination cursor |
| `limit` | integer | No | Items per page (default: 20, max: 100) |

**Response (200):**

```json
{
  "data": [
    {
      "report_id": "report_001",
      "name": "Weekly Brand Report",
      "status": "completed",
      "format": "pdf",
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
curl -X GET "https://a2zsoc.com/api/v1/reports?status=completed" \
  -H "Authorization: Bearer <token>"
```

---

#### GET /api/v1/reports/{report_id}

Get a report by ID.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `report_id` | string | Yes | Report identifier |

**Response (200):**

```json
{
  "report_id": "report_001",
  "name": "Weekly Brand Report",
  "status": "completed",
  "format": "pdf",
  "download_url": "https://a2zsoc.com/downloads/report_001.pdf",
  "period": {"start": "2026-09-01", "end": "2026-09-30"},
  "created_at": "2026-10-01T00:00:00Z",
  "completed_at": "2026-10-01T00:05:00Z"
}
```

**Example:**

```bash
curl -X GET https://a2zsoc.com/api/v1/reports/report_001 \
  -H "Authorization: Bearer <token>"
```

---

### Reputation

#### GET /api/v1/brand/reputation

Get brand reputation metrics.

**Response (200):**

```json
{
  "reputation_score": 85,
  "review_average": 4.5,
  "total_reviews": 1200,
  "response_rate": 0.92,
  "response_time_hours": 4.5,
  "platform_breakdown": [
    {"platform": "google", "average": 4.6, "count": 800},
    {"platform": "trustpilot", "average": 4.3, "count": 300},
    {"platform": "yelp", "average": 4.2, "count": 100}
  ],
  "trend": "stable",
  "last_updated": "2026-10-01T00:00:00Z"
}
```

**Example:**

```bash
curl -X GET https://a2zsoc.com/api/v1/brand/reputation \
  -H "Authorization: Bearer <token>"
```

---

### Health

#### GET /api/v1/health

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
curl -X GET https://a2zsoc.com/api/v1/health
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

Subscribe to brand monitoring events:

| Event | Description |
|-------|-------------|
| `mention.created` | New brand mention detected |
| `mention.sentiment_flagged` | Negative sentiment mention detected |
| `sentiment.changed` | Overall sentiment changed significantly |
| `reputation.updated` | Reputation metrics updated |
| `report.completed` | Report generation completed |

**Webhook Payload:**

```json
{
  "event": "mention.created",
  "timestamp": "2026-10-01T00:00:00Z",
  "data": {
    "mention_id": "mention_001",
    "platform": "twitter",
    "sentiment": "positive",
    "content": "Love this brand!"
  }
}
```
