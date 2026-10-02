# Customer Segmentation API Reference

> Last updated: 2026-10-02 | Base URL: `https://a2zsoc.com`

AI-powered customer segmentation with RFM analysis, behavioral profiling, demographic segmentation, and predictive scoring.

---

## Table of Contents

- [Overview](#overview)
- [Endpoints](#endpoints)
  - [GET /api/v1/segments](#get--api-v1-segments)
  - [POST /api/v1/segments](#post--api-v1-segments)
  - [GET /api/v1/segments/{segment_id}](#get--api-v1-segments-segment_id)
  - [PUT /api/v1/segments/{segment_id}](#put--api-v1-segments-segment_id)
  - [DELETE /api/v1/segments/{segment_id}](#delete--api-v1-segments-segment_id)
  - [POST /api/v1/segments/{segment_id}/analyze](#post--api-v1-segments-segment_id-analyze)
  - [GET /api/v1/customers](#get--api-v1-customers)
  - [GET /api/v1/customers/{customer_id}](#get--api-v1-customers-customer_id)
  - [POST /api/v1/customers/enrich](#post--api-v1-customers-enrich)
- [Error Codes](#error-codes)
- [Rate Limiting](#rate-limiting)
- [Pagination](#pagination)
- [Authentication](#authentication)
- [Idempotency](#idempotency)

---

## Overview

The Customer Segmentation API provides programmatic access to AI-powered customer segmentation, including RFM (Recency, Frequency, Monetary) analysis, behavioral profiling, demographic segmentation, and predictive scoring. Supports multiple segment types and automated analysis pipelines.

**Base Path:** `/api/v1`

All endpoints require authentication via Bearer token and tenant scoping.

---

## Endpoints

### GET /api/v1/segments

List all customer segments.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `page` | integer | No | Page number (default: 1) |
| `page_size` | integer | No | Items per page (default: 50, max: 200) |
| `segment_type` | string | No | Filter by type: `rfm`, `behavioral`, `demographic`, `predictive`, `custom` |
| `status` | string | No | Filter by status: `draft`, `active`, `archived`, `processing` |

**Response (200):**

```json
{
  "data": [
    {
      "id": "seg_001",
      "name": "High-Value Customers",
      "description": "Top 20% by revenue",
      "segment_type": "rfm",
      "status": "active",
      "size": 250,
      "quality_score": 0.92
    }
  ],
  "total": 15,
  "page": 1,
  "page_size": 50
}
```

**Example:**

```bash
curl -X GET "https://a2zsoc.com/api/v1/segments?segment_type=rfm&status=active" \
  -H "Authorization: Bearer ***"
```

### POST /api/v1/segments

Create a new customer segment.

**Request Body:**

```json
{
  "name": "At-Risk Customers",
  "description": "Customers with declining engagement",
  "segment_type": "behavioral",
  "criteria": {
    "churn_risk_min": 0.6,
    "engagement_score_max": 30,
    "last_order_days": 60
  }
}
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | string | Yes | Segment name (1-200 chars) |
| `description` | string | No | Segment description |
| `segment_type` | string | No | Segment type: `rfm`, `behavioral`, `demographic`, `predictive`, `custom` (default: `custom`) |
| `criteria` | object | No | Segmentation criteria |

**Response (201):**

```json
{
  "id": "seg_002",
  "name": "At-Risk Customers",
  "description": "Customers with declining engagement",
  "segment_type": "behavioral",
  "status": "draft",
  "size": 0,
  "criteria": {
    "churn_risk_min": 0.6,
    "engagement_score_max": 30
  },
  "created_at": "2026-10-01T00:00:00Z"
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/segments \
  -H "Authorization: Bearer ***" \
  -H "Content-Type: application/json" \
  -H "X-Idempotency-Key: 01J0ABC1234567890" \
  -d '{"name": "At-Risk", "segment_type": "behavioral"}'
```

### GET /api/v1/segments/{segment_id}

Get a segment by ID.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `segment_id` | string | Yes | Segment identifier (path) |

**Response (200):**

```json
{
  "id": "seg_001",
  "name": "High-Value Customers",
  "description": "Top 20% by revenue",
  "segment_type": "rfm",
  "status": "active",
  "size": 250,
  "criteria": {
    "rfm_segment": "champions",
    "min_lifetime_value": 10000
  },
  "rfm_profile": {
    "recency_days": 5,
    "frequency": 25,
    "monetary_value": 15000.00,
    "r_score": 5,
    "f_score": 5,
    "m_score": 5,
    "rfm_segment": "champions"
  },
  "quality_score": 0.92,
  "created_at": "2026-09-01T00:00:00Z"
}
```

**Example:**

```bash
curl -X GET https://a2zsoc.com/api/v1/segments/seg_001 \
  -H "Authorization: Bearer ***"
```

### PUT /api/v1/segments/{segment_id}

Update a segment.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `segment_id` | string | Yes | Segment identifier (path) |

**Request Body:**

```json
{
  "name": "Updated Segment Name",
  "description": "Updated description",
  "status": "active",
  "criteria": {
    "min_lifetime_value": 5000
  }
}
```

**Response (200):**

```json
{
  "id": "seg_001",
  "name": "Updated Segment Name",
  "description": "Updated description",
  "segment_type": "rfm",
  "status": "active",
  "size": 250,
  "updated_at": "2026-10-01T00:00:00Z"
}
```

**Example:**

```bash
curl -X PUT https://a2zsoc.com/api/v1/segments/seg_001 \
  -H "Authorization: Bearer ***" \
  -H "Content-Type: application/json" \
  -d '{"name": "Updated Name"}'
```

### DELETE /api/v1/segments/{segment_id}

Delete a segment.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `segment_id` | string | Yes | Segment identifier (path) |

**Example:**

```bash
curl -X DELETE https://a2zsoc.com/api/v1/segments/seg_001 \
  -H "Authorization: Bearer ***" \
  -H "X-Idempotency-Key: 01J0ABC1234567890"
```

### POST /api/v1/segments/{segment_id}/analyze

Trigger AI-powered analysis for a segment.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `segment_id` | string | Yes | Segment identifier (path) |

**Response (202):**

```json
{
  "analysis_id": "analysis_001",
  "segment_id": "seg_001",
  "status": "running",
  "estimated_completion": "2026-10-01T00:05:00Z"
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/segments/seg_001/analyze \
  -H "Authorization: Bearer ***" \
  -H "X-Idempotency-Key: 01J0ABC1234567890"
```

### GET /api/v1/customers

List customers with optional filtering.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `page` | integer | No | Page number (default: 1) |
| `page_size` | integer | No | Items per page (default: 50, max: 200) |
| `segment_id` | string | No | Filter by segment membership |
| `churn_risk_min` | float | No | Minimum churn risk (0-1) |
| `churn_risk_max` | float | No | Maximum churn risk (0-1) |

**Response (200):**

```json
{
  "data": [
    {
      "id": "cust_001",
      "email": "john@example.com",
      "first_name": "John",
      "last_name": "Doe",
      "company": "Acme Corp",
      "industry": "Technology",
      "total_revenue": 15000.00,
      "total_orders": 25,
      "lifetime_value": 25000.00,
      "churn_risk": 0.35,
      "engagement_score": 72.5,
      "segment_ids": ["seg_001"]
    }
  ],
  "total": 250,
  "page": 1,
  "page_size": 50
}
```

**Example:**

```bash
curl -X GET "https://a2zsoc.com/api/v1/customers?segment_id=seg_001" \
  -H "Authorization: Bearer ***"
```

### GET /api/v1/customers/{customer_id}

Get a customer by ID.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `customer_id` | string | Yes | Customer identifier (path) |

**Response (200):**

```json
{
  "id": "cust_001",
  "email": "john@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "company": "Acme Corp",
  "industry": "Technology",
  "job_title": "CTO",
  "total_revenue": 15000.00,
  "total_orders": 25,
  "lifetime_value": 25000.00,
  "churn_risk": 0.35,
  "engagement_score": 72.5,
  "segment_ids": ["seg_001", "seg_003"],
  "metadata": {}
}
```

**Example:**

```bash
curl -X GET https://a2zsoc.com/api/v1/customers/cust_001 \
  -H "Authorization: Bearer ***"
```

### POST /api/v1/customers/enrich

Enrich customer data from external sources.

**Request Body:**

```json
{
  "customer_ids": ["cust_001", "cust_002"],
  "sources": ["salesforce", "hubspot", "google_analytics"]
}
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `customer_ids` | array | Yes | List of customer IDs (1-1000) |
| `sources` | array | No | Data sources (default: all) |

**Response (201):**

```json
{
  "enriched_count": 2,
  "failed_count": 0,
  "results": {
    "cust_001": {
      "salesforce": {"title": "CTO", "account": "Acme Corp"},
      "hubspot": {"lifecycle_stage": "customer"}
    }
  },
  "errors": []
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/customers/enrich \
  -H "Authorization: Bearer ***" \
  -H "Content-Type: application/json" \
  -d '{"customer_ids": ["cust_001"], "sources": ["salesforce"]}'
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
