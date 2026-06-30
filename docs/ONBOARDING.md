# GRC_Claw Developer Onboarding Guide

> **Goal:** Zero to productive in 30 minutes. Every section gives you something to run.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Clone and Install](#2-clone-and-install)
3. [Build the Project](#3-build-the-project)
4. [Run the Test Suite](#4-run-the-test-suite)
5. [Start the Gateway](#5-start-the-gateway)
6. [Explore the API](#6-explore-the-api)
7. [Understand the Architecture](#7-understand-the-architecture)
8. [Key Packages to Know](#8-key-packages-to-know)
9. [Development Workflow](#9-development-workflow)
10. [Code Style](#10-code-style)
11. [Common Tasks](#11-common-tasks)
12. [Debugging Tips](#12-debugging-tips)
13. [Resources](#13-resources)

---

## 1. Prerequisites

| Tool | Minimum Version | Check | Install |
|------|----------------|-------|---------|
| **Node.js** | 20+ | `node -v` | `brew install node` or [nodejs.org](https://nodejs.org) |
| **npm** | 10+ (bundled with Node 20) | `npm -v` | Comes with Node |
| **Git** | 2.30+ | `git -v` | `brew install git` |
| **PostgreSQL** | 15+ (optional) | `psql -V` | `brew install postgresql@15` |

PostgreSQL is optional. Without it, the gateway runs in **demo mode** with in-memory state. With it, you get persistence.

```bash
# Verify all prerequisites at once
node -v && npm -v && git -v
```

---

## 2. Clone and Install

```bash
# 1. Clone the repo
git clone https://github.com/AAH20/GRC_Claw.git

# 2. Enter the project
cd GRC_Claw

# 3. Install all workspace dependencies (89 packages)
npm install

# 4. Verify workspaces resolved
npm ls --depth=0 2>/dev/null | head -20

# 5. Create your local env file
cp .env.example .env 2>/dev/null || echo 'GRC_CLAW_GATEWAY_TOKEN=dev-token' > .env
```

**What just happened?** npm workspaces linked 89 packages under `packages/*` and `apps/*` so they resolve each other's imports without publishing.

---

## 3. Build the Project

```bash
# Full monorepo build (TypeScript project references)
npm run build
```

This compiles all 89 packages in dependency order via `tsc -b tsconfig.json`. Expect 1–3 minutes on first build. Incremental builds are fast.

**Verify the build succeeded:**

```bash
# Check gateway compiled
ls packages/gateway/dist/cli.js

# Check CLI compiled
ls packages/cli/dist/index.js

# Check core types
ls packages/core/dist/index.d.ts
```

---

## 4. Run the Test Suite

```bash
# Run the comprehensive test suite (unit + integration + gateway)
npm run test:comprehensive
```

This runs:
- Unit tests for `ingest`, `aims`, `connectors`
- BYOC connector tests
- Gateway integration tests (starts gateway, runs curl-based assertions)

**Run individual package tests:**

```bash
npm run test -w @grc-claw/ingest        # Log normalization
npm run test -w @grc-claw/aims          # ISO 42001 AIMS
npm run test -w @grc-claw/connectors    # BYOC LLM connectors
npm run test -w @grc-claw/evidence      # Evidence store
```

**Run the ISO 42001 specific tests:**

```bash
npm run test:iso42001
```

---

## 5. Start the Gateway

```bash
# Start the gateway daemon on port 18791
npm run gateway
```

The gateway binds to `127.0.0.1:18791` by default. You'll see startup logs confirming:
- Gateway listening on port 18791
- A2Z SOC mode (demo by default)
- Connector registry initialized
- Security graph seeded

**Verify the gateway is running:**

```bash
curl -s http://127.0.0.1:18791/health | python3 -m json.tool
```

**Set a custom token (optional):**

```bash
GRC_CLAW_GATEWAY_TOKEN=my-secret-token npm run gateway
```

**Stop the gateway:**

```bash
lsof -ti :18791 | xargs kill
```

---

## 6. Explore the API

All endpoints require the `X-GRC-Claw-Token` header (or `Authorization: Bearer <token>`).

### 6.1 Health Check (no auth required)

```bash
curl -s http://127.0.0.1:18791/health | python3 -m json.tool
```

### 6.2 List Compliance Frameworks

```bash
curl -s http://127.0.0.1:18791/api/frameworks \
  -H "X-GRC-Claw-Token: dev-token" | python3 -m json.tool
```

Returns all 13+ framework packs (SOC 2, ISO 27001, NIST CSF, HIPAA, PCI DSS, GDPR, CMMC, etc.) with their controls.

### 6.3 Normalize a Security Event (SIEM Ingest)

```bash
curl -s -X POST http://127.0.0.1:18791/api/ingest/normalize \
  -H "X-GRC-Claw-Token: dev-token" \
  -H "Content-Type: application/json" \
  -d '{
    "source": "suricata",
    "tenantId": 1,
    "payload": {
      "timestamp": "2026-01-15T12:00:00Z",
      "event_type": "alert",
      "src_ip": "10.1.1.1",
      "dest_ip": "10.2.2.2",
      "alert": {
        "signature_id": 2024896,
        "signature": "ET MALWARE Cobalt Strike Beacon",
        "severity": 1
      }
    }
  }' | python3 -m json.tool
```

Returns the canonical `SecurityEventCanonical` shape with compliance impact mappings.

### 6.4 Get Action Ledger (Audit Trail)

```bash
curl -s http://127.0.0.1:18791/api/action-ledger \
  -H "X-GRC-Claw-Token: dev-token" | python3 -m json.tool
```

Returns all recorded agent actions with hash chain integrity status.

### 6.5 Get Assurance Envelope Summary

```bash
curl -s http://127.0.0.1:18791/api/assurance \
  -H "X-GRC-Claw-Token: dev-token" | python3 -m json.tool
```

Returns the assurance graph summary — agent identity, risk scores, and envelope count.

---

## 7. Understand the Architecture

GRC_Claw follows a **3-plane model**:

```
┌─────────────────────────────────────────────────────────┐
│                    CONTROL PLANE                        │
│  Gateway · Agent Runtime · RBAC · Policy Firewall       │
│  Auth · Routing · Jobs · Agent Tool Dispatch            │
├─────────────────────────────────────────────────────────┤
│                    EVIDENCE PLANE                       │
│  Evidence Store · Frameworks · Crosswalk · ZK Proofs    │
│  Controls · Tests · Hashed Artifacts · Assurance        │
├─────────────────────────────────────────────────────────┤
│                      DATA PLANE                        │
│  A2Z Connector · SIEM Events · Org/Tenant Sync         │
│  Cloud Connectors · Ingest · Persistence                │
└─────────────────────────────────────────────────────────┘
```

### Key architectural principles

1. **Local-first**: Runs fully standalone with in-memory state. PostgreSQL and A2Z SOC are optional add-ons.
2. **Monorepo with workspace isolation**: Each package publishes independently. No proprietary A2Z SOC code lives in this repo.
3. **Fail-closed auth**: Every authenticated endpoint uses `timingSafeEqual`. Bad tokens return 401 immediately.
4. **Idempotency**: `evidence.attach`, `control.test`, and `agent.tool` calls are idempotent via cache.
5. **3-phase agent loop**: Plan → Act → Verify, with trust scoring and auto-pause below threshold.

### Data flow

```
SIEM/Cloud Source → Ingest Normalizer → Canonical Event
                                              ↓
Agent Runtime → Policy Decision → Tool Execution → Evidence Hash
                                              ↓
                                    Action Ledger (hash chain)
                                              ↓
                                    Assurance Envelope → A2Z SOC / Auditor
```

---

## 8. Key Packages to Know

These are the 10 packages you'll touch most often:

| Package | Path | What It Does |
|---------|------|--------------|
| `@grc-claw/core` | `packages/core` | Domain types (`ComplianceControl`, `SecurityEventCanonical`, `GRCEngineFacade`) |
| `@grc-claw/gateway` | `packages/gateway` | HTTP/WebSocket daemon — all routes, auth, rate limiting, metrics |
| `@grc-claw/cli` | `packages/cli` | `grc` CLI — 27 commands for scan, audit, diff, report, agent |
| `@grc-claw/frameworks` | `packages/frameworks` | 13 compliance framework packs with 824+ controls |
| `@grc-claw/evidence` | `packages/evidence` | SHA-256 evidence lineage, action ledger, assurance envelopes |
| `@grc-claw/ingest` | `packages/ingest` | SIEM/IDS/firewall log normalizers (Wazuh, Suricata, Snort, UFW) |
| `@grc-claw/agent-runtime` | `packages/agent-runtime` | 3-phase autonomous agent, tool dispatch, exec policy |
| `@grc-claw/framework-crosswalk` | `packages/framework-crosswalk` | 27,596 cross-framework control mappings |
| `@grc-claw/mcp-server` | `packages/mcp-server` | MCP server for Claude/AI assistant integration |
| `@grc-claw/persistence` | `packages/persistence` | PostgreSQL persistence layer |

---

## 9. Development Workflow

### Branch strategy

```bash
# Create a feature branch from main
git checkout main && git pull
git checkout -b feat/my-new-feature

# Make changes, build, test
npm run build
npm run test:comprehensive

# Commit with conventional format
git add -A
git commit -m "feat(ingest): add Azure Sentinel normalizer"

# Push and open PR
git push -u origin feat/my-new-feature
gh pr create --title "feat(ingest): add Azure Sentinel normalizer" --body "Adds normalized output for Azure Sentinel alerts mapped to ISO A.8.16"
```

### Commit convention

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(scope): description
fix(scope): description
docs(scope): description
chore(scope): description
```

Scopes: `ingest`, `gateway`, `evidence`, `frameworks`, `agent`, `cli`, `mcp`, `core`, etc.

### Pre-commit checklist

```bash
npm run build                      # Must compile cleanly
npm run test -w @grc-claw/ingest   # At minimum, test the package you changed
npm run test:comprehensive         # Full suite before PR
```

---

## 10. Code Style

### TypeScript conventions

```typescript
// tsconfig.base.json settings (applies to all packages):
// target: ES2022, module: NodeNext, strict: true, declaration: true

// File: packages/my-package/src/index.ts

// 1. ESM only — use .js extensions in imports
import { createEventUuid } from '@grc-claw/core';
import { readFile } from 'node:fs/promises';  // node: prefix for builtins

// 2. Named exports preferred over default exports
export interface MyServiceConfig {
  tenantId: number;
  frameworks: string[];
}

export class MyService {
  constructor(private readonly config: MyServiceConfig) {}
  
  async run(): Promise<MyResult> {
    // implementation
  }
}

// 3. Types over interfaces for simple shapes, interfaces for extensible contracts
type Severity = 'low' | 'medium' | 'high' | 'critical';

// 4. Async/await, no callbacks
// 5. No comments unless asked — code should be self-documenting
```

### Naming conventions

| Element | Convention | Example |
|---------|-----------|---------|
| Files | `kebab-case.ts` | `action-ledger.ts`, `evidence-graph.ts` |
| Classes | `PascalCase` | `EvidenceStore`, `DriftDetector` |
| Interfaces | `PascalCase` | `TenantContext`, `GatewayConfig` |
| Functions | `camelCase` | `buildExecPolicyWithConnectors()` |
| Constants | `SCREAMING_SNAKE_CASE` | `REQUEST_TIMEOUT_MS`, `MAX_BODY_BYTES` |
| Package scope | `@grc-claw/` | `@grc-claw/evidence` |
| Env vars | `GRC_CLAW_` prefix | `GRC_CLAW_GATEWAY_TOKEN` |

### File structure per package

```
packages/my-package/
├── package.json        # name: @grc-claw/my-package
├── tsconfig.json       # extends ../../tsconfig.base.json
├── src/
│   ├── index.ts        # Public API — re-exports everything
│   ├── my-service.ts   # Implementation
│   └── my-service.test.ts  # Tests (colocated)
└── dist/               # Compiled output (gitignored)
```

---

## 11. Common Tasks

### 11.1 Adding a New Compliance Framework

1. Create the framework definition file:

```typescript
// packages/frameworks/src/my-framework.ts
import type { ComplianceControl } from '@grc-claw/core';

export const MY_FRAMEWORK_CONTROLS: ComplianceControl[] = [
  {
    id: 'mf-1',
    controlCode: 'MF-1.1',
    title: 'My Framework Control',
    frameworkCode: 'my_framework',
    domain: 'Security',
  },
  // ... more controls
];
```

2. Register it in `packages/frameworks/src/index.ts`:

```typescript
import { MY_FRAMEWORK_CONTROLS } from './my-framework.js';

// Add to listFrameworkPacks()
{
  code: 'my_framework',
  name: 'My Framework',
  version: '1.0',
  controls: MY_FRAMEWORK_CONTROLS,
}
```

3. Add crosswalk mappings in `packages/framework-crosswalk/src/`.

4. Build and test:

```bash
npm run build -w @grc-claw/frameworks
npm run test:comprehensive
```

### 11.2 Adding a New Evidence Connector

1. Create the connector file:

```typescript
// packages/cloud-connectors/src/my-service.ts
import type { EvidenceConnector, EvidenceEnvelope } from '@grc-claw/evidence';

export class MyServiceConnector implements EvidenceConnector {
  readonly id = 'my-service';
  readonly name = 'My Service';

  async collect(): Promise<EvidenceEnvelope[]> {
    // Fetch evidence from the external service
    return [{
      controlId: 'soc2-cc6.1',
      sha256: '...',
      uri: 'https://...',
      collectedAt: new Date().toISOString(),
      source: this.id,
    }];
  }
}
```

2. Export from `packages/cloud-connectors/src/index.ts`:

```typescript
export { MyServiceConnector } from './my-service.js';
```

3. Wire into the gateway connector registry in `packages/gateway/src/connectors-api.ts`.

4. Build and test:

```bash
npm run build -w @grc-claw/cloud-connectors
npm run test:cloud
```

### 11.3 Adding a New CLI Command

1. Add the command handler in `packages/cli/src/index.ts`:

```typescript
// Inside the command routing logic
if (command === 'my-command') {
  const result = await myCommandHandler(args);
  console.log(JSON.stringify(result, null, 2));
  process.exit(0);
}
```

2. Implement the handler:

```typescript
async function myCommandHandler(args: string[]): Promise<MyResult> {
  // Your logic here
  return { ok: true, message: 'Done' };
}
```

3. Build and test:

```bash
npm run build -w @grc-claw/cli
node packages/cli/dist/index.js my-command
```

### 11.4 Adding a New API Endpoint

1. Open `packages/gateway/src/server.ts`.

2. Add your route inside the `createServer` callback, following the existing pattern:

```typescript
if (path === '/api/my-endpoint' && req.method === 'GET') {
  if (!authOk(req)) {
    res.writeHead(401);
    res.end(JSON.stringify({ error: 'unauthorized' }));
    return;
  }

  const result = { ok: true, data: myLogic() };
  res.writeHead(200, { 'Content-Type': 'application/json' });
  res.end(JSON.stringify(result));
  return;
}
```

3. Add the route to `docs/openapi.yaml`.

4. Build and test:

```bash
npm run build -w @grc-claw/gateway
npm run gateway &
curl -s http://127.0.0.1:18791/api/my-endpoint \
  -H "X-GRC-Claw-Token: dev-token"
```

### 11.5 Adding a New Agent Tool

1. Define the tool in the agent tools registry (see `BUILTIN_AGENT_TOOLS` in `packages/agent-runtime`):

```typescript
{
  name: 'my_tool',
  description: 'Does something useful',
  tier: 'read',  // 'read' | 'write' | 'destructive'
  handler: async (args) => {
    return { ok: true, result: 'tool output' };
  },
}
```

2. Add the tool to the exec policy allowlist in `packages/gateway/src/connectors-api.ts`.

3. Test via the gateway:

```bash
curl -s -X POST http://127.0.0.1:18791/api/agent/invoke \
  -H "X-GRC-Claw-Token: dev-token" \
  -H "Content-Type: application/json" \
  -d '{"sessionId":"test","tool":"my_tool","args":{}}'
```

---

## 12. Debugging Tips

### Enable verbose logging

```bash
# Gateway verbose mode
GRC_CLAW_LOG=debug npm run gateway

# CLI verbose mode
grc scan . --verbose
```

### Common errors and fixes

| Error | Cause | Fix |
|-------|-------|-----|
| `401 unauthorized` | Missing or wrong `X-GRC-Claw-Token` header | Check your token matches `GRC_CLAW_GATEWAY_TOKEN` |
| `508 request_timeout` | Request exceeded 30s limit | Break into smaller operations or check for infinite loops |
| `EADDRINUSE :::18791` | Gateway already running on that port | `lsof -ti :18791 \| xargs kill` then restart |
| `MODULE_NOT_FOUND` for `@grc-claw/*` | Package not built | Run `npm run build` from monorepo root |
| `Cannot find module './foo.js'` | Missing `.js` extension in ESM import | Add `.js` extension to the import path |
| `TS2307: Cannot find module '@grc-claw/...'` | Workspace resolution issue | Run `npm install` again, check `package.json` name matches |

### Inspect the action ledger

```bash
# View recent actions
curl -s http://127.0.0.1:18791/api/action-ledger?limit=10 \
  -H "X-GRC-Claw-Token: dev-token" | python3 -m json.tool

# Check hash chain integrity
curl -s http://127.0.0.1:18791/api/action-ledger \
  -H "X-GRC-Claw-Token: dev-token" | python3 -c "import sys,json; d=json.load(sys.stdin); print('Chain valid:', d.get('integrity',{}).get('valid'))"
```

### Check metrics (Prometheus format)

```bash
curl -s http://127.0.0.1:18791/metrics
```

### Run doctor for environment checks

```bash
npm run doctor
```

### Reset in-memory state

Just restart the gateway. Without PostgreSQL, all state is ephemeral:

```bash
lsof -ti :18791 | xargs kill 2>/dev/null; sleep 1; npm run gateway
```

---

## 13. Resources

| Resource | Location |
|----------|----------|
| **OpenAPI Spec** | `docs/openapi.yaml` (4,338 lines, all 137+ endpoints) |
| **CLI Reference** | `docs/CLI-REFERENCE.md` (27 commands with examples) |
| **Architecture** | `ARCHITECTURE.md` (C4 context, planes, ADRs) |
| **Developer Guide** | `docs/DEVELOPER-V15.md` (full API reference, auth, event shapes) |
| **ISO 42001 Guide** | `docs/ISO_42001_AIMS.md` (AI management system) |
| **Performance SLOs** | `docs/PERFORMANCE-V17.md` |
| **Contributing** | `CONTRIBUTING.md` (connector, framework, rule patterns) |
| **BYOC Connectors** | `docs/BYOC_CONNECTORS.md` (bring your own LLM) |
| **Sovereign Deploy** | `deploy/sovereign/` (Terraform + Docker Compose) |
| **Changelog** | `CHANGELOG.md` |

### Quick links

```bash
# Read the OpenAPI spec
cat docs/openapi.yaml | head -100

# Browse all CLI commands
cat docs/CLI-REFERENCE.md | grep "^### grc"

# List all packages
ls packages/ | wc -l

# Check which packages have tests
grep -r '"test"' packages/*/package.json | grep -v node_modules
```

---

## Quick Reference Card

```bash
# Essential commands
npm install              # Install all dependencies
npm run build            # Build all 89 packages
npm run test:comprehensive  # Full test suite
npm run gateway          # Start gateway on :18791
npm run doctor           # Environment health check

# Single-package workflows
npm run build -w @grc-claw/gateway
npm run test -w @grc-claw/ingest
npm run dev -w @grc-claw/console

# Gateway API
curl http://127.0.0.1:18791/health
curl -H "X-GRC-Claw-Token: dev-token" http://127.0.0.1:18791/api/frameworks
```

Welcome to GRC_Claw. You're ready to build.
