# APEX-OS: Cyber Warfare — Graph-Based Attack Path Mapping Architecture

**Domain:** Cyber Warfare — Attack Path Mapping, Threat Correlation, Critical Asset Protection  
**Version:** 1.0  
**Date:** 2026-10-01  
**Status:** Design  
**Predecessor:** `orbital-graph-architecture.md` (Space SSA domain — this document extends the graph-native paradigm to the cyber warfare domain)

---

## 1. Executive Summary

This document specifies the architecture for APEX-OS's **cyber warfare attack path mapping** subsystem. It models enterprise and military networks as **temporal property graphs** where hosts, vulnerabilities, attackers, and security controls are first-class graph entities. The system computes **attack paths** from any entry point to any critical asset, correlates **threat intelligence** with live graph topology, and identifies **god-nodes** — high-centrality vertices whose compromise would maximize attacker reach.

**Key differentiators from existing cyber graph tools:**

| Capability | Traditional (CyGraph, MulVAL, NetSPA) | APEX-OS |
|---|---|---|
| Graph model | Static attack graph | Temporal property graph with full state versioning |
| Threat correlation | Manual IOC matching | Graph-native threat intel fusion with edge-level confidence |
| Critical asset protection | Single-path analysis | God-node decomposition + multi-objective hardening |
| Scale | Single network | Federated multi-domain with cross-domain path computation |
| Replay | None | Full forensic reconstruction via temporal queries |

---

## 2. Design Principles

| Principle | Rationale |
|---|---|
| **Graph as substrate** | Attack paths are inherently relational: hosts connect, vulnerabilities chain, privileges escalate. A graph captures this natively. |
| **Temporal versioning** | Network topology, vuln states, and threat intel change continuously. Every mutation is versioned for forensic replay. |
| **Threat-in-the-loop** | Threat intelligence is not a sidecar — it is fused into the graph as typed edges with confidence scores, enabling correlation queries. |
| **God-node first** | Not all assets are equal. Centrality-driven god-node identification focuses protection budget on the vertices that matter most. |
| **Federation over centralization** | Multi-domain operations (coalition, multi-tenant cloud) require federated graph queries without centralizing raw topology. |
| **Zero-trust verification** | Every graph query is authenticated, authorized, and audited. Attack path results are classified at the edge level. |

---

## 3. System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     COALITION / MULTI-DOMAIN FEDERATION LAYER           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │ Domain A │  │ Domain B │  │ Domain C │  │ Domain N │  ...          │
│  │ Graph    │  │ Graph    │  │ Graph    │  │ Graph    │              │
│  │ Shard    │  │ Shard    │  │ Shard    │  │ Shard    │              │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘              │
│       └──────────────┴──────┬───────┴──────────────┘                   │
│                    ┌────────▼────────┐                                  │
│                    │  Federation     │                                  │
│                    │  Gateway        │                                  │
│                    │  (Query Router) │                                  │
│                    └────────┬────────┘                                  │
├─────────────────────────────┼───────────────────────────────────────────┤
│                     CORE GRAPH LAYER                                    │
│  ┌──────────────────────────▼──────────────────────────┐               │
│  │           Cyber Attack Graph Database (CAGD)         │               │
│  │  ┌─────────────┐  ┌──────────────┐  ┌────────────┐ │               │
│  │  │  Graph      │  │  Temporal    │  │  Spatial   │ │               │
│  │  │  Storage    │  │  Versioning  │  │  Index     │ │               │
│  │  │  Engine     │  │  Engine      │  │  (R-Tree)  │ │               │
│  │  └─────────────┘  └──────────────┘  └────────────┘ │               │
│  └──────────────────────────────────────────────────────┘               │
├──────────────────────────────────────────────────────────────────────────┤
│                     INTELLIGENCE LAYER                                   │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌────────────┐    │
│  │ Attack Path  │ │  Threat      │ │  God-Node    │ │  Hardening │    │
│  │ Mapper       │ │  Correlator  │ │  Identifier  │ │  Advisor   │    │
│  │ Engine       │ │  Engine      │ │  Engine      │ │  Engine    │    │
│  └──────────────┘ └──────────────┘ └──────────────┘ └────────────┘    │
├──────────────────────────────────────────────────────────────────────────┤
│                     INGESTION LAYER                                     │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐    │
│  │ Network  │ │  Vuln    │ │  Threat  │ │  Asset   │ │  Policy  │    │
│  │ Scanner  │ │  Scanner │ │  Intel   │ │  Inventory│ │  Engine  │    │
│  │ Ingester │ │  Ingester│ │  Ingester│ │  Ingester│ │  Ingester│    │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘    │
├──────────────────────────────────────────────────────────────────────────┤
│                     API & INTERFACE LAYER                               │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐    │
│  │ GraphQL  │ │  SPARQL  │ │  WebSocket│ │  REST    │ │  CLI     │    │
│  │  API     │ │  Endpoint│ │  Subscriptions│ │  API    │ │  Tool    │    │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘    │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Graph Data Model

### 4.1 Node Types (Vertex Labels)

| Node Type | Key Properties | Description |
|---|---|---|
| `Host` | `host_id`, `ip`, `mac`, `os`, `os_version`, `hostname`, `domain`, `criticality_score` | Network endpoint (server, workstation, IoT, OT device) |
| `Service` | `service_id`, `host_id`, `port`, `protocol`, `service_name`, `version`, `banner` | Running service on a host |
| `Vulnerability` | `cve_id`, `cvss_score`, `cvss_vector`, `exploit_available`, `exploit_maturity`, `cwe_id`, `published_date`, `patch_available` | Known vulnerability (CVE/CWE) |
| `Attacker` | `attacker_id`, `threat_actor_id`, `apt_group`, `capability_level`, `motivation`, `sophistication` | Threat actor or attacker entity |
| `ThreatIntel` | `intel_id`, `source`, `indicator_type` (IP/domain/hash/CVE), `indicator_value`, `confidence`, `severity`, `first_seen`, `last_seen`, `kill_chain_phase` | Threat intelligence indicator |
| `SecurityControl` | `control_id`, `control_type` (firewall/IDS/EDR/ACL/SIEM), `rule_id`, `effectiveness`, `coverage` | Security control or countermeasure |
| `NetworkSegment` | `segment_id`, `cidr`, `vlan_id`, `zone` (DMZ/internal/restricted), `trust_level` | Network segmentation boundary |
| `UserAccount` | `account_id`, `host_id`, `username`, `privilege_level` (user/admin/root), `domain_account`, `service_account` | User or service account |
| `Credential` | `credential_id`, `account_id`, `credential_type` (password/hash/token/key), `strength`, `rotation_date`, `exposed` | Authentication credential |
| `AttackStep` | `step_id`, `technique_id` (MITRE ATT&CK), `tactic`, `technique_name`, `description`, `platform` | MITRE ATT&CK technique instance |
| `PolicyRule` | `rule_id`, `classification_level`, `access_conditions`, `data_types` | Data access / security policy |
| `AuditEvent` | `timestamp`, `actor`, `action`, `target`, `result` | Immutable audit trail |
| `GodNode` | `god_node_id`, `host_id`, `centrality_score`, `betweenness_score`, `eigenvector_score`, `compromise_impact_score`, `protection_priority` | Identified critical vertex (derived) |

### 4.2 Edge Types (Relationship Labels)

| Edge Type | From → To | Properties | Semantics |
|---|---|---|---|
| `RUNS_SERVICE` | Host → Service | `start_date`, `status` | Host runs service |
| `HAS_VULNERABILITY` | Service → Vulnerability | `discovered_date`, `confirmed`, `exploit_confidence` | Service has known CVE |
| `EXPLOITS` | Vulnerability → AttackStep | `exploit_maturity`, `success_probability` | CVE maps to ATT&CK technique |
| `REACHES` | Host → Host | `protocol`, `port`, `direction`, `firewall_rule_id`, `allowed` | Network reachability |
| `SEGMENT_MEMBER` | Host → NetworkSegment | `membership_date` | Host belongs to segment |
| `SEGMENT_GATEWAY` | NetworkSegment → NetworkSegment | `gateway_type`, `trust_direction`, `acl_rules` | Inter-segment connectivity |
| `HAS_ACCOUNT` | Host → UserAccount | `account_type`, `created_date` | Host has user account |
| `USES_CREDENTIAL` | UserAccount → Credential | `auth_protocol`, `last_used` | Account uses credential |
| `PRIVILEGE_ESCALATION` | UserAccount → UserAccount | `escalation_path`, `technique_id`, `probability` | PrivEsc path between accounts |
| `HAS_PRIVILEGE` | UserAccount → Host | `privilege_level`, `scope` | Account has privilege on host |
| `MATCHES_INTEL` | (any node) → ThreatIntel | `match_type`, `confidence`, `correlation_date` | Node matches threat indicator |
| `ATTRIBUTED_TO` | ThreatIntel → Attacker | `confidence`, `attribution_source` | Indicator attributed to actor |
| `CAPABLE_OF` | Attacker → AttackStep | `proficiency`, `observed_usage` | Actor known to use technique |
| `PROTECTED_BY` | Host → SecurityControl | `control_effectiveness`, `coverage_scope` | Host protected by control |
| `MITIGATES` | SecurityControl → Vulnerability | `mitigation_effectiveness`, `residual_risk` | Control mitigates CVE |
| `AT_STEP` | AttackStep → AttackStep | `sequence_order`, `tactic_transition` | ATT&CK technique chaining |
| `GOD_NODE_OF` | GodNode → Host | `identification_date`, `score_version` | God-node designation |
| `GOVERNED_BY` | (any node) → PolicyRule | `classification`, `effective_date` | Data access policy |
| `AUDITED_BY` | AuditEvent → (any node) | `action_type`, `timestamp` | Audit trail link |
| `FEDERATED_WITH` | NetworkSegment ↔ NetworkSegment | `agreement_type`, `data_types`, `privacy_level` | Inter-domain data sharing |

### 4.3 Temporal Graph Model

Every node and edge carries temporal metadata:

- `valid_from` / `valid_to`: Real-world time the fact was true
- `recorded_from` / `recorded_to`: Time the fact was recorded in the system
- `version`: Monotonically increasing version counter

This enables:

- **Point-in-time queries**: "What was the attack path from Internet to DB server on 2026-09-15?"
- **Temporal traversals**: "Show all new attack paths discovered in the last 24 hours"
- **Forensic reconstruction**: "How did the attacker move from initial access to domain admin?"
- **Trend analysis**: "How has the attack surface evolved over the past 90 days?"

---

## 5. Core Components

### 5.1 Cyber Attack Graph Database (CAGD)

**Technology choice:** Distributed property graph with native temporal support.

**Implementation options:**
- **Primary**: Neo4j 5.x+ with temporal extensions (for single-domain shards)
- **Federated**: Apache TinkerPop/Gremlin-compatible graph for cross-domain queries
- **Alternative**: Amazon Neptune or Azure Cosmos DB Gremlin API for cloud-deployed domains

**Sharding strategy:**
- Each domain operates a **local graph shard** containing their sovereign network topology
- A **federated catalog** (lightweight metadata graph) indexes cross-domain queries without exposing raw topology
- Shared entities (e.g., multi-domain hosts) use **consensus-based merging** with conflict resolution

**Storage layout:**
```
cagd/
├── nodes/
│   ├── host/
│   ├── service/
│   ├── vulnerability/
│   ├── attacker/
│   ├── threat_intel/
│   ├── security_control/
│   ├── network_segment/
│   ├── user_account/
│   ├── credential/
│   ├── attack_step/
│   ├── policy_rule/
│   ├── audit_event/
│   └── god_node/
├── edges/
│   ├── runs_service/
│   ├── has_vulnerability/
│   ├── exploits/
│   ├── reaches/
│   ├── segment_member/
│   ├── segment_gateway/
│   ├── has_account/
│   ├── uses_credential/
│   ├── privilege_escalation/
│   ├── has_privilege/
│   ├── matches_intel/
│   ├── attributed_to/
│   ├── capable_of/
│   ├── protected_by/
│   ├── mitigates/
│   ├── at_step/
│   ├── god_node_of/
│   ├── governed_by/
│   ├── audited_by/
│   └── federated_with/
├── temporal/
│   ├── versions/
│   └── snapshots/
└── spatial/
    ├── rtree_index/
    └── geohash_index/
```

### 5.2 Attack Path Mapper Engine

Graph-native attack path computation from any entry point to any critical asset.

**Algorithm:**

1. **Entry point identification**: Identify all externally reachable hosts (DMZ, VPN endpoints, public-facing services)
2. **Goal identification**: Identify all critical assets (god-nodes, sensitive data stores, domain controllers)
3. **Path enumeration**: Use modified Dijkstra/BFS with edge weights = f(CVSS, exploit maturity, control effectiveness)
4. **Path scoring**: Compute cumulative risk score for each path
5. **Path ranking**: Rank paths by (probability of success, impact, time-to-compromise)

**Graph query example (Cypher-like):**
```cypher
MATCH path = shortestPath(
  (entry:Host {zone: 'DMZ'})-[*..10]->(target:Host {criticality_score: 0.95})
)
WHERE ALL(r IN relationships(path) WHERE r.allowed = true)
RETURN path,
       reduce(s = 1.0, r IN relationships(path) |
         s * r.success_probability
       ) AS path_probability,
       reduce(s = 0, r IN relationships(path) |
         s + r.cvss_score
       ) AS cumulative_cvss
ORDER BY path_probability DESC
LIMIT 20
```

**Multi-objective path optimization:**
- Minimize: path length (number of hops)
- Minimize: cumulative CVSS (difficulty)
- Maximize: path probability (success likelihood)
- Maximize: impact score (criticality of target)

**Integration with ApexGraphSwarm kernels:**
- `shortest-path/dijkstra.py` — base shortest-path with custom edge weights
- `shortest-path/astar.py` — heuristic-guided path finding for large graphs
- `shortest-path/bellman_ford.py` — negative-weight handling for control bypasses

### 5.3 Threat Correlator Engine

Graph-native threat intelligence fusion — correlates external threat intel with live graph topology.

**Correlation pipeline:**

1. **Indicator ingestion**: Ingest IOCs from threat feeds (MISP, STIX/TAXII, commercial feeds)
2. **Graph matching**: Match indicators to graph nodes using multi-key matching:
   - IP → Host.ip
   - Domain → Host.hostname
   - Hash → Service.banner, Credential hash
   - CVE → Vulnerability.cve_id
3. **Edge creation**: Create `MATCHES_INTEL` edges with confidence scores
4. **Attribution**: Link indicators to `Attacker` nodes via `ATTRIBUTED_TO` edges
5. **Path enrichment**: Recompute attack paths with threat intel context
6. **Alert generation**: Generate alerts when threat intel matches create new or shortened attack paths

**Correlation scoring:**
```
confidence = w1 * indicator_confidence
           + w2 * source_reliability
           + w3 * freshness_score
           + w4 * graph_context_match
```

Where:
- `indicator_confidence`: Feed-provided confidence (0-1)
- `source_reliability`: Historical accuracy of the source (0-1)
- `freshness_score`: Decay function based on `last_seen` vs current time
- `graph_context_match`: How well the indicator fits the surrounding graph context (0-1)

**Graph query example:**
```cypher
MATCH (ti:ThreatIntel)-[m:MATCHES_INTEL]->(h:Host)
WHERE ti.indicator_type = 'IP'
  AND ti.confidence > 0.7
  AND m.correlation_date > datetime() - duration('P7D')
MATCH path = shortestPath((h)-[*..8]->(target:Host {criticality_score: 0.9}))
RETURN ti.indicator_value, ti.threat_actor_id,
       h.hostname, target.hostname,
       length(path) AS hops,
       m.confidence AS match_confidence
ORDER BY m.confidence DESC, hops ASC
```

### 5.4 God-Node Identifier Engine

Centrality-driven identification of critical vertices whose compromise maximizes attacker reach.

**God-node scoring algorithm:**

For each host node `v` in the attack graph, compute:

```
god_score(v) = α * betweenness_centrality(v)
             + β * eigenvector_centrality(v)
             + γ * compromise_impact(v)
             + δ * threat_exposure(v)
```

Where:
- `betweenness_centrality(v)`: Fraction of shortest paths passing through `v` — measures how often `v` is a bridge
- `eigenvector_centrality(v)`: Influence based on connections to other high-scoring nodes — measures how well-connected `v` is to other critical nodes
- `compromise_impact(v)`: Number of critical assets reachable from `v` weighted by their criticality — measures blast radius
- `threat_exposure(v)`: Number of threat intel matches and attacker capabilities targeting `v` — measures current threat landscape

**Weights (α, β, γ, δ)** are configurable per deployment. Default: α=0.3, β=0.2, γ=0.3, δ=0.2

**God-node identification process:**

1. Compute centrality metrics for all host nodes
2. Compute compromise impact via multi-hop reachability analysis
3. Compute threat exposure via threat intel correlation
4. Calculate composite god_score for each node
5. Rank nodes by god_score
6. Designate top-N as `GodNode` vertices with `GOD_NODE_OF` edges
7. Set `protection_priority` based on rank

**Graph query example:**
```cypher
MATCH (h:Host)
WITH h,
     apoc.algo.betweenness(['REACHES'], h, 'BOTH') AS betweenness,
     apoc.algo.eigenvector(h, 'REACHES') AS eigenvector
MATCH (h)-[*1..5]->(target:Host)
WHERE target.criticality_score > 0.8
WITH h, betweenness, eigenvector,
     count(DISTINCT target) * avg(target.criticality_score) AS impact
MATCH (h)-[m:MATCHES_INTEL]->(ti:ThreatIntel)
WITH h, betweenness, eigenvector, impact,
     count(ti) * avg(ti.confidence) AS exposure
WITH h, 0.3 * betweenness + 0.2 * eigenvector +
     0.3 * impact + 0.2 * exposure AS god_score
ORDER BY god_score DESC
LIMIT 20
RETURN h.hostname, h.ip, god_score, betweenness, eigenvector, impact, exposure
```

**Integration with ApexGraphSwarm kernels:**
- `community_detection/louvain.py` — identify network communities for segmented god-node analysis
- `community_detection/leiden.py` — higher-resolution community detection for large networks
- `community_detection/label_propagation.py` — fast approximate community detection for real-time updates
- `formal_verification/graph_theory.py` — formal verification of centrality properties
- `formal_verification/invariant_checker.py` — verify god-node invariants (e.g., "no single point of failure")

### 5.5 Hardening Advisor Engine

Graph-based security control optimization — recommends where to place security controls for maximum risk reduction.

**Algorithm:**

1. **Current state analysis**: Identify all attack paths to god-nodes
2. **Control gap analysis**: For each attack path, identify missing or weak controls
3. **What-if analysis**: For each candidate control placement, simulate its effect on the graph
4. **ROI scoring**: Compute risk reduction per dollar for each candidate
5. **Recommendation**: Rank recommendations by ROI

**What-if simulation:**
```cypher
// Simulate adding a firewall rule between segment A and segment B
MATCH (segA:NetworkSegment {zone: 'DMZ'})-[g:SEGMENT_GATEWAY]->(segB:NetworkSegment {zone: 'internal'})
WITH segA, segB, g
// Remove or weaken the gateway edge
SET g.allowed = false
// Recompute attack paths
MATCH path = shortestPath(
  (entry:Host {zone: 'DMZ'})-[*..10]->(target:Host {criticality_score: 0.95})
)
WHERE ALL(r IN relationships(path) WHERE r.allowed = true)
RETURN count(path) AS remaining_paths,
       avg(length(path)) AS avg_path_length
// Restore the edge
SET g.allowed = true
```

**Recommendation types:**
- **Network segmentation**: Add segment gateways between high-trust and low-trust zones
- **Patch management**: Prioritize patching vulnerabilities on god-node attack paths
- **Access control**: Remove unnecessary `REACHES` edges (firewall rules)
- **Monitoring**: Add `SecurityControl` nodes on high-betweenness edges
- **Credential hardening**: Rotate exposed credentials on privilege escalation paths

### 5.6 Federation Gateway

The Federation Gateway is the **neutral intermediary** that enables multi-domain attack path queries without centralizing raw topology.

**Responsibilities:**
1. **Query decomposition**: Break a multi-domain attack path query into sub-queries for each domain shard
2. **Privacy enforcement**: Apply differential privacy, k-anonymity, and data classification filters before results leave a domain shard
3. **Result aggregation**: Merge results from multiple shards, resolving conflicts via consensus protocol
4. **Audit logging**: Record all federated queries in the audit graph

**Federation protocol:**
```
1. Client submits attack path query to Federation Gateway
2. Gateway authenticates client (mutual TLS + coalition PKI)
3. Gateway decomposes query into domain-specific sub-queries
4. Each domain shard executes sub-query locally
5. Domain shard applies privacy filter (noise injection, aggregation, redaction)
6. Filtered results returned to Gateway
7. Gateway merges results (consensus for conflicting data)
8. Final result returned to client with audit trail
```

**Privacy mechanisms:**
- **Differential privacy**: Add calibrated noise to path counts and centrality scores
- **k-anonymity**: Suppress results that would identify fewer than k hosts
- **Data classification**: Each domain classifies their data (UNCLASSIFIED, RESTRICTED, CONFIDENTIAL, SECRET); the gateway enforces need-to-know
- **Secure multi-party computation (SMPC)**: For highly sensitive queries, compute on encrypted data without decryption

---

## 6. Attack Path Lifecycle

### 6.1 Attack Path States

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ DISCOVERED│───▶│ ANALYZED │───▶│ MITIGATED│───▶│ RESOLVED │
│          │    │          │    │          │    │          │
│ New path │    │ Scored & │    │ Control  │    │ Verified │
│ found    │    │ ranked   │    │ deployed │    │ closed   │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
     │                                               │
     │              ┌──────────┐                     │
     └─────────────▶│ EXPIRED  │◀────────────────────┘
                    │          │
                    │ No longer│
                    │ valid    │
                    └──────────┘
```

### 6.2 State Transitions

| From | To | Trigger | Audit Event |
|---|---|---|---|
| — | DISCOVERED | New path found by mapper | `path.discovered` |
| DISCOVERED | ANALYZED | Path scored and ranked | `path.analyzed` |
| ANALYZED | MITIGATED | Control recommended & deployed | `path.mitigated` |
| MITIGATED | RESOLVED | Control verified effective | `path.resolved` |
| ANALYZED | EXPIRED | Path no longer valid (topology change) | `path.expired` |
| MITIGATED | EXPIRED | Control bypassed or removed | `path.expired` |
| EXPIRED | DISCOVERED | Path re-discovered | `path.rediscovered` |

---

## 7. Threat Correlation Framework

### 7.1 Kill Chain Integration

The threat correlator maps indicators to the Cyber Kill Chain:

```
┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│RECON     │─▶│WEAPONIZE │─▶│ DELIVERY │─▶│EXPLOIT   │─▶│INSTALL   │─▶│C2        │─▶│OBJECTIVES│
│          │  │          │  │          │  │          │  │          │  │          │  │          │
│Scan      │  │Build     │  │Phishing  │  │CVE       │  │Persist   │  │Beacon    │  │Exfil     │
│OSINT     │  │Malware   │  │Watering  │  │0-day     │  │Backdoor  │  │Lateral   │  │Destroy   │
│          │  │          │  │Hole      │  │          │  │          │  │Movement  │  │          │
└──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘
     │              │              │              │              │              │              │
     ▼              ▼              ▼              ▼              ▼              ▼              ▼
  MATCHES_INTEL  MATCHES_INTEL  MATCHES_INTEL  MATCHES_INTEL  MATCHES_INTEL  MATCHES_INTEL  MATCHES_INTEL
  on Host        on Service     on Host        on Vuln        on Host        on Host        on Host
```

### 7.2 Correlation Rules

| Rule ID | Indicator Type | Graph Match | Confidence Boost | Action |
|---|---|---|---|---|
| `CORR-001` | CVE | `Vulnerability.cve_id` | +0.3 if exploit_available | Create alert, prioritize patching |
| `CORR-002` | IP | `Host.ip` | +0.2 if in DMZ | Create alert, check reachability |
| `CORR-003` | Domain | `Host.hostname` | +0.2 if resolves to host | Create alert, check DNS logs |
| `CORR-004` | File Hash | `Service.banner` | +0.1 if service exposed | Create alert, scan for file |
| `CORR-005` | Email | `UserAccount.username` | +0.1 if external | Create alert, check email gateway |
| `CORR-006` | YARA Rule | `Service.banner` | +0.2 if match | Create alert, isolate host |
| `CORR-007` | TTP | `AttackStep.technique_id` | +0.3 if actor known | Create alert, update ATT&CK mapping |

### 7.3 Threat Actor Attribution

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ ThreatIntel  │────▶│ AttributedTo │────▶│ Attacker     │
│ (indicator)  │     │ (edge with   │     │ (threat      │
│              │     │  confidence) │     │  actor)      │
└──────────────┘     └──────────────┘     └──────────────┘
                                               │
                                               ▼
                                        ┌──────────────┐
                                        │ CapableOf    │
                                        │ (edge with   │
                                        │  proficiency)│
                                        └──────────────┘
                                               │
                                               ▼
                                        ┌──────────────┐
                                        │ AttackStep   │
                                        │ (ATT&CK      │
                                        │  technique)  │
                                        └──────────────┘
```

---

## 8. God-Node Protection Framework

### 8.1 God-Node Tiers

| Tier | God Score Range | Protection Level | Response Time | Example Assets |
|---|---|---|---|---|
| **Tier 1 — Critical** | 0.90 – 1.00 | Maximum — air-gapped, zero-trust, continuous monitoring | < 15 minutes | Domain controllers, root CAs, SCADA masters |
| **Tier 2 — High** | 0.70 – 0.89 | Enhanced — micro-segmentation, EDR, SIEM correlation | < 1 hour | Database servers, ERP systems, PKI intermediates |
| **Tier 3 — Medium** | 0.50 – 0.69 | Standard — firewall, IDS, regular patching | < 4 hours | Application servers, file servers |
| **Tier 4 — Low** | 0.30 – 0.49 | Basic — perimeter defense, baseline hardening | < 24 hours | Workstations, printers, IoT devices |

### 8.2 Protection Strategies per Tier

**Tier 1 — Critical:**
- Air-gapped or micro-segmented with dedicated `SecurityControl` nodes
- Multi-factor authentication on all `Credential` nodes
- Continuous `AuditEvent` logging with real-time SIEM correlation
- Formal verification of all `REACHES` edges (using `formal_verification` kernel)
- Redundant `GodNode` monitoring with automated incident response

**Tier 2 — High:**
- Network segmentation with `SEGMENT_GATEWAY` edges to less-trusted zones
- EDR deployment with `PROTECTED_BY` edges
- Regular vulnerability scanning with `HAS_VULNERABILITY` edge updates
- Privileged access management on `UserAccount` nodes

**Tier 3 — Medium:**
- Standard firewall rules (`REACHES` edges with `allowed: false`)
- IDS/IPS deployment with `PROTECTED_BY` edges
- Regular patching cadence for `Vulnerability` nodes

**Tier 4 — Low:**
- Perimeter defense
- Baseline OS hardening
- Default-deny `REACHES` edges

### 8.3 God-Node Monitoring

```cypher
// Real-time god-node compromise detection
MATCH (g:GodNode)-[:GOD_NODE_OF]->(h:Host)
OPTIONAL MATCH (h)-[m:MATCHES_INTEL]->(ti:ThreatIntel)
WHERE m.correlation_date > datetime() - duration('PT1H')
WITH g, h, count(ti) AS recent_intel_matches
WHERE recent_intel_matches > 0
RETURN g.protection_priority, h.hostname, h.ip,
       recent_intel_matches, g.compromise_impact_score
ORDER BY g.protection_priority ASC, recent_intel_matches DESC
```

---

## 9. Integration with ApexGraphSwarm Kernels

The cyber attack graph architecture leverages existing ApexGraphSwarm kernels:

| Kernel | Module | Use in Cyber Architecture |
|---|---|---|
| `shortest-path` | `dijkstra.py` | Base attack path finding with weighted edges |
| `shortest-path` | `astar.py` | Heuristic-guided path finding for large networks |
| `shortest-path` | `bellman_ford.py` | Negative-weight handling for control bypasses |
| `shortest-path` | `floyd_warshall.py` | All-pairs shortest paths for god-node pre-computation |
| `community_detection` | `louvain.py` | Network community detection for segmented analysis |
| `community_detection` | `leiden.py` | High-resolution community detection for large networks |
| `community_detection` | `label_propagation.py` | Fast approximate community detection for real-time updates |
| `formal_verification` | `graph_theory.py` | Formal verification of centrality and path properties |
| `formal_verification` | `invariant_checker.py` | Verify god-node invariants (no SPOF, etc.) |
| `formal_verification` | `proof_certificate.py` | Generate proof certificates for audit |
| `graph_coloring` | — | Channel assignment for network segmentation |
| `graph_partitioning` | — | Graph partitioning for federated sharding |
| `max-flow` | — | Network capacity analysis for DDoS path mapping |
| `mst` | — | Minimum spanning tree for critical path identification |

---

## 10. API Specification

### 10.1 GraphQL Schema (Core Types)

```graphql
type Host {
  host_id: ID!
  ip: String!
  mac: String
  os: String
  hostname: String
  zone: String
  criticality_score: Float!
  services: [Service!]!
  vulnerabilities: [Vulnerability!]!
  accounts: [UserAccount!]!
  godNode: GodNode
  threatMatches: [ThreatIntel!]!
  reachableHosts: [Host!]!
}

type AttackPath {
  path_id: ID!
  entryPoint: Host!
  target: Host!
  hops: [Host!]!
  edges: [PathEdge!]!
  path_probability: Float!
  cumulative_cvss: Float!
  impact_score: Float!
  state: PathState!
  discovered_at: DateTime!
  mitigated_at: DateTime
  resolved_at: DateTime
}

type GodNode {
  god_node_id: ID!
  host: Host!
  centrality_score: Float!
  betweenness_score: Float!
  eigenvector_score: Float!
  compromise_impact_score: Float!
  threat_exposure: Float!
  protection_priority: Int!
  tier: GodNodeTier!
}

type ThreatCorrelation {
  correlation_id: ID!
  indicator: ThreatIntel!
  matchedNode: Host!
  confidence: Float!
  kill_chain_phase: String!
  correlated_at: DateTime!
}

type Query {
  attackPaths(
    entryPoint: HostInput
    target: HostInput
    maxHops: Int = 10
    minProbability: Float = 0.0
    limit: Int = 20
  ): [AttackPath!]!

  godNodes(
    tier: GodNodeTier
    minScore: Float = 0.0
    limit: Int = 50
  ): [GodNode!]!

  threatCorrelations(
    indicatorType: IndicatorType
    minConfidence: Float = 0.5
    timeWindow: Duration = P7D
  ): [ThreatCorrelation!]!

  whatIfAnalysis(
    controlChange: ControlChangeInput!
    target: HostInput
  ): WhatIfResult!
}

type Mutation {
  deployControl(control: ControlDeployInput!): SecurityControl!
  mitigatePath(pathId: ID!, action: MitigationAction!): AttackPath!
  updateThreatIntel(intel: ThreatIntelInput!): ThreatIntel!
}
```

### 10.2 REST Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/attack-paths` | List attack paths (filterable by entry, target, probability) |
| `GET` | `/api/v1/attack-paths/{id}` | Get attack path details |
| `POST` | `/api/v1/attack-paths/compute` | Compute new attack paths |
| `GET` | `/api/v1/god-nodes` | List identified god-nodes |
| `GET` | `/api/v1/god-nodes/{id}` | Get god-node details |
| `POST` | `/api/v1/god-nodes/recompute` | Recompute god-node scores |
| `GET` | `/api/v1/threat-correlations` | List threat correlations |
| `POST` | `/api/v1/threat-correlate` | Run threat correlation |
| `POST` | `/api/v1/what-if` | Run what-if analysis |
| `GET` | `/api/v1/hardening-recommendations` | Get hardening recommendations |
| `POST` | `/api/v1/controls/deploy` | Deploy security control |

---

## 11. Deployment Architecture

### 11.1 Single-Domain Deployment

```
┌─────────────────────────────────────────────┐
│                  Client                      │
│  (CLI / Web UI / SIEM Integration)          │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│              API Gateway                     │
│  (GraphQL / REST / WebSocket)               │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│           CAGD Cluster                       │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐     │
│  │ Shard 1 │  │ Shard 2 │  │ Shard N │     │
│  │ (Neo4j) │  │ (Neo4j) │  │ (Neo4j) │     │
│  └─────────┘  └─────────┘  └─────────┘     │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│           Ingestion Pipeline                 │
│  ┌────────┐ ┌────────┐ ┌────────┐          │
│  │Network │ │Vuln    │ │Threat  │          │
│  │Scanner │ │Scanner │ │Intel   │          │
│  └────────┘ └────────┘ └────────┘          │
└─────────────────────────────────────────────┘
```

### 11.2 Multi-Domain Federation Deployment

```
┌──────────────────────────────────────────────────────────┐
│                    Client                                 │
└──────────────────────────┬───────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────┐
│                 Federation Gateway                        │
│  (Query Router / Privacy Filter / Audit Logger)          │
└───────┬──────────┬──────────┬──────────┬────────────────┘
        │          │          │          │
┌───────▼──┐ ┌─────▼────┐ ┌───▼──────┐ ┌▼───────────────┐
│ Domain A │ │ Domain B │ │ Domain C │ │ Domain N       │
│ CAGD     │ │ CAGD     │ │ CAGD     │ │ CAGD           │
│ Shard    │ │ Shard    │ │ Shard    │ │ Shard          │
│          │ │          │ │          │ │                │
│ ┌──────┐ │ │ ┌──────┐ │ │ ┌──────┐ │ │ ┌──────┐      │
│ │Attack│ │ │ │Attack│ │ │ │Attack│ │ │ │Attack│      │
│ │Path  │ │ │ │Path  │ │ │ │Path  │ │ │ │Path  │      │
│ │Mapper│ │ │ │Mapper│ │ │ │Mapper│ │ │ │Mapper│      │
│ └──────┘ │ │ └──────┘ │ │ └──────┘ │ │ └──────┘      │
│ ┌──────┐ │ │ ┌──────┐ │ │ ┌──────┐ │ │ ┌──────┐      │
│ │Threat│ │ │ │Threat│ │ │ │Threat│ │ │ │Threat│      │
│ │Corr. │ │ │ │Corr. │ │ │ │Corr. │ │ │ │Corr. │      │
│ └──────┘ │ │ └──────┘ │ │ └──────┘ │ │ └──────┘      │
│ ┌──────┐ │ │ ┌──────┐ │ │ ┌──────┐ │ │ ┌──────┐      │
│ │God-  │ │ │ │God-  │ │ │ │God-  │ │ │ │God-  │      │
│ │Node  │ │ │ │Node  │ │ │ │Node  │ │ │ │Node  │      │
│ └──────┘ │ │ └──────┘ │ │ └──────┘ │ │ └──────┘      │
└──────────┘ └──────────┘ └──────────┘ └────────────────┘
```

---

## 12. Security Considerations

### 12.1 Graph Security

| Threat | Mitigation |
|---|---|
| Graph injection via malicious indicator | Input validation, indicator sanitization, rate limiting |
| Path enumeration reveals network topology | Differential privacy, k-anonymity, result redaction |
| God-node identification reveals critical assets | Role-based access control, need-to-know enforcement |
| Temporal queries reveal historical topology | Time-based access controls, audit logging |
| Federated queries leak cross-domain info | SMPC, secure enclaves, privacy filters |

### 12.2 Zero-Trust Verification

- Every graph query is authenticated (mutual TLS + coalition PKI)
- Every query is authorized (RBAC + ABAC with classification levels)
- Every query is audited (immutable `AuditEvent` nodes)
- Every result is classified (edge-level data classification)
- Every mutation is versioned (temporal graph integrity)

---

## 13. Performance Targets

| Metric | Target | Notes |
|---|---|---|
| Attack path computation | < 5s for 10K-node graph | Single domain, cached topology |
| God-node identification | < 30s for 100K-node graph | Full centrality recomputation |
| Threat correlation | < 1s per indicator | Incremental matching |
| Federated query | < 10s for 3-domain federation | Including privacy filters |
| Temporal query | < 2s for 90-day lookback | Point-in-time reconstruction |
| Graph ingestion | > 10K nodes/minute | Bulk scanner import |
| Concurrent queries | > 100 QPS | Per domain shard |

---

## 14. Future Work

| Phase | Feature | Description |
|---|---|---|
| **Phase 2** | ML-augmented path scoring | Train models on historical attack data to improve path probability estimates |
| **Phase 2** | Automated remediation | Auto-deploy controls via SOAR integration |
| **Phase 3** | Predictive attack path mapping | Use threat actor TTPs to predict future attack paths before they exist |
| **Phase 3** | Cross-domain god-node federation | Identify god-nodes spanning multiple federated domains |
| **Phase 4** | Quantum-resistant graph cryptography | Post-quantum security for federated graph queries |
| **Phase 4** | Autonomous defense | Self-healing network topology based on real-time attack path analysis |

---

## 15. Appendix: Graph Query Cookbook

### A. Find all attack paths from DMZ to domain controller
```cypher
MATCH path = shortestPath(
  (dmz:Host {zone: 'DMZ'})-[*..10]->(dc:Host {hostname: 'DC01'})
)
WHERE ALL(r IN relationships(path) WHERE r.allowed = true)
RETURN path, length(path) AS hops
ORDER BY hops ASC
```

### B. Find all hosts reachable from a compromised host
```cypher
MATCH (compromised:Host {ip: '10.0.1.50'})-[*1..5]->(reachable:Host)
WHERE ALL(r IN relationships(path) WHERE r.allowed = true)
RETURN DISTINCT reachable.hostname, reachable.ip, reachable.criticality_score
ORDER BY reachable.criticality_score DESC
```

### C. Find all vulnerabilities on the attack path to a god-node
```cypher
MATCH path = shortestPath(
  (entry:Host {zone: 'DMZ'})-[*..10]->(g:GodNode)-[:GOD_NODE_OF]->(target:Host)
)
UNWIND nodes(path) AS n
MATCH (n)-[:HAS_VULNERABILITY]->(v:Vulnerability)
RETURN v.cve_id, v.cvss_score, v.exploit_available, n.hostname
ORDER BY v.cvss_score DESC
```

### D. Find all threat intel matching hosts on critical attack paths
```cypher
MATCH path = shortestPath(
  (entry:Host {zone: 'DMZ'})-[*..10]->(target:Host {criticality_score: 0.95})
)
UNWIND nodes(path) AS n
MATCH (n)-[m:MATCHES_INTEL]->(ti:ThreatIntel)
RETURN ti.indicator_value, ti.threat_actor_id, ti.confidence,
       n.hostname, m.correlation_date
ORDER BY ti.confidence DESC
```

### E. Find the shortest path with the highest cumulative CVSS
```cypher
MATCH path = (entry:Host {zone: 'DMZ'})-[*..10]->(target:Host {criticality_score: 0.95})
WHERE ALL(r IN relationships(path) WHERE r.allowed = true)
WITH path,
     reduce(s = 0, r IN relationships(path) | s + r.cvss_score) AS total_cvss
ORDER BY total_cvss DESC
LIMIT 1
RETURN path, total_cvss
```

### F. Find all privilege escalation paths from a user account to domain admin
```cypher
MATCH path = shortestPath(
  (user:UserAccount {username: 'jsmith'})-[*..5]->(admin:UserAccount {privilege_level: 'domain_admin'})
)
WHERE ALL(r IN relationships(path) WHERE r:PRIVILEGE_ESCALATION)
RETURN path, length(path) AS escalation_hops
```

### G. Find all exposed credentials on the attack path to a god-node
```cypher
MATCH path = shortestPath(
  (entry:Host {zone: 'DMZ'})-[*..10]->(g:GodNode)-[:GOD_NODE_OF]->(target:Host)
)
UNWIND nodes(path) AS n
MATCH (n)-[:HAS_ACCOUNT]->(ua:UserAccount)-[:USES_CREDENTIAL]->(c:Credential)
WHERE c.exposed = true
RETURN c.credential_id, ua.username, n.hostname, c.credential_type
```

### H. Temporal query: attack path state on a specific date
```cypher
MATCH path = shortestPath(
  (entry:Host {zone: 'DMZ'})-[*..10]->(target:Host {hostname: 'DC01'})
)
WHERE ALL(r IN relationships(path) WHERE r.allowed = true)
  AND ALL(n IN nodes(path) WHERE n.valid_from <= datetime('2026-09-15') AND n.valid_to >= datetime('2026-09-15'))
  AND ALL(r IN relationships(path) WHERE r.valid_from <= datetime('2026-09-15') AND r.valid_to >= datetime('2026-09-15'))
RETURN path, length(path) AS hops
```

---

**Document Control:**
- **Author:** APEX-OS Architecture Team
- **Reviewers:** Cyber Warfare Domain Lead, Graph Infrastructure Lead
- **Approval:** APEX-OS Technical Steering Committee
- **Next Review:** 2026-11-01
