# Marketing Compliance API Reference

> Last updated: 2026-10-02 | Base URL: `https://a2zsoc.com`

AI-powered marketing compliance monitoring with policy management, violation detection, and automated response workflows.

---

## Table of Contents

- [Overview](#overview)
- [Endpoints](#endpoints)
  - [GET /api/v1/policies](#get--api-v1-policies)
  - [POST /api/v1/policies](#post--api-v1-policies)
  - [GET /api/v1/policies/{policy_id}](#get--api-v1-policies-policy_id)
  - [PUT /api/v1/policies/{policy_id}](#put--api-v1-policies-policy_id)
  - [DELETE /api/v1/policies/{policy_id}](#delete--api-v1-policies-policy_id)
  - [GET /api/v1/violations](#get--api-v1-violations)
  - [POST /api/v1/violations](#post--api-v1-violations)
  - [GET /api/v1/violations/{violation_id}](#get--api-v1-violations-violation_id)
  - [PUT /api/v1/violations/{violation_id}/resolve](#put--api-v1-violations-violation_id-resolve)
  - [POST /api/v1/violations/{violation_id}/resolve](#post--api-v1-violations-violation_id-resolve)
- [Error Codes](#error-codes)
- [Rate Limiting](#rate-limiting)
- [Pagination](#pagination)
- [Authentication](#authentication)
- [Idempotency](#idempotency)

---

## Overview

The Marketing Compliance API provides programmatic access to compliance policy management, violation detection, tracking, and resolution workflows. Supports automated monitoring of marketing content across multiple channels including email, social media, and advertising platforms.

**Base Path:** `/api/v1`

All endpoints require authentication via Bearer token and tenant scoping.

---

## Endpoints

### GET /api/v1/policies

List compliance policies.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `enabled` | boolean | No | Filter by enabled status |

**Response (200):**

```json
[
  {
    "id": "pol_0001",
    "name": "GDPR Consent Check",
    "description": "Verify explicit consent before sending marketing emails",
    "severity": "critical",
    "enabled": true,
    "rules": ["check_consent_flag", "verify_opt_in_date"],
    "created_at": "2026-09-01T00:00:00Z",
    "updated_at": "2026-09-01T00:00:00Z"
  }
]
```

**Example:**

```bash
curl -X GET "https://a2zsoc.com/api/v1/policies?enabled=true" \
  -H "Authorization: Bearer ***"
```

### POST /api/v1/policies

Create a new compliance policy.

**Request Body:**

```json
{
  "name": "CAN-SPAM Compliance",
  "description": "Ensure all emails include unsubscribe links and physical address",
  "severity": "high",
  "enabled": true,
  "rules": ["check_unsubscribe_link", "verify_physical_address", "validate_from_header"]
}
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | string | Yes | Policy name (1-128 chars) |
| `description` | string | No | Policy description (max 2048 chars) |
| `severity` | string | No | Severity level: `low`, `medium`, `high`, `critical` (default: `medium`) |
| `enabled` | boolean | No | Whether policy is enabled (default: true) |
| `rules` | array | No | List of rule identifiers |

**Response (201):**

```json
{
  "id": "pol_0002",
  "name": "CAN-SPAM Compliance",
  "description": "Ensure all emails include unsubscribe links and physical address",
  "severity": "high",
  "enabled": true,
  "rules": ["check_unsubscribe_link", "verify_physical_address"],
  "created_at": "2026-10-01T00:00:00Z",
  "updated_at": "2026-10-01T00:00:00Z"
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/policies \
  -H "Authorization: Bearer ***" \
  -H "Content-Type: application/json" \
  -H "X-Idempotency-Key: 01J0ABC1234567890" \
  -d '{"name": "CAN-SPAM", "severity": "high"}'
```

### GET /api/v1/policies/{policy_id}

Fetch a single policy by ID.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `policy_id` | string | Yes | Policy identifier (path) |

**Response (200):**

```json
{
  "id": "pol_0001",
  "name": "GDPR Consent Check",
  "description": "Verify explicit consent before sending marketing emails",
  "severity": "critical",
  "enabled": true,
  "rules": ["check_consent_flag", "verify_opt_in_date"],
  "created_at": "2026-09-01T00:00:00Z",
  "updated_at": "2026-09-01T00:00:00Z"
}
```

**Example:**

```bash
curl -X GET https://a2zsoc.com/api/v1/policies/pol_0001 \
  -H "Authorization: Bearer ***"
```

### PUT /api/v1/policies/{policy_id}

Replace an existing policy.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `policy_id` | string | Yes | Policy identifier (path) |

**Request Body:**

```json
{
  "name": "Updated GDPR Policy",
  "description": "Updated description",
  "severity": "critical",
  "enabled": true,
  "rules": ["check_consent_flag"]
}
```

**Response (200):**

```json
{
  "id": "pol_0001",
  "name": "Updated GDPR Policy",
  "description": "Updated description",
  "severity": "critical",
  "enabled": true,
  "rules": ["check_consent_flag"],
  "created_at": "2026-09-01T00:00:00Z",
  "updated_at": "2026-10-01T00:00:00Z"
}
```

**Example:**

```bash
curl -X PUT https://a2zsoc.com/api/v1/policies/pol_0001 \
  -H "Authorization: Bearer ***" \
  -H "Content-Type: application/json" \
  -d '{"name": "Updated Policy"}'
```

### DELETE /api/v1/policies/{policy_id}

Delete a policy.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `policy_id` | string | Yes | Policy identifier (path) |

**Response:** 204 No Content

**Example:**

```bash
curl -X DELETE https://a2zsoc.com/api/v1/policies/pol_0001 \
  -H "Authorization: Bearer ***" \
  -H "X-Idempotency-Key: 01J0ABC1234567890"
```

### GET /api/v1/violations

List violations with optional filters.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `severity` | string | No | Filter by severity: `low`, `medium`, `high`, `critical` |
| `status` | string | No | Filter by status: `open`, `in_review`, `resolved`, `dismissed` |
| `source` | string | No | Filter by source platform |

**Response (200):**

```json
[
  {
    "id": "vio_0001",
    "content_id": "content_001",
    "source": "mailchimp",
    "rule": "check_unsubscribe_link",
    "severity": "high",
    "description": "Missing unsubscribe link in email campaign",
    "confidence": 0.95,
    "excerpt": "...",
    "status": "open",
    "detected_at": "2026-10-01T00:00:00Z",
    "resolved_at": null,
    "resolution": null
  }
]
```

**Example:**

```bash
curl -X GET "https://a2zsoc.com/api/v1/violations?severity=high&status=open" \
  -H "Authorization: Bearer ***"
```

### POST /api/v1/violations

Report a new violation.

**Request Body:**

```json
{
  "content_id": "content_001",
  "source": "mailchimp",
  "rule": "check_unsubscribe_link",
  "severity": "high",
  "description": "Missing unsubscribe link in email campaign",
  "confidence": 0.95,
  "excerpt": "Email body without unsubscribe link..."
}
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `content_id` | string | Yes | Content identifier |
| `source` | string | Yes | Source platform |
| `rule` | string | Yes | Rule that was violated |
| `severity` | string | No | Severity level (default: `medium`) |
| `description` | string | No | Violation description |
| `confidence` | float | No | Confidence score 0-1 (default: 0) |
| `excerpt` | string | No | Excerpt of violating content |

**Response (201):**

```json
{
  "id": "vio_0002",
  "content_id": "content_001",
  "source": "mailchimp",
  "rule": "check_unsubscribe_link",
  "severity": "high",
  "description": "Missing unsubscribe link",
  "confidence": 0.95,
  "excerpt": "...",
  "status": "open",
  "detected_at": "2026-10-01T00:00:00Z",
  "resolved_at": null,
  "resolution": null
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/violations \
  -H "Authorization: Bearer ***" \
  -H "Content-Type: application/json" \
  -H "X-Idempotency-Key: 01J0ABC1234567890" \
  -d '{"content_id": "content_001", "source": "mailchimp", "rule": "check_unsubscribe_link"}'
```

### GET /api/v1/violations/{violation_id}

Fetch a single violation by ID.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `violation_id` | string | Yes | Violation identifier (path) |

**Response (200):**

```json
{
  "id": "vio_0001",
  "content_id": "content_001",
  "source": "mailchimp",
  "rule": "check_unsubscribe_link",
  "severity": "high",
  "description": "Missing unsubscribe link in email campaign",
  "confidence": 0.95,
  "excerpt": "...",
  "status": "open",
  "detected_at": "2026-10-01T00:00:00Z",
  "resolved_at": null,
  "resolution": null
}
```

**Example:**

```bash
curl -X GET https://a2zsoc.com/api/v1/violations/vio_0001 \
  -H "Authorization: Bearer ***"
```

### PUT /api/v1/violations/{violation_id}/resolve

Resolve a violation via PUT.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `violation_id` | string | Yes | Violation identifier (path) |

**Request Body:**

```json
{
  "resolution": "Added unsubscribe link to email template",
  "status": "resolved"
}
```

**Response (200):**

```json
{
  "id": "vio_0001",
  "content_id": "content_001",
  "source": "mailchimp",
  "rule": "check_unsubscribe_link",
  "severity": "high",
  "status": "resolved",
  "detected_at": "2026-10-01T00:00:00Z",
  "resolved_at": "2026-10-01T00:05:00Z",
  "resolution": "Added unsubscribe link to email template"
}
```

**Example:**

```bash
curl -X PUT https://a2zsoc.com/api/v1/violations/vio_0001/resolve \
  -H "Authorization: Bearer ***" \
  -H "Content-Type: application/json" \
  -d '{"resolution": "Fixed unsubscribe link"}'
```

### POST /api/v1/violations/{violation_id}/resolve

Resolve a violation via POST.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `violation_id` | string | Yes | Violation identifier (path) |

**Request Body:**

```json
{
  "resolution": "Added unsubscribe link to email template",
  "status": "resolved"
}
```

**Response (200):**

```json
{
  "id": "vio_0001",
  "content_id": "content_001",
  "source": "mailchimp",
  "rule": "check_unsubscribe_link",
  "severity": "high",
  "status": "resolved",
  "detected_at": "2026-10-01T00:00:00Z",
  "resolved_at": "2026-10-01T00:05:00Z",
  "resolution": "Added unsubscribe link to email template"
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/violations/vio_0001/resolve \
  -H "Authorization: Bearer ***" \
  -H "Content-Type: application/json" \
  -d '{"resolution": "Fixed unsubscribe link"}'
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
