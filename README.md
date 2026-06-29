# GRC_Claw v13.0

Open-source GRC automation engine — 84 packages, 27,596 control mappings, autonomous agent, Terraform provider, VS Code extension

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![npm](https://img.shields.io/badge/npm-%40grc--claw-red?logo=npm)](https://www.npmjs.com/search?q=%40grc-claw)
[![Node](https://img.shields.io/badge/node-%3E%3D20-brightgreen)](package.json)
[![GitHub](https://img.shields.io/badge/GitHub-AAH20%2FGRC__Claw-181717?logo=github)](https://github.com/AAH20/GRC_Claw)
[![A2Z SOC](https://img.shields.io/badge/A2Z%20SOC-a2zsoc.com-red)](https://a2zsoc.com)

---

## What's New in v13.0

| Feature | Description |
|---|---|
| **Compliance Revenue Assurance** | Track how compliance artifacts (SOC 2 reports, questionnaire kits, trust seals) influence pipeline. Measure ROI in dollars of deals influenced. |
| **Regulatory Change Velocity Engine** | Auto-diff framework updates against your control coverage. Know exactly which controls break when NIST 2.0 or ISO 27002 publishes a change. |
| **Continuous Offensive Pentest Mesh** | Nightly automated probes (TLS, headers, SPF, DMARC) mapped to MITRE ATT&CK. CC7.1 evidence collected automatically. |
| **AI Red Team Simulation** | Claude generates realistic phishing campaigns, social engineering scripts, and insider threat scenarios for security awareness training. CC9.1 evidence. |
| **GRC Plugin Marketplace** | Third-party developers publish compliance packs, evidence collectors, and framework templates. Revenue share model. 6 verified plugins at launch. |
| **vCISO White-Label Portal** | MSPs and vCISOs manage all client orgs under their own brand with AI-generated monthly compliance reports. |
| **Evidence Chain of Custody** | SHA-256 hash of every evidence item at collection. Live re-hash verification for auditors. Legally defensible provenance. |
| **Compliance API Economy** | Metered REST API exposing the 27,596-row framework control mapping dataset. 4 tiers (Free → Enterprise). SHA-256 key auth. |
| **Board Governance AI** | Claude writes quarterly board risk narratives automatically — health status, compliance trends, recommended decisions. |
| **Adversarial AI Compliance Monitor** | Daily bias/hallucination/toxicity/accuracy checks per AI system. Auto-generates EU AI Act Article 9 conformity reports. |

---

## What's New in v12.0

| Feature | Description |
|---------|-------------|
| **GRC Copilot** | Natural Language Compliance Query Engine — chat UI powered by Claude, full session history, ask compliance questions in plain English and receive control-mapped, evidence-linked answers |
| **Real-Time Compliance Feed** | Live event stream aggregating KEV alerts, regulatory deadlines, evidence expiry warnings, control failures, and remediation triggers — 10-second polling with push delivery |
| **Compliance Digital Twin** | Pre-audit simulation engine: Claude acts as auditor to produce predicted pass / qualified / fail verdicts plus detailed findings before the real audit window opens |
| **AI Governance Registry** | EU AI Act risk tier classification (minimal / limited / high / unacceptable) with full NIST AI RMF mapping, inventory tracking, and assessment workflows for every AI system in scope |
| **Quantum-Resistant Crypto Planner** | PQC vulnerability scanner across codebase and infrastructure, paired with a NIST PQC migration roadmap generator (ML-KEM-768, ML-DSA-65) and prioritized remediation tasks |
| **Federated Compliance Mesh** | Multi-subsidiary posture management — aggregate controls, evidence, gaps, and risk across legal entities into a single consolidated compliance dashboard |
| **Predictive Compliance AI** | 90-day evidence velocity forecast per control with nightly gap detection, failure probability scoring, and proactive remediation recommendations before audit windows open |
| **Employee Lifecycle Automation** | Okta offboarding detection triggers automatic deprovisioning evidence collection mapped to CC6.2 / CC6.3, closing the most common SOC 2 access-control audit gap automatically |
| **Third-Party Vendor Risk Feed** | Continuous CVE monitoring per vendor via NVD API, vendor breach acknowledgment workflows, and risk-scored vendor posture updates pushed to the evidence graph in real time |
| **Zero-Trust Immutable Audit Trail** | SHA-256 Merkle-chained append-only log with RFC 3161 TSA timestamps (FreeTSA.org) — every compliance event is cryptographically sequenced and verifiable by external auditors without raw data access |

---

## What's New in v11.0

| Feature | Description |
|---------|-------------|
| **GitHub PR Security Gate** | Composite GitHub Action (`GRC_Claw/.github/actions/scan/action.yml`) — IaC scan + secret detection on every PR, posts GitHub check runs, maps findings directly to SOC 2 controls |
| **`@grc-claw/policy-engine`** | Compliance-as-Code: `.grc-policy.yaml` parser, `validatePolicy()`, `generatePolicyTemplate()`, and continuous drift detection against live control state |
| **Sovereign Deployment Kit** | Production-grade Terraform (AWS VPC / EC2 / EIP / S3 / IAM) + Docker Compose (Supabase self-hosted, Ollama LLM, Nginx TLS, Certbot, nightly S3 backups) in `GRC_Claw/deploy/sovereign/` — supports UAE, KSA, India, EU financial services, and US government air-gapped deployments |
| **New packages (84 total)** | `evidence-graph`, `policy-engine`, `federated-compliance-mesh`, `federated-learning`, `quantum-resistant-crypto`, `natural-language-compliance`, `predictive-compliance`, and more — up from 79 in v10.0 |

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

GRC_Claw is a TypeScript/Go monorepo (84 packages, 288,053+ LOC) that turns compliance operations into code. The core is a **27,596-mapping crosswalk corpus** spanning 13 frameworks and 824 controls — the machine-readable layer that lets the SDK, CLI, VS Code extension, and Terraform provider all speak the same control language. An autonomous agent runtime (3-phase plan → act → verify, with trust scoring and auto-pause) ties it together for continuous compliance monitoring. The platform ships with **151 integration connectors**, **212 agent tools**, **137+ HTTP endpoints**, **27 CLI commands**, **PostgreSQL persistence**, **RBAC multi-tenancy**, **notification engine** (Slack/Email/Teams), **browser-based evidence collection** (Playwright), **blockchain-style hash chain audit trail**, **Evidence Graph object plane**, **compliance knowledge graph**, **predictive compliance engine**, **compliance marketplace**, **zero-trust audit trail**, **federated learning network**, **compliance intelligence API**, **autonomous compliance agent**, **compliance digital twin**, **quantum-resistant cryptography**, **natural language compliance querying**, and **compliance automation marketplace**.

The project follows an **open-core model**: GRC_Claw is MIT-licensed and ships **32 packages** to npm under the `@grc-claw/` scope. The commercial layer is **[A2Z SOC](https://a2zsoc.com)** — a hosted SOC platform that consumes the GRC_Claw engine for production security operations, SIEM, and enterprise multi-tenancy. You can run GRC_Claw fully standalone, or point it at A2Z SOC for the cloud control plane.

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

## Packages (40 listed · 44 private — 84 total)

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
| `@grc-claw/continuous-trust-engine` | Dynamic trust scoring across evidence, controls, agents, risk, and behavior | v1.0.0 |
| `@grc-claw/agent-collaboration` | Multi-agent collaboration sessions, capability matching, and consensus workflows | v1.0.0 |
| `@grc-claw/regulatory-change-management` | Regulatory source tracking, impact analysis, timelines, and remediation gaps | v1.0.0 |
| `@grc-claw/ai-governance` | AI system inventory, EU AI Act risk classification, assessments, and monitoring | v1.0.0 |
| `@grc-claw/compliance-knowledge-graph` | Living graph of frameworks, controls, evidence, threats, technologies, and posture | v1.0.0 |
| `@grc-claw/predictive-compliance` | Failure forecasting, risk scoring, trend analysis, and remediation recommendations | v1.0.0 |
| `@grc-claw/compliance-marketplace` | Proof-backed compliance pack publishing, discovery, installation, and ratings | v1.0.0 |
| `@grc-claw/zero-trust-audit` | Cryptographic audit trail with hash chains, Merkle proofs, and evidence export | v1.0.0 |
| `@grc-claw/evidence-graph` | Deterministic graph-object envelope, hashing, and snapshot builder for gateway/MCP proof paths | v1.0.0 |
| `@grc-claw/federated-learning` | Federated learning network for cross-org compliance pattern sharing with differential privacy | v1.0.0 |
| `@grc-claw/compliance-intelligence-api` | Real-time compliance intelligence from the network — trends, benchmarks, recommendations | v1.0.0 |
| `@grc-claw/autonomous-compliance-agent` | Self-healing compliance — detect, diagnose, remediate, verify automatically | v1.0.0 |
| `@grc-claw/compliance-digital-twin` | Virtual compliance twin — simulate, forecast, what-if analysis | v1.0.0 |
| `@grc-claw/quantum-resistant-crypto` | NIST FIPS 203/204 post-quantum cryptography (Kyber + Dilithium + hybrid mode) | v1.0.0 |
| `@grc-claw/natural-language-compliance` | Ask compliance questions in plain English — 7 intents, 8 frameworks, 8 languages | v1.0.0 |
| `@grc-claw/compliance-automation-marketplace` | Share, discover, and monetize compliance automations — ratings, reviews, versioning | v1.0.0 |
| `@grc-claw/real-time-compliance-monitor` | Live compliance dashboards, alerts, SLA monitoring, trend analysis | v1.0.0 |

The remaining 44 packages are private or pre-release. See the monorepo root `package.json` for the full workspace list.

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

## Sovereign Deployment Kit

`GRC_Claw/deploy/sovereign/` is a production-grade, data-residency-first deployment kit for regulated and air-gapped environments.

### What it ships

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Terraform** | AWS VPC, EC2, EIP, S3, IAM | Provisions an isolated cloud footprint — network, compute, static IP, encrypted object store, and least-privilege roles |
| **Docker Compose** | Supabase (self-hosted), Ollama, Nginx, Certbot | Full application stack with TLS termination, local LLM inference, and PostgreSQL-backed evidence storage |
| **Nightly S3 backup** | `scripts/` cron job | Encrypts and uploads the evidence vault to your private S3 bucket every night |
| **Nginx TLS** | `nginx/` config + Certbot | Automatic certificate issuance and renewal — no manual certificate management |

### Supported deployment targets

- **UAE / KSA** — data residency in AWS me-south-1 / me-central-1, compliant with UAE PDPL and KSA NDMO requirements
- **India** — data stored in AWS ap-south-1, aligned with DPDP Act locality requirements
- **EU financial services** — AWS eu-central-1 / eu-west-1, satisfying DORA, GDPR, and EBA cloud-outsourcing guidelines
- **US government / air-gapped** — no outbound internet required; Ollama handles all LLM inference locally; Supabase and evidence vault run entirely on-prem

### Quick start

```bash
# 1. Provision cloud infrastructure
cd GRC_Claw/deploy/sovereign
cp terraform.tfvars.example terraform.tfvars   # fill in your AWS account, region, key pair
terraform init && terraform apply

# 2. Launch the full application stack on the provisioned host
docker compose -f docker-compose.yml up -d

# 3. Bootstrap GRC_Claw against the sovereign stack
SOVEREIGN_MODE=true GRC_SOVEREIGN_URL=https://<your-eip> grc sovereign init
```

**Data residency guarantee:** with `SOVEREIGN_MODE=true` and the sovereign stack running, zero compliance data, evidence, or LLM prompts leave the designated cloud region or on-prem boundary. The `@grc-claw/connectors` package enforces this at the network layer.

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

## 2026 graph-backed acquisition moat priorities

The latest graph-first review of A2Z SOC + GRC_Claw shows the platform is already wide enough to compete with proprietary GRC suites and open-source compliance automation projects. The next move is not adding more disconnected pages. It is turning the existing route, package, connector, and evidence surface area into compounding infrastructure that gets stronger with every tenant, audit, pack, PR, agent action, and verifier interaction.

Recommended improvement order:

1. **Evidence Graph as the permanent system of record**
   - Promote `/api/platform/evidence-graph/*` and `/api/evidence-graph/*` from feature endpoints into the core data plane.
   - Every trust score, control test, questionnaire answer, vendor claim, PR gate result, SaaS finding, attack-surface scan, data-store classification, ZK bundle, and agent action should write graph nodes and signed edges.
   - Winning outcome: auditors and buyers can ask "why should I trust this claim?" and receive a scoped, cryptographically linked proof path instead of screenshots.

2. **Agent Policy Firewall before agent orchestration**
   - Make the gateway enforce scope, tenant boundaries, tool risk, approval thresholds, sandbox policy, idempotency, replay protection, receipt generation, and blast-radius scoring before any MCP/tool/browser/cloud action runs.
   - This is the irreplaceable layer above generic agent harnesses: harness teams optimize execution; GRC_Claw governs whether execution is allowed, provable, reversible, and audit-safe.

3. **CMMC / NIST 800-171 / ISO 42001 procurement cockpit**
   - Productize SSP, POA&M, SPRS scoring, CUI boundary mapping, AI system inventory, supplier evidence, SBOM/AI-BOM, FedRAMP inheritance, and agent receipts in one workflow.
   - This is the fastest route into defense industrial base, AI procurement, cybersecurity, and GRC budgets because it connects compliance proof to purchase permission.

4. **Signed pack marketplace with maintainer reputation**
   - Treat compliance packs like a regulated software supply chain: signed provenance, semantic versions, tests, control mappings, evidence collectors, remediation playbooks, dependency metadata, maintainer trust, verifier results, and revenue share.
   - This creates a Terraform Registry-style network effect for compliance: developers contribute packs, auditors verify packs, A2Z SOC monetizes trust distribution.

5. **Verifier network and audit rooms**
   - Add scoped verifier rooms for auditors, customers, brokers, MSPs, PE diligence teams, primes, and regulators.
   - The moat is not another dashboard. The moat is becoming the clearinghouse where external parties verify evidence without raw tenant data leakage.

6. **PR-to-proof engineering compliance**
   - Expand the GitHub PR Security Gate, VS Code Compliance Copilot, Terraform provider, and CLI into one developer compliance lane.
   - Every code change should be able to produce control mappings, evidence deltas, risk deltas, policy exceptions, and auditor-readable receipts.

7. **Live exposure collectors as evidence generators**
   - Convert SaaS Discovery, External Attack Surface Scan, Data Store Risk Classification, cloud connectors, SIEM/EDR sources, and browser evidence into first-class evidence graph writers.
   - This makes A2Z SOC more than a questionnaire platform: it becomes the continuously refreshed truth layer behind GRC claims.

8. **Risk economics everywhere**
   - Attach dollarized exposure, remediation cost, expected-loss reduction, audit-delay cost, and procurement-blocker severity to every evidence gap, failed test, vendor issue, agent exception, and control weakness.
   - Proprietary incumbents sell workflow. The differentiated product sells CFO-visible risk reduction.

9. **Agent memory and behavioral anomaly attestations**
   - Persist agent decisions, approvals, denied actions, drift signals, model/provider changes, policy overrides, and unusual behavior as signed governance receipts.
   - This creates a defensible AI governance primitive that stays relevant as agent frameworks change.

10. **Gateway modularity and contract hardening**
    - The graph shows `@grc-claw/gateway` as the central hotspot. Preserve the gateway as the product control plane, but split route registration, policy evaluation, agent dispatch, evidence graph writes, connector lifecycle, and verifier exports behind stable interfaces.
    - Add route contract tests and golden evidence fixtures so the gateway can grow without becoming fragile.

Execution focus:

- **This week:** make all new A2Z SOC proof-producing surfaces write Evidence Graph objects, not just local API responses.
- **Next 30 days:** ship Agent Policy Firewall v1 with signed receipts and route-level contract tests.
- **Next 60 days:** launch the CMMC/NIST 800-171/ISO 42001 procurement cockpit as the flagship paid lane.
- **Next 90 days:** publish the signed pack marketplace with verifier badges and maintainer reputation.
- **Next 6 months:** build the verifier network and anonymized benchmark layer so the platform compounds from real audit outcomes.

The strategic line: the code can be copied, isolated features can be copied, and dashboards can be outspent. The durable asset is the proof network: signed evidence, crosswalk semantics, policy-governed agent actions, verified packs, live exposure telemetry, procurement artifacts, auditor trust, and benchmark data accumulating in one graph.

---

## Post-v11.0 acquisition-grade moat: what to build next

The current platform now has the breadth most GRC startups spend years trying to assemble: open-source execution engine, hosted A2Z SOC control plane, 27,596 control mappings, 84 package families, PR security gates, policy-as-code, Evidence Graph object plane, post-quantum crypto, natural-language compliance, automation marketplace, real-time monitoring, sovereign deployment, and live proof-producing A2Z SOC surfaces.

The next step is to stop treating those capabilities as separate modules and turn them into a single compounding trust operating system.

Highest-leverage improvements, ordered by defensibility:

1. **Evidence Graph object plane as the canonical truth layer**
   - A2Z SOC now has a durable `evidence_graph_objects` layer with graph IDs, source references, object hashes, control mappings, confidence, and metadata.
   - GRC_Claw now mirrors this as a local `@grc-claw/evidence-graph` package with graph-object writes, deterministic hashes, normalized snapshots, and gateway/MCP tools.
   - Every package should emit graph objects: PR gates, policy engine, PQC scans, natural-language compliance answers, marketplace automations, real-time monitor alerts, sovereign deployment attestations, and agent receipts.

2. **Agent Policy Firewall as the default gateway runtime**
   - Make every tool call pass through one policy firewall before execution: tenant scope, role, approval threshold, sandbox policy, idempotency key, replay check, data boundary, blast radius, and expected control impact.
   - Emit three graph objects for every action: `intent`, `decision`, and `result`.
   - This is the layer agent harness companies will struggle to copy because it requires GRC semantics, evidence lineage, tenancy, auditability, and tool governance at once.

3. **Defense procurement cockpit**
   - Turn CMMC, NIST 800-171, FedRAMP, ISO 42001, AI inventory, SBOM, AI-BOM, CUI boundary, supplier risk, SSP, POA&M, SPRS, and sovereign deploy into one acquisition workflow.
   - The paid outcome is not “compliance dashboard”; it is “this vendor can pass procurement faster.”
   - Add exports for auditor packet, prime-contractor packet, board packet, insurance packet, and government buyer packet.

4. **Verifier network and scoped audit rooms**
   - Build external verifier rooms for auditors, customers, MSPs, brokers, PE diligence teams, primes, and regulators.
   - Each room should expose graph paths, redacted evidence, policy decisions, signed pack provenance, and risk economics without leaking raw tenant data.
   - This turns A2Z SOC into the trust clearinghouse while GRC_Claw remains the inspectable local engine.

5. **Signed automation marketplace**
   - Upgrade `@grc-claw/compliance-automation-marketplace` from catalog to supply chain: signed automations, test fixtures, required scopes, control mappings, evidence outputs, maintainer trust, semantic versions, rollback plan, and revenue share.
   - Let third parties sell automations that run only through the Agent Policy Firewall and write Evidence Graph objects.
   - The marketplace becomes stronger as more auditors, MSPs, and specialists contribute verified automations.

6. **Natural-language compliance with proof paths**
   - Every answer from `@grc-claw/natural-language-compliance` should include citations to controls, graph objects, evidence hashes, policy decisions, risk economics, and exportable verifier links.
   - The product should never merely “answer”; it should answer with an audit-safe graph path.

7. **Real-time compliance monitor as graph signal router**
   - `@grc-claw/real-time-compliance-monitor` should become the alert/event layer for graph changes: stale evidence, failed control test, SaaS risk spike, attack-surface regression, policy override, vendor issue, agent anomaly, or PQC migration blocker.
   - Every alert should carry control impact, procurement impact, owner, deadline, expected loss, and recommended automation.

8. **Quantum-resistant trust chain**
   - `@grc-claw/quantum-resistant-crypto` should be wired into long-term audit artifacts: ZK audit bundles, verifier rooms, procurement packets, sovereign deployments, and evidence graph exports.
   - The near-term value is migration readiness; the long-term value is durable proof for contracts, defense, finance, healthcare, and government buyers.

9. **Benchmark and outcome data network**
   - Aggregate opt-in, anonymized signals: audit duration, evidence freshness, remediation latency, control reuse, connector reliability, automation success rate, policy-denial rate, vendor response time, and procurement blockers.
   - These benchmarks become the compounding asset proprietary incumbents cannot buy quickly and open-source clones cannot bootstrap alone.

10. **Gateway modularization without weakening the gateway**
    - Preserve `@grc-claw/gateway` as the product control plane, but split stable submodules for route registry, policy firewall, graph writer, verifier export, marketplace execution, connector lifecycle, and agent dispatch.
    - Add golden contract tests for every gateway route and every MCP tool so the platform can grow without central-file fragility.

Immediate implementation ladder:

- **Week 1:** create `@grc-claw/evidence-graph` and make gateway `evidence_graph.*` use the same graph-object envelope as A2Z SOC. **Implemented first slice:** HTTP `/api/evidence-graph/*` and agent `evidence_graph.*` now share deterministic graph-object snapshots.
- **Week 2:** ship Agent Policy Firewall v1 for gateway + MCP tools, with intent/decision/result receipts.
- **Week 3:** make PR gate, policy engine, PQC scan, natural-language compliance, marketplace automations, and real-time monitor write graph objects.
- **Week 4:** launch the defense procurement cockpit around CMMC/NIST 800-171/ISO 42001.
- **Weeks 5-8:** ship scoped verifier rooms and signed automation marketplace revenue share.
- **Quarter 2:** add benchmark network APIs and anonymized outcome analytics.

The practical acquisition thesis: buyers do not acquire “another GRC app.” They acquire a trust graph, a control-mapping corpus, a verifier network, a marketplace, a governed agent runtime, and the longitudinal evidence/outcome dataset that lets them dominate procurement, audit, insurance, and AI governance workflows.

---

## Phase 35 graph-first moat review: A2Z SOC + GRC_Claw beyond acquisition-grade GRC

This review used the codebase-memory graph-first workflow before falling back to targeted repository reads. The graph indexer discovered **2,792 platform files**, extracted **38,410 graph nodes**, **46,204 call edges**, **25,243 usage edges**, and **924 route nodes**, but the local graph cache failed during the final dump phase. That means the platform is visibly large enough for graph-native governance, but the codebase graph itself should now become a first-class product and QA artifact rather than an occasional developer aid.

The strategic reading is clear: A2Z SOC and GRC_Claw already have the breadth of a serious acquisition target. The next step is not more disconnected pages, more dashboards, or more framework badges. The next step is turning the platform into a **trust operating system**: an evidence graph, a governed agent runtime, a defense procurement workflow, a verifier network, and a signed automation marketplace that compound together.

Highest-leverage improvements, ordered by monopoly-grade defensibility:

1. **Make the Evidence Graph the product kernel**
   - Every A2Z SOC API, cron job, GRC_Claw package, gateway tool, PR gate, marketplace automation, risk feed, vendor event, employee lifecycle event, and immutable audit event should emit the same graph-object envelope.
   - Add a schema registry for graph object types, signed migrations, golden fixtures, and compatibility tests between A2Z SOC `evidence_graph_objects` and `@grc-claw/evidence-graph`.
   - The moat is not “we store evidence.” The moat is “every trust claim has a deterministic, inspectable proof path.”

2. **Ship Agent Policy Firewall before adding more agent features**
   - Route every MCP/tool/browser/cloud/CLI action through one firewall: tenant scope, role, approval threshold, sandbox policy, connector risk, data boundary, blast radius, replay protection, idempotency, and expected control impact.
   - Emit `intent`, `decision`, `execution`, `result`, and `verifier_receipt` graph objects for every action.
   - Agent harness teams can copy orchestration. They will struggle to copy audit-grade authorization, evidence lineage, cross-framework semantics, and external verifier trust in one layer.

3. **Turn CMMC / NIST 800-171 / ISO 42001 into the flagship procurement cockpit**
   - Package CUI boundary mapping, SSP, POA&M, SPRS scoring, supplier evidence, AI system inventory, AI-BOM, SBOM, FedRAMP inheritance, incident history, agent receipts, and sovereign deployment into one buyer-ready workflow.
   - The paid promise should be: **pass procurement faster, answer prime-contractor due diligence faster, and prove agentic AI governance before competitors can assemble the packet.**
   - This is the strongest wedge into defense, aerospace, critical infrastructure, MSP, PE diligence, and AI governance budgets.

4. **Create verifier rooms as the commercial network effect**
   - Auditors, customers, MSPs, brokers, PE diligence teams, primes, insurers, and regulators should get scoped rooms that expose graph paths, redacted evidence, policy decisions, signed pack provenance, and risk economics without leaking raw tenant data.
   - Every verifier action should create its own signed receipt and improve the trust score.
   - A dashboard can be cloned; a verifier network with historical outcomes and trust relationships is much harder to copy.

5. **Upgrade the automation marketplace into a regulated supply chain**
   - Treat every automation as a signed package with required scopes, test fixtures, control mappings, graph outputs, rollback plan, maintainer reputation, semantic versioning, and revenue share.
   - Only allow marketplace automations to run through the Agent Policy Firewall and write Evidence Graph objects.
   - This creates the Terraform Registry / npm / GitHub Actions equivalent for compliance operations, with A2Z SOC owning trust distribution.

6. **Build the benchmark and outcome data network**
   - Aggregate opt-in anonymized signals: audit duration, evidence freshness, remediation latency, control reuse, vendor response time, failed automation rate, policy denial rate, procurement blocker frequency, and verifier acceptance rate.
   - Attach these benchmarks to every recommendation: “this control gap usually delays SOC 2 by 11 days,” “this vendor issue is a common CMMC blocker,” “this automation reduced evidence collection time by 42%.”
   - Proprietary incumbents have workflow data; the durable asset is outcome data tied to proof paths.

7. **Make natural-language compliance answer with proof, not prose**
   - GRC Copilot and `@grc-claw/natural-language-compliance` should never return unsupported advice.
   - Every answer should include control citations, graph object IDs, evidence hashes, policy decisions, risk economics, remediation owner, verifier-room export, and confidence provenance.
   - This turns AI from a support layer into an audit-safe query interface over the trust graph.

8. **Use immutable audit and post-quantum readiness as the long-horizon trust chain**
   - Wire immutable audit trail, RFC 3161 timestamps, ZK audit bundles, and `@grc-claw/quantum-resistant-crypto` into every long-lived procurement artifact.
   - Defense, finance, healthcare, and government buyers care about proof durability. Make “trust claims survive platform, model, vendor, and cryptographic era changes” a core message.

9. **Turn the codebase graph into a dogfooded governance primitive**
   - Fix the codebase-memory dump failure and publish a local/private graph manifest during CI: route counts, centrality hotspots, dead routes, package dependency drift, ownerless APIs, and evidence-writer coverage.
   - Add a “graph coverage” gate: new API routes and gateway tools should fail CI unless they have owner metadata, tests, navigation intent, and Evidence Graph emission.
   - This makes the platform itself a living demonstration of graph-governed software assurance.

10. **Collapse navigation around durable buyer jobs**
    - A2Z SOC should prioritize evergreen workflows in the sidebar: Evidence Graph, Agent Policy Firewall, Defense Procurement, Verifier Rooms, Trust Score, Audit Trail, Vendor Risk, Employee Lifecycle, Predictive Compliance, and Automation Marketplace.
    - Pages that are demos, seasonal campaigns, or duplicated dashboards should move under hubs or be hidden from primary navigation.
    - The product should feel like a control plane, not a museum of features.

Immediate execution ladder:

- **48 hours:** fix codebase-memory dump/index reliability, add Evidence Graph schema registry, and add graph-object fixtures for the v12.0-D A2Z SOC surfaces: Predictive Compliance, Employee Lifecycle, Vendor Risk Feed, and Immutable Audit Trail.
- **7 days:** ship Agent Policy Firewall v1 inside `@grc-claw/gateway` and A2Z SOC platform APIs, with intent/decision/result receipts.
- **14 days:** make GRC Copilot answer only through proof paths: controls, evidence hashes, graph IDs, risk economics, and verifier export.
- **30 days:** launch the CMMC / NIST 800-171 / ISO 42001 procurement cockpit as the flagship paid workflow.
- **60 days:** launch verifier rooms and signed automation marketplace revenue share.
- **90 days:** publish anonymized benchmark APIs and procurement outcome analytics.

The acquisition-grade thesis: the platform becomes difficult to compete with when A2Z SOC owns the hosted trust network and GRC_Claw owns the inspectable local execution engine. Competitors can copy screens. They cannot quickly copy the accumulated graph of controls, evidence, agent decisions, verifier receipts, marketplace automations, procurement packets, and real audit outcomes.

---

## Phase 36 graph-first review: from broad platform to category-control system

This phase used the live codebase-memory graph before editing the roadmap. The current A2Z SOC + GRC_Claw workspace indexed to **24,873 graph nodes**, **76,888 edges**, **575 route nodes**, and high-cohesion GRC_Claw clusters around the gateway, agent dispatch, framework packs, evidence graph, marketplace, digital twin, predictive compliance, cloud connectors, Helm, Terraform, and MCP surfaces.

The important finding is blunt: breadth is no longer the scarce asset. The scarce asset is **proof density**. A2Z SOC and GRC_Claw should now optimize every product surface around one question: can a buyer, auditor, prime contractor, regulator, insurer, or AI governance team verify the claim without trusting the UI?

Priority improvements to exceed proprietary and open-source GRC projects:

1. **Make Evidence Graph coverage a release gate**
   - Every new route, gateway tool, MCP method, connector, marketplace automation, agent action, control test, risk forecast, and export should emit a deterministic graph object.
   - CI should report graph coverage: routes with proof paths, tools with policy receipts, controls with evidence writers, packs with signed provenance, and exports with verifier links.
   - This turns engineering velocity into compounding trust assets instead of feature sprawl.

2. **Turn Agent Policy Firewall into the runtime moat**
   - Treat MCP tools, browser agents, cloud connectors, CLI commands, SOAR playbooks, and remediation bots as untrusted actuators until the firewall approves them.
   - Require tenant scope, role, sandbox policy, idempotency key, replay window, tool risk, blast radius, data boundary, approval threshold, expected control impact, and rollback plan.
   - Emit `intent`, `decision`, `execution`, `result`, and `verifier_receipt` objects for every action.

3. **Package CMMC / NIST 800-171 / ISO 42001 as the flagship paid workflow**
   - Build the defense procurement cockpit around CUI boundary, SSP, POA&M, SPRS, FedRAMP inheritance, SBOM, AI-BOM, AI inventory, supplier risk, incident history, sovereign deployment, and agent receipts.
   - The buyer promise should be: **shorten procurement, answer primes faster, and prove agentic AI governance with audit-safe evidence.**
   - A2Z SOC should own the hosted cockpit; GRC_Claw should own the local/offline execution engine.

4. **Make GRC Copilot proof-native**
   - Natural-language compliance answers should be generated from graph paths, not loose prose.
   - Every answer should cite control IDs, framework mappings, evidence hashes, graph object IDs, policy decisions, risk economics, owner, deadline, and verifier-room export.
   - Unsupported answers should degrade into “missing evidence” tasks instead of confident text.

5. **Upgrade the marketplace into a regulated automation supply chain**
   - Every pack and automation should include signed provenance, maintainer identity, required scopes, test fixtures, control mappings, graph outputs, rollback plan, semantic versioning, dependency policy, verifier score, and revenue share.
   - Marketplace code should only execute through the Agent Policy Firewall and should only publish value when it writes Evidence Graph objects.
   - This is the compliance equivalent of Terraform Registry plus GitHub Actions plus auditor trust.

6. **Create verifier rooms as the commercial network**
   - Auditors, customers, primes, MSPs, brokers, insurers, PE diligence teams, and regulators should get scoped rooms that expose graph paths, redacted evidence, signed receipts, control crosswalks, risk economics, and export packets.
   - Every verifier review, acceptance, rejection, and comment should feed back into trust score and benchmark intelligence.
   - The network effect is not the account; it is the history of third-party verification.

7. **Build benchmark intelligence from outcomes, not vanity metrics**
   - Aggregate opt-in anonymized metrics: audit cycle time, evidence freshness, remediation latency, vendor response time, procurement blocker frequency, policy denial rate, automation success, verifier acceptance, and control reuse.
   - Attach benchmarks to product recommendations and Copilot answers.
   - This becomes a proprietary dataset that open-source projects cannot bootstrap and incumbents cannot buy instantly.

8. **Use sovereign, offline, and post-quantum proof as the long-horizon trust chain**
   - Wire zero-trust audit trail, RFC 3161 timestamps, ZK bundles, verifiable credentials, sovereign deployment, local models, and post-quantum crypto planning into procurement packets and verifier rooms.
   - The message for regulated buyers is durable: trust claims should survive vendor change, model change, cloud boundary change, and cryptographic-era change.

9. **Simplify navigation around durable buyer jobs**
   - Primary A2Z SOC navigation should bias toward Evidence Graph, Agent Policy Firewall, Defense Procurement, Verifier Rooms, Trust Score, Audit Trail, Vendor Risk, Employee Lifecycle, Predictive Compliance, Automation Marketplace, GRC Copilot, and Sovereign Deployment.
   - Duplicate demos, seasonal pages, and isolated feature pages should roll up under hubs.
   - The platform should feel like a mission control system, not a feature museum.

Immediate execution order:

- **48 hours:** add graph coverage checks and proof-path fixtures for gateway tools, A2Z SOC APIs, and the most valuable paid pages. **Implemented first slice:** `npm run graph:coverage` now verifies required graph/proof packages, Evidence Graph HTTP routes, `evidence_graph.*` gateway tools, action-ledger lifecycle events, assurance envelope receipts, and the CMMC / NIST 800-171 / ISO 42001 roadmap wedge.
- **7 days:** make Agent Policy Firewall v1 mandatory for gateway/MCP tool execution and emit receipts for every action.
- **14 days:** make GRC Copilot proof-native with missing-evidence fallbacks and verifier-room export.
- **30 days:** ship the CMMC / NIST 800-171 / ISO 42001 procurement cockpit as the paid flagship.
- **60 days:** launch verifier rooms and signed automation marketplace revenue share.
- **90 days:** expose benchmark intelligence across dashboards, Copilot, exports, and sales packets.

The category-control thesis: proprietary competitors can outspend UI development, and open-source projects can copy utilities. What compounds defensibly is the graph of signed evidence, governed agent actions, verified packs, procurement packets, third-party verifier outcomes, and benchmark intelligence. A2Z SOC should own the hosted trust network; GRC_Claw should be the open, inspectable engine that proves the network is real.

---

## Phase 37 graph-first monopoly moves: beyond acquired proprietary GRC and open-source clones

This review used the healthy codebase-memory graph cache before editing the roadmap. The combined A2Z SOC platform now indexes at **24,990 graph nodes**, **76,948 edges**, **575 route nodes**, and high-fan-in product primitives such as `MainLayout`, `GrcHubNav`, `useSeo`, GRC pages, PLG APIs, evidence surfaces, trust-center routes, and marketplace/procurement pages. The standalone GRC_Claw graph indexes at **3,987 nodes**, **10,518 edges**, **36 route nodes**, and dense clusters around `gateway`, `agent-runtime`, `evidence`, `a2z-connector`, `compliance-orchestrator`, `cloud-connectors`, `frameworks`, `compliance-copilot`, and `skill-executor`.

The market lesson from recent cybersecurity consolidation is simple: buyers pay premium prices for platforms that become control planes, not tools. Cloud security consolidation rewards multi-cloud visibility and risk correlation; AI security consolidation rewards runtime protection and governance; GRC incumbents compete around trust intelligence, privacy, third-party risk, and AI governance workflows. A2Z SOC and GRC_Claw should therefore avoid becoming another dashboard bundle. The monopoly path is to become the **proof and procurement operating system for agentic AI, cybersecurity, and GRC**.

Highest-leverage improvements, ordered by defensibility:

1. **Verified Trust Transaction Protocol**
   - Create one canonical transaction envelope for every trust event: actor, tenant, tool, policy decision, evidence hash, control mapping, data boundary, idempotency key, risk score, verifier scope, and export format.
   - Use it across A2Z SOC APIs, GRC_Claw gateway tools, MCP calls, Copilot answers, marketplace automations, procurement packets, audit rooms, and benchmark analytics.
   - This becomes the Stripe-like primitive for compliance: a transaction ledger for trust, not a pile of attestations.

2. **Agent Policy Firewall as a paid default, not a feature**
   - Make every AI/MCP/browser/cloud/CLI/SOAR action pass through risk scoring, scope enforcement, sandbox policy, approval thresholds, replay prevention, rollback metadata, and receipt generation.
   - Publish policy-firewall coverage in `npm run graph:coverage`: routes covered, tools covered, denied actions, missing receipts, and evidence writers.
   - Agent harness teams will build orchestration; A2Z SOC should own the regulated execution boundary they need to sell into enterprise, defense, finance, and healthcare.

3. **Defense and regulated procurement cockpit**
   - Fuse CMMC, NIST 800-171, ISO 42001, NIST AI RMF, SOC 2, FedRAMP inheritance, SBOM, AI-BOM, CUI boundary, supplier risk, SPRS-style scoring, SSP, POA&M, and sovereign deployment into one buyer workflow.
   - Add “packet modes”: prime contractor, auditor, insurer, board, PE diligence, government buyer, and MSP/vCISO.
   - The commercial outcome is not compliance posture; it is faster procurement, shorter diligence cycles, fewer questionnaires, and proof that agentic AI is governed.

4. **Proof-native GRC Copilot**
   - Copilot should answer by compiling graph paths, not writing prose. Every answer should include controls, mappings, evidence hashes, policy receipts, freshness, owner, risk economics, and verifier-room export.
   - If proof is missing, Copilot should create a missing-evidence task, recommend the connector or marketplace automation, and show which buyer packet is blocked.
   - This makes the AI layer defensible because it depends on proprietary evidence history and verifier outcomes.

5. **Signed automation and evidence marketplace**
   - Every marketplace pack should ship with signed provenance, maintainer identity, required scopes, test fixtures, evidence outputs, rollback plan, semantic versioning, compatibility matrix, verifier score, and revenue share.
   - Marketplace automation must execute only through the Agent Policy Firewall and must emit Verified Trust Transactions.
   - This turns GRC_Claw into the Terraform Registry / GitHub Actions / npm equivalent for regulated compliance work, with A2Z SOC owning distribution and verification.

6. **Verifier-room network**
   - Build scoped rooms for auditors, customers, primes, MSPs, insurers, PE firms, regulators, and internal boards.
   - Verifiers should see graph paths, redacted evidence, signed receipts, pack provenance, control crosswalks, risk economics, benchmark comparisons, and acceptance/rejection history.
   - The network effect is the accumulated third-party verification record, not the UI.

7. **Outcome benchmark intelligence**
   - Aggregate opt-in anonymized metrics: audit cycle time, procurement delay, evidence freshness, remediation latency, vendor response time, automation success, policy denial rate, verifier acceptance rate, deal influence, and control reuse.
   - Attach benchmarks to every recommendation: “this control gap blocks prime-contractor packets,” “this evidence class usually expires before audit,” “this automation reduces collection time,” “this vendor response is below peer median.”
   - This is the dataset that proprietary incumbents cannot buy quickly and open-source projects cannot bootstrap alone.

8. **Acquirer-grade due diligence API**
   - Add an export that lets a strategic acquirer or enterprise buyer inspect platform value without reverse engineering the repo: package graph, route graph, proof coverage, recurring evidence objects, marketplace supply, benchmark density, control corpus, verifier activity, and tenant-safe revenue influence.
   - The API should produce a redacted “why this platform is hard to clone” packet.
   - This makes the platform legible to buyers, partners, auditors, and enterprise procurement teams.

9. **Sovereign and post-quantum proof lane**
   - Wire local models, Ollama/private LLMs, sovereign deployment, immutable audit, RFC 3161 timestamps, ZK bundles, verifiable credentials, and post-quantum crypto planning into every long-lived packet.
   - The durable message: trust artifacts survive model churn, cloud churn, vendor churn, regulator churn, and cryptographic-era change.

10. **Navigation reduction around the buyer operating system**
    - Primary A2Z SOC navigation should collapse around Evidence Graph, Agent Policy Firewall, GRC Copilot, Defense Procurement, Verifier Rooms, Trust Score, Audit Trail, Vendor Risk, AI Governance, Automation Marketplace, Benchmark Intelligence, and Sovereign Deployment.
    - Everything else should live under hubs or be treated as proof-path support.
    - The product should feel like the cockpit for trust operations, not an archive of every shipped experiment.

Immediate implementation ladder:

- **48 hours:** extend `npm run graph:coverage` from existence checks to coverage ratios: route-to-proof, tool-to-policy, Copilot-to-evidence, marketplace-to-signed-pack, procurement-to-export.
- **7 days:** implement Verified Trust Transaction schema and make gateway/MCP tools emit it behind a compatibility flag.
- **14 days:** make GRC Copilot refuse unsupported answers and produce missing-evidence tasks with suggested connectors/automations.
- **30 days:** ship the CMMC / NIST 800-171 / ISO 42001 procurement cockpit as a paid flagship workflow with packet exports.
- **60 days:** launch verifier rooms and signed automation marketplace revenue share.
- **90 days:** launch benchmark intelligence APIs and show benchmarks inside Copilot, dashboards, packet exports, and GTM pages.

The monopoly-grade thesis: A2Z SOC should own the hosted trust network; GRC_Claw should own the open, inspectable execution engine. Competitors can copy a control catalog, policy generator, chatbot, or dashboard. They cannot quickly copy a longitudinal graph of signed trust transactions, governed agent actions, verified automations, procurement packet outcomes, auditor acceptances, benchmark intelligence, and sovereign/offline proof paths.

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
