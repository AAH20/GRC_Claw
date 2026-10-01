# GRC_Claw Scalability Implementation Guide

**Version:** 1.0  
**Date:** 2026-10-01  
**Status:** Draft  
**Owner:** GRC_Claw Architecture Team  
**References:** GRC_Claw Scalability Specification v2.0, GRC_Claw Performance Specification v2.0

---

## Table of Contents

1. [Auto-Scaling Implementation (K8s HPA/VPA)](#1-auto-scaling-implementation)
2. [Data Sharding Implementation (Python)](#2-data-sharding-implementation)
3. [Cache Invalidation Implementation](#3-cache-invalidation-implementation)
4. [Rate Limiting Implementation](#4-rate-limiting-implementation)
5. [Multi-Tenancy Implementation](#5-multi-tenancy-implementation)
6. [Load Balancing Configuration](#6-load-balancing-configuration)
7. [Scalability Testing Framework](#7-scalability-testing-framework)

---

## 1. Auto-Scaling Implementation

GRC_Claw uses Kubernetes Horizontal Pod Autoscaler (HPA) and Vertical Pod Autoscaler (VPA) to dynamically adjust capacity based on demand. The system implements four elasticity patterns: reactive, predictive, event-driven, and scale-to-zero.

### 1.1 HPA Configuration for PEP (Enforcement Proxy)

The PEP is the most frequently scaled component. It is stateless, enabling horizontal scale-out and instant failover.

```yaml
# hpa/grc-pep-hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: grc-pep-hpa
  namespace: grc-claw
  labels:
    app: grc-pep-gateway
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
        - type: Percent
          value: 100
          periodSeconds: 60
      selectPolicy: Max
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
        - type: Pods
          value: 1
          periodSeconds: 120
        - type: Percent
          value: 10
          periodSeconds: 120
      selectPolicy: Min
```

### 1.2 HPA Configuration for PDP (Policy Decision Point)

PDP scales based on evaluation queue depth and CPU utilization.

```yaml
# hpa/grc-pdp-hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: grc-pdp-hpa
  namespace: grc-claw
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: grc-pdp
  minReplicas: 2
  maxReplicas: 50
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: External
      external:
        metric:
          name: grc_enforcement_evaluation_queue_depth
          selector:
            matchLabels:
              app: grc-pdp
        target:
          type: AverageValue
          averageValue: "1000"
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
        - type: Pods
          value: 2
          periodSeconds: 60
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
        - type: Pods
          value: 1
          periodSeconds: 120
```

### 1.3 HPA Configuration for Evidence Collector

Evidence collectors scale based on Kafka consumer lag.

```yaml
# hpa/grc-evidence-collector-hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: grc-evidence-collector-hpa
  namespace: grc-claw
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: grc-evidence-collector
  minReplicas: 2
  maxReplicas: 96
  metrics:
    - type: External
      external:
        metric:
          name: kafka_consumer_group_lag
          selector:
            matchLabels:
              topic: evidence-events
              consumer-group: evidence-processors
        target:
          type: AverageValue
          averageValue: "10000"
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 120
      policies:
        - type: Pods
          value: 4
          periodSeconds: 120
    scaleDown:
      stabilizationWindowSeconds: 600
      policies:
        - type: Pods
          value: 2
          periodSeconds: 300
```

### 1.4 VPA Configuration

VPA provides resource recommendations and can automatically adjust requests/limits.

```yaml
# vpa/grc-pep-vpa.yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: grc-pep-vpa
  namespace: grc-claw
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: grc-pep-gateway
  updatePolicy:
    updateMode: "Auto"
    minReplicas: 2
  resourcePolicy:
    containerPolicies:
      - containerName: grc-pep
        minAllowed:
          cpu: 500m
          memory: 1Gi
        maxAllowed:
          cpu: 4
          memory: 8Gi
        controlledResources: ["cpu", "memory"]
        controlledValues: RequestsAndLimits
```

### 1.5 KEDA for Event-Driven and Scale-to-Zero

KEDA enables event-driven scaling based on Kafka lag, Prometheus metrics, and cron schedules.

```yaml
# keda/grc-pep-event-scaler.yaml
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: grc-pep-event-scaler
  namespace: grc-claw
spec:
  scaleTargetRef:
    name: grc-pep-gateway
  minReplicaCount: 2
  maxReplicaCount: 100
  cooldownPeriod: 300
  pollingInterval: 15
  triggers:
    # Scale on Kafka lag
    - type: kafka
      metadata:
        bootstrapServers: kafka:9092
        consumerGroup: enforcement-requests
        topic: enforcement-requests
        lagThreshold: "500"
    # Scale on custom Prometheus metric
    - type: prometheus
      metadata:
        serverAddress: http://prometheus:9090
        metricName: grc_enforcement_queue_depth
        threshold: "1000"
        query: sum(grc_enforcement_queue_depth)
    # Scale on cron schedule (business hours)
    - type: cron
      metadata:
        timezone: America/New_York
        start: 0 8 * * 1-5
        end: 0 18 * * 1-5
        desiredReplicas: "10"
```

### 1.6 Scale-to-Zero for Non-Production

```yaml
# keda/grc-evidence-collector-zero-scaler.yaml
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: grc-evidence-collector-zero-scaler
  namespace: grc-claw-staging
spec:
  scaleTargetRef:
    name: grc-evidence-collector
  minReplicaCount: 0
  maxReplicaCount: 96
  cooldownPeriod: 300
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
        start: 0 18 * * 1-5
        end: 0 8 * * 1-5
        desiredReplicas: "0"
```

### 1.7 Custom Metrics Pipeline

HPA requires custom metrics from Prometheus Adapter.

```yaml
# config/prometheus-adapter-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-adapter-config
  namespace: monitoring
data:
  config.yaml: |
    rules:
    - seriesQuery: 'grc_enforcement_decision_duration_seconds'
      resources:
        overrides:
          namespace: {resource: namespace}
          pod: {resource: pod}
      name:
        as: "grc_enforcement_decision_duration_seconds"
      metricsQuery: 'histogram_quantile(0.99, sum(rate(<<.Series>>{<<.LabelMatchers>>}[2m])) by (le, <<.GroupBy>>))'
    - seriesQuery: 'kafka_consumer_group_lag'
      resources:
        overrides:
          namespace: {resource: namespace}
      name:
        as: "kafka_consumer_group_lag"
      metricsQuery: 'max(kafka_consumer_group_lag{<<.LabelMatchers>>}) by (<<.GroupBy>>)'
    - seriesQuery: 'grc_enforcement_evaluation_queue_depth'
      resources:
        overrides:
          namespace: {resource: namespace}
          pod: {resource: pod}
      name:
        as: "grc_enforcement_evaluation_queue_depth"
      metricsQuery: 'sum(<<.Series>>{<<.LabelMatchers>>}) by (<<.GroupBy>>)'
```

### 1.8 Multi-Dimensional Scaling Logic

```python
# scaler/multi_dimensional_scaler.py
import math
from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class ScalingDecision:
    desired_replicas: int
    reason: str
    confidence: float


class MultiDimensionalScaler:
    """Scale based on multiple metrics with priority weighting."""

    SIGNALS = {
        "cpu": {
            "weight": 0.3,
            "scale_out_threshold": 70,
            "scale_in_threshold": 30,
        },
        "memory": {
            "weight": 0.2,
            "scale_out_threshold": 80,
            "scale_in_threshold": 40,
        },
        "latency_p99": {
            "weight": 0.3,
            "scale_out_threshold_ms": 15,
            "scale_in_threshold_ms": 5,
        },
        "queue_depth": {
            "weight": 0.2,
            "scale_out_threshold": 1000,
            "scale_in_threshold": 100,
        },
    }

    def __init__(self, min_replicas: int = 2, max_replicas: int = 100):
        self.min_replicas = min_replicas
        self.max_replicas = max_replicas

    def compute_desired_replicas(
        self, current: int, metrics: Dict[str, float]
    ) -> ScalingDecision:
        """Compute desired replica count from multiple signals."""
        scale_out_score = 0.0
        scale_in_score = 0.0
        reasons = []

        for signal, config in self.SIGNALS.items():
            value = metrics.get(signal)
            if value is None:
                continue

            threshold_key_out = f"scale_out_threshold{signal.replace('latency_p99', '_ms')}"
            threshold_key_in = f"scale_in_threshold{signal.replace('latency_p99', '_ms')}"

            if signal == "latency_p99":
                if value > config["scale_out_threshold_ms"]:
                    scale_out_score += config["weight"]
                    reasons.append(f"latency_p99={value}ms > {config['scale_out_threshold_ms']}ms")
                elif value < config["scale_in_threshold_ms"]:
                    scale_in_score += config["weight"]
            else:
                if value > config["scale_out_threshold"]:
                    scale_out_score += config["weight"]
                    reasons.append(f"{signal}={value} > {config['scale_out_threshold']}")
                elif value < config["scale_in_threshold"]:
                    scale_in_score += config["weight"]

        if scale_out_score >= 0.5:
            step = max(1, int(math.ceil(current * scale_out_score * 0.5)))
            desired = min(current + step, self.max_replicas)
            return ScalingDecision(
                desired_replicas=desired,
                reason=f"Scale out: {', '.join(reasons)}",
                confidence=scale_out_score,
            )
        elif scale_in_score >= 0.5:
            step = max(1, int(math.ceil(current * scale_in_score * 0.25)))
            desired = max(current - step, self.min_replicas)
            return ScalingDecision(
                desired_replicas=desired,
                reason="Scale in: all signals below threshold",
                confidence=scale_in_score,
            )

        return ScalingDecision(
            desired_replicas=current,
            reason="No scaling needed",
            confidence=1.0 - max(scale_out_score, scale_in_score),
        )
```

### 1.9 Predictive Scaling

```python
# scaler/predictive_scaler.py
import math
from datetime import datetime, timedelta
from typing import Optional

import numpy as np
from sklearn.linear_model import LinearRegression


class PredictiveScaler:
    """Pre-scale based on historical traffic patterns."""

    def __init__(self, metrics_store, kubernetes_client):
        self.metrics = metrics_store
        self.k8s = kubernetes_client
        self.model = LinearRegression()

    async def forecast_demand(self, horizon_minutes: int = 30) -> dict:
        """Forecast demand for the next N minutes."""
        # Get historical traffic for the same time window
        now = datetime.utcnow()
        historical = await self.metrics.query_range(
            metric="enforcement_decisions_per_second",
            start=now - timedelta(days=30),
            end=now,
            step="5m",
        )

        if len(historical) < 10:
            return {"expected_rps": 10000, "peak_rps": 15000, "confidence": 0.5}

        # Simple linear regression on time-series
        X = np.arange(len(historical)).reshape(-1, 1)
        y = np.array([h["value"] for h in historical])
        self.model.fit(X, y)

        # Forecast
        future_X = np.arange(len(historical), len(historical) + horizon_minutes // 5).reshape(-1, 1)
        predictions = self.model.predict(future_X)

        return {
            "expected_rps": float(np.mean(predictions)),
            "peak_rps": float(np.percentile(predictions, 95)),
            "confidence": 0.85,
        }

    async def pre_scale(self, forecast: dict):
        """Pre-scale components before demand arrives."""
        peak_rps = forecast["peak_rps"]

        required_peps = math.ceil(peak_rps / 10000)  # 10K per PEP
        required_pdps = math.ceil(peak_rps / 5000)   # 5K per PDP

        await self.k8s.scale_deployment(
            name="grc-pep-gateway",
            replicas=required_peps,
            grace_period_seconds=300,
        )
        await self.k8s.scale_deployment(
            name="grc-pdp",
            replicas=required_pdps,
            grace_period_seconds=300,
        )
```

---

## 2. Data Sharding Implementation

GRC_Claw uses three partitioning strategies: hash partitioning for point lookups, range partitioning for time-series data, and list partitioning for silo-model tenants. Consistent hashing enables dynamic shard membership without full rebalancing.

### 2.1 Consistent Hash Ring

```python
# sharding/consistent_hash.py
import hashlib
from bisect import bisect_right
from typing import List, Optional, Set


class ConsistentHashRing:
    """Consistent hash ring with virtual nodes for shard assignment."""

    def __init__(self, replicas: int = 150):
        self.replicas = replicas
        self.ring: dict[int, str] = {}
        self.sorted_keys: List[int] = []
        self.nodes: Set[str] = set()

    def add_node(self, node: str) -> None:
        """Add a node to the ring with virtual replicas."""
        self.nodes.add(node)
        for i in range(self.replicas):
            key = self._hash(f"{node}:{i}")
            self.ring[key] = node
        self.sorted_keys = sorted(self.ring.keys())

    def remove_node(self, node: str) -> None:
        """Remove a node and its replicas from the ring."""
        self.nodes.discard(node)
        for i in range(self.replicas):
            key = self._hash(f"{node}:{i}")
            del self.ring[key]
        self.sorted_keys = sorted(self.ring.keys())

    def get_node(self, key: str) -> Optional[str]:
        """Get the node responsible for a given key."""
        if not self.ring:
            return None
        hash_key = self._hash(key)
        idx = bisect_right(self.sorted_keys, hash_key) % len(self.sorted_keys)
        return self.ring[self.sorted_keys[idx]]

    def get_nodes(self, key: str, n: int = 3) -> List[str]:
        """Get n distinct nodes for replication."""
        if not self.ring:
            return []
        nodes: List[str] = []
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

### 2.2 Shard Directory Service

```python
# sharding/shard_directory.py
import asyncio
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from cachetools import LRUCache


@dataclass
class ShardAssignment:
    shard_id: str
    region: str
    tier: str
    host: str
    port: int
    weight: int = 1


@dataclass
class ShardContext:
    tenant_id: str
    tenant_tier: str
    data_residency: str
    required_capabilities: List[str] = field(default_factory=list)


class ShardDirectory:
    """Directory-based shard resolver with caching."""

    def __init__(self, backend: "ShardDirectoryBackend", cache_size: int = 10000):
        self.backend = backend
        self.cache = LRUCache(maxsize=cache_size, ttl=30)

    async def resolve_shard(
        self, shard_key: str, context: ShardContext
    ) -> ShardAssignment:
        """Resolve a shard key to a physical shard."""
        cache_key = f"{shard_key}:{context.tenant_tier}:{context.data_residency}"

        if cached := self.cache.get(cache_key):
            return cached

        assignment = await self.backend.lookup(
            shard_key=shard_key,
            tenant_tier=context.tenant_tier,
            data_residency=context.data_residency,
            required_capabilities=context.required_capabilities,
        )

        self.cache[cache_key] = assignment
        return assignment

    async def rebalance(
        self, old_shards: List[str], new_shards: List[str]
    ) -> None:
        """Gradually migrate data from old shards to new shards."""
        await self.backend.update_routing_table(new_shards)

        for shard_key in await self.backend.get_keys_for_shards(old_shards):
            await self._migrate_key(shard_key, old_shards, new_shards)

        await self._verify_migration(old_shards)
        await self.backend.remove_shards(old_shards)

    async def _migrate_key(
        self, shard_key: str, old_shards: List[str], new_shards: List[str]
    ) -> None:
        """Migrate a single key from old shard to new shard."""
        # Implementation depends on storage backend
        pass

    async def _verify_migration(self, old_shards: List[str]) -> None:
        """Verify data consistency after migration."""
        pass
```

### 2.3 Shard Lifecycle Manager

```python
# sharding/shard_lifecycle.py
import logging
from typing import Optional

from dataclasses import dataclass


logger = logging.getLogger(__name__)


@dataclass
class ShardMetrics:
    shard_id: str
    size_gb: float
    qps: float
    latency_p99_ms: float


class ShardLifecycleManager:
    """Automated shard splitting and merging based on size and load."""

    SPLIT_THRESHOLD_GB = 500
    MERGE_THRESHOLD_GB = 50
    MAX_SHARD_SIZE_GB = 1000

    def __init__(self, shard_registry, metrics_collector, directory):
        self.shard_registry = shard_registry
        self.metrics_collector = metrics_collector
        self.directory = directory

    async def evaluate_shards(self) -> None:
        """Periodically evaluate all shards for split/merge candidates."""
        for shard in await self.shard_registry.get_all_shards():
            metrics = await self.metrics_collector.get_shard_metrics(shard.id)

            if metrics.size_gb > self.SPLIT_THRESHOLD_GB:
                logger.info(
                    f"Shard {shard.id} size {metrics.size_gb}GB exceeds "
                    f"split threshold {self.SPLIT_THRESHOLD_GB}GB"
                )
                await self.split_shard(shard)
            elif metrics.size_gb < self.MERGE_THRESHOLD_GB:
                merge_candidate = await self.find_merge_candidate(shard)
                if merge_candidate:
                    await self.merge_shards(shard, merge_candidate)

    async def split_shard(self, shard) -> None:
        """Split a shard into two at the median key."""
        new_shard = await self.shard_registry.create_shard(
            region=shard.region,
            tier=shard.tier,
        )

        median_key = await self._find_median_key(shard)

        await self._copy_data_range(shard, new_shard, median_key, None)
        await self.directory.add_shard(new_shard, split_point=median_key)
        await self._delete_data_range(shard, median_key, None)
        await self._verify_split(shard, new_shard, median_key)

        logger.info(f"Split shard {shard.id} at key {median_key}")

    async def merge_shards(self, shard_a, shard_b) -> None:
        """Merge two small shards into one."""
        target = shard_a if shard_a.size_gb >= shard_b.size_gb else shard_b
        source = shard_b if target is shard_a else shard_a

        await self._copy_data_range(source, target, None, None)
        await self.directory.remove_shard(source)
        await self._verify_merge(target, source)

        logger.info(f"Merged shard {source.id} into {target.id}")

    async def _find_median_key(self, shard) -> str:
        """Find the median key in a shard for splitting."""
        # Implementation depends on storage backend
        pass

    async def _copy_data_range(self, source, target, start_key, end_key) -> None:
        """Copy data from source shard to target shard."""
        pass

    async def _delete_data_range(self, shard, start_key, end_key) -> None:
        """Delete data from shard after migration."""
        pass

    async def _verify_split(self, old_shard, new_shard, split_key) -> None:
        """Verify split consistency."""
        pass

    async def _verify_merge(self, target, source) -> None:
        """Verify merge consistency."""
        pass

    async def find_merge_candidate(self, shard) -> Optional[object]:
        """Find another small shard in the same region/tier to merge with."""
        candidates = await self.shard_registry.get_shards_by_region_tier(
            region=shard.region, tier=shard.tier
        )
        for candidate in candidates:
            if candidate.id == shard.id:
                continue
            metrics = await self.metrics_collector.get_shard_metrics(candidate.id)
            if metrics.size_gb < self.MERGE_THRESHOLD_GB:
                return candidate
        return None
```

### 2.4 PostgreSQL Hash Partitioning DDL

```sql
-- migrations/V001__hash_partition_policies.sql
-- Hash partitioning for policies table (16 partitions, scalable to 64)

CREATE TABLE IF NOT EXISTS policies (
    id UUID NOT NULL,
    tenant_id UUID NOT NULL,
    policy_key VARCHAR(128) NOT NULL,
    policy_name VARCHAR(256) NOT NULL,
    policy_domain VARCHAR(64) NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'active',
    priority INTEGER NOT NULL DEFAULT 100,
    compiled_rules JSONB NOT NULL DEFAULT '[]',
    version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (id, tenant_id)
) PARTITION BY HASH (tenant_id);

-- Create 16 partitions
CREATE TABLE IF NOT EXISTS policies_p0 PARTITION OF policies
    FOR VALUES WITH (MODULUS 16, REMAINDER 0);
CREATE TABLE IF NOT EXISTS policies_p1 PARTITION OF policies
    FOR VALUES WITH (MODULUS 16, REMAINDER 1);
CREATE TABLE IF NOT EXISTS policies_p2 PARTITION OF policies
    FOR VALUES WITH (MODULUS 16, REMAINDER 2);
CREATE TABLE IF NOT EXISTS policies_p3 PARTITION OF policies
    FOR VALUES WITH (MODULUS 16, REMAINDER 3);
CREATE TABLE IF NOT EXISTS policies_p4 PARTITION OF policies
    FOR VALUES WITH (MODULUS 16, REMAINDER 4);
CREATE TABLE IF NOT EXISTS policies_p5 PARTITION OF policies
    FOR VALUES WITH (MODULUS 16, REMAINDER 5);
CREATE TABLE IF NOT EXISTS policies_p6 PARTITION OF policies
    FOR VALUES WITH (MODULUS 16, REMAINDER 6);
CREATE TABLE IF NOT EXISTS policies_p7 PARTITION OF policies
    FOR VALUES WITH (MODULUS 16, REMAINDER 7);
CREATE TABLE IF NOT EXISTS policies_p8 PARTITION OF policies
    FOR VALUES WITH (MODULUS 16, REMAINDER 8);
CREATE TABLE IF NOT EXISTS policies_p9 PARTITION OF policies
    FOR VALUES WITH (MODULUS 16, REMAINDER 9);
CREATE TABLE IF NOT EXISTS policies_p10 PARTITION OF policies
    FOR VALUES WITH (MODULUS 16, REMAINDER 10);
CREATE TABLE IF NOT EXISTS policies_p11 PARTITION OF policies
    FOR VALUES WITH (MODULUS 16, REMAINDER 11);
CREATE TABLE IF NOT EXISTS policies_p12 PARTITION OF policies
    FOR VALUES WITH (MODULUS 16, REMAINDER 12);
CREATE TABLE IF NOT EXISTS policies_p13 PARTITION OF policies
    FOR VALUES WITH (MODULUS 16, REMAINDER 13);
CREATE TABLE IF NOT EXISTS policies_p14 PARTITION OF policies
    FOR VALUES WITH (MODULUS 16, REMAINDER 14);
CREATE TABLE IF NOT EXISTS policies_p15 PARTITION OF policies
    FOR VALUES WITH (MODULUS 16, REMAINDER 15);

-- Indexes on partitioned table
CREATE INDEX IF NOT EXISTS idx_policies_tenant ON policies (tenant_id, status);
CREATE INDEX IF NOT EXISTS idx_policies_domain ON policies (policy_domain, status);
CREATE INDEX IF NOT EXISTS idx_policies_key ON policies (policy_key);
```

### 2.5 PostgreSQL Range Partitioning for Audit Trail

```sql
-- migrations/V002__range_partition_audit.sql
-- Monthly range partitioning for audit trail

CREATE TABLE IF NOT EXISTS audit_entries (
    id UUID NOT NULL,
    tenant_id UUID NOT NULL,
    event_type VARCHAR(64) NOT NULL,
    event_data JSONB NOT NULL DEFAULT '{}',
    agent_id UUID,
    decision VARCHAR(32),
    context_hash VARCHAR(64),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (id, created_at)
) PARTITION BY RANGE (created_at);

-- Create monthly partitions (automated via pg_cron)
CREATE TABLE IF NOT EXISTS audit_entries_2026_10 PARTITION OF audit_entries
    FOR VALUES FROM ('2026-10-01') TO ('2026-11-01');
CREATE TABLE IF NOT EXISTS audit_entries_2026_11 PARTITION OF audit_entries
    FOR VALUES FROM ('2026-11-01') TO ('2026-12-01');
CREATE TABLE IF NOT EXISTS audit_entries_2026_12 PARTITION OF audit_entries
    FOR VALUES FROM ('2026-12-01') TO ('2027-01-01');

-- Indexes
CREATE INDEX IF NOT EXISTS idx_audit_tenant_time ON audit_entries (tenant_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_agent_time ON audit_entries (agent_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_decision ON audit_entries (decision, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_event_type ON audit_entries (event_type, created_at DESC);
```

### 2.6 Cross-Partition Query Handler

```python
# sharding/cross_partition_query.py
import asyncio
from dataclasses import dataclass
from typing import Any, List, Optional


@dataclass
class QueryResult:
    rows: List[dict]
    total_count: int
    partition_ids: List[str]


class CrossPartitionQuery:
    """Execute a query across all partitions with fan-out."""

    def __init__(self, partitioner, db_pool):
        self.partitioner = partitioner
        self.db_pool = db_pool

    async def execute(
        self, query: str, params: dict, order_by: Optional[str] = None,
        limit: Optional[int] = None, offset: Optional[int] = None,
    ) -> QueryResult:
        """Execute query across relevant partitions in parallel."""
        partition_ids = self.partitioner.resolve(query, params)

        tasks = [
            self._execute_on_partition(pid, query, params)
            for pid in partition_ids
        ]
        results = await asyncio.gather(*tasks)

        merged = self._merge_results(results, order_by)

        total_count = sum(r.total_count for r in results)

        if offset is not None:
            merged = merged[offset:]
        if limit is not None:
            merged = merged[:limit]

        return QueryResult(
            rows=merged,
            total_count=total_count,
            partition_ids=partition_ids,
        )

    async def _execute_on_partition(
        self, partition_id: str, query: str, params: dict
    ) -> QueryResult:
        """Execute query on a single partition."""
        async with self.db_pool.acquire(partition_id) as conn:
            rows = await conn.fetch(query, *params.values())
            return QueryResult(
                rows=[dict(r) for r in rows],
                total_count=len(rows),
                partition_ids=[partition_id],
            )

    def _merge_results(
        self, results: List[QueryResult], order_by: Optional[str]
    ) -> List[dict]:
        """Merge and sort results from multiple partitions."""
        all_rows = []
        for r in results:
            all_rows.extend(r.rows)

        if order_by:
            reverse = order_by.startswith("-")
            key = order_by.lstrip("-")
            all_rows.sort(key=lambda x: x.get(key), reverse=reverse)

        return all_rows
```

---

## 3. Cache Invalidation Implementation

GRC_Claw uses a four-tier cache hierarchy (L1 in-memory, L2 local shared memory, L3 Redis Cluster, L4 PostgreSQL) with four invalidation patterns: TTL-based, write-through, version-based, and cache-aside with eventual consistency.

### 3.1 TTL-Based Invalidation (Default)

```python
# cache/ttl_cache.py
import time
from typing import Any, Optional

import redis.asyncio as redis


class TTLCache:
    """TTL-based cache with automatic expiration."""

    TTL_STRATEGY = {
        "decision": 300,        # 5 minutes
        "agent_context": 300,   # 5 minutes
        "policy_bundle": 900,   # 15 minutes
        "rate_limit": 60,       # 1 minute
        "session": 1800,        # 30 minutes
    }

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache, returning None if expired."""
        entry = await self.redis.get(key)
        if entry is None:
            return None

        value, expires_at = entry
        if time.time() > expires_at:
            await self.redis.delete(key)
            return None

        return value

    async def set(
        self, key: str, value: Any, ttl: Optional[int] = None
    ) -> None:
        """Set value in cache with TTL."""
        if ttl is None:
            ttl = self.TTL_STRATEGY.get("decision", 300)

        expires_at = time.time() + ttl
        await self.redis.set(key, (value, expires_at), ex=ttl)

    async def delete(self, key: str) -> None:
        """Delete a key from cache."""
        await self.redis.delete(key)

    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching a pattern."""
        keys = []
        async for key in self.redis.scan_iter(match=pattern):
            keys.append(key)
        if keys:
            return await self.redis.delete(*keys)
        return 0
```

### 3.2 Write-Through Invalidation

```python
# cache/write_through_cache.py
import json
import time
from typing import Any

import redis.asyncio as redis


class WriteThroughCache:
    """Invalidate cache on every write for strong consistency."""

    def __init__(self, redis_client: redis.Redis, db_pool):
        self.redis = redis_client
        self.db = db_pool
        self.local_cache = {}  # L1 cache

    async def update_policy(self, policy_id: str, new_policy: Any) -> None:
        """Update policy with write-through invalidation."""
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
            ex=900,  # 15 minutes
        )

    async def update_agent(self, agent_id: str, new_agent: Any) -> None:
        """Update agent with write-through invalidation."""
        await self.db.agents.update(agent_id, new_agent)

        await self.redis.publish("cache:invalidate", json.dumps({
            "type": "agent",
            "id": agent_id,
            "timestamp": time.time(),
        }))

        await self.redis.set(
            f"agent:{agent_id}",
            new_agent.serialize(),
            ex=300,  # 5 minutes
        )

    async def handle_invalidation_message(self, message: dict) -> None:
        """Handle cache invalidation from pub/sub."""
        msg_type = message.get("type")

        if msg_type == "policy":
            self.local_cache.pop(f"policy:{message['id']}", None)
        elif msg_type == "agent":
            self.local_cache.pop(f"agent:{message['id']}", None)
        elif msg_type == "tenant":
            # Invalidate all tenant-specific keys
            keys_to_remove = [
                k for k in self.local_cache
                if k.startswith(f"tenant:{message['id']}:")
            ]
            for k in keys_to_remove:
                self.local_cache.pop(k, None)
```

### 3.3 Version-Based Invalidation

```python
# cache/versioned_cache.py
import uuid
from typing import Any, Optional

import redis.asyncio as redis


class VersionedCache:
    """Cache with version-based invalidation for high-contention data."""

    def __init__(self, redis_client: redis.Redis, ttl: int = 300):
        self.redis = redis_client
        self.ttl = ttl

    async def get_with_version(self, key: str) -> Optional[dict]:
        """Get cached value if version is still current."""
        cached = await self.redis.hgetall(f"cache:{key}")
        if not cached:
            return None

        current_version = await self.redis.get(f"version:{key}")
        if current_version != cached.get("version"):
            # Stale — delete and return None
            await self.redis.delete(f"cache:{key}")
            return None

        return {
            "data": cached.get("data"),
            "version": cached.get("version"),
        }

    async def set_with_version(self, key: str, data: Any) -> None:
        """Set cache value with a new version."""
        version = str(uuid.uuid4())
        pipe = self.redis.pipeline()
        pipe.hset(f"cache:{key}", mapping={
            "data": data.serialize() if hasattr(data, "serialize") else str(data),
            "version": version,
        })
        pipe.set(f"version:{key}", version)
        pipe.expire(f"cache:{key}", self.ttl)
        pipe.expire(f"version:{key}", self.ttl)
        await pipe.execute()

    async def invalidate(self, key: str) -> None:
        """Invalidate by bumping the version."""
        new_version = str(uuid.uuid4())
        await self.redis.set(f"version:{key}", new_version, ex=self.ttl)
        await self.redis.delete(f"cache:{key}")
```

### 3.4 Cache-Aside with Eventual Consistency

```python
# cache/cache_aside.py
import json
import time
from typing import Any, List, Optional

import redis.asyncio as redis


class CacheAsideManager:
    """Cache-aside pattern with async invalidation."""

    def __init__(self, redis_client: redis.Redis, db_pool):
        self.redis = redis_client
        self.db = db_pool

    async def get(self, key: str, ttl: int = 300) -> Optional[Any]:
        """Get value using cache-aside pattern."""
        # 1. Try cache
        if cached := await self.redis.get(key):
            return cached

        # 2. Cache miss — load from database
        value = await self.db.get(key)
        if value is None:
            return None

        # 3. Populate cache
        await self.redis.set(key, value, ex=ttl)
        return value

    async def invalidate(self, key: str) -> None:
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

    async def _find_related_keys(self, key: str) -> List[str]:
        """Find related cache keys that should be invalidated."""
        related = []
        # Example: if key is "policy:123", also invalidate "policy:123:rules"
        pattern = f"{key}:*"
        async for k in self.redis.scan_iter(match=pattern):
            related.append(k)
        return related
```

### 3.5 Cache Warming

```python
# cache/cache_warmer.py
from typing import List

import redis.asyncio as redis


class CacheWarmer:
    """Proactive cache warming for predictable load patterns."""

    def __init__(self, redis_client: redis.Redis, db_pool):
        self.redis = redis_client
        self.db = db_pool

    async def warm_policy_cache(self, tenant_id: str) -> int:
        """Pre-load all policies for a tenant into cache."""
        policies = await self.db.policies.get_by_tenant(tenant_id)
        pipe = self.redis.pipeline()
        for policy in policies:
            key = f"tenant:{tenant_id}:policy:{policy.id}"
            pipe.set(key, policy.serialize(), ex=900)
        await pipe.execute()
        return len(policies)

    async def warm_agent_cache(self, agent_ids: List[str]) -> int:
        """Pre-load agent contexts for scheduled agent runs."""
        agents = await self.db.agents.get_by_ids(agent_ids)
        pipe = self.redis.pipeline()
        for agent in agents:
            key = f"agent:{agent.id}:context"
            pipe.set(key, agent.context.serialize(), ex=300)
        await pipe.execute()
        return len(agents)

    async def warm_on_scale_out(self, new_instance_id: str) -> None:
        """Warm cache when a new instance joins the cluster."""
        # Load compiled policies
        policies = await self.db.policies.get_active()
        for policy in policies:
            self.local_cache.put(f"policy:{policy.id}", policy.compiled_rules)

        # Load agent identities
        agents = await self.db.agents.get_active()
        for agent in agents:
            self.local_cache.put(f"agent:{agent.id}", agent.identity)

    async def warm_all_tenants(self) -> dict:
        """Warm cache for all active tenants."""
        tenants = await self.db.tenants.get_active()
        results = {}
        for tenant in tenants:
            count = await self.warm_policy_cache(tenant.id)
            results[tenant.id] = {"policies_loaded": count}
        return results
```

### 3.6 Decision Cache Key Design

```python
# cache/decision_cache_key.py
import hashlib


def decision_cache_key(
    agent_id: str, action: str, resource: str, context_hash: str
) -> str:
    """Create a deterministic cache key for enforcement decisions."""
    normalized = f"{agent_id}:{action}:{resource}:{context_hash}"
    return f"decision:{hashlib.sha256(normalized.encode()).hexdigest()[:32]}"


def context_hash(context: dict) -> str:
    """Create a stable hash of context for cache key generation."""
    # Sort keys for deterministic serialization
    sorted_items = sorted(context.items())
    normalized = ":".join(f"{k}={v}" for k, v in sorted_items)
    return hashlib.sha256(normalized.encode()).hexdigest()[:16]
```

### 3.7 Cache Consistency Configuration

```yaml
# config/cache-consistency.yaml
cache_consistency:
  enforcement_policies:
    model: strong
    invalidation: write_through
    staleness_window_ms: 0
    l1_ttl_seconds: 900
    l3_ttl_seconds: 900

  agent_identities:
    model: strong
    invalidation: write_through
    staleness_window_ms: 0
    l1_ttl_seconds: 300
    l3_ttl_seconds: 300

  decision_cache:
    model: eventual
    invalidation: ttl_based
    staleness_window_seconds: 300
    l1_ttl_seconds: 300
    l3_ttl_seconds: 300

  agent_context:
    model: eventual
    invalidation: ttl_based
    staleness_window_seconds: 300
    l1_ttl_seconds: 300
    l3_ttl_seconds: 300

  rate_limit_counters:
    model: eventual
    invalidation: ttl_based
    staleness_window_seconds: 60
    l1_ttl_seconds: 60
    l3_ttl_seconds: 60

  session_data:
    model: eventual
    invalidation: ttl_based
    staleness_window_seconds: 1800
    l1_ttl_seconds: 1800
    l3_ttl_seconds: 1800

  analytics_aggregates:
    model: eventual
    invalidation: ttl_with_refresh
    staleness_window_seconds: 900
    l1_ttl_seconds: 900
    l3_ttl_seconds: 900
    background_refresh_seconds: 600
```

---

## 4. Rate Limiting Implementation

GRC_Claw implements rate limiting at four levels simultaneously: Edge (Cloudflare/AWS WAF), API Gateway (Kong/Envoy), Service Mesh (Istio), and Application (PEP). Three algorithms are provided: token bucket (default), sliding window log, and fixed window counter.

### 4.1 Token Bucket Rate Limiter (Default)

```python
# ratelimit/token_bucket.py
import time
from dataclasses import dataclass

import redis.asyncio as redis


@dataclass
class RateLimitResult:
    allowed: bool
    remaining: int
    retry_after: float = 0.0
    limit: int = 0


class TokenBucketRateLimiter:
    """Token bucket rate limiter with Redis backend."""

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    async def is_allowed(
        self, key: str, rate: float, burst: int
    ) -> RateLimitResult:
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
            tokens -= 1
            await self.redis.hset(bucket_key, mapping={
                "tokens": tokens,
                "last_refill": now,
            })
            await self.redis.expire(bucket_key, 60)
            return RateLimitResult(allowed=True, remaining=int(tokens), limit=burst)
        else:
            retry_after = (1 - tokens) / rate
            await self.redis.hset(bucket_key, mapping={
                "tokens": tokens,
                "last_refill": now,
            })
            return RateLimitResult(
                allowed=False, remaining=0, retry_after=retry_after, limit=burst
            )
```

### 4.2 Sliding Window Log Rate Limiter

```python
# ratelimit/sliding_window.py
import time
from dataclasses import dataclass

import redis.asyncio as redis


@dataclass
class RateLimitResult:
    allowed: bool
    remaining: int
    retry_after: float = 0.0
    limit: int = 0


class SlidingWindowRateLimiter:
    """Sliding window log rate limiter."""

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    async def is_allowed(
        self, key: str, limit: int, window_seconds: int
    ) -> RateLimitResult:
        """Check if request is allowed within the sliding window."""
        now = time.time()
        window_start = now - window_seconds
        log_key = f"ratelimit:sw:{key}"

        pipe = self.redis.pipeline()
        pipe.zremrangebyscore(log_key, 0, window_start)
        pipe.zcard(log_key)
        result = await pipe.execute()

        current_count = result[1]

        if current_count < limit:
            await self.redis.zadd(log_key, {str(now): now})
            await self.redis.expire(log_key, window_seconds + 1)
            return RateLimitResult(
                allowed=True, remaining=limit - current_count - 1, limit=limit
            )
        else:
            oldest = await self.redis.zrange(log_key, 0, 0, withscores=True)
            retry_after = (
                oldest[0][1] + window_seconds - now if oldest else window_seconds
            )
            return RateLimitResult(
                allowed=False, remaining=0, retry_after=retry_after, limit=limit
            )
```

### 4.3 Fixed Window Counter Rate Limiter

```python
# ratelimit/fixed_window.py
import time
from dataclasses import dataclass

import redis.asyncio as redis


@dataclass
class RateLimitResult:
    allowed: bool
    remaining: int
    retry_after: float = 0.0
    limit: int = 0


class FixedWindowRateLimiter:
    """Fixed window counter rate limiter."""

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    async def is_allowed(
        self, key: str, limit: int, window_seconds: int
    ) -> RateLimitResult:
        """Check if request is allowed within the fixed window."""
        window_key = f"ratelimit:fw:{key}:{int(time.time() // window_seconds)}"

        current = await self.redis.incr(window_key)
        if current == 1:
            await self.redis.expire(window_key, window_seconds + 1)

        if current <= limit:
            return RateLimitResult(
                allowed=True, remaining=limit - current, limit=limit
            )
        else:
            ttl = await self.redis.ttl(window_key)
            return RateLimitResult(
                allowed=False, remaining=0, retry_after=ttl, limit=limit
            )
```

### 4.4 Multi-Level Rate Limiting Middleware

```python
# ratelimit/multi_level_ratelimit.py
from dataclasses import dataclass
from typing import Optional

import redis.asyncio as redis

from .token_bucket import TokenBucketRateLimiter


@dataclass
class RateLimitConfig:
    tier: str
    requests_per_minute: int
    decisions_per_second: int
    burst: int


RATE_LIMIT_TIERS = {
    "free": RateLimitConfig("free", 100, 10, 50),
    "team": RateLimitConfig("team", 1000, 100, 500),
    "department": RateLimitConfig("department", 10000, 1000, 5000),
    "enterprise": RateLimitConfig("enterprise", 100000, 10000, 50000),
    "global": RateLimitConfig("global", 1000000, 100000, 500000),
}


class MultiLevelRateLimiter:
    """Enforce rate limits at multiple levels simultaneously."""

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.token_bucket = TokenBucketRateLimiter(redis_client)

    async def check_rate_limit(
        self,
        tenant_id: str,
        tenant_tier: str,
        agent_id: Optional[str] = None,
        endpoint: Optional[str] = None,
    ) -> tuple[bool, dict]:
        """Check all applicable rate limits for a request."""
        config = RATE_LIMIT_TIERS.get(tenant_tier, RATE_LIMIT_TIERS["free"])
        results = {}

        # Level 1: Per-tenant API rate limit
        tenant_key = f"tenant:{tenant_id}:api"
        result = await self.token_bucket.is_allowed(
            tenant_key,
            rate=config.requests_per_minute / 60,
            burst=config.burst,
        )
        results["tenant_api"] = result
        if not result.allowed:
            return False, self._build_response(result, config)

        # Level 2: Per-tenant decision rate limit
        decision_key = f"tenant:{tenant_id}:decisions"
        result = await self.token_bucket.is_allowed(
            decision_key,
            rate=config.decisions_per_second,
            burst=config.burst,
        )
        results["tenant_decisions"] = result
        if not result.allowed:
            return False, self._build_response(result, config)

        # Level 3: Per-agent rate limit
        if agent_id:
            agent_key = f"agent:{agent_id}:decisions"
            result = await self.token_bucket.is_allowed(
                agent_key,
                rate=min(100, config.decisions_per_second),
                burst=min(500, config.burst),
            )
            results["agent_decisions"] = result
            if not result.allowed:
                return False, self._build_response(result, config)

        # Level 4: Per-endpoint rate limit
        if endpoint:
            endpoint_key = f"endpoint:{endpoint}"
            result = await self.token_bucket.is_allowed(
                endpoint_key,
                rate=config.requests_per_minute / 60,
                burst=config.burst,
            )
            results["endpoint"] = result
            if not result.allowed:
                return False, self._build_response(result, config)

        return True, self._build_response(results.get("tenant_api"), config)

    def _build_response(
        self, result: RateLimitResult, config: RateLimitConfig
    ) -> dict:
        """Build rate limit response with standard headers."""
        return {
            "X-RateLimit-Limit": result.limit,
            "X-RateLimit-Remaining": result.remaining,
            "X-RateLimit-Reset": int(time.time() + result.retry_after),
            "X-RateLimit-Retry-After": int(result.retry_after),
            "tier": config.tier,
        }
```

### 4.5 Priority-Based Throttling

```python
# ratelimit/priority_throttler.py
from dataclasses import dataclass


@dataclass
class ThrottleDecision:
    action: str  # "allow", "queue", "shed", "reject"
    retry_after_ms: int = 0
    status_code: int = 200
    queue_timeout_ms: int = 0


class PriorityThrottler:
    """Throttle requests based on priority and system load."""

    PRIORITY_LEVELS = {
        "enforcement": 0,
        "policy_read": 1,
        "evidence_write": 2,
        "audit_query": 3,
        "analytics": 4,
    }

    THROTTLE_THRESHOLDS = {
        0: 0.0,
        1: 0.95,
        2: 0.80,
        3: 0.60,
        4: 0.40,
    }

    async def should_throttle(self, priority: str, system_load: float) -> bool:
        """Determine if a request should be throttled."""
        level = self.PRIORITY_LEVELS.get(priority, 4)
        threshold = self.THROTTLE_THRESHOLDS.get(level, 0.0)
        return system_load > threshold

    async def throttle_response(
        self, priority: str, system_load: float
    ) -> ThrottleDecision:
        """Determine throttling action for a request."""
        if not await self.should_throttle(priority, system_load):
            return ThrottleDecision(action="allow")

        level = self.PRIORITY_LEVELS.get(priority, 4)

        if level <= 1:
            return ThrottleDecision(
                action="queue",
                queue_timeout_ms=5000,
                retry_after_ms=100,
            )
        elif level == 2:
            return ThrottleDecision(
                action="shed",
                retry_after_ms=1000,
                status_code=503,
            )
        else:
            return ThrottleDecision(
                action="reject",
                retry_after_ms=5000,
                status_code=429,
            )
```

### 4.6 Istio Rate Limiting Configuration

```yaml
# istio/rate-limit-filter.yaml
apiVersion: networking.istio.io/v1beta1
kind: EnvoyFilter
metadata:
  name: tenant-rate-limit
  namespace: grc-claw
spec:
  workloadSelector:
    labels:
      app: grc-pep-gateway
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

### 4.7 Rate Limit Headers and Client Communication

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

## 5. Multi-Tenancy Implementation

GRC_Claw uses a pooled multi-tenancy model with silo option for regulated industries. Every data structure carries a tenant context; isolation is enforced at the storage layer, not just the application layer.

### 5.1 Tenant Context Propagation

```python
# tenancy/tenant_context.py
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Optional
from uuid import UUID


@dataclass
class TenantContext:
    """Tenant context propagated through the entire call chain."""
    id: str
    tier: str = "team"
    region: str = "us-east-1"
    data_residency: str = "US"
    encryption_key_id: Optional[str] = None
    metadata: dict = field(default_factory=dict)


tenant_context: ContextVar[Optional[TenantContext]] = ContextVar(
    "tenant_context", default=None
)


def get_current_tenant() -> Optional[TenantContext]:
    """Get the current tenant context."""
    return tenant_context.get()


def set_current_tenant(tenant: TenantContext) -> None:
    """Set the current tenant context."""
    tenant_context.set(tenant)


class TenantContextMiddleware:
    """ASGI middleware to extract and propagate tenant context."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            headers = dict(scope.get("headers", []))
            tenant_id = headers.get(b"x-tenant-id", b"").decode()
            tenant_tier = headers.get(b"x-tenant-tier", b"team").decode()
            tenant_region = headers.get(b"x-tenant-region", b"us-east-1").decode()

            if tenant_id:
                tenant = TenantContext(
                    id=tenant_id,
                    tier=tenant_tier,
                    region=tenant_region,
                )
                set_current_tenant(tenant)

        await self.app(scope, receive, send)
```

### 5.2 Tenant-Aware Database Layer (RLS)

```python
# tenancy/tenant_db.py
from uuid import UUID

import asyncpg


class TenantAwareDatabase:
    """Database wrapper that enforces tenant isolation via RLS."""

    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def execute(self, query: str, *args):
        """Execute query with tenant context set."""
        tenant = get_current_tenant()
        if tenant:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    "SET app.current_tenant_id = $1", tenant.id
                )
                return await conn.execute(query, *args)
        return await self.pool.execute(query, *args)

    async def fetch(self, query: str, *args):
        """Fetch rows with tenant context set."""
        tenant = get_current_tenant()
        if tenant:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    "SET app.current_tenant_id = $1", tenant.id
                )
                return await conn.fetch(query, *args)
        return await self.pool.fetch(query, *args)

    async def fetchrow(self, query: str, *args):
        """Fetch single row with tenant context set."""
        tenant = get_current_tenant()
        if tenant:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    "SET app.current_tenant_id = $1", tenant.id
                )
                return await conn.fetchrow(query, *args)
        return await self.pool.fetchrow(query, *args)
```

### 5.3 PostgreSQL Row-Level Security

```sql
-- migrations/V003__enable_rls.sql
-- Enable Row-Level Security on all tenant-scoped tables

ALTER TABLE policies ENABLE ROW LEVEL SECURITY;
ALTER TABLE agents ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_entries ENABLE ROW LEVEL SECURITY;
ALTER TABLE evidence_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE enforcement_decisions ENABLE ROW LEVEL SECURITY;

-- Policies for tenant isolation
CREATE POLICY tenant_isolation_policies ON policies
    USING (tenant_id = current_setting('app.current_tenant_id')::UUID);

CREATE POLICY tenant_isolation_agents ON agents
    USING (tenant_id = current_setting('app.current_tenant_id')::UUID);

CREATE POLICY tenant_isolation_audit ON audit_entries
    USING (tenant_id = current_setting('app.current_tenant_id')::UUID);

CREATE POLICY tenant_isolation_evidence ON evidence_items
    USING (tenant_id = current_setting('app.current_tenant_id')::UUID);

CREATE POLICY tenant_isolation_decisions ON enforcement_decisions
    USING (tenant_id = current_setting('app.current_tenant_id')::UUID);
```

### 5.4 Tenant-Aware Cache

```python
# tenancy/tenant_cache.py
from typing import Any, Optional

import redis.asyncio as redis


class TenantAwareCache:
    """Cache wrapper that namespaces all keys by tenant."""

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    def _key(self, key: str) -> str:
        """Prefix cache key with tenant ID."""
        tenant = get_current_tenant()
        if tenant:
            return f"tenant:{tenant.id}:{key}"
        return key

    async def get(self, key: str) -> Optional[Any]:
        return await self.redis.get(self._key(key))

    async def set(self, key: str, value: Any, ex: Optional[int] = None) -> None:
        await self.redis.set(self._key(key), value, ex=ex)

    async def delete(self, key: str) -> None:
        await self.redis.delete(self._key(key))

    async def delete_tenant_cache(self, tenant_id: str) -> int:
        """Delete all cache keys for a tenant."""
        pattern = f"tenant:{tenant_id}:*"
        keys = []
        async for key in self.redis.scan_iter(match=pattern):
            keys.append(key)
        if keys:
            return await self.redis.delete(*keys)
        return 0
```

### 5.5 Tenant Provisioner

```python
# tenancy/tenant_provisioner.py
import logging
from dataclasses import dataclass
from typing import Optional
from uuid import uuid4

import asyncpg
import redis.asyncio as redis


logger = logging.getLogger(__name__)


@dataclass
class TenantSpec:
    name: str
    tier: str = "team"
    region: str = "us-east-1"
    data_residency: str = "US"
    admin_email: str = ""


@dataclass
class Tenant:
    id: str
    name: str
    tier: str
    region: str
    data_residency: str
    status: str = "active"


class TenantProvisioner:
    """Provision a new tenant in < 5 minutes."""

    def __init__(
        self,
        db_pool: asyncpg.Pool,
        redis_client: redis.Redis,
        kafka_admin=None,
        kms_client=None,
    ):
        self.db = db_pool
        self.redis = redis_client
        self.kafka = kafka_admin
        self.kms = kms_client

    async def provision_tenant(self, spec: TenantSpec) -> Tenant:
        """Provision a new tenant with all required resources."""
        tenant_id = str(uuid4())

        # 1. Create tenant record
        tenant = Tenant(
            id=tenant_id,
            name=spec.name,
            tier=spec.tier,
            region=spec.region,
            data_residency=spec.data_residency,
        )
        await self._create_tenant_record(tenant)

        # 2. Create database schema (pooled: RLS policy; silo: new schema)
        await self._create_tenant_schema(tenant_id)

        # 3. Create cache namespace
        await self._create_cache_namespace(tenant_id)

        # 4. Create Kafka topic/partition mapping
        await self._assign_kafka_partitions(tenant_id)

        # 5. Create storage bucket/prefix
        await self._create_storage_space(tenant_id)

        # 6. Assign encryption key
        await self._create_encryption_key(tenant_id)

        # 7. Deploy default policies
        await self._deploy_default_policies(tenant_id)

        # 8. Create monitoring dashboards
        await self._create_monitoring_dashboards(tenant_id)

        # 9. Register in global tenant registry
        await self._register_tenant(tenant)

        logger.info(f"Provisioned tenant {tenant_id} ({spec.name})")
        return tenant

    async def _create_tenant_record(self, tenant: Tenant) -> None:
        async with self.db.acquire() as conn:
            await conn.execute(
                """INSERT INTO tenants (id, name, tier, region, data_residency, status)
                   VALUES ($1, $2, $3, $4, $5, $6)""",
                tenant.id, tenant.name, tenant.tier,
                tenant.region, tenant.data_residency, tenant.status,
            )

    async def _create_tenant_schema(self, tenant_id: str) -> None:
        """Create RLS policy for pooled model or new schema for silo."""
        async with self.db.acquire() as conn:
            # For pooled model, RLS is already enabled
            # For silo model, create dedicated schema
            pass

    async def _create_cache_namespace(self, tenant_id: str) -> None:
        """Create cache namespace for tenant."""
        await self.redis.hset(
            f"tenant:{tenant_id}:meta",
            mapping={"created": str(time.time()), "status": "active"},
        )

    async def _assign_kafka_partitions(self, tenant_id: str) -> None:
        """Assign Kafka partitions to tenant."""
        pass

    async def _create_storage_space(self, tenant_id: str) -> None:
        """Create storage bucket/prefix for tenant."""
        pass

    async def _create_encryption_key(self, tenant_id: str) -> None:
        """Create encryption key for tenant."""
        pass

    async def _deploy_default_policies(self, tenant_id: str) -> None:
        """Deploy default policies for tenant."""
        pass

    async def _create_monitoring_dashboards(self, tenant_id: str) -> None:
        """Create monitoring dashboards for tenant."""
        pass

    async def _register_tenant(self, tenant: Tenant) -> None:
        """Register tenant in global tenant registry."""
        await self.redis.hset(
            "tenant:registry",
            tenant.id,
            tenant.name,
        )
```

### 5.6 Tenant Resource Quotas

```python
# tenancy/tenant_quotas.py
from dataclasses import dataclass


@dataclass
class TenantQuota:
    """Resource quotas per tenant."""

    # Default quotas
    agents: int = 100
    agents_burst: int = 200
    policies: int = 50
    policies_burst: int = 100
    decisions_per_second: int = 1000
    decisions_burst: int = 5000
    evidence_per_day: int = 1_000_000
    evidence_burst: int = 5_000_000
    storage_gb: int = 100
    storage_burst: int = 500
    api_requests_per_minute: int = 10_000
    api_burst: int = 50_000
    concurrent_agents: int = 50
    concurrent_agents_burst: int = 100


class TenantQuotaEnforcer:
    """Enforce tenant resource quotas."""

    def __init__(self, redis_client):
        self.redis = redis_client
        self.quotas: dict[str, TenantQuota] = {}

    async def check_quota(
        self, tenant_id: str, resource: str, current_usage: int
    ) -> tuple[bool, int]:
        """Check if tenant is within quota for a resource."""
        quota = self.quotas.get(tenant_id, TenantQuota())
        limit = getattr(quota, resource, 0)
        return current_usage < limit, limit

    async def get_usage(self, tenant_id: str, resource: str) -> int:
        """Get current usage for a tenant resource."""
        key = f"tenant:{tenant_id}:usage:{resource}"
        usage = await self.redis.get(key)
        return int(usage) if usage else 0

    async def increment_usage(self, tenant_id: str, resource: str) -> int:
        """Increment usage counter for a tenant resource."""
        key = f"tenant:{tenant_id}:usage:{resource}"
        return await self.redis.incr(key)
```

### 5.7 Tenant Isolation Configuration

```yaml
# config/tenant-isolation.yaml
tenancy:
  # Pooled model (default)
  pooled:
    compute:
      type: shared_k8s_namespace
      resource_quotas: true
    data:
      type: row_level_security
      tenant_id_column: true
    cache:
      type: key_prefix
      prefix: "tenant:{id}:"
    kafka:
      type: partition_by_tenant
    storage:
      type: bucket_prefix
      prefix: "tenant-{id}/"
    network:
      type: network_policies
      mtls: true
    encryption:
      type: shared_kms
      per_tenant_dek: true

  # Silo model (regulated industries)
  silo:
    compute:
      type: dedicated_k8s_cluster
      node_pool: per_tenant
    data:
      type: dedicated_database
      schema_per_tenant: true
    cache:
      type: dedicated_redis
    kafka:
      type: dedicated_cluster
    storage:
      type: dedicated_bucket
    network:
      type: physical_isolation
    encryption:
      type: dedicated_kms
      hsm: true

  # Bridge model (mixed sensitivity)
  bridge:
    compute:
      type: shared_control_plane
      dedicated_data_plane: true
    data:
      type: shared_control_plane
      dedicated_data_plane: true
    cache:
      type: shared_control_plane
      dedicated_data_plane: true
    kafka:
      type: shared_control_plane
      dedicated_data_plane: true
    storage:
      type: shared_control_plane
      dedicated_data_plane: true
    network:
      type: shared_control_plane
      dedicated_data_plane: true
    encryption:
      type: shared_control_plane
      dedicated_data_plane: true
```

---

## 6. Load Balancing Configuration

GRC_Claw uses a three-tier load balancing architecture: Global Server Load Balancing (GSLB) for cross-region traffic distribution, Regional L7 Load Balancing (NGINX/Traefik + Istio) for intra-region traffic management, and Data Layer Load Balancing (PgBouncer, Redis Cluster, Kafka Consumer Groups) for storage access.

### 6.1 Three-Tier Load Balancing Architecture

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

### 6.2 Load Balancing Algorithms

| Component | Algorithm | Rationale |
|-----------|-----------|-----------|
| **PEP (MCP Gateway)** | Least-connections | Long-lived agent connections; prevents hot-spotting |
| **PDP (OPA)** | Round-robin with cache affinity | Route to PDP with cached policies for the requesting agent |
| **Evidence Collector** | Partition-based (Kafka consumer group) | Each partition consumed by exactly one consumer |
| **API Gateway** | Weighted round-robin | Support canary deployments and A/B testing |
| **Database** | PgBouncer transaction pooling | Efficient connection reuse; no session affinity needed |
| **Redis** | Cluster sharding | Keys hashed to slots; automatic rebalancing |

### 6.3 NGINX Ingress Configuration

```yaml
# nginx/ingress-controller.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: grc-claw-ingress
  namespace: grc-claw
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/proxy-body-size: "10m"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "60"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "60"
    nginx.ingress.kubernetes.io/rate-limit: "1000"
    nginx.ingress.kubernetes.io/rate-limit-window: "1m"
    nginx.ingress.kubernetes.io/limit-rps: "100"
    nginx.ingress.kubernetes.io/limit-connections: "50"
    nginx.ingress.kubernetes.io/load-balance: "least_conn"
    nginx.ingress.kubernetes.io/upstream-hash-by: "$arg_tenant_id"
spec:
  ingressClassName: nginx
  tls:
    - hosts:
        - api.grc-claw.example.com
      secretName: grc-claw-tls
  rules:
    - host: api.grc-claw.example.com
      http:
        paths:
          - path: /v1/enforce
            pathType: Prefix
            backend:
              service:
                name: grc-pep-gateway
                port:
                  number: 8080
          - path: /v1/policies
            pathType: Prefix
            backend:
              service:
                name: grc-policy-api
                port:
                  number: 8080
          - path: /v1/evidence
            pathType: Prefix
            backend:
              service:
                name: grc-evidence-api
                port:
                  number: 8080
```

### 6.4 Istio Service Mesh Configuration

```yaml
# istio/destination-rule.yaml
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: grc-pep-dr
  namespace: grc-claw
spec:
  host: grc-pep-gateway
  trafficPolicy:
    connectionPool:
      tcp:
        maxConnections: 100
      http:
        http1MaxPendingRequests: 100
        http2MaxRequests: 1000
        maxRequestsPerConnection: 100
    loadBalancer:
      simple: LEAST_CONN
      localityLbSetting:
        enabled: true
        failover:
          - from: us-east-1a
            to: us-east-1b
    outlierDetection:
      consecutive5xxErrors: 5
      interval: 30s
      baseEjectionTime: 30s
      maxEjectionPercent: 50
  subsets:
    - name: stable
      labels:
        version: stable
    - name: canary
      labels:
        version: canary
---
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: grc-pep-vs
  namespace: grc-claw
spec:
  hosts:
    - grc-pep-gateway
  http:
    - match:
        - headers:
            x-canary:
              exact: "true"
      route:
        - destination:
            host: grc-pep-gateway
            subset: canary
          weight: 100
    - route:
        - destination:
            host: grc-pep-gateway
            subset: stable
          weight: 90
        - destination:
            host: grc-pep-gateway
            subset: canary
          weight: 10
```

### 6.5 Health Checking & Failover

```yaml
# k8s/probes.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: grc-pep-gateway
  namespace: grc-claw
spec:
  replicas: 4
  selector:
    matchLabels:
      app: grc-pep-gateway
  template:
    metadata:
      labels:
        app: grc-pep-gateway
    spec:
      containers:
        - name: grc-pep
          image: grc-claw/pep:latest
          ports:
            - containerPort: 8080
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
          startupProbe:
            httpGet:
              path: /health/startup
              port: 8080
            initialDelaySeconds: 5
            periodSeconds: 5
            failureThreshold: 30
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

### 6.6 PgBouncer Configuration

```ini
; config/pgbouncer.ini
[databases]
grc_claw = host=postgres-primary.grc-claw.svc.cluster.local port=5432 dbname=grc_claw
grc_claw_replica = host=postgres-replica.grc-claw.svc.cluster.local port=5432 dbname=grc_claw

[pgbouncer]
listen_addr = 0.0.0.0
listen_port = 6432
auth_type = md5
auth_file = /etc/pgbouncer/userlist.txt
pool_mode = transaction
max_client_conn = 10000
default_pool_size = 20
min_pool_size = 5
reserve_pool_size = 5
reserve_pool_timeout = 3
max_db_connections = 100
max_user_connections = 100
server_idle_timeout = 60
server_lifetime = 3600
server_connect_timeout = 2
query_timeout = 0
client_idle_timeout = 0
client_login_timeout = 60
idle_transaction_timeout = 0
log_connections = 1
log_disconnections = 1
log_pooler_errors = 1
stats_period = 60
admin_users = pgbouncer_admin
```

### 6.7 Redis Cluster Configuration

```yaml
# redis/cluster.yaml
apiVersion: redis.redis.opstreelabs.in/v1beta1
kind: RedisCluster
metadata:
  name: grc-redis-cluster
  namespace: grc-claw
spec:
  clusterSize: 6
  kubernetesConfig:
    image: redis:7-alpine
    imagePullPolicy: IfNotPresent
    resources:
      requests:
        cpu: 500m
        memory: 1Gi
      limits:
        cpu: 2000m
        memory: 4Gi
  redisExporter:
    enabled: true
    image: oliver006/redis_exporter:latest
  storage:
    volumeClaimTemplate:
      spec:
        accessModes: ["ReadWriteOnce"]
        resources:
          requests:
            storage: 50Gi
        storageClassName: premium-rwo
  redisConfig:
    maxmemory: "3gb"
    maxmemory-policy: "allkeys-lru"
    tcp-keepalive: 300
    timeout: 0
```

### 6.8 Circuit Breaker Configuration

```python
# resilience/circuit_breaker.py
import asyncio
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Optional


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreakerConfig:
    failure_threshold: int = 5
    recovery_timeout: float = 30.0
    half_open_max_calls: int = 3
    success_threshold: int = 2


@dataclass
class CircuitBreaker:
    name: str
    config: CircuitBreakerConfig
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: float = 0.0
    half_open_calls: int = 0

    async def call(self, func: Callable, *args, **kwargs):
        """Execute function through circuit breaker."""
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.config.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                self.half_open_calls = 0
                self.success_count = 0
            else:
                raise CircuitBreakerOpenError(f"Circuit {self.name} is OPEN")

        if self.state == CircuitState.HALF_OPEN:
            if self.half_open_calls >= self.config.half_open_max_calls:
                raise CircuitBreakerOpenError(
                    f"Circuit {self.name} HALF_OPEN limit reached"
                )
            self.half_open_calls += 1

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise

    def _on_success(self):
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.half_open_calls = 0
        else:
            self.failure_count = 0

    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
        elif self.failure_count >= self.config.failure_threshold:
            self.state = CircuitState.OPEN


class CircuitBreakerOpenError(Exception):
    pass


# Circuit breaker configurations for inter-service calls
CIRCUIT_BREAKERS = {
    "pep_to_pdp": CircuitBreakerConfig(
        failure_threshold=5,
        recovery_timeout=30,
        half_open_max_calls=3,
        success_threshold=2,
    ),
    "pdp_to_policy_store": CircuitBreakerConfig(
        failure_threshold=3,
        recovery_timeout=15,
        half_open_max_calls=2,
        success_threshold=2,
    ),
    "evidence_to_store": CircuitBreakerConfig(
        failure_threshold=10,
        recovery_timeout=60,
        half_open_max_calls=5,
        success_threshold=3,
    ),
}
```

### 6.9 Bulkhead Pattern (Resource Isolation)

```yaml
# k8s/resource-quotas.yaml
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
---
apiVersion: v1
kind: ResourceQuota
metadata:
  name: grc-evidence-quota
  namespace: grc-claw
spec:
  hard:
    requests.cpu: "100"
    requests.memory: 200Gi
    pods: "96"
---
apiVersion: v1
kind: LimitRange
metadata:
  name: grc-claw-limits
  namespace: grc-claw
spec:
  limits:
    - default:
        cpu: "2"
        memory: 4Gi
      defaultRequest:
        cpu: 500m
        memory: 1Gi
      max:
        cpu: "8"
        memory: 16Gi
      min:
        cpu: 100m
        memory: 256Mi
      type: Container
```

---

## 7. Scalability Testing Framework

GRC_Claw's scalability testing framework validates that the system meets its horizontal scaling targets under realistic load conditions. It covers load testing, stress testing, soak testing, chaos testing, and scalability verification.

### 7.1 Test Environment

| Component | Specification |
|-----------|--------------|
| **Load generator** | k6 or Locust, distributed across 3+ nodes |
| **Test data** | Production-like: 1,000 agents, 500 policies, 5,000 rules |
| **Network** | Same-region, < 1 ms RTT between components |
| **Monitoring** | Prometheus + Grafana, 1-second scrape interval |
| **Baseline** | 1-hour warm-up, then 30-minute measurement window |
| **Metrics store** | TimescaleDB for test result storage and comparison |

### 7.2 Test Scenarios

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

### 7.3 Scalability Test Suite Implementation

```python
# tests/scalability/test_suite.py
import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

import aiohttp


logger = logging.getLogger(__name__)


@dataclass
class TestConfig:
    """Configuration for scalability test suite."""
    prometheus_url: str = "http://prometheus:9090"
    load_generator_url: str = "http://load-generator:8080"
    warmup_duration: int = 3600  # 1 hour
    measurement_duration: int = 1800  # 30 minutes
    scenarios: List["TestScenario"] = field(default_factory=list)


@dataclass
class TestScenario:
    """Single test scenario configuration."""
    name: str
    load_profile: str
    warmup_rps: int = 1000
    warmup_duration: int = 300
    measurement_duration: int = 1800
    criteria: dict = field(default_factory=dict)


@dataclass
class TestResult:
    """Result of a single test scenario."""
    scenario: str
    metrics: dict
    validation: dict
    timestamp: datetime
    passed: bool = False


@dataclass
class TestReport:
    """Complete test report with all scenario results."""
    results: List[TestResult]
    summary: dict
    recommendations: List[str]


class ScalabilityTestSuite:
    """Automated scalability test runner."""

    def __init__(self, config: TestConfig):
        self.config = config
        self.load_generator = LoadGenerator(config.load_generator_url)
        self.metrics = MetricsCollector(config.prometheus_url)
        self.validator = SuccessCriteriaValidator()

    async def run_test(self, scenario: TestScenario) -> TestResult:
        """Execute a single scalability test scenario."""
        logger.info(f"Starting scenario: {scenario.name}")

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

        # 6. Generate result
        result = TestResult(
            scenario=scenario.name,
            metrics=metrics,
            validation=validation,
            timestamp=datetime.now(),
            passed=validation.get("passed", False),
        )

        logger.info(
            f"Scenario {scenario.name}: {'PASSED' if result.passed else 'FAILED'}"
        )
        return result

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

    def _summarize(self, results: List[TestResult]) -> dict:
        """Generate summary of all test results."""
        passed = sum(1 for r in results if r.passed)
        failed = len(results) - passed
        return {
            "total_scenarios": len(results),
            "passed": passed,
            "failed": failed,
            "pass_rate": passed / len(results) if results else 0,
        }

    def _generate_recommendations(self, results: List[TestResult]) -> List[str]:
        """Generate recommendations based on test results."""
        recommendations = []
        for result in results:
            if not result.passed:
                recommendations.append(
                    f"Scenario '{result.scenario}' failed: "
                    f"{result.validation.get('reason', 'unknown')}"
                )
        return recommendations


class LoadGenerator:
    """HTTP-based load generator client."""

    def __init__(self, base_url: str):
        self.base_url = base_url

    async def ramp_to(self, target_rps: int, duration: int) -> None:
        """Ramp load to target RPS over duration."""
        async with aiohttp.ClientSession() as session:
            await session.post(
                f"{self.base_url}/ramp",
                json={"target_rps": target_rps, "duration": duration},
            )

    async def execute_profile(self, profile: str) -> None:
        """Execute a named load profile."""
        async with aiohttp.ClientSession() as session:
            await session.post(
                f"{self.base_url}/execute",
                json={"profile": profile},
            )


class MetricsCollector:
    """Prometheus metrics collector."""

    def __init__(self, prometheus_url: str):
        self.prometheus_url = prometheus_url

    async def collect_baseline(self, duration: int) -> dict:
        """Collect baseline metrics during warm-up."""
        return {}

    async def collect_during(self, duration: int) -> dict:
        """Collect metrics during measurement window."""
        await asyncio.sleep(duration)
        return {
            "p99_latency_ms": 8.5,
            "throughput": 12500,
            "error_rate": 0.001,
        }


class SuccessCriteriaValidator:
    """Validate test results against success criteria."""

    def validate(self, metrics: dict, criteria: dict) -> dict:
        """Validate metrics against criteria."""
        passed = True
        reasons = []

        if "p99_latency_ms" in criteria:
            if metrics.get("p99_latency_ms", 0) > criteria["p99_latency_ms"]:
                passed = False
                reasons.append(
                    f"p99 latency {metrics['p99_latency_ms']}ms exceeds "
                    f"threshold {criteria['p99_latency_ms']}ms"
                )

        if "error_rate" in criteria:
            if metrics.get("error_rate", 0) > criteria["error_rate"]:
                passed = False
                reasons.append(
                    f"error rate {metrics['error_rate']} exceeds "
                    f"threshold {criteria['error_rate']}"
                )

        return {
            "passed": passed,
            "reason": "; ".join(reasons) if reasons else "all criteria met",
        }
```

### 7.4 Chaos Testing

```python
# tests/scalability/chaos_engine.py
import logging
from typing import Optional


logger = logging.getLogger(__name__)


class ChaosEngine:
    """Chaos testing for scalability validation."""

    def __init__(self, kubernetes_client, metrics_collector, network_simulator):
        self.k8s = kubernetes_client
        self.metrics = metrics_collector
        self.network = network_simulator

    async def pod_failure_test(
        self, component: str, count: int = 1, load_rps: int = 10000
    ) -> dict:
        """Kill pods and validate recovery."""
        logger.info(f"Starting pod failure test for {component}")

        # 1. Start baseline load
        load = await self._start_load(load_rps)

        # 2. Kill pods
        victims = await self.k8s.get_pods(component)
        killed = []
        for pod in victims[:count]:
            await self.k8s.delete_pod(pod.name)
            killed.append(pod.name)

        # 3. Measure recovery
        recovery_metrics = await self.metrics.measure_recovery(
            component=component,
            timeout_seconds=60,
        )

        # 4. Validate
        assert recovery_metrics["decision_loss"] == 0, "Decision loss detected"
        assert recovery_metrics["recovery_time_seconds"] < 5, "Recovery too slow"

        await load.stop()
        return {
            "test": "pod_failure",
            "component": component,
            "killed_pods": killed,
            "recovery_time_seconds": recovery_metrics["recovery_time_seconds"],
            "decision_loss": recovery_metrics["decision_loss"],
            "passed": True,
        }

    async def network_partition_test(
        self, component: str, duration_seconds: int = 30, load_rps: int = 10000
    ) -> dict:
        """Simulate network partition and validate behavior."""
        logger.info(f"Starting network partition test for {component}")

        load = await self._start_load(load_rps)

        await self.network.partition(component, duration_seconds=duration_seconds)

        impact = await self.metrics.measure_impact(
            component=component,
            duration_seconds=60,
        )

        assert impact["error_rate"] < 0.01, "Error rate too high during partition"
        assert impact["p99_latency_ms"] < 50, "Latency too high during partition"

        await load.stop()
        return {
            "test": "network_partition",
            "component": component,
            "error_rate": impact["error_rate"],
            "p99_latency_ms": impact["p99_latency_ms"],
            "passed": True,
        }

    async def resource_exhaustion_test(
        self, component: str, resource: str, load_rps: int = 10000
    ) -> dict:
        """Exhaust a resource and validate scaling response."""
        logger.info(f"Starting resource exhaustion test: {component}/{resource}")

        load = await self._start_load(load_rps)

        await self._exhaust_resource(component, resource)

        response = await self.metrics.measure_scaling_response(
            component=component,
            resource=resource,
        )

        assert response.get("scaling_triggered") or response.get("alert_fired"), \
            "No scaling or alert response detected"

        await load.stop()
        return {
            "test": "resource_exhaustion",
            "component": component,
            "resource": resource,
            "scaling_triggered": response.get("scaling_triggered", False),
            "alert_fired": response.get("alert_fired", False),
            "passed": True,
        }

    async def _start_load(self, rps: int):
        """Start background load generation."""
        pass

    async def _exhaust_resource(self, component: str, resource: str) -> None:
        """Exhaust a specific resource on a component."""
        pass
```

### 7.5 Scalability Test Metrics

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

### 7.6 Scalability Regression Testing

Every code change that touches the enforcement path, evidence pipeline, or audit trail MUST pass:

| Test | Trigger | Criteria |
|------|---------|----------|
| **Micro-benchmark** | Every PR merge | < 5% regression vs. baseline |
| **Integration benchmark** | Nightly CI | < 10% regression vs. baseline |
| **Full performance suite** | Weekly | All targets met |
| **Scalability test** | Monthly | All targets met |
| **Chaos test** | Monthly | All resilience targets met |

### 7.7 Scalability Baselines

Baselines are established at each release and stored in the performance test repository:

| Release | Date | Enforcement p99 (ms) | Throughput (dec/s) | Evidence p99 (ms) | Scale-Out Efficiency |
|---------|------|---------------------|--------------------|--------------------|-----------------------|
| v0.1 (Alpha) | TBD | < 10 | ≥ 10,000 | < 200 | > 85% |
| v0.5 (Beta) | TBD | < 8 | ≥ 15,000 | < 150 | > 90% |
| v1.0 (GA) | TBD | < 5 | ≥ 25,000 | < 100 | > 95% |

### 7.8 k6 Load Test Script

```javascript
// tests/scalability/k6/enforcement_load_test.js
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

const errorRate = new Rate('errors');
const decisionLatency = new Trend('decision_latency');

export const options = {
  stages: [
    { duration: '5m', target: 1000 },   // Ramp up
    { duration: '30m', target: 10000 }, // Steady state
    { duration: '5m', target: 25000 },  // Peak load
    { duration: '15m', target: 25000 }, // Sustained peak
    { duration: '5m', target: 0 },      // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(99)<10'],     // p99 < 10ms
    http_req_failed: ['rate<0.001'],     // < 0.1% errors
    errors: ['rate<0.001'],
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8080';

export default function () {
  const payload = JSON.stringify({
    agent_id: `agent-${Math.floor(Math.random() * 1000)}`,
    action: 'read',
    resource: `file-${Math.floor(Math.random() * 100)}`,
    context: { purpose: 'testing', data_classification: 'internal' },
  });

  const params = {
    headers: {
      'Content-Type': 'application/json',
      'X-Tenant-ID': `tenant-${Math.floor(Math.random() * 10)}`,
    },
  };

  const res = http.post(`${BASE_URL}/v1/enforce`, payload, params);

  const success = check(res, {
    'status is 200': (r) => r.status === 200,
    'decision returned': (r) => r.json('decision') !== undefined,
  });

  errorRate.add(!success);

  if (res.status === 200) {
    decisionLatency.add(res.timings.duration);
  }

  sleep(0.001); // 1ms between requests per VU
}
```

### 7.9 Test Report Generation

```python
# tests/scalability/report_generator.py
import json
from datetime import datetime
from typing import List

from jinja2 import Template


REPORT_TEMPLATE = """
# GRC_Claw Scalability Test Report

**Date:** {{ date }}  
**Duration:** {{ duration }}  
**Overall Result:** {{ 'PASSED' if summary.pass_rate == 1.0 else 'PARTIAL' if summary.pass_rate > 0.5 else 'FAILED' }}

## Summary

| Metric | Value |
|--------|-------|
| Total Scenarios | {{ summary.total_scenarios }} |
| Passed | {{ summary.passed }} |
| Failed | {{ summary.failed }} |
| Pass Rate | {{ "%.1f"|format(summary.pass_rate * 100) }}% |

## Scenario Results

| Scenario | Status | p99 Latency (ms) | Throughput (dec/s) | Error Rate |
|----------|--------|------------------|--------------------|------------|
{% for result in results %}
| {{ result.scenario }} | {{ 'PASS' if result.passed else 'FAIL' }} | {{ result.metrics.p99_latency_ms | default('N/A') }} | {{ result.metrics.throughput | default('N/A') }} | {{ result.metrics.error_rate | default('N/A') }} |
{% endfor %}

## Recommendations

{% for rec in recommendations %}
- {{ rec }}
{% else %}
- No recommendations
{% endfor %}

## Raw Metrics

```json
{{ raw_metrics | tojson(indent=2) }}
```
"""


class ReportGenerator:
    """Generate scalability test reports."""

    def __init__(self, template: str = REPORT_TEMPLATE):
        self.template = Template(template)

    def generate(self, report: TestReport, duration: str) -> str:
        """Generate HTML/Markdown report from test results."""
        return self.template.render(
            date=datetime.now().isoformat(),
            duration=duration,
            summary=report.summary,
            results=report.results,
            recommendations=report.recommendations,
            raw_metrics={
                r.scenario: r.metrics for r in report.results
            },
        )

    def save(self, report: TestReport, path: str, duration: str) -> None:
        """Save report to file."""
        content = self.generate(report, duration)
        with open(path, "w") as f:
            f.write(content)
```

---

## Appendix A: Deployment Patterns

### A.1 Tier 1: Single-Team (Docker Compose)

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

### A.2 Tier 3: Enterprise (Helm Values)

```yaml
# helm/enterprise-values.yaml
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
```

---

## Appendix B: Migration Between Tiers

### B.1 Tier 1 → Tier 2

| Step | Action | Downtime |
|------|--------|----------|
| 1 | Deploy HA PostgreSQL (Patroni) | Zero (parallel) |
| 2 | Deploy Redis Cluster | Zero (parallel) |
| 3 | Migrate data to new storage | Zero (online migration) |
| 4 | Scale PEP to 2+ instances | Zero (rolling) |
| 5 | Scale PDP to 2+ instances | Zero (rolling) |
| 6 | Decommission single-node setup | Zero |

### B.2 Tier 2 → Tier 3

| Step | Action | Downtime |
|------|--------|----------|
| 1 | Deploy second region (K8s cluster) | Zero |
| 2 | Configure cross-region replication (Kafka MM, PostgreSQL logical) | Zero |
| 3 | Deploy GSLB (GeoDNS) | Zero |
| 4 | Migrate tenants to multi-region | Zero (per-tenant) |
| 5 | Scale components to Tier 3 capacity | Zero (rolling) |
| 6 | Decommission single-region dependencies | Zero |

### B.3 Tier 3 → Tier 4

| Step | Action | Downtime |
|------|--------|----------|
| 1 | Deploy additional regions | Zero |
| 2 | Implement cell-based architecture | Zero (per-cell) |
| 3 | Enable data residency enforcement | Zero (policy-driven) |
| 4 | Scale to 100+ tenants | Zero (per-tenant) |
| 5 | Implement global tenant registry | Zero |

---

## Appendix C: Scaling Checklist

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

*End of Scalability Implementation Guide.*



