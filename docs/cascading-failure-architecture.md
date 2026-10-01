# Cascading Failure Analysis Engine — Architecture

## 1. System Overview

A real-time engine that models critical infrastructure as a multi-layer dependency graph, simulates cascading failure propagation across hops, and optimizes network-wide resilience through critical-node identification and mitigation recommendation.

**Domain**: Critical infrastructure (power grids, telecom, water, transport interdependencies)

---

## 2. Core Components

### 2.1 Data Ingestion & Normalization Layer
- **Telemetry Collectors**: Stream metrics (load, capacity, health) from SCADA, IoT sensors, BSS/OSS
- **Topology Importers**: Parse GIS, CIM (Common Information Model), NetJSON, custom YAML/JSON
- **Dependency Mapper**: Auto-discovers direct dependencies via traffic analysis, config parsing, and operator input
- **Output**: Unified `InfrastructureNode` and `DependencyEdge` records

### 2.2 Multi-Hop Dependency Graph Engine
- **Graph Store**: Property graph (Neo4j / Dgraph / in-memory NetworkX for small deployments)
- **Edge Types**:
  - `DEPENDS_ON` (A requires B to function)
  - `CAPACITY_FEEDS` (B supplies capacity to A)
  - `LOGICAL_ROUTE` (traffic/power flows through)
  - `CO_LOCATED` (shared physical risk)
- **Transitive Closure**: Pre-computes N-hop reachability for fast cascade simulation
- **Conditional Edges**: Probabilistic dependencies (e.g., "B fails → A fails with p=0.7 if load > 80%")
- **Dynamic Weights**: Edge strength varies with real-time load, time-of-day, maintenance windows

### 2.3 Failure Propagation Simulator
- **Seed Failure Injection**: Single-node, multi-node, or region-based initial failure
- **Propagation Algorithm**:
  1. Mark seed node(s) as `FAILED`
  2. For each outgoing edge, compute failure probability: `P(fail) = base_prob × load_factor × redundancy_factor`
  3. If dependent node fails, recurse (BFS/DFS with cycle detection)
  4. Track cascade depth, blast radius, time-to-fail per hop
- **Monte Carlo Mode**: Run 10k+ simulations with randomized parameters for statistical confidence
- **Temporal Simulation**: Discrete-event simulation with realistic failure/recovery timelines

### 2.4 Network-Wide Optimization Engine
- **Criticality Scoring**:
  - Betweenness centrality (traffic routing importance)
  - PageRank on dependency graph (transitive influence)
  - Cascade potential: expected blast radius if this node fails
  - Recovery cost × downtime impact
- **Redundancy Optimizer**: Identifies single-points-of-failure (SPOFs), recommends backup paths
- **Resource Reallocation**: Given capacity constraints, suggests load redistribution to minimize cascade risk
- **Maintenance Scheduling**: Optimizes maintenance windows to avoid correlated vulnerability

### 2.5 Impact Assessment & Blast Radius Calculator
- **Service Impact Mapping**: Maps infrastructure nodes to downstream services/customers affected
- **Cascading Depth Analysis**: Reports max hops reached, time to full cascade
- **Sector Cross-Impact**: Tracks inter-sector cascades (power → telecom → water → transport)
- **Economic Impact Estimation**: Downtime cost per minute × affected population

### 2.6 Alerting & Recommendation System
- **Early Warning**: Detects pre-cascade conditions (rising load correlations, near-threshold nodes)
- **Mitigation Playbooks**: Auto-generated runbooks per cascade scenario
- **What-If Analysis**: Operator can simulate "what if we shed load X from node Y"
- **Integration**: PagerDuty, Slack, SOAR platforms via webhooks

### 2.7 Visualization & API Layer
- **Graph Visualization**: D3.js / Cytoscape.js force-directed graph with cascade animation
- **Geospatial Overlay**: Map-based view with cascade propagation animation
- **REST/gRPC API**: Query graph, trigger simulation, get recommendations
- **WebSocket Stream**: Real-time cascade simulation updates

---

## 3. Data Flow

```
Telemetry → Ingestion → Normalization → Dependency Graph
                                            ↓
                                    Failure Injection
                                            ↓
                              Propagation Simulator (BFS + Monte Carlo)
                                            ↓
                              Impact Assessment + Blast Radius
                                            ↓
                              Optimization Engine (criticality + redundancy)
                                            ↓
                              Alerts + Recommendations + Visualization
```

---

## 4. Technology Stack

| Layer | Technology |
|-------|-----------|
| Graph Store | Neo4j / Dgraph / ArangoDB |
| Stream Processing | Apache Kafka + Flink |
| Simulation Engine | Python (NetworkX, SimPy) / Rust (petgraph) for performance |
| Optimization | OR-Tools / Gurobi / custom heuristics |
| API | FastAPI (Python) / gRPC |
| Frontend | React + D3.js / Mapbox GL |
| Deployment | Kubernetes, Helm charts |

---

## 5. Key Algorithms

### 5.1 Cascade Propagation (BFS with Probabilistic Edges)
```
function simulate_cascade(seed_nodes, graph, params):
    failed = set(seed_nodes)
    queue = deque([(n, 0) for n in seed_nodes])  # (node, hop_depth)
    cascade_log = []
    
    while queue:
        node, depth = queue.popleft()
        for edge in graph.outgoing(node):
            target = edge.target
            if target in failed:
                continue
            p_fail = edge.base_prob × load_factor(target) × (1 - redundancy(target))
            if random() < p_fail:
                failed.add(target)
                queue.append((target, depth + 1))
                cascade_log.append(CascadeEvent(node, target, depth, timestamp))
    
    return CascadeResult(failed, cascade_log, max_depth, blast_radius)
```

### 5.2 Criticality Score
```
criticality(node) = (
    w1 × betweenness_centrality(node) +
    w2 × pagerank(node) +
    w3 × expected_blast_radius(node) +
    w4 × recovery_cost(node) +
    w5 × affected_services_count(node)
)
```

### 5.3 Multi-Hop Reachability (Transitive Closure)
- Pre-compute k-hop neighbors for k=1..5 using matrix multiplication on adjacency
- Store as materialized views for O(1) cascade depth queries
- Update incrementally on topology changes

---

## 6. Scalability & Performance

- **Graph Partitioning**: Shard by geographic region or sector
- **Parallel Simulation**: Monte Carlo runs distributed across workers
- **Incremental Updates**: Only recompute affected subgraphs on topology change
- **Caching**: Pre-computed criticality scores refreshed every N minutes
- **Target**: < 2s for 10k-node cascade simulation, < 100ms for criticality query

---

## 7. Resilience & Safety

- **Engine runs in isolated namespace** — cannot affect production infrastructure
- **Read-only data plane** — simulation results require human approval for action
- **Audit trail** — every simulation logged with parameters and results
- **Graceful degradation** — falls back to cached graph if live telemetry unavailable

---

## 8. Future Extensions

- **ML-Enhanced Propagation**: Train GNN on historical failure data for better probability estimates
- **Adversarial Simulation**: Red-team mode — find minimal set of nodes whose failure maximizes damage
- **Cross-Domain Federation**: Share anonymized dependency data across organizations for collective resilience
- **Digital Twin Integration**: Full infrastructure digital twin with real-time state mirroring
