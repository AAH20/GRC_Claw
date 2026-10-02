# CRM Enhancer API Reference

> Last updated: 2026-10-02 | Base URL: `https://a2zsoc.com`

Enhance CRM data with AI-powered contact enrichment, deal scoring, and task automation.

---

## Table of Contents

- [Overview](#overview)
- [Endpoints](#endpoints)
  - [GET /health](#get-health)
  - [GET /metrics](#get-metrics)
  - [POST /api/v1/contacts/enrich](#post-api-v1-contacts-enrich)
  - [POST /api/v1/deals/score](#post-api-v1-deals-score)
  - [GET /api/v1/deals/{deal_id}](#get-api-v1-deals-deal_id)
  - [GET /api/v1/deals](#get-api-v1-deals)
- [Error Codes](#error-codes)
- [Rate Limiting](#rate-limiting)
- [Pagination](#pagination)
- [Authentication](#authentication)
- [Idempotency](#idempotency)

---

## Overview

The CRM Enhancer API provides programmatic access to enhance CRM data with AI-powered contact enrichment, deal scoring, and task automation.

**Base Path:** `/api/v1`

All endpoints require authentication via Bearer token and tenant scoping.

---

## Endpoints

### GET /health

Health check endpoint.

**Response (200):**

```json
{
  "status": "healthy",
  "service": "crm-enhancer"
}
```

**Example:**

```bash
curl -X GET https://a2zsoc.com/health
```

---

### GET /metrics

Prometheus metrics endpoint.

**Response (200):**

```
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{method="POST",endpoint="/api/v1/contacts/enrich",status="200"} 10
```

**Example:**

```bash
curl -X GET https://a2zsoc.com/metrics
```

---

### POST /api/v1/contacts/enrich

Enrich a contact record with additional data.

**Request Body:**

```json
{
  "email": "john.doe@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "company": "Acme Corp",
  "phone": "+1-555-0123",
  "linkedin_url": "https://linkedin.com/in/johndoe"
}
```

**Response (200):**

```json
{
  "contact": {
    "email": "john.doe@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "company": "Acme Corp",
    "phone": "+1-555-0123",
    "linkedin_url": "https://linkedin.com/in/johndoe"
  },
  "company_domain": "acme.com",
  "company_size": "50-200",
  "industry": "Technology",
  "revenue": "$10M-$50M",
  "technologies": ["Salesforce", "HubSpot"],
  "social_profiles": {
    "twitter": "@johndoe",
    "linkedin": "https://linkedin.com/in/johndoe"
  },
  "confidence_score": 0.92,
  "sources": ["clearbit", "linkedin"]
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/contacts/enrich \
  -H "Authorization: Bearer ***" \
  -H "Content-Type: application/json" \
  -d '{"email": "john.doe@example.com", "first_name": "John", "last_name": "Doe"}'
```

---

### POST /api/v1/deals/score

Score a deal using the deal scoring agent.

**Request Body:**

```json
{
  "deal_id": "deal_001",
  "title": "Enterprise License",
  "value": 50000,
  "stage": "negotiation",
  "contact_email": "john.doe@example.com",
  "company": "Acme Corp",
  "days_in_stage": 14,
  "activities_count": 8,
  "last_activity_days": 2,
  "source": "inbound"
}
```

**Response (200):**

```json
{
  "deal_id": "deal_001",
  "total_score": 85.5,
  "factors": [
    {"name": "deal_value", "weight": 0.3, "score": 90},
    {"name": "engagement", "weight": 0.4, "score": 85},
    {"name": "recency", "weight": 0.3, "score": 80}
  ],
  "priority": "high",
  "win_probability": 0.75,
  "recommendation": "Schedule executive meeting to close deal"
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/deals/score \
  -H "Authorization: Bearer ***" \
  -H "Content-Type: application/json" \
  -d '{"deal_id": "deal_001", "title": "Enterprise License", "value": 50000, "stage": "negotiation"}'
```

---

### GET /api/v1/deals/{deal_id}

Get a deal by ID.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `deal_id` | string | Yes | Deal identifier |

**Response (200):**

```json
{
  "deal_id": "deal_001",
  "title": "Enterprise License",
  "value": 50000,
  "stage": "negotiation",
  "contact_email": "john.doe@example.com",
  "company": "Acme Corp",
  "score": 85.5,
  "priority": "high"
}
```

**Example:**

```bash
curl -X GET https://a2zsoc.com/api/v1/deals/deal_001 \
  -H "Authorization: Bearer ***"
```

---

### GET /api/v1/deals

List deals with optional filtering.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `stage` | string | No | Filter by stage |
| `limit` | integer | No | Maximum number to return (default: 50) |
| `offset` | integer | No | Number to skip (default: 0) |

**Response (200):**

```json
[
  {
    "deal_id": "deal_001",
    "title": "Enterprise License",
    "value": 50000,
    "stage": "negotiation",
    "contact_email": "john.doe@example.com",
    "company": "Acme Corp",
    "score": 85.5,
    "priority": "high"
  }
]
```

**Example:**

```bash
curl -X GET "https://a2zsoc.com/api/v1/deals?stage=negotiation&limit=10" \
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
