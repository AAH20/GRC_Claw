# Finance Marketing API Reference

> Last updated: 2026-10-02 | Base URL: `https://a2zsoc.com`

Compliant marketing for financial services. Lead nurturing, regulatory compliance, and customer education.

---

## Table of Contents

- [Overview](#overview)
- [Endpoints](#endpoints)
  - [POST /api/v1/finance/campaigns](#post--api-v1-finance-campaigns)
  - [GET /api/v1/finance/campaigns](#get--api-v1-finance-campaigns)
  - [GET /api/v1/finance/campaigns/{fin_camp}](#get--api-v1-finance-campaigns-fin-camp)
  - [PUT /api/v1/finance/campaigns/{fin_camp}](#put--api-v1-finance-campaigns-fin-camp)
  - [DELETE /api/v1/finance/campaigns/{fin_camp}](#delete--api-v1-finance-campaigns-fin-camp)
  - [POST /api/v1/finance/leads](#post--api-v1-finance-leads)
  - [GET /api/v1/finance/compliance](#get--api-v1-finance-compliance)
- [Error Codes](#error-codes)
- [Rate Limiting](#rate-limiting)
- [Pagination](#pagination)
- [Authentication](#authentication)
- [Idempotency](#idempotency)

---

## Overview

The Finance Marketing API provides programmatic access to compliant marketing for financial services. lead nurturing, regulatory compliance, and customer education.

**Base Path:** `/api/v1/finance`

All endpoints require authentication via Bearer token and tenant scoping.

---

## Endpoints


### POST /api/v1/finance/campaigns

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
  "id": "fin_camp_001",
  "name": "New Campaign",
  "status": "active",
  "created_at": "2026-10-01T00:00:00Z"
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/finance/campaigns \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -H "X-Idempotency-Key: 01J0ABC1234567890" \
  -d '{"name": "New Campaign"}'
```


### GET /api/v1/finance/campaigns

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
      "id": "fin_camp_001",
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
curl -X GET "https://a2zsoc.com/api/v1/finance/campaigns" \
  -H "Authorization: Bearer <token>"
```


### GET /api/v1/finance/campaigns/{fin_camp}

Get a campaign by ID.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `fin_camp` | string | Yes | Campaign identifier |

**Response (200):**

```json
{
  "id": "fin_camp_001",
  "name": "Example",
  "status": "active"
}
```

**Example:**

```bash
curl -X GET https://a2zsoc.com/api/v1/finance/campaigns/fin_camp_001 \
  -H "Authorization: Bearer <token>"
```


### PUT /api/v1/finance/campaigns/{fin_camp}

Update a campaign.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `fin_camp` | string | Yes | Campaign identifier |

**Request Body:**

```json
{
  "name": "Updated Name"
}
```

**Response (200):**

```json
{
  "id": "fin_camp_001",
  "name": "Updated Name",
  "status": "active"
}
```

**Example:**

```bash
curl -X PUT https://a2zsoc.com/api/v1/finance/campaigns/fin_camp_001 \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "Updated Name"}'
```


### DELETE /api/v1/finance/campaigns/{fin_camp}

Delete a campaign.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `fin_camp` | string | Yes | Campaign identifier |

**Example:**

```bash
curl -X DELETE https://a2zsoc.com/api/v1/finance/campaigns/fin_camp_001 \
  -H "Authorization: Bearer <token>" \
  -H "X-Idempotency-Key: 01J0ABC1234567890"
```


### POST /api/v1/finance/leads

Create a finance lead.

**Request Body:**

```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "product_interest": "mortgage",
  "credit_score_range": "700-750"
}
```

**Response (201):**

```json
{
  "lead_id": "fin_lead_001",
  "name": "John Doe",
  "product_interest": "mortgage",
  "status": "new",
  "created_at": "2026-10-01T00:00:00Z"
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/finance/leads \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -H "X-Idempotency-Key: 01J0ABC1234567890" \
  -d '{"name": "John Doe", "email": "john@example.com", "product_interest": "mortgage"}'
```


### GET /api/v1/finance/compliance

Get compliance status for marketing materials.

**Response (200):**

```json
{
  "compliant": true,
  "pending_review": 0,
  "violations": 0,
  "last_audit": "2026-10-01T00:00:00Z"
}
```

**Example:**

```bash
curl -X GET https://a2zsoc.com/api/v1/finance/compliance \
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
