# Social Media Manager API Reference

> Last updated: 2026-10-02 | Base URL: `https://a2zsoc.com`

Manage social media posts, schedule content, track engagement, and analyze performance across multiple platforms.

---

## Table of Contents

- [Overview](#overview)
- [Endpoints](#endpoints)
  - [GET /health](#get-health)
  - [GET /api/v1/agents](#get-api-v1-agents)
  - [POST /api/v1/agents/{agent_name}/invoke](#post-api-v1-agents-agent_name-invoke)
  - [POST /api/v1/posts](#post-api-v1-posts)
  - [GET /api/v1/posts](#get-api-v1-posts)
  - [GET /api/v1/posts/{post_id}](#get-api-v1-posts-post_id)
  - [PATCH /api/v1/posts/{post_id}/status](#patch-api-v1-posts-post_id-status)
  - [DELETE /api/v1/posts/{post_id}](#delete-api-v1-posts-post_id)
  - [GET /api/v1/analytics](#get-api-v1-analytics)
  - [GET /api/v1/analytics/{platform}](#get-api-v1-analytics-platform)
- [Error Codes](#error-codes)
- [Rate Limiting](#rate-limiting)
- [Pagination](#pagination)
- [Authentication](#authentication)
- [Idempotency](#idempotency)

---

## Overview

The Social Media Manager API provides programmatic access to manage social media posts, schedule content, track engagement, and analyze performance across Twitter, Instagram, Facebook, LinkedIn, and TikTok.

**Base Path:** `/api/v1`

All endpoints require authentication via Bearer token and tenant scoping.

---

## Endpoints

### GET /health

Health check endpoint for liveness and readiness probes.

**Response (200):**

```json
{
  "status": "ok",
  "version": "0.1.0",
  "environment": "production"
}
```

**Example:**

```bash
curl -X GET https://a2zsoc.com/health
```

---

### GET /api/v1/agents

List all registered agents and their descriptions.

**Response (200):**

```json
{
  "agents": [
    {"name": "content_creation", "description": "Generate social media content"},
    {"name": "scheduling", "description": "Schedule posts for optimal timing"},
    {"name": "engagement", "description": "Manage audience engagement"},
    {"name": "social_listening", "description": "Monitor brand mentions and trends"},
    {"name": "influencer_identification", "description": "Identify relevant influencers"},
    {"name": "performance_analytics", "description": "Analyze post performance"}
  ]
}
```

**Example:**

```bash
curl -X GET https://a2zsoc.com/api/v1/agents \
  -H "Authorization: Bearer ***"
```

---

### POST /api/v1/agents/{agent_name}/invoke

Invoke a named agent with a JSON payload.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `agent_name` | string | Yes | Agent identifier |

**Request Body:**

```json
{
  "payload": {}
}
```

**Response (200):**

```json
{
  "agent": "content_creation",
  "success": true,
  "data": {},
  "error": null,
  "duration_ms": 150.0
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/agents/content_creation/invoke \
  -H "Authorization: Bearer ***" \
  -H "Content-Type: application/json" \
  -d '{"payload": {"topic": "product launch"}}'
```

---

### POST /api/v1/posts

Create a new social media post.

**Request Body:**

```json
{
  "platform": "twitter",
  "content": "Excited to announce our new product! #innovation",
  "scheduled_at": "2026-10-05T14:00:00Z",
  "hashtags": ["innovation", "product"],
  "metadata": {"campaign_id": "camp_001"}
}
```

**Response (201):**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "platform": "twitter",
  "content": "Excited to announce our new product! #innovation",
  "scheduled_at": "2026-10-05T14:00:00Z",
  "hashtags": ["innovation", "product"],
  "metadata": {"campaign_id": "camp_001"},
  "status": "scheduled",
  "created_at": "2026-10-02T10:00:00Z",
  "updated_at": "2026-10-02T10:00:00Z"
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/posts \
  -H "Authorization: Bearer ***" \
  -H "Content-Type: application/json" \
  -H "X-Idempotency-Key: 01J0ABC1234567890" \
  -d '{"platform": "twitter", "content": "Hello world!"}'
```

---

### GET /api/v1/posts

List posts with pagination, newest first.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `limit` | integer | No | Maximum posts to return (default: 50, max: 200) |
| `offset` | integer | No | Number of posts to skip (default: 0) |

**Response (200):**

```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "platform": "twitter",
      "content": "Hello world!",
      "status": "published",
      "created_at": "2026-10-02T10:00:00Z"
    }
  ],
  "total": 1,
  "limit": 50,
  "offset": 0
}
```

**Example:**

```bash
curl -X GET "https://a2zsoc.com/api/v1/posts?limit=20&offset=0" \
  -H "Authorization: Bearer ***"
```

---

### GET /api/v1/posts/{post_id}

Fetch a single post by ID.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `post_id` | string | Yes | Post identifier |

**Response (200):**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "platform": "twitter",
  "content": "Hello world!",
  "status": "published",
  "created_at": "2026-10-02T10:00:00Z"
}
```

**Example:**

```bash
curl -X GET https://a2zsoc.com/api/v1/posts/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer ***"
```

---

### PATCH /api/v1/posts/{post_id}/status

Transition a post to a new lifecycle status.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `post_id` | string | Yes | Post identifier |
| `new_status` | string | Yes | New status: `draft`, `scheduled`, `published`, `failed` |

**Response (200):**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "platform": "twitter",
  "content": "Hello world!",
  "status": "published",
  "updated_at": "2026-10-02T11:00:00Z"
}
```

**Example:**

```bash
curl -X PATCH "https://a2zsoc.com/api/v1/posts/550e8400-e29b-41d4-a716-446655440000/status?new_status=published" \
  -H "Authorization: Bearer ***"
```

---

### DELETE /api/v1/posts/{post_id}

Delete a post.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `post_id` | string | Yes | Post identifier |

**Example:**

```bash
curl -X DELETE https://a2zsoc.com/api/v1/posts/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer ***" \
  -H "X-Idempotency-Key: 01J0ABC1234567890"
```

---

### GET /api/v1/analytics

Return an analytics overview aggregated across all platforms.

**Response (200):**

```json
{
  "total_posts": 150,
  "posts_by_platform": {
    "twitter": 50,
    "instagram": 40,
    "facebook": 30,
    "linkedin": 20,
    "tiktok": 10
  },
  "posts_by_status": {
    "published": 120,
    "scheduled": 20,
    "draft": 10
  },
  "platforms_tracked": ["facebook", "instagram", "linkedin", "tiktok", "twitter"]
}
```

**Example:**

```bash
curl -X GET https://a2zsoc.com/api/v1/analytics \
  -H "Authorization: Bearer ***"
```

---

### GET /api/v1/analytics/{platform}

Return performance metrics for a specific platform.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `platform` | string | Yes | Platform name: `twitter`, `instagram`, `facebook`, `linkedin`, `tiktok` |

**Response (200):**

```json
{
  "platform": "twitter",
  "total_posts": 50,
  "total_impressions": 100000,
  "total_likes": 5000,
  "total_comments": 1000,
  "total_shares": 500,
  "engagement_rate": 0.065
}
```

**Example:**

```bash
curl -X GET https://a2zsoc.com/api/v1/analytics/twitter \
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

List endpoints support offset-based pagination:

```typescript
interface PaginatedResponse<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
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
