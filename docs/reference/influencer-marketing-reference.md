# Influencer Marketing API Reference

> Last updated: 2026-10-02 | Base URL: `https://a2zsoc.com` | Version: `0.1.0`

Agentic AI platform for end-to-end influencer marketing campaign management. Discover, vet, outreach, and manage influencers across Instagram, TikTok, and YouTube.

---

## Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [Endpoints](#endpoints)
  - [Influencers](#influencers)
    - [POST /api/v1/influencers](#post--api-v1-influencers)
    - [GET /api/v1/influencers](#get--api-v1-influencers)
    - [GET /api/v1/influencers/{influencer_id}](#get--api-v1-influencers-influencer_id)
    - [PUT /api/v1/influencers/{influencer_id}](#put--api-v1-influencers-influencer_id)
    - [DELETE /api/v1/influencers/{influencer_id}](#delete--api-v1-influencers-influencer_id)
  - [Campaigns](#campaigns)
    - [POST /api/v1/campaigns](#post--api-v1-campaigns)
    - [GET /api/v1/campaigns](#get--api-v1-campaigns)
    - [GET /api/v1/campaigns/{campaign_id}](#get--api-v1-campaigns-campaign_id)
    - [PUT /api/v1/campaigns/{campaign_id}](#put--api-v1-campaigns-campaign_id)
    - [DELETE /api/v1/campaigns/{campaign_id}](#delete--api-v1-campaigns-campaign_id)
    - [GET /api/v1/campaigns/{campaign_id}/performance](#get--api-v1-campaigns-campaign_id-performance)
    - [POST /api/v1/campaigns/{campaign_id}/launch](#post--api-v1-campaigns-campaign_id-launch)
- [Error Codes](#error-codes)
- [Rate Limiting](#rate-limiting)
- [Pagination](#pagination)
- [Idempotency](#idempotency)
- [Webhooks](#webhooks)

---

## Overview

The Influencer Marketing API provides programmatic access to manage influencer relationships, campaigns, and track performance across social platforms.

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

### Influencers

#### POST /api/v1/influencers

Add a new influencer to the platform.

**Request Body:**

```json
{
  "name": "Jane Smith",
  "handle": "@janesmith",
  "platform": "instagram",
  "followers": 50000,
  "niche": "technology",
  "email": "jane@example.com",
  "location": "San Francisco, CA",
  "language": "en",
  "categories": ["tech", "gadgets", "software"],
  "engagement_rate": 0.045,
  "profile_url": "https://instagram.com/janesmith",
  "profile_image_url": "https://cdn.example.com/images/janesmith.jpg",
  "metadata": {}
}
```

**Response (201):**

```json
{
  "influencer_id": "inf_001",
  "name": "Jane Smith",
  "handle": "@janesmith",
  "platform": "instagram",
  "followers": 50000,
  "niche": "technology",
  "status": "active",
  "created_at": "2026-10-01T00:00:00Z"
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/influencers \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -H "X-Idempotency-Key: 01J0ABC1234567890" \
  -d '{"name": "Jane Smith", "handle": "@janesmith", "platform": "instagram"}'
```

---

#### GET /api/v1/influencers

List all influencers.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `platform` | string | No | Filter by platform: `instagram`, `tiktok`, `youtube` |
| `niche` | string | No | Filter by niche |
| `status` | string | No | Filter by status: `active`, `inactive`, `pending` |
| `min_followers` | integer | No | Minimum follower count |
| `max_followers` | integer | No | Maximum follower count |
| `cursor` | string | No | Pagination cursor |
| `limit` | integer | No | Items per page (default: 20, max: 100) |

**Response (200):**

```json
{
  "data": [
    {
      "influencer_id": "inf_001",
      "name": "Jane Smith",
      "handle": "@janesmith",
      "platform": "instagram",
      "followers": 50000,
      "niche": "technology",
      "status": "active",
      "engagement_rate": 0.045,
      "created_at": "2026-10-01T00:00:00Z"
    }
  ],
  "pagination": {
    "cursor": "eyJpZCI6ImlmZl8wMDEifQ==",
    "hasMore": true,
    "totalCount": 150
  }
}
```

**Example:**

```bash
curl -X GET "https://a2zsoc.com/api/v1/influencers?platform=instagram&niche=technology" \
  -H "Authorization: Bearer <token>"
```

---

#### GET /api/v1/influencers/{influencer_id}

Get a specific influencer by ID.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `influencer_id` | string | Yes | Influencer identifier |

**Response (200):**

```json
{
  "influencer_id": "inf_001",
  "name": "Jane Smith",
  "handle": "@janesmith",
  "platform": "instagram",
  "followers": 50000,
  "following_count": 1200,
  "post_count": 350,
  "engagement_rate": 0.045,
  "niche": "technology",
  "email": "jane@example.com",
  "location": "San Francisco, CA",
  "language": "en",
  "categories": ["tech", "gadgets"],
  "profile_url": "https://instagram.com/janesmith",
  "profile_image_url": "https://cdn.example.com/images/janesmith.jpg",
  "status": "active",
  "metadata": {},
  "created_at": "2026-10-01T00:00:00Z",
  "updated_at": "2026-10-01T00:00:00Z"
}
```

**Example:**

```bash
curl -X GET https://a2zsoc.com/api/v1/influencers/inf_001 \
  -H "Authorization: Bearer <token>"
```

---

#### PUT /api/v1/influencers/{influencer_id}

Update an existing influencer.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `influencer_id` | string | Yes | Influencer identifier |

**Request Body:**

```json
{
  "name": "Jane Smith Updated",
  "followers": 55000,
  "status": "active",
  "metadata": {}
}
```

**Response (200):**

```json
{
  "influencer_id": "inf_001",
  "name": "Jane Smith Updated",
  "followers": 55000,
  "status": "active",
  "updated_at": "2026-10-01T12:00:00Z"
}
```

**Example:**

```bash
curl -X PUT https://a2zsoc.com/api/v1/influencers/inf_001 \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"followers": 55000}'
```

---

#### DELETE /api/v1/influencers/{influencer_id}

Delete an influencer.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `influencer_id` | string | Yes | Influencer identifier |

**Response:** `204 No Content`

**Example:**

```bash
curl -X DELETE https://a2zsoc.com/api/v1/influencers/inf_001 \
  -H "Authorization: Bearer <token>" \
  -H "X-Idempotency-Key: 01J0ABC1234567890"
```

---

### Campaigns

#### POST /api/v1/campaigns

Create an influencer marketing campaign.

**Request Body:**

```json
{
  "name": "Product Launch 2026",
  "description": "Q4 product launch influencer campaign",
  "influencer_ids": ["inf_001", "inf_002"],
  "budget": 10000,
  "deliverables": [
    {
      "type": "post",
      "count": 3,
      "platform": "instagram",
      "requirements": "Product mention with image"
    },
    {
      "type": "story",
      "count": 5,
      "platform": "instagram",
      "requirements": "Swipe-up link to product page"
    }
  ],
  "start_date": "2026-10-15",
  "end_date": "2026-11-15",
  "status": "draft"
}
```

**Response (201):**

```json
{
  "campaign_id": "inf_camp_001",
  "name": "Product Launch 2026",
  "description": "Q4 product launch influencer campaign",
  "status": "draft",
  "influencer_count": 2,
  "budget": 10000,
  "deliverables": [
    {"type": "post", "count": 3},
    {"type": "story", "count": 5}
  ],
  "start_date": "2026-10-15",
  "end_date": "2026-11-15",
  "created_at": "2026-10-01T00:00:00Z"
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/campaigns \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -H "X-Idempotency-Key: 01J0ABC1234567890" \
  -d '{"name": "Product Launch", "influencer_ids": ["inf_001"]}'
```

---

#### GET /api/v1/campaigns

List all campaigns.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `status` | string | No | Filter by status: `draft`, `active`, `paused`, `completed` |
| `cursor` | string | No | Pagination cursor |
| `limit` | integer | No | Items per page (default: 20, max: 100) |

**Response (200):**

```json
{
  "data": [
    {
      "campaign_id": "inf_camp_001",
      "name": "Product Launch 2026",
      "status": "active",
      "influencer_count": 2,
      "budget": 10000,
      "created_at": "2026-10-01T00:00:00Z"
    }
  ],
  "pagination": {
    "cursor": "eyJpZCI6ImluZl9jYW1wXzAwMSJ9",
    "hasMore": false,
    "totalCount": 1
  }
}
```

**Example:**

```bash
curl -X GET "https://a2zsoc.com/api/v1/campaigns?status=active" \
  -H "Authorization: Bearer <token>"
```

---

#### GET /api/v1/campaigns/{campaign_id}

Get a campaign by ID.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `campaign_id` | string | Yes | Campaign identifier |

**Response (200):**

```json
{
  "campaign_id": "inf_camp_001",
  "name": "Product Launch 2026",
  "status": "active",
  "influencer_ids": ["inf_001", "inf_002"],
  "budget": 10000,
  "deliverables": [],
  "start_date": "2026-10-15",
  "end_date": "2026-11-15",
  "created_at": "2026-10-01T00:00:00Z",
  "updated_at": "2026-10-01T00:00:00Z"
}
```

**Example:**

```bash
curl -X GET https://a2zsoc.com/api/v1/campaigns/inf_camp_001 \
  -H "Authorization: Bearer <token>"
```

---

#### PUT /api/v1/campaigns/{campaign_id}

Update a campaign.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `campaign_id` | string | Yes | Campaign identifier |

**Request Body:**

```json
{
  "name": "Updated Campaign Name",
  "status": "paused",
  "budget": 15000
}
```

**Response (200):**

```json
{
  "campaign_id": "inf_camp_001",
  "name": "Updated Campaign Name",
  "status": "paused",
  "budget": 15000,
  "updated_at": "2026-10-01T12:00:00Z"
}
```

**Example:**

```bash
curl -X PUT https://a2zsoc.com/api/v1/campaigns/inf_camp_001 \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"status": "paused"}'
```

---

#### DELETE /api/v1/campaigns/{campaign_id}

Delete a campaign.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `campaign_id` | string | Yes | Campaign identifier |

**Response:** `204 No Content`

**Example:**

```bash
curl -X DELETE https://a2zsoc.com/api/v1/campaigns/inf_camp_001 \
  -H "Authorization: Bearer <token>" \
  -H "X-Idempotency-Key: 01J0ABC1234567890"
```

---

#### GET /api/v1/campaigns/{campaign_id}/performance

Get campaign performance metrics.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `campaign_id` | string | Yes | Campaign identifier |

**Response (200):**

```json
{
  "campaign_id": "inf_camp_001",
  "impressions": 250000,
  "engagements": 12500,
  "reach": 200000,
  "engagement_rate": 0.05,
  "conversions": 150,
  "spend": 8500,
  "roas": 3.2,
  "cost_per_engagement": 0.68,
  "cost_per_impression": 0.034,
  "influencer_breakdown": [
    {
      "influencer_id": "inf_001",
      "impressions": 150000,
      "engagements": 8000,
      "conversions": 100
    }
  ],
  "period": {
    "start": "2026-10-15",
    "end": "2026-11-15"
  }
}
```

**Example:**

```bash
curl -X GET https://a2zsoc.com/api/v1/campaigns/inf_camp_001/performance \
  -H "Authorization: Bearer <token>"
```

---

#### POST /api/v1/campaigns/{campaign_id}/launch

Launch a draft campaign.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `campaign_id` | string | Yes | Campaign identifier |

**Response (200):**

```json
{
  "campaign_id": "inf_camp_001",
  "status": "active",
  "launched_at": "2026-10-01T00:00:00Z"
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/campaigns/inf_camp_001/launch \
  -H "Authorization: Bearer <token>"
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

Subscribe to campaign and influencer events:

| Event | Description |
|-------|-------------|
| `influencer.created` | New influencer added |
| `influencer.updated` | Influencer profile updated |
| `campaign.created` | New campaign created |
| `campaign.launched` | Campaign moved to active |
| `campaign.completed` | Campaign finished |
| `campaign.performance.updated` | Performance metrics updated |

**Webhook Payload:**

```json
{
  "event": "campaign.launched",
  "timestamp": "2026-10-01T00:00:00Z",
  "data": {
    "campaign_id": "inf_camp_001",
    "status": "active",
    "launched_at": "2026-10-01T00:00:00Z"
  }
}
```
