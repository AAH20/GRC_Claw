# Partner Management API Reference

> Last updated: 2026-10-02 | Base URL: `https://a2zsoc.com`

Manage strategic partnerships, co-marketing campaigns, and partner enablement.

---

## Table of Contents

- [Overview](#overview)
- [Endpoints](#endpoints)
  - [POST /api/v1/partners](#post--api-v1-partners)
  - [GET /api/v1/partners](#get--api-v1-partners)
  - [GET /api/v1/partners/{partner}](#get--api-v1-partners-partner)
  - [PUT /api/v1/partners/{partner}](#put--api-v1-partners-partner)
  - [DELETE /api/v1/partners/{partner}](#delete--api-v1-partners-partner)
  - [POST /api/v1/partners/{partner_id}/campaigns](#post--api-v1-partners-partner-id-campaigns)
  - [GET /api/v1/partners/{partner_id}/performance](#get--api-v1-partners-partner-id-performance)
- [Error Codes](#error-codes)
- [Rate Limiting](#rate-limiting)
- [Pagination](#pagination)
- [Authentication](#authentication)
- [Idempotency](#idempotency)

---

## Overview

The Partner Management API provides programmatic access to manage strategic partnerships, co-marketing campaigns, and partner enablement.

**Base Path:** `/api/v1/partners`

All endpoints require authentication via Bearer token and tenant scoping.

---

## Endpoints


### POST /api/v1/partners

Create a new partner.

**Request Body:**

```json
{
  "name": "New Partner",
  "description": "A partner"
}
```

**Response (201):**

```json
{
  "id": "partner_001",
  "name": "New Partner",
  "status": "active",
  "created_at": "2026-10-01T00:00:00Z"
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/partners \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -H "X-Idempotency-Key: 01J0ABC1234567890" \
  -d '{"name": "New Partner"}'
```


### GET /api/v1/partners

List all partners.

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
      "id": "partner_001",
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
curl -X GET "https://a2zsoc.com/api/v1/partners" \
  -H "Authorization: Bearer <token>"
```


### GET /api/v1/partners/{partner}

Get a partner by ID.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `partner` | string | Yes | Partner identifier |

**Response (200):**

```json
{
  "id": "partner_001",
  "name": "Example",
  "status": "active"
}
```

**Example:**

```bash
curl -X GET https://a2zsoc.com/api/v1/partners/partner_001 \
  -H "Authorization: Bearer <token>"
```


### PUT /api/v1/partners/{partner}

Update a partner.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `partner` | string | Yes | Partner identifier |

**Request Body:**

```json
{
  "name": "Updated Name"
}
```

**Response (200):**

```json
{
  "id": "partner_001",
  "name": "Updated Name",
  "status": "active"
}
```

**Example:**

```bash
curl -X PUT https://a2zsoc.com/api/v1/partners/partner_001 \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "Updated Name"}'
```


### DELETE /api/v1/partners/{partner}

Delete a partner.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `partner` | string | Yes | Partner identifier |

**Example:**

```bash
curl -X DELETE https://a2zsoc.com/api/v1/partners/partner_001 \
  -H "Authorization: Bearer <token>" \
  -H "X-Idempotency-Key: 01J0ABC1234567890"
```


### POST /api/v1/partners/{partner_id}/campaigns

Create a co-marketing campaign with a partner.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `partner_id` | string | Yes | Partner identifier |

**Request Body:**

```json
{
  "name": "Joint Webinar",
  "type": "webinar",
  "budget": 5000,
  "split": "50/50"
}
```

**Response (201):**

```json
{
  "campaign_id": "co_camp_001",
  "partner_id": "partner_001",
  "status": "active",
  "created_at": "2026-10-01T00:00:00Z"
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/partners/partner_001/campaigns \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "Joint Webinar", "type": "webinar"}'
```


### GET /api/v1/partners/{partner_id}/performance

Get partner performance metrics.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `partner_id` | string | Yes | Partner identifier |

**Response (200):**

```json
{
  "partner_id": "partner_001",
  "leads_generated": 500,
  "revenue": 25000,
  "roi": 5.0
}
```

**Example:**

```bash
curl -X GET https://a2zsoc.com/api/v1/partners/partner_001/performance \
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
