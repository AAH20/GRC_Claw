# GRC_Claw Changelog

All notable changes documented here. Format: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) — [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] — 2026-06-26

### Summary
First stable release. API contract locked. All 15 core packages now have `publishConfig.access: public` and are ready for npm publish. Breaking changes from 0.x will be tracked from this version forward.

### Added
- **`@grc-claw/cli`** — `grc scan`, `grc report`, `grc frameworks list`, `grc doctor` (developer-led adoption flywheel)
- **`@grc-claw/registry`** — GRC Registry with 8 built-in framework packs, PackVerifier, trust scoring, `grc add <framework>` install model
- **Federated Compliance Attestation Mesh** — `@grc-claw/federated-compliance-mesh` live, ZK-attested cross-org proofs published to `api/compliance-mesh`
- **Regulatory Intelligence Feed** — `api/regulatory-intelligence` endpoint with 10 monitored regulatory sources, alert digest, impact analysis
- **AIMS Vendor Gap Report API** — `api/aims-report` serving scored gap matrix for Anthropic, OpenAI, Google, Cursor, OpenClaw (graded against ISO 42001 clauses + EU AI Act articles)
- **GRC Bible Knowledge API** — `api/grc/knowledge` exposing `methodologyContent.ts` (15,929 LOC GRC knowledge base) as queryable REST
- **GitHub App Webhook** — `api/github-app/webhook` for compliance-copilot PR gates (wires to GitHub Marketplace when `GITHUB_APP_ID` + `GITHUB_APP_PRIVATE_KEY` are set)
- **Multi-Tenant Supabase RLS** — `scripts/supabase-multi-tenant-rls.sql` adds `organizations`, `organization_members`, `api_keys`, `compliance_controls`, `evidence_artifacts`, `compliance_snapshots`, `gateway_events` tables with full RLS
- **WebSocket SOC Push** — `packages/gateway/src/server.ts` now broadcasts normalized SIEM events to authenticated `subscribe:soc_events` WebSocket clients in real-time
- **Control Evidence Deduplication** — `@grc-claw/compliance-orchestrator` expanded from 7 to 70+ cross-framework equivalency mappings (ISO 27001 ↔ ISO 42001, SOC 2, NIST CSF, GDPR, HIPAA, PCI DSS, DORA, NIS2, FedRAMP, EU AI Act)
- **`publishConfig.access: public`** on all 15 core packages
- **CHANGELOG.md** (this file)

### Changed
- All 44 packages: version `0.1.0` → `1.0.0` (stable API contract)
- README roadmap: speculative phases 25-33 moved to `speculative/FUTURE_RESEARCH.md`
- README roadmap: replaced speculative items with concrete 90-day delivery targets
- `@grc-claw/registry` added to workspace packages

### Security
- 3-phase exec policy (allowlist → approval → sandbox) — unchanged, audited
- WebSocket SOC push requires authenticated `X-GRC-Claw-Token` before subscribing
- GitHub App webhook verifies `x-hub-signature-256` HMAC-SHA256 before processing
- Supabase RLS: all new tables have row-level security enabled; service role bypass only for trusted server functions
- API keys stored as SHA-256 hash only — plaintext never persisted

## [0.1.0] — 2026-01-01

### Added
- Initial release — core gateway, agent-runtime, frameworks, evidence, ingest, aims, connectors, skill-executor, a2z-connector
- 3-phase exec policy (allowlist → approval → sandbox)
- ISO 42001 AIMS vendor gap matrix (8 vendor-graded rows)
- 9-source SIEM normalizers (Wazuh, Suricata, Snort, Elastic, UFW, GuardDuty, Sentinel, Chronicle)
- BYOC LLM connectors (OpenAI, Anthropic, Gemini, Ollama, OpenRouter)
- Operator console (Vite + React, Gemini + Cursor Auto chat)
- Docker Compose + systemd + Helm chart deployment
- OpenTelemetry observability + Prometheus metrics
- AI-BOM generator (SPDX/CycloneDX-aligned)
