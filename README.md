# GRC_Claw

### The OSS chassis for ISO 42001-compliant agentic AI — Swarm Harness, Anti-Swarm WAF, MAVLink & UAS compliance, a2zsoc.com bridge

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Node](https://img.shields.io/badge/node-%3E%3D20-brightgreen)](package.json)
[![GitHub](https://img.shields.io/badge/GitHub-AAH20%2FGRC__Claw-181717?logo=github)](https://github.com/AAH20/GRC_Claw)
[![OpenClaw for GRC](https://img.shields.io/badge/OpenClaw-for%20GRC-8b5cf6)](ARCHITECTURE.md)
[![Agentic AI Security](https://img.shields.io/badge/Agentic%20AI-Secured-green)](docs/AGENTIC_AI_SECURITY.md)
[![A2Z SOC](https://img.shields.io/badge/A2Z%20SOC-a2zsoc.com-red)](https://a2zsoc.com)

**GRC_Claw** is a production-grade, open-source GRC (Governance, Risk & Compliance) platform with **67 packages**, **132 agent tools** (124 real implementations), **110+ HTTP endpoints**, **167 integration connectors**, **39 compliance framework packs**, **16 CLI commands**, and **PostgreSQL persistence**. It is the only open-source platform that combines agentic AI governance, compliance automation, risk quantification, and continuous monitoring in a single monorepo.

Built on the [OpenClaw](https://github.com/openclaw/openclaw) daemon philosophy, GRC_Claw extends it into a full-stack GRC engine with RBAC multi-tenancy, Terraform provider for compliance-as-code, and optional integration with **[a2zsoc.com](https://a2zsoc.com)** for enterprise SOC operations.

| | [OpenClaw](https://github.com/openclaw/openclaw) | **GRC_Claw** (this repo) |
|---|----------|----------|
| **Primary use** | Personal assistant & chat channels | **Enterprise GRC + SOC automation** |
| **Control plane** | Gateway daemon (WebSocket) | Gateway daemon (**WS + HTTP APIs**) |
| **Agent governance** | Tools + skills (operator-defined) | **Mandatory exec policy** + **`claw.*` skill executor** |
| **Compliance** | General-purpose | **39 framework packs** (ISO 27001, NIST CSF, SOC 2, ISO 42001, GDPR, HIPAA, PCI DSS, FedRAMP, CMMC, DORA, NIS2, EU AI Act, etc.) |
| **Evidence** | Workspace files | **SHA-256 lineage** + PostgreSQL persistence + SOC attach API |
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
- [CLI](#cli)
- [Configuration](#configuration)
- [Gateway API](#gateway-api)
- [Integration Marketplace](#integration-marketplace)
- [RBAC & Multi-Tenancy](#rbac--multi-tenancy)
- [Terraform Provider](#terraform-provider)
- [Log and alert ingestion](#log-and-alert-ingestion)
- [A2Z SOC integration](#a2z-soc-integration)
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
| **39 Framework Packs** | ISO 27001, NIST CSF, SOC 2, ISO 42001, EU AI Act, DORA, HIPAA, PCI DSS, GDPR, FedRAMP, CMMC, CIS Controls, COBIT, CSA CCM, ISO 27701, ISO 27017, ISO 27018, SOC 1, NIS2, CCPA, LGPD, PIPEDA, APRA CPS 234, MAS TRM, Singapore PDPA, Japan APPI, India DPDP, China PIPL, Saudi PDPL, TISAX, SWIFT CSP, FFIEC, SOX, ENS High |
| **156 Integration Connectors** | GitHub, GitLab, AWS (IAM/S3/CloudTrail/GuardDuty/Lambda/RDS/KMS), Azure (AD/Sentinel/Policy/DevOps), GCP (IAM/SCC/Config/Firestore/BigQuery), Okta, Auth0, Jira, Slack, PagerDuty, Snowflake, Datadog, CrowdStrike, Qualys, Snyk, Terraform Cloud, Docker Hub, Kubernetes, Salesforce, HubSpot, BambooHR, Workday, ServiceNow, Splunk, Confluence, Notion, Box, Dropbox, Google Workspace, Microsoft 365, and 100+ more |
| **Risk Quantification** | Monte Carlo simulation (MersenneTwister PRNG, 5 distributions), FAIR risk calculator, risk register with heatmaps |
| **Compliance Autopilot** | Continuous monitoring, gap detection, remediation, verification cycles with audit trail |
| **Drift Detection** | Baseline capture, compliance drift detection, alert history, severity scoring |
| **Agent Identity (DID:GRC)** | Decentralized identifier creation, credential issuance/verification, attestation signing |
| **Agent Trust Scoring** | Behavioral signal analysis, dimensional trust profiles, risk level classification |
| **Security Graph** | Real-time graph with BFS attack path tracing, blast radius calculation, weighted risk scoring |
| **SOAR Playbook Engine** | DAG-based playbook engine, 4 built-in playbooks, 14 step actions, SLA enforcement |
| **Observability (OpenTelemetry)** | Distributed tracing, Prometheus metrics, OTLP export for Datadog/Grafana/Jaeger |
| **Compliance-as-Code SDK** | Declarative `grcfile.yaml`, plan/apply/audit workflow, CI/CD-ready |
| **OWASP Agentic Top 10** | Full mapping of all 10 OWASP Agentic AI risks with 100% coverage |
| **AI Bill of Materials** | SPDX/CycloneDX-aligned AI-BOM generator for EU AI Act Art. 53 |
| **156 Integration Connectors** | GitHub, GitLab, AWS, Azure, GCP, Okta, Jira, CrowdStrike, Wiz, Prisma, and 100+ more |
| **Terraform Provider** | IaC for GRC resources: grc_framework, grc_control, grc_evidence, grc_risk, grc_agent_policy |
| **RBAC Multi-Tenancy** | JWT auth, 5 roles, 90 permissions, tenant isolation, scope validation |
| **Policy Management Hub** | Policy lifecycle (create → approve → publish → attest), 52 templates |
| **Vendor Risk Management** | Vendor CRUD, risk scoring, questionnaires, monitoring, alerts |
| **Employee Lifecycle** | Onboarding/offboarding, compliance checks, access reviews |
| **Compliance Task Engine** | Task lifecycle, bulk-from-findings, analytics |
| **Evidence Automation** | Scheduled collection, gap detection, summary reporting |
| **Federated Compliance Mesh** | Multi-org ZK-attested compliance sharing |
| **AI Supply Chain Sovereignty** | Model provenance, TEE/ZK attestation, federated consensus |
| **ZK Compliance Proofs** | Cryptographic compliance verification |
| **Board Reporting** | Automated executive dashboards |
| **ChatGRC** | GRC-aware chatbot with intent classification |
| **Agent Discovery** | Codebase scanning for agent patterns |
| **OpenAPI Generator** | Auto-generated API specifications |
| **Evidence Collector Engine** | System-level evidence (MFA, encryption, patches) |
| **Browser Evidence** | Automated browser-based evidence collection |
| **Auto Evidence** | Cloud provider evidence collection |
| **CLI Tool** | 16 commands: scan, plan, apply, audit, report, init, iac-scan, pqc-scan, ai-bom, doctor, drift, diff, status, frameworks, version, sovereign init |
| **Operator Console** | React UI with dashboard, agent chat, compliance gauge, risk heatmap |
| **WebSocket Real-time** | SOC events + compliance updates broadcasting |
| **PostgreSQL Persistence** | Full database layer for evidence, audit, entities, identity |
| **120+ Agent Tools** | Policy-gated tool dispatch with exec policy enforcement |
| **110+ HTTP Endpoints** | Complete REST API for all GRC operations |
| **A2Z SOC Integration** | Bidirectional sync via a2zsoc.com bridge |

---

## Monorepo structure

```
GRC_Claw/
├── package.json              # 66 workspaces
├── tsconfig.json             # TypeScript project references
├── LICENSE                   # MIT
├── ARCHITECTURE.md
├── apps/
│   └── console/              # Operator UI (Vite + React)
├── docs/
├── packages/
│   ├── core/                 # Canonical events, GRCEngineFacade
│   ├── gateway/              # OpenClaw for GRC — HTTP/WS gateway daemon
│   ├── agent-runtime/        # Exec policy, SoD, Anti-Swarm engine
│   ├── agent-identity/       # DID:GRC Agent Identity Fabric
│   ├── security-graph/       # Real-time security graph + attack paths
│   ├── soar/                 # Agentic SOAR playbook engine
│   ├── observability/        # OpenTelemetry tracing + AI-BOM
│   ├── sdk/                  # Compliance-as-Code SDK + grcfile.yaml
│   ├── evidence/             # SHA-256 evidence lineage + PostgreSQL
│   ├── frameworks/           # 39 compliance framework packs
│   ├── aims/                 # ISO/IEC 42001 AIMS
│   ├── connectors/           # BYOC LLM + MCP registry
│   ├── skill-executor/       # Skill discovery + claw.* dispatch
│   ├── ingest/               # OSS + cloud normalizers (15+ sources)
│   ├── persistence/          # PostgreSQL persistence layer
│   ├── agent-audit-trail/    # Blockchain-style hash chain audit
│   ├── agent-builder/        # Custom agent definitions
│   ├── agent-discovery/      # Agent pattern scanner
│   ├── agent-trust-score/    # Trust scoring engine
│   ├── accm/                 # Automated Compliance-as-Code Management
│   ├── compliance-autopilot/ # Continuous monitoring + remediation
│   ├── compliance-task-engine/ # Task lifecycle management
│   ├── drift-detector/       # Compliance drift detection
│   ├── evidence-collector/   # System-level evidence collection
│   ├── evidence-automation-engine/ # Scheduled evidence collection
│   ├── risk-quantification/  # Monte Carlo + FAIR risk calculation
│   ├── entity-management/    # Multi-entity compliance rollup
│   ├── integration-marketplace/ # 156 SaaS/cloud connectors
│   ├── policy-management-hub/ # Policy lifecycle + approval workflows
│   ├── vendor-risk-management/ # Vendor risk scoring + monitoring
│   ├── employee-lifecycle/   # Onboarding/offboarding workflows
│   ├── chat-grc/             # GRC-aware chatbot
│   ├── framework-crosswalk/  # Multi-framework control mapping
│   ├── browser-evidence/     # Automated browser evidence collection
│   ├── device-agent/         # Endpoint compliance agent
│   ├── openapi-generator/    # Auto-generated API specs
│   ├── rbac-multi-tenant/    # RBAC + multi-tenancy
│   ├── terraform-provider/   # IaC for GRC resources
│   ├── cli/                  # CLI tool (16 commands)
│   ├── mcp-server/           # MCP protocol server
│   ├── zk-compliance/        # Zero-knowledge compliance proofs
│   ├── ai-supply-chain/      # AI supply chain sovereignty
│   ├── ai-threat-detection/  # Anomaly detection
│   ├── compliance-copilot/   # Compliance assistant
│   ├── compliance-orchestrator/ # Framework compilation
│   ├── continuous-compliance/ # Continuous monitoring
│   ├── dev-compliance/       # GitHub PR review + CI/CD gates
│   ├── federated-compliance-mesh/ # Multi-org compliance sharing
│   ├── incident-response/    # Incident management
│   ├── questionnaire-automation/ # Security questionnaire auto-fill
│   ├── regulatory-intelligence/ # Regulation change monitoring
│   ├── third-party-risk/     # Third-party risk assessment
│   ├── trust-center/         # Public trust pages
│   ├── trust-marketplace/    # Trust marketplace
│   ├── business-impact/      # Business impact analysis
│   ├── auto-evidence/        # Automated evidence collection
│   ├── board-reporting/      # Executive dashboards
│   ├── grc-engineering/      # GRC engineering utilities
│   ├── registry/             # Package registry
│   ├── sdk-client/           # HTTP SDK client
│   ├── observability/        # OpenTelemetry tracing
│   ├── a2z-connector/        # a2zsoc.com API bridge
│   ├── oscal/                # OSCAL support
│   ├── vscode-extension/     # VS Code extension
│   └── cli/                  # CLI tool
├── integrations/
├── deploy/
├── examples/
└── scripts/
```

---

## Packages

| Package | Description |
|---------|-------------|
| `@grc-claw/core` | Canonical events, `GRCEngineFacade` |
| `@grc-claw/gateway` | **OpenClaw for GRC** — HTTP/WS gateway daemon |
| `@grc-claw/agent-runtime` | Exec policy, SoD, Anti-Swarm engine |
| `@grc-claw/agent-identity` | **DID:GRC** Agent Identity Fabric |
| `@grc-claw/security-graph` | Real-time **Security Graph** |
| `@grc-claw/soar` | **Agentic SOAR** playbook engine |
| `@grc-claw/observability` | **OpenTelemetry** tracing + AI-BOM |
| `@grc-claw/sdk` | **Compliance-as-Code** SDK |
| `@grc-claw/evidence` | SHA-256 evidence lineage + PostgreSQL |
| `@grc-claw/frameworks` | 39 compliance framework packs |
| `@grc-claw/aims` | ISO 42001 vendor gaps, clause map |
| `@grc-claw/connectors` | BYOC LLM + MCP registry |
| `@grc-claw/skill-executor` | Skill discovery + `claw.*` dispatch |
| `@grc-claw/ingest` | OSS SIEM/IDS/firewall + cloud normalizers |
| `@grc-claw/persistence` | PostgreSQL persistence layer |
| `@grc-claw/risk-quantification` | Monte Carlo + FAIR risk calculation |
| `@grc-claw/entity-management` | Multi-entity compliance rollup |
| `@grc-claw/integration-marketplace` | 156 SaaS/cloud connectors |
| `@grc-claw/policy-management-hub` | Policy lifecycle + approval workflows |
| `@grc-claw/vendor-risk-management` | Vendor risk scoring + monitoring |
| `@grc-claw/employee-lifecycle` | Onboarding/offboarding workflows |
| `@grc-claw/compliance-task-engine` | Task lifecycle management |
| `@grc-claw/evidence-automation-engine` | Scheduled evidence collection |
| `@grc-claw/chat-grc` | GRC-aware chatbot |
| `@grc-claw/framework-crosswalk` | Multi-framework control mapping |
| `@grc-claw/browser-evidence` | Automated browser evidence collection |
| `@grc-claw/device-agent` | Endpoint compliance agent |
| `@grc-claw/openapi-generator` | Auto-generated API specs |
| `@grc-claw/rbac-multi-tenant` | RBAC + multi-tenancy |
| `@grc-claw/terraform-provider` | IaC for GRC resources |
| `@grc-claw/cli` | CLI tool (16 commands) |
| `@grc-claw/mcp-server` | MCP protocol server |
| `@grc-claw/compliance-autopilot` | Continuous monitoring + remediation |
| `@grc-claw/drift-detector` | Compliance drift detection |
| `@grc-claw/evidence-collector` | System-level evidence collection |
| `@grc-claw/agent-audit-trail` | Blockchain-style hash chain audit |
| `@grc-claw/agent-builder` | Custom agent definitions |
| `@grc-claw/agent-discovery` | Agent pattern scanner |
| `@grc-claw/zk-compliance` | Zero-knowledge compliance proofs |
| `@grc-claw/ai-supply-chain` | AI supply chain sovereignty |
| `@grc-claw/ai-threat-detection` | Anomaly detection |
| `@grc-claw/compliance-copilot` | Compliance assistant |
| `@grc-claw/compliance-orchestrator` | Framework compilation |
| `@grc-claw/continuous-compliance` | Continuous monitoring |
| `@grc-claw/dev-compliance` | GitHub PR review + CI/CD gates |
| `@grc-claw/federated-compliance-mesh` | Multi-org compliance sharing |
| `@grc-claw/incident-response` | Incident management |
| `@grc-claw/questionnaire-automation` | Security questionnaire auto-fill |
| `@grc-claw/regulatory-intelligence` | Regulation change monitoring |
| `@grc-claw/third-party-risk` | Third-party risk assessment |
| `@grc-claw/trust-center` | Public trust pages |
| `@grc-claw/trust-marketplace` | Trust marketplace |
| `@grc-claw/business-impact` | Business impact analysis |
| `@grc-claw/auto-evidence` | Automated evidence collection |
| `@grc-claw/board-reporting` | Executive dashboards |
| `@grc-claw/grc-engineering` | GRC engineering utilities |
| `@grc-claw/registry` | Package registry |
| `@grc-claw/sdk-client` | HTTP SDK client |
| `@grc-claw/observability` | OpenTelemetry tracing |
| `@grc-claw/a2z-connector` | a2zsoc.com API bridge |
| `@grc-claw/oscal` | OSCAL support |
| `@grc-claw/vscode-extension` | VS Code extension |
| `@grc-claw/console` | Operator UI |

---

## Architecture

**Architecture first, daemons second** — informed by [OpenClaw](https://github.com/openclaw/openclaw), extended for GRC and security operations.

| Plane | Components | Role |
|-------|------------|------|
| **Control** | `gateway`, `agent-runtime` | Auth, WS `connect`, routing, agent policy, RBAC |
| **Evidence** | `evidence`, `frameworks` | Controls, hashed artifacts, 39 framework packs |
| **Data** | `ingest`, `a2z-connector` | Alerts → canonical events → compliance impact |
| **Risk** | `risk-quantification`, `drift-detector` | Monte Carlo, FAIR, drift detection |
| **Automation** | `compliance-autopilot`, `soar`, `accm` | Continuous monitoring, SOAR playbooks, auto-remediation |
| **Identity** | `agent-identity`, `rbac-multi-tenant` | DID:GRC, JWT auth, tenant isolation |
| **Integration** | `integration-marketplace`, `terraform-provider` | 156 connectors, IaC for GRC |

```text
  Wazuh · Suricata · Sentinel · GuardDuty · Chronicle · 156 Connectors
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
    risk-quant       compliance-      integration-
    drift-detector   autopilot        marketplace
```

Details: [ARCHITECTURE.md](ARCHITECTURE.md).

---

## Quick start

```bash
git clone https://github.com/AAH20/GRC_Claw.git && cd GRC_Claw
npm install && npm run build

export GRC_CLAW_GATEWAY_TOKEN=change-me-in-production
export DATABASE_URL=postgresql://user:pass@localhost:5432/grc_claw
npm run gateway
curl -s http://127.0.0.1:18791/health | jq .
```

**Docker:**

```bash
docker compose -f deploy/docker-compose.yml up --build
```

---

## Operator console

The **operator console** (`apps/console`) is a React app with:
- Dashboard with compliance gauge, risk heatmap, time series charts
- Framework management (39 frameworks)
- Agent chat (Gemini + Cursor Auto modes)
- Settings and configuration

```bash
npm run console  # → http://localhost:5174
```

---

## CLI

The CLI provides 16 commands for compliance automation:

```bash
grc init                    # Scaffold grcfile.yaml + GitHub Actions
grc scan .                  # Codebase compliance scan (12 rules)
grc plan                    # Generate compliance plan
grc apply                   # Apply compliance plan
grc audit                   # Full compliance audit
grc status                  # Current compliance posture
grc drift                   # Detect compliance drift
grc report                  # Generate evidence report
grc diff                    # Compliance delta between git refs
grc doctor                  # Environment checks + --fix
grc iac-scan .              # Terraform/K8s compliance (8 rules)
grc pqc-scan .              # Post-quantum crypto migration (6 rules)
grc ai-bom generate         # AI Bill of Materials (EU AI Act)
grc ai-bom publish          # Publish AI-BOM
grc frameworks list         # List framework packs
grc version                 # Print version
```

---

## Configuration

| Variable | Description |
|----------|-------------|
| `GRC_CLAW_GATEWAY_TOKEN` | API auth token (**required**) |
| `GRC_CLAW_HOST` / `GRC_CLAW_PORT` | Bind (default `127.0.0.1:18791`) |
| `DATABASE_URL` | PostgreSQL connection string |
| `GRC_CLAW_CONSOLE_STATIC` | Path to built console |
| `GRC_CLAW_CORS_ORIGIN` | CORS origin (default `*`) |
| `GRC_CLAW_JWT_SECRET` | JWT signing secret for RBAC |
| `A2Z_SOC_MODE` | `demo` or `private` |
| `A2Z_SOC_BASE_URL` | A2Z SOC API base |
| `A2Z_SOC_API_KEY` | Integration key |
| `GRC_CLAW_CONNECTORS_CONFIG` | Path to BYOC JSON file |
| `GEMINI_API_KEY` | Google Gemini API key |
| `JIRA_URL` / `JIRA_TOKEN` | Jira integration |
| `SLACK_WEBHOOK_URL` | Slack integration |

Run `npm run doctor` before production.

---

## Gateway API

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Status, persistence mode, connector summary |
| `GET` | `/metrics` | Prometheus metrics (real compliance score) |
| `POST` | `/api/agent/invoke` | Gated agent tool call |
| `GET` | `/api/frameworks` | 39 framework packs |
| `POST` | `/api/ingest/normalize` | Alert → canonical event |
| `POST` | `/api/risk/monte-carlo` | Monte Carlo simulation |
| `POST` | `/api/risk/fair` | FAIR risk analysis |
| `GET` | `/api/risk/register` | Risk register + portfolio |
| `POST` | `/api/entities` | Entity CRUD |
| `GET` | `/api/entities` | List entities |
| `POST` | `/api/accm/detect-gaps` | Compliance gap detection |
| `POST` | `/api/accm/full-cycle` | Full remediation cycle |
| `GET` | `/api/integrations` | 156 connectors |
| `POST` | `/api/policies/create` | Create policy |
| `GET` | `/api/vendor-risk/vendors` | Vendor risk management |
| `GET` | `/api/employees` | Employee lifecycle |
| `POST` | `/api/tasks` | Compliance tasks |
| `POST` | `/api/evidence-automation/schedule` | Evidence automation |
| `POST` | `/api/auth/login` | RBAC authentication |
| `POST` | `/api/terraform/plan` | Terraform compliance plan |
| `POST` | `/api/accm/full-cycle` | Auto-compliance cycle |
| `GET` | `/api/dashboard/realtime` | Real-time compliance |
| `GET` | `/api/openapi.json` | OpenAPI spec |
| `WS` | `/ws` | SOC events + compliance updates |

See [docs/BYOC_CONNECTORS.md](docs/BYOC_CONNECTORS.md) for configuration.

---

## Integration Marketplace

**156 connectors** across 15+ categories:

| Category | Examples |
|----------|----------|
| **Cloud Security** | AWS (IAM/S3/CloudTrail/GuardDuty/Lambda/RDS/KMS), Azure (AD/Sentinel/Policy/DevOps), GCP (IAM/SCC/Config/Firestore/BigQuery) |
| **Security** | CrowdStrike, SentinelOne, Qualys, Snyk, Prisma Cloud, Wiz, PaloAlto, CheckPoint, Fortinet, Zscaler |
| **DevOps** | GitHub, GitLab, Jenkins, Travis, ArgoCD, Helm, Terraform Cloud, Docker Hub, Kubernetes |
| **Identity** | Okta, Auth0, PingFederate, ForgeRock, CyberArk, SailPoint |
| **Data** | Snowflake, Databricks, Tableau, PowerBI, MongoDB, Kafka, Redis |
| **HR** | Workday, SAP SuccessFactors, ADP, BambooHR |
| **Finance** | NetSuite, QuickBooks, Xero, Stripe, DocuSign |
| **Communication** | Slack, Zoom, Teams, Discord, PagerDuty |
| **Plus 60+ more** | ServiceNow, Splunk, Confluence, Notion, Box, Dropbox, and more |

---

## RBAC & Multi-Tenancy

**Built-in RBAC with multi-tenant isolation:**

- 5 roles: `admin`, `compliance_officer`, `auditor`, `viewer`, `custom`
- 90 permission combinations (15 resources × 6 actions)
- 3 scope levels: `global`, `entity`, `department`
- JWT authentication with role claims
- Tenant-scoped data isolation
- Permission audit logging

```bash
# Login
curl -X POST /api/auth/login -d '{"email":"user@co.com","password":"pass"}'

# Use JWT
curl -H "Authorization: Bearer <jwt>" /api/frameworks
```

---

## Terraform Provider

**Compliance-as-Code with Terraform:**

```hcl
resource "grc_framework" "soc2" {
  name     = "SOC 2 Type II"
  controls = ["CC6.1", "CC7.2", "CC8.1"]
}

resource "grc_control" "mfa" {
  framework_id = grc_framework.soc2.id
  code         = "CC6.1"
  name         = "Multi-Factor Authentication"
}

resource "grc_evidence" "mfa_evidence" {
  control_id = grc_control.mfa.id
  source     = "okta_mfa_report"
  hash       = "abc123..."
}
```

```bash
grc plan    # Generate compliance plan
grc apply   # Apply to GRC_Claw
```

---

## Log and alert ingestion

`POST /api/ingest/normalize` — `source`, `tenantId`, `payload`.

**OSS:** `wazuh` · `suricata` · `snort` · `elastic` · `ufw`

**Cloud:** `aws_guardduty` · `aws_cloudwatch` · `aws_securityhub` · `aws_cloudtrail` · `azure_sentinel` · `azure_defender` · `azure_monitor` · `gcp_chronicle` · `gcp_scc` · `gcp_cloud_logging`

---

## A2Z SOC integration

Production security operations live on **[a2zsoc.com](https://a2zsoc.com)**. GRC_Claw connects via `@grc-claw/a2z-connector`:

```bash
A2Z_SOC_MODE=private
A2Z_SOC_BASE_URL=https://a2zsoc.com
A2Z_SOC_API_KEY=<your-integration-key>
```

**Demo mode** (`A2Z_SOC_MODE=demo`) works offline for CI and local dev.

---

## Agentic AI security

OpenClaw for GRC means agents are **untrusted by default**:

1. **Allowlist** — registered tools only
2. **Approval** — destructive SOAR needs `approvalToken`
3. **Sandbox** — Docker default

| Tier | Examples |
|------|----------|
| Read | `claw.list_skills`, `grc.list_controls`, `soc.query_events` |
| Write | `claw.run_skill`, `evidence.attach` |
| Destructive | `sentinel.run_playbook`, `chronicle.soar.run_playbook` |

---

## Testing

```bash
npm run test:comprehensive   # Full test suite
npm run test:skills          # Skill executor
npm run test:iso42001        # ISO 42001 AIMS
npm run test:cloud           # Cloud connectors
npm run test:byoc            # BYOC connectors
```

**Total: 401+ tests across 47 test files**

---

## Deployment

- **systemd:** [deploy/systemd/grc-claw-gateway.service](deploy/systemd/grc-claw-gateway.service)
- **Docker:** [deploy/docker-compose.yml](deploy/docker-compose.yml)
- **Helm:** [deploy/helm/](deploy/helm/)

---

## Documentation

| Doc | Topic |
|-----|--------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | Gateway daemon, planes, OpenClaw mapping |
| [docs/AGENTIC_AI_SECURITY.md](docs/AGENTIC_AI_SECURITY.md) | Agent threat model |
| [docs/BYOC_CONNECTORS.md](docs/BYOC_CONNECTORS.md) | Bring Your Own LLM + MCP |
| [docs/SKILL_EXECUTOR.md](docs/SKILL_EXECUTOR.md) | `claw.*` tools, run loop |
| [docs/ISO_42001_AIMS.md](docs/ISO_42001_AIMS.md) | ISO/IEC 42001 AIMS |
| [integrations/a2z-soc/README.md](integrations/a2z-soc/README.md) | API contract |

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

### Completed

- [x] 67 packages with 132 agent tools (124 real implementations)
- [x] 167 integration connectors
- [x] 16 CLI commands (scan, plan, apply, audit, report, init, iac-scan, pqc-scan, ai-bom, doctor, drift, diff, status, frameworks, version, sovereign init)
- [x] RBAC multi-tenancy with JWT auth
- [x] Terraform provider for compliance-as-code
- [x] 39 compliance framework packs
- [x] Monte Carlo + FAIR risk quantification
- [x] Compliance autopilot with continuous monitoring
- [x] Agent identity (DID:GRC) with verifiable credentials
- [x] Security graph with attack path tracing
- [x] SOAR playbook engine with 4 built-in playbooks
- [x] Observability (OpenTelemetry + Prometheus)
- [x] PostgreSQL persistence with in-memory cache
- [x] Blockchain-style hash chain audit trail
- [x] Real-time WebSocket streaming
- [x] OpenAPI auto-generation
- [x] Agent discovery scanner
- [x] ZK compliance proofs
- [x] Federated compliance mesh
- [x] AI supply chain sovereignty
- [x] Board reporting
- [x] ChatGRC chatbot
- [x] Framework crosswalk (10 mapping sets)
- [x] Policy management hub (52 templates)
- [x] Vendor risk management
- [x] Employee lifecycle
- [x] Compliance task engine
- [x] Evidence automation
- [x] Drift detection
- [x] Browser evidence collection
- [x] Device compliance agent
- [x] Questionnaire automation
- [x] MCP server (16 tools)
- [x] OpenAPI generator
- [x] Agent discovery scanner
- [x] 167 integration connectors

### Upcoming

- [ ] AI Agent Governance Dashboard (drift, trust scores, audit)
- [ ] Compliance-as-Code Linter (grcfile.yaml validation)
- [ ] Real-time compliance trend charts in console
- [ ] Evidence provenance graph visualization
- [ ] Multi-framework compliance crosswalk UI
- [ ] Vendor risk questionnaire auto-fill with AI
- [ ] Board reporting with PDF export
- [ ] Slack/Teams notification integration (notification-engine exists)
- [ ] OAuth 2.0 flow for integration marketplace connectors
- [ ] Real PaloAlto/Fortinet firewall SOAR integration
- [ ] Real Azure Sentinel/Chronicle SOAR integration
- [ ] Execution history store for SOAR playbooks
- [ ] Multi-tenant audit portal for customers
- [ ] Compliance simulator (what-if scenarios)
- [ ] Real-time compliance drift alerting via notification engine

---

**Inspired by [OpenClaw](https://github.com/openclaw/openclaw). Engineered for enterprise GRC. Secured for agents. Production SOC at [a2zsoc.com](https://a2zsoc.com).**
