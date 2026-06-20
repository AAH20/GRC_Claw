# ISO/IEC 42001 AIMS in GRC_Claw

GRC_Claw implements **ISO/IEC 42001:2023** (AI Management System) as architecture, code, and API—not a certification claim. Use this with the Cursor skill `.cursor/skills/iso-42001-ai-management-engineering/` and package `@grc-claw/aims`.

## AIMS planes (GRC_Claw mapping)

| Plane | Components |
|-------|------------|
| Governance | `iso42001` framework pack, scope template in `@grc-claw/aims` |
| Control | Gateway daemon, `ExecPolicy`, idempotency |
| Experience | Operator docs, health flags, integration READMEs |
| Evidence | `@grc-claw/evidence`, agent audit logs |
| Data | `@grc-claw/ingest` → [a2zsoc.com](https://a2zsoc.com) |

## Packages and APIs

| Item | Description |
|------|-------------|
| `@grc-claw/aims` | Vendor gap matrix (Anthropic, OpenAI, Cursor, OpenClaw), clause map, technical controls |
| `@grc-claw/frameworks` | `iso42001` starter pack (Annex A–aligned controls) |
| `GET /api/aims/vendor-gaps` | Optional `?vendor=anthropic\|openai\|cursor\|openclaw` |
| `GET /api/aims/technical-controls` | Scope template + TC-01…TC-06 |
| `GET /health` | `iso_42001_aims: true` |

## Vendor gap review (summary)

Architecture review prompts for common agentic stacks:

- **Anthropic** — Customer-operated AIMS boundary; tool-chain visibility via gateway mediation.
- **OpenAI** — Autonomous loops; mitigate with exec policy + max calls per session.
- **Cursor** — Local vs cloud processing in SoA; MCP supply-chain governance.
- **OpenClaw** — Deployer accountability; harden with token auth, `doctor`, SIEM forward to a2zsoc.com.

Full matrix: `import { VENDOR_GAP_MATRIX } from '@grc-claw/aims'` or `curl …/api/aims/vendor-gaps`.

## Evidence commands

```bash
export TOKEN=your-gateway-token

# Human oversight (TC-01)
curl -s -X POST http://127.0.0.1:18791/api/agent/invoke \
  -H "X-GRC-Claw-Token: $TOKEN" -H "Content-Type: application/json" \
  -d '{"sessionId":"aims-audit","tool":"soar.run_playbook","args":{}}'

# AIMS metadata
curl -s http://127.0.0.1:18791/api/aims/technical-controls | jq .

npm run test:iso42001
```

## Deliverables checklist

1. AIMS scope statement (`AIMS_SCOPE_TEMPLATE` in `@grc-claw/aims`)
2. AI risk register (customer-owned)
3. Statement of Applicability (map `iso42001` controls)
4. C4 diagrams — see [ARCHITECTURE.md](../ARCHITECTURE.md)
5. ADRs — [docs/adr/](../docs/adr/)
6. Evidence index — link gateway audit + evidence hashes

## Related

- [integrations/iso-42001/README.md](../integrations/iso-42001/README.md)
- [docs/AGENTIC_AI_SECURITY.md](./AGENTIC_AI_SECURITY.md)
- [examples in skill](../.cursor/skills/iso-42001-ai-management-engineering/examples.md)
