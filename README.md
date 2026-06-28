# GRC_Claw

Open-source GRC automation engine — 67 packages, 27,596 control mappings, autonomous agent, Terraform provider, VS Code extension

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![npm](https://img.shields.io/badge/npm-%40grc--claw-red?logo=npm)](https://www.npmjs.com/search?q=%40grc-claw)
[![Node](https://img.shields.io/badge/node-%3E%3D20-brightgreen)](package.json)
[![GitHub](https://img.shields.io/badge/GitHub-AAH20%2FGRC__Claw-181717?logo=github)](https://github.com/AAH20/GRC_Claw)
[![A2Z SOC](https://img.shields.io/badge/A2Z%20SOC-a2zsoc.com-red)](https://a2zsoc.com)

---

## What it is

GRC_Claw is a TypeScript/Go monorepo (67 packages, 288,053 LOC) that turns compliance operations into code. The core is a **27,596-mapping crosswalk corpus** spanning 13 frameworks and 824 controls — the machine-readable layer that lets the SDK, CLI, VS Code extension, and Terraform provider all speak the same control language. An autonomous agent runtime (3-phase plan → act → verify, with trust scoring and auto-pause) ties it together for continuous compliance monitoring.

The project follows an **open-core model**: GRC_Claw is MIT-licensed and ships 26 packages to npm under the `@grc-claw/` scope. The commercial layer is **[A2Z SOC](https://a2zsoc.com)** — a hosted SOC platform that consumes the GRC_Claw engine for production security operations, SIEM, and enterprise multi-tenancy. You can run GRC_Claw fully standalone, or point it at A2Z SOC for the cloud control plane.

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

## Packages (26 published · 41 private)

| Package | Description | Version |
|---------|-------------|---------|
| `@grc-claw/sdk` | TypeScript SDK for A2Z SOC platform | v0.8.0 |
| `@grc-claw/cli` | GRC CLI — 16 commands | v0.8.0 |
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

The remaining 41 packages are private or pre-release. See the monorepo root `package.json` for the full workspace list.

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

The `terraform-provider-grc` (Go implementation) lets you manage GRC resources as infrastructure code.

**Resources:**

- `grc_control` — declare a compliance control and its metadata
- `grc_evidence` — attach an evidence artifact to a control with hash lineage

```hcl
terraform {
  required_providers {
    grc = {
      source  = "registry.terraform.io/a2zsoc/grc"
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

`@grc-claw/cli` ships 16 commands:

```bash
grc init                    # Scaffold grcfile.yaml + GitHub Actions workflow
grc scan .                  # Codebase compliance scan
grc plan                    # Generate compliance remediation plan
grc apply                   # Apply plan to GRC_Claw
grc audit                   # Full compliance audit with evidence
grc status                  # Current compliance posture
grc drift                   # Detect compliance drift from baseline
grc diff                    # Crosswalk delta between git refs or frameworks
grc report                  # Generate evidence report
grc doctor                  # Environment checks (add --fix to auto-remediate)
grc iac-scan .              # Terraform / Kubernetes compliance scan
grc pqc-scan .              # Post-quantum cryptography migration scan
grc ai-bom generate         # AI Bill of Materials (EU AI Act Article 53)
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

## MCP server

`@grc-claw/mcp-server` exposes GRC_Claw capabilities to Claude and other MCP-compatible AI assistants. Point your MCP client at the server to query controls, retrieve crosswalk mappings, trigger scans, and read evidence — all from within your AI assistant's context.

---

## A2Z SOC integration

[A2Z SOC](https://a2zsoc.com) is the commercial platform built on top of GRC_Claw. It adds:

- Hosted crosswalk API with the full 27,596-mapping corpus
- Multi-tenant enterprise SIEM and SOC operations
- Managed PostgreSQL evidence store
- Production alerting, dashboards, and reporting

```bash
A2Z_SOC_BASE_URL=https://a2zsoc.com
A2Z_SOC_API_KEY=<your-key>
```

See [a2zsoc.com](https://a2zsoc.com) for pricing and API key self-serve.

---

## Contributing

GRC_Claw is MIT-licensed. PRs welcome — framework packs, language rules for the VS Code extension, additional Terraform resources, and connector implementations are the highest-value contributions.

```bash
git clone https://github.com/AAH20/GRC_Claw.git
cd GRC_Claw
npm install && npm run build
npm run test:comprehensive
```

Repository: [github.com/AAH20/GRC_Claw](https://github.com/AAH20/GRC_Claw)

---

## License

[MIT](LICENSE)
