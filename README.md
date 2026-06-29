# GRC_Claw

Open-source GRC automation engine — 79 packages, 27,596 control mappings, autonomous agent, Terraform provider, VS Code extension

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![npm](https://img.shields.io/badge/npm-%40grc--claw-red?logo=npm)](https://www.npmjs.com/search?q=%40grc-claw)
[![Node](https://img.shields.io/badge/node-%3E%3D20-brightgreen)](package.json)
[![GitHub](https://img.shields.io/badge/GitHub-AAH20%2FGRC__Claw-181717?logo=github)](https://github.com/AAH20/GRC_Claw)
[![A2Z SOC](https://img.shields.io/badge/A2Z%20SOC-a2zsoc.com-red)](https://a2zsoc.com)

---

## What's New in v10.0

| Feature | Description |
|---------|-------------|
| **ZK Audit Bundle** | SHA-256 Merkle tree + RFC 3161 TSA timestamp (FreeTSA.org); public `/verify` endpoint for auditor-safe proof |
| **FAIR Risk Quantification** | EAL = (TEF × Vuln%) × (Primary + Secondary Loss); dollar-denominated risk tiers |
| **STRIDE Threat Modeling** | Claude-backed `stride_matrix` JSON output with MITRE ATT&CK mappings |
| **Trust Score Badge** | 5-factor score (evidence 25%, vuln 25%, controls 20%, training 15%, incidents 15%) → 0–100 with A/B/C/D/F grade + embeddable SVG badge |
| **Pack Marketplace** | Community GRC pack submission and catalog (YAML schema with control mappings) |
| **Continuous Control Testing** | 5 built-in SOC 2 tests, automated via cron |
| **Evidence Daemon** | Auto-pulls GitHub branch protection (CC8.1) and Okta MFA (CC6.1) every 24 h |
| **Shared Answer Library** | SHA-256 keyed, confidence scoring (0.5 → 0.99 via votes), cross-org knowledge sharing |
| **Regulatory Deadline Engine** | Auto-creates tasks at 90/60/30 days before regulation deadlines |
| **Standards Exports** | OCSF 1.1 (`ocsf.ts`), STIX 2.1 (`stix.ts`), SARIF 2.1.0 (`sarif.ts`) added to `packages/oscal` |
| **Cloud Connectors** | Jira, Linear, CrowdStrike, AWS Asset Inventory — see [Cloud connectors](#cloud-connectors-v100-) below |

---

## What it is

GRC_Claw is a TypeScript/Go monorepo (79 packages, 288,053+ LOC) that turns compliance operations into code. The core is a **27,596-mapping crosswalk corpus** spanning 13 frameworks and 824 controls — the machine-readable layer that lets the SDK, CLI, VS Code extension, and Terraform provider all speak the same control language. An autonomous agent runtime (3-phase plan → act → verify, with trust scoring and auto-pause) ties it together for continuous compliance monitoring. The platform ships with **168 integration connectors**, **191 agent tools** (146 real implementations), **150+ HTTP endpoints**, **18 CLI commands**, **PostgreSQL persistence**, **RBAC multi-tenancy**, **notification engine** (Slack/Email/Teams), **browser-based evidence collection** (Playwright), **blockchain-style hash chain audit trail**, **compliance knowledge graph**, **predictive compliance engine**, **compliance marketplace**, and **zero-trust audit trail**.

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

## Packages (32 published · 47 private)

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
| `@grc-claw/compliance-knowledge-graph` | Living graph of frameworks, controls, evidence, threats, technologies, and posture | v0.8.0 |
| `@grc-claw/predictive-compliance` | Failure forecasting, risk scoring, trend analysis, and remediation recommendations | v0.8.0 |
| `@grc-claw/compliance-marketplace` | Proof-backed compliance pack publishing, discovery, installation, and ratings | v0.8.0 |
| `@grc-claw/zero-trust-audit` | Cryptographic audit trail with hash chains, Merkle proofs, and evidence export | v0.8.0 |

The remaining 47 packages are private or pre-release. See the monorepo root `package.json` for the full workspace list.

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

## Cloud connectors (v10.0)

`packages/cloud-connectors` gained four new integrations in v10.0:

| Connector | File | What it collects |
|-----------|------|-----------------|
| **Jira** | `jira.ts` | Issues, projects, and workflow audit data for change management evidence |
| **Linear** | `linear.ts` | Issues and cycles for engineering change tracking |
| **CrowdStrike** | `crowdstrike.ts` | Endpoint detections, host inventory, and vulnerability findings |
| **AWS Asset Inventory** | `aws-asset-inventory.ts` | EC2, S3, IAM, RDS, and Lambda asset discovery for cloud posture evidence |

All connectors implement the standard `EvidenceConnector` interface and emit typed evidence envelopes compatible with `@grc-claw/evidence`.

---

## Standards exports (OSCAL / OCSF / STIX / SARIF)

`packages/oscal/src` ships four standards export modules:

| Module | Standard | File |
|--------|----------|------|
| OSCAL | OSCAL 1.1.2 SSP, POA&M, Component Definition | `oscal.ts` |
| OCSF | Open Cybersecurity Schema Framework 1.1 | `ocsf.ts` |
| STIX | STIX 2.1 threat intelligence bundles | `stix.ts` |
| SARIF | Static Analysis Results Interchange Format 2.1.0 | `sarif.ts` |

All four are consumed by the CLI (`grc report`) and the MCP server, and can be imported directly from `@grc-claw/oscal`.

---

## ZK Audit Bundle

`packages/zk-compliance` produces a cryptographically verifiable audit bundle:

- SHA-256 Merkle tree over all evidence records in a compliance period
- RFC 3161 timestamp from FreeTSA.org embedded in the bundle (ASN.1/DER format)
- Public `/verify` endpoint returns `{ valid: true, root, timestamp, chain }` — auditors can verify without raw data access
- Compatible with the zero-trust audit room and `@grc-claw/zero-trust-audit`

---

## FAIR Risk Quantification

`@grc-claw/risk-quantification` calculates dollar-denominated risk using the FAIR model:

```
EAL = (TEF × Vulnerability%) × (Primary Loss + Secondary Loss)
```

- Input: threat event frequency, vulnerability rate, primary/secondary loss magnitudes
- Output: expected annual loss in USD with confidence intervals (Monte Carlo simulation)
- Risk tiers: Critical / High / Medium / Low with color-coded thresholds
- Integrated into the agent verify phase and the CLI `grc audit` command

---

## STRIDE Threat Modeling

The agent runtime now generates structured threat models via Claude:

- Accepts an architecture description (system prompt or YAML component list)
- Outputs a `stride_matrix` JSON: each threat category (Spoofing, Tampering, Repudiation, Information Disclosure, DoS, Elevation of Privilege) mapped to affected components with MITRE ATT&CK technique IDs
- Threat entries automatically link to GRC_Claw controls and produce remediation tasks
- Accessible via `grc agent run` and the MCP `stride_threat_model` tool

---

## Trust Score Badge

`@grc-claw/continuous-trust-engine` computes a 0–100 trust score from five weighted factors:

| Factor | Weight |
|--------|--------|
| Evidence freshness | 25% |
| Vulnerability exposure | 25% |
| Control test pass rate | 20% |
| Training completion | 15% |
| Incident transparency | 15% |

- Grade: A (90–100), B (80–89), C (70–79), D (60–69), F (<60)
- Embeddable SVG badge at `/api/trust-score/badge.svg`
- Score is signed, decomposable into proof objects, and exportable to buyer portals

---

## Pack Marketplace

`@grc-claw/compliance-marketplace` is a community GRC pack registry:

- YAML schema with control mappings, evidence collectors, remediation playbooks, and semantic versioning
- Pack submission via `grc marketplace publish`
- Discovery and installation via `grc marketplace install <pack-name>`
- Signed provenance, ratings, and maintainer reputation per pack

---

## Continuous Control Testing

Five built-in SOC 2 control tests run automatically on a configurable cron schedule:

1. MFA enforcement check (CC6.1)
2. Encryption at rest verification (CC6.7)
3. Audit log retention check (CC7.2)
4. Access review completeness (CC6.3)
5. Incident response test (CC7.3)

Results feed directly into the Trust Score and the evidence vault.

---

## Evidence Daemon

An always-on background process auto-collects evidence every 24 hours:

- **GitHub branch protection** → maps to SOC 2 CC8.1 (change management)
- **Okta MFA status** → maps to SOC 2 CC6.1 (logical access)

Evidence is hashed, timestamped, and written to the evidence vault with full lineage. Configure via `grc.config.yaml` under `evidence_daemon`.

---

## Shared Answer Library

Cross-organization compliance knowledge sharing:

- Answers keyed by SHA-256 hash of the question text
- Confidence scoring from 0.50 (single unverified answer) to 0.99 (high-vote consensus)
- Votes from verified organizations increase confidence; contradictions trigger review
- Accessible via the MCP `answer_library_lookup` tool and `@grc-claw/compliance-knowledge-graph`

---

## Regulatory Deadline Engine

`@grc-claw/regulatory-change-management` auto-creates tasks ahead of regulatory deadlines:

- Monitors tracked regulation dates (e.g., DORA go-live, NIS2 review cycles, CMMC assessment windows)
- Creates remediation tasks at 90, 60, and 30 days before each deadline
- Tasks link to affected controls, evidence gaps, and responsible owners
- Integrates with the notification engine for Slack/Email/Teams alerts

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

## 2026-2030 monopoly-grade build priorities

The next moat is not another dashboard. It is a compounding trust network where A2Z SOC is the hosted control plane and GRC_Claw is the open, inspectable execution engine.

1. **Compliance knowledge graph** — unify frameworks, controls, evidence, threats, assets, vendors, AI systems, regulations, and remediation history into one traversable graph. The graph should answer "what changed, who is affected, what evidence proves it, and which customers can reuse it?"
2. **Proof-backed pack marketplace** — let auditors, MSPs, defense contractors, cloud specialists, and industry experts publish signed compliance packs with tests, mappings, evidence collectors, remediation playbooks, pricing, ratings, and provenance.
3. **Predictive compliance engine** — forecast audit failure, evidence staleness, control drift, regulator-change impact, vendor risk, and remediation cost before the audit window. The product should sell prevention, not just reporting.
4. **Zero-trust audit room** — replace static trust centers with a verifier portal where buyers and auditors can inspect signed receipts, OSCAL exports, verifiable credentials, change history, redacted evidence lineage, and exception approvals without raw-data access.
5. **Agent policy firewall** — govern every MCP/tool/agent action with allowlists, approval thresholds, blast-radius scoring, tenant scope, idempotency, replay prevention, and receipt generation. This is the security layer agent harness teams will need but rarely want to build.
6. **Defense procurement lane** — package CMMC, NIST 800-171, FedRAMP, ISO 42001, SBOM, AI BOM, supplier risk, and sovereign deployment into one acquisition-ready path for defense industrial base, critical infrastructure, and government-adjacent vendors.
7. **Benchmark data network** — aggregate opt-in, anonymized metrics for evidence freshness, audit duration, remediation latency, control reuse, connector reliability, and regulatory-change exposure. Over time, these benchmarks become harder to copy than the software.

Near-term execution order:

- **First 30 days:** ship the knowledge graph and zero-trust audit room as visible A2Z SOC surfaces backed by GRC_Claw packages.
- **Next 60 days:** turn compliance packs into a marketplace with signed provenance, ratings, and revenue share.
- **Next 90 days:** add predictive compliance scoring to every dashboard, MCP response, and audit export.
- **Next 6 months:** make CMMC/NIST 800-171 + ISO 42001 the flagship procurement bundle.

The strategic line: proprietary incumbents can outspend a feature sprint, and open-source projects can copy isolated utilities. The hard-to-copy asset is the networked history of signed evidence, control mappings, agent receipts, verified packs, customer benchmarks, and auditor trust.

---

## Graph-backed next moves: acquisition-grade monopoly path

A June 2026 graph-first audit of the combined A2Z SOC + GRC_Claw codebase shows the moat is no longer missing breadth. The platform already has hundreds of GRC, SOC, trust, marketplace, risk, threat-modeling, ZK audit, MCP, and procurement surfaces. The next advantage comes from turning those surfaces into compounding engines that competitors cannot clone by shipping another UI.

Highest-leverage improvements:

1. **Unify every proof surface into an Evidence Graph API**
   Merge evidence vault entries, control tests, trust scores, ZK audit bundles, risk scenarios, threat models, marketplace packs, agent receipts, and framework mappings into one queryable graph. A2Z SOC should expose this as a hosted verifier API; GRC_Claw should expose the local engine. The buyer outcome: "show me every claim, control, proof, agent action, and downstream dependency behind this trust score."

2. **Turn Pack Marketplace into a signed compliance supply chain**
   The marketplace should not be a content catalog. Every pack should include signed provenance, tests, control mappings, evidence collectors, remediation playbooks, maintainer reputation, semantic versioning, dependency rules, revenue share, and verifier results. This creates the HashiCorp/Terraform-registry style network effect for compliance.

3. **Ship an Agent Policy Firewall as the default gateway mode**
   MCP, browser agents, IDE agents, cloud agents, SOAR workflows, and remediation bots should pass through a policy firewall with scope checks, approval thresholds, idempotency keys, tool risk scoring, replay prevention, and receipt export. Agent harness teams can build orchestration; they will not want to build audit-grade governance from scratch.

4. **Make Trust Score explainable, signed, and portable**
   The trust score should become a public, embeddable, signed credential backed by evidence freshness, control-test results, vulnerability exposure, training completion, incident transparency, and procurement readiness. Every score should be decomposable into proof objects and exportable to buyer portals, auditors, brokers, and marketplace listings.

5. **Build the CMMC / NIST 800-171 / ISO 42001 procurement lane**
   Package SPRS scoring, SSP/POA&M generation, CUI boundary mapping, supplier risk, AI system inventory, SBOM/AI-BOM, FedRAMP inheritance, and agent-action receipts into a single defense-industrial-base readiness workflow. This is the fastest wedge into cybersecurity, GRC, agentic AI governance, and procurement budgets at once.

6. **Add predictive compliance economics everywhere**
   Risk quantification should not live as a separate calculator. Every control, evidence gap, vendor issue, failed test, and agent exception should produce dollarized exposure, remediation cost, time-to-audit impact, and expected-loss reduction. This moves the product from "compliance tracking" to CFO-visible risk economics.

7. **Convert threat modeling into live control generation**
   STRIDE outputs should automatically create controls, tests, evidence requirements, remediation tasks, and framework mappings. The monopoly move is closing the loop from architecture description → threat model → controls → evidence → auditor proof → trust score.

8. **Create a verifier network, not just tenant dashboards**
   Auditors, customers, brokers, MSPs, PE diligence teams, and primes should be able to verify claims through scoped rooms without seeing raw tenant data. This makes A2Z SOC the trust clearinghouse while GRC_Claw remains the inspectable execution layer.

Immediate execution priority:

- **Week 1:** normalize Trust Score, ZK Audit Bundle, Control Tests, Risk Quantification, Threat Modeling, and Pack Marketplace outputs into one Evidence Graph schema. **Implemented first slice:** A2Z SOC now exposes `/api/platform/evidence-graph/*` and GRC_Claw exposes `/api/evidence-graph/*`.
- **Week 2:** expose matching `evidence_graph.*` tools in GRC_Claw for agent/MCP callers. **Implemented first slice:** `evidence_graph.get`, `get_summary`, `get_nodes`, `get_edges`, and `get_recommendations`.
- **Week 3:** add signed pack verification and maintainer reputation to the marketplace.
- **Week 4:** ship the CMMC/NIST 800-171/ISO 42001 procurement cockpit with SSP, POA&M, SPRS, AI inventory, supplier evidence, and agent receipts.

The acquisition-grade thesis: the most valuable asset is not the code count, page count, or number of framework packs. It is the accumulated, signed, cross-tenant map of which controls, evidence, tests, agents, vendors, and remediation paths actually survive audits and procurement reviews.

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
