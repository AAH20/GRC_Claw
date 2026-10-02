# Lead Scorer API Reference

> Last updated: 2026-10-02 | Base URL: `https://a2zsoc.com`

AI-driven lead scoring and qualification. Scores leads based on firmographic, technographic, intent, engagement, and timing signals.

---

## Table of Contents

- [Overview](#overview)
- [Endpoints](#endpoints)
  - [POST /api/v1/leads/score](#post-api-v1leadsscore)
  - [POST /api/v1/leads/score/batch](#post-api-v1leadsscorebatch)
  - [GET /api/v1/leads/{lead_id}](#get-api-v1leadslead_id)
  - [POST /api/v1/leads/qualify](#post-api-v1leadsqualify)
  - [POST /api/v1/leads/churn-predict](#post-api-v1leadschurn-predict)
  - [POST /api/v1/leads/next-action](#post-api-v1leadsnext-action)
  - [POST /api/v1/leads/insights](#post-api-v1leadsinsights)
- [Error Codes](#error-codes)
- [Rate Limiting](#rate-limiting)
- [Pagination](#pagination)
- [Authentication](#authentication)
- [Idempotency](#idempotency)

---

## Overview

The Lead Scorer API provides programmatic access to AI-driven lead scoring and qualification. Scores leads based on firmographic, technographic, intent, engagement, and timing signals.

**Base Path:** `/api/v1/leads`

All endpoints require authentication via Bearer token and tenant scoping.

---

## Endpoints

### POST /api/v1/leads/score

Score a single lead using the AI scoring engine.

**Request Body:**

```json
{
  "lead_id": "lead_001",
  "company_name": "Acme Corp",
  "domain": "acme.com",
  "firmographic_score": 75.0,
  "technographic_score": 80.0,
  "intent_score": 65.0,
  "engagement_score": 70.0,
  "timing_score": 85.0,
  "evidence_confidence": 0.8
}
```

**Response (200):**

```json
{
  "lead_id": "lead_001",
  "total_score": 74.5,
  "grade": "B+",
  "breakdown": [
    {
      "dimension": "firmographic",
      "score": 75.0,
      "weight": 0.25,
      "weighted_score": 18.75,
      "rationale": "Strong company size and industry fit"
    },
    {
      "dimension": "technographic",
      "score": 80.0,
      "weight": 0.20,
      "weighted_score": 16.0,
      "rationale": "Uses complementary technologies"
    },
    {
      "dimension": "intent",
      "score": 65.0,
      "weight": 0.25,
      "weighted_score": 16.25,
      "rationale": "Moderate buying signals detected"
    },
    {
      "dimension": "engagement",
      "score": 70.0,
      "weight": 0.20,
      "weighted_score": 14.0,
      "rationale": "Regular email opens and site visits"
    },
    {
      "dimension": "timing",
      "score": 85.0,
      "weight": 0.10,
      "weighted_score": 8.5,
      "rationale": "Recent funding round, active evaluation"
    }
  ],
  "confidence": 0.82,
  "scoring_model": "ensemble-v3",
  "timestamp": "2026-10-01T00:00:00Z",
  "rationale": "Strong overall fit with high intent signals and favorable timing"
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/leads/score \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "lead_id": "lead_001",
    "company_name": "Acme Corp",
    "domain": "acme.com",
    "firmographic_score": 75.0,
    "technographic_score": 80.0,
    "intent_score": 65.0,
    "engagement_score": 70.0,
    "timing_score": 85.0
  }'
```

---

### POST /api/v1/leads/score/batch

Batch score multiple leads in a single request.

**Request Body:**

```json
{
  "leads": [
    {
      "lead_id": "lead_001",
      "company_name": "Acme Corp",
      "domain": "acme.com",
      "firmographic_score": 75.0,
      "technographic_score": 80.0,
      "intent_score": 65.0,
      "engagement_score": 70.0,
      "timing_score": 85.0
    }
  ]
}
```

**Response (200):**

```json
{
  "results": [
    {
      "lead_id": "lead_001",
      "total_score": 74.5,
      "grade": "B+",
      "breakdown": [],
      "confidence": 0.82,
      "scoring_model": "ensemble-v3",
      "timestamp": "2026-10-01T00:00:00Z",
      "rationale": "Strong overall fit"
    }
  ],
  "total_processed": 1,
  "total_failed": 0
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/leads/score/batch \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "leads": [
      {
        "lead_id": "lead_001",
        "company_name": "Acme",
        "domain": "acme.com"
      }
    ]
  }'
```

---

### GET /api/v1/leads/{lead_id}

Get the latest score for a lead.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `lead_id` | string | Yes | Lead identifier |

**Response (200):**

```json
{
  "lead_id": "lead_001",
  "total_score": 74.5,
  "grade": "B+",
  "breakdown": [],
  "confidence": 0.82,
  "scoring_model": "ensemble-v3",
  "timestamp": "2026-10-01T00:00:00Z",
  "rationale": "Strong overall fit"
}
```

**Example:**

```bash
curl -X GET https://a2zsoc.com/api/v1/leads/lead_001 \
  -H "Authorization: Bearer <token>"
```

---

### POST /api/v1/leads/qualify

Qualify a lead using BANT, MEDDIC, or CHAMP framework.

**Request Body:**

```json
{
  "lead_id": "lead_001",
  "company_name": "Acme Corp",
  "framework": "BANT",
  "budget": "$50,000 - $100,000",
  "authority": "CTO is decision maker",
  "need": "Need to scale infrastructure",
  "timeline": "Q1 2026"
}
```

**Response (200):**

```json
{
  "lead_id": "lead_001",
  "framework": "BANT",
  "qualified": true,
  "qualification_score": 85.0,
  "criteria": [
    {
      "name": "Budget",
      "met": true,
      "score": 90
    },
    {
      "name": "Authority",
      "met": true,
      "score": 85
    },
    {
      "name": "Need",
      "met": true,
      "score": 80
    },
    {
      "name": "Timeline",
      "met": true,
      "score": 85
    }
  ],
  "next_steps": [
    "Schedule demo with technical team",
    "Prepare ROI analysis",
    "Send case studies"
  ],
  "risk_factors": [],
  "summary": "Strong BANT qualification with all criteria met"
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/leads/qualify \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "lead_id": "lead_001",
    "company_name": "Acme Corp",
    "framework": "BANT"
  }'
```

---

### POST /api/v1/leads/churn-predict

Predict churn probability for a customer.

**Request Body:**

```json
{
  "customer_id": "cust_001",
  "company_name": "Acme Corp",
  "tenure_months": 24,
  "contract_value": 50000,
  "usage_trend": "declining",
  "support_tickets_90d": 5,
  "nps_score": 6.0,
  "engagement_score": 45.0,
  "last_login_days": 14,
  "feature_adoption_rate": 0.3,
  "stakeholder_changes": 2,
  "contract_renewal_date": "2026-12-31",
  "competitor_mentions": 3
}
```

**Response (200):**

```json
{
  "customer_id": "cust_001",
  "churn_probability": 0.72,
  "risk_level": "high",
  "risk_factors": [
    {
      "factor": "declining_usage",
      "weight": 0.3,
      "description": "Usage decreased 40% over 90 days"
    },
    {
      "factor": "low_engagement",
      "weight": 0.25,
      "description": "Last login 14 days ago"
    },
    {
      "factor": "stakeholder_changes",
      "weight": 0.2,
      "description": "2 key contacts left"
    }
  ],
  "protective_factors": [
    "Long tenure (24 months)",
    "High contract value"
  ],
  "recommended_actions": [
    "Schedule executive business review",
    "Offer training and onboarding refresh",
    "Provide dedicated success manager"
  ],
  "confidence": 0.85,
  "prediction_window_days": 90,
  "summary": "High churn risk due to declining usage and low engagement"
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/leads/churn-predict \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "cust_001",
    "company_name": "Acme Corp",
    "tenure_months": 24
  }'
```

---

### POST /api/v1/leads/next-action

Get next best action recommendation for a lead.

**Request Body:**

```json
{
  "lead_id": "lead_001",
  "company_name": "Acme Corp",
  "lead_score": 74.5,
  "grade": "B+",
  "qualified": true,
  "industry": "Technology",
  "company_size": "500-1000",
  "current_stage": "qualified",
  "last_interaction": "2026-09-28",
  "preferred_channel": "email",
  "pain_points": [
    "scaling infrastructure",
    "reducing costs"
  ],
  "interests": [
    "cloud migration",
    "automation"
  ]
}
```

**Response (200):**

```json
{
  "lead_id": "lead_001",
  "actions": [
    {
      "action": "send_personalized_email",
      "priority": 1,
      "channel": "email",
      "template": "case_study_cloud_migration",
      "timing": "within 24 hours"
    },
    {
      "action": "schedule_demo",
      "priority": 2,
      "channel": "calendar",
      "timing": "within 48 hours"
    }
  ],
  "overall_strategy": "accelerate",
  "urgency": "high",
  "next_review_date": "2026-10-08",
  "summary": "High-intent lead ready for sales engagement"
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/leads/next-action \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "lead_id": "lead_001",
    "company_name": "Acme Corp",
    "lead_score": 74.5
  }'
```

---

### POST /api/v1/leads/insights

Generate comprehensive insights for a lead.

**Request Body:**

```json
{
  "lead_id": "lead_001",
  "company_name": "Acme Corp"
}
```

**Response (200):**

```json
{
  "lead_id": "lead_001",
  "overall_assessment": "High-value prospect with strong fit",
  "key_insights": [
    {
      "type": "firmographic",
      "insight": "Ideal company size and industry"
    },
    {
      "type": "behavioral",
      "insight": "Active evaluation of solutions"
    },
    {
      "type": "competitive",
      "insight": "Currently using CompetitorX"
    }
  ],
  "action_items": [
    {
      "action": "Send competitive comparison",
      "owner": "sales",
      "due": "2026-10-05"
    },
    {
      "action": "Schedule technical demo",
      "owner": "sales",
      "due": "2026-10-08"
    }
  ],
  "opportunities": [
    "Upsell potential",
    "Expansion to other departments"
  ],
  "risks": [
    "Budget constraints",
    "Long sales cycle"
  ],
  "recommended_approach": "Solution-selling with ROI focus",
  "confidence": 0.88,
  "summary": "Strong prospect ready for targeted engagement"
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/leads/insights \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "lead_id": "lead_001",
    "company_name": "Acme Corp"
  }'
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
Authorization: Bearer <jwt_token>
```

## Idempotency

All `POST`, `PUT`, `PATCH`, and `DELETE` endpoints require an `X-Idempotency-Key` header:

```
X-Idempotency-Key: <ulid>
```

Duplicate requests with the same key return the cached response with `X-Idempotent-Replay: true`.
