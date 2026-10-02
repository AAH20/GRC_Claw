# Marketing Attribution API Reference

> Last updated: 2026-10-02 | Base URL: `https://a2zsoc.com`

AI-powered marketing attribution with multi-touch attribution models, predictive analytics, real-time dashboards, and comprehensive reporting.

---

## Table of Contents

- [Overview](#overview)
- [Endpoints](#endpoints)
  - [POST /api/v1/attribution/calculate](#post--api-v1-attribution-calculate)
  - [GET /api/v1/attribution/models](#get--api-v1-attribution-models)
  - [POST /api/v1/attribution/compare-models](#post--api-v1-attribution-compare-models)
  - [GET /api/v1/reports](#get--api-v1-reports)
  - [POST /api/v1/reports/generate](#post--api-v1-reports-generate)
  - [GET /api/v1/reports/{report_id}](#get--api-v1-reports-report_id)
  - [GET /api/v1/dashboard/metrics](#get--api-v1-dashboard-metrics)
  - [WebSocket /api/v1/dashboard/stream](#websocket--api-v1-dashboard-stream)
- [Error Codes](#error-codes)
- [Rate Limiting](#rate-limiting)
- [Pagination](#pagination)
- [Authentication](#authentication)
- [Idempotency](#idempotency)

---

## Overview

The Marketing Attribution API provides programmatic access to multi-touch attribution modeling, predictive analytics, real-time dashboard streaming, and comprehensive reporting. Supports first-touch, last-touch, linear, time-decay, and data-driven attribution models.

**Base Path:** `/api/v1`

All endpoints require authentication via Bearer token and tenant scoping.

---

## Endpoints

### POST /api/v1/attribution/calculate

Calculate attribution for customer journeys.

**Request Body:**

```json
{
  "journeys": [
    {
      "journey_id": "journey_001",
      "touchpoints": [
        {
          "timestamp": "2026-09-01T00:00:00Z",
          "source": "google_ads",
          "campaign_id": "camp_001",
          "campaign_name": "Q3 Search Campaign",
          "interaction_type": "click"
        },
        {
          "timestamp": "2026-09-15T00:00:00Z",
          "source": "email",
          "campaign_id": "camp_002",
          "campaign_name": "Nurture Sequence",
          "interaction_type": "click"
        }
      ],
      "conversion_value": 5000.00,
      "converted": true
    }
  ],
  "model": "data_driven"
}
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `journeys` | array | Yes | List of customer journeys with touchpoints |
| `model` | string | Yes | Attribution model: `first_touch`, `last_touch`, `linear`, `time_decay`, `data_driven` |

**Response (201):**

```json
{
  "results": [
    {
      "journey_id": "journey_001",
      "model": "data_driven",
      "credited_touchpoints": {
        "0": 0.35,
        "1": 0.65
      },
      "total_credit": 1.0
    }
  ],
  "aggregated_by_campaign": [
    {
      "campaign_id": "camp_001",
      "campaign_name": "Q3 Search Campaign",
      "source": "google_ads",
      "attributed_conversions": 0.35,
      "attributed_revenue": 1750.00,
      "attributed_spend": 500.00,
      "roas": 3.5,
      "model": "data_driven"
    }
  ]
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/attribution/calculate \
  -H "Authorization: Bearer ***" \
  -H "Content-Type: application/json" \
  -H "X-Idempotency-Key: 01J0ABC1234567890" \
  -d '{"journeys": [{"journey_id": "j1", "touchpoints": [], "converted": true}], "model": "data_driven"}'
```

### GET /api/v1/attribution/models

List all supported attribution models.

**Response (200):**

```json
{
  "models": [
    {
      "id": "first_touch",
      "name": "First Touch",
      "description": "100% credit to the first touchpoint"
    },
    {
      "id": "last_touch",
      "name": "Last Touch",
      "description": "100% credit to the last touchpoint"
    },
    {
      "id": "linear",
      "name": "Linear",
      "description": "Equal credit to all touchpoints"
    },
    {
      "id": "time_decay",
      "name": "Time Decay",
      "description": "More credit to touchpoints closer to conversion"
    },
    {
      "id": "data_driven",
      "name": "Data Driven",
      "description": "Shapley-value-inspired weighting based on position and interaction type"
    }
  ]
}
```

**Example:**

```bash
curl -X GET https://a2zsoc.com/api/v1/attribution/models \
  -H "Authorization: Bearer ***"
```

### POST /api/v1/attribution/compare-models

Run all attribution models and return comparison.

**Request Body:**

```json
{
  "journeys": [
    {
      "journey_id": "journey_001",
      "touchpoints": [
        {
          "timestamp": "2026-09-01T00:00:00Z",
          "source": "google_ads",
          "campaign_id": "camp_001",
          "campaign_name": "Q3 Search",
          "interaction_type": "click"
        }
      ],
      "conversion_value": 5000.00,
      "converted": true
    }
  ]
}
```

**Response (201):**

```json
{
  "comparison": {
    "first_touch": [
      {
        "journey_id": "journey_001",
        "credited_touchpoints": {"0": 1.0}
      }
    ],
    "last_touch": [
      {
        "journey_id": "journey_001",
        "credited_touchpoints": {"0": 1.0}
      }
    ],
    "linear": [...],
    "time_decay": [...],
    "data_driven": [...]
  }
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/attribution/compare-models \
  -H "Authorization: Bearer ***" \
  -H "Content-Type: application/json" \
  -d '{"journeys": []}'
```

### GET /api/v1/reports

List all generated reports.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `page` | integer | No | Page number (default: 1) |
| `page_size` | integer | No | Items per page (default: 50, max: 200) |
| `format` | string | No | Filter by format: `json`, `csv`, `pdf` |

**Response (200):**

```json
{
  "data": [
    {
      "report_id": "RPT-20261001000000",
      "title": "Attribution Report 2026-10-01",
      "format": "json",
      "created_at": "2026-10-01T00:00:00Z",
      "total_journeys": 1500,
      "total_campaigns": 25
    }
  ],
  "total": 5,
  "page": 1,
  "page_size": 50
}
```

**Example:**

```bash
curl -X GET "https://a2zsoc.com/api/v1/reports?format=json" \
  -H "Authorization: Bearer ***"
```

### POST /api/v1/reports/generate

Generate a new attribution report.

**Request Body:**

```json
{
  "format": "json",
  "title": "Q3 Attribution Report",
  "date_range": {
    "start": "2026-07-01T00:00:00Z",
    "end": "2026-09-30T00:00:00Z"
  },
  "models": ["first_touch", "last_touch", "data_driven"]
}
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `format` | string | Yes | Report format: `json`, `csv`, `pdf` |
| `title` | string | No | Report title |
| `date_range` | object | No | Date range for the report |
| `models` | array | No | Attribution models to include |

**Response (201):**

```json
{
  "report_id": "RPT-20261001000000",
  "title": "Q3 Attribution Report",
  "format": "json",
  "created_at": "2026-10-01T00:00:00Z",
  "summary": {
    "totals": {
      "spend": 100000.00,
      "revenue": 350000.00,
      "conversions": 500,
      "roas": 3.5
    },
    "attributed": {
      "revenue": 350000.00,
      "conversions": 500
    }
  }
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/reports/generate \
  -H "Authorization: Bearer ***" \
  -H "Content-Type: application/json" \
  -H "X-Idempotency-Key: 01J0ABC1234567890" \
  -d '{"format": "json", "title": "Q3 Report"}'
```

### GET /api/v1/reports/{report_id}

Get a report by ID.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `report_id` | string | Yes | Report identifier (path) |

**Response (200):**

```json
{
  "report_id": "RPT-20261001000000",
  "title": "Q3 Attribution Report",
  "format": "json",
  "created_at": "2026-10-01T00:00:00Z",
  "content": "...",
  "summary": {
    "totals": {
      "spend": 100000.00,
      "revenue": 350000.00,
      "conversions": 500
    }
  }
}
```

**Example:**

```bash
curl -X GET https://a2zsoc.com/api/v1/reports/RPT-20261001000000 \
  -H "Authorization: Bearer ***"
```

### GET /api/v1/dashboard/metrics

Get current dashboard metrics.

**Response (200):**

```json
{
  "timestamp": "2026-10-01T00:00:00Z",
  "total_spend": 100000.00,
  "total_revenue": 350000.00,
  "total_conversions": 500.00,
  "total_impressions": 250000,
  "total_clicks": 12500,
  "active_campaigns": 25,
  "roas": 3.5,
  "cpa": 200.00,
  "ctr": 5.0,
  "top_campaigns": [
    {
      "campaign_id": "camp_001",
      "campaign_name": "Q3 Search Campaign",
      "source": "google_ads",
      "attributed_revenue": 150000.00,
      "roas": 4.5
    }
  ]
}
```

**Example:**

```bash
curl -X GET https://a2zsoc.com/api/v1/dashboard/metrics \
  -H "Authorization: Bearer ***"
```

### WebSocket /api/v1/dashboard/stream

Stream real-time dashboard updates via WebSocket.

**Connection:**

```
wss://a2zsoc.com/api/v1/dashboard/stream
```

**Messages:**

```json
{
  "type": "metrics",
  "payload": {
    "timestamp": "2026-10-01T00:00:00Z",
    "total_spend": 100000.00,
    "total_revenue": 350000.00,
    "roas": 3.5
  }
}
```

**Example:**

```javascript
const ws = new WebSocket('wss://a2zsoc.com/api/v1/dashboard/stream');
ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  console.log(update);
};
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
