# Architecture

## Gated Communities — System Architecture

---

## Table of Contents

- [System Overview](#system-overview)
- [High-Level Architecture](#high-level-architecture)
- [Data Flow](#data-flow)
- [Module Dependencies](#module-dependencies)
- [Agent Architecture](#agent-architecture)
- [Integration Layer](#integration-layer)
- [Infrastructure](#infrastructure)
- [Security](#security)
- [Scalability](#scalability)

---

## System Overview

Gated Communities is a modular, microservices-inspired platform built as a monolithic FastAPI application. It consolidates 10 independent domain services into a unified system with 57 AI-powered agents.

```mermaid
graph TB
    subgraph "Client Layer"
        Web[Web App<br/>Next.js]
        Mobile[Mobile App]
        Admin[Admin Panel]
        API[API Clients]
    end

    subgraph "API Gateway Layer"
        GW[FastAPI Gateway]
        Auth[Auth Middleware]
        RateLimit[Rate Limiter]
        CORS[CORS Middleware]
    end

    subgraph "Agent Services Layer"
        direction TB
        subgraph "Tier Management"
            TE[Tier Evaluator]
            TA[Tier Analytics]
            TR[Upgrade Recommender]
            BM[Benefit Manager]
            AC[Access Controller]
        end
        subgraph "Moderation Queue"
            AM[Auto Moderator]
            QO[Queue Optimizer]
            HR[Human Review Router]
            PS[Priority Scorer]
            ESC[Escalation]
        end
        subgraph "Access Control"
            PE[Permission Evaluator]
            RM[Role Manager]
            AE[Access Auditor]
            AR[Access Recommender]
            PE2[Policy Enforcer]
        end
        subgraph "Community Health"
            TD[Toxicity Detector]
            EM[Engagement Metrics]
        end
        subgraph "Member Verification"
            IV[Identity Verifier]
            DC[Document Checker]
            FP[Fraud Preventor]
            TS[Trust Scorer]
            EX[Explainer]
        end
        subgraph "Escalation Workflow"
            AR2[Auto Resolver]
            SO[Resolution Optimizer]
            ST[SLA Tracker]
            EA[Escalation Analyzer]
            PR[Priority Router]
        end
        subgraph "Reputation System"
            RS[Reputation Scorer]
            BT[Trust Tier]
            BM2[Badge Manager]
            RH[Reputation History]
            RE[Reputation Explainer]
        end
        subgraph "Compliance Monitor"
            PT[Policy Tracker]
            AR3[Audit Reporter]
            CS[Compliance Scorer]
            VD[Violation Detector]
            REM[Remediation]
        end
        subgraph "Moderation Analytics"
            MP[Moderation Predictor]
            MPerf[Moderator Performance]
            PE3[Policy Effectiveness]
            AE2[Analytics Explainer]
            TA2[Trend Analyzer]
        end
        subgraph "Community Governance"
            DR[Dispute Resolver]
            GA[Governance Analytics]
            RE2[Rule Enforcer]
            PM[Policy Manager]
            GE[Governance Explainer]
        end
    end

    subgraph "Integration Layer"
        LLM[LLM Service<br/>LangChain]
        DB[(PostgreSQL)]
        Cache[(Redis)]
        Notif[Notifications<br/>Slack/Email]
        Ext[External APIs]
        Storage[File Storage]
    end

    subgraph "Infrastructure Layer"
        K8s[Kubernetes]
        CI[CI/CD Pipeline]
        Mon[Monitoring<br/>Prometheus]
        Log[Logging<br/>structlog]
    end

    Web & Mobile & Admin & API --> GW
    GW --> Auth --> RateLimit --> CORS
    CORS --> Agent Services Layer
    Agent Services Layer --> Integration Layer
    Agent Services Layer --> Infrastructure Layer
```

---

## High-Level Architecture

The system follows a layered architecture pattern:

### 1. Client Layer

| Client | Technology | Purpose |
|--------|------------|---------|
| Web App | Next.js 14 + React 18 | Primary user interface |
| Mobile App | React Native | Mobile access |
| Admin Panel | Next.js | Administrative operations |
| API Clients | Any HTTP client | Third-party integrations |

### 2. API Gateway Layer

- **FastAPI** — High-performance async web framework
- **Auth Middleware** — JWT-based authentication
- **Rate Limiter** — Request throttling per client
- **CORS Middleware** — Cross-origin resource sharing

### 3. Agent Services Layer

57 specialized AI agents organized into 10 domain modules. Each agent is a self-contained unit with its own logic, scoring algorithms, and LLM integration.

### 4. Integration Layer

External service integrations providing data persistence, caching, notifications, and LLM capabilities.

### 5. Infrastructure Layer

Kubernetes orchestration, CI/CD pipelines, monitoring, and structured logging.

---

## Data Flow

```mermaid
sequenceDiagram
    participant C as Client
    participant API as API Gateway
    participant Auth as Auth Middleware
    participant Agent as Agent
    participant LLM as LLM Service
    participant DB as Database
    participant Cache as Cache

    C->>API: HTTP Request
    API->>Auth: Validate Token
    Auth-->>API: Authenticated
    API->>API: Rate Limit Check
    API->>Agent: Route to Agent
    Agent->>Cache: Check Cache
    alt Cache Hit
        Cache-->>Agent: Cached Result
    else Cache Miss
        Agent->>LLM: LLM Inference
        LLM-->>Agent: LLM Response
        Agent->>DB: Persist Data
        DB-->>Agent: Stored
        Agent->>Cache: Cache Result
    end
    Agent-->>API: Agent Response
    API-->>C: HTTP Response
```

---

## Module Dependencies

```mermaid
graph LR
    TM[Tier Management] --> AC[Access Control]
    TM --> RS[Reputation System]
    MQ[Moderation Queue] --> EW[Escalation Workflow]
    MQ --> CM[Compliance Monitor]
    CH[Community Health] --> MQ
    MV[Member Verification] --> TM
    MV --> RS
    EW --> CM
    RS --> AC
    MA[Moderation Analytics] --> MQ
    MA --> CM
    CG[Community Governance] --> CM
    CG --> MQ
```

### Dependency Descriptions

| Source | Target | Relationship |
|--------|--------|--------------|
| Tier Management | Access Control | Tier determines access policies |
| Tier Management | Reputation System | Tier affects reputation scoring |
| Moderation Queue | Escalation Workflow | Escalations created from queue items |
| Moderation Queue | Compliance Monitor | Violations tracked for compliance |
| Community Health | Moderation Queue | Health scores trigger moderation |
| Member Verification | Tier Management | Verification unlocks tiers |
| Member Verification | Reputation System | Verification boosts reputation |
| Escalation Workflow | Compliance Monitor | Escalations logged for audit |
| Reputation System | Access Control | Reputation affects access decisions |
| Moderation Analytics | Moderation Queue | Analytics inform queue optimization |
| Moderation Analytics | Compliance Monitor | Analytics track compliance trends |
| Community Governance | Compliance Monitor | Governance policies drive compliance |
| Community Governance | Moderation Queue | Governance rules trigger moderation |

---

## Agent Architecture

Each agent follows a consistent pattern:

```mermaid
classDiagram
    class BaseAgent {
        <<abstract>>
        +initialize() async
        +execute(request) async
        +health_check() async
        -logger: Logger
        -settings: Settings
    }

    class TierEvaluatorAgent {
        +evaluate(member_id, target_tier_id) TierEvaluation
        -score_activity(member_id) float
        -score_contributions(member_id) float
        -score_engagement(member_id) float
    }

    class AccessControllerAgent {
        +execute(request) AccessCheckResponse
        +add_policy(policy) void
        +remove_policy(policy_id) void
        -evaluate_policies(request) AccessDecision
    }

    class ReputationScorerAgent {
        +calculate_score(member_id) float
        -weight_factors() dict
        -apply_decay() void
    }

    BaseAgent <|-- TierEvaluatorAgent
    BaseAgent <|-- AccessControllerAgent
    BaseAgent <|-- ReputationScorerAgent
```

### Agent Lifecycle

```mermaid
stateDiagram-v2
    [*] --> Initialized
    Initialized --> Running: initialize()
    Running --> Processing: execute(request)
    Processing --> Running: return result
    Running --> Error: exception
    Error --> Running: retry / recover
    Running --> Stopped: shutdown()
    Stopped --> [*]
```

---

## Integration Layer

### Database (PostgreSQL)

```mermaid
erDiagram
    TIERS ||--o{ MEMBERS : has
    MEMBERS ||--o{ REPUTATION_HISTORY : tracks
    MEMBERS ||--o{ ACCESS_LOGS : generates
    POLICIES ||--o{ ACCESS_LOGS : governs
    MODERATION_ITEMS ||--o{ ESCALATIONS : escalates_to
    COMPLIANCE_POLICIES ||--o{ VIOLATIONS : detects
    DISPUTES ||--o{ RESOLUTIONS : resolves_to
```

### Cache (Redis)

- Session storage
- Rate limiting counters
- Agent result caching
- Real-time leaderboards

### LLM Integration (LangChain)

```mermaid
graph LR
    Agent[Agent] --> LLMClient[LLM Client]
    LLMClient --> OpenAI[OpenAI API]
    LLMClient --> Cache[Response Cache]
    OpenAI --> LLMClient
    LLMClient --> Agent
```

### Notifications

- **Slack** — Escalation alerts, queue notifications
- **Email** — Review reminders, compliance reports
- **PagerDuty** — Critical escalation alerts
- **Webhooks** — Custom integrations

---

## Infrastructure

### Kubernetes Architecture

```mermaid
graph TB
    subgraph "Kubernetes Namespace: gated-communities"
        subgraph "Deployment: gated-communities"
            P1[Pod 1]
            P2[Pod 2]
            P3[Pod 3]
        end
        subgraph "Services"
            SVC[ClusterIP Service]
        end
        subgraph "Ingress"
            ING[NGINX Ingress]
        end
        subgraph "Autoscaling"
            HPA[Horizontal Pod Autoscaler<br/>2-10 replicas]
        end
        subgraph "Config"
            CM[ConfigMap]
            SEC[Secrets]
        end
        subgraph "Disruption Budget"
            PDB[PodDisruptionBudget<br/>minAvailable: 1]
        end
    end

    ING --> SVC
    SVC --> P1 & P2 & P3
    HPA --> P1 & P2 & P3
    CM --> P1 & P2 & P3
    SEC --> P1 & P2 & P3
```

### CI/CD Pipeline

```mermaid
graph LR
    Push[Git Push] --> Test[Test Job<br/>Lint + Type Check + Pytest]
    Test --> Build[Build Job<br/>Docker Image]
    Build --> Push_Registry[Push to Registry]
    Push_Registry --> Deploy[Deploy Job<br/>Kubernetes Rollout]
```

---

## Security

### Authentication & Authorization

- JWT-based authentication
- Role-based access control (RBAC)
- Policy-based access control (PBAC)
- API key management for external clients

### Data Protection

- Secrets stored in Kubernetes Secrets
- TLS termination at ingress
- CORS configuration
- Rate limiting per client
- Input validation via Pydantic

### Audit Logging

- All access decisions logged
- Compliance audit trail (365-day retention)
- Structured logging with structlog
- Prometheus metrics for monitoring

---

## Scalability

### Horizontal Scaling

- **HPA:** 2-10 replicas based on CPU (70%) and memory (80%)
- **PDB:** Minimum 1 pod available during disruptions
- **Stateless design:** All state in PostgreSQL/Redis

### Performance

- **Async I/O:** Full async/await throughout
- **Connection pooling:** Database pool size 20
- **Caching:** Redis for hot data
- **LLM response caching:** Reduces API calls

### Resource Limits

| Resource | Request | Limit |
|----------|---------|-------|
| CPU | 250m | 500m |
| Memory | 256Mi | 512Mi |
