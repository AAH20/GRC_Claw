# Agency Marketing API Reference

> Last updated: 2026-10-02 | Base URL: `https://a2zsoc.com`

Marketing platform for agencies. Client management, white-label reporting, and campaign orchestration.

---

## Table of Contents

- [Overview](#overview)
- [Endpoints](#endpoints)
  - [POST /api/v1/agency/clients](#post--api-v1-agency-clients)
  - [GET /api/v1/agency/clients](#get--api-v1-agency-clients)
  - [GET /api/v1/agency/clients/{client}](#get--api-v1-agency-clients-client)
  - [PUT /api/v1/agency/clients/{client}](#put--api-v1-agency-clients-client)
  - [DELETE /api/v1/agency/clients/{client}](#delete--api-v1-agency-clients-client)
  - [POST /api/v1/agency/reports](#post--api-v1-agency-reports)
  - [GET /api/v1/agency/clients/{client_id}/campaigns](#get--api-v1-agency-clients-client-id-campaigns)
- [Error Codes](#error-codes)
- [Rate Limiting](#rate-limiting)
- [Pagination](#pagination)
- [Authentication](#authentication)
- [Idempotency](#idempotency)

---

## Overview

The Agency Marketing API provides programmatic access to marketing platform for agencies. client management, white-label reporting, and campaign orchestration.

**Base Path:** `/api/v1/agency`

All endpoints require authentication via Bearer token and tenant scoping.

---

## Endpoints


### POST /api/v1/agency/clients

Create a new client.

**Request Body:**

```json
{
  "name": "New Client",
  "description": "A client"
}
```

**Response (201):**

```json
{
  "id": "client_001",
  "name": "New Client",
  "status": "active",
  "created_at": "2026-10-01T00:00:00Z"
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/agency/clients \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -H "X-Idempotency-Key: 01J0ABC1234567890" \
  -d '{"name": "New Client"}'
```


### GET /api/v1/agency/clients

List all clients.

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
      "id": "client_001",
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
curl -X GET "https://a2zsoc.com/api/v1/agency/clients" \
  -H "Authorization: Bearer <token>"
```


### GET /api/v1/agency/clients/{client}

Get a client by ID.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `client` | string | Yes | Client identifier |

**Response (200):**

```json
{
  "id": "client_001",
  "name": "Example",
  "status": "active"
}
```

**Example:**

```bash
curl -X GET https://a2zsoc.com/api/v1/agency/clients/client_001 \
  -H "Authorization: Bearer <token>"
```


### PUT /api/v1/agency/clients/{client}

Update a client.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `client` | string | Yes | Client identifier |

**Request Body:**

```json
{
  "name": "Updated Name"
}
```

**Response (200):**

```json
{
  "id": "client_001",
  "name": "Updated Name",
  "status": "active"
}
```

**Example:**

```bash
curl -X PUT https://a2zsoc.com/api/v1/agency/clients/client_001 \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "Updated Name"}'
```


### DELETE /api/v1/agency/clients/{client}

Delete a client.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `client` | string | Yes | Client identifier |

**Example:**

```bash
curl -X DELETE https://a2zsoc.com/api/v1/agency/clients/client_001 \
  -H "Authorization: Bearer <token>" \
  -H "X-Idempotency-Key: 01J0ABC1234567890"
```


### POST /api/v1/agency/reports

Generate a white-label client report.

**Request Body:**

```json
{
  "client_id": "client_001",
  "report_type": "monthly",
  "branding": {
    "logo_url": "https://cdn.example.com/logo.png",
    "primary_color": "#0066CC"
  }
}
```

**Response (202):**

```json
{
  "report_id": "agency_report_001",
  "client_id": "client_001",
  "status": "generating",
  "download_url": null
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/agency/reports \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"client_id": "client_001", "report_type": "monthly"}'
```


### GET /api/v1/agency/clients/{client_id}/campaigns

Get all campaigns for a client.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `client_id` | string | Yes | Client identifier |

**Response (200):**

```json
{
  "client_id": "client_001",
  "campaigns": [
    {
      "campaign_id": "camp_001",
      "name": "Q4 Campaign",
      "status": "active"
    }
  ],
  "total": 1
}
```

**Example:**

```bash
curl -X GET https://a2zsoc.com/api/v1/agency/clients/client_001/campaigns \
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
