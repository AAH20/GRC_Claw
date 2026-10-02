# Business Intelligence API Reference

> Last updated: 2026-10-02 | Base URL: `https://a2zsoc.com` | Version: `0.1.0`

Agentic AI business intelligence platform with multi-agent orchestration. Create dashboards, track KPIs, generate reports, and perform statistical analysis on marketing data.

---

## Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [Endpoints](#endpoints)
  - [Dashboards](#dashboards)
    - [POST /api/v1/dashboards](#post--api-v1-dashboards)
    - [GET /api/v1/dashboards](#get--api-v1-dashboards)
    - [GET /api/v1/dashboards/{dashboard_id}](#get--api-v1-dashboards-dashboard_id)
    - [PUT /api/v1/dashboards/{dashboard_id}](#put--api-v1-dashboards-dashboard_id)
    - [DELETE /api/v1/dashboards/{dashboard_id}](#delete--api-v1-dashboards-dashboard_id)
  - [Reports](#reports)
    - [POST /api/v1/reports](#post--api-v1-reports)
    - [GET /api/v1/reports](#get--api-v1-reports)
    - [GET /api/v1/reports/{report_id}](#get--api-v1-reports-report_id)
  - [KPIs](#kpis)
    - [GET /api/v1/kpis](#get--api-v1-kpis)
    - [POST /api/v1/kpis](#post--api-v1-kpis)
  - [Data Collection](#data-collection)
    - [POST /api/v1/data/collect](#post--api-v1-data-collect)
  - [Analysis](#analysis)
    - [POST /api/v1/analysis](#post--api-v1-analysis)
- [Error Codes](#error-codes)
- [Rate Limiting](#rate-limiting)
- [Pagination](#pagination)
- [Idempotency](#idempotency)

---

## Overview

The Business Intelligence API provides programmatic access to business intelligence dashboards, KPI tracking, and data visualization for marketing performance.

**Base Path:** `/api/v1`

All endpoints require authentication via Bearer token and tenant scoping.

---

## Authentication

All endpoints require Bearer token authentication:

```
Authorization: Bearer <token>
```

---

## Endpoints

### Dashboards

#### POST /api/v1/dashboards

Create a new dashboard.

**Request Body:**

```json
{
  "name": "Marketing Overview",
  "description": "High-level marketing performance dashboard",
  "widgets": [
    {
      "type": "kpi",
      "title": "Monthly Revenue",
      "data_source": "crm",
      "config": {"metric": "revenue", "aggregation": "sum"}
    },
    {
      "type": "chart",
      "title": "Lead Funnel",
      "data_source": "analytics",
      "config": {"chart_type": "funnel", "metrics": ["visits", "leads", "customers"]}
    }
  ],
  "is_public": false,
  "tags": ["marketing", "executive"]
}
```

**Response (201):**

```json
{
  "dashboard_id": "dash_001",
  "name": "Marketing Overview",
  "description": "High-level marketing performance dashboard",
  "status": "active",
  "widgets_count": 2,
  "created_at": "2026-10-01T00:00:00Z"
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/dashboards \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -H "X-Idempotency-Key: 01J0ABC1234567890" \
  -d '{"name": "Marketing Overview"}'
```

---

#### GET /api/v1/dashboards

List all dashboards.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `status` | string | No | Filter by status: `active`, `archived` |
| `tag` | string | No | Filter by tag |
| `cursor` | string | No | Pagination cursor |
| `limit` | integer | No | Items per page (default: 20, max: 100) |

**Response (200):**

```json
{
  "data": [
    {
      "dashboard_id": "dash_001",
      "name": "Marketing Overview",
      "status": "active",
      "widgets_count": 2,
      "tags": ["marketing", "executive"],
      "created_at": "2026-10-01T00:00:00Z"
    }
  ],
  "pagination": {
    "cursor": "eyJpZCI6ImRhc2hfMDAxIn0=",
    "hasMore": false,
    "totalCount": 1
  }
}
```

**Example:**

```bash
curl -X GET "https://a2zsoc.com/api/v1/dashboards?tag=marketing" \
  -H "Authorization: Bearer <token>"
```

---

#### GET /api/v1/dashboards/{dashboard_id}

Get a dashboard by ID.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `dashboard_id` | string | Yes | Dashboard identifier |

**Response (200):**

```json
{
  "dashboard_id": "dash_001",
  "name": "Marketing Overview",
  "description": "High-level marketing performance dashboard",
  "status": "active",
  "widgets": [
    {
      "type": "kpi",
      "title": "Monthly Revenue",
      "config": {"metric": "revenue", "aggregation": "sum"}
    }
  ],
  "is_public": false,
  "tags": ["marketing", "executive"],
  "created_at": "2026-10-01T00:00:00Z",
  "updated_at": "2026-10-01T00:00:00Z"
}
```

**Example:**

```bash
curl -X GET https://a2zsoc.com/api/v1/dashboards/dash_001 \
  -H "Authorization: Bearer <token>"
```

---

#### PUT /api/v1/dashboards/{dashboard_id}

Update a dashboard.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `dashboard_id` | string | Yes | Dashboard identifier |

**Request Body:**

```json
{
  "name": "Updated Dashboard Name",
  "description": "Updated description",
  "is_public": true,
  "tags": ["marketing", "v2"]
}
```

**Response (200):**

```json
{
  "dashboard_id": "dash_001",
  "name": "Updated Dashboard Name",
  "status": "active",
  "is_public": true,
  "updated_at": "2026-10-01T12:00:00Z"
}
```

**Example:**

```bash
curl -X PUT https://a2zsoc.com/api/v1/dashboards/dash_001 \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "Updated Name"}'
```

---

#### DELETE /api/v1/dashboards/{dashboard_id}

Delete a dashboard.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `dashboard_id` | string | Yes | Dashboard identifier |

**Response:** `204 No Content`

**Example:**

```bash
curl -X DELETE https://a2zsoc.com/api/v1/dashboards/dash_001 \
  -H "Authorization: Bearer <token>" \
  -H "X-Idempotency-Key: 01J0ABC1234567890"
```

---

### Reports

#### POST /api/v1/reports

Generate a custom BI report.

**Request Body:**

```json
{
  "name": "Monthly Marketing Report",
  "description": "Comprehensive monthly marketing performance",
  "metrics": ["revenue", "leads", "conversions", "roas"],
  "dimensions": ["channel", "campaign", "date"],
  "filters": {
    "date_range": {"start": "2026-09-01", "end": "2026-09-30"},
    "channel": ["email", "social", "ppc"]
  },
  "format": "pdf",
  "schedule": "monthly"
}
```

**Response (202):**

```json
{
  "report_id": "bi_report_001",
  "name": "Monthly Marketing Report",
  "status": "generating",
  "created_at": "2026-10-01T00:00:00Z"
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/reports \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "Monthly Report", "metrics": ["revenue"]}'
```

---

#### GET /api/v1/reports

List all reports.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `status` | string | No | Filter by status: `generating`, `completed`, `failed` |
| `cursor` | string | No | Pagination cursor |
| `limit` | integer | No | Items per page (default: 20, max: 100) |

**Response (200):**

```json
{
  "data": [
    {
      "report_id": "bi_report_001",
      "name": "Monthly Marketing Report",
      "status": "completed",
      "format": "pdf",
      "created_at": "2026-10-01T00:00:00Z"
    }
  ],
  "pagination": {
    "cursor": null,
    "hasMore": false,
    "totalCount": 1
  }
}
```

**Example:**

```bash
curl -X GET "https://a2zsoc.com/api/v1/reports?status=completed" \
  -H "Authorization: Bearer <token>"
```

---

#### GET /api/v1/reports/{report_id}

Get a report by ID.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `report_id` | string | Yes | Report identifier |

**Response (200):**

```json
{
  "report_id": "bi_report_001",
  "name": "Monthly Marketing Report",
  "status": "completed",
  "format": "pdf",
  "download_url": "https://a2zsoc.com/downloads/bi_report_001.pdf",
  "metrics": ["revenue", "leads", "conversions", "roas"],
  "dimensions": ["channel", "campaign", "date"],
  "created_at": "2026-10-01T00:00:00Z",
  "completed_at": "2026-10-01T00:05:00Z"
}
```

**Example:**

```bash
curl -X GET https://a2zsoc.com/api/v1/reports/bi_report_001 \
  -H "Authorization: Bearer <token>"
```

---

### KPIs

#### GET /api/v1/kpis

Get all configured KPIs.

**Response (200):**

```json
{
  "kpis": [
    {
      "kpi_id": "kpi_001",
      "name": "Monthly Revenue",
      "value": 150000,
      "target": 200000,
      "trend": "up",
      "unit": "USD",
      "change_percent": 12.5
    },
    {
      "kpi_id": "kpi_002",
      "name": "Lead Conversion Rate",
      "value": 0.035,
      "target": 0.05,
      "trend": "down",
      "unit": "percent",
      "change_percent": -2.1
    }
  ]
}
```

**Example:**

```bash
curl -X GET https://a2zsoc.com/api/v1/kpis \
  -H "Authorization: Bearer <token>"
```

---

#### POST /api/v1/kpis

Create a new KPI.

**Request Body:**

```json
{
  "name": "Customer Acquisition Cost",
  "target": 50,
  "unit": "USD",
  "data_source": "analytics",
  "config": {"metric": "cac", "aggregation": "average"}
}
```

**Response (201):**

```json
{
  "kpi_id": "kpi_003",
  "name": "Customer Acquisition Cost",
  "value": 45,
  "target": 50,
  "trend": "stable",
  "unit": "USD",
  "created_at": "2026-10-01T00:00:00Z"
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/kpis \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "CAC", "target": 50}'
```

---

### Data Collection

#### POST /api/v1/data/collect

Collect data from a specified source.

**Request Body:**

```json
{
  "source_type": "api",
  "api_endpoint": "https://api.example.com/data",
  "api_headers": {"Authorization": "Bearer token"},
  "query": "SELECT * FROM marketing_data",
  "batch_size": 1000,
  "timeout_seconds": 30
}
```

**Response (200):**

```json
{
  "success": true,
  "row_count": 5000,
  "columns": ["date", "channel", "revenue", "leads"],
  "metadata": {
    "source": "https://api.example.com/data",
    "format": "json"
  }
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/data/collect \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"source_type": "api", "api_endpoint": "https://api.example.com/data"}'
```

---

### Analysis

#### POST /api/v1/analysis

Perform statistical analysis on a dataset.

**Request Body:**

```json
{
  "dataset_id": "ds_001",
  "analysis_types": ["summary", "trends", "anomalies", "correlations"],
  "confidence_level": 0.95,
  "columns": ["revenue", "leads", "conversions"]
}
```

**Response (200):**

```json
{
  "success": true,
  "summary_statistics": {
    "revenue": {
      "count": 5000,
      "mean": 1500.0,
      "median": 1200.0,
      "std": 800.0,
      "min": 100.0,
      "max": 5000.0,
      "q25": 900.0,
      "q75": 2000.0,
      "skewness": 1.2,
      "kurtosis": 0.5,
      "missing_pct": 0.02
    }
  },
  "trends": {
    "revenue": {
      "slope": 15.3,
      "r_squared": 0.85,
      "p_value": 0.001,
      "direction": "increasing",
      "significant": true
    }
  },
  "anomalies": [
    {
      "column": "revenue",
      "index": 42,
      "value": 4800.0,
      "lower_bound": 500.0,
      "upper_bound": 3500.0
    }
  ],
  "correlations": {
    "matrix": {},
    "top_pairs": [
      {"column_1": "revenue", "column_2": "leads", "correlation": 0.78}
    ]
  },
  "insights": [
    "Dataset contains 5000 rows and 3 columns (3 numeric, 0 categorical).",
    "Detected 1 anomalies across 1 columns."
  ]
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/analysis \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"dataset_id": "ds_001", "analysis_types": ["summary", "trends"]}'
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

---

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

---

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

---

## Idempotency

All `POST`, `PUT`, `PATCH`, and `DELETE` endpoints require an `X-Idempotency-Key` header:

```
X-Idempotency-Key: <ulid>
```

Duplicate requests with the same key return the cached response with `X-Idempotent-Replay: true`.
