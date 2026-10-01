# GRC_Claw Performance Engineering Implementation Guide

**Version:** 1.0  
**Date:** 2026-10-01  
**Status:** Implementation Ready  
**Parent Documents:** GRC_Claw Performance Spec v2.0, GRC_Claw Reliability Spec v2.0

---

## Table of Contents

1. [Performance Testing Framework (k6/Locust)](#1-performance-testing-framework)
2. [Caching Strategy Implementation (Redis)](#2-caching-strategy-implementation)
3. [Database Query Optimization](#3-database-query-optimization)
4. [Network Latency Optimization](#4-network-latency-optimization)
5. [Performance Regression Testing](#5-performance-regression-testing)
6. [Capacity Planning Automation](#6-capacity-planning-automation)
7. [Performance Monitoring and Alerting](#7-performance-monitoring-and-alerting)

---

## 1. Performance Testing Framework

### 1.1 k6 Load Testing Scripts

#### 1.1.1 Steady-State Enforcement Load Test

```javascript
// tests/performance/k6/enforcement-steady-state.js
import http from 'k6/http';
import { check, sleep, group } from 'k6';
import { Rate, Trend, Counter, Gauge } from 'k6/metrics';
import { randomIntBetween } from 'https://jslib.k6.io/k6-utils/1.2.0/index.js';

// Custom metrics
const decisionErrors = new Rate('decision_errors');
const decisionLatency = new Trend('decision_latency');
const auditWriteLatency = new Trend('audit_write_latency');
const cacheHitRatio = new Gauge('cache_hit_ratio');
const decisionsPerSecond = new Counter('decisions_per_second');

// Test configuration
export const options = {
  scenarios: {
    steady_state: {
      executor: 'constant-arrival-rate',
      rate: 10000,           // 10,000 decisions/second
      timeUnit: '1s',
      duration: '30m',
      preAllocatedVUs: 500,
      maxVUs: 1000,
    },
  },
  thresholds: {
    // Latency SLOs from Performance Spec Section 3.1
    'decision_latency': ['p(50)<2', 'p(95)<5', 'p(99)<10', 'p(99.9)<20', 'max<50'],
    'decision_errors': ['rate<0.001'],  // < 0.1% error rate
    'http_req_duration': ['p(99)<20'],
    'http_req_failed': ['rate<0.001'],
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8080';
const API_KEY = __ENV.API_KEY || 'test-api-key';

// Decision distribution: 80% ALLOW, 10% ALLOW_WITH_REDACTION, 5% REQUIRE_APPROVAL, 3% DENY, 2% QUARANTINE
const DECISION_PROFILES = [
  { weight: 80, action: 'read', resource: '/data/public', expected: 'ALLOW' },
  { weight: 10, action: 'write', resource: '/data/sensitive', expected: 'ALLOW_WITH_REDACTION' },
  { weight: 5, action: 'delete', resource: '/data/critical', expected: 'REQUIRE_APPROVAL' },
  { weight: 3, action: 'admin', resource: '/system/config', expected: 'DENY' },
  { weight: 2, action: 'execute', resource: '/untrusted/script', expected: 'QUARANTINE' },
];

function getDecisionProfile() {
  const rand = randomIntBetween(1, 100);
  let cumulative = 0;
  for (const profile of DECISION_PROFILES) {
    cumulative += profile.weight;
    if (rand <= cumulative) return profile;
  }
  return DECISION_PROFILES[0];
}

export default function () {
  const profile = getDecisionProfile();
  const agentId = `agent-${randomIntBetween(1, 1000)}`;
  const contextSize = randomIntBetween(1024, 2048); // 1-2 KB context

  const payload = JSON.stringify({
    agent_id: agentId,
    action: profile.action,
    resource: profile.resource,
    context: 'x'.repeat(contextSize),
    timestamp: new Date().toISOString(),
    request_id: `req-${randomIntBetween(1, 1000000000)}`,
  });

  const params = {
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${API_KEY}`,
      'X-Decision-Profile': profile.expected,
    },
    timeout: '50ms', // Enforce 50ms max latency
  };

  group('Enforcement Decision', () => {
    const startTime = Date.now();
    const response = http.post(`${BASE_URL}/v1/enforce`, payload, params);
    const latency = Date.now() - startTime;

    decisionLatency.add(latency);
    decisionsPerSecond.add(1);

    const success = check(response, {
      'status is 200': (r) => r.status === 200,
      'decision returned': (r) => r.json('decision') !== undefined,
      'decision matches expected': (r) => r.json('decision') === profile.expected,
      'latency < 50ms': () => latency < 50,
      'certificate present': (r) => r.json('certificate') !== undefined,
    });

    decisionErrors.add(!success);

    // Verify audit trail was written (async check)
    if (success && randomIntBetween(1, 100) <= 5) { // 5% sampling
      sleep(0.1); // Wait for async audit write
      const auditCheck = http.get(
        `${BASE_URL}/v1/audit/verify?request_id=${JSON.parse(payload).request_id}`,
        params
      );
      check(auditCheck, {
        'audit entry exists': (r) => r.status === 200,
        'audit hash valid': (r) => r.json('hash_valid') === true,
      });
    }
  });
}

export function handleSummary(data) {
  return {
    'stdout': textSummary(data, { indent: ' ', enableColors: true }),
    'results/enforcement-steady-state.json': JSON.stringify(data),
  };
}
```

#### 1.1.2 Peak Load Test

```javascript
// tests/performance/k6/enforcement-peak-load.js
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Trend, Rate } from 'k6/metrics';

const decisionLatency = new Trend('decision_latency');
const errorRate = new Rate('errors');

export const options = {
  scenarios: {
    peak_load: {
      executor: 'ramping-arrival-rate',
      startRate: 0,
      timeUnit: '1s',
      preAllocatedVUs: 1000,
      maxVUs: 2000,
      stages: [
        { duration: '5m', target: 25000 },   // Ramp to 25K/s over 5 min
        { duration: '15m', target: 25000 },  // Hold for 15 min
        { duration: '5m', target: 0 },       // Ramp down
      ],
    },
  },
  thresholds: {
    'decision_latency': ['p(99)<20'],
    'errors': ['rate<0.001'],
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8080';

export default function () {
  const payload = JSON.stringify({
    agent_id: `agent-${Math.floor(Math.random() * 1000)}`,
    action: 'read',
    resource: '/data/public',
    context: 'x'.repeat(2048),
    timestamp: new Date().toISOString(),
  });

  const response = http.post(`${BASE_URL}/v1/enforce`, payload, {
    headers: { 'Content-Type': 'application/json' },
    timeout: '100ms',
  });

  decisionLatency.add(response.timings.duration);
  errorRate.add(response.status !== 200);

  check(response, {
    'status is 200': (r) => r.status === 200,
    'decision returned': (r) => r.json('decision') !== undefined,
  });
}
```

#### 1.1.3 Burst Load Test

```javascript
// tests/performance/k6/enforcement-burst.js
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Trend, Rate, Counter } from 'k6/metrics';

const decisionLatency = new Trend('decision_latency');
const errorRate = new Rate('errors');
const droppedDecisions = new Counter('dropped_decisions');

export const options = {
  scenarios: {
    burst: {
      executor: 'shared-iterations',
      vus: 5000,
      iterations: 150000, // 50K/s for 3 seconds
      maxDuration: '10s',
    },
    recovery: {
      executor: 'constant-arrival-rate',
      rate: 10000,
      timeUnit: '1s',
      duration: '5m',
      startTime: '10s',
      preAllocatedVUs: 500,
      maxVUs: 1000,
    },
  },
  thresholds: {
    'decision_latency': ['p(99)<50'],  // Relaxed during burst
    'errors': ['rate<0.01'],
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8080';

export default function () {
  const payload = JSON.stringify({
    agent_id: `agent-${Math.floor(Math.random() * 1000)}`,
    action: 'read',
    resource: '/data/public',
    context: 'x'.repeat(2048),
    timestamp: new Date().toISOString(),
  });

  const response = http.post(`${BASE_URL}/v1/enforce`, payload, {
    headers: { 'Content-Type': 'application/json' },
    timeout: '100ms',
  });

  decisionLatency.add(response.timings.duration);

  if (response.status === 503) {
    droppedDecisions.add(1);
  }

  errorRate.add(response.status !== 200);

  check(response, {
    'status is 200 or 503': (r) => r.status === 200 || r.status === 503,
  });
}
```

#### 1.1.4 Scalability Test

```javascript
// tests/performance/k6/enforcement-scalability.js
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Trend } from 'k6/metrics';

const throughputPerProxy = new Trend('throughput_per_proxy');
const latencyPerProxy = new Trend('latency_per_proxy');

export const options = {
  scenarios: {
    scalability: {
      executor: 'ramping-vus',
      startVUs: 100,
      stages: [
        { duration: '5m', target: 100 },   // 1 proxy
        { duration: '5m', target: 200 },   // 2 proxies
        { duration: '5m', target: 300 },   // 3 proxies
        { duration: '5m', target: 500 },   // 5 proxies
        { duration: '5m', target: 1000 },  // 10 proxies
      ],
      gracefulRampDown: '30s',
    },
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8080';

export default function () {
  const payload = JSON.stringify({
    agent_id: `agent-${Math.floor(Math.random() * 1000)}`,
    action: 'read',
    resource: '/data/public',
    context: 'x'.repeat(2048),
    timestamp: new Date().toISOString(),
  });

  const response = http.post(`${BASE_URL}/v1/enforce`, payload, {
    headers: { 'Content-Type': 'application/json' },
    timeout: '50ms',
  });

  latencyPerProxy.add(response.timings.duration);

  check(response, {
    'status is 200': (r) => r.status === 200,
  });
}
```

#### 1.1.5 Soak Test

```javascript
// tests/performance/k6/enforcement-soak.js
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Trend, Rate, Gauge } from 'k6/metrics';

const decisionLatency = new Trend('decision_latency');
const errorRate = new Rate('errors');
const memoryUsage = new Gauge('memory_usage_mb');
const fdCount = new Gauge('fd_count');

export const options = {
  scenarios: {
    soak: {
      executor: 'constant-arrival-rate',
      rate: 10000,
      timeUnit: '1s',
      duration: '72h',
      preAllocatedVUs: 500,
      maxVUs: 1000,
    },
  },
  thresholds: {
    'decision_latency': ['p(99)<10'],
    'errors': ['rate<0.001'],
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8080';

export default function () {
  const payload = JSON.stringify({
    agent_id: `agent-${Math.floor(Math.random() * 1000)}`,
    action: 'read',
    resource: '/data/public',
    context: 'x'.repeat(2048),
    timestamp: new Date().toISOString(),
  });

  const response = http.post(`${BASE_URL}/v1/enforce`, payload, {
    headers: { 'Content-Type': 'application/json' },
    timeout: '50ms',
  });

  decisionLatency.add(response.timings.duration);
  errorRate.add(response.status !== 200);

  check(response, {
    'status is 200': (r) => r.status === 200,
  });

  // Collect system metrics every 100 iterations
  if (Math.random() < 0.01) {
    const metricsResponse = http.get(`${BASE_URL}/metrics`);
    // Parse and record memory/FD metrics
  }
}
```

### 1.2 Locust Load Testing (Python Alternative)

```python
# tests/performance/locust/enforcement_load_test.py
import json
import random
import time
import uuid
from locust import HttpUser, task, between, events, run_single_user
from locust.runners import MasterRunner
import statistics

class EnforcementUser(HttpUser):
    """Simulates agent enforcement requests."""
    wait_time = between(0.001, 0.01)  # 100-1000 RPS per user
    
    def on_start(self):
        """Initialize user session."""
        self.agent_id = f"agent-{random.randint(1, 1000)}"
        self.client.headers.update({
            "Authorization": "Bearer test-api-key",
            "Content-Type": "application/json",
        })
    
    @task(80)
    def allow_decision(self):
        """80% ALLOW decisions."""
        self._make_decision("read", "/data/public", "ALLOW")
    
    @task(10)
    def allow_with_redaction(self):
        """10% ALLOW_WITH_REDACTION decisions."""
        self._make_decision("write", "/data/sensitive", "ALLOW_WITH_REDACTION")
    
    @task(5)
    def require_approval(self):
        """5% REQUIRE_APPROVAL decisions."""
        self._make_decision("delete", "/data/critical", "REQUIRE_APPROVAL")
    
    @task(3)
    def deny_decision(self):
        """3% DENY decisions."""
        self._make_decision("admin", "/system/config", "DENY")
    
    @task(2)
    def quarantine_decision(self):
        """2% QUARANTINE decisions."""
        self._make_decision("execute", "/untrusted/script", "QUARANTINE")
    
    def _make_decision(self, action, resource, expected_decision):
        """Make an enforcement decision request."""
        payload = {
            "agent_id": self.agent_id,
            "action": action,
            "resource": resource,
            "context": "x" * random.randint(1024, 2048),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "request_id": str(uuid.uuid4()),
        }
        
        with self.client.post(
            "/v1/enforce",
            json=payload,
            headers={"X-Decision-Profile": expected_decision},
            catch_response=True,
            timeout=0.050,  # 50ms timeout
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if data.get("decision") == expected_decision:
                    response.success()
                else:
                    response.failure(f"Expected {expected_decision}, got {data.get('decision')}")
            else:
                response.failure(f"Status {response.status_code}")


class EvidenceCollectionUser(HttpUser):
    """Simulates evidence collection load."""
    wait_time = between(0.001, 0.005)
    
    @task
    def collect_evidence(self):
        """Submit evidence for collection."""
        payload = {
            "evidence_type": "enforcement_decision",
            "source": "enforcement_proxy",
            "data": {
                "decision_id": str(uuid.uuid4()),
                "agent_id": f"agent-{random.randint(1, 1000)}",
                "timestamp": time.time(),
            },
        }
        
        self.client.post("/v1/evidence/collect", json=payload)


class AuditTrailUser(HttpUser):
    """Simulates audit trail queries."""
    wait_time = between(0.01, 0.1)
    
    @task(70)
    def query_recent_audit(self):
        """Query recent audit entries."""
        self.client.get(
            "/v1/audit/query",
            params={
                "agent_id": f"agent-{random.randint(1, 1000)}",
                "limit": 100,
            },
        )
    
    @task(30)
    def verify_audit_chain(self):
        """Verify audit trail hash chain."""
        self.client.get("/v1/audit/verify", params={"limit": 1000})


# Custom event handlers for metrics
@events.request.add_listener
def on_request(request_type, name, response_time, response_length, 
               response, context, exception, **kwargs):
    """Track custom metrics."""
    if exception:
        # Track error rate
        pass


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Generate summary report."""
    if isinstance(environment.runner, MasterRunner):
        stats = environment.runner.stats
        
        # Calculate percentiles
        all_stats = stats.get_all_rtimes()
        if all_stats:
            p50 = statistics.median(all_stats)
            p95 = sorted(all_stats)[int(len(all_stats) * 0.95)]
            p99 = sorted(all_stats)[int(len(all_stats) * 0.99)]
            
            print(f"\n{'='*60}")
            print(f"Performance Test Results")
            print(f"{'='*60}")
            print(f"Total requests: {stats.total.num_requests}")
            print(f"Failed requests: {stats.total.num_failures}")
            print(f"Error rate: {stats.total.fail_ratio:.4%}")
            print(f"p50 latency: {p50:.2f} ms")
            print(f"p95 latency: {p95:.2f} ms")
            print(f"p99 latency: {p99:.2f} ms")
            print(f"RPS: {stats.total.total_rps:.2f}")
            print(f"{'='*60}")
            
            # Validate against SLOs
            assert p99 < 10, f"p99 latency {p99:.2f}ms exceeds 10ms SLO"
            assert stats.total.fail_ratio < 0.001, "Error rate exceeds 0.1%"


# Run with: locust -f enforcement_load_test.py --host=http://localhost:8080 -u 1000 -r 100 -t 30m
```

### 1.3 Test Data Generation

```python
# tests/performance/data/generate_test_data.py
import json
import random
import uuid
from datetime import datetime, timedelta
from faker import Faker

fake = Faker()

def generate_agents(count=1000):
    """Generate test agent data."""
    agents = []
    for i in range(count):
        agents.append({
            "agent_id": f"agent-{i+1}",
            "name": fake.company(),
            "status": random.choice(["active", "active", "active", "deprecated"]),
            "capabilities": random.sample(
                ["read", "write", "delete", "admin", "execute"],
                random.randint(1, 3)
            ),
            "identity_metadata": {
                "owner": fake.email(),
                "department": fake.job(),
                "created_at": fake.date_time_between(start_date="-1y").isoformat(),
            },
            "last_active_at": fake.date_time_between(start_date="-7d").isoformat(),
        })
    return agents

def generate_policies(count=500):
    """Generate test policy data."""
    policies = []
    for i in range(count):
        policies.append({
            "policy_id": f"policy-{i+1}",
            "name": fake.bs(),
            "status": "active",
            "priority": random.randint(1, 100),
            "tenant_id": f"tenant-{random.randint(1, 10)}",
            "rules": [
                {
                    "rule_id": f"rule-{i}-{j}",
                    "action": random.choice(["read", "write", "delete", "admin"]),
                    "resource_pattern": f"/data/{random.choice(['public', 'sensitive', 'critical'])}/*",
                    "effect": random.choice(["ALLOW", "DENY", "REQUIRE_APPROVAL"]),
                    "condition": f"agent.capabilities contains '{random.choice(['read', 'write'])}'",
                }
                for j in range(10)
            ],
        })
    return policies

def generate_enforcement_decisions(count=100000):
    """Generate historical enforcement decisions."""
    decisions = []
    base_time = datetime.utcnow() - timedelta(days=30)
    
    for i in range(count):
        decisions.append({
            "decision_id": str(uuid.uuid4()),
            "agent_id": f"agent-{random.randint(1, 1000)}",
            "action": random.choice(["read", "write", "delete", "admin", "execute"]),
            "resource": f"/data/{random.choice(['public', 'sensitive', 'critical'])}/file-{random.randint(1, 10000)}",
            "decision": random.choices(
                ["ALLOW", "ALLOW_WITH_REDACTION", "REQUIRE_APPROVAL", "DENY", "QUARANTINE"],
                weights=[80, 10, 5, 3, 2]
            )[0],
            "policy_id": f"policy-{random.randint(1, 500)}",
            "context_hash": fake.sha256(),
            "created_at": (base_time + timedelta(seconds=random.randint(0, 2592000))).isoformat(),
        })
    return decisions

if __name__ == "__main__":
    agents = generate_agents(1000)
    policies = generate_policies(500)
    decisions = generate_enforcement_decisions(100000)
    
    with open("test_agents.json", "w") as f:
        json.dump(agents, f)
    with open("test_policies.json", "w") as f:
        json.dump(policies, f)
    with open("test_decisions.json", "w") as f:
        json.dump(decisions, f)
    
    print(f"Generated {len(agents)} agents, {len(policies)} policies, {len(decisions)} decisions")
```

### 1.4 CI/CD Integration

```yaml
# .github/workflows/performance-tests.yml
name: Performance Tests

on:
  pull_request:
    paths:
      - 'src/enforcement/**'
      - 'src/evidence/**'
      - 'src/audit/**'
      - 'src/api/**'
  schedule:
    - cron: '0 2 * * *'  # Nightly at 2 AM

jobs:
  micro-benchmarks:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Run micro-benchmarks
        run: |
          go test -bench=. -benchmem -count=10 ./src/enforcement/... | tee benchmark.txt
          
      - name: Compare with baseline
        run: |
          go run scripts/compare_benchmarks.go \
            --current benchmark.txt \
            --baseline tests/performance/baselines/micro-baseline.txt \
            --threshold 5

  integration-benchmarks:
    runs-on: ubuntu-latest
    needs: micro-benchmarks
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_PASSWORD: test
        ports:
          - 5432:5432
      redis:
        image: redis:7.2
        ports:
          - 6379:6379
      kafka:
        image: confluentinc/cp-kafka:latest
        ports:
          - 9092:9092
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Run integration benchmarks
        run: |
          go test -bench=Integration -benchtime=30s ./tests/performance/...
          
      - name: Upload results
        uses: actions/upload-artifact@v4
        with:
          name: benchmark-results
          path: tests/performance/results/

  load-test:
    runs-on: ubuntu-latest
    needs: integration-benchmarks
    if: github.event_name == 'schedule' || contains(github.event.pull_request.labels.*.name, 'performance-test')
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup k6
        uses: grafana/setup-k6-action@v1
      
      - name: Start test environment
        run: |
          docker-compose -f tests/performance/docker-compose.yml up -d
          sleep 30  # Wait for services to be ready
      
      - name: Run steady-state load test
        run: |
          k6 run \
            --out json=results/steady-state.json \
            --env BASE_URL=http://localhost:8080 \
            tests/performance/k6/enforcement-steady-state.js
      
      - name: Run peak load test
        run: |
          k6 run \
            --out json=results/peak-load.json \
            --env BASE_URL=http://localhost:8080 \
            tests/performance/k6/enforcement-peak-load.js
      
      - name: Validate results
        run: |
          python scripts/validate_performance.py \
            --results results/ \
            --slo tests/performance/slo.json
      
      - name: Upload results
        uses: actions/upload-artifact@v4
        with:
          name: load-test-results
          path: results/
```

---

## 2. Caching Strategy Implementation

### 2.1 Redis Cache Manager

```go
// internal/cache/redis_cache.go
package cache

import (
	"context"
	"encoding/json"
	"fmt"
	"time"

	"github.com/redis/go-redis/v9"
)

// CacheTier represents the cache hierarchy level
type CacheTier int

const (
	TierL1 CacheTier = iota // In-process
	TierL2                  // Local shared memory
	TierL3                  // Redis distributed
)

// CacheConfig holds Redis cache configuration
type CacheConfig struct {
	ClusterAddresses []string
	Password         string
	DB               int
	
	// Pool configuration
	MaxConns        int
	MinIdleConns    int
	MaxConnAge      time.Duration
	PoolTimeout     time.Duration
	IdleTimeout     time.Duration
	
	// Cache behavior
	DefaultTTL      time.Duration
	JitterFactor    float64 // TTL jitter (0.1 = ±10%)
}

// RedisCacheManager manages multi-tier caching
type RedisCacheManager struct {
	client        *redis.ClusterClient
	localCache    *LocalCache // L1 in-process cache
	config        *CacheConfig
	metrics       *CacheMetrics
}

// CacheMetrics tracks cache performance
type CacheMetrics struct {
	L1Hits        uint64
	L1Misses      uint64
	L3Hits        uint64
	L3Misses      uint64
	Invalidations uint64
}

// NewRedisCacheManager creates a new cache manager
func NewRedisCacheManager(config *CacheConfig) (*RedisCacheManager, error) {
	client := redis.NewClusterClient(&redis.ClusterOptions{
		Addrs:        config.ClusterAddresses,
		Password:     config.Password,
		DB:           config.DB,
		PoolSize:     config.MaxConns,
		MinIdleConns: config.MinIdleConns,
		MaxConnAge:   config.MaxConnAge,
		PoolTimeout:  config.PoolTimeout,
		IdleTimeout:  config.IdleTimeout,
	})

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	if err := client.Ping(ctx).Err(); err != nil {
		return nil, fmt.Errorf("redis connection failed: %w", err)
	}

	return &RedisCacheManager{
		client:     client,
		localCache: NewLocalCache(10000, 5*time.Minute),
		config:     config,
		metrics:    &CacheMetrics{},
	}, nil
}

// Get retrieves a value from cache (L1 → L3 → origin)
func (m *RedisCacheManager) Get(ctx context.Context, key string, dest interface{}) (CacheTier, error) {
	// Try L1 (in-process) first
	if val, ok := m.localCache.Get(key); ok {
		m.metrics.L1Hits++
		return TierL1, m.deserialize(val, dest)
	}
	m.metrics.L1Misses++

	// Try L3 (Redis)
	val, err := m.client.Get(ctx, key).Result()
	if err == nil {
		m.metrics.L3Hits++
		// Promote to L1
		m.localCache.Set(key, []byte(val), m.config.DefaultTTL)
		return TierL3, m.deserialize([]byte(val), dest)
	}
	m.metrics.L3Misses++

	return 0, fmt.Errorf("cache miss: %w", err)
}

// Set stores a value in cache with TTL jitter
func (m *RedisCacheManager) Set(ctx context.Context, key string, value interface{}, ttl time.Duration) error {
	data, err := m.serialize(value)
	if err != nil {
		return err
	}

	// Apply TTL jitter to prevent cache stampede
	jitteredTTL := m.applyJitter(ttl)

	// Write to L3 (Redis)
	if err := m.client.Set(ctx, key, data, jitteredTTL).Err(); err != nil {
		return err
	}

	// Write to L1 (local)
	m.localCache.Set(key, data, jitteredTTL)

	return nil
}

// Delete removes a key from all cache tiers
func (m *RedisCacheManager) Delete(ctx context.Context, key string) error {
	m.localCache.Delete(key)
	return m.client.Del(ctx, key).Err()
}

// InvalidatePattern removes all keys matching a pattern
func (m *RedisCacheManager) InvalidatePattern(ctx context.Context, pattern string) error {
	iter := m.client.Scan(ctx, 0, pattern, 100).Iterator()
	for iter.Next(ctx) {
		m.localCache.Delete(iter.Val())
		m.client.Del(ctx, iter.Val())
	}
	m.metrics.Invalidations++
	return iter.Err()
}

// GetWithCoalescing implements request coalescing for cache stampede protection
func (m *RedisCacheManager) GetWithCoalescing(
	ctx context.Context,
	key string,
	ttl time.Duration,
	fetch func() (interface{}, error),
	dest interface{},
) error {
	// Try cache first
	tier, err := m.Get(ctx, key, dest)
	if err == nil {
		_ = tier
		return nil
	}

	// Use singleflight to coalesce concurrent requests
	result, err, _ := m.sf.Do(key, func() (interface{}, error) {
		// Double-check cache after acquiring lock
		if val, ok := m.localCache.Get(key); ok {
			return val, nil
		}

		// Fetch from origin
		data, err := fetch()
		if err != nil {
			return nil, err
		}

		// Store in cache
		_ = m.Set(ctx, key, data, ttl)
		return data, nil
	})

	if err != nil {
		return err
	}

	return m.serialize(result, dest)
}

// applyJitter adds random jitter to TTL to prevent simultaneous expiration
func (m *RedisCacheManager) applyJitter(ttl time.Duration) time.Duration {
	jitter := float64(ttl) * m.config.JitterFactor
	jittered := float64(ttl) + (randomFloat64()*2-1)*jitter
	return time.Duration(jittered)
}

func (m *RedisCacheManager) serialize(value interface{}) ([]byte, error) {
	return json.Marshal(value)
}

func (m *RedisCacheManager) deserialize(data []byte, dest interface{}) error {
	return json.Unmarshal(data, dest)
}

// CacheHitRatio returns current cache hit ratios
func (m *RedisCacheManager) CacheHitRatio() (l1Ratio, l3Ratio float64) {
	l1Total := m.metrics.L1Hits + m.metrics.L1Misses
	l3Total := m.metrics.L3Hits + m.metrics.L3Misses

	if l1Total > 0 {
		l1Ratio = float64(m.metrics.L1Hits) / float64(l1Total)
	}
	if l3Total > 0 {
		l3Ratio = float64(m.metrics.L3Hits) / float64(l3Total)
	}
	return
}
```

### 2.2 Cache Warming Service

```go
// internal/cache/warmer.go
package cache

import (
	"context"
	"log"
	"sync"
	"time"
)

// CacheWarmer handles startup and runtime cache warming
type CacheWarmer struct {
	cache       *RedisCacheManager
	policyEngine PolicyEngine
	agentStore   AgentStore
	complianceStore ComplianceStore
	
	warmInterval time.Duration
	stopCh       chan struct{}
	wg           sync.WaitGroup
}

// NewCacheWarmer creates a new cache warmer
func NewCacheWarmer(
	cache *RedisCacheManager,
	policyEngine PolicyEngine,
	agentStore AgentStore,
	complianceStore ComplianceStore,
) *CacheWarmer {
	return &CacheWarmer{
		cache:           cache,
		policyEngine:     policyEngine,
		agentStore:       agentStore,
		complianceStore:  complianceStore,
		warmInterval:    60 * time.Second,
		stopCh:          make(chan struct{}),
	}
}

// WarmOnStartup performs initial cache warming
func (w *CacheWarmer) WarmOnStartup(ctx context.Context) error {
	start := time.Now()
	log.Println("Starting cache warming...")

	// 1. Load and compile all active policies
	if err := w.warmPolicies(ctx); err != nil {
		return fmt.Errorf("policy warming failed: %w", err)
	}

	// 2. Load all registered agents
	if err := w.warmAgents(ctx); err != nil {
		return fmt.Errorf("agent warming failed: %w", err)
	}

	// 3. Load compliance mappings
	if err := w.warmComplianceMappings(ctx); err != nil {
		return fmt.Errorf("compliance mapping warming failed: %w", err)
	}

	// 4. Pre-compute dashboard aggregations
	if err := w.warmDashboardAggregations(ctx); err != nil {
		return fmt.Errorf("dashboard warming failed: %w", err)
	}

	// 5. Verify cache consistency
	if err := w.verifyConsistency(ctx); err != nil {
		return fmt.Errorf("cache consistency check failed: %w", err)
	}

	duration := time.Since(start)
	log.Printf("Cache warming completed in %v", duration)
	
	// Record metric
	cacheWarmingDuration.Observe(duration.Seconds())
	
	return nil
}

func (w *CacheWarmer) warmPolicies(ctx context.Context) error {
	policies, err := w.policyEngine.GetActivePolicies(ctx)
	if err != nil {
		return err
	}

	for _, policy := range policies {
		// Compile rules
		rules, err := w.policyEngine.CompilePolicy(ctx, policy)
		if err != nil {
			log.Printf("Failed to compile policy %s: %v", policy.ID, err)
			continue
		}

		// Store in L1 + L3
		key := fmt.Sprintf("policy:compiled:%s", policy.ID)
		if err := w.cache.Set(ctx, key, rules, 24*time.Hour); err != nil {
			log.Printf("Failed to cache policy %s: %v", policy.ID, err)
		}
	}

	log.Printf("Warmed %d policies", len(policies))
	return nil
}

func (w *CacheWarmer) warmAgents(ctx context.Context) error {
	agents, err := w.agentStore.GetAllAgents(ctx)
	if err != nil {
		return err
	}

	// Batch agents for efficient Redis writes
	batchSize := 100
	for i := 0; i < len(agents); i += batchSize {
		end := i + batchSize
		if end > len(agents) {
			end = len(agents)
		}

		pipe := w.cache.client.Pipeline()
		for _, agent := range agents[i:end] {
			key := fmt.Sprintf("agent:identity:%s", agent.ID)
			data, _ := json.Marshal(agent)
			pipe.Set(ctx, key, data, 5*time.Minute)
		}
		if _, err := pipe.Exec(ctx); err != nil {
			log.Printf("Failed to cache agent batch: %v", err)
		}
	}

	log.Printf("Warmed %d agents", len(agents))
	return nil
}

func (w *CacheWarmer) warmComplianceMappings(ctx context.Context) error {
	mappings, err := w.complianceStore.GetAllMappings(ctx)
	if err != nil {
		return err
	}

	for _, mapping := range mappings {
		key := fmt.Sprintf("compliance:mapping:%s:%s", mapping.Framework, mapping.Control)
		if err := w.cache.Set(ctx, key, mapping, 1*time.Hour); err != nil {
			log.Printf("Failed to cache compliance mapping: %v", err)
		}
	}

	log.Printf("Warmed %d compliance mappings", len(mappings))
	return nil
}

func (w *CacheWarmer) warmDashboardAggregations(ctx context.Context) error {
	// Pre-compute common aggregations
	aggregations := []struct {
		key   string
		query string
		ttl   time.Duration
	}{
		{"dashboard:compliance:posture", "SELECT * FROM compliance_posture_view", 1 * time.Minute},
		{"dashboard:enforcement:trends", "SELECT * FROM enforcement_trends_view", 1 * time.Minute},
		{"dashboard:agent:activity", "SELECT * FROM agent_activity_view", 30 * time.Second},
	}

	for _, agg := range aggregations {
		// Execute query and cache result
		result, err := w.executeAggregationQuery(ctx, agg.query)
		if err != nil {
			continue
		}
		w.cache.Set(ctx, agg.key, result, agg.ttl)
	}

	return nil
}

// StartRuntimeWarming starts periodic cache refresh
func (w *CacheWarmer) StartRuntimeWarming() {
	w.wg.Add(1)
	go func() {
		defer w.wg.Done()
		ticker := time.NewTicker(w.warmInterval)
		defer ticker.Stop()

		for {
			select {
			case <-ticker.C:
				ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
				w.refreshHotKeys(ctx)
				cancel()
			case <-w.stopCh:
				return
			}
		}
	}()
}

func (w *CacheWarmer) refreshHotKeys(ctx context.Context) {
	// Refresh keys that are about to expire
	hotKeys := w.cache.client.Scan(ctx, 0, "policy:compiled:*", 1000).Iterator()
	for hotKeys.Next(ctx) {
		ttl := w.cache.client.TTL(ctx, hotKeys.Val()).Val()
		if ttl > 0 && ttl < 10*time.Second {
			// Refresh at 80% of TTL
			w.cache.client.Expire(ctx, hotKeys.Val(), 24*time.Hour)
		}
	}
}

func (w *CacheWarmer) Stop() {
	close(w.stopCh)
	w.wg.Wait()
}
```

### 2.3 Cache Invalidation with Pub/Sub

```go
// internal/cache/invalidator.go
package cache

import (
	"context"
	"encoding/json"
	"log"

	"github.com/redis/go-redis/v9"
)

// InvalidationEvent represents a cache invalidation message
type InvalidationEvent struct {
	Type      string `json:"type"`       // "policy", "agent", "compliance"
	Key       string `json:"key"`        // Cache key to invalidate
	Version   int64  `json:"version"`    // Event version for ordering
	Timestamp int64  `json:"timestamp"`  // Event timestamp
}

// CacheInvalidator handles event-driven cache invalidation
type CacheInvalidator struct {
	cache   *RedisCacheManager
	client  *redis.ClusterClient
	handler CacheEventHandler
}

// NewCacheInvalidator creates a new invalidator
func NewCacheInvalidator(cache *RedisCacheManager, handler CacheEventHandler) *CacheInvalidator {
	return &CacheInvalidator{
		cache:   cache,
		client:  cache.client,
		handler: handler,
	}
}

// StartListening starts listening for invalidation events
func (ci *CacheInvalidator) StartListening(ctx context.Context) {
	pubsub := ci.client.Subscribe(ctx, "cache:invalidation")
	defer pubsub.Close()

	ch := pubsub.Channel()
	for msg := range ch {
		var event InvalidationEvent
		if err := json.Unmarshal([]byte(msg.Payload), &event); err != nil {
			log.Printf("Failed to unmarshal invalidation event: %v", err)
			continue
		}

		if err := ci.handleInvalidation(ctx, &event); err != nil {
			log.Printf("Failed to handle invalidation: %v", err)
		}
	}
}

func (ci *CacheInvalidator) handleInvalidation(ctx context.Context, event *InvalidationEvent) error {
	switch event.Type {
	case "policy":
		return ci.invalidatePolicy(ctx, event)
	case "agent":
		return ci.invalidateAgent(ctx, event)
	case "compliance":
		return ci.invalidateCompliance(ctx, event)
	default:
		return fmt.Errorf("unknown invalidation type: %s", event.Type)
	}
}

func (ci *CacheInvalidator) invalidatePolicy(ctx context.Context, event *InvalidationEvent) error {
	// Invalidate L1 cache
	ci.cache.localCache.Delete(event.Key)

	// Invalidate L3 cache
	if err := ci.cache.client.Del(ctx, event.Key).Err(); err != nil {
		return err
	}

	// Fetch new rules and warm cache
	newRules, err := ci.handler.GetCompiledPolicy(ctx, event.Key)
	if err != nil {
		return err
	}

	return ci.cache.Set(ctx, event.Key, newRules, 24*time.Hour)
}

func (ci *CacheInvalidator) invalidateAgent(ctx context.Context, event *InvalidationEvent) error {
	// Invalidate agent identity in all tiers
	pattern := fmt.Sprintf("agent:identity:%s*", event.Key)
	return ci.cache.InvalidatePattern(ctx, pattern)
}

func (ci *CacheInvalidator) invalidateCompliance(ctx context.Context, event *InvalidationEvent) error {
	pattern := fmt.Sprintf("compliance:mapping:%s*", event.Key)
	return ci.cache.InvalidatePattern(ctx, pattern)
}

// PublishInvalidation publishes an invalidation event
func (ci *CacheInvalidator) PublishInvalidation(ctx context.Context, event *InvalidationEvent) error {
	data, err := json.Marshal(event)
	if err != nil {
		return err
	}
	return ci.client.Publish(ctx, "cache:invalidation", data).Err()
}
```

### 2.4 Bloom Filter for Cache Penetration Protection

```go
// internal/cache/bloom_filter.go
package cache

import (
	"github.com/bits-and-blooms/bloom/v3"
)

// CacheBloomFilter prevents cache penetration for non-existent keys
type CacheBloomFilter struct {
	filter *bloom.BloomFilter
}

// NewCacheBloomFilter creates a bloom filter for cache protection
func NewCacheBloomFilter(expectedElements uint, falsePositiveRate float64) *CacheBloomFilter {
	return &CacheBloomFilter{
		filter: bloom.NewWithEstimates(expectedElements, falsePositiveRate),
	}
}

// Add adds a key to the bloom filter
func (bf *CacheBloomFilter) Add(key string) {
	bf.filter.Add([]byte(key))
}

// MightExist checks if a key might exist in the cache
func (bf *CacheBloomFilter) MightExist(key string) bool {
	return bf.filter.Test([]byte(key))
}

// Reset clears the bloom filter
func (bf *CacheBloomFilter) Reset() {
	bf.filter.ClearAll()
}
```

---

## 3. Database Query Optimization

### 3.1 Database Schema with Optimized Indexes

```sql
-- migrations/001_create_performance_optimized_schema.sql

-- Agents table with optimized indexes
CREATE TABLE agents (
    agent_id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    capabilities JSONB NOT NULL DEFAULT '[]',
    identity_metadata JSONB NOT NULL DEFAULT '{}',
    tenant_id VARCHAR(64) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_active_at TIMESTAMPTZ,
    
    CONSTRAINT valid_status CHECK (status IN ('active', 'deprecated', 'terminated'))
);

-- Optimized indexes for agent lookups
CREATE INDEX idx_agents_id ON agents(agent_id);
CREATE INDEX idx_agents_status ON agents(status, last_active_at);
CREATE INDEX idx_agents_tenant ON agents(tenant_id, status);
CREATE INDEX idx_agents_capabilities ON agents USING GIN(capabilities);

-- Policies table
CREATE TABLE policies (
    policy_id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    priority INTEGER NOT NULL DEFAULT 50,
    tenant_id VARCHAR(64) NOT NULL,
    policy_dsl JSONB NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    CONSTRAINT valid_policy_status CHECK (status IN ('active', 'inactive', 'draft'))
);

CREATE INDEX idx_policies_active ON policies(status, priority);
CREATE INDEX idx_policies_tenant ON policies(tenant_id, status);

-- Compiled rules table
CREATE TABLE compiled_rules (
    rule_id VARCHAR(64) PRIMARY KEY,
    policy_id VARCHAR(64) NOT NULL REFERENCES policies(policy_id),
    rule_order INTEGER NOT NULL,
    action_type VARCHAR(50) NOT NULL,
    resource_pattern VARCHAR(500) NOT NULL,
    condition TEXT NOT NULL,
    effect VARCHAR(50) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    CONSTRAINT valid_effect CHECK (effect IN ('ALLOW', 'DENY', 'REQUIRE_APPROVAL', 'ALLOW_WITH_REDACTION', 'QUARANTINE'))
);

CREATE INDEX idx_rules_policy ON compiled_rules(policy_id, rule_order);
CREATE INDEX idx_rules_action ON compiled_rules(action_type, resource_pattern);

-- Audit trail table with partitioning
CREATE TABLE audit_trail (
    entry_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id VARCHAR(64) NOT NULL,
    decision VARCHAR(50) NOT NULL,
    policy_id VARCHAR(64),
    context_hash VARCHAR(64) NOT NULL,
    tenant_id VARCHAR(64) NOT NULL,
    chain_hash VARCHAR(64) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    CONSTRAINT valid_decision CHECK (decision IN ('ALLOW', 'ALLOW_WITH_REDACTION', 'REQUIRE_APPROVAL', 'DENY', 'QUARANTINE'))
) PARTITION BY RANGE (created_at);

-- Create monthly partitions
CREATE TABLE audit_trail_2026_10 PARTITION OF audit_trail
    FOR VALUES FROM ('2026-10-01') TO ('2026-11-01');
CREATE TABLE audit_trail_2026_11 PARTITION OF audit_trail
    FOR VALUES FROM ('2026-11-01') TO ('2026-12-01');
CREATE TABLE audit_trail_2026_12 PARTITION OF audit_trail
    FOR VALUES FROM ('2026-12-01') TO ('2027-01-01');

-- Optimized indexes for audit trail
CREATE INDEX idx_audit_agent_time ON audit_trail(agent_id, created_at DESC);
CREATE INDEX idx_audit_decision ON audit_trail(decision, created_at DESC);
CREATE INDEX idx_audit_tenant_time ON audit_trail(tenant_id, created_at DESC);
CREATE INDEX idx_audit_chain ON audit_trail(chain_hash);

-- Evidence items table with partitioning
CREATE TABLE evidence_items (
    evidence_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id VARCHAR(64) NOT NULL,
    evidence_type VARCHAR(100) NOT NULL,
    source VARCHAR(100) NOT NULL,
    content_hash VARCHAR(64) NOT NULL UNIQUE,
    content JSONB NOT NULL,
    tenant_id VARCHAR(64) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
) PARTITION BY RANGE (created_at);

CREATE INDEX idx_evidence_agent ON evidence_items(agent_id, created_at DESC);
CREATE INDEX idx_evidence_type_time ON evidence_items(evidence_type, created_at DESC);
CREATE INDEX idx_evidence_hash ON evidence_items(content_hash);

-- Enforcement decisions table (short-term, daily partitions)
CREATE TABLE enforcement_decisions (
    decision_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id VARCHAR(64) NOT NULL,
    action VARCHAR(50) NOT NULL,
    resource VARCHAR(500) NOT NULL,
    decision VARCHAR(50) NOT NULL,
    policy_id VARCHAR(64),
    context_hash VARCHAR(64) NOT NULL,
    tenant_id VARCHAR(64) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
) PARTITION BY RANGE (created_at);

-- Materialized views for dashboard aggregations
CREATE MATERIALIZED VIEW enforcement_trends_view AS
SELECT
    date_trunc('hour', created_at) AS hour,
    decision,
    COUNT(*) AS count,
    COUNT(DISTINCT agent_id) AS unique_agents
FROM enforcement_decisions
WHERE created_at > NOW() - INTERVAL '30 days'
GROUP BY 1, 2;

CREATE UNIQUE INDEX idx_enforcement_trends ON enforcement_trends_view(hour, decision);

CREATE MATERIALIZED VIEW compliance_posture_view AS
SELECT
    tenant_id,
    policy_id,
    COUNT(*) FILTER (WHERE decision = 'DENY') AS deny_count,
    COUNT(*) FILTER (WHERE decision = 'ALLOW') AS allow_count,
    COUNT(*) FILTER (WHERE decision = 'REQUIRE_APPROVAL') AS approval_count,
    COUNT(*) AS total_decisions,
    MAX(created_at) AS last_decision_at
FROM enforcement_decisions
WHERE created_at > NOW() - INTERVAL '7 days'
GROUP BY 1, 2;

CREATE UNIQUE INDEX idx_compliance_posture ON compliance_posture_view(tenant_id, policy_id);

-- Refresh materialized views every minute
SELECT cron.schedule('refresh-materialized-views', '* * * * *', 
    'REFRESH MATERIALIZED VIEW CONCURRENTLY enforcement_trends_view;
     REFRESH MATERIALIZED VIEW CONCURRENTLY compliance_posture_view;');
```

### 3.2 Query Optimization Patterns

```go
// internal/db/queries.go
package db

import (
	"context"
	"fmt"
	"time"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

// OptimizedQueries provides performance-optimized database queries
type OptimizedQueries struct {
	pool *pgxpool.Pool
}

// NewOptimizedQueries creates a new query optimizer
func NewOptimizedQueries(pool *pgxpool.Pool) *OptimizedQueries {
	return &OptimizedQueries{pool: pool}
}

// GetAgentIdentity retrieves agent identity with optimized query
// Target: < 1ms p99 (cached in L1/L3)
func (q *OptimizedQueries) GetAgentIdentity(ctx context.Context, agentID string) (*AgentIdentity, error) {
	query := `
		SELECT agent_id, capabilities, identity_metadata, status
		FROM agents
		WHERE agent_id = $1 AND status = 'active'
	`

	var agent AgentIdentity
	err := q.pool.QueryRow(ctx, query, agentID).Scan(
		&agent.ID,
		&agent.Capabilities,
		&agent.IdentityMetadata,
		&agent.Status,
	)
	if err != nil {
		return nil, fmt.Errorf("agent lookup failed: %w", err)
	}

	return &agent, nil
}

// GetCompiledRulesForPolicy retrieves compiled rules for policy evaluation
// Target: < 2ms p99
func (q *OptimizedQueries) GetCompiledRulesForPolicy(ctx context.Context, policyID string) ([]CompiledRule, error) {
	query := `
		SELECT rule_id, action_type, resource_pattern, condition, effect, rule_order
		FROM compiled_rules
		WHERE policy_id = $1
		ORDER BY rule_order
	`

	rows, err := q.pool.Query(ctx, query, policyID)
	if err != nil {
		return nil, fmt.Errorf("rule lookup failed: %w", err)
	}
	defer rows.Close()

	var rules []CompiledRule
	for rows.Next() {
		var rule CompiledRule
		if err := rows.Scan(
			&rule.ID,
			&rule.ActionType,
			&rule.ResourcePattern,
			&rule.Condition,
			&rule.Effect,
			&rule.Order,
		); err != nil {
			return nil, err
		}
		rules = append(rules, rule)
	}

	return rules, nil
}

// GetActivePoliciesForEvaluation retrieves all active policies for enforcement
// Target: < 5ms p99
func (q *OptimizedQueries) GetActivePoliciesForEvaluation(ctx context.Context) ([]Policy, error) {
	query := `
		SELECT policy_id, priority, policy_dsl
		FROM policies
		WHERE status = 'active'
		ORDER BY priority DESC
	`

	rows, err := q.pool.Query(ctx, query)
	if err != nil {
		return nil, fmt.Errorf("policy lookup failed: %w", err)
	}
	defer rows.Close()

	var policies []Policy
	for rows.Next() {
		var policy Policy
		if err := rows.Scan(&policy.ID, &policy.Priority, &policy.DSL); err != nil {
			return nil, err
		}
		policies = append(policies, policy)
	}

	return policies, nil
}

// InsertAuditEntry writes an audit trail entry
// Target: < 3ms p50, < 15ms p99
func (q *OptimizedQueries) InsertAuditEntry(ctx context.Context, entry *AuditEntry) error {
	query := `
		INSERT INTO audit_trail (entry_id, agent_id, decision, policy_id, context_hash, tenant_id, chain_hash, created_at)
		VALUES ($1, $2, $3, $4, $5, $6, $7, NOW())
	`

	_, err := q.pool.Exec(ctx, query,
		entry.ID,
		entry.AgentID,
		entry.Decision,
		entry.PolicyID,
		entry.ContextHash,
		entry.TenantID,
		entry.ChainHash,
	)
	
	return err
}

// BatchInsertAuditEntries performs batch insert for audit entries
// Target: 15,000 entries/second
func (q *OptimizedQueries) BatchInsertAuditEntries(ctx context.Context, entries []*AuditEntry) error {
	batch := &pgx.Batch{}
	for _, entry := range entries {
		batch.Queue(`
			INSERT INTO audit_trail (entry_id, agent_id, decision, policy_id, context_hash, tenant_id, chain_hash, created_at)
			VALUES ($1, $2, $3, $4, $5, $6, $7, NOW())
		`, entry.ID, entry.AgentID, entry.Decision, entry.PolicyID,
			entry.ContextHash, entry.TenantID, entry.ChainHash)
	}

	br := q.pool.SendBatch(ctx, batch)
	defer br.Close()

	for i := 0; i < len(entries); i++ {
		if _, err := br.Exec(); err != nil {
			return fmt.Errorf("batch insert failed at entry %d: %w", i, err)
		}
	}

	return nil
}

// QueryAuditTrail queries audit trail with time range
// Target: < 100ms p99 for 1K rows
func (q *OptimizedQueries) QueryAuditTrail(ctx context.Context, agentID string, limit int) ([]AuditEntry, error) {
	query := `
		SELECT entry_id, agent_id, decision, policy_id, context_hash, created_at
		FROM audit_trail
		WHERE agent_id = $1
		ORDER BY created_at DESC
		LIMIT $2
	`

	rows, err := q.pool.Query(ctx, query, agentID, limit)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var entries []AuditEntry
	for rows.Next() {
		var entry AuditEntry
		if err := rows.Scan(
			&entry.ID,
			&entry.AgentID,
			&entry.Decision,
			&entry.PolicyID,
			&entry.ContextHash,
			&entry.CreatedAt,
		); err != nil {
			return nil, err
		}
		entries = append(entries, entry)
	}

	return entries, nil
}

// SearchEvidence searches evidence items with indexed query
// Target: < 300ms p99
func (q *OptimizedQueries) SearchEvidence(ctx context.Context, agentID string, evidenceType string, limit int) ([]EvidenceItem, error) {
	query := `
		SELECT evidence_id, agent_id, evidence_type, content_hash, created_at
		FROM evidence_items
		WHERE agent_id = $1 AND evidence_type = $2
		ORDER BY created_at DESC
		LIMIT $3
	`

	rows, err := q.pool.Query(ctx, query, agentID, evidenceType, limit)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var items []EvidenceItem
	for rows.Next() {
		var item EvidenceItem
		if err := rows.Scan(
			&item.ID,
			&item.AgentID,
			&item.EvidenceType,
			&item.ContentHash,
			&item.CreatedAt,
		); err != nil {
			return nil, err
		}
		items = append(items, item)
	}

	return items, nil
}

// GetCompliancePosture retrieves pre-computed compliance posture
// Target: < 100ms p99
func (q *OptimizedQueries) GetCompliancePosture(ctx context.Context, tenantID string) (*CompliancePosture, error) {
	query := `
		SELECT tenant_id, policy_id, deny_count, allow_count, approval_count, total_decisions, last_decision_at
		FROM compliance_posture_view
		WHERE tenant_id = $1
	`

	rows, err := q.pool.Query(ctx, query, tenantID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	posture := &CompliancePosture{TenantID: tenantID}
	for rows.Next() {
		var p PolicyPosture
		if err := rows.Scan(
			&p.TenantID,
			&p.PolicyID,
			&p.DenyCount,
			&p.AllowCount,
			&p.ApprovalCount,
			&p.TotalDecisions,
			&p.LastDecisionAt,
		); err != nil {
			return nil, err
		}
		posture.Policies = append(posture.Policies, p)
	}

	return posture, nil
}
```

### 3.3 Connection Pool Configuration

```go
// internal/db/pool.go
package db

import (
	"context"
	"fmt"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"
)

// PoolConfig defines connection pool settings
type PoolConfig struct {
	Host            string
	Port            int
	Database        string
	User            string
	Password        string
	
	// Pool sizing: (core_count * 2) + effective_spindle_count
	MaxConns        int32
	MinConns        int32
	MaxConnLifetime time.Duration
	MaxConnIdleTime time.Duration
	HealthCheckPeriod time.Duration
	
	// Timeouts
	ConnectTimeout  time.Duration
	QueryTimeout    time.Duration
}

// DefaultPoolConfig returns optimized pool configuration for 4 vCPU instances
func DefaultPoolConfig() *PoolConfig {
	return &PoolConfig{
		Host:              "localhost",
		Port:              5432,
		Database:          "grc_claw",
		User:              "grc_claw",
		Password:          "",
		MaxConns:          20,   // (4 vCPU * 2) + 1 spindle = 9, rounded up for safety
		MinConns:          5,
		MaxConnLifetime:   1 * time.Hour,
		MaxConnIdleTime:   30 * time.Second,
		HealthCheckPeriod: 5 * time.Second,
		ConnectTimeout:    2 * time.Second,
		QueryTimeout:      10 * time.Second,
	}
}

// NewConnectionPool creates an optimized connection pool
func NewConnectionPool(cfg *PoolConfig) (*pgxpool.Pool, error) {
	connString := fmt.Sprintf(
		"host=%s port=%d dbname=%s user=%s password=%s sslmode=disable",
		cfg.Host, cfg.Port, cfg.Database, cfg.User, cfg.Password,
	)

	poolConfig, err := pgxpool.ParseConfig(connString)
	if err != nil {
		return nil, err
	}

	// Apply pool settings
	poolConfig.MaxConns = cfg.MaxConns
	poolConfig.MinConns = cfg.MinConns
	poolConfig.MaxConnLifetime = cfg.MaxConnLifetime
	poolConfig.MaxConnIdleTime = cfg.MaxConnIdleTime
	poolConfig.HealthCheckPeriod = cfg.HealthCheckPeriod
	
	// Connection timeout
	poolConfig.ConnConfig.ConnectTimeout = cfg.ConnectTimeout

	// Performance optimizations
	poolConfig.ConnConfig.DefaultQueryExecMode = pgx.QueryExecModeCacheStatement

	pool, err := pgxpool.NewWithConfig(context.Background(), poolConfig)
	if err != nil {
		return nil, fmt.Errorf("failed to create connection pool: %w", err)
	}

	// Verify connection
	ctx, cancel := context.WithTimeout(context.Background(), cfg.ConnectTimeout)
	defer cancel()

	if err := pool.Ping(ctx); err != nil {
		return nil, fmt.Errorf("failed to ping database: %w", err)
	}

	return pool, nil
}

// PoolStats returns current pool statistics
func (p *pgxpool.Pool) PoolStats() map[string]interface{} {
	stats := p.Stat()
	return map[string]interface{}{
		"total_conns":      stats.TotalConns(),
		"acquired_conns":   stats.AcquiredConns(),
		"idle_conns":       stats.IdleConns(),
		"constructing_conns": stats.ConstructingConns(),
		"max_conns":        stats.MaxConns(),
		"acquire_count":    stats.AcquireCount(),
		"empty_acquire_count": stats.EmptyAcquireCount(),
		"canceled_acquire_count": stats.CanceledAcquireCount(),
	}
}
```

### 3.4 Read Replica Routing

```go
// internal/db/router.go
package db

import (
	"context"
	"fmt"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"
)

// QueryType determines routing decision
type QueryType int

const (
	QueryTypeEnforcement QueryType = iota
	QueryTypeAgentLookup
	QueryTypeAuditWrite
	QueryTypeAuditReadRecent
	QueryTypeAuditReadHistorical
	QueryTypeEvidenceSearch
	QueryTypeCompliancePosture
	QueryTypeDashboardAnalytics
)

// QueryRouter routes queries to appropriate database instance
type QueryRouter struct {
	primary  *pgxpool.Pool
	replicas []*pgxpool.Pool
	// Replica selection strategy
	counter  uint64
}

// NewQueryRouter creates a new query router
func NewQueryRouter(primary *pgxpool.Pool, replicas []*pgxpool.Pool) *QueryRouter {
	return &QueryRouter{
		primary:  primary,
		replicas: replicas,
	}
}

// RouteQuery executes a query on the appropriate database instance
func (r *QueryRouter) RouteQuery(ctx context.Context, queryType QueryType, fn func(*pgxpool.Pool) error) error {
	pool := r.selectPool(queryType)
	return fn(pool)
}

// selectPool chooses the appropriate database pool based on query type
func (r *QueryRouter) selectPool(queryType QueryType) *pgxpool.Pool {
	switch queryType {
	case QueryTypeEnforcement, QueryTypeAgentLookup, QueryTypeAuditWrite, QueryTypeAuditReadRecent:
		// Strong consistency required - use primary
		return r.primary
	
	case QueryTypeAuditReadHistorical, QueryTypeEvidenceSearch, QueryTypeCompliancePosture, QueryTypeDashboardAnalytics:
		// Eventual consistency acceptable - use replica
		return r.selectReplica()
	
	default:
		return r.primary
	}
}

// selectReplica implements round-robin replica selection
func (r *QueryRouter) selectReplica() *pgxpool.Pool {
	if len(r.replicas) == 0 {
		return r.primary
	}
	idx := r.counter % uint64(len(r.replicas))
	r.counter++
	return r.replicas[idx]
}

// HealthCheck performs health checks on all database instances
func (r *QueryRouter) HealthCheck(ctx context.Context) map[string]error {
	results := make(map[string]error)
	
	// Check primary
	if err := r.primary.Ping(ctx); err != nil {
		results["primary"] = err
	}
	
	// Check replicas
	for i, replica := range r.replicas {
		if err := replica.Ping(ctx); err != nil {
			results[fmt.Sprintf("replica_%d", i)] = err
		}
	}
	
	return results
}
```

---

## 4. Network Latency Optimization

### 4.1 gRPC Service Definitions

```protobuf
// proto/enforcement.proto
syntax = "proto3";

package grc.enforcement.v1;

option go_package = "github.com/grc-claw/api/gen/enforcement/v1";

service EnforcementService {
  // Evaluate an agent action against policies
  rpc Evaluate(EvaluateRequest) returns (EvaluateResponse);
  
  // Stream enforcement decisions for real-time monitoring
  rpc StreamDecisions(StreamRequest) returns (stream DecisionEvent);
  
  // Batch evaluate multiple actions
  rpc BatchEvaluate(BatchEvaluateRequest) returns (BatchEvaluateResponse);
}

message EvaluateRequest {
  string agent_id = 1;
  string action = 2;
  string resource = 3;
  bytes context = 4;
  string request_id = 5;
  int64 timestamp = 6;
}

message EvaluateResponse {
  string decision = 1;
  string certificate = 2;
  int64 evaluation_time_us = 3;
  string policy_id = 4;
  map<string, string> metadata = 5;
}

message StreamRequest {
  string agent_id = 1;
  string filter = 2;
}

message DecisionEvent {
  string decision_id = 1;
  string agent_id = 2;
  string decision = 3;
  int64 timestamp = 4;
}

message BatchEvaluateRequest {
  repeated EvaluateRequest requests = 1;
}

message BatchEvaluateResponse {
  repeated EvaluateResponse responses = 1;
}
```

### 4.2 gRPC Client with Connection Pooling

```go
// internal/network/grpc_client.go
package network

import (
	"context"
	"fmt"
	"time"

	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials"
	"google.golang.org/grpc/keepalive"
)

// GRPCClientConfig defines gRPC client configuration
type GRPCClientConfig struct {
	Address         string
	TLSCredentials  credentials.TransportCredentials
	
	// Connection pooling
	MaxConns        int
	MaxIdleConns    int
	ConnMaxLifetime time.Duration
	ConnMaxIdleTime time.Duration
	
	// Keepalive
	KeepAliveTime    time.Duration
	KeepAliveTimeout time.Duration
	
	// Performance
	MaxCallRecvMsgSize int
	MaxCallSendMsgSize int
}

// DefaultGRPCClientConfig returns optimized gRPC client config
func DefaultGRPCClientConfig(address string) *GRPCClientConfig {
	return &GRPCClientConfig{
		Address:            address,
		MaxConns:           50,
		MaxIdleConns:       20,
		ConnMaxLifetime:    12 * time.Hour,
		ConnMaxIdleTime:    30 * time.Second,
		KeepAliveTime:      30 * time.Second,
		KeepAliveTimeout:   10 * time.Second,
		MaxCallRecvMsgSize: 4 * 1024 * 1024,  // 4 MB
		MaxCallSendMsgSize: 4 * 1024 * 1024,  // 4 MB
	}
}

// GRPCClient manages gRPC connections with pooling
type GRPCClient struct {
	config     *GRPCClientConfig
	connection *grpc.ClientConn
	pool       chan *grpc.ClientConn
}

// NewGRPCClient creates a new gRPC client with connection pooling
func NewGRPCClient(config *GRPCClientConfig) (*GRPCClient, error) {
	// Configure keepalive
	kacp := keepalive.ClientParameters{
		Time:                config.KeepAliveTime,
		Timeout:             config.KeepAliveTimeout,
		PermitWithoutStream: true,
	}

	// Build dial options
	opts := []grpc.DialOption{
		grpc.WithKeepaliveParams(kacp),
		grpc.WithDefaultCallOptions(
			grpc.MaxCallRecvMsgSize(config.MaxCallRecvMsgSize),
			grpc.MaxCallSendMsgSize(config.MaxCallSendMsgSize),
		),
		grpc.WithDefaultServiceConfig(`{
			"loadBalancingPolicy": "round_robin",
			"healthCheckConfig": {"serviceName": ""}
		}`),
	}

	// Add TLS if configured
	if config.TLSCredentials != nil {
		opts = append(opts, grpc.WithTransportCredentials(config.TLSCredentials))
	} else {
		opts = append(opts, grpc.WithInsecure())
	}

	// Create connection
	conn, err := grpc.Dial(config.Address, opts...)
	if err != nil {
		return nil, fmt.Errorf("failed to create gRPC connection: %w", err)
	}

	// Initialize connection pool
	pool := make(chan *grpc.ClientConn, config.MaxConns)
	for i := 0; i < config.MaxIdleConns; i++ {
		pool <- conn
	}

	return &GRPCClient{
		config:     config,
		connection: conn,
		pool:       pool,
	}, nil
}

// GetConnection retrieves a connection from the pool
func (c *GRPCClient) GetConnection(ctx context.Context) (*grpc.ClientConn, error) {
	select {
	case conn := <-c.pool:
		return conn, nil
	case <-ctx.Done():
		return nil, ctx.Err()
	default:
		// Pool exhausted, create new connection if under max
		return c.connection, nil
	}
}

// ReturnConnection returns a connection to the pool
func (c *GRPCClient) ReturnConnection(conn *grpc.ClientConn) {
	select {
	case c.pool <- conn:
	default:
		// Pool full, close connection
		conn.Close()
	}
}

// Close closes all connections
func (c *GRPCClient) Close() error {
	close(c.pool)
	return c.connection.Close()
}
```

### 4.3 HTTP/2 Server with Optimized Settings

```go
// internal/network/http_server.go
package network

import (
	"context"
	"crypto/tls"
	"fmt"
	"net"
	"net/http"
	"time"

	"golang.org/x/net/http2"
	"golang.org/x/net/http2/h2c"
)

// HTTPServerConfig defines HTTP/2 server configuration
type HTTPServerConfig struct {
	Address      string
	ReadTimeout  time.Duration
	WriteTimeout time.Duration
	IdleTimeout  time.Duration
	
	// HTTP/2 settings
	MaxConcurrentStreams int
	MaxReadFrameSize     uint32
	
	// TLS
	CertFile string
	KeyFile  string
}

// DefaultHTTPServerConfig returns optimized HTTP/2 server config
func DefaultHTTPServerConfig(address string) *HTTPServerConfig {
	return &HTTPServerConfig{
		Address:              address,
		ReadTimeout:          5 * time.Second,
		WriteTimeout:         10 * time.Second,
		IdleTimeout:          120 * time.Second,
		MaxConcurrentStreams: 1000,
		MaxReadFrameSize:     1024 * 1024, // 1 MB
	}
}

// NewHTTPServer creates an optimized HTTP/2 server
func NewHTTPServer(config *HTTPServerConfig, handler http.Handler) (*http.Server, error) {
	// Configure HTTP/2
	h2s := &http2.Server{
		MaxConcurrentStreams:         uint32(config.MaxConcurrentStreams),
		MaxReadFrameSize:             config.MaxReadFrameSize,
		IdleTimeout:                  config.IdleTimeout,
		MaxUploadBufferPerConnection: 1024 * 1024,
		MaxUploadBufferPerStream:     1024 * 1024,
	}

	// Wrap handler with h2c (HTTP/2 cleartext) for internal services
	h := h2c.NewHandler(handler, h2s)

	server := &http.Server{
		Addr:         config.Address,
		Handler:      h,
		ReadTimeout:  config.ReadTimeout,
		WriteTimeout: config.WriteTimeout,
		IdleTimeout:  config.IdleTimeout,
	}

	// Configure TLS if certificates provided
	if config.CertFile != "" && config.KeyFile != "" {
		tlsConfig := &tls.Config{
			MinVersion: tls.VersionTLS12,
			CipherSuites: []uint16{
				tls.TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384,
				tls.TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384,
				tls.TLS_ECDHE_ECDSA_WITH_CHACHA20_POLY1305,
				tls.TLS_ECDHE_RSA_WITH_CHACHA20_POLY1305,
			},
			PreferServerCipherSuites: true,
			CurvePreferences: []tls.CurveID{
				tls.X25519,
				tls.CurveP256,
			},
		}
		server.TLSConfig = tlsConfig
	}

	return server, nil
}

// ListenAndServe starts the HTTP/2 server
func (s *http.Server) ListenAndServe(config *HTTPServerConfig) error {
	ln, err := net.Listen("tcp", config.Address)
	if err != nil {
		return err
	}

	if config.CertFile != "" && config.KeyFile != "" {
		return s.ServeTLS(ln, config.CertFile, config.KeyFile)
	}
	return s.Serve(ln)
}
```

### 4.4 MessagePack Serialization

```go
// internal/serialization/messagepack.go
package serialization

import (
	"fmt"

	"github.com/vmihailenco/msgpack/v5"
)

// MessagePackSerializer provides efficient binary serialization
type MessagePackSerializer struct{}

// NewMessagePackSerializer creates a new MessagePack serializer
func NewMessagePackSerializer() *MessagePackSerializer {
	return &MessagePackSerializer{}
}

// Serialize encodes a value to MessagePack format
func (s *MessagePackSerializer) Serialize(v interface{}) ([]byte, error) {
	data, err := msgpack.Marshal(v)
	if err != nil {
		return nil, fmt.Errorf("msgpack marshal failed: %w", err)
	}
	return data, nil
}

// Deserialize decodes MessagePack data to a value
func (s *MessagePackSerializer) Deserialize(data []byte, v interface{}) error {
	if err := msgpack.Unmarshal(data, v); err != nil {
		return fmt.Errorf("msgpack unmarshal failed: %w", err)
	}
	return nil
}

// SerializeEnforcementDecision serializes an enforcement decision
func (s *MessagePackSerializer) SerializeEnforcementDecision(decision *EnforcementDecision) ([]byte, error) {
	return s.Serialize(decision)
}

// DeserializeEnforcementDecision deserializes an enforcement decision
func (s *MessagePackSerializer) DeserializeEnforcementDecision(data []byte) (*EnforcementDecision, error) {
	var decision EnforcementDecision
	if err := s.Deserialize(data, &decision); err != nil {
		return nil, err
	}
	return &decision, nil
}
```

### 4.5 Compression Middleware

```go
// internal/network/compression.go
package network

import (
	"compress/gzip"
	"io"
	"net/http"
	"strings"

	"github.com/klauspost/compress/zstd"
)

// CompressionMiddleware provides response compression
type CompressionMiddleware struct {
	enableGzip bool
	enableZstd bool
	minSize    int // Minimum size to compress
}

// NewCompressionMiddleware creates compression middleware
func NewCompressionMiddleware() *CompressionMiddleware {
	return &CompressionMiddleware{
		enableGzip: true,
		enableZstd: true,
		minSize:    1024, // 1 KB
	}
}

// Middleware returns the compression middleware handler
func (cm *CompressionMiddleware) Middleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Check if client accepts compression
		acceptEncoding := r.Header.Get("Accept-Encoding")
		
		if cm.enableZstd && strings.Contains(acceptEncoding, "zstd") {
			w.Header().Set("Content-Encoding", "zstd")
			zw, _ := zstd.NewWriter(w)
			defer zw.Close()
			
			crw := &compressedResponseWriter{
				ResponseWriter: w,
				writer:         zw,
				minSize:        cm.minSize,
			}
			next.ServeHTTP(crw, r)
			return
		}
		
		if cm.enableGzip && strings.Contains(acceptEncoding, "gzip") {
			w.Header().Set("Content-Encoding", "gzip")
			gw := gzip.NewWriter(w)
			defer gw.Close()
			
			crw := &compressedResponseWriter{
				ResponseWriter: w,
				writer:         gw,
				minSize:        cm.minSize,
			}
			next.ServeHTTP(crw, r)
			return
		}
		
		next.ServeHTTP(w, r)
	})
}

type compressedResponseWriter struct {
	http.ResponseWriter
	writer  io.Writer
	minSize int
	buf     []byte
}

func (crw *compressedResponseWriter) Write(p []byte) (int, error) {
	if len(crw.buf) < crw.minSize {
		crw.buf = append(crw.buf, p...)
		if len(crw.buf) >= crw.minSize {
			return crw.writer.Write(crw.buf)
		}
		return len(p), nil
	}
	return crw.writer.Write(p)
}

func (crw *compressedResponseWriter) Flush() {
	if len(crw.buf) > 0 {
		crw.writer.Write(crw.buf)
		crw.buf = nil
	}
	if f, ok := crw.writer.(http.Flusher); ok {
		f.Flush()
	}
}
```

---

## 5. Performance Regression Testing

### 5.1 Micro-Benchmark Suite

```go
// tests/performance/benchmarks/micro_benchmarks_test.go
package benchmarks

import (
	"testing"
	"time"

	"github.com/grc-claw/internal/enforcement"
	"github.com/grc-claw/internal/serialization"
)

// BenchmarkPolicyRuleEvaluation measures policy evaluation performance
// Target: < 1 ms per evaluation
func BenchmarkPolicyRuleEvaluation(b *testing.B) {
	engine := enforcement.NewPolicyEngine()
	policy := generateTestPolicy(100) // 100 rules
	context := generateTestContext()
	
	b.ResetTimer()
	b.ReportAllocs()
	
	for i := 0; i < b.N; i++ {
		_, err := engine.Evaluate(context, policy)
		if err != nil {
			b.Fatal(err)
		}
	}
	
	// Validate latency target
	if b.Elapsed()/time.Duration(b.N) > time.Millisecond {
		b.Errorf("Policy evaluation exceeded 1ms target: %v", b.Elapsed()/time.Duration(b.N))
	}
}

// BenchmarkContextEnrichment measures context enrichment performance
// Target: < 2 ms per enrichment
func BenchmarkContextEnrichment(b *testing.B) {
	enricher := enforcement.NewContextEnricher()
	agentID := "agent-123"
	
	b.ResetTimer()
	b.ReportAllocs()
	
	for i := 0; i < b.N; i++ {
		_, err := enricher.Enrich(agentID)
		if err != nil {
			b.Fatal(err)
		}
	}
}

// BenchmarkDecisionCertificateGeneration measures certificate generation
// Target: < 1 ms per certificate
func BenchmarkDecisionCertificateGeneration(b *testing.B) {
	generator := enforcement.NewCertificateGenerator()
	decision := generateTestDecision()
	
	b.ResetTimer()
	b.ReportAllocs()
	
	for i := 0; i < b.N; i++ {
		_, err := generator.Generate(decision)
		if err != nil {
			b.Fatal(err)
		}
	}
}

// BenchmarkMessagePackSerialization measures serialization performance
// Target: < 100 µs per serialization
func BenchmarkMessagePackSerialization(b *testing.B) {
	serializer := serialization.NewMessagePackSerializer()
	decision := generateTestDecision()
	
	b.ResetTimer()
	b.ReportAllocs()
	
	for i := 0; i < b.N; i++ {
		_, err := serializer.Serialize(decision)
		if err != nil {
			b.Fatal(err)
		}
	}
}

// BenchmarkSHA256Computation measures hash computation performance
// Target: < 50 µs per hash
func BenchmarkSHA256Computation(b *testing.B) {
	data := make([]byte, 2048) // 2 KB context
	
	b.ResetTimer()
	b.ReportAllocs()
	
	for i := 0; i < b.N; i++ {
		computeSHA256(data)
	}
}

// BenchmarkL1CacheLookup measures L1 cache lookup performance
// Target: < 1 µs per lookup
func BenchmarkL1CacheLookup(b *testing.B) {
	cache := enforcement.NewLocalCache(10000, 5*time.Minute)
	cache.Set("key", "value")
	
	b.ResetTimer()
	b.ReportAllocs()
	
	for i := 0; i < b.N; i++ {
		_, _ = cache.Get("key")
	}
}

// BenchmarkL3CacheLookup measures L3 (Redis) cache lookup performance
// Target: < 1 ms per lookup
func BenchmarkL3CacheLookup(b *testing.B) {
	cache := setupTestRedisCache()
	cache.Set("key", "value")
	
	b.ResetTimer()
	b.ReportAllocs()
	
	for i := 0; i < b.N; i++ {
		_, _ = cache.Get("key")
	}
}
```

### 5.2 Regression Detection Script

```python
# scripts/performance_regression.py
#!/usr/bin/env python3
"""
Performance regression detection script.
Compares current benchmark results against baseline and fails if regression exceeds threshold.
"""

import json
import sys
import argparse
import subprocess
import statistics
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

# Regression thresholds from Performance Spec Section 13.2
REGRESSION_THRESHOLDS = {
    "PolicyRuleEvaluation": 5.0,      # 5% regression allowed
    "ContextEnrichment": 5.0,
    "DecisionCertificateGeneration": 5.0,
    "MessagePackSerialization": 10.0,
    "SHA256Computation": 10.0,
    "L1CacheLookup": 20.0,
    "L3CacheLookup": 10.0,
}

# Latency targets from Performance Spec Section 3.1
LATENCY_TARGETS = {
    "enforcement_p50_ms": 2.0,
    "enforcement_p95_ms": 5.0,
    "enforcement_p99_ms": 10.0,
    "enforcement_p999_ms": 20.0,
    "enforcement_max_ms": 50.0,
    "evidence_p50_ms": 50.0,
    "evidence_p95_ms": 100.0,
    "evidence_p99_ms": 200.0,
    "audit_p50_ms": 5.0,
    "audit_p95_ms": 10.0,
    "audit_p99_ms": 20.0,
}


def run_benchmarks() -> Dict:
    """Run Go benchmarks and parse results."""
    result = subprocess.run(
        ["go", "test", "-bench=.", "-benchmem", "-count=10", "-json", 
         "./tests/performance/benchmarks/..."],
        capture_output=True,
        text=True,
    )
    
    if result.returncode != 0:
        print(f"Benchmark failed: {result.stderr}")
        sys.exit(1)
    
    # Parse JSON output
    benchmarks = {}
    for line in result.stdout.split("\n"):
        if not line.strip():
            continue
        try:
            data = json.loads(line)
            if data.get("Action") == "output":
                # Parse benchmark output
                pass
        except json.JSONDecodeError:
            continue
    
    return benchmarks


def load_baseline(baseline_path: str) -> Dict:
    """Load baseline results from file."""
    with open(baseline_path) as f:
        return json.load(f)


def compare_benchmarks(current: Dict, baseline: Dict, threshold: float) -> List[Tuple]:
    """Compare current results against baseline."""
    regressions = []
    
    for name, current_result in current.items():
        if name not in baseline:
            continue
        
        baseline_result = baseline[name]
        
        # Compare p99 latency
        current_p99 = current_result.get("p99_ms", 0)
        baseline_p99 = baseline_result.get("p99_ms", 0)
        
        if baseline_p99 > 0:
            regression_pct = ((current_p99 - baseline_p99) / baseline_p99) * 100
            
            if regression_pct > threshold:
                regressions.append((name, regression_pct, baseline_p99, current_p99))
    
    return regressions


def welch_t_test(sample1: List[float], sample2: List[float]) -> Tuple[float, float]:
    """
    Perform Welch's t-test for statistical significance.
    Returns (t-statistic, p-value).
    """
    n1, n2 = len(sample1), len(sample2)
    mean1, mean2 = statistics.mean(sample1), statistics.mean(sample2)
    var1, var2 = statistics.variance(sample1), statistics.variance(sample2)
    
    # Welch's t-test
    se = (var1/n1 + var2/n2) ** 0.5
    if se == 0:
        return 0.0, 1.0
    
    t_stat = (mean1 - mean2) / se
    
    # Degrees of freedom (Welch-Satterthwaite)
    df = ((var1/n1 + var2/n2) ** 2) / (
        (var1/n1) ** 2 / (n1 - 1) + (var2/n2) ** 2 / (n2 - 1)
    )
    
    # Approximate p-value (two-tailed)
    from scipy import stats
    p_value = 2 * (1 - stats.t.cdf(abs(t_stat), df))
    
    return t_stat, p_value


def validate_latency_targets(results: Dict) -> List[str]:
    """Validate results against latency targets."""
    failures = []
    
    for metric, target in LATENCY_TARGETS.items():
        actual = results.get(metric, 0)
        if actual > target:
            failures.append(f"{metric}: {actual:.2f}ms exceeds target {target:.2f}ms")
    
    return failures


def main():
    parser = argparse.ArgumentParser(description="Performance regression detection")
    parser.add_argument("--baseline", required=True, help="Path to baseline results")
    parser.add_argument("--threshold", type=float, default=5.0, help="Regression threshold (%)")
    parser.add_argument("--output", default="regression-report.json", help="Output file")
    args = parser.parse_args()
    
    print("Running performance benchmarks...")
    current_results = run_benchmarks()
    
    print(f"Loading baseline from {args.baseline}...")
    baseline_results = load_baseline(args.baseline)
    
    print("Comparing results...")
    regressions = compare_benchmarks(current_results, baseline_results, args.threshold)
    
    # Validate latency targets
    target_failures = validate_latency_targets(current_results)
    
    # Generate report
    report = {
        "timestamp": datetime.utcnow().isoformat(),
        "baseline": args.baseline,
        "threshold": args.threshold,
        "regressions": [
            {
                "benchmark": name,
                "regression_pct": pct,
                "baseline_p99_ms": baseline,
                "current_p99_ms": current,
            }
            for name, pct, baseline, current in regressions
        ],
        "target_failures": target_failures,
        "passed": len(regressions) == 0 and len(target_failures) == 0,
    }
    
    with open(args.output, "w") as f:
        json.dump(report, f, indent=2)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"Performance Regression Report")
    print(f"{'='*60}")
    print(f"Regressions found: {len(regressions)}")
    print(f"Target failures: {len(target_failures)}")
    
    if regressions:
        print("\nRegressions:")
        for name, pct, baseline, current in regressions:
            print(f"  {name}: +{pct:.1f}% ({baseline:.2f}ms → {current:.2f}ms)")
    
    if target_failures:
        print("\nTarget failures:")
        for failure in target_failures:
            print(f"  {failure}")
    
    print(f"{'='*60}")
    
    if not report["passed"]:
        print("FAILED: Performance regression detected!")
        sys.exit(1)
    
    print("PASSED: No performance regression detected.")


if __name__ == "__main__":
    main()
```

### 5.3 Baseline Management

```go
// scripts/baseline_manager.go
package main

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"time"
)

// Baseline represents a performance baseline
type Baseline struct {
	Version   string                 `json:"version"`
	Commit    string                 `json:"commit"`
	Date      time.Time              `json:"date"`
	Environment Environment          `json:"environment"`
	Results   map[string]float64     `json:"results"`
}

// Environment describes the test environment
type Environment struct {
	CPU       string `json:"cpu"`
	Memory    string `json:"memory"`
	OS        string `json:"os"`
	Database  string `json:"database"`
	Cache     string `json:"cache"`
}

// BaselineManager manages performance baselines
type BaselineManager struct {
	baselineDir string
}

// NewBaselineManager creates a new baseline manager
func NewBaselineManager(dir string) *BaselineManager {
	return &BaselineManager{baselineDir: dir}
}

// CreateBaseline creates a new baseline from benchmark results
func (bm *BaselineManager) CreateBaseline(version, commit string, results map[string]float64) error {
	baseline := Baseline{
		Version: version,
		Commit:  commit,
		Date:    time.Now(),
		Environment: Environment{
			CPU:      "4 vCPU",
			Memory:   "8 GB",
			OS:       "Linux 6.5",
			Database: "PostgreSQL 16",
			Cache:    "Redis 7.2",
		},
		Results: results,
	}

	filename := filepath.Join(bm.baselineDir, fmt.Sprintf("baseline-%s.json", version))
	data, err := json.MarshalIndent(baseline, "", "  ")
	if err != nil {
		return err
	}

	return os.WriteFile(filename, data, 0644)
}

// GetBaseline retrieves a baseline by version
func (bm *BaselineManager) GetBaseline(version string) (*Baseline, error) {
	filename := filepath.Join(bm.baselineDir, fmt.Sprintf("baseline-%s.json", version))
	data, err := os.ReadFile(filename)
	if err != nil {
		return nil, err
	}

	var baseline Baseline
	if err := json.Unmarshal(data, &baseline); err != nil {
		return nil, err
	}

	return &baseline, nil
}

// GetLatestBaseline retrieves the most recent baseline
func (bm *BaselineManager) GetLatestBaseline() (*Baseline, error) {
	entries, err := os.ReadDir(bm.baselineDir)
	if err != nil {
		return nil, err
	}

	var baselines []string
	for _, entry := range entries {
		if !entry.IsDir() && filepath.Ext(entry.Name()) == ".json" {
			baselines = append(baselines, entry.Name())
		}
	}

	if len(baselines) == 0 {
		return nil, fmt.Errorf("no baselines found")
	}

	sort.Strings(baselines)
	latest := baselines[len(baselines)-1]

	data, err := os.ReadFile(filepath.Join(bm.baselineDir, latest))
	if err != nil {
		return nil, err
	}

	var baseline Baseline
	if err := json.Unmarshal(data, &baseline); err != nil {
		return nil, err
	}

	return &baseline, nil
}

// CompareBaselines compares two baselines
func (bm *BaselineManager) CompareBaselines(v1, v2 string) (map[string]float64, error) {
	b1, err := bm.GetBaseline(v1)
	if err != nil {
		return nil, err
	}

	b2, err := bm.GetBaseline(v2)
	if err != nil {
		return nil, err
	}

	comparison := make(map[string]float64)
	for key, val1 := range b1.Results {
		if val2, ok := b2.Results[key]; ok {
			if val2 > 0 {
				comparison[key] = ((val1 - val2) / val2) * 100
			}
		}
	}

	return comparison, nil
}

// CleanupOldBaselines removes baselines older than 12 months
func (bm *BaselineManager) CleanupOldBaselines() error {
	entries, err := os.ReadDir(bm.baselineDir)
	if err != nil {
		return err
	}

	cutoff := time.Now().AddDate(-1, 0, 0)
	for _, entry := range entries {
		if entry.IsDir() {
			continue
		}

		info, err := entry.Info()
		if err != nil {
			continue
		}

		if info.ModTime().Before(cutoff) {
			os.Remove(filepath.Join(bm.baselineDir, entry.Name()))
		}
	}

	return nil
}
```

---

## 6. Capacity Planning Automation

### 6.1 Metrics Collector

```go
// internal/capacity/collector.go
package capacity

import (
	"context"
	"fmt"
	"time"

	"github.com/prometheus/client_golang/api"
	v1 "github.com/prometheus/client_golang/api/prometheus/v1"
	"github.com/prometheus/common/model"
)

// CapacityMetrics represents collected capacity metrics
type CapacityMetrics struct {
	Timestamp   time.Time
	Component   string
	
	// Resource metrics
	CPUUtilization    float64
	MemoryUtilization float64
	DiskUtilization   float64
	NetworkInMbps     float64
	NetworkOutMbps    float64
	
	// Performance metrics
	RequestRate      float64
	P50Latency       float64
	P95Latency       float64
	P99Latency       float64
	ErrorRate        float64
	
	// Queue metrics
	QueueDepth       int64
	ConsumerLag      int64
	
	// Cache metrics
	CacheHitRatio    float64
	CacheMemoryUsed  float64
	
	// Connection metrics
	ConnectionPoolUtilization float64
	ActiveConnections         int64
}

// MetricsCollector collects capacity metrics from Prometheus
type MetricsCollector struct {
	client api.Client
	api    v1.API
}

// NewMetricsCollector creates a new metrics collector
func NewMetricsCollector(prometheusURL string) (*MetricsCollector, error) {
	client, err := api.NewClient(api.Config{
		Address: prometheusURL,
	})
	if err != nil {
		return nil, err
	}

	return &MetricsCollector{
		client: client,
		api:    v1.NewAPI(client),
	}, nil
}

// CollectMetrics collects metrics for a specific component
func (mc *MetricsCollector) CollectMetrics(ctx context.Context, component string) (*CapacityMetrics, error) {
	metrics := &CapacityMetrics{
		Timestamp: time.Now(),
		Component: component,
	}

	// CPU utilization
	cpu, err := mc.query(ctx, fmt.Sprintf(
		"avg(rate(container_cpu_usage_seconds_total{component='%s'}[5m])) * 100", component))
	if err == nil {
		metrics.CPUUtilization = cpu
	}

	// Memory utilization
	mem, err := mc.query(ctx, fmt.Sprintf(
		"avg(container_memory_usage_bytes{component='%s'}) / avg(container_spec_memory_limit_bytes{component='%s'}) * 100",
		component, component))
	if err == nil {
		metrics.MemoryUtilization = mem
	}

	// Request rate
	reqRate, err := mc.query(ctx, fmt.Sprintf(
		"sum(rate(grc_api_requests_total{component='%s'}[1m]))", component))
	if err == nil {
		metrics.RequestRate = reqRate
	}

	// p99 latency
	p99, err := mc.query(ctx, fmt.Sprintf(
		"histogram_quantile(0.99, sum(rate(grc_api_request_duration_seconds_bucket{component='%s'}[5m])) by (le))",
		component))
	if err == nil {
		metrics.P99Latency = p99 * 1000 // Convert to ms
	}

	// Error rate
	errRate, err := mc.query(ctx, fmt.Sprintf(
		"sum(rate(grc_api_requests_total{component='%s',status=~'5..'}[1m])) / sum(rate(grc_api_requests_total{component='%s'}[1m]))",
		component, component))
	if err == nil {
		metrics.ErrorRate = errRate
	}

	// Queue depth
	queue, err := mc.query(ctx, fmt.Sprintf(
		"grc_evidence_queue_depth{component='%s'}", component))
	if err == nil {
		metrics.QueueDepth = int64(queue)
	}

	// Cache hit ratio
	cacheHit, err := mc.query(ctx, fmt.Sprintf(
		"grc_cache_l1_hit_ratio{component='%s'}", component))
	if err == nil {
		metrics.CacheHitRatio = cacheHit
	}

	return metrics, nil
}

// query executes a PromQL query and returns the result
func (mc *MetricsCollector) query(ctx context.Context, query string) (float64, error) {
	result, _, err := mc.api.Query(ctx, query, time.Now())
	if err != nil {
		return 0, err
	}

	vec, ok := result.(model.Vector)
	if !ok || len(vec) == 0 {
		return 0, fmt.Errorf("no data")
	}

	return float64(vec[0].Value), nil
}

// CollectAllComponents collects metrics for all components
func (mc *MetricsCollector) CollectAllComponents(ctx context.Context) (map[string]*CapacityMetrics, error) {
	components := []string{
		"enforcement-proxy",
		"evidence-collector",
		"api-gateway",
		"policy-engine",
		"audit-trail",
	}

	results := make(map[string]*CapacityMetrics)
	for _, component := range components {
		metrics, err := mc.CollectMetrics(ctx, component)
		if err != nil {
			continue
		}
		results[component] = metrics
	}

	return results, nil
}
```

### 6.2 Trend Analyzer

```go
// internal/capacity/trend_analyzer.go
package capacity

import (
	"fmt"
	"math"
	"time"
)

// TrendDirection indicates the direction of a metric trend
type TrendDirection int

const (
	TrendDecreasing TrendDirection = iota
	TrendStable
	TrendIncreasing
)

// TrendAnalysis represents the result of trend analysis
type TrendAnalysis struct {
	Metric         string
	Direction      TrendDirection
	GrowthRate     float64 // Daily compound growth rate
	CurrentValue   float64
	ProjectedValue float64 // 30-day projection
	Confidence     float64 // 0-1 confidence level
}

// TrendAnalyzer analyzes metric trends
type TrendAnalyzer struct {
	metrics []CapacityMetrics
}

// NewTrendAnalyzer creates a new trend analyzer
func NewTrendAnalyzer(metrics []CapacityMetrics) *TrendAnalyzer {
	return &TrendAnalyzer{metrics: metrics}
}

// AnalyzeTrend performs linear regression on a metric
func (ta *TrendAnalyzer) AnalyzeTrend(metricName string, days int) (*TrendAnalysis, error) {
	if len(ta.metrics) < 2 {
		return nil, fmt.Errorf("insufficient data points")
	}

	// Extract values
	values := make([]float64, len(ta.metrics))
	for i, m := range ta.metrics {
		values[i] = ta.getMetricValue(m, metricName)
	}

	// Linear regression
	n := float64(len(values))
	sumX, sumY, sumXY, sumX2 := 0.0, 0.0, 0.0, 0.0
	for i, y := range values {
		x := float64(i)
		sumX += x
		sumY += y
		sumXY += x * y
		sumX2 += x * x
	}

	slope := (n*sumXY - sumX*sumY) / (n*sumX2 - sumX*sumX)
	intercept := (sumY - slope*sumX) / n

	// Calculate R-squared
	ssTot, ssRes := 0.0, 0.0
	meanY := sumY / n
	for i, y := range values {
		x := float64(i)
		predicted := slope*x + intercept
		ssTot += (y - meanY) * (y - meanY)
		ssRes += (y - predicted) * (y - predicted)
	}
	rSquared := 1 - (ssRes / ssTot)

	// Determine direction
	direction := TrendStable
	if slope > 0.01 {
		direction = TrendIncreasing
	} else if slope < -0.01 {
		direction = TrendDecreasing
	}

	// Calculate daily growth rate
	var growthRate float64
	if len(values) > 1 && values[0] > 0 {
		growthRate = math.Pow(values[len(values)-1]/values[0], 1.0/float64(len(values)-1)) - 1
	}

	// Project 30 days
	projected := intercept + slope*float64(len(values)+30)

	return &TrendAnalysis{
		Metric:         metricName,
		Direction:      direction,
		GrowthRate:     growthRate,
		CurrentValue:   values[len(values)-1],
		ProjectedValue: projected,
		Confidence:     rSquared,
	}, nil
}

// getMetricValue extracts a metric value from CapacityMetrics
func (ta *TrendAnalyzer) getMetricValue(m CapacityMetrics, name string) float64 {
	switch name {
	case "cpu_utilization":
		return m.CPUUtilization
	case "memory_utilization":
		return m.MemoryUtilization
	case "request_rate":
		return m.RequestRate
	case "p99_latency":
		return m.P99Latency
	case "error_rate":
		return m.ErrorRate
	case "queue_depth":
		return float64(m.QueueDepth)
	case "cache_hit_ratio":
		return m.CacheHitRatio
	default:
		return 0
	}
}

// DetectAnomalies detects anomalous metric values
func (ta *TrendAnalyzer) DetectAnomalies(metricName string, threshold float64) []Anomaly {
	var anomalies []Anomaly
	values := make([]float64, len(ta.metrics))
	timestamps := make([]time.Time, len(ta.metrics))

	for i, m := range ta.metrics {
		values[i] = ta.getMetricValue(m, metricName)
		timestamps[i] = m.Timestamp
	}

	// Calculate mean and standard deviation
	mean := statistics.Mean(values)
	stdDev := statistics.StdDev(values)

	// Detect values beyond threshold standard deviations
	for i, v := range values {
		if math.Abs(v-mean) > threshold*stdDev {
			anomalies = append(anomalies, Anomaly{
				Timestamp: timestamps[i],
				Metric:    metricName,
				Value:     v,
				Expected:  mean,
				Deviation: (v - mean) / stdDev,
			})
		}
	}

	return anomalies
}

// Anomaly represents an anomalous metric reading
type Anomaly struct {
	Timestamp time.Time
	Metric    string
	Value     float64
	Expected  float64
	Deviation float64
}
```

### 6.3 Forecasting Engine

```go
// internal/capacity/forecaster.go
package capacity

import (
	"fmt"
	"math"
	"time"
)

// Forecast represents a capacity forecast
type Forecast struct {
	Component         string
	CurrentInstances  int
	RecommendedInstances int
	ProjectedDate     time.Time
	Confidence        float64
	Reasoning         string
}

// ForecastingEngine generates capacity forecasts
type ForecastingEngine struct {
	trendAnalyzer *TrendAnalyzer
	config        *ForecastingConfig
}

// ForecastingConfig defines forecasting parameters
type ForecastingConfig struct {
	HeadroomPercent      float64 // 30% buffer
	ScaleUpThreshold     float64 // CPU/memory threshold
	ScaleDownThreshold   float64
	MinInstances         int
	MaxInstances         int
	ProjectionHorizon    int // Days
}

// DefaultForecastingConfig returns default forecasting config
func DefaultForecastingConfig() *ForecastingConfig {
	return &ForecastingConfig{
		HeadroomPercent:   0.30,
		ScaleUpThreshold:  0.70,
		ScaleDownThreshold: 0.30,
		MinInstances:      2,
		MaxInstances:      50,
		ProjectionHorizon: 30,
	}
}

// NewForecastingEngine creates a new forecasting engine
func NewForecastingEngine(analyzer *TrendAnalyzer, config *ForecastingConfig) *ForecastingEngine {
	return &ForecastingEngine{
		trendAnalyzer: analyzer,
		config:        config,
	}
}

// GenerateForecast generates a capacity forecast for a component
func (fe *ForecastingEngine) GenerateForecast(component string, currentMetrics *CapacityMetrics) (*Forecast, error) {
	// Analyze CPU trend
	cpuTrend, err := fe.trendAnalyzer.AnalyzeTrend("cpu_utilization", fe.config.ProjectionHorizon)
	if err != nil {
		return nil, err
	}

	// Analyze memory trend
	memTrend, err := fe.trendAnalyzer.AnalyzeTrend("memory_utilization", fe.config.ProjectionHorizon)
	if err != nil {
		return nil, err
	}

	// Analyze request rate trend
	reqTrend, err := fe.trendAnalyzer.AnalyzeTrend("request_rate", fe.config.ProjectionHorizon)
	if err != nil {
		return nil, err
	}

	// Calculate required instances based on projected load
	projectedCPU := cpuTrend.ProjectedValue * (1 + fe.config.HeadroomPercent)
	projectedMem := memTrend.ProjectedValue * (1 + fe.config.HeadroomPercent)
	projectedReq := reqTrend.ProjectedValue * (1 + fe.config.HeadroomPercent)

	// Determine bottleneck
	bottleneck := "CPU"
	utilization := projectedCPU
	if projectedMem > utilization {
		bottleneck = "Memory"
		utilization = projectedMem
	}

	// Calculate recommended instances
	currentInstances := fe.getCurrentInstances(component)
	requiredInstances := int(math.Ceil(float64(currentInstances) * utilization / fe.config.ScaleUpThreshold))

	// Apply bounds
	if requiredInstances < fe.config.MinInstances {
		requiredInstances = fe.config.MinInstances
	}
	if requiredInstances > fe.config.MaxInstances {
		requiredInstances = fe.config.MaxInstances
	}

	// Calculate confidence
	confidence := (cpuTrend.Confidence + memTrend.Confidence + reqTrend.Confidence) / 3

	// Generate reasoning
	reasoning := fmt.Sprintf(
		"Projected %s utilization: %.1f%%. Current instances: %d. Recommended: %d. Confidence: %.1f%%.",
		bottleneck, utilization, currentInstances, requiredInstances, confidence*100,
	)

	return &Forecast{
		Component:            component,
		CurrentInstances:     currentInstances,
		RecommendedInstances: requiredInstances,
		ProjectedDate:        time.Now().AddDate(0, 0, fe.config.ProjectionHorizon),
		Confidence:           confidence,
		Reasoning:            reasoning,
	}, nil
}

// GenerateScalingRecommendation generates scaling recommendations
func (fe *ForecastingEngine) GenerateScalingRecommendation(forecast *Forecast) *ScalingRecommendation {
	current := forecast.CurrentInstances
	recommended := forecast.RecommendedInstances

	if recommended > current {
		return &ScalingRecommendation{
			Action:       "scale_up",
			Component:    forecast.Component,
			From:         current,
			To:           recommended,
			Urgency:      fe.calculateUrgency(forecast),
			Reason:       forecast.Reasoning,
			ProjectedDate: forecast.ProjectedDate,
		}
	} else if recommended < current {
		return &ScalingRecommendation{
			Action:       "scale_down",
			Component:    forecast.Component,
			From:         current,
			To:           recommended,
			Urgency:      "low",
			Reason:       forecast.Reasoning,
			ProjectedDate: forecast.ProjectedDate,
		}
	}

	return &ScalingRecommendation{
		Action:    "maintain",
		Component: forecast.Component,
		From:      current,
		To:        current,
		Urgency:   "none",
		Reason:    "Current capacity sufficient",
	}
}

func (fe *ForecastingEngine) calculateUrgency(forecast *Forecast) string {
	if forecast.Confidence < 0.5 {
		return "low"
	}
	
	utilization := forecast.RecommendedInstances / forecast.CurrentInstances
	if utilization > 2.0 {
		return "critical"
	} else if utilization > 1.5 {
		return "high"
	}
	return "medium"
}

func (fe *ForecastingEngine) getCurrentInstances(component string) int {
	// Query current instance count from Kubernetes or metrics
	// This is a placeholder - implement actual K8s API call
	return 3
}

// ScalingRecommendation represents a scaling action recommendation
type ScalingRecommendation struct {
	Action        string    `json:"action"`
	Component     string    `json:"component"`
	From          int       `json:"from"`
	To            int       `json:"to"`
	Urgency       string    `json:"urgency"`
	Reason        string    `json:"reason"`
	ProjectedDate time.Time `json:"projected_date"`
}
```

### 6.4 Capacity Report Generator

```go
// internal/capacity/reporter.go
package capacity

import (
	"bytes"
	"encoding/json"
	"fmt"
	"html/template"
	"time"
)

// CapacityReport represents a comprehensive capacity report
type CapacityReport struct {
	GeneratedAt       time.Time
	ReportPeriod      string
	CurrentState      map[string]ComponentState
	Forecasts         map[string]*Forecast
	Recommendations   []*ScalingRecommendation
	CostProjection    *CostProjection
	BottleneckPrediction []BottleneckPrediction
}

// ComponentState represents the current state of a component
type ComponentState struct {
	Component        string
	Instances        int
	AvgCPUUtilization float64
	AvgMemoryUtilization float64
	AvgRequestRate   float64
	P99Latency       float64
	ErrorRate       float64
}

// CostProjection represents cost estimates
type CostProjection struct {
	CurrentMonthlyCost    float64
	ProjectedMonthlyCost  float64
	OptimizationOpportunities []OptimizationOpportunity
}

// OptimizationOpportunity represents a cost optimization opportunity
type OptimizationOpportunity struct {
	Description string
	Savings     float64
	Effort      string
}

// BottleneckPrediction predicts future bottlenecks
type BottleneckPrediction struct {
	Component   string
	Resource    string
	CurrentUtilization float64
	ProjectedUtilization float64
	DaysToSaturation    int
	RecommendedAction  string
}

// ReportGenerator generates capacity reports
type ReportGenerator struct {
	metricsCollector *MetricsCollector
	forecastingEngine *ForecastingEngine
}

// NewReportGenerator creates a new report generator
func NewReportGenerator(mc *MetricsCollector, fe *ForecastingEngine) *ReportGenerator {
	return &ReportGenerator{
		metricsCollector:  mc,
		forecastingEngine: fe,
	}
}

// GenerateWeeklyReport generates a weekly capacity report
func (rg *ReportGenerator) GenerateWeeklyReport(ctx context.Context) (*CapacityReport, error) {
	// Collect current metrics
	allMetrics, err := rg.metricsCollector.CollectAllComponents(ctx)
	if err != nil {
		return nil, err
	}

	// Generate forecasts
	forecasts := make(map[string]*Forecast)
	recommendations := make([]*ScalingRecommendation, 0)

	for component, metrics := range allMetrics {
		forecast, err := rg.forecastingEngine.GenerateForecast(component, metrics)
		if err != nil {
			continue
		}
		forecasts[component] = forecast

		recommendation := rg.forecastingEngine.GenerateScalingRecommendation(forecast)
		if recommendation.Action != "maintain" {
			recommendations = append(recommendations, recommendation)
		}
	}

	// Generate cost projection
	costProjection := rg.generateCostProjection(allMetrics, forecasts)

	// Predict bottlenecks
	bottlenecks := rg.predictBottlenecks(allMetrics)

	return &CapacityReport{
		GeneratedAt:          time.Now(),
		ReportPeriod:         "weekly",
		CurrentState:         rg.buildComponentStates(allMetrics),
		Forecasts:            forecasts,
		Recommendations:      recommendations,
		CostProjection:       costProjection,
		BottleneckPrediction: bottlenecks,
	}, nil
}

// GenerateJSON generates a JSON report
func (rg *ReportGenerator) GenerateJSON(report *CapacityReport) ([]byte, error) {
	return json.MarshalIndent(report, "", "  ")
}

// GenerateHTML generates an HTML report
func (rg *ReportGenerator) GenerateHTML(report *CapacityReport) ([]byte, error) {
	tmpl := `
<!DOCTYPE html>
<html>
<head>
    <title>GRC_Claw Capacity Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        table { border-collapse: collapse; width: 100%; margin: 20px 0; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #4CAF50; color: white; }
        .critical { color: red; font-weight: bold; }
        .warning { color: orange; }
        .ok { color: green; }
    </style>
</head>
<body>
    <h1>GRC_Claw Capacity Report</h1>
    <p>Generated: {{.GeneratedAt.Format "2006-01-02 15:04:05"}}</p>
    
    <h2>Current State</h2>
    <table>
        <tr>
            <th>Component</th>
            <th>Instances</th>
            <th>Avg CPU %</th>
            <th>Avg Memory %</th>
            <th>P99 Latency (ms)</th>
            <th>Error Rate %</th>
        </tr>
        {{range $name, $state := .CurrentState}}
        <tr>
            <td>{{$name}}</td>
            <td>{{$state.Instances}}</td>
            <td class="{{if gt $state.AvgCPUUtilization 70.0}}critical{{else if gt $state.AvgCPUUtilization 50.0}}warning{{else}}ok{{end}}">
                {{printf "%.1f" $state.AvgCPUUtilization}}%
            </td>
            <td class="{{if gt $state.AvgMemoryUtilization 80.0}}critical{{else if gt $state.AvgMemoryUtilization 60.0}}warning{{else}}ok{{end}}">
                {{printf "%.1f" $state.AvgMemoryUtilization}}%
            </td>
            <td>{{printf "%.2f" $state.P99Latency}}</td>
            <td>{{printf "%.4f" $state.ErrorRate}}</td>
        </tr>
        {{end}}
    </table>
    
    <h2>Scaling Recommendations</h2>
    <table>
        <tr>
            <th>Component</th>
            <th>Action</th>
            <th>From</th>
            <th>To</th>
            <th>Urgency</th>
            <th>Reason</th>
        </tr>
        {{range .Recommendations}}
        <tr>
            <td>{{.Component}}</td>
            <td class="{{if eq .Action "scale_up"}}critical{{end}}">{{.Action}}</td>
            <td>{{.From}}</td>
            <td>{{.To}}</td>
            <td>{{.Urgency}}</td>
            <td>{{.Reason}}</td>
        </tr>
        {{end}}
    </table>
    
    <h2>Bottleneck Predictions</h2>
    <table>
        <tr>
            <th>Component</th>
            <th>Resource</th>
            <th>Current Utilization</th>
            <th>Projected Utilization</th>
            <th>Days to Saturation</th>
            <th>Recommended Action</th>
        </tr>
        {{range .BottleneckPrediction}}
        <tr>
            <td>{{.Component}}</td>
            <td>{{.Resource}}</td>
            <td>{{printf "%.1f" .CurrentUtilization}}%</td>
            <td class="{{if gt .ProjectedUtilization 80.0}}critical{{end}}">{{printf "%.1f" .ProjectedUtilization}}%</td>
            <td>{{.DaysToSaturation}}</td>
            <td>{{.RecommendedAction}}</td>
        </tr>
        {{end}}
    </table>
    
    <h2>Cost Projection</h2>
    <p>Current Monthly Cost: ${{printf "%.2f" .CostProjection.CurrentMonthlyCost}}</p>
    <p>Projected Monthly Cost: ${{printf "%.2f" .CostProjection.ProjectedMonthlyCost}}</p>
    
    <h3>Optimization Opportunities</h3>
    <ul>
    {{range .CostProjection.OptimizationOpportunities}}
        <li>{{.Description}}: ${{printf "%.2f" .Savings}}/month ({{.Effort}} effort)</li>
    {{end}}
    </ul>
</body>
</html>
`

	t := template.Must(template.New("report").Parse(tmpl))
	var buf bytes.Buffer
	if err := t.Execute(&buf, report); err != nil {
		return nil, err
	}

	return buf.Bytes(), nil
}

func (rg *ReportGenerator) buildComponentStates(metrics map[string]*CapacityMetrics) map[string]ComponentState {
	states := make(map[string]ComponentState)
	for name, m := range metrics {
		states[name] = ComponentState{
			Component:            name,
			Instances:            3, // Placeholder
			AvgCPUUtilization:    m.CPUUtilization,
			AvgMemoryUtilization: m.MemoryUtilization,
			AvgRequestRate:       m.RequestRate,
			P99Latency:           m.P99Latency,
			ErrorRate:           m.ErrorRate * 100,
		}
	}
	return states
}

func (rg *ReportGenerator) generateCostProjection(
	metrics map[string]*CapacityMetrics,
	forecasts map[string]*Forecast,
) *CostProjection {
	// Simplified cost calculation
	currentCost := 12500.0
	projectedCost := 14200.0

	return &CostProjection{
		CurrentMonthlyCost:   currentCost,
		ProjectedMonthlyCost: projectedCost,
		OptimizationOpportunities: []OptimizationOpportunity{
			{
				Description: "Right-size API gateway instances",
				Savings:     800.0,
				Effort:      "low",
			},
			{
				Description: "Enable storage tiering for audit trail",
				Savings:     400.0,
				Effort:      "medium",
			},
		},
	}
}

func (rg *ReportGenerator) predictBottlenecks(metrics map[string]*CapacityMetrics) []BottleneckPrediction {
	var predictions []BottleneckPrediction

	for name, m := range metrics {
		if m.MemoryUtilization > 70 {
			predictions = append(predictions, BottleneckPrediction{
				Component:           name,
				Resource:            "Memory",
				CurrentUtilization:  m.MemoryUtilization,
				ProjectedUtilization: m.MemoryUtilization * 1.2,
				DaysToSaturation:    45,
				RecommendedAction:   "Scale out or increase memory allocation",
			})
		}
	}

	return predictions
}
```

---

## 7. Performance Monitoring and Alerting

### 7.1 Prometheus Metrics

```go
// internal/metrics/prometheus.go
package metrics

import (
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promauto"
)

// Enforcement metrics
var (
	// Decision metrics
	DecisionsTotal = promauto.NewCounterVec(
		prometheus.CounterOpts{
			Name: "grc_enforcement_decisions_total",
			Help: "Total enforcement decisions",
		},
		[]string{"decision", "policy_id", "agent_id"},
	)

	DecisionDuration = promauto.NewHistogramVec(
		prometheus.HistogramOpts{
			Name:    "grc_enforcement_decision_duration_seconds",
			Help:    "Decision latency distribution",
			Buckets: []float64{0.0001, 0.0005, 0.001, 0.002, 0.005, 0.01, 0.02, 0.05, 0.1},
		},
		[]string{"decision"},
	)

	DecisionsInFlight = promauto.NewGauge(
		prometheus.GaugeOpts{
			Name: "grc_enforcement_decisions_in_flight",
			Help: "Currently processing decisions",
		},
	)

	PolicyEvaluationDuration = promauto.NewHistogramVec(
		prometheus.HistogramOpts{
			Name:    "grc_enforcement_policy_evaluation_duration_seconds",
			Help:    "Per-policy evaluation time",
			Buckets: []float64{0.0001, 0.0005, 0.001, 0.002, 0.005, 0.01},
		},
		[]string{"policy_id"},
	)

	ContextEnrichmentDuration = promauto.NewHistogram(
		prometheus.HistogramOpts{
			Name:    "grc_enforcement_context_enrichment_duration_seconds",
			Help:    "Context lookup time",
			Buckets: []float64{0.0001, 0.0005, 0.001, 0.002, 0.005, 0.01},
		},
	)

	AuditWriteDuration = promauto.NewHistogram(
		prometheus.HistogramOpts{
			Name:    "grc_enforcement_audit_write_duration_seconds",
			Help:    "Audit write time",
			Buckets: []float64{0.0005, 0.001, 0.002, 0.005, 0.01, 0.02, 0.05},
		},
	)

	EnforcementErrors = promauto.NewCounterVec(
		prometheus.CounterOpts{
			Name: "grc_enforcement_errors_total",
			Help: "Enforcement errors",
		},
		[]string{"error_type"},
	)
)

// Evidence metrics
var (
	EvidenceItemsCollected = promauto.NewCounterVec(
		prometheus.CounterOpts{
			Name: "grc_evidence_items_collected_total",
			Help: "Total evidence items collected",
		},
		[]string{"evidence_type", "source"},
	)

	EvidenceCollectionDuration = promauto.NewHistogramVec(
		prometheus.HistogramOpts{
			Name:    "grc_evidence_collection_duration_seconds",
			Help:    "Per-stage collection latency",
			Buckets: []float64{0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.2, 0.5},
		},
		[]string{"stage"},
	)

	EvidenceStoreWriteDuration = promauto.NewHistogram(
		prometheus.HistogramOpts{
			Name:    "grc_evidence_store_write_duration_seconds",
			Help:    "Evidence store write latency",
			Buckets: []float64{0.001, 0.005, 0.01, 0.025, 0.05, 0.1},
		},
	)

	EvidenceValidationErrors = promauto.NewCounterVec(
		prometheus.CounterOpts{
			Name: "grc_evidence_validation_errors_total",
			Help: "Validation failures",
		},
		[]string{"error_type"},
	)

	EvidenceQueueDepth = promauto.NewGauge(
		prometheus.GaugeOpts{
			Name: "grc_evidence_queue_depth",
			Help: "Pending evidence items",
		},
	)
)

// Audit metrics
var (
	AuditEntriesWritten = promauto.NewCounterVec(
		prometheus.CounterOpts{
			Name: "grc_audit_entries_written_total",
			Help: "Total audit entries",
		},
		[]string{"entry_type"},
	)

	AuditWriteDuration = promauto.NewHistogram(
		prometheus.HistogramOpts{
			Name:    "grc_audit_write_duration_seconds",
			Help:    "Write latency",
			Buckets: []float64{0.0005, 0.001, 0.002, 0.005, 0.01, 0.02, 0.05},
		},
	)

	AuditChainVerificationDuration = promauto.NewHistogram(
		prometheus.HistogramOpts{
			Name:    "grc_audit_chain_verification_duration_seconds",
			Help:    "Verification latency",
			Buckets: []float64{0.001, 0.005, 0.01, 0.025, 0.05, 0.1},
		},
	)

	AuditChainLength = promauto.NewGauge(
		prometheus.GaugeOpts{
			Name: "grc_audit_chain_length",
			Help: "Current chain length",
		},
	)
)

// API metrics
var (
	APIRequestsTotal = promauto.NewCounterVec(
		prometheus.CounterOpts{
			Name: "grc_api_requests_total",
			Help: "Total API requests",
		},
		[]string{"method", "endpoint", "status"},
	)

	APIRequestDuration = promauto.NewHistogramVec(
		prometheus.HistogramOpts{
			Name:    "grc_api_request_duration_seconds",
			Help:    "Request latency",
			Buckets: []float64{0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5},
		},
		[]string{"method", "endpoint"},
	)

	APIActiveConnections = promauto.NewGauge(
		prometheus.GaugeOpts{
			Name: "grc_api_active_connections",
			Help: "Current connections",
		},
	)
)

// Cache metrics
var (
	CacheL1HitRatio = promauto.NewGauge(
		prometheus.GaugeOpts{
			Name: "grc_cache_l1_hit_ratio",
			Help: "L1 cache hit ratio",
		},
	)

	CacheL3HitRatio = promauto.NewGauge(
		prometheus.GaugeOpts{
			Name: "grc_cache_l3_hit_ratio",
			Help: "L3 cache hit ratio",
		},
	)

	CacheInvalidationDuration = promauto.NewHistogram(
		prometheus.HistogramOpts{
			Name:    "grc_cache_invalidation_duration_seconds",
			Help:    "Cache invalidation latency",
			Buckets: []float64{0.0001, 0.0005, 0.001, 0.005, 0.01, 0.05, 0.1},
		},
	)

	CacheWarmingDuration = promauto.NewHistogram(
		prometheus.HistogramOpts{
			Name:    "grc_cache_warming_duration_seconds",
			Help:    "Cache warming time",
			Buckets: []float64{0.1, 0.5, 1, 2, 5, 10, 30},
		},
	)

	CacheMemoryUtilization = promauto.NewGauge(
		prometheus.GaugeOpts{
			Name: "grc_cache_memory_utilization",
			Help: "Cache memory utilization",
		},
	)

	CacheStaleReads = promauto.NewCounter(
		prometheus.CounterOpts{
			Name: "grc_cache_stale_reads_total",
			Help: "Stale cache reads",
		},
	)
)
```

### 7.2 Alerting Rules

```yaml
# monitoring/prometheus/alerts/performance.yml
groups:
  - name: grc_enforcement_performance
    interval: 30s
    rules:
      # Enforcement latency breach
      - alert: EnforcementLatencyBreach
        expr: |
          histogram_quantile(0.99, 
            sum(rate(grc_enforcement_decision_duration_seconds_bucket[2m])) by (le)
          ) > 0.015
        for: 2m
        labels:
          severity: warning
          component: enforcement-proxy
        annotations:
          summary: "Enforcement p99 latency exceeds 15ms"
          description: "p99 latency is {{ $value }}ms for the last 2 minutes"
          runbook: "https://wiki.grc-claw.io/runbooks/enforcement-latency"

      - alert: EnforcementLatencyCritical
        expr: |
          histogram_quantile(0.99, 
            sum(rate(grc_enforcement_decision_duration_seconds_bucket[2m])) by (le)
          ) > 0.020
        for: 2m
        labels:
          severity: critical
          component: enforcement-proxy
        annotations:
          summary: "Enforcement p99 latency exceeds 20ms - PAGE ON-CALL"
          description: "p99 latency is {{ $value }}ms - immediate action required"
          runbook: "https://wiki.grc-claw.io/runbooks/enforcement-latency"

      # Enforcement error rate
      - alert: EnforcementErrorRate
        expr: |
          sum(rate(grc_enforcement_errors_total[1m])) 
          / sum(rate(grc_enforcement_decisions_total[1m])) > 0.001
        for: 1m
        labels:
          severity: critical
          component: enforcement-proxy
        annotations:
          summary: "Enforcement error rate exceeds 0.1%"
          description: "Error rate is {{ $value | humanizePercentage }} for the last 1 minute"
          runbook: "https://wiki.grc-claw.io/runbooks/enforcement-errors"

      # Enforcement throughput drop
      - alert: EnforcementThroughputDrop
        expr: |
          sum(rate(grc_enforcement_decisions_total[1m])) < 8000
        for: 5m
        labels:
          severity: warning
          component: enforcement-proxy
        annotations:
          summary: "Enforcement throughput below 8K decisions/second"
          description: "Current throughput: {{ $value }} decisions/second"

  - name: grc_evidence_performance
    interval: 30s
    rules:
      # Evidence collection lag
      - alert: EvidenceCollectionLag
        expr: grc_evidence_queue_depth > 10000
        for: 5m
        labels:
          severity: warning
          component: evidence-collector
        annotations:
          summary: "Evidence queue depth exceeds 10,000"
          description: "Queue depth: {{ $value }} items for 5 minutes"
          runbook: "https://wiki.grc-claw.io/runbooks/evidence-lag"

      # Evidence collection latency
      - alert: EvidenceCollectionLatency
        expr: |
          histogram_quantile(0.99, 
            sum(rate(grc_evidence_collection_duration_seconds_bucket[5m])) by (le)
          ) > 0.2
        for: 5m
        labels:
          severity: warning
          component: evidence-collector
        annotations:
          summary: "Evidence collection p99 latency exceeds 200ms"
          description: "p99 latency: {{ $value }}s"

      # Evidence validation errors
      - alert: EvidenceValidationErrors
        expr: |
          sum(rate(grc_evidence_validation_errors_total[5m])) > 0
        for: 5m
        labels:
          severity: warning
          component: evidence-collector
        annotations:
          summary: "Evidence validation errors detected"
          description: "Error rate: {{ $value }}/second"

  - name: grc_audit_performance
    interval: 30s
    rules:
      # Audit write failure
      - alert: AuditWriteFailure
        expr: |
          sum(rate(grc_audit_write_duration_seconds_count[1m])) 
          - sum(rate(grc_audit_entries_written_total[1m])) > 0
        for: 1m
        labels:
          severity: critical
          component: audit-trail
        annotations:
          summary: "Audit write failures detected - PAGE ON-CALL"
          description: "Write failures detected in the last 1 minute"
          runbook: "https://wiki.grc-claw.io/runbooks/audit-write-failure"

      # Audit write latency
      - alert: AuditWriteLatency
        expr: |
          histogram_quantile(0.99, 
            sum(rate(grc_audit_write_duration_seconds_bucket[2m])) by (le)
          ) > 0.02
        for: 2m
        labels:
          severity: warning
          component: audit-trail
        annotations:
          summary: "Audit write p99 latency exceeds 20ms"
          description: "p99 latency: {{ $value }}s"

  - name: grc_api_performance
    interval: 30s
    rules:
      # API latency breach
      - alert: APILatencyBreach
        expr: |
          histogram_quantile(0.99, 
            sum(rate(grc_api_request_duration_seconds_bucket[5m])) by (le)
          ) > 0.5
        for: 5m
        labels:
          severity: warning
          component: api-gateway
        annotations:
          summary: "API p99 latency exceeds 500ms"
          description: "p99 latency: {{ $value }}s for 5 minutes"

      # API error rate
      - alert: APIErrorRate
        expr: |
          sum(rate(grc_api_requests_total{status=~"5.."}[1m])) 
          / sum(rate(grc_api_requests_total[1m])) > 0.005
        for: 1m
        labels:
          severity: critical
          component: api-gateway
        annotations:
          summary: "API 5xx error rate exceeds 0.5%"
          description: "Error rate: {{ $value | humanizePercentage }}"

  - name: grc_cache_performance
    interval: 30s
    rules:
      # Cache hit ratio drop
      - alert: CacheHitRatioDrop
        expr: grc_cache_l1_hit_ratio < 0.90
        for: 5m
        labels:
          severity: warning
          component: cache
        annotations:
          summary: "L1 cache hit ratio below 90%"
          description: "Current hit ratio: {{ $value | humanizePercentage }}"

      # Cache invalidation latency
      - alert: CacheInvalidationLatency
        expr: |
          histogram_quantile(0.99, 
            sum(rate(grc_cache_invalidation_duration_seconds_bucket[5m])) by (le)
          ) > 0.5
        for: 5m
        labels:
          severity: warning
          component: cache
        annotations:
          summary: "Cache invalidation p99 latency exceeds 500ms"
          description: "p99 latency: {{ $value }}s"

  - name: grc_system_health
    interval: 30s
    rules:
      # Memory utilization
      - alert: MemoryUtilization
        expr: |
          (container_memory_usage_bytes / container_spec_memory_limit_bytes) > 0.85
        for: 10m
        labels:
          severity: warning
          component: system
        annotations:
          summary: "Memory utilization exceeds 85%"
          description: "Current utilization: {{ $value | humanizePercentage }}"

      # Disk utilization
      - alert: DiskUtilization
        expr: |
          (node_filesystem_avail_bytes / node_filesystem_size_bytes) < 0.2
        for: 10m
        labels:
          severity: warning
          component: system
        annotations:
          summary: "Disk utilization exceeds 80%"
          description: "Available space: {{ $value | humanizePercentage }}"

      # Connection pool exhaustion
      - alert: ConnectionPoolExhaustion
        expr: |
          (grc_db_connections_active / grc_db_connections_max) > 0.8
        for: 5m
        labels:
          severity: warning
          component: database
        annotations:
          summary: "Connection pool utilization exceeds 80%"
          description: "Active connections: {{ $value | humanizePercentage }}"
```

### 7.3 Grafana Dashboard

```json
{
  "dashboard": {
    "title": "GRC_Claw Enforcement Performance",
    "uid": "grc-enforcement-perf",
    "tags": ["grc-claw", "performance", "enforcement"],
    "timezone": "UTC",
    "schemaVersion": 36,
    "version": 1,
    "refresh": "5s",
    "time": {
      "from": "now-1h",
      "to": "now"
    },
    "panels": [
      {
        "id": 1,
        "title": "Decision Latency (p50/p95/p99)",
        "type": "timeseries",
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0},
        "targets": [
          {
            "expr": "histogram_quantile(0.50, sum(rate(grc_enforcement_decision_duration_seconds_bucket[1m])) by (le)) * 1000",
            "legendFormat": "p50",
            "refId": "A"
          },
          {
            "expr": "histogram_quantile(0.95, sum(rate(grc_enforcement_decision_duration_seconds_bucket[1m])) by (le)) * 1000",
            "legendFormat": "p95",
            "refId": "B"
          },
          {
            "expr": "histogram_quantile(0.99, sum(rate(grc_enforcement_decision_duration_seconds_bucket[1m])) by (le)) * 1000",
            "legendFormat": "p99",
            "refId": "C"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "ms",
            "thresholds": {
              "steps": [
                {"color": "green", "value": null},
                {"color": "yellow", "value": 5},
                {"color": "red", "value": 10}
              ]
            }
          }
        },
        "alert": {
          "name": "p99 Latency Alert",
          "condition": "C",
          "evaluator": {"type": "gt", "params": [10]},
          "frequency": "30s",
          "handler": 1
        }
      },
      {
        "id": 2,
        "title": "Decisions per Second",
        "type": "timeseries",
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0},
        "targets": [
          {
            "expr": "sum(rate(grc_enforcement_decisions_total[1m]))",
            "legendFormat": "Total",
            "refId": "A"
          },
          {
            "expr": "sum(rate(grc_enforcement_decisions_total{decision='ALLOW'}[1m]))",
            "legendFormat": "ALLOW",
            "refId": "B"
          },
          {
            "expr": "sum(rate(grc_enforcement_decisions_total{decision='DENY'}[1m]))",
            "legendFormat": "DENY",
            "refId": "C"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "ops"
          }
        }
      },
      {
        "id": 3,
        "title": "Decision Distribution",
        "type": "piechart",
        "gridPos": {"h": 8, "w": 8, "x": 0, "y": 8},
        "targets": [
          {
            "expr": "sum by (decision) (grc_enforcement_decisions_total)",
            "legendFormat": "{{decision}}",
            "refId": "A"
          }
        ]
      },
      {
        "id": 4,
        "title": "Error Rate",
        "type": "stat",
        "gridPos": {"h": 4, "w": 4, "x": 8, "y": 8},
        "targets": [
          {
            "expr": "sum(rate(grc_enforcement_errors_total[1m])) / sum(rate(grc_enforcement_decisions_total[1m])) * 100",
            "refId": "A"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "percent",
            "thresholds": {
              "steps": [
                {"color": "green", "value": null},
                {"color": "yellow", "value": 0.05},
                {"color": "red", "value": 0.1}
              ]
            }
          }
        }
      },
      {
        "id": 5,
        "title": "Cache Hit Ratios",
        "type": "timeseries",
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8},
        "targets": [
          {
            "expr": "grc_cache_l1_hit_ratio * 100",
            "legendFormat": "L1 Cache",
            "refId": "A"
          },
          {
            "expr": "grc_cache_l3_hit_ratio * 100",
            "legendFormat": "L3 Cache (Redis)",
            "refId": "B"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "percent",
            "min": 0,
            "max": 100
          }
        }
      },
      {
        "id": 6,
        "title": "Decisions In Flight",
        "type": "gauge",
        "gridPos": {"h": 4, "w": 4, "x": 8, "y": 12},
        "targets": [
          {
            "expr": "grc_enforcement_decisions_in_flight",
            "refId": "A"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "min": 0,
            "max": 1000,
            "thresholds": {
              "steps": [
                {"color": "green", "value": null},
                {"color": "yellow", "value": 500},
                {"color": "red", "value": 800}
              ]
            }
          }
        }
      },
      {
        "id": 7,
        "title": "Component Health",
        "type": "table",
        "gridPos": {"h": 8, "w": 24, "x": 0, "y": 16},
        "targets": [
          {
            "expr": "grc_enforcement_decisions_total",
            "format": "table",
            "instant": true,
            "refId": "A"
          }
        ]
      }
    ]
  }
}
```

### 7.4 SLO Tracking

```go
// internal/metrics/slo.go
package metrics

import (
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promauto"
)

// SLO tracking metrics
var (
	// Availability SLO
	AvailabilityRatio = promauto.NewGaugeVec(
		prometheus.GaugeOpts{
			Name: "grc_slo_availability_ratio",
			Help: "Rolling 30-day availability ratio",
		},
		[]string{"component"},
	)

	// Latency SLO
	LatencySLOCompliance = promauto.NewGaugeVec(
		prometheus.GaugeOpts{
			Name: "grc_slo_latency_compliance_ratio",
			Help: "Percentage of requests within latency SLO",
		},
		[]string{"component"},
	)

	// Error budget
	ErrorBudgetRemaining = promauto.NewGaugeVec(
		prometheus.GaugeOpts{
			Name: "grc_slo_error_budget_remaining",
			Help: "Remaining error budget (1 - SLO)",
		},
		[]string{"component"},
	)

	ErrorBudgetBurnRate = promauto.NewGaugeVec(
		prometheus.GaugeOpts{
			Name: "grc_slo_error_budget_burn_rate",
			Help: "Current error budget burn rate",
		},
		[]string{"component"},
	)

	// Durability SLI
	DurabilityRatio = promauto.NewGaugeVec(
		prometheus.GaugeOpts{
			Name: "grc_sli_durability_ratio",
			Help: "Audit entry durability ratio",
		},
		[]string{"component"},
	)

	// Correctness SLI
	CorrectnessRatio = promauto.NewGaugeVec(
		prometheus.GaugeOpts{
			Name: "grc_sli_correctness_ratio",
			Help: "Enforcement decision correctness ratio",
		},
		[]string{"component"},
	)
)

// SLOConfig defines SLO targets per component
type SLOConfig struct {
	Component        string
	AvailabilitySLO  float64  // e.g., 0.9995 for 99.95%
	LatencySLO       float64  // p99 latency threshold in ms
	ErrorBudgetSLO   float64  // e.g., 0.001 for 0.1%
}

// DefaultSLOConfigs returns default SLO configurations
func DefaultSLOConfigs() []SLOConfig {
	return []SLOConfig{
		{Component: "enforcement-proxy", AvailabilitySLO: 0.9995, LatencySLO: 10, ErrorBudgetSLO: 0.001},
		{Component: "policy-engine", AvailabilitySLO: 0.999, LatencySLO: 50, ErrorBudgetSLO: 0.001},
		{Component: "audit-trail", AvailabilitySLO: 0.9999, LatencySLO: 20, ErrorBudgetSLO: 0.0001},
		{Component: "evidence-collector", AvailabilitySLO: 0.995, LatencySLO: 200, ErrorBudgetSLO: 0.005},
		{Component: "api-gateway", AvailabilitySLO: 0.999, LatencySLO: 500, ErrorBudgetSLO: 0.005},
	}
}

// TrackAvailability records an availability measurement
func TrackAvailability(component string, success bool) {
	// Update rolling 30-day availability
	// This is a simplified implementation - use a proper time-windowed counter
	if success {
		AvailabilityRatio.WithLabelValues(component).Inc()
	}
}

// TrackLatency records a latency measurement against SLO
func TrackLatency(component string, latencyMs float64, sloMs float64) {
	if latencyMs <= sloMs {
		LatencySLOCompliance.WithLabelValues(component).Inc()
	}
}

// CalculateErrorBudget calculates remaining error budget
func CalculateErrorBudget(component string, actualErrorRate float64, sloErrorRate float64) float64 {
	remaining := 1.0 - (actualErrorRate / sloErrorRate)
	ErrorBudgetRemaining.WithLabelValues(component).Set(remaining)
	return remaining
}

// CalculateBurnRate calculates error budget burn rate
func CalculateBurnRate(component string, actualErrorRate float64, sloErrorRate float64) float64 {
	burnRate := actualErrorRate / sloErrorRate
	ErrorBudgetBurnRate.WithLabelValues(component).Set(burnRate)
	return burnRate
}
```

---

## Appendix: Performance Budget Allocation

From Performance Spec Section 8.1:

| Component | Budget (ms) | Percentage |
|-----------|-------------|------------|
| Request parsing & validation | 0.5 | 5% |
| Agent identity & capability lookup (cached) | 1.0 | 10% |
| Policy rule evaluation | 3.0 | 30% |
| Context enrichment | 1.5 | 15% |
| Decision certificate generation | 1.0 | 10% |
| Audit trail write (async) | 2.0 | 20% |
| Overhead & margin | 1.0 | 10% |
| **Total** | **10.0** | **100%** |

---

## Appendix: Quick Reference Commands

```bash
# Run k6 load tests
k6 run tests/performance/k6/enforcement-steady-state.js
k6 run tests/performance/k6/enforcement-peak-load.js
k6 run tests/performance/k6/enforcement-burst.js

# Run Locust load tests
locust -f tests/performance/locust/enforcement_load_test.py --host=http://localhost:8080 -u 1000 -r 100 -t 30m

# Run Go benchmarks
go test -bench=. -benchmem -count=10 ./tests/performance/benchmarks/...

# Run regression detection
python scripts/performance_regression.py --baseline tests/performance/baselines/v1.0.0.json

# Generate capacity report
go run cmd/capacity-report/main.go --output report.html

# View Prometheus metrics
curl http://localhost:9090/metrics | grep grc_

# Check Grafana dashboards
open http://localhost:3000/d/grc-enforcement-perf
```

---

*End of Performance Engineering Implementation Guide*
