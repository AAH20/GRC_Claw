# GRC_Claw Developer Portal Design
# =================================
#
# This document defines the developer portal for GRC_Claw — the central hub
# for API documentation, SDK downloads, API key management, interactive
# exploration, and community support.
#
# Portal URL: https://portal.grc-claw.io

---

## 1. Portal Architecture

### 1.1 Technology Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| Frontend | Next.js 14 (React) | SSR, App Router, excellent DX |
| Styling | Tailwind CSS + shadcn/ui | Consistent, accessible components |
| API Docs | OpenAPI 3.1 + Scalar | Interactive API exploration |
| GraphQL Docs | GraphiQL / Apollo Studio | Schema introspection |
| Auth | NextAuth.js + GRC_Claw OIDC | SSO with GRC_Claw identity |
| Hosting | Vercel / Cloudflare Pages | Edge deployment, global CDN |
| CMS | Sanity / Contentful | Documentation content management |

### 1.2 Information Architecture

```
portal.grc-claw.io
├── /                          # Landing page
├── /docs                      # Documentation
│   ├── /getting-started       # Quick start guides
│   ├── /api-reference         # REST API reference (OpenAPI)
│   ├── /graphql              # GraphQL schema docs
│   ├── /grpc                  # gRPC service docs
│   ├── /webhooks              # Webhook event catalog
│   ├── /sdks                  # SDK documentation
│   │   ├── /python
│   │   ├── /typescript
│   │   ├── /go
│   │   ├── /java
│   │   └── /rust
│   ├── /guides                # How-to guides
│   │   ├── /authentication
│   │   ├── /policies
│   │   ├── /evidence
│   │   ├── /enforcement
│   │   ├── /assessments
│   │   ├── /compliance
│   │   └── /webhooks
│   ├── /tutorials             # Step-by-step tutorials
│   ├── /changelog             # API changelog
│   └── /migration             # Version migration guides
├── /api-explorer              # Interactive API explorer
├── /graphql-playground       # GraphQL playground
├── /dashboard                # Developer dashboard
│   ├── /api-keys              # API key management
│   ├── /usage                 # Usage analytics
│   ├── /webhooks              # Webhook management
│   ├── /logs                  # Request logs
│   └── /settings              # Account settings
├── /community                 # Community resources
│   ├── /forum                 # Discussion forum
│   ├── /discord               # Discord invite
│   ├── /github                # GitHub repository
│   └── /status                # API status page
└── /support                   # Support resources
    ├── /help-center           # FAQ and help articles
    ├── /contact               # Contact support
    └── /sla                   # SLA information
```

---

## 2. Page Designs

### 2.1 Landing Page

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  GRC_Claw Developer Portal                              [Sign In] [Docs]   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                     │   │
│  │          Governance, Risk & Compliance for Agentic AI              │   │
│  │                                                                     │   │
│  │     Build compliant AI systems with deterministic enforcement,     │   │
│  │     evidence-first design, and multi-framework mapping.            │   │
│  │                                                                     │   │
│  │     [Get Started]  [View API Reference]  [GitHub]                  │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Quick Start                                                        │   │
│  │                                                                     │   │
│  │  pip install grc-claw-sdk                                          │   │
│  │                                                                     │   │
│  │  from grc_claw import GRCClawClient                                 │   │
│  │                                                                     │   │
│  │  client = GRCClawClient(                                            │   │
│  │      api_key="grc_live_...",                                       │   │
│  │      tenant_id="org-acme",                                         │   │
│  │  )                                                                  │   │
│  │                                                                     │   │
│  │  decision = client.enforcement.decide(                              │   │
│  │      agent_id="agent-42",                                          │   │
│  │      action="read",                                                │   │
│  │      resource="s3://data/public/dataset.csv",                      │   │
│  │  )                                                                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │ REST API     │  │ GraphQL      │  │ gRPC         │  │ Webhooks     │   │
│  │ 40+ endpoints│  │ Nested queries│ │ Streaming    │  │ Event-driven │   │
│  │ [Explore →]  │  │ [Explore →]  │  │ [Explore →]  │  │ [Explore →]  │   │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Supported Frameworks                                               │   │
│  │                                                                     │   │
│  │  NIST 800-53  │  SOC 2  │  ISO 27001  │  ISO 42001  │  GDPR         │   │
│  │  HIPAA        │  PCI DSS │  COBIT      │  NIST AI RMF│  EU AI Act   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 API Reference Page

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  GRC_Claw Developer Portal    API Reference      [Search...]  [Sign In]    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─── Navigation ──────────────────────────────────────────────────────┐   │
│  │                                                                    │   │
│  │  Policies                                                          │   │
│  │    List Policies                                    GET /v1.0/policies│   │
│  │    Create Policy                                   POST /v1.0/policies│   │
│  │    Get Policy                                     GET /v1.0/policies/{id}│
│  │    Update Policy                                  PUT /v1.0/policies/{id}│
│  │    Delete Policy                               DELETE /v1.0/policies/{id}│
│  │    Compile Policy                              POST .../compile    │   │
│  │    Dry-Run Policy                              POST .../dry-run    │   │
│  │                                                                    │   │
│  │  Evidence                                                           │   │
│  │    Search Evidence                                 GET /v1.0/evidence│   │
│  │    Submit Evidence                                POST /v1.0/evidence│   │
│  │    ...                                                             │   │
│  │                                                                    │   │
│  │  Enforcement                                                        │   │
│  │    Request Decision                           POST /v1.0/enforcement/decide│
│  │    Batch Decisions                        POST /v1.0/enforcement/decide-batch│
│  │    ...                                                             │   │
│  │                                                                    │   │
│  │  Assessments                                                        │   │
│  │  Compliance                                                         │   │
│  │  Agents                                                             │   │
│  │  Audit                                                              │   │
│  │  Webhooks                                                           │   │
│  │                                                                    │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─── Content ────────────────────────────────────────────────────────┐   │
│  │                                                                    │   │
│  │  Request Enforcement Decision                    POST /v1.0/enforcement/decide│
│  │  ─────────────────────────────────────────────────────────────────  │   │
│  │                                                                    │   │
│  │  Evaluates agent action against policies and returns a decision.  │   │
│  │                                                                    │   │
│  │  ┌─ Request Body ──────────────────────────────────────────────┐   │   │
│  │  │ {                                                          │   │   │
│  │  │   "agent_id": "agent-42",                                  │   │   │
│  │  │   "action": "read",                                        │   │   │
│  │  │   "resource": "s3://data/public/dataset.csv",              │   │   │
│  │  │   "context": {                                             │   │   │
│  │  │     "time": "2026-10-01T14:30:00Z",                       │   │   │
│  │  │     "environment": "production"                            │   │   │
│  │  │   },                                                       │   │   │
│  │  │   "policy_ids": ["pol-001"],                               │   │   │
│  │  │   "include_evidence": true                                 │   │   │
│  │  │ }                                                          │   │   │
│  │  └────────────────────────────────────────────────────────────┘   │   │
│  │                                                                    │   │
│  │  ┌─ Response 200 ──────────────────────────────────────────────┐   │   │
│  │  │ {                                                          │   │   │
│  │  │   "decision_id": "dec-001",                                │   │   │
│  │  │   "verdict": "ALLOW",                                      │   │   │
│  │  │   "policy_id": "pol-001",                                  │   │   │
│  │  │   "policy_version": "1.2.0",                               │   │   │
│  │  │   "evaluation_time_ms": 2.3,                               │   │   │
│  │  │   "matched_rules": ["allow_read_public"]                  │   │   │
│  │  │ }                                                          │   │   │
│  │  └────────────────────────────────────────────────────────────┘   │   │
│  │                                                                    │   │
│  │  ┌─ Code Examples ─────────────────────────────────────────────┐   │   │
│  │  │ [Python] [TypeScript] [Go] [Java] [cURL]                    │   │   │
│  │  │                                                            │   │   │
│  │  │ decision = client.enforcement.decide(                      │   │   │
│  │  │     agent_id="agent-42",                                   │   │   │
│  │  │     action="read",                                         │   │   │
│  │  │     resource="s3://data/public/dataset.csv",               │   │   │
│  │  │     context={"environment": "production"},                  │   │   │
│  │  │ )                                                          │   │   │
│  │  └────────────────────────────────────────────────────────────┘   │   │
│  │                                                                    │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.3 API Explorer (Interactive)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  GRC_Claw Developer Portal    API Explorer   [Sign In to Try]              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─── Endpoint Selector ──────────────────────────────────────────────┐   │
│  │                                                                    │   │
│  │  Method: [POST ▼]  URL: [/v1.0/enforcement/decide          ]       │   │
│  │                                                                    │   │
│  │  ┌─ Headers ──────────────────────────────────────────────────┐   │   │
│  │  │ Authorization: Bearer [grc_live_...                    ]  │   │   │
│  │  │ X-Tenant-ID:    [org-acme                               ]  │   │   │
│  │  │ Content-Type:   [application/json                       ]  │   │   │
│  │  └────────────────────────────────────────────────────────────┘   │   │
│  │                                                                    │   │
│  │  ┌─ Body ────────────────────────────────────────────────────┐   │   │
│  │  │ {                                                          │   │   │
│  │  │   "agent_id": "agent-42",                                  │   │   │
│  │  │   "action": "read",                                        │   │   │
│  │  │   "resource": "s3://data/public/dataset.csv",              │   │   │
│  │  │   "context": {                                             │   │   │
│  │  │     "environment": "production"                            │   │   │
│  │  │   }                                                        │   │   │
│  │  │ }                                                          │   │   │
│  │  └────────────────────────────────────────────────────────────┘   │   │
│  │                                                                    │   │
│  │  [Send Request]                                                    │   │
│  │                                                                    │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─── Response ───────────────────────────────────────────────────────┐   │
│  │                                                                    │   │
│  │  Status: 200 OK    Time: 12ms    Size: 1.2 KB                     │   │
│  │                                                                    │   │
│  │  {                                                                 │   │
│  │    "decision_id": "dec-001",                                      │   │
│  │    "verdict": "ALLOW",                                            │   │
│  │    "policy_id": "pol-001",                                        │   │
│  │    "policy_version": "1.2.0",                                     │   │
│  │    "agent_id": "agent-42",                                        │   │
│  │    "action": "read",                                              │   │
│  │    "resource": "s3://data/public/dataset.csv",                    │   │
│  │    "evaluation_time_ms": 2.3,                                     │   │
│  │    "matched_rules": ["allow_read_public"],                       │   │
│  │    "timestamp": "2026-10-01T14:30:00.123Z",                      │   │
│  │    "ttl": 300,                                                    │   │
│  │    "signature": "ecdsa-p256:def456..."                           │   │
│  │  }                                                                 │   │
│  │                                                                    │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.4 Developer Dashboard

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  GRC_Claw Developer Portal    Dashboard              [user@acme.com ▼]      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─── Sidebar ────────────────────────────────────────────────────────┐    │
│  │                                                                    │    │
│  │  Dashboard                                                         │    │
│  │  API Keys                                                          │    │
│  │  Usage Analytics                                                   │    │
│  │  Webhooks                                                          │    │
│  │  Request Logs                                                      │    │
│  │  Settings                                                          │    │
│  │                                                                    │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  ┌─── Main Content ───────────────────────────────────────────────────┐    │
│  │                                                                    │    │
│  │  API Keys                                                          │    │
│  │  ────────────────────────────────────────────────────────────────  │    │
│  │                                                                    │    │
│  │  ┌────────────────────────────────────────────────────────────┐   │    │
│  │  │ Production Keys                                            │   │    │
│  │  │                                                            │   │    │
│  │  │ Key Name          Prefix       Created      Status          │   │    │
│  │  │ ────────────────────────────────────────────────────────── │   │    │
│  │  │ prod-api-key      grc_live_a1  2026-08-01   ● Active       │   │    │
│  │  │ prod-ci-cd        grc_live_b2  2026-09-15   ● Active       │   │    │
│  │  │                                                            │   │    │
│  │  │ [+ Create New Key]                                         │   │    │
│  │  └────────────────────────────────────────────────────────────┘   │    │
│  │                                                                    │    │
│  │  ┌────────────────────────────────────────────────────────────┐   │    │
│  │  │ Test Keys                                                  │   │    │
│  │  │                                                            │   │    │
│  │  │ Key Name          Prefix       Created      Status          │   │    │
│  │  │ ────────────────────────────────────────────────────────── │   │    │
│  │  │ test-api-key      grc_test_c3  2026-09-20   ● Active       │   │    │
│  │  │                                                            │   │    │
│  │  │ [+ Create New Key]                                         │   │    │
│  │  └────────────────────────────────────────────────────────────┘   │    │
│  │                                                                    │    │
│  │  Usage Analytics (Last 30 Days)                                   │    │
│  │  ────────────────────────────────────────────────────────────────  │    │
│  │                                                                    │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │    │
│  │  │ Total        │  │ Rate Limited │  │ Avg Latency  │              │    │
│  │  │ Requests     │  │ Requests     │  │              │              │    │
│  │  │              │  │              │  │              │              │    │
│  │  │ 1,247,892    │  │ 1,247        │  │ 12ms         │              │    │
│  │  │              │  │              │  │              │              │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘              │    │
│  │                                                                    │    │
│  │  ┌────────────────────────────────────────────────────────────┐   │    │
│  │  │ Usage by Endpoint                                          │   │    │
│  │  │                                                            │   │    │
│  │  │ /v1.0/enforcement/decide    ████████████████████  847,291  │   │    │
│  │  │ /v1.0/policies              ██████                249,578  │   │    │
│  │  │ /v1.0/evidence              ████                  124,789  │   │    │
│  │  │ /v1.0/agents                ██                     26,234  │   │    │
│  │  │                                                            │   │    │
│  │  └────────────────────────────────────────────────────────────┘   │    │
│  │                                                                    │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.5 Webhook Management

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  GRC_Claw Developer Portal    Webhooks               [user@acme.com ▼]      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─── Main Content ───────────────────────────────────────────────────┐    │
│  │                                                                    │    │
│  │  Webhook Subscriptions                                             │    │
│  │  ────────────────────────────────────────────────────────────────  │    │
│  │                                                                    │    │
│  │  ┌────────────────────────────────────────────────────────────┐   │    │
│  │  │ Production Webhooks                                        │   │    │
│  │  │                                                            │   │    │
│  │  │ URL                                    Events      Status  │   │    │
│  │  │ ────────────────────────────────────────────────────────── │   │    │
│  │  │ https://api.acme.com/hooks/grc      12 events   ● Active   │   │    │
│  │  │ https://hooks.slack.com/...          3 events   ● Active   │   │    │
│  │  │                                                            │   │    │
│  │  │ [+ Create Webhook]                                         │   │    │
│  │  └────────────────────────────────────────────────────────────┘   │    │
│  │                                                                    │    │
│  │  Delivery History (Last 7 Days)                                    │    │
│  │  ────────────────────────────────────────────────────────────────  │    │
│  │                                                                    │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │    │
│  │  │ Total        │  │ Successful   │  │ Failed       │              │    │
│  │  │ Deliveries   │  │ Deliveries   │  │ Deliveries   │              │    │
│  │  │              │  │              │  │              │              │    │
│  │  │ 12,478       │  │ 12,471       │  │ 7            │              │    │
│  │  │              │  │ (99.94%)     │  │ (0.06%)      │              │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘              │    │
│  │                                                                    │    │
│  │  ┌────────────────────────────────────────────────────────────┐   │    │
│  │  │ Recent Deliveries                                          │   │    │
│  │  │                                                            │   │    │
│  │  │ Time     Event                Status    Attempts  Duration │   │    │
│  │  │ ────────────────────────────────────────────────────────── │   │    │
│  │  │ 14:30:05 policy.created       ✅ 200     1         45ms     │   │    │
│  │  │ 14:30:03 enforcement.decision ✅ 200     1         38ms     │   │    │
│  │  │ 14:29:58 evidence.collected   ✅ 200     1         52ms     │   │    │
│  │  │ 14:29:55 policy.updated       ✅ 200     1         41ms     │   │    │
│  │  │ 14:29:50 agent.trust_score   ⚠️ 503→200  3         2.1s     │   │    │
│  │  │                                                            │   │    │
│  │  └────────────────────────────────────────────────────────────┘   │    │
│  │                                                                    │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. SDK Documentation Pages

### 3.1 Python SDK Page

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  GRC_Claw Developer Portal    SDKs > Python                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─── Navigation ──────────────────────────────────────────────────────┐   │
│  │  Python SDK                                                          │   │
│  │   Installation                                                       │   │
│  │   Quick Start                                                        │   │
│  │   Configuration                                                      │   │
│  │   Policies                                                           │   │
│  │   Evidence                                                           │   │
│  │   Enforcement                                                        │   │
│  │   Assessments                                                        │   │
│  │   Compliance                                                         │   │
│  │   Agents                                                             │   │
│  │   Audit                                                              │   │
│  │   Webhooks                                                           │   │
│  │   Error Handling                                                     │   │
│  │   Advanced Usage                                                     │   │
│  │   Async Support                                                      │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─── Content ────────────────────────────────────────────────────────┐   │
│  │                                                                    │   │
│  │  Python SDK                                                        │   │
│  │  ═══════════                                                       │   │
│  │                                                                    │   │
│  │  Installation                                                      │   │
│  │  ─────────────                                                     │   │
│  │                                                                    │   │
│  │  pip install grc-claw-sdk                                          │   │
│  │                                                                    │   │
│  │  Quick Start                                                        │   │
│  │  ──────────                                                        │   │
│  │                                                                    │   │
│  │  from grc_claw import GRCClawClient                                │   │
│  │                                                                    │   │
│  │  client = GRCClawClient(                                           │   │
│  │      api_key="grc_live_abc123...",                                 │   │
│  │      tenant_id="org-acme",                                         │   │
│  │      environment="production"                                      │   │
│  │  )                                                                 │   │
│  │                                                                    │   │
│  │  # Create a policy                                                 │   │
│  │  policy = client.policies.create(                                  │   │
│  │      policy_key="AI-ETHICS-001",                                   │   │
│  │      name="Data Access Control Policy",                            │   │
│  │      category="privacy",                                           │   │
│  │      cedar_policy='permit(principal, action, resource) when { ... }'│   │
│  │  )                                                                 │   │
│  │                                                                    │   │
│  │  # Request enforcement decision                                    │   │
│  │  decision = client.enforcement.decide(                             │   │
│  │      agent_id="agent-42",                                          │   │
│  │      action="read",                                                │   │
│  │      resource="s3://data/public/dataset.csv",                      │   │
│  │      context={"environment": "production"}                          │   │
│  │  )                                                                 │   │
│  │                                                                    │   │
│  │  if decision.verdict == "ALLOW":                                   │   │
│  │      print("Action allowed")                                       │   │
│  │                                                                    │   │
│  │  Configuration                                                     │   │
│  │  ──────────────                                                    │   │
│  │                                                                    │   │
│  │  client = GRCClawClient(                                           │   │
│  │      api_key="grc_live_...",          # Required                  │   │
│  │      tenant_id="org-acme",            # Required                  │   │
│  │      environment="production",        # production|staging|dev    │   │
│  │      timeout=30.0,                    # Request timeout (seconds)  │   │
│  │      max_retries=3,                   # Max retry attempts         │   │
│  │  )                                                                 │   │
│  │                                                                    │   │
│  │  Error Handling                                                     │   │
│  │  ──────────────                                                    │   │
│  │                                                                    │   │
│  │  from grc_claw import GRCClawClient, RateLimitError, NotFoundError │   │
│  │                                                                    │   │
│  │  try:                                                              │   │
│  │      policy = client.policies.get("pol-001")                       │   │
│  │  except NotFoundError:                                              │   │
│  │      print("Policy not found")                                     │   │
│  │  except RateLimitError as e:                                       │   │
│  │      print(f"Rate limited. Retry after {e.retry_after}s")          │   │
│  │                                                                    │   │
│  │  Async Support                                                      │   │
│  │  ───────────                                                       │   │
│  │                                                                    │   │
│  │  from grc_claw import AsyncGRCClawClient                           │   │
│  │                                                                    │   │
│  │  async with AsyncGRCClawClient(api_key="...", tenant_id="...") as client:│
│  │      decision = await client.enforcement.decide(...)               │   │
│  │                                                                    │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. API Key Management

### 4.1 Key Creation Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Create API Key                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Key Name:        [Production API Key                        ]              │
│                                                                             │
│  Environment:     (•) Production  ( ) Test                                  │
│                                                                             │
│  Scopes:                                                                  │
│  [✓] policies:read    [✓] policies:write                                   │
│  [✓] evidence:read    [✓] evidence:write                                   │
│  [✓] enforcement:decide                                                     │
│  [✓] assessments:read  [ ] assessments:write                               │
│  [✓] compliance:read   [ ] compliance:write                                 │
│  [✓] agents:read       [ ] agents:write                                     │
│  [✓] audit:read                                                            │
│  [ ] webhooks:manage                                                        │
│                                                                             │
│  Rate Limit Tier: [Standard ▼]                                              │
│                   Free: 10 req/s, 10K req/day                                │
│                   Standard: 100 req/s, 1M req/day                           │
│                   Enterprise: 1000 req/s, 10M req/day                       │
│                                                                             │
│  Expiration:      [Never ▼]                                                 │
│                   Never / 30 days / 90 days / 1 year                        │
│                                                                             │
│  IP Allowlist:    [                              ]                          │
│                   Optional: Comma-separated IP addresses or CIDR ranges     │
│                                                                             │
│  [Cancel]  [Create Key]                                                     │
│                                                                             │
│  ⚠️  Your API key will only be shown once. Store it securely.              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Key Display (One-Time)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  API Key Created Successfully                                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Your API key:                                                              │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ grc_live_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6  📋  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ⚠️  This is the only time your API key will be displayed.                 │
│      Store it securely. You can create a new key at any time.               │
│                                                                             │
│  [Copy to Clipboard]  [Done]                                                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Interactive API Explorer

### 5.1 Features

| Feature | Description |
|---------|-------------|
| **Endpoint Browser** | Browse all 40+ endpoints by category |
| **Request Builder** | Build requests with auto-completion |
| **Response Viewer** | Syntax-highlighted JSON response viewer |
| **Code Generation** | Generate code snippets in Python, TypeScript, Go, Java, cURL |
| **Authentication** | Auto-inject API key from logged-in session |
| **History** | View recent API calls |
| **Save & Share** | Save request configurations and share via URL |

### 5.2 Code Generation Examples

The API explorer generates code snippets for each endpoint:

```python
# Python
from grc_claw import GRCClawClient

client = GRCClawClient(
    api_key="grc_live_...",
    tenant_id="org-acme",
)

decision = client.enforcement.decide(
    agent_id="agent-42",
    action="read",
    resource="s3://data/public/dataset.csv",
    context={"environment": "production"},
)
```

```typescript
// TypeScript
import { GRCClawClient } from '@grc-claw/sdk';

const client = new GRCClawClient({
  apiKey: 'grc_live_...',
  tenantId: 'org-acme',
});

const decision = await client.enforcement.decide({
  agentId: 'agent-42',
  action: 'read',
  resource: 's3://data/public/dataset.csv',
  context: { environment: 'production' },
});
```

```bash
# cURL
curl -X POST https://api.grc-claw.io/v1.0/enforcement/decide \
  -H "Authorization: Bearer grc_live_..." \
  -H "X-Tenant-ID: org-acme" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "agent-42",
    "action": "read",
    "resource": "s3://data/public/dataset.csv",
    "context": {"environment": "production"}
  }'
```

---

## 6. Documentation Content Structure

### 6.1 Getting Started

| Page | Content |
|------|---------|
| Introduction | What is GRC_Claw? Why agent governance? |
| Quick Start | Create first policy, get first decision in 5 minutes |
| Authentication | OAuth 2.1, API keys, mTLS setup |
| Core Concepts | Policies, Evidence, Enforcement, Assessments, Compliance |
| Architecture | PEP/PDP separation, deterministic enforcement |

### 6.2 API Reference

| Page | Content |
|------|---------|
| Overview | API design principles, versioning, error format |
| Authentication | Token management, API key scopes, mTLS |
| Rate Limiting | Tiers, headers, best practices |
| Policies | CRUD, compile, dry-run, versions, dependencies |
| Evidence | Submit, search, verify, export |
| Enforcement | Single, batch, streaming decisions |
| Assessments | CRUD, findings, reports |
| Compliance | Frameworks, controls, posture, crosswalk |
| Agents | Registry, trust scores, policy bindings |
| Audit | Query, verify chain |
| Webhooks | Subscriptions, delivery, signatures |
| GraphQL | Schema, queries, mutations, subscriptions |
| gRPC | Services, messages, streaming |

### 6.3 Guides

| Guide | Description |
|-------|-------------|
| Authentication Deep Dive | OAuth 2.1 flows, token refresh, mTLS |
| Policy Authoring | Cedar syntax, Rego compilation, best practices |
| Evidence Collection | Automated collection, verification levels |
| Enforcement Integration | PEP/PDP patterns, agent SDK integration |
| Assessment Workflows | Risk, compliance, maturity assessments |
| Compliance Mapping | Multi-framework mapping, crosswalk queries |
| Webhook Integration | Subscription management, retry handling |
| CI/CD Integration | Policy as code, automated compliance checks |
| Multi-Tenant Setup | Tenant isolation, RBAC configuration |

### 6.4 Tutorials

| Tutorial | Duration | Difficulty |
|----------|----------|------------|
| Your First Policy | 10 min | Beginner |
| Agent Enforcement Integration | 20 min | Intermediate |
| Compliance Dashboard | 30 min | Intermediate |
| Evidence Collection Pipeline | 45 min | Advanced |
| Multi-Framework Mapping | 30 min | Advanced |
| CI/CD Compliance Gates | 45 min | Advanced |

---

## 7. Community & Support

### 7.1 Community Resources

| Resource | URL | Description |
|----------|-----|-------------|
| GitHub | github.com/grc-claw/grc-claw | Source code, issues, PRs |
| Discord | discord.gg/grc-claw | Real-time community chat |
| Forum | community.grc-claw.io | Discussions, Q&A |
| Stack Overflow | [grc-claw] tag | Technical questions |
| Blog | blog.grc-claw.io | Updates, tutorials, case studies |

### 7.2 Support Channels

| Channel | Availability | Response Time |
|---------|-------------|---------------|
| Community Discord | 24/7 | Best effort |
| GitHub Issues | 24/7 | 48 hours |
| Email Support | Business hours | 24 hours (Standard), 4 hours (Enterprise) |
| Dedicated Slack | Business hours | 1 hour (Enterprise) |
| Phone | Business hours | Immediate (Enterprise Critical) |

### 7.3 Status Page

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  GRC_Claw API Status                                          All Systems │
│                                                                 Operational │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  API (REST)          ● Operational    99.99% uptime (30d)                  │
│  API (GraphQL)       ● Operational    99.99% uptime (30d)                  │
│  API (gRPC)          ● Operational    99.99% uptime (30d)                  │
│  Webhooks            ● Operational    99.95% uptime (30d)                  │
│  Auth Service        ● Operational    99.99% uptime (30d)                  │
│  Developer Portal    ● Operational    99.99% uptime (30d)                  │
│                                                                             │
│  ┌─ Incident History ──────────────────────────────────────────────────┐   │
│  │                                                                    │   │
│  │  Oct 1, 2026  —  No incidents                                      │   │
│  │  Sep 15, 2026 —  Minor latency spike (resolved in 15 min)          │   │
│  │  Sep 1, 2026  —  No incidents                                      │   │
│  │                                                                    │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Subscribe to updates: [Email] [RSS] [Webhook] [Slack]                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 8. Portal Features Summary

### 8.1 Developer Experience

| Feature | Description |
|---------|-------------|
| **Interactive API Explorer** | Try endpoints directly in the browser |
| **Multi-Language Code Snippets** | Python, TypeScript, Go, Java, cURL |
| **SDK Downloads** | One-click install for all SDKs |
| **API Key Management** | Create, rotate, revoke keys |
| **Usage Analytics** | Real-time usage dashboards |
| **Webhook Testing** | Test webhook deliveries in-browser |
| **Request Logs** | Debug API calls with full request/response |
| **Schema Downloads** | OpenAPI, GraphQL SDL, Protobuf |

### 8.2 Content Features

| Feature | Description |
|---------|-------------|
| **Search** | Full-text search across all docs |
| **Version Selector** | Switch between API versions |
| **Dark Mode** | Toggle light/dark theme |
| **Copy One-Click** | Copy code snippets with one click |
| **Feedback** | Rate docs pages, suggest improvements |
| **Changelog** | Track API changes and deprecations |
| **Migration Guides** | Step-by-step version migration |

### 8.3 Account Features

| Feature | Description |
|---------|-------------|
| **Organizations** | Multi-team management |
| **Role-Based Access** | Admin, Developer, Viewer roles |
| **Audit Log** | Track all portal actions |
| **Notifications** | Email, Slack, webhook notifications |
| **API Key Scopes** | Granular permission control |
| **Custom Domains** | White-label for enterprise |

---

*End of Developer Portal Design*
