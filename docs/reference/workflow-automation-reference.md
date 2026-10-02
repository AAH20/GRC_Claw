# Workflow Automation API Reference

> Last updated: 2026-10-02 | Base URL: `https://a2zsoc.com` | Version: `0.1.0`

Agentic AI marketing workflow automation platform. Discover, create, and execute automated workflows across n8n, Zapier, and Make integrations.

---

## Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [Endpoints](#endpoints)
  - [Workflows](#workflows)
    - [POST /api/v1/workflows](#post--api-v1-workflows)
    - [GET /api/v1/workflows](#get--api-v1-workflows)
    - [GET /api/v1/workflows/{workflow_id}](#get--api-v1-workflows-workflow_id)
    - [PUT /api/v1/workflows/{workflow_id}](#put--api-v1-workflows-workflow_id)
    - [DELETE /api/v1/workflows/{workflow_id}](#delete--api-v1-workflows-workflow_id)
    - [POST /api/v1/workflows/{workflow_id}/execute](#post--api-v1-workflows-workflow_id-execute)
    - [POST /api/v1/workflows/{workflow_id}/pause](#post--api-v1-workflows-workflow_id-pause)
    - [POST /api/v1/workflows/{workflow_id}/resume](#post--api-v1-workflows-workflow_id-resume)
  - [Processes](#processes)
    - [POST /api/v1/processes](#post--api-v1-processes)
    - [GET /api/v1/processes](#get--api-v1-processes)
    - [GET /api/v1/processes/{process_id}](#get--api-v1-processes-process_id)
    - [POST /api/v1/processes/{process_id}/execute](#post--api-v1-processes-process_id-execute)
    - [GET /api/v1/processes/{process_id}/executions](#get--api-v1-processes-process_id-executions)
    - [POST /api/v1/executions/{execution_id}/cancel](#post--api-v1-executions-execution_id-cancel)
  - [Discovery](#discovery)
    - [POST /api/v1/workflows/discover](#post--api-v1-workflows-discover)
- [Error Codes](#error-codes)
- [Rate Limiting](#rate-limiting)
- [Pagination](#pagination)
- [Idempotency](#idempotency)
- [Webhooks](#webhooks)

---

## Overview

The Workflow Automation API provides programmatic access to automate marketing workflows with visual workflow builder, triggers, and actions.

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

### Workflows

#### POST /api/v1/workflows

Create a new workflow.

**Request Body:**

```json
{
  "name": "Lead Nurture Workflow",
  "description": "Automated lead nurturing sequence",
  "trigger": "lead_created",
  "workflow_type": "lead_generation",
  "steps": [
    {
      "step_id": "step_001",
      "name": "Send Welcome Email",
      "description": "Send welcome email to new lead",
      "step_type": "email",
      "config": {
        "template": "welcome",
        "delay": 0
      },
      "order": 0,
      "depends_on": []
    },
    {
      "step_id": "step_002",
      "name": "Check Lead Score",
      "description": "Evaluate lead score threshold",
      "step_type": "condition",
      "config": {
        "field": "lead_score",
        "operator": "greater_than",
        "value": 70
      },
      "order": 1,
      "depends_on": ["step_001"]
    },
    {
      "step_id": "step_003",
      "name": "Notify Sales Team",
      "description": "Send notification to sales",
      "step_type": "action",
      "config": {
        "action": "notify_sales",
        "channel": "slack"
      },
      "order": 2,
      "depends_on": ["step_002"]
    }
  ],
  "status": "active",
  "metadata": {}
}
```

**Response (201):**

```json
{
  "workflow_id": "wf_001",
  "name": "Lead Nurture Workflow",
  "description": "Automated lead nurturing sequence",
  "workflow_type": "lead_generation",
  "status": "active",
  "steps_count": 3,
  "created_at": "2026-10-01T00:00:00Z"
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/workflows \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -H "X-Idempotency-Key: 01J0ABC1234567890" \
  -d '{"name": "Lead Nurture", "trigger": "lead_created"}'
```

---

#### GET /api/v1/workflows

List all workflows.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `status` | string | No | Filter by status: `active`, `paused`, `draft`, `error` |
| `workflow_type` | string | No | Filter by type: `lead_generation`, `email_campaign`, `social_media`, `analytics`, `onboarding`, `custom` |
| `source` | string | No | Filter by source: `n8n`, `zapier`, `make` |
| `cursor` | string | No | Pagination cursor |
| `limit` | integer | No | Items per page (default: 20, max: 100) |

**Response (200):**

```json
{
  "data": [
    {
      "workflow_id": "wf_001",
      "name": "Lead Nurture Workflow",
      "status": "active",
      "workflow_type": "lead_generation",
      "source": "n8n",
      "steps_count": 3,
      "created_at": "2026-10-01T00:00:00Z"
    }
  ],
  "pagination": {
    "cursor": "eyJpZCI6IndmXzAwMSJ9",
    "hasMore": false,
    "totalCount": 1
  }
}
```

**Example:**

```bash
curl -X GET "https://a2zsoc.com/api/v1/workflows?status=active" \
  -H "Authorization: Bearer <token>"
```

---

#### GET /api/v1/workflows/{workflow_id}

Get a workflow by ID.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `workflow_id` | string | Yes | Workflow identifier |

**Response (200):**

```json
{
  "workflow_id": "wf_001",
  "name": "Lead Nurture Workflow",
  "description": "Automated lead nurturing sequence",
  "workflow_type": "lead_generation",
  "status": "active",
  "source": "n8n",
  "steps": [
    {
      "step_id": "step_001",
      "name": "Send Welcome Email",
      "step_type": "email",
      "config": {"template": "welcome", "delay": 0},
      "order": 0,
      "depends_on": []
    }
  ],
  "metadata": {},
  "created_at": "2026-10-01T00:00:00Z",
  "updated_at": "2026-10-01T00:00:00Z"
}
```

**Example:**

```bash
curl -X GET https://a2zsoc.com/api/v1/workflows/wf_001 \
  -H "Authorization: Bearer <token>"
```

---

#### PUT /api/v1/workflows/{workflow_id}

Update a workflow.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `workflow_id` | string | Yes | Workflow identifier |

**Request Body:**

```json
{
  "name": "Updated Workflow",
  "status": "paused",
  "steps": []
}
```

**Response (200):**

```json
{
  "workflow_id": "wf_001",
  "name": "Updated Workflow",
  "status": "paused",
  "updated_at": "2026-10-01T12:00:00Z"
}
```

**Example:**

```bash
curl -X PUT https://a2zsoc.com/api/v1/workflows/wf_001 \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"status": "paused"}'
```

---

#### DELETE /api/v1/workflows/{workflow_id}

Delete a workflow.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `workflow_id` | string | Yes | Workflow identifier |

**Response:** `204 No Content`

**Example:**

```bash
curl -X DELETE https://a2zsoc.com/api/v1/workflows/wf_001 \
  -H "Authorization: Bearer <token>" \
  -H "X-Idempotency-Key: 01J0ABC1234567890"
```

---

#### POST /api/v1/workflows/{workflow_id}/execute

Manually trigger a workflow execution.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `workflow_id` | string | Yes | Workflow identifier |

**Request Body:**

```json
{
  "input_data": {
    "lead_id": "lead_001",
    "email": "lead@example.com",
    "source": "website"
  },
  "triggered_by": "manual"
}
```

**Response (202):**

```json
{
  "execution_id": "exec_001",
  "workflow_id": "wf_001",
  "status": "running",
  "started_at": "2026-10-01T00:00:00Z",
  "triggered_by": "manual"
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/workflows/wf_001/execute \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"input_data": {"lead_id": "lead_001"}}'
```

---

#### POST /api/v1/workflows/{workflow_id}/pause

Pause an active workflow.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `workflow_id` | string | Yes | Workflow identifier |

**Response (200):**

```json
{
  "workflow_id": "wf_001",
  "status": "paused",
  "paused_at": "2026-10-01T00:00:00Z"
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/workflows/wf_001/pause \
  -H "Authorization: Bearer <token>"
```

---

#### POST /api/v1/workflows/{workflow_id}/resume

Resume a paused workflow.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `workflow_id` | string | Yes | Workflow identifier |

**Response (200):**

```json
{
  "workflow_id": "wf_001",
  "status": "active",
  "resumed_at": "2026-10-01T00:00:00Z"
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/workflows/wf_001/resume \
  -H "Authorization: Bearer <token>"
```

---

### Processes

#### POST /api/v1/processes

Create a new automated process.

**Request Body:**

```json
{
  "name": "Daily Data Sync",
  "description": "Sync CRM data daily",
  "process_type": "data_sync",
  "steps": [
    {
      "step_id": "step_001",
      "name": "Fetch CRM Data",
      "action": "http_request",
      "config": {
        "url": "https://api.crm.example.com/contacts",
        "method": "GET",
        "headers": {"Authorization": "Bearer crm_token"}
      },
      "order": 0,
      "depends_on": [],
      "timeout_seconds": 300,
      "max_retries": 3
    },
    {
      "step_id": "step_002",
      "name": "Transform Data",
      "action": "data_transform",
      "config": {
        "source_key": "data",
        "transform_type": "map",
        "mapping": {"name": "full_name", "email": "email_address"}
      },
      "order": 1,
      "depends_on": ["step_001"]
    },
    {
      "step_id": "step_003",
      "name": "Update Database",
      "action": "update_database",
      "config": {
        "table": "contacts",
        "operation": "upsert"
      },
      "order": 2,
      "depends_on": ["step_002"]
    }
  ],
  "schedule": "0 2 * * *",
  "is_active": true,
  "metadata": {}
}
```

**Response (201):**

```json
{
  "process_id": "proc_001",
  "name": "Daily Data Sync",
  "process_type": "data_sync",
  "status": "active",
  "steps_count": 3,
  "schedule": "0 2 * * *",
  "created_at": "2026-10-01T00:00:00Z"
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/processes \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -H "X-Idempotency-Key: 01J0ABC1234567890" \
  -d '{"name": "Daily Sync", "process_type": "data_sync"}'
```

---

#### GET /api/v1/processes

List all processes.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `process_type` | string | No | Filter by type: `data_sync`, `report_generation`, `lead_routing`, `content_distribution`, `campaign_management`, `custom` |
| `is_active` | boolean | No | Filter by active status |
| `cursor` | string | No | Pagination cursor |
| `limit` | integer | No | Items per page (default: 20, max: 100) |

**Response (200):**

```json
{
  "data": [
    {
      "process_id": "proc_001",
      "name": "Daily Data Sync",
      "process_type": "data_sync",
      "is_active": true,
      "schedule": "0 2 * * *",
      "created_at": "2026-10-01T00:00:00Z"
    }
  ],
  "pagination": {
    "cursor": "eyJpZCI6InByb2NfMDAxIn0=",
    "hasMore": false,
    "totalCount": 1
  }
}
```

**Example:**

```bash
curl -X GET "https://a2zsoc.com/api/v1/processes?process_type=data_sync" \
  -H "Authorization: Bearer <token>"
```

---

#### GET /api/v1/processes/{process_id}

Get a process by ID.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `process_id` | string | Yes | Process identifier |

**Response (200):**

```json
{
  "process_id": "proc_001",
  "name": "Daily Data Sync",
  "process_type": "data_sync",
  "is_active": true,
  "schedule": "0 2 * * *",
  "steps": [],
  "metadata": {},
  "created_at": "2026-10-01T00:00:00Z",
  "updated_at": "2026-10-01T00:00:00Z"
}
```

**Example:**

```bash
curl -X GET https://a2zsoc.com/api/v1/processes/proc_001 \
  -H "Authorization: Bearer <token>"
```

---

#### POST /api/v1/processes/{process_id}/execute

Execute a process.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `process_id` | string | Yes | Process identifier |

**Request Body:**

```json
{
  "parameters": {
    "date": "2026-10-01"
  },
  "triggered_by": "manual"
}
```

**Response (202):**

```json
{
  "execution_id": "exec_001",
  "process_id": "proc_001",
  "status": "running",
  "started_at": "2026-10-01T00:00:00Z",
  "triggered_by": "manual"
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/processes/proc_001/execute \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"parameters": {"date": "2026-10-01"}}'
```

---

#### GET /api/v1/processes/{process_id}/executions

List executions for a process.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `process_id` | string | Yes | Process identifier |
| `status` | string | No | Filter by status: `pending`, `running`, `completed`, `failed`, `cancelled`, `timed_out` |
| `cursor` | string | No | Pagination cursor |
| `limit` | integer | No | Items per page (default: 20, max: 100) |

**Response (200):**

```json
{
  "data": [
    {
      "execution_id": "exec_001",
      "process_id": "proc_001",
      "status": "completed",
      "started_at": "2026-10-01T02:00:00Z",
      "completed_at": "2026-10-01T02:05:00Z",
      "duration_seconds": 300.0,
      "triggered_by": "schedule"
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
curl -X GET "https://a2zsoc.com/api/v1/processes/proc_001/executions?status=completed" \
  -H "Authorization: Bearer <token>"
```

---

#### POST /api/v1/executions/{execution_id}/cancel

Cancel a running execution.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `execution_id` | string | Yes | Execution identifier |

**Response (200):**

```json
{
  "execution_id": "exec_001",
  "status": "cancelled",
  "cancelled_at": "2026-10-01T00:00:00Z"
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/executions/exec_001/cancel \
  -H "Authorization: Bearer <token>"
```

---

### Discovery

#### POST /api/v1/workflows/discover

Discover existing workflows from connected platforms.

**Request Body:**

```json
{
  "sources": ["n8n", "zapier", "make"],
  "workflow_types": ["lead_generation", "email_campaign"],
  "include_inactive": false,
  "max_results": 100
}
```

**Response (200):**

```json
{
  "discovery_id": "disc_001",
  "workflows": [
    {
      "workflow_id": "wf_disc_001",
      "name": "n8n_lead_gen_workflow",
      "description": "Lead generation workflow from n8n",
      "workflow_type": "lead_generation",
      "status": "active",
      "source": "n8n",
      "steps": [
        {
          "step_id": "step_001",
          "name": "trigger",
          "description": "Form submission trigger",
          "step_type": "trigger",
          "order": 0
        }
      ],
      "created_at": "2026-10-01T00:00:00Z"
    }
  ],
  "total_found": 1,
  "sources_queried": ["n8n", "zapier", "make"],
  "duration_seconds": 2.5,
  "created_at": "2026-10-01T00:00:00Z"
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/workflows/discover \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"sources": ["n8n"], "workflow_types": ["lead_generation"]}'
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

Subscribe to workflow and process events:

| Event | Description |
|-------|-------------|
| `workflow.created` | New workflow created |
| `workflow.executed` | Workflow execution started |
| `workflow.paused` | Workflow paused |
| `workflow.resumed` | Workflow resumed |
| `process.executed` | Process execution started |
| `process.completed` | Process execution completed |
| `process.failed` | Process execution failed |
| `execution.cancelled` | Execution cancelled |

**Webhook Payload:**

```json
{
  "event": "workflow.executed",
  "timestamp": "2026-10-01T00:00:00Z",
  "data": {
    "workflow_id": "wf_001",
    "execution_id": "exec_001",
    "status": "running"
  }
}
```
