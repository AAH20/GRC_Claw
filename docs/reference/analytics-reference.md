# Analytics API Reference

> Last updated: 2026-10-02 | Base URL: `https://a2zsoc.com`

Track attribution, forecast revenue, predict churn, and generate marketing analytics reports.

---

## Table of Contents

- [Overview](#overview)
- [Endpoints](#endpoints)
  - [GET /health](#get-health)
  - [GET /api/v1/attribution/models](#get-api-v1-attribution-models)
  - [POST /api/v1/attribution/run](#post-api-v1-attribution-run)
  - [POST /api/v1/attribution/compare](#post-api-v1-attribution-compare)
  - [POST /api/v1/forecasting/revenue](#post-api-v1-forecasting-revenue)
  - [POST /api/v1/forecasting/churn](#post-api-v1-forecasting-churn)
  - [GET /api/v1/forecasting/models](#get-api-v1-forecasting-models)
- [Error Codes](#error-codes)
- [Rate Limiting](#rate-limiting)
- [Pagination](#pagination)
- [Authentication](#authentication)
- [Idempotency](#idempotency)

---

## Overview

The Analytics API provides programmatic access to track attribution, forecast revenue, predict churn, and generate marketing analytics reports.

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
  "version": "0.1.0"
}
```

**Example:**

```bash
curl -X GET https://a2zsoc.com/health
```

---

### GET /api/v1/attribution/models

List all available attribution models.

**Response (200):**

```json
{
  "models": [
    {
      "id": "first_touch",
      "name": "First Touch",
      "description": "100% credit to the first touchpoint in the customer journey."
    },
    {
      "id": "last_touch",
      "name": "Last Touch",
      "description": "100% credit to the last touchpoint before conversion."
    },
    {
      "id": "linear",
      "name": "Linear",
      "description": "Equal credit distributed across all touchpoints."
    },
    {
      "id": "time_decay",
      "name": "Time Decay",
      "description": "More credit to touchpoints closer to conversion (exponential decay)."
    },
    {
      "id": "data_driven",
      "name": "Data Driven",
      "description": "Shapley value approximation for fair credit distribution."
    }
  ],
  "default": "data_driven"
}
```

**Example:**

```bash
curl -X GET https://a2zsoc.com/api/v1/attribution/models \
  -H "Authorization: Bearer ***"
```

---

### POST /api/v1/attribution/run

Run attribution analysis on collected data.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `model` | string | No | Attribution model (default: `data_driven`) |
| `start_date` | datetime | No | Start date for analysis |
| `end_date` | datetime | No | End date for analysis |

**Response (200):**

```json
{
  "model": "data_driven",
  "period": {
    "start": "2026-09-02T00:00:00",
    "end": "2026-10-02T00:00:00"
  },
  "summary": {
    "total_revenue": 50000,
    "journey_count": 1000,
    "converted_journeys": 150
  },
  "channel_attributions": {
    "organic": 15000,
    "paid_search": 20000,
    "social": 8000,
    "email": 5000,
    "referral": 2000
  },
  "channel_percentages": {
    "organic": 0.30,
    "paid_search": 0.40,
    "social": 0.16,
    "email": 0.10,
    "referral": 0.04
  }
}
```

**Example:**

```bash
curl -X POST "https://a2zsoc.com/api/v1/attribution/run?model=data_driven&start_date=2026-09-01T00:00:00Z&end_date=2026-10-01T00:00:00Z" \
  -H "Authorization: Bearer ***" \
  -H "X-Idempotency-Key: 01J0ABC1234567890"
```

---

### POST /api/v1/attribution/compare

Compare all attribution models.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `start_date` | datetime | No | Start date for analysis |
| `end_date` | datetime | No | End date for analysis |

**Response (200):**

```json
{
  "period": {
    "start": "2026-09-02T00:00:00",
    "end": "2026-10-02T00:00:00"
  },
  "models": {
    "first_touch": {
      "channel_totals": {"organic": 25000, "paid_search": 10000},
      "channel_percentages": {"organic": 0.71, "paid_search": 0.29},
      "total_revenue": 50000
    },
    "last_touch": {
      "channel_totals": {"organic": 5000, "paid_search": 30000},
      "channel_percentages": {"organic": 0.14, "paid_search": 0.86},
      "total_revenue": 50000
    }
  }
}
```

**Example:**

```bash
curl -X POST "https://a2zsoc.com/api/v1/attribution/compare?start_date=2026-09-01T00:00:00Z&end_date=2026-10-01T00:00:00Z" \
  -H "Authorization: Bearer ***" \
  -H "X-Idempotency-Key: 01J0ABC1234567890"
```

---

### POST /api/v1/forecasting/revenue

Generate a revenue forecast.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `horizon_days` | integer | No | Number of days to forecast (default: 30, max: 365) |
| `model_type` | string | No | Model type: `linear_regression`, `random_forest`, `gradient_boosting` |

**Response (200):**

```json
{
  "model_type": "gradient_boosting",
  "horizon_days": 30,
  "metrics": {
    "mae": 150.5,
    "rmse": 200.3,
    "mape": 0.05
  },
  "forecast": [
    {
      "date": "2026-10-03",
      "predicted_value": 1200.0,
      "lower_bound": 1000.0,
      "upper_bound": 1400.0
    }
  ],
  "summary": {
    "total_predicted": 36000.0,
    "average_daily": 1200.0
  }
}
```

**Example:**

```bash
curl -X POST "https://a2zsoc.com/api/v1/forecasting/revenue?horizon_days=30&model_type=gradient_boosting" \
  -H "Authorization: Bearer ***" \
  -H "X-Idempotency-Key: 01J0ABC1234567890"
```

---

### POST /api/v1/forecasting/churn

Predict churn for users.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `model_type` | string | No | Model type: `linear_regression`, `random_forest`, `gradient_boosting` |

**Response (200):**

```json
{
  "model_metrics": {
    "accuracy": 0.85,
    "precision": 0.82,
    "recall": 0.78,
    "f1_score": 0.80
  },
  "predictions": [
    {
      "user_id": "user_0",
      "churn_probability": 0.75,
      "risk_tier": "high",
      "top_factors": ["low_engagement", "support_tickets"]
    }
  ],
  "summary": {
    "total_users": 20,
    "high_risk": 5,
    "medium_risk": 8,
    "low_risk": 7
  }
}
```

**Example:**

```bash
curl -X POST "https://a2zsoc.com/api/v1/forecasting/churn?model_type=gradient_boosting" \
  -H "Authorization: Bearer ***" \
  -H "X-Idempotency-Key: 01J0ABC1234567890"
```

---

### GET /api/v1/forecasting/models

List available forecasting models.

**Response (200):**

```json
{
  "models": [
    {
      "id": "linear_regression",
      "name": "Linear Regression",
      "description": "Simple linear regression for trend-based forecasting."
    },
    {
      "id": "random_forest",
      "name": "Random Forest",
      "description": "Ensemble of decision trees for non-linear patterns."
    },
    {
      "id": "gradient_boosting",
      "name": "Gradient Boosting",
      "description": "Gradient-boosted trees for high-accuracy predictions."
    }
  ]
}
```

**Example:**

```bash
curl -X GET https://a2zsoc.com/api/v1/forecasting/models \
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
