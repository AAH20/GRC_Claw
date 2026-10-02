# Customer Retention API Reference

> Last updated: 2026-10-02 | Base URL: `https://a2zsoc.com`

AI-powered customer retention platform with churn prediction, automated interventions, campaign optimization, and performance analytics.

---

## Table of Contents

- [Overview](#overview)
- [Endpoints](#endpoints)
  - [GET /api/v1/customers](#get--api-v1-customers)
  - [GET /api/v1/customers/{id}](#get--api-v1-customers-id)
  - [POST /api/v1/customers](#post--api-v1-customers)
  - [GET /api/v1/customers/{id}/churn-risk](#get--api-v1-customers-id-churn-risk)
  - [GET /api/v1/campaigns](#get--api-v1-campaigns)
  - [POST /api/v1/campaigns](#post--api-v1-campaigns)
  - [GET /api/v1/campaigns/{id}](#get--api-v1-campaigns-id)
  - [POST /api/v1/campaigns/{id}/optimize](#post--api-v1-campaigns-id-optimize)
  - [GET /api/v1/analytics/retention](#get--api-v1-analytics-retention)
  - [GET /api/v1/analytics/cohorts](#get--api-v1-analytics-cohorts)
- [Error Codes](#error-codes)
- [Rate Limiting](#rate-limiting)
- [Pagination](#pagination)
- [Authentication](#authentication)
- [Idempotency](#idempotency)

---

## Overview

The Customer Retention API provides programmatic access to churn risk scoring, customer health monitoring, retention campaign management, and cohort analysis. Built with multi-agent architecture for prediction, intervention, optimization, and performance analytics.

**Base Path:** `/api/v1`

All endpoints require authentication via Bearer token and tenant scoping.

---

## Endpoints

### GET /api/v1/customers

List all customers with optional filtering.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `page` | integer | No | Page number (default: 1) |
| `page_size` | integer | No | Items per page (default: 50, max: 200) |
| `churn_risk_min` | float | No | Minimum churn risk score (0-1) |
| `churn_risk_max` | float | No | Maximum churn risk score (0-1) |
| `segment` | string | No | Filter by segment |
| `industry` | string | No | Filter by industry |

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
      "last_order_date": "2026-09-15T00:00:00Z"
    }
  ],
  "total": 150,
  "page": 1,
  "page_size": 50
}
```

**Example:**

```bash
curl -X GET "https://a2zsoc.com/api/v1/customers?churn_risk_min=0.5&page=1" \
  -H "Authorization: Bearer ***"
```

### GET /api/v1/customers/{id}

Get a customer by ID.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `id` | string | Yes | Customer identifier (path) |

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
  "last_order_date": "2026-09-15T00:00:00Z",
  "first_order_date": "2025-01-10T00:00:00Z",
  "segment_ids": ["seg_001", "seg_003"]
}
```

**Example:**

```bash
curl -X GET https://a2zsoc.com/api/v1/customers/cust_001 \
  -H "Authorization: Bearer ***"
```

### POST /api/v1/customers

Create a new customer record.

**Request Body:**

```json
{
  "email": "jane@example.com",
  "first_name": "Jane",
  "last_name": "Smith",
  "company": "TechCorp",
  "industry": "Technology",
  "job_title": "VP Engineering",
  "phone": "+1-555-0123",
  "country": "US",
  "city": "San Francisco"
}
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `email` | string | Yes | Customer email address |
| `first_name` | string | No | First name |
| `last_name` | string | No | Last name |
| `company` | string | No | Company name |
| `industry` | string | No | Industry |
| `job_title` | string | No | Job title |
| `phone` | string | No | Phone number |
| `country` | string | No | Country code |
| `city` | string | No | City |

**Response (201):**

```json
{
  "id": "cust_002",
  "email": "jane@example.com",
  "first_name": "Jane",
  "last_name": "Smith",
  "company": "TechCorp",
  "industry": "Technology",
  "total_revenue": 0.00,
  "total_orders": 0,
  "lifetime_value": 0.00,
  "churn_risk": null,
  "engagement_score": null,
  "created_at": "2026-10-01T00:00:00Z"
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/customers \
  -H "Authorization: Bearer ***" \
  -H "Content-Type: application/json" \
  -H "X-Idempotency-Key: 01J0ABC1234567890" \
  -d '{"email": "jane@example.com", "first_name": "Jane", "last_name": "Smith"}'
```

### GET /api/v1/customers/{id}/churn-risk

Get churn risk score and analysis for a customer.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `id` | string | Yes | Customer identifier (path) |

**Response (200):**

```json
{
  "customer_id": "cust_001",
  "churn_risk": 0.35,
  "risk_level": "medium",
  "confidence": 0.87,
  "factors": [
    {
      "factor": "recency",
      "impact": "negative",
      "weight": 0.3,
      "description": "No orders in 30+ days"
    },
    {
      "factor": "engagement",
      "impact": "positive",
      "weight": 0.2,
      "description": "High email open rate"
    },
    {
      "factor": "support_tickets",
      "impact": "negative",
      "weight": 0.15,
      "description": "3 open support tickets"
    }
  ],
  "predicted_churn_date": "2026-11-15",
  "recommended_actions": [
    "Send re-engagement email",
    "Offer loyalty discount",
    "Schedule check-in call"
  ],
  "calculated_at": "2026-10-01T00:00:00Z"
}
```

**Example:**

```bash
curl -X GET https://a2zsoc.com/api/v1/customers/cust_001/churn-risk \
  -H "Authorization: Bearer ***"
```

### GET /api/v1/campaigns

List retention campaigns.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `page` | integer | No | Page number (default: 1) |
| `page_size` | integer | No | Items per page (default: 50, max: 200) |
| `status` | string | No | Filter by status: `draft`, `active`, `paused`, `completed` |
| `type` | string | No | Filter by type: `win_back`, `loyalty`, `re_engagement`, `onboarding` |

**Response (200):**

```json
{
  "data": [
    {
      "id": "camp_001",
      "name": "Q3 Win-Back Campaign",
      "type": "win_back",
      "status": "active",
      "segment_id": "seg_001",
      "start_date": "2026-07-01T00:00:00Z",
      "end_date": "2026-09-30T00:00:00Z",
      "budget": 10000.00,
      "metrics": {
        "sent": 500,
        "opened": 250,
        "clicked": 100,
        "converted": 25,
        "revenue": 5000.00
      }
    }
  ],
  "total": 10,
  "page": 1,
  "page_size": 50
}
```

**Example:**

```bash
curl -X GET "https://a2zsoc.com/api/v1/campaigns?status=active" \
  -H "Authorization: Bearer ***"
```

### POST /api/v1/campaigns

Create a new retention campaign.

**Request Body:**

```json
{
  "name": "Q4 Loyalty Rewards",
  "type": "loyalty",
  "segment_id": "seg_002",
  "start_date": "2026-10-15T00:00:00Z",
  "end_date": "2026-12-31T00:00:00Z",
  "budget": 15000.00,
  "channels": ["email", "push"],
  "personalization": {
    "tone": "friendly",
    "incentive_type": "discount",
    "incentive_value": 15
  }
}
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | string | Yes | Campaign name |
| `type` | string | Yes | Campaign type: `win_back`, `loyalty`, `re_engagement`, `onboarding` |
| `segment_id` | string | Yes | Target segment identifier |
| `start_date` | datetime | Yes | Campaign start date (ISO 8601) |
| `end_date` | datetime | Yes | Campaign end date (ISO 8601) |
| `budget` | float | No | Campaign budget |
| `channels` | array | No | Delivery channels |
| `personalization` | object | No | Personalization settings |

**Response (201):**

```json
{
  "id": "camp_002",
  "name": "Q4 Loyalty Rewards",
  "type": "loyalty",
  "status": "draft",
  "segment_id": "seg_002",
  "start_date": "2026-10-15T00:00:00Z",
  "end_date": "2026-12-31T00:00:00Z",
  "budget": 15000.00,
  "created_at": "2026-10-01T00:00:00Z"
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/campaigns \
  -H "Authorization: Bearer ***" \
  -H "Content-Type: application/json" \
  -H "X-Idempotency-Key: 01J0ABC1234567890" \
  -d '{"name": "Q4 Loyalty", "type": "loyalty", "segment_id": "seg_002"}'
```

### GET /api/v1/campaigns/{id}

Get campaign details by ID.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `id` | string | Yes | Campaign identifier (path) |

**Response (200):**

```json
{
  "id": "camp_001",
  "name": "Q3 Win-Back Campaign",
  "type": "win_back",
  "status": "active",
  "segment_id": "seg_001",
  "start_date": "2026-07-01T00:00:00Z",
  "end_date": "2026-09-30T00:00:00Z",
  "budget": 10000.00,
  "metrics": {
    "sent": 500,
    "opened": 250,
    "clicked": 100,
    "converted": 25,
    "revenue": 5000.00,
    "roas": 0.5
  }
}
```

**Example:**

```bash
curl -X GET https://a2zsoc.com/api/v1/campaigns/camp_001 \
  -H "Authorization: Bearer ***"
```

### POST /api/v1/campaigns/{id}/optimize

Trigger AI-powered optimization for a campaign.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `id` | string | Yes | Campaign identifier (path) |

**Request Body:**

```json
{
  "optimization_goals": ["roas", "conversion_rate"],
  "constraints": {
    "max_budget_increase_percent": 20,
    "min_roas": 1.5
  }
}
```

**Response (202):**

```json
{
  "optimization_id": "opt_001",
  "campaign_id": "camp_001",
  "status": "running",
  "estimated_completion": "2026-10-01T00:05:00Z"
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/campaigns/camp_001/optimize \
  -H "Authorization: Bearer ***" \
  -H "Content-Type: application/json" \
  -d '{"optimization_goals": ["roas", "conversion_rate"]}'
```

### GET /api/v1/analytics/retention

Get retention metrics for a given time period.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `start_date` | datetime | No | Start date (default: 30 days ago) |
| `end_date` | datetime | No | End date (default: now) |
| `granularity` | string | No | `daily`, `weekly`, `monthly` (default: `weekly`) |

**Response (200):**

```json
{
  "period": {
    "start": "2026-09-01T00:00:00Z",
    "end": "2026-10-01T00:00:00Z"
  },
  "metrics": {
    "retention_rate": 0.85,
    "churn_rate": 0.15,
    "average_lifetime_value": 25000.00,
    "average_orders_per_customer": 12.5,
    "net_revenue_retention": 1.05,
    "customer_health_score": 78.0
  },
  "trends": [
    {
      "date": "2026-09-01T00:00:00Z",
      "retention_rate": 0.83,
      "churn_rate": 0.17
    },
    {
      "date": "2026-09-08T00:00:00Z",
      "retention_rate": 0.85,
      "churn_rate": 0.15
    }
  ]
}
```

**Example:**

```bash
curl -X GET "https://a2zsoc.com/api/v1/analytics/retention?granularity=weekly" \
  -H "Authorization: Bearer ***"
```

### GET /api/v1/analytics/cohorts

Get cohort analysis with retention windows.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `cohort_granularity` | string | No | `weekly`, `monthly` (default: `weekly`) |
| `retention_windows` | array | No | Retention windows in days (default: [7, 30, 90, 180, 365]) |

**Response (200):**

```json
{
  "cohorts": [
    {
      "cohort_id": "cohort_2026_w40",
      "start_date": "2026-09-29T00:00:00Z",
      "end_date": "2026-10-05T00:00:00Z",
      "size": 250,
      "retention": {
        "7d": 0.92,
        "30d": 0.85,
        "90d": 0.78,
        "180d": null,
        "365d": null
      },
      "revenue": {
        "7d": 15000.00,
        "30d": 45000.00,
        "90d": 120000.00
      }
    }
  ],
  "summary": {
    "average_retention_7d": 0.90,
    "average_retention_30d": 0.82,
    "average_retention_90d": 0.75
  }
}
```

**Example:**

```bash
curl -X GET "https://a2zsoc.com/api/v1/analytics/cohorts?cohort_granularity=weekly" \
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
