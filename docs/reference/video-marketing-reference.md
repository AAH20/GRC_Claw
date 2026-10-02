# Video Marketing API Reference

> Last updated: 2026-10-02 | Base URL: `https://a2zsoc.com`

Create, manage, and optimize video marketing content across platforms.

---

## Table of Contents

- [Overview](#overview)
- [Endpoints](#endpoints)
  - [POST /api/v1/video/videos](#post--api-v1-video-videos)
  - [GET /api/v1/video/videos](#get--api-v1-video-videos)
  - [GET /api/v1/video/videos/{vid}](#get--api-v1-video-videos-vid)
  - [PUT /api/v1/video/videos/{vid}](#put--api-v1-video-videos-vid)
  - [DELETE /api/v1/video/videos/{vid}](#delete--api-v1-video-videos-vid)
  - [POST /api/v1/video/generate](#post--api-v1-video-generate)
  - [GET /api/v1/video/{video_id}/analytics](#get--api-v1-video-video-id-analytics)
- [Error Codes](#error-codes)
- [Rate Limiting](#rate-limiting)
- [Pagination](#pagination)
- [Authentication](#authentication)
- [Idempotency](#idempotency)

---

## Overview

The Video Marketing API provides programmatic access to create, manage, and optimize video marketing content across platforms.

**Base Path:** `/api/v1/video`

All endpoints require authentication via Bearer token and tenant scoping.

---

## Endpoints


### POST /api/v1/video/videos

Create a new video.

**Request Body:**

```json
{
  "name": "New Video",
  "description": "A video"
}
```

**Response (201):**

```json
{
  "id": "vid_001",
  "name": "New Video",
  "status": "active",
  "created_at": "2026-10-01T00:00:00Z"
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/video/videos \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -H "X-Idempotency-Key: 01J0ABC1234567890" \
  -d '{"name": "New Video"}'
```


### GET /api/v1/video/videos

List all videos.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `page` | integer | No | Page number |
| `page_size` | integer | No | Items per page |

**Response (200):**

```json
{
  "data": [
    {
      "id": "vid_001",
      "name": "Example"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20
}
```

**Example:**

```bash
curl -X GET "https://a2zsoc.com/api/v1/video/videos" \
  -H "Authorization: Bearer <token>"
```


### GET /api/v1/video/videos/{vid}

Get a video by ID.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `vid` | string | Yes | Video identifier |

**Response (200):**

```json
{
  "id": "vid_001",
  "name": "Example",
  "status": "active"
}
```

**Example:**

```bash
curl -X GET https://a2zsoc.com/api/v1/video/videos/vid_001 \
  -H "Authorization: Bearer <token>"
```


### PUT /api/v1/video/videos/{vid}

Update a video.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `vid` | string | Yes | Video identifier |

**Request Body:**

```json
{
  "name": "Updated Name"
}
```

**Response (200):**

```json
{
  "id": "vid_001",
  "name": "Updated Name",
  "status": "active"
}
```

**Example:**

```bash
curl -X PUT https://a2zsoc.com/api/v1/video/videos/vid_001 \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "Updated Name"}'
```


### DELETE /api/v1/video/videos/{vid}

Delete a video.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `vid` | string | Yes | Video identifier |

**Example:**

```bash
curl -X DELETE https://a2zsoc.com/api/v1/video/videos/vid_001 \
  -H "Authorization: Bearer <token>" \
  -H "X-Idempotency-Key: 01J0ABC1234567890"
```


### POST /api/v1/video/generate

Generate a video from a script or template.

**Request Body:**

```json
{
  "script": "Welcome to our product demo...",
  "template": "product_demo",
  "duration_seconds": 60,
  "aspect_ratio": "16:9"
}
```

**Response (202):**

```json
{
  "video_id": "vid_gen_001",
  "status": "rendering",
  "estimated_completion": "2026-10-01T00:05:00Z"
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/video/generate \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"script": "Welcome...", "template": "product_demo"}'
```


### GET /api/v1/video/{video_id}/analytics

Get video performance analytics.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `video_id` | string | Yes | Video identifier |

**Response (200):**

```json
{
  "video_id": "vid_001",
  "views": 50000,
  "avg_watch_time": 45,
  "completion_rate": 0.65,
  "engagement_rate": 0.08
}
```

**Example:**

```bash
curl -X GET https://a2zsoc.com/api/v1/video/vid_001/analytics \
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
