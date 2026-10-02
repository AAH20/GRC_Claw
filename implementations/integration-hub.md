# Integration Hub Architecture — Agentic AI Marketing

> **Version:** 1.0  
> **Date:** 2026-10-01  
> **Status:** Design  
> **Owner:** Ahmed Hassan  

---

## Table of Contents

1. [Integration Hub Architecture](#1-integration-hub-architecture)
2. [API Gateway and Routing](#2-api-gateway-and-routing)
3. [Connector SDK and Framework](#3-connector-sdk-and-framework)
4. [Pre-built Connectors](#4-pre-built-connectors)
5. [Data Transformation and Mapping](#5-data-transformation-and-mapping)
6. [Rate Limiting and Throttling](#6-rate-limiting-and-throttling)
7. [Error Handling and Retry Logic](#7-error-handling-and-retry-logic)
8. [Integration Monitoring](#8-integration-monitoring)
9. [Implementation Roadmap](#9-implementation-roadmap)

---

## 1. Integration Hub Architecture

### 1.1 Overview

The Integration Hub is the central nervous system of the agentic AI marketing platform. It provides a unified, extensible layer that connects 1,500+ external applications — ad platforms, CRMs, marketing automation, analytics, and custom tools — to the AI agent orchestration engine. The hub abstracts away API heterogeneity, authentication diversity, and rate-limit fragmentation behind a single, consistent interface.

### 1.2 Design Principles

| Principle | Description |
|---|---|
| **Uniform Abstraction** | Every connector implements the same `BaseConnector` interface regardless of the underlying API style (REST, GraphQL, gRPC, SOAP, webhook). |
| **Pluggability** | New connectors are added by dropping a connector module into the registry — no changes to the core hub. |
| **Agent-First** | All operations are exposed as typed, schema-validated tools that AI agents can discover and invoke via function calling. |
| **Event-Driven** | Supports both synchronous request/response and asynchronous event streaming (webhooks, SSE, polling). |
| **Multi-Tenant** | Each tenant (client workspace) gets isolated credentials, rate-limit budgets, and data partitions. |
| **Observability by Default** | Every call is traced, logged, and metered — no connector is a black box. |
| **Graceful Degradation** | If a connector fails, the hub falls back to cached data, queued retries, or alternative connectors. |

### 1.3 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        AI Agent Orchestrator                         │
│  (Tool Discovery → Schema Validation → Function Calling → Planner)  │
└──────────────────────────────┬──────────────────────────────────────┘
                               │  Tool Invocation (JSON-RPC / MCP)
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        Integration Hub Core                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌───────────────────┐  │
│  │  Router  │  │  Auth    │  │  Rate    │  │  Transformation   │  │
│  │  Engine  │  │  Manager │  │  Limiter │  │  Engine           │  │
│  └──────────┘  └──────────┘  └──────────┘  └───────────────────┘  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌───────────────────┐  │
│  │  Retry   │  │  Cache   │  │  Event   │  │  Schema           │  │
│  │  Engine  │  │  Layer   │  │  Bus     │  │  Registry         │  │
│  └──────────┘  └──────────┘  └──────────┘  └───────────────────┘  │
└──────────────────────────────┬──────────────────────────────────────┘
                               │  Connector Protocol
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     Connector Registry (1,500+)                      │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌──────┐ │
│  │  Meta  │ │ Google │ │LinkedIn│ │Salesfo │ │HubSpot │ │ ...  │ │
│  │Ads/Mgr │ │ Ads/   │ │  Ads/  │ │  rce   │ │        │ │      │ │
│  │        │ │Analytics│ │  API   │ │        │ │        │ │      │ │
│  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘ └──────┘ │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌──────┐ │
│  │GoHigh- │ │Shopify │ │Stripe  │ │Zapier  │ │Custom  │ │ ...  │ │
│  │ Level  │ │        │ │        │ │        │ │Webhook │ │      │ │
│  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘ └──────┘ │
└─────────────────────────────────────────────────────────────────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   External APIs      │
                    │  (1,500+ platforms)  │
                    └─────────────────────┘
```

### 1.4 Core Components

#### 1.4.1 Router Engine
- Receives tool invocations from the AI agent orchestrator.
- Resolves the target connector by name or capability (e.g., "create_ad_campaign" → Meta, Google, or LinkedIn).
- Supports **capability-based routing**: if the agent requests "publish_social_post," the router selects the best connector based on tenant config, connector health, and cost.
- Maintains a **routing table** mapping capabilities → connector priorities.

#### 1.4.2 Auth Manager
- Centralized credential vault (HashiCorp Vault / AWS Secrets Manager).
- Supports OAuth 1.0a, OAuth 2.0 (authorization code, client credentials, PKCE), API keys, JWT, mTLS, and custom auth flows.
- Automatic token refresh with configurable pre-expiry windows.
- Credential rotation without downtime (dual-key overlap).
- Per-tenant, per-connector credential isolation.

#### 1.4.3 Rate Limiter
- Token-bucket and sliding-window algorithms.
- Per-connector, per-tenant, and global rate limits.
- Respects provider-specific rate-limit headers (`X-RateLimit-Remaining`, `Retry-After`).
- See [Section 6](#6-rate-limiting-and-throttling) for details.

#### 1.4.4 Transformation Engine
- Schema-aware data mapping between canonical internal models and provider-specific formats.
- Supports field mapping, value transformation, and computed fields.
- See [Section 5](#5-data-transformation-and-mapping) for details.

#### 1.4.5 Retry Engine
- Configurable retry policies per connector and per operation type.
- Exponential backoff with jitter, circuit breaker pattern, and dead-letter queues.
- See [Section 7](#7-error-handling-and-retry-logic) for details.

#### 1.4.6 Cache Layer
- Multi-tier caching: in-memory (LRU) → Redis → persistent store.
- Caches OAuth tokens, schema definitions, reference data, and idempotent operation results.
- TTL-based and event-based invalidation.

#### 1.4.7 Event Bus
- Apache Kafka / AWS EventBridge for asynchronous event flow.
- Webhook ingestion from external platforms → normalized events → agent-consumable stream.
- Supports event replay, ordering guarantees, and dead-letter topics.

#### 1.4.8 Schema Registry
- Central repository of all connector input/output schemas (JSON Schema / OpenAPI).
- Versioned schemas with backward-compatibility checks.
- Agent tool discovery: the orchestrator queries the registry to build the tool catalog.

### 1.5 Data Flow

```
Agent Request → Orchestrator → Hub Router → Auth Check → Rate Limit Check
    → Schema Validation → Transformation → Connector Execution
    → Response Transformation → Cache Update → Agent Response
```

For asynchronous flows:
```
External Webhook → Event Bus → Event Normalizer → Agent Notification
    → Agent Decision → Hub Router → Connector Execution → Response
```

### 1.6 Technology Stack

| Layer | Technology |
|---|---|
| Hub Core | Python 3.12+ / FastAPI |
| Async Runtime | asyncio + uvloop |
| Event Bus | Apache Kafka (MSK) / AWS EventBridge |
| Cache | Redis Cluster (ElastiCache) |
| Credential Vault | HashiCorp Vault |
| Schema Registry | Confluent Schema Registry / custom |
| Observability | OpenTelemetry + Prometheus + Grafana + Jaeger |
| Deployment | Kubernetes (EKS) with Helm |
| CI/CD | GitHub Actions |
| Infrastructure | Terraform |

---

## 2. API Gateway and Routing

### 2.1 Gateway Architecture

The API Gateway is the single entry point for all traffic entering the Integration Hub — from AI agent orchestrators, from external webhooks, and from the management console.

```
                         ┌──────────────────────┐
                         │   Load Balancer      │
                         │   (AWS ALB / NGINX)  │
                         └──────────┬───────────┘
                                    │
                         ┌──────────▼───────────┐
                         │   API Gateway        │
                         │   (Kong / AWS API    │
                         │    Gateway / Envoy)  │
                         └──────────┬───────────┘
                                    │
              ┌─────────────────────┼─────────────────────┐
              │                     │                     │
    ┌─────────▼─────────┐ ┌────────▼────────┐ ┌─────────▼─────────┐
    │  Agent-Facing API │ │  Webhook Ingest │ │  Management API   │
    │  (MCP / JSON-RPC) │ │  (REST / SSE)   │ │  (REST / gRPC)    │
    └─────────┬─────────┘ └────────┬────────┘ └─────────┬─────────┘
              │                     │                     │
              └─────────────────────┼─────────────────────┘
                                    │
                         ┌──────────▼───────────┐
                         │   Hub Core Services   │
                         └──────────────────────┘
```

### 2.2 Agent-Facing API

The agent-facing API uses the **Model Context Protocol (MCP)** as the primary transport, with JSON-RPC 2.0 as a fallback.

#### 2.2.1 MCP Tool Discovery

```json
{
  "method": "tools/list",
  "result": {
    "tools": [
      {
        "name": "meta.create_campaign",
        "description": "Create a new ad campaign on Meta (Facebook/Instagram)",
        "inputSchema": {
          "type": "object",
          "properties": {
            "name": { "type": "string" },
            "objective": { "enum": ["AWARENESS", "TRAFFIC", "CONVERSIONS"] },
            "budget": { "type": "number", "minimum": 1 },
            "start_date": { "type": "string", "format": "date" },
            "end_date": { "type": "string", "format": "date" }
          },
          "required": ["name", "objective", "budget"]
        }
      }
    ]
  }
}
```

#### 2.2.2 Tool Invocation

```json
{
  "method": "tools/call",
  "params": {
    "name": "meta.create_campaign",
    "arguments": {
      "name": "Q4 Product Launch",
      "objective": "CONVERSIONS",
      "budget": 500.00,
      "start_date": "2026-10-15",
      "end_date": "2026-11-15"
    }
  }
}
```

#### 2.2.3 Response Format

```json
{
  "content": [
    {
      "type": "text",
      "text": "{\"campaign_id\": \"123456789\", \"status\": \"ACTIVE\", \"created_at\": \"2026-10-01T12:00:00Z\"}"
    }
  ],
  "isError": false,
  "metadata": {
    "connector": "meta",
    "operation": "create_campaign",
    "duration_ms": 342,
    "trace_id": "abc123"
  }
}
```

### 2.3 Webhook Ingestion

External platforms push events to the hub via webhooks.

#### 2.3.1 Webhook Endpoint Structure

```
POST /v1/webhooks/{connector}/{tenant_id}
```

Example: `POST /v1/webhooks/meta/tenant_abc123`

#### 2.3.2 Webhook Processing Pipeline

```
Webhook Received → Signature Verification → Deduplication
    → Schema Validation → Event Normalization → Event Bus Publish
    → Agent Notification (if subscribed)
```

#### 2.3.3 Signature Verification

| Platform | Method |
|---|---|
| Meta | HMAC-SHA256 signature in `X-Hub-Signature-256` header |
| Google | JWT-based verification with Google's public keys |
| LinkedIn | OAuth 2.0 token validation |
| Salesforce | HMAC signature using consumer secret |
| HubSpot | HMAC-SHA256 signature in `X-HubSpot-Signature` header |
| Stripe | Webhook signing secret |
| GoHighLevel | Custom HMAC signature |

### 2.4 Management API

RESTful API for connector lifecycle management:

| Endpoint | Method | Description |
|---|---|---|
| `/v1/connectors` | GET | List all available connectors |
| `/v1/connectors/{id}` | GET | Get connector details and health |
| `/v1/connectors/{id}/enable` | POST | Enable a connector for a tenant |
| `/v1/connectors/{id}/disable` | POST | Disable a connector |
| `/v1/connectors/{id}/config` | PUT | Update connector configuration |
| `/v1/connectors/{id}/test` | POST | Test connector connectivity |
| `/v1/tenants/{id}/credentials` | PUT | Store/update credentials |
| `/v1/tenants/{id}/mappings` | PUT | Configure data mappings |
| `/v1/audit-log` | GET | Query audit trail |

### 2.5 Routing Strategies

#### 2.5.1 Direct Routing
Agent specifies the exact connector: `meta.create_campaign` → Meta connector.

#### 2.5.2 Capability-Based Routing
Agent specifies a capability: `create_ad_campaign` → Router selects the best connector based on:
- Tenant's enabled connectors
- Connector health score
- Cost per operation
- Historical success rate
- Rate-limit headroom

#### 2.5.3 Fallback Routing
If the primary connector fails, the router automatically falls back to the next-best connector for the same capability.

#### 2.5.4 Multi-Connector Fan-Out
For operations like "publish to all social platforms," the router fans out to multiple connectors in parallel and aggregates results.

### 2.6 Request/Response Transformation at the Gateway

The gateway performs lightweight transformation:
- **Request**: JSON → internal canonical format
- **Response**: internal canonical format → JSON (or MCP content blocks)
- **Error normalization**: All connector errors → unified error format

```json
{
  "error": {
    "code": "RATE_LIMITED",
    "message": "Meta API rate limit exceeded. Retry after 300s.",
    "connector": "meta",
    "retryable": true,
    "retry_after": 300
  }
}
```

---

## 3. Connector SDK and Framework

### 3.1 SDK Philosophy

The Connector SDK enables rapid development of new connectors with minimal boilerplate. A developer only needs to:
1. Define the connector's capabilities (operations).
2. Implement the operation handlers.
3. Declare the input/output schemas.
4. Configure authentication.

The SDK handles: rate limiting, retry, caching, logging, metrics, error normalization, and schema registration automatically.

### 3.2 SDK Structure

```
connector-sdk/
├── base/
│   ├── base_connector.py       # Abstract base class
│   ├── base_auth.py            # Auth provider base classes
│   ├── base_schema.py          # Schema definition helpers
│   └── base_operation.py       # Operation definition
├── runtime/
│   ├── executor.py             # Operation execution engine
│   ├── rate_limiter.py         # Rate limiting middleware
│   ├── retry.py                # Retry middleware
│   ├── cache.py                # Caching middleware
│   └── telemetry.py            # Metrics and tracing
├── auth/
│   ├── oauth2.py               # OAuth 2.0 flows
│   ├── oauth1.py               # OAuth 1.0a
│   ├── api_key.py              # API key auth
│   ├── jwt.py                  # JWT bearer auth
│   └── mTLS.py                 # Mutual TLS
├── schema/
│   ├── registry.py             # Schema registration client
│   └── validator.py            # Input/output validation
├── events/
│   ├── webhook_handler.py      # Webhook ingestion base
│   └── event_normalizer.py     # Event normalization
├── testing/
│   ├── mock_server.py          # Mock external API server
│   ├── fixtures.py             # Test data fixtures
│   └── test_harness.py         # Connector test runner
└── cli/
    ├── scaffold.py             # Generate new connector from template
    ├── validate.py             # Validate connector schema
    └── publish.py              # Publish connector to registry
```

### 3.3 BaseConnector Interface

```python
from connector_sdk import BaseConnector, Operation, AuthProvider
from connector_sdk.schema import Schema, Field, String, Number, Boolean
from connector_sdk.auth import OAuth2Provider

class MetaAdsConnector(BaseConnector):
    """Meta (Facebook) Ads API connector."""

    name = "meta_ads"
    display_name = "Meta Ads"
    version = "2.0.0"
    description = "Manage Meta (Facebook/Instagram) ad campaigns, ad sets, and ads."

    auth = OAuth2Provider(
        authorize_url="https://www.facebook.com/v18.0/dialog/oauth",
        token_url="https://graph.facebook.com/v18.0/oauth/access_token",
        scopes=["ads_management", "ads_read", "business_management"],
        refresh_window_minutes=30,
    )

    operations = [
        Operation(
            name="create_campaign",
            description="Create a new ad campaign",
            input_schema=Schema(
                fields=[
                    Field("name", String, required=True, max_length=128),
                    Field("objective", String, required=True,
                          enum=["AWARENESS", "TRAFFIC", "CONVERSIONS", "LEAD_GENERATION"]),
                    Field("budget", Number, required=True, minimum=0.01),
                    Field("budget_type", String, default="daily", enum=["daily", "lifetime"]),
                    Field("start_date", String, required=True, format="date"),
                    Field("end_date", String, required=False, format="date"),
                    Field("status", String, default="PAUSED", enum=["ACTIVE", "PAUSED"]),
                ]
            ),
            output_schema=Schema(
                fields=[
                    Field("campaign_id", String),
                    Field("status", String),
                    Field("created_at", String, format="date-time"),
                ]
            ),
            rate_limit_weight=10,
            retry_policy="standard",
            cache_ttl=0,  # No cache for write operations
        ),
        Operation(
            name="get_campaign_insights",
            description="Retrieve performance metrics for a campaign",
            input_schema=Schema(
                fields=[
                    Field("campaign_id", String, required=True),
                    Field("date_range", String, required=True, enum=["today", "last_7d", "last_30d", "custom"]),
                    Field("metrics", String, required=False, default="impressions,clicks,spend,conversions"),
                ]
            ),
            output_schema=Schema(
                fields=[
                    Field("campaign_id", String),
                    Field("metrics", Object),
                    Field("date_range", Object),
                ]
            ),
            rate_limit_weight=5,
            retry_policy="standard",
            cache_ttl=300,  # Cache for 5 minutes
        ),
        # ... more operations
    ]

    async def execute(self, operation: str, params: dict, context: dict) -> dict:
        """Execute an operation against the Meta Graph API."""
        auth_token = await self.auth.get_token(context["tenant_id"])
        url = f"{self.api_base}/{operation}"
        
        response = await self.http_client.post(
            url,
            headers={"Authorization": f"Bearer {auth_token}"},
            json=self._transform_params(operation, params),
        )
        
        return self._transform_response(operation, response.json())
```

### 3.4 Operation Definition

Each operation declares:

| Property | Description |
|---|---|
| `name` | Unique operation identifier |
| `description` | Human-readable description (used by AI agents) |
| `input_schema` | JSON Schema for input validation |
| `output_schema` | JSON Schema for output validation |
| `rate_limit_weight` | Relative cost for rate-limit budgeting |
| `retry_policy` | Retry strategy: `none`, `standard`, `aggressive`, `custom` |
| `cache_ttl` | Cache duration in seconds (0 = no cache) |
| `timeout` | Request timeout in seconds |
| `idempotent` | Whether the operation is safe to retry |
| `webhook_events` | Events this operation can trigger |

### 3.5 Authentication Providers

#### 3.5.1 OAuth 2.0 (Authorization Code + PKCE)

```python
OAuth2Provider(
    authorize_url="https://provider.com/oauth/authorize",
    token_url="https://provider.com/oauth/token",
    scopes=["scope1", "scope2"],
    pkce=True,  # Use PKCE for enhanced security
    refresh_window_minutes=30,  # Refresh 30 min before expiry
)
```

#### 3.5.2 OAuth 2.0 (Client Credentials)

```python
OAuth2Provider(
    token_url="https://provider.com/oauth/token",
    client_credentials=True,
    scopes=["scope1"],
)
```

#### 3.5.3 API Key

```python
APIKeyProvider(
    key_name="X-API-Key",
    key_location="header",  # or "query"
)
```

#### 3.5.4 Custom Auth

```python
class CustomAuthProvider(AuthProvider):
    async def get_auth_headers(self, context: dict) -> dict:
        token = await self.vault.get_secret(context["tenant_id"], "custom_token")
        return {"X-Custom-Auth": token}
```

### 3.6 Middleware Pipeline

Every operation execution passes through a middleware pipeline:

```
Input → Schema Validation → Auth Check → Rate Limit Check
    → Cache Lookup → Retry Wrapper → HTTP Execution
    → Cache Store → Output Validation → Telemetry → Output
```

Each middleware is composable and configurable per operation.

### 3.7 Connector CLI

```bash
# Scaffold a new connector
connector-cli scaffold --name "my_connector" --template rest-api

# Validate connector schema
connector-cli validate ./connectors/my_connector/

# Run tests against mock server
connector-cli test ./connectors/my_connector/ --mock

# Publish to connector registry
connector-cli publish ./connectors/my_connector/ --version 1.0.0
```

### 3.8 Connector Lifecycle

```
Development → Validation → Testing (Mock) → Testing (Sandbox)
    → Staging → Production → Monitoring → Deprecation → Removal
```

Each stage has automated gates:
- **Validation**: Schema correctness, security scan, linting.
- **Mock Testing**: All operations tested against mock server.
- **Sandbox Testing**: Real API calls against provider sandbox.
- **Staging**: Limited production traffic with synthetic data.
- **Production**: Full traffic with monitoring and alerting.

---

## 4. Pre-built Connectors

### 4.1 Connector Catalog

The following connectors are available out-of-the-box. Each connector is versioned independently and can be updated without hub redeployment.

### 4.2 Ad Platforms

#### 4.2.1 Meta (Facebook & Instagram) Ads

| Operation | Description | Rate Limit Weight |
|---|---|---|
| `create_campaign` | Create a new ad campaign | 10 |
| `update_campaign` | Modify campaign settings | 5 |
| `delete_campaign` | Delete a campaign | 5 |
| `get_campaign` | Retrieve campaign details | 2 |
| `list_campaigns` | List all campaigns | 3 |
| `create_ad_set` | Create an ad set within a campaign | 10 |
| `update_ad_set` | Modify ad set (budget, targeting, schedule) | 5 |
| `create_ad` | Create a creative ad | 10 |
| `get_ad_insights` | Retrieve performance metrics | 5 |
| `get_account_insights` | Account-level aggregated metrics | 5 |
| `create_audience` | Create a custom audience | 8 |
| `update_audience` | Add/remove users from audience | 8 |
| `create_custom_conversion` | Set up custom conversion tracking | 5 |

**Auth**: OAuth 2.0 (Business Login)  
**API Version**: Graph API v18.0  
**Webhook Events**: `ad_account_update`, `campaign_status_change`

#### 4.2.2 Google Ads

| Operation | Description | Rate Limit Weight |
|---|---|---|
| `create_campaign` | Create a new Google Ads campaign | 10 |
| `update_campaign` | Modify campaign settings | 5 |
| `create_ad_group` | Create an ad group | 8 |
| `create_ad` | Create a responsive search/display ad | 10 |
| `get_campaign_report` | Retrieve campaign performance | 5 |
| `get_keyword_report` | Keyword-level performance | 5 |
| `manage_keywords` | Add/pause/update keywords | 8 |
| `create_conversion_action` | Set up conversion tracking | 5 |
| `upload_conversion` | Upload offline conversions | 3 |
| `get_account_info` | Retrieve account metadata | 2 |

**Auth**: OAuth 2.0 (Google Ads API scope)  
**API Version**: Google Ads API v14  
**Webhook Events**: N/A (polling-based)

#### 4.2.3 LinkedIn Ads

| Operation | Description | Rate Limit Weight |
|---|---|---|
| `create_campaign` | Create a LinkedIn ad campaign | 10 |
| `update_campaign` | Modify campaign settings | 5 |
| `create_ad_creative` | Create a sponsored content creative | 10 |
| `get_campaign_analytics` | Campaign performance metrics | 5 |
| `get_account_analytics` | Account-level analytics | 5 |
| `create_audience` | Create a matched audience | 8 |
| `sync_audience` | Sync audience members | 8 |

**Auth**: OAuth 2.0 (LinkedIn Marketing Developer Platform)  
**API Version**: LinkedIn REST API v2  
**Webhook Events**: N/A (polling-based)

#### 4.2.4 TikTok Ads

| Operation | Description | Rate Limit Weight |
|---|---|---|
| `create_campaign` | Create a TikTok ad campaign | 10 |
| `create_ad_group` | Create an ad group | 8 |
| `create_ad` | Create a TikTok ad | 10 |
| `get_campaign_report` | Campaign performance | 5 |
| `get_audience_insights` | Audience analytics | 5 |

**Auth**: OAuth 2.0 (TikTok Marketing API)  
**API Version**: TikTok Business API v1.3

#### 4.2.5 X (Twitter) Ads

| Operation | Description | Rate Limit Weight |
|---|---|---|
| `create_campaign` | Create a promoted campaign | 10 |
| `create_promoted_tweet` | Promote a tweet | 8 |
| `get_campaign_stats` | Campaign analytics | 5 |

**Auth**: OAuth 1.0a + OAuth 2.0  
**API Version**: X Ads API v12

### 4.3 CRM Platforms

#### 4.3.1 Salesforce

| Operation | Description | Rate Limit Weight |
|---|---|---|
| `create_lead` | Create a new lead | 3 |
| `update_lead` | Update lead fields | 2 |
| `convert_lead` | Convert lead to contact/opportunity | 5 |
| `create_contact` | Create a contact | 3 |
| `create_opportunity` | Create an opportunity | 3 |
| `update_opportunity` | Update opportunity stage/amount | 2 |
| `create_account` | Create an account | 3 |
| `query_soql` | Execute a SOQL query | 5 |
| `search_sosl` | Execute a SOSL search | 5 |
| `create_task` | Create a task | 2 |
| `create_event` | Create an event | 2 |
| `get_user` | Retrieve user info | 1 |

**Auth**: OAuth 2.0 (Web Server flow)  
**API Version**: Salesforce REST API v59.0  
**Webhook Events**: Platform Events, Change Data Capture

#### 4.3.2 HubSpot

| Operation | Description | Rate Limit Weight |
|---|---|---|
| `create_contact` | Create a new contact | 3 |
| `update_contact` | Update contact properties | 2 |
| `create_company` | Create a company | 3 |
| `create_deal` | Create a deal | 3 |
| `update_deal_stage` | Move deal to a new stage | 2 |
| `create_ticket` | Create a support ticket | 3 |
| `add_to_list` | Add contact to a list | 2 |
| `create_workflow` | Create an automation workflow | 5 |
| `enroll_in_workflow` | Enroll contact in workflow | 3 |
| `get_analytics` | Retrieve analytics data | 5 |
| `create_form` | Create a form | 3 |
| `submit_form` | Submit form data | 2 |

**Auth**: OAuth 2.0 (HubSpot API)  
**API Version**: HubSpot API v3  
**Webhook Events**: Subscription-based webhooks (contact, deal, company events)

#### 4.3.3 GoHighLevel

| Operation | Description | Rate Limit Weight |
|---|---|---|
| `create_contact` | Create a new contact | 3 |
| `update_contact` | Update contact fields | 2 |
| `create_opportunity` | Create an opportunity | 3 |
| `update_opportunity` | Update opportunity | 2 |
| `create_appointment` | Book an appointment | 3 |
| `create_pipeline` | Create a pipeline | 5 |
| `add_to_campaign` | Add contact to a campaign | 3 |
| `send_sms` | Send an SMS message | 2 |
| `send_email` | Send an email | 2 |
| `create_note` | Add a note to a contact | 2 |
| `get_locations` | List sub-accounts/locations | 2 |
| `create_webhook` | Register a webhook | 3 |

**Auth**: OAuth 2.0 (GoHighLevel API)  
**API Version**: GoHighLevel API v2024  
**Webhook Events**: Contact events, opportunity events, appointment events

### 4.4 Marketing Automation

#### 4.4.1 Mailchimp

| Operation | Description | Rate Limit Weight |
|---|---|---|
| `create_campaign` | Create an email campaign | 5 |
| `send_campaign` | Send a campaign | 8 |
| `add_subscriber` | Add subscriber to audience | 2 |
| `update_subscriber` | Update subscriber fields | 2 |
| `create_automation` | Create an automation | 5 |
| `get_report` | Campaign performance report | 5 |

**Auth**: OAuth 2.0 / API Key  
**API Version**: Mailchimp API v3.0

#### 4.4.2 ActiveCampaign

| Operation | Description | Rate Limit Weight |
|---|---|---|
| `create_contact` | Create a contact | 3 |
| `add_to_list` | Add contact to list | 2 |
| `create_automation` | Create an automation | 5 |
| `trigger_automation` | Trigger automation for contact | 3 |
| `get_deal` | Retrieve deal info | 2 |

**Auth**: API Key  
**API Version**: ActiveCampaign API v3

### 4.5 E-Commerce

#### 4.5.1 Shopify

| Operation | Description | Rate Limit Weight |
|---|---|---|
| `create_product` | Create a product | 5 |
| `update_inventory` | Update stock levels | 3 |
| `create_order` | Create a draft order | 5 |
| `get_customer` | Retrieve customer details | 2 |
| `create_customer` | Create a customer | 3 |
| `create_discount` | Create a discount code | 5 |
| `get_analytics` | Store analytics | 5 |

**Auth**: OAuth 2.0 (Shopify Admin API)  
**API Version**: Shopify Admin API 2024-01  
**Webhook Events**: Orders, products, customers, inventory

#### 4.5.2 Stripe

| Operation | Description | Rate Limit Weight |
|---|---|---|
| `create_customer` | Create a customer | 3 |
| `create_payment_link` | Create a payment link | 5 |
| `create_invoice` | Create an invoice | 5 |
| `get_charge` | Retrieve charge details | 2 |
| `create_refund` | Issue a refund | 5 |
| `get_subscription` | Retrieve subscription | 2 |

**Auth**: API Key (Secret Key)  
**API Version**: Stripe API 2024-06-20  
**Webhook Events**: Payment events, subscription events, refund events

### 4.6 Analytics

#### 4.6.1 Google Analytics 4

| Operation | Description | Rate Limit Weight |
|---|---|---|
| `run_report` | Execute a GA4 report query | 5 |
| `get_realtime` | Real-time analytics data | 3 |
| `create_conversion` | Mark a conversion event | 3 |
| `list_accounts` | List accessible GA4 accounts | 2 |

**Auth**: OAuth 2.0 (Google Analytics scope)  
**API Version**: GA4 Data API v1beta

#### 4.6.2 Mixpanel

| Operation | Description | Rate Limit Weight |
|---|---|---|
| `track_event` | Track a custom event | 1 |
| `query_events` | Query event data | 5 |
| `create_funnel` | Create a funnel report | 5 |
| `get_retention` | Retention analysis | 5 |

**Auth**: API Key / OAuth 2.0  
**API Version**: Mixpanel API v2

### 4.7 Communication

#### 4.7.1 Twilio (SMS/Voice)

| Operation | Description | Rate Limit Weight |
|---|---|---|
| `send_sms` | Send an SMS message | 1 |
| `send_whatsapp` | Send a WhatsApp message | 1 |
| `make_call` | Initiate a voice call | 3 |
| `get_message_status` | Check message delivery status | 1 |

**Auth**: API Key (Account SID + Auth Token)  
**API Version**: Twilio API v2010-04-01

#### 4.7.2 SendGrid (Email)

| Operation | Description | Rate Limit Weight |
|---|---|---|
| `send_email` | Send a transactional email | 2 |
| `create_template` | Create an email template | 5 |
| `get_stats` | Email delivery statistics | 5 |
| `manage_suppression` | Manage bounce/block lists | 2 |

**Auth**: API Key  
**API Version**: SendGrid API v3

### 4.8 Social Media Management

#### 4.8.1 Buffer

| Operation | Description | Rate Limit Weight |
|---|---|---|
| `create_post` | Schedule a social post | 3 |
| `get_analytics` | Post performance analytics | 5 |
| `list_profiles` | List connected social profiles | 2 |

**Auth**: OAuth 2.0  
**API Version**: Buffer API v1

#### 4.8.2 Hootsuite

| Operation | Description | Rate Limit Weight |
|---|---|---|
| `create_post` | Schedule a post | 3 |
| `get_streams` | Retrieve social streams | 5 |
| `get_analytics` | Social analytics | 5 |

**Auth**: OAuth 2.0  
**API Version**: Hootsuite API v1

### 4.9 Custom Webhook Connector

For any platform without a pre-built connector, the **Custom Webhook Connector** allows users to define:

- **Endpoint URL**: The external API endpoint.
- **HTTP Method**: GET, POST, PUT, PATCH, DELETE.
- **Headers**: Static or dynamic headers.
- **Authentication**: Any supported auth provider.
- **Request Template**: Jinja2 template for request body.
- **Response Mapping**: JSONPath or Jinja2 mapping for response transformation.
- **Webhook Inbound**: URL path, signature verification, payload mapping.

```yaml
name: custom_crm
display_name: "My Custom CRM"
version: 1.0.0
auth:
  type: api_key
  key_name: X-API-Key
  key_location: header
operations:
  - name: create_lead
    method: POST
    url: https://api.customcrm.com/v1/leads
    request_template: |
      {
        "first_name": "{{ first_name }}",
        "last_name": "{{ last_name }}",
        "email": "{{ email }}",
        "company": "{{ company }}"
      }
    response_mapping:
      lead_id: "$.id"
      status: "$.status"
```

### 4.10 Connector Summary Table

| Category | Connectors | Count |
|---|---|---|
| Ad Platforms | Meta, Google, LinkedIn, TikTok, X, Pinterest, Snapchat, Reddit | 8 |
| CRM | Salesforce, HubSpot, GoHighLevel, Pipedrive, Zoho, Freshsales, Insightly, Attio | 8 |
| Marketing Automation | Mailchimp, ActiveCampaign, Klaviyo, Braze, Iterable, Customer.io, Drip, ConvertKit | 8 |
| E-Commerce | Shopify, Stripe, WooCommerce, BigCommerce, Squarespace, Magento, Gumroad, PayPal | 8 |
| Analytics | Google Analytics 4, Mixpanel, Amplitude, Segment, Hotjar, Heap, Looker, Tableau | 8 |
| Communication | Twilio, SendGrid, Mailgun, Slack, Discord, WhatsApp Business, Zoom, Microsoft Teams | 8 |
| Social Media | Buffer, Hootsuite, Sprout Social, Later, Loomly, SocialBee, Agorapulse, Zoho Social | 8 |
| Productivity | Notion, Airtable, Asana, Trello, Monday, ClickUp, Jira, Linear | 8 |
| Custom | Webhook Connector, GraphQL Connector, gRPC Connector, SOAP Connector | 4 |
| **Total Pre-built** | | **68** |
| **Community/Partner** | | **1,432+** |
| **Grand Total** | | **1,500+** |

---

## 5. Data Transformation and Mapping

### 5.1 The Transformation Challenge

Each external platform has its own data model, field names, formats, and semantics. The Transformation Engine bridges the gap between the **canonical internal model** (used by AI agents) and **provider-specific models** (used by each connector).

### 5.2 Canonical Data Model

The canonical model is a unified schema that represents marketing entities in a platform-agnostic way.

#### 5.2.1 Core Entities

```
Campaign
├── id: string
├── name: string
├── status: enum [DRAFT, ACTIVE, PAUSED, COMPLETED, ARCHIVED]
├── objective: enum [AWARENESS, TRAFFIC, ENGAGEMENT, LEADS, SALES, APP_INSTALLS]
├── budget: Money
│   ├── amount: number
│   ├── currency: string (ISO 4217)
│   └── type: enum [DAILY, LIFETIME]
├── schedule: DateRange
│   ├── start: datetime
│   └── end: datetime (optional)
├── targeting: Targeting
│   ├── demographics: Demographics
│   ├── interests: string[]
│   ├── behaviors: string[]
│   ├── custom_audiences: string[]
│   └── lookalike_audiences: string[]
├── creatives: Creative[]
├── platform: string (meta, google, linkedin, etc.)
├── platform_id: string (ID on the external platform)
├── metadata: object
└── created_at: datetime

AdSet
├── id: string
├── campaign_id: string
├── name: string
├── status: enum [ACTIVE, PAUSED, DELETED]
├── budget: Money
├── bid_strategy: enum [LOWEST_COST, COST_CAP, BID_CAP, MIN_ROAS]
├── bid_amount: Money
├── targeting: Targeting
├── placement: string[]
├── schedule: DateRange
└── platform_id: string

Contact
├── id: string
├── email: string
├── phone: string
├── first_name: string
├── last_name: string
├── company: string
├── job_title: string
├── address: Address
├── tags: string[]
├── custom_fields: object
├── source: string
├── lifecycle_stage: enum [LEAD, MQL, SQL, OPPORTUNITY, CUSTOMER, CHURNED]
├── platform: string
├── platform_id: string
└── last_activity: datetime

Opportunity
├── id: string
├── name: string
├── contact_id: string
├── account_id: string
├── value: Money
├── stage: enum [DISCOVERY, QUALIFIED, PROPOSAL, NEGOTIATION, CLOSED_WON, CLOSED_LOST]
├── probability: number (0-100)
├── close_date: date
├── platform: string
├── platform_id: string
└── created_at: datetime
```

### 5.3 Mapping Configuration

Mappings are defined in YAML and stored per tenant per connector.

```yaml
# Meta Ads Campaign Mapping
connector: meta_ads
entity: campaign
operation: create_campaign

field_mappings:
  # canonical_field: provider_field
  name: "name"
  objective: "objective"
  budget.amount: "daily_budget"
  budget.currency: null  # Not sent to Meta (uses account currency)
  schedule.start: "start_time"
  schedule.end: "end_time"
  targeting.interests: "targeting.interests"
  targeting.custom_audiences: "targeting.custom_audiences"

value_transformations:
  # Transform canonical values to provider values
  objective:
    AWARENESS: "BRAND_AWARENESS"
    TRAFFIC: "LINK_CLICKS"
    CONVERSIONS: "CONVERSIONS"
    LEADS: "LEAD_GENERATION"
  budget.amount:
    transform: "multiply"
    factor: 100  # Meta uses cents
  schedule.start:
    transform: "datetime_to_timestamp"
    format: "unix"

conditional_mappings:
  - when: "budget.type == 'LIFETIME'"
    then:
      budget.amount: "lifetime_budget"
    else:
      budget.amount: "daily_budget"

defaults:
  status: "PAUSED"
  special_ad_categories: "[]"

excluded_fields:
  - "platform_id"  # Read-only on Meta
  - "created_at"   # Set by Meta
```

### 5.4 Transformation Pipeline

```
Canonical Input → Field Mapping → Value Transformation
    → Conditional Logic → Default Injection → Provider-Specific Output
```

#### 5.4.1 Field Mapping
Maps canonical field names to provider field names. Supports nested paths (e.g., `targeting.interests`).

#### 5.4.2 Value Transformation
Transforms values from canonical format to provider format:

| Transform | Description | Example |
|---|---|---|
| `multiply` | Multiply by factor | `50.00` → `5000` (cents) |
| `divide` | Divide by factor | `5000` → `50.00` |
| `format_date` | Format date/datetime | `2026-10-01` → `2026-10-01T00:00:00Z` |
| `datetime_to_timestamp` | Convert to Unix timestamp | `2026-10-01T00:00:00Z` → `1759276800` |
| `timestamp_to_datetime` | Convert from Unix timestamp | `1759276800` → `2026-10-01T00:00:00Z` |
| `enum_map` | Map enum values | `AWARENESS` → `BRAND_AWARENESS` |
| `join` | Join array to string | `["a", "b"]` → `"a,b"` |
| `split` | Split string to array | `"a,b"` → `["a", "b"]` |
| `template` | Jinja2 template | `"{{ first_name }} {{ last_name }}"` |
| `lookup` | Lookup in reference table | `"US"` → `"United States"` |
| `hash` | Hash a value (PII) | `"john@email.com` → `"a3f2..."` |
| `encrypt` | Encrypt a value | `"sensitive"` → `"enc:v1:abc..."` |

#### 5.4.3 Conditional Logic
Supports conditional field mapping based on input values:

```yaml
conditional_mappings:
  - when: "budget.type == 'LIFETIME'"
    then:
      field: "lifetime_budget"
      value: "{{ budget.amount * 100 }}"
  - when: "budget.type == 'DAILY'"
    then:
      field: "daily_budget"
      value: "{{ budget.amount * 100 }}"
```

#### 5.4.4 Default Injection
Automatically injects default values for fields not provided:

```yaml
defaults:
  status: "PAUSED"
  special_ad_categories: "[]"
  bid_strategy: "LOWEST_COST"
```

### 5.5 Response Transformation

Responses from external APIs are transformed back to the canonical model:

```yaml
# Meta Ads Campaign Response Mapping
response_mapping:
  campaign_id: "id"
  name: "name"
  status: "status"
  objective: "objective"
  created_at: "created_time"
  platform_id: "id"

response_value_transformations:
  status:
    transform: "lowercase"
  objective:
    BRAND_AWARENESS: "AWARENESS"
    LINK_CLICKS: "TRAFFIC"
    CONVERSIONS: "CONVERSIONS"
    LEAD_GENERATION: "LEADS"
  created_at:
    transform: "iso_to_datetime"
```

### 5.6 Schema Inference

For connectors without explicit mappings, the Transformation Engine can **infer mappings** by:

1. Fetching the provider's API schema (OpenAPI spec or discovery endpoint).
2. Matching field names using fuzzy matching (Levenshtein distance).
3. Matching field types and formats.
4. Using an LLM to suggest semantic mappings.
5. Presenting suggestions to the user for confirmation.

### 5.7 Data Validation

#### 5.7.1 Input Validation
- JSON Schema validation against the operation's `input_schema`.
- Custom validators for business rules (e.g., `end_date > start_date`).
- PII detection and redaction before logging.

#### 5.7.2 Output Validation
- JSON Schema validation against the operation's `output_schema`.
- Sanitization of sensitive fields before returning to the agent.

### 5.8 Bidirectional Sync

For entities that exist on both sides (e.g., contacts in HubSpot and Salesforce), the Transformation Engine supports **bidirectional sync**:

```
HubSpot Contact ←→ Canonical Contact ←→ Salesforce Lead
```

Sync rules:
- **Conflict resolution**: Last-write-wins, source-priority, or field-level merge.
- **Sync direction**: One-way (push/pull) or two-way.
- **Sync trigger**: Real-time (webhook), scheduled (cron), or manual.
- **Delta sync**: Only sync changed fields using change tracking.

---

## 6. Rate Limiting and Throttling

### 6.1 The Rate Limiting Problem

External APIs impose rate limits that vary by:
- **Platform**: Meta allows ~200 calls/hour per ad account; Google Ads allows ~15,000 queries/day.
- **Operation type**: Read operations typically have higher limits than write operations.
- **Account tier**: Higher-spend accounts get higher limits.
- **Time window**: Per-second, per-minute, per-hour, per-day limits.

Exceeding rate limits results in throttling (HTTP 429), temporary bans, or account suspension.

### 6.2 Multi-Layer Rate Limiting

```
┌─────────────────────────────────────────────────────────┐
│                    Global Rate Limiter                    │
│         (Protects hub infrastructure)                     │
│         Max: 10,000 req/sec across all tenants            │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│                  Tenant Rate Limiter                      │
│         (Fair share across tenants)                       │
│         Max: 100 req/sec per tenant                       │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│               Connector Rate Limiter                      │
│         (Per-connector budget)                            │
│         Max: 50 req/sec per connector per tenant          │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│            Provider Rate Limiter                          │
│         (Respects external API limits)                    │
│         Max: Platform-specific (e.g., 200/hr for Meta)    │
└─────────────────────────────────────────────────────────┘
```

### 6.3 Rate Limiting Algorithms

#### 6.3.1 Token Bucket

Used for per-second and per-minute limits.

```python
class TokenBucket:
    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity          # Maximum tokens
        self.tokens = capacity            # Current tokens
        self.refill_rate = refill_rate    # Tokens per second
        self.last_refill = time.monotonic()

    async def consume(self, tokens: int = 1) -> bool:
        self._refill()
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False

    def _refill(self):
        now = time.monotonic()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now
```

#### 6.3.2 Sliding Window

Used for per-hour and per-day limits where the window is large.

```python
class SlidingWindow:
    def __init__(self, limit: int, window_seconds: int):
        self.limit = limit
        self.window = window_seconds
        self.requests = deque()  # Timestamps of recent requests

    async def allow(self) -> bool:
        now = time.monotonic()
        # Remove requests outside the window
        while self.requests and self.requests[0] < now - self.window:
            self.requests.popleft()
        if len(self.requests) < self.limit:
            self.requests.append(now)
            return True
        return False
```

#### 6.3.3 Operation Weighting

Different operations consume different amounts of rate-limit budget:

| Operation Type | Weight | Example |
|---|---|---|
| Read (list/get) | 1 | `get_campaign` |
| Read (report) | 3 | `get_campaign_insights` |
| Write (create/update) | 5 | `create_campaign` |
| Write (delete) | 3 | `delete_campaign` |
| Bulk operation | 10 | `bulk_update_creatives` |

### 6.4 Provider-Specific Rate Limit Handling

#### 6.4.1 Meta (Facebook) Ads

- **Limit**: ~200 calls/hour per ad account (varies by account age and spend).
- **Headers**: `X-Ad-Account-Usage`, `X-Business-Use-Case-Usage`.
- **Strategy**: Token bucket with 200 tokens/hour, operation weighting, and header-based adjustment.

#### 6.4.2 Google Ads

- **Limit**: ~15,000 queries/day per developer token; per-account limits vary.
- **Headers**: `X-RateLimit-Remaining`, `X-RateLimit-Reset`.
- **Strategy**: Sliding window (24-hour), with daily quota tracking.

#### 6.4.3 LinkedIn Ads

- **Limit**: ~500 calls/day per application; per-user limits vary.
- **Headers**: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`.
- **Strategy**: Sliding window (24-hour).

#### 6.4.4 Salesforce

- **Limit**: Varies by edition (Enterprise: ~15,000 API calls/24h).
- **Headers**: `Sforce-Limit-Info`.
- **Strategy**: Sliding window with header-based adjustment.

#### 6.4.5 HubSpot

- **Limit**: 100 requests/10 seconds per API key; 250,000 requests/day.
- **Headers**: `X-HubSpot-RateLimit-Limit`, `X-HubSpot-RateLimit-Remaining`, `X-HubSpot-RateLimit-Duration`.
- **Strategy**: Token bucket (100/10s) + sliding window (daily).

### 6.5 Rate Limit Response Handling

When a rate limit is hit:

```
1. Receive HTTP 429 (or platform-specific throttling response)
2. Extract retry-after from header or response body
3. Calculate backoff: max(retry_after, exponential_backoff)
4. Queue the request for retry
5. Update rate-limit budget tracking
6. If retry-after > threshold, alert operations team
```

### 6.6 Rate Limit Headers Parsing

```python
class RateLimitParser:
    @staticmethod
    def parse(headers: dict) -> RateLimitInfo:
        return RateLimitInfo(
            limit=headers.get("X-RateLimit-Limit"),
            remaining=headers.get("X-RateLimit-Remaining"),
            reset_at=headers.get("X-RateLimit-Reset"),
            retry_after=headers.get("Retry-After"),
        )
```

### 6.7 Adaptive Rate Limiting

The rate limiter adapts based on observed behavior:

- **Success rate tracking**: If a connector's success rate drops below 95%, reduce the rate limit by 20%.
- **Latency tracking**: If p99 latency exceeds threshold, reduce the rate limit to prevent cascading failures.
- **Time-of-day awareness**: Some platforms have different limits at different times; the limiter learns patterns.
- **Burst allowance**: Short bursts above the sustained rate are allowed up to a maximum burst size.

### 6.8 Rate Limit Monitoring

| Metric | Description | Alert Threshold |
|---|---||
| `rate_limit_hits_total` | Total rate-limited requests | > 100/minute |
| `rate_limit_wait_seconds` | Total time spent waiting | > 60s/minute |
| `rate_limit_budget_remaining` | Remaining budget percentage | < 10% |
| `rate_limit_429_errors` | HTTP 429 responses | > 10/minute |

### 6.9 Configuration

```yaml
rate_limiting:
  global:
    max_requests_per_second: 10000
  tenant:
    max_requests_per_second: 100
  connector:
    max_requests_per_second: 50
  provider:
    meta_ads:
      algorithm: token_bucket
      capacity: 200
      refill_rate: 0.0556  # 200/hour = 0.0556/second
      operation_weights:
        read: 1
        write: 5
        report: 3
    google_ads:
      algorithm: sliding_window
      limit: 15000
      window_seconds: 86400
    linkedin_ads:
      algorithm: sliding_window
      limit: 500
      window_seconds: 86400
```

---

## 7. Error Handling and Retry Logic

### 7.1 Error Classification

All errors are classified into categories that determine the handling strategy:

| Category | Description | Retryable | Example |
|---|---|---|---|
| `TRANSIENT` | Temporary failure, likely to succeed on retry | Yes | HTTP 500, 502, 503, 504, timeout |
| `RATE_LIMITED` | Rate limit exceeded | Yes (with backoff) | HTTP 429 |
| `AUTH` | Authentication failure | No (requires re-auth) | HTTP 401, 403, invalid token |
| `VALIDATION` | Invalid input data | No | HTTP 400, schema validation error |
| `NOT_FOUND` | Resource does not exist | No | HTTP 404 |
| `CONFLICT` | Resource state conflict | Conditional | HTTP 409, duplicate resource |
| `PERMISSION` | Insufficient permissions | No | HTTP 403, insufficient scope |
| `PROVIDER_ERROR` | External platform error | Conditional | Platform-specific errors |
| `INTERNAL` | Hub internal error | Yes | Bug, configuration error |
| `NETWORK` | Network connectivity issue | Yes | DNS failure, connection refused, TLS error |

### 7.2 Retry Policies

#### 7.2.1 Standard Retry Policy

Used for most operations:

```yaml
retry_policy:
  name: standard
  max_attempts: 3
  initial_delay: 1.0        # seconds
  max_delay: 60.0           # seconds
  backoff_multiplier: 2.0   # exponential
  jitter: full              # full jitter: random(0, min(cap, base * 2^attempt))
  retryable_errors:
    - TRANSIENT
    - RATE_LIMITED
    - NETWORK
    - INTERNAL
  non_retryable_errors:
    - AUTH
    - VALIDATION
    - NOT_FOUND
    - PERMISSION
```

#### 7.2.2 Aggressive Retry Policy

Used for critical operations (e.g., payment processing):

```yaml
retry_policy:
  name: aggressive
  max_attempts: 5
  initial_delay: 0.5
  max_delay: 30.0
  backoff_multiplier: 2.0
  jitter: equal             # equal jitter: base/2 + random(0, base/2)
  retryable_errors:
    - TRANSIENT
    - RATE_LIMITED
    - NETWORK
    - INTERNAL
    - PROVIDER_ERROR
```

#### 7.2.3 No-Retry Policy

Used for non-idempotent operations or operations where retries could cause harm:

```yaml
retry_policy:
  name: none
  max_attempts: 1
```

### 7.3 Exponential Backoff with Jitter

```python
import random
import time

def calculate_backoff(attempt: int, initial: float, max_delay: float,
                       multiplier: float, jitter: str) -> float:
    """Calculate backoff delay with jitter."""
    base = min(max_delay, initial * (multiplier ** attempt))
    
    if jitter == "none":
        return base
    elif jitter == "full":
        return random.uniform(0, base)
    elif jitter == "equal":
        return base / 2 + random.uniform(0, base / 2)
    elif jitter == "decorrelated":
        # Decorrelated jitter: faster recovery
        return min(max_delay, random.uniform(initial, base * 3))
    
    return base
```

**Why jitter?** Without jitter, many clients retrying simultaneously create a "thundering herd" that overwhelms the recovering service. Jitter spreads retries across a time window.

### 7.4 Circuit Breaker Pattern

The circuit breaker prevents cascading failures by stopping calls to a failing service.

```
CLOSED → (failure threshold exceeded) → OPEN → (timeout) → HALF_OPEN → (success) → CLOSED
                                                                        → (failure) → OPEN
```

```python
class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 30.0,
                 half_open_max_calls: int = 3):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        self.state = "CLOSED"
        self.failures = 0
        self.last_failure_time = None
        self.half_open_calls = 0

    async def call(self, func, *args, **kwargs):
        if self.state == "OPEN":
            if time.monotonic() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
                self.half_open_calls = 0
            else:
                raise CircuitBreakerOpenError("Circuit breaker is OPEN")

        if self.state == "HALF_OPEN" and self.half_open_calls >= self.half_open_max_calls:
            raise CircuitBreakerOpenError("Circuit breaker is HALF_OPEN (max calls reached)")

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise

    def _on_success(self):
        self.failures = 0
        if self.state == "HALF_OPEN":
            self.state = "CLOSED"
            self.half_open_calls = 0

    def _on_failure(self):
        self.failures += 1
        self.last_failure_time = time.monotonic()
        if self.failures >= self.failure_threshold:
            self.state = "OPEN"
```

#### 7.4.1 Circuit Breaker States

| State | Behavior |
|---|---|
| **CLOSED** | Normal operation. Requests pass through. Failures are counted. |
| **OPEN** | All requests fail immediately. No calls to the failing service. After `recovery_timeout`, transition to HALF_OPEN. |
| **HALF_OPEN** | Limited number of test requests allowed. If they succeed, transition to CLOSED. If any fail, transition back to OPEN. |

#### 7.4.2 Per-Connector Circuit Breakers

Each connector has its own circuit breaker, configured per operation type:

```yaml
circuit_breaker:
  meta_ads:
    failure_threshold: 5
    recovery_timeout: 60
    half_open_max_calls: 3
  google_ads:
    failure_threshold: 3
    recovery_timeout: 120
    half_open_max_calls: 2
```

### 7.5 Dead Letter Queue (DLQ)

Requests that exhaust all retry attempts are sent to a Dead Letter Queue for manual inspection and replay.

```yaml
dead_letter_queue:
  enabled: true
  max_retention_days: 30
  max_entries: 100000
  replay_enabled: true
  alert_on_entry: true
  storage: kafka  # or SQS, RabbitMQ
```

#### 7.5.1 DLQ Entry Format

```json
{
  "dlq_id": "dlq_abc123",
  "timestamp": "2026-10-01T12:00:00Z",
  "tenant_id": "tenant_xyz",
  "connector": "meta_ads",
  "operation": "create_campaign",
  "params": { "name": "Q4 Launch", "budget": 500 },
  "error": {
    "category": "PROVIDER_ERROR",
    "code": "CAMPAIGN_REJECTED",
    "message": "Campaign objective not supported for this account",
    "http_status": 400
  },
  "attempts": 3,
  "last_attempt_at": "2026-10-01T12:00:45Z"
}
```

### 7.6 Idempotency

For operations that are idempotent (safe to retry), the hub uses idempotency keys:

```python
class IdempotencyKeyManager:
    def generate_key(self, tenant_id: str, operation: str, params: dict) -> str:
        """Generate a deterministic idempotency key."""
        canonical = json.dumps(params, sort_keys=True)
        return hashlib.sha256(
            f"{tenant_id}:{operation}:{canonical}".encode()
        ).hexdigest()

    async def check_and_store(self, key: str, ttl: int = 86400) -> bool:
        """Check if key exists. If not, store it. Returns True if new."""
        return await self.redis.set(key, "1", nx=True, ex=ttl)
```

### 7.7 Error Response Format

All errors returned to the AI agent follow a unified format:

```json
{
  "error": {
    "code": "RATE_LIMITED",
    "message": "Meta API rate limit exceeded. Retry after 300s.",
    "category": "RATE_LIMITED",
    "connector": "meta_ads",
    "operation": "create_campaign",
    "retryable": true,
    "retry_after": 300,
    "details": {
      "provider_error_code": "17",
      "provider_error_message": "User request limit reached"
    },
    "trace_id": "abc123",
    "timestamp": "2026-10-01T12:00:00Z"
  }
}
```

### 7.8 Error Handling Flow

```
Request Received
    │
    ▼
┌─────────────────┐
│ Schema Validation │──→ VALIDATION error (no retry)
└────────┬────────┘
         │
    ┌────▼────┐
    │ Auth Check │──→ AUTH error (trigger re-auth flow)
    └────┬────┘
         │
    ┌────▼────────┐
    │ Rate Limit   │──→ RATE_LIMITED error (queue with backoff)
    └────┬────────┘
         │
    ┌────▼──────────┐
    │ Circuit Breaker│──→ OPEN: fail fast, return error
    └────┬──────────┘
         │
    ┌────▼────────┐
    │ Execute Call  │
    └────┬────────┘
         │
    ┌────▼────────┐
    │ Success?     │
    └────┬────────┘
         │
    ┌────▼────────────────┐
    │ Yes → Return result  │
    │ No  → Classify error │
    └────┬────────────────┘
         │
    ┌────▼────────────────┐
    │ Retryable?           │
    │ Yes → Retry with     │
    │       backoff        │
    │ No  → Return error   │
    └────┬────────────────┘
         │
    ┌────▼────────────────┐
    │ Max attempts reached?│
    │ Yes → Send to DLQ    │
    │ No  → Retry          │
    └─────────────────────┘
```

---

## 8. Integration Monitoring

### 8.1 Monitoring Philosophy

Every aspect of the Integration Hub is observable. Monitoring is not an afterthought — it is built into every layer.

### 8.2 Monitoring Layers

```
┌─────────────────────────────────────────────────────────┐
│                  Business Metrics                        │
│  (Campaigns created, leads synced, revenue attributed)   │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│                 Application Metrics                       │
│  (Request rate, error rate, latency, throughput)          │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│                 Connector Metrics                         │
│  (Per-connector health, rate-limit budget, auth status)   │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│                 Infrastructure Metrics                    │
│  (CPU, memory, network, disk, queue depth)                │
└─────────────────────────────────────────────────────────┘
```

### 8.3 Key Metrics

#### 8.3.1 Request Metrics

| Metric | Type | Description |
|---|---|---|
| `hub_requests_total` | Counter | Total requests processed |
| `hub_request_duration_seconds` | Histogram | Request latency (p50, p95, p99) |
| `hub_requests_per_second` | Gauge | Current request rate |
| `hub_active_requests` | Gauge | Currently in-flight requests |

#### 8.3.2 Error Metrics

| Metric | Type | Description |
|---|---|---|
| `hub_errors_total` | Counter | Total errors by category |
| `hub_error_rate` | Gauge | Errors / total requests |
| `hub_retry_total` | Counter | Total retry attempts |
| `hub_retry_success_total` | Counter | Retries that eventually succeeded |
| `hub_dlq_entries_total` | Counter | Entries sent to dead letter queue |

#### 8.3.3 Connector Metrics

| Metric | Type | Description |
|---|---|---|
| `connector_health_status` | Gauge | 0=unhealthy, 1=degraded, 2=healthy |
| `connector_rate_limit_remaining` | Gauge | Remaining rate-limit budget |
| `connector_rate_limit_reset_seconds` | Gauge | Seconds until rate-limit reset |
| `connector_auth_token_expiry` | Gauge | Seconds until token expiry |
| `connector_circuit_breaker_state` | Gauge | 0=closed, 1=open, 2=half-open |
| `connector_last_success_timestamp` | Gauge | Unix timestamp of last successful call |
| `connector_last_error_timestamp` | Gauge | Unix timestamp of last error |

#### 8.3.4 Cache Metrics

| Metric | Type | Description |
|---|---|---|
| `hub_cache_hits_total` | Counter | Cache hits |
| `hub_cache_misses_total` | Counter | Cache misses |
| `hub_cache_hit_ratio` | Gauge | Hits / (hits + misses) |
| `hub_cache_evictions_total` | Counter | Entries evicted |

### 8.4 Distributed Tracing

Every request is traced end-to-end using OpenTelemetry:

```
Agent Request (trace_id: abc123)
    │
    ├── Hub Router (span: route_request, 2ms)
    │   ├── Auth Check (span: auth_check, 5ms)
    │   ├── Rate Limit (span: rate_limit_check, 1ms)
    │   ├── Cache Lookup (span: cache_lookup, 3ms)
    │   ├── Connector Execution (span: meta_create_campaign, 342ms)
    │   │   ├── HTTP Request (span: POST graph.facebook.com, 330ms)
    │   │   └── Response Transform (span: transform_response, 12ms)
    │   └── Cache Store (span: cache_store, 2ms)
    │
    └── Total: 355ms
```

#### 8.4.1 Trace Context Propagation

Trace context is propagated across:
- Agent → Hub (via `traceparent` header)
- Hub → Connector (via OpenTelemetry SDK)
- Hub → Event Bus (via Kafka message headers)
- Hub → Cache (via Redis key tagging)

### 8.5 Logging

#### 8.5.1 Structured Logging

All logs are structured JSON:

```json
{
  "timestamp": "2026-10-01T12:00:00.123Z",
  "level": "INFO",
  "trace_id": "abc123",
  "span_id": "def456",
  "tenant_id": "tenant_xyz",
  "connector": "meta_ads",
  "operation": "create_campaign",
  "message": "Operation completed successfully",
  "duration_ms": 342,
  "request_id": "req_789",
  "user_id": "user_456"
}
```

#### 8.5.2 Log Levels

| Level | Usage |
|---|---|
| `DEBUG` | Detailed transformation steps, cache operations |
| `INFO` | Operation start/success, connector state changes |
| `WARN` | Rate limit approaching, retry attempts, deprecated connector usage |
| `ERROR` | Operation failures, auth failures, circuit breaker open |
| `FATAL` | Hub startup failure, credential vault unreachable |

#### 8.5.3 PII Handling

- PII fields (email, phone, name) are **redacted** in logs by default.
- Redaction is configurable per tenant (some tenants require full logging for compliance).
- Redacted fields appear as `"***REDACTED***"` in log output.

### 8.6 Alerting

#### 8.6.1 Alert Rules

| Alert | Condition | Severity | Notification |
|---|---|---|---|
| `HighErrorRate` | Error rate > 5% for 5 minutes | P1 | PagerDuty + Slack |
| `ConnectorDown` | Connector health = 0 for 2 minutes | P1 | PagerDuty + Slack |
| `CircuitBreakerOpen` | Any circuit breaker opens | P2 | Slack |
| `RateLimitCritical` | Rate-limit budget < 5% | P2 | Slack |
| `DLQGrowth` | DLQ entries > 100 in 10 minutes | P2 | Slack |
| `AuthTokenExpiring` | Token expires in < 1 hour | P3 | Slack |
| `HighLatency` | p99 latency > 5s for 5 minutes | P2 | Slack |
| `CacheHitRatioLow` | Cache hit ratio < 50% for 10 minutes | P3 | Slack |

#### 8.6.2 Alert Routing

```
P1 (Critical) → PagerDuty → Phone call + SMS + Slack
P2 (Warning)  → Slack + Email
P3 (Info)     → Slack
```

### 8.7 Dashboards

#### 8.7.1 Executive Dashboard

- Total operations per day
- Success rate trend
- Top 10 connectors by usage
- Error rate by connector
- Cost per operation (where applicable)

#### 8.7.2 Operations Dashboard

- Real-time request rate
- Error rate by category
- Latency percentiles (p50, p95, p99)
- Circuit breaker states
- Rate-limit budget utilization
- DLQ depth

#### 8.7.3 Connector Health Dashboard

- Per-connector health status
- Per-connector success rate
- Per-connector latency
- Per-connector rate-limit budget
- Per-connector auth token status
- Per-connector last error

#### 8.7.4 Tenant Dashboard

- Per-tenant usage metrics
- Per-tenant error rate
- Per-tenant rate-limit consumption
- Per-tenant connector enablement status

### 8.8 Health Checks

#### 8.8.1 Liveness Probe

```
GET /health/live
→ 200 OK if the hub process is running
```

#### 8.8.2 Readiness Probe

```
GET /health/ready
→ 200 OK if all dependencies are reachable:
  - Credential Vault
  - Cache (Redis)
  - Event Bus (Kafka)
  - Schema Registry
→ 503 Service Unavailable otherwise
```

#### 8.8.3 Connector Health Check

```
GET /v1/connectors/{id}/health
→ {
    "connector": "meta_ads",
    "status": "healthy",  // healthy | degraded | unhealthy
    "last_check": "2026-10-01T12:00:00Z",
    "details": {
      "api_reachable": true,
      "auth_valid": true,
      "rate_limit_remaining": 180,
      "rate_limit_reset_in": 3600,
      "circuit_breaker": "closed",
      "last_success": "2026-10-01T11:59:00Z",
      "last_error": null
    }
  }
```

### 8.9 SLOs (Service Level Objectives)

| SLO | Target | Measurement |
|---|---|---|
| Availability | 99.9% | Uptime / total time |
| Success Rate | 99.5% | Successful ops / total ops |
| p50 Latency | < 200ms | Median request latency |
| p99 Latency | < 2s | 99th percentile latency |
| Error Rate | < 0.5% | Errors / total requests |
| DLQ Rate | < 0.1% | DLQ entries / total requests |

---

## 9. Implementation Roadmap

### 9.1 Phase Overview

```
Phase 1 (Months 1-3)     → Core Hub + 5 Key Connectors
Phase 2 (Months 4-6)     → SDK + 15 Additional Connectors
Phase 3 (Months 7-9)     → Advanced Features + 30 Connectors
Phase 4 (Months 10-12)   → Scale + 100 Connectors
Phase 5 (Months 13-18)   → Ecosystem + 500+ Connectors
Phase 6 (Months 19-24)   → Full Coverage → 1,500+ Connectors
```

### 9.2 Phase 1: Foundation (Months 1-3)

**Objective**: Build the core hub infrastructure and ship the 5 most critical connectors.

#### Month 1: Core Infrastructure

| Week | Deliverable |
|---|---|
| 1 | Project scaffolding, CI/CD pipeline, dev environment |
| 2 | Hub Core: Router Engine, Auth Manager, Schema Registry |
| 3 | Rate Limiter, Cache Layer, Retry Engine |
| 4 | Transformation Engine (basic), Event Bus integration |

#### Month 2: Gateway + SDK

| Week | Deliverable |
|---|---|
| 1 | API Gateway (Kong/Envoy), Agent-Facing API (MCP) |
| 2 | Webhook Ingestion, Management API |
| 3 | Connector SDK: BaseConnector, Auth Providers, Middleware |
| 4 | Connector SDK: CLI, Testing Framework, Documentation |

#### Month 3: First 5 Connectors

| Week | Deliverable |
|---|---|
| 1 | Meta Ads Connector (campaigns, ad sets, ads, insights) |
| 2 | Google Ads Connector (campaigns, ad groups, reports) |
| 3 | Salesforce Connector (leads, contacts, opportunities, accounts) |
| 4 | HubSpot Connector (contacts, companies, deals, workflows) |

**Phase 1 Exit Criteria**:
- [ ] Hub core services deployed and running in staging
- [ ] API Gateway handling agent requests via MCP
- [ ] 5 connectors operational with >99% success rate
- [ ] Rate limiting and retry logic functional
- [ ] Basic monitoring dashboards live
- [ ] SDK documentation published

### 9.3 Phase 2: Expansion (Months 4-6)

**Objective**: Expand connector coverage to 20 and add advanced features.

#### Month 4: More Ad Platforms + CRM

| Week | Deliverable |
|---|---|
| 1 | LinkedIn Ads Connector |
| 2 | GoHighLevel Connector |
| 3 | TikTok Ads Connector |
| 4 | Pipedrive Connector |

#### Month 5: Marketing + E-Commerce

| Week | Deliverable |
|---|---|
| 1 | Mailchimp Connector |
| 2 | ActiveCampaign Connector |
| 3 | Shopify Connector |
| 4 | Stripe Connector |

#### Month 6: Advanced Features

| Week | Deliverable |
|---|---|
| 1 | Bidirectional Sync Engine |
| 2 | Advanced Transformation (conditional mappings, templates) |
| 3 | Adaptive Rate Limiting |
| 4 | Connector Health Checks + Auto-Recovery |

**Phase 2 Exit Criteria**:
- [ ] 20 connectors operational
- [ ] Bidirectional sync working for contacts (HubSpot ↔ Salesforce)
- [ ] Adaptive rate limiting reducing 429 errors by 80%
- [ ] SDK v1.0 published with 5 example connectors
- [ ] 99.5% success rate across all connectors

### 9.4 Phase 3: Scale (Months 7-9)

**Objective**: Scale to 50 connectors and add enterprise features.

#### Month 7: Analytics + Communication

| Week | Deliverable |
|---|---|
| 1 | Google Analytics 4 Connector |
| 2 | Mixpanel Connector |
| 3 | Twilio Connector |
| 4 | SendGrid Connector |

#### Month 8: Social + Productivity

| Week | Deliverable |
|---|---|
| 1 | Buffer Connector |
| 2 | Hootsuite Connector |
| 3 | Notion Connector |
| 4 | Airtable Connector |

#### Month 9: Enterprise Features

| Week | Deliverable |
|---|---|
| 1 | Multi-Region Deployment |
| 2 | Advanced Security (mTLS, IP allowlisting, audit logging) |
| 3 | Custom Webhook Connector (self-service) |
| 4 | Connector Marketplace (beta) |

**Phase 3 Exit Criteria**:
- [ ] 50 connectors operational
- [ ] Multi-region deployment with failover
- [ ] Custom Webhook Connector self-service UI
- [ ] Connector Marketplace beta with 10 community connectors
- [ ] 99.9% availability SLO met

### 9.5 Phase 4: Ecosystem (Months 10-12)

**Objective**: Open the ecosystem and scale to 150 connectors.

#### Month 10: SDK v2 + Partner Program

| Week | Deliverable |
|---|---|
| 1 | SDK v2.0 with GraphQL and gRPC support |
| 2 | Partner Developer Program launch |
| 3 | Connector Certification Program |
| 4 | Community connector templates |

#### Month 11: Bulk Connector Development

| Week | Deliverable |
|---|---|
| 1 | Batch 1: 20 connectors (productivity, project management) |
| 2 | Batch 2: 20 connectors (HR, finance, legal) |
| 3 | Batch 3: 20 connectors (customer support, helpdesk) |
| 4 | Batch 4: 20 connectors (advertising, SEO, content) |

#### Month 12: Quality + Scale

| Week | Deliverable |
|---|---|
| 1 | Automated connector testing at scale |
| 2 | Performance optimization (p99 < 1s) |
| 3 | Cost optimization (reduce API call costs by 30%) |
| 4 | Phase 4 review and Phase 5 planning |

**Phase 4 Exit Criteria**:
- [ ] 150 connectors operational
- [ ] 50+ community/partner connectors in marketplace
- [ ] SDK v2.0 adopted by 10+ partners
- [ ] p99 latency < 1s across all connectors
- [ ] 99.9% availability SLO maintained at scale

### 9.6 Phase 5: Full Coverage (Months 13-18)

**Objective**: Achieve 650+ connectors through community and partner ecosystem.

#### Months 13-15: Community Growth

- Connector hackathons
- University partnerships
- Open-source connector program
- Revenue sharing for premium connectors

#### Months 16-18: Long-Tail Connectors

- Niche industry connectors (real estate, healthcare, education)
- Regional connectors (local payment providers, regional social platforms)
- Legacy system connectors (SOAP, FTP, database connectors)

**Phase 5 Exit Criteria**:
- [ ] 650+ connectors operational
- [ ] 200+ community connectors in marketplace
- [ ] Top 100 connectors cover 95% of common marketing use cases
- [ ] Connector development time reduced to < 1 day for standard REST APIs

### 9.7 Phase 6: Complete Coverage (Months 19-24)

**Objective**: Reach 1,500+ connectors and achieve full market coverage.

#### Months 19-21: AI-Powered Connector Generation

- LLM-based connector generation from API documentation
- Automated schema inference and mapping
- One-click connector deployment from OpenAPI specs

#### Months 22-24: Maintenance + Optimization

- Automated connector health monitoring and self-healing
- Predictive rate-limit management
- Cost optimization across all connectors
- Deprecation of unused connectors

**Phase 6 Exit Criteria**:
- [ ] 1,500+ connectors operational
- [ ] AI-powered connector generation reduces development time to < 1 hour
- [ ] 99.95% availability SLO
- [ ] Full marketing technology landscape coverage
- [ ] Self-healing connectors with < 5 min MTTR

### 9.8 Resource Planning

| Phase | Duration | Team Size | Connectors Delivered |
|---|---|---|---|
| Phase 1 | 3 months | 8 engineers | 5 |
| Phase 2 | 3 months | 12 engineers | 15 (cumulative: 20) |
| Phase 3 | 3 months | 15 engineers | 30 (cumulative: 50) |
| Phase 4 | 3 months | 18 engineers + 5 partners | 100 (cumulative: 150) |
| Phase 5 | 6 months | 20 engineers + 20 partners | 500 (cumulative: 650) |
| Phase 6 | 6 months | 20 engineers + 50 partners | 850 (cumulative: 1,500) |

### 9.9 Risk Mitigation

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| External API breaking changes | High | High | Schema versioning, automated change detection, rapid patch deployment |
| Rate limit reductions by providers | Medium | High | Adaptive rate limiting, multi-account support, fallback connectors |
| Security breach (credential leak) | Low | Critical | Vault encryption, credential rotation, IP allowlisting, audit logging |
| Key person dependency | Medium | High | Documentation, pair programming, cross-training |
| Scope creep | High | Medium | Strict phase gates, MVP-first approach, regular stakeholder alignment |
| Provider API deprecation | Medium | Medium | Multi-provider support, abstraction layer, migration tools |

### 9.10 Success Metrics

| Metric | Phase 1 | Phase 3 | Phase 6 |
|---|---|---|---|
| Connectors | 5 | 50 | 1,500+ |
| Daily API Calls | 10K | 500K | 10M+ |
| Success Rate | 99% | 99.5% | 99.9% |
| p99 Latency | 3s | 1s | 500ms |
| Availability | 99% | 99.9% | 99.95% |
| MTTR | 1 hour | 15 min | 5 min |
| Developer Onboarding | 1 week | 2 days | 1 hour |

---

## Appendix A: Glossary

| Term | Definition |
|---|---|
| **Canonical Model** | The unified internal data model that abstracts provider-specific formats |
| **Connector** | A module that integrates an external platform with the hub |
| **Hub** | The Integration Hub — the central integration layer |
| **MCP** | Model Context Protocol — the agent-facing tool invocation protocol |
| **Operation** | A single API action exposed by a connector (e.g., `create_campaign`) |
| **Schema Registry** | Central repository of connector input/output schemas |
| **Transformation Engine** | Component that maps data between canonical and provider-specific formats |
| **DLQ** | Dead Letter Queue — storage for failed requests awaiting manual inspection |
| **Circuit Breaker** | Pattern that prevents cascading failures by stopping calls to failing services |
| **Idempotency Key** | A unique key that ensures an operation is not duplicated on retry |

## Appendix B: References

- [Model Context Protocol Specification](https://modelcontextprotocol.io)
- [OpenTelemetry Documentation](https://opentelemetry.io/docs/)
- [OAuth 2.0 Specification (RFC 6749)](https://tools.ietf.org/html/rfc6749)
- [JSON Schema Specification](https://json-schema.org/)
- [Circuit Breaker Pattern — Martin Fowler](https://martinfowler.com/bliki/CircuitBreaker.html)
- [Token Bucket Algorithm — Wikipedia](https://en.wikipedia.org/wiki/Token_bucket)
- [Exponential Backoff and Jitter — AWS Architecture Blog](https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/)

---

*End of document.*
