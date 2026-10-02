# Affiliate Marketing API Reference

> Last updated: 2026-10-02 | Base URL: `https://a2zsoc.com`

Manage affiliate programs, track commissions, and optimize partner performance.

---

## Table of Contents

- [Overview](#overview)
- [Endpoints](#endpoints)
  - [POST /api/v1/affiliate/affiliates](#post--api-v1-affiliate-affiliates)
  - [GET /api/v1/affiliate/affiliates](#get--api-v1-affiliate-affiliates)
  - [GET /api/v1/affiliate/affiliates/{aff}](#get--api-v1-affiliate-affiliates-aff)
  - [PUT /api/v1/affiliate/affiliates/{aff}](#put--api-v1-affiliate-affiliates-aff)
  - [DELETE /api/v1/affiliate/affiliates/{aff}](#delete--api-v1-affiliate-affiliates-aff)
  - [POST /api/v1/affiliate/programs](#post--api-v1-affiliate-programs)
  - [GET /api/v1/affiliate/programs/{program_id}/performance](#get--api-v1-affiliate-programs-program-id-performance)
- [Error Codes](#error-codes)
- [Rate Limiting](#rate-limiting)
- [Pagination](#pagination)
- [Authentication](#authentication)
- [Idempotency](#idempotency)

---

## Overview

The Affiliate Marketing API provides programmatic access to manage affiliate programs, track commissions, and optimize partner performance.

**Base Path:** `/api/v1/affiliate`

All endpoints require authentication via Bearer token and tenant scoping.

---

## Endpoints


### POST /api/v1/affiliate/affiliates

Create a new affiliate.

**Request Body:**

```json
{
  "name": "New Affiliate",
  "description": "A affiliate"
}
```

**Response (201):**

```json
{
  "id": "aff_001",
  "name": "New Affiliate",
  "status": "active",
  "created_at": "2026-10-01T00:00:00Z"
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/affiliate/affiliates \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -H "X-Idempotency-Key: 01J0ABC1234567890" \
  -d '{"name": "New Affiliate"}'
```


### GET /api/v1/affiliate/affiliates

List all affiliates.

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
      "id": "aff_001",
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
curl -X GET "https://a2zsoc.com/api/v1/affiliate/affiliates" \
  -H "Authorization: Bearer <token>"
```


### GET /api/v1/affiliate/affiliates/{aff}

Get a affiliate by ID.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `aff` | string | Yes | Affiliate identifier |

**Response (200):**

```json
{
  "id": "aff_001",
  "name": "Example",
  "status": "active"
}
```

**Example:**

```bash
curl -X GET https://a2zsoc.com/api/v1/affiliate/affiliates/aff_001 \
  -H "Authorization: Bearer <token>"
```


### PUT /api/v1/affiliate/affiliates/{aff}

Update a affiliate.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `aff` | string | Yes | Affiliate identifier |

**Request Body:**

```json
{
  "name": "Updated Name"
}
```

**Response (200):**

```json
{
  "id": "aff_001",
  "name": "Updated Name",
  "status": "active"
}
```

**Example:**

```bash
curl -X PUT https://a2zsoc.com/api/v1/affiliate/affiliates/aff_001 \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "Updated Name"}'
```


### DELETE /api/v1/affiliate/affiliates/{aff}

Delete a affiliate.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `aff` | string | Yes | Affiliate identifier |

**Example:**

```bash
curl -X DELETE https://a2zsoc.com/api/v1/affiliate/affiliates/aff_001 \
  -H "Authorization: Bearer <token>" \
  -H "X-Idempotency-Key: 01J0ABC1234567890"
```


### POST /api/v1/affiliate/programs

Create an affiliate program.

**Request Body:**

```json
{
  "name": "Partner Program",
  "commission_rate": 0.2,
  "cookie_duration_days": 30,
  "payout_threshold": 100
}
```

**Response (201):**

```json
{
  "program_id": "prog_001",
  "name": "Partner Program",
  "status": "active",
  "created_at": "2026-10-01T00:00:00Z"
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/affiliate/programs \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "Partner Program", "commission_rate": 0.20}'
```


### GET /api/v1/affiliate/programs/{program_id}/performance

Get program performance metrics.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `program_id` | string | Yes | Program identifier |

**Response (200):**

```json
{
  "program_id": "prog_001",
  "clicks": 10000,
  "conversions": 500,
  "revenue": 50000,
  "commission_earned": 10000
}
```

**Example:**

```bash
curl -X GET https://a2zsoc.com/api/v1/affiliate/programs/prog_001/performance \
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
