# Broker Enablement API Reference

> Last updated: 2026-10-02 | Base URL: `https://a2zsoc.com`

Onboard partners, track commissions, manage enablement workflows, and analyze broker performance.

---

## Table of Contents

- [Overview](#overview)
- [Endpoints](#endpoints)
  - [GET /health](#get-health)
  - [POST /partners](#post-partners)
  - [GET /partners/{partner_id}](#get-partners-partner_id)
  - [POST /partners/{partner_id}/enable](#post-partners-partner_id-enable)
  - [POST /commissions/calculate](#post-commissions-calculate)
  - [GET /commissions/{partner_id}](#get-commissions-partner_id)
  - [POST /commissions/{commission_id}/payout](#post-commissions-commission_id-payout)
- [Error Codes](#error-codes)
- [Rate Limiting](#rate-limiting)
- [Pagination](#pagination)
- [Authentication](#authentication)
- [Idempotency](#idempotency)

---

## Overview

The Broker Enablement API provides programmatic access to onboard partners, track commissions, manage enablement workflows, and analyze broker performance.

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

### POST /partners

Register a new partner with KYC verification and account provisioning.

**Request Body:**

```json
{
  "business_name": "Acme Brokerage",
  "contact_email": "contact@acmebrokerage.com",
  "contact_phone": "+1-555-0123",
  "business_type": "llc",
  "tax_id": "12-3456789",
  "address": {
    "street": "123 Main St",
    "city": "New York",
    "state": "NY",
    "zip": "10001",
    "country": "US"
  },
  "kyc_documents": [
    {"type": "business_license", "url": "https://docs.example.com/license.pdf"}
  ]
}
```

**Response (201):**

```json
{
  "partner_id": "part_001",
  "business_name": "Acme Brokerage",
  "status": "pending_verification",
  "kyc_status": "pending",
  "created_at": "2026-10-02T10:00:00Z"
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/partners \
  -H "Authorization: Bearer ***" \
  -H "Content-Type: application/json" \
  -H "X-Idempotency-Key: 01J0ABC1234567890" \
  -d '{"business_name": "Acme Brokerage", "contact_email": "contact@acmebrokerage.com"}'
```

---

### GET /partners/{partner_id}

Get partner details by ID.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `partner_id` | string | Yes | Partner identifier |

**Response (200):**

```json
{
  "partner_id": "part_001",
  "business_name": "Acme Brokerage",
  "status": "active",
  "kyc_status": "verified"
}
```

**Example:**

```bash
curl -X GET https://a2zsoc.com/partners/part_001 \
  -H "Authorization: Bearer ***"
```

---

### POST /partners/{partner_id}/enable

Start the enablement workflow for a partner.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `partner_id` | string | Yes | Partner identifier |

**Request Body:**

```json
{
  "partner_id": "part_001",
  "enablement_track": "standard",
  "training_modules": ["product_overview", "sales_process", "compliance"],
  "assigned_manager": "mgr_001"
}
```

**Response (200):**

```json
{
  "partner_id": "part_001",
  "enablement_id": "enable_001",
  "status": "in_progress",
  "progress": 0.0,
  "started_at": "2026-10-02T10:00:00Z",
  "estimated_completion": "2026-10-16T10:00:00Z"
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/partners/part_001/enable \
  -H "Authorization: Bearer ***" \
  -H "Content-Type: application/json" \
  -H "X-Idempotency-Key: 01J0ABC1234567890" \
  -d '{"enablement_track": "standard", "training_modules": ["product_overview"]}'
```

---

### POST /commissions/calculate

Calculate commission for a transaction.

**Request Body:**

```json

{
  "partner_id": "part_001",
  "transaction_id": "txn_001",
  "transaction_amount": 10000.00,
  "product_type": "subscription",
  "commission_rate": 0.15
}
```

**Response (201):**

```json
{
  "commission_id": "comm_001",
  "partner_id": "part_001",
  "transaction_id": "txn_001",
  "transaction_amount": 10000.00,
  "commission_rate": 0.15,
  "commission_amount": 1500.00,
  "status": "pending",
  "created_at": "2026-10-02T10:00:00Z"
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/commissions/calculate \
  -H "Authorization: Bearer ***" \
  -H "Content-Type: application/json" \
  -H "X-Idempotency-Key: 01J0ABC1234567890" \
  -d '{"partner_id": "part_001", "transaction_id": "txn_001", "transaction_amount": 10000.00, "commission_rate": 0.15}'
```

---

### GET /commissions/{partner_id}

Get commission records for a partner.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `partner_id` | string | Yes | Partner identifier |
| `status_filter` | string | No | Filter by status: `pending`, `approved`, `paid` |

**Response (200):**

```json
[
  {
    "commission_id": "comm_001",
    "partner_id": "part_001",
    "transaction_id": "txn_001",
    "transaction_amount": 10000.00,
    "commission_rate": 0.15,
    "commission_amount": 1500.00,
    "status": "pending",
    "created_at": "2026-10-02T10:00:00Z"
  }
]
```

**Example:**

```bash
curl -X GET "https://a2zsoc.com/commissions/part_001?status_filter=pending" \
  -H "Authorization: Bearer ***"
```

---

### POST /commissions/{commission_id}/payout

Process payout for a commission via Stripe.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `commission_id` | string | Yes | Commission identifier |

**Response (200):**

```json
{
  "commission_id": "comm_001",
  "payout_id": "pay_001",
  "status": "processing",
  "amount": 1500.00,
  "destination": "acct_1234567890",
  "estimated_arrival": "2026-10-04T10:00:00Z"
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/commissions/comm_001/payout \
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
