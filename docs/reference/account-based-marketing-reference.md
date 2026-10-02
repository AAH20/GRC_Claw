# Account-Based Marketing API Reference

> Last updated: 2026-10-02 | Base URL: `https://a2zsoc.com`

AI-powered account-based marketing platform with account identification, intent scoring, buying committee mapping, and multi-channel orchestration.

---

## Table of Contents

- [Overview](#overview)
- [Endpoints](#endpoints)
  - [GET /api/v1/accounts](#get--api-v1-accounts)
  - [POST /api/v1/accounts/identify](#post--api-v1-accounts-identify)
  - [GET /api/v1/accounts/{account_id}](#get--api-v1-accounts-account_id)
  - [GET /api/v1/accounts/{account_id}/intent](#get--api-v1-accounts-account_id-intent)
  - [GET /api/v1/accounts/{account_id}/committee](#get--api-v1-accounts-account_id-committee)
  - [POST /api/v1/campaigns](#post--api-v1-campaigns)
  - [GET /api/v1/campaigns/{campaign_id}](#get--api-v1-campaigns-campaign_id)
  - [GET /api/v1/campaigns/{campaign_id}/analytics](#get--api-v1-campaigns-campaign_id-analytics)
  - [POST /api/v1/campaigns/{campaign_id}/personalize](#post--api-v1-campaigns-campaign_id-personalize)
  - [POST /api/v1/campaigns/{campaign_id}/orchestrate](#post--api-v1-campaigns-campaign_id-orchestrate)
- [Error Codes](#error-codes)
- [Rate Limiting](#rate-limiting)
- [Pagination](#pagination)
- [Authentication](#authentication)
- [Idempotency](#idempotency)

---

## Overview

The Account-Based Marketing API provides programmatic access to AI-powered ABM capabilities including ideal customer profile (ICP) matching, account identification, intent scoring, buying committee mapping, campaign management, content personalization, and multi-channel orchestration.

**Base Path:** `/api/v1`

All endpoints require authentication via Bearer token and tenant scoping.

---

## Endpoints

### GET /api/v1/accounts

List target accounts with pagination.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `limit` | integer | No | Maximum number of accounts to return (default: 50, max: 200) |
| `offset` | integer | No | Number of accounts to skip (default: 0) |

**Response (200):**

```json
[
  {
    "id": "acc_001",
    "name": "Company 1",
    "domain": "company1.com",
    "score": 0.9,
    "industry": "Technology",
    "employee_count": 510
  }
]
```

**Example:**

```bash
curl -X GET "https://a2zsoc.com/api/v1/accounts?limit=50&offset=0" \
  -H "Authorization: Bearer ***"
```

### POST /api/v1/accounts/identify

Identify new target accounts based on ICP criteria.

**Request Body:**

```json
{
  "industry": "Technology",
  "employee_count_min": 100,
  "employee_count_max": 1000,
  "geography": ["US", "UK"],
  "technologies": ["salesforce", "hubspot"],
  "revenue_min": 1000000
}
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `industry` | string | No | Target industry |
| `employee_count_min` | integer | No | Minimum employee count |
| `employee_count_max` | integer | No | Maximum employee count |
| `geography` | array | No | Target geographies |
| `technologies` | array | No | Target technologies |
| `revenue_min` | float | No | Minimum annual revenue |

**Response (201):**

```json
[
  {
    "account_id": "acc_001",
    "name": "Acme Corp",
    "domain": "acme.com",
    "score": 0.92,
    "firmographic_match": 0.95,
    "technographic_match": 0.88,
    "engagement_level": "high",
    "signals": [
      {
        "type": "job_posting",
        "description": "Hiring 5 sales reps"
      }
    ]
  }
]
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/accounts/identify \
  -H "Authorization: Bearer ***" \
  -H "Content-Type: application/json" \
  -H "X-Idempotency-Key: 01J0ABC1234567890" \
  -d '{"industry": "Technology", "employee_count_min": 100}'
```

### GET /api/v1/accounts/{account_id}

Get detailed information about a specific account.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `account_id` | string | Yes | Account identifier (path) |

**Response (200):**

```json
{
  "account_id": "acc_001",
  "name": "Acme Corp",
  "domain": "acme.com",
  "industry": "Technology",
  "employee_count": 500,
  "annual_revenue": 50000000,
  "technologies": ["salesforce", "hubspot", "slack"],
  "engagement_score": 0.85,
  "recent_activities": [
    {
      "type": "website_visit",
      "timestamp": "2026-09-28T00:00:00Z",
      "page": "/pricing"
    }
  ]
}
```

**Example:**

```bash
curl -X GET https://a2zsoc.com/api/v1/accounts/acc_001 \
  -H "Authorization: Bearer ***"
```

### GET /api/v1/accounts/{account_id}/intent

Get intent score and signals for an account.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `account_id` | string | Yes | Account identifier (path) |

**Response (200):**

```json
{
  "account_id": "acc_001",
  "total_score": 85.5,
  "normalized_score": 0.855,
  "trend": "increasing",
  "last_activity": "2026-09-28T00:00:00Z",
  "signals": [
    {
      "type": "website_visit",
      "timestamp": "2026-09-28T00:00:00Z",
      "weight": 0.3,
      "metadata": {"page": "/pricing"}
    },
    {
      "type": "content_download",
      "timestamp": "2026-09-25T00:00:00Z",
      "weight": 0.5,
      "metadata": {"content": "whitepaper"}
    }
  ]
}
```

**Example:**

```bash
curl -X GET https://a2zsoc.com/api/v1/accounts/acc_001/intent \
  -H "Authorization: Bearer ***"
```

### GET /api/v1/accounts/{account_id}/committee

Get buying committee map for an account.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `account_id` | string | Yes | Account identifier (path) |

**Response (200):**

```json
{
  "account_id": "acc_001",
  "completeness_score": 0.75,
  "identified_gaps": ["economic_buyer", "technical_evaluator"],
  "members": [
    {
      "contact_id": "cont_001",
      "name": "John Smith",
      "title": "CTO",
      "role": "decision_maker",
      "influence_score": 0.9,
      "engagement_level": "high",
      "email": "john@acme.com",
      "linkedin_url": "https://linkedin.com/in/johnsmith"
    }
  ]
}
```

**Example:**

```bash
curl -X GET https://a2zsoc.com/api/v1/accounts/acc_001/committee \
  -H "Authorization: Bearer ***"
```

### POST /api/v1/campaigns

Create a new ABM campaign.

**Request Body:**

```json
{
  "name": "Q1 ABM Campaign",
  "account_ids": ["acc_001", "acc_002"],
  "content_type": "email",
  "persona": "executive",
  "start_date": "2026-01-01T00:00:00Z",
  "budget": 50000.00,
  "description": "Targeted outreach to high-value accounts"
}
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | string | Yes | Campaign name (1-200 chars) |
| `account_ids` | array | Yes | Target account IDs (min 1) |
| `content_type` | string | No | Content type: `email`, `linkedin_ads`, `direct_mail` (default: `email`) |
| `persona` | string | No | Target persona: `executive`, `technical`, `financial` (default: `executive`) |
| `start_date` | datetime | No | Campaign start date |
| `budget` | float | No | Campaign budget |
| `description` | string | No | Campaign description |

**Response (201):**

```json
{
  "campaign_id": "campaign_20261001000000",
  "name": "Q1 ABM Campaign",
  "status": "draft",
  "account_count": 2,
  "content_type": "email",
  "persona": "executive",
  "created_at": "2026-10-01T00:00:00Z"
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/campaigns \
  -H "Authorization: Bearer ***" \
  -H "Content-Type: application/json" \
  -H "X-Idempotency-Key: 01J0ABC1234567890" \
  -d '{"name": "Q1 ABM", "account_ids": ["acc_001"]}'
```

### GET /api/v1/campaigns/{campaign_id}

Get campaign details.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `campaign_id` | string | Yes | Campaign identifier (path) |

**Response (200):**

```json
{
  "campaign_id": "campaign_001",
  "name": "Q1 ABM Campaign",
  "status": "active",
  "accounts": ["acc_001", "acc_002", "acc_003"],
  "channels": ["email", "linkedin_ads"],
  "start_date": "2024-01-01T00:00:00Z"
}
```

**Example:**

```bash
curl -X GET https://a2zsoc.com/api/v1/campaigns/campaign_001 \
  -H "Authorization: Bearer ***"
```

### GET /api/v1/campaigns/{campaign_id}/analytics

Get comprehensive analytics for a campaign.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `campaign_id` | string | Yes | Campaign identifier (path) |

**Response (200):**

```json
{
  "campaign_id": "campaign_001",
  "metrics": {
    "accounts_targeted": 50,
    "accounts_engaged": 35,
    "meetings_booked": 12,
    "pipeline_generated": 2500000.00,
    "revenue_influenced": 5000000.00,
    "roas": 10.0
  },
  "channel_performance": [
    {
      "channel": "email",
      "sent": 500,
      "opened": 250,
      "clicked": 100,
      "responded": 25
    }
  ]
}
```

**Example:**

```bash
curl -X GET https://a2zsoc.com/api/v1/campaigns/campaign_001/analytics \
  -H "Authorization: Bearer ***"
```

### POST /api/v1/campaigns/{campaign_id}/personalize

Generate personalized content for all accounts in a campaign.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `campaign_id` | string | Yes | Campaign identifier (path) |

**Response (201):**

```json
{
  "campaign_id": "campaign_001",
  "content_generated": 3,
  "content": [
    {
      "content_id": "content_001",
      "account_id": "acc_001",
      "content_type": "email",
      "subject": "John, see how Acme can help",
      "body": "Hi John, I noticed Acme is expanding...",
      "call_to_action": "Schedule a demo"
    }
  ]
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/campaigns/campaign_001/personalize \
  -H "Authorization: Bearer ***" \
  -H "X-Idempotency-Key: 01J0ABC1234567890"
```

### POST /api/v1/campaigns/{campaign_id}/orchestrate

Trigger channel orchestration for a campaign.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `campaign_id` | string | Yes | Campaign identifier (path) |

**Response (201):**

```json
{
  "campaign_id": "campaign_001",
  "plan_id": "plan_001",
  "execution_results": [
    {
      "channel": "email",
      "status": "sent",
      "recipients": 50
    },
    {
      "channel": "linkedin_ads",
      "status": "activated",
      "audience_size": 5000
    }
  ]
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/campaigns/campaign_001/orchestrate \
  -H "Authorization: Bearer ***" \
  -H "X-Idempotency-Key: 01J0ABC1234567890"
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
