# Gated Communities API — Advanced Usage

## Error Handling

All API errors follow RFC 7807 problem details:

```json
{
  "type": "https://api.gated-communities.dev/errors/quota-exceeded",
  "title": "Quota Exceeded",
  "status": 429,
  "detail": "Rate limit reached for tier 'pro'",
  "instance": "/v1/communities/abc/members",
  "retry_after_seconds": 30
}
```

| Status | Type | Resolution |
|--------|------|------------|
| 400 | `validation-error` | Fix request body per `detail` |
| 401 | `unauthorized` | Refresh API key |
| 403 | `forbidden` | Check community permissions |
| 404 | `not-found` | Verify resource ID |
| 409 | `conflict` | Resolve state mismatch |
| 429 | `quota-exceeded` | Back off using `Retry-After` |
| 500 | `internal-error` | Retry with exponential backoff |

**Retry pattern (Python):**

```python
import time, requests

def call_with_retry(fn, max_attempts=3, base_delay=1.0):
    for attempt in range(max_attempts):
        try:
            return fn()
        except requests.HTTPError as e:
            if e.response.status_code not in (429, 500, 502, 503):
                raise
            delay = e.response.headers.get("Retry-After", base_delay * (2 ** attempt))
            time.sleep(float(delay))
    raise RuntimeError("max retries exceeded")
```

## SDK Usage

### Install

```bash
npm install @gated-communities/sdk
# or
pip install gated-communities
```

### Initialize

```typescript
import { GatedCommunities } from "@gated-communities/sdk";

const gc = new GatedCommunities({
  apiKey: process.env.GC_API_KEY,
  baseUrl: "https://api.gated-communities.dev",
});
```

### Common Operations

```typescript
// Create a gated community
const community = await gc.communities.create({
  name: "Founders Circle",
  gateType: "token-holder",
  tokenContract: "0xABC…",
  minBalance: "1000",
});

// Add a member with gate verification
await gc.members.add(community.id, {
  address: "0xMember…",
  role: "member",
});

// Verify gate status for a wallet
const status = await gc.gates.verify(community.id, "0xWallet…");
console.log(status.eligible, status.reason);

// List members with pagination
for await (const page of gc.members.list(community.id, { limit: 100 })) {
  for (const member of page.data) {
    console.log(member.address, member.role);
  }
}
```

### Error Handling in SDK

```typescript
import { GatedCommunitiesError, RateLimitError } from "@gated-communities/sdk";

try {
  await gc.communities.create(payload);
} catch (err) {
  if (err instanceof RateLimitError) {
    console.log(`Retry after ${err.retryAfter}s`);
  } else if (err instanceof GatedCommunitiesError) {
    console.log(err.code, err.detail);
  }
}
```

## Webhooks

### Configure Endpoint

```bash
curl -X POST https://api.gated-communities.dev/v1/webhooks \
  -H "Authorization: Bearer $GC_API_KEY" \
  -d '{
    "url": "https://example.com/hooks/gc",
    "events": ["member.added", "member.removed", "gate.passed", "gate.failed"],
    "secret": "whsec_…"
  }'
```

### Event Payload

```json
{
  "id": "evt_01J…",
  "type": "member.added",
  "created": "2026-10-03T12:00:00Z",
  "data": {
    "community_id": "comm_abc",
    "member": {
      "address": "0xMember…",
      "role": "member",
    }
  }
}
```

### Verify Signatures

```python
import hmac, hashlib

def verify_webhook(payload: bytes, secret: str, signature: str) -> bool:
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)
```

### Handle Events (Express)

```javascript
app.post("/hooks/gc", express.raw({ type: "application/json" }), (req, res) => {
  const sig = req.headers["x-gc-signature"];
  if (!verifyWebhook(req.body, process.env.WC_SECRET, sig)) {
    return res.status(401).send("invalid signature");
  }
  const event = JSON.parse(req.body);
  switch (event.type) {
    case "member.added":
      grantAccess(event.data.member.address);
      break;
    case "member.removed":
      revokeAccess(event.data.member.address);
      break;
  }
  res.status(200).end();
});
```

## Integration Guide

### Authentication

All requests require a Bearer token:

```
Authorization: Bearer gc_live_…
```

Keys are scoped per environment (`gc_test_` / `gc_live_`). Rotate via dashboard.

### Idempotency

Pass `Idempotency-Key` header for safe retries:

```bash
curl -X POST /v1/communities \
  -H "Idempotency-Key: 550e8400-e29b-41d4-a716-446655440000" \
  -d '{…}'
```

### Rate Limits

| Tier | Requests/min | Burst |
|------|-------------|-------|
| free | 60 | 10 |
| pro | 600 | 100 |
| enterprise | 6000 | 1000 |

Headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`.

### Pagination

Cursor-based. Use `starting_after` from the previous response's `next_cursor`.

```python
cursor = None
while True:
    resp = client.communities.list(cursor=cursor, limit=50)
    process(resp.data)
    cursor = resp.next_cursor
    if not cursor:
        break
```

### Full Integration Example (Node.js)

```javascript
const express = require("express");
const { GatedCommunities } = require("@gated-communities/sdk");

const gc = new GatedCommunities({ apiKey: process.env.GC_API_KEY });
const app = express();

app.post("/join", async (req, res) => {
  const { communityId, address } = req.body;
  try {
    const gate = await gc.gates.verify(communityId, address);
    if (!gate.eligible) {
      return res.status(403).json({ error: gate.reason });
    }
    const member = await gc.members.add(communityId, { address });
    res.json({ member });
  } catch (err) {
    if (err.code === "quota-exceeded") {
      return res.status(429).json({ error: "rate limited" });
    }
    throw err;
  }
});

app.listen(3000);
```

### Testing

Use the sandbox environment with test keys. Mock webhook delivery:

```bash
curl -X POST https://api.gated-communities.dev/v1/webhooks/test \
  -H "Authorization: Bearer gc_test_…" \
  -d '{"event": "member.added", "data": {…}}'
```
