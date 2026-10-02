# SaaS Marketing API Reference

> Last updated: 2026-10-02 | Base URL: `http://localhost:8000`

AI-powered marketing automation for SaaS PLG (Product-Led Growth). Campaign management, user scoring, churn prevention, and analytics.

---

## Table of Contents

- [Overview](#overview)
- [Endpoints](#endpoints)
  - [GET /](#get-)
  - [GET /health](#get-health)
  - [GET /metrics](#get-metrics)
  - [Campaigns](#campaigns)
    - [POST /api/v1/campaigns](#post-apiv1campaigns)
    - [GET /api/v1/campaigns](#get-apiv1campaigns)
    - [GET /api/v1/campaigns/{campaign_id}](#get-apiv1campaignscampaign_id)
    - [PATCH /api/v1/campaigns/{campaign_id}](#patch-apiv1campaignscampaign_id)
    - [DELETE /api/v1/campaigns/{campaign_id}](#delete-apiv1campaignscampaign_id)
  - [Users](#users)
    - [POST /api/v1/users/{user_id}/score](#post-apiv1usersuser_idscore)
    - [GET /api/v1/users/{user_id}/churn-risk](#get-apiv1usersuser_idchurn-risk)
    - [GET /api/v1/users/{user_id}/health](#get-apiv1usersuser_idhealth)
- [Data Models](#data-models)
- [Error Codes](#error-codes)
- [Authentication](#authentication)

---

## Overview

The SaaS Marketing API provides programmatic access to AI-driven marketing automation for SaaS PLG operations. It manages marketing campaigns, user PQL scoring, churn risk assessment, and user health monitoring.

**Base Path:** `/api/v1`

**Technology:** FastAPI with Pydantic v2 models, structured logging via structlog, Prometheus metrics middleware, and CORS middleware.

---

## Endpoints

### GET /

Root endpoint with basic API information.

**Response (200):**

```json
{
  "name": "SaaS Marketing API",
  "version": "0.1.0",
  "docs": "/docs",
  "health": "/health"
}
```

---

### GET /health

Health check endpoint for load balancers and monitoring.

**Response (200):**

```json
{
  "status": "healthy",
  "version": "0.1.0",
  "service": "saas-marketing"
}
```

---

### GET /metrics

Prometheus metrics endpoint for monitoring.

**Response (200):**

```
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{endpoint="/health",method="GET",status="200"} 42.0
# HELP http_request_duration_seconds HTTP request latency in seconds
# TYPE http_request_duration_seconds histogram
http_request_duration_seconds_bucket{endpoint="/health",le="0.005",method="GET"} 42.0
```

---

## Campaigns

### POST /api/v1/campaigns

Create a new marketing campaign.

**Request Body:**

```json
{
  "name": "Trial to Paid Conversion",
  "campaign_type": "email",
  "target_audience": "trial_users",
  "budget": 5000.00,
  "start_date": "2026-10-01T00:00:00Z",
  "end_date": "2026-12-31T23:59:59Z",
  "goals": ["convert_trials", "reduce_churn"],
  "channels": ["email", "in_app"]
}
```

**Response (201):**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Trial to Paid Conversion",
  "campaign_type": "email",
  "status": "draft",
  "target_audience": "trial_users",
  "budget": 5000.00,
  "start_date": "2026-10-01T00:00:00Z",
  "end_date": "2026-12-31T23:59:59Z",
  "goals": ["convert_trials", "reduce_churn"],
  "channels": ["email", "in_app"],
  "created_at": "2026-10-02T12:00:00Z",
  "updated_at": "2026-10-02T12:00:00Z"
}
```

**Example:**

```bash
curl -X POST http://localhost:8000/api/v1/campaigns \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Trial to Paid Conversion",
    "campaign_type": "email",
    "target_audience": "trial_users",
    "start_date": "2026-10-01T00:00:00Z",
    "end_date": "2026-12-31T23:59:59Z"
  }'
```

---

### GET /api/v1/campaigns

List all campaigns with optional filtering.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `status_filter` | string | No | Filter by campaign status |
| `campaign_type` | string | No | Filter by campaign type: email, social, paid, content |

**Response (200):**

```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Trial to Paid Conversion",
    "campaign_type": "email",
    "status": "draft",
    "target_audience": "trial_users",
    "budget": 5000.00,
    "start_date": "2026-10-01T00:00:00Z",
    "end_date": "2026-12-31T23:59:59Z",
    "goals": ["convert_trials"],
    "channels": ["email"],
    "created_at": "2026-10-02T12:00:00Z",
    "updated_at": "2026-10-02T12:00:00Z"
  }
]
```

---

### GET /api/v1/campaigns/{campaign_id}

Get a specific campaign by ID.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `campaign_id` | string (UUID) | Yes | Campaign identifier |

**Response (200):**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Trial to Paid Conversion",
  "campaign_type": "email",
  "status": "draft",
  "target_audience": "trial_users",
  "budget": 5000.00,
  "start_date": "2026-10-01T00:00:00Z",
  "end_date": "2026-12-31T23:59:59Z",
  "goals": ["convert_trials", "reduce_churn"],
  "channels": ["email", "in_app"],
  "created_at": "2026-10-02T12:00:00Z",
  "updated_at": "2026-10-02T12:00:00Z"
}
```

---

### PATCH /api/v1/campaigns/{campaign_id}

Update an existing campaign.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `campaign_id` | string (UUID) | Yes | Campaign identifier |

**Request Body:**

```json
{
  "name": "Updated Campaign Name",
  "status": "active",
  "budget": 7500.00
}
```

**Response (200):**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Updated Campaign Name",
  "status": "active",
  "budget": 7500.00,
  "updated_at": "2026-10-02T12:30:00Z"
}
```

---

### DELETE /api/v1/campaigns/{campaign_id}

Delete a campaign.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `campaign_id` | string (UUID) | Yes | Campaign identifier |

**Response:** `204 No Content`

---

## Users

### POST /api/v1/users/{user_id}/score

Score a user's PQL (Product Qualified Lead) status.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `user_id` | string | Yes | User identifier |

**Request Body:**

```json
{
  "user_id": "user_001",
  "feature_usage_count": 15,
  "total_sessions": 25,
  "avg_session_duration_seconds": 420.5,
  "days_since_signup": 14,
  "key_actions_completed": ["signup", "onboarding", "first_project"],
  "team_size": 3,
  "billing_page_visits": 2,
  "integration_attempts": 1,
  "nps_score": 8
}
```

**Response (200):**

```json
{
  "user_id": "user_001",
  "pql_score": 72.5,
  "is_pql": true,
  "factors": [
    {"factor": "feature_usage", "weight": 0.3, "value": "high"},
    {"factor": "session_frequency", "weight": 0.25, "value": "high"},
    {"factor": "key_actions", "weight": 0.25, "value": "strong"},
    {"factor": "team_size", "weight": 0.1, "value": "medium"},
    {"factor": "billing_engagement", "weight": 0.1, "value": "moderate"}
  ],
  "recommendations": [
    "Schedule product demo",
    "Send case study content"
  ]
}
```

---

### GET /api/v1/users/{user_id}/churn-risk

Get churn risk assessment for a user/account.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `user_id` | string | Yes | User or account identifier |

**Response (200):**

```json
{
  "account_id": "user_001",
  "churn_risk": "low",
  "risk_score": 0.25,
  "factors": [
    {"factor": "engagement", "weight": 0.35, "value": "high"},
    {"factor": "support_tickets", "weight": 0.2, "value": "low"},
    {"factor": "payment_failures", "weight": 0.25, "value": "none"},
    {"factor": "nps", "weight": 0.2, "value": "promoter"}
  ],
  "recommendations": [
    "Continue current engagement pattern",
    "Consider upsell opportunity"
  ]
}
```

---

### GET /api/v1/users/{user_id}/health

Get overall user health score combining PQL and churn signals.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `user_id` | string | Yes | User identifier |

**Response (200):**

```json
{
  "user_id": "user_001",
  "overall_health": "good",
  "pql_score": 72.5,
  "churn_risk": "low",
  "last_active": "2024-01-15T10:30:00Z",
  "recommendations": [
    "Continue current engagement pattern",
    "Consider upsell opportunity"
  ]
}
```

---

## Data Models

### Campaign

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Unique campaign identifier |
| `name` | string | Campaign name (1-200 chars) |
| `campaign_type` | string | Type: email, social, paid, content |
| `status` | string | Campaign status (default: draft) |
| `target_audience` | string | Target audience segment |
| `budget` | float | Campaign budget in USD (>= 0) |
| `start_date` | datetime | Campaign start date |
| `end_date` | datetime | Campaign end date |
| `goals` | list[string] | Campaign goals |
| `channels` | list[string] | Marketing channels |
| `created_at` | datetime | Creation timestamp |
| `updated_at` | datetime | Last update timestamp |

### UserScoreRequest

| Field | Type | Description |
|-------|------|-------------|
| `user_id` | string | User identifier |
| `feature_usage_count` | int | Features used (default: 0) |
| `total_sessions` | int | Total sessions (default: 0) |
| `avg_session_duration_seconds` | float | Avg session duration (default: 0.0) |
| `days_since_signup` | int | Days since signup (default: 0) |
| `key_actions_completed` | list[string] | Key actions (default: []) |
| `team_size` | int | Team size (default: 1) |
| `billing_page_visits` | int | Billing page visits (default: 0) |
| `integration_attempts` | int | Integration attempts (default: 0) |
| `nps_score` | int | NPS score (optional) |

### UserChurnRequest

| Field | Type | Description |
|-------|------|-------------|
| `account_id` | string | Account identifier |
| `mrr` | float | Monthly recurring revenue (default: 0.0) |
| `active_users` | int | Active users (default: 0) |
| `total_seats` | int | Total seats (default: 0) |
| `days_since_last_login` | int | Days since last login (default: 0) |
| `support_tickets_30d` | int | Support tickets in 30 days (default: 0) |
| `nps_score` | int | NPS score (optional) |
| `feature_adoption_rate` | float | Feature adoption rate (default: 0.0) |
| `contract_end_days` | int | Days until contract ends (default: 0) |
| `payment_failures` | int | Payment failures (default: 0) |
| `engagement_trend` | string | Engagement trend (default: stable) |

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

### Error Response Format

```json
{
  "detail": "Internal server error"
}
```

---

## Authentication

All endpoints require Bearer token authentication:

```
Authorization: Bearer <token>
```

CORS is configured to allow all origins. In production, restrict to configured origins only.
