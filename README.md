# GRC_Claw

Open-source GRC automation engine — 71 packages, 27,596 control mappings, autonomous agent, Terraform provider, VS Code extension

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![npm](https://img.shields.io/badge/npm-%40grc--claw-red?logo=npm)](https://www.npmjs.com/search?q=%40grc-claw)
[![Node](https://img.shields.io/badge/node-%3E%3D20-brightgreen)](package.json)
[![GitHub](https://img.shields.io/badge/GitHub-AAH20%2FGRC__Claw-181717?logo=github)](https://github.com/AAH20/GRC_Claw)
[![A2Z SOC](https://img.shields.io/badge/A2Z%20SOC-a2zsoc.com-red)](https://a2zsoc.com)

---

## What it is

GRC_Claw is a TypeScript/Go monorepo (71 packages, 288,053+ LOC) that turns compliance operations into code. The core is a **27,596-mapping crosswalk corpus** spanning 13 frameworks and 824 controls — the machine-readable layer that lets the SDK, CLI, VS Code extension, and Terraform provider all speak the same control language. An autonomous agent runtime (3-phase plan → act → verify, with trust scoring and auto-pause) ties it together for continuous compliance monitoring. The platform ships with **168 integration connectors**, **163 agent tools** (124 real implementations), **130+ HTTP endpoints**, **18 CLI commands**, **PostgreSQL persistence**, **RBAC multi-tenancy**, **notification engine** (Slack/Email/Teams), **browser-based evidence collection** (Playwright), and a **blockchain-style hash chain audit trail**.

The project follows an **open-core model**: GRC_Claw is MIT-licensed and ships 32 packages to npm under the `@grc-claw/` scope. The commercial layer is **[A2Z SOC](https://a2zsoc.com)** — a hosted SOC platform that consumes the GRC_Claw engine for production security operations, SIEM, and enterprise multi-tenancy. You can run GRC_Claw fully standalone, or point it at A2Z SOC for the cloud control plane.

---

## Install

### npm (recommended)

v0.8.0 is live on the npm registry under the `@grc-claw/` scope.

```bash
npm install -g @grc-claw/cli
```

### Homebrew (macOS / Linux)
```bash
brew tap a2zsoc/grc https://github.com/AAH20/GRC_Claw
brew install grc-claw
```

### From source
```bash
git clone https://github.com/AAH20/GRC_Claw
cd GRC_Claw && npm install && npm run build
```

---

## Quick start

```bash
npm install @grc-claw/sdk
```

```bash
# Install CLI globally
npm install -g @grc-claw/cli

# Scan current directory for compliance issues
grc scan .

# Run the autonomous compliance agent
grc agent run

# Bootstrap a sovereign (air-gap) deployment with Ollama
grc sovereign init
```

---

## Packages (32 published · 39 private)

| Package | Description | Version |
|---------|-------------|---------|
| `@grc-claw/sdk` | TypeScript SDK for A2Z SOC platform | v0.8.0 |
| `@grc-claw/cli` | GRC CLI — 18 commands | v0.8.0 |
| `@grc-claw/mcp-server` | MCP server for Claude / AI assistant integration | v0.8.0 |
| `@grc-claw/compliance-copilot` | VS Code extension — 11 rules, 6 languages | v0.8.0 |
| `@grc-claw/agent-runtime` | 3-phase autonomous agent (plan → act → verify) | v0.8.0 |
| `@grc-claw/connectors` | BYOC LLM (OpenAI / Anthropic / Ollama) + SOVEREIGN_MODE | v0.8.0 |
| `@grc-claw/security-graph` | BFS blast-radius analysis | v0.8.0 |
| `@grc-claw/zk-compliance` | RFC 3161 TSA proof chain (FreeTSA.org, ASN.1/DER) | v0.8.0 |
| `@grc-claw/oscal` | OSCAL 1.1.2 SSP, POA&M, Component Definition export | v0.8.0 |
| `@grc-claw/soar` | SOAR playbook engine — 5 built-in playbooks | v0.8.0 |
| `@grc-claw/framework-crosswalk` | 27,596-mapping multi-framework crosswalk corpus | v0.8.0 |
| `@grc-claw/evidence` | SHA-256 evidence lineage + PostgreSQL persistence | v0.8.0 |
| `@grc-claw/agent-identity` | DID:GRC verifiable credentials (W3C VC JSON-LD) | v0.8.0 |
| `@grc-claw/risk-quantification` | Monte Carlo simulation + FAIR risk calculator | v0.8.0 |
| `@grc-claw/frameworks` | 13 compliance framework packs, 824 controls | v0.8.0 |
| `@grc-claw/ingest` | OSS SIEM / IDS / firewall + cloud normalizers | v0.8.0 |
| `@grc-claw/persistence` | PostgreSQL persistence layer | v0.8.0 |
| `@grc-claw/rbac-multi-tenant` | JWT auth, 5 roles, tenant isolation | v0.8.0 |
| `@grc-claw/compliance-autopilot` | Continuous monitoring + gap detection + remediation | v0.8.0 |
| `@grc-claw/drift-detector` | Compliance drift detection + severity scoring | v0.8.0 |
| `@grc-claw/policy-management-hub` | Policy lifecycle — create → approve → publish → attest | v0.8.0 |
| `@grc-claw/vendor-risk-management` | Vendor risk scoring + questionnaires + monitoring | v0.8.0 |
| `@grc-claw/observability` | OpenTelemetry tracing + Prometheus metrics | v0.8.0 |
| `@grc-claw/a2z-connector` | A2Z SOC platform API bridge | v0.8.0 |
| `@grc-claw/core` | Canonical events, GRCEngineFacade | v0.8.0 |
| `@grc-claw/gateway` | HTTP/WebSocket gateway daemon | v0.8.0 |
| `@grc-claw/continuous-trust-engine` | Dynamic trust scoring across evidence, controls, agents, risk, and behavior | internal |
| `@grc-claw/agent-collaboration` | Multi-agent collaboration sessions, capability matching, and consensus workflows | internal |
| `@grc-claw/regulatory-change-management` | Regulatory source tracking, impact analysis, timelines, and remediation gaps | internal |
| `@grc-claw/ai-governance` | AI system inventory, EU AI Act risk classification, assessments, and monitoring | internal |

The remaining 45 packages are private or pre-release. See the monorepo root `package.json` for the full workspace list.

---

## The crosswalk corpus

The **27,596 framework control mappings** stored in the live A2Z SOC database are GRC_Claw's most defensible asset. They express, for every control in every supported framework, exactly which controls in peer frameworks are equivalent or overlapping — so a single evidence artifact can satisfy requirements across multiple audits simultaneously.

- **13 frameworks** covered: ISO 27001, SOC 2, NIST CSF, NIST 800-53, HIPAA, PCI DSS, GDPR, FedRAMP, CMMC, CIS Controls, DORA, NIS2, EU AI Act
- **824 unique controls** indexed
- Exposed via the **Crosswalk API** at [a2zsoc.com/crosswalk-api](https://a2zsoc.com/crosswalk-api)
- Consumed by `@grc-claw/framework-crosswalk` and the CLI `grc diff` command

---

## VS Code extension

`@grc-claw/compliance-copilot` adds real-time compliance linting to VS Code:

- **11 compliance rules** covering secrets, logging, encryption, access control, and audit trails
- **6 languages**: TypeScript, JavaScript, Python, Go, Rust, Java
- 500 ms debounce for low-latency inline diagnostics
- Maps findings directly to framework control IDs

Install from the VS Code Marketplace or `code --install-extension grc-claw.compliance-copilot`.

---

## Terraform provider

The `terraform-provider-grc` (Go implementation) lets you manage GRC resources as infrastructure code. The provider is published to the Terraform Registry at [`registry.terraform.io/providers/a2zsoc/grc`](https://registry.terraform.io/providers/a2zsoc/grc). Release automation uses `.goreleaser.yml` in `packages/terraform-provider/`.

**Resources:**

- `grc_control` — declare a compliance control and its metadata
- `grc_evidence` — attach an evidence artifact to a control with hash lineage
- `grc_framework` — register a compliance framework with control mappings
- `grc_risk` — define a risk scenario with FAIR quantification parameters
- `grc_agent_policy` — configure autonomous agent guardrails and approval workflows

```hcl
terraform {
  required_providers {
    grc = {
      source  = "registry.terraform.io/providers/a2zsoc/grc"
      version = "~> 0.8"
    }
  }
}

resource "grc_control" "mfa" {
  framework = "soc2"
  code      = "CC6.1"
  name      = "Multi-Factor Authentication"
}

resource "grc_evidence" "mfa_report" {
  control_id = grc_control.mfa.id
  source     = "okta_mfa_report"
  hash       = filesha256("reports/mfa_audit.pdf")
}
```

```bash
terraform init && terraform plan && terraform apply
```

---

## Sovereign / air-gap mode

Set `SOVEREIGN_MODE=true` to route all LLM traffic through a local Ollama instance. No data leaves your network.

```bash
export SOVEREIGN_MODE=true
grc sovereign init          # writes docker-compose.sovereign.yml
docker compose -f docker-compose.sovereign.yml up
```

`grc sovereign init` generates a Docker Compose stack with Ollama pre-configured as the sole LLM backend. The `@grc-claw/connectors` package enforces the routing — any call that would otherwise reach OpenAI or Anthropic is redirected to `http://localhost:11434`.

---

## Verifiable Credentials

`@grc-claw/agent-identity` issues W3C Verifiable Credentials for compliance attestations:

- **DID method**: `did:grc:a2zsoc` — the issuer DID anchored to the A2Z SOC platform
- **Proof type**: `SHA256Proof2026` (JSON-LD linked data proof)
- **Timestamp anchoring**: RFC 3161 TSA via FreeTSA.org, with an inline ASN.1/DER encoder for portable timestamp tokens
- Credentials are stored in PostgreSQL and verifiable offline against the public DID document

```bash
grc agent run   # agent signs attestations automatically during verify phase
```

---

## CLI commands

`@grc-claw/cli` ships 18 commands:

```bash
grc init                    # Scaffold grcfile.yaml + GitHub Actions workflow
grc scan .                  # Codebase compliance scan (12 rules, posture score)
grc plan                    # Generate compliance remediation plan
grc apply                   # Apply plan to GRC_Claw
grc audit                   # Full compliance audit with evidence
grc status                  # Current compliance posture
grc drift                   # Detect compliance drift from baseline
grc diff                    # Crosswalk delta between git refs or frameworks
grc report                  # Generate evidence report
grc doctor                  # Environment checks (add --fix to auto-remediate)
grc iac-scan .              # Terraform / Kubernetes compliance scan (8 rules)
grc pqc-scan .              # Post-quantum cryptography migration scan (6 patterns)
grc ai-bom generate         # AI Bill of Materials (EU AI Act Article 53)
grc ai-bom publish          # Publish AI BOM to A2Z SOC registry
grc frameworks list         # List available compliance framework packs
grc agent run               # Launch autonomous 3-phase compliance agent
grc sovereign init          # Write Ollama Docker Compose stack
grc version                 # Print version
```

---

## Autonomous agent

`@grc-claw/agent-runtime` implements a 3-phase execution loop:

1. **Plan** — discovers controls, gaps, and remediation actions
2. **Act** — executes remediations within policy constraints
3. **Verify** — collects evidence, issues verifiable credentials, updates trust score

The agent maintains a **trust score** derived from behavioral signals. If the score drops below the configured threshold, the agent auto-pauses and requires human review before continuing. Destructive actions require an explicit `approvalToken`.

---

## Agentic assurance receipts

`@grc-claw/evidence` now exposes an auditor-safe receipt primitive for agentic systems:

- `createAssuranceEnvelope(...)` builds a redacted receipt from action-ledger intent, policy decision, and result events.
- `verifyAssuranceEnvelope(...)` checks required ledger hashes, identity metadata, timestamps, and payload-redaction markers.
- `hashAssuranceEnvelope(...)` produces a deterministic SHA-256 receipt fingerprint for proof rooms, export APIs, and auditor portals.
- `redactAssuranceEnvelopeForSharing(...)` returns a share-safe version for third-party verification.

The gateway records these envelopes around supervised agent actions and exposes the assurance graph through `/api/assurance`.

---

## MCP server

`@grc-claw/mcp-server` exposes GRC_Claw capabilities to Claude and other MCP-compatible AI assistants. Point your MCP client at the server to query controls, retrieve crosswalk mappings, trigger scans, and read evidence — all from within your AI assistant's context.

---

## Cloud connectors (v9.0)

`packages/cloud-connectors` gained four new integrations in v9.0:

| Connector | File | What it collects |
|-----------|------|-----------------|
| **Jira** | `jira.ts` | Issues, projects, and workflow audit data for change management evidence |
| **Linear** | `linear.ts` | Issues and cycles for engineering change tracking |
| **CrowdStrike** | `crowdstrike.ts` | Endpoint detections, host inventory, and vulnerability findings |
| **AWS Asset Inventory** | `aws-asset-inventory.ts` | EC2, S3, IAM, RDS, and Lambda asset discovery for cloud posture evidence |

All connectors implement the standard `EvidenceConnector` interface and emit typed evidence envelopes compatible with `@grc-claw/evidence`.

---

## Notification engine

`@grc-claw/notification-engine` delivers compliance alerts across three channels:

- **Slack** — Block Kit rich formatting via incoming webhooks
- **Email** — raw SMTP with STARTTLS and AUTH LOGIN
- **Microsoft Teams** — webhook cards with theme colors

Includes rate limiting (per minute/hour/day), exponential backoff retry, delivery history, and delivery stats. Six built-in templates: compliance alert, drift alert, remediation complete, incident created, risk threshold exceeded, custom.

---

## Browser evidence collection

`@grc-claw/browser-evidence` provides Playwright-based evidence collection for web application controls:

- Dynamic Playwright import (graceful error if not installed)
- Chromium launch with configurable headless, timeout, slowMo, userAgent, viewport
- Full `BrowserAdapter` interface: `launch()`, `navigate()`, `screenshot()`, `getContent()`, `fillInput()`, `click()`, `getText()`, `elementExists()`

---

## Agent audit trail

`@grc-claw/agent-audit-trail` maintains a blockchain-style hash chain for all agent actions:

- Each record's SHA-256 hash includes the previous record's hash
- Write-through to PostgreSQL for persistence
- `verify()` validates entire chain integrity (genesis hash check, chain linkage, tamper detection)
- `query()` supports filtering by agent DID, tool, date range, pagination
- `export()` supports JSON and CSV formats

---

## Agent trust scoring

`@grc-claw/agent-trust-score` derives behavioral trust signals from the audit trail:

- Trust score derived from tool usage patterns, error rates, and approval compliance
- Auto-pause when score drops below configured threshold
- Destructive actions require explicit `approvalToken`
- Trust profile persisted across sessions

---

## A2Z SOC integration

[A2Z SOC](https://a2zsoc.com) is the commercial platform built on top of GRC_Claw. It adds:

- Hosted crosswalk API with the full 27,596-mapping corpus
- Multi-tenant enterprise SIEM and SOC operations
- Managed PostgreSQL evidence store
- Production alerting, dashboards, and reporting
- 669 page React dashboard with 182 components
- 350+ navigation items across GRC, SOC, Enterprise, and PLG surfaces
- vCISO marketplace, broker channels, PE cyber diligence
- Learning center with training and certifications

```bash
A2Z_SOC_BASE_URL=https://a2zsoc.com
A2Z_SOC_API_KEY=<your-key>
```

See [a2zsoc.com](https://a2zsoc.com) for pricing and API key self-serve.

---

## Strategic moat roadmap

GRC_Claw is designed to compound around assets that are hard to clone with capital alone:

1. **Agentic assurance receipts** — every autonomous plan, tool call, remediation, exception, approval, and verification step should emit a signed, redacted receipt with intent, policy decision, evidence hash, control mapping, actor identity, timestamp, and replay-safe metadata.
2. **Crosswalk network effects** — every new framework pack, mapping, audit exception, and customer evidence pattern should strengthen the shared control graph instead of living as one-off implementation work.
3. **Evidence connector marketplace** — cloud, SaaS, SIEM, EDR, ticketing, source-control, IaC, browser, and local-agent collectors should plug into one evidence envelope format so third parties can build connectors without fragmenting audit semantics.
4. **Regulated AI procurement wedge** — CMMC, NIST 800-171, ISO 42001, NIST AI RMF, EU AI Act, SOC 2, ISO 27001, FedRAMP, and defense/critical-infrastructure procurement packs should share one proof model instead of separate dashboards.
5. **Auditor and verifier interfaces** — read-only proof rooms, OSCAL exports, verifiable credentials, RFC 3161 timestamp proofs, and evidence lineage APIs should let external auditors verify claims without trusting the application UI.
6. **Sovereign and air-gap deployments** — the same engine should run hosted on A2Z SOC, self-hosted for enterprises, or fully local with Ollama/private models for defense, government, and regulated operators.
7. **Benchmark intelligence** — anonymized, opt-in metrics for evidence freshness, remediation latency, control reuse, drift frequency, connector reliability, and audit readiness should become the industry reference layer.

The anti-commoditization principle is simple: dashboards are copyable; a longitudinal, signed history of controls, evidence, agent actions, crosswalk decisions, and auditor-verified outcomes is not.

---

## Contributing

GRC_Claw is MIT-licensed. PRs welcome — framework packs, language rules for the VS Code extension, additional Terraform resources, and connector implementations are the highest-value contributions.

```bash
git clone https://github.com/AAH20/GRC_Claw.git
cd GRC_Claw
npm install && npm run build
npm run test:comprehensive
```

**Test results:** 401+ tests passing, 0 failures.

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines, code style, and PR process.

Repository: [github.com/AAH20/GRC_Claw](https://github.com/AAH20/GRC_Claw)

---

## Community

- [COMMUNITY.md](COMMUNITY.md) — code of conduct, support channels, and community norms
- [CONTRIBUTING.md](CONTRIBUTING.md) — how to contribute, run tests, and submit PRs
- [GitHub Discussions](https://github.com/AAH20/GRC_Claw/discussions) — questions, ideas, and show-and-tell
- [GitHub Issues](https://github.com/AAH20/GRC_Claw/issues) — bug reports and feature requests

---

## License

[MIT](LICENSE)
