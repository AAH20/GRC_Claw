# Ecommerce Marketing API Reference

> Last updated: 2026-10-02 | Base URL: `https://a2zsoc.com`

Marketing automation for ecommerce. Product recommendations, cart abandonment, and post-purchase campaigns.

---

## Table of Contents

- [Overview](#overview)
- [Endpoints](#endpoints)
  - [POST /api/v1/ecommerce/products](#post--api-v1-ecommerce-products)
  - [GET /api/v1/ecommerce/products](#get--api-v1-ecommerce-products)
  - [POST /api/v1/ecommerce/campaigns](#post--api-v1-ecommerce-campaigns)
  - [GET /api/v1/ecommerce/analytics](#get--api-v1-ecommerce-analytics)
- [Error Codes](#error-codes)
- [Rate Limiting](#rate-limiting)
- [Pagination](#pagination)
- [Authentication](#authentication)
- [Idempotency](#idempotency)

---

## Overview

The Ecommerce Marketing API provides programmatic access to marketing automation for ecommerce. product recommendations, cart abandonment, and post-purchase campaigns.

**Base Path:** `/api/v1/ecommerce`

All endpoints require authentication via Bearer token and tenant scoping.

---

## Endpoints


### POST /api/v1/ecommerce/products

Add a product to the ecommerce platform.

**Request Body:**

```json
{
  "name": "Product A",
  "price": 99.99,
  "category": "Electronics",
  "sku": "PROD-001"
}
```

**Response (201):**

```json
{
  "product_id": "prod_001",
  "name": "Product A",
  "price": 99.99,
  "status": "active",
  "created_at": "2026-10-01T00:00:00Z"
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/ecommerce/products \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -H "X-Idempotency-Key: 01J0ABC1234567890" \
  -d '{"name": "Product A", "price": 99.99}'
```


### GET /api/v1/ecommerce/products

List all products.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `category` | string | No | Filter by category |

**Response (200):**

```json
{
  "products": [
    {
      "product_id": "prod_001",
      "name": "Product A",
      "price": 99.99
    }
  ],
  "total": 1
}
```

**Example:**

```bash
curl -X GET https://a2zsoc.com/api/v1/ecommerce/products \
  -H "Authorization: Bearer <token>"
```


### POST /api/v1/ecommerce/campaigns

Create an ecommerce marketing campaign.

**Request Body:**

```json
{
  "name": "Cart Abandonment Recovery",
  "type": "cart_abandonment",
  "trigger": "cart_abandoned",
  "delay_hours": 1,
  "discount_code": "COMEBACK10"
}
```

**Response (201):**

```json
{
  "campaign_id": "ecom_camp_001",
  "name": "Cart Abandonment Recovery",
  "status": "active",
  "created_at": "2026-10-01T00:00:00Z"
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/ecommerce/campaigns \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "Cart Recovery", "type": "cart_abandonment"}'
```


### GET /api/v1/ecommerce/analytics

Get ecommerce marketing analytics.

**Response (200):**

```json
{
  "revenue": 150000,
  "orders": 1500,
  "aov": 100,
  "conversion_rate": 0.03,
  "cart_abandonment_rate": 0.7
}
```

**Example:**

```bash
curl -X GET https://a2zsoc.com/api/v1/ecommerce/analytics \
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
