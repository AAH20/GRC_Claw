# ISO 42001 Implementation Examples

## AIMS scope (from `@grc-claw/aims`)

```typescript
import { AIMS_SCOPE_TEMPLATE } from '@grc-claw/aims';
console.log(AIMS_SCOPE_TEMPLATE);
```

## Vendor gaps API

```bash
curl -s 'http://127.0.0.1:18791/api/aims/vendor-gaps?vendor=cursor' | jq .
```

## Technical evidence — GRC_Claw

```bash
export TOKEN=your-gateway-token

curl -s -X POST http://127.0.0.1:18791/api/agent/invoke \
  -H "X-GRC-Claw-Token: $TOKEN" -H "Content-Type: application/json" \
  -d '{"sessionId":"audit","tool":"soar.run_playbook","args":{}}'
# Expect HTTP 403, allowed:false

curl -s http://127.0.0.1:18791/api/aims/technical-controls | jq '.controls[] | select(.id=="TC-01")'

npm run test:iso42001
```

## Statement of Applicability (row example)

| Control | Applicable | Implementation | Evidence ID |
|---------|------------|----------------|-------------|
| aims-a.12.3 | Yes | ExecPolicy destructive tier | EV-AGENT-001 |
| aims-a.9.1 | Yes | Supplier register + env keys | EV-SUP-003 |

## Management review KPIs

| KPI | Source |
|-----|--------|
| % destructive calls blocked without approval | Agent audit via `/api/agent/invoke` |
| Evidence attach latency | a2zsoc.com + `@grc-claw/evidence` |
| Sessions hitting max tool calls | Gateway audit logs |
