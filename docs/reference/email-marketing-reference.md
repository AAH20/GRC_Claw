# Email Marketing API Reference

> Last updated: 2026-10-02 | Base URL: `https://a2zsoc.com`

Create, manage, and track email campaigns, automate sequences, and analyze engagement metrics.

---

## Table of Contents

- [Overview](#overview)
- [Endpoints](#endpoints)
  - [GET /health](#get-health)
  - [POST /api/v1/campaigns](#post-api-v1-campaigns)
  - [GET /api/v1/campaigns](#get-api-v1-campaigns)
  - [GET /api/v1/campaigns/{campaign_id}](#get-api-v1-campaigns-campaign_id)
  - [PUT /api/v1/campaigns/{campaign_id}](#put-api-v1-campaigns-campaign_id)
  - [DELETE /api/v1/campaigns/{campaign_id}](#delete-api-v1-campaigns-campaign_id)
  - [POST /api/v1/campaigns/{campaign_id}/send](#post-api-v1-campaigns-campaign_id-send)
  - [POST /api/v1/campaigns/{campaign_id}/schedule](#post-api-v1-campaigns-campaign_id-schedule)
  - [GET /api/v1/campaigns/{campaign_id}/stats](#get-api-v1-campaigns-campaign_id-stats)
  - [POST /api/v1/segments](#post-api-v1-segments)
  - [GET /api/v1/segments](#get-api-v1-segments)
  - [GET /api/v1/segments/{segment_id}](#get-api-v1-segments-segment_id)
  - [PUT /api/v1/segments/{segment_id}](#put-api-v1-segments-segment_id)
  - [DELETE /api/v1/segments/{segment_id}](#delete-api-v1-segments-segment_id)
  - [POST /api/v1/templates](#post-api-v1-templates)
  - [GET /api/v1/templates](#get-api-v1-templates)
  - [GET /api/v1/templates/{template_id}](#get-api-v1-templates-template_id)
  - [PUT /api/v1/templates/{template_id}](#put-api-v1-templates-template_id)
  - [DELETE /api/v1/templates/{template_id}](#delete-api-v1-templates-template_id)
  - [POST /api/v1/automations](#post-api-v1-automations)
  - [GET /api/v1/automations](#get-api-v1-automations)
  - [GET /api/v1/automations/{automation_id}](#get-api-v1-automations-automation_id)
  - [PUT /api/v1/automations/{automation_id}](#put-api-v1-automations-automation_id)
  - [DELETE /api/v1/automations/{automation_id}](#delete-api-v1-automations-automation_id)
  - [POST /api/v1/automations/{automation_id}/activate](#post-api-v1-automations-automation_id-activate)
  - [POST /api/v1/automations/{automation_id}/deactivate](#post-api-v1-automations-automation_id-deactivate)
  - [POST /api/v1/subscribers](#post-api-v1-subscribers)
  - [GET /api/v1/subscribers](#get-api-v1-subscribers)
  - [GET /api/v1/subscribers/{subscriber_id}](#get-api-v1-subscribers-subscriber_id)
  - [PUT /api/v1/subscribers/{subscriber_id}](#put-api-v1-subscribers-subscriber_id)
  - [DELETE /api/v1/subscribers/{subscriber_id}](#delete-api-v1-subscribers-subscriber_id)
  - [POST /api/v1/subscribers/{subscriber_id}/unsubscribe](#post-api-v1-subscribers-subscriber_id-unsubscribe)
- [Error Codes](#error-codes)
- [Rate Limiting](#rate-limiting)
- [Pagination](#pagination)
- [Authentication](#authentication)
- [Idempotency](#idempotency)

---

## Overview

The Email Marketing API provides programmatic access to create, manage, and track email campaigns, automate sequences, and analyze engagement metrics.

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

### POST /api/v1/campaigns

Create a new email campaign.

**Request Body:**

```json
{
  "name": "October Newsletter",
  "subject": "Your October Update",
  "from_name": "Marketing Team",
  "from_email": "marketing@example.com",
  "template_id": "tmpl_001",
  "segment_id": "seg_001",
  "status": "draft"
}
```

**Response (201):**

```json
{
  "id": "camp_001",
  "name": "October Newsletter",
  "subject": "Your October Update",
  "from_name": "Marketing Team",
  "from_email": "marketing@example.com",
  "template_id": "tmpl_001",
  "segment_id": "seg_001",
  "status": "draft",
  "created_at": "2026-10-02T10:00:00Z"
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/campaigns \
  -H "Authorization: Bearer ***" \
  -H "Content-Type: application/json" \
  -H "X-Idempotency-Key: 01J0ABC1234567890" \
  -d '{"name": "October Newsletter", "subject": "Your October Update"}'
```

---

### GET /api/v1/campaigns

List all campaigns.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `page` | integer | No | Page number |
| `page_size` | integer | No | Items per page |
| `status` | string | No | Filter by status: `draft`, `scheduled`, `sent`, `archived` |

**Response (200):**

```json
{
  "data": [
    {
      "id": "camp_001",
      "name": "October Newsletter",
      "status": "draft"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20
}
```

**Example:**

```bash
curl -X GET "https://a2zsoc.com/api/v1/campaigns?status=draft" \
  -H "Authorization: Bearer ***"
```

---

### GET /api/v1/campaigns/{campaign_id}

Get a campaign by ID.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `campaign_id` | string | Yes | Campaign identifier |

**Response (200):**

```json
{
  "id": "camp_001",
  "name": "October Newsletter",
  "subject": "Your October Update",
  "status": "draft",
  "created_at": "2026-10-02T10:00:00Z"
}
```

**Example:**

```bash
curl -X GET https://a2zsoc.com/api/v1/campaigns/camp_001 \
  -H "Authorization: Bearer ***"
```

---

### PUT /api/v1/campaigns/{campaign_id}

Update a campaign.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `campaign_id` | string | Yes | Campaign identifier |

**Request Body:**

```json
{
  "name": "Updated Newsletter Name",
  "subject": "Updated Subject"
}
```

**Response (200):**

```json
{
  "id": "camp_001",
  "name": "Updated Newsletter Name",
  "subject": "Updated Subject",
  "status": "draft"
}
```

**Example:**

```bash
curl -X PUT https://a2zsoc.com/api/v1/campaigns/camp_001 \
  -H "Authorization: Bearer ***" \
  -H "Content-Type: application/json" \
  -d '{"name": "Updated Newsletter Name"}'
```

---

### DELETE /api/v1/campaigns/{campaign_id}

Delete a campaign.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `campaign_id` | string | Yes | Campaign identifier |

**Example:**

```bash
curl -X DELETE https://a2zsoc.com/api/v1/campaigns/camp_001 \
  -H "Authorization: Bearer ***" \
  -H "X-Idempotency-Key: 01J0ABC1234567890"
```

---

### POST /api/v1/campaigns/{campaign_id}/send

Send a campaign immediately.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `campaign_id` | string | Yes | Campaign identifier |

**Response (200):**

```json
{
  "campaign_id": "camp_001",
  "status": "sending",
  "recipients_count": 5000
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/campaigns/camp_001/send \
  -H "Authorization: Bearer ***" \
  -H "X-Idempotency-Key: 01J0ABC1234567890"
```

---

### POST /api/v1/campaigns/{campaign_id}/schedule

Schedule a campaign for future delivery.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `campaign_id` | string | Yes | Campaign identifier |

**Request Body:**

```json

{
  "scheduled_at": "2026-10-05T14:00:00Z"
}
```

**Response (200):**

```json
{
  "campaign_id": "camp_001",
  "status": "scheduled",
  "scheduled_at": "2026-10-05T14:00:00Z"
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/campaigns/camp_001/schedule \
  -H "Authorization: Bearer ***" \
  -H "Content-Type: application/json" \
  -d '{"scheduled_at": "2026-10-05T14:00:00Z"}'
```

---

### GET /api/v1/campaigns/{campaign_id}/stats

Get campaign performance statistics.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `campaign_id` | string | Yes | Campaign identifier |

**Response (200):**

```json
{
  "campaign_id": "camp_001",
  "recipients": 5000,
  "delivered": 4950,
  "opened": 2000,
  "clicked": 800,
  "bounced": 50,
  "unsubscribed": 10,
  "open_rate": 0.404,
  "click_rate": 0.162,
  "bounce_rate": 0.01
}
```

**Example:**

```bash
curl -X GET https://a2zsoc.com/api/v1/campaigns/camp_001/stats \
  -H "Authorization: Bearer ***"
```

---

### POST /api/v1/segments

Create a new subscriber segment.

**Request Body:**

```json
{
  "name": "Active Customers",
  "description": "Customers who purchased in the last 90 days",
  "criteria": {
    "field": "last_purchase_date",
    "operator": "within_days",
    "value": 90
  }
}
```

**Response (201):**

```json
{
  "id": "seg_001",
  "name": "Active Customers",
  "description": "Customers who purchased in the last 90 days",
  "criteria": {
    "field": "last_purchase_date",
    "operator": "within_days",
    "value": 90
  },
  "created_at": "2026-10-02T10:00:00Z"
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/segments \
  -H "Authorization: Bearer ***" \
  -H "Content-Type: application/json" \
  -d '{"name": "Active Customers"}'
```

---

### GET /api/v1/segments

List all segments.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `page` | integer | No | Page number |
| `page_size` | integer | No | Items per page |

**Response (200):**

```json
{
  "data": [
    {
      "id": "seg_001",
      "name": "Active Customers"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20
}
```

**Example:**

```bash
curl -X GET https://a2zsoc.com/api/v1/segments \
  -H "Authorization: Bearer ***"
```

---

### GET /api/v1/segments/{segment_id}

Get a segment by ID.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `segment_id` | string | Yes | Segment identifier |

**Response (200):**

```json
{
  "id": "seg_001",
  "name": "Active Customers",
  "description": "Customers who purchased in the last 90 days"
}
```

**Example:**

```bash
curl -X GET https://a2zsoc.com/api/v1/segments/seg_001 \
  -H "Authorization: Bearer ***"
```

---

### PUT /api/v1/segments/{segment_id}

Update a segment.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `segment_id` | string | Yes | Segment identifier |

**Request Body:**

```json
{
  "name": "VIP Customers"
}
```

**Response (200):**

```json
{
  "id": "seg_001",
  "name": "VIP Customers"
}
```

**Example:**

```bash
curl -X PUT https://a2zsoc.com/api/v1/segments/seg_001 \
  -H "Authorization: Bearer ***" \
  -H "Content-Type: application/json" \
  -d '{"name": "VIP Customers"}'
```

---

### DELETE /api/v1/segments/{segment_id}

Delete a segment.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `segment_id` | string | Yes | Segment identifier |

**Example:**

```bash
curl -X DELETE https://a2zsoc.com/api/v1/segments/seg_001 \
  -H "Authorization: Bearer ***" \
  -H "X-Idempotency-Key: 01J0ABC1234567890"
```

---

### POST /api/v1/templates

Create a new email template.

**Request Body:**

```json
{
  "name": "Welcome Email",
  "subject": "Welcome to Our Platform!",
  "html_content": "<h1>Welcome!</h1><p>Thanks for joining us.</p>",
  "text_content": "Welcome! Thanks for joining us."
}
```

**Response (201):**

```json
{
  "id": "tmpl_001",
  "name": "Welcome Email",
  "subject": "Welcome to Our Platform!",
  "html_content": "<h1>Welcome!</h1><p>Thanks for joining us.</p>",
  "text_content": "Welcome! Thanks for joining us.",
  "created_at": "2026-10-02T10:00:00Z"
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/templates \
  -H "Authorization: Bearer ***" \
  -H "Content-Type: application/json" \
  -d '{"name": "Welcome Email", "subject": "Welcome!"}'
```

---

### GET /api/v1/templates

List all templates.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `page` | integer | No | Page number |
| `page_size` | integer | No | Items per page |

**Response (200):**

```json
{
  "data": [
    {
      "id": "tmpl_001",
      "name": "Welcome Email"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20
}
```

**Example:**

```bash
curl -X GET https://a2zsoc.com/api/v1/templates \
  -H "Authorization: Bearer ***"
```

---

### GET /api/v1/templates/{template_id}

Get a template by ID.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `template_id` | string | Yes | Template identifier |

**Response (200):**

```json
{
  "id": "tmpl_001",
  "name": "Welcome Email",
  "subject": "Welcome to Our Platform!"
}
```

**Example:**

```bash
curl -X GET https://a2zsoc.com/api/v1/templates/tmpl_001 \
  -H "Authorization: Bearer ***"
```

---

### PUT /api/v1/templates/{template_id}

Update a template.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `template_id` | string | Yes | Template identifier |

**Request Body:**

```json
{
  "name": "Updated Welcome Email"
}
```

**Response (200):**

```json
{
  "id": "tmpl_001",
  "name": "Updated Welcome Email"
}
```

**Example:**

```bash
curl -X PUT https://a2zsoc.com/api/v1/templates/tmpl_001 \
  -H "Authorization: Bearer ***" \
  -H "Content-Type: application/json" \
  -d '{"name": "Updated Welcome Email"}'
```

---

### DELETE /api/v1/templates/{template_id}

Delete a template.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `template_id` | string | Yes | Template identifier |

**Example:**

```bash
curl -X DELETE https://a2zsoc.com/api/v1/templates/tmpl_001 \
  -H "Authorization: Bearer ***" \
  -H "X-Idempotency-Key: 01J0ABC1234567890"
```

---

### POST /api/v1/automations

Create a new automation sequence.

**Request Body:**

```json
{
  "name": "Welcome Series",
  "trigger": "subscriber_added",
  "steps": [
    {
      "type": "email",
      "template_id": "tmpl_001",
      "delay_days": 0
    },
    {
      "type": "email",
      "template_id": "tmpl_002",
      "delay_days": 3
    }
  ],
  "status": "draft"
}
```

**Response (201):**

```json
{
  "id": "auto_001",
  "name": "Welcome Series",
  "trigger": "subscriber_added",
  "steps": [
    {
      "type": "email",
      "template_id": "tmpl_001",
      "delay_days": 0
    },
    {
      "type": "email",
      "template_id": "tmpl_002",
      "delay_days": 3
    }
  ],
  "status": "draft",
  "created_at": "2026-10-02T10:00:00Z"
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/automations \
  -H "Authorization: Bearer ***" \
  -H "Content-Type: application/json" \
  -d '{"name": "Welcome Series", "trigger": "subscriber_added"}'
```

---

### GET /api/v1/automations

List all automations.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `page` | integer | No | Page number |
| `page_size` | integer | No | Items per page |
| `status` | string | No | Filter by status: `draft`, `active`, `paused` |

**Response (200):**

```json
{
  "data": [
    {
      "id": "auto_001",
      "name": "Welcome Series",
      "status": "draft"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20
}
```

**Example:**

```bash
curl -X GET https://a2zsoc.com/api/v1/automations \
  -H "Authorization: Bearer ***"
```

---

### GET /api/v1/automations/{automation_id}

Get an automation by ID.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `automation_id` | string | Yes | Automation identifier |

**Response (200):**

```json
{
  "id": "auto_001",
  "name": "Welcome Series",
  "trigger": "subscriber_added",
  "status": "draft"
}
```

**Example:**

```bash
curl -X GET https://a2zsoc.com/api/v1/automations/auto_001 \
  -H "Authorization: Bearer ***"
```

---

### PUT /api/v1/automations/{automation_id}

Update an automation.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `automation_id` | string | Yes | Automation identifier |

**Request Body:**

```json
{
  "name": "Updated Welcome Series"
}
```

**Response (200):**

```json
{
  "id": "auto_001",
  "name": "Updated Welcome Series",
  "status": "draft"
}
```

**Example:**

```bash
curl -X PUT https://a2zsoc.com/api/v1/automations/auto_001 \
  -H "Authorization: Bearer ***" \
  -H "Content-Type: application/json" \
  -d '{"name": "Updated Welcome Series"}'
```

---

### DELETE /api/v1/automations/{automation_id}

Delete an automation.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `automation_id` | string | Yes | Automation identifier |

**Example:**

```bash
curl -X DELETE https://a2zsoc.com/api/v1/automations/auto_001 \
  -H "Authorization: Bearer ***" \
  -H "X-Idempotency-Key: 01J0ABC1234567890"
```

---

### POST /api/v1/automations/{automation_id}/activate

Activate an automation.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `automation_id` | string | Yes | Automation identifier |

**Response (200):**

```json
{
  "id": "auto_001",
  "status": "active"
  "activated_at": "2026-10-02T10:00:00Z"
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/automations/auto_001/activate \
  -H "Authorization: Bearer ***" \
  -H "X-Idempotency-Key: 01J0ABC1234567890"
```

---

### POST /api/v1/automations/{automation_id}/deactivate

Deactivate an automation.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `automation_id` | string | Yes | Automation identifier |

**Response (200):**

```json
{
  "id": "auto_001",
  "status": "paused",
  "deactivated_at": "2026-10-02T10:00:00Z"
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/automations/auto_001/deactivate \
  -H "Authorization: Bearer ***" \
  -H "X-Idempotency-Key: 01J0ABC1234567890"
```

---

### POST /api/v1/subscribers

Add a new subscriber.

**Request Body:**

```json
{
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "status": "subscribed",
  "tags": ["newsletter", "product-updates"],
  "custom_fields": {"plan": "premium"}
}
```

**Response (201):**

```json
{
  "id": "sub_001",
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "status": "subscribed",
  "tags": ["newsletter", "product-updates"],
  "custom_fields": {"plan": "premium"},
  "created_at": "2026-10-02T10:00:00Z"
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/subscribers \
  -H "Authorization: Bearer ***" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "first_name": "John"}'
```

---

### GET /api/v1/subscribers

List all subscribers.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `page` | integer | No | Page number |
| `page_size` | integer | No | Items per page |
| `status` | string | No | Filter by status: `subscribed`, `unsubscribed`, `bounced` |

**Response (200):**

```json
{
  "data": [
    {
      "id": "sub_001",
      "email": "user@example.com",
      "status": "subscribed"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20
}
```

**Example:**

```bash
curl -X GET https://a2zsoc.com/api/v1/subscribers \
  -H "Authorization: Bearer ***"
```

---

### GET /api/v1/subscribers/{subscriber_id}

Get a subscriber by ID.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `subscriber_id` | string | Yes | Subscriber identifier |

**Response (200):**

```json
{
  "id": "sub_001",
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "status": "subscribed"
}
```

**Example:**

```bash
curl -X GET https://a2zsoc.com/api/v1/subscribers/sub_001 \
  -H "Authorization: Bearer ***"
```

---

### PUT /api/v1/subscribers/{subscriber_id}

Update a subscriber.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `subscriber_id` | string | Yes | Subscriber identifier |

**Request Body:**

```json
{
  "first_name": "Jane",
  "tags": ["vip"]
}
```

**Response (200):**

```json
{
  "id": "sub_001",
  "email": "user@example.com",
  "first_name": "Jane",
  "tags": ["vip"]
}
```

**Example:**

```bash
curl -X PUT https://a2zsoc.com/api/v1/subscribers/sub_001 \
  -H "Authorization: Bearer ***" \
  -H "Content-Type: application/json" \
  -d '{"first_name": "Jane"}'
```

---

### DELETE /api/v1/subscribers/{subscriber_id}

Delete a subscriber.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `subscriber_id` | string | Yes | Subscriber identifier |

**Example:**

```bash
curl -X DELETE https://a2zsoc.com/api/v1/subscribers/sub_001 \
  -H "Authorization: Bearer ***" \
  -H "X-Idempotency-Key: 01J0ABC1234567890"
```

---

### POST /api/v1/subscribers/{subscriber_id}/unsubscribe

Unsubscribe a subscriber.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `subscriber_id` | string | Yes | Subscriber identifier |

**Response (200):**

```json
{
  "id": "sub_001",
  "status": "unsubscribed",
  "unsubscribed_at": "2026-10-02T10:00:00Z"
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/subscribers/sub_001/unsubscribe \
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
