# Content Generator API Reference

> Last updated: 2026-10-02 | Base URL: `https://a2zsoc.com`

AI-powered content creation for marketing campaigns. Generates blog posts, social media content, ad copy, email sequences, and more.

---

## Table of Contents

- [Overview](#overview)
- [Endpoints](#endpoints)
  - [POST /api/v1/content/generate](#post-api-v1contentgenerate)
  - [POST /api/v1/content/social](#post-api-v1contentsocial)
  - [POST /api/v1/content/ad-copy](#post-api-v1contentad-copy)
  - [POST /api/v1/content/email-sequence](#post-api-v1contentemail-sequence)
  - [GET /api/v1/content/{content_id}](#get-api-v1contentcontent_id)
  - [POST /api/v1/content/rewrite](#post-api-v1contentrewrite)
  - [POST /api/v1/content/seo-optimize](#post-api-v1contentseo-optimize)
- [Error Codes](#error-codes)
- [Rate Limiting](#rate-limiting)
- [Pagination](#pagination)
- [Authentication](#authentication)
- [Idempotency](#idempotency)

---

## Overview

The Content Generator API provides programmatic access to AI-powered content creation for marketing campaigns. Generates blog posts, social media content, ad copy, email sequences, and more.

**Base Path:** `/api/v1/content`

All endpoints require authentication via Bearer token and tenant scoping.

---

## Endpoints

### POST /api/v1/content/generate

Generate marketing content using AI.

**Request Body:**

```json
{
  "content_type": "blog_post",
  "topic": "10 Tips for Remote Team Productivity",
  "tone": "professional",
  "word_count": 1500,
  "keywords": ["remote work", "productivity", "team management"],
  "target_audience": "engineering managers",
  "call_to_action": "Sign up for our productivity platform"
}
```

**Response (201):**

```json
{
  "content_id": "content_abc123",
  "content_type": "blog_post",
  "title": "10 Tips for Remote Team Productivity",
  "body": "Full article content here...",
  "meta_description": "Discover 10 actionable tips...",
  "word_count": 1500,
  "reading_time_minutes": 7,
  "seo_score": 85,
  "readability_score": 78,
  "generated_at": "2026-10-01T00:00:00Z"
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/content/generate \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -H "X-Idempotency-Key: 01J0ABC1234567890" \
  -d '{
    "content_type": "blog_post",
    "topic": "Remote Work Tips"
  }'
```

---

### POST /api/v1/content/social

Generate social media content for multiple platforms.

**Request Body:**

```json
{
  "platforms": ["twitter", "linkedin", "facebook"],
  "topic": "Product Launch",
  "tone": "excited",
  "include_hashtags": true,
  "include_emojis": true
}
```

**Response (201):**

```json
{
  "content_id": "social_xyz789",
  "platforms": {
    "twitter": {
      "text": "Excited to announce our biggest launch yet!...",
      "hashtags": ["#ProductLaunch", "#Innovation"],
      "character_count": 267
    },
    "linkedin": {
      "text": "We're thrilled to share...",
      "hashtags": ["#ProductLaunch"],
      "character_count": 1200
    }
  },
  "generated_at": "2026-10-01T00:00:00Z"
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/content/social \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "platforms": ["twitter"],
    "topic": "Product Launch"
  }'
```

---

### POST /api/v1/content/ad-copy

Generate ad copy for paid campaigns.

**Request Body:**

```json
{
  "platform": "google_ads",
  "product_name": "ProductivityPro",
  "key_benefits": ["Save 10 hours/week", "AI-powered insights"],
  "call_to_action": "Start Free Trial",
  "character_limits": {
    "headline": 30,
    "description": 90
  }
}
```

**Response (201):**

```json
{
  "content_id": "ad_copy_123",
  "platform": "google_ads",
  "headlines": [
    "Save 10 Hours Every Week",
    "AI-Powered Productivity Insights",
    "Join 10,000+ Teams"
  ],
  "descriptions": [
    "ProductivityPro uses AI to automate your workflow...",
    "Start your free 14-day trial today..."
  ],
  "generated_at": "2026-10-01T00:00:00Z"
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/content/ad-copy \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "google_ads",
    "product_name": "ProductivityPro"
  }'
```

---

### POST /api/v1/content/email-sequence

Generate an email nurture sequence.

**Request Body:**

```json
{
  "sequence_name": "Welcome Series",
  "emails": 5,
  "topic": "Getting started with ProductivityPro",
  "tone": "friendly",
  "goal": "activation"
}
```

**Response (201):**

```json
{
  "content_id": "email_seq_456",
  "sequence_name": "Welcome Series",
  "emails": [
    {
      "email_number": 1,
      "subject": "Welcome to ProductivityPro!",
      "body": "Hi {name}, welcome aboard...",
      "delay_days": 0
    },
    {
      "email_number": 2,
      "subject": "Quick win: Set up your first project",
      "body": "Let's get you started...",
      "delay_days": 2
    }
  ],
  "generated_at": "2026-10-01T00:00:00Z"
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/content/email-sequence \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "sequence_name": "Welcome Series",
    "emails": 5
  }'
```

---

### GET /api/v1/content/{content_id}

Retrieve generated content by ID.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `content_id` | string | Yes | Content identifier |

**Response (200):**

```json
{
  "content_id": "content_abc123",
  "content_type": "blog_post",
  "title": "10 Tips for Remote Team Productivity",
  "body": "Full article content...",
  "word_count": 1500,
  "generated_at": "2026-10-01T00:00:00Z"
}
```

**Example:**

```bash
curl -X GET https://a2zsoc.com/api/v1/content/content_abc123 \
  -H "Authorization: Bearer <token>"
```

---

### POST /api/v1/content/rewrite

Rewrite existing content with different tone or style.

**Request Body:**

```json
{
  "content_id": "content_abc123",
  "tone": "casual",
  "target_audience": "developers"
}
```

**Response (201):**

```json
{
  "content_id": "content_abc123-v2",
  "content_type": "blog_post",
  "title": "10 Tips for Remote Team Productivity",
  "body": "Rewritten content...",
  "word_count": 1450,
  "generated_at": "2026-10-01T00:00:00Z"
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/content/rewrite \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "content_id": "content_abc123",
    "tone": "casual"
  }'
```

---

### POST /api/v1/content/seo-optimize

Optimize content for SEO.

**Request Body:**

```json
{
  "content_id": "content_abc123",
  "target_keywords": ["remote work", "productivity"],
  "content_type": "blog_post"
}
```

**Response (201):**

```json
{
  "content_id": "content_abc123_seo",
  "seo_score": 92,
  "improvements": [
    "Added meta description",
    "Improved heading structure",
    "Added internal links"
  ],
  "optimized_content": "...",
  "generated_at": "2026-10-01T00:00:00Z"
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/content/seo-optimize \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "content_id": "content_abc123",
    "target_keywords": ["remote work"]
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
