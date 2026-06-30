# GRC_Claw Performance Benchmarks & SLOs — V17

> Last updated: 2026-06-30 | Status: Living Document
> Baseline environment: Node.js 20 LTS, 8 vCPU / 32 GB RAM, Supabase Pro, Redis 7

---

## 1. API Response Time SLOs

All response times measured at the gateway layer (after TLS termination, before business logic). Percentiles collected via `MetricsCollector` histograms exported to Prometheus.

### 1.1 Evidence CRUD Operations

| Operation | p50 | p95 | p99 | SLO Target | Measurement |
|-----------|-----|-----|-----|------------|-------------|
| `POST /api/v1/evidence` (attach) | 18 ms | 45 ms | 82 ms | p99 < 100 ms | `http_request_duration_ms{route="evidence.create"}` |
| `GET /api/v1/evidence/:id` | 8 ms | 22 ms | 38 ms | p99 < 50 ms | `http_request_duration_ms{route="evidence.get"}` |
| `GET /api/v1/evidence?controlId=X` (list by control) | 25 ms | 68 ms | 120 ms | p99 < 150 ms | `http_request_duration_ms{route="evidence.list"}` |
| `PUT /api/v1/evidence/:id` (update metadata) | 20 ms | 50 ms | 90 ms | p99 < 100 ms | `http_request_duration_ms{route="evidence.update"}` |
| `DELETE /api/v1/evidence/:id` | 12 ms | 30 ms | 55 ms | p99 < 75 ms | `http_request_duration_ms{route="evidence.delete"}` |
| `POST /api/v1/evidence/bulk` (batch insert, 100 records) | 180 ms | 420 ms | 750 ms | p99 < 1000 ms | `http_request_duration_ms{route="evidence.bulk"}` |

**Notes:**
- In-memory cache reads (`EvidenceStore.get()`) return in < 1 ms.
- PostgreSQL writes use write-through with async flush; latency is visible only on flush barrier.
- SHA-256 hashing for `EvidenceStore.hashContent()` adds ~0.3 ms per 1 KB payload.

### 1.2 Framework Crosswalk Lookups

| Operation | p50 | p95 | p99 | SLO Target |
|-----------|-----|-----|-----|------------|
| `GET /api/v1/crosswalk?from=ISO27001&to=NIST-CSF` | 35 ms | 85 ms | 150 ms | p99 < 200 ms |
| `GET /api/v1/crosswalk?from=ISO27001&to=PCI-DSS` | 30 ms | 72 ms | 130 ms | p99 < 200 ms |
| `GET /api/v1/crosswalk/bulk` (all framework pairs) | 250 ms | 600 ms | 1100 ms | p99 < 1500 ms |
| `POST /api/v1/crosswalk/generate` (on-demand mapping) | 500 ms | 1200 ms | 2500 ms | p99 < 3000 ms |

**Notes:**
- Crosswalk results are cached in Redis with 1-hour TTL.
- First-call cold cache penalty: +40–80 ms for `FrameworkCrosswalk` initialization.
- Bulk crosswalk paginates internally; 100ms per-page overhead beyond 50 frameworks.

### 1.3 Trust Score Calculations

| Operation | p50 | p95 | p99 | SLO Target |
|-----------|-----|-----|-----|------------|
| `GET /api/v1/trust/score/:agentId` (single agent) | 45 ms | 110 ms | 200 ms | p99 < 250 ms |
| `GET /api/v1/trust/score?tenant=X` (tenant aggregate) | 120 ms | 300 ms | 550 ms | p99 < 700 ms |
| `POST /api/v1/trust/recalculate` (full recalc) | 800 ms | 2000 ms | 4000 ms | p99 < 5000 ms |
| `GET /api/v1/trust/history/:agentId` (30-day trend) | 90 ms | 200 ms | 380 ms | p99 < 500 ms |

**Notes:**
- Trust scores are computed from `AgentTrustScore` engine with FAIR model weights.
- Recalculation triggers fan-out across all agent identities for the tenant.
- Cached results expire after 5 minutes; stale reads are served with `X-Stale: true` header.

### 1.4 Agent Execution

| Operation | p50 | p95 | p99 | SLO Target |
|-----------|-----|-----|-----|------------|
| `POST /api/v1/agent/dispatch` (tool invocation) | 150 ms | 400 ms | 800 ms | p99 < 1000 ms |
| `GET /api/v1/agent/session/:id` (session state) | 12 ms | 28 ms | 45 ms | p99 < 60 ms |
| `POST /api/v1/agent/skill/execute` (skill run) | 200 ms | 600 ms | 1200 ms | p99 < 1500 ms |
| `GET /api/v1/agent/audit-trail/:id` (execution history) | 30 ms | 70 ms | 120 ms | p99 < 150 ms |
| `POST /api/v1/agent/collaborate` (multi-agent handoff) | 250 ms | 700 ms | 1500 ms | p99 < 2000 ms |

**Notes:**
- `AgentSession` dispatches through `BUILTIN_AGENT_TOOLS` registry.
- Skill execution via `SkillExecutor` includes policy firewall evaluation (~15 ms overhead).
- Collaboration fan-out scales linearly with participant count (3 agents = ~3x base latency).

### 1.5 Verifier Room Operations

| Operation | p50 | p95 | p99 | SLO Target |
|-----------|-----|-----|-----|------------|
| `POST /api/v1/verifier/rooms` (create room) | 80 ms | 180 ms | 320 ms | p99 < 400 ms |
| `POST /api/v1/verifier/rooms/:id/join` (join room) | 40 ms | 90 ms | 160 ms | p99 < 200 ms |
| `POST /api/v1/verifier/rooms/:id/submit` (submit evidence) | 60 ms | 140 ms | 250 ms | p99 < 300 ms |
| `POST /api/v1/verifier/rooms/:id/finalize` (close room) | 150 ms | 350 ms | 650 ms | p99 < 800 ms |
| `GET /api/v1/verifier/rooms/:id/audit-log` (room history) | 25 ms | 60 ms | 100 ms | p99 < 125 ms |
| `GET /api/v1/verifier/rooms?status=open` (list open rooms) | 35 ms | 80 ms | 140 ms | p99 < 175 ms |

**Notes:**
- Room state is held in Redis with 24-hour TTL.
- Finalization triggers async report generation via `export-daemon`.
- Audit log writes are append-only with hash-chain verification.

### 1.6 Benchmark Aggregations

| Operation | p50 | p95 | p99 | SLO Target |
|-----------|-----|-----|-----|------------|
| `GET /api/v1/benchmarks/outcomes` (aggregated metrics) | 100 ms | 250 ms | 450 ms | p99 < 600 ms |
| `GET /api/v1/benchmarks/cycle-time` (audit cycle analytics) | 120 ms | 280 ms | 500 ms | p99 < 600 ms |
| `GET /api/v1/benchmarks/remediation-latency` | 90 ms | 200 ms | 380 ms | p99 < 500 ms |
| `POST /api/v1/benchmarks/compare` (peer benchmark) | 200 ms | 500 ms | 900 ms | p99 < 1200 ms |

**Notes:**
- Benchmark data sourced from opt-in anonymized `BenchmarkIntelligence` aggregates.
- Peer comparison involves cross-tenant aggregation with differential privacy noise (ε=1.0).

---

## 2. Throughput SLOs

### 2.1 Evidence Ingestion Rate

| Metric | Target | Measurement | Burst |
|--------|--------|-------------|-------|
| Steady-state ingestion | ≥ 500 events/sec | `evidence_ingest_rate_total` counter | ≤ 2000 events/sec for 60s |
| Peak burst (connector reconnect) | ≥ 2000 events/sec | `evidence_ingest_burst_total` | 5s sustained window |
| Deduplication throughput | ≥ 10,000 dedup checks/sec | `dedup_check_rate_total` | Idempotency cache hit ratio > 95% |
| PostgreSQL write throughput | ≥ 300 writes/sec | `pg_write_total` | Batch inserts with `ON CONFLICT DO NOTHING` |

**Ingest Pipeline Breakdown:**
```
Connector → normalize (2ms) → dedup check (0.5ms) → policy eval (3ms)
         → write to PG (6ms) → event bus publish (1ms) = ~12.5ms total
         → theoretical max: 80 events/sec per core
         → 8 cores = 640 events/sec steady state
```

### 2.2 Concurrent Agent Executions

| Metric | Target | Measurement |
|--------|--------|-------------|
| Concurrent tool dispatches | ≥ 50 | `agent_concurrent_executions` gauge |
| Concurrent skill executions | ≥ 20 | `skill_concurrent_executions` gauge |
| Concurrent multi-agent collaborations | ≥ 10 | `collab_concurrent_sessions` gauge |
| Agent session pool size | 100 sessions | `agent_session_pool_active` gauge |

**Concurrency Model:**
- `AgentSession` uses worker pool (configurable `AGENT_WORKER_POOL_SIZE`, default: CPU count × 2).
- Each dispatch acquires a semaphore; queue depth alerting at > 80% saturation.
- `AgentCollaboration` creates ephemeral task graphs with bounded fan-out (max 8 participants).

### 2.3 API Requests Per Second

| Metric | Target | Measurement |
|--------|--------|-------------|
| Read-only endpoints (GET) | ≥ 2000 rps | `http_requests_total` with `method=GET` |
| Mutating endpoints (POST/PUT) | ≥ 500 rps | `http_requests_total` with `method=POST` |
| Total gateway throughput | ≥ 2500 rps | `http_requests_total` (all methods) |
| WebSocket message throughput | ≥ 5000 msg/sec | `ws_messages_total` |

**Rate Limiting:**
- Per-tenant: 1000 req/min (configurable via `RATE_LIMIT_PER_TENANT`).
- Global: 10,000 req/min across all tenants.
- Burst allowance: 2x steady rate for 10-second windows.
- Rate limit headers: `X-RateLimit-Remaining`, `X-RateLimit-Reset`.

### 2.4 WebSocket Connections

| Metric | Target | Measurement |
|--------|--------|-------------|
| Concurrent WS connections | ≥ 500 | `ws_connections_active` gauge |
| Connection establishment time | p99 < 200 ms | `ws_handshake_duration_ms` histogram |
| Message delivery latency (gateway → client) | p99 < 50 ms | `ws_message_latency_ms` histogram |
| Reconnection success rate | ≥ 99.5% | `ws_reconnection_success_total` / `ws_reconnection_attempts_total` |

**WebSocket Channels:**
- `/ws/soc-events` — real-time SOC event stream (normalized security events)
- `/ws/compliance-updates` — compliance posture change notifications
- `/ws/verifier-rooms` — verifier room collaboration messages
- `/ws/agent-stream` — agent execution output streaming

---

## 3. Resource Utilization

### 3.1 Memory Usage Per Package

| Package | Base Memory | Per-Instance | Notes |
|---------|-------------|--------------|-------|
| `@grc-claw/gateway` | 85 MB | — | Node.js process + V8 heap |
| `@grc-claw/evidence` | 12 MB | +0.5 MB per 1000 records | In-memory cache (write-through) |
| `@grc-claw/framework-crosswalk` | 8 MB | +2 MB per framework loaded | Framework mapping tables |
| `@grc-claw/agent-runtime` | 15 MB | +3 MB per active session | Session state + tool registry |
| `@grc-claw/verifier-network` | 10 MB | +1 MB per active room | Room state + audit log buffer |
| `@grc-claw/skill-executor` | 5 MB | +1 MB per loaded skill | Skill manifest cache |
| `@grc-claw/risk-quantification` | 18 MB | +5 MB per Monte Carlo run | FAIR model + simulation data |
| `@grc-claw/compliance-knowledge-graph` | 20 MB | +10 MB per graph snapshot | Neo4j-style adjacency lists |
| `@grc-claw/observability` | 8 MB | +2 MB per traced agent | Span buffer + trace exporter |
| `@grc-claw/rbac-multi-tenant` | 6 MB | +0.1 MB per tenant | Policy cache (OPA/Wasm) |

**Total estimated gateway memory (89 packages loaded):** ~350 MB baseline + tenant-specific allocations.

**Memory Alerts:**
- Warning at RSS > 1.5 GB (75% of 2 GB limit).
- Critical at RSS > 1.8 GB (90%).
- OOM kill expected at RSS > 2 GB (container limit).

### 3.2 CPU Utilization During Builds

| Operation | Duration (8 vCPU) | Peak CPU | Notes |
|-----------|-------------------|----------|-------|
| `npm run build` (full monorepo, 89 packages) | 45–75 sec | 780% (8 cores) | Parallel TypeScript compilation |
| `tsc -b` (incremental, 5 changed packages) | 8–15 sec | 400% | Affinity-based rebuild |
| `npm run test` (all packages) | 30–60 sec | 650% | Node.js test runner parallelism |
| Single package build (`@grc-claw/gateway`) | 3–6 sec | 250% | Single-threaded TS compilation |
| `docker build` (production image) | 90–180 sec | 300% | Multi-stage, layer caching |

### 3.3 Disk I/O for Evidence Storage

| Operation | IOPS | Throughput | Latency |
|-----------|------|------------|---------|
| Single evidence write (PostgreSQL) | 500 | 10 MB/s | 2 ms |
| Batch evidence write (100 records) | 2000 | 80 MB/s | 20 ms (batched) |
| Evidence read (by ID, indexed) | 3000 | 50 MB/s | 0.3 ms |
| Evidence read (by control, scan) | 800 | 30 MB/s | 5–15 ms |
| Audit log append | 1500 | 25 MB/s | 0.7 ms |
| WAL flush (PostgreSQL) | — | 200 MB/s | 1 ms |

**Disk Alerts:**
- Warning at disk usage > 80%.
- Critical at disk usage > 90%.
- Evidence retention: 7 years (configurable per framework requirement).

### 3.4 Network Bandwidth for Sync Operations

| Operation | Bandwidth | Latency | Notes |
|-----------|-----------|---------|-------|
| Connector → Gateway (event stream) | 50 Mbps sustained | < 5 ms LAN | HTTPS/2 multiplexing |
| Gateway → Supabase (writes) | 20 Mbps | < 10 ms (same region) | Connection pooling (PgBouncer) |
| Gateway → Supabase (reads) | 100 Mbps | < 5 ms | Read replica preferred |
| WebSocket broadcast (500 clients) | 200 Mbps peak | < 50 ms | Fan-out via `socClients` set |
| Sync daemon → external SIEM | 10 Mbps | < 50 ms | Batched every 5s |
| Evidence export (PDF/CSV bundle) | 5 Mbps | — | Async via `export-daemon` |

---

## 4. Scalability Targets

### 4.1 Multi-Tenant Limits

| Metric | Minimum | Target | Maximum (Stretched) |
|--------|---------|--------|---------------------|
| Concurrent tenants | 10 | 100 | 1,000 |
| Evidence records per tenant | 10,000 | 1,000,000 | 10,000,000 |
| Control mappings per tenant | 100 | 10,000 | 100,000 |
| Concurrent verifier rooms | 5 | 50 | 200 |
| Concurrent agent sessions per tenant | 5 | 20 | 50 |
| Framework crosswalks per tenant | 5 | 20 | 50 |
| Connector registrations per tenant | 3 | 15 | 50 |

### 4.2 Data Growth Projections

| Time Period | Evidence Records | Audit Log Entries | Total Storage |
|-------------|-----------------|-------------------|---------------|
| Month 1 (pilot) | 50,000 | 200,000 | 2 GB |
| Month 6 (growth) | 2,000,000 | 8,000,000 | 50 GB |
| Year 1 (production) | 10,000,000 | 50,000,000 | 200 GB |
| Year 3 (enterprise) | 50,000,000 | 250,000,000 | 1 TB |

**Partitioning Strategy:**
- Evidence table partitioned by `created_at` (monthly partitions).
- Audit log partitioned by `created_at` (weekly partitions).
- Old partitions archived to cold storage (S3/GCS) after 90 days.
- Active partitions kept on SSD-backed storage.

### 4.3 Horizontal Scaling Thresholds

| Metric | Scale-Out Trigger | Scale-In Trigger |
|--------|-------------------|------------------|
| Worker pods (Kubernetes) | CPU > 70% for 5 min | CPU < 30% for 10 min |
| Event bus queue depth | > 10,000 pending | < 1,000 pending |
| WebSocket connections per pod | > 250 | < 50 |
| Evidence write latency (p95) | > 200 ms | < 50 ms |
| Agent dispatch queue depth | > 20 | < 5 |

---

## 5. Reliability SLOs

### 5.1 Availability Targets

| SLO | Target | Measurement | Error Budget |
|-----|--------|-------------|--------------|
| Gateway uptime | 99.9% (8.76 hrs/yr downtime) | `up` metric in Prometheus | 43.8 min/month |
| Evidence write availability | 99.95% | `evidence_write_success_total` / `evidence_write_total` | 21.9 min/month |
| WebSocket availability | 99.9% | `ws_connections_active` / `ws_connections_expected` | 43.8 min/month |
| Agent execution availability | 99.5% | `agent_dispatch_success_total` / `agent_dispatch_total` | 3.6 hrs/month |

### 5.2 Recovery Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Mean Time to Recovery (MTTR) | < 5 minutes | Time from alert to service restored |
| Mean Time Between Failures (MTBF) | > 720 hours | Time between P1 incidents |
| Recovery Time Objective (RTO) | < 15 minutes | Time to restore from backup |
| Recovery Point Objective (RPO) | < 5 minutes | Maximum data loss window |

### 5.3 Data Durability

| Metric | Target | Mechanism |
|--------|--------|-----------|
| Evidence data durability | 99.999999% (8 nines) | PostgreSQL WAL replication (sync) |
| Audit log durability | 99.999999% | Append-only + hash chain + remote backup |
| Trust score durability | 99.999% | Recomputable from evidence graph |
| Configuration durability | 99.999% | Git-backed + database |

**Durability Mechanisms:**
- PostgreSQL synchronous replication to 1 standby (RPO = 0 for committed transactions).
- Asynchronous replication to 2+ read replicas (eventual consistency).
- Daily encrypted backups to S3 with 30-day retention.
- Monthly backup verification (automated restore test).
- Evidence hash chain: every record includes `parentHash` linking to predecessor.

### 5.4 Backup & Recovery

| Backup Type | Frequency | Retention | Recovery Test |
|-------------|-----------|-----------|---------------|
| Full database backup | Daily 02:00 UTC | 30 days | Weekly automated restore |
| WAL archival (continuous) | Real-time | 7 days | Point-in-time recovery |
| Evidence bundle export | Weekly | 1 year | Monthly verification |
| Configuration backup | On change | 90 days | N/A (git-based) |
| Disaster recovery drill | Quarterly | — | Full failover test |

---

## 6. Performance Testing Methodology

### 6.1 Load Testing Tools

| Tool | Use Case | Configuration |
|------|----------|---------------|
| **k6** (Grafana) | API endpoint load testing | VUs: 10–500, duration: 5–30 min |
| **autocannon** | HTTP throughput benchmarking | Connections: 10–100, duration: 10–60s |
| **Node.js `node:test`** | Unit-level performance regression | Benchmark suite in each package |
| **Artillery** | WebSocket load testing | Connections: 100–1000, duration: 5 min |

### 6.2 Stress Testing Scenarios

| Scenario | VUs | Duration | Success Criteria |
|----------|-----|----------|------------------|
| **Steady State** | 50 | 30 min | p99 < target SLO, error rate < 0.1% |
| **Spike Test** | 50 → 500 → 50 | 10 min | Recovery < 30s after spike |
| **Soak Test** | 100 | 4 hours | No memory leak (RSS growth < 5%), error rate stable |
| **Breakpoint** | 10 → ∞ (ramp) | Until failure | Identify max throughput before degradation |
| **Recovery Test** | 100 | 5 min → kill → restart | Service recovers within RTO |

### 6.3 Benchmark Automation

Benchmarks are automated via `npm run bench` and integrated into CI:

```bash
# Run all benchmarks
npm run bench

# Run specific benchmark suite
npm run bench:api          # API response time benchmarks
npm run bench:ingest       # Evidence ingestion throughput
npm run bench:agent        # Agent execution benchmarks
npm run bench:verifier     # Verifier room benchmarks
npm run bench:crosswalk    # Framework crosswalk benchmarks
npm run bench:websocket    # WebSocket throughput
npm run bench:memory       # Memory leak detection
npm run bench:full         # Full benchmark suite (CI only)
```

### 6.4 Benchmark Scripts

#### 6.4.1 API Response Time Benchmark (`scripts/bench-api.mjs`)

```javascript
#!/usr/bin/env node
/**
 * GRC_Claw API Response Time Benchmark
 * Usage: node scripts/bench-api.mjs [--iterations=1000] [--concurrency=50]
 */

import { performance } from 'node:perf_hooks';
import http from 'node:http';

const GATEWAY_URL = process.env.GATEWAY_URL || 'http://localhost:3000';
const ITERATIONS = parseInt(process.env.BENCH_ITERATIONS || '1000', 10);
const CONCURRENCY = parseInt(process.env.BENCH_CONCURRENCY || '50', 10);
const TENANT_ID = process.env.BENCH_TENANT_ID || 'bench-tenant-001';
const AUTH_TOKEN = process.env.BENCH_AUTH_TOKEN || '';

const endpoints = [
  { name: 'Evidence List', method: 'GET', path: '/api/v1/evidence?controlId=ISO-A.5.1.1' },
  { name: 'Evidence Get', method: 'GET', path: '/api/v1/evidence/ev-0000000000000001' },
  { name: 'Crosswalk ISO→NIST', method: 'GET', path: '/api/v1/crosswalk?from=ISO27001&to=NIST-CSF' },
  { name: 'Trust Score', method: 'GET', path: '/api/v1/trust/score/agent-001' },
  { name: 'Agent Session', method: 'GET', path: '/api/v1/agent/session/sess-001' },
  { name: 'Verifier Rooms', method: 'GET', path: '/api/v1/verifier/rooms?status=open' },
  { name: 'Benchmark Outcomes', method: 'GET', path: '/api/v1/benchmarks/outcomes' },
];

function makeRequest(endpoint) {
  return new Promise((resolve, reject) => {
    const url = new URL(endpoint.path, GATEWAY_URL);
    const options = {
      hostname: url.hostname,
      port: url.port,
      path: url.pathname + url.search,
      method: endpoint.method,
      headers: {
        'Content-Type': 'application/json',
        'X-Tenant-Id': TENANT_ID,
        ...(AUTH_TOKEN ? { 'Authorization': `Bearer ${AUTH_TOKEN}` } : {}),
      },
      timeout: 10000,
    };

    const start = performance.now();
    const req = http.request(options, (res) => {
      let data = '';
      res.on('data', (chunk) => data += chunk);
      res.on('end', () => {
        const duration = performance.now() - start;
        resolve({
          status: res.statusCode,
          duration,
          size: data.length,
        });
      });
    });
    req.on('error', reject);
    req.on('timeout', () => { req.destroy(); reject(new Error('timeout')); });
    req.end();
  });
}

function percentile(sorted, p) {
  const idx = Math.ceil((p / 100) * sorted.length) - 1;
  return sorted[Math.max(0, idx)];
}

async function benchmarkEndpoint(endpoint, iterations) {
  const durations = [];
  let errors = 0;

  for (let i = 0; i < iterations; i++) {
    try {
      const result = await makeRequest(endpoint);
      if (result.status >= 400) errors++;
      durations.push(result.duration);
    } catch {
      errors++;
      durations.push(Infinity);
    }
  }

  durations.sort((a, b) => a - b);
  const finite = durations.filter((d) => d !== Infinity);

  return {
    endpoint: endpoint.name,
    iterations,
    p50: percentile(finite, 50).toFixed(1),
    p95: percentile(finite, 95).toFixed(1),
    p99: percentile(finite, 99).toFixed(1),
    max: finite.length > 0 ? Math.max(...finite).toFixed(1) : 'N/A',
    avg: (finite.reduce((a, b) => a + b, 0) / finite.length).toFixed(1),
    errors,
    errorRate: ((errors / iterations) * 100).toFixed(2) + '%',
  };
}

async function runConcurrentBenchmarks() {
  console.log(`\nGRC_Claw API Benchmark`);
  console.log(`Gateway: ${GATEWAY_URL}`);
  console.log(`Iterations: ${ITERATIONS}, Concurrency: ${CONCURRENCY}\n`);

  const results = [];

  // Run endpoints sequentially to avoid overwhelming the server
  for (const endpoint of endpoints) {
    process.stdout.write(`  Benchmarking ${endpoint.name}...`);
    const result = await benchmarkEndpoint(endpoint, ITERATIONS);
    console.log(` done`);
    results.push(result);
  }

  console.log(`\n${'─'.repeat(90)}`);
  console.log(
    'Endpoint'.padEnd(28) +
    'p50 (ms)'.padStart(10) +
    'p95 (ms)'.padStart(10) +
    'p99 (ms)'.padStart(10) +
    'max (ms)'.padStart(10) +
    'errors'.padStart(8) +
    'error %'.padStart(10)
  );
  console.log(`${'─'.repeat(90)}`);

  for (const r of results) {
    console.log(
      r.endpoint.padEnd(28) +
      r.p50.padStart(10) +
      r.p95.padStart(10) +
      r.p99.padStart(10) +
      r.max.padStart(10) +
      String(r.errors).padStart(8) +
      r.errorRate.padStart(10)
    );
  }
  console.log(`${'─'.repeat(90)}\n`);

  // Check SLO violations
  const violations = [];
  for (const r of results) {
    if (parseFloat(r.p99) > 1000) {
      violations.push(`${r.endpoint}: p99 ${r.p99}ms > 1000ms`);
    }
  }
  if (violations.length > 0) {
    console.log('SLO VIOLATIONS:');
    violations.forEach((v) => console.log(`  ✗ ${v}`));
    process.exit(1);
  } else {
    console.log('All endpoints within SLO targets.\n');
  }
}

runConcurrentBenchmarks().catch((err) => {
  console.error('Benchmark failed:', err);
  process.exit(1);
});
```

#### 6.4.2 Evidence Ingestion Benchmark (`scripts/bench-ingest.mjs`)

```javascript
#!/usr/bin/env node
/**
 * GRC_Claw Evidence Ingestion Throughput Benchmark
 * Usage: node scripts/bench-ingest.mjs [--events=10000] [--batch-size=100]
 */

import { performance } from 'node:perf_hooks';
import http from 'node:http';
import { randomUUID } from 'node:crypto';

const GATEWAY_URL = process.env.GATEWAY_URL || 'http://localhost:3000';
const TOTAL_EVENTS = parseInt(process.env.BENCH_EVENTS || '10000', 10);
const BATCH_SIZE = parseInt(process.env.BENCH_BATCH_SIZE || '100', 10);
const TENANT_ID = process.env.BENCH_TENANT_ID || 'bench-tenant-001';
const AUTH_TOKEN = process.env.BENCH_AUTH_TOKEN || '';

function generateEvidenceEvent(index) {
  return {
    controlId: `ISO-A.${String(Math.floor(index / 100) + 1).padStart(2, '0')}.${String(index % 100).padStart(2, '0')}`,
    uri: `s3://bench-evidence/${randomUUID()}.pdf`,
    collectedAt: new Date().toISOString(),
    lineage: { source: 'bench-mark' },
    metadata: { batchIndex: index, benchmark: true },
  };
}

function postBatch(events) {
  return new Promise((resolve, reject) => {
    const url = new URL('/api/v1/evidence/bulk', GATEWAY_URL);
    const body = JSON.stringify({ events });

    const options = {
      hostname: url.hostname,
      port: url.port,
      path: url.pathname,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Tenant-Id': TENANT_ID,
        'X-Idempotency-Key': randomUUID(),
        'Content-Length': Buffer.byteLength(body),
        ...(AUTH_TOKEN ? { 'Authorization': `Bearer ${AUTH_TOKEN}` } : {}),
      },
      timeout: 30000,
    };

    const start = performance.now();
    const req = http.request(options, (res) => {
      let data = '';
      res.on('data', (chunk) => data += chunk);
      res.on('end', () => {
        resolve({
          status: res.statusCode,
          duration: performance.now() - start,
          eventsProcessed: events.length,
        });
      });
    });
    req.on('error', reject);
    req.write(body);
    req.end();
  });
}

async function runIngestBenchmark() {
  console.log(`\nGRC_Claw Evidence Ingestion Benchmark`);
  console.log(`Gateway: ${GATEWAY_URL}`);
  console.log(`Total events: ${TOTAL_EVENTS}, Batch size: ${BATCH_SIZE}\n`);

  const batches = Math.ceil(TOTAL_EVENTS / BATCH_SIZE);
  const results = [];
  let totalEvents = 0;
  let totalErrors = 0;

  const overallStart = performance.now();

  for (let i = 0; i < batches; i++) {
    const batchEvents = [];
    const batchSize = Math.min(BATCH_SIZE, TOTAL_EVENTS - totalEvents);

    for (let j = 0; j < batchSize; j++) {
      batchEvents.push(generateEvidenceEvent(totalEvents + j));
    }

    process.stdout.write(`  Batch ${i + 1}/${batches} (${batchEvents.length} events)...`);

    try {
      const result = await postBatch(batchEvents);
      results.push(result);
      totalEvents += batchSize;
      console.log(` ${result.status} ${result.duration.toFixed(0)}ms`);
    } catch (err) {
      totalErrors += batchSize;
      console.log(` ERROR: ${err.message}`);
    }
  }

  const totalDuration = performance.now() - overallStart;
  const durations = results.map((r) => r.duration).sort((a, b) => a - b);
  const finite = durations.filter((d) => d !== Infinity);

  console.log(`\n${'─'.repeat(60)}`);
  console.log(`Total events:    ${totalEvents}`);
  console.log(`Total errors:    ${totalErrors}`);
  console.log(`Total duration:  ${(totalDuration / 1000).toFixed(1)}s`);
  console.log(`Throughput:      ${(totalEvents / (totalDuration / 1000)).toFixed(0)} events/sec`);
  console.log(`Batch p50:       ${finite[Math.floor(finite.length * 0.5)]?.toFixed(0) || 'N/A'}ms`);
  console.log(`Batch p95:       ${finite[Math.floor(finite.length * 0.95)]?.toFixed(0) || 'N/A'}ms`);
  console.log(`Batch p99:       ${finite[Math.floor(finite.length * 0.99)]?.toFixed(0) || 'N/A'}ms`);
  console.log(`${'─'.repeat(60)}\n`);

  const throughput = totalEvents / (totalDuration / 1000);
  if (throughput < 500) {
    console.log(`SLO VIOLATION: Throughput ${throughput.toFixed(0)} events/sec < 500 target`);
    process.exit(1);
  } else {
    console.log(`Throughput target met: ${throughput.toFixed(0)} events/sec >= 500 target\n`);
  }
}

runIngestBenchmark().catch((err) => {
  console.error('Benchmark failed:', err);
  process.exit(1);
});
```

#### 6.4.3 Memory Leak Detection (`scripts/bench-memory.mjs`)

```javascript
#!/usr/bin/env node
/**
 * GRC_Claw Memory Leak Detection Benchmark
 * Runs sustained load and monitors RSS growth over time.
 * Usage: node scripts/bench-memory.mjs [--duration=300] [--interval=10]
 */

import { performance } from 'node:perf_hooks';
import http from 'node:http';
import { randomUUID } from 'node:crypto';

const GATEWAY_URL = process.env.GATEWAY_URL || 'http://localhost:3000';
const DURATION_SEC = parseInt(process.env.BENCH_DURATION || '300', 10);
const INTERVAL_SEC = parseInt(process.env.BENCH_INTERVAL || '10', 10);
const TENANT_ID = process.env.BENCH_TENANT_ID || 'bench-tenant-001';
const AUTH_TOKEN = process.env.BENCH_AUTH_TOKEN || '';

function makeRequest(path) {
  return new Promise((resolve, reject) => {
    const url = new URL(path, GATEWAY_URL);
    const options = {
      hostname: url.hostname,
      port: url.port,
      path: url.pathname,
      method: 'GET',
      headers: {
        'X-Tenant-Id': TENANT_ID,
        ...(AUTH_TOKEN ? { 'Authorization': `Bearer ${AUTH_TOKEN}` } : {}),
      },
      timeout: 10000,
    };
    const req = http.request(options, (res) => {
      let data = '';
      res.on('data', (chunk) => data += chunk);
      res.on('end', () => resolve({ status: res.statusCode, size: data.length }));
    });
    req.on('error', reject);
    req.end();
  });
}

function getMemoryUsage() {
  const mem = process.memoryUsage();
  return {
    rss: mem.rss,
    heapUsed: mem.heapUsed,
    heapTotal: mem.heapTotal,
    external: mem.external,
    timestamp: Date.now(),
  };
}

async function runMemoryBenchmark() {
  console.log(`\nGRC_Claw Memory Leak Detection`);
  console.log(`Duration: ${DURATION_SEC}s, Sample interval: ${INTERVAL_SEC}s\n`);

  const endpoints = [
    '/api/v1/evidence?controlId=ISO-A.5.1.1',
    '/api/v1/crosswalk?from=ISO27001&to=NIST-CSF',
    '/api/v1/trust/score/agent-001',
    '/api/v1/verifier/rooms?status=open',
  ];

  const samples = [];
  const startTime = Date.now();
  const endTime = startTime + DURATION_SEC * 1000;
  let requestCount = 0;
  let errorCount = 0;

  // Take initial sample
  samples.push(getMemoryUsage());

  while (Date.now() < endTime) {
    // Make requests in parallel
    const batchSize = 10;
    const promises = [];
    for (let i = 0; i < batchSize; i++) {
      const endpoint = endpoints[i % endpoints.length];
      promises.push(
        makeRequest(endpoint)
          .then(() => { requestCount++; })
          .catch(() => { errorCount++; requestCount++; })
      );
    }
    await Promise.all(promises);

    // Check if it's time for a sample
    const elapsed = Date.now() - startTime;
    if (elapsed % (INTERVAL_SEC * 1000) < 100) {
      samples.push(getMemoryUsage());
    }
  }

  // Final sample
  samples.push(getMemoryUsage());

  // Analyze results
  const rssValues = samples.map((s) => s.rss);
  const initialRss = rssValues[0];
  const finalRss = rssValues[rssValues.length - 1];
  const peakRss = Math.max(...rssValues);
  const rssGrowth = finalRss - initialRss;
  const rssGrowthPercent = (rssGrowth / initialRss) * 100;

  console.log(`${'─'.repeat(60)}`);
  console.log(`Requests made:     ${requestCount}`);
  console.log(`Errors:            ${errorCount} (${((errorCount / requestCount) * 100).toFixed(2)}%)`);
  console.log(`Initial RSS:       ${(initialRss / 1024 / 1024).toFixed(1)} MB`);
  console.log(`Final RSS:         ${(finalRss / 1024 / 1024).toFixed(1)} MB`);
  console.log(`Peak RSS:          ${(peakRss / 1024 / 1024).toFixed(1)} MB`);
  console.log(`RSS growth:        ${(rssGrowth / 1024 / 1024).toFixed(1)} MB (${rssGrowthPercent.toFixed(1)}%)`);
  console.log(`${'─'.repeat(60)}\n`);

  // Memory leak detection: RSS growth should be < 5% over the test duration
  if (rssGrowthPercent > 5) {
    console.log(`MEMORY LEAK DETECTED: RSS grew by ${rssGrowthPercent.toFixed(1)}% (threshold: 5%)`);
    process.exit(1);
  } else {
    console.log(`No memory leak detected. RSS growth within acceptable range.\n`);
  }
}

runMemoryBenchmark().catch((err) => {
  console.error('Benchmark failed:', err);
  process.exit(1);
});
```

#### 6.4.4 WebSocket Throughput Benchmark (`scripts/bench-websocket.mjs`)

```javascript
#!/usr/bin/env node
/**
 * GRC_Claw WebSocket Throughput Benchmark
 * Usage: node scripts/bench-websocket.mjs [--connections=100] [--duration=60]
 */

import WebSocket from 'ws';

const WS_URL = process.env.BENCH_WS_URL || 'ws://localhost:3000/ws/soc-events';
const NUM_CONNECTIONS = parseInt(process.env.BENCH_WS_CONNECTIONS || '100', 10);
const DURATION_SEC = parseInt(process.env.BENCH_WS_DURATION || '60', 10);
const AUTH_TOKEN = process.env.BENCH_AUTH_TOKEN || '';

function createConnection(id) {
  return new Promise((resolve, reject) => {
    const ws = new WebSocket(WS_URL, {
      headers: {
        ...(AUTH_TOKEN ? { Authorization: `Bearer ${AUTH_TOKEN}` } : {}),
      },
    });

    let messageCount = 0;
    let firstMessageTime = 0;

    ws.on('open', () => {
      resolve({
        id,
        ws,
        messageCount: () => messageCount,
        firstMessageTime: () => firstMessageTime,
      });
    });

    ws.on('message', () => {
      if (messageCount === 0) firstMessageTime = Date.now();
      messageCount++;
    });

    ws.on('error', (err) => {
      reject(new Error(`Connection ${id}: ${err.message}`));
    });

    setTimeout(() => reject(new Error(`Connection ${id}: timeout`)), 10000);
  });
}

async function runWebSocketBenchmark() {
  console.log(`\nGRC_Claw WebSocket Throughput Benchmark`);
  console.log(`URL: ${WS_URL}`);
  console.log(`Connections: ${NUM_CONNECTIONS}, Duration: ${DURATION_SEC}s\n`);

  const connections = [];
  let connectedCount = 0;
  let failedCount = 0;

  // Establish connections
  process.stdout.write(`  Establishing ${NUM_CONNECTIONS} connections...`);
  for (let i = 0; i < NUM_CONNECTIONS; i++) {
    try {
      const conn = await createConnection(i);
      connections.push(conn);
      connectedCount++;
    } catch {
      failedCount++;
    }
  }
  console.log(` done (${connectedCount} connected, ${failedCount} failed)`);

  // Wait for duration
  process.stdout.write(`  Waiting ${DURATION_SEC}s for messages...`);
  await new Promise((resolve) => setTimeout(resolve, DURATION_SEC * 1000));
  console.log(` done`);

  // Collect results
  let totalMessages = 0;
  const latencies = [];

  for (const conn of connections) {
    const count = conn.messageCount();
    totalMessages += count;
    conn.ws.close();
  }

  const messagesPerSecond = totalMessages / DURATION_SEC;

  console.log(`\n${'─'.repeat(60)}`);
  console.log(`Connections established: ${connectedCount}`);
  console.log(`Total messages received: ${totalMessages}`);
  console.log(`Messages/sec:            ${messagesPerSecond.toFixed(0)}`);
  console.log(`Messages per connection: ${(totalMessages / connectedCount).toFixed(1)}`);
  console.log(`${'─'.repeat(60)}\n`);

  if (messagesPerSecond < 5000) {
    console.log(`SLO VIOLATION: ${messagesPerSecond.toFixed(0)} msg/sec < 5000 target`);
    process.exit(1);
  } else {
    console.log(`WebSocket throughput target met: ${messagesPerSecond.toFixed(0)} msg/sec >= 5000\n`);
  }
}

runWebSocketBenchmark().catch((err) => {
  console.error('Benchmark failed:', err);
  process.exit(1);
});
```

### 6.5 Benchmark Report Format

All benchmark runs produce a JSON report for CI integration:

```json
{
  "runId": "bench-20260630-001",
  "timestamp": "2026-06-30T14:30:00Z",
  "environment": {
    "node": "20.18.0",
    "platform": "linux",
    "cpus": 8,
    "memory": "32GB",
    "gateway": "1.0.0"
  },
  "results": {
    "api": {
      "evidenceCreate": { "p50": 18, "p95": 45, "p99": 82, "slo": 100, "passed": true },
      "crosswalkLookup": { "p50": 35, "p95": 85, "p99": 150, "slo": 200, "passed": true },
      "trustScore": { "p50": 45, "p95": 110, "p99": 200, "slo": 250, "passed": true }
    },
    "ingest": {
      "throughput": 640,
      "slo": 500,
      "passed": true
    },
    "memory": {
      "growthPercent": 2.1,
      "slo": 5.0,
      "passed": true
    }
  },
  "verdict": "ALL_SLO_PASSED"
}
```

---

## 7. Monitoring & Alerting

### 7.1 Key Metrics to Monitor

| Metric | Warning | Critical | Action |
|--------|---------|----------|--------|
| `http_request_duration_ms` (p99) | > 80% of SLO | > 95% of SLO | Scale workers |
| `evidence_ingest_rate` | < 600/s | < 300/s | Check connector health |
| `agent_concurrent_executions` | > 40 | > 48 (96% pool) | Scale agent workers |
| `ws_connections_active` | > 400 | > 480 | Add gateway pod |
| `process_resident_memory_bytes` | > 1.5 GB | > 1.8 GB | Restart/OOM kill |
| `evidence_write_error_rate` | > 0.1% | > 1.0% | Check Supabase health |
| `policy_eval_duration_ms` (p99) | > 30 ms | > 50 ms | Review OPA policies |

### 7.2 Dashboard Queries (Prometheus/Grafana)

```promql
# Request rate by endpoint
rate(http_requests_total[5m])

# p99 latency by endpoint
histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))

# Evidence ingestion throughput
rate(evidence_ingest_rate_total[1m])

# Memory utilization
process_resident_memory_bytes / 1024 / 1024

# Error rate
rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])

# WebSocket connections
ws_connections_active

# Agent queue depth
agent_dispatch_queue_depth
```

---

## 8. Performance Regression Detection

### 8.1 CI Integration

```yaml
# .github/workflows/perf.yml
name: Performance Regression
on:
  pull_request:
    paths:
      - 'packages/gateway/src/**'
      - 'packages/evidence/src/**'
      - 'packages/ingest/src/**'

jobs:
  benchmark:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: npm ci
      - run: npm run build
      - run: npm run bench:api
      - run: npm run bench:ingest
      - run: npm run bench:memory -- --duration=60
```

### 8.2 Regression Thresholds

| Metric | Regression Threshold | Action |
|--------|---------------------|--------|
| p50 latency | +10% from baseline | Block merge |
| p99 latency | +20% from baseline | Block merge |
| Throughput | -10% from baseline | Block merge |
| Memory growth | +20% from baseline | Block merge |
| Error rate | +0.1% from baseline | Block merge |

Baseline is stored in `benchmarks/baseline.json` and updated on each release branch merge.

---

## Appendix A: Environment Configurations

| Environment | CPUs | Memory | Supabase Tier | Redis | Max Tenants |
|-------------|------|--------|---------------|-------|-------------|
| Development | 2 | 4 GB | Free | Local | 1 |
| Staging | 4 | 16 GB | Pro | Managed | 10 |
| Production | 8 | 32 GB | Pro | Managed | 100 |
| Enterprise | 16 | 64 GB | Team | Clustered | 1,000 |

## Appendix B: Benchmark Schedule

| Benchmark | Frequency | Duration | Runner |
|-----------|-----------|----------|--------|
| API response times | Every PR | 5 min | GitHub Actions |
| Ingestion throughput | Nightly | 10 min | Cron job |
| Memory leak detection | Weekly | 30 min | Cron job |
| Full load test | Pre-release | 4 hours | Manual trigger |
| Stress test | Quarterly | 1 hour | Manual trigger |
| Disaster recovery drill | Quarterly | 2 hours | Manual trigger |
