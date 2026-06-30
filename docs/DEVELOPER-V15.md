# GRC_Claw Developer Guide V15

> Last updated: 2026-06-30 | Status: Living Document

---

## 1. API Reference

### Base URL

```
Production:  https://api.grc-claw.com/v1
Staging:     https://api.staging.grc-claw.com/v1
Development: http://localhost:3000/v1
```

### Authentication

All requests require `Authorization: Bearer <jwt>` header.

### Endpoint Catalog (137+ Endpoints)

#### Authentication & Identity (12 endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/login` | User login (email/password) |
| POST | `/auth/login/saml` | SAML SSO login |
| POST | `/auth/login/oidc` | OIDC SSO login |
| POST | `/auth/refresh` | Refresh access token |
| POST | `/auth/logout` | Invalidate session |
| POST | `/auth/mfa/enroll` | Enroll MFA device |
| POST | `/auth/mfa/verify` | Verify MFA challenge |
| POST | `/auth/mfa/disable` | Disable MFA |
| GET | `/auth/sessions` | List active sessions |
| DELETE | `/auth/sessions/:id` | Revoke session |
| POST | `/auth/password/reset` | Request password reset |
| PUT | `/auth/password/change` | Change password |

**Request: POST /auth/login**

```json
// Request
{
  "email": "analyst@example.com",
  "password": "••••••••",
  "tenant_id": "tenant_abc"
}

// Response (200)
{
  "access_token": "eyJhbGciOiJSUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJSUzI1NiIs...",
  "expires_in": 3600,
  "token_type": "Bearer",
  "user": {
    "id": "usr_01H8X...",
    "email": "analyst@example.com",
    "roles": ["analyst"],
    "tenant_id": "tenant_abc"
  }
}
```

#### Events & Ingestion (15 endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/events/ingest` | Ingest single event |
| POST | `/events/ingest/batch` | Ingest batch (max 1000) |
| GET | `/events` | List events (paginated) |
| GET | `/events/:id` | Get event by ID |
| GET | `/events/:id/timeline` | Event timeline |
| PUT | `/events/:id` | Update event |
| POST | `/events/:id/enrich` | Trigger enrichment |
| POST | `/events/:id/escalate` | Escalate event |
| POST | `/events/:id/resolve` | Resolve event |
| POST | `/events/:id/assign` | Assign to analyst |
| GET | `/events/:id/evidence` | Get evidence chain |
| POST | `/events/:id/notes` | Add analyst note |
| GET | `/events/search` | Advanced search |
| POST | `/events/export` | Export events |
| DELETE | `/events/:id` | Soft delete event |

**Request: POST /events/ingest**

```json
// Request
{
  "source": "siem-wazuh",
  "severity": "high",
  "category": "authentication",
  "title": "Failed login attempts from external IP",
  "description": "5 failed login attempts from 203.0.113.42",
  "metadata": {
    "source_ip": "203.0.113.42",
    "target_user": "admin",
    "attempts": 5
  },
  "tags": ["brute-force", "external"]
}

// Response (201)
{
  "id": "evt_01J0...",
  "status": "new",
  "created_at": "2026-06-30T12:00:00Z",
  "evidence_chain": {
    "node_id": "evn_01J0...",
    "sequence": 1,
    "hash": "sha256:abcdef..."
  }
}
```

#### Evidence Graph (18 endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/evidence/append` | Append evidence node |
| GET | `/evidence/:eventId` | Get evidence chain |
| GET | `/evidence/:eventId/verify` | Verify chain integrity |
| GET | `/evidence/:eventId/ancestry` | Get ancestry path |
| GET | `/evidence/:eventId/descendants` | Get descendant nodes |
| POST | `/evidence/:eventId/link` | Link to external evidence |
| PUT | `/evidence/:nodeId` | Update evidence metadata |
| DELETE | `/evidence/:nodeId` | Soft delete (requires SoD) |
| GET | `/evidence/graph/stats` | Graph statistics |
| GET | `/evidence/graph/export` | Export subgraph |
| POST | `/evidence/graph/verify-all` | Bulk verification |
| GET | `/evidence/:eventId/audit-trail` | Audit trail |
| POST | `/evidence/:eventId/attest` | Add attestation |
| GET | `/evidence/:eventId/attestations` | List attestations |
| PUT | `/evidence/:nodeId/classification` | Update classification |
| GET | `/evidence/:eventId/impact` | Impact analysis |
| POST | `/evidence/:eventId/cross-reference` | Cross-reference events |
| GET | `/evidence/graph/integrity-report` | Integrity report |

**Request: POST /evidence/append**

```json
// Request
{
  "event_id": "evt_01J0...",
  "evidence_type": "log_entry",
  "source": "wazuh-agent",
  "content": {
    "log": "Jun 30 12:00:00 host sshd[1234]: Failed password for admin from 203.0.113.42",
    "parsed": {
      "service": "sshd",
      "action": "failed_password",
      "user": "admin",
      "source_ip": "203.0.113.42"
    }
  },
  "parent_node_id": "evn_01J0...",
  "hash_chain": true
}

// Response (201)
{
  "node_id": "evn_01J0...",
  "sequence": 2,
  "hash": "sha256:123456...",
  "parent_hash": "sha256:abcdef...",
  "chain_valid": true,
  "created_at": "2026-06-30T12:00:01Z"
}
```

#### Compliance & Verifiers (20 endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/compliance/run` | Run compliance verifier |
| GET | `/compliance/runs` | List verifier runs |
| GET | `/compliance/runs/:id` | Get run details |
| GET | `/compliance/runs/:id/results` | Get run results |
| POST | `/compliance/runs/:id/export` | Export run report |
| GET | `/compliance/frameworks` | List frameworks |
| GET | `/compliance/frameworks/:id` | Get framework details |
| GET | `/compliance/frameworks/:id/controls` | List controls |
| GET | `/compliance/controls/:id` | Get control details |
| PUT | `/compliance/controls/:id/status` | Update control status |
| POST | `/compliance/controls/:id/evidence` | Attach evidence |
| GET | `/compliance/controls/:id/evidence` | List attached evidence |
| GET | `/compliance/dashboard` | Compliance dashboard |
| GET | `/compliance/gaps` | Gap analysis |
| POST | `/compliance/gaps/:id/remediation` | Create remediation plan |
| GET | `/compliance/remediations` | List remediation plans |
| PUT | `/compliance/remediations/:id` | Update remediation |
| POST | `/compliance/remediations/:id/approve` | Approve remediation |
| GET | `/compliance/audit-trail` | Compliance audit trail |
| POST | `/compliance/generate-report` | Generate compliance report |

#### Connectors (15 endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/connectors` | Register connector |
| GET | `/connectors` | List connectors |
| GET | `/connectors/:id` | Get connector details |
| PUT | `/connectors/:id` | Update connector |
| DELETE | `/connectors/:id` | Delete connector |
| POST | `/connectors/:id/test` | Test connectivity |
| POST | `/connectors/:id/enable` | Enable connector |
| POST | `/connectors/:id/disable` | Disable connector |
| POST | `/connectors/:id/rotate-credentials` | Rotate credentials |
| GET | `/connectors/:id/health` | Health check |
| GET | `/connectors/:id/metrics` | Connector metrics |
| POST | `/connectors/:id/sync` | Trigger sync |
| GET | `/connectors/:id/sync-history` | Sync history |
| POST | `/connectors/:id/configure` | Update configuration |
| GET | `/connectors/templates` | Available templates |

#### Marketplace (12 endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/marketplace/plugins` | List available plugins |
| GET | `/marketplace/plugins/:id` | Get plugin details |
| POST | `/marketplace/plugins/:id/install` | Install plugin |
| DELETE | `/marketplace/plugins/:id/uninstall` | Uninstall plugin |
| POST | `/marketplace/plugins/:id/enable` | Enable plugin |
| POST | `/marketplace/plugins/:id/disable` | Disable plugin |
| GET | `/marketplace/plugins/:id/config` | Get plugin config |
| PUT | `/marketplace/plugins/:id/config` | Update plugin config |
| POST | `/marketplace/plugins/:id/execute` | Execute plugin |
| GET | `/marketplace/plugins/:id/usage` | Usage metrics |
| GET | `/marketplace/plugins/:id/reviews` | Plugin reviews |
| POST | `/marketplace/plugins/:id/reviews` | Submit review |

#### Detection Rules (12 endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/detections/rules` | Create detection rule |
| GET | `/detections/rules` | List rules |
| GET | `/detections/rules/:id` | Get rule details |
| PUT | `/detections/rules/:id` | Update rule |
| DELETE | `/detections/rules/:id` | Delete rule |
| POST | `/detections/rules/:id/activate` | Activate rule |
| POST | `/detections/rules/:id/deactivate` | Deactivate rule |
| POST | `/detections/rules/:id/test` | Test rule against sample |
| GET | `/detections/rules/:id/matches` | Get rule matches |
| GET | `/detections/rules/:id/metrics` | Rule performance |
| POST | `/detections/rules/simulate` | Simulate rule set |
| GET | `/detections/templates` | Rule templates |

#### Tenants & RBAC (14 endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/tenants` | Create tenant |
| GET | `/tenants` | List tenants |
| GET | `/tenants/:id` | Get tenant details |
| PUT | `/tenants/:id` | Update tenant |
| DELETE | `/tenants/:id` | Delete tenant |
| GET | `/tenants/:id/users` | List tenant users |
| POST | `/tenants/:id/users` | Add user to tenant |
| DELETE | `/tenants/:id/users/:userId` | Remove user |
| PUT | `/tenants/:id/users/:userId/role` | Update role |
| GET | `/roles` | List roles |
| POST | `/roles` | Create role |
| PUT | `/roles/:id` | Update role |
| DELETE | `/roles/:id` | Delete role |
| POST | `/roles/:id/permissions` | Assign permissions |

#### Reports & Exports (10 endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/reports/generate` | Generate report |
| GET | `/reports` | List reports |
| GET | `/reports/:id` | Get report details |
| GET | `/reports/:id/download` | Download report |
| DELETE | `/reports/:id` | Delete report |
| POST | `/reports/schedule` | Schedule recurring report |
| GET | `/reports/schedules` | List schedules |
| PUT | `/reports/schedules/:id` | Update schedule |
| DELETE | `/reports/schedules/:id` | Delete schedule |
| GET | `/reports/templates` | Report templates |

#### Dashboard & Analytics (10 endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/dashboard/summary` | Dashboard summary |
| GET | `/dashboard/events-by-severity` | Events by severity |
| GET | `/dashboard/events-by-category` | Events by category |
| GET | `/dashboard/events-timeline` | Events timeline |
| GET | `/dashboard/top-threats` | Top detected threats |
| GET | `/dashboard/mean-time-to-detect` | MTTD metrics |
| GET | `/dashboard/mean-time-to-respond` | MTTR metrics |
| GET | `/dashboard/compliance-score` | Compliance score |
| GET | `/dashboard/connector-health` | Connector health |
| GET | `/dashboard/agent-metrics` | Agent performance |

#### System & Admin (9 endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/system/health` | System health check |
| GET | `/system/version` | Version info |
| GET | `/system/metrics` | System metrics |
| GET | `/system/audit-log` | System audit log |
| POST | `/system/cache/purge` | Purge cache |
| GET | `/system/daemons` | Daemon status |
| POST | `/system/daemons/:id/restart` | Restart daemon |
| GET | `/system/config` | System configuration |
| PUT | `/system/config` | Update configuration |

### Standard Error Response

```json
{
  "error": {
    "code": "EVIDENCE_CHAIN_BROKEN",
    "message": "Evidence chain integrity verification failed at node evn_01J0...",
    "details": {
      "broken_at_sequence": 5,
      "expected_hash": "sha256:abcdef...",
      "actual_hash": "sha256:123456..."
    },
    "correlationId": "req_01J0...",
    "timestamp": "2026-06-30T12:00:00Z",
    "retryable": false
  }
}
```

---

## 2. SDK Quickstart

### TypeScript

```typescript
import { GRCclaw } from '@grc-claw/sdk';

const client = new GRCclaw({
  apiKey: process.env.GRC_CLAW_API_KEY,
  tenantId: 'tenant_abc',
  environment: 'production',  // or 'staging', 'development'
});

// Ingest an event
const event = await client.events.ingest({
  source: 'wazuh',
  severity: 'high',
  category: 'authentication',
  title: 'Failed login attempts',
  metadata: {
    source_ip: '203.0.113.42',
    attempts: 5,
  },
});

// Append evidence
const evidence = await client.evidence.append({
  eventId: event.id,
  evidenceType: 'log_entry',
  source: 'wazuh-agent',
  content: { log: '...' },
});

// Verify evidence chain integrity
const verification = await client.evidence.verify(event.id);
console.log(`Chain valid: ${verification.valid}`);

// Run compliance check
const run = await client.compliance.run({
  framework: 'soc2',
  scope: { tenantId: 'tenant_abc' },
});

// Stream events (real-time)
for await (const evt of client.events.stream({ severity: ['high', 'critical'] })) {
  console.log(`New event: ${evt.title}`);
}
```

### Python

```python
from grc_claw import GRCclaw

client = GRCclaw(
    api_key=os.environ["GRC_CLAW_API_KEY"],
    tenant_id="tenant_abc",
    environment="production",
)

# Ingest an event
event = client.events.ingest(
    source="wazuh",
    severity="high",
    category="authentication",
    title="Failed login attempts",
    metadata={"source_ip": "203.0.113.42", "attempts": 5},
)

# Append evidence
evidence = client.evidence.append(
    event_id=event.id,
    evidence_type="log_entry",
    source="wazuh-agent",
    content={"log": "..."},
)

# Verify chain
verification = client.evidence.verify(event.id)
print(f"Chain valid: {verification.valid}")

# Run compliance verifier
run = client.compliance.run(framework="soc2", scope={"tenant_id": "tenant_abc"})

# Async support
import asyncio
async def stream_events():
    async for evt in client.events.stream(severity=["high", "critical"]):
        print(f"New event: {evt.title}")

asyncio.run(stream_events())
```

### Go

```go
package main

import (
    "context"
    "fmt"
    "os"

    grcclaw "github.com/grc-claw/go-sdk"
)

func main() {
    client := grcclaw.NewClient(
        grcclaw.WithAPIKey(os.Getenv("GRC_CLAW_API_KEY")),
        grcclaw.WithTenantID("tenant_abc"),
        grcclaw.WithEnvironment("production"),
    )

    ctx := context.Background()

    // Ingest an event
    event, err := client.Events.Ingest(ctx, &grcclaw.IngestRequest{
        Source:   "wazuh",
        Severity: "high",
        Category: "authentication",
        Title:    "Failed login attempts",
        Metadata: map[string]interface{}{
            "source_ip": "203.0.113.42",
            "attempts":  5,
        },
    })
    if err != nil {
        panic(err)
    }
    fmt.Printf("Event ID: %s\n", event.ID)

    // Append evidence
    evidence, err := client.Evidence.Append(ctx, &grcclaw.AppendRequest{
        EventID:      event.ID,
        EvidenceType: "log_entry",
        Source:       "wazuh-agent",
        Content:      map[string]interface{}{"log": "..."},
    })
    if err != nil {
        panic(err)
    }
    fmt.Printf("Evidence node: %s, valid: %v\n", evidence.NodeID, evidence.ChainValid)

    // Verify chain
    verification, err := client.Evidence.Verify(ctx, event.ID)
    if err != nil {
        panic(err)
    }
    fmt.Printf("Chain valid: %v\n", verification.Valid)
}
```

---

## 3. CLI Command Reference

### Installation

```bash
# npm
npm install -g @grc-claw/cli

# Homebrew
brew install grc-claw/tap/grc-claw

# Go
go install github.com/grc-claw/cli@latest
```

### Authentication

```bash
grc-claw auth login --email analyst@example.com --tenant tenant_abc
grc-claw auth status
grc-claw auth logout
```

### Event Management (6 commands)

```bash
grc-claw events list [--severity high] [--status open] [--limit 50]
grc-claw events get <event-id>
grc-claw events ingest --source wazuh --severity high --title "Failed login"
grc-claw events ingest --file events.json --batch
grc-claw events assign <event-id> --user analyst@example.com
grc-claw events resolve <event-id> --reason "False positive"
```

### Evidence Management (5 commands)

```bash
grc-claw evidence list <event-id>
grc-claw evidence append <event-id> --type log_entry --source wazuh
grc-claw evidence verify <event-id>
grc-claw evidence verify --all
grc-claw evidence export <event-id> --format json
```

### Compliance (5 commands)

```bash
grc-claw compliance run --framework soc2
grc-claw compliance runs [--limit 10]
grc-claw compliance run get <run-id>
grc-claw compliance run export <run-id> --format pdf
grc-claw compliance gaps [--framework iso27001]
```

### Connectors (4 commands)

```bash
grc-claw connectors list
grc-claw connectors test <connector-id>
grc-claw connectors enable <connector-id>
grc-claw connectors disable <connector-id>
```

### Detection Rules (3 commands)

```bash
grc-claw detections list [--status active]
grc-claw detections test <rule-id> --file sample-events.json
grc-claw detections simulate --rules-rule1,rule2 --events-file sample.json
```

### System & Admin (4 commands)

```bash
grc-claw system health
grc-claw system version
grc-claw system daemons
grc-claw system logs --daemon gateway --follow
```

### Global Options

```
--api-key <key>        Override API key (env: GRC_CLAW_API_KEY)
--tenant <id>          Override tenant (env: GRC_CLAW_TENANT)
--environment <env>    production | staging | development
--format <fmt>         json | table | csv | yaml
--output <file>        Write output to file
--verbose              Enable verbose logging
--no-color             Disable colored output
```

### Configuration

```bash
grc-claw config init                    # Create ~/.grc-claw/config.yaml
grc-claw config set api-key <key>       # Set API key
grc-claw config set tenant <id>         # Set default tenant
grc-claw config get                     # Show current config
grc-claw config list                    # List all config values
```

---

## 4. Terraform Provider

### Resources

```hcl
# Provider configuration
terraform {
  required_providers {
    grcclaw = {
      source  = "grc-claw/grcclaw"
      version = "~> 15.0"
    }
  }
}

provider "grcclaw" {
  api_key  = var.grc_claw_api_key
  tenant   = var.tenant_id
  base_url = "https://api.grc-claw.com/v1"
}

# Tenant
resource "grcclaw_tenant" "main" {
  name        = "production"
  plan        = "enterprise"
  settings {
    retention_days = 365
    max_events     = 1000000
  }
}

# Detection Rule
resource "grcclaw_detection_rule" "brute_force" {
  name        = "Brute Force Detection"
  description = "Detects brute force login attempts"
  severity    = "high"
  category    = "authentication"
  rule_type   = "threshold"
  condition = jsonencode({
    field    = "failed_attempts"
    operator = ">="
    value    = 5
    window   = "5m"
  })
  enabled = true
}

# Connector
resource "grcclaw_connector" "wazuh" {
  name     = "Wazuh SIEM"
  type     = "wazuh"
  enabled  = true
  config = jsonencode({
    host     = "wazuh.example.com"
    port     = 1514
    protocol = "tcp"
  })
  credentials = {
    api_key = var.wazuh_api_key
  }
}

# RBAC Role
resource "grcclaw_role" "analyst" {
  name        = "Security Analyst"
  description = "Standard analyst permissions"
  permissions = [
    "events:read",
    "events:write",
    "evidence:read",
    "evidence:append",
    "compliance:read",
  ]
}
```

### Data Sources

```hcl
# List events
data "grcclaw_events" "critical" {
  severity = ["critical", "high"]
  status   = ["new", "investigating"]
  limit    = 100
}

# Get compliance framework
data "grcclaw_framework" "soc2" {
  name = "soc2"
}

# Get connector health
data "grcclaw_connector" "wazuh" {
  id = grcclaw_connector.wazuh.id
}

# Output
output "critical_events_count" {
  value = length(data.grcclaw_events.critical.events)
}

output "soc2_controls_count" {
  value = length(data.grcclaw_framework.soc2.controls)
}
```

---

## 5. VS Code Extension

### Installation

Search for "GRC_Claw" in VS Code Marketplace or install via CLI:

```bash
code --install-extension grc-claw.vscode-grc-claw
```

### Features

| Feature | Description | Shortcut |
|---------|-------------|----------|
| Event Viewer | Browse and search events in sidebar | `Ctrl+Shift+E` |
| Evidence Inspector | View evidence chains with graph visualization | `Ctrl+Shift+V` |
| Compliance Status | Framework compliance score in status bar | — |
| Detection Rule Editor | Syntax highlighting + validation for rules | Auto |
| API Explorer | Test API endpoints from VS Code | `Ctrl+Shift+A` |
| Log Formatter | Format and parse GRC_Claw logs | `Ctrl+Shift+L` |
| Connector Status | Show connector health in sidebar | — |

### Configuration

```json
{
  "grc-claw.apiKey": "${env:GRC_CLAW_API_KEY}",
  "grc-claw.tenant": "tenant_abc",
  "grc-claw.environment": "production",
  "grc-claw.theme": "dark",
  "grc-claw.autoRefresh": true,
  "grc-claw.refreshInterval": 30000,
  "grc-claw.evidenceGraph.layout": "dagre",
  "grc-claw.evidenceGraph.showHash": true,
  "grc-claw.evidenceGraph.interactive": true
}
```

### Rules (`.vscode/grc-claw-rules.json`)

```json
{
  "rules": [
    {
      "id": "no-hardcoded-secrets",
      "pattern": "(api_key|secret|password)\\s*[=:]\\s*[\"'][^\"']+[\"']",
      "severity": "error",
      "message": "Hardcoded secret detected. Use environment variables or Vault."
    },
    {
      "id": "evidence-hash-required",
      "pattern": "appendEvidence\\(",
      "severity": "info",
      "message": "Ensure evidence is appended with hash_chain=true",
      "autoFix": true
    }
  ]
}
```

---

## 6. MCP Server Integration

### Configuration

Add to your MCP client configuration:

```json
{
  "mcpServers": {
    "grc-claw": {
      "command": "npx",
      "args": ["-y", "@grc-claw/mcp-server"],
      "env": {
        "GRC_CLAW_API_KEY": "${env:GRC_CLAW_API_KEY}",
        "GRC_CLAW_TENANT": "tenant_abc"
      }
    }
  }
}
```

### Available MCP Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `grc_claw_search_events` | Search security events | `query`, `severity?`, `status?`, `limit?` |
| `grc_claw_get_event` | Get event details with evidence chain | `event_id` |
| `grc_claw_get_evidence` | Get evidence chain for event | `event_id`, `verify?` |
| `grc_claw_verify_chain` | Verify evidence chain integrity | `event_id` |
| `grc_claw_run_compliance` | Run compliance check | `framework`, `scope?` |
| `grc_claw_get_compliance_status` | Get compliance dashboard | `framework?` |
| `grc_claw_list_connectors` | List connector status | `status?` |
| `grc_claw_get_detection_rules` | List detection rules | `status?`, `category?` |
| `grc_claw_get_system_health` | System health status | — |

### Usage Examples

```typescript
// Using MCP tools from Claude or other AI agents
const events = await mcp.callTool('grc_claw_search_events', {
  query: 'brute force login',
  severity: ['high', 'critical'],
  limit: 10,
});

const evidence = await mcp.callTool('grc_claw_get_evidence', {
  event_id: 'evt_01J0...',
  verify: true,
});

const compliance = await mcp.callTool('grc_claw_run_compliance', {
  framework: 'soc2',
  scope: { tenant_id: 'tenant_abc' },
});
```

### MCP Resources

| Resource URI | Description |
|-------------|-------------|
| `grcclaw://events/{id}` | Event details as MCP resource |
| `grcclaw://evidence/{id}` | Evidence chain as MCP resource |
| `grcclaw://compliance/{framework}` | Compliance status as MCP resource |
| `grcclaw://connectors` | Connector inventory as MCP resource |
| `grcclaw://system/health` | System health as MCP resource |

---

## 7. Contributing Guidelines

### Code Style

```yaml
# .editorconfig
root = true

[*]
indent_style = space
indent_size = 2
end_of_line = lf
charset = utf-8
trim_trailing_whitespace = true
insert_final_newline = true

[*.md]
trim_trailing_whitespace = false

[Makefile]
indent_style = tab
```

### TypeScript Conventions

```typescript
// 1. Use explicit return types for exported functions
export function createEvent(input: CreateEventInput): Promise<Event> {
  // ...
}

// 2. Use Zod for runtime validation
const CreateEventSchema = z.object({
  source: z.string().min(1).max(100),
  severity: z.enum(['low', 'medium', 'high', 'critical']),
  title: z.string().min(1).max(500),
  metadata: z.record(z.unknown()).optional(),
});

// 3. Use branded types for IDs
type EventId = string & { readonly __brand: 'EventId' };
function createEventId(raw: string): EventId {
  return raw as EventId;
}

// 4. Prefer named exports over default exports
export { createEvent, getEvent, listEvents };

// 5. No barrel files (index.ts re-exports) in src/
//    Import directly from the module file
```

### PR Process

```
1. Fork and create feature branch: feat/add-xyz or fix/resolve-abc
2. Make changes with tests (coverage ≥80% for new code)
3. Run linter: npm run lint
4. Run typecheck: npm run typecheck
5. Run tests: npm test
6. Run security scan: npm run security:check
7. Update documentation if API changes
8. Create PR with conventional commit title
9. Fill PR template completely
10. Request review from CODEOWNERS
11. Address review feedback
12. Squash merge after approval
```

### PR Template

```markdown
## Summary
<Brief description of changes>

## Type of Change
- [ ] Bug fix (non-breaking change)
- [ ] New feature (non-breaking change)
- [ ] Breaking change (fix or feature causing existing functionality to change)
- [ ] Documentation update
- [ ] Refactoring (no functional changes)

## Test Plan
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] E2E tests added/updated
- [ ] Manual testing performed

## Security Checklist
- [ ] No hardcoded secrets
- [ ] Input validation added
- [ ] RLS policies updated (if DB changes)
- [ ] RBAC permissions reviewed
- [ ] No new attack surface introduced

## Documentation
- [ ] API docs updated (if endpoint changes)
- [ ] README updated (if setup changes)
- [ ] ADR created (if architectural decision)

## Related Issues
Closes #<issue-number>
```

### Test Requirements

```
Unit Tests:
  - Every new function has unit tests
  - Edge cases and error paths covered
  - Mock external dependencies (DB, API calls)
  - Use: vitest (TypeScript), pytest (Python), testing (Go)

Integration Tests:
  - API endpoint tests with real Supabase (test project)
  - Evidence chain integrity tests
  - Policy evaluation tests
  - Use: vitest + supertest (TypeScript)

E2E Tests:
  - Critical user flows (login → ingest → evidence → compliance)
  - Multi-tenant isolation verification
  - Use: Playwright

Performance Tests:
  - Ingestion throughput (events/second)
  - API response times (p50, p95, p99)
  - Evidence chain verification latency
  - Use: k6
```

### Commit Convention

```
feat: add new feature
fix: resolve bug
docs: documentation changes
style: formatting changes (no logic change)
refactor: code restructuring (no behavior change)
test: adding or updating tests
chore: build process, CI/CD, tooling
perf: performance improvement
security: security fix or hardening

Examples:
feat(events): add batch ingestion endpoint
fix(evidence): resolve hash chain verification race condition
docs(api): add OpenAPI spec for compliance endpoints
security(auth): rotate JWT signing keys quarterly
```

### Development Workflow

```bash
# Setup
git clone https://github.com/grc-claw/grc-claw.git
cd grc-claw
cp .env.example .env
docker compose up -d
npm install
npm run db:migrate
npm run db:seed

# Development
npm run dev          # Start dev server with hot reload
npm run test:watch   # Run tests in watch mode
npm run lint:fix     # Auto-fix lint issues

# Before PR
npm run lint
npm run typecheck
npm test
npm run test:e2e
npm run security:check
```
