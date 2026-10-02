# Event Management API Reference

> Last updated: 2026-10-02 | Base URL: `https://a2zsoc.com` | Version: `0.1.0`

Agentic AI event management system with five specialized agents. Manage marketing events, webinars, and conferences. Registration, attendance tracking, and post-event analytics.

---

## Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [Endpoints](#endpoints)
  - [Events](#events)
    - [POST /api/v1/events](#post--api-v1-events)
    - [GET /api/v1/events](#get--api-v1-events)
    - [GET /api/v1/events/{event_id}](#get--api-v1-events-event_id)
    - [PUT /api/v1/events/{event_id}](#put--api-v1-events-event_id)
    - [DELETE /api/v1/events/{event_id}](#delete--api-v1-events-event_id)
    - [POST /api/v1/events/{event_id}/plan](#post--api-v1-events-event_id-plan)
  - [Attendees](#attendees)
    - [POST /api/v1/events/{event_id}/register](#post--api-v1-events-event_id-register)
    - [GET /api/v1/events/{event_id}/attendees](#get--api-v1-events-event_id-attendees)
    - [PUT /api/v1/attendees/{attendee_id}](#put--api-v1-attendees-attendee_id)
    - [DELETE /api/v1/attendees/{attendee_id}](#delete--api-v1-attendees-attendee_id)
  - [Analytics](#analytics)
    - [GET /api/v1/events/{event_id}/analytics](#get--api-v1-events-event_id-analytics)
- [Error Codes](#error-codes)
- [Rate Limiting](#rate-limiting)
- [Pagination](#pagination)
- [Idempotency](#idempotency)
- [Webhooks](#webhooks)

---

## Overview

The Event Management API provides programmatic access to manage marketing events, webinars, and conferences. Registration, attendance tracking, and post-event analytics.

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

### Events

#### POST /api/v1/events

Create a new event.

**Request Body:**

```json
{
  "name": "Annual Marketing Summit 2026",
  "description": "Our flagship marketing conference",
  "event_type": "conference",
  "date": "2026-11-15",
  "duration_hours": 8,
  "expected_attendees": 500,
  "budget_total": 50000,
  "venue": {
    "name": "Downtown Conference Center",
    "address": "123 Main St, City Center",
    "capacity": 600
  },
  "goals": ["brand awareness", "lead generation", "customer education"],
  "status": "planning",
  "tags": ["conference", "marketing", "flagship"]
}
```

**Response (201):**

```json
{
  "event_id": "evt_001",
  "name": "Annual Marketing Summit 2026",
  "event_type": "conference",
  "status": "planning",
  "expected_attendees": 500,
  "created_at": "2026-10-01T00:00:00Z"
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/events \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -H "X-Idempotency-Key: 01J0ABC1234567890" \
  -d '{"name": "Marketing Summit", "event_type": "conference"}'
```

---

#### GET /api/v1/events

List all events.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `status` | string | No | Filter by status: `planning`, `registration_open`, `active`, `completed`, `cancelled` |
| `event_type` | string | No | Filter by type: `conference`, `workshop`, `meetup`, `webinar`, `social` |
| `start_date` | string | No | Filter by start date |
| `end_date` | string | No | Filter by end date |
| `cursor` | string | No | Pagination cursor |
| `limit` | integer | No | Items per page (default: 20, max: 100) |

**Response (200):**

```json
{
  "data": [
    {
      "event_id": "evt_001",
      "name": "Annual Marketing Summit 2026",
      "event_type": "conference",
      "status": "registration_open",
      "date": "2026-11-15",
      "expected_attendees": 500,
      "registered_count": 320,
      "created_at": "2026-10-01T00:00:00Z"
    }
  ],
  "pagination": {
    "cursor": "eyJpZCI6ImV2dF8wMDEifQ==",
    "hasMore": false,
    "totalCount": 1
  }
}
```

**Example:**

```bash
curl -X GET "https://a2zsoc.com/api/v1/events?status=registration_open" \
  -H "Authorization: Bearer <token>"
```

---

#### GET /api/v1/events/{event_id}

Get an event by ID.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `event_id` | string | Yes | Event identifier |

**Response (200):**

```json
{
  "event_id": "evt_001",
  "name": "Annual Marketing Summit 2026",
  "description": "Our flagship marketing conference",
  "event_type": "conference",
  "date": "2026-11-15",
  "duration_hours": 8,
  "expected_attendees": 500,
  "registered_count": 320,
  "budget_total": 50000,
  "venue": {
    "name": "Downtown Conference Center",
    "address": "123 Main St, City Center",
    "capacity": 600
  },
  "goals": ["brand awareness", "lead generation"],
  "status": "registration_open",
  "tags": ["conference", "marketing"],
  "created_at": "2026-10-01T00:00:00Z",
  "updated_at": "2026-10-01T00:00:00Z"
}
```

**Example:**

```bash
curl -X GET https://a2zsoc.com/api/v1/events/evt_001 \
  -H "Authorization: Bearer <token>"
```

---

#### PUT /api/v1/events/{event_id}

Update an event.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `event_id` | string | Yes | Event identifier |

**Request Body:**

```json
{
  "name": "Updated Event Name",
  "status": "active",
  "expected_attendees": 600,
  "budget_total": 55000
}
```

**Response (200):**

```json
{
  "event_id": "evt_001",
  "name": "Updated Event Name",
  "status": "active",
  "expected_attendees": 600,
  "updated_at": "2026-10-01T12:00:00Z"
}
```

**Example:**

```bash
curl -X PUT https://a2zsoc.com/api/v1/events/evt_001 \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"status": "active"}'
```

---

#### DELETE /api/v1/events/{event_id}

Delete an event.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `event_id` | string | Yes | Event identifier |

**Response:** `204 No Content`

**Example:**

```bash
curl -X DELETE https://a2zsoc.com/api/v1/events/evt_001 \
  -H "Authorization: Bearer <token>" \
  -H "X-Idempotency-Key: 01J0ABC1234567890"
```

---

#### POST /api/v1/events/{event_id}/plan

Generate an event plan using AI.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `event_id` | string | Yes | Event identifier |

**Response (200):**

```json
{
  "event_id": "evt_001",
  "event_strategy": "Plan a conference event 'Annual Marketing Summit 2026' for 500 attendees...",
  "venue_options": [
    {
      "name": "Downtown Conference Center",
      "address": "123 Main St, City Center",
      "capacity": 550,
      "cost": 15000,
      "amenities": ["WiFi", "AV Equipment", "Catering Kitchen"],
      "pros": ["Central location", "Full AV support"],
      "cons": ["Higher cost"],
      "score": 0.85
    }
  ],
  "recommended_venue": {
    "name": "Downtown Conference Center",
    "score": 0.85
  },
  "budget_breakdown": [
    {"category": "Venue", "estimated_cost": 15000, "priority": "high"},
    {"category": "Catering", "estimated_cost": 12500, "priority": "high"},
    {"category": "Marketing", "estimated_cost": 7500, "priority": "medium"}
  ],
  "timeline": [
    {"name": "Venue Booking", "start_date": "T-90 days", "end_date": "T-75 days", "owner": "Event Manager"},
    {"name": "Speaker Outreach", "start_date": "T-75 days", "end_date": "T-45 days", "owner": "Content Lead"}
  ],
  "risk_assessment": ["Venue availability may be limited for popular dates"],
  "recommendations": ["Book venue at least 90 days in advance for best rates"]
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/events/evt_001/plan \
  -H "Authorization: Bearer <token>"
```

---

### Attendees

#### POST /api/v1/events/{event_id}/register

Register an attendee for an event.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `event_id` | string | Yes | Event identifier |

**Request Body:**

```json
{
  "attendee_name": "John Doe",
  "attendee_email": "john@example.com",
  "ticket_type": "general",
  "company": "Acme Corp",
  "role": "Marketing Manager",
  "dietary_requirements": ["vegetarian"],
  "special_requests": ""
}
```

**Response (201):**

```json
{
  "registration_id": "reg_001",
  "event_id": "evt_001",
  "attendee_name": "John Doe",
  "attendee_email": "john@example.com",
  "ticket_type": "general",
  "status": "confirmed",
  "created_at": "2026-10-01T00:00:00Z"
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/events/evt_001/register \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"attendee_name": "John Doe", "attendee_email": "john@example.com"}'
```

---

#### GET /api/v1/events/{event_id}/attendees

Get event attendees.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `event_id` | string | Yes | Event identifier |
| `status` | string | No | Filter by status: `confirmed`, `cancelled`, `waitlisted`, `checked_in` |
| `ticket_type` | string | No | Filter by ticket type |
| `cursor` | string | No | Pagination cursor |
| `limit` | integer | No | Items per page (default: 20, max: 100) |

**Response (200):**

```json
{
  "data": [
    {
      "registration_id": "reg_001",
      "event_id": "evt_001",
      "name": "John Doe",
      "email": "john@example.com",
      "company": "Acme Corp",
      "role": "Marketing Manager",
      "ticket_type": "general",
      "status": "confirmed",
      "registered_at": "2026-10-01T00:00:00Z"
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
curl -X GET "https://a2zsoc.com/api/v1/events/evt_001/attendees?status=confirmed" \
  -H "Authorization: Bearer <token>"
```

---

#### PUT /api/v1/attendees/{attendee_id}

Update an attendee registration.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `attendee_id` | string | Yes | Registration identifier |

**Request Body:**

```json
{
  "status": "checked_in",
  "ticket_type": "vip"
}
```

**Response (200):**

```json
{
  "registration_id": "reg_001",
  "status": "checked_in",
  "ticket_type": "vip",
  "updated_at": "2026-10-01T12:00:00Z"
}
```

**Example:**

```bash
curl -X PUT https://a2zsoc.com/api/v1/attendees/reg_001 \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"status": "checked_in"}'
```

---

#### DELETE /api/v1/attendees/{attendee_id}

Cancel an attendee registration.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `attendee_id` | string | Yes | Registration identifier |

**Response:** `204 No Content`

**Example:**

```bash
curl -X DELETE https://a2zsoc.com/api/v1/attendees/reg_001 \
  -H "Authorization: Bearer <token>" \
  -H "X-Idempotency-Key: 01J0ABC1234567890"
```

---

### Analytics

#### GET /api/v1/events/{event_id}/analytics

Get post-event analytics.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `event_id` | string | Yes | Event identifier |

**Response (200):**

```json
{
  "event_id": "evt_001",
  "registration_count": 500,
  "attendance_count": 450,
  "attendance_rate": 0.9,
  "revenue": 75000,
  "budget_spent": 48000,
  "roi": 1.56,
  "satisfaction_score": 4.5,
  "nps_score": 55,
  "top_sessions": [
    {"title": "Keynote: Future of Marketing", "attendance": 400, "rating": 4.8}
  ],
  "demographics": {
    "by_role": [{"role": "Marketing Manager", "count": 200}],
    "by_company_size": [{"size": "100-500", "count": 150}]
  }
}
```

**Example:**

```bash
curl -X GET https://a2zsoc.com/api/v1/events/evt_001/analytics \
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

Subscribe to event management events:

| Event | Description |
|-------|-------------|
| `event.created` | New event created |
| `event.updated` | Event details updated |
| `event.registration_opened` | Registration opened |
| `event.registration_closed` | Registration closed |
| `attendee.registered` | New attendee registered |
| `attendee.cancelled` | Attendee cancelled |
| `attendee.checked_in` | Attendee checked in |
| `event.analytics_ready` | Post-event analytics available |

**Webhook Payload:**

```json
{
  "event": "attendee.registered",
  "timestamp": "2026-10-01T00:00:00Z",
  "data": {
    "event_id": "evt_001",
    "registration_id": "reg_001",
    "attendee_email": "john@example.com"
  }
}
```
