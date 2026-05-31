# ISO/IEC 42001 — GRC_Claw integration

This folder documents how **GRC_Claw** supports an **AIMS** (AI Management System) aligned with ISO/IEC 42001:2023.

## Quick start

```bash
cd GRC_Claw
npm install && npm run build
GRC_CLAW_GATEWAY_TOKEN=your-token npm run gateway

curl -s http://127.0.0.1:18791/health | jq .iso_42001_aims
curl -s http://127.0.0.1:18791/api/aims/vendor-gaps | jq .
curl -s http://127.0.0.1:18791/api/aims/technical-controls | jq .
curl -s http://127.0.0.1:18791/api/frameworks | jq '.packs[] | select(.code=="iso42001")'
```

## npm packages

| Package | Role |
|---------|------|
| `@grc-claw/aims` | Vendor gaps, clauses, technical control catalog |
| `@grc-claw/frameworks` | `iso42001` control pack |
| `@grc-claw/agent-runtime` | Human oversight (approval tokens) |
| `@grc-claw/gateway` | HTTP/WS control plane |
| `@grc-claw/evidence` | Immutable evidence hashes |
| `@grc-claw/ingest` | Security event normalization → monitoring controls |

## Production SOC

Live tenant GRC and security operations: **[https://a2z-soc.com](https://a2z-soc.com)** via `@grc-claw/a2z-connector`.

## Tests

```bash
npm run test:iso42001
npm run test:comprehensive   # includes agent gating + ingest
```

## Cursor skill

`.cursor/skills/iso-42001-ai-management-engineering/` — session workflow, templates, vendor gap reference.

## Documentation

- [docs/ISO_42001_AIMS.md](../../docs/ISO_42001_AIMS.md)
