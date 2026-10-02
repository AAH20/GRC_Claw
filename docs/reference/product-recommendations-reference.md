# Product Recommendations API Reference

> Last updated: 2026-10-02 | Base URL: `https://a2zsoc.com`

AI-powered product recommendations engine using collaborative filtering, content-based filtering, and cross-sell/upsell analysis.

---

## Table of Contents

- [Overview](#overview)
- [Endpoints](#endpoints)
  - [POST /api/v1/recommendations](#post--api-v1-recommendations)
  - [GET /api/v1/recommendations/{customer_id}](#get--api-v1-recommendations-customer_id)
  - [POST /api/v1/cross-sell](#post--api-v1-cross-sell)
  - [POST /api/v1/upsell](#post--api-v1-upsell)
  - [GET /api/v1/products](#get--api-v1-products)
  - [GET /api/v1/products/{product_id}](#get--api-v1-products-product_id)
  - [POST /api/v1/feedback](#post--api-v1-feedback)
- [Error Codes](#error-codes)
- [Rate Limiting](#rate-limiting)
- [Pagination](#pagination)
- [Authentication](#authentication)
- [Idempotency](#idempotency)

---

## Overview

The Product Recommendations API provides programmatic access to personalized product recommendations, cross-sell suggestions, upsell opportunities, and product catalog management. The engine uses a hybrid approach combining collaborative filtering (user-item interactions) and content-based filtering (product attributes).

**Base Path:** `/api/v1`

All endpoints require authentication via Bearer token and tenant scoping.

---

## Endpoints

### POST /api/v1/recommendations

Generate personalized product recommendations for a customer.

**Request Body:**

```json
{
  "customer_id": "cust_001",
  "context": {
    "cart_items": ["prod_001"],
    "current_page": "product_detail",
    "device": "mobile"
  },
  "max_results": 10,
  "diversity_factor": 0.2
}
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `customer_id` | string | Yes | Customer identifier |
| `context` | object | No | Additional context (cart items, page, device) |
| `max_results` | integer | No | Maximum recommendations (default: 10, max: 50) |
| `diversity_factor` | float | No | Diversity re-ranking factor 0-1 (default: 0.2) |

**Response (201):**

```json
{
  "customer_id": "cust_001",
  "recommendations": [
    {
      "product": {
        "id": "prod_002",
        "title": "Standard Gadget",
        "price": 29.99,
        "category": "gadgets",
        "tags": ["electronics", "accessories"]
      },
      "score": 0.85,
      "reason": "preferred category: gadgets, matching tags",
      "algorithm": "hybrid"
    }
  ],
  "context": {
    "cart_items": ["prod_001"]
  },
  "generated_at": "2026-10-01T00:00:00"
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/recommendations \
  -H "Authorization: Bearer ***" \
  -H "Content-Type: application/json" \
  -H "X-Idempotency-Key: 01J0ABC1234567890" \
  -d '{"customer_id": "cust_001", "max_results": 10}'
```

### GET /api/v1/recommendations/{customer_id}

Retrieve previously generated recommendations for a customer.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `customer_id` | string | Yes | Customer identifier (path) |

**Response (200):**

```json
{
  "customer_id": "cust_001",
  "recommendations": [
    {
      "product": {
        "id": "prod_002",
        "title": "Standard Gadget",
        "price": 29.99
      },
      "score": 0.85,
      "algorithm": "hybrid"
    }
  ],
  "generated_at": "2026-10-01T00:00:00"
}
```

**Example:**

```bash
curl -X GET https://a2zsoc.com/api/v1/recommendations/cust_001 \
  -H "Authorization: Bearer ***"
```

### POST /api/v1/cross-sell

Find cross-sell opportunities for a given product.

**Request Body:**

```json
{
  "product_id": "prod_001",
  "cart_items": ["prod_001", "prod_003"],
  "max_suggestions": 5
}
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `product_id` | string | Yes | Source product identifier |
| `cart_items` | array | No | Current cart items for context |
| `max_suggestions` | integer | No | Maximum suggestions (default: 5, max: 20) |

**Response (201):**

```json
{
  "suggestions": [
    {
      "source_product_id": "prod_001",
      "suggested_product_id": "prod_002",
      "confidence": 0.75,
      "relationship_type": "complementary",
      "reason": "Customers who bought Premium Widget also bought Standard Gadget"
    }
  ],
  "bundles": [
    {
      "name": "Premium Widget Bundle",
      "product_ids": ["prod_001", "prod_002", "prod_003"],
      "total_price": 116.98,
      "discount_percent": 10.0,
      "confidence": 0.65,
      "reason": "Save 10% when you buy these together"
    }
  ],
  "context": {
    "source_product": "Premium Widget",
    "cart_items": ["prod_001"]
  }
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/cross-sell \
  -H "Authorization: Bearer ***" \
  -H "Content-Type: application/json" \
  -d '{"product_id": "prod_001", "max_suggestions": 5}'
```

### POST /api/v1/upsell

Find upsell opportunities (higher-value alternatives) for a product.

**Request Body:**

```json
{
  "product_id": "prod_001"
}
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `product_id` | string | Yes | Source product identifier |

**Response (201):**

```json
{
  "suggestions": [
    {
      "source_product_id": "prod_001",
      "suggested_product_id": "prod_003",
      "confidence": 0.60,
      "relationship_type": "upgrade",
      "reason": "Upgrade to Deluxe Thingamajig for $50.00 more"
    }
  ]
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/upsell \
  -H "Authorization: Bearer ***" \
  -H "Content-Type: application/json" \
  -d '{"product_id": "prod_001"}'
```

### GET /api/v1/products

List all products in the catalog.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `page` | integer | No | Page number (default: 1) |
| `page_size` | integer | No | Items per page (default: 50, max: 200) |
| `category` | string | No | Filter by category |
| `platform` | string | No | Filter by platform |

**Response (200):**

```json
{
  "products": [
    {
      "product_id": "prod_001",
      "name": "Premium Widget",
      "current_price": 49.99,
      "cost": 25.00,
      "category": "widgets",
      "platform": "shopify"
    }
  ],
  "total": 3,
  "page": 1,
  "page_size": 50
}
```

**Example:**

```bash
curl -X GET "https://a2zsoc.com/api/v1/products?category=widgets&page=1" \
  -H "Authorization: Bearer ***"
```

### GET /api/v1/products/{product_id}

Get a single product by ID.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `product_id` | string | Yes | Product identifier (path) |

**Response (200):**

```json
{
  "product_id": "prod_001",
  "name": "Premium Widget",
  "current_price": 49.99,
  "cost": 25.00,
  "category": "widgets",
  "platform": "shopify"
}
```

**Example:**

```bash
curl -X GET https://a2zsoc.com/api/v1/products/prod_001 \
  -H "Authorization: Bearer ***"
```

### POST /api/v1/feedback

Submit feedback on recommendations to improve future results.

**Request Body:**

```json
{
  "customer_id": "cust_001",
  "recommendation_id": "rec_001",
  "feedback_type": "click",
  "product_id": "prod_002",
  "metadata": {
    "position": 1,
    "page": "homepage"
  }
}
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `customer_id` | string | Yes | Customer identifier |
| `recommendation_id` | string | Yes | Recommendation identifier |
| `feedback_type` | string | Yes | Type: `click`, `purchase`, `dismiss`, `ignore` |
| `product_id` | string | Yes | Product identifier |
| `metadata` | object | No | Additional feedback context |

**Response (201):**

```json
{
  "feedback_id": "fb_001",
  "status": "recorded"
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/feedback \
  -H "Authorization: Bearer ***" \
  -H "Content-Type: application/json" \
  -d '{"customer_id": "cust_001", "recommendation_id": "rec_001", "feedback_type": "click", "product_id": "prod_002"}'
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
Authorization: Bearer ***
```

## Idempotency

All `POST`, `PUT`, `PATCH`, and `DELETE` endpoints require an `X-Idempotency-Key` header:

```
X-Idempotency-Key: <ulid>
```

Duplicate requests with the same key return the cached response with `X-Idempotent-Replay: true`.
