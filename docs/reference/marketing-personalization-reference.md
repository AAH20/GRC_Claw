# Marketing Personalization API Reference

> Last updated: 2026-10-02 | Base URL: `https://a2zsoc.com`

Personalize marketing content and experiences based on customer behavior, preferences, and segments.

---

## Table of Contents

- [Overview](#overview)
- [Endpoints](#endpoints)
  - [POST /api/v1/personalization/segments](#post--api-v1-personalization-segments)
  - [GET /api/v1/personalization/segments](#get--api-v1-personalization-segments)
  - [GET /api/v1/personalization/segments/{seg}](#get--api-v1-personalization-segments-seg)
  - [PUT /api/v1/personalization/segments/{seg}](#put--api-v1-personalization-segments-seg)
  - [DELETE /api/v1/personalization/segments/{seg}](#delete--api-v1-personalization-segments-seg)
  - [POST /api/v1/personalization/campaigns](#post--api-v1-personalization-campaigns)
  - [POST /api/v1/personalization/content](#post--api-v1-personalization-content)
- [Error Codes](#error-codes)
- [Rate Limiting](#rate-limiting)
- [Pagination](#pagination)
- [Authentication](#authentication)
- [Idempotency](#idempotency)

---

## Overview

The Marketing Personalization API provides programmatic access to personalize marketing content and experiences based on customer behavior, preferences, and segments.

**Base Path:** `/api/v1/personalization`

All endpoints require authentication via Bearer token and tenant scoping.

---

## Endpoints


### POST /api/v1/personalization/segments

Create a new segment.

**Request Body:**

```json
{
  "name": "New Segment",
  "description": "A segment"
}
```

**Response (201):**

```json
{
  "id": "seg_001",
  "name": "New Segment",
  "status": "active",
  "created_at": "2026-10-01T00:00:00Z"
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/personalization/segments \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -H "X-Idempotency-Key: 01J0ABC1234567890" \
  -d '{"name": "New Segment"}'
```


### GET /api/v1/personalization/segments

List all segments.

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
      "id": "seg_001",
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
curl -X GET "https://a2zsoc.com/api/v1/personalization/segments" \
  -H "Authorization: Bearer <token>"
```


### GET /api/v1/personalization/segments/{seg}

Get a segment by ID.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `seg` | string | Yes | Segment identifier |

**Response (200):**

```json
{
  "id": "seg_001",
  "name": "Example",
  "status": "active"
}
```

**Example:**

```bash
curl -X GET https://a2zsoc.com/api/v1/personalization/segments/seg_001 \
  -H "Authorization: Bearer <token>"
```


### PUT /api/v1/personalization/segments/{seg}

Update a segment.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `seg` | string | Yes | Segment identifier |

**Request Body:**

```json
{
  "name": "Updated Name"
}
```

**Response (200):**

```json
{
  "id": "seg_001",
  "name": "Updated Name",
  "status": "active"
}
```

**Example:**

```bash
curl -X PUT https://a2zsoc.com/api/v1/personalization/segments/seg_001 \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "Updated Name"}'
```


### DELETE /api/v1/personalization/segments/{seg}

Delete a segment.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `seg` | string | Yes | Segment identifier |

**Example:**

```bash
curl -X DELETE https://a2zsoc.com/api/v1/personalization/segments/seg_001 \
  -H "Authorization: Bearer <token>" \
  -H "X-Idempotency-Key: 01J0ABC1234567890"
```


### POST /api/v1/personalization/campaigns

Create a personalized marketing campaign.

**Request Body:**

```json
{
  "name": "Personalized Product Launch",
  "segment_id": "seg_001",
  "channels": [
    "email",
    "push"
  ],
  "personalization_rules": {
    "product_recommendations": true,
    "dynamic_content": true
  }
}
```

**Response (201):**

```json
{
  "campaign_id": "pers_camp_001",
  "name": "Personalized Product Launch",
  "status": "active",
  "segment_id": "seg_001",
  "created_at": "2026-10-01T00:00:00Z"
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/personalization/campaigns \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "Personalized Launch", "segment_id": "seg_001"}'
```


### POST /api/v1/personalization/content

Generate personalized content for a customer.

**Request Body:**

```json
{
  "customer_id": "cust_001",
  "content_type": "email",
  "context": "product_recommendation"
}
```

**Response (201):**

```json
{
  "content_id": "pers_content_001",
  "customer_id": "cust_001",
  "content": "Hi John, based on your interest in technology...",
  "personalization_tokens": {
    "name": "John",
    "interests": [
      "technology"
    ]
  }
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/personalization/content \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"customer_id": "cust_001", "content_type": "email"}'
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
