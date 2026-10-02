# Sales Forecaster API Reference

> Last updated: 2026-10-02 | Base URL: `https://a2zsoc.com`

AI-powered sales forecasting with multi-source data collection, trend analysis, prediction, and automated action recommendations.

---

## Table of Contents

- [Overview](#overview)
- [Endpoints](#endpoints)
  - [POST /api/v1/forecasts](#post--api-v1-forecasts)
  - [GET /api/v1/forecasts](#get--api-v1-forecasts)
  - [GET /api/v1/forecasts/{forecast_id}](#get--api-v1-forecasts-forecast_id)
  - [DELETE /api/v1/forecasts/{forecast_id}](#delete--api-v1-forecasts-forecast_id)
  - [POST /api/v1/pipeline/run](#post--api-v1-pipeline-run)
  - [GET /api/v1/pipeline](#get--api-v1-pipeline)
  - [GET /api/v1/pipeline/status/{run_id}](#get--api-v1-pipeline-status-run_id)
- [Error Codes](#error-codes)
- [Rate Limiting](#rate-limiting)
- [Pagination](#pagination)
- [Authentication](#authentication)
- [Idempotency](#idempotency)

---

## Overview

The Sales Forecaster API provides programmatic access to AI-powered sales forecasting, pipeline execution, and performance analytics. Supports Salesforce, HubSpot, and SAP data sources with automated data collection, analysis, prediction, and action recommendation stages.

**Base Path:** `/api/v1`

All endpoints require authentication via Bearer token and tenant scoping.

---

## Endpoints

### POST /api/v1/forecasts

Generate a new sales forecast.

Collects data from configured sources, analyzes trends, and generates a forecast with confidence intervals.

**Request Body:**

```json
{
  "sources": ["salesforce", "hubspot"],
  "period": "monthly",
  "horizon_days": 90
}
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `sources` | array | No | Data sources to use. Defaults to all configured sources. Options: `salesforce`, `hubspot`, `sap` |
| `period` | string | No | Forecast period granularity: `daily`, `weekly`, `monthly`, `quarterly` (default: `monthly`) |
| `horizon_days` | integer | No | Number of days to forecast (1-365, default: 90) |

**Response (201):**

```json
{
  "success": true,
  "data": {
    "id": "forecast_001",
    "created_at": "2026-10-01T00:00:00Z",
    "period": "monthly",
    "horizon_days": 90,
    "points": [
      {
        "date": "2026-10-01T00:00:00Z",
        "value": 150000.00,
        "lower_bound": 135000.00,
        "upper_bound": 165000.00,
        "confidence": 0.95
      }
    ],
    "model_used": "prophet",
    "mape": 0.08,
    "rmse": 12000.00
  },
  "request_id": "req_001"
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/forecasts \
  -H "Authorization: Bearer ***" \
  -H "Content-Type: application/json" \
  -H "X-Idempotency-Key: 01J0ABC1234567890" \
  -d '{"period": "monthly", "horizon_days": 90}'
```

### GET /api/v1/forecasts

List all forecasts.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `limit` | integer | No | Maximum number of results (default: 10, max: 100) |
| `offset` | integer | No | Number of results to skip (default: 0) |

**Response (200):**

```json
{
  "success": true,
  "data": [
    {
      "id": "forecast_001",
      "created_at": "2026-10-01T00:00:00Z",
      "period": "monthly",
      "horizon_days": 90,
      "model_used": "prophet",
      "mape": 0.08
    }
  ],
  "request_id": "req_002"
}
```

**Example:**

```bash
curl -X GET "https://a2zsoc.com/api/v1/forecasts?limit=10&offset=0" \
  -H "Authorization: Bearer ***"
```

### GET /api/v1/forecasts/{forecast_id}

Get a forecast by ID.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `forecast_id` | string | Yes | Forecast identifier (path) |

**Response (200):**

```json
{
  "success": true,
  "data": {
    "id": "forecast_001",
    "created_at": "2026-10-01T00:00:00Z",
    "period": "monthly",
    "horizon_days": 90,
    "points": [
      {
        "date": "2026-10-01T00:00:00Z",
        "value": 150000.00,
        "lower_bound": 135000.00,
        "upper_bound": 165000.00,
        "confidence": 0.95
      }
    ],
    "model_used": "prophet",
    "mape": 0.08,
    "rmse": 12000.00
  },
  "request_id": "req_003"
}
```

**Example:**

```bash
curl -X GET https://a2zsoc.com/api/v1/forecasts/forecast_001 \
  -H "Authorization: Bearer ***"
```

### DELETE /api/v1/forecasts/{forecast_id}

Delete a forecast by ID.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `forecast_id` | string | Yes | Forecast identifier (path) |

**Response (200):**

```json
{
  "success": true,
  "data": {
    "deleted": "forecast_001"
  },
  "request_id": "req_004"
}
```

**Example:**

```bash
curl -X DELETE https://a2zsoc.com/api/v1/forecasts/forecast_001 \
  -H "Authorization: Bearer ***" \
  -H "X-Idempotency-Key: 01J0ABC1234567890"
```

### POST /api/v1/pipeline/run

Start a full pipeline run in the background.

Executes all stages: data collection, analysis, prediction, action recommendations, and performance analytics.

**Request Body:**

```json
{
  "sources": ["salesforce", "hubspot"],
  "period": "monthly"
}
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `sources` | array | No | Data sources to use. Defaults to all configured sources. |
| `period` | string | No | Forecast period: `daily`, `weekly`, `monthly`, `quarterly` (default: `monthly`) |

**Response (202):**

```json
{
  "success": true,
  "data": {
    "id": "pipeline_001",
    "status": "pending",
    "started_at": "2026-10-01T00:00:00Z",
    "completed_at": null,
    "stages": {},
    "error": null
  },
  "request_id": "pipeline_001"
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/pipeline/run \
  -H "Authorization: Bearer ***" \
  -H "Content-Type: application/json" \
  -d '{"period": "monthly"}'
```

### GET /api/v1/pipeline

List pipeline runs.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `limit` | integer | No | Maximum number of results (default: 10) |
| `offset` | integer | No | Number of results to skip (default: 0) |

**Response (200):**

```json
{
  "success": true,
  "data": [
    {
      "id": "pipeline_001",
      "status": "completed",
      "started_at": "2026-10-01T00:00:00Z",
      "completed_at": "2026-10-01T00:02:30Z",
      "stages": {
        "data_collection": {"status": "completed", "record_count": 1500},
        "analysis": {"status": "completed", "trend": "upward", "seasonality_detected": true},
        "prediction": {"status": "completed", "forecast_id": "forecast_001", "model_used": "prophet"},
        "action": {"status": "completed", "recommendation_count": 5},
        "performance_analytics": {"status": "completed", "forecast_accuracy": 0.92, "alert_count": 2}
      },
      "error": null
    }
  ],
  "request_id": "req_005"
}
```

**Example:**

```bash
curl -X GET "https://a2zsoc.com/api/v1/pipeline?limit=10" \
  -H "Authorization: Bearer ***"
```

### GET /api/v1/pipeline/status/{run_id}

Get the status of a pipeline run.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `run_id` | string | Yes | Pipeline run identifier (path) |

**Response (200):**

```json
{
  "success": true,
  "data": {
    "id": "pipeline_001",
    "status": "running",
    "started_at": "2026-10-01T00:00:00Z",
    "completed_at": null,
    "stages": {
      "data_collection": {"status": "completed", "record_count": 1500},
      "analysis": {"status": "running"}
    },
    "error": null
  },
  "request_id": "req_006"
}
```

**Example:**

```bash
curl -X GET https://a2zsoc.com/api/v1/pipeline/status/pipeline_001 \
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
