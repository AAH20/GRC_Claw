# Grand Unified Architecture — Agentic AI Marketing Platform

> **Version:** 1.0 | **Date:** 2026-10-01 | **Status:** Production-Ready  
> **Author:** Ahmed Hassan | **Stack:** LangChain DeepAgents + GRC_Claw + ApexGraphSwarm + Nerve + Laya + Cognee  
> **Target:** $30K+ MRR per project within 6–9 months; 72% gross margin; ~$1,060/mo production cost

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Core Library Specification](#2-core-library-specification)
3. [Project Template & Structure](#3-project-template--structure)
4. [Integration Patterns](#4-integration-patterns)
5. [Shared Infrastructure](#5-shared-infrastructure)
6. [Governance Framework](#6-governance-framework)
7. [Deployment Strategy](#7-deployment-strategy)
8. [CI/CD Pipeline Template](#8-cicd-pipeline-template)
9. [Monitoring & Observability](#9-monitoring--observability)
10. [Revenue Model & Pricing](#10-revenue-model--pricing)

---

## 1. System Overview

### 1.1 Vision

A unified platform that organizes all agentic AI marketing capabilities as **standalone modularized projects** sharing a common core library, governance framework, and infrastructure. Each project operates independently but communicates through well-defined integration patterns, enabling composability without coupling.

### 1.2 Design Principles

| Principle | Rationale |
|-----------|-----------|
| **Modularity First** | Each project is a standalone deployable unit with its own domain logic, data models, and API surface |
| **Shared Core Library** | Common agent framework, governance, monitoring, security, and data access patterns live in a versioned core library (`@grc/core`) |
| **Event-Driven Communication** | Projects communicate via Kafka events and MCP protocols, not direct service-to-service calls |
| **Governance by Default** | Every agent action is policy-checked, audit-logged, and explainable from day one |
| **Multi-Tenant Isolation** | Tenant data is isolated at the database, cache, and event-stream level |
| **LLM-Agnostic** | Apex Harness routes to the best model per task; no single-provider lock-in |
| **Cost-Aware** | Every component tracks token usage and cost; budgets are enforced at the agent level |

### 1.3 High-Level Architecture

```mermaid
graph TB
    subgraph CLIENTS["Client Layer"]
        WEB[Web Dashboard]
        API[REST API]
        WS[WebSocket Stream]
        MOB[Mobile App]
    end

    subgraph EDGE["Edge Layer"]
        GW[API Gateway<br/>Kong / AWS API Gateway]
        AUTH[Auth Service<br/>OAuth 2.1 + OIDC]
        RATE[Rate Limiter<br/>Redis-backed]
    end

    subgraph PROJECTS["Standalone Modularized Projects"]
        P1[Autonomous Campaign<br/>Optimization]
        P2[AI-Powered Lead<br/>Scoring]
        P3[Agentic Customer<br/>Journey Orchestration]
        P4[Content Generation]
        P5[Brand Monitoring]
        P6[Social Media<br/>Management]
        P7[Email Marketing]
        P8[SEO Optimization]
        P9[Analytics &<br/>Attribution]
        P10[Market Research]
    end

    subgraph CORE["Shared Core Library — @grc/core"]
        AF[Agent Framework<br/>LangChain DeepAgents]
        GOV[Governance Layer<br/>GRC_Claw]
        MON[Monitoring<br/>OpenTelemetry]
        SEC[Security<br/>DID + Policy Firewall]
        DATA[Data Layer<br/>PostgreSQL + Snowflake]
        INT[Integration Hub<br/>MCP + A2A]
        MEM[Memory Layer<br/>Cognee + Vector DB]
        SUP[Supervision<br/>Nerve]
        RTE[Real-Time Engine<br/>Laya]
        GRAPH[Graph Engine<br/>ApexGraphSwarm]
    end

    subgraph INFRA["Shared Infrastructure"]
        KAFKA[Apache Kafka<br/>Event Backbone]
        REDIS[Redis Cluster<br/>Cache + Feature Store]
        PG[PostgreSQL 16<br/>Transactional DB]
        SF[Snowflake<br/>Data Warehouse]
        K8S[Kubernetes<br/>EKS / GKE]
        S3[S3 / GCS<br/>Artifact Storage]
    end

    subgraph EXTERNAL["External Systems"]
        CRM[CRM<br/>Salesforce / HubSpot]
        ADS[Ad Platforms<br/>Google / Meta / LinkedIn]
        CDP[CDP<br/>Segment / LiveRamp]
        AN[Analytics<br/>GA4 / Adobe]
        LLM[LLM Providers<br/>Anthropic / OpenAI / Local]
    end

    CLIENTS --> EDGE
    EDGE --> PROJECTS
    PROJECTS --> CORE
    CORE --> INFRA
    CORE --> EXTERNAL
    PROJECTS <-->|Events| KAFKA
    PROJECTS <-->|MCP / A2A| PROJECTS
```

### 1.4 Project Taxonomy

| Category | Projects | Shared Dependencies |
|----------|----------|-------------------|
| **Revenue-Generating** | Campaign Optimization, Lead Scoring, Journey Orchestration | All core modules |
| **Content** | Content Generation, SEO Optimization, Social Media | Agent framework, Memory, Integration Hub |
| **Intelligence** | Market Research, Brand Monitoring, Analytics & Attribution | Data layer, Graph engine, Monitoring |
| **Engagement** | Email Marketing, Customer Retention, Feedback Management | Agent framework, Integration Hub, Memory |

### 1.5 Technology Stack Summary

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Agent Orchestration** | LangChain DeepAgents + LangGraph | Stateful multi-agent coordination |
| **Inter-Agent Protocol** | A2A v1.0 (Linux Foundation) | Agent-to-agent task delegation |
| **Tool Protocol** | MCP 2025-11-25 (Linux Foundation) | Agent-to-tool connectivity |
| **Governance** | GRC_Claw | Policy enforcement, audit, compliance |
| **Graph Analytics** | ApexGraphSwarm | Customer journey graph, community detection |
| **Supervision** | Nerve | Definition of Done, quality verification |
| **Real-Time Routing** | Laya | Sub-33ms decision routing |
| **Knowledge Graph** | Cognee | Cross-session memory, RAG |
| **Event Streaming** | Apache Kafka (MSK) | Event backbone, inter-project communication |
| **Cache & Feature Store** | Redis Cluster | Sub-millisecond feature access |
| **Transactional DB** | PostgreSQL 16 (Aurora) | Project-specific operational data |
| **Data Warehouse** | Snowflake | Cross-project analytics, ML training |
| **Container Orchestration** | Kubernetes (EKS/GKE) | Deployment, scaling, self-healing |
| **Observability** | Prometheus + Grafana + Loki + Tempo | Metrics, logs, traces, dashboards |
| **CI/CD** | GitHub Actions + Helm + ArgoCD | Build, test, deploy, GitOps |

---

## 2. Core Library Specification

### 2.1 Overview

The `@grc/core` library is a **versioned Python package** (published to private PyPI) that provides all shared components. Every project depends on it via a pinned version in `pyproject.toml`. The library follows semantic versioning; breaking changes require a major version bump and migration guide.

### 2.2 Package Structure

```
@grc/core/
├── agent_framework/          # LangChain DeepAgents integration
│   ├── base_agent.py        # Abstract base class for all agents
│   ├── orchestrator.py      # Multi-agent orchestration (supervisor pattern)
│   ├── subagent.py          # Subagent definition and lifecycle
│   ├── tools.py             # Tool registration and execution
│   ├── memory.py            # Short-term and long-term memory management
│   └── routing.py           # Laya-based real-time routing
├── governance/              # GRC_Claw integration
│   ├── policy_engine.py     # Policy definition and evaluation
│   ├── firewall.py          # Agent Policy Firewall
│   ├── audit.py             # Immutable audit logging
│   ├── compliance.py        # GDPR/CCPA/CAN-SPAM/EU AI Act
│   ├── identity.py          # DID-based agent identity
│   └── trust_score.py       # Agent trust scoring
├── monitoring/              # OpenTelemetry instrumentation
│   ├── tracer.py            # Agent execution tracing
│   ├── metrics.py           # Prometheus metric definitions
│   ├── cost_tracker.py      # Token usage and cost tracking
│   └── alerting.py          # Alert rule definitions
├── security/                # Security primitives
│   ├── auth.py              # OAuth 2.1 + OIDC authentication
│   ├── rbac.py              # Role-based access control
│   ├── encryption.py        # Field-level encryption
│   └── sandbox.py           # Agent sandboxing (Docker-based)
├── data/                    # Data access layer
│   ├── postgres.py          # PostgreSQL connection pool
│   ├── snowflake.py         # Snowflake query interface
│   ├── redis.py             # Redis cache abstraction
│   ├── feature_store.py     # Feature store (Feast/Tecton)
│   └── models.py            # Shared Pydantic data models
├── integration/             # Integration hub
│   ├── mcp_server.py        # MCP server implementation
│   ├── mcp_client.py        # MCP client for tool discovery
│   ├── a2a.py               # A2A protocol handler
│   ├── connectors/          # Pre-built connectors (CRM, Ads, etc.)
│   └── webhooks.py          # Webhook ingestion and dispatch
├── events/                  # Event system
│   ├── publisher.py         # Kafka event publisher
│   ├── consumer.py          # Kafka event consumer
│   ├── schemas.py           # Event schema registry (Avro)
│   └── routing.py           # Event routing and filtering
├── graph/                   # ApexGraphSwarm integration
│   ├── builder.py           # Graph construction from events
│   ├── kernels.py           # Graph algorithm wrappers
│   └── attribution.py       # Shapley value attribution
├── supervision/             # Nerve integration
│   ├── dod.py               # Definition of Done
│   ├── verify.py            # Outcome verification
│   └── events.py            # Supervision event emission
└── config/                  # Configuration management
    ├── settings.py          # Pydantic settings (env-based)
    ├── secrets.py           # Secrets Manager integration
    └── feature_flags.py     # Feature flag management
```

### 2.3 Agent Framework Module

#### 2.3.1 Base Agent Class

```python
# @grc/core/agent_framework/base_agent.py
from abc import ABC, abstractmethod
from typing import Any, Optional
from pydantic import BaseModel, Field

class AgentConfig(BaseModel):
    agent_id: str
    agent_type: str
    model: str = "anthropic:claude-sonnet-5"
    autonomy_level: str = "L2"  # L1-L4
    max_blast_radius: int = 10000
    approval_threshold: str = "human"
    tools: list[str] = []
    subagents: list[dict] = []
    memory_scope: str = "project"  # project | global
    cost_budget_usd: float = 100.0

class AgentContext(BaseModel):
    tenant_id: str
    project_id: str
    campaign_id: Optional[str] = None
    customer_id: Optional[str] = None
    session_id: str
    trace_id: str
    metadata: dict[str, Any] = Field(default_factory=dict)

class AgentResult(BaseModel):
    success: bool
    output: Any
    reasoning_chain: list[dict]
    confidence: float
    cost_usd: float
    tokens_used: int
    duration_ms: int
    governance_verdict: str
    audit_hash: str

class BaseAgent(ABC):
    """Abstract base class for all marketing agents."""

    def __init__(self, config: AgentConfig):
        self.config = config
        self.tracer = AgentTracer(agent_id=config.agent_id, agent_type=config.agent_type)
        self.policy_engine = PolicyEngine(tenant_scope=config.tenant_id)
        self.cost_tracker = CostTracker(budget_usd=config.cost_budget_usd)
        self.memory = AgentMemory(scope=config.memory_scope)

    @abstractmethod
    async def execute(self, context: AgentContext, input_data: dict) -> AgentResult:
        """Execute the agent's primary task."""
        pass

    async def pre_execute(self, context: AgentContext) -> bool:
        """Governance check before execution. Returns True if allowed."""
        verdict = await self.policy_engine.evaluate(
            agent_id=self.config.agent_id,
            action="execute",
            context=context.model_dump(),
            blast_radius=self.config.max_blast_radius
        )
        return verdict.allowed

    async def post_execute(self, result: AgentResult, context: AgentContext):
        """Audit logging and cost tracking after execution."""
        await self.cost_tracker.record(result.cost_usd, result.tokens_used)
        await AuditLogger.log(
            agent_id=self.config.agent_id,
            context=context,
            result=result,
            hash=result.audit_hash
        )
```

#### 2.3.2 Orchestrator Pattern

```python
# @grc/core/agent_framework/orchestrator.py
class OrchestratorAgent(BaseAgent):
    """Supervisor agent that coordinates specialist agents."""

    def __init__(self, config: AgentConfig, specialists: list[BaseAgent]):
        super().__init__(config)
        self.specialists = {s.config.agent_type: s for s in specialists}
        self.consensus_engine = RaftConsensus()

    async def execute(self, context: AgentContext, goal: dict) -> AgentResult:
        # 1. Decompose goal into sub-tasks
        plan = await self._create_plan(goal, context)

        # 2. Dispatch to specialist agents
        results = []
        for task in plan.tasks:
            specialist = self.specialists[task.agent_type]
            result = await specialist.execute(context, task.input_data)
            results.append(result)

        # 3. Aggregate and reach consensus
        final_decision = await self.consensus_engine.propose(
            cluster=results,
            quorum=len(results) // 2 + 1
        )

        # 4. Return aggregated result
        return AgentResult(
            success=all(r.success for r in results),
            output=final_decision,
            reasoning_chain=[r.reasoning_chain for r in results],
            confidence=sum(r.confidence for r in results) / len(results),
            cost_usd=sum(r.cost_usd for r in results),
            tokens_used=sum(r.tokens_used for r in results),
            duration_ms=sum(r.duration_ms for r in results),
            governance_verdict="passed",
            audit_hash=self._compute_audit_hash(results)
        )
```

### 2.4 Governance Module

#### 2.4.1 Policy Engine

```python
# @grc/core/governance/policy_engine.py
class PolicyEngine:
    """Evaluates agent actions against governance policies."""

    def __init__(self, tenant_scope: str):
        self.tenant_scope = tenant_scope
        self.policy_store = PolicyStore()  # Compiled AST policies
        self.compliance_orchestrator = ComplianceOrchestrator()

    async def evaluate(
        self,
        agent_id: str,
        action: str,
        context: dict,
        blast_radius: int
    ) -> PolicyVerdict:
        # 1. Check agent identity (DID)
        identity = await self._verify_identity(agent_id)
        if not identity.valid:
            return PolicyVerdict(allowed=False, reason="invalid_identity")

        # 2. Check tool access
        if action not in identity.allowed_tools:
            return PolicyVerdict(allowed=False, reason="tool_not_authorized")

        # 3. Check blast radius
        if blast_radius > identity.max_blast_radius:
            return PolicyVerdict(allowed=False, reason="blast_radius_exceeded")

        # 4. Check compliance policies
        compliance = await self.compliance_orchestrator.check(
            action=action,
            context=context,
            regulations=["gdpr", "ccpa", "can-spam", "eu-ai-act"]
        )
        if not compliance.passed:
            return PolicyVerdict(allowed=False, reason="compliance_violation")

        # 5. Check spending guardrails
        if action in ["budget.reallocate", "bid.adjust"]:
            guardrail = await self._check_spending_guardrails(context)
            if not guardrail.passed:
                return PolicyVerdict(allowed=False, reason="guardrail_violation")

        return PolicyVerdict(allowed=True, reason="all_checks_passed")
```

#### 2.4.2 Agent Identity (DID)

```json
{
  "id": "did:grc:perf-mkt-agent-001",
  "credentials": [{
    "framework": "iso42001",
    "certifiedControls": ["A.6.1.1", "A.6.1.2", "A.6.1.3"],
    "toolTierAccess": ["read", "write"],
    "tenantScope": ["tenant-001"],
    "sovereignBoundary": "eu-only"
  }],
  "riskScore": 12,
  "status": "active",
  "metadata": {
    "channel": "paid-search",
    "budgetLimit": 50000,
    "brandGuidelinesVersion": "v3.2",
    "autonomyLevel": "L3"
  }
}
```

### 2.5 Monitoring Module

#### 2.5.1 Agent Tracing

```python
# @grc/core/monitoring/tracer.py
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider

class AgentTracer:
    """OpenTelemetry-based agent execution tracing."""

    def __init__(self, agent_id: str, agent_type: str):
        self.tracer = trace.get_tracer(__name__)
        self.agent_id = agent_id
        self.agent_type = agent_type

    @contextmanager
    def trace_execution(self, context: AgentContext):
        with self.tracer.start_as_current_span(
            f"agent.{self.agent_type}.execute",
            attributes={
                "agent.id": self.agent_id,
                "agent.type": self.agent_type,
                "tenant.id": context.tenant_id,
                "project.id": context.project_id,
                "trace.id": context.trace_id
            }
        ) as span:
            yield span

    def record_llm_call(self, span, model: str, tokens: int, cost: float):
        span.set_attribute("llm.model", model)
        span.set_attribute("llm.tokens", tokens)
        span.set_attribute("llm.cost_usd", cost)

    def record_tool_call(self, span, tool_name: str, duration_ms: int, success: bool):
        span.set_attribute("tool.name", tool_name)
        span.set_attribute("tool.duration_ms", duration_ms)
        span.set_attribute("tool.success", success)
```

#### 2.5.2 Cost Tracking

```python
# @grc/core/monitoring/cost_tracker.py
class CostTracker:
    """Tracks LLM token usage and cost per agent, per project, per tenant."""

    def __init__(self, budget_usd: float):
        self.budget_usd = budget_usd
        self.redis = RedisClient()

    async def record(self, cost_usd: float, tokens: int):
        key = f"cost:{self.agent_id}:{datetime.utcnow().strftime('%Y-%m-%d')}"
        await self.redis.hincrbyfloat(key, "total_cost", cost_usd)
        await self.redis.hincrby(key, "total_tokens", tokens)
        await self.redis.expire(key, 86400 * 30)  # 30-day retention

        # Check budget
        current = float(await self.redis.hget(key, "total_cost") or 0)
        if current > self.budget_usd:
            await self._trigger_budget_alert(current, self.budget_usd)
```

### 2.6 Data Layer Module

#### 2.6.1 Connection Management

```python
# @grc/core/data/postgres.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

class PostgresManager:
    """Async PostgreSQL connection pool with tenant isolation."""

    def __init__(self, dsn: str, pool_size: int = 20):
        self.engine = create_async_engine(
            dsn,
            pool_size=pool_size,
            max_overflow=10,
            pool_pre_ping=True,
            echo=False
        )
        self.session_factory = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def get_session(self, tenant_id: str) -> AsyncSession:
        """Get a session with tenant_id set for row-level security."""
        session = self.session_factory()
        await session.execute(f"SET app.tenant_id = '{tenant_id}'")
        return session
```

#### 2.6.2 Snowflake Integration

```python
# @grc/core/data/snowflake.py
from snowflake.connector import connect

class SnowflakeManager:
    """Snowflake data warehouse interface for analytics and ML training."""

    def __init__(self, account: str, user: str, password: str, warehouse: str):
        self.conn = connect(
            account=account, user=user, password=password,
            warehouse=warehouse, database="GRC_MARKETING"
        )

    async def query_analytics(self, query: str, params: dict = None) -> pd.DataFrame:
        """Execute analytics query and return DataFrame."""
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        return cursor.fetch_pandas_all()

    async def export_training_data(self, dataset: str, start_date: str, end_date: str):
        """Export labeled data for model training."""
        query = f"""
            SELECT * FROM {dataset}
            WHERE created_at BETWEEN %(start)s AND %(end)s
            AND label IS NOT NULL
        """
        return await self.query_analytics(query, {"start": start_date, "end": end_date})
```

### 2.7 Integration Hub Module

#### 2.7.1 MCP Server

```python
# @grc/core/integration/mcp_server.py
from mcp.server import Server
from mcp.types import Tool, Resource, Prompt

class GRCMCPServer:
    """MCP server exposing marketing tools to AI agents."""

    def __init__(self, project_id: str):
        self.server = Server(f"grc-{project_id}")
        self.tools = self._register_tools()

    def _register_tools(self) -> list[Tool]:
        return [
            Tool(
                name="get_campaign_metrics",
                description="Get performance metrics for a campaign",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "campaign_id": {"type": "string"},
                        "start_date": {"type": "string", "format": "date"},
                        "end_date": {"type": "string", "format": "date"}
                    },
                    "required": ["campaign_id"]
                }
            ),
            Tool(
                name="update_bid",
                description="Update bid for a campaign",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "campaign_id": {"type": "string"},
                        "bid_amount": {"type": "number"},
                        "platform": {"type": "string", "enum": ["google", "meta", "linkedin"]}
                    },
                    "required": ["campaign_id", "bid_amount", "platform"]
                }
            ),
            # ... more tools
        ]

    async def handle_request(self, request: dict) -> dict:
        """Handle JSON-RPC 2.0 requests."""
        method = request.get("method")
        params = request.get("params", {})

        if method == "tools/list":
            return {"tools": [t.model_dump() for t in self.tools]}
        elif method == "tools/call":
            return await self._execute_tool(params["name"], params["arguments"])
        elif method == "resources/list":
            return {"resources": self._list_resources()}
        else:
            raise MethodNotFoundError(f"Unknown method: {method}")
```

### 2.8 Event System Module

#### 2.8.1 Event Schema Registry

```python
# @grc/core/events/schemas.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class EventBase(BaseModel):
    event_id: str  # UUID v4
    event_type: str  # e.g., "campaign.created"
    source_project: str  # e.g., "campaign-optimization"
    tenant_id: str
    timestamp: datetime
    trace_id: str
    payload: dict

class CampaignCreatedEvent(EventBase):
    event_type: str = "campaign.created"
    payload: dict  # Campaign entity

class LeadScoredEvent(EventBase):
    event_type: str = "lead.scored"
    payload: dict  # Lead score entity

class BudgetReallocatedEvent(EventBase):
    event_type: str = "budget.reallocated"
    payload: dict  # Reallocation details

class AgentDecisionEvent(EventBase):
    event_type: str = "agent.decision_made"
    payload: dict  # Agent decision record
```

#### 2.8.2 Event Publisher

```python
# @grc/core/events/publisher.py
from confluent_kafka import Producer
import json

class EventPublisher:
    """Kafka event publisher with schema validation."""

    def __init__(self, bootstrap_servers: str, schema_registry_url: str):
        self.producer = Producer({
            "bootstrap.servers": bootstrap_servers,
            "client.id": "grc-event-publisher",
            "acks": "all",
            "enable.idempotence": True,
            "max.in.flight.requests.per.connection": 5
        })
        self.schema_registry = SchemaRegistry(schema_registry_url)

    async def publish(self, event: EventBase):
        """Publish event to Kafka with schema validation."""
        # Validate against schema
        schema = self.schema_registry.get_schema(event.event_type)
        validated = schema.validate(event.payload)

        # Produce to topic
        topic = f"grc.events.{event.source_project}.{event.event_type}"
        self.producer.produce(
            topic=topic,
            key=event.tenant_id,
            value=json.dumps(event.model_dump()),
            headers={
                "trace-id": event.trace_id,
                "tenant-id": event.tenant_id,
                "event-type": event.event_type
            }
        )
        self.producer.flush()
```

### 2.9 Configuration Management

```python
# @grc/core/config/settings.py
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Project
    PROJECT_ID: str
    PROJECT_NAME: str
    ENVIRONMENT: str = "production"  # dev | staging | production
    VERSION: str = "1.0.0"

    # Database
    POSTGRES_DSN: str
    SNOWFLAKE_ACCOUNT: str
    SNOWFLAKE_USER: str
    SNOWFLAKE_PASSWORD: str
    SNOWFLAKE_WAREHOUSE: str = "GRC_MARKETING"

    # Cache
    REDIS_URL: str
    REDIS_CLUSTER_NODES: str  # comma-separated

    # Kafka
    KAFKA_BOOTSTRAP_SERVERS: str
    KAFKA_SCHEMA_REGISTRY_URL: str

    # LLM
    ANTHROPIC_API_KEY: str
    OPENAI_API_KEY: str
    DEFAULT_LLM_MODEL: str = "anthropic:claude-sonnet-5"

    # Governance
    GRC_CLAW_GATEWAY_URL: str
    POLICY_STORE_PATH: str
    AUDIT_LOG_RETENTION_DAYS: int = 2555  # 7 years

    # Monitoring
    OTEL_EXPORTER_OTLP_ENDPOINT: str
    PROMETHEUS_PUSHGATEWAY: str
    COST_BUDGET_USD_PER_DAY: float = 100.0

    # Security
    JWT_SECRET: str
    ENCRYPTION_KEY_ID: str  # KMS key ID
    OAUTH_ISSUER: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

@lru_cache()
def get_settings() -> Settings:
    return Settings()
```

---

## 3. Project Template & Structure

### 3.1 Standard Directory Layout

Every project follows this exact structure. The template is available as a Cookiecutter template (`grc-project-template`).

```
project-name/
├── pyproject.toml              # Project metadata, dependencies
├── README.md                   # Project overview, setup, API docs
├── CHANGELOG.md                # Version history
├── LICENSE                     # Proprietary
├── .env.example                # Environment variable template
├── .gitignore
├── .dockerignore
├── Dockerfile                  # Multi-stage build
├── docker-compose.yml          # Local development
├── Makefile                    # Common commands
│
├── config/
│   ├── settings.yaml           # Project-specific settings
│   ├── agents.yaml             # Agent definitions
│   ├── policies/               # Governance policies
│   │   ├── gdpr.yaml
│   │   ├── ccpa.yaml
│   │   └── brand-safety.yaml
│   ├── features/               # Feature flags
│   │   └── flags.yaml
│   └── kubernetes/             # K8s manifests
│       ├── deployment.yaml
│       ├── service.yaml
│       ├── hpa.yaml
│       └── configmap.yaml
│
├── src/
│   └── project_name/
│       ├── __init__.py
│       ├── __main__.py         # Entry point
│       ├── api/                # REST API (FastAPI)
│       │   ├── __init__.py
│       │   ├── routes/
│       │   │   ├── __init__.py
│       │   │   ├── campaigns.py
│       │   │   ├── leads.py
│       │   │   └── health.py
│       │   ├── schemas/        # Pydantic request/response
│       │   │   ├── __init__.py
│       │   │   ├── requests.py
│       │   │   └── responses.py
│       │   └── dependencies.py  # FastAPI dependencies
│       │
│       ├── agents/             # Agent implementations
│       │   ├── __init__.py
│       │   ├── base.py         # Project-specific base agent
│       │   ├── orchestrator.py # Multi-agent orchestrator
│       │   ├── specialists/    # Specialist agents
│       │   │   ├── __init__.py
│       │   │   ├── research.py
│       │   │   ├── creative.py
│       │   │   ├── bidding.py
│       │   │   └── critic.py
│       │   └── tools/          # Agent tools
│       │       ├── __init__.py
│       │       ├── analytics.py
│       │       ├── audience.py
│       │       └── content.py
│       │
│       ├── services/           # Business logic
│       │   ├── __init__.py
│       │   ├── campaign_service.py
│       │   ├── scoring_service.py
│       │   └── routing_service.py
│       │
│       ├── models/             # Data models
│       │   ├── __init__.py
│       │   ├── entities.py     # SQLAlchemy models
│       │   ├── schemas.py      # Pydantic schemas
│       │   └── events.py       # Event definitions
│       │
│       ├── events/             # Event handlers
│       │   ├── __init__.py
│       │   ├── handlers.py     # Event consumers
│       │   └── publishers.py   # Event publishers
│       │
│       ├── integrations/       # External integrations
│       │   ├── __init__.py
│       │   ├── crm.py
│       │   ├── ad_platforms.py
│       │   └── analytics.py
│       │
│       ├── governance/         # Project-specific governance
│       │   ├── __init__.py
│       │   ├── policies.py     # Policy definitions
│       │   └── compliance.py   # Compliance rules
│       │
│       └── utils/              # Utilities
│           ├── __init__.py
│           ├── logging.py
│           └── helpers.py
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py             # Pytest fixtures
│   ├── unit/
│   │   ├── test_agents.py
│   │   ├── test_services.py
│   │   └── test_models.py
│   ├── integration/
│   │   ├── test_api.py
│   │   ├── test_events.py
│   │   └── test_integrations.py
│   └── e2e/
│       └── test_campaign_flow.py
│
├── alembic/                    # Database migrations
│   ├── versions/
│   └── env.py
│
├── scripts/
│   ├── seed_data.py
│   ├── migrate.py
│   └── health_check.py
│
├── docs/
│   ├── api.md                  # API documentation
│   ├── architecture.md         # Project architecture
│   └── runbook.md              # Operational runbook
│
└── helm/
    ├── Chart.yaml
    ├── values.yaml
    ├── values-staging.yaml
    ├── values-production.yaml
    └── templates/
        ├── deployment.yaml
        ├── service.yaml
        ├── ingress.yaml
        ├── configmap.yaml
        ├── secret.yaml
        └── hpa.yaml
```

### 3.2 Configuration Files

#### 3.2.1 `pyproject.toml`

```toml
[project]
name = "grc-campaign-optimization"
version = "1.0.0"
description = "Autonomous Campaign Optimization — Agentic AI Marketing"
readme = "README.md"
requires-python = ">=3.11"
license = {text = "Proprietary"}
authors = [{name = "Ahmed Hassan", email = "ahmed@grc-claw.com"}]

dependencies = [
    # Core library
    "@grc/core>=1.0.0,<2.0.0",

    # API
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.30.0",
    "websockets>=12.0",

    # Data
    "sqlalchemy[asyncio]>=2.0.0",
    "asyncpg>=0.29.0",
    "alembic>=1.13.0",
    "redis>=5.0.0",
    "snowflake-connector-python>=3.12.0",

    # Events
    "confluent-kafka>=2.5.0",
    "avro>=1.12.0",

    # Observability
    "opentelemetry-api>=1.27.0",
    "opentelemetry-sdk>=1.27.0",
    "opentelemetry-exporter-otlp>=1.27.0",
    "prometheus-client>=0.21.0",

    # Security
    "pyjwt>=2.9.0",
    "cryptography>=43.0.0",
    "passlib[bcrypt]>=1.7.4",

    # Utilities
    "pydantic>=2.9.0",
    "pydantic-settings>=2.5.0",
    "pyyaml>=6.0.1",
    "httpx>=0.27.0",
    "tenacity>=9.0.0",
    "structlog>=24.4.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.3.0",
    "pytest-asyncio>=0.24.0",
    "pytest-cov>=5.0.0",
    "httpx>=0.27.0",
    "ruff>=0.7.0",
    "mypy>=1.11.0",
    "pre-commit>=4.0.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_configs = true

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

#### 3.2.2 `config/agents.yaml`

```yaml
# Agent definitions for this project
agents:
  - id: agent_strategy_001
    type: strategy
    model: anthropic:claude-opus-4-6
    autonomy_level: L3
    max_blast_radius: 10000
    approval_threshold: human
    tools:
      - web_search
      - competitive_intelligence
      - market_research
    cost_budget_usd_per_day: 50.0

  - id: agent_research_001
    type: research
    model: anthropic:claude-sonnet-5
    autonomy_level: L2
    max_blast_radius: 5000
    tools:
      - web_search
      - social_listening
      - google_trends
    cost_budget_usd_per_day: 30.0

  - id: agent_creative_001
    type: creative
    model: openai:gpt-5.2
    autonomy_level: L2
    max_blast_radius: 5000
    tools:
      - content_generate
      - image_generate
      - brand_compliance_check
    cost_budget_usd_per_day: 40.0

  - id: agent_bidding_001
    type: bidding
    model: anthropic:claude-sonnet-5
    autonomy_level: L3
    max_blast_radius: 10000
    tools:
      - google_ads_api
      - meta_marketing_api
      - linkedin_campaign_api
    cost_budget_usd_per_day: 20.0

  - id: agent_critic_001
    type: critic
    model: anthropic:claude-opus-4-6
    autonomy_level: L2
    max_blast_radius: 10000
    tools:
      - analytics.read
      - brand_safety_check
      - compliance_check
    cost_budget_usd_per_day: 25.0
```

#### 3.2.3 `config/settings.yaml`

```yaml
# Project-specific settings
project:
  id: campaign-optimization
  name: "Autonomous Campaign Optimization"
  description: "Multi-agent system for autonomous campaign planning, execution, and optimization"

api:
  host: 0.0.0.0
  port: 8080
  workers: 4
  cors_origins:
    - "https://app.grc-claw.com"
    - "https://dashboard.grc-claw.com"

database:
  pool_size: 20
  max_overflow: 10
  pool_timeout: 30
  echo: false

kafka:
  consumer_group: campaign-optimization-cg
  auto_offset_reset: earliest
  enable_auto_commit: false
  max_poll_records: 500

features:
  enable_realtime_optimization: true
  enable_creative_generation: true
  enable_cross_channel_bidding: true
  enable_predictive_audience: false  # Coming in Phase 3

autonomy:
  default_level: L2
  escalation_threshold: 0.85  # Confidence below this triggers human review
  max_daily_spend_usd: 50000
  kill_switch_enabled: true
```

### 3.3 Dependencies Between Projects

```mermaid
graph LR
    subgraph PROJECTS["Projects"]
        CO[Campaign Optimization]
        LS[Lead Scoring]
        JO[Journey Orchestration]
        CG[Content Generation]
        BM[Brand Monitoring]
        SM[Social Media]
        EM[Email Marketing]
        SO[SEO Optimization]
        AA[Analytics & Attribution]
        MR[Market Research]
    end

    CO -->|creative requests| CG
    CO -->|audience segments| LS
    CO -->|journey events| JO
    LS -->|lead scores| JO
    LS -->|enrichment data| CO
    JO -->|journey state| CO
    JO -->|journey state| EM
    JO -->|journey state| SM
    CG -->|content assets| CO
    CG -->|content assets| EM
    CG -->|content assets| SM
    BM -->|brand signals| CO
    BM -->|sentiment| AA
    SO -->|content| CG
    SO -->|keywords| CO
    MR -->|market insights| CO
    MR -->|competitive intel| AA
    AA -->|attribution| CO
    AA -->|attribution| LS
```

---

## 4. Integration Patterns

### 4.1 Communication Patterns Overview

```mermaid
graph TB
    subgraph PATTERNS["Integration Patterns"]
        E1[Pattern 1: Event-Driven<br/>Kafka Topics]
        E2[Pattern 2: Request-Response<br/>REST API]
        E3[Pattern 3: Real-Time Stream<br/>WebSocket]
        E4[Pattern 4: Agent-to-Agent<br/>A2A Protocol]
        E5[Pattern 5: Tool Invocation<br/>MCP]
        E6[Pattern 6: Shared Data<br/>Database + Cache]
    end

    subgraph USE_CASES["Use Cases"]
        UC1[Cross-project event propagation]
        UC2[Synchronous API calls]
        UC3[Real-time dashboards]
        UC4[Agent task delegation]
        UC5[Agent tool access]
        UC6[Shared feature store]
    end

    E1 --> UC1
    E2 --> UC2
    E3 --> UC3
    E4 --> UC4
    E5 --> UC5
    E6 --> UC6
```

### 4.2 Pattern 1: Event-Driven (Kafka)

**When to use:** Asynchronous communication between projects, event propagation, decoupled workflows.

```mermaid
graph LR
    subgraph PRODUCER["Producer Project"]
        P1[Campaign Optimization]
    end

    subgraph KAFKA["Kafka Cluster"]
        T1[grc.events.campaign-optimization.campaign.created]
        T2[grc.events.campaign-optimization.budget.reallocated]
        T3[grc.events.campaign-optimization.variant.killed]
        T4[grc.events.lead-scoring.lead.scored]
        T5[grc.events.journey-orchestration.journey.updated]
    end

    subgraph CONSUMERS["Consumer Projects"]
        C1[Journey Orchestration]
        C2[Analytics & Attribution]
        C3[Email Marketing]
        C4[Brand Monitoring]
    end

    P1 --> T1
    P1 --> T2
    P1 --> T3
    T1 --> C1
    T2 --> C2
    T3 --> C4
    T4 --> C1
    T5 --> C3
```

**Topic naming convention:** `grc.events.{project-id}.{entity}.{action}`

**Event delivery guarantees:**
- At-least-once delivery (idempotent consumers)
- Exactly-once for critical financial events (transactions)
- Dead-letter queue for failed events (3 retries → DLQ)

### 4.3 Pattern 2: Request-Response (REST API)

**When to use:** Synchronous queries, CRUD operations, real-time API calls.

```mermaid
sequenceDiagram
    participant CO as Campaign Optimization
    participant LS as Lead Scoring
    participant API as API Gateway

    CO->>API: GET /api/v1/leads/{id}/score
    API->>LS: GET /api/v1/leads/{id}/score
    LS-->>API: 200 OK {score: 78, confidence: 0.85}
    API-->>CO: 200 OK {score: 78, confidence: 0.85}

    CO->>API: POST /api/v1/campaigns
    API->>CO: POST /api/v1/campaigns
    CO-->>API: 201 Created {campaign_id: "camp_001"}
    API-->>Client: 201 Created {campaign_id: "camp_001"}
```

**API standards:**
- OpenAPI 3.0 specification for every endpoint
- JSON request/response (Avro for internal events)
- OAuth 2.1 bearer token authentication
- Rate limiting: 1000 req/min per tenant
- Idempotency keys for POST/PUT operations
- Request/response correlation IDs for tracing

### 4.4 Pattern 3: Real-Time Stream (WebSocket)

**When to use:** Real-time dashboards, live campaign monitoring, agent decision streaming.

```mermaid
sequenceDiagram
    participant Client as Dashboard
    participant WS as WebSocket Gateway
    participant CO as Campaign Optimization
    participant KAFKA as Kafka

    Client->>WS: wss://api.grc-claw.com/v1/stream/campaigns/camp_001
    WS->>Client: Connection established

    CO->>KAFKA: Publish campaign.status_changed
    KAFKA->>WS: Event: campaign.status_changed
    WS->>Client: {"event": "campaign.status_changed", "data": {...}}

    CO->>KAFKA: Publish agent.decision_made
    KAFKA->>WS: Event: agent.decision_made
    WS->>Client: {"event": "agent.decision_made", "data": {...}}
```

### 4.5 Pattern 4: Agent-to-Agent (A2A Protocol)

**When to use:** Delegating tasks between agents in different projects, multi-project agent collaboration.

```mermaid
sequenceDiagram
    participant OA as Campaign Orchestrator
    participant A2A as A2A Protocol
    participant LS as Lead Scoring Agent
    participant JO as Journey Orchestration Agent

    OA->>A2A: Task delegation: "Score leads for campaign"
    A2A->>LS: Agent Card discovery
    LS-->>A2A: Capabilities: lead_scoring, churn_prediction
    A2A->>LS: Task: Score 500 leads
    LS-->>A2A: Task result: 500 leads scored
    A2A-->>OA: Task completed

    OA->>A2A: Task delegation: "Update journey for qualified leads"
    A2A->>JO: Agent Card discovery
    JO-->>A2A: Capabilities: journey_update, next_best_action
    A2A->>JO: Task: Update journeys for 50 qualified leads
    JO-->>A2A: Task result: 50 journeys updated
    A2A-->>OA: Task completed
```

**A2A Agent Card format:**

```json
{
  "name": "Lead Scoring Agent",
  "description": "AI-powered lead scoring and qualification",
  "url": "https://lead-scoring.grc-claw.com/a2a",
  "version": "1.0.0",
  "capabilities": {
    "streaming": true,
    "pushNotifications": true
  },
  "skills": [
    {
      "id": "lead-scoring",
      "name": "Lead Scoring",
      "description": "Score and qualify leads using multi-agent pipeline",
      "tags": ["scoring", "qualification", "prediction"]
    },
    {
      "id": "churn-prediction",
      "name": "Churn Prediction",
      "description": "Predict customer churn risk",
      "tags": ["churn", "prediction", "retention"]
    }
  ]
}
```

### 4.6 Pattern 5: Tool Invocation (MCP)

**When to use:** Agents need to invoke tools exposed by other projects or external systems.

```mermaid
sequenceDiagram
    participant Agent as Campaign Agent
    participant MCP as MCP Client
    participant Server as MCP Server (Lead Scoring)
    participant Ext as External API (Google Ads)

    Agent->>MCP: tools/list
    MCP->>Server: tools/list
    Server-->>MCP: [get_lead_score, get_churn_risk, ...]
    MCP-->>Agent: Available tools

    Agent->>MCP: tools/call(get_lead_score, {lead_id: "lead_001"})
    MCP->>Server: tools/call(get_lead_score, {lead_id: "lead_001"})
    Server->>Ext: Query lead data
    Ext-->>Server: Lead data
    Server-->>MCP: {score: 78, confidence: 0.85}
    MCP-->>Agent: {score: 78, confidence: 0.85}
```

### 4.7 Pattern 6: Shared Data (Database + Cache)

**When to use:** Shared feature store, cross-project analytics, real-time profile access.

```mermaid
graph TB
    subgraph SHARED["Shared Data Stores"]
        FS[Feature Store<br/>Redis / Feast]
        PG[(PostgreSQL<br/>Tenant-isolated)]
        SF[(Snowflake<br/>Analytics Warehouse)]
        VDB[(Vector DB<br/>Cognee Memory)]
    end

    subgraph PROJECTS["Projects"]
        CO[Campaign Optimization]
        LS[Lead Scoring]
        JO[Journey Orchestration]
    end

    CO -->|read/write features| FS
    LS -->|read/write features| FS
    JO -->|read/write features| FS

    CO -->|CRUD operations| PG
    LS -->|CRUD operations| PG
    JO -->|CRUD operations| PG

    CO -->|analytics queries| SF
    LS -->|analytics queries| SF
    JO -->|analytics queries| SF

    CO -->|memory store/recall| VDB
    LS -->|memory store/recall| VDB
    JO -->|memory store/recall| VDB
```

---

## 5. Shared Infrastructure

### 5.1 Infrastructure Overview

```mermaid
graph TB
    subgraph CLOUD["Multi-Cloud (AWS Primary)"]
        subgraph K8S["Kubernetes Cluster"]
            subgraph NS1["Namespace: campaign-optimization"]
                D1[Deployment: API]
                D2[Deployment: Agents]
                D3[Deployment: Workers]
            end
            subgraph NS2["Namespace: lead-scoring"]
                D4[Deployment: API]
                D5[Deployment: Agents]
                D6[Deployment: Workers]
            end
            subgraph NS3["Namespace: journey-orchestration"]
                D7[Deployment: API]
                D8[Deployment: Agents]
                D9[Deployment: Workers]
            end
            subgraph NS4["Namespace: shared-services"]
                D10[Deployment: Kafka Connect]
                D11[Deployment: MCP Gateway]
                D12[Deployment: Auth Service]
            end
        end

        subgraph DATA["Data Layer"]
            PG[(Amazon Aurora<br/>PostgreSQL 16)]
            SF[(Snowflake<br/>Data Warehouse)]
            RD[(ElastiCache<br/>Redis Cluster)]
            S3[(S3<br/>Artifact Storage)]
        end

        subgraph STREAMING["Streaming Layer"]
            MSK[(Amazon MSK<br/>Apache Kafka)]
        end

        subgraph MONITORING["Observability Stack"]
            PR[(Prometheus<br/>Metrics)]
            GR[(Grafana<br/>Dashboards)]
            LK[(Loki<br/>Logs)]
            TP[(Tempo<br/>Traces)]
        end
    end

    K8S --> DATA
    K8S --> STREAMING
    K8S --> MONITORING
```

### 5.2 Apache Kafka

#### 5.2.1 Cluster Configuration

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Brokers | 3 (multi-AZ) | HA with replication factor 3 |
| Partitions per topic | 12 | Parallel consumption |
| Replication factor | 3 | Durability |
| Min ISR | 2 | Consistency |
| Retention | 7 days (hot), 90 days (cold) | Cost optimization |
| Compression | LZ4 | Throughput |

#### 5.2.2 Topic Design

| Topic | Partitions | Retention | Purpose |
|-------|-----------|-----------|---------|
| `grc.events.{project}.{entity}.{action}` | 12 | 7 days | Inter-project events |
| `grc.commands.{project}.{action}` | 6 | 3 days | Command dispatch |
| `grc.audit.{tenant_id}` | 6 | 2555 days (7 years) | Audit trail |
| `grc.dlq.{project}` | 3 | 30 days | Dead letter queue |
| `grc.feature-updates` | 6 | 1 day | Feature store updates |

#### 5.2.3 Schema Registry

```json
{
  "type": "record",
  "name": "CampaignCreatedEvent",
  "namespace": "com.grc.events.campaign",
  "fields": [
    {"name": "event_id", "type": "string"},
    {"name": "event_type", "type": {"type": "enum", "name": "EventType", "symbols": ["campaign.created"]}},
    {"name": "source_project", "type": "string"},
    {"name": "tenant_id", "type": "string"},
    {"name": "timestamp", "type": {"type": "long", "logicalType": "timestamp-millis"}},
    {"name": "trace_id", "type": "string"},
    {"name": "payload", "type": {
      "type": "record",
      "name": "CampaignPayload",
      "fields": [
        {"name": "campaign_id", "type": "string"},
        {"name": "name", "type": "string"},
        {"name": "status", "type": "string"},
        {"name": "budget_total", "type": "double"},
        {"name": "autonomy_level", "type": "string"}
      ]
    }}
  ]
}
```

### 5.3 Redis Cluster

#### 5.3.1 Cluster Configuration

| Parameter | Value |
|-----------|-------|
| Nodes | 6 (3 masters + 3 replicas) |
| Memory per node | 16 GB |
| Max memory policy | allkeys-lru |
| Persistence | AOF (appendfsync everysec) |
| Cluster mode | Enabled |

#### 5.3.2 Data Structures

| Key Pattern | Type | Purpose | TTL |
|-------------|------|---------|-----|
| `session:{session_id}` | Hash | Agent session state | 24 hours |
| `feature:{entity}:{id}` | Hash | Feature store values | 7 days |
| `cost:{agent_id}:{date}` | Hash | Daily cost tracking | 30 days |
| `rate_limit:{tenant_id}` | String | Rate limit counters | 1 minute |
| `cache:{query_hash}` | String | Query result cache | 5 minutes |
| `lock:{resource}` | String | Distributed locks | 30 seconds |
| `queue:{project}` | List | Agent task queue | Persistent |

### 5.4 PostgreSQL

#### 5.4.1 Instance Configuration

| Parameter | Value |
|-----------|-------|
| Engine | PostgreSQL 16 |
| Instance | Amazon Aurora (Multi-AZ) |
| Instance class | db.r6g.2xlarge |
| Storage | 500 GB (auto-scaling) |
| Max connections | 500 |
| RLS | Enabled (tenant_id isolation) |
| Encryption | AES-256 (KMS) |
| Backup | 35-day retention, cross-region |

#### 5.4.2 Database Per Project

Each project gets its own database within the shared PostgreSQL cluster:

```
GRC_MARKETING (cluster)
├── campaign_optimization      # Project 1
├── lead_scoring               # Project 2
├── journey_orchestration      # Project 3
├── content_generation          # Project 4
├── brand_monitoring            # Project 5
├── social_media                # Project 6
├── email_marketing             # Project 7
├── seo_optimization            # Project 8
├── analytics_attribution       # Project 9
├── market_research             # Project 10
└── grc_core                    # Shared: tenants, users, audit
```

#### 5.4.3 Row-Level Security

```sql
-- Enable RLS on all tenant tables
ALTER TABLE campaigns ENABLE ROW LEVEL SECURITY;

-- Policy: tenants can only see their own data
CREATE POLICY tenant_isolation ON campaigns
    USING (tenant_id = current_setting('app.tenant_id')::TEXT);

-- Policy: agents can only access their assigned tenant
CREATE POLICY agent_tenant_isolation ON campaigns
    USING (tenant_id = current_setting('app.agent_tenant_id')::TEXT);
```

### 5.5 Snowflake

#### 5.5.1 Configuration

| Parameter | Value |
|-----------|-------|
| Warehouse | GRC_MARKETING (Medium, auto-suspend 5 min) |
| Database | GRC_MARKETING |
| Schemas | RAW, STAGING, ANALYTICS, ML |
| Clustering | tenant_id, event_date |
| Time travel | 90 days |

#### 5.5.2 Data Flow

```mermaid
graph LR
    subgraph SOURCES["Data Sources"]
        KAFKA[Kafka Events]
        PG[(PostgreSQL)]
        EXT[External APIs]
    end

    subgraph SNOWFLAKE["Snowflake"]
        RAW[RAW Schema<br/>Event ingestion]
        STG[STAGING Schema<br/>Cleansed data]
        ANA[ANALYTICS Schema<br/>Aggregated views]
        ML[ML Schema<br/>Training datasets]
    end

    KAFKA -->|Snowpipe| RAW
    pg -->|CDC / Fivetran| RAW
    EXT -->|Airbyte| RAW
    RAW --> STG --> ANA
    STG --> ML
```

### 5.6 Kubernetes

#### 5.6.1 Cluster Configuration

| Parameter | Value |
|-----------|-------|
| Version | 1.29+ |
| Node groups | general (m6i.2xlarge), gpu (g5.2xlarge), spot (m6i.xlarge) |
| Auto-scaling | Cluster Autoscaler + KEDA |
| Service mesh | Istio |
| Ingress | AWS ALB Ingress Controller |
| Secrets | AWS Secrets Manager + External Secrets Operator |
| Monitoring | Prometheus Operator + Grafana |

#### 5.6.2 Namespace Strategy

```
ai-marketing/
├── campaign-optimization/     # Project 1
├── lead-scoring/              # Project 2
├── journey-orchestration/     # Project 3
├── content-generation/         # Project 4
├── brand-monitoring/           # Project 5
├── social-media/               # Project 6
├── email-marketing/            # Project 7
├── seo-optimization/           # Project 8
├── analytics-attribution/      # Project 9
├── market-research/            # Project 10
├── shared-services/            # Kafka Connect, MCP Gateway, Auth
├── monitoring/                # Prometheus, Grafana, Loki, Tempo
└── kube-system/                # Kubernetes system
```

---

## 6. Governance Framework

### 6.1 Cross-Project Governance Architecture

```mermaid
graph TB
    subgraph GOVERNANCE["Governance Layer — GRC_Claw"]
        subgraph TIER1["Tier 1: Operating Layer"]
            ORCH[Unified Orchestrator<br/>Cross-project coordination]
            POLICY[Policy Engine<br/>Centralized policy evaluation]
            RBAC[RBAC<br/>Role-based access control]
        end

        subgraph TIER2["Tier 2: Decision Layer"]
            XAI[Explainable AI<br/>Decision trails]
            AUDIT[Audit Logger<br/>Immutable records]
            BIAS[Bias Detection<br/>Fairness scoring]
        end

        subgraph TIER3["Tier 3: Trust & Control"]
            DID[Agent Identity<br/>DID + Verifiable Credentials]
            FW[Policy Firewall<br/>Pre-execution checks]
            TS[Trust Score<br/>Agent reliability]
            DRIFT[Drift Detector<br/>Model monitoring]
            KILL[Kill Switch<br/>Emergency halt]
        end
    end

    subgraph PROJECTS["Projects"]
        P1[Campaign Optimization]
        P2[Lead Scoring]
        P3[Journey Orchestration]
        P4[Other Projects...]
    end

    subgraph COMPLIANCE["Compliance"]
        GDPR[GDPR]
        CCPA[CCPA/CPRA]
        CANSPAM[CAN-SPAM]
        EUIA[EU AI Act]
        HIPAA[HIPAA]
    end

    PROJECTS -->|Every action| FW
    FW -->|Policy check| POLICY
    POLICY -->|Compliance| COMPLIANCE
    PROJECTS -->|Audit trail| AUDIT
    PROJECTS -->|Identity| DID
    PROJECTS -->|Trust scoring| TS
    PROJECTS -->|Drift detection| DRIFT
    PROJECTS -->|Explainability| XAI
```

### 6.2 Autonomy Levels

```mermaid
graph TD
    L1[L1: Advisory<br/>Agents recommend, humans approve] --> L2[L2: Supervised Execution<br/>Low-risk automated, high-risk approved]
    L2 --> L3[L3: Constrained Autonomy<br/>Agents allocate within thresholds]
    L3 --> L4[L4: Adaptive Optimization<br/>Policies updated via experimentation]
```

| Level | Description | Use Case | Approval |
|-------|-------------|----------|----------|
| **L1: Advisory** | Agents recommend; humans approve all actions | Initial deployment, high-risk channels | All actions |
| **L2: Supervised Execution** | Low-risk actions automated; high-risk require approval | Email timing, creative rotation | High-risk only |
| **L3: Constrained Autonomy** | Agents allocate budget within explicit thresholds | Bid management, budget pacing | Threshold breaches |
| **L4: Adaptive Optimization** | Policies updated via monitored experimentation | Full-funnel optimization | Exception-based |

### 6.3 Risk Tiering & Approval Gates

| Risk Level | Decision Types | Approval Required | Auto-Execute |
|------------|---------------|-------------------|--------------|
| **Low** | Content refresh, segment grooming, reporting | None | Yes |
| **Medium** | New campaign launch, new creative claims | Notify + time-bound auto-approve | Yes (with timeout) |
| **High** | Budget reallocation >15%, regulated claims, new audience targeting | Human approval | No |
| **Critical** | Strategic positioning, brand-sensitive creative | Human approval + legal review | No |

### 6.4 Compliance Mapping

| Regulation | Marketing Controls | Enforcement Point |
|------------|-------------------|-------------------|
| **GDPR** | Consent management, right to erasure, data minimization, Art. 22 automated decisions | Audience targeting, data processing |
| **CCPA/CPRA** | Opt-out rights, data sale disclosure, behavioral profile protection | Data sharing, third-party integrations |
| **CAN-SPAM** | Unsubscribe headers, subject line accuracy, physical address | Email campaigns |
| **CASL** | Consent requirements, identification, unsubscribe | Canadian email marketing |
| **EU AI Act** | Transparency, risk classification, human oversight | AI-generated content, automated decision-making |
| **HIPAA** | PHI protection, tenant isolation | Healthcare marketing (if applicable) |

### 6.5 Audit Trail Schema

```sql
CREATE TABLE audit_log (
    audit_id BIGSERIAL PRIMARY KEY,
    event_id UUID NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    agent_id VARCHAR(100) NOT NULL,
    agent_type VARCHAR(50) NOT NULL,
    tenant_id VARCHAR(100) NOT NULL,
    project_id VARCHAR(100) NOT NULL,
    action VARCHAR(100) NOT NULL,
    context JSONB NOT NULL,
    decision JSONB NOT NULL,
    governance_verdict VARCHAR(50) NOT NULL,
    policy_checks JSONB NOT NULL,
    blast_radius INTEGER,
    approval_status VARCHAR(50),
    approved_by VARCHAR(100),
    evidence_hash VARCHAR(64) NOT NULL,  -- SHA-256
    trace_id VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Partitioning
    CONSTRAINT audit_log_partition_check CHECK (created_at >= '2026-01-01')
) PARTITION BY RANGE (created_at);

-- Indexes
CREATE INDEX idx_audit_tenant ON audit_log (tenant_id, created_at DESC);
CREATE INDEX idx_audit_agent ON audit_log (agent_id, created_at DESC);
CREATE INDEX idx_audit_event ON audit_log (event_type, created_at DESC);
CREATE INDEX idx_audit_evidence ON audit_log (evidence_hash);
```

### 6.6 Agent Trust Score

```python
# Trust score calculation
class TrustScoreEngine:
    """Computes agent trust score based on historical performance."""

    def compute_score(self, agent_id: str, window_days: int = 30) -> float:
        decisions = self.get_decisions(agent_id, window_days)
        
        if not decisions:
            return 0.5  # Neutral score for new agents

        # Factors
        success_rate = sum(1 for d in decisions if d.outcome == "success") / len(decisions)
        compliance_rate = sum(1 for d in decisions if d.governance_verdict == "passed") / len(decisions)
        avg_confidence = sum(d.confidence for d in decisions) / len(decisions)
        human_override_rate = sum(1 for d in decisions if d.human_override) / len(decisions)
        anomaly_flags = self.get_anomaly_flags(agent_id, window_days)

        # Weighted score
        score = (
            0.35 * success_rate +
            0.25 * compliance_rate +
            0.20 * avg_confidence +
            0.10 * (1 - human_override_rate) +
            0.10 * (1 - min(len(anomaly_flags) / 10, 1.0))
        )

        return round(score, 2)
```

---

## 7. Deployment Strategy

### 7.1 Multi-Project Deployment Architecture

```mermaid
graph TB
    subgraph GITOPS["GitOps — ArgoCD"]
        REPO[Git Repository<br/>per project]
        ARGO[ArgoCD<br/>Application Controller]
    end

    subgraph CI["CI/CD Pipeline"]
        GH[GitHub Actions]
        BUILD[Build & Test]
        SCAN[Security Scan]
        PUSH[Push to ECR]
    end

    subgraph K8S["Kubernetes Cluster"]
        subgraph NS["Namespace: project-name"]
            DEP[Deployment]
            SVC[Service]
            ING[Ingress]
            HPA[Horizontal Pod Autoscaler]
            VPA[Vertical Pod Autoscaler]
        end
    end

    subgraph HELM["Helm Charts"]
        CHART[Project Chart<br/>helm/project-name/]
        VALUES[Values Files<br/>values-{env}.yaml]
    end

    REPO --> GH
    GH --> BUILD --> SCAN --> PUSH
    PUSH --> ARGO
    ARGO --> CHART
    CHART --> K8S
```

### 7.2 Docker Configuration

#### 7.2.1 Dockerfile (Multi-Stage)

```dockerfile
# Stage 1: Builder
FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
RUN pip install --no-cache-dir hatchling

COPY src/ src/
RUN hatchling build --hooks-only

# Stage 2: Runtime
FROM python:3.11-slim AS runtime

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -r grc && useradd -r -g grc grc

COPY --from=builder /app/dist/*.whl /tmp/
RUN pip install --no-cache-dir /tmp/*.whl && rm /tmp/*.whl

COPY --chown=grc:grc src/ src/

USER grc

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

CMD ["uvicorn", "project_name.__main__:app", "--host", "0.0.0.0", "--port", "8080"]
```

#### 7.2.2 Docker Compose (Local Development)

```yaml
version: "3.9"

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile
      target: runtime
    ports:
      - "8080:8080"
    environment:
      - POSTGRES_DSN=postgresql+asyncpg://grc:grc@postgres:5432/campaign_optimization
      - REDIS_URL=redis://redis:6379/0
      - KAFKA_BOOTSTRAP_SERVERS=kafka:9092
      - OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4318
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      kafka:
        condition: service_healthy
    volumes:
      - ./config:/app/config:ro

  worker:
    build:
      context: .
      dockerfile: Dockerfile
      target: runtime
    command: ["python", "-m", "project_name.worker"]
    environment:
      - POSTGRES_DSN=postgresql+asyncpg://grc:grc@postgres:5432/campaign_optimization
      - REDIS_URL=redis://redis:6379/0
      - KAFKA_BOOTSTRAP_SERVERS=kafka:9092
    depends_on:
      - kafka
      - redis

  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: grc
      POSTGRES_PASSWORD: grc
      POSTGRES_DB: campaign_optimization
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U grc"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5

  kafka:
    image: confluentinc/cp-kafka:7.6.0
    ports:
      - "9092:9092"
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
    depends_on:
      - zookeeper
    healthcheck:
      test: ["CMD", "kafka-broker-api-versions", "--bootstrap-server", "localhost:9092"]
      interval: 10s
      timeout: 5s
      retries: 5

  zookeeper:
    image: confluentinc/cp-zookeeper:7.6.0
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181

volumes:
  postgres_data:
```

### 7.3 Helm Chart

#### 7.3.1 Chart Structure

```
helm/project-name/
├── Chart.yaml
├── values.yaml
├── values-staging.yaml
├── values-production.yaml
└── templates/
    ├── _helpers.tpl
    ├── deployment.yaml
    ├── service.yaml
    ├── ingress.yaml
    ├── configmap.yaml
    ├── secret.yaml
    ├── hpa.yaml
    ├── pdb.yaml
    ├── serviceaccount.yaml
    ├── networkpolicy.yaml
    └── servicemonitor.yaml
```

#### 7.3.2 Chart.yaml

```yaml
apiVersion: v2
name: grc-campaign-optimization
description: Autonomous Campaign Optimization — Agentic AI Marketing
type: application
version: 1.0.0
appVersion: "1.0.0"
keywords:
  - agentic-ai
  - marketing
  - autonomous-campaigns
maintainers:
  - name: Ahmed Hassan
    email: ahmed@grc-claw.com
dependencies:
  - name: postgresql
    version: 15.5.0
    repository: https://charts.bitnami.com/bitnami
    condition: postgresql.enabled
  - name: redis
    version: 20.0.0
    repository: https://charts.bitnami.com/bitnami
    condition: redis.enabled
```

#### 7.3.3 Deployment Template

```yaml
# templates/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "project-name.fullname" . }}
  labels:
    {{- include "project-name.labels" . | nindent 4 }}
spec:
  replicas: {{ .Values.replicaCount }}
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      {{- include "project-name.selectorLabels" . | nindent 6 }}
  template:
    metadata:
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8080"
        prometheus.io/path: "/metrics"
        checksum/config: {{ include (print $.Template.BasePath "/configmap.yaml") . | sha256sum }}
      labels:
        {{- include "project-name.selectorLabels" . | nindent 8 }}
    spec:
      serviceAccountName: {{ include "project-name.serviceAccountName" . }}
      securityContext:
        runAsNonRoot: true
        runAsUser: 999
        fsGroup: 999
      containers:
        - name: {{ .Chart.Name }}
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag | default .Chart.AppVersion }}"
          imagePullPolicy: {{ .Values.image.pullPolicy }}
          ports:
            - name: http
              containerPort: 8080
              protocol: TCP
            - name: metrics
              containerPort: 9090
              protocol: TCP
          envFrom:
            - configMapRef:
                name: {{ include "project-name.fullname" . }}-config
            - secretRef:
                name: {{ include "project-name.fullname" . }}-secrets
          resources:
            {{- toYaml .Values.resources | nindent 12 }}
          livenessProbe:
            httpGet:
              path: /health/live
              port: http
            initialDelaySeconds: 30
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /health/ready
              port: http
            initialDelaySeconds: 10
            periodSeconds: 5
          startupProbe:
            httpGet:
              path: /health/startup
              port: http
            failureThreshold: 30
            periodSeconds: 10
          volumeMounts:
            - name: tmp
              mountPath: /tmp
      volumes:
        - name: tmp
          emptyDir: {}
      {{- with .Values.nodeSelector }}
      nodeSelector:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      {{- with .Values.tolerations }}
      tolerations:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      {{- with .Values.affinity }}
      affinity:
        {{- toYaml . | nindent 8 }}
      {{- end }}
```

#### 7.3.4 Values Files

```yaml
# values-production.yaml
replicaCount: 3

image:
  repository: 123456789012.dkr.ecr.us-east-1.amazonaws.com/grc-campaign-optimization
  tag: "1.0.0"
  pullPolicy: IfNotPresent

resources:
  requests:
    cpu: 500m
    memory: 1Gi
  limits:
    cpu: 2000m
    memory: 4Gi

autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 20
  targetCPUUtilizationPercentage: 70
  targetMemoryUtilizationPercentage: 80
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
        - type: Percent
          value: 10
          periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 0
      policies:
        - type: Percent
          value: 100
          periodSeconds: 15

podDisruptionBudget:
  enabled: true
  minAvailable: 2

ingress:
  enabled: true
  className: alb
  annotations:
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
    alb.ingress.kubernetes.io/listen-ports: '[{"HTTPS":443}]'
    alb.ingress.kubernetes.io/certificate-arn: arn:aws:acm:us-east-1:123456789012:certificate/xxx
  hosts:
    - host: campaign-optimization.grc-claw.com
      paths:
        - path: /
          pathType: Prefix

config:
  ENVIRONMENT: production
  LOG_LEVEL: INFO
  PROJECT_ID: campaign-optimization
  KAFKA_CONSUMER_GROUP: campaign-optimization-cg
  KAFKA_AUTO_OFFSET_RESET: earliest
  COST_BUDGET_USD_PER_DAY: "100.0"
  DEFAULT_LLM_MODEL: "anthropic:claude-sonnet-5"

secrets:
  POSTGRES_DSN: ""
  REDIS_URL: ""
  KAFKA_BOOTSTRAP_SERVERS: ""
  ANTHROPIC_API_KEY: ""
  OPENAI_API_KEY: ""
  JWT_SECRET: ""
  ENCRYPTION_KEY_ID: ""

networkPolicy:
  enabled: true
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              name: istio-system
      ports:
        - protocol: TCP
          port: 8080
  egress:
    - to:
        - namespaceSelector:
            matchLabels:
              name: monitoring
      ports:
        - protocol: TCP
          port: 9090
```

### 7.4 Deployment Environments

| Environment | Cluster | Namespace | Replicas | Auto-scaling | Purpose |
|-------------|---------|-----------|----------|--------------|---------|
| **Dev** | EKS (single-AZ) | `*-dev` | 1 | No | Local development, feature branches |
| **Staging** | EKS (multi-AZ) | `*-staging` | 2 | Yes (1-5) | Integration testing, QA |
| **Production** | EKS (multi-AZ) | `*-production` | 3+ | Yes (3-20) | Live traffic |
| **DR** | GKE (multi-region) | `*-dr` | 3+ | Yes (3-20) | Disaster recovery |

---

## 8. CI/CD Pipeline Template

### 8.1 Pipeline Architecture

```mermaid
graph LR
    subgraph TRIGGER["Trigger"]
        PR[Pull Request]
        PUSH[Push to main]
        TAG[Tag Release]
    end

    subgraph CI["Continuous Integration"]
        LINT[Lint & Type Check]
        TEST[Unit Tests]
        COV[Coverage]
        BUILD[Build Image]
        SCAN[Security Scan]
    end

    subgraph CD["Continuous Deployment"]
        PUSH_ECR[Push to ECR]
        DEPLOY_STG[Deploy to Staging]
        E2E[E2E Tests]
        DEPLOY_PRD[Deploy to Production]
        VERIFY[Smoke Tests]
    end

    TRIGGER --> CI
    CI --> CD
```

### 8.2 GitHub Actions Workflow

```yaml
# .github/workflows/ci-cd.yaml
name: CI/CD Pipeline

on:
  pull_request:
    branches: [main, develop]
  push:
    branches: [main]
    tags: ["v*"]

env:
  PYTHON_VERSION: "3.11"
  POETRY_VERSION: "1.8.0"
  ECR_REGISTRY: "123456789012.dkr.ecr.us-east-1.amazonaws.com"
  IMAGE_NAME: "grc-campaign-optimization"

jobs:
  # ──────────────────────────────────────────────
  # Stage 1: Lint & Type Check
  # ──────────────────────────────────────────────
  lint:
    name: Lint & Type Check
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Install dependencies
        run: |
          pip install ruff mypy
          pip install -e ".[dev]"

      - name: Ruff lint
        run: ruff check src/ tests/

      - name: Ruff format check
        run: ruff format --check src/ tests/

      - name: MyPy type check
        run: mypy src/ --strict

  # ──────────────────────────────────────────────
  # Stage 2: Unit Tests
  # ──────────────────────────────────────────────
  test:
    name: Unit Tests
    runs-on: ubuntu-latest
    needs: lint
    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_USER: grc
          POSTGRES_PASSWORD: grc
          POSTGRES_DB: test_campaign_optimization
        ports:
          - 5432:5432
        options: >-
          --health-cmd "pg_isready -U grc"
          --health-interval 5s
          --health-timeout 5s
          --health-retries 5
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 5s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Install dependencies
        run: pip install -e ".[dev]"

      - name: Run unit tests
        run: pytest tests/unit/ -v --cov=src --cov-report=xml --cov-report=term
        env:
          POSTGRES_DSN: postgresql+asyncpg://grc:grc@localhost:5432/test_campaign_optimization
          REDIS_URL: redis://localhost:6379/0

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          file: ./coverage.xml
          fail_ci_if_error: true

  # ──────────────────────────────────────────────
  # Stage 3: Security Scan
  # ──────────────────────────────────────────────
  security:
    name: Security Scan
    runs-on: ubuntu-latest
    needs: lint
    steps:
      - uses: actions/checkout@v4

      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: fs
          scan-ref: .
          severity: CRITICAL,HIGH
          exit-code: "1"

      - name: Run Bandit security linter
        run: |
          pip install bandit
          bandit -r src/ -f json -o bandit-report.json || true

      - name: Run pip-audit
        run: |
          pip install pip-audit
          pip-audit --strict

      - name: Upload security report
        uses: actions/upload-artifact@v4
        with:
          name: security-report
          path: bandit-report.json

  # ──────────────────────────────────────────────
  # Stage 4: Build & Push Docker Image
  # ──────────────────────────────────────────────
  build:
    name: Build & Push Image
    runs-on: ubuntu-latest
    needs: [test, security]
    if: github.event_name == 'push'
    outputs:
      image_tag: ${{ steps.meta.outputs.tags }}
      image_digest: ${{ steps.build.outputs.digest }}
    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1

      - name: Login to Amazon ECR
        uses: aws-actions/amazon-ecr-login@v2

      - name: Extract metadata
        id: meta
        run: |
          VERSION=$(echo ${{ github.ref }} | sed 's/refs\/tags\/v//')
          if [ -z "$VERSION" ]; then
            VERSION=${{ github.sha }}
          fi
          echo "tags=${{ env.ECR_REGISTRY }}/${{ env.IMAGE_NAME }}:${VERSION}" >> $GITHUB_OUTPUT
          echo "version=${VERSION}" >> $GITHUB_OUTPUT

      - name: Build and push
        id: build
        uses: docker/build-push-action@v6
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
          platforms: linux/amd64,linux/arm64

      - name: Scan image with Trivy
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: ${{ steps.meta.outputs.tags }}
          severity: CRITICAL,HIGH
          exit-code: "1"

  # ──────────────────────────────────────────────
  # Stage 5: Deploy to Staging
  # ──────────────────────────────────────────────
  deploy-staging:
    name: Deploy to Staging
    runs-on: ubuntu-latest
    needs: build
    if: github.ref == 'refs/heads/main'
    environment:
      name: staging
      url: https://staging-campaign-optimization.grc-claw.com
    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1

      - name: Update kubeconfig
        run: aws eks update-kubeconfig --name grc-staging-cluster

      - name: Deploy with Helm
        run: |
          helm upgrade --install campaign-optimization ./helm/project-name \
            --namespace campaign-optimization-staging \
            --values ./helm/project-name/values-staging.yaml \
            --set image.tag=${{ github.sha }} \
            --wait --timeout 5m

      - name: Run smoke tests
        run: |
          curl -sf https://staging-campaign-optimization.grc-claw.com/health/ready
          curl -sf https://staging-campaign-optimization.grc-claw.com/health/live

      - name: Run E2E tests
        run: |
          pip install -e ".[dev]"
          pytest tests/e2e/ -v --base-url=https://staging-campaign-optimization.grc-claw.com

  # ──────────────────────────────────────────────
  # Stage 6: Deploy to Production
  # ──────────────────────────────────────────────
  deploy-production:
    name: Deploy to Production
    runs-on: ubuntu-latest
    needs: build
    if: startsWith(github.ref, 'refs/tags/v')
    environment:
      name: production
      url: https://campaign-optimization.grc-claw.com
    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1

      - name: Update kubeconfig
        run: aws eks update-kubeconfig --name grc-production-cluster

      - name: Deploy with Helm (Canary)
        run: |
          helm upgrade --install campaign-optimization ./helm/project-name \
            --namespace campaign-optimization-production \
            --values ./helm/project-name/values-production.yaml \
            --set image.tag=${{ steps.meta.outputs.version }} \
            --set canary.enabled=true \
            --set canary.weight=10 \
            --wait --timeout 10m

      - name: Canary analysis (5 min)
        run: |
          echo "Running canary analysis..."
          sleep 300
          # Check error rate, latency, business metrics
          ERROR_RATE=$(curl -s "https://prometheus.grc-claw.com/api/v1/query?query=..." | jq '.data.result[0].value[1]')
          if (( $(echo "$ERROR_RATE > 0.01" | bc -l) )); then
            echo "Canary failed: error rate $ERROR_RATE"
            helm rollback campaign-optimization 0 -n campaign-optimization-production
            exit 1
          fi

      - name: Promote to 100%
        run: |
          helm upgrade --install campaign-optimization ./helm/project-name \
            --namespace campaign-optimization-production \
            --values ./helm/project-name/values-production.yaml \
            --set image.tag=${{ steps.meta.outputs.version }} \
            --set canary.enabled=false \
            --wait --timeout 10m

      - name: Run production smoke tests
        run: |
          curl -sf https://campaign-optimization.grc-claw.com/health/ready
          curl -sf https://campaign-optimization.grc-claw.com/health/live

      - name: Notify Slack
        uses: slackapi/slack-github-action@v1
        with:
          payload: |
            {
              "text": "✅ Deployed ${{ env.IMAGE_NAME }}:${{ steps.meta.outputs.version }} to production"
            }
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
```

### 8.3 Pipeline Stages Summary

| Stage | Jobs | Trigger | Duration | Gates |
|-------|------|---------|----------|-------|
| **CI** | Lint, Type Check | Every PR | 2 min | Zero errors |
| **CI** | Unit Tests | Every PR | 5 min | >80% coverage |
| **CI** | Security Scan | Every PR | 3 min | Zero CRITICAL/HIGH |
| **CD** | Build & Push | Push to main/tag | 5 min | Image scanned |
| **CD** | Deploy Staging | Push to main | 3 min | Smoke tests pass |
| **CD** | E2E Tests | After staging deploy | 10 min | All tests pass |
| **CD** | Deploy Production | Tag release | 15 min | Canary analysis pass |
| **CD** | Smoke Tests | After prod deploy | 2 min | Health checks pass |

---

## 9. Monitoring & Observability

### 9.1 Cross-Project Monitoring Architecture

```mermaid
graph TB
    subgraph COLLECTION["Collection Layer"]
        OTEL[OpenTelemetry SDK<br/>Auto-instrumentation]
        PROM[Prometheus Exporters<br/>Custom metrics]
        FLUENT[Fluent Bit<br/>Log shipping]
    end

    subgraph PROCESSING["Processing Layer"]
        FLINK[Apache Flink<br/>Stream processing]
        VECTOR[Vector<br/>Log transformation]
        COST[Cost Aggregation<br/>Token → Dollar]
    end

    subgraph STORAGE["Storage Layer"]
        PROMETHEUS[(Prometheus / Mimir<br/>Metrics)]
        LOKI[(Loki<br/>Logs)]
        TEMPO[(Tempo<br/>Traces)]
        CLICKHOUSE[(ClickHouse<br/>Events)]
    end

    subgraph PRESENTATION["Presentation Layer"]
        GRAFANA[Grafana<br/>Unified Dashboards]
        ALERT[Alertmanager<br/>Multi-channel alerts]
        COST_EXPLORER[Cost Explorer<br/>Per-agent cost]
    end

    COLLECTION --> PROCESSING --> STORAGE --> PRESENTATION
```

### 9.2 Metrics Architecture

#### 9.2.1 Metric Categories

| Category | Metrics | Labels | Storage |
|----------|---------|--------|---------|
| **Agent Performance** | execution_total, duration, tokens, cost | agent_id, agent_type, model | Prometheus |
| **Campaign Performance** | impressions, clicks, conversions, spend, roas | campaign_id, channel, variant_id | Prometheus |
| **API Performance** | request_duration, request_count, error_rate | endpoint, method, status | Prometheus |
| **Infrastructure** | cpu, memory, disk, network | node, pod, namespace | Prometheus |
| **Business** | leads_scored, campaigns_created, revenue | tenant_id, project_id | ClickHouse |
| **Cost** | llm_cost, infrastructure_cost, total_cost | agent_id, project_id, tenant_id | Prometheus |

#### 9.2.2 Key Metric Definitions

```yaml
# Prometheus metric definitions
metrics:
  # Agent metrics
  - name: agent_execution_total
    type: counter
    description: Total agent executions
    labels: [agent_id, agent_type, status, tenant_id]

  - name: agent_execution_duration_seconds
    type: histogram
    description: Agent execution duration
    labels: [agent_id, agent_type]
    buckets: [0.1, 0.5, 1, 2, 5, 10, 30, 60, 120, 300]

  - name: agent_llm_cost_dollars
    type: counter
    description: LLM cost per agent
    labels: [agent_id, model, provider, tenant_id]

  - name: agent_tool_calls_total
    type: counter
    description: Tool invocations per agent
    labels: [agent_id, tool_name, status]

  # Campaign metrics
  - name: campaign_spend_total
    type: counter
    description: Total campaign spend
    labels: [campaign_id, channel, tenant_id]

  - name: campaign_conversions_total
    type: counter
    description: Total conversions
    labels: [campaign_id, channel, variant_id]

  - name: campaign_roas
    type: gauge
    description: Return on ad spend
    labels: [campaign_id, channel]

  # API metrics
  - name: http_request_duration_seconds
    type: histogram
    description: HTTP request duration
    labels: [method, endpoint, status_code]

  - name: http_requests_total
    type: counter
    description: HTTP request count
    labels: [method, endpoint, status_code]

  # Cost metrics
  - name: daily_llm_cost_dollars
    type: gauge
    description: Daily LLM cost
    labels: [project_id, tenant_id]

  - name: daily_infrastructure_cost_dollars
    type: gauge
    description: Daily infrastructure cost
    labels: [project_id, tenant_id]
```

### 9.3 Grafana Dashboards

#### 9.3.1 Dashboard Inventory

| Dashboard | Purpose | Refresh | Panels |
|-----------|---------|---------|--------|
| **Agent Health** | Agent performance, errors, trust scores | 30s | 12 |
| **Campaign Performance** | Real-time campaign metrics, ROAS, CPA | 15s | 16 |
| **Cost Explorer** | LLM cost, infrastructure cost, budget tracking | 1m | 10 |
| **API Performance** | Request rate, latency, error rate | 30s | 8 |
| **Governance** | Policy violations, audit events, compliance | 1m | 8 |
| **Infrastructure** | K8s pods, nodes, resource utilization | 30s | 12 |
| **Cross-Project** | All projects overview, event flow | 30s | 14 |

#### 9.3.2 Agent Health Dashboard (Key Panels)

```json
{
  "dashboard": {
    "title": "Agent Health — Campaign Optimization",
    "refresh": "30s",
    "panels": [
      {
        "title": "Agent Execution Rate",
        "type": "timeseries",
        "targets": [{
          "expr": "rate(agent_execution_total[5m])",
          "legendFormat": "{{agent_type}} — {{agent_id}}"
        }]
      },
      {
        "title": "Agent Error Rate",
        "type": "timeseries",
        "targets": [{
          "expr": "rate(agent_execution_total{status=\"error\"}[5m]) / rate(agent_execution_total[5m])",
          "legendFormat": "{{agent_type}}"
        }],
        "alert": {
          "conditions": [{
            "evaluator": {"params": [0.05], "type": "gt"},
            "operator": {"type": "and"},
            "query": {"params": ["A", "5m", "now"]},
            "reducer": {"type": "avg"}
          }],
          "name": "High agent error rate",
          "message": "Agent error rate > 5%"
        }
      },
      {
        "title": "LLM Cost per Agent",
        "type": "bargauge",
        "targets": [{
          "expr": "agent_llm_cost_dollars",
          "legendFormat": "{{agent_id}} ({{model}})"
        }]
      },
      {
        "title": "Agent Trust Score",
        "type": "stat",
        "targets": [{
          "expr": "agent_trust_score",
          "legendFormat": "{{agent_id}}"
        }],
        "thresholds": {
          "steps": [
            {"color": "red", "value": 0},
            {"color": "yellow", "value": 0.7},
            {"color": "green", "value": 0.85}
          ]
        }
      },
      {
        "title": "Token Usage",
        "type": "timeseries",
        "targets": [{
          "expr": "rate(agent_llm_tokens_total[5m])",
          "legendFormat": "{{agent_id}} — {{token_type}}"
        }]
      }
    ]
  }
}
```

### 9.4 Alerting Rules

```yaml
# Prometheus alerting rules
groups:
  - name: agent_alerts
    rules:
      - alert: AgentHighErrorRate
        expr: rate(agent_execution_total{status="error"}[5m]) / rate(agent_execution_total[5m]) > 0.05
        for: 5m
        labels:
          severity: warning
          team: ai-agents
        annotations:
          summary: "High error rate for {{ $labels.agent_type }}"
          description: "Agent {{ $labels.agent_id }} error rate is {{ $value | humanizePercentage }}"

      - alert: AgentHighLatency
        expr: histogram_quantile(0.95, rate(agent_execution_duration_seconds_bucket[5m])) > 30
        for: 5m
        labels:
          severity: warning
          team: ai-agents
        annotations:
          summary: "High latency for {{ $labels.agent_type }}"
          description: "P95 latency for {{ $labels.agent_id }} is {{ $value }}s"

      - alert: AgentBudgetExceeded
        expr: daily_llm_cost_dollars > 100
        for: 1m
        labels:
          severity: critical
          team: finance
        annotations:
          summary: "LLM budget exceeded for {{ $labels.project_id }}"
          description: "Daily cost ${{ $value }} exceeds budget"

      - alert: AgentLowTrustScore
        expr: agent_trust_score < 0.7
        for: 15m
        labels:
          severity: warning
          team: governance
        annotations:
          summary: "Low trust score for {{ $labels.agent_id }}"
          description: "Trust score {{ $value }} below threshold"

  - name: campaign_alerts
    rules:
      - alert: CampaignHighCPA
        expr: campaign_spend_total / campaign_conversions_total > 200
        for: 15m
        labels:
          severity: warning
          team: marketing
        annotations:
          summary: "High CPA for {{ $labels.campaign_id }}"
          description: "CPA ${{ $value }} exceeds $200 target"

      - alert: CampaignLowROAS
        expr: campaign_roas < 2.0
        for: 30m
        labels:
          severity: warning
          team: marketing
        annotations:
          summary: "Low ROAS for {{ $labels.campaign_id }}"
          description: "ROAS {{ $value }} below 2.0× target"

      - alert: CampaignSpendSpike
        expr: rate(campaign_spend_total[1h]) > 3 * rate(campaign_spend_total[1h] offset 1d)
        for: 15m
        labels:
          severity: critical
          team: marketing
        annotations:
          summary: "Spend spike for {{ $labels.campaign_id }}"
          description: "Spend 3× higher than yesterday"

  - name: infrastructure_alerts
    rules:
      - alert: PodCrashLooping
        expr: rate(kube_pod_container_status_restarts_total[15m]) > 0
        for: 5m
        labels:
          severity: critical
          team: platform
        annotations:
          summary: "Pod crash looping: {{ $labels.pod }}"
          description: "Pod {{ $labels.pod }} in {{ $labels.namespace }} is crash looping"

      - alert: HighMemoryUsage
        expr: container_memory_usage_bytes / container_spec_memory_limit_bytes > 0.9
        for: 5m
        labels:
          severity: warning
          team: platform
        annotations:
          summary: "High memory usage: {{ $labels.pod }}"
          description: "Memory usage > 90% for {{ $labels.pod }}"
```

### 9.5 Alert Routing

```yaml
# Alertmanager configuration
route:
  receiver: default
  group_by: [alertname, project_id, severity]
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h

  routes:
    - match:
        severity: critical
      receiver: pagerduty-critical
      group_wait: 0s
      repeat_interval: 15m

    - match:
        severity: warning
      receiver: slack-warning
      group_wait: 1m
      repeat_interval: 2h

    - match:
        team: finance
      receiver: slack-finance

    - match:
        team: governance
      receiver: slack-governance

receivers:
  - name: default
    slack_configs:
      - api_url: https://hooks.slack.com/services/xxx
        channel: "#ai-marketing-alerts"

  - name: pagerduty-critical
    pagerduty_configs:
      - service_key: xxx
        severity: critical

  - name: slack-warning
    slack_configs:
      - api_url: https://hooks.slack.com/services/xxx
        channel: "#ai-marketing-warnings"

  - name: slack-finance
    slack_configs:
      - api_url: https://hooks.slack.com/services/xxx
        channel: "#finance-alerts"

  - name: slack-governance
    slack_configs:
      - api_url: https://hooks.slack.com/services/xxx
        channel: "#governance-alerts"
```

### 9.6 Log Aggregation

```yaml
# Fluent Bit configuration
service:
  flush: 5
  log_level: info
  parsers_file: parsers.conf

pipeline:
  inputs:
    - name: kubernetes
      tag: kube.*
      kube_url: https://kubernetes.default.svc:443
      kube_ca_file: /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
      kube_token_file: /var/run/secrets/kubernetes.io/serviceaccount/token

  filters:
    - name: kubernetes
      match: kube.*
      kube_url: https://kubernetes.default.svc:443
      merge_log: true
      keep_log: false
      k8s-logging.parser: on
      k8s-logging.exclude: on

    - name: modify
      match: kube.*
      rename:
        log: message
        kubernetes_pod_name: pod
        kubernetes_namespace_name: namespace
        kubernetes_container_name: container

    - name: grep
      match: kube.*
      regex: message ERROR|CRITICAL|FATAL

  outputs:
    - name: loki
      match: kube.*
      host: loki.monitoring.svc.cluster.local
      port: 3100
      labels:
        job: fluent-bit
        namespace: $namespace
        pod: $pod
        container: $container
```

---

## 10. Revenue Model & Pricing

### 10.1 Four-Tier Pricing

```mermaid
graph LR
    subgraph TIERS["Pricing Tiers"]
        T1[Starter<br/>$499/mo]
        T2[Professional<br/>$1,200/mo]
        T3[Enterprise<br/>$2,500-$5,000/mo]
        T4[Agency White-Label<br/>$2,000/mo + usage]
    end

    subgraph TARGETS["Target Customers"]
        T1 --> SMB[SMBs<br/>Single channel]
        T2 --> MM[Mid-market<br/>Multi-channel]
        T3 --> ENT[Agencies & Enterprises<br/>Unlimited]
        T4 --> AGC[Marketing Agencies<br/>White-label]
    end
```

| Feature | Starter ($499/mo) | Professional ($1,200/mo) | Enterprise ($2,500-$5,000/mo) | Agency White-Label ($2,000/mo + usage) |
|---------|-------------------|--------------------------|------------------------------|----------------------------------------|
| **Channels** | 1 | 3 | Unlimited | Unlimited |
| **Agents** | 5 | 6 | 6 + custom | 6 + custom |
| **Autonomy Level** | L2 | L3 | L4 | L4 |
| **Analytics** | Basic | Full | Full + custom | Full + white-label |
| **Integrations** | 10 | 50 | Unlimited + custom | Unlimited |
| **API Access** | 1,000 calls/mo | 10,000 calls/mo | Unlimited | Unlimited |
| **Support** | Email | Priority | Dedicated CSM | Dedicated + SLA |
| **White-Label** | No | No | No | Yes |
| **Sub-Accounts** | 0 | 5 | Unlimited | Unlimited |
| **Custom Models** | No | No | Yes | Yes |
| **SLA** | 99.5% | 99.9% | 99.95% | 99.95% |
| **Data Residency** | US | US | US/EU/APAC | US/EU/APAC |
| **Onboarding** | Self-serve | Guided | White-glove | White-glove |

### 10.2 Unit Economics

#### 10.2.1 Cost Structure (Per $1 of Revenue)

| Cost Category | % of Revenue | $/mo at $1,200 tier | Notes |
|--------------|-------------|---------------------|-------|
| **LLM API Costs** | 15% | $180 | Claude Sonnet 5, GPT-5.2, optimized routing |
| **Infrastructure** | 8% | $96 | K8s, Kafka, Redis, PostgreSQL, Snowflake |
| **Data & Storage** | 3% | $36 | S3, backups, data transfer |
| **Monitoring** | 2% | $24 | Prometheus, Grafana, Loki, Tempo |
| **Security** | 2% | $24 | Auth, encryption, compliance tooling |
| **Total COGS** | **30%** | **$360** | |
| **Gross Margin** | **70%** | **$840** | Target: 72% blended |

#### 10.2.2 Production Cost Target

| Component | Monthly Cost | Notes |
|-----------|-------------|-------|
| **EKS Cluster** | $300 | 3 nodes, m6i.2xlarge |
| **Aurora PostgreSQL** | $150 | db.r6g.large, Multi-AZ |
| **ElastiCache Redis** | $80 | cache.r6g.large, cluster mode |
| **MSK (Kafka)** | $120 | 3 brokers, kafka.m5.large |
| **Snowflake** | $100 | Medium warehouse, auto-suspend |
| **S3 + Data Transfer** | $50 | Artifacts, backups |
| **Monitoring Stack** | $80 | Prometheus, Grafana, Loki, Tempo |
| **LLM API (baseline)** | $180 | ~$0.60 per agent execution |
| **Miscellaneous** | $50 | DNS, certificates, WAF |
| **Total** | **$1,060/mo** | |

#### 10.2.3 LTV:CAC Analysis

| Metric | Value | Calculation |
|--------|-------|-------------|
| **CAC (Customer Acquisition Cost)** | $500 | Sales + marketing spend per customer |
| **LTV (Lifetime Value)** | $18,000 | $1,200/mo × 15 months avg lifetime |
| **LTV:CAC Ratio** | 36:1 | Excellent (target: >3:1) |
| **Gross Margin** | 72% | Blended across tiers |
| **Payback Period** | 1 month | CAC recovered in first month |
| **Net Revenue Retention** | 120% | Expansion revenue from upgrades |

### 10.3 Revenue Projections

```mermaid
gantt
    title Revenue Projections — 12 Months
    dateFormat  YYYY-MM
    section Starter
    5 clients (Month 3)     :milestone, 2026-12, 0d
    15 clients (Month 6)    :milestone, 2027-03, 0d
    25 clients (Month 12)   :milestone, 2027-09, 0d
    section Professional
    3 clients (Month 3)    :milestone, 2026-12, 0d
    10 clients (Month 6)   :milestone, 2027-03, 0d
    20 clients (Month 12)  :milestone, 2027-09, 0d
    section Enterprise
    1 client (Month 6)     :milestone, 2027-03, 0d
    5 clients (Month 12)   :milestone, 2027-09, 0d
    section Agency
    2 clients (Month 6)    :milestone, 2027-03, 0d
    5 clients (Month 12)   :milestone, 2027-09, 0d
```

| Timeline | Starter | Professional | Enterprise | Agency | Total MRR | Total ARR |
|----------|---------|-------------|------------|--------|-----------|-----------|
| Month 3 | 5 × $499 = $2,495 | 3 × $1,200 = $3,600 | — | — | $6,095 | $73,140 |
| Month 6 | 15 × $499 = $7,485 | 10 × $1,200 = $12,000 | 1 × $3,500 = $3,500 | 2 × $2,000 = $4,000 | $26,985 | $323,820 |
| Month 9 | 20 × $499 = $9,980 | 15 × $1,200 = $18,000 | 3 × $3,500 = $10,500 | 3 × $2,000 = $6,000 | $44,480 | $533,760 |
| Month 12 | 25 × $499 = $12,475 | 20 × $1,200 = $24,000 | 5 × $3,500 = $17,500 | 5 × $2,000 = $10,000 | $63,975 | $767,700 |

### 10.4 Revenue Streams

| Stream | % of Revenue | Description |
|--------|-------------|-------------|
| **Subscription** | 70% | Monthly SaaS fees per tier |
| **Usage-Based** | 20% | Per-decision pricing for API access, overage charges |
| **Professional Services** | 10% | Implementation, training, custom integrations |

### 10.5 Broker Channel

#### 10.5.1 Broker Program Structure

```mermaid
graph TB
    subgraph BROKER["Broker Channel"]
        B1[Tier 1: Referral Partner<br/>10% commission]
        B2[Tier 2: Reseller<br/>20% commission]
        B3[Tier 3: Technology Partner<br/>25% commission]
        B4[Tier 4: Strategic Alliance<br/>30% commission + co-selling]
    end

    subgraph BENEFITS["Broker Benefits"]
        C1[Recurring commission<br/>for customer lifetime]
        C2[Co-marketing<br/>funding]
        C3[Priority<br/>support]
        C4[White-label<br/>options]
        C5[Training &<br/>certification]
    end

    BROKER --> BENEFITS
```

#### 10.5.2 Broker Commission Tiers

| Tier | Commission | Requirements | Benefits |
|------|-----------|-------------|----------|
| **Referral Partner** | 10% | 1+ customer referral | Recurring commission, link tracking |
| **Reseller** | 20% | 5+ active customers, certified | Co-marketing, priority support, training |
| **Technology Partner** | 25% | 10+ active customers, integration | Joint GTM, co-selling, API access |
| **Strategic Alliance** | 30% | 25+ active customers, dedicated team | White-label, custom development, executive sponsorship |

#### 10.5.3 Broker Enablement

| Asset | Description | Format |
|-------|-------------|--------|
| **Sales Deck** | Product overview, pricing, competitive comparison | PowerPoint |
| **Demo Environment** | Pre-configured demo with sample data | Cloud instance |
| **API Documentation** | Complete API reference with examples | OpenAPI + Docs |
| **Training Portal** | Product training, certification courses | LMS |
| **Co-Marketing Kit** | Logos, brand guidelines, case studies | Digital assets |
| **Deal Registration** | Partner portal for deal tracking | Web portal |

### 10.6 Pricing Strategy

#### 10.6.1 Value-Based Pricing Anchors

| Value Metric | Baseline (Manual) | With AI Agents | Value Multiplier |
|--------------|-------------------|----------------|-----------------|
| **CAC** | $200 | $80 (60% reduction) | 2.5× |
| **ROAS** | 2.0× | 9.0× | 4.5× |
| **Creative velocity** | 5 variants/week | 200+ variants/day | 280× |
| **Time to launch** | 3 days | 5 minutes | 864× |
| **Rep time saved** | 0 hrs/mo | 40 hrs/mo | $2,000/mo at $50/hr |

#### 10.6.2 Competitive Pricing Comparison

| Platform | Entry Price | Mid-Tier | Enterprise | Key Limitation |
|----------|-------------|----------|------------|----------------|
| **GoHighLevel** | $97/mo | $297/mo | $499/mo | Rule-based workflows, no autonomous optimization |
| **HubSpot** | $800/mo | $2,000/mo | $5,000+/mo | Human-built journeys, no agentic AI |
| **This Platform** | $499/mo | $1,200/mo | $2,500-$5,000/mo | — |

**Pricing advantage:** 40-60% lower than HubSpot at equivalent capability, with autonomous agentic AI that neither competitor offers.

---

## Appendix A: Glossary

| Term | Definition |
|------|-----------|
| **Agent** | An autonomous AI entity with a defined role, tools, and governance scope |
| **A2A** | Agent-to-Agent protocol for inter-agent task delegation (Linux Foundation) |
| **MCP** | Model Context Protocol for agent-to-tool connectivity (Linux Foundation) |
| **DID** | Decentralized Identifier for agent identity verification |
| **Blast Radius** | Maximum number of customers affected by a single agent action |
| **Laya** | Real-time decision routing engine (<33ms) |
| **Nerve** | Supervision framework for Definition of Done verification |
| **Cognee** | Knowledge graph memory system for cross-session learning |
| **ApexGraphSwarm** | Graph analytics engine for customer journey optimization |
| **GRC_Claw** | Governance, Risk, and Compliance layer for agent policy enforcement |
| **Autonomy Level** | L1 (Advisory) to L4 (Adaptive Optimization) — degree of agent independence |

## Appendix B: Document References

| Document | Path | Purpose |
|----------|------|---------|
| Top 3 Project Specs | `implementations/top-3-specs.md` | Detailed specs for 3 main projects |
| Unified Architecture | `research/unified-architecture.md` | Overall system architecture |
| Technical Architecture | `research/technical-architecture.md` | Technical deep-dive |
| Deployment Infrastructure | `implementations/deployment-infrastructure.md` | K8s, multi-cloud, Helm |
| Monitoring & Observability | `implementations/monitoring-observability.md` | Prometheus, Grafana, tracing |
| Governance Layer | `implementations/governance-layer.md` | GRC_Claw governance |
| Data Layer | `implementations/data-layer.md` | PostgreSQL, Snowflake, Redis |
| Campaign Optimization | `implementations/campaign-optimization.md` | Project 1 details |
| Lead Scoring | `implementations/lead-scoring.md` | Project 2 details |
| Journey Orchestration | `implementations/journey-orchestration-impl.md` | Project 3 details |

---

*Document generated from comprehensive analysis of 119 research and implementation documents (10.3 MB) in ~/GRC_Claw/research/ and ~/GRC_Claw/implementations/.*
