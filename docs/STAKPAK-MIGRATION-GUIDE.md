# Stakpak → A2Z SOC + GRC_Claw Migration Guide

> **Version:** 1.0 | **Last Updated:** 2026-07-17

This guide walks Stakpak users through migrating to A2Z SOC (hosted control plane) and GRC_Claw (open-source GRC engine). Expect a 1–3 day migration depending on data volume and framework scope.

---

## Table of Contents

1. [Overview: Why Migrate](#1-overview-why-migrate)
2. [Prerequisites](#2-prerequisites)
3. [Step-by-Step Migration](#3-step-by-step-migration)
4. [Feature Mapping](#4-feature-mapping)
5. [Data Migration](#5-data-migration)
6. [Configuration Migration](#6-configuration-migration)
7. [Testing & Verification](#7-testing--verification)
8. [Rollback Plan](#8-rollback-plan)
9. [FAQ](#9-faq)
10. [Support](#10-support)

---

## 1. Overview: Why Migrate

| Capability | Stakpak | A2Z SOC + GRC_Claw |
|---|---|---|
| **Framework coverage** | Limited subset | 13+ frameworks, 824+ controls, 27,596 cross-framework mappings |
| **AI governance** | None | ISO 42001, NIST AI RMF, EU AI Act, AI BOM |
| **Evidence model** | Proprietary | SHA-256 hash chain, RFC 3161 timestamps, zero-trust audit trail |
| **Agent automation** | None | 3-phase autonomous agent (plan → act → verify), 212+ tools |
| **Deployment** | SaaS only | Local-first, sovereign/air-gap, Docker Compose, Terraform |
| **MCP integration** | None | Native MCP server for Claude and AI assistants |
| **Procurement** | Basic questionnaires | CMMC passports, defense procurement cockpit, broker trust desk |
| **Pricing** | Per-seat SaaS | Open-source engine (MIT) + optional hosted A2Z SOC tiers |

---

## 2. Prerequisites

### Required before migrating

| Item | Requirement | Verify |
|---|---|---|
| Node.js | 20+ | `node -v` |
| npm | 10+ | `npm -v` |
| Git | 2.30+ | `git -v` |
| PostgreSQL | 15+ (optional, for persistence) | `psql -V` |
| Stakpak account | Active with admin access | Stakpak dashboard |
| Export permissions | Stakpak API key or data export rights | Stakpak settings |

### Recommended

- Docker (for containerized deployment)
- Terraform (for infrastructure-as-code)
- A2Z SOC account at [a2zsoc.com](https://a2zsoc.com) (for hosted control plane)

---

## 3. Step-by-Step Migration

### Step 1: Export Stakpak Configuration

Export your Stakpak data before decommissioning.

```bash
# 1. Export your framework controls
# In Stakpak: Settings → Export → Controls → JSON
# Save as: stakpak-controls.json

# 2. Export evidence records
# In Stakpak: Evidence → Export All → JSON
# Save as: stakpak-evidence.json

# 3. Export audit trails
# In Stakpak: Audit Log → Export → CSV or JSON
# Save as: stakpak-audit-trail.json

# 4. Export policies and rules
# In Stakpak: Policies → Export → YAML or JSON
# Save as: stakpak-policies.json
```

If Stakpak provides a CLI or API, automate the export:

```bash
# Example: Using Stakpak API (adjust endpoint to match their docs)
curl -s -H "Authorization: Bearer $STAKPAK_API_KEY" \
  "https://api.stakpak.com/v1/controls" > stakpak-controls.json

curl -s -H "Authorization: Bearer $STAKPAK_API_KEY" \
  "https://api.stakpak.com/v1/evidence" > stakpak-evidence.json

curl -s -H "Authorization: Bearer $STAKPAK_API_KEY" \
  "https://api.stakpak.com/v1/audit-log" > stakpak-audit-trail.json
```

### Step 2: Install A2Z SOC + GRC_Claw

```bash
# Install the CLI globally
npm install -g @grc-claw/cli

# Verify installation
grc version

# Scaffold a new project
grc init

# This creates:
# - grcfile.yaml (project configuration)
# - .github/workflows/grc-scan.yml (GitHub Actions integration)
# - .grc/ (local evidence directory)
```

**Alternative: Docker Compose deployment**

```bash
git clone https://github.com/AAH20/GRC_Claw.git
cd GRC_Claw

# Start the gateway
docker compose -f deploy/docker-compose.yml up -d

# Verify health
curl -s http://127.0.0.1:18791/health
```

**Alternative: Sovereign/air-gap deployment**

```bash
# For regulated environments
SOVEREIGN_MODE=true grc sovereign init
docker compose -f docker-compose.sovereign.yml up -d
```

### Step 3: Import Configuration

Map your Stakpak controls to GRC_Claw framework packs.

```bash
# List available framework packs
grc frameworks list
```

**Create `grcfile.yaml` with your target frameworks:**

```yaml
version: "1.0"
project: "migrated-from-stakpak"
frameworks:
  - soc2
  - iso27001
  - nist-csf
  - hipaa        # Add as needed
  - pci-dss      # Add as needed
  - gdpr         # Add as needed
scan:
  paths:
    - ./src
    - ./infra
    - ./docs
  exclude:
    - node_modules
    - .git
    - dist
iac:
  paths:
    - ./terraform
    - ./kubernetes
```

**Import Stakpak controls using the SDK:**

```typescript
import { readFileSync } from 'node:fs';
import { ComplianceControl } from '@grc-claw/core';

// Read your exported Stakpak data
const stakpakData = JSON.parse(
  readFileSync('stakpak-controls.json', 'utf-8')
);

// Map Stakpak controls to GRC_Claw format
const controls: ComplianceControl[] = stakpakData.map((c: any) => ({
  id: `stakpak-${c.id}`,
  controlCode: c.code,
  title: c.name,
  frameworkCode: c.framework.toLowerCase().replace(/\s+/g, '-'),
  domain: c.domain || 'General',
  description: c.description,
}));

console.log(`Mapped ${controls.length} controls from Stakpak`);
```

**Use the crosswalk engine for automatic mapping:**

```typescript
import { crosswalkControl } from '@grc-claw/framework-crosswalk';

// Find GRC_Claw equivalents for Stakpak controls
for (const stakpakCtrl of stakpakData) {
  const equivalents = crosswalkControl(stakpakCtrl.code);
  if (equivalents.length > 0) {
    console.log(
      `${stakpakCtrl.code} → ${equivalents.map((e: any) => e.targetCode).join(', ')}`
    );
  }
}
```

### Step 4: Migrate Evidence

```typescript
import { readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';

// Read exported Stakpak evidence
const stakpakEvidence = JSON.parse(
  readFileSync('stakpak-evidence.json', 'utf-8')
);

// Convert to GRC_Claw evidence envelopes
for (const item of stakpakEvidence) {
  const envelope = {
    controlId: item.controlId,
    sha256: createHash('sha256')
      .update(item.content || item.raw)
      .digest('hex'),
    uri: item.url || `stakpak://evidence/${item.id}`,
    collectedAt: item.createdAt || new Date().toISOString(),
    source: 'stakpak-migration',
    metadata: {
      originalId: item.id,
      migratedAt: new Date().toISOString(),
      framework: item.framework,
    },
  };

  // Attach to GRC_Claw evidence store via gateway
  await fetch('http://127.0.0.1:18791/api/evidence/attach', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-GRC-Claw-Token': process.env.GRC_CLAW_GATEWAY_TOKEN || '',
    },
    body: JSON.stringify(envelope),
  });
}
```

**Batch import via CLI:**

```bash
# After preparing evidence in GRC_Claw format, run:
grc audit --config grcfile.yaml

# This validates evidence linkage and generates a fresh report
```

### Step 5: Verify Compliance

```bash
# 1. Run a full compliance scan
grc scan .

# 2. Generate a compliance audit report
grc audit

# 3. Check compliance status
grc status

# 4. Detect any drift from baseline
grc drift

# 5. Run the crosswalk delta
grc diff
```

**Verify evidence chain integrity:**

```bash
# List all evidence items
grc evidence list --json

# Verify evidence hash chain
grc evidence verify
```

**Check trust score:**

```bash
grc trust score
```

### Step 6: Connect to A2Z SOC (Optional)

For hosted evidence, benchmarks, and auditor workflows:

```bash
# Configure A2Z SOC connection
export A2Z_SOC_BASE_URL=https://a2zsoc.com
export A2Z_SOC_API_KEY=your-api-key
export A2Z_SOC_TENANT_ID=your-tenant-id

# Push evidence to A2Z SOC
curl -X POST http://127.0.0.1:18791/api/a2z/sync \
  -H "X-GRC-Claw-Token: $GRC_CLAW_GATEWAY_TOKEN"
```

### Step 7: Decommission Stakpak

Only after verifying GRC_Claw is fully operational:

```bash
# 1. Confirm GRC_Claw is producing valid reports
grc audit --json > final-audit.json

# 2. Verify all critical controls are covered
grc frameworks list --json | python3 -c "
import sys, json
data = json.load(sys.stdin)
for fw in data:
    print(f\"{fw['code']}: {fw['controlCount']} controls\")
"

# 3. Export your data as a final backup
grc report --format json --output stakpak-migration-final.json

# 4. Cancel Stakpak subscription (via their dashboard)
# 5. Revoke Stakpak API keys
```

---

## 4. Feature Mapping

### Control & Framework Management

| Stakpak Feature | A2Z SOC + GRC_Claw Equivalent |
|---|---|
| Framework controls | `grc frameworks list` → `@grc-claw/frameworks` (824+ controls) |
| Control catalog | `GET /api/frameworks` endpoint on gateway |
| Custom controls | Define in `packages/frameworks/src/` and register |
| Framework mapping | `@grc-claw/framework-crosswalk` (27,596 mappings) |
| Control testing | `grc scan .` → 12+ built-in rules, extensible |

### Evidence Management

| Stakpak Feature | A2Z SOC + GRC_Claw Equivalent |
|---|---|
| Evidence upload | `POST /api/evidence/attach` (idempotent, SHA-256 hashed) |
| Evidence storage | `@grc-claw/evidence` + PostgreSQL via `@grc-claw/persistence` |
| Evidence verification | `grc evidence verify` → hash chain + Merkle proof |
| Evidence export | `grc report --format json\|yaml\|csv` |
| Audit trail | `@grc-claw/zero-trust-audit` (SHA-256 Merkle chain, RFC 3161 timestamps) |

### Scanning & Assessment

| Stakpak Feature | A2Z SOC + GRC_Claw Equivalent |
|---|---|
| Code scanning | `grc scan .` (12 rules, 6 languages) |
| IaC scanning | `grc iac-scan .` (Terraform, Kubernetes, 8 rules) |
| PQC scanning | `grc pqc-scan .` (post-quantum crypto migration) |
| AI BOM | `grc ai-bom generate` (EU AI Act Article 53) |
| Drift detection | `grc drift` (continuous baseline deviation) |

### Agent & Automation

| Stakpak Feature | A2Z SOC + GRC_Claw Equivalent |
|---|---|
| Manual remediation workflows | `grc agent run` (3-phase autonomous agent) |
| Scheduled checks | `grc apply` → cron-based continuous monitoring |
| Alerting | `POST /api/compliance/alerts` → Slack/Email/Teams notifications |
| Playbooks | `@grc-claw/soar` (5 built-in playbooks) |

### Reporting & Dashboards

| Stakpak Feature | A2Z SOC + GRC_Claw Equivalent |
|---|---|
| Compliance dashboards | `@grc-claw/real-time-compliance-monitor` |
| Executive reports | `grc report` → board-ready narratives |
| Peer benchmarking | `@grc-claw/benchmark-intelligence` |
| Trust score | `grc trust score` → 5-factor scoring (evidence, vuln, controls, training, incidents) |
| Board narratives | `grc report --format narrative` → AI-generated board summaries |

### AI Governance (Stakpak: None)

| A2Z SOC + GRC_Claw Feature |
|---|
| ISO 42001 AI Management System engine |
| EU AI Act risk classification + Article 9 conformity |
| NIST AI RMF mapping |
| AI system inventory + AI BOM registry |
| Adversarial AI compliance monitoring |
| Agent policy firewall + trust scoring |

### Integration & Export

| Stakpak Feature | A2Z SOC + GRC_Claw Equivalent |
|---|---|
| API access | 137+ HTTP endpoints via gateway |
| Webhooks | WebSocket events + `POST /api/events/ingest` |
| Standards export | OSCAL 1.1.2, OCSF 1.1, STIX 2.1, SARIF 2.1.0 |
| SIEM integration | `@grc-claw/ingest` (Wazuh, Suricata, Snort, UFW) |
| VS Code extension | `@grc-claw/compliance-copilot` (11 rules, 6 languages) |
| Terraform provider | `terraform-provider-grc` (Registry: `a2zsoc/grc`) |
| MCP server | `@grc-claw/mcp-server` for Claude/AI assistants |

---

## 5. Data Migration

### Evidence Records

```bash
# Export all evidence from GRC_Claw after import
grc evidence list --json > grc-evidence-imported.json

# Verify count matches your Stakpak export
echo "Stakpak: $(cat stakpak-evidence.json | python3 -c 'import sys,json; print(len(json.load(sys.stdin)))')"
echo "GRC_Claw: $(cat grc-evidence-imported.json | python3 -c 'import sys,json; print(len(json.load(sys.stdin)))')"
```

### Audit Trails

The GRC_Claw audit trail uses SHA-256 Merkle chaining. Stakpak audit logs should be re-hashed and stored as evidence artifacts:

```typescript
import { createHash } from 'node:crypto';
import { readFileSync, writeFileSync } from 'node:fs';

const stakpakAudit = JSON.parse(
  readFileSync('stakpak-audit-trail.json', 'utf-8')
);

const migratedAudit = stakpakAudit.map((entry: any, index: number) => ({
  id: `stakpak-audit-${index}`,
  action: entry.action,
  actor: entry.user || entry.actor,
  timestamp: entry.timestamp,
  dataIntegrityHash: createHash('sha256')
    .update(JSON.stringify(entry))
    .digest('hex'),
  source: 'stakpak-migration',
}));

writeFileSync(
  'migrated-audit-trail.json',
  JSON.stringify(migratedAudit, null, 2)
);
```

### Control Mappings

```typescript
import { readFileSync } from 'node:fs';

const stakpakControls = JSON.parse(
  readFileSync('stakpak-controls.json', 'utf-8')
);

// Build a mapping table
const controlMap = stakpakControls.map((c: any) => ({
  stakpakCode: c.code,
  stakpakFramework: c.framework,
  grcClawEquivalent: findEquivalent(c.code),
  migrationStatus: findEquivalent(c.code) ? 'auto-mapped' : 'needs-manual-review',
}));

function findEquivalent(code: string): string | null {
  // Cross-reference with GRC_Claw's crosswalk corpus
  // This uses the 27,596-mapping database
  const mapping = require('@grc-claw/framework-crosswalk');
  const results = mapping.crosswalkControl(code);
  return results.length > 0 ? results[0].targetCode : null;
}

console.table(controlMap);
```

### Policies and Rules

```yaml
# Migrate Stakpak policies to .grc-policy.yaml
policies:
  - id: sp-access-control
    name: "Access Control Policy (migrated from Stakpak)"
    source: stakpak-migration
    controls:
      - soc2-cc6.1
      - iso27001-a.9.1
    rules:
      - name: "MFA required for all users"
        condition: "auth.mfa_enabled == false"
        severity: critical
        action: block

  - id: sp-encryption
    name: "Encryption Policy (migrated from Stakpak)"
    source: stakpak-migration
    controls:
      - soc2-cc6.7
      - iso27001-a.10.1
    rules:
      - name: "TLS 1.2+ required"
        condition: "tls.version < 1.2"
        severity: high
        action: alert
```

---

## 6. Configuration Migration

### grcfile.yaml

```yaml
version: "1.0"
project: "post-stakpak-migration"

frameworks:
  - soc2
  - iso27001
  - nist-csf
  - hipaa
  - pci-dss
  - gdpr

scan:
  paths:
    - .
    - ./src
    - ./infra
  exclude:
    - node_modules
    - .git
    - dist
    - .grc

iac:
  paths:
    - ./terraform
    - ./kubernetes
  rules:
    - encryption-at-rest
    - public-access
    - logging
    - network-segmentation

evidence:
  storage:
    driver: postgresql   # or "memory" for demo mode
    dsn: ${DATABASE_URL}
  retention:
    days: 365

notifications:
  slack:
    webhook: ${SLACK_WEBHOOK_URL}
  email:
    smtp: ${SMTP_HOST}
```

### Environment Variables

```bash
# .env (GRC_Claw)
GRC_CLAW_GATEWAY_TOKEN=your-secure-token
GRC_CLAW_LOG=info

# PostgreSQL (optional, for persistence)
DATABASE_URL=postgresql://user:pass@localhost:5432/grcclaw

# A2Z SOC (optional, for hosted control plane)
A2Z_SOC_BASE_URL=https://a2zsoc.com
A2Z_SOC_API_KEY=your-a2z-api-key
A2Z_SOC_TENANT_ID=1

# LLM provider (for agent and copilot features)
GRC_LLM_PROVIDER=openai
GRC_LLM_MODEL=gpt-4o
OPENAI_API_KEY=sk-...

# Sovereign mode (uncomment for air-gapped)
# SOVEREIGN_MODE=true
# GRC_SOVEREIGN_URL=https://your-sovereign-host
```

### GitHub Actions Integration

```yaml
# .github/workflows/grc-scan.yml (generated by grc init)
name: GRC Compliance Scan

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  grc-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - run: npm install -g @grc-claw/cli
      - run: grc scan . --json --output grc-results.json
      - run: grc iac-scan . --json --output grc-iac-results.json
      - uses: actions/upload-artifact@v4
        with:
          name: grc-results
          path: grc-*.json
```

---

## 7. Testing & Verification

### Pre-Migration Checklist

```bash
# 1. Verify Stakpak export integrity
python3 -c "
import json
data = json.load(open('stakpak-controls.json'))
print(f'Controls exported: {len(data)}')
data = json.load(open('stakpak-evidence.json'))
print(f'Evidence exported: {len(data)}')
"

# 2. Verify GRC_Claw installation
grc version
grc doctor
```

### Post-Migration Verification

```bash
# 1. Health check
curl -s http://127.0.0.1:18791/health | python3 -m json.tool

# 2. Verify framework coverage
grc frameworks list --json | python3 -c "
import sys, json
data = json.load(sys.stdin)
total = sum(f['controlCount'] for f in data)
print(f'Frameworks: {len(data)}, Total controls: {total}')
"

# 3. Run full compliance scan
grc scan . --json > /tmp/grc-scan.json

# 4. Run compliance audit
grc audit --json > /tmp/grc-audit.json

# 5. Check evidence count
grc evidence list --json | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f'Evidence items: {len(data)}')
"

# 6. Verify hash chain integrity
grc evidence verify

# 7. Check trust score
grc trust score

# 8. Generate and review report
grc report --format json --output /tmp/grc-report.json
python3 -c "
import json
r = json.load(open('/tmp/grc-report.json'))
print(f'Compliance score: {r.get(\"score\", \"N/A\")}')
print(f'Frameworks assessed: {r.get(\"frameworks\", [])}')
"
```

### Regression Test

```bash
# Run the full test suite
cd GRC_Claw && npm run test:comprehensive

# Run individual package tests
npm run test -w @grc-claw/evidence
npm run test -w @grc-claw/framework-crosswalk
npm run test -w @grc-claw/gateway
```

---

## 8. Rollback Plan

If migration fails or you need to revert:

### Immediate Rollback (First 48 Hours)

```bash
# 1. Stop the GRC_Claw gateway
lsof -ti :18791 | xargs kill 2>/dev/null

# 2. Your Stakpak account should still be active
# Log in to Stakpak dashboard and verify data is intact

# 3. Revoke GRC_Claw API keys if you connected to A2Z SOC
# (via A2Z SOC dashboard or CLI)

# 4. Keep your Stakpak exports as backup
ls -la stakpak-*.json
```

### Partial Rollback

If specific data didn't migrate correctly:

```bash
# Re-run the migration script for specific controls
node scripts/migrate-controls.js --framework soc2 --force

# Re-attach evidence for specific controls
node scripts/migrate-evidence.js --control-id soc2-cc6.1
```

### Full Revert

```bash
# 1. Remove GRC_Claw installation
npm uninstall -g @grc-claw/cli

# 2. Remove local project files
rm -rf .grc/
rm grcfile.yaml

# 3. If using Docker
docker compose -f deploy/docker-compose.yml down -v

# 4. Reactivate Stakpak subscription
# (via Stakpak billing portal)
```

---

## 9. FAQ

### General

**Q: Will I lose my Stakpak data during migration?**
A: No. Export everything first (Step 1) and keep exports as backup. Stakpak data remains intact until you cancel the subscription.

**Q: How long does the migration take?**
A: 1–3 days depending on data volume. Most migrations complete in 1 day.

**Q: Can I run both Stakpak and GRC_Claw simultaneously?**
A: Yes. Run them in parallel during the verification period (Step 5) before decommissioning Stakpak.

### Technical

**Q: My Stakpak controls don't map cleanly to GRC_Claw frameworks. What do I do?**
A: Use `@grc-claw/framework-crosswalk` to find equivalents. For unmapped controls, define custom controls in `packages/frameworks/src/` and register them. The crosswalk corpus covers 27,596 mappings across 20+ frameworks.

**Q: Does GRC_Claw support the same compliance frameworks as Stakpak?**
A: GRC_Claw supports 13+ frameworks with 824+ controls: SOC 2, ISO 27001, NIST CSF, NIST 800-53, HIPAA, PCI DSS, GDPR, FedRAMP, CMMC, CIS Controls, DORA, NIS2, EU AI Act, COBIT 2019, and more.

**Q: What about my existing audit trails?**
A: Migrate them as evidence artifacts. GRC_Claw uses SHA-256 Merkle-chained audit trails with RFC 3161 timestamps — cryptographically stronger than most SaaS platforms.

**Q: Can I use GRC_Claw without A2Z SOC?**
A: Yes. GRC_Claw runs fully standalone with in-memory or PostgreSQL persistence. A2Z SOC is optional for hosted evidence vaults, auditor workflows, and benchmarks.

**Q: Is my data secure during migration?**
A: All data stays local on your machine during migration. GRC_Claw is local-first — nothing is sent to A2Z SOC unless you explicitly configure the connector.

### Pricing

**Q: What does GRC_Claw cost?**
A: The engine is MIT-licensed and free. A2Z SOC offers optional hosted tiers for evidence vaults, auditor rooms, and managed services.

**Q: What about A2Z SOC pricing?**
A: See [a2zsoc.com](https://a2zsoc.com) for current pricing. Entry points include:
- AI Assurance Passport: $2,500 setup + $3,500/mo
- CMMC Procurement Readiness: $999 triage → $3,500/mo
- Broker Trust Desk: $999/mo partner fee

---

## 10. Support

### Community

| Channel | URL |
|---|---|
| GitHub Issues | [github.com/AAH20/GRC_Claw/issues](https://github.com/AAH20/GRC_Claw/issues) |
| Documentation | `GRC_Claw/docs/` (OpenAPI, CLI Reference, Architecture) |
| Changelog | `GRC_Claw/CHANGELOG.md` |

### Professional

| Service | URL |
|---|---|
| A2Z SOC Platform | [a2zsoc.com](https://a2zsoc.com) |
| Partner Deal Room | [a2zsoc.com/international-partners](https://a2zsoc.com/international-partners) |
| Trust Center | [a2zsoc.com/trust-center](https://a2zsoc.com/trust-center) |
| Productized Services | [a2zsoc.com/productized-services](https://a2zsoc.com/productized-services) |

### Migration Assistance

For hands-on migration support, engage through the partner deal room or contact A2Z SOC directly. The team provides:

- Stakpak data mapping review
- Framework crosswalk validation
- Evidence migration verification
- Post-migration compliance audit
- Training for your team on GRC_Claw workflows

### CLI Help

```bash
grc --help                    # All commands
grc scan --help               # Scan options
grc audit --help              # Audit options
grc frameworks list --help    # Framework listing
grc doctor                    # Environment health check
```

### Resources

| Document | Location |
|---|---|
| OpenAPI Spec (137+ endpoints) | `GRC_Claw/docs/openapi.yaml` |
| CLI Reference (27 commands) | `GRC_Claw/docs/CLI-REFERENCE.md` |
| Architecture (C4, planes, ADRs) | `GRC_Claw/ARCHITECTURE.md` |
| Onboarding Guide | `GRC_Claw/docs/ONBOARDING.md` |
| Developer Guide | `GRC_Claw/docs/DEVELOPER-V15.md` |
| ISO 42001 Guide | `GRC_Claw/docs/ISO_42001_AIMS.md` |
| Security Audit | `GRC_Claw/docs/SECURITY-AUDIT.md` |
| Contributing | `GRC_Claw/CONTRIBUTING.md` |
