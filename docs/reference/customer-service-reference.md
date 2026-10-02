# Customer Service API Reference

> Last updated: 2026-10-02 | Base URL: `https://a2zsoc.com`

Manage customer tickets, analyze sentiment, automate resolutions, and track customer health.

---

## Table of Contents

- [Overview](#overview)
- [Endpoints](#endpoints)
  - [GET /health](#get-health)
  - [POST /api/v1/tickets](#post-api-v1-tickets)
  - [GET /api/v1/tickets/{ticket_id}](#get-api-v1-tickets-ticket_id)
  - [POST /api/v1/tickets/{ticket_id}/triage](#post-api-v1-tickets-ticket_id-triage)
  - [POST /api/v1/tickets/{ticket_id}/resolve](#post-api-v1-tickets-ticket_id-resolve)
  - [POST /api/v1/tickets/{ticket_id}/escalate](#post-api-v1-tickets-ticket_id-escalate)
  - [GET /api/v1/customers/{customer_id}](#get-api-v1-customers-customer_id)
  - [POST /api/v1/customers/{customer_id}/sentiment](#post-api-v1-customers-customer_id-sentiment)
  - [POST /api/v1/customers/{customer_id}/outreach](#post-api-v1-customers-customer_id-outreach)
- [Error Codes](#error-codes)
- [Rate Limiting](#rate-limiting)
- [Pagination](#pagination)
- [Authentication](#authentication)
- [Idempotency](#idempotency)

---

## Overview

The Customer Service API provides programmatic access to manage customer tickets, analyze sentiment, automate resolutions, and track customer health.

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

### POST /api/v1/tickets

Create a new customer ticket.

**Request Body:**

```json
{
  "customer_id": "cust_001",
  "subject": "Cannot access account",
  "content": "I am unable to log in to my account after resetting my password.",
  "channel": "email",
  "metadata": {"priority": "high", "source": "web"}
}
```

**Response (201):**

```json
{
  "ticket_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "open",
  "message": "Ticket created successfully"
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/tickets \
  -H "Authorization: Bearer ***" \
  -H "Content-Type: application/json" \
  -H "X-Idempotency-Key: 01J0ABC1234567890" \
  -d '{"customer_id": "cust_001", "subject": "Cannot access account", "content": "I am unable to log in."}'
```

---

### GET /api/v1/tickets/{ticket_id}

Get ticket details by ID.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `ticket_id` | string | Yes | Ticket identifier |

**Response (200):**

```json
{
  "ticket_id": "550e8400-e29b-41d4-a716-446655440000",
  "customer_id": "cust_001",
  "subject": "Cannot access account",
  "content": "I am unable to log in to my account after resetting my password.",
  "channel": "email",
  "status": "open",
  "metadata": {"priority": "high", "source": "web"}
}
```

**Example:**

```bash
curl -X GET https://a2zsoc.com/api/v1/tickets/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer ***"
```

---

### POST /api/v1/tickets/{ticket_id}/triage

Run triage classification on a ticket.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `ticket_id` | string | Yes | Ticket identifier |

**Response (200):**

```json
{
  "category": "account_access",
  "priority": "high",
  "confidence": 0.95,
  "intent": "password_reset_issue",
  "summary": "Customer unable to access account after password reset",
  "suggested_team": "technical_support"
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/tickets/550e8400-e29b-41d4-a716-446655440000/triage \
  -H "Authorization: Bearer ***" \
  -H "X-Idempotency-Key: 01J0ABC1234567890"
```

---

### POST /api/v1/tickets/{ticket_id}/resolve

Generate resolution suggestion for a ticket.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `ticket_id` | string | Yes | Ticket identifier |

**Response (200):**

```json
{
  "suggestion": "Please try clearing your browser cache and cookies, then attempt to log in again. If the issue persists, we can manually reset your password.",
  "confidence": 0.88,
  "auto_reply": "Thank you for contacting support. Please try clearing your browser cache...",
  "escalation_recommended": false
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/tickets/550e8400-e29b-41d4-a716-446655440000/resolve \
  -H "Authorization: Bearer ***" \
  -H "X-Idempotency-Key: 01J0ABC1234567890"
```

---

### POST /api/v1/tickets/{ticket_id}/escalate

Evaluate and process ticket escalation.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `ticket_id` | string | Yes | Ticket identifier |

**Response (200):**

```json
{
  "should_escalate": true,
  "reason": "Customer has attempted self-resolution without success",
  "urgency": "high",
  "assigned_team": "senior_support",
  "context_summary": "Customer unable to access account after password reset. Self-service attempts failed."
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/tickets/550e8400-e29b-41d4-a716-446655440000/escalate \
  -H "Authorization: Bearer ***" \
  -H "X-Idempotency-Key: 01J0ABC1234567890"
```

---

### GET /api/v1/customers/{customer_id}

Get customer profile by ID.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `customer_id` | string | Yes | Customer identifier |

**Response (200):**

```json
{
  "customer_id": "cust_001",
  "name": "John Doe",
  "email": "john.doe@example.com",
  "tier": "premium",
  "metadata": {"signup_date": "2025-01-15", "plan": "enterprise"}
}
```

**Example:**

```bash
curl -X GET https://a2zsoc.com/api/v1/customers/cust_001 \
  -H "Authorization: Bearer ***"
```

---

### POST /api/v1/customers/{customer_id}/sentiment

Analyze sentiment for a customer communication.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `customer_id` | string | Yes | Customer identifier |

**Request Body:**

```json
{
  "text": "I am extremely frustrated with the service. This is unacceptable!",
  "interaction_history": [
    {"date": "2026-10-01", "channel": "email", "sentiment": "neutral"}
  ]
}
```

**Response (200):**

```json
{
  "overall_sentiment": "negative",
  "sentiment_score": -0.85,
  "satisfaction_level": "very_dissatisfied",
  "frustration_level": "high",
  "churn_risk": "high"
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/customers/cust_001/sentiment \
  -H "Authorization: Bearer ***" \
  -H "Content-Type: application/json" \
  -d '{"text": "I am extremely frustrated with the service."}'
```

---

### POST /api/v1/customers/{customer_id}/outreach

Trigger proactive customer success outreach.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `customer_id` | string | Yes | Customer identifier |

**Request Body:**

```json
{
  "customer_data": {"tier": "premium", "plan": "enterprise"},
  "interaction_history": [
    {"date": "2026-10-01", "channel": "email", "sentiment": "negative"}
  ],
  "usage_data": {"last_login": "2026-09-28", "sessions_this_month": 5}
}
```

**Response (200):**

```json
{
  "health_score": 35.0,
  "churn_risk": "high",
  "recommended_actions": [
    "Schedule executive check-in call",
    "Offer personalized onboarding session",
    "Provide account credit"
  ],
  "outreach_message": "Hi John, we noticed you've been having some challenges...",
  "engagement_level": "low"
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/customers/cust_001/outreach \
  -H "Authorization: Bearer ***" \
  -H "Content-Type: application/json" \
  -d '{"customer_data": {"tier": "premium"}, "usage_data": {"sessions_this_month": 5}}'
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
