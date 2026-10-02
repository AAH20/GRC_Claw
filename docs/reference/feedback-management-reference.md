# Feedback Management API Reference

> Last updated: 2026-10-02 | Base URL: `https://a2zsoc.com` | Version: `0.1.0`

Agentic AI-powered feedback collection, analysis, and response system. NPS surveys, sentiment analysis, feedback routing, and automated response generation.

---

## Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [Endpoints](#endpoints)
  - [Feedback](#feedback)
    - [POST /api/v1/feedback](#post--api-v1-feedback)
    - [GET /api/v1/feedback](#get--api-v1-feedback)
    - [GET /api/v1/feedback/{feedback_id}](#get--api-v1-feedback-feedback_id)
    - [PUT /api/v1/feedback/{feedback_id}](#put--api-v1-feedback-feedback_id)
    - [DELETE /api/v1/feedback/{feedback_id}](#delete--api-v1-feedback-feedback_id)
  - [Surveys](#surveys)
    - [POST /api/v1/surveys](#post--api-v1-surveys)
    - [GET /api/v1/surveys](#get--api-v1-surveys)
    - [GET /api/v1/surveys/{survey_id}](#get--api-v1-surveys-survey_id)
    - [POST /api/v1/surveys/{survey_id}/responses](#post--api-v1-surveys-survey_id-responses)
  - [Sentiment](#sentiment)
    - [GET /api/v1/feedback/sentiment](#get--api-v1-feedback-sentiment)
    - [POST /api/v1/feedback/analyze](#post--api-v1-feedback-analyze)
  - [Responses](#responses)
    - [POST /api/v1/feedback/{feedback_id}/respond](#post--api-v1-feedback-feedback_id-respond)
- [Error Codes](#error-codes)
- [Rate Limiting](#rate-limiting)
- [Pagination](#pagination)
- [Idempotency](#idempotency)
- [Webhooks](#webhooks)

---

## Overview

The Feedback Management API provides programmatic access to collect, analyze, and act on customer feedback. NPS surveys, sentiment analysis, and feedback routing.

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

### Feedback

#### POST /api/v1/feedback

Submit new feedback.

**Request Body:**

```json
{
  "customer_id": "cust_001",
  "customer_email": "customer@example.com",
  "type": "nps",
  "rating": 9,
  "comment": "Great product, love the new features!",
  "source": "email",
  "metadata": {
    "product_version": "2.0",
    "platform": "web"
  },
  "tags": ["product", "positive"]
}
```

**Response (201):**

```json
{
  "feedback_id": "fb_001",
  "customer_id": "cust_001",
  "type": "nps",
  "rating": 9,
  "comment": "Great product, love the new features!",
  "sentiment": "positive",
  "status": "new",
  "source": "email",
  "created_at": "2026-10-01T00:00:00Z"
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/feedback \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -H "X-Idempotency-Key: 01J0ABC1234567890" \
  -d '{"customer_id": "cust_001", "type": "nps", "rating": 9}'
```

---

#### GET /api/v1/feedback

List all feedback.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `type` | string | No | Filter by type: `nps`, `csat`, `ces`, `review`, `complaint` |
| `status` | string | No | Filter by status: `new`, `in_review`, `responded`, `closed` |
| `sentiment` | string | No | Filter by sentiment: `positive`, `neutral`, `negative` |
| `rating_min` | integer | No | Minimum rating |
| `rating_max` | integer | No | Maximum rating |
| `start_date` | string | No | Filter by start date (ISO 8601) |
| `end_date` | string | No | Filter by end date (ISO 8601) |
| `cursor` | string | No | Pagination cursor |
| `limit` | integer | No | Items per page (default: 20, max: 100) |

**Response (200):**

```json
{
  "data": [
    {
      "feedback_id": "fb_001",
      "customer_id": "cust_001",
      "type": "nps",
      "rating": 9,
      "sentiment": "positive",
      "status": "new",
      "source": "email",
      "created_at": "2026-10-01T00:00:00Z"
    }
  ],
  "pagination": {
    "cursor": "eyJpZCI6ImZiXzAwMSJ9",
    "hasMore": false,
    "totalCount": 1
  }
}
```

**Example:**

```bash
curl -X GET "https://a2zsoc.com/api/v1/feedback?sentiment=positive&type=nps" \
  -H "Authorization: Bearer <token>"
```

---

#### GET /api/v1/feedback/{feedback_id}

Get feedback by ID.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `feedback_id` | string | Yes | Feedback identifier |

**Response (200):**

```json
{
  "feedback_id": "fb_001",
  "customer_id": "cust_001",
  "customer_email": "customer@example.com",
  "type": "nps",
  "rating": 9,
  "comment": "Great product, love the new features!",
  "sentiment": "positive",
  "status": "new",
  "source": "email",
  "metadata": {"product_version": "2.0", "platform": "web"},
  "tags": ["product", "positive"],
  "response": null,
  "created_at": "2026-10-01T00:00:00Z",
  "updated_at": "2026-10-01T00:00:00Z"
}
```

**Example:**

```bash
curl -X GET https://a2zsoc.com/api/v1/feedback/fb_001 \
  -H "Authorization: Bearer <token>"
```

---

#### PUT /api/v1/feedback/{feedback_id}

Update feedback.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `feedback_id` | string | Yes | Feedback identifier |

**Request Body:**

```json
{
  "status": "in_review",
  "tags": ["product", "positive", "featured"],
  "metadata": {"priority": "high"}
}
```

**Response (200):**

```json
{
  "feedback_id": "fb_001",
  "status": "in_review",
  "tags": ["product", "positive", "featured"],
  "updated_at": "2026-10-01T12:00:00Z"
}
```

**Example:**

```bash
curl -X PUT https://a2zsoc.com/api/v1/feedback/fb_001 \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"status": "in_review"}'
```

---

#### DELETE /api/v1/feedback/{feedback_id}

Delete feedback.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `feedback_id` | string | Yes | Feedback identifier |

**Response:** `204 No Content`

**Example:**

```bash
curl -X DELETE https://a2zsoc.com/api/v1/feedback/fb_001 \
  -H "Authorization: Bearer <token>" \
  -H "X-Idempotency-Key: 01J0ABC1234567890"
```

---

### Surveys

#### POST /api/v1/surveys

Create a feedback survey.

**Request Body:**

```json
{
  "name": "NPS Survey",
  "type": "nps",
  "description": "Quarterly NPS survey",
  "questions": [
    {
      "text": "How likely are you to recommend us?",
      "type": "scale",
      "min": 0,
      "max": 10,
      "required": true
    },
    {
      "text": "What could we improve?",
      "type": "text",
      "required": false
    }
  ],
  "target_audience": "all_customers",
  "start_date": "2026-10-01",
  "end_date": "2026-10-31",
  "status": "draft"
}
```

**Response (201):**

```json
{
  "survey_id": "survey_001",
  "name": "NPS Survey",
  "type": "nps",
  "status": "draft",
  "questions_count": 2,
  "created_at": "2026-10-01T00:00:00Z"
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/surveys \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "NPS Survey", "type": "nps"}'
```

---

#### GET /api/v1/surveys

List all surveys.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `status` | string | No | Filter by status: `draft`, `active`, `closed` |
| `type` | string | No | Filter by type: `nps`, `csat`, `ces` |
| `cursor` | string | No | Pagination cursor |
| `limit` | integer | No | Items per page (default: 20, max: 100) |

**Response (200):**

```json
{
  "data": [
    {
      "survey_id": "survey_001",
      "name": "NPS Survey",
      "type": "nps",
      "status": "active",
      "responses_count": 150,
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
curl -X GET "https://a2zsoc.com/api/v1/surveys?status=active" \
  -H "Authorization: Bearer <token>"
```

---

#### GET /api/v1/surveys/{survey_id}

Get a survey by ID.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `survey_id` | string | Yes | Survey identifier |

**Response (200):**

```json
{
  "survey_id": "survey_001",
  "name": "NPS Survey",
  "type": "nps",
  "description": "Quarterly NPS survey",
  "status": "active",
  "questions": [
    {"text": "How likely are you to recommend us?", "type": "scale", "min": 0, "max": 10}
  ],
  "responses_count": 150,
  "nps_score": 45,
  "created_at": "2026-10-01T00:00:00Z"
}
```

**Example:**

```bash
curl -X GET https://a2zsoc.com/api/v1/surveys/survey_001 \
  -H "Authorization: Bearer <token>"
```

---

#### POST /api/v1/surveys/{survey_id}/responses

Submit a survey response.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `survey_id` | string | Yes | Survey identifier |

**Request Body:**

```json
{
  "respondent_id": "cust_001",
  "answers": [
    {"question_index": 0, "value": 9},
    {"question_index": 1, "value": "More integrations would be great"}
  ],
  "metadata": {"completion_time_seconds": 45}
}
```

**Response (201):**

```json
{
  "response_id": "resp_001",
  "survey_id": "survey_001",
  "respondent_id": "cust_001",
  "nps_category": "promoter",
  "submitted_at": "2026-10-01T00:00:00Z"
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/surveys/survey_001/responses \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"respondent_id": "cust_001", "answers": [{"question_index": 0, "value": 9}]}'
```

---

### Sentiment

#### GET /api/v1/feedback/sentiment

Get sentiment analysis for feedback.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `start_date` | string | No | Start date (ISO 8601) |
| `end_date` | string | No | End date (ISO 8601) |
| `type` | string | No | Filter by feedback type |

**Response (200):**

```json
{
  "positive": 0.65,
  "neutral": 0.25,
  "negative": 0.10,
  "total_responses": 1000,
  "trend": "improving",
  "period": {"start": "2026-09-01", "end": "2026-09-30"},
  "top_positive_themes": ["ease of use", "customer support", "features"],
  "top_negative_themes": ["pricing", "learning curve", "bugs"]
}
```

**Example:**

```bash
curl -X GET "https://a2zsoc.com/api/v1/feedback/sentiment?start_date=2026-09-01&end_date=2026-09-30" \
  -H "Authorization: Bearer <token>"
```

---

#### POST /api/v1/feedback/analyze

Analyze sentiment of a text.

**Request Body:**

```json
{
  "text": "This product has transformed our workflow. Highly recommended!",
  "language": "en",
  "aspects": ["product", "workflow", "recommendation"]
}
```

**Response (200):**

```json
{
  "sentiment": "positive",
  "score": 0.92,
  "confidence": 0.95,
  "aspects": [
    {"aspect": "product", "sentiment": "positive", "score": 0.88},
    {"aspect": "workflow", "sentiment": "positive", "score": 0.95},
    {"aspect": "recommendation", "sentiment": "positive", "score": 0.93}
  ],
  "key_phrases": ["transformed our workflow", "highly recommended"]
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/feedback/analyze \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"text": "Great product!"}'
```

---

### Responses

#### POST /api/v1/feedback/{feedback_id}/respond

Generate or submit a response to feedback.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `feedback_id` | string | Yes | Feedback identifier |

**Request Body:**

```json
{
  "message": "Thank you for your feedback! We're glad you're enjoying the new features.",
  "auto_generate": false,
  "send_email": true,
  "status": "responded"
}
```

**Response (200):**

```json
{
  "feedback_id": "fb_001",
  "response_id": "resp_001",
  "message": "Thank you for your feedback!",
  "status": "responded",
  "responded_at": "2026-10-01T00:00:00Z"
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/feedback/fb_001/respond \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"message": "Thank you!", "send_email": true}'
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

---

## Webhooks

Subscribe to feedback events:

| Event | Description |
|-------|-------------|
| `feedback.created` | New feedback submitted |
| `feedback.responded` | Response sent to feedback |
| `feedback.sentiment_flagged` | Negative sentiment detected |
| `survey.created` | New survey created |
| `survey.response` | Survey response submitted |

**Webhook Payload:**

```json
{
  "event": "feedback.created",
  "timestamp": "2026-10-01T00:00:00Z",
  "data": {
    "feedback_id": "fb_001",
    "type": "nps",
    "rating": 9,
    "sentiment": "positive"
  }
}
```
