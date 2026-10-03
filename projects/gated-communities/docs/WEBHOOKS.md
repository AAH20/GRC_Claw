# Webhook Documentation

## Overview

Webhooks allow you to receive real-time notifications when events occur in your community.

## Creating a Webhook

POST /api/v1/webhooks
Content-Type: application/json

{
  "url": "https://your-app.com/webhooks",
  "events": ["member.created", "member.updated", "moderation.flagged"],
  "secret": "your-webhook-secret"
}

## Event Types

| Event | Description |
|-------|-------------|
| member.created | New member joined |
| member.updated | Member profile updated |
| member.banned | Member was banned |
| moderation.flagged | Content was flagged |
| moderation.resolved | Moderation issue resolved |
| tier.created | New tier created |
| tier.updated | Tier was updated |

## Payload Format

{
  "id": "evt_1234567890",
  "type": "member.created",
  "created": "2024-01-15T10:30:00Z",
  "data": {
    "member_id": "mem_123",
    "community_id": "com_456",
    "user_id": "usr_789"
  }
}

## Verifying Signatures

Each webhook request includes a X-Webhook-Signature header with an HMAC-SHA256 signature.

## Retry Policy

Failed webhook deliveries are retried with exponential backoff:
- 1st retry: 1 minute
- 2nd retry: 5 minutes
- 3rd retry: 30 minutes
- 4th retry: 2 hours
- 5th retry: 12 hours
