# Conversational Marketing API Reference

> Last updated: 2026-10-02 | Base URL: `https://a2zsoc.com`

AI-powered chatbots and conversational marketing across web, social, and messaging platforms.

---

## Table of Contents

- [Overview](#overview)
- [Endpoints](#endpoints)
  - [POST /api/v1/conversational/conversations](#post--api-v1-conversational-conversations)
  - [GET /api/v1/conversational/conversations](#get--api-v1-conversational-conversations)
  - [GET /api/v1/conversational/conversations/{conv}](#get--api-v1-conversational-conversations-conv)
  - [PUT /api/v1/conversational/conversations/{conv}](#put--api-v1-conversational-conversations-conv)
  - [DELETE /api/v1/conversational/conversations/{conv}](#delete--api-v1-conversational-conversations-conv)
  - [POST /api/v1/conversational/chatbots](#post--api-v1-conversational-chatbots)
  - [POST /api/v1/conversational/chatbots/{bot_id}/train](#post--api-v1-conversational-chatbots-bot-id-train)
- [Error Codes](#error-codes)
- [Rate Limiting](#rate-limiting)
- [Pagination](#pagination)
- [Authentication](#authentication)
- [Idempotency](#idempotency)

---

## Overview

The Conversational Marketing API provides programmatic access to ai-powered chatbots and conversational marketing across web, social, and messaging platforms.

**Base Path:** `/api/v1/conversational`

All endpoints require authentication via Bearer token and tenant scoping.

---

## Endpoints


### POST /api/v1/conversational/conversations

Create a new conversation.

**Request Body:**

```json
{
  "name": "New Conversation",
  "description": "A conversation"
}
```

**Response (201):**

```json
{
  "id": "conv_001",
  "name": "New Conversation",
  "status": "active",
  "created_at": "2026-10-01T00:00:00Z"
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/conversational/conversations \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -H "X-Idempotency-Key: 01J0ABC1234567890" \
  -d '{"name": "New Conversation"}'
```


### GET /api/v1/conversational/conversations

List all conversations.

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
      "id": "conv_001",
      "name": "Example"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20
}
```

**Example:**

```bash
curl -X GET "https://a2zsoc.com/api/v1/conversational/conversations" \
  -H "Authorization: Bearer <token>"
```


### GET /api/v1/conversational/conversations/{conv}

Get a conversation by ID.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `conv` | string | Yes | Conversation identifier |

**Response (200):**

```json
{
  "id": "conv_001",
  "name": "Example",
  "status": "active"
}
```

**Example:**

```bash
curl -X GET https://a2zsoc.com/api/v1/conversational/conversations/conv_001 \
  -H "Authorization: Bearer <token>"
```


### PUT /api/v1/conversational/conversations/{conv}

Update a conversation.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `conv` | string | Yes | Conversation identifier |

**Request Body:**

```json
{
  "name": "Updated Name"
}
```

**Response (200):**

```json
{
  "id": "conv_001",
  "name": "Updated Name",
  "status": "active"
}
```

**Example:**

```bash
curl -X PUT https://a2zsoc.com/api/v1/conversational/conversations/conv_001 \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "Updated Name"}'
```


### DELETE /api/v1/conversational/conversations/{conv}

Delete a conversation.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `conv` | string | Yes | Conversation identifier |

**Example:**

```bash
curl -X DELETE https://a2zsoc.com/api/v1/conversational/conversations/conv_001 \
  -H "Authorization: Bearer <token>" \
  -H "X-Idempotency-Key: 01J0ABC1234567890"
```


### POST /api/v1/conversational/chatbots

Create a new chatbot.

**Request Body:**

```json
{
  "name": "Sales Assistant",
  "platform": "web",
  "personality": "professional",
  "fallback_message": "Let me connect you with a human."
}
```

**Response (201):**

```json
{
  "chatbot_id": "bot_001",
  "name": "Sales Assistant",
  "status": "active",
  "created_at": "2026-10-01T00:00:00Z"
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/conversational/chatbots \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "Sales Assistant", "platform": "web"}'
```


### POST /api/v1/conversational/chatbots/{bot_id}/train

Train a chatbot with new data.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `bot_id` | string | Yes | Chatbot identifier |

**Request Body:**

```json
{
  "training_data": [
    {
      "question": "What is your pricing?",
      "answer": "Our pricing starts at $99/month."
    }
  ]
}
```

**Response (200):**

```json
{
  "bot_id": "bot_001",
  "status": "training",
  "estimated_completion": "2026-10-01T00:05:00Z"
}
```

**Example:**

```bash
curl -X POST https://a2zsoc.com/api/v1/conversational/chatbots/bot_001/train \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"training_data": []}'
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
