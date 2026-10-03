# API Reference

## Gated Communities API v1

**Base URL:** `http://localhost:8000/api/v1`

**Content-Type:** `application/json`

---

## Table of Contents

- [Health](#health)
- [Tiers](#tiers)
- [Access Control](#access-control)
- [Moderation](#moderation)
- [Reputation](#reputation)
- [Compliance](#compliance)
- [Analytics](#analytics)
- [Governance](#governance)
- [Verification](#verification)
- [Escalations](#escalations)
- [Metrics](#metrics)
- [Error Handling](#error-handling)

---

## Health

### GET /health

Health check endpoint.

**Response `200`**

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2024-01-15T10:30:00Z",
  "checks": {
    "api": true,
    "agents": true
  }
}
```

### GET /ready

Readiness probe for Kubernetes.

**Response `200`**

```json
{
  "ready": true,
  "version": "1.0.0"
}
```

### GET /live

Liveness probe for Kubernetes.

**Response `200`**

```json
{
  "alive": true
}
```

---

## Tiers

### GET /tiers

List all tiers with optional filtering.

**Query Parameters**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `level` | string | No | Filter by tier level (`bronze`, `silver`, `gold`, `platinum`, `diamond`) |
| `status` | string | No | Filter by status (`active`, `inactive`, `suspended`, `pending`, `expired`) |
| `skip` | integer | No | Records to skip (default: 0) |
| `limit` | integer | No | Max records to return (default: 100, max: 1000) |

**Response `200`**

```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Gold",
    "level": "gold",
    "status": "active",
    "description": "Gold tier membership",
    "requirements": {
      "min_activity_score": 70,
      "min_tenure_days": 30
    },
    "benefits": ["priority_support", "exclusive_access"],
    "max_members": 1000,
    "monthly_fee": 29.99,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-15T10:30:00Z",
    "metadata": {}
  }
]
```

### POST /tiers

Create a new tier.

**Request Body**

```json
{
  "name": "Platinum",
  "level": "platinum",
  "description": "Premium platinum membership",
  "requirements": {
    "min_activity_score": 90,
    "min_tenure_days": 90
  },
  "benefits": ["priority_support", "exclusive_access", "bonus_credits"],
  "max_members": 500,
  "monthly_fee": 99.99
}
```

**Response `201`**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "name": "Platinum",
  "level": "platinum",
  "status": "active",
  "description": "Premium platinum membership",
  "requirements": {
    "min_activity_score": 90,
    "min_tenure_days": 90
  },
  "benefits": ["priority_support", "exclusive_access", "bonus_credits"],
  "max_members": 500,
  "monthly_fee": 99.99,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "metadata": {}
}
```

### GET /tiers/{tier_id}

Get a specific tier by ID.

**Response `200`**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Gold",
  "level": "gold",
  "status": "active",
  "description": "Gold tier membership",
  "requirements": {},
  "benefits": ["priority_support"],
  "max_members": 1000,
  "monthly_fee": 29.99,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "metadata": {}
}
```

### PUT /tiers/{tier_id}

Update an existing tier.

**Request Body**

```json
{
  "name": "Gold Plus",
  "monthly_fee": 39.99
}
```

**Response `200`**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Gold Plus",
  "level": "gold",
  "status": "active",
  "description": "Gold tier membership",
  "requirements": {},
  "benefits": ["priority_support"],
  "max_members": 1000,
  "monthly_fee": 39.99,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-15T11:00:00Z",
  "metadata": {}
}
```

### DELETE /tiers/{tier_id}

Delete a tier.

**Response `204`** — No content

---

## Access Control

### POST /access/check

Check if a member has access to a resource.

**Request Body**

```json
{
  "member_id": "550e8400-e29b-41d4-a716-446655440000",
  "resource": "premium_forum",
  "action": "read",
  "context": {
    "ip_address": "192.168.1.1",
    "user_agent": "Mozilla/5.0"
  }
}
```

**Response `200`**

```json
{
  "member_id": "550e8400-e29b-41d4-a716-446655440000",
  "resource": "premium_forum",
  "action": "read",
  "decision": "granted",
  "tier_id": "550e8400-e29b-41d4-a716-446655440001",
  "reason": "Member tier 'gold' grants access to 'premium_forum'",
  "checked_at": "2024-01-15T10:30:00Z",
  "policy_id": "550e8400-e29b-41d4-a716-446655440002"
}
```

### POST /access/policies

Create a new access policy.

**Request Body**

```json
{
  "name": "Gold Forum Access",
  "tier_id": "550e8400-e29b-41d4-a716-446655440000",
  "resource": "premium_forum",
  "action": "read",
  "effect": "granted",
  "conditions": {
    "time_restrictions": null,
    "quota_limit": null
  },
  "priority": 10,
  "enabled": true
}
```

**Response `201`**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440002",
  "name": "Gold Forum Access",
  "tier_id": "550e8400-e29b-41d4-a716-446655440000",
  "resource": "premium_forum",
  "action": "read",
  "effect": "granted",
  "conditions": {},
  "priority": 10,
  "enabled": true,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "expires_at": null
}
```

### GET /access/policies

List access policies with optional filtering.

**Query Parameters**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `tier_id` | UUID | No | Filter by tier |

**Response `200`**

```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440002",
    "name": "Gold Forum Access",
    "tier_id": "550e8400-e29b-41d4-a716-446655440000",
    "resource": "premium_forum",
    "action": "read",
    "effect": "granted",
    "conditions": {},
    "priority": 10,
    "enabled": true,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z",
    "expires_at": null
  }
]
```

### GET /access/policies/{policy_id}

Get a specific access policy.

**Response `200`**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440002",
  "name": "Gold Forum Access",
  "tier_id": "550e8400-e29b-41d4-a716-446655440000",
  "resource": "premium_forum",
  "action": "read",
  "effect": "granted",
  "conditions": {},
  "priority": 10,
  "enabled": true,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "expires_at": null
}
```

### DELETE /access/policies/{policy_id}

Delete an access policy.

**Response `204`** — No content

---

## Moderation

### GET /moderation/queue

Get moderation queue items.

**Query Parameters**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `status` | string | No | Filter by status (`pending`, `in_review`, `resolved`) |
| `priority` | string | No | Filter by priority (`low`, `medium`, `high`, `critical`) |

**Response `200`**

```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "content": "Potentially inappropriate post content",
    "status": "pending",
    "priority": "high",
    "created_at": "2024-01-15T10:30:00Z"
  }
]
```

---

## Reputation

### GET /reputation

Get reputation scores for a member.

**Query Parameters**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `member_id` | string | Yes | Member identifier |

**Response `200`**

```json
{
  "member_id": "550e8400-e29b-41d4-a716-446655440000",
  "score": 85.5,
  "tier": "gold",
  "badges": ["helpful_contributor", "early_adopter"],
  "history": [
    {
      "action": "contribution",
      "points": 10,
      "timestamp": "2024-01-10T10:30:00Z"
    }
  ]
}
```

---

## Compliance

### GET /compliance/policies

List compliance policies.

**Response `200`**

```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Content Moderation Policy",
    "description": "Rules for acceptable content",
    "rules": [
      {
        "type": "prohibited_content",
        "severity": "high"
      }
    ],
    "active": true
  }
]
```

---

## Analytics

### GET /analytics/moderation

Get moderation analytics.

**Query Parameters**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `start_date` | date | No | Start date for analytics period |
| `end_date` | date | No | End date for analytics period |

**Response `200`**

```json
{
  "total_items": 150,
  "resolved_items": 120,
  "average_resolution_time": 2.5,
  "top_violations": [
    {
      "type": "spam",
      "count": 45
    },
    {
      "type": "harassment",
      "count": 30
    }
  ]
}
```

---

## Governance

### GET /governance/disputes

List disputes.

**Response `200`**

```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "Content removal dispute",
    "status": "open",
    "parties": ["user_1", "user_2"],
    "created_at": "2024-01-15T10:30:00Z"
  }
]
```

---

## Verification

### POST /verification/verify

Verify member identity.

**Request Body**

```json
{
  "member_id": "550e8400-e29b-41d4-a716-446655440000",
  "document_type": "passport",
  "document_data": "base64_encoded_document_data"
}
```

**Response `200`**

```json
{
  "verified": true,
  "confidence": 0.95,
  "risk_level": "low"
}
```

---

## Escalations

### GET /escalations

List escalations.

**Response `200`**

```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "Urgent moderation review",
    "status": "open",
    "priority": "critical",
    "assignee": "moderator_1",
    "created_at": "2024-01-15T10:30:00Z"
  }
]
```

### POST /escalations

Create escalation.

**Request Body**

```json
{
  "title": "Urgent moderation review",
  "priority": "critical",
  "description": "Content requires immediate review"
}
```

**Response `201`**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Urgent moderation review",
  "status": "open",
  "priority": "critical",
  "assignee": null,
  "created_at": "2024-01-15T10:30:00Z"
}
```

---

## Metrics

### GET /metrics

Get Prometheus-formatted metrics.

**Response `200`** — Plain text

```
# TYPE http_requests_total counter
http_requests_total{method="GET",endpoint="/health"} 1523
# TYPE http_request_duration_seconds gauge
http_request_duration_seconds{endpoint="/api/v1/tiers"} 0.045
```

---

## Error Handling

All errors follow a consistent format:

```json
{
  "detail": "Human-readable error message"
}
```

### HTTP Status Codes

| Code | Description |
|------|-------------|
| `200` | Success |
| `201` | Created |
| `204` | No content |
| `400` | Bad request |
| `401` | Unauthorized |
| `403` | Forbidden |
| `404` | Not found |
| `422` | Validation error |
| `429` | Rate limited |
| `500` | Internal server error |

### Common Errors

**404 — Not Found**

```json
{
  "detail": "Tier '550e8400-e29b-41d4-a716-446655440000' not found"
}
```

**422 — Validation Error**

```json
{
  "detail": [
    {
      "loc": ["body", "name"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

**500 — Internal Server Error**

```json
{
  "detail": "Internal server error"
}
```

---

## Interactive Documentation

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **OpenAPI JSON:** http://localhost:8000/openapi.json
