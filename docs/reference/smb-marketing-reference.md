# SMB Marketing API Reference

> Last updated: 2026-10-02 | Base URL: `https://a2zsoc.com`

Marketing automation for small and medium-sized businesses. Simplified campaigns, local SEO, and reputation management.

---

## Table of Contents

- [Overview](#overview)
- [Endpoints](#endpoints)
  - [POST /api/v1/smb/campaigns](#post--api-v1-smb-campaigns)
  - [GET /api/v1/smb/campaigns](#get--api-v1-smb-campaigns)
  - [GET /api/v1/smb/campaigns/{smb_camp}](#get--api-v1-smb-campaigns-smb-camp)
  - [PUT /api/v1/smb/campaigns/{smb_camp}](#put--api-v1-smb-campaigns-smb-camp)
  - [DELETE /api/v1/smb/campaigns/{smb_camp}](#delete--api-v1-smb-campaigns-smb-camp)
  - [POST /api/v1/smb/local-seo](#post--api-v1-smb-local-seo)
  - [GET /api/v1/smb/reputation](#get--api-v1-smb-reputation)
- [Error Codes](#error-codes)
- [Rate Limiting](#rate-limiting)
- [Pagination](#pagination)
- [Authentication](#authentication)
- [Idempotency](#idempotency)

---

## Overview

The SMB Marketing API provides programmatic access to marketing automation for small and medium-sized businesses. simplified campaigns, local seo, and reputation management.

**Base Path:** `/api/v1/smb`

All endpoints require authentication via Bearer token and tenant scoping.

---

## Endpoints


### POST /api/v1/smb/campaigns

Create a new campaign.

**Request Body:**

```json
{
  "name": "New Campaign",
  "description": "A campaign"
}
```

**Response (201):**

```json
{
  "id": "smb_camp_001",
  "name": "New Campaign",
  "status": "active",
  "created_at": "2026-10-01T00:00:00Z"
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/smb/campaigns \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -H "X-Idempotency-Key: 01J0ABC1234567890" \
  -d '{"name": "New Campaign"}'
```


### GET /api/v1/smb/campaigns

List all campaigns.

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
      "id": "smb_camp_001",
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
curl -X GET "https://a2zsoc.com/api/v1/smb/campaigns" \
  -H "Authorization: Bearer <token>"
```


### GET /api/v1/smb/campaigns/{smb_camp}

Get a campaign by ID.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `smb_camp` | string | Yes | Campaign identifier |

**Response (200):**

```json
{
  "id": "smb_camp_001",
  "name": "Example",
  "status": "active"
}
```

**Example:**

```bash
curl -X GET https://a2zsoc.com/api/v1/smb/campaigns/smb_camp_001 \
  -H "Authorization: Bearer <token>"
```


### PUT /api/v1/smb/campaigns/{smb_camp}

Update a campaign.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `smb_camp` | string | Yes | Campaign identifier |

**Request Body:**

```json
{
  "name": "Updated Name"
}
```

**Response (200):**

```json
{
  "id": "smb_camp_001",
  "name": "Updated Name",
  "status": "active"
}
```

**Example:**

```bash
curl -X PUT https://a2zsoc.com/api/v1/smb/campaigns/smb_camp_001 \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "Updated Name"}'
```


### DELETE /api/v1/smb/campaigns/{smb_camp}

Delete a campaign.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `smb_camp` | string | Yes | Campaign identifier |

**Example:**

```bash
curl -X DELETE https://a2zsoc.com/api/v1/smb/campaigns/smb_camp_001 \
  -H "Authorization: Bearer <token>" \
  -H "X-Idempotency-Key: 01J0ABC1234567890"
```


### POST /api/v1/smb/local-seo

Optimize local SEO for a business.

**Request Body:**

```json
{
  "business_name": "Acme Coffee",
  "address": "123 Main St",
  "city": "San Francisco",
  "phone": "+1-555-0123"
}
```

**Response (201):**

```json
{
  "optimization_id": "local_seo_001",
  "status": "completed",
  "improvements": [
    "Google Business Profile updated",
    "NAP consistency checked"
  ]
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/smb/local-seo \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"business_name": "Acme Coffee", "address": "123 Main St"}'
```


### GET /api/v1/smb/reputation

Get business reputation metrics.

**Response (200):**

```json
{
  "rating": 4.5,
  "total_reviews": 120,
  "response_rate": 0.92,
  "sentiment": "positive"
}
```

**Example:**

```bash
curl -X GET https://a2zsoc.com/api/v1/smb/reputation \
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
