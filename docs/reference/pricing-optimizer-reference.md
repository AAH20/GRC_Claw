# Pricing Optimizer API Reference

> Last updated: 2026-10-02 | Base URL: `https://a2zsoc.com`

AI-powered pricing optimization engine with market intelligence, constraint-based optimization, and multi-platform price management.

---

## Table of Contents

- [Overview](#overview)
- [Endpoints](#endpoints)
  - [POST /api/v1/pricing/optimize](#post--api-v1-pricing-optimize)
  - [GET /api/v1/pricing/recommendations](#get--api-v1-pricing-recommendations)
  - [POST /api/v1/pricing/apply](#post--api-v1-pricing-apply)
  - [GET /api/v1/products](#get--api-v1-products)
  - [GET /api/v1/products/{product_id}](#get--api-v1-products-product_id)
- [Error Codes](#error-codes)
- [Rate Limiting](#rate-limiting)
- [Pagination](#pagination)
- [Authentication](#authentication)
- [Idempotency](#idempotency)

---

## Overview

The Pricing Optimizer API provides programmatic access to AI-powered pricing optimization, market intelligence analysis, and multi-platform price management. Supports Shopify, WooCommerce, and Stripe integrations.

**Base Path:** `/api/v1`

All endpoints require authentication via Bearer token and tenant scoping.

---

## Endpoints

### POST /api/v1/pricing/optimize

Run pricing optimization for a set of products.

**Request Body:**

```json
{
  "products": [
    {
      "product_id": "prod_001",
      "current_price": 49.99,
      "cost": 25.00
    }
  ],
  "constraints": {
    "min_price": 10.00,
    "max_price": 200.00,
    "min_margin_percent": 15.0,
    "max_price_change_percent": 20.0,
    "target_margin_percent": 40.0
  },
  "strategy": "profit_maximization",
  "include_market_intelligence": true
}
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `products` | array | Yes | List of products with product_id, current_price, and cost |
| `constraints` | object | No | Business constraints (min_price, max_price, min_margin_percent, etc.) |
| `strategy` | string | No | Optimization strategy: `profit_maximization`, `revenue_maximization`, `market_share`, `competitive_parity` (default: `profit_maximization`) |
| `include_market_intelligence` | boolean | No | Include market intelligence data (default: true) |

**Response (201):**

```json
{
  "success": true,
  "message": "Generated 1 pricing recommendations",
  "data": {
    "recommendations": [
      {
        "product_id": "prod_001",
        "current_price": 49.99,
        "recommended_price": 54.99,
        "change_percent": 10.0,
        "expected_margin_percent": 54.5,
        "expected_demand_change_percent": -5.0,
        "confidence": 0.85,
        "reasoning": "Market analysis supports 10% price increase based on competitive positioning and demand elasticity"
      }
    ],
    "market_intelligence": {
      "competitor_average_price": 52.99,
      "market_demand_trend": "stable",
      "price_elasticity": -1.2
    }
  }
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/pricing/optimize \
  -H "Authorization: Bearer ***" \
  -H "Content-Type: application/json" \
  -H "X-Idempotency-Key: 01J0ABC1234567890" \
  -d '{"products": [{"product_id": "prod_001", "current_price": 49.99, "cost": 25.00}]}'
```

### GET /api/v1/pricing/recommendations

Get current pricing recommendations.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `product_id` | string | No | Filter by product ID |

**Response (200):**

```json
{
  "success": true,
  "message": "No active recommendations",
  "data": {
    "recommendations": [],
    "product_id": null
  }
}
```

**Example:**

```bash
curl -X GET "https://a2zsoc.com/api/v1/pricing/recommendations?product_id=prod_001" \
  -H "Authorization: Bearer ***"
```

### POST /api/v1/pricing/apply

Apply recommended prices to the target platform.

**Request Body:**

```json
{
  "recommendations": [
    {
      "product_id": "prod_001",
      "recommended_price": 54.99
    }
  ],
  "platform": "shopify",
  "dry_run": false
}
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `recommendations` | array | Yes | List of price recommendations to apply |
| `platform` | string | Yes | Target platform: `shopify`, `woocommerce`, `stripe` |
| `dry_run` | boolean | No | If true, simulate without making changes (default: false) |

**Response (201):**

```json
{
  "success": true,
  "message": "Applied 1 price changes to shopify",
  "data": {
    "platform": "shopify",
    "dry_run": false,
    "applied_count": 1,
    "results": [
      {
        "product_id": "prod_001",
        "old_price": 49.99,
        "new_price": 54.99,
        "status": "applied"
      }
    ]
  }
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/pricing/apply \
  -H "Authorization: Bearer ***" \
  -H "Content-Type: application/json" \
  -d '{"recommendations": [{"product_id": "prod_001", "recommended_price": 54.99}], "platform": "shopify"}'
```

### GET /api/v1/products

List all products with optional filtering and pagination.

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
