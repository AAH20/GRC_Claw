# GRC_Claw Rate Limiting & Quota Management

Comprehensive rate limiting, quota enforcement, usage tracking, and billing integration for the GRC_Claw API platform.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        API Request                          │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                  RateLimitMiddleware                         │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │ Identifier   │→ │ Rate Limiter │→ │ RateLimitResult   │  │
│  │ Extraction   │  │ (Algorithm)  │  │ (allowed/headers) │  │
│  └─────────────┘  └──────────────┘  └───────────────────┘  │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                    QuotaEngine                               │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │ Tier Config  │→ │ Quota Check  │→ │ QuotaCheckResult  │  │
│  │ Lookup       │  │ & Consume    │  │ (allowed/remaining)│ │
│  └─────────────┘  └──────────────┘  └───────────────────┘  │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                   UsageTracker                               │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │ Record Usage │→ │ Aggregate    │→ │ UsageSummary      │  │
│  │ Events       │  │ & Index      │  │ & Export          │  │
│  └─────────────┘  └──────────────┘  └───────────────────┘  │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                BillingHookManager                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ Webhook Hook │  │ Logging Hook │  │ Callback Hook    │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Rate Limiting Algorithms

### Token Bucket
- Tokens are added at a constant rate up to a maximum burst capacity
- Each request consumes one token
- When the bucket is empty, requests are rejected until tokens refill
- **Best for:** General API rate limiting with burst tolerance

### Sliding Window
- Tracks individual request timestamps within a rolling window
- More accurate than fixed window (no boundary burst issues)
- Uses more memory as it stores each request timestamp
- **Best for:** Precise rate limiting where boundary bursts are unacceptable

### Leaky Bucket
- Requests are added to a bucket and processed at a constant rate
- If the bucket overflows (exceeds capacity), the request is rejected
- Smooths bursty traffic into a steady stream
- **Best for:** Protecting downstream services from bursts

### Fixed Window
- Simple counter that resets at fixed intervals (per second)
- Can allow burst at window boundaries
- Simplest to implement and least memory usage
- **Best for:** Simple use cases where boundary bursts are acceptable

## Quota Types

| Type | Description | Example |
|------|-------------|---------|
| `REQUEST_COUNT` | Number of API requests | 10,000 requests/day |
| `BANDWIDTH` | Data transfer volume | 1 GB/month |
| `STORAGE` | Storage usage | 100 GB |
| `COMPUTE` | Compute time | 500 hours/month |
| `TOKEN_COUNT` | AI token consumption | 1M tokens/month |
| `CUSTOM` | Custom metric | Custom business metric |

## Quota Periods

| Period | Reset Frequency |
|--------|----------------|
| `MINUTELY` | Every minute |
| `HOURLY` | Every hour |
| `DAILY` | Every day at midnight UTC |
| `WEEKLY` | Every week |
| `MONTHLY` | First day of each month |
| `YEARLY` | January 1st |
| `NEVER` | Never resets (lifetime quota) |

## Service Tiers

| Tier | RPS | Burst | Daily Limit | Price |
|------|-----|-------|-------------|-------|
| Free | 10 | 20 | 10,000 | $0 |
| Starter | 50 | 100 | 100,000 | $49/mo |
| Professional | 200 | 500 | 1,000,000 | $199/mo |
| Enterprise | 1,000 | 2,000 | 10,000,000 | $999/mo |

## Quick Start

### Middleware Setup

```python
from grcclaw.rate_limit import RateLimitMiddleware, RateLimitConfig
from grcclaw.rate_limit.models import RateLimitAlgorithm

config = RateLimitConfig(
    algorithm=RateLimitAlgorithm.TOKEN_BUCKET,
    requests_per_second=100,
    burst_size=200,
    daily_limit=100000,
)

app.add_middleware(RateLimitMiddleware, config=config)
```

### Dependency Setup

```python
from fastapi import Depends
from grcclaw.rate_limit.middleware import rate_limit_dependency

@app.get("/v1.0/policies")
async def list_policies(
    result: Annotated[RateLimitResult, Depends(rate_limit_dependency)]
):
    return {"policies": []}
```

### Quota Management

```python
from grcclaw.rate_limit import QuotaEngine, QuotaType, QuotaPeriod

engine = QuotaEngine()

# Check quota
result = engine.check_quota("tenant-123", "api_calls", requested_quantity=1)
if result.allowed:
    # Process request
    engine.consume_quota("tenant-123", "api_calls", quantity=1)

# Get quota status
status = engine.get_quota_status("tenant-123", "api_calls")
print(f"Used: {status.used}/{status.limit} ({status.usage_percentage:.1f}%)")
```

### Usage Tracking

```python
from grcclaw.rate_limit import UsageTracker

tracker = UsageTracker(retention_hours=48)

# Record usage
tracker.record(
    tenant_id="tenant-123",
    identifier="apikey:abc123",
    endpoint="/v1.0/policies",
    method="GET",
    cost=0.001,
)

# Get usage summary
summary = tracker.get_usage_summary("tenant-123")
print(f"Total requests: {summary.total_requests}")
print(f"Total cost: ${summary.total_cost:.4f}")
```

### Billing Integration

```python
from grcclaw.rate_limit import (
    BillingHookManager,
    WebhookBillingHook,
    LoggingBillingHook,
)

manager = BillingHookManager()

# Add webhook hook for real-time billing
manager.register_hook(WebhookBillingHook("https://billing.example.com/webhook"))

# Add logging hook for debugging
manager.register_hook(LoggingBillingHook())

# Notify events
await manager.notify_rate_limit_hit(
    tenant_id="tenant-123",
    endpoint="/v1.0/policies",
    retry_after=30,
    limit=1000,
)

await manager.notify_quota_exceeded(
    tenant_id="tenant-123",
    quota_name="api_calls",
    used=10001,
    limit=10000,
    reset_at="2024-02-01T00:00:00Z",
)
```

## HTTP Headers

### Rate Limit Headers (on every response)

| Header | Description |
|--------|-------------|
| `X-RateLimit-Limit` | Maximum requests allowed in the window |
| `X-RateLimit-Remaining` | Requests remaining in the current window |
| `X-RateLimit-Reset` | Unix timestamp when the window resets |
| `X-RateLimit-Policy` | Name of the rate limit policy applied |
| `X-RateLimit-Algorithm` | Algorithm used (token_bucket, sliding_window, etc.) |

### Rate Limit Exceeded Response (429)

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Please retry after the specified time.",
    "details": {
      "limit": 1000,
      "remaining": 0,
      "retry_after_seconds": 30,
      "reset_at": 1704067200,
      "policy": "token_bucket",
      "algorithm": "token_bucket"
    }
  }
}
```

Headers on 429 response:
- `Retry-After: 30`
- `X-RateLimit-Limit: 1000`
- `X-RateLimit-Remaining: 0`
- `X-RateLimit-Reset: 1704067200`

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `RATE_LIMIT_ENABLED` | `true` | Enable/disable rate limiting |
| `RATE_LIMIT_ALGORITHM` | `token_bucket` | Default algorithm |
| `RATE_LIMIT_RPS` | `100` | Default requests per second |
| `RATE_LIMIT_BURST` | `200` | Default burst size |
| `RATE_LIMIT_DAILY_LIMIT` | | Default daily request limit |
| `QUOTA_ENFORCE` | `true` | Enable/disable quota enforcement |
| `QUOTA_ALLOW_OVERAGE` | `false` | Allow quota overage |
| `QUOTA_OVERAGE_MULTIPLIER` | `1.5` | Overage limit multiplier |
| `QUOTA_WARNING_THRESHOLD` | `0.8` | Warning threshold (80%) |
| `QUOTA_CRITICAL_THRESHOLD` | `0.95` | Critical threshold (95%) |

## Endpoint-Specific Limits

| Endpoint | Algorithm | RPS | Burst |
|----------|-----------|-----|-------|
| `POST /v1.0/enforcement/decide` | token_bucket | 10,000 | 2,000 |
| `POST /v1.0/enforcement/decide-batch` | token_bucket | 1,000 | 200 |
| `GET /v1.0/policies` | token_bucket | 1,000 | 200 |
| `POST /v1.0/policies` | token_bucket | 100 | 20 |
| `POST /v1.0/evidence` | token_bucket | 5,000 | 500 |
| `GET /v1.0/audit` | token_bucket | 500 | 50 |
| `POST /v1.0/compliance/reports` | token_bucket | 10 | 20 |
| `POST /v1.0/graphql` | token_bucket | 1,000 | 200 |

## Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `RATE_LIMIT_EXCEEDED` | 429 | Rate limit exceeded |
| `QUOTA_EXCEEDED` | 429 | Quota exceeded |
| `QUOTA_NOT_FOUND` | 404 | Quota definition not found |
| `RATE_LIMIT_CONFIG_ERROR` | 500 | Invalid rate limit configuration |

## Best Practices

1. **Use tier-based defaults** with endpoint-specific overrides
2. **Set burst size** to 2x the RPS for burst tolerance
3. **Monitor quota thresholds** at 80% and 95%
4. **Use Redis** for distributed rate limiting in production
5. **Record all usage** for billing and analytics
6. **Set appropriate Retry-After** headers for client backoff
7. **Skip rate limiting** for health checks and metrics endpoints
8. **Use sliding window** when boundary bursts are a concern
9. **Configure overage** carefully to balance UX and cost
10. **Export usage data** regularly for billing reconciliation
