# GRC_Claw

### OpenClaw for GRC — built for enterprise compliance operations

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Node](https://img.shields.io/badge/node-%3E%3D20-brightgreen)](package.json)
[![GitHub](https://img.shields.io/badge/GitHub-AAH20%2FGRC__Claw-181717?logo=github)](https://github.com/AAH20/GRC_Claw)
[![OpenClaw for GRC](https://img.shields.io/badge/OpenClaw-for%20GRC-8b5cf6)](ARCHITECTURE.md)
[![Agentic AI Security](https://img.shields.io/badge/Agentic%20AI-Secured-green)](docs/AGENTIC_AI_SECURITY.md)
[![A2Z SOC](https://img.shields.io/badge/A2Z%20SOC-a2z--soc.com-red)](https://a2z-soc.com)

**GRC_Claw** takes the local gateway control-plane pattern from **[OpenClaw](https://github.com/openclaw/openclaw)** and extends it into a production-grade stack for **governance, risk, and compliance (GRC)** and security operations.

[OpenClaw](https://github.com/openclaw/openclaw) is an excellent foundation for personal AI assistants—messaging channels, skills, and a supervised gateway on your own hardware. **GRC_Claw is architecturally related but purpose-built for a different class of problem:** regulated tenants, continuous control monitoring, immutable evidence, SIEM and cloud alert normalization, ISO/IEC 42001 AIMS alignment, and optional integration with a live SOC at **[a2z-soc.com](https://a2z-soc.com)**. Same daemon philosophy; materially deeper surface area for security and compliance teams.

| | [OpenClaw](https://github.com/openclaw/openclaw) | **GRC_Claw** (this repo) |
|---|----------|----------|
| **Primary use** | Personal assistant & chat channels | **Enterprise GRC + SOC automation** |
| **Control plane** | Gateway daemon (WebSocket) | Gateway daemon (**WS + HTTP APIs**) |
| **Agent governance** | Tools + skills (operator-defined) | **Mandatory exec policy** (allowlist → approval → sandbox) |
| **Compliance** | General-purpose | **Framework packs** (ISO 27001, NIST CSF, SOC 2, ISO 42001 AIMS) |
| **Evidence** | Workspace files | **SHA-256 lineage** + SOC attach API |
| **Ingest** | Channel messages | **OSS SIEM/IDS/firewall + AWS/Azure/GCP** normalizers |
| **AI supply chain** | Model provider choice | **BYOC LLM + MCP** with gated tool registry |
| **Production SOC** | Bring your own | **[a2z-soc.com](https://a2z-soc.com)** bridge (events, controls, alerts) |

---

## Why GRC_Claw

GRC_Claw is an MIT **npm workspaces monorepo** for organizations that need more than a general agent gateway: continuous control testing, audit-ready framework packs, evidence you can defend in an assessment, and **agentic AI that cannot bypass policy**—without giving up the operability that made [OpenClaw](https://github.com/openclaw/openclaw) influential in the first place.

Pair the OSS gateway with **[a2z-soc.com](https://a2z-soc.com)** for enterprise SIEM, multi-cloud ingest, and production SOC operations—or run GRC_Claw standalone for demos, audits, and integrator builds.

---

## Table of contents

- [Features](#features)
- [Monorepo structure](#monorepo-structure)
- [Packages](#packages)
- [Architecture](#architecture)
- [Quick start](#quick-start)
- [Configuration](#configuration)
- [Gateway API](#gateway-api)
- [Log and alert ingestion](#log-and-alert-ingestion)
- [A2Z SOC integration (a2z-soc.com)](#a2z-soc-integration-a2z-soccom)
- [Agentic AI security](#agentic-ai-security)
- [Testing](#testing)
- [Deployment](#deployment)
- [Documentation](#documentation)
- [License](#license)
- [Contributing](#contributing)
- [Roadmap](#roadmap)

---

## Features

| Area | What you get |
|------|----------------|
| **OpenClaw for GRC** | Long-lived gateway, `connect` handshake, idempotency, collector nodes |
| **GRC engine** | `GRCEngineFacade`, framework packs, control ↔ evidence linkage |
| **Agentic AI security** | Three-phase exec policy, tool tiers, session audit log |
| **OSS SIEM / IDS / firewall** | Wazuh, Suricata, Snort, Elastic, UFW → canonical events |
| **Multi-cloud security** | AWS, Azure, GCP (CloudWatch, Sentinel, Chronicle, GuardDuty, …) |
| **ISO/IEC 42001 AIMS** | Vendor gap matrix (Anthropic, OpenAI, Cursor, OpenClaw), technical controls API |
| **BYOC connectors** | Bring your own **LLM** (OpenAI, Anthropic, Ollama) and **MCP** servers — gated by exec policy |
| **[a2z-soc.com](https://a2z-soc.com)** | Optional connector for live SOC + GRC sync |
| **Ship-ready OSS** | Docker Compose, systemd, comprehensive tests |

---

## Monorepo structure

```
GRC_Claw/
├── package.json
├── tsconfig.json
├── LICENSE
├── ARCHITECTURE.md
├── docs/
├── packages/
│   ├── core/
│   ├── gateway/                 # OpenClaw-style control plane
│   ├── agent-runtime/
│   ├── evidence/
│   ├── frameworks/
│   ├── aims/                    # ISO/IEC 42001 AIMS (vendor gaps, clauses)
│   ├── connectors/              # BYOC LLM + MCP registry
│   ├── ingest/                  # OSS + cloud normalizers
│   └── a2z-connector/           # a2z-soc.com API bridge
├── integrations/iso-42001/
├── .cursor/skills/iso-42001-ai-management-engineering/
├── integrations/a2z-soc/
├── deploy/
├── examples/
└── scripts/
```

### Requirements

- **Node.js** ≥ 20 · **npm** ≥ 9 (workspaces)

```bash
git clone https://github.com/AAH20/GRC_Claw.git && cd GRC_Claw
npm install && npm run build
```

---

## Packages

| Package | Description |
|---------|-------------|
| `@grc-claw/core` | Canonical events, `GRCEngineFacade` |
| `@grc-claw/gateway` | **OpenClaw for GRC** — HTTP/WS gateway daemon |
| `@grc-claw/agent-runtime` | Exec policy + audited agent sessions |
| `@grc-claw/evidence` | SHA-256 evidence lineage |
| `@grc-claw/frameworks` | ISO 27001, NIST CSF, SOC 2, ISO 42001 starter packs |
| `@grc-claw/aims` | ISO 42001 vendor gaps, clause map, technical controls |
| `@grc-claw/connectors` | BYOC LLM providers + MCP servers (registry, proxy, policy tools) |
| `@grc-claw/ingest` | OSS SIEM/IDS/firewall + AWS/Azure/GCP normalizers |
| `@grc-claw/a2z-connector` | Bridge to **[a2z-soc.com](https://a2z-soc.com)** APIs |

| Script | Command |
|--------|---------|
| Build | `npm run build` |
| Gateway | `npm run gateway` |
| Doctor | `npm run doctor` |
| Tests | `npm run test` · `npm run test:byoc` · `npm run test:iso42001` · `npm run test:cloud` · `npm run test:comprehensive` |

---

## Architecture

**Architecture first, daemons second** — informed by [OpenClaw](https://github.com/openclaw/openclaw), extended for GRC and security operations.

| Plane | Components | Role |
|-------|------------|------|
| **Control** | `gateway`, `agent-runtime` | Auth, WS `connect`, routing, agent policy |
| **Evidence** | `evidence`, `frameworks` | Controls, hashed artifacts, frameworks |
| **Data** | `ingest`, `a2z-connector` | Alerts → canonical events → compliance impact |

```text
  Wazuh · Suricata · Sentinel · GuardDuty · Chronicle …
                        │
                        ▼
              ┌─────────────────────┐
              │   GRC_Claw Gateway   │  ← OpenClaw for GRC
              │   :18791 · WS + HTTP │
              └──────────┬──────────┘
                         │
         ┌───────────────┼───────────────┐
         ▼               ▼               ▼
    frameworks      agent-runtime    a2z-soc.com
    evidence         (gated SOAR)     (optional)
```

Details: [ARCHITECTURE.md](ARCHITECTURE.md).

---

## Quick start

```bash
cp examples/a2z-private-bridge.env.example .env

export GRC_CLAW_GATEWAY_TOKEN=change-me-in-production
export A2Z_SOC_MODE=demo   # use private + a2z-soc.com URL for production

npm run gateway
curl -s http://127.0.0.1:18791/health | jq .
```

**Example — normalize a Suricata alert:**

```bash
curl -s -X POST http://127.0.0.1:18791/api/ingest/normalize \
  -H "X-GRC-Claw-Token: $GRC_CLAW_GATEWAY_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"source":"suricata","tenantId":1,"payload":{"alert":{"severity":1,"signature":"ET SCAN"},"src_ip":"10.0.0.5","dest_ip":"10.0.0.10"}}'
```

**Docker:**

```bash
docker compose -f deploy/docker-compose.yml up --build
```

---

## Configuration

| Variable | Description |
|----------|-------------|
| `GRC_CLAW_GATEWAY_TOKEN` | API auth token (**required**) |
| `GRC_CLAW_HOST` / `GRC_CLAW_PORT` | Bind (default `127.0.0.1:18791`) |
| `A2Z_SOC_MODE` | `demo` or `private` (live **[a2z-soc.com](https://a2z-soc.com)**) |
| `A2Z_SOC_BASE_URL` | Your A2Z SOC API base (e.g. `https://a2z-soc.com`) |
| `A2Z_SOC_API_KEY` | Integration key from A2Z SOC |
| `A2Z_SOC_TENANT_ID` | Tenant scope |

Run `npm run doctor` before production.

---

## Gateway API

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Status, `iso_42001_aims`, `cloud_sources` |
| `GET` | `/api/frameworks` | Framework packs |
| `GET` | `/api/aims/vendor-gaps` | Anthropic / OpenAI / Cursor / OpenClaw gap matrix |
| `GET` | `/api/aims/technical-controls` | AIMS scope, clauses, TC-01…TC-06 |
| `POST` | `/api/ingest/normalize` | Alert → canonical event + control impact |
| `POST` | `/api/a2z/sync` | Sync events from A2Z SOC |
| `POST` | `/api/agent/invoke` | Gated agent tool call |
| `GET` | `/api/connectors` | BYOC LLM + MCP registry (redacted) |
| `POST` | `/api/connectors/llm/:id/chat` | LLM chat proxy |
| `GET` | `/api/connectors/mcp/:id/tools` | Discover MCP tools |
| `WS` | `/` | `connect` → `hello-ok` |

See [docs/BYOC_CONNECTORS.md](docs/BYOC_CONNECTORS.md) for configuration.

Auth: `X-GRC-Claw-Token` or `Authorization: Bearer`.

---

## Log and alert ingestion

`POST /api/ingest/normalize` — `source`, `tenantId`, `payload`.

**OSS:** `wazuh` · `suricata` · `snort` · `elastic` · `ufw`

**Cloud:** `aws_guardduty` · `aws_cloudwatch` · `aws_securityhub` · `aws_cloudtrail` · `azure_sentinel` · `azure_defender` · `azure_monitor` · `gcp_chronicle` · `gcp_scc` · `gcp_cloud_logging`

Canonical shape (`@grc-claw/core`):

```json
{
  "eventUuid": "<stable-uuid>",
  "eventType": "network.intrusion",
  "severity": "high",
  "sourceSystem": "azure_sentinel",
  "tenantId": 1,
  "eventData": { "@timestamp": "…", "message": "…", "raw": {} }
}
```

See [packages/ingest](packages/ingest).

---

## A2Z SOC integration (a2z-soc.com)

Production security operations and tenant GRC data live on **[a2z-soc.com](https://a2z-soc.com)**. GRC_Claw connects via `@grc-claw/a2z-connector`:

```bash
A2Z_SOC_MODE=private
A2Z_SOC_BASE_URL=https://a2z-soc.com
A2Z_SOC_API_KEY=<your-integration-key>
A2Z_SOC_TENANT_ID=1
```

| Direction | Behavior |
|-----------|----------|
| **Inbound** | Security events → normalized → compliance control impact |
| **Outbound** | Control test failures → SOC alerts |
| **GRC** | Scores, controls, evidence (see [integrations/a2z-soc/README.md](integrations/a2z-soc/README.md)) |

**Demo mode** (`A2Z_SOC_MODE=demo`) works offline for CI and local dev—no API key required.

Learn more about the platform: **[https://a2z-soc.com](https://a2z-soc.com)**

---

## Agentic AI security

OpenClaw for GRC means agents are **untrusted by default**:

1. **Allowlist** — registered tools only  
2. **Approval** — destructive SOAR (Sentinel playbooks, etc.) needs `approvalToken`  
3. **Sandbox** — Docker default  

| Tier | Examples |
|------|----------|
| Read | `grc.list_controls`, `sentinel.get_incident`, `soc.query_events` |
| Write | `evidence.attach` (+ idempotency key) |
| Destructive | `sentinel.run_playbook`, `chronicle.soar.run_playbook` |

[docs/AGENTIC_AI_SECURITY.md](docs/AGENTIC_AI_SECURITY.md)

---

## Testing

```bash
npm run test:comprehensive   # OSS + architecture + ISO 42001 + cloud
npm run test:iso42001        # AIMS package + gateway AIMS APIs
npm run test:cloud           # AWS / Azure / GCP
./scripts/test.sh            # Gateway smoke
```

---

## Deployment

- **systemd:** [deploy/systemd/grc-claw-gateway.service](deploy/systemd/grc-claw-gateway.service)  
- **Docker:** [deploy/docker-compose.yml](deploy/docker-compose.yml)  

Production: strong gateway token, TLS at reverse proxy, scoped **a2z-soc.com** API key, agent approvals enabled.

---

## Documentation

| Doc | Topic |
|-----|--------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | Gateway daemon, planes, OpenClaw mapping |
| [docs/AGENTIC_AI_SECURITY.md](docs/AGENTIC_AI_SECURITY.md) | Agent threat model |
| [docs/MARKETING_A2Z_SOC.md](docs/MARKETING_A2Z_SOC.md) | Positioning with [a2z-soc.com](https://a2z-soc.com) |
| [integrations/a2z-soc/README.md](integrations/a2z-soc/README.md) | API contract |
| [docs/BYOC_CONNECTORS.md](docs/BYOC_CONNECTORS.md) | Bring Your Own LLM + MCP |
| [docs/ISO_42001_AIMS.md](docs/ISO_42001_AIMS.md) | ISO/IEC 42001 AIMS architecture + APIs |
| [integrations/iso-42001/README.md](integrations/iso-42001/README.md) | ISO 42001 integration guide |
| Cursor skill | `.cursor/skills/iso-42001-ai-management-engineering/` |

---

## License

GRC_Claw is [MIT licensed](LICENSE). Fork, integrate, and ship.

---

## Contributing

PRs welcome: framework packs, cloud connectors, agent policy presets.

```bash
npm install && npm run build && npm run test:comprehensive
```

---

## Roadmap

- [ ] npm publish `@grc-claw/*`
- [ ] Helm chart
- [ ] Gateway metrics (Prometheus)
- [ ] Signed auditor export bundles

---

**Inspired by [OpenClaw](https://github.com/openclaw/openclaw). Engineered for enterprise GRC. Secured for agents. Production SOC at [a2z-soc.com](https://a2z-soc.com).**
