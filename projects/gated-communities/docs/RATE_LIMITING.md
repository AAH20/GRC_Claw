# Rate Limiting

## Overview

Gated Communities API implements rate limiting to ensure fair usage and protect against abuse.

## Limits

| Endpoint Type | Rate Limit |
|--------------|------------|
| General API | 100 requests/minute |
| Authentication | 10 requests/minute |
| Search | 30 requests/minute |
| Export | 10 requests/minute |
| Bulk Operations | 5 requests/minute |

## Headers

Each response includes rate limit headers:
- X-RateLimit-Limit: 100
- X-RateLimit-Remaining: 95
- X-RateLimit-Reset: 1640995200

## Handling Rate Limits

When you receive a 429 response, wait for the specified time before retrying.

## Best Practices

1. Implement exponential backoff
2. Cache responses when possible
3. Use bulk operations instead of individual requests
4. Monitor your rate limit usage
