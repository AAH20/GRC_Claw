# Onboarding Training API Reference

> Last updated: 2026-10-02 | Base URL: `https://a2zsoc.com` | Version: `0.1.0`

AI-powered onboarding and training platform for marketing teams. Course creation, learner management, progress tracking, and LMS delivery.

---

## Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [Endpoints](#endpoints)
  - [Courses](#courses)
    - [POST /api/v1/courses](#post--api-v1-courses)
    - [GET /api/v1/courses](#get--api-v1-courses)
    - [GET /api/v1/courses/{course_id}](#get--api-v1-courses-course_id)
    - [PUT /api/v1/courses/{course_id}](#put--api-v1-courses-course_id)
    - [DELETE /api/v1/courses/{course_id}](#delete--api-v1-courses-course_id)
    - [POST /api/v1/courses/{course_id}/deliver](#post--api-v1-courses-course_id-deliver)
    - [POST /api/v1/courses/{course_id}/publish](#post--api-v1-courses-course_id-publish)
  - [Learners](#learners)
    - [POST /api/v1/learners](#post--api-v1-learners)
    - [GET /api/v1/learners](#get--api-v1-learners)
    - [GET /api/v1/learners/{learner_id}](#get--api-v1-learners-learner_id)
    - [POST /api/v1/learners/{learner_id}/enroll](#post--api-v1-learners-learner_id-enroll)
    - [GET /api/v1/learners/{learner_id}/progress](#get--api-v1-learners-learner_id-progress)
    - [GET /api/v1/learners/{learner_id}/assessments](#get--api-v1-learners-learner_id-assessments)
- [Error Codes](#error-codes)
- [Rate Limiting](#rate-limiting)
- [Pagination](#pagination)
- [Idempotency](#idempotency)

---

## Overview

The Onboarding Training API provides programmatic access to AI-powered onboarding and training platform for marketing teams. Course creation, learner management, and progress tracking.

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

### Courses

#### POST /api/v1/courses

Create a new onboarding course for a role.

**Request Body:**

```json
{
  "role": "marketing_manager",
  "level": "novice",
  "language": "en",
  "title": "Marketing Manager Onboarding",
  "description": "Complete onboarding for new marketing managers",
  "modules": [
    {
      "title": "Platform Overview",
      "description": "Introduction to the marketing platform",
      "lessons": [
        {"title": "Getting Started", "content": "..."},
        {"title": "Dashboard Tour", "content": "..."}
      ]
    }
  ],
  "tags": ["onboarding", "marketing"]
}
```

**Response (201):**

```json
{
  "course_id": "course_001",
  "role": "marketing_manager",
  "level": "novice",
  "language": "en",
  "title": "Marketing Manager Onboarding",
  "status": "draft",
  "modules_count": 1,
  "created_at": "2026-10-01T00:00:00Z"
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/courses \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -H "X-Idempotency-Key: 01J0ABC1234567890" \
  -d '{"role": "marketing_manager", "level": "novice"}'
```

---

#### GET /api/v1/courses

List all courses.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `status_filter` | string | No | Filter by status: `draft`, `published`, `archived` |
| `role` | string | No | Filter by target role |
| `level` | string | No | Filter by level: `novice`, `intermediate`, `advanced` |
| `language` | string | No | Filter by language code |
| `cursor` | string | No | Pagination cursor |
| `limit` | integer | No | Items per page (default: 20, max: 100) |

**Response (200):**

```json
{
  "data": [
    {
      "course_id": "course_001",
      "role": "marketing_manager",
      "level": "novice",
      "status": "draft",
      "title": "Marketing Manager Onboarding",
      "created_at": "2026-10-01T00:00:00Z"
    }
  ],
  "pagination": {
    "cursor": "eyJpZCI6ImNvdXJzZV8wMDEifQ==",
    "hasMore": false,
    "totalCount": 1
  }
}
```

**Example:**

```bash
curl -X GET "https://a2zsoc.com/api/v1/courses?status_filter=published" \
  -H "Authorization: Bearer <token>"
```

---

#### GET /api/v1/courses/{course_id}

Get a course by ID.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `course_id` | string | Yes | Course identifier |

**Response (200):**

```json
{
  "course_id": "course_001",
  "role": "marketing_manager",
  "level": "novice",
  "language": "en",
  "title": "Marketing Manager Onboarding",
  "description": "Complete onboarding for new marketing managers",
  "status": "draft",
  "modules": [
    {
      "title": "Platform Overview",
      "lessons": [
        {"title": "Getting Started", "content": "..."}
      ]
    }
  ],
  "tags": ["onboarding", "marketing"],
  "created_at": "2026-10-01T00:00:00Z",
  "updated_at": "2026-10-01T00:00:00Z"
}
```

**Example:**

```bash
curl -X GET https://a2zsoc.com/api/v1/courses/course_001 \
  -H "Authorization: Bearer <token>"
```

---

#### PUT /api/v1/courses/{course_id}

Update a course.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `course_id` | string | Yes | Course identifier |

**Request Body:**

```json
{
  "title": "Updated Course Title",
  "description": "Updated description",
  "level": "intermediate",
  "tags": ["onboarding", "v2"]
}
```

**Response (200):**

```json
{
  "course_id": "course_001",
  "title": "Updated Course Title",
  "level": "intermediate",
  "status": "draft",
  "updated_at": "2026-10-01T12:00:00Z"
}
```

**Example:**

```bash
curl -X PUT https://a2zsoc.com/api/v1/courses/course_001 \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"title": "Updated Title"}'
```

---

#### DELETE /api/v1/courses/{course_id}

Delete a course.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `course_id` | string | Yes | Course identifier |

**Response:** `204 No Content`

**Example:**

```bash
curl -X DELETE https://a2zsoc.com/api/v1/courses/course_001 \
  -H "Authorization: Bearer <token>" \
  -H "X-Idempotency-Key: 01J0ABC1234567890"
```

---

#### POST /api/v1/courses/{course_id}/deliver

Deliver a course to an LMS.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `course_id` | string | Yes | Course identifier |

**Request Body:**

```json
{
  "provider": "canvas",
  "publish": true,
  "lms_config": {
    "api_key": "canvas_api_key",
    "base_url": "https://canvas.instructure.com"
  }
}
```

**Response (200):**

```json
{
  "course_id": "course_001",
  "lms_course_id": "lms_001",
  "provider": "canvas",
  "status": "delivered",
  "delivered_at": "2026-10-01T00:00:00Z"
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/courses/course_001/deliver \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"provider": "canvas", "publish": true}'
```

---

#### POST /api/v1/courses/{course_id}/publish

Publish a draft course.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `course_id` | string | Yes | Course identifier |

**Response (200):**

```json
{
  "course_id": "course_001",
  "status": "published",
  "published_at": "2026-10-01T00:00:00Z"
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/courses/course_001/publish \
  -H "Authorization: Bearer <token>"
```

---

### Learners

#### POST /api/v1/learners

Register a new learner.

**Request Body:**

```json
{
  "email": "learner@example.com",
  "full_name": "John Doe",
  "role": "marketing_manager",
  "level": "novice",
  "department": "Marketing",
  "start_date": "2026-10-01"
}
```

**Response (201):**

```json
{
  "learner_id": "learner_001",
  "email": "learner@example.com",
  "full_name": "John Doe",
  "role": "marketing_manager",
  "level": "novice",
  "enrolled_course_ids": [],
  "created_at": "2026-10-01T00:00:00Z"
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/learners \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -H "X-Idempotency-Key: 01J0ABC1234567890" \
  -d '{"email": "learner@example.com", "full_name": "John Doe", "role": "marketing_manager"}'
```

---

#### GET /api/v1/learners

List all learners.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `role` | string | No | Filter by job role |
| `level` | string | No | Filter by proficiency level |
| `course_id` | string | No | Filter by enrolled course |
| `cursor` | string | No | Pagination cursor |
| `limit` | integer | No | Items per page (default: 20, max: 100) |

**Response (200):**

```json
{
  "data": [
    {
      "learner_id": "learner_001",
      "email": "learner@example.com",
      "full_name": "John Doe",
      "role": "marketing_manager",
      "level": "novice",
      "enrolled_course_ids": ["course_001"],
      "created_at": "2026-10-01T00:00:00Z"
    }
  ],
  "pagination": {
    "cursor": "eyJpZCI6ImxlYXJuZXJfMDAxIn0=",
    "hasMore": false,
    "totalCount": 1
  }
}
```

**Example:**

```bash
curl -X GET "https://a2zsoc.com/api/v1/learners?role=marketing_manager" \
  -H "Authorization: Bearer <token>"
```

---

#### GET /api/v1/learners/{learner_id}

Get a learner by ID.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `learner_id` | string | Yes | Learner identifier |

**Response (200):**

```json
{
  "learner_id": "learner_001",
  "email": "learner@example.com",
  "full_name": "John Doe",
  "role": "marketing_manager",
  "level": "novice",
  "enrolled_course_ids": ["course_001"],
  "department": "Marketing",
  "created_at": "2026-10-01T00:00:00Z",
  "updated_at": "2026-10-01T00:00:00Z"
}
```

**Example:**

```bash
curl -X GET https://a2zsoc.com/api/v1/learners/learner_001 \
  -H "Authorization: Bearer <token>"
```

---

#### POST /api/v1/learners/{learner_id}/enroll

Enroll a learner in a course.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `learner_id` | string | Yes | Learner identifier |

**Request Body:**

```json
{
  "course_id": "course_001"
}
```

**Response (200):**

```json
{
  "learner_id": "learner_001",
  "enrolled_course_ids": ["course_001"],
  "enrolled_at": "2026-10-01T00:00:00Z"
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/learners/learner_001/enroll \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"course_id": "course_001"}'
```

---

#### GET /api/v1/learners/{learner_id}/progress

Get progress summary for a learner.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `learner_id` | string | Yes | Learner identifier |

**Response (200):**

```json
{
  "learner_id": "learner_001",
  "enrolled_courses": 2,
  "completed_courses": 1,
  "completion_rate": 0.5,
  "average_score": 85.0,
  "total_assessments": 5,
  "course_progress": [
    {
      "course_id": "course_001",
      "status": "completed",
      "score": 85.0,
      "completed_at": "2026-10-01T00:00:00Z"
    },
    {
      "course_id": "course_002",
      "status": "in_progress",
      "progress_percent": 60.0
    }
  ]
}
```

**Example:**

```bash
curl -X GET https://a2zsoc.com/api/v1/learners/learner_001/progress \
  -H "Authorization: Bearer <token>"
```

---

#### GET /api/v1/learners/{learner_id}/assessments

Get all assessment results for a learner.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `learner_id` | string | Yes | Learner identifier |

**Response (200):**

```json
{
  "assessments": [
    {
      "assessment_id": "assess_001",
      "course_id": "course_001",
      "score": 85.0,
      "passed": true,
      "completed_at": "2026-10-01T00:00:00Z",
      "answers": [
        {"question_id": "q1", "correct": true}
      ]
    }
  ],
  "total": 1
}
```

**Example:**

```bash
curl -X GET https://a2zsoc.com/api/v1/learners/learner_001/assessments \
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
