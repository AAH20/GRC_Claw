# A2Z SOC × GRC_Claw Integration Contract

GRC_Claw (OSS) connects to **Private A2Z SOC** via `@grc-claw/a2z-connector`. No proprietary A2Z code ships in GRC_Claw—only HTTP contracts.

## Authentication

| Header | Purpose |
|--------|---------|
| `Authorization: Bearer <A2Z_SOC_API_KEY>` | Integration principal |
| `X-A2Z-Tenant-Id` | Tenant scope |
| `X-GRC-Claw-Bridge: 1` | Identifies GRC_Claw traffic |
| `Idempotency-Key` | Required on writes |

## Endpoints (implemented in Private A2Z SOC)

### `GET /api/events?since=<iso>&limit=100`

Returns `security_events` rows for SIEM → GRC correlation.

### `POST /api/events/ingest`

Optional reverse path when GRC_Claw generates compliance-derived events.

### `GET /api/grc/controls?framework=iso27001`

Org-scoped control list (maps to Supabase `compliance_controls` today).

### `GET /api/grc/score?tenant_id=&framework=`

Compliance score for executive dashboards.

### `POST /api/grc/evidence`

Attach evidence with hash + URI (idempotent).

### `POST /api/compliance/alerts`

Push control test failures into SOC analyst queues.

## Event mapping

GRC_Claw `mapSecurityEventToControls()` writes `compliance_impact` compatible with A2Z schema:

```json
{
  "controlIds": ["iso-a.8.16", "nist-de.ae"],
  "rationale": "Mapped network.intrusion from suricata",
  "suggestedSeverity": "high"
}
```

## Deployment topology

```
[Branch sensors] → [Private A2Z SOC] ←HTTPS→ [GRC_Claw Gateway]
                              ↑
                        Analysts / Entra SSO
```

## Demo without private SOC

```bash
A2Z_SOC_MODE=demo npm run gateway
curl http://127.0.0.1:18791/health
curl -X POST http://127.0.0.1:18791/api/a2z/sync -H "X-GRC-Claw-Token: dev-change-me"
```

## Marketing

Publish GRC_Claw on GitHub; sell **Private A2Z SOC** as the production control plane with Wazuh, Snort, Suricata, and KSA-scale operations. GRC_Claw proves agent safety and GRC depth before the enterprise buy.
