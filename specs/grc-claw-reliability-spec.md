# GRC_Claw Reliability Specification

**Document ID:** GRC-REL-001  
**Version:** 2.0  
**Status:** Draft  
**Owner:** GRC_Claw Architecture Team  
**Last Updated:** 2026-10-01  
**Parent Documents:** GRC_Claw Roadmap v1.0, Gap Analysis v1.0, Performance Spec v1.0, Third-Party Risk Spec v1.0, CI Framework v1.0

---

## 1. Purpose & Scope

### 1.1 Purpose

This specification defines the reliability requirements, fault tolerance patterns, disaster recovery procedures, SRE practices, reliability engineering patterns, chaos engineering framework, failure mode analysis, reliability testing automation, and reliability monitoring & alerting for GRC_Claw — an open-source GRC platform for agentic AI governance. It establishes measurable availability targets, resilience contracts, and operational procedures that ensure continuous governance operation even under adverse conditions.

GRC_Claw is a **safety-critical governance layer**: if it fails, agentic AI systems may operate without oversight. Reliability is not a nice-to-have — it is a core governance requirement.

### 1.2 Scope

**In scope:**
- All GRC_Claw runtime components — policy engine, enforcement proxy, evidence collection, audit trail, monitoring, analytics, and API gateway
- Infrastructure dependencies — PostgreSQL, Redis, Kafka, object storage, and external identity providers
- Deployment topologies — single-node, high-availability, multi-region, and air-gapped configurations
- Operational procedures — incident response, failover, backup/restore, and disaster recovery
- SRE practices — SLOs, SLIs, error budgets, toil reduction, and operational excellence
- Reliability engineering patterns — circuit breakers, bulkheads, fallbacks, rate limiting, backpressure, and leader election
- Chaos engineering — controlled failure injection, GameDays, and resilience validation
- Failure mode analysis — FMEA, fault tree analysis, and failure taxonomy
- Reliability testing automation — CI/CD-integrated failure injection, reliability gates, and automated validation
- Reliability monitoring & alerting — four golden signals, SLO-based alerting, and observability

**Out of scope:**
- Build-time reliability (covered by CI/CD pipeline specification)
- End-user device reliability
- Third-party AI system reliability (covered by Third-Party Risk Spec GRC-TPR-001)

### 1.3 Design Principles

| Principle | Rationale |
|-----------|-----------|
| **Governance continuity** | A governance system that fails is worse than no system — it creates a false sense of compliance. GRC_Claw must fail safely, not silently. |
| **Fail-closed by default** | When the enforcement proxy cannot evaluate a policy, it must deny the action (not allow it). Availability of the governed system is secondary to governance integrity. |
| **Graceful degradation** | Under partial failure, GRC_Claw prioritizes enforcement decisions over non-critical features (analytics, dashboards, reporting). |
| **Observability-first** | Every component exposes health metrics, structured logs, and distributed traces. You cannot ensure reliability you cannot measure. |
| **Automated recovery** | Human-paced recovery is too slow for a governance layer. Failover, restart, and self-healing must be automated wherever possible. |
| **SLO-driven operations** | Reliability is measured against explicit SLOs with error budgets that balance feature velocity against stability. |
| **Continuous validation** | Reliability is not a one-time achievement — it is continuously validated through chaos engineering, soak tests, and DR drills. |

---

## 2. SRE Practices — SLOs, SLIs, and Error Budgets

### 2.1 Service Level Objectives (SLOs)

| Component | SLO | Downtime Budget/Month | Priority |
|-----------|-----|----------------------|----------|
| **Enforcement Proxy** | 99.95% | 21.9 min | Critical — agent actions blocked without it |
| **Policy Engine** | 99.9% | 43.8 min | Critical — no policy updates or evaluation |
| **Audit Trail** | 99.99% | 4.38 min | Critical — compliance evidence must be immutable and available |
| **Evidence Collection** | 99.5% | 3.6 hours | High — delayed evidence is acceptable; lost evidence is not |
| **API Gateway** | 99.9% | 43.8 min | High — management plane access |
| **Monitoring & Alerting** | 99.5% | 3.6 hours | Medium — operational visibility |
| **Analytics & Dashboards** | 99.0% | 7.2 hours | Low — non-blocking; degraded mode acceptable |
| **Compliance Reporting** | 99.0% | 7.2 hours | Low — batch-oriented; delayed reports acceptable |

### 2.2 Composite Platform Availability

The **end-to-end governance availability** — the probability that an agent action can be evaluated and audited at any given moment — is:

```
P(governance available) = P(enforcement proxy) × P(policy engine) × P(audit trail)
                        = 0.9995 × 0.999 × 0.9999
                        = 0.99840  (99.84%)
```

**Target: ≥ 99.8% composite availability** for the critical governance path.

### 2.3 Service Level Indicators (SLIs)

SLIs are the quantitative measurements that feed into SLOs. Each SLI must be measurable, aggregatable, and attributable to a specific component.

#### 2.3.1 Availability SLI

```
SLI_availability = (valid responses) / (total valid requests)
```

- **Valid request:** A request that reaches the component and expects a response (excludes malformed requests and health checks)
- **Valid response:** A response with status code 2xx or 3xx (excludes 4xx client errors, 5xx server errors, and timeouts)
- **Measurement window:** Rolling 30 days
- **Granularity:** Per-component and per-endpoint

#### 2.3.2 Latency SLI

```
SLI_latency = (requests completing within latency threshold) / (total requests)
```

| Component | Latency Threshold | Measurement Point |
|-----------|-------------------|-------------------|
| Enforcement Proxy | p99 < 10 ms | Enforcement proxy internal timer |
| Policy Engine | p99 < 50 ms | Policy evaluation timer |
| Audit Trail Write | p99 < 20 ms | Audit trail internal timer |
| Evidence Collection | p99 < 200 ms | Evidence collector internal timer |
| API Gateway | p99 < 500 ms | API gateway internal timer |

#### 2.3.3 Durability SLI

```
SLI_durability = (audit entries successfully written and verified) / (audit entries attempted)
```

- **Target:** 100% (zero tolerance for audit entry loss)
- **Verification:** Hash chain verification after write
- **Measurement:** Continuous, per-write

#### 2.3.4 Correctness SLI

```
SLI_correctness = (enforcement decisions matching expected policy outcome) / (total enforcement decisions)
```

- **Target:** 100% (zero tolerance for incorrect enforcement decisions)
- **Measurement:** Shadow evaluation against reference policy engine
- **Sampling:** 1% of all decisions, continuously

### 2.4 Error Budget Methodology

#### 2.4.1 Error Budget Calculation

```
Error Budget = 1 - SLO
Monthly Error Budget (minutes) = (1 - SLO) × 30 days × 24 hours × 60 minutes
```

| SLO | Error Budget | Monthly Budget (min) | Daily Budget (min) |
|-----|-------------|---------------------|-------------------|
| 99.0% | 1.0% | 432 | 14.4 |
| 99.5% | 0.5% | 216 | 7.2 |
| 99.9% | 0.1% | 43.2 | 1.44 |
| 99.95% | 0.05% | 21.6 | 0.72 |
| 99.99% | 0.01% | 4.32 | 0.144 |

#### 2.4.2 Error Budget Burn Rate

```
Burn Rate = (actual error ratio) / (error budget ratio)
```

| Burn Rate | Interpretation | Action |
|-----------|---------------|--------|
| < 1.0 | Budget consuming slower than planned | Normal operations |
| 1.0 | Budget consuming at planned rate | Monitor closely |
| 1.0 – 2.0 | Budget consuming faster than planned | Investigate; reliability review |
| 2.0 – 10.0 | Budget will deplete in < 30 days | Freeze non-critical features |
| > 10.0 | Budget will deplete in < 3 days | All hands on reliability; incident response |

#### 2.4.3 Error Budget Policy

When error budget is depleted or burning too fast:

| Budget Status | Policy | Approval |
|---------------|--------|----------|
| **> 50% remaining** | Normal feature development | None required |
| **20–50% remaining** | Reliability review required for new features | Engineering Lead |
| **5–20% remaining** | Freeze non-critical features; reliability sprint | SRE Lead + Product |
| **< 5% remaining** | Freeze all features; all hands on reliability | CTO |
| **0% (depleted)** | Reliability sprint until budget recovers; no new features | CTO + Risk Committee |

#### 2.4.4 Error Budget Exceptions

- **Planned maintenance:** Does not count against budget if active-active mode is operational
- **Emergency maintenance:** Does not count; documented post-hoc
- **Third-party outage:** Counts against budget unless SLA with compensation is in place
- **Force majeure:** Risk Committee may grant exception with documented justification

### 2.5 Availability Tier Definitions

| Tier | Availability | Max Downtime/Year | Use Case |
|------|-------------|-------------------|----------|
| **Tier 1 — Critical** | 99.99% | 52.6 min | Financial services, healthcare, safety-critical agentic AI |
| **Tier 2 — Standard** | 99.9% | 8.76 hours | Enterprise production deployments |
| **Tier 3 — Basic** | 99.5% | 3.65 days | Development, staging, non-critical workloads |
| **Tier 4 — Best Effort** | 99.0% | 36.5 days | Community/self-hosted, no SLA |

### 2.6 Maintenance Windows

- **Planned maintenance** is permitted during a 4-hour window (Saturday 02:00–06:00 UTC), with 72-hour advance notice.
- Planned maintenance counts against the downtime budget unless the platform operates in active-active mode.
- Emergency maintenance (security patches, critical bug fixes) does not count against the SLO but must be documented post-hoc.

### 2.7 Toil Reduction

Toil is the repetitive, manual, automatable operational work that scales with system growth. GRC_Claw actively reduces toil:

| Toil Category | Example | Automation Target |
|---------------|---------|-------------------|
| **Incident response** | Manual failover, restart scripts | 100% automated |
| **Capacity management** | Manual scaling decisions | 100% automated (HPA/VPA) |
| **Backup verification** | Manual restore tests | 100% automated |
| **Certificate renewal** | Manual cert rotation | 100% automated (cert-manager) |
| **Runbook execution** | Manual DR procedures | 90% automated; 10% human decision |
| **Alert triage** | Manual alert investigation | 80% automated; 20% human analysis |

**Toil budget:** Maximum 50% of SRE time spent on toil. Excess toil triggers automation sprint.

---

## 3. Reliability Engineering Patterns

### 3.1 Circuit Breaker Pattern

Circuit breakers prevent cascading failures when a dependency is unhealthy. GRC_Claw implements circuit breakers on all external calls.

#### 3.1.1 Circuit Breaker States

```
┌──────────┐   failure threshold   ┌──────────┐   timeout   ┌──────────┐
│  CLOSED  │──────────────────────▶│   OPEN   │────────────▶│  HALF-   │
│ (normal) │                       │ (failing)│             │  OPEN    │
│          │◀──────────────────────│          │◀────────────│ (testing)│
└──────────┘   success threshold   └──────────┘   success    └──────────┘
```

#### 3.1.2 Circuit Breaker Configuration

| Dependency | Failure Threshold | Timeout | Half-Open Probes | Fallback Behavior |
|------------|-------------------|---------|-------------------|-------------------|
| PostgreSQL | 5 failures in 10s | 2s | 3 | Use cached policies; queue audit writes |
| Redis | 3 failures in 5s | 1s | 2 | In-memory cache; skip rate limiting |
| Kafka | 5 failures in 10s | 2s | 3 | Local disk spool; replay on recovery |
| Object Storage (S3) | 3 failures in 10s | 5s | 2 | Local disk buffer; alert operator |
| Identity Provider (OIDC) | 3 failures in 5s | 1s | 2 | Cached agent identities; fail-closed for new agents |
| External Compliance API | 5 failures in 30s | 5s | 3 | Use last-known-good compliance mapping |

#### 3.1.3 Enforcement Proxy Circuit Breaker

The enforcement proxy has a **special circuit breaker** — the governance circuit breaker:

| State | Behavior | Agent Impact |
|-------|----------|-------------|
| **CLOSED** | Normal policy evaluation | None — full governance |
| **OPEN (fail-closed)** | All actions denied; agent receives explicit denial with reason | Agent cannot take any action until governance recovers |
| **OPEN (fail-open)** | All actions allowed; audit trail records "governance bypass" | Agent operates without oversight; requires post-hoc review |
| **HALF-OPEN** | Limited policy evaluation (cached rules only) | Reduced governance; only cached policies enforced |

**Default: fail-closed.** Fail-open requires explicit per-policy configuration and generates a P1 alert.

### 3.2 Retry Pattern

All transient failures are retried with exponential backoff and jitter.

#### 3.2.1 Retry Configuration

| Operation | Max Retries | Base Delay | Max Delay | Jitter | Retryable Errors |
|-----------|-------------|------------|-----------|--------|-----------------|
| PostgreSQL write | 3 | 100ms | 2s | Full | Connection timeout, deadlock, serialization failure |
| Redis operation | 3 | 50ms | 1s | Full | Connection timeout, MOVED/ASK redirect |
| Kafka produce | 5 | 200ms | 5s | Full | NotLeaderForPartition, TimeoutException |
| Object storage write | 3 | 500ms | 10s | Full | 503 SlowDown, 500 InternalError |
| OIDC token validation | 2 | 100ms | 1s | Full | 503, timeout |
| Evidence cross-validation | 2 | 1s | 5s | None | 503, timeout |

#### 3.2.2 Retry Budget

To prevent retry storms, each component enforces a **retry budget**:

- Maximum 10 retries per second per component
- Maximum 100 retries per minute per component
- When budget is exhausted, circuit breaker opens immediately

#### 3.2.3 Idempotency

All retried operations must be idempotent. GRC_Claw uses:
- **Client-generated request IDs** (UUID v4) for all mutations
- **Idempotency keys** on all write operations
- **Deduplication** at the storage layer (PostgreSQL `ON CONFLICT DO NOTHING`, Kafka idempotent producer)

### 3.3 Fallback Pattern

When a dependency is unavailable, GRC_Claw degrades to a predefined fallback.

#### 3.3.1 Fallback Hierarchy

```
Full Service ──▶ Degraded Mode ──▶ Minimal Mode ──▶ Fail-Closed
   (all features)  (enforcement only)  (deny all)    (refuse connections)
```

#### 3.3.2 Fallback Strategies by Component

| Component | Fallback Strategy | Data Freshness | Governance Impact |
|-----------|-------------------|----------------|-------------------|
| **Policy Engine** | Serve last-known-good compiled rules from local cache | Stale by seconds | Minimal — policies rarely change |
| **Agent Identity** | Serve cached agent identities from Redis or local cache | Stale by minutes | Low — agent identities are stable |
| **Audit Trail** | Write to local disk spool; replay to Kafka on recovery | Delayed | None — audit integrity preserved |
| **Evidence Collection** | Buffer in memory; spill to disk if queue full | Delayed | None — evidence not lost |
| **Compliance Mapping** | Use last-known-good mapping from cache | Stale by hours | Low — mappings change infrequently |
| **Analytics** | Disable; serve stale dashboard data | Stale | None — non-critical path |
| **OIDC/SSO** | Use cached JWTs; fail-closed for new authentications | Stale by token TTL | Medium — new agents cannot authenticate |

#### 3.3.3 Cache Warming

To ensure fallbacks are effective, GRC_Claw implements **cache warming**:

- On startup, the enforcement proxy loads all active policies and compiled rules into memory
- Agent identities are pre-loaded for all registered agents
- Compliance mappings are loaded into local cache
- Cache is refreshed every 60 seconds (configurable) or on policy change events

### 3.4 Bulkhead Pattern

GRC_Claw isolates failure domains using bulkheads:

| Bulkhead | Isolation Mechanism | Resource Limit |
|----------|---------------------|----------------|
| **Enforcement proxy** | Dedicated thread pool per agent | Max 100 concurrent decisions per agent |
| **Audit trail** | Separate Kafka topic per tenant | Max 15,000 entries/sec per tenant |
| **Evidence collection** | Separate consumer group per evidence type | Max 5,000 items/sec per type |
| **API** | Rate limiting per API key | Max 1,000 req/min per key |
| **Database** | Connection pool per component | Max 50 connections per component |

### 3.5 Timeout Pattern

All external calls have strict timeouts to prevent cascading latency:

| Call Type | Connect Timeout | Read Timeout | Total Timeout |
|-----------|----------------|--------------|---------------|
| PostgreSQL | 2s | 5s | 10s |
| Redis | 1s | 2s | 5s |
| Kafka | 2s | 5s | 10s |
| Object Storage | 3s | 10s | 30s |
| OIDC | 2s | 3s | 5s |
| External API | 3s | 10s | 15s |

### 3.6 Rate Limiting Pattern

Rate limiting protects GRC_Claw from being overwhelmed by excessive requests.

#### 3.6.1 Rate Limiting Strategy

| Scope | Algorithm | Limit | Burst |
|-------|-----------|-------|-------|
| Per API key | Token bucket | 1,000 req/min | 100 |
| Per agent | Token bucket | 100 req/sec | 20 |
| Per tenant | Token bucket | 10,000 req/min | 500 |
| Per IP (unauthenticated) | Sliding window | 100 req/min | 10 |
| Global enforcement | Token bucket | 50,000 req/sec | 5,000 |

#### 3.6.2 Rate Limit Response

When rate limit is exceeded:
- HTTP 429 (Too Many Requests) returned to client
- `Retry-After` header indicates when to retry
- Rate limit events logged and counted in reliability metrics
- Sustained rate limit violations trigger alert

### 3.7 Backpressure Pattern

Backpressure propagates load upstream when downstream components are saturated.

#### 3.7.1 Backpressure Mechanisms

| Component | Signal | Response |
|-----------|--------|----------|
| Enforcement proxy | Queue depth > 1,000 | Reject new requests with 503; shed load |
| Audit trail | Kafka consumer lag > 10,000 | Pause consumption; spool to disk |
| Evidence collector | Buffer > 80% capacity | Pause ingestion; alert operator |
| API gateway | Active connections > 1,000 | Reject new connections; return 503 |
| PostgreSQL | Connection pool > 80% | Queue requests; timeout after 10s |

#### 3.7.2 Load Shedding Priority

When backpressure is insufficient, GRC_Claw sheds load in priority order:

1. **Tier 1:** Enforcement decisions (never shed)
2. **Tier 2:** Audit trail writes (spool to disk)
3. **Tier 3:** Evidence collection (queue in Kafka)
4. **Tier 4:** API requests (rate limit; return 503)
5. **Tier 5:** Analytics and dashboards (disable; serve stale data)
6. **Tier 6:** Compliance reporting (defer to off-peak)

### 3.8 Leader Election Pattern

For components that require a single active instance (e.g., policy compiler, backup coordinator):

| Component | Election Mechanism | Failover Time | Split-Brain Prevention |
|-----------|-------------------|---------------|----------------------|
| Policy compiler | etcd/consul leader election | < 5 seconds | Fencing token; lease-based locks |
| Backup coordinator | Kubernetes Lease API | < 10 seconds | Resource lock; TTL-based |
| Certificate rotator | Distributed lock (Redis Redlock) | < 15 seconds | Quorum-based; TTL enforcement |
| Schema migrator | PostgreSQL advisory lock | < 5 seconds | Advisory lock; single-writer |

**Split-brain prevention:** All leader-elected operations use fencing tokens. A leader that loses its lease cannot perform writes — the token is invalidated on new leader election.

### 3.9 Pattern Selection Guide

| Failure Scenario | Primary Pattern | Secondary Pattern |
|-----------------|-----------------|-------------------|
| Dependency slow | Timeout | Circuit breaker |
| Dependency down | Circuit breaker | Fallback |
| Traffic spike | Rate limiting | Load shedding |
| Resource exhaustion | Bulkhead | Backpressure |
| Cascading failure | Circuit breaker | Bulkhead |
| Partial degradation | Fallback | Graceful degradation |
| Split-brain | Leader election | Fencing token |
| Retry storm | Retry budget | Circuit breaker |

### 3.10 Anti-Patterns to Avoid

| Anti-Pattern | Why It's Harmful | GRC_Claw Approach |
|-------------|-----------------|-------------------|
| **Retry without backoff** | Amplifies load on failing dependency | Exponential backoff with jitter |
| **Infinite retries** | Hides failures; wastes resources | Max retries with circuit breaker |
| **Shared thread pool** | One slow dependency blocks all | Bulkhead isolation |
| **Silent failures** | Undetected degradation | Explicit fallback with alerting |
| **Tight coupling** | Cascading failures | Circuit breaker + bulkhead |
| **Manual failover** | Too slow; human error | Automated failover with health checks |
| **Missing timeouts** | Cascading latency | Strict timeouts on all calls |

---

## 4. High Availability Architecture

### 4.1 Deployment Topologies

#### 4.1.1 Single-Node (Tier 3–4)

```
┌─────────────────────────────────┐
│         Single Node             │
│  ┌───────────┐  ┌───────────┐  │
│  │ Enforcement│  │  Policy   │  │
│  │  Proxy     │  │  Engine   │  │
│  └───────────┘  └───────────┘  │
│  ┌───────────┐  ┌───────────┐  │
│  │  Audit    │  │  Evidence │  │
│  │  Trail    │  │ Collector │  │
│  └───────────┘  └───────────┘  │
│  ┌───────────────────────────┐ │
│  │  PostgreSQL + Redis       │ │
│  │  (embedded or local)       │ │
│  └───────────────────────────┘ │
└─────────────────────────────────┘
```

- **Availability:** 99.5% (single point of failure)
- **Use case:** Development, staging, small deployments
- **RPO:** 1 hour (hourly backups)
- **RTO:** 1 hour

#### 4.1.2 High-Availability (Tier 2)

```
                    ┌──────────────┐
                    │  Load Balancer│
                    └──────┬───────┘
                           │
            ┌──────────────┼──────────────┐
            │              │              │
     ┌──────▼──────┐ ┌────▼─────┐ ┌─────▼─────┐
     │ Enforcement │ │Enforcement│ │Enforcement│
     │ Proxy 1     │ │Proxy 2    │ │Proxy 3    │
     └──────┬──────┘ └────┬─────┘ └─────┬─────┘
            │              │              │
            └──────────────┼──────────────┘
                           │
              ┌────────────▼────────────┐
              │    Redis Cluster        │
              │  (3 masters + 3 replicas)│
              └────────────┬────────────┘
                           │
              ┌────────────▼────────────┐
              │  PostgreSQL Cluster     │
              │  (1 primary + 2 replicas)│
              └────────────┬────────────┘
                           │
              ┌────────────▼────────────┐
              │  Kafka Cluster          │
              │  (3 brokers, RF=3)      │
              └────────────┬────────────┘
                           │
              ┌────────────▼────────────┐
              │  Object Storage         │
              │  (S3-compatible,        │
              │   cross-region replica) │
              └─────────────────────────┘
```

- **Availability:** 99.9%
- **Use case:** Production enterprise deployments
- **RPO:** 5 minutes (synchronous replication for audit trail)
- **RTO:** 15 minutes

#### 4.1.3 Multi-Region Active-Active (Tier 1)

```
    Region A (Primary)              Region B (Secondary)
┌─────────────────────┐          ┌─────────────────────┐
│  ┌───────────────┐  │          │  ┌───────────────┐  │
│  │  Load Balancer│  │          │  │  Load Balancer│  │
│  └───────┬───────┘  │          │  └───────┬───────┘  │
│          │          │          │          │          │
│  ┌───────▼───────┐  │          │  ┌───────▼───────┐  │
│  │ Enforcement   │  │          │  │ Enforcement   │  │
│  │ Proxies       │  │          │  │ Proxies       │  │
│  └───────┬───────┘  │          │  └───────┬───────┘  │
│          │          │          │          │          │
│  ┌───────▼───────┐  │  Global  │  ┌───────▼───────┐  │
│  │ Redis Cluster │◀─┼─Cluster──▶│  │ Redis Cluster │  │
│  └───────┬───────┘  │  (CRDT)  │  └───────┬───────┘  │
│          │          │          │          │          │
│  ┌───────▼───────┐  │          │  ┌───────▼───────┐  │
│  │ PostgreSQL    │◀─┼─Sync────▶│  │ PostgreSQL    │  │
│  │ (Primary)     │  │  Repl.   │  │ (Replica)     │  │
│  └───────┬───────┘  │          │  └───────┬───────┘  │
│          │          │          │          │          │
│  ┌───────▼───────┐  │          │  ┌───────▼───────┐  │
│  │ Kafka Cluster │◀─┼─Mirror──▶│  │ Kafka Cluster │  │
│  └───────────────┘  │  Maker   │  └───────────────┘  │
└─────────────────────┘          └─────────────────────┘
```

- **Availability:** 99.99%
- **Use case:** Financial services, healthcare, safety-critical agentic AI
- **RPO:** Near-zero (synchronous cross-region replication for audit trail)
- **RTO:** 5 minutes (automated failover)

### 4.2 Stateless Component Design

All GRC_Claw components are **stateless** wherever possible:

- Enforcement proxies hold compiled rules in local cache but source of truth is the policy engine
- API gateway is stateless; session state is in Redis
- Evidence collectors are stateless; Kafka maintains consumer offsets
- Policy engine is stateless; policies are in PostgreSQL

**Stateful components** (PostgreSQL, Redis, Kafka) use clustering and replication for availability.

### 4.3 Health Checks

Every component exposes three health check endpoints:

| Endpoint | Purpose | Check |
|----------|---------|-------|
| `/health/live` | Liveness — is the process running? | Process is up and event loop is not blocked |
| `/health/ready` | Readiness — can it serve traffic? | All dependencies reachable; cache warmed |
| `/health/startup` | Startup — has it initialized? | Configuration loaded; schema migrated |

**Kubernetes integration:** Liveness probes restart the container; readiness probes remove the pod from the load balancer.

---

## 5. Disaster Recovery

### 5.1 Recovery Objectives

| Tier | RPO (Data Loss) | RTO (Service Restoration) | Backup Frequency |
|------|-----------------|---------------------------|-----------------|
| **Tier 1 — Critical** | Near-zero (sync replication) | 5 minutes | Continuous (WAL archiving) |
| **Tier 2 — Standard** | 5 minutes | 15 minutes | Every 15 minutes (incremental) |
| **Tier 3 — Basic** | 1 hour | 1 hour | Hourly |
| **Tier 4 — Best Effort** | 24 hours | 24 hours | Daily |

### 5.2 Backup Strategy

#### 5.2.1 Backup Components

| Data | Backup Method | Frequency | Retention | Storage |
|------|---------------|-----------|-----------|---------|
| **PostgreSQL (policies, audit trail)** | WAL archiving + pg_basebackup | Continuous WAL + daily full | 35 days | Cross-region S3 |
| **Redis (cache, sessions)** | RDB snapshots | Every 15 minutes | 7 days | Local + S3 |
| **Kafka (audit events, evidence)** | MirrorMaker 2 to DR region | Continuous | 7 days (compacted) | DR region Kafka |
| **Object Storage (evidence artifacts)** | Cross-region replication | Continuous | Per retention policy | Cross-region S3 |
| **Configuration (policies, agent registry)** | GitOps — infrastructure as code | On change | Indefinite | Git repository |

#### 5.2.2 Backup Verification

- **Automated restore test:** Weekly — restore backup to isolated environment and verify data integrity
- **Checksum verification:** Daily — verify SHA-256 checksums of all backup files
- **Recovery drill:** Monthly — full disaster recovery drill with documented runbook

### 5.3 Disaster Recovery Procedures

#### 5.3.1 Scenario 1: Single Component Failure

**Detection:** Health check failure or alert threshold breach  
**Response:** Automated (no human intervention required)

```
1. Load balancer detects unhealthy instance (health check fails)
2. Traffic routed to healthy instances (within 5 seconds)
3. Kubernetes/Docker restarts failed container (within 30 seconds)
4. Container warms cache from policy engine (within 10 seconds)
5. Container rejoins load balancer (within 45 seconds total)
```

**Escalation:** If automated recovery fails within 5 minutes, page on-call engineer.

#### 5.3.2 Scenario 2: Database Failure

**Detection:** PostgreSQL primary unreachable or replication lag > 30 seconds  
**Response:** Automated failover

```
1. Patroni/etcd detects primary failure (within 10 seconds)
2. Replica promoted to primary (within 30 seconds)
3. Connection pooler (PgBouncer) updates routing (within 5 seconds)
4. Enforcement proxies reconnect using cached credentials (within 10 seconds)
5. Total downtime: < 60 seconds
```

**Data loss:** Zero (synchronous replication for audit trail); < 5 seconds (asynchronous for policies).

#### 5.3.3 Scenario 3: Complete Region Failure

**Detection:** All health checks in region failing; global load balancer detects region unreachable  
**Response:** Automated cross-region failover

```
1. Global load balancer marks region as unhealthy (within 30 seconds)
2. DNS failover to DR region (within 60 seconds, TTL-dependent)
3. DR region PostgreSQL replica promoted (within 30 seconds)
4. DR region enforcement proxies activate (within 15 seconds)
5. Total RTO: < 5 minutes
```

**Data loss:** Near-zero for audit trail (synchronous cross-region replication); < 5 minutes for policies and evidence.

#### 5.3.4 Scenario 4: Data Corruption

**Detection:** Audit trail hash chain verification failure or data integrity check alert  
**Response:** Manual intervention required

```
1. Halt all write operations to affected data store
2. Identify corruption scope (which records, which time range)
3. Restore from last known good backup (before corruption)
4. Replay WAL logs up to corruption point
5. Verify hash chain integrity
6. Resume operations
7. Post-incident review within 24 hours
```

**RPO:** Time of last verified good backup  
**RTO:** 1–4 hours (depending on backup size and replay time)

#### 5.3.5 Scenario 5: Ransomware / Security Breach

**Detection:** Anomalous encryption activity, unauthorized access alerts, or security team notification  
**Response:** Incident response plan activation

```
1. Isolate affected systems (revoke network access)
2. Activate incident response team
3. Assess scope of compromise
4. Restore from clean backups (verified uncompromised)
5. Rotate all credentials, certificates, and API keys
6. Forensic analysis of attack vector
7. Resume operations with enhanced monitoring
8. Regulatory notification if PII/compliance data affected (72-hour GDPR deadline)
```

### 5.4 Disaster Recovery Runbook

A detailed, step-by-step runbook is maintained at `docs/runbooks/disaster-recovery.md` and includes:

- Contact information for on-call engineers and escalation paths
- Exact commands for each recovery procedure
- Verification steps to confirm successful recovery
- Rollback procedures if recovery fails
- Communication templates for stakeholder notification

### 5.5 Disaster Recovery Testing

| Test Type | Frequency | Scope | Success Criteria |
|-----------|-----------|-------|-----------------|
| **Backup restore** | Weekly | Single component | Data verified intact; checksums match |
| **Failover test** | Monthly | Single region | RTO < 15 min; RPO < 5 min |
| **Full DR drill** | Quarterly | Cross-region | RTO < 5 min; RPO near-zero |
| **Chaos engineering** | Monthly | Random component kill | Automated recovery; no data loss |
| **Tabletop exercise** | Annually | Full team | Runbook accuracy; decision-making validation |

---

## 6. Reliability Testing Methodology

### 6.1 Testing Pyramid

```
                    ┌─────────┐
                    │  Chaos  │  Monthly
                    │Engineering│
                   ┌┴─────────┴┐
                  │  DR Drills │  Quarterly
                 ┌┴─────────────┴┐
                │  Soak Tests   │  Weekly
               ┌┴───────────────┴┐
              │  Failure Tests  │  Per release
             ┌┴─────────────────┴┐
            │  Integration Tests │  Per PR
           ┌┴─────────────────────┴┐
          │    Unit Tests (fault)   │  Per PR
         ┌┴───────────────────────────┴┐
        │  Reliability Gates (CI/CD)    │  Per PR
       ┌┴───────────────────────────────┴┐
      │  Static Analysis & Linting       │  Per PR
     ┌┴───────────────────────────────────┴┐
    │  Architecture Review (Reliability)    │  Per design
    └───────────────────────────────────────┘
```

### 6.2 Unit-Level Fault Injection

Every component includes unit tests that simulate failures:

| Test | What It Validates |
|------|-------------------|
| `test_circuit_breaker_opens_on_failure` | Circuit breaker transitions to OPEN after threshold |
| `test_circuit_breaker_half_open_recovery` | Circuit breaker transitions to HALF-OPEN then CLOSED |
| `test_retry_with_backoff` | Retries use exponential backoff with jitter |
| `test_retry_budget_exhaustion` | Retry budget prevents retry storms |
| `test_fallback_on_dependency_failure` | Fallback strategy activates when dependency is down |
| `test_fail_closed_on_enforcement_failure` | Enforcement proxy denies actions when policy engine is unreachable |
| `test_audit_spool_on_kafka_failure` | Audit writes spool to local disk when Kafka is down |
| `test_cache_warming_on_startup` | Cache is populated from policy engine on startup |
| `test_rate_limiting_enforcement` | Rate limiter rejects requests exceeding threshold |
| `test_backpressure_propagation` | Backpressure signal propagates upstream |
| `test_bulkhead_isolation` | Bulkhead prevents cross-component cascading |
| `test_timeout_enforcement` | Timeouts fire and release resources |
| `test_leader_election_failover` | Leader election completes within SLA |
| `test_split_brain_prevention` | Fencing token prevents dual-write |

### 6.3 Integration Failure Tests

Run in CI on every PR merge:

| Test | Scenario | Expected Behavior |
|------|----------|-------------------|
| **Database failure during enforcement** | Kill PostgreSQL mid-transaction | Circuit breaker opens; fail-closed; zero data loss |
| **Redis flush during active enforcement** | Flush all Redis data | Enforcement continues using in-memory cache; identities served from local cache |
| **Kafka broker termination** | Kill one Kafka broker | Producer retries; consumer rebalances; zero message loss |
| **OIDC provider outage** | Block OIDC endpoint | Cached JWTs used; new agent authentication fails-closed |
| **Policy engine restart** | Kill policy engine during load | Enforcement proxies use cached rules; queue policy updates; resume on recovery |
| **Network partition** | Isolate enforcement proxy from policy engine | Fail-closed; agent actions denied; alert generated |
| **Disk full** | Fill disk on evidence collector | Spool to alternate location; alert operator; no evidence loss |
| **Clock skew** | Set system clock forward 5 minutes | Audit trail timestamps use logical clock; alert on clock skew |
| **Rate limit burst** | Send 10x rate limit in 1 second | Requests rejected with 429; Retry-After header set |
| **Connection pool exhaustion** | Exhaust PostgreSQL connection pool | Requests queued; timeout after 10s; no crash |
| **Memory pressure** | Inject 90% memory usage | OOM killer targets non-critical components; enforcement survives |
| **Certificate expiry** | Expire TLS certificate mid-connection | Connection rejected; alert fires; auto-renewal triggered |

### 6.4 Chaos Engineering Framework

#### 6.4.1 Chaos Engineering Principles

GRC_Claw follows the principles of chaos engineering as defined by the Principles of Chaos Engineering:

1. **Build a hypothesis around steady-state behavior** — Define measurable steady-state metrics (e.g., p99 latency < 10 ms, error rate < 0.1%) before injecting failure.
2. **Vary real-world events** — Inject failures that occur in production: process kills, network latency, disk full, DNS failure, certificate expiry.
3. **Run experiments in production** — Staging is a starting point, but production experiments reveal real failure modes.
4. **Automate experiments to run continuously** — Manual chaos experiments are insufficient; automate and schedule.
5. **Minimize blast radius** — Start with small, controlled experiments; expand gradually.

#### 6.4.2 Chaos Experiment Design

Every chaos experiment follows this structure:

```
Experiment: [Name]
├── Hypothesis: If [failure injected], then [steady-state metric] remains within [threshold]
├── Steady-State Definition: [Metric] = [Value] ± [Tolerance]
├── Blast Radius: [Scope of impact]
├── Failure Injection: [What to inject]
├── Abort Condition: [When to stop automatically]
├── Expected Recovery: [How system should recover]
├── Success Criteria: [Measurable outcome]
└── Rollback Procedure: [How to undo]
```

#### 6.4.3 Chaos Experiment Taxonomy

| Category | Experiment | Hypothesis | Blast Radius | Automated Stop |
|----------|-----------|------------|--------------|----------------|
| **Process** | Random pod kill | Kubernetes restarts failed pods within 30s | Single enforcement proxy | If error rate > 1% |
| **Process** | Policy engine kill | Enforcement proxies use cached rules; zero decision loss | All enforcement proxies | If any decision error |
| **Process** | Audit trail kill | Audit writes spool to disk; zero data loss | Audit trail component | If spool > 80% capacity |
| **Network** | Latency injection | p99 latency stays < 50ms with 100ms added latency | Enforcement path | If p99 > 100ms |
| **Network** | Packet loss | Circuit breaker opens; fail-closed; zero data loss | Single component | If any data loss |
| **Network** | DNS failure | Components use cached DNS; retry on failure | Service discovery | If any component unreachable > 30s |
| **Network** | Network partition | Fail-closed; agent actions denied; alert generated | Enforcement path | If any incorrect decision |
| **Resource** | Disk full | Spool to alternate location; alert operator; no data loss | Single component | If disk > 95% |
| **Resource** | Memory leak injection | Memory limits trigger OOM kill and restart | Single component | If restart count > 3/hour |
| **Resource** | CPU throttling | Load shedding activates; enforcement prioritized | Single component | If enforcement latency > 50ms |
| **Dependency** | Database primary kill | Patroni fails over within 60s | All components briefly | If failover > 120s |
| **Dependency** | Redis flush | Enforcement continues using in-memory cache | Cache-dependent components | If any decision error |
| **Dependency** | Kafka broker kill | Producer retries; consumer rebalances; zero loss | Audit and evidence | If any message loss |
| **Dependency** | OIDC provider outage | Cached JWTs used; new auth fails-closed | Authentication | If any incorrect auth |
| **Time** | Clock skew | Audit trail uses logical clock; alert on skew | Audit trail | If any timestamp anomaly |
| **Security** | Certificate expiry | Alert fires 30 days before expiry | TLS connections | If any cert expired |
| **Security** | Token expiry | Cached tokens refreshed; fail-closed for new auth | Authentication | If any auth failure |
| **Scale** | Full region evacuation | DR region activates within 5 minutes | Primary region | If RTO > 10 min |

#### 6.4.4 Chaos Engineering Maturity Model

| Level | Name | Characteristics |
|-------|------|----------------|
| **0 — Ad Hoc** | No chaos engineering | Failures discovered by users |
| **1 — Manual** | Manual chaos experiments | GameDays run manually; no automation |
| **2 — Automated** | Automated chaos experiments | Experiments run on schedule; results collected |
| **3 — Continuous** | Continuous chaos engineering | Experiments run continuously; integrated with CI/CD |
| **4 — Proactive** | Proactive resilience validation | Experiments drive architecture improvements; FMEA updated from results |

**GRC_Claw target: Level 3 (Continuous)** — automated chaos experiments running continuously in staging, with monthly production GameDays.

#### 6.4.5 GameDay Procedures

GameDays are planned, team-participated chaos experiments:

```
1. PLANNING (1 week before)
   - Define experiment scope and objectives
   - Identify participants and roles (observer, injector, recorder)
   - Define abort criteria and rollback procedures
   - Notify stakeholders

2. PREPARATION (1 day before)
   - Verify monitoring and alerting are functional
   - Verify rollback procedures are tested
   - Verify communication channels are available
   - Brief participants on experiment plan

3. EXECUTION (GameDay)
   - Establish baseline metrics (15 minutes)
   - Inject failure according to experiment plan
   - Monitor steady-state metrics
   - Abort if criteria breached
   - Document observations in real-time

4. REVIEW (within 24 hours)
   - Compare results against hypothesis
   - Identify gaps in monitoring, alerting, runbooks
   - Document lessons learned
   - Create action items for improvement

5. FOLLOW-UP (within 1 week)
   - Complete action items
   - Update FMEA with new findings
   - Update runbooks with new procedures
   - Share results with organization
```

### 6.5 Soak Testing

Weekly 72-hour soak tests:

- **Load profile:** Sustained 10,000 decisions/second with full evidence collection
- **Success criteria:**
  - No memory growth > 10%
  - No connection leaks
  - No file descriptor leaks
  - p99 latency drift < 5%
  - Zero decision errors
  - Zero audit write failures
  - Zero evidence loss

### 6.6 Failure Mode and Effects Analysis (FMEA)

#### 6.6.1 FMEA Methodology

GRC_Claw maintains a living FMEA document for all critical components. The FMEA process:

1. **Identify failure modes** — For each component, enumerate all possible failure modes
2. **Assess severity** — Rate the impact of each failure mode (1–10 scale)
3. **Assess occurrence** — Rate the likelihood of each failure mode (1–10 scale)
4. **Assess detection** — Rate how easily the failure is detected (1–10 scale)
5. **Calculate RPN** — Risk Priority Number = Severity × Occurrence × Detection
6. **Prioritize mitigation** — Address highest RPN items first
7. **Update continuously** — FMEA is updated after every incident, chaos experiment, and architecture change

#### 6.6.2 Severity Scale

| Score | Severity | Description |
|-------|----------|-------------|
| 10 | Catastrophic | Complete governance failure; agents operating without oversight; regulatory violation |
| 9 | Critical | Audit trail data loss; compliance evidence invalidated |
| 8 | Major | Enforcement unavailable; all agent actions blocked |
| 7 | Significant | Major feature unavailable; significant degradation |
| 6 | Moderate | Feature degradation; workaround available |
| 5 | Minor | Minor feature impact; no workaround needed |
| 4 | Negligible | Minimal impact; cosmetic issues |
| 3–1 | Insignificant | No meaningful impact |

#### 6.6.3 FMEA Table

| Component | Failure Mode | Effect | Detection | Mitigation | Severity | Occurrence | Detection | RPN |
|-----------|-------------|--------|-----------|------------|----------|------------|-----------|-----|
| Enforcement proxy | Process crash | Agent actions unevaluated | Health check | Kubernetes restart; fail-closed | 8 | 3 | 2 | 48 |
| Enforcement proxy | Memory leak | Gradual degradation | Memory monitoring | OOM kill; restart; scale out | 6 | 4 | 3 | 72 |
| Enforcement proxy | Cache corruption | Incorrect enforcement decisions | Decision validation | Cache invalidation; reload from policy engine | 9 | 2 | 4 | 72 |
| Policy engine | Policy corruption | Incorrect enforcement decisions | Schema validation | Version rollback; audit trail alert | 9 | 2 | 3 | 54 |
| Policy engine | Compilation failure | Policy not deployed | Compilation error alert | Rollback to previous version; alert | 7 | 3 | 2 | 42 |
| Audit trail | Hash chain break | Compliance evidence invalid | Hash verification | Halt writes; restore from backup | 9 | 2 | 2 | 36 |
| Audit trail | Write failure | Missing audit entries | Write error monitoring | Disk spool; retry; alert | 9 | 3 | 2 | 54 |
| PostgreSQL | Data loss | Policies and audit records gone | Replication monitoring | WAL archiving; cross-region replica | 10 | 1 | 2 | 20 |
| PostgreSQL | Primary failure | Write unavailability | Health check | Patroni failover; < 60s | 8 | 3 | 2 | 48 |
| PostgreSQL | Replication lag | Stale reads from replica | Lag monitoring | Route reads to primary; alert | 5 | 4 | 2 | 40 |
| Redis | Cache miss | Increased latency | Hit rate monitoring | Cache warming; fallback to DB | 4 | 5 | 2 | 40 |
| Redis | Memory eviction | Identity data lost | Eviction monitoring | Increase memory; persist to disk | 5 | 3 | 3 | 45 |
| Kafka | Message loss | Missing audit events | Consumer lag monitoring | MirrorMaker; disk spool | 9 | 2 | 3 | 54 |
| Kafka | Broker failure | Reduced throughput | Health check | Replication; leader election | 6 | 3 | 2 | 36 |
| Object Storage | Write failure | Evidence artifacts lost | Write error monitoring | Cross-region replication; retry | 7 | 3 | 2 | 42 |
| Object Storage | Read failure | Evidence unavailable | Read error monitoring | Cross-region replica; cache | 5 | 3 | 2 | 30 |
| OIDC Provider | Outage | New agents cannot authenticate | Auth failure monitoring | Cached JWTs; fail-closed | 6 | 4 | 2 | 48 |
| Certificate | Expiry | TLS connections fail | Expiry monitoring | Auto-renewal; alert 30 days prior | 7 | 2 | 1 | 14 |
| Disk | Full | Write failures | Disk monitoring | Spool to alternate; alert | 6 | 3 | 2 | 36 |
| Network | Partition | Component unreachable | Health check | Fail-closed; alert | 8 | 2 | 2 | 32 |
| Clock | Skew | Timestamp anomalies | Clock sync monitoring | Logical clock; alert | 5 | 2 | 3 | 30 |

#### 6.6.4 Fault Tree Analysis

For catastrophic failures (Severity ≥ 9), GRC_Claw maintains fault tree analyses:

```
TOP EVENT: Complete Governance Failure
├── Enforcement Proxy Unavailable (OR)
│   ├── All proxy instances crashed (AND)
│   │   ├── OOM kill on all instances
│   │   └── Bug causing crash on all instances
│   ├── All proxy instances partitioned from policy engine (AND)
│   │   ├── Network partition
│   │   └── DNS failure
│   └── All proxy instances rate-limited (AND)
│       ├── Misconfigured rate limit
│       └── Traffic spike
├── Policy Engine Unavailable (OR)
│   ├── All policy engine instances crashed
│   ├── Policy engine partitioned from enforcement proxies
│   └── Policy corruption preventing evaluation
└── Audit Trail Unavailable (OR)
    ├── All audit trail instances crashed
    ├── Audit trail storage full
    └── Audit trail hash chain corruption
```

### 6.7 Reliability Testing Automation

#### 6.7.1 CI/CD Integration

Reliability tests are integrated into the CI/CD pipeline as automated gates:

```
PR Opened
  │
  ▼
┌─────────────────────┐
│ Static Analysis      │  Lint, type check, security scan
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│ Unit Tests           │  Including fault injection unit tests
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│ Integration Tests    │  Including failure scenario tests
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│ Reliability Gate 1   │  Circuit breaker config valid
│                      │  Timeout config valid
│                      │  Retry budget config valid
│                      │  Fallback config valid
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│ Build & Deploy       │  Build container image
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│ Reliability Gate 2   │  Health check endpoints respond
│                      │  Metrics endpoint exposes reliability metrics
│                      │  Graceful shutdown works
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│ Staging Deploy       │  Deploy to staging
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│ Reliability Gate 3   │  Automated failure injection in staging
│                      │  Chaos experiment passes
│                      │  Soak test (short) passes
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│ Performance Gate     │  Latency regression < 5%
│                      │  Throughput regression < 10%
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│ Production Deploy    │  Canary deployment
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│ Reliability Gate 4   │  Canary error rate < 0.1%
│                      │  Canary p99 latency < 2x baseline
│                      │  No circuit breaker openings
│                      │  No fallback activations
└─────────┬───────────┘
          │
          ▼
      DEPLOYED
```

#### 6.7.2 Automated Failure Injection Framework

GRC_Claw includes a built-in failure injection framework for testing:

| Injection Type | Mechanism | Scope | Safety |
|---------------|-----------|-------|--------|
| **Process kill** | `kill -9` or Kubernetes pod delete | Single instance | Staging only |
| **Network latency** | `tc netem` or Istio fault injection | Service-to-service | Staging + production (controlled) |
| **Network partition** | `iptables` or Istio fault injection | Service-to-service | Staging only |
| **Packet loss** | `tc netem` | Service-to-service | Staging only |
| **DNS failure** | `iptables` blocking DNS or CoreDNS config | Service discovery | Staging only |
| **Disk fill** | `dd` writing to disk | Single instance | Staging only |
| **Memory pressure** | `stress-ng` or memory limit | Single instance | Staging only |
| **CPU throttling** | `stress-ng` or CPU limit | Single instance | Staging only |
| **Clock skew** | `libfaketime` or `date` command | Single instance | Staging only |
| **Certificate expiry** | Short-lived cert injection | TLS connections | Staging only |
| **Dependency failure** | Service mesh fault injection | External dependency | Staging + production (controlled) |

#### 6.7.3 Reliability Gates in Deployment Pipeline

| Gate | Stage | Criteria | Action on Failure |
|------|-------|----------|-------------------|
| **Config validation** | Pre-build | All circuit breakers, timeouts, retries, fallbacks configured | Block build |
| **Unit fault tests** | Build | All fault injection unit tests pass | Block build |
| **Integration failure tests** | Post-build | All failure scenario tests pass | Block deploy |
| **Health check validation** | Staging | All health endpoints respond correctly | Block deploy |
| **Metrics validation** | Staging | All reliability metrics exposed | Block deploy |
| **Chaos experiment** | Staging | Automated chaos experiment passes | Block deploy |
| **Canary analysis** | Production | Error rate < 0.1%, p99 < 2x baseline, no CB openings | Automatic rollback |

#### 6.7.4 Test Automation Schedule

| Test Suite | Frequency | Environment | Trigger |
|------------|-----------|-------------|---------|
| Unit fault injection | Every PR | CI | Automatic |
| Integration failure tests | Every PR | CI | Automatic |
| Reliability gate validation | Every PR | CI | Automatic |
| Chaos experiment (short) | Daily | Staging | Scheduled |
| Soak test (short — 4 hours) | Daily | Staging | Scheduled |
| Full chaos experiment | Weekly | Staging | Scheduled |
| Full soak test (72 hours) | Weekly | Staging | Scheduled |
| DR failover test | Monthly | Staging | Scheduled |
| Production GameDay | Monthly | Production | Planned |
| Full DR drill | Quarterly | Production | Planned |

### 6.8 Reliability Metrics and SLO Tracking

#### 6.8.1 Reliability Metrics

All components expose Prometheus metrics for reliability tracking:

| Metric | Type | Description |
|--------|------|-------------|
| `grc_reliability_availability_ratio` | Gauge | Rolling 30-day availability ratio |
| `grc_reliability_error_budget_remaining` | Gauge | Remaining error budget (1 - SLO) |
| `grc_reliability_error_budget_burn_rate` | Gauge | Current error budget burn rate |
| `grc_reliability_circuit_breaker_state` | Gauge | Current circuit breaker state (0=closed, 1=open, 2=half-open) |
| `grc_reliability_retry_count_total` | Counter | Total retries by operation |
| `grc_reliability_fallback_activations_total` | Counter | Total fallback activations by type |
| `grc_reliability_failover_duration_seconds` | Histogram | Time to complete failover |
| `grc_reliability_recovery_time_seconds` | Histogram | Time to recover from failure |
| `grc_reliability_data_loss_events_total` | Counter | Total data loss events (should always be 0) |
| `grc_reliability_slo_compliance_ratio` | Gauge | Current SLI / SLO ratio |
| `grc_reliability_chaos_experiment_result` | Gauge | Last chaos experiment result (0=fail, 1=pass) |
| `grc_reliability_fmea_rpn_max` | Gauge | Highest RPN in FMEA |

#### 6.8.2 Error Budget Policy

Error budgets balance reliability against feature velocity:

| SLO | Monthly Error Budget | Action When Budget Depleted |
|-----|---------------------|---------------------------|
| 99.9% | 43.8 min downtime | Freeze non-critical features; focus on reliability |
| 99.95% | 21.9 min downtime | Freeze all features; reliability sprint |
| 99.99% | 4.38 min downtime | All hands on reliability; post-incident review |

**Error budget tracking:** Automated dashboard showing burn rate and remaining budget, reviewed weekly.

---

## 7. Operational Procedures

### 7.1 Incident Response

#### 7.1.1 Incident Severity Levels

| Severity | Definition | Response Time | Escalation |
|----------|-----------|---------------|------------|
| **P1 — Critical** | Governance unavailable; agents operating without oversight | 5 minutes | Page on-call → CTO → Risk Committee |
| **P2 — High** | Significant degradation; enforcement latency > 50ms or error rate > 1% | 15 minutes | Page on-call → Engineering Lead |
| **P3 — Medium** | Minor degradation; single component failure with fallback active | 1 hour | Assign to on-call engineer |
| **P4 — Low** | Warning signs; no user impact | 4 hours | Create ticket; address in next sprint |

#### 7.1.2 Incident Response Process

```
1. DETECT    → Alert fires or user reports issue
2. TRIAGE    → Assess severity; declare incident if P1/P2
3. MITIGATE  → Apply runbook; failover; scale; rollback
4. RESOLVE   → Confirm recovery; monitor for 30 minutes
5. REVIEW    → Post-incident review within 48 hours (P1) or 1 week (P2)
6. LEARN     → Update runbooks; add tests; fix root cause
```

### 7.2 Deployment Safety

#### 7.2.1 Canary Deployments

All production deployments use canary releases:

```
Phase 1: 1% of traffic → 15 minutes → automated checks
Phase 2: 10% of traffic → 30 minutes → automated checks
Phase 3: 50% of traffic → 1 hour → automated checks
Phase 4: 100% of traffic → complete
```

**Automated rollback triggers:**
- Error rate > 0.1%
- p99 latency > 2× baseline
- Any audit write failure
- Any circuit breaker opening

#### 7.2.2 Feature Flags

All new features are behind feature flags:
- **Kill switch:** Instantly disable any feature without deployment
- **Gradual rollout:** Enable for specific tenants or agent groups
- **A/B testing:** Compare reliability impact of new features

### 7.3 Capacity Management

#### 7.3.1 Capacity Thresholds

| Resource | Scale-Up Threshold | Scale-Down Threshold | Max Capacity |
|----------|-------------------|---------------------|--------------|
| CPU | > 70% for 5 min | < 30% for 30 min | 85% |
| Memory | > 80% for 5 min | < 40% for 30 min | 90% |
| Disk | > 80% | N/A | 95% |
| Network | > 70% for 5 min | < 30% for 30 min | 85% |
| Kafka consumer lag | > 10,000 for 5 min | < 1,000 for 30 min | 50,000 |

#### 7.3.2 Load Shedding

When capacity is exhausted, GRC_Claw sheds load in priority order:

1. **Tier 1:** Enforcement decisions (never shed)
2. **Tier 2:** Audit trail writes (spool to disk)
3. **Tier 3:** Evidence collection (queue in Kafka)
4. **Tier 4:** API requests (rate limit; return 503)
5. **Tier 5:** Analytics and dashboards (disable; serve stale data)
6. **Tier 6:** Compliance reporting (defer to off-peak)

### 7.4 Reliability Monitoring and Alerting

#### 7.4.1 Four Golden Signals

GRC_Claw monitors the four golden signals for every component:

| Signal | Metric | SLI | SLO | Alert Threshold |
|--------|--------|-----|-----|-----------------|
| **Latency** | `grc_reliability_request_duration_seconds` | p99 < threshold | Per-component SLO | p99 > 2× threshold for 5 min |
| **Traffic** | `grc_reliability_requests_total` | Request rate | N/A (informational) | Sudden 5× increase or decrease |
| **Errors** | `grc_reliability_errors_total` | Error ratio | < 0.1% | Error ratio > 0.1% for 1 min |
| **Saturation** | `grc_reliability_resource_utilization` | Resource usage | < 80% | > 80% for 5 min |

#### 7.4.2 SLO-Based Alerting

Alerts are based on SLO burn rates, not static thresholds:

| Alert | Condition | Severity | Action |
|-------|-----------|----------|--------|
| **Fast burn** | Error budget burn rate > 14.4× (budget depleting in < 2 days) | Critical | Page on-call; declare incident |
| **Slow burn** | Error budget burn rate > 2× (budget depleting in < 15 days) | Warning | Investigate; reliability review |
| **SLO breach** | Availability < SLO for 5 minutes | Critical | Page on-call; declare incident |
| **Error budget depleted** | Error budget remaining = 0 | Critical | Freeze features; reliability sprint |

#### 7.4.3 Alert Fatigue Prevention

To prevent alert fatigue:

| Practice | Implementation |
|----------|---------------|
| **Actionable alerts** | Every alert must have a runbook entry and clear action |
| **Alert deduplication** | Alerts for the same root cause are grouped |
| **Severity calibration** | Alerts are calibrated to avoid false positives (< 5% false positive rate) |
| **Quiet hours** | Non-critical alerts suppressed during on-call sleep hours |
| **Alert review** | Weekly review of all alerts; remove or tune noisy alerts |
| **SLO-based alerting** | Alert on SLO burn rate, not individual request failures |

#### 7.4.4 Monitoring Stack Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Grafana Dashboards                 │
│  (Reliability Overview, Failure Analysis, DR)       │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│                   Prometheus                         │
│  (Metrics collection, alerting rules, SLO tracking) │
└──────────────────────┬──────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
┌───────▼──────┐ ┌────▼─────┐ ┌─────▼─────┐
│   GRC_Claw   │ │  Node     │ │  Kafka    │
│  Components  │ │ Exporter  │ │ Exporter  │
│  (/metrics)  │ │           │ │           │
└──────────────┘ └──────────┘ └───────────┘
        │
┌───────▼──────────────────────────────────────────────┐
│              OpenTelemetry Collector                  │
│  (Traces, logs, metrics aggregation)                  │
└──────────────────────┬──────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
┌───────▼──────┐ ┌────▼─────┐ ┌─────▼─────┐
│   Jaeger     │ │  Loki    │ │  Tempo    │
│  (Traces)    │ │  (Logs)  │ │  (Traces) │
└──────────────┘ └──────────┘ └───────────┘
```

#### 7.4.5 Reliability Dashboards

Four Grafana dashboards are provided:

1. **Reliability Overview** — SLO status, error budget, availability by component, incident timeline
2. **Failure Analysis** — Circuit breaker states, retry rates, fallback activations, failure distribution
3. **Disaster Recovery** — Backup status, replication lag, DR readiness, last DR drill results
4. **SLO Compliance** — SLI vs SLO by component, error budget burn rate, burn rate alerts

#### 7.4.6 Alerting Rules

| Alert | Condition | Severity | Action |
|-------|-----------|----------|--------|
| **SLO breach** | Availability < SLO for 5 minutes | Critical | Page on-call; declare incident |
| **Error budget burn** | > 50% of monthly budget consumed in < 7 days | Warning | Investigate; reliability sprint |
| **Circuit breaker open** | Any circuit breaker in OPEN state | Warning | Investigate dependency |
| **Audit write failure** | Any audit write failure | Critical | Page on-call immediately |
| **Replication lag** | PostgreSQL replication lag > 30 seconds | Warning | Investigate network or DB load |
| **Backup failure** | Any backup job failure | Critical | Page on-call; manual backup |
| **DR drill overdue** | Last DR drill > 90 days ago | Warning | Schedule DR drill |
| **Certificate expiry** | Any certificate expires in < 30 days | Warning | Renew certificate |
| **Fast burn rate** | Error budget burn rate > 14.4× | Critical | Page on-call; declare incident |
| **Data loss event** | Any data loss event detected | Critical | Page on-call; halt writes; investigate |
| **Fail-open activated** | Any fail-open circuit breaker activated | Critical | Page on-call; review governance bypass |
| **Chaos experiment failure** | Any automated chaos experiment fails | Warning | Investigate; create action items |

#### 7.4.7 Observability Practices

| Practice | Implementation |
|----------|---------------|
| **Structured logging** | JSON logs with trace ID, span ID, component, severity, timestamp |
| **Distributed tracing** | OpenTelemetry traces across all components; 10% sampling |
| **Metrics labeling** | All metrics labeled with component, instance, tenant, endpoint |
| **Log correlation** | Trace ID injected into all logs for end-to-end correlation |
| **Error tracking** | Errors aggregated by type, component, and endpoint |
| **SLO tracking** | Real-time SLI calculation and SLO compliance monitoring |

---

## 8. Data Durability and Integrity

### 8.1 Audit Trail Durability

The audit trail is the **most critical data asset** — it is the evidence base for compliance.

| Property | Guarantee | Mechanism |
|----------|-----------|-----------|
| **Immutability** | Append-only; no modification or deletion | Database permissions; WORM storage option |
| **Integrity** | Hash-chained; tamper-evident | SHA-256 hash chain; periodic verification |
| **Availability** | 99.99% | Cross-region replication; WAL archiving |
| **Durability** | Zero data loss | Synchronous replication; WAL archiving; backup verification |
| **Retention** | Configurable; default 7 years | Automated lifecycle policies |

### 8.2 Evidence Durability

| Property | Guarantee | Mechanism |
|----------|-----------|-----------|
| **Completeness** | Zero evidence loss | Kafka replication (RF=3); disk spool fallback |
| **Integrity** | SHA-256 checksums | Signed artifacts; verification on access |
| **Availability** | 99.5% | Cross-region S3 replication |
| **Retention** | Configurable; default 7 years | S3 lifecycle policies |

### 8.3 Backup Verification

Every backup is verified:

1. **Checksum verification** — SHA-256 checksums computed and stored alongside backup
2. **Restore test** — Weekly automated restore to isolated environment
3. **Integrity check** — Database consistency checks (pg_checksums)
4. **Audit trail verification** — Hash chain verification after restore

---

## 9. Reliability Maintenance

### 9.1 Reliability Review Cadence

| Review | Frequency | Participants | Output |
|--------|-----------|-------------|--------|
| **SLO review** | Weekly | Engineering + Product | SLO compliance report; error budget status |
| **Incident review** | Per incident | Engineering + SRE | Post-incident report; action items |
| **FMEA update** | Monthly | Architecture team | Updated FMEA document |
| **DR drill** | Quarterly | Full team | DR drill report; runbook updates |
| **Capacity review** | Monthly | Engineering + SRE | Capacity plan; scaling recommendations |
| **Reliability audit** | Annually | External auditor | Reliability assessment report |
| **Chaos experiment review** | Monthly | Engineering + SRE | Chaos experiment results; action items |
| **Alert review** | Weekly | SRE | Alert tuning; noise reduction |

### 9.2 Reliability Improvement Process

GRC_Claw follows a continuous improvement loop for reliability:

```
┌──────────────┐
│ 1. MEASURE   │  Track SLOs, error budgets, failure rates
└──────┬───────┘
       │
┌──────▼───────┐
│ 2. IDENTIFY  │  Find weak points via FMEA, incident analysis, chaos tests
└──────┬───────┘
       │
┌──────▼───────┐
│ 3. PRIORITIZE│  Rank by severity × likelihood × blast radius
└──────┬───────┘
       │
┌──────▼───────┐
│ 4. IMPLEMENT │  Add circuit breakers, retries, fallbacks, tests
└──────┬───────┘
       │
┌──────▼───────┐
│ 5. VERIFY    │  Chaos tests, soak tests, DR drills
└──────┬───────┘
       │
       └──────▶ Return to MEASURE
```

### 9.3 Reliability Requirements for Changes

Every change to GRC_Claw must satisfy:

| Requirement | Verification |
|-------------|-------------|
| **No single point of failure** | Architecture review; component redundancy |
| **Graceful degradation** | Failure injection test; fallback validation |
| **Automated recovery** | Chaos test; failover test |
| **No data loss** | Backup verification; replication test |
| **SLO compliance** | Performance test; latency regression < 5% |
| **Observability** | Metrics, logs, and traces for all new code |
| **Runbook update** | Updated runbooks for new failure modes |

### 9.4 Reliability Training

All engineers working on GRC_Claw must complete:

- **Onboarding:** Reliability principles, SLOs, incident response process
- **Quarterly:** Chaos engineering participation; DR drill involvement
- **Annually:** External reliability training (SRE conference, workshop, or course)

---

## 10. Compliance and Framework Alignment

This reliability specification supports the following framework requirements:

| Framework | Control | Reliability Requirement |
|-----------|---------|------------------------|
| **ISO 42001** | Clause 9.1 (Monitoring) | Continuous availability monitoring with SLOs |
| **ISO 42001** | Clause 10.2 (Corrective Action) | Incident response and reliability improvement process |
| **NIST AI RMF** | MANAGE 2 (Risk Response) | Automated failover and disaster recovery |
| **NIST AI RMF** | MANAGE 4.2 (Updates) | Deployment safety; canary releases; feature flags |
| **SOC 2** | CC7.2 (System Monitoring) | Reliability monitoring and alerting |
| **SOC 2** | CC7.3 (Incident Response) | Incident response process with severity levels |
| **SOC 2** | A1.2 (Availability) | Availability targets and SLOs |
| **SOC 2** | A1.3 (Disaster Recovery) | DR procedures and testing |
| **DORA** | Art. 5 (ICT Risk Management) | FMEA; fault tolerance patterns |
| **DORA** | Art. 6 (ICT Incident Reporting) | Incident severity levels and response times |
| **DORA** | Art. 7 (Digital Operational Resilience Testing) | Chaos engineering; DR drills; soak tests |
| **COBIT 2019** | MEA01 (Performance Monitoring) | Reliability metrics and SLO tracking |
| **COBIT 2019** | BAI03 (Manage Availability) | Availability targets and capacity management |

---

## 11. Roles and Responsibilities

| Role | Responsibility |
|------|---------------|
| **SRE Team** | Operates GRC_Claw in production; incident response; capacity management; DR execution; toil reduction |
| **Engineering Team** | Implements fault tolerance patterns; writes reliability tests; maintains runbooks |
| **Architecture Team** | Defines reliability requirements; reviews designs for SPOFs; maintains FMEA |
| **Product Team** | Defines SLOs with customers; manages error budget tradeoffs |
| **QA Team** | Executes reliability test suite; validates failure scenarios |
| **Security Team** | Security incident response; ransomware recovery; forensic analysis |
| **CTO** | Approves SLOs; owns reliability budget; incident escalation |

---

## 12. Appendices

### Appendix A: Glossary

| Term | Definition |
|------|------------|
| **SLO** | Service Level Objective — a target reliability level (e.g., 99.9% availability) |
| **SLI** | Service Level Indicator — a measured reliability metric (e.g., actual availability) |
| **Error Budget** | The allowable unreliability (1 - SLO) that can be spent on feature development |
| **Burn Rate** | The rate at which error budget is being consumed relative to the planned rate |
| **RPO** | Recovery Point Objective — maximum acceptable data loss measured in time |
| **RTO** | Recovery Time Objective — maximum acceptable downtime measured in time |
| **Circuit Breaker** | A pattern that stops calling a failing dependency to prevent cascading failures |
| **Bulkhead** | A pattern that isolates failure domains to prevent system-wide cascading failures |
| **Fail-Closed** | Defaulting to denial of service when governance is unavailable |
| **Fail-Open** | Defaulting to allowing actions when governance is unavailable (requires explicit configuration) |
| **FMEA** | Failure Mode and Effects Analysis — systematic identification of potential failures |
| **RPN** | Risk Priority Number — Severity × Occurrence × Detection; used to prioritize FMEA items |
| **Chaos Engineering** | Controlled experiments that inject failures to validate resilience |
| **GameDay** | A planned, team-participated chaos experiment |
| **WORM** | Write-Once-Read-Many — storage that prevents modification or deletion |
| **Backpressure** | A mechanism to propagate load upstream when downstream is saturated |
| **Rate Limiting** | A mechanism to restrict the number of requests per unit time |
| **Leader Election** | A mechanism to select a single active instance among replicas |
| **Fencing Token** | A monotonically increasing token used to prevent split-brain dual-writes |
| **Toil** | Repetitive, manual, automatable operational work that scales with system growth |
| **Four Golden Signals** | Latency, traffic, errors, saturation — the four key metrics for monitoring |
| **Steady-State** | The expected normal behavior of a system, used as baseline for chaos experiments |
| **Blast Radius** | The scope of impact of a failure or chaos experiment |

### Appendix B: Reliability Test Checklist

Before each release, verify:

- [ ] All unit-level fault injection tests pass
- [ ] All integration failure tests pass
- [ ] Soak test (72-hour) passes with no degradation
- [ ] Chaos experiment results reviewed and action items addressed
- [ ] DR drill completed within last 90 days
- [ ] Backup restore test passed
- [ ] All circuit breakers configured and tested
- [ ] All fallbacks validated
- [ ] All timeouts configured and tested
- [ ] All rate limits configured and tested
- [ ] All backpressure mechanisms tested
- [ ] Error budget status reviewed
- [ ] SLO compliance verified for last 30 days
- [ ] Runbooks updated for any new failure modes
- [ ] Monitoring dashboards functional
- [ ] Alerting rules tested
- [ ] Capacity plan updated
- [ ] FMEA updated for any new components
- [ ] Reliability gates pass in CI/CD pipeline
- [ ] Four golden signals monitored for all components
- [ ] SLO-based alerting configured and tested

### Appendix C: Incident Response Runbook Template

```
# Incident: [Title]
## Severity: P1/P2/P3/P4
## Date: [YYYY-MM-DD]
## Author: [Name]

### Summary
[One-paragraph description of the incident]

### Timeline
- [HH:MM] Detection: [How was it detected?]
- [HH:MM] Triage: [Initial assessment]
- [HH:MM] Mitigation: [Actions taken]
- [HH:MM] Resolution: [How was it resolved?]
- [HH:MM] Recovery: [Confirmation of full recovery]

### Root Cause
[Detailed root cause analysis]

### Impact
- Duration: [X minutes/hours]
- Affected components: [List]
- Affected tenants/agents: [List]
- Data loss: [Yes/No; details]
- Error budget consumed: [X minutes]

### Action Items
| Action | Owner | Deadline | Status |
|--------|-------|----------|--------|
| [Action 1] | [Name] | [Date] | Open/Closed |
| [Action 2] | [Name] | [Date] | Open/Closed |

### Lessons Learned
[What went well? What could be improved?]

### Prevention
[What changes will prevent this from recurring?]
```

### Appendix D: Chaos Experiment Template

```
# Chaos Experiment: [Name]

## Hypothesis
If [failure injected], then [steady-state metric] remains within [threshold]

## Steady-State Definition
- Metric: [e.g., p99 latency]
- Value: [e.g., < 10 ms]
- Tolerance: [e.g., ± 2 ms]

## Blast Radius
- Scope: [e.g., single enforcement proxy]
- Components affected: [list]
- Tenants affected: [list or "none"]

## Failure Injection
- Type: [e.g., process kill, network latency]
- Mechanism: [e.g., Kubernetes pod delete, tc netem]
- Duration: [e.g., 5 minutes]

## Abort Condition
- [e.g., error rate > 1%]
- [e.g., p99 latency > 100ms]
- [e.g., any data loss]

## Expected Recovery
- [e.g., Kubernetes restarts pod within 30s]
- [e.g., traffic rerouted to healthy instances within 5s]

## Success Criteria
- [e.g., zero decision errors]
- [e.g., zero audit write failures]
- [e.g., p99 latency returns to < 10ms within 60s]

## Rollback Procedure
- [e.g., restart all pods in deployment]
- [e.g., remove network policy]

## Results
- Date: [YYYY-MM-DD]
- Outcome: Pass/Fail
- Observations: [notes]
- Action Items: [list]
```

---

**Document Approval:**

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Author | GRC_Claw Architecture Team | — | 2026-10-01 |
| Reviewer | SRE Lead | — | — |
| Reviewer | CTO | — | — |
| Approver | Risk Committee | — | — |

---

*End of Reliability Specification*