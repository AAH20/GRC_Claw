# GRC_Claw Scalability Specification

**Version:** 2.0  
**Date:** 2026-10-01  
**Status:** Draft  
**Owner:** GRC_Claw Architecture Team  
**Parent Documents:** GRC_Claw Reference Architecture v1.0, Performance Spec v1.0, Storage Spec v1.0, Gap Analysis v1.0  
**Related Documents:** GRC_Claw Performance Specification v1.0

---

## 1. Purpose & Scope

This specification defines how GRC_Claw scales from a single-team deployment to enterprise-grade, multi-tenant, geographically distributed operations. It establishes the horizontal scaling patterns, multi-tenancy model, data partitioning strategy, and load balancing architecture that enable GRC_Claw to grow with organizational needs without re-architecture.

**In scope:** All GRC_Claw runtime components — PDP, PEP, evidence pipeline, audit trail, policy engine, compliance mapping, observability, and data storage.  
**Out of scope:** Build-time scalability, developer tooling, CI/CD pipeline scaling.

---

## 2. Design Principles

| Principle | Rationale |
|-----------|-----------|
| **Stateless enforcement** | PDP and PEP instances hold no session state; any instance can serve any request, enabling horizontal scale-out and instant failover |
| **Shared-nothing data plane** | Each data partition is independent; no cross-partition transactions in the enforcement path |
| **Tenant-isolated by default** | Every data structure carries a tenant context; isolation is enforced at the storage layer, not just the application layer |
| **Graceful degradation** | Under extreme load, non-critical features (analytics, dashboards, cross-validation) shed load before enforcement decisions |
| **Linear scale-out** | Adding capacity (instances, partitions) yields proportional throughput improvement within 15% of ideal |
| **Zero-downtime operations** | Policy deployments, schema changes, and rolling restarts never interrupt enforcement |

---

## 3. Scaling Tiers

GRC_Claw defines four deployment tiers. Each tier is a superset of the previous — no re-architecture required to move between tiers.

### Tier 1: Single-Team (1–50 agents)

```
┌─────────────────────────────────────────────┐
│              Single Node                     │
│  ┌─────────┐  ┌─────────┐  ┌─────────────┐ │
│  │   PDP   │  │   PEP   │  │  Evidence   │ │
│  │  (OPA)  │  │(Gateway)│  │  Collector  │ │
│  └────┬────┘  └────┬────┘  └──────┬──────┘ │
│       │            │              │         │
│       └────────────┼──────────────┘         │
│                    │                        │
│              ┌─────▼─────┐                  │
│              │ PostgreSQL │                  │
│              │  + Redis   │                  │
│              │  + MinIO   │                  │
│              └───────────┘                  │
└─────────────────────────────────────────────┘
```

| Attribute | Target |
|-----------|--------|
| Agents | 1–50 |
| Decisions/sec | 100–1,000 |
| Policies | 1–50 |
| Evidence items | < 1M |
| Tenants | 1 |
| Availability | 99.5% |
| Deployment | Single Docker Compose or single K8s node |

### Tier 2: Department (50–500 agents)

```
┌──────────────────────────────────────────────────────────┐
│                    Kubernetes Cluster                      │
│                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐               │
│  │  PEP x2  │  │  PEP x2  │  │  PEP x2  │  (MCP Gateway)│
│  └────┬─────┘  └────┬─────┘  └────┬─────┘               │
│       │              │              │                     │
│       └──────────────┼──────────────┘                     │
│                      │                                    │
│              ┌───────▼───────┐                            │
│              │  PDP x2 (OPA) │                            │
│              └───────┬───────┘                            │
│                      │                                    │
│       ┌──────────────┼──────────────┐                     │
│       │              │              │                     │
│  ┌────▼────┐   ┌────▼────┐   ┌────▼────┐                │
│  │Evidence │   │  Audit  │   │ Policy  │                │
│  │Collector│   │ Trail   │   │  API    │                │
│  │  x2     │   │  x2     │   │  x2     │                │
│  └────┬────┘   └────┬────┘   └────┬────┘                │
│       │              │              │                     │
│       └──────────────┼──────────────┘                     │
│                      │                                    │
│  ┌───────────────────▼───────────────────┐               │
│  │           Data Layer                   │               │
│  │  PostgreSQL (HA)  │  Redis Cluster     │               │
│  │  MinIO (WORM)      │  Kafka (3 brokers) │               │
│  └───────────────────────────────────────┘               │
└──────────────────────────────────────────────────────────┘
```

| Attribute | Target |
|-----------|--------|
| Agents | 50–500 |
| Decisions/sec | 1,000–10,000 |
| Policies | 50–500 |
| Evidence items | 1M–100M |
| Tenants | 1–10 |
| Availability | 99.9% |
| Deployment | Multi-node K8s, HA PostgreSQL, Redis Cluster |

### Tier 3: Enterprise (500–5,000 agents)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        Multi-Region Kubernetes                           │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                     Global Load Balancer                         │   │
│  │              (GeoDNS / Anycast / Cloud LB)                       │   │
│  └──────────────────────────┬──────────────────────────────────────┘   │
│                             │                                           │
│  ┌──────────────────────────┼──────────────────────────────────────┐   │
│  │                          │                                       │   │
│  │  ┌───────────────────────▼───────────────────────────────────┐  │   │
│  │  │              Regional Load Balancer (L7)                   │  │   │
│  │  └───────────────────────┬───────────────────────────────────┘  │   │
│  │                          │                                       │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │   │
│  │  │ PEP xN   │  │ PEP xN   │  │ PEP xN   │  │ PEP xN   │       │   │
│  │  │(per AZ)  │  │(per AZ)  │  │(per AZ)  │  │(per AZ)  │       │   │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘       │   │
│  │       │              │              │              │              │   │
│  │       └──────────────┼──────────────┘              │              │   │
│  │                      │                             │              │   │
│  │              ┌───────▼───────┐           ┌────────▼────────┐    │   │
│  │              │  PDP xN (OPA) │           │  PDP xN (OPA)   │    │   │
│  │              │  (per region) │           │  (per region)   │    │   │
│  │              └───────┬───────┘           └────────┬────────┘    │   │
│  │                      │                             │              │   │
│  │  ┌───────────────────▼─────────────────────────────▼───────────┐  │   │
│  │  │              Shared Services (per region)                    │  │   │
│  │  │  Evidence xN  │  Audit xN  │  Policy API xN  │  Identity   │  │   │
│  │  └───────────────────────────┬────────────────────────────────┘  │   │
│  │                              │                                    │   │
│  │  ┌───────────────────────────▼────────────────────────────────┐  │   │
│  │  │              Data Layer (per region, replicated)            │  │   │
│  │  │  PostgreSQL (Patroni HA)  │  Redis Cluster  │  Kafka       │  │   │
│  │  │  MinIO (WORM, erasure-coded)│  Neo4j (clustered)│  Timescale │  │   │
│  │  └────────────────────────────────────────────────────────────┘  │   │
│  │                                                                   │   │
│  └───────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  Cross-region: Async replication (Kafka maker-maker, PostgreSQL logical) │
└─────────────────────────────────────────────────────────────────────────┘
```

| Attribute | Target |
|-----------|--------|
| Agents | 500–5,000 |
| Decisions/sec | 10,000–50,000 |
| Policies | 500–5,000 |
| Evidence items | 100M–1B |
| Tenants | 10–100 |
| Availability | 99.95% |
| Deployment | Multi-region K8s, Patroni HA, Redis Cluster, Kafka MM replication |

### Tier 4: Global Enterprise (5,000–50,000+ agents)

| Attribute | Target |
|-----------|--------|
| Agents | 5,000–50,000+ |
| Decisions/sec | 50,000–200,000+ |
| Policies | 5,000–50,000 |
| Evidence items | 1B–10B+ |
| Tenants | 100–1,000+ |
| Availability | 99.99% |
| Deployment | Multi-region active-active, cell-based architecture, data residency enforcement |

---

## 4. Horizontal Scaling Patterns

### 4.1 Enforcement Proxy (PEP) Scaling

The PEP is the most frequently scaled component — it intercepts every agent action.

**Pattern: Stateless Horizontal Scale-Out**

```
                    ┌─────────────────┐
                    │   Load Balancer  │
                    │  (L4/L7, anycast)│
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
     ┌────────▼───────┐ ┌───▼────────┐ ┌──▼──────────┐
     │ PEP Instance 1 │ │ PEP Inst 2 │ │ PEP Inst N  │
     │                │ │            │ │             │
     │ • No session   │ │ • No sess  │ │ • No sess   │
     │ • Local cache  │ │ • Local c  │ │ • Local c   │
     │ • Stateless    │ │ • Stateless│ │ • Stateless │
     └────────┬───────┘ └─────┬──────┘ └──────┬──────┘
              │               │               │
              └───────────────┼───────────────┘
                              │
                    ┌─────────▼─────────┐
                    │  Shared State      │
                    │  (Redis Cluster +  │
                    │   PostgreSQL)      │
                    └───────────────────┘
```

**Scaling characteristics:**

| Aspect | Detail |
|--------|--------|
| **State** | Stateless — all session state in Redis/PostgreSQL |
| **Local cache** | Compiled policies, agent identities, decision cache (LRU, 5-min TTL) |
| **Scale trigger** | CPU > 70% for 5 min, or p99 latency > 15 ms for 2 min |
| **Scale increment** | +1 instance (scale out), -1 instance (scale in) |
| **Max instances** | 100 per region (soft limit; hard limit 500) |
| **Warm-up** | New instance loads policy cache from Redis in < 5 seconds |
| **Drain** | In-flight requests complete before termination (30s grace) |

**Kubernetes HPA configuration:**

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: grc-pep-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: grc-pep-gateway
  minReplicas: 2
  maxReplicas: 100
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Pods
      pods:
        metric:
          name: grc_enforcement_decision_duration_seconds
        target:
          type: AverageValue
          averageValue: 15m  # 15ms p99 target
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
        - type: Pods
          value: 4
          periodSeconds: 60
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
        - type: Pods
          value: 1
          periodSeconds: 120
```

### 4.2 Policy Decision Point (PDP) Scaling

**Pattern: Partitioned Evaluation with Shared Cache**

The PDP evaluates policies against input documents. Scaling is achieved through:

1. **Policy partitioning** — Policies are grouped by domain (data-access, content-safety, agent-lifecycle). Each PDP instance evaluates a subset.
2. **Decision caching** — Identical (agent, action, resource, context) tuples return cached decisions.
3. **Pre-computation** — Scheduled actions have decisions pre-computed and stored.

```
┌─────────────────────────────────────────────────────────────┐
│                    PDP Cluster                               │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ PDP Shard 1  │  │ PDP Shard 2  │  │ PDP Shard N  │     │
│  │              │  │              │  │              │     │
│  │ Domain:      │  │ Domain:      │  │ Domain:      │     │
│  │ data-access  │  │ content-safety│  │ agent-lifecycle│   │
│  │              │  │              │  │              │     │
│  │ Policies:    │  │ Policies:    │  │ Policies:    │     │
│  │ pol-001..100 │  │ pol-101..200 │  │ pol-201..300 │     │
│  │              │  │              │  │              │     │
│  │ Local cache: │  │ Local cache: │  │ Local cache: │     │
│  │ 10K decisions│  │ 10K decisions│  │ 10K decisions│     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
│         │                 │                 │              │
│         └─────────────────┼─────────────────┘              │
│                           │                                │
│                  ┌────────▼────────┐                       │
│                  │  Redis Cluster  │                       │
│                  │  (Decision Cache│                       │
│                  │   + Policy Dist)│                       │
│                  └─────────────────┘                       │
└─────────────────────────────────────────────────────────────┘
```

**Scaling characteristics:**

| Aspect | Detail |
|--------|--------|
| **Partition key** | Policy domain (data-access, content-safety, agent-lifecycle, etc.) |
| **Rebalancing** | Policies reassigned via consistent hashing when shards added/removed |
| **Cache hit rate** | Target > 80% for repeated agent actions |
| **Scale trigger** | Evaluation queue depth > 1,000 or p99 evaluation > 30 ms |
| **Max instances** | 50 per region |

### 4.3 Evidence Pipeline Scaling

**Pattern: Partitioned Stream Processing**

Evidence collection is the highest-volume write path. It scales via Kafka partition parallelism.

```
┌──────────┐     ┌──────────────────────────────────────────┐
│ Collectors│────▶│           Kafka Cluster                   │
│ (xN)      │     │                                          │
└──────────┘     │  Topic: evidence-events                  │
                 │  Partitions: 24 (scalable to 96)         │
                 │  Replication: 3                          │
                 │                                          │
                 │  ┌────────┐ ┌────────┐ ┌────────┐       │
                 │  │Part 0-7│ │Part 8-15│ │Part 16-23│     │
                 │  └───┬────┘ └───┬────┘ └───┬────┘       │
                 └──────┼──────────┼──────────┼─────────────┘
                        │          │          │
                 ┌──────▼──────────▼──────────▼─────────────┐
                 │         Evidence Processors (xN)          │
                 │                                          │
                 │  • Normalize to OSCAL                    │
                 │  • Schema validate                        │
                 │  • Hash compute (SHA-256)                 │
                 │  • Write to evidence store               │
                 │  • Update audit chain                    │
                 └──────────────────────────────────────────┘
```

**Scaling characteristics:**

| Aspect | Detail |
|--------|--------|
| **Partition key** | `tenant_id + agent_id` (ensures per-agent ordering) |
| **Consumer group** | Evidence processors consume in parallel; one consumer per partition |
| **Scale trigger** | Consumer lag > 10,000 messages or processing p99 > 500 ms |
| **Max partitions** | 96 per topic (Kafka practical limit) |
| **Backpressure** | If evidence store is slow, consumers pause; Kafka retains events |
| **Dead-letter queue** | Failed events routed to DLQ after 3 retries; manual review workflow |

### 4.4 Audit Trail Scaling

**Pattern: Append-Only Partitioned Log**

The audit trail is an append-only, hash-chained log. It scales via:

1. **Time-based partitioning** — Monthly partitions (hot) → yearly partitions (cold)
2. **Hash chain sharding** — Each tenant has an independent hash chain; chains are verified in parallel
3. **Async verification** — Hash chain verification runs asynchronously, not in the write path

```
┌─────────────────────────────────────────────────────────────┐
│                   Audit Trail Architecture                    │
│                                                             │
│  Write Path (fast, async):                                 │
│  ┌────────┐    ┌────────┐    ┌────────┐    ┌────────┐     │
│  │ PEP    │───▶│ Kafka  │───▶│ Audit  │───▶│ immudb │     │
│  │ Events │    │ (audit)│    │ Writer │    │ (WORM) │     │
│  └────────┘    └────────┘    └────────┘    └────────┘     │
│                                                             │
│  Verification Path (async, parallel):                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Verify Shard │  │ Verify Shard │  │ Verify Shard │     │
│  │ (tenant A-M) │  │ (tenant N-Z) │  │ (cross-tenant)│     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                             │
│  Partitioning:                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ 2026-10 │ 2026-09 │ 2026-08 │ ... │ 2025-01 │ 2024  │  │
│  │  (hot)   │  (hot)   │  (warm) │     │ (cold)  │(arch)│  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 5. Multi-Tenancy Requirements

### 5.1 Tenant Model

GRC_Claw uses a **pooled multi-tenancy** model with **silo** option for regulated industries.

| Model | Description | Use Case |
|-------|-------------|----------|
| **Pooled (default)** | Shared infrastructure, logical data isolation via `tenant_id` | Most organizations — cost-efficient, operationally simple |
| **Silo (dedicated)** | Dedicated infrastructure per tenant | Regulated industries (HIPAA, PCI DSS), government — physical isolation |
| **Bridge** | Shared control plane, dedicated data plane | Organizations with mixed sensitivity levels |

### 5.2 Tenant Isolation Requirements

| Layer | Pooled Model | Silo Model |
|-------|-------------|------------|
| **Compute** | Shared K8s namespace, resource quotas | Dedicated K8s cluster or node pool |
| **Data** | Row-level security (RLS) on `tenant_id` | Dedicated database instances |
| **Cache** | Key prefix `tenant:{id}:` | Dedicated Redis instances |
| **Kafka** | Topic per tenant or partition by `tenant_id` | Dedicated Kafka cluster |
| **Storage** | Bucket prefix `tenant-{id}/` | Dedicated MinIO/S3 buckets |
| **Network** | Network policies, mTLS | Physical network isolation |
| **Encryption** | Shared KMS, per-tenant DEKs | Dedicated KMS/HSM |

### 5.3 Tenant Context Propagation

Every request carries tenant context through the entire call chain:

```json
{
  "tenant": {
    "id": "tenant-uuid",
    "tier": "enterprise",
    "region": "us-east-1",
    "data_residency": "US",
    "encryption_key_id": "key-uuid"
  }
}
```

**Propagation mechanism:**

| Layer | Mechanism |
|-------|-----------|
| HTTP/gRPC | `X-Tenant-ID` header + JWT claim |
| Kafka | Message header `tenant_id` |
| OpenTelemetry | Baggage item `tenant.id` |
| Database | `app.current_tenant_id` session variable (RLS) |
| Cache | Key prefix `tenant:{id}:` |

### 5.4 Tenant Lifecycle

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ Provision│───▶│  Active  │───▶│ Suspended│───▶│ Archived │───▶│ Deleted  │
│          │    │          │    │          │    │          │    │          │
│ • Create │    │ • Full   │    │ • Read-  │    │ • Data   │    │ • Crypto │
│   infra  │    │   service│    │   only   │    │   export │    │   erase  │
│ • Assign │    │ • Agents │    │ • No new │    │ • 30-day │    │ • Audit  │
│   quota  │    │   active │    │   agents │    │   retain │    │   retain │
│ • Set    │    │ • Policies│   │ • Policies│   │ • Then   │    │ • Then   │
│   policies│   │   active │    │   frozen │    │   purge  │    │   purge  │
└──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘
```

### 5.5 Tenant Resource Quotas

| Resource | Default Quota | Burst Quota | Enforcement |
|----------|--------------|-------------|-------------|
| Agents | 100 | 200 | Hard limit at 200 |
| Policies | 50 | 100 | Hard limit at 100 |
| Decisions/sec | 1,000 | 5,000 | Rate limit + queue |
| Evidence items/day | 1M | 5M | Soft limit + alert |
| Storage | 100 GB | 500 GB | Hard limit at 500 GB |
| API requests/min | 10,000 | 50,000 | Rate limit |
| Concurrent agents | 50 | 100 | Hard limit at 100 |

### 5.6 Tenant Onboarding

```python
class TenantProvisioner:
    """Provision a new tenant in < 5 minutes."""
    
    async def provision_tenant(self, tenant_spec: TenantSpec) -> Tenant:
        # 1. Create tenant record
        tenant = await self.tenant_repo.create(tenant_spec)
        
        # 2. Create database schema (pooled: RLS policy; silo: new schema)
        await self.db_provisioner.create_tenant_schema(tenant.id)
        
        # 3. Create cache namespace
        await self.cache_provisioner.create_namespace(tenant.id)
        
        # 4. Create Kafka topic/partition mapping
        await self.kafka_provisioner.assign_partitions(tenant.id)
        
        # 5. Create storage bucket/prefix
        await self.storage_provisioner.create_tenant_space(tenant.id)
        
        # 6. Assign encryption key
        await self.kms_provisioner.create_tenant_key(tenant.id)
        
        # 7. Deploy default policies
        await self.policy_provisioner.deploy_defaults(tenant.id)
        
        # 8. Create monitoring dashboards
        await self.monitoring_provisioner.create_tenant_dashboards(tenant.id)
        
        # 9. Register in global tenant registry
        await self.registry.register(tenant)
        
        return tenant
```

---

## 6. Data Partitioning Strategies

### 6.1 Partitioning Overview

GRC_Claw uses **three partitioning strategies** depending on data type and access pattern:

| Strategy | Data | Rationale |
|----------|------|-----------|
| **Hash partitioning** | Policies, agents, enforcement actions | Even distribution, point lookups |
| **Range partitioning** | Evidence, audit trail, metrics | Time-based queries, efficient aging |
| **List partitioning** | Tenant data (silo model) | Physical isolation per tenant |

### 6.2 Hash Partitioning

Used for entities with UUID primary keys and point-lookup access patterns.

```sql
-- PostgreSQL: Hash partitioning for policies
CREATE TABLE policies (
    id UUID NOT NULL,
    tenant_id UUID NOT NULL,
    policy_key VARCHAR(128) NOT NULL,
    -- ... other columns
    PRIMARY KEY (id, tenant_id)
) PARTITION BY HASH (tenant_id);

-- Create 16 partitions (scalable to 64)
CREATE TABLE policies_p0 PARTITION OF policies FOR VALUES WITH (MODULUS 16, REMAINDER 0);
CREATE TABLE policies_p1 PARTITION OF policies FOR VALUES WITH (MODULUS 16, REMAINDER 1);
-- ... p2 through p15
```

**Partition count selection:**

| Data Size | Partitions | When to Add |
|-----------|-----------|-------------|
| < 10M rows | 8 | — |
| 10M–100M rows | 16 | Add 8 when > 50M rows |
| 100M–1B rows | 32 | Add 16 when > 500M rows |
| > 1B rows | 64 | Add 32 when > 5B rows |

### 6.3 Range Partitioning

Used for time-series data (evidence, audit trail, metrics).

```sql
-- PostgreSQL: Range partitioning for audit trail (monthly)
CREATE TABLE audit_entries (
    id UUID NOT NULL,
    tenant_id UUID NOT NULL,
    event_type VARCHAR(64) NOT NULL,
    event_data JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (id, created_at)
) PARTITION BY RANGE (created_at);

-- Monthly partitions (automated creation)
CREATE TABLE audit_entries_2026_10 PARTITION OF audit_entries
    FOR VALUES FROM ('2026-10-01') TO ('2026-11-01');
CREATE TABLE audit_entries_2026_11 PARTITION OF audit_entries
    FOR VALUES FROM ('2026-11-01') TO ('2026-12-01');
-- ... auto-created by pg_cron

-- TimescaleDB: Hypertable for evidence metrics
SELECT create_hypertable('evidence_metrics', 'time',
    chunk_time_interval => INTERVAL '7 days',
    partitioning_column => 'tenant_id',
    number_partitions => 16
);
```

**Partition lifecycle:**

| Age | Tier | Storage | Query Performance |
|-----|------|---------|-------------------|
| 0–30 days | Hot | SSD (NVMe) | < 10 ms |
| 30–90 days | Warm | SSD (SATA) | < 50 ms |
| 90–365 days | Cold | Object storage (S3) | < 500 ms |
| 1–7 years | Archive | Glacier / cold storage | < 5 seconds |
| > 7 years | Purge | Deleted (per retention policy) | N/A |

### 6.4 List Partitioning (Silo Model)

For dedicated-tenant deployments, data is physically isolated:

```sql
-- Each tenant gets a dedicated schema
CREATE SCHEMA tenant_acme_corp;
CREATE SCHEMA tenant_globex_inc;

-- Tables created per tenant schema
CREATE TABLE tenant_acme_corp.policies (LIKE public.policies INCLUDING ALL);
CREATE TABLE tenant_globex_inc.policies (LIKE public.policies INCLUDING ALL);
```

### 6.5 Cross-Partition Queries

Cross-partition queries are **avoided in the enforcement path** (p99 < 10 ms). They are permitted only in analytics and reporting:

```python
class CrossPartitionQuery:
    """Execute a query across all partitions with fan-out."""
    
    async def execute(self, query: str, params: dict) -> QueryResult:
        # 1. Determine relevant partitions
        partition_ids = self.partitioner.resolve(query, params)
        
        # 2. Fan-out to all relevant partitions in parallel
        tasks = [
            self.execute_on_partition(pid, query, params)
            for pid in partition_ids
        ]
        results = await asyncio.gather(*tasks)
        
        # 3. Merge and sort results
        merged = self.merge_results(results, query.order_by)
        
        # 4. Apply limit/offset
        return merged.offset(query.offset).limit(query.limit)
```

### 6.6 Data Residency

For global deployments, data residency is enforced at the partition level:

```yaml
# Tenant data residency configuration
tenant:
  id: "tenant-acme-eu"
  data_residency: "EU"
  allowed_regions: ["eu-west-1", "eu-central-1"]
  encryption:
    key_store: "aws-kms:eu-west-1"
    key_id: "arn:aws:kms:eu-west-1:123456789:key/abc-123"
  storage:
    primary: "s3://grc-claw-eu-primary/"
    replica: "s3://grc-claw-eu-replica/"
  database:
    primary: "postgres://grc-claw-eu.db.internal:5432"
    read_replicas: ["postgres://grc-claw-eu-ro1.db.internal:5432"]
```

### 6.7 Consistent Hashing for Sharding

For dynamic shard membership (adding/removing shards without full rebalancing), GRC_Claw uses consistent hashing with virtual nodes:

```python
import hashlib
from bisect import bisect_right

class ConsistentHashRing:
    """Consistent hash ring with virtual nodes for shard assignment."""
    
    def __init__(self, replicas: int = 150):
        self.replicas = replicas
        self.ring = {}  # hash -> node
        self.sorted_keys = []
        self.nodes = set()
    
    def add_node(self, node: str):
        """Add a node to the ring with virtual replicas."""
        self.nodes.add(node)
        for i in range(self.replicas):
            key = self._hash(f"{node}:{i}")
            self.ring[key] = node
        self.sorted_keys = sorted(self.ring.keys())
    
    def remove_node(self, node: str):
        """Remove a node and its replicas from the ring."""
        self.nodes.discard(node)
        for i in range(self.replicas):
            key = self._hash(f"{node}:{i}")
            del self.ring[key]
        self.sorted_keys = sorted(self.ring.keys())
    
    def get_node(self, key: str) -> str:
        """Get the node responsible for a given key."""
        if not self.ring:
            return None
        hash_key = self._hash(key)
        idx = bisect_right(self.sorted_keys, hash_key) % len(self.sorted_keys)
        return self.ring[self.sorted_keys[idx]]
    
    def get_nodes(self, key: str, n: int = 3) -> list:
        """Get n distinct nodes for replication."""
        if not self.ring:
            return []
        nodes = []
        hash_key = self._hash(key)
        idx = bisect_right(self.sorted_keys, hash_key)
        while len(nodes) < n and len(nodes) < len(self.nodes):
            node = self.ring[self.sorted_keys[idx % len(self.sorted_keys)]]
            if node not in nodes:
                nodes.append(node)
            idx += 1
        return nodes
    
    @staticmethod
    def _hash(key: str) -> int:
        return int(hashlib.md5(key.encode()).hexdigest(), 16)
```

**Sharding strategy comparison:**

| Strategy | Rebalance Cost | Data Movement | Use Case |
|----------|---------------|---------------|----------|
| Hash modulo | High (full remap) | All data | Static shard count |
| Consistent hashing | Low (1/N keys) | Only adjacent keys | Dynamic shard membership |
| Range-based | Medium | Range boundaries | Time-series, ordered data |
| Directory-based | Low | Lookup table only | Complex routing logic |

### 6.8 Directory-Based Sharding

For complex routing logic (e.g., tenant tier, data residency, compliance requirements), a directory service maps shard keys to physical shards:

```python
class ShardDirectory:
    """Directory-based shard resolver with caching."""
    
    def __init__(self, backend: ShardDirectoryBackend):
        self.backend = backend
        self.cache = LRUCache(max_size=10000, ttl_seconds=30)
    
    async def resolve_shard(self, shard_key: str, context: ShardContext) -> ShardAssignment:
        """Resolve a shard key to a physical shard."""
        cache_key = f"{shard_key}:{context.tenant_tier}:{context.data_residency}"
        
        # Check cache first
        if cached := self.cache.get(cache_key):
            return cached
        
        # Resolve via directory service
        assignment = await self.backend.lookup(
            shard_key=shard_key,
            tenant_tier=context.tenant_tier,
            data_residency=context.data_residency,
            required_capabilities=context.required_capabilities,
        )
        
        # Cache the assignment
        self.cache.put(cache_key, assignment)
        return assignment
    
    async def rebalance(self, old_shards: list[str], new_shards: list[str]):
        """Gradually migrate data from old shards to new shards."""
        # 1. Update directory to point new writes to new shards
        await self.backend.update_routing_table(new_shards)
        
        # 2. Migrate existing data in background
        for shard_key in await self.backend.get_keys_for_shards(old_shards):
            await self._migrate_key(shard_key, old_shards, new_shards)
        
        # 3. Verify consistency
        await self._verify_migration(old_shards)
        
        # 4. Remove old shards
        await self.backend.remove_shards(old_shards)
```

### 6.9 Shard Splitting and Merging

```python
class ShardLifecycleManager:
    """Automated shard splitting and merging based on size and load."""
    
    SPLIT_THRESHOLD_GB = 500
    MERGE_THRESHOLD_GB = 50
    MAX_SHARD_SIZE_GB = 1000
    
    async def evaluate_shards(self):
        """Periodically evaluate all shards for split/merge candidates."""
        for shard in await self.shard_registry.get_all_shards():
            metrics = await self.metrics_collector.get_shard_metrics(shard.id)
            
            if metrics.size_gb > self.SPLIT_THRESHOLD_GB:
                await self.split_shard(shard)
            elif metrics.size_gb < self.MERGE_THRESHOLD_GB:
                merge_candidate = await self.find_merge_candidate(shard)
                if merge_candidate:
                    await self.merge_shards(shard, merge_candidate)
    
    async def split_shard(self, shard: Shard):
        """Split a shard into two at the median key."""
        # 1. Create new shard
        new_shard = await self.shard_registry.create_shard(
            region=shard.region,
            tier=shard.tier,
        )
        
        # 2. Determine split point
        median_key = await self._find_median_key(shard)
        
        # 3. Copy data >= median_key to new shard
        await self._copy_data_range(shard, new_shard, median_key, None)
        
        # 4. Update directory
        await self.directory.add_shard(new_shard, split_point=median_key)
        
        # 5. Delete migrated data from old shard
        await self._delete_data_range(shard, median_key, None)
        
        # 6. Verify consistency
        await self._verify_split(shard, new_shard, median_key)
```

---

## 7. Load Balancing

### 7.1 Load Balancing Layers

GRC_Claw uses a **three-tier load balancing** architecture:

```
┌─────────────────────────────────────────────────────────────────────┐
│  Tier 1: Global Server Load Balancing (GSLB)                        │
│                                                                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                │
│  │  us-east-1  │  │  eu-west-1  │  │  ap-south-1 │                │
│  │  (primary)  │  │  (replica)  │  │  (replica)  │                │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘                │
│         │                │                │                        │
│         └────────────────┼────────────────┘                        │
│                          │                                         │
│                   ┌──────▼──────┐                                  │
│                   │   GeoDNS    │  (Route 53 / Cloudflare)         │
│                   │  + Anycast  │                                  │
│                   └─────────────┘                                  │
└─────────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────────┐
│  Tier 2: Regional Load Balancing (L7)                               │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │              Ingress Controller (NGINX / Traefik)            │   │
│  │                                                             │   │
│  │  • TLS termination                                          │   │
│  │  • JWT validation                                           │   │
│  │  • Rate limiting (per tenant)                               │   │
│  │  • Request routing (by path, header, tenant)                 │   │
│  │  • Circuit breaker                                          │   │
│  └──────────────────────────┬──────────────────────────────────┘   │
│                             │                                       │
│  ┌──────────────────────────▼──────────────────────────────────┐   │
│  │              Service Mesh (Istio / Linkerd)                  │   │
│  │                                                             │   │
│  │  • mTLS between services                                    │   │
│  │  • Traffic splitting (canary, blue-green)                   │   │
│  │  • Retry + timeout policies                                 │   │
│  │  • Outlier detection (eject unhealthy pods)                 │   │
│  │  • Load balancing: least-request (default)                  │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────────┐
│  Tier 3: Data Layer Load Balancing                                  │
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │
│  │ PgBouncer    │  │ Redis        │  │ Kafka        │            │
│  │ (connection  │  │ Cluster      │  │ Consumer     │            │
│  │  pooling)    │  │ (sharding)   │  │ Group        │            │
│  └──────────────┘  └──────────────┘  └──────────────┘            │
└─────────────────────────────────────────────────────────────────────┘
```

### 7.2 Load Balancing Algorithms

| Component | Algorithm | Rationale |
|-----------|-----------|-----------|
| **PEP (MCP Gateway)** | Least-connections | Long-lived agent connections; prevents hot-spotting |
| **PDP (OPA)** | Round-robin with cache affinity | Route to PDP with cached policies for the requesting agent |
| **Evidence Collector** | Partition-based (Kafka consumer group) | Each partition consumed by exactly one consumer |
| **API Gateway** | Weighted round-robin | Support canary deployments and A/B testing |
| **Database** | PgBouncer transaction pooling | Efficient connection reuse; no session affinity needed |
| **Redis** | Cluster sharding | Keys hashed to slots; automatic rebalancing |

### 7.3 Health Checking & Failover

```yaml
# Kubernetes readiness and liveness probes
readinessProbe:
  httpGet:
    path: /health/ready
    port: 8080
  initialDelaySeconds: 10
  periodSeconds: 5
  failureThreshold: 3

livenessProbe:
  httpGet:
    path: /health/live
    port: 8080
  initialDelaySeconds: 30
  periodSeconds: 10
  failureThreshold: 3

# Istio outlier detection
outlierDetection:
  consecutive5xxErrors: 5
  interval: 30s
  baseEjectionTime: 30s
  maxEjectionPercent: 50
```

**Failover behavior:**

| Failure | Detection | Action | Recovery |
|---------|-----------|--------|----------|
| PEP pod unhealthy | Readiness probe fails (3x) | Remove from service endpoint | Auto-restart, rejoin when healthy |
| PDP pod unhealthy | Readiness probe fails (3x) | Remove from service endpoint | Auto-restart, rejoin when healthy |
| PostgreSQL primary fails | Patroni health check | Promote replica (< 10 seconds) | Auto-reconfigure |
| Redis node fails | Cluster health check | Promote replica (< 5 seconds) | Auto-rebalance |
| Kafka broker fails | Controller election | Reassign partitions (< 30 seconds) | Auto-rebalance |
| Region failure | GSLB health check | DNS failover to replica region (< 60 seconds) | Manual or auto-recovery |

### 7.4 Rate Limiting

Rate limiting is enforced at multiple layers:

```yaml
# Istio rate limiting (per tenant)
apiVersion: networking.istio.io/v1beta1
kind: EnvoyFilter
metadata:
  name: tenant-rate-limit
spec:
  configPatches:
    - applyTo: HTTP_FILTER
      match:
        context: SIDECAR_INBOUND
      patch:
        operation: INSERT_BEFORE
        value:
          name: envoy.filters.http.local_ratelimit
          typed_config:
            "@type": type.googleapis.com/udpa.type.v1.TypedStruct
            type_url: type.googleapis.com/envoy.extensions.filters.http.local_ratelimit.v3.LocalRateLimit
            value:
              stat_prefix: http_local_rate_limiter
              token_bucket:
                max_tokens: 1000
                tokens_per_fill: 1000
                fill_interval: 1s
              filter_enabled:
                runtime_key: local_rate_limit_enabled
                default_value:
                  numerator: 100
                  denominator: HUNDRED
              filter_enforced:
                runtime_key: local_rate_limit_enforced
                default_value:
                  numerator: 100
                  denominator: HUNDRED
              response_headers_to_add:
                - append_action: OVERWRITE_IF_EXISTS_OR_ADD
                  header:
                    key: x-rate-limit-remaining
                    value: "%DYNAMIC_METADATA(envoy.filters.http.local_ratelimit:remaining)%"
```

**Rate limit tiers:**

| Tier | Requests/min | Decisions/sec | Burst |
|------|-------------|---------------|-------|
| Free | 100 | 10 | 50 |
| Team | 1,000 | 100 | 500 |
| Department | 10,000 | 1,000 | 5,000 |
| Enterprise | 100,000 | 10,000 | 50,000 |
| Global | 1,000,000 | 100,000 | 500,000 |

### 7.5 Rate Limiting Algorithms

GRC_Claw implements three rate limiting algorithms, each suited to different traffic patterns:

#### Algorithm 1: Token Bucket (Default)

Allows bursts up to a maximum while maintaining a steady-state rate:

```python
class TokenBucketRateLimiter:
    """Token bucket rate limiter with Redis backend."""
    
    def __init__(self, redis: RedisCluster):
        self.redis = redis
    
    async def is_allowed(self, key: str, rate: float, burst: int) -> RateLimitResult:
        """Check if a request is allowed under the rate limit.
        
        Args:
            key: Rate limit bucket key (e.g., "tenant:abc:decisions")
            rate: Sustained rate (tokens per second)
            burst: Maximum bucket size (maximum burst)
        """
        now = time.time()
        bucket_key = f"ratelimit:{key}"
        
        pipe = self.redis.pipeline()
        pipe.hgetall(bucket_key)
        result = await pipe.execute()
        
        bucket = result[0] if result[0] else {}
        tokens = float(bucket.get("tokens", burst))
        last_refill = float(bucket.get("last_refill", now))
        
        # Refill tokens based on elapsed time
        elapsed = now - last_refill
        tokens = min(burst, tokens + elapsed * rate)
        
        if tokens >= 1:
            # Consume one token
            tokens -= 1
            await self.redis.hset(bucket_key, mapping={
                "tokens": tokens,
                "last_refill": now,
            })
            await self.redis.expire(bucket_key, 60)
            return RateLimitResult(allowed=True, remaining=int(tokens))
        else:
            # Not enough tokens
            retry_after = (1 - tokens) / rate
            await self.redis.hset(bucket_key, mapping={
                "tokens": tokens,
                "last_refill": now,
            })
            return RateLimitResult(allowed=False, retry_after=retry_after)
```

#### Algorithm 2: Sliding Window Log

Provides precise rate limiting without burst allowance:

```python
class SlidingWindowRateLimiter:
    """Sliding window log rate limiter."""
    
    def __init__(self, redis: RedisCluster):
        self.redis = redis
    
    async def is_allowed(self, key: str, limit: int, window_seconds: int) -> RateLimitResult:
        """Check if request is allowed within the sliding window."""
        now = time.time()
        window_start = now - window_seconds
        log_key = f"ratelimit:sw:{key}"
        
        pipe = self.redis.pipeline()
        # Remove entries outside the window
        pipe.zremrangebyscore(log_key, 0, window_start)
        # Count entries in current window
        pipe.zcard(log_key)
        result = await pipe.execute()
        
        current_count = result[1]
        
        if current_count < limit:
            # Add current request to the window
            await self.redis.zadd(log_key, {str(now): now})
            await self.redis.expire(log_key, window_seconds + 1)
            return RateLimitResult(allowed=True, remaining=limit - current_count - 1)
        else:
            # Window is full — calculate retry after
            oldest = await self.redis.zrange(log_key, 0, 0, withscores=True)
            retry_after = oldest[0][1] + window_seconds - now if oldest else window_seconds
            return RateLimitResult(allowed=False, retry_after=retry_after)
```

#### Algorithm 3: Fixed Window Counter

Simplest algorithm — suitable for coarse-grained limits:

```python
class FixedWindowRateLimiter:
    """Fixed window counter rate limiter."""
    
    def __init__(self, redis: RedisCluster):
        self.redis = redis
    
    async def is_allowed(self, key: str, limit: int, window_seconds: int) -> RateLimitResult:
        """Check if request is allowed within the fixed window."""
        window_key = f"ratelimit:fw:{key}:{int(time.time() // window_seconds)}"
        
        current = await self.redis.incr(window_key)
        if current == 1:
            await self.redis.expire(window_key, window_seconds + 1)
        
        if current <= limit:
            return RateLimitResult(allowed=True, remaining=limit - current)
        else:
            ttl = await self.redis.ttl(window_key)
            return RateLimitResult(allowed=False, retry_after=ttl)
```

**Algorithm comparison:**

| Algorithm | Burst Handling | Memory | Precision | Use Case |
|-----------|---------------|--------|-----------|----------|
| Token bucket | Configurable | O(1) | High | General-purpose, API rate limits |
| Sliding window log | No bursts | O(n) | Very high | Strict compliance limits |
| Fixed window | 2x burst at boundary | O(1) | Low | Coarse-grained, high-volume |

### 7.6 Multi-Level Rate Limiting

Rate limiting is enforced at multiple levels simultaneously:

```
┌─────────────────────────────────────────────────────────────┐
│  Level 1: Edge (Cloudflare / AWS WAF)                       │
│  • DDoS protection                                          │
│  • IP-based blocking                                        │
│  • Geographic restrictions                                  │
│  • Limit: 10,000 req/s per IP                              │
├─────────────────────────────────────────────────────────────┤
│  Level 2: API Gateway (Kong / Envoy)                        │
│  • Per-tenant rate limits                                   │
│  • Per-endpoint rate limits                                 │
│  • API key validation                                       │
│  • Limit: 100,000 req/min per tenant                        │
├─────────────────────────────────────────────────────────────┤
│  Level 3: Service Mesh (Istio)                              │
│  • Per-service rate limits                                  │
│  • Per-agent rate limits                                    │
│  • Circuit breaker integration                              │
│  • Limit: 10,000 decisions/sec per agent                    │
├─────────────────────────────────────────────────────────────┤
│  Level 4: Application (PEP)                                 │
│  • Per-agent-action rate limits                             │
│  • Per-policy evaluation limits                             │
│  • Queue-based throttling                                   │
│  • Limit: 100 decisions/sec per agent-action                │
└─────────────────────────────────────────────────────────────┘
```

### 7.7 Throttling Strategies

When rate limits are exceeded, GRC_Claw applies throttling based on request priority:

```python
class PriorityThrottler:
    """Throttle requests based on priority and system load."""
    
    PRIORITY_LEVELS = {
        "enforcement": 0,      # Highest — never throttled
        "policy_read": 1,      # High — throttled only under extreme load
        "evidence_write": 2,   # Medium — throttled under high load
        "audit_query": 3,      # Low — throttled under moderate load
        "analytics": 4,        # Lowest — throttled first
    }
    
    THROTTLE_THRESHOLDS = {
        0: 0.0,    # Never throttled
        1: 0.95,   # Throttle when system > 95% capacity
        2: 0.80,   # Throttle when system > 80% capacity
        3: 0.60,   # Throttle when system > 60% capacity
        4: 0.40,   # Throttle when system > 40% capacity
    }
    
    async def should_throttle(self, priority: str, system_load: float) -> bool:
        """Determine if a request should be throttled."""
        level = self.PRIORITY_LEVELS.get(priority, 4)
        threshold = self.THROTTLE_THRESHOLDS.get(level, 0.0)
        return system_load > threshold
    
    async def throttle_response(self, priority: str, system_load: float) -> ThrottleDecision:
        """Determine throttling action for a request."""
        if not await self.should_throttle(priority, system_load):
            return ThrottleDecision(action="allow")
        
        level = self.PRIORITY_LEVELS.get(priority, 4)
        
        if level <= 1:
            # High priority — queue with timeout
            return ThrottleDecision(
                action="queue",
                queue_timeout_ms=5000,
                retry_after_ms=100,
            )
        elif level == 2:
            # Medium priority — shed load with retry hint
            return ThrottleDecision(
                action="shed",
                retry_after_ms=1000,
                status_code=503,
            )
        else:
            # Low priority — reject immediately
            return ThrottleDecision(
                action="reject",
                retry_after_ms=5000,
                status_code=429,
            )
```

### 7.8 Rate Limit Headers and Client Communication

Every rate-limited response includes standard headers:

```http
HTTP/1.1 429 Too Many Requests
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1696165200
X-RateLimit-Retry-After: 30
Retry-After: 30
Content-Type: application/json

{
  "error": "rate_limit_exceeded",
  "message": "Rate limit exceeded. Retry after 30 seconds.",
  "limit": 1000,
  "remaining": 0,
  "reset_at": "2026-10-01T12:00:00Z",
  "retry_after": 30
}
```

---

## 8. Caching Strategy

### 8.1 Cache Hierarchy

```
┌─────────────────────────────────────────────────────────────┐
│  L1: In-Memory (per instance)                               │
│  • Compiled policies (LRU, 10K entries)                     │
│  • Agent identities (LRU, 5K entries)                       │
│  • Decision cache (LRU, 50K entries, 5-min TTL)             │
│  • Hit rate target: > 80%                                   │
│  • Latency: < 0.1 ms                                        │
├─────────────────────────────────────────────────────────────┤
│  L2: Redis Cluster (shared)                                 │
│  • Agent context (5-min TTL)                                │
│  • Policy bundles (15-min TTL)                              │
│  • Decision cache (5-min TTL)                               │
│  • Rate limit counters (1-min TTL)                          │
│  • Hit rate target: > 95%                                   │
│  • Latency: < 1 ms                                          │
├─────────────────────────────────────────────────────────────┤
│  L3: PostgreSQL (source of truth)                           │
│  • Policies, agents, evidence, audit                        │
│  • Latency: < 10 ms (indexed)                               │
└─────────────────────────────────────────────────────────────┘
```

### 8.2 Cache Invalidation

| Event | Invalidation | Propagation |
|-------|-------------|-------------|
| Policy updated | L1 + L2 policy cache | Kafka event → all instances purge local cache |
| Agent modified | L1 + L2 agent cache | Kafka event → all instances purge local cache |
| Decision TTL expired | L2 decision cache | Automatic (Redis TTL) |
| Tenant suspended | All L1 + L2 caches for tenant | Kafka event → all instances purge tenant keys |
| Regional failover | L1 caches (new region) | Warm-up from L2 on startup |

### 8.3 Decision Cache Key Design

```python
def decision_cache_key(agent_id: str, action: str, resource: str, context_hash: str) -> str:
    """Create a deterministic cache key for enforcement decisions."""
    # Normalize context to stable hash
    normalized = f"{agent_id}:{action}:{resource}:{context_hash}"
    return f"decision:{hashlib.sha256(normalized.encode()).hexdigest()[:32]}"
```

### 8.4 Cache Invalidation Patterns

GRC_Claw uses four cache invalidation patterns depending on data change frequency and consistency requirements:

#### Pattern 1: TTL-Based Invalidation (Default)

For data that can tolerate brief staleness:

```python
class TTLCache:
    """TTL-based cache with automatic expiration."""
    
    TTL_STRATEGY = {
        "decision": 300,        # 5 minutes
        "agent_context": 300,   # 5 minutes
        "policy_bundle": 900,   # 15 minutes
        "rate_limit": 60,       # 1 minute
        "session": 1800,        # 30 minutes
    }
    
    def get(self, key: str) -> Optional[Any]:
        entry = self.redis.get(key)
        if entry is None:
            return None
        
        value, expires_at = entry
        if time.time() > expires_at:
            self.redis.delete(key)
            return None
        
        return value
```

#### Pattern 2: Write-Through Invalidation

For data that must be immediately consistent:

```python
class WriteThroughCache:
    """Invalidate cache on every write."""
    
    async def update_policy(self, policy_id: str, new_policy: Policy):
        # 1. Update database (source of truth)
        await self.db.policies.update(policy_id, new_policy)
        
        # 2. Invalidate L1 caches on all instances via pub/sub
        await self.redis.publish("cache:invalidate", json.dumps({
            "type": "policy",
            "id": policy_id,
            "timestamp": time.time(),
        }))
        
        # 3. Update L2 cache
        await self.redis.set(
            f"policy:{policy_id}",
            new_policy.serialize(),
            ex=self.TTL_STRATEGY["policy_bundle"],
        )
    
    async def handle_invalidation_message(self, message: dict):
        """Handle cache invalidation from pub/sub."""
        if message["type"] == "policy":
            # Invalidate local L1 cache
            self.local_cache.delete(f"policy:{message['id']}")
        elif message["type"] == "agent":
            self.local_cache.delete(f"agent:{message['id']}")
        elif message["type"] == "tenant":
            # Invalidate all tenant-specific keys
            self.local_cache.delete_pattern(f"tenant:{message['id']}:*")
```

#### Pattern 3: Version-Based Invalidation

For high-contention data where TTL alone is insufficient:

```python
class VersionedCache:
    """Cache with version-based invalidation."""
    
    async def get_with_version(self, key: str) -> Optional[CachedValue]:
        cached = self.redis.hgetall(f"cache:{key}")
        if not cached:
            return None
        
        # Check if version is still current
        current_version = await self.redis.get(f"version:{key}")
        if current_version != cached["version"]:
            # Stale — delete and return None
            self.redis.delete(f"cache:{key}")
            return None
        
        return CachedValue(
            data=cached["data"],
            version=cached["version"],
        )
    
    async def set_with_version(self, key: str, data: Any):
        """Set cache value with a new version."""
        version = str(uuid.uuid4())
        pipe = self.redis.pipeline()
        pipe.hset(f"cache:{key}", mapping={
            "data": serialize(data),
            "version": version,
        })
        pipe.set(f"version:{key}", version)
        pipe.expire(f"cache:{key}", self.TTL)
        pipe.expire(f"version:{key}", self.TTL)
        await pipe.execute()
```

#### Pattern 4: Cache-Aside with Eventual Consistency

For read-heavy, write-rare data:

```python
class CacheAsideManager:
    """Cache-aside pattern with async invalidation."""
    
    async def get(self, key: str) -> Optional[Any]:
        # 1. Try cache
        if cached := await self.redis.get(key):
            return deserialize(cached)
        
        # 2. Cache miss — load from database
        value = await self.db.get(key)
        if value is None:
            return None
        
        # 3. Populate cache
        await self.redis.set(key, serialize(value), ex=self.TTL)
        return value
    
    async def invalidate(self, key: str):
        """Invalidate a cache key and all related keys."""
        # Delete primary key
        await self.redis.delete(key)
        
        # Delete related keys (e.g., list views, aggregations)
        related_keys = await self._find_related_keys(key)
        if related_keys:
            await self.redis.delete(*related_keys)
        
        # Publish invalidation event for L1 caches
        await self.redis.publish("cache:invalidate", json.dumps({
            "key": key,
            "related": related_keys,
            "timestamp": time.time(),
        }))
```

### 8.5 Cache Warming Strategies

```python
class CacheWarmer:
    """Proactive cache warming for predictable load patterns."""
    
    async def warm_policy_cache(self, tenant_id: str):
        """Pre-load all policies for a tenant into cache."""
        policies = await self.db.policies.get_by_tenant(tenant_id)
        pipe = self.redis.pipeline()
        for policy in policies:
            key = f"tenant:{tenant_id}:policy:{policy.id}"
            pipe.set(key, policy.serialize(), ex=900)
        await pipe.execute()
    
    async def warm_agent_cache(self, agent_ids: list[str]):
        """Pre-load agent contexts for scheduled agent runs."""
        agents = await self.db.agents.get_by_ids(agent_ids)
        pipe = self.redis.pipeline()
        for agent in agents:
            key = f"agent:{agent.id}:context"
            pipe.set(key, agent.context.serialize(), ex=300)
        await pipe.execute()
    
    async def warm_on_scale_out(self, new_instance_id: str):
        """Warm cache when a new instance joins the cluster."""
        # Load compiled policies
        policies = await self.db.policies.get_active()
        for policy in policies:
            self.local_cache.put(f"policy:{policy.id}", policy.compiled_rules)
        
        # Load agent identities
        agents = await self.db.agents.get_active()
        for agent in agents:
            self.local_cache.put(f"agent:{agent.id}", agent.identity)
```

### 8.6 Cache Consistency Guarantees

| Data Type | Consistency Model | Invalidation Pattern | Staleness Window |
|-----------|-------------------|---------------------|------------------|
| Enforcement policies | Strong | Write-through + pub/sub | 0 ms |
| Agent identities | Strong | Write-through + pub/sub | 0 ms |
| Decision cache | Eventual | TTL-based | 5 min |
| Agent context | Eventual | TTL-based | 5 min |
| Rate limit counters | Eventual | TTL-based | 1 min |
| Session data | Eventual | TTL-based | 30 min |
| Analytics/aggregates | Eventual | TTL-based + scheduled refresh | 15 min |

---

## 9. Auto-Scaling Policies

### 9.1 Component Scaling Matrix

| Component | Scale Metric | Scale Out Trigger | Scale In Trigger | Min | Max | Cool-down |
|-----------|-------------|-------------------|-------------------|-----|-----|-----------|
| PEP | CPU > 70% or p99 > 15ms | 5 min | 10 min | 2 | 100 | 60s up / 300s down |
| PDP | CPU > 70% or eval queue > 1K | 5 min | 10 min | 2 | 50 | 60s up / 300s down |
| Evidence Collector | Consumer lag > 10K | 5 min | 15 min | 2 | 96 | 120s up / 600s down |
| Audit Writer | Write latency p99 > 20ms | 3 min | 10 min | 2 | 32 | 60s up / 300s down |
| API Gateway | CPU > 70% or p99 > 200ms | 5 min | 10 min | 2 | 50 | 60s up / 300s down |
| PostgreSQL | Connection count > 80% | N/A (vertical) | N/A | 1 | 1 primary + 5 replicas | N/A |
| Redis | Memory > 80% | N/A (add shards) | N/A | 3 | 30 shards | N/A |

### 9.2 Predictive Scaling

For known patterns (e.g., business hours, scheduled agent runs), GRC_Claw supports predictive scaling:

```yaml
# Scheduled scaling policy
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: grc-pep-predictive
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: grc-pep-gateway
  minReplicas: 2
  maxReplicas: 100
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
  # Scale up before business hours
  # Scale down after business hours
  # Based on historical traffic patterns
```

### 9.3 Scale-to-Zero (Non-Production)

For development and staging environments, non-critical components can scale to zero:

```yaml
# KEDA scaled object for evidence collectors
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: grc-evidence-collector-scaler
spec:
  scaleTargetRef:
    name: grc-evidence-collector
  minReplicaCount: 0  # Scale to zero
  maxReplicaCount: 96
  triggers:
    - type: kafka
      metadata:
        bootstrapServers: kafka:9092
        consumerGroup: evidence-processors
        topic: evidence-events
        lagThreshold: "100"
```

### 9.4 Elasticity Patterns

GRC_Claw implements four elasticity patterns to match capacity to demand dynamically:

#### Pattern 1: Reactive Auto-Scaling (Default)

The baseline pattern — scale in response to observed metrics:

```
Metric breaches threshold → Stabilization window → Scale action → Cooldown
```

| Parameter | PEP | PDP | Evidence Collector |
|-----------|-----|-----|-------------------|
| Scale-out threshold | CPU > 70% or p99 > 15ms | CPU > 70% or queue > 1K | Lag > 10K |
| Stabilization (up) | 60s | 60s | 120s |
| Scale-in threshold | CPU < 30% and p99 < 5ms | CPU < 30% and queue < 100 | Lag < 1K |
| Stabilization (down) | 300s | 300s | 600s |
| Scale step (up) | +4 pods | +2 pods | +4 pods |
| Scale step (down) | -1 pod | -1 pod | -2 pods |
| Cooldown (up) | 60s | 60s | 120s |
| Cooldown (down) | 300s | 300s | 600s |

#### Pattern 2: Predictive Scaling

For known traffic patterns (business hours, scheduled agent runs, compliance deadlines):

```python
class PredictiveScaler:
    """Pre-scale based on historical traffic patterns."""
    
    def __init__(self, metrics_store: TimeSeriesDB, ml_model: ForecastModel):
        self.metrics = metrics_store
        self.model = ml_model
    
    async def forecast_demand(self, horizon_minutes: int = 30) -> DemandForecast:
        """Forecast demand for the next N minutes."""
        # Get historical traffic for the same time window
        historical = await self.metrics.query(
            metric="enforcement_decisions_per_second",
            lookback_days=30,
            time_of_day=datetime.now().time(),
        )
        
        # Apply forecasting model
        forecast = self.model.predict(
            historical,
            horizon=horizon_minutes,
            confidence_interval=0.95,
        )
        
        return DemandForecast(
            expected_rps=forecast.mean,
            peak_rps=forecast.p95,
            confidence=forecast.confidence,
        )
    
    async def pre_scale(self, forecast: DemandForecast):
        """Pre-scale components before demand arrives."""
        required_peps = math.ceil(forecast.peak_rps / 10000)  # 10K per PEP
        required_pdps = math.ceil(forecast.peak_rps / 5000)   # 5K per PDP
        
        # Scale 15 minutes before predicted peak
        await self.kubernetes.scale_deployment(
            name="grc-pep-gateway",
            replicas=required_peps,
            grace_period_seconds=300,  # 5 min warm-up
        )
```

#### Pattern 3: Event-Driven Scaling

For discrete events that cause known load spikes:

| Event | Trigger | Action | Lead Time |
|-------|---------|--------|-----------|
| Policy deployment | Policy change event | Pre-warm PDP cache | 30s before |
| Scheduled agent run | Cron trigger | Scale PEP + PDP | 5 min before |
| Compliance deadline | Calendar event | Scale evidence pipeline | 1 hour before |
| Tenant onboarding | Tenant provision event | Allocate dedicated capacity | Immediate |
| Security incident | Alert trigger | Scale audit + evidence | Immediate |

```yaml
# KEDA ScaledObject for event-driven scaling
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: grc-pep-event-scaler
spec:
  scaleTargetRef:
    name: grc-pep-gateway
  minReplicas: 2
  maxReplicas: 100
  triggers:
    # Scale on Kafka lag
    - type: kafka
      metadata:
        bootstrapServers: kafka:9092
        consumerGroup: enforcement-requests
        topic: enforcement-requests
        lagThreshold: "500"
    # Scale on custom metric
    - type: prometheus
      metadata:
        serverAddress: http://prometheus:9090
        metricName: grc_enforcement_queue_depth
        threshold: "1000"
        query: sum(grc_enforcement_queue_depth)
    # Scale on cron schedule
    - type: cron
      metadata:
        timezone: America/New_York
        start: 0 8 * * 1-5    # 8 AM weekdays
        end: 0 18 * * 1-5     # 6 PM weekdays
        desiredReplicas: "10"
```

#### Pattern 4: Scale-to-Zero (Non-Production)

For development and staging environments:

```yaml
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: grc-evidence-collector-zero-scaler
spec:
  scaleTargetRef:
    name: grc-evidence-collector
  minReplicaCount: 0
  maxReplicaCount: 96
  cooldownPeriod: 300  # 5 min before scaling to zero
  triggers:
    - type: kafka
      metadata:
        bootstrapServers: kafka:9092
        consumerGroup: evidence-processors
        topic: evidence-events
        lagThreshold: "100"
    - type: cron
      metadata:
        timezone: America/New_York
        start: 0 18 * * 1-5    # 6 PM weekdays
        end: 0 8 * * 1-5      # 8 AM weekdays
        desiredReplicas: "0"
```

### 9.5 Multi-Dimensional Scaling

Components scale on multiple signals simultaneously:

```python
class MultiDimensionalScaler:
    """Scale based on multiple metrics with priority weighting."""
    
    SIGNALS = {
        "cpu": {"weight": 0.3, "scale_out_threshold": 70, "scale_in_threshold": 30},
        "memory": {"weight": 0.2, "scale_out_threshold": 80, "scale_in_threshold": 40},
        "latency_p99": {"weight": 0.3, "scale_out_threshold_ms": 15, "scale_in_threshold_ms": 5},
        "queue_depth": {"weight": 0.2, "scale_out_threshold": 1000, "scale_in_threshold": 100},
    }
    
    def compute_desired_replicas(self, current: int, metrics: dict) -> int:
        """Compute desired replica count from multiple signals."""
        scale_out_score = 0
        scale_in_score = 0
        
        for signal, config in self.SIGNALS.items():
            value = metrics.get(signal)
            if value is None:
                continue
            
            if value > config["scale_out_threshold"]:
                scale_out_score += config["weight"]
            elif value < config["scale_in_threshold"]:
                scale_in_score += config["weight"]
        
        if scale_out_score >= 0.5:
            return min(current + self._step(scale_out_score), self.max_replicas)
        elif scale_in_score >= 0.5:
            return max(current - self._step(scale_in_score), self.min_replicas)
        
        return current
```

---

## 10. Capacity Planning

### 10.1 Growth Projections

| Metric | Tier 1 | Tier 2 | Tier 3 | Tier 4 |
|--------|--------|--------|--------|--------|
| Agents | 50 | 500 | 5,000 | 50,000 |
| Decisions/sec | 1,000 | 10,000 | 50,000 | 200,000 |
| Evidence items/day | 100K | 10M | 100M | 1B |
| Audit entries/day | 500K | 50M | 500M | 5B |
| Storage (audit) | 10 GB | 500 GB | 5 TB | 50 TB |
| PEP instances | 1 | 4 | 24 | 200 |
| PDP instances | 1 | 2 | 12 | 100 |
| Evidence collectors | 1 | 4 | 24 | 200 |
| PostgreSQL | 1 node | 1 primary + 2 replicas | Patroni HA (3+ nodes) | Multi-region Patroni |
| Redis | 1 node | 3-node cluster | 6-node cluster (3 shards) | Multi-region cluster |
| Kafka | 1 broker | 3 brokers | 6 brokers | Multi-region MM |

### 10.2 Resource per Instance

| Component | vCPU | RAM | Disk | Network |
|-----------|------|-----|------|---------|
| PEP | 2 | 4 GB | 10 GB | 1 Gbps |
| PDP | 4 | 8 GB | 20 GB | 1 Gbps |
| Evidence Collector | 2 | 4 GB | 50 GB | 1 Gbps |
| Audit Writer | 2 | 4 GB | 100 GB | 1 Gbps |
| API Gateway | 2 | 4 GB | 10 GB | 1 Gbps |
| PostgreSQL | 8 | 32 GB | 500 GB SSD | 10 Gbps |
| Redis | 4 | 16 GB | 50 GB SSD | 10 Gbps |
| Kafka | 4 | 16 GB | 200 GB SSD | 10 Gbps |

### 10.3 Cost Optimization

| Strategy | Implementation | Savings |
|----------|---------------|---------|
| Spot instances | Use spot/preemptible for evidence collectors and analytics | 60–90% compute |
| Reserved capacity | 1-year commit for baseline PEP/PDP capacity | 30–50% compute |
| Storage tiering | Auto-move cold data to object storage | 70–90% storage |
| Scale-to-zero | Non-production environments scale to zero overnight | 50–80% dev/staging |
| Right-sizing | Continuous resource utilization analysis | 20–30% overall |

---

## 11. Failure Modes & Resilience at Scale

### 11.1 Failure Domains

```
┌─────────────────────────────────────────────────────────────────────┐
│  Failure Domain 1: Single Pod                                       │
│  • Impact: Minimal — traffic routed to other pods                  │
│  • Detection: Health check (5s)                                    │
│  • Recovery: Auto-restart (< 30s)                                  │
├─────────────────────────────────────────────────────────────────────┤
│  Failure Domain 2: Single Node / Availability Zone                 │
│  • Impact: Reduced capacity — N-1 redundancy                       │
│  • Detection: Node controller (30s)                                │
│  • Recovery: Pods rescheduled to other nodes (< 2 min)             │
├─────────────────────────────────────────────────────────────────────┤
│  Failure Domain 3: Single Region                                    │
│  • Impact: Full region loss — GSLB failover                        │
│  • Detection: GSLB health check (60s)                              │
│  • Recovery: DNS failover to replica region (< 5 min)              │
├─────────────────────────────────────────────────────────────────────┤
│  Failure Domain 4: Data Corruption                                 │
│  • Impact: Data loss — backup recovery                             │
│  • Detection: Hash chain verification (async)                     │
│  • Recovery: Point-in-time restore (< 4 hours RTO)                 │
└─────────────────────────────────────────────────────────────────────┘
```

### 11.2 Circuit Breakers

```python
# Circuit breaker configuration for inter-service calls
CIRCUIT_BREAKERS = {
    "pep_to_pdp": {
        "failure_threshold": 5,        # Open after 5 consecutive failures
        "recovery_timeout": 30,        # Try half-open after 30s
        "half_open_max_calls": 3,      # Max calls in half-open state
        "success_threshold": 2,        # Close after 2 consecutive successes
    },
    "pdp_to_policy_store": {
        "failure_threshold": 3,
        "recovery_timeout": 15,
        "half_open_max_calls": 2,
        "success_threshold": 2,
    },
    "evidence_to_store": {
        "failure_threshold": 10,
        "recovery_timeout": 60,
        "half_open_max_calls": 5,
        "success_threshold": 3,
    },
}
```

### 11.3 Bulkhead Pattern

Resource isolation prevents cascade failures:

```yaml
# Kubernetes resource quotas per component
apiVersion: v1
kind: ResourceQuota
metadata:
  name: grc-pep-quota
  namespace: grc-claw
spec:
  hard:
    requests.cpu: "200"
    requests.memory: 400Gi
    pods: "100"
---
apiVersion: v1
kind: ResourceQuota
metadata:
  name: grc-pdp-quota
  namespace: grc-claw
spec:
  hard:
    requests.cpu: "100"
    requests.memory: 200Gi
    pods: "50"
```

---

## 12. Observability at Scale

### 12.1 Metrics Cardinality Management

High-cardinality metrics (per-agent, per-policy) are managed via:

| Approach | Implementation |
|----------|---------------|
| **Label limits** | Max 20 labels per metric; agent_id and policy_id are separate metrics, not labels |
| **Sampling** | 10% trace sampling for high-volume paths; 100% for enforcement decisions |
| **Aggregation** | Pre-aggregate per-agent metrics in 1-minute windows before storage |
| **Cardinality limits** | Prometheus relabeling drops high-cardinality labels beyond threshold |

### 12.2 Distributed Tracing at Scale

```
┌─────────────────────────────────────────────────────────────┐
│  Trace Sampling Strategy                                     │
│                                                             │
│  Enforcement decisions: 100% (compliance requirement)       │
│  Policy evaluations: 100%                                   │
│  Evidence collection: 10% (high volume)                     │
│  Analytics queries: 1% (low priority)                       │
│  Health checks: 0% (noise)                                  │
│                                                             │
│  Trace retention:                                           │
│  • Hot traces: 7 days (Jaeger/Tempo)                       │
│  • Cold traces: 90 days (S3/GCS)                           │
│  • Audit traces: 7 years (WORM storage)                    │
└─────────────────────────────────────────────────────────────┘
```

### 12.3 Scaling Dashboards

Three Grafana dashboards are provided:

1. **Enforcement at Scale** — Real-time decisions/sec, p99 latency, error rate, per-tenant breakdown
2. **Data Pipeline** — Evidence ingestion rate, consumer lag, storage utilization, partition health
3. **Capacity & Cost** — Resource utilization per component, cost per tenant, scaling events, forecast

---

## 13. Scalability Testing Framework

### 13.1 Testing Philosophy

Scalability testing validates that GRC_Claw meets its horizontal scaling targets under realistic load conditions. The framework covers:

- **Load testing** — Validate throughput and latency at target scale
- **Stress testing** — Find breaking points and validate graceful degradation
- **Soak testing** — Detect resource leaks and performance drift over time
- **Chaos testing** — Validate resilience under component failure
- **Scalability verification** — Confirm linear scale-out behavior

### 13.2 Test Environment

| Component | Specification |
|-----------|--------------|
| **Load generator** | k6 or Locust, distributed across 3+ nodes |
| **Test data** | Production-like: 1,000 agents, 500 policies, 5,000 rules |
| **Network** | Same-region, < 1 ms RTT between components |
| **Monitoring** | Prometheus + Grafana, 1-second scrape interval |
| **Baseline** | 1-hour warm-up, then 30-minute measurement window |
| **Metrics store** | TimescaleDB for test result storage and comparison |

### 13.3 Test Scenarios

#### Scenario 1: Steady-State Enforcement Load

- **Purpose:** Validate sustained throughput and latency under normal operating conditions
- **Load profile:** Constant 10,000 decisions/second for 30 minutes
- **Success criteria:** p99 < 10 ms, zero decision errors, zero audit write failures

#### Scenario 2: Peak Load

- **Purpose:** Validate system behavior under maximum expected load
- **Load profile:** Ramp from 0 to 25,000 decisions/second over 5 minutes, hold for 15 minutes
- **Success criteria:** p99 < 20 ms, < 0.1% decision errors, graceful degradation

#### Scenario 3: Burst Load

- **Purpose:** Validate system behavior under sudden traffic spikes
- **Load profile:** 50,000 decisions/second for 3 seconds, then 10,000/second for 5 minutes
- **Success criteria:** No dropped decisions, p99 < 50 ms during burst, recovery to < 10 ms within 30 seconds

#### Scenario 4: Scalability Test

- **Purpose:** Validate horizontal scaling behavior
- **Load profile:** Start with 1 enforcement proxy, add instances at 5-minute intervals up to 10
- **Success criteria:** Linear throughput scaling (within 15% of ideal), latency remains stable

#### Scenario 5: Soak Test

- **Purpose:** Validate long-term stability and resource leak detection
- **Load profile:** Constant 10,000 decisions/second for 72 hours
- **Success criteria:** No memory growth > 10%, no connection leaks, no file descriptor leaks, p99 latency drift < 5%

#### Scenario 6: Failure Recovery

- **Purpose:** Validate system behavior during component failure
- **Load profile:** Constant 10,000 decisions/second, kill one enforcement proxy at minute 15
- **Success criteria:** Zero decision loss, traffic rerouted within 5 seconds, p99 < 50 ms during failover

#### Scenario 7: Policy Hot-Reload

- **Purpose:** Validate policy change deployment under load
- **Load profile:** Constant 10,000 decisions/second, deploy 10 policy changes at minute 15
- **Success criteria:** All enforcement points updated within 10 seconds, zero decision errors during deployment

#### Scenario 8: Evidence Pipeline Under Load

- **Purpose:** Validate evidence collection keeps pace with enforcement decisions
- **Load profile:** Constant 10,000 decisions/second with full evidence collection enabled
- **Success criteria:** Evidence collection p99 < 200 ms, zero evidence loss, evidence store write latency < 50 ms

#### Scenario 9: Multi-Tenant Isolation Under Load

- **Purpose:** Validate tenant isolation holds under high load
- **Load profile:** 10 tenants, each generating 1,000 decisions/second simultaneously
- **Success criteria:** No cross-tenant data leakage, per-tenant latency within 10% of single-tenant baseline

#### Scenario 10: Cache Invalidation Under Load

- **Purpose:** Validate cache consistency during high-velocity policy changes
- **Load profile:** Constant 10,000 decisions/second, deploy policy changes every 30 seconds
- **Success criteria:** Zero stale cache hits, all enforcement points updated within 5 seconds

#### Scenario 11: Auto-Scaling Response Time

- **Purpose:** Validate auto-scaling reacts within acceptable time bounds
- **Load profile:** Step from 1,000 to 20,000 decisions/second over 2 minutes
- **Success criteria:** Scale-out initiated within 60 seconds, full capacity within 5 minutes, no p99 breach > 20 ms

#### Scenario 12: Scale-In Stability

- **Purpose:** Validate scale-in does not cause instability
- **Load profile:** Ramp from 20,000 to 1,000 decisions/second over 10 minutes
- **Success criteria:** No connection drops, no in-flight request loss, graceful drain

### 13.4 Scalability Test Automation

```python
class ScalabilityTestSuite:
    """Automated scalability test runner."""
    
    def __init__(self, config: TestConfig):
        self.config = config
        self.load_generator = LoadGenerator(config.load_profile)
        self.metrics = MetricsCollector(config.prometheus_url)
        self.validator = SuccessCriteriaValidator(config.criteria)
    
    async def run_test(self, scenario: TestScenario) -> TestResult:
        """Execute a single scalability test scenario."""
        # 1. Warm-up phase
        await self.load_generator.ramp_to(
            target_rps=scenario.warmup_rps,
            duration=scenario.warmup_duration,
        )
        await self.metrics.collect_baseline(duration=scenario.warmup_duration)
        
        # 2. Measurement phase
        measurement_task = asyncio.create_task(
            self.metrics.collect_during(duration=scenario.measurement_duration)
        )
        
        # 3. Execute load profile
        await self.load_generator.execute_profile(scenario.load_profile)
        
        # 4. Collect results
        metrics = await measurement_task
        
        # 5. Validate success criteria
        validation = self.validator.validate(metrics, scenario.criteria)
        
        # 6. Generate report
        return TestResult(
            scenario=scenario.name,
            metrics=metrics,
            validation=validation,
            timestamp=datetime.now(),
        )
    
    async def run_all(self) -> TestReport:
        """Run all scalability test scenarios."""
        results = []
        for scenario in self.config.scenarios:
            result = await self.run_test(scenario)
            results.append(result)
        
        return TestReport(
            results=results,
            summary=self._summarize(results),
            recommendations=self._generate_recommendations(results),
        )
```

### 13.5 Scalability Regression Testing

Every code change that touches the enforcement path, evidence pipeline, or audit trail MUST pass:

| Test | Trigger | Criteria |
|------|---------|----------|
| **Micro-benchmark** | Every PR merge | < 5% regression vs. baseline |
| **Integration benchmark** | Nightly CI | < 10% regression vs. baseline |
| **Full performance suite** | Weekly | All targets met |
| **Scalability test** | Monthly | All targets met |
| **Chaos test** | Monthly | All resilience targets met |

### 13.6 Scalability Baselines

Baselines are established at each release and stored in the performance test repository:

| Release | Date | Enforcement p99 (ms) | Throughput (dec/s) | Evidence p99 (ms) | Scale-Out Efficiency |
|---------|------|---------------------|--------------------|--------------------|-----------------------|
| v0.1 (Alpha) | TBD | < 10 | ≥ 10,000 | < 200 | > 85% |
| v0.5 (Beta) | TBD | < 8 | ≥ 15,000 | < 150 | > 90% |
| v1.0 (GA) | TBD | < 5 | ≥ 25,000 | < 100 | > 95% |

### 13.7 Scalability Test Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `grc_test_load_rps` | Gauge | scenario | Current load in requests/second |
| `grc_test_decisions_total` | Counter | scenario, decision | Total decisions during test |
| `grc_test_decision_duration_seconds` | Histogram | scenario | Decision latency distribution |
| `grc_test_scale_out_duration_seconds` | Gauge | component | Time to scale out |
| `grc_test_scale_in_duration_seconds` | Gauge | component | Time to scale in |
| `grc_test_cache_hit_rate` | Gauge | cache_layer | Cache hit rate during test |
| `grc_test_error_rate` | Gauge | error_type | Error rate during test |
| `grc_test_resource_utilization` | Gauge | component, resource | CPU/memory/disk utilization |

### 13.8 Chaos Testing

```python
class ChaosEngine:
    """Chaos testing for scalability validation."""
    
    async def pod_failure_test(self, component: str, count: int = 1):
        """Kill pods and validate recovery."""
        # 1. Start baseline load
        load = self.load_generator.start(constant_rps=10000)
        
        # 2. Kill pods
        victims = await self.kubernetes.get_pods(component)
        for pod in victims[:count]:
            await self.kubernetes.delete_pod(pod.name)
        
        # 3. Measure recovery
        recovery_metrics = await self.metrics.measure_recovery(
            component=component,
            timeout_seconds=60,
        )
        
        # 4. Validate
        assert recovery_metrics.decision_loss == 0
        assert recovery_metrics.recovery_time_seconds < 5
        
        await load.stop()
    
    async def network_partition_test(self, component: str):
        """Simulate network partition and validate behavior."""
        # 1. Start baseline load
        load = self.load_generator.start(constant_rps=10000)
        
        # 2. Create network partition
        await self.network.partition(component, duration_seconds=30)
        
        # 3. Measure impact
        impact = await self.metrics.measure_impact(
            component=component,
            duration_seconds=60,
        )
        
        # 4. Validate graceful degradation
        assert impact.error_rate < 0.01
        assert impact.p99_latency_ms < 50
        
        await load.stop()
    
    async def resource_exhaustion_test(self, component: str, resource: str):
        """Exhaust a resource and validate scaling response."""
        # 1. Start baseline load
        load = self.load_generator.start(constant_rps=10000)
        
        # 2. Exhaust resource (e.g., fill disk, exhaust connections)
        await self.resource.exhaust(component, resource)
        
        # 3. Measure scaling response
        response = await self.metrics.measure_scaling_response(
            component=component,
            resource=resource,
        )
        
        # 4. Validate auto-scaling or alerting
        assert response.scaling_triggered or response.alert_fired
        
        await load.stop()
```

---

## 14. Deployment Patterns

### 14.1 Small Team (Tier 1)

```yaml
# docker-compose.yml
version: "3.8"
services:
  grc-pdp:
    image: grc-claw/pdp:latest
    environment:
      - REDIS_URL=redis://redis:6379
      - DB_URL=postgresql://postgres:5432/grc_claw
    deploy:
      resources:
        limits:
          cpus: "2"
          memory: 4G

  grc-pep:
    image: grc-claw/pep:latest
    ports:
      - "8080:8080"
    environment:
      - PDP_URL=http://grc-pdp:8081
      - REDIS_URL=redis://redis:6379
    deploy:
      resources:
        limits:
          cpus: "2"
          memory: 4G

  postgres:
    image: postgres:16
    volumes:
      - pgdata:/var/lib/postgresql/data

  redis:
    image: redis:7
    command: redis-server --maxmemory 2gb --maxmemory-policy allkeys-lru

  minio:
    image: minio/minio
    command: server /data --console-address ":9001"
    volumes:
      - miniodata:/data

volumes:
  pgdata:
  miniodata:
```

### 14.2 Enterprise (Tier 3)

```yaml
# Helm values for enterprise deployment
global:
  region: us-east-1
  tenants:
    - id: tenant-acme
      tier: enterprise
      data_residency: US
    - id: tenant-globex
      tier: enterprise
      data_residency: EU

pep:
  replicas: 12
  autoscaling:
    enabled: true
    minReplicas: 4
    maxReplicas: 50
  resources:
    requests:
      cpu: 2
      memory: 4Gi
    limits:
      cpu: 4
      memory: 8Gi

pdp:
  replicas: 6
  autoscaling:
    enabled: true
    minReplicas: 2
    maxReplicas: 25
  resources:
    requests:
      cpu: 4
      memory: 8Gi
    limits:
      cpu: 8
      memory: 16Gi

evidenceCollector:
  replicas: 12
  autoscaling:
    enabled: true
    minReplicas: 4
    maxReplicas: 96
  kafka:
    partitions: 48
    replicationFactor: 3

postgresql:
  enabled: true
  architecture: replication
  replicaCount: 3
  resources:
    requests:
      cpu: 8
      memory: 32Gi
  persistence:
    size: 500Gi
    storageClass: premium-rwo

redis:
  enabled: true
  architecture: cluster
  cluster:
    shards: 3
    replicasPerShard: 1

kafka:
  enabled: true
  replicaCount: 6
  resources:
    requests:
      cpu: 4
      memory: 16Gi
  persistence:
    size: 200Gi
```

---

## 15. Migration Between Tiers

### 15.1 Tier 1 → Tier 2

| Step | Action | Downtime |
|------|--------|----------|
| 1 | Deploy HA PostgreSQL (Patroni) | Zero (parallel) |
| 2 | Deploy Redis Cluster | Zero (parallel) |
| 3 | Migrate data to new storage | Zero (online migration) |
| 4 | Scale PEP to 2+ instances | Zero (rolling) |
| 5 | Scale PDP to 2+ instances | Zero (rolling) |
| 6 | Decommission single-node setup | Zero |

### 15.2 Tier 2 → Tier 3

| Step | Action | Downtime |
|------|--------|----------|
| 1 | Deploy second region (K8s cluster) | Zero |
| 2 | Configure cross-region replication (Kafka MM, PostgreSQL logical) | Zero |
| 3 | Deploy GSLB (GeoDNS) | Zero |
| 4 | Migrate tenants to multi-region | Zero (per-tenant) |
| 5 | Scale components to Tier 3 capacity | Zero (rolling) |
| 6 | Decommission single-region dependencies | Zero |

### 15.3 Tier 3 → Tier 4

| Step | Action | Downtime |
|------|--------|----------|
| 1 | Deploy additional regions | Zero |
| 2 | Implement cell-based architecture | Zero (per-cell) |
| 3 | Enable data residency enforcement | Zero (policy-driven) |
| 4 | Scale to 100+ tenants | Zero (per-tenant) |
| 5 | Implement global tenant registry | Zero |

---

## 16. Compliance & Framework Alignment

This scalability specification supports the following framework requirements:

| Framework | Control | Scalability Requirement |
|-----------|---------|------------------------|
| **ISO 42001** | Clause 9 (Performance Evaluation) | Continuous monitoring with defined thresholds and alerting at scale |
| **ISO 42001** | A.6 (AI System Lifecycle) | Scalable enforcement that maintains performance as agent count grows |
| **NIST AI RMF** | MEASURE 3 (AI System Monitoring) | Sub-100ms monitoring latency at enterprise scale |
| **NIST AI RMF** | MANAGE 2 (Risk Response) | Automated response within latency bounds under load |
| **SOC 2** | CC7.2 (System Monitoring) | Continuous monitoring with alerting across all tenants |
| **SOC 2** | CC7.3 (Incident Response) | Performance degradation triggers incident response automatically |
| **SOC 2** | CC6.1 (Logical Access) | Multi-tenant isolation with complete data separation |
| **GDPR** | Art. 25 (Data Protection by Design) | Data residency enforcement, encryption at scale |
| **GDPR** | Art. 32 (Security of Processing) | Scalable encryption, key management, access control |
| **EU AI Act** | Art. 9 (Risk Management) | Scalable risk monitoring and enforcement |
| **EU AI Act** | Art. 12 (Record-keeping) | Scalable audit trail with 7-year retention |

---

## 17. Appendix A: Glossary

| Term | Definition |
|------|------------|
| **Cell** | An independent, self-contained deployment unit that serves a subset of tenants |
| **Consistent hashing** | A hashing technique that minimizes rebalancing when nodes are added or removed |
| **GSLB** | Global Server Load Balancing — DNS-based traffic distribution across regions |
| **Hash partitioning** | Distributing data across partitions based on a hash of the partition key |
| **Multi-tenancy** | Serving multiple organizations (tenants) from a shared infrastructure |
| **Pooled tenancy** | Shared infrastructure with logical data isolation |
| **Range partitioning** | Distributing data across partitions based on value ranges (e.g., time) |
| **Silo tenancy** | Dedicated infrastructure per tenant for physical isolation |
| **Token bucket** | A rate limiting algorithm that allows bursts up to a configurable maximum |
| **Predictive scaling** | Pre-scaling capacity based on historical traffic patterns and forecasts |
| **Elasticity** | The ability to automatically add or remove resources to match demand |
| **Cache warming** | Pre-loading cache entries before they are needed to avoid cold-start latency |
| **Shard splitting** | Dividing an oversized shard into two smaller shards at a split point |
| **Sliding window log** | A rate limiting algorithm that provides precise limits without burst allowance |

---

## 18. Appendix B: Scaling Checklist

Before each tier upgrade, verify:

- [ ] All latency targets met at current tier (Performance Spec)
- [ ] All throughput targets met at current tier
- [ ] Auto-scaling policies configured and tested
- [ ] Predictive scaling configured for known traffic patterns
- [ ] Multi-tenancy isolation verified (no cross-tenant data leakage)
- [ ] Data partitioning strategy validated for target data volume
- [ ] Consistent hashing ring configured for dynamic shard membership
- [ ] Shard splitting/merging thresholds configured
- [ ] Cache invalidation patterns verified (TTL, write-through, version-based)
- [ ] Cache warming strategies tested for scale-out events
- [ ] Rate limiting configured at all levels (edge, gateway, mesh, application)
- [ ] Throttling priorities configured and tested
- [ ] Load balancing health checks and failover tested
- [ ] Circuit breakers configured and tested
- [ ] Scalability test suite passing (all 12 scenarios)
- [ ] Chaos testing completed (pod failure, network partition, resource exhaustion)
- [ ] Scale-out efficiency > 90% of ideal
- [ ] Scale-in stability verified (no connection drops, no in-flight loss)
- [ ] Backup and recovery procedures tested at scale
- [ ] Monitoring dashboards functional at target scale
- [ ] Alerting thresholds configured and tested
- [ ] Capacity plan updated for next 12 months
- [ ] Cost optimization opportunities identified
- [ ] Disaster recovery runbook updated
- [ ] Security review completed for new tier

---

*End of Scalability Specification.*
