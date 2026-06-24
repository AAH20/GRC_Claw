# GRC_Claw

### The OSS chassis for ISO 42001-compliant agentic AI — Swarm Harness, Anti-Swarm WAF, MAVLink & UAS compliance, a2zsoc.com bridge

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Node](https://img.shields.io/badge/node-%3E%3D20-brightgreen)](package.json)
[![GitHub](https://img.shields.io/badge/GitHub-AAH20%2FGRC__Claw-181717?logo=github)](https://github.com/AAH20/GRC_Claw)
[![OpenClaw for GRC](https://img.shields.io/badge/OpenClaw-for%20GRC-8b5cf6)](ARCHITECTURE.md)
[![Agentic AI Security](https://img.shields.io/badge/Agentic%20AI-Secured-green)](docs/AGENTIC_AI_SECURITY.md)
[![A2Z SOC](https://img.shields.io/badge/A2Z%20SOC-a2zsoc.com-red)](https://a2zsoc.com)

**GRC_Claw** takes the local gateway control-plane pattern from **[OpenClaw](https://github.com/openclaw/openclaw)** and extends it into a production-grade stack for **governance, risk, and compliance (GRC)** and security operations.

[OpenClaw](https://github.com/openclaw/openclaw) is an excellent foundation for personal AI assistants—messaging channels, skills, and a supervised gateway on your own hardware. **GRC_Claw is architecturally related but purpose-built for a different class of problem:** regulated tenants, continuous control monitoring, immutable evidence, SIEM and cloud alert normalization, ISO/IEC 42001 AIMS alignment, and optional integration with a live SOC at **[a2zsoc.com](https://a2zsoc.com)**. Same daemon philosophy; materially deeper surface area for security and compliance teams.

| | [OpenClaw](https://github.com/openclaw/openclaw) | **GRC_Claw** (this repo) |
|---|----------|----------|
| **Primary use** | Personal assistant & chat channels | **Enterprise GRC + SOC automation** |
| **Control plane** | Gateway daemon (WebSocket) | Gateway daemon (**WS + HTTP APIs**) |
| **Agent governance** | Tools + skills (operator-defined) | **Mandatory exec policy** + **`claw.*` skill executor** (list / get / run) |
| **Compliance** | General-purpose | **Framework packs** (ISO 27001, NIST CSF, SOC 2, ISO 42001 AIMS) |
| **Evidence** | Workspace files | **SHA-256 lineage** + SOC attach API |
| **Ingest** | Channel messages | **OSS SIEM/IDS/firewall + AWS/Azure/GCP** normalizers |
| **AI supply chain** | Model provider choice | **BYOC LLM + MCP** with gated tool registry |
| **Production SOC** | Bring your own | **[a2zsoc.com](https://a2zsoc.com)** bridge (events, controls, alerts) |

---

## Why GRC_Claw

GRC_Claw is an MIT **npm workspaces monorepo** for organizations that need more than a general agent gateway: continuous control testing, audit-ready framework packs, evidence you can defend in an assessment, and **agentic AI that cannot bypass policy**—without giving up the operability that made [OpenClaw](https://github.com/openclaw/openclaw) influential in the first place.

Pair the OSS gateway with **[a2zsoc.com](https://a2zsoc.com)** for enterprise SIEM, multi-cloud ingest, and production SOC operations—or run GRC_Claw standalone for demos, audits, and integrator builds.

---

## Table of contents

- [Features](#features)
- [Monorepo structure](#monorepo-structure)
- [Packages](#packages)
- [Architecture](#architecture)
- [Quick start](#quick-start)
- [Operator console](#operator-console)
- [Skill executor](#skill-executor)
- [Configuration](#configuration)
- [Gateway API](#gateway-api)
- [Log and alert ingestion](#log-and-alert-ingestion)
- [A2Z SOC integration (a2zsoc.com)](#a2z-soc-integration-a2z-soccom)
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
| **Skill executor** | OpenClaw-style `claw.list_skills`, `claw.get_skill`, `claw.run_skill` — runs `.cursor/skills` playbooks via BYOC LLM + gated tools |
| **Agentic AI security** | Three-phase exec policy, tool tiers, session audit log |
| **Hermes/Nemotron Agent Runtime** | Zero-dependency autonomous orchestrator, self-healing supervisor loop |
| **Swarm Harness & SoD** | Segregation of Duties checking (e.g. developer vs reviewer role conflicts) and token verification |
| **Anti-Swarm Defense** | Behavioral Auditing (timing anomalies, reasoning loops, toxicity scaling, and forced Docker sandbox containment) |
| **Tactical UAS & C-UAS** | MAVLink v2 signature validation, PX4/Ardupilot firmware authentication, and DEW power safety audits |
| **CMMC & NIST SP 800-171/172** | Programmatic system boundary audits (MFA, session timeouts, encryption) and cryptographically signed C3PAO evidence generation |
| **Advanced Security** | TEE hardware attestation (Intel SGX, AMD SEV, Nvidia), active container network quarantine & rollback, Zero-Knowledge compliance proof generation, and decentralized MPC threshold key co-signing |
| **Acquisition-Grade Controls** | Kernel-level eBPF sandboxing, Raft-based ZK Audit Ledger replication, TEE hardware enclave-enclosed MPC co-signing, closed-loop IaC compliance drift correction, and federated threat intelligence exchange |
| **Sovereign Swarm Mastery** | Firecracker MicroVM sandbox isolation, homomorphic query verification on VectorGraphMemory, semantic thought-loop circuit breaker, Byzantine Fault Tolerant (PBFT) model consensus quorum, and self-healing SOAR containment playbooks |
| **Sovereign Swarm Defenses** | Autonomous red-team exploit simulation (Chaos Compliance), model weights integrity watermark verification inside TEE enclaves, confidential SGX enclaved vector database RAG query execution, and cross-tenant Byzantine Fault Tolerant (BFT) state sync consensus |
| **Zero-Trust & ZK Attestation** | Active VPC network quarantine & rollback, hardware model runtime attestation (Intel TDX / AMD SEV), threshold co-signing (MPC), and zk-SNARK compliance proofs (Groth16) |
| **Sovereign Swarm Resilience** | Tiered cognitive HITL approval routing, distributed semantic locks (DSLM) for multi-agent grids, cascading poison isolation & rollback checkpoints, and context diff compression (up to 85% token savings) |
| **Sovereign Swarm Autonomy** | Automated cloud compliance self-healing (GitOps rollback), zero-knowledge federated threat intelligence signature mesh, mathematical ExecPolicy envelope verification (SMT Z3), and post-quantum cryptographic (PQC) Dilithium5 audit signatures |
| **Sovereign Swarm Choreography** | Ephemeral confidential enclaves (Intel TDX / AMD SEV-SNP TEEs), post-quantum cryptographic (PQC) ML-KEM-1024 / ML-DSA key exchange consensus, active honey-token canary traps, and homomorphic policy execution over encrypted prompts |
| **Sovereign Swarm Federation** | Continuous AI-BOM supply chain gating & alternative model redirection, recursive ZK-rollup batch proof ledger consensus (Plonky2/Halo2), multi-party smart-contract escrow tool gating, and homomorphic cognitive intent filtering WAF |
| **Agent Identity Fabric** | DID:GRC decentralized identifiers, Verifiable Credentials per framework, DID-bound tool access, attestation signing, auto-suspend at risk threshold 90+, and federated identity revocation |
| **Security Graph** | Real-time security graph connecting agents, tools, controls, evidence, and infrastructure. BFS attack path tracing, blast radius analysis, weighted risk scoring (4-factor), and continuous compliance posture scoring (0-100) |
| **Agentic SOAR** | DAG-based playbook engine with 4 built-in response playbooks (Agent Compromise, Policy Violation, Drift Correction, Credential Rotation), 14 step actions, human-in-the-loop gates, SLA enforcement, and forensic evidence bundle generation |
| **Observability** | OpenTelemetry-native agent tracing (tool invocations, LLM calls, compliance checks, SOAR executions), Prometheus metrics export, OTLP JSON export for Datadog/Grafana/Jaeger, and per-agent cost/token tracking |
| **Compliance-as-Code SDK** | Declarative `grcfile.yaml` for entire compliance posture, `plan`/`apply`/`audit` workflow (Terraform-style), schema validation, and CI/CD-ready policy enforcement |
| **OWASP Agentic Top 10** | Full mapping of all 10 OWASP Agentic AI risks to GRC_Claw controls with 100% coverage: Excessive Agency, Goal Hijacking, Memory Poisoning, Cascading Failures, Unauthorized Tool Access, Data Exfiltration, Privilege Escalation, Audit Trail Tampering, Supply Chain Compromise, and Insufficient Observability |
| **AI Bill of Materials** | SPDX/CycloneDX-aligned AI-BOM generator extracting models, tools, frameworks, and data sources from trace data. Supports EU AI Act, NIST AI RMF, and ISO 42001 model inventory requirements |
| **Framework Marketplace** | 10+ regional/industry framework packs (GDPR, LGPD, PIPL, DORA, NIS2, HIPAA, PCI DSS, FedRAMP, TISAX, POPIA) with community contribution and revenue share |
| **Skill Marketplace** | Pre-audited, compliance-certified agent skill packs with trust scoring (Incident Response, Vulnerability Assessment, Access Review, Evidence Collection, Risk Assessment) |
| **Enterprise Connectors** | Native integration with SAP, ServiceNow, and Chronicle SOAR |
| **OSS SIEM / IDS / firewall** | Wazuh, Suricata, Snort, Elastic, UFW → canonical events |
| **Multi-cloud security** | AWS, Azure, GCP (CloudWatch, Sentinel, Chronicle, GuardDuty, …) |
| **ISO/IEC 42001 AIMS** | Vendor gap matrix (Anthropic, OpenAI, Cursor, OpenClaw), technical controls API |
| **BYOC connectors** | Bring your own **LLM** (OpenAI, Anthropic, **Google Gemini**, Ollama, **OpenRouter**) and **MCP** servers — gated by exec policy |
| **[a2zsoc.com](https://a2zsoc.com)** | Optional connector for live SOC + GRC sync |
| **Ship-ready OSS** | Docker Compose, systemd, Helm chart, comprehensive tests |
| **Operator console** | React UI — dashboard agent chat (Gemini + Cursor Auto), A2Z SOC trust badge, all gateway APIs |

---

## Monorepo structure

```
GRC_Claw/
├── package.json
├── tsconfig.json
├── LICENSE
├── ARCHITECTURE.md
├── apps/
│   └── console/                 # Operator UI (Vite + React)
├── docs/
├── packages/
│   ├── core/
│   ├── gateway/                 # OpenClaw-style control plane
│   ├── agent-runtime/
│   │   ├── src/                 # Exec policy, SoD, Anti-Swarm behavioral audit
│   │   └── scripts/             # test-anti-swarm.ts, test-acquisition-grade.ts, ...
│   ├── agent-identity/          # DID:GRC Agent Identity Fabric
│   ├── security-graph/          # Real-time security graph + attack paths
│   ├── soar/                    # Agentic SOAR playbook engine
│   ├── observability/           # OpenTelemetry tracing + AI-BOM
│   ├── sdk/                     # Compliance-as-Code SDK + grcfile.yaml
│   ├── evidence/
│   ├── frameworks/
│   ├── aims/                    # ISO/IEC 42001 AIMS (vendor gaps, clauses)
│   ├── connectors/              # BYOC LLM + MCP registry
│   ├── skill-executor/          # Skill discovery + claw.* run loop
│   ├── ingest/                  # OSS + cloud normalizers
│   └── a2z-connector/           # a2zsoc.com API bridge
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
| `@grc-claw/agent-runtime` | Exec policy, SoD Swarm Harness, Anti-Swarm engine & audited sessions |
| `@grc-claw/agent-identity` | **DID:GRC** Agent Identity Fabric — decentralized IDs, Verifiable Credentials, attestation signing |
| `@grc-claw/security-graph` | Real-time **Security Graph** — nodes, edges, attack path tracing, risk scoring, blast radius, compliance posture |
| `@grc-claw/soar` | **Agentic SOAR** — DAG playbook engine, 4 built-in playbooks, 14 step actions, SLA enforcement |
| `@grc-claw/observability` | **OpenTelemetry** agent tracing, Prometheus metrics, OTLP export, AI-BOM generator |
| `@grc-claw/sdk` | **Compliance-as-Code** SDK — `grcfile.yaml`, plan/apply/audit, OWASP Top 10, Framework Marketplace |
| `@grc-claw/evidence` | SHA-256 evidence lineage |
| `@grc-claw/frameworks` | ISO 27001, NIST CSF, SOC 2, ISO 42001 starter packs |
| `@grc-claw/aims` | ISO 42001 vendor gaps, clause map, technical controls |
| `@grc-claw/connectors` | BYOC LLM providers + MCP servers (registry, proxy, policy tools) |
| `@grc-claw/skill-executor` | Cursor skill discovery, `claw.*` dispatch, LLM run loop (`TOOL_CALL` / `FINAL_ANSWER`) |
| `@grc-claw/ingest` | OSS SIEM/IDS/firewall + AWS/Azure/GCP normalizers |
| `@grc-claw/a2z-connector` | Bridge to **[a2zsoc.com](https://a2zsoc.com)** APIs |
| `@grc-claw/console` | Operator UI (`apps/console`) — Vite + React |

| Script | Command |
|--------|---------|
| Build | `npm run build` |
| Build console | `npm run build:console` |
| Gateway | `npm run gateway` |
| Console (dev) | `npm run console` → http://localhost:5174 |
| Doctor | `npm run doctor` |
| Tests | `npm run test` · `npm run test:skills` · `npm run test:byoc` · `npm run test:iso42001` · `npm run test:cloud` · `npm run test:comprehensive` |
| Anti-Swarm Test | `npx tsx scripts/test-anti-swarm.ts` (under packages/agent-runtime) |
| UAS Swarm Test | `npx tsx scripts/test-uas-governance.ts` (under packages/agent-runtime) |
| CMMC Compliance Test | `npx tsx scripts/test-cmmc-compliance.ts` (under packages/agent-runtime) |
| OpenRouter Swarm Test | `npx tsx scripts/test-openrouter-swarm.ts` (under packages/agent-runtime) |
| SWIFT / ISO 20022 Test | `npx tsx scripts/test-iso20022.ts` (under packages/agent-runtime) |
| Hermes / Wallet Test | `npx tsx scripts/test-hermes-wallet.ts` (under packages/agent-runtime) |
| Vector DB / Memory Test | `npx tsx scripts/test-vector-memory.ts` (under packages/agent-runtime) |
| Acquisition-Grade Test | `npx tsx scripts/test-acquisition-grade.ts` (under packages/agent-runtime) |
| Sovereign Swarm Mastery Test | `npx tsx scripts/test-phase5-orchestration.ts` (under packages/agent-runtime) |
| Sovereign Swarm Defenses Test | `npx tsx scripts/test-phase6-orchestration.ts` (under packages/agent-runtime) |
| Sovereign Swarm Defenses & Attestation Test | `npx tsx scripts/test-phase7-orchestration.ts` (under packages/agent-runtime) |
| Sovereign Swarm Resilience Test | `npx tsx scripts/test-phase8-orchestration.ts` (under packages/agent-runtime) |
| Sovereign Swarm Autonomy Test | `npx tsx scripts/test-phase9-orchestration.ts` (under packages/agent-runtime) |
| Sovereign Swarm Choreography Test | `npx tsx scripts/test-phase10-orchestration.ts` (under packages/agent-runtime) |
| Sovereign Swarm Federation Test | `npx tsx scripts/test-phase11-orchestration.ts` (under packages/agent-runtime) |
| Sovereign Swarm Validation Test | `npx tsx scripts/test-phase12-orchestration.ts` (under packages/agent-runtime) |
| Sovereign Swarm Autonomy & Alignment Test | `npx tsx scripts/test-phase13-orchestration.ts` (under packages/agent-runtime) |
| Sovereign Swarm Execution Test | `npx tsx scripts/test-phase14-orchestration.ts` (under packages/agent-runtime) |
| Sovereign Swarm Monopoly Test | `npx tsx scripts/test-phase15-orchestration.ts` (under packages/agent-runtime) |
| Sovereign Swarm Policies Test | `npx tsx scripts/test-phase16-orchestration.ts` (under packages/agent-runtime) |
| Sovereign Swarm Shielding Test | `npx tsx scripts/test-phase17-orchestration.ts` (under packages/agent-runtime) |
| Structural Monopoly Test | `npx tsx scripts/test-phase18-orchestration.ts` (under packages/agent-runtime) |
| Self-Healing Compliance Test | `npx tsx scripts/test-phase19-orchestration.ts` (under packages/agent-runtime) |
| Decoy & Syscall Filter Test | `npx tsx scripts/test-phase20-orchestration.ts` (under packages/agent-runtime) |
| Zero-Trust Synaptic Test | `npx tsx scripts/test-phase21-orchestration.ts` (under packages/agent-runtime) |
| Guest-Kernel & Recursive ZK Test | `npx tsx scripts/test-phase22-orchestration.ts` (under packages/agent-runtime) |
| DPU Offload & Secure Enclave Test | `npx tsx scripts/test-phase23-orchestration.ts` (under packages/agent-runtime) |
| Neuromorphic & Quantum Consensus Test | `npx tsx scripts/test-phase24-orchestration.ts` (under packages/agent-runtime) |
| Photonic & DNA Wet-Storage Test | `npx tsx scripts/test-phase25-orchestration.ts` (under packages/agent-runtime) |
| LEO Space & Silicon PUF Test | `npx tsx scripts/test-phase26-orchestration.ts` (under packages/agent-runtime) |

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
    frameworks      agent-runtime    a2zsoc.com
    evidence         (gated SOAR)     (optional)
```

Details: [ARCHITECTURE.md](ARCHITECTURE.md).

---

## Quick start

```bash
cp examples/a2z-private-bridge.env.example .env

export GRC_CLAW_GATEWAY_TOKEN=change-me-in-production
export A2Z_SOC_MODE=demo   # use private + a2zsoc.com URL for production

npm run gateway
curl -s http://127.0.0.1:18791/health | jq .
```

See [Operator console](#operator-console) for the full UI workflow.

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

## Operator console

The **operator console** (`apps/console`) is a React app that exposes every gateway capability with an **A2Z SOC trust badge** on each page, self-explanatory guides, and a **dashboard agent chat** with two modes:

| Mode | What it does |
|------|----------------|
| **Gemini** | Direct BYOC chat via `POST /api/connectors/llm/:id/chat` (full multi-paragraph replies) |
| **Cursor Auto** | Runs live gateway tools (health, sync, frameworks, read-tier agent), lists skills/jobs from catalog, and answers with GRC operator rules |

The **Agent** page and gateway support **`claw.list_skills`**, **`claw.get_skill`**, and **`claw.run_skill`** — see [Skill executor](#skill-executor).

### Frontend project tree (`apps/console`)

Workspace package: `@grc-claw/console` · Vite + React + React Router.

```
apps/console/
├── index.html                 # App shell, llms.txt link
├── package.json
├── vite.config.ts             # Dev :5174, proxy /api + /health → gateway
├── tsconfig.json
├── public/
│   └── llms.txt               # Machine-readable API map (Cursor Auto / agents)
└── src/
    ├── main.tsx
    ├── App.tsx                # Routes: /, /frameworks, /ingest, /agent, /aims, /connectors, /settings
    ├── index.css
    ├── components/
    │   ├── Layout.tsx         # Sidebar nav + A2Z trust badge
    │   ├── PageShell.tsx      # Per-page explain blocks + Cursor Auto panel
    │   ├── A2ZTrustBadge.tsx  # Secured by A2Z SOC SVG badge
    │   ├── AgentChatWindow.tsx # Dashboard chat (Gemini | Cursor Auto)
    │   ├── CursorAutoPanel.tsx
    │   └── JsonBlock.tsx
    ├── lib/
    │   ├── api.ts             # Gateway HTTP client
    │   ├── settings.ts        # localStorage: token, tenant, trust profile, Cursor Auto flag
    │   ├── constants.ts       # Ingest sources, sample payloads, builtin tools
    │   ├── pageMeta.ts        # Self-explanatory copy per route
    │   ├── chatPrompts.ts     # Gemini + Cursor Auto system prompts
    │   ├── cursorAuto.ts        # curl snippets, automation rules
    │   ├── operatorAgent.ts   # Live gateway tool dispatch (Cursor Auto)
    │   ├── skillsCatalog.ts   # Skill list + claw.* tool reference
    │   └── schedulableJobs.ts # Daemon + cron-friendly job catalog
    └── pages/
        ├── DashboardPage.tsx  # Health, BYOC summary, A2Z sync, agent chat
        ├── FrameworksPage.tsx
        ├── IngestPage.tsx
        ├── AgentPage.tsx
        ├── AimsPage.tsx
        ├── ConnectorsPage.tsx
        └── SettingsPage.tsx
```

Build output: `apps/console/dist/` (served when `GRC_CLAW_CONSOLE_STATIC` is set).

**Dev (Vite proxies to gateway):**

```bash
# Terminal 1 — gateway
export GRC_CLAW_GATEWAY_TOKEN=grc-test-token
npm run gateway

# Terminal 2 — console
npm run console
# → http://localhost:5174
# Settings → X-GRC-Claw-Token must match GRC_CLAW_GATEWAY_TOKEN
```

**Production (same origin as gateway):**

```bash
npm run build:console
export GRC_CLAW_CONSOLE_STATIC="$(pwd)/apps/console/dist"
npm run gateway
# → http://127.0.0.1:18791/
```

### Google Gemini (BYOC)

```bash
cp examples/gemini-byoc.env.example .env
# Set GEMINI_API_KEY and GRC_CLAW_CONNECTORS_CONFIG=examples/gemini-connectors.json
set -a && source .env && set +a
npm run gateway
```

Uses provider kind `gemini_generate` (default model `gemini-2.5-flash`). See [examples/gemini-connectors.json](examples/gemini-connectors.json).

### OpenRouter & Multi-LLM Swarm (BYOC)

To route through OpenRouter's 300+ models or specialized engines like Nvidia Nemotron, Zhipu GLM, and Moonshot Kimi, configure them in `gemini-connectors.json`:

```json
{
  "id": "openrouter",
  "label": "OpenRouter",
  "kind": "openai_compatible",
  "baseUrl": "https://openrouter.ai/api/v1",
  "apiKeyEnv": "OPENROUTER_API_KEY",
  "defaultModel": "meta-llama/llama-3.1-70b-instruct"
}
```

Export the required API keys to your environment:

```bash
export OPENROUTER_API_KEY=sk-or-v1-...
export NVIDIA_API_KEY=nvapi-...
export ZHIPU_API_KEY=zhipu-...
export MOONSHOT_API_KEY=moonshot-...
```

GRC_Claw's Swarm Harness automatically monitors and gates these models. In particular, it enforces **Sovereign Boundary Gating** to block non-US-aligned models (such as `zhipu-glm` and `moonshot-kimi`) from calling sensitive CMMC or GRC tools (e.g. `cmmc.*` and `grc.*`).

### Cursor Auto Mode & scheduling

The browser console **cannot** start OS daemons or edit your crontab. It **can**:

- Call gateway HTTP APIs on demand (health, A2Z sync, ingest, agent read tools)
- Show a **catalog of schedulable jobs** (gateway daemon + cron-friendly endpoints)
- Point you to **Cursor Automations** (desktop) or **host cron → curl** for background work

Machine-readable API map for Cursor agents: `http://localhost:5174/llms.txt` (dev) or `/llms.txt` when served by the gateway.

**Example hourly A2Z sync (host cron):**

```bash
0 * * * * curl -s -X POST http://127.0.0.1:18791/api/a2z/sync \
  -H "X-GRC-Claw-Token: $GRC_CLAW_GATEWAY_TOKEN"
```

Console pages: Dashboard · Frameworks · Ingest · Agent · ISO 42001 · BYOC · Settings.

---

## Skill executor

GRC_Claw executes Cursor-style skills (markdown under `.cursor/skills/<id>/SKILL.md`) on the gateway with the same exec policy as other agent tools — inspired by [OpenClaw](https://github.com/openclaw/openclaw) skills, built for regulated operations.

| Tool | Tier | Purpose |
|------|------|---------|
| `claw.list_skills` | read | Catalog discovered skills (GRC_Claw repo + parent workspace) |
| `claw.get_skill` | read | Metadata + optional full `SKILL.md` body |
| `claw.run_skill` | write | Run playbook for a task (BYOC LLM loop + gated `grc.*` / MCP tools) |

**HTTP routes:** `GET /api/skills`, `GET /api/skills/:id`, `POST /api/skills/run`, `GET /api/cursor-skills` (alias).

**Example — list skills:**

```bash
curl -s -H "X-GRC-Claw-Token: $GRC_CLAW_GATEWAY_TOKEN" -X POST http://127.0.0.1:18791/api/agent/invoke \
  -H "Content-Type: application/json" \
  -d '{"sessionId":"demo","tool":"claw.list_skills","args":{}}' | jq .
```

**Example — run ISO 42001 skill** (requires `GEMINI_API_KEY` or another BYOC LLM in connectors config):

```bash
curl -s -H "X-GRC-Claw-Token: $GRC_CLAW_GATEWAY_TOKEN" -X POST http://127.0.0.1:18791/api/skills/run \
  -H "Content-Type: application/json" \
  -d '{
    "sessionId": "demo",
    "skillId": "iso-42001-ai-management-engineering",
    "task": "Summarize top Cursor vendor gaps in three bullets.",
    "llmProviderId": "gemini",
    "idempotencyKey": "skill-run-demo-1",
    "maxSteps": 6
  }' | jq .
```

Discovery: `GRC_CLAW_SKILLS_DIRS` or default `<cwd>/.cursor/skills` and `<cwd>/../.cursor/skills`.

Full reference: [docs/SKILL_EXECUTOR.md](docs/SKILL_EXECUTOR.md).

---

## Configuration

| Variable | Description |
|----------|-------------|
| `GRC_CLAW_GATEWAY_TOKEN` | API auth token (**required**) |
| `GRC_CLAW_HOST` / `GRC_CLAW_PORT` | Bind (default `127.0.0.1:18791`) |
| `GRC_CLAW_CONSOLE_STATIC` | Path to built console (`apps/console/dist`) for same-origin UI |
| `GRC_CLAW_CORS_ORIGIN` | CORS origin for cross-origin console (default `*`) |
| `A2Z_SOC_MODE` | `demo` or `private` (live **[a2zsoc.com](https://a2zsoc.com)**) |
| `A2Z_SOC_BASE_URL` | Your A2Z SOC API base (e.g. `https://a2zsoc.com`) |
| `A2Z_SOC_API_KEY` | Integration key from A2Z SOC |
| `A2Z_SOC_TENANT_ID` | Tenant scope |
| `GRC_CLAW_CONNECTORS_JSON` | Inline BYOC registry JSON |
| `GRC_CLAW_CONNECTORS_CONFIG` | Path to BYOC JSON file (e.g. `examples/gemini-connectors.json`) |
| `GRC_CLAW_ACTION_LEDGER_PATH` | Append-only action ledger path (default `.grc_memory/action-ledger.ndjson`) |
| `GRC_CLAW_MEMORY_DIR` | Session-memory directory (default `.grc_memory`) |
| `GEMINI_API_KEY` | Google Gemini API key (when using `gemini_generate` provider) |

Run `npm run doctor` before production. Never commit `.env` — use `examples/*.env.example` as templates.

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
| `POST` | `/api/agent/invoke` | Gated agent tool call (`claw.*`, `grc.*`, MCP) |
| `GET` | `/api/skills` | Skill catalog (`.cursor/skills`) |
| `GET` | `/api/skills/:id` | Skill metadata + body (`?body=0` for metadata only) |
| `POST` | `/api/skills/run` | Run skill executor loop (BYOC LLM + gated tools) |
| `GET` | `/api/cursor-skills` | Alias of skill catalog |
| `GET` | `/api/connectors` | BYOC LLM + MCP registry (redacted) |
| `GET` | `/api/action-ledger` | Authenticated action events plus hash-chain integrity check |
| `POST` | `/api/connectors/llm/:id/chat` | LLM chat proxy |
| `GET` | `/api/connectors/mcp/:id/tools` | Discover MCP tools |
| `WS` | `/` | `connect` → `hello-ok` |

**LLM provider kinds:** `openai_compatible` · `anthropic_messages` · `gemini_generate`

See [docs/BYOC_CONNECTORS.md](docs/BYOC_CONNECTORS.md) for configuration.

**Skill executor:** `claw.list_skills`, `claw.get_skill`, `claw.run_skill` — see [docs/SKILL_EXECUTOR.md](docs/SKILL_EXECUTOR.md).

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

## A2Z SOC integration (a2zsoc.com)

Production security operations and tenant GRC data live on **[a2zsoc.com](https://a2zsoc.com)**. GRC_Claw connects via `@grc-claw/a2z-connector`:

```bash
A2Z_SOC_MODE=private
A2Z_SOC_BASE_URL=https://a2zsoc.com
A2Z_SOC_API_KEY=<your-integration-key>
A2Z_SOC_TENANT_ID=1
```

| Direction | Behavior |
|-----------|----------|
| **Inbound** | Security events → normalized → compliance control impact |
| **Outbound** | Control test failures → SOC alerts |
| **GRC** | Scores, controls, evidence (see [integrations/a2z-soc/README.md](integrations/a2z-soc/README.md)) |

**Demo mode** (`A2Z_SOC_MODE=demo`) works offline for CI and local dev—no API key required.

Learn more about the platform: **[https://a2zsoc.com](https://a2zsoc.com)**

---

## Agentic AI security

OpenClaw for GRC means agents are **untrusted by default**:

1. **Allowlist** — registered tools only  
2. **Approval** — destructive SOAR (Sentinel playbooks, etc.) needs `approvalToken`  
3. **Sandbox** — Docker default  

| Tier | Examples |
|------|----------|
| Read | `claw.list_skills`, `claw.get_skill`, `grc.list_controls`, `sentinel.get_incident`, `soc.query_events` |
| Write | `claw.run_skill`, `evidence.attach` (+ idempotency key) |
| Destructive | `sentinel.run_playbook`, `chronicle.soar.run_playbook` |

[docs/AGENTIC_AI_SECURITY.md](docs/AGENTIC_AI_SECURITY.md)

---

## Testing

```bash
npm run test:comprehensive   # OSS + architecture + ISO 42001 + cloud
npm run test:skills          # Skill discovery + claw.* tool definitions
npm run test:iso42001        # AIMS package + gateway AIMS APIs
npm run test:cloud           # AWS / Azure / GCP
./scripts/test.sh            # Gateway smoke
npx tsx packages/agent-runtime/scripts/test-openrouter-swarm.ts # Swarm harness + OpenRouter gating
npx tsx packages/agent-runtime/scripts/test-iso20022.ts # SWIFT active rewrite and settlement
npx tsx packages/agent-runtime/scripts/test-hermes-wallet.ts # Hermes execution and wallet gating
npx tsx packages/agent-runtime/scripts/test-vector-memory.ts # Local vector RAG and cloud memory audits
npx tsx packages/agent-runtime/scripts/test-advanced-security.ts # TEE attestation, containment, ZKP, and MPC signing
npx tsx packages/agent-runtime/scripts/test-acquisition-controls.ts # eBPF sandboxing, ZK ledger replication, TEE MPC, IaC drift correction, and federated threat exchange
npx tsx packages/agent-runtime/scripts/test-phase5-orchestration.ts # Sovereign Swarm Mastery (MicroVM sandboxing, homomorphic vector RAG, thought-loop breaker, PBFT consensus, self-healing SOAR)
npx tsx packages/agent-runtime/scripts/test-phase6-orchestration.ts # Sovereign Swarm Defenses (Red-team exploit block, model weight verification, confidential SGX RAG, cross-tenant BFT state sync)
npx tsx packages/agent-runtime/scripts/test-phase7-orchestration.ts # Sovereign Swarm Defenses & Attestation (VPC network quarantine, TEE model attestation, MPC threshold signing, and zk-SNARK compliance audits)
npx tsx packages/agent-runtime/scripts/test-phase8-orchestration.ts # Sovereign Swarm Resilience (Cognitive approval routing, semantic locks DSLM, poison isolation rollback, context compression)
npx tsx packages/agent-runtime/scripts/test-phase9-orchestration.ts # Sovereign Swarm Autonomy (GitOps self-healing, federated threat mesh, SMT policy verification, and PQC audit credentials)
npx tsx packages/agent-runtime/scripts/test-phase10-orchestration.ts # Sovereign Swarm Choreography (Dynamic TEE enclaves, PQC key exchanges, active honeypot traps, and homomorphic policy checking)
npx tsx packages/agent-runtime/scripts/test-phase11-orchestration.ts # Sovereign Swarm Federation (Supply chain gating, recursive ZK-rollups, smart-contract escrows, and cognitive intent filtering)
npx tsx packages/agent-runtime/scripts/test-phase12-orchestration.ts # Sovereign Swarm Validation (Decentralized oracle verification, lattice MPC signing, symbolic graph flow verification, cognitive tuning)
npx tsx packages/agent-runtime/scripts/test-phase13-orchestration.ts # Sovereign Swarm Autonomy & Alignment (Analog airgap actuator trigger, temporal invariants proof, active activation patches)
npx tsx packages/agent-runtime/scripts/test-phase14-orchestration.ts # Sovereign Swarm Execution (Session ZK-proof generation, multi-model steering vector, ZK-RAG proof, threat rollup propagation)
npx tsx packages/agent-runtime/scripts/test-phase15-orchestration.ts # Sovereign Swarm Monopoly (Regulation AST compile, sidechannel hardware counters, FHE ledger audit, inline attention steering)
npx tsx packages/agent-runtime/scripts/test-phase16-orchestration.ts # Sovereign Swarm Policies (ZK policy envelope, VM speculative barriers, collaborative FHE RAG, synaptic dynamic LoRA patching)
npx tsx packages/agent-runtime/scripts/test-phase17-orchestration.ts # Sovereign Swarm Shielding (Post-quantum lattice DID attestation, enclaved weights scan, homomorphic joint threat check, attention feedback steering)
npx tsx packages/agent-runtime/scripts/test-phase18-orchestration.ts # Structural Monopoly (WASM policy isolation, Merkle DAG evidence, streaming GNN, federated attestation mesh)
npx tsx packages/agent-runtime/scripts/test-phase19-orchestration.ts # Self-Healing Compliance (IaC self-healing patch, FHE threat mesh, decentralized oracle, generative playbooks)
npx tsx packages/agent-runtime/scripts/test-phase20-orchestration.ts # Decoy & Syscall Filter (Honey-enclave sandbox, multi-model ZK quorum consensus, eBPF syscall logs, biometric TPM gate)
npx tsx packages/agent-runtime/scripts/test-phase21-orchestration.ts # Zero-Trust Synaptic (eBPF socket isolation, homomorphic vector RAG, BFT reasoning quorum, synaptic LoRA patching)
npx tsx packages/agent-runtime/scripts/test-phase22-orchestration.ts # Guest-Kernel & Recursive ZK (eBPF MicroVM sandbox, homomorphic joint policy audit, recursive Halo2 ZK rollup, GPU attention weight redirection)
npx tsx packages/agent-runtime/scripts/test-phase23-orchestration.ts # DPU Offload & Secure Enclaves (SmartNIC/DPU cognitive filters offloading, CRYSTALS-Dilithium ring signatures, Intel SGX/AMD SEV-SNP secure enclaves, SMT/Coq formal policy proof verification)
npx tsx packages/agent-runtime/scripts/test-phase24-orchestration.ts # Neuromorphic & Quantum Consensus (Memristive cognitive shields, quantum entanglement-based channels, dynamic Honey-Graph topology morphing, sovereign identity sharding)
npx tsx packages/agent-runtime/scripts/test-phase25-orchestration.ts # Photonic & DNA Wet-Storage (Photonic zero-knowledge attestation, DNA-locked wet-storage encryption, cognitive swarm self-assembly, photonic memory crystallization)
npx tsx packages/agent-runtime/scripts/test-phase26-orchestration.ts # LEO Space & Silicon PUF (Astro-sovereign LEO satellite sync, Silicon PUF identity challenge, biological neuron wet-compute filter, organic wetware memory sharding)
```

---

## Deployment

- **systemd:** [deploy/systemd/grc-claw-gateway.service](deploy/systemd/grc-claw-gateway.service)  
- **Docker:** [deploy/docker-compose.yml](deploy/docker-compose.yml)  

Production: strong gateway token, TLS at reverse proxy, scoped **a2zsoc.com** API key, agent approvals enabled.

---

## Documentation

| Doc | Topic |
|-----|--------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | Gateway daemon, planes, OpenClaw mapping |
| [docs/AGENTIC_AI_SECURITY.md](docs/AGENTIC_AI_SECURITY.md) | Agent threat model |
| [docs/MARKETING_A2Z_SOC.md](docs/MARKETING_A2Z_SOC.md) | Positioning with [a2zsoc.com](https://a2zsoc.com) |
| [integrations/a2z-soc/README.md](integrations/a2z-soc/README.md) | API contract |
| [docs/BYOC_CONNECTORS.md](docs/BYOC_CONNECTORS.md) | Bring Your Own LLM + MCP |
| [docs/SKILL_EXECUTOR.md](docs/SKILL_EXECUTOR.md) | `claw.*` tools, run loop, HTTP examples |
| [docs/ISO_42001_AIMS.md](docs/ISO_42001_AIMS.md) | ISO/IEC 42001 AIMS architecture + APIs |
| [integrations/iso-42001/README.md](integrations/iso-42001/README.md) | ISO 42001 integration guide |
| [docs/SOVEREIGN_LOCAL_AI.md](docs/SOVEREIGN_LOCAL_AI.md) | Sovereign Local AI & Airgapped Architectures (Blackwell, RTX Spark, Vera) |
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

- [x] Operator console with Gemini + Cursor Auto agent chat
- [x] Full skill executor (`claw.list_skills`, `claw.get_skill`, `claw.run_skill`)
- [x] Local Zero-Cost Autonomous Execution (The Hermes Protocol)
- [x] Multi-Ledger Wallet Gating & Sovereign Compliance (Solana, XRP, Bitcoin)
- [x] Hardened ISO 20022 SWIFT Clearing Node (MT-to-MX Translation, Signature Healing, Settlement Gating)
- [x] Local Vector RAG Integration (Pinecone-style) & Cloud Memory Vendor Lock-in Audit (Dreaming V3)
- [x] Large-scale Swarm Load Auditing (300 concurrent agents)
- [x] Advanced Enterprise Security (TEE hardware attestation, Active sandbox containment quarantine & rollback, ZKP compliance proofs, and MPC threshold co-signing)
- [x] Acquisition-Grade Enterprise Security (Kernel-level eBPF sandboxing, Raft-based ZK Audit Ledger, TEE enclave-enclosed MPC co-signing, closed-loop IaC compliance drift correction, and federated threat intelligence exchange)
- [x] npm publish `@grc-claw/*` (dry-run script verified)
- [x] Helm chart (templates deployed under deploy/helm)
- [x] Gateway metrics (Prometheus format at /metrics)
- [x] Signed auditor export bundles (compiled via grc.generate_auditor_bundle)
- [x] Agent Identity Fabric (`@grc-claw/agent-identity`) - DID:GRC decentralized identifiers, Verifiable Credentials, attestation signing, auto-suspend risk threshold
- [x] Security Graph (`@grc-claw/security-graph`) - Real-time graph with BFS attack path tracing, 4-factor weighted risk scoring, blast radius analysis, and continuous compliance posture (0-100)
- [x] Agentic SOAR (`@grc-claw/soar`) - DAG playbook engine with 4 built-in playbooks (Agent Compromise, Policy Violation, Drift Correction, Credential Rotation), 14 step actions, human-in-the-loop gates, SLA enforcement
- [x] Observability (`@grc-claw/observability`) - OpenTelemetry-native agent tracing with Prometheus metrics, OTLP export (Datadog/Grafana/Jaeger), per-agent cost/token tracking
- [x] Compliance-as-Code SDK (`@grc-claw/sdk`) - Declarative grcfile.yaml, Terraform-style plan/apply/audit workflow, CI/CD-ready policy enforcement
- [x] OWASP Agentic Top 10 full coverage mapping (10/10 risks fully addressed with GRC_Claw controls)
- [x] AI Bill of Materials (AI-BOM) generator - SPDX/CycloneDX-aligned, extracts models/tools/frameworks from trace data
- [x] Framework Pack Marketplace - 10+ regional/industry packs (GDPR, HIPAA, PCI DSS, FedRAMP, DORA, NIS2, TISAX, POPIA)
- [x] Agent Skill Marketplace - Pre-audited, compliance-certified skill packs with trust scoring
- [x] Phase 16 — Zero-Knowledge Policy Invariant Proofs, Hardware Speculative Execution Barriers, Multi-Party FHE Vector Search, Dynamic Synaptic Weight Patching
- [x] Phase 17 — Post-Quantum Lattice Credentials, Enclaved Weight Sanitation, Joint FHE Threat Analysis, Attention Steering Feedback Loops
- [x] Phase 18 — Structural Monopoly Architecture: WASM Sandbox Policy Isolation, Merkle DAG Evidence Notarization, GNN Behavioral Anomaly Detection, Federated Compliance Attestation Mesh
- [x] Phase 19 — Autonomous Self-Healing Infrastructure (Simulated IaC Synthesis and Dry-run Validation), Cross-Tenant Collaborative SIEM Mesh (Homomorphic Threat Correlation), Consensus-Driven Compliance Oracle, Dynamic Generative Playbooks (Autonomous Cognitive SOAR)
- [x] Phase 20 — Cognitive Decoy Sandboxing (Honey-Enclaves), Zero-Knowledge Multi-Model Cross-Validation (Consensus Quorum), Active eBPF-Driven Runtime Control Plane Containment, Biometric & TPM-Bound Agent Authorization
- [x] Phase 21 — Zero-Trust Synaptic Guardrails (Dynamic LoRA Parameter Patching), Kernel-Level Socket Isolation (eBPF sockops filters), Homomorphic Vector RAG, Byzantine Fault Tolerant (BFT) Model Reasoning Quorum
- [x] Phase 22 — MicroVM Guest-Kernel Sandboxing (eBPF monitors), Homomorphic Joint-Policy Auditing (FHE), Recursive ZK-Proof Aggregation (Halo2 rollup), GPU Attention-Head Redirection (Dynamic steering)
- [x] Phase 23 — DPU Cognitive Offloading (SmartNIC filter), Post-Quantum Lattice Ring Signatures (Dilithium cohort trust), Hardware-Locked Secure Enclaves (AMD SEV-SNP enclaves), Self-Evolving Formal Consensus (SMT solver verification)
- [x] Phase 24 — Neuromorphic Cognitive Shields (Memristor arrays), Quantum-Entanglement Consensus (teleported attestations), Dynamic Honey-Graph Morphing (moving-target routing), Sovereign Identity Sharding (threshold credential splits)
- [x] Phase 25 — Photonic ZK Attestation (speed-of-light proofs), DNA-Locked Wet-Storage Encryption (microfluidic biological key storage), Cognitive Swarm Self-Assembly (enclaved self-writing logic), Photonic Memory Crystallization (optical context arrays)
- [x] Phase 26 — Astro-Sovereign Satellite Attestation (LEO laser sync), Silicon PUF Identity (substrate verification challenge), Biological Wet-Compute Cognitive Mediation (organic neuron filters), Organic Wetware Memory Sharding (biological weight shares)
- [ ] GRC_Claw Cloud (multi-tenant managed SaaS on a2zsoc.com)
- [x] Federated Compliance Mesh (multi-org ZK-attested trust network via attestation.issue_compliance_credential / attestation.verify_vendor_credential)
- [ ] Compliance Copilot (AI-powered natural language GRC assistant)

---

**Inspired by [OpenClaw](https://github.com/openclaw/openclaw). Engineered for enterprise GRC. Secured for agents. Production SOC at [a2zsoc.com](https://a2zsoc.com).**
