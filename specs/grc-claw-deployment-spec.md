# GRC_Claw Deployment Specification

**Version:** 2.0  
**Date:** 2026-10-01  
**Status:** Draft  
**Owner:** GRC_Claw Architecture Team  
**Parent Documents:** GRC_Claw Reference Architecture v1.0, Performance Spec v1.0, Storage Spec v1.0, CI Framework v1.0, Scalability Spec v1.0

---

## 1. Purpose & Scope

This specification defines how GRC_Claw is deployed, operated, and maintained in production environments. It establishes the containerization strategy, cloud-native architecture patterns, scaling policies, high availability design, disaster recovery procedures, GitOps pipelines, progressive delivery, multi-cloud deployment, edge computing, serverless components, and cost optimization strategies.

**In scope:** All GRC_Claw runtime components — control plane (PDP, PEP, Policy API), evidence collection, observability, agent identity, compliance mapping, analytics, and supporting data infrastructure. Deployment automation (ArgoCD), progressive delivery (Argo Rollouts), multi-cloud patterns, edge architecture, serverless (Knative), and FinOps practices.

**Out of scope:** Build-time tooling, developer environment setup, CI/CD pipeline internals (covered by GRC_Claw CI Framework v1.0).

---

## 2. Deployment Architecture Overview

### 2.1 Production Topology

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              CLOUD REGION (Primary)                              │
│                                                                                 │
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │                         Kubernetes Cluster (EKS/GKE/AKS)                  │  │
│  │                                                                           │  │
│  │  ┌─────────────────────────────────────────────────────────────────────┐  │  │
│  │  │                      Ingress Controller                             │  │  │
│  │  │                 (NGINX / Traefik / Istio Ingress)                   │  │  │
│  │  │                    TLS termination, WAF, rate limiting               │  │  │
│  │  └─────────────────────────────────────────────────────────────────────┘  │  │
│  │                                    │                                        │  │
│  │  ┌─────────────────────────────────▼─────────────────────────────────────┐  │  │
│  │  │                      API Gateway (Kong / Envoy)                       │  │  │
│  │  │            AuthN (OAuth 2.1/OIDC), AuthZ, rate limiting, routing      │  │  │
│  │  └─────────────────────────────────────────────────────────────────────┘  │  │
│  │                                    │                                        │  │
│  │  ┌─────────────────────────────────▼─────────────────────────────────────┐  │  │
│  │  │                        SERVICE MESH (Istio)                           │  │  │
│  │  │              mTLS, traffic management, observability                  │  │  │
│  │  └─────────────────────────────────────────────────────────────────────┘  │  │
│  │                                    │                                        │  │
│  │  ┌─────────────────────────────────▼─────────────────────────────────────┐  │  │
│  │  │                      MICROSERVICES LAYER                              │  │  │
│  │  │                                                                       │  │  │
│  │  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌─────────────┐ │  │  │
│  │  │  │  Policy      │ │  PDP Service │ │  PEP Gateway │ │  Agent      │ │  │  │
│  │  │  │  Definition  │ │  (OPA/Cedar) │ │  (MCP/Envoy) │ │  Identity   │ │  │  │
│  │  │  │  (FastAPI)   │ │              │ │              │ │  (SPIRE)    │ │  │  │
│  │  │  │  3 replicas  │ │  3 replicas  │ │  3 replicas  │ │  3 replicas │ │  │  │
│  │  │  └──────────────┘ └──────────────┘ └──────────────┘ └─────────────┘ │  │  │
│  │  │                                                                       │  │  │
│  │  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌─────────────┐ │  │  │
│  │  │  │  Evidence    │ │  Compliance  │ │  Analytics   │ │  Reporting  │ │  │  │
│  │  │  │  Collection  │ │  Mapping     │ │  Engine      │ │  Engine     │ │  │  │
│  │  │  │  (Collectors)│ │  (Crosswalk) │ │  (ML/Stats)  │ │  (Grafana)  │ │  │  │
│  │  │  │  3 replicas  │ │  2 replicas  │ │  2 replicas  │ │  2 replicas │ │  │  │
│  │  │  └──────────────┘ └──────────────┘ └──────────────┘ └─────────────┘ │  │  │
│  │  │                                                                       │  │  │
│  │  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌─────────────┐ │  │  │
│  │  │  │  Discovery   │ │  Risk        │ │  Monitoring  │ │  Approval   │ │  │  │
│  │  │  │  Engine      │ │  Assessment  │ │  (OTel)      │ │  Workflow   │ │  │  │
│  │  │  │  (Scanners)  │ │  Engine      │ │  Collector   │ │  (Temporal) │ │  │  │
│  │  │  │  2 replicas  │ │  2 replicas  │ │  2 replicas  │ │  2 replicas │ │  │  │
│  │  │  └──────────────┘ └──────────────┘ └──────────────┘ └─────────────┘ │  │  │
│  │  │                                                                       │  │  │
│  │  └───────────────────────────────────────────────────────────────────────┘  │  │
│  │                                    │                                        │  │
│  │  ┌─────────────────────────────────▼─────────────────────────────────────┐  │  │
│  │  │                      DATA LAYER (StatefulSets)                        │  │  │
│  │  │                                                                       │  │  │
│  │  │  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐         │  │  │
│  │  │  │ PostgreSQL │ │  Redis     │ │  Kafka     │ │  MinIO     │         │  │  │
│  │  │  │ (HA: 3     │ │  (HA: 6    │ │  (HA: 3    │ │  (WORM     │         │  │  │
│  │  │  │  nodes)    │ │  nodes)    │ │  brokers)  │ │  object)   │         │  │  │
│  │  │  └────────────┘ └────────────┘ └────────────┘ └────────────┘         │  │  │
│  │  │  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐         │  │  │
│  │  │  │  Neo4j     │ │  immudb    │ │  Tempo     │ │  Vault     │         │  │  │
│  │  │  │  (HA: 3    │ │  (HA: 3    │ │  (traces)  │ │  (secrets) │         │  │  │
│  │  │  │  nodes)    │ │  nodes)    │ │            │ │            │         │  │  │
│  │  │  └────────────┘ └────────────┘ └────────────┘ └────────────┘         │  │  │
│  │  │                                                                       │  │  │
│  │  └───────────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                           │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
│                                                                                 │
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │                      SERVERLESS / MANAGED LAYER                            │  │
│  │                                                                           │  │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌─────────────┐      │  │
│  │  │  Evidence    │ │  Compliance  │ │  Regulatory  │ │  ML Model   │      │  │
│  │  │  Packaging   │ │  Report      │ │  Change      │ │  Serving    │      │  │
│  │  │  (Lambda/    │ │  Generation  │ │  Monitor     │ │  (SageMaker/│      │  │
│  │  │  Cloud Func) │ │  (Lambda/    │ │  (Event-     │ │  Vertex)    │      │  │
│  │  │              │ │  Cloud Func) │ │  driven)     │ │             │      │  │
│  │  └──────────────┘ └──────────────┘ └──────────────┘ └─────────────┘      │  │
│  │                                                                           │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘

                                    │
                          Cross-Region Replication
                                    │
                                    ▼

┌─────────────────────────────────────────────────────────────────────────────────┐
│                              CLOUD REGION (DR)                                   │
│                                                                                 │
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │                    Kubernetes Cluster (Standby)                            │  │
│  │                                                                           │  │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐            │  │
│  │  │ PostgreSQL │ │  Redis     │ │  Kafka     │ │  MinIO     │            │  │
│  │  │ (Replica)  │ │  (Replica) │ │  (Replica) │ │  (Replica) │            │  │
│  │  └────────────┘ └────────────┘ └────────────┘ └────────────┘            │  │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐                           │  │
│  │  │  Neo4j     │ │  immudb    │ │  Vault     │                           │  │
│  │  │  (Replica) │ │  (Replica) │ │  (Replica) │                           │  │
│  │  └────────────┘ └────────────┘ └────────────┘                           │  │
│  │                                                                           │  │
│  │  [Microservices scaled to 0 — activated on failover]                         │  │
│  │                                                                           │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Environment Tiers

| Tier | Purpose | Availability | RTO | RPO | Data |
|------|---------|-------------|-----|-----|------|
| **Production** | Live governance enforcement | 99.95% | 1 hour | 5 minutes | Full replication |
| **Staging** | Pre-production validation | 99.5% | 4 hours | 1 hour | Anonymized snapshot |
| **Development** | Feature development | 99% | 24 hours | 24 hours | Synthetic data |
| **DR** | Disaster recovery standby | 99.9% | 4 hours | 30 minutes | Cross-region replica |

---

## 3. Containerization Strategy

### 3.1 Docker Image Standards

All GRC_Claw components are built as OCI-compliant container images following these standards:

| Standard | Requirement |
|----------|-------------|
| **Base image** | Distroless or Alpine Linux (minimal attack surface) |
| **Image signing** | Cosign (Sigstore) — all images signed at build time |
| **Vulnerability scanning** | Trivy scan at build; CRITICAL/HIGH vulnerabilities block deployment |
| **SBOM** | Syft-generated SBOM attached to every image |
| **Labels** | OCI annotations: `org.opencontainers.image.version`, `org.opencontainers.image.revision`, `grc.component`, `grc.tier` |
| **Non-root** | All containers run as non-root user (UID 65534) |
| **Read-only root** | Container filesystem is read-only; writes go to mounted volumes |
| **Health checks** | `/healthz` (liveness), `/readyz` (readiness), `/metrics` (Prometheus) |

### 3.2 Dockerfile Pattern

```dockerfile
# Multi-stage build for Policy Definition Service
FROM python:3.12-slim AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM gcr.io/distroless/python3-debian12 AS runtime
COPY --from=builder /install /usr/local
COPY --chown=nonroot:nonroot src/ /app/
WORKDIR /app
USER 65534:65534
EXPOSE 8080
HEALTHCHECK --interval=10s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/healthz')"
ENTRYPOINT ["python", "-m", "grc_claw.policy_service"]
```

### 3.3 Image Registry

| Registry | Purpose | Retention |
|----------|---------|-----------|
| **Primary** (ECR/GCR/ACR) | Production images | Indefinite (immutable tags) |
| **Staging** | Pre-production validation | 30 days |
| **Dev** | Development builds | 7 days |
| **Public** (ghcr.io) | Open-source release images | Indefinite (semver tags) |

### 3.4 Container Resource Standards

| Component | CPU Request | CPU Limit | Memory Request | Memory Limit | Replicas (min) |
|-----------|-------------|-----------|----------------|--------------|-----------------|
| Policy Definition API | 500m | 2000m | 512Mi | 2Gi | 3 |
| PDP Service (OPA) | 1000m | 4000m | 1Gi | 4Gi | 3 |
| PEP Gateway | 500m | 2000m | 512Mi | 2Gi | 3 |
| Agent Identity (SPIRE) | 250m | 1000m | 256Mi | 1Gi | 3 |
| Evidence Collector | 500m | 2000m | 512Mi | 2Gi | 3 |
| Compliance Mapping | 250m | 1000m | 256Mi | 1Gi | 2 |
| Analytics Engine | 1000m | 4000m | 2Gi | 8Gi | 2 |
| Reporting Engine | 250m | 1000m | 256Mi | 1Gi | 2 |
| Discovery Engine | 250m | 1000m | 256Mi | 1Gi | 2 |
| Risk Assessment | 500m | 2000m | 512Mi | 2Gi | 2 |
| OTel Collector | 250m | 1000m | 256Mi | 1Gi | 2 |
| Approval Workflow (Temporal) | 500m | 2000m | 512Mi | 2Gi | 2 |

---

## 4. Kubernetes Architecture

### 4.1 Namespace Strategy

```
grc-claw/                          # Parent namespace (Istio enabled)
├── grc-claw-control-plane/        # PDP, PEP, Policy API, Agent Identity
├── grc-claw-evidence/             # Evidence collection, normalization, storage
├── grc-claw-analytics/           # Analytics engine, risk scoring, ML
├── grc-claw-observability/       # OTel, Prometheus, Grafana, Loki, Tempo
├── grc-claw-data/                 # PostgreSQL, Redis, Kafka, MinIO, Neo4j, immudb, Vault
├── grc-claw-serverless/           # Knative services (evidence packaging, report generation)
└── grc-claw-ingress/              # Ingress controllers, API gateway
```

### 4.2 Deployment Patterns

#### 4.2.1 Stateless Microservices (Deployments)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: pdp-service
  namespace: grc-claw-control-plane
  labels:
    app: pdp-service
    grc.component: pdp
    grc.tier: control-plane
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: pdp-service
  template:
    metadata:
      labels:
        app: pdp-service
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8080"
        prometheus.io/path: "/metrics"
    spec:
      serviceAccountName: pdp-service
      securityContext:
        runAsNonRoot: true
        runAsUser: 65534
        fsGroup: 65534
      containers:
        - name: pdp
          image: ghcr.io/grc-claw/pdp-service:v1.2.0
          imagePullPolicy: Always
          ports:
            - containerPort: 8080
              name: http
            - containerPort: 9090
              name: grpc
          resources:
            requests:
              cpu: 1000m
              memory: 1Gi
            limits:
              cpu: 4000m
              memory: 4Gi
          livenessProbe:
            httpGet:
              path: /healthz
              port: 8080
            initialDelaySeconds: 10
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /readyz
              port: 8080
            initialDelaySeconds: 5
            periodSeconds: 5
          securityContext:
            readOnlyRootFilesystem: true
            allowPrivilegeEscalation: false
            capabilities:
              drop: ["ALL"]
          volumeMounts:
            - name: tmp
              mountPath: /tmp
            - name: opa-policies
              mountPath: /policies
              readOnly: true
      volumes:
        - name: tmp
          emptyDir: {}
        - name: opa-policies
          configMap:
            name: opa-policy-bundles
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
            - weight: 100
              podAffinityTerm:
                labelSelector:
                  matchLabels:
                    app: pdp-service
                topologyKey: topology.kubernetes.io/zone
      topologySpreadConstraints:
        - maxSkew: 1
          topologyKey: topology.kubernetes.io/zone
          whenUnsatisfiable: DoNotSchedule
          labelSelector:
            matchLabels:
              app: pdp-service
```

#### 4.2.2 Stateful Data Services (StatefulSets)

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgresql
  namespace: grc-claw-data
spec:
  serviceName: postgresql
  replicas: 3
  selector:
    matchLabels:
      app: postgresql
  template:
    metadata:
      labels:
        app: postgresql
    spec:
      containers:
        - name: postgresql
          image: ghcr.io/grc-claw/postgresql:16.4
          ports:
            - containerPort: 5432
          env:
            - name: POSTGRES_DB
              value: grc_claw
            - name: POSTGRES_USER
              valueFrom:
                secretKeyRef:
                  name: db-credentials
                  key: username
            - name: POSTGRES_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: db-credentials
                  key: password
            - name: PGDATA
              value: /var/lib/postgresql/data/pgdata
          volumeMounts:
            - name: data
              mountPath: /var/lib/postgresql/data
          resources:
            requests:
              cpu: 2000m
              memory: 4Gi
            limits:
              cpu: 8000m
              memory: 16Gi
  volumeClaimTemplates:
    - metadata:
        name: data
      spec:
        storageClassName: premium-rwo
        accessModes: ["ReadWriteOnce"]
        resources:
          requests:
            storage: 500Gi
```

### 4.3 Pod Disruption Budgets

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: pdp-service-pdb
  namespace: grc-claw-control-plane
spec:
  minAvailable: 2
  selector:
    matchLabels:
      app: pdp-service
---
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: postgresql-pdb
  namespace: grc-claw-data
spec:
  minAvailable: 2
  selector:
    matchLabels:
      app: postgresql
```

### 4.4 Network Policies

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: pdp-service-netpol
  namespace: grc-claw-control-plane
spec:
  podSelector:
    matchLabels:
      app: pdp-service
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
        - podSelector:
            matchLabels:
              app: pep-gateway
        - podSelector:
            matchLabels:
              app: policy-api
      ports:
        - protocol: TCP
          port: 8080
        - protocol: TCP
          port: 9090
  egress:
    - to:
        - podSelector:
            matchLabels:
              app: postgresql
      ports:
        - protocol: TCP
          port: 5432
    - to:
        - podSelector:
            matchLabels:
              app: redis
      ports:
        - protocol: TCP
          port: 6379
```

### 4.5 Service Mesh Configuration (Istio)

```yaml
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: pdp-service-mtls
  namespace: grc-claw-control-plane
spec:
  host: pdp-service
  trafficPolicy:
    tls:
      mode: ISTIO_MUTUAL
    connectionPool:
      tcp:
        maxConnections: 100
      http:
        http1MaxPendingRequests: 100
        http2MaxRequests: 1000
    outlierDetection:
      consecutive5xxErrors: 5
      interval: 30s
      baseEjectionTime: 30s
      maxEjectionPercent: 50
---
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: pdp-service-routing
  namespace: grc-claw-control-plane
spec:
  hosts:
    - pdp-service
  http:
    - match:
        - headers:
            x-canary:
              exact: "true"
      route:
        - destination:
            host: pdp-service
            subset: canary
          weight: 10
        - destination:
            host: pdp-service
            subset: stable
          weight: 90
    - route:
        - destination:
            host: pdp-service
            subset: stable
```

---

## 5. Cloud-Native Patterns

### 5.1 Microservices Architecture

GRC_Claw is deployed as a set of loosely coupled microservices, each with a single responsibility:

| Service | Responsibility | Scaling Trigger | Stateless |
|---------|---------------|-----------------|-----------|
| **Policy Definition API** | CRUD, versioning, dependency graph for policies | CPU > 70% | Yes |
| **PDP Service** | Evaluate Cedar/Rego policies, return decisions | p99 latency > 15ms | Yes |
| **PEP Gateway** | Intercept agent actions, enforce decisions | p99 latency > 20ms | Yes |
| **Agent Identity** | SVID issuance, trust scoring, registry | CPU > 70% | Yes |
| **Evidence Collector** | Collect, normalize, validate evidence | Queue depth > 10K | Yes |
| **Compliance Mapping** | Crosswalk engine, gap analysis | CPU > 70% | Yes |
| **Analytics Engine** | Risk scoring, anomaly detection, drift | CPU > 70% | Yes |
| **Reporting Engine** | Dashboard data, report generation | Request rate > 5K/s | Yes |
| **Discovery Engine** | AI asset scanning, inventory | Schedule-based | Yes |
| **Risk Assessment** | Multi-dimensional risk scoring | CPU > 70% | Yes |
| **Approval Workflow** | Human-in-the-loop approval routing | Queue depth > 100 | Yes (Temporal) |

**Inter-service communication:**
- **Synchronous:** gRPC (internal), REST/HTTPS (external)
- **Asynchronous:** Apache Kafka (event-driven)
- **Service mesh:** Istio for mTLS, traffic management, observability

### 5.2 Serverless Components

> **Note:** For detailed Knative service definitions, event-driven patterns, cold start mitigation, and serverless security, see **Section 19: Serverless Components**.

Event-driven and bursty workloads use serverless functions (Knative on Kubernetes or cloud-managed equivalents):

| Component | Trigger | Platform | Use Case |
|-----------|---------|----------|----------|
| **Evidence Packaging** | Scheduled (monthly/quarterly) | Knative / Lambda | Generate audit evidence packages |
| **Report Generation** | On-demand (auditor request) | Knative / Lambda | Generate compliance reports |
| **Regulatory Change Monitor** | Event-driven (RSS/API poll) | Knative / Cloud Function | Detect regulatory changes, trigger impact analysis |
| **Compliance Score Recalculation** | Event-driven (new evidence) | Knative / Lambda | Recalculate compliance scores as evidence lands |
| **Anomaly Response** | Event-driven (anomaly detected) | Knative / Lambda | Automated response to detected anomalies |
| **Data Retention Enforcement** | Scheduled (daily) | Knative / Lambda | Enforce retention policies, archive expired data |

### 5.3 Event-Driven Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Enforcement │     │  Evidence   │     │  Compliance │     │  Analytics  │
│  Decision    │────▶│  Collected  │────▶│  Score      │────▶│  Risk       │
│  Event       │     │  Event      │     │  Updated    │     │  Updated    │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
       │                   │                   │                   │
       └───────────────────┴───────────────────┴───────────────────┘
                           │
                    ┌──────▼──────┐
                    │    Kafka    │
                    │   Cluster   │
                    │             │
                    │ Topics:     │
                    │ • decisions │
                    │ • evidence  │
                    │ • policy-   │
                    │   changes   │
                    │ • agent-    │
                    │   lifecycle │
                    │ • compliance│
                    │   -updates  │
                    │ • audit-    │
                    │   events    │
                    │ • anomaly-  │
                    │   alerts    │
                    └─────────────┘
```

**Kafka Topic Configuration:**

| Topic | Partitions | Retention | Replication Factor | Consumers |
|-------|-----------|-----------|-------------------|-----------|
| `decisions` | 12 | 7 days | 3 | Evidence, Analytics, Audit |
| `evidence.collected` | 12 | 7 days | 3 | Compliance, Analytics, Reporting |
| `policy.changes` | 6 | 30 days | 3 | PDP, PEP, Cache invalidation |
| `agent.lifecycle` | 6 | 30 days | 3 | Identity, Discovery, Analytics |
| `compliance.updates` | 6 | 7 days | 3 | Reporting, Dashboard |
| `audit.events` | 12 | 90 days | 3 | immudb, Evidence store |
| `anomaly.alerts` | 6 | 7 days | 3 | Response engine, PagerDuty |

### 5.4 Sidecar Pattern

Each microservice pod includes sidecar containers:

| Sidecar | Purpose | Technology |
|---------|---------|------------|
| **Service mesh proxy** | mTLS, traffic management, telemetry | Istio Envoy |
| **Log shipper** | Ship logs to Loki/Elastic | Fluent Bit |
| **Secret agent** | Fetch secrets from Vault | Vault Agent |
| **OTel collector** | Trace/metric collection | OpenTelemetry Collector |

---

## 6. Scaling Strategies

### 6.1 Horizontal Pod Autoscaling (HPA)

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: pdp-service-hpa
  namespace: grc-claw-control-plane
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: pdp-service
  minReplicas: 3
  maxReplicas: 20
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
    - type: Pods
      pods:
        metric:
          name: grc_enforcement_decision_duration_seconds
        target:
          type: AverageValue
          averageValue: 15m
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
        - type: Percent
          value: 100
          periodSeconds: 60
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
        - type: Percent
          value: 10
          periodSeconds: 60
```

### 6.2 Vertical Pod Autoscaling (VPA)

Used for stateful services where horizontal scaling is not appropriate:

```yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: postgresql-vpa
  namespace: grc-claw-data
spec:
  targetRef:
    apiVersion: apps/v1
    kind: StatefulSet
    name: postgresql
  updatePolicy:
    updateMode: "Auto"
  resourcePolicy:
    containerPolicies:
      - containerName: postgresql
        minAllowed:
          cpu: 1000m
          memory: 2Gi
        maxAllowed:
          cpu: 8000m
          memory: 32Gi
        controlledResources: ["cpu", "memory"]
```

### 6.3 Cluster Autoscaling

```yaml
apiVersion: karpenter.sh/v1beta1
kind: NodePool
metadata:
  name: grc-claw-compute
spec:
  template:
    spec:
      requirements:
        - key: karpenter.sh/capacity-type
          operator: In
          values: ["spot", "on-demand"]
        - key: node.kubernetes.io/instance-type
          operator: In
          values: ["m6i.2xlarge", "m6i.4xlarge", "c6i.2xlarge"]
        - key: topology.kubernetes.io/zone
          operator: In
          values: ["us-east-1a", "us-east-1b", "us-east-1c"]
      nodeClassRef:
        name: grc-claw-node-class
  limits:
    cpu: 1000
    memory: 4000Gi
  disruption:
    consolidationPolicy: WhenUnderutilized
    expireAfter: 720h
```

### 6.4 Scaling Policies by Component

| Component | Scaling Strategy | Min | Max | Trigger | Cooldown |
|-----------|-----------------|-----|-----|---------|----------|
| PDP Service | HPA (CPU + latency) | 3 | 20 | CPU > 70% or p99 > 15ms | 60s up / 300s down |
| PEP Gateway | HPA (CPU + latency) | 3 | 20 | CPU > 70% or p99 > 20ms | 60s up / 300s down |
| Policy API | HPA (CPU) | 3 | 10 | CPU > 70% | 60s up / 300s down |
| Evidence Collector | HPA (queue depth) | 3 | 15 | Queue > 10K | 60s up / 300s down |
| Analytics Engine | HPA (CPU) | 2 | 8 | CPU > 70% | 120s up / 600s down |
| PostgreSQL | VPA + read replicas | 3 | 5 | N/A (manual) | N/A |
| Redis | HPA (CPU) | 6 | 12 | CPU > 70% | 120s up / 600s down |
| Kafka | Partition scaling | 3 | 6 | N/A (manual) | N/A |

### 6.5 Load Testing & Capacity Validation

| Test | Frequency | Tool | Success Criteria |
|------|-----------|------|------------------|
| Load test | Weekly | k6 / Locust | p99 < 10ms at 10K dec/s |
| Stress test | Monthly | k6 / Locust | Graceful degradation at 25K dec/s |
| Soak test | Monthly | k6 | 72h at 10K dec/s, no leaks |
| Chaos test | Monthly | Litmus / Chaos Mesh | Recovery < 5min on component failure |
| Failover test | Quarterly | Manual / Automated | RTO < 4h, RPO < 5min |

---

## 7. High Availability

### 7.1 Availability Targets

| Tier | Availability | Max Downtime/Year | Components |
|------|-------------|-------------------|------------|
| **Critical** | 99.99% | 52.6 minutes | PDP, PEP, Policy API, Agent Identity |
| **Standard** | 99.95% | 4.38 hours | Evidence, Compliance, Analytics, Reporting |
| **Supporting** | 99.9% | 8.76 hours | Discovery, Risk Assessment, Approval Workflow |

### 7.2 Multi-Zone Deployment

All critical components are distributed across at least 3 availability zones:

```
┌─────────────────────────────────────────────────────────────┐
│                        Region                                │
│                                                             │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐   │
│  │   Zone A      │  │   Zone B      │  │   Zone C      │   │
│  │               │  │               │  │               │   │
│  │  PDP-1        │  │  PDP-2        │  │  PDP-3        │   │
│  │  PEP-1        │  │  PEP-2        │  │  PEP-3        │   │
│  │  Policy-1     │  │  Policy-2     │  │  Policy-3     │   │
│  │  PostgreSQL-1 │  │  PostgreSQL-2 │  │  PostgreSQL-3 │   │
│  │  Redis-1      │  │  Redis-2      │  │  Redis-3      │   │
│  │  Kafka-1      │  │  Kafka-2      │  │  Kafka-3      │   │
│  └───────────────┘  └───────────────┘  └───────────────┘   │
│                                                             │
│  [Load Balancer — cross-zone traffic distribution]          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 7.3 Database High Availability

#### PostgreSQL (Patroni + etcd)

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgresql
  namespace: grc-claw-data
spec:
  replicas: 3
  serviceName: postgresql
  template:
    spec:
      containers:
        - name: patroni
          image: ghcr.io/grc-claw/patroni:16.4
          env:
            - name: PATRONI_ETCD3_HOSTS
              value: "etcd-0:2379,etcd-1:2379,etcd-2:2379"
            - name: PATRONI_SCOPE
              value: grc-claw-db
            - name: PATRONI_NAME
              valueFrom:
                fieldRef:
                  fieldPath: metadata.name
          ports:
            - containerPort: 5432
            - containerPort: 8008  # Patroni REST API
```

**Failover behavior:**
- Automatic failover via Patroni leader election
- Failover time: < 30 seconds
- Replication: Synchronous for critical tables, asynchronous for analytics
- Connection pooling: PgBouncer (transaction mode)

#### Redis (Cluster Mode)

- 6 nodes (3 masters + 3 replicas) across 3 zones
- Automatic failover via Redis Sentinel
- Persistence: AOF (append-only file) + RDB snapshots
- Max memory policy: `allkeys-lru` for cache, `noeviction` for session data

#### Kafka

- 3 brokers across 3 zones
- Replication factor: 3 for all topics
- Min ISR: 2
- Unclean leader election: disabled

### 7.4 Service-Level Resilience

| Pattern | Implementation | Components |
|---------|---------------|------------|
| **Circuit breaker** | Istio outlier detection | All service-to-service calls |
| **Retry with backoff** | Istio retry policy | Idempotent operations only |
| **Timeout** | Istio timeout + application-level | All external calls |
| **Bulkhead** | Separate connection pools per dependency | Database, Redis, Kafka |
| **Rate limiting** | API Gateway (Kong) + Istio | All ingress traffic |
| **Graceful degradation** | Feature flags + fallback logic | Analytics, Reporting |
| **Health-based routing** | Kubernetes readiness probes | All services |

### 7.5 Health Check Strategy

| Check | Endpoint | Interval | Timeout | Failure Threshold | Action |
|-------|----------|----------|---------|-------------------|--------|
| Liveness | `/healthz` | 10s | 5s | 3 | Restart container |
| Readiness | `/readyz` | 5s | 3s | 3 | Remove from service |
| Startup | `/startz` | 5s | 30s | 6 | Restart container |
| Deep health | `/deepz` | 60s | 10s | 3 | Alert + investigate |

---

## 8. Disaster Recovery

### 8.1 DR Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PRIMARY REGION                                     │
│                                                                             │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐                   │
│  │ Application │     │  Data       │     │  Config     │                   │
│  │ Services    │     │  Services   │     │  (GitOps)   │                   │
│  │             │     │             │     │             │                   │
│  │ • PDP       │     │ • PostgreSQL│     │ • Helm      │                   │
│  │ • PEP       │     │ • Redis     │     │   charts    │                   │
│  │ • Policy    │     │ • Kafka     │     │ • Kustomize │                   │
│  │ • Evidence  │     │ • MinIO     │     │ • ArgoCD    │                   │
│  │ • Analytics │     │ • Neo4j     │     │             │                   │
│  └──────┬──────┘     └──────┬──────┘     └──────┬──────┘                   │
│         │                   │                   │                           │
│         └───────────────────┼───────────────────┘                           │
│                             │                                               │
│                    ┌────────▼────────┐                                      │
│                    │  Replication    │                                      │
│                    │                 │                                      │
│                    │ • PostgreSQL:   │                                      │
│                    │   Streaming     │                                      │
│                    │   (sync)        │                                      │
│                    │ • Redis:        │                                      │
│                    │   Sentinel      │                                      │
│                    │   (async)       │                                      │
│                    │ • Kafka:        │                                      │
│                    │   MirrorMaker2  │                                      │
│                    │   (async)       │                                      │
│                    │ • MinIO:        │                                      │
│                    │   Bucket        │                                      │
│                    │   replication   │                                      │
│                    │   (async)       │                                      │
│                    │ • immudb:       │                                      │
│                    │   Read replica  │                                      │
│                    │   (async)       │                                      │
│                    └────────┬────────┘                                      │
│                             │                                               │
└─────────────────────────────┼───────────────────────────────────────────────┘
                              │
                    Cross-Region Replication
                              │
┌─────────────────────────────┼───────────────────────────────────────────────┐
│                             │                                               │
│                           DR REGION                                         │
│                             │                                               │
│                    ┌────────▼────────┐                                      │
│                    │  Standby        │                                      │
│                    │                 │                                      │
│                    │ • PostgreSQL    │                                      │
│                    │   (replica)     │                                      │
│                    │ • Redis         │                                      │
│                    │   (replica)     │                                      │
│                    │ • Kafka         │                                      │
│                    │   (replica)     │                                      │
│                    │ • MinIO         │                                      │
│                    │   (replica)     │                                      │
│                    │ • immudb        │                                      │
│                    │   (replica)     │                                      │
│                    │                 │                                      │
│                    │ [K8s cluster    │                                      │
│                    │  scaled to 0    │                                      │
│                    │  services]      │                                      │
│                    └─────────────────┘                                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 8.2 Recovery Objectives

| Data Store | RPO | RTO | Replication | Failover |
|-----------|-----|-----|-------------|----------|
| PostgreSQL (policies, enforcement) | ≤ 5 minutes | ≤ 1 hour | Synchronous streaming | Automatic (Patroni) |
| PostgreSQL (analytics) | ≤ 30 minutes | ≤ 4 hours | Asynchronous streaming | Manual |
| Redis (cache, sessions) | ≤ 1 minute | ≤ 5 minutes | Sentinel async | Automatic |
| Kafka (events) | ≤ 1 second | ≤ 15 minutes | MirrorMaker2 | Automatic |
| MinIO (WORM evidence) | ≤ 30 minutes | ≤ 4 hours | Bucket replication | Manual |
| Neo4j (graph) | ≤ 30 minutes | ≤ 4 hours | Causal cluster | Automatic |
| immudb (audit) | ≤ 5 minutes | ≤ 1 hour | Read replica | Manual |
| Vault (secrets) | ≤ 1 minute | ≤ 15 minutes | Performance replica | Automatic |

### 8.3 Backup Strategy

| Data Store | Backup Type | Frequency | Retention | Storage | Encryption |
|-----------|------------|-----------|-----------|---------|------------|
| PostgreSQL | Full (pgBackRest) | Daily | 30 days | S3/GCS (cross-region) | AES-256 |
| PostgreSQL | WAL archiving | Continuous | 7 days | S3/GCS (cross-region) | AES-256 |
| Redis | RDB snapshot | Every 6 hours | 7 days | S3/GCS | AES-256 |
| Kafka | Topic snapshot | Daily | 14 days | S3/GCS | AES-256 |
| MinIO | Object versioning | Continuous | Indefinite | Cross-region bucket | SSE-S3 |
| Neo4j | Full (neo4j-admin) | Daily | 30 days | S3/GCS | AES-256 |
| immudb | Full | Daily | 90 days | S3/GCS | AES-256 |
| Vault | Raft snapshot | Daily | 30 days | S3/GCS | AES-256 |
| Kubernetes | etcd snapshot | Every 6 hours | 30 days | S3/GCS | AES-256 |
| GitOps | Git repository | Continuous | Indefinite | GitHub/GitLab | N/A |

### 8.4 DR Failover Procedures

#### Scenario 1: Single Component Failure (Automatic)

```
1. Kubernetes detects failure (liveness probe fails)
2. Pod rescheduled to healthy node (< 2 minutes)
3. Istio reroutes traffic to healthy instances (< 5 seconds)
4. Alert fired to on-call engineer
5. Post-incident review scheduled
```

#### Scenario 2: Zone Failure (Automatic)

```
1. Load balancer detects zone failure
2. Traffic routed to remaining zones (< 30 seconds)
3. HPA scales up replicas in remaining zones (< 5 minutes)
4. Patroni promotes PostgreSQL replica in healthy zone (< 30 seconds)
5. Redis Sentinel promotes replica (< 10 seconds)
6. Kafka reassigns partitions (< 2 minutes)
7. Alert fired to on-call engineer
```

#### Scenario 3: Region Failure (Manual)

```
1. On-call engineer declares region failure
2. ArgoCD promotes DR cluster to production (< 15 minutes)
3. PostgreSQL replica promoted to primary (< 5 minutes)
4. Redis replica promoted (< 2 minutes)
5. Kafka MirrorMaker2 reversed (< 5 minutes)
6. MinIO bucket replication reversed (< 10 minutes)
7. Vault performance replica promoted (< 5 minutes)
8. DNS updated to DR region (< 5 minutes)
9. Microservices scaled up in DR region (< 15 minutes)
10. Total RTO: < 4 hours
```

### 8.5 DR Testing

| Test | Frequency | Scope | Success Criteria |
|------|-----------|-------|------------------|
| **Component failure** | Weekly | Kill single pod | Recovery < 2 min, zero data loss |
| **Zone failure** | Monthly | Simulate zone loss | Recovery < 15 min, RPO < 5 min |
| **Region failure** | Quarterly | Full region failover | RTO < 4 hours, RPO < 30 min |
| **Backup restore** | Monthly | Restore to staging | Data integrity verified |
| **Chaos engineering** | Monthly | Random component kills | Graceful degradation |

---

## 9. Observability & Operations

### 9.1 Monitoring Stack

| Layer | Tool | Purpose |
|-------|------|---------|
| **Metrics** | Prometheus + Grafana | System and application metrics |
| **Logs** | Loki / Elasticsearch | Centralized log aggregation |
| **Traces** | Tempo / Jaeger | Distributed tracing |
| **Profiling** | Pyroscope / pprof | Continuous profiling |
| **Alerting** | Alertmanager + PagerDuty | Incident notification |
| **Dashboards** | Grafana | Operational dashboards |
| **SLOs** | Sloth / Pyrra | SLO monitoring and error budgets |

### 9.2 Key Operational Dashboards

| Dashboard | Audience | Key Metrics |
|-----------|----------|-------------|
| **Executive** | C-Suite, Board | Compliance score, risk posture, incident count |
| **Operations** | SRE, Platform | Availability, latency, error rate, saturation |
| **Enforcement** | Governance team | Decision rate, decision distribution, policy violations |
| **Evidence** | Compliance, Audit | Evidence freshness, verification levels, coverage |
| **Infrastructure** | Platform | CPU, memory, disk, network, pod health |
| **DR** | SRE, DR team | Replication lag, backup status, failover readiness |

### 9.3 Alerting Severity Matrix

| Severity | Condition | Response Time | Escalation |
|----------|-----------|---------------|------------|
| **P1 — Critical** | Enforcement down, data loss risk, security breach | 5 minutes | Page on-call → Manager → Director |
| **P2 — High** | p99 latency > 50ms, error rate > 1%, replication lag > 30s | 15 minutes | Page on-call → Manager |
| **P3 — Medium** | p99 latency > 20ms, disk > 80%, backup failure | 1 hour | Slack alert → On-call |
| **P4 — Low** | Disk > 70%, certificate expiry < 30 days, minor config drift | 24 hours | Slack alert → Team |

### 9.4 Log Management

| Log Type | Destination | Retention | Format |
|----------|-------------|-----------|--------|
| Application logs | Loki | 30 days | JSON |
| Audit logs | immudb | 7 years | JSON (hash-chained) |
| Access logs | Loki | 90 days | JSON |
| System logs | Loki | 30 days | JSON |
| Security logs | SIEM (Splunk/Elastic) | 7 years | CEF/JSON |
| Performance traces | Tempo | 14 days | OTLP |

### 9.5 SLO Definitions

| Service | SLO | Error Budget | Measurement |
|---------|-----|-------------|-------------|
| PDP Service | 99.95% availability | 21.9 min/month | Uptime / total time |
| PEP Gateway | 99.95% availability | 21.9 min/month | Uptime / total time |
| Policy API | 99.9% availability | 43.8 min/month | Uptime / total time |
| Evidence Collection | 99.9% availability | 43.8 min/month | Successful writes / total writes |
| Overall Platform | 99.9% availability | 43.8 min/month | Weighted average |

---

## 10. Security in Deployment

### 10.1 Secret Management

```
┌─────────────────────────────────────────────────────────────┐
│                    HashiCorp Vault                            │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ PKI         │  │ KV v2       │  │ Database    │         │
│  │ (mTLS certs)│  │ (app secrets)│  │ (dynamic    │         │
│  │             │  │             │  │  credentials)│         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ Transit     │  │ PKI         │  │ AWS/GCP     │         │
│  │ (encryption)│  │ (SSH certs) │  │ (cloud auth)│         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Secret rotation schedule:**

| Secret Type | Rotation Frequency | Method |
|-------------|-------------------|--------|
| mTLS certificates | 24 hours | Vault PKI + cert-manager |
| API tokens | 7 days | Vault dynamic secrets |
| Database credentials | 30 days | Vault database secrets engine |
| Encryption keys (DEK) | 90 days | Vault transit engine |
| Signing keys | 1 year | HSM-backed, manual rotation |
| Vault tokens | 24 hours | Kubernetes auth method |

### 10.2 Network Security

| Layer | Control | Implementation |
|-------|---------|---------------|
| **Edge** | WAF + DDoS protection | AWS Shield / Cloud Armor |
| **Ingress** | TLS 1.3, mTLS | cert-manager + Istio |
| **Service mesh** | mTLS, authorization | Istio PeerAuthorization |
| **Network policies** | Micro-segmentation | Kubernetes NetworkPolicy |
| **Egress** | Egress filtering | Istio Egress Gateway |
| **Database** | Private subnets, no public IP | Cloud provider VPC |

### 10.3 Compliance in Deployment

| Control | Implementation |
|---------|---------------|
| **Image scanning** | Trivy in CI/CD; admission control via OPA/Gatekeeper |
| **Runtime security** | Falco for threat detection |
| **Pod security** | Pod Security Standards (restricted) |
| **Audit logging** | Kubernetes audit logs → SIEM |
| **Encryption** | AES-256 at rest, TLS 1.3 in transit |
| **Access control** | RBAC + ABAC via OPA |

---

## 11. GitOps & Deployment Pipeline

> **Note:** This section provides a high-level overview. For detailed ArgoCD configuration, ApplicationSet patterns, sync waves, rollback strategies, and GitOps security controls, see **Section 15: GitOps Pipeline with ArgoCD**.

### 11.1 GitOps Workflow

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  Code    │───▶│  CI      │───▶│  Image   │───▶│  CD      │───▶│  Prod    │
│  Commit  │    │  Build   │    │  Registry│    │  Deploy  │    │  Cluster │
│          │    │          │    │          │    │          │    │          │
│ GitHub   │    │ GitHub   │    │ ghcr.io  │    │ ArgoCD   │    │ K8s      │
│          │    │ Actions  │    │          │    │          │    │          │
└──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘
                     │                               │
                     ▼                               ▼
              ┌──────────┐                    ┌──────────┐
              │  Tests   │                    │  Git    │
              │  • Unit  │                    │  Repo   │
              │  • Integ │                    │  (config)│
              │  • SAST  │                    │          │
              │  • DAST  │                    │  Helm    │
              │  • Perf  │                    │  Charts  │
              └──────────┘                    └──────────┘
```

### 11.2 Deployment Strategies

> **Note:** For detailed Argo Rollouts configuration, canary analysis templates, blue-green deployment, feature flags, and traffic splitting, see **Section 16: Progressive Delivery**.

| Strategy | Use Case | Components |
|----------|----------|------------|
| **Rolling update** | Stateless services | PDP, PEP, Policy API, Evidence |
| **Blue/green** | Critical services | Policy API, Agent Identity |
| **Canary** | Risky changes | All services (10% → 50% → 100%) |
| **Recreate** | Stateful services | PostgreSQL, Redis, Kafka (maintenance windows) |

### 11.3 Helm Chart Structure

```
grc-claw/
├── Chart.yaml
├── values/
│   ├── values-production.yaml
│   ├── values-staging.yaml
│   └── values-development.yaml
├── templates/
│   ├── _helpers.tpl
│   ├── namespace.yaml
│   ├── network-policies.yaml
│   ├── pod-disruption-budgets.yaml
│   ├── control-plane/
│   │   ├── policy-api/
│   │   │   ├── deployment.yaml
│   │   │   ├── service.yaml
│   │   │   ├── hpa.yaml
│   │   │   └── configmap.yaml
│   │   ├── pdp-service/
│   │   ├── pep-gateway/
│   │   └── agent-identity/
│   ├── evidence/
│   │   ├── collector/
│   │   ├── normalizer/
│   │   └── validator/
│   ├── analytics/
│   │   ├── engine/
│   │   └── reporting/
│   ├── observability/
│   │   ├── otel-collector/
│   │   ├── prometheus/
│   │   ├── grafana/
│   │   └── loki/
│   └── data/
│       ├── postgresql/
│       ├── redis/
│       ├── kafka/
│       ├── minio/
│       ├── neo4j/
│       ├── immudb/
│       └── vault/
└── charts/
    ├── postgresql-ha/
    ├── redis-cluster/
    ├── kafka/
    ├── minio/
    ├── neo4j-cluster/
    └── vault/
```

---

## 12. Capacity Planning

### 12.1 Resource Allocation by Environment

| Resource | Production | Staging | Development |
|----------|-----------|---------|-------------|
| **Compute (vCPU)** | 200 | 60 | 20 |
| **Memory (GB)** | 800 | 240 | 80 |
| **Storage (TB)** | 50 | 15 | 5 |
| **Nodes** | 30-50 | 10-15 | 5-8 |
| **Monthly cost (est.)** | $50K-100K | $15K-30K | $5K-10K |

### 12.2 Growth Projections

| Metric | Current | 6 Months | 12 Months | 24 Months |
|--------|---------|----------|-----------|-----------|
| Registered agents | 1,000 | 2,500 | 5,000 | 10,000 |
| Decisions/second | 10,000 | 25,000 | 50,000 | 100,000 |
| Evidence items/day | 10M | 25M | 50M | 100M |
| Audit trail entries | 500M | 1.5B | 3B | 6B |
| Storage (audit trail) | 500 GB | 1.2 TB | 2.5 TB | 5 TB |
| PDP replicas | 3 | 6 | 12 | 24 |
| PEP replicas | 3 | 6 | 12 | 24 |
| Evidence collectors | 3 | 4 | 8 | 16 |

### 12.3 Cost Optimization

> **Note:** For detailed FinOps framework, right-sizing automation, spot instance management, storage tiering, network cost optimization, cost allocation, and continuous optimization practices, see **Section 20: Cost Optimization Strategies**.

| Strategy | Implementation | Savings |
|----------|---------------|---------|
| **Spot instances** | Use spot for stateless workloads | 60-70% compute |
| **Right-sizing** | VPA recommendations | 20-30% waste reduction |
| **Storage tiering** | Move cold data to S3 Glacier | 50-80% storage |
| **Reserved instances** | 1-year commitment for baseline | 30-40% compute |
| **Autoscaling** | Scale to zero for dev/test | 50-70% non-prod |

---

## 13. Operational Runbooks

### 13.1 Common Operational Procedures

| Procedure | Frequency | Tool | Runbook |
|-----------|-----------|------|---------|
| **Certificate rotation** | 24 hours | cert-manager | `runbooks/cert-rotation.md` |
| **Database failover test** | Monthly | Patroni | `runbooks/db-failover.md` |
| **Backup verification** | Daily | Automated | `runbooks/backup-verify.md` |
| **DR failover drill** | Quarterly | ArgoCD | `runbooks/dr-failover.md` |
| **Security patching** | Weekly | Renovate + ArgoCD | `runbooks/security-patch.md` |
| **Capacity review** | Monthly | Prometheus + Grafana | `runbooks/capacity-review.md` |
| **Log rotation** | Daily | Loki | `runbooks/log-rotation.md` |
| **Secret rotation** | Per schedule | Vault | `runbooks/secret-rotation.md` |

### 13.2 Incident Response

| Severity | Response | Escalation | Communication |
|----------|----------|------------|---------------|
| **P1** | Page on-call immediately | On-call → Manager → Director → VP | Status page + Slack #incidents |
| **P2** | Page on-call within 15 min | On-call → Manager | Slack #incidents |
| **P3** | Slack alert, next business day | On-call | Slack #alerts |
| **P4** | Slack alert, weekly review | Team | Slack #alerts |

---

## 14. Deployment Checklist

### 14.1 Pre-Deployment

- [ ] All container images built, scanned, and signed
- [ ] SBOM generated and archived
- [ ] Helm charts linted and validated
- [ ] Kubernetes manifests validated (kubeval/kustomize)
- [ ] Network policies defined
- [ ] Pod security policies applied
- [ ] Resource quotas and limits set
- [ ] Secrets configured in Vault
- [ ] Database migrations tested
- [ ] Backup/restore tested
- [ ] DR failover tested
- [ ] Monitoring dashboards configured
- [ ] Alerting rules tested
- [ ] Runbooks updated
- [ ] On-call schedule confirmed
- [ ] ArgoCD ApplicationSet configured for all target clusters
- [ ] Argo Rollouts canary/blue-green strategy defined
- [ ] Feature flags configured and tested
- [ ] Multi-cloud failover tested (if applicable)
- [ ] Edge node provisioning tested (if applicable)
- [ ] Knative services deployed and scale-to-zero verified
- [ ] Cost allocation tags and budgets configured

### 14.2 Deployment

- [ ] GitOps sync initiated (ArgoCD)
- [ ] Canary deployment (5% traffic)
- [ ] Metrics validated (latency, error rate, success rate)
- [ ] Canary deployment (20% traffic)
- [ ] Metrics validated
- [ ] Canary deployment (50% traffic)
- [ ] Metrics validated
- [ ] Full rollout (100% traffic)
- [ ] Post-deployment verification
- [ ] Stakeholder notification

### 14.3 Post-Deployment

- [ ] All health checks passing
- [ ] All SLOs within budget
- [ ] All alerts functional
- [ ] All dashboards populated
- [ ] All logs flowing
- [ ] All traces visible
- [ ] All backups completing
- [ ] All replication healthy
- [ ] All certificates valid
- [ ] All secrets accessible
- [ ] All runbooks accessible
- [ ] All on-call personnel briefed
- [ ] ArgoCD sync status healthy
- [ ] Canary analysis metrics within thresholds
- [ ] Feature flag audit log populated
- [ ] Multi-cloud replication lag within SLA
- [ ] Edge nodes synced and healthy
- [ ] Serverless functions responding to triggers
- [ ] Cost dashboard showing expected spend

---

## 15. GitOps Pipeline with ArgoCD

### 15.1 ArgoCD Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        GitOps Control Plane                                 │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     ArgoCD Server (HA: 3 replicas)                  │   │
│  │                                                                     │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │   │
│  │  │ API Server   │  │ Repository   │  │ Controller   │             │   │
│  │  │ (REST/gRPC)  │  │ Server       │  │ (State       │             │   │
│  │  │              │  │ (Git ops)    │  │  Reconciler) │             │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘             │   │
│  │                                                                     │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │   │
│  │  │ Dex (SSO)    │  │ Redis        │  │ Application  │             │   │
│  │  │ (OIDC/LDAP)  │  │ (Cache)      │  │ Set          │             │   │
│  │  │              │  │              │  │ Controller   │             │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     External Secrets Operator                        │   │
│  │              (Vault → Kubernetes Secrets sync)                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
└────────────────────────────────────┼────────────────────────────────────────┘
                                     │
                    ┌────────────────┼────────────────┐
                    │                │                │
                    ▼                ▼                ▼
          ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
          │  Production  │  │   Staging    │  │     DR       │
          │  Cluster     │  │   Cluster    │  │   Cluster    │
          │              │  │              │  │              │
          │ EKS/GKE/AKS  │  │ EKS/GKE/AKS  │  │ EKS/GKE/AKS  │
          └──────────────┘  └──────────────┘  └──────────────┘
```

### 15.2 GitOps Repository Structure

```
grc-claw-gitops/
├── apps/                          # Application definitions (AppProject)
│   ├── control-plane/
│   │   ├── appproject.yaml
│   │   ├── applicationset.yaml
│   │   └── kustomization.yaml
│   ├── evidence/
│   ├── analytics/
│   ├── observability/
│   └── data/
├── environments/                  # Environment-specific configs
│   ├── production/
│   │   ├── us-east-1/
│   │   │   ├── kustomization.yaml
│   │   │   ├── values-pdp.yaml
│   │   │   ├── values-pep.yaml
│   │   │   ├── values-evidence.yaml
│   │   │   └── values-data.yaml
│   │   ├── eu-west-1/
│   │   └── ap-south-1/
│   ├── staging/
│   │   └── us-east-1/
│   └── dr/
│       └── us-west-2/
├── infrastructure/                # Infrastructure components
│   ├── istio/
│   │   ├── base/
│   │   └── overlays/
│   ├── cert-manager/
│   ├── external-secrets/
│   ├── monitoring/
│   └── ingress/
├── policies/                      # OPA/Gatekeeper policies
│   ├── require-labels/
│   ├── restrict-image-registries/
│   ├── require-pdb/
│   └── restrict-node-selectors/
└── bootstrap/                     # Bootstrap ArgoCD itself
    ├── root-application.yaml
    └── argocd-install/
```

### 15.3 ArgoCD Application Definition

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: grc-claw-control-plane
  namespace: argocd
  finalizers:
    - resources-finalizer.argocd.argoproj.io
  annotations:
    argocd.argoproj.io/sync-wave: "2"
spec:
  project: grc-claw-production
  source:
    repoURL: https://github.com/grc-claw/grc-claw-gitops.git
    targetRevision: HEAD
    path: environments/production/us-east-1/control-plane
    helm:
      valueFiles:
        - values-pdp.yaml
        - values-pep.yaml
        - values-policy-api.yaml
        - values-agent-identity.yaml
  destination:
    server: https://kubernetes.default.svc
    namespace: grc-claw-control-plane
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
      allowEmpty: false
    syncOptions:
      - CreateNamespace=true
      - PrunePropagationPolicy=foreground
      - PruneLast=true
      - RespectIgnoreDifferences=true
    retry:
      limit: 5
      backoff:
        duration: 5s
        factor: 2
        maxDuration: 3m
  ignoreDifferences:
    - group: apps
      kind: Deployment
      jsonPointers:
        - /spec/replicas
```

### 15.4 AppProject Configuration

```yaml
apiVersion: argoproj.io/v1alpha1
kind: AppProject
metadata:
  name: grc-claw-production
  namespace: argocd
spec:
  description: GRC_Claw Production Workloads
  sourceRepos:
    - https://github.com/grc-claw/grc-claw-gitops.git
    - https://github.com/grc-claw/grc-claw-helm.git
  destinations:
    - server: https://prod-us-east-1.grc-claw.internal
      namespace: grc-claw-*
    - server: https://prod-eu-west-1.grc-claw.internal
      namespace: grc-claw-*
  clusterResourceWhitelist:
    - group: ""
      kind: Namespace
    - group: ""
      kind: ResourceQuota
    - group: ""
      kind: LimitRange
  namespaceResourceWhitelist:
    - group: ""
      kind: ConfigMap
    - group: ""
      kind: Secret
    - group: apps
      kind: Deployment
    - group: apps
      kind: StatefulSet
    - group: policy
      kind: PodDisruptionBudget
    - group: networking.istio.io
      kind: VirtualService
    - group: networking.istio.io
      kind: DestinationRule
  roles:
    - name: developer
      description: Developer read-only access
      policies:
        - p, proj:grc-claw-production:developer, applications, get, grc-claw-production/*, allow
        - p, proj:grc-claw-production:developer, applications, sync, grc-claw-production/*, deny
      groups:
        - grc-claw-developers
    - name: operator
      description: Operator full access
      policies:
        - p, proj:grc-claw-production:operator, applications, *, grc-claw-production/*, allow
      groups:
        - grc-claw-operators
```

### 15.5 ApplicationSet for Multi-Cluster Deployment

```yaml
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: grc-claw-control-plane
  namespace: argocd
spec:
  generators:
    - list:
        elements:
          - cluster: prod-us-east-1
            url: https://prod-us-east-1.grc-claw.internal
            region: us-east-1
            tier: production
          - cluster: prod-eu-west-1
            url: https://prod-eu-west-1.grc-claw.internal
            region: eu-west-1
            tier: production
          - cluster: prod-ap-south-1
            url: https://prod-ap-south-1.grc-claw.internal
            region: ap-south-1
            tier: production
          - cluster: staging-us-east-1
            url: https://staging-us-east-1.grc-claw.internal
            region: us-east-1
            tier: staging
          - cluster: dr-us-west-2
            url: https://dr-us-west-2.grc-claw.internal
            region: us-west-2
            tier: dr
  template:
    metadata:
      name: 'grc-claw-control-plane-{{cluster}}'
      annotations:
        argocd.argoproj.io/sync-wave: "2"
    spec:
      project: 'grc-claw-{{tier}}'
      source:
        repoURL: https://github.com/grc-claw/grc-claw-gitops.git
        targetRevision: HEAD
        path: 'environments/{{tier}}/{{region}}/control-plane'
        helm:
          valueFiles:
            - 'values-{{tier}}.yaml'
      destination:
        server: '{{url}}'
        namespace: grc-claw-control-plane
      syncPolicy:
        automated:
          prune: true
          selfHeal: true
        syncOptions:
          - CreateNamespace=true
```

### 15.6 Secret Management with External Secrets Operator

```yaml
apiVersion: external-secrets.io/v1beta1
kind: ClusterSecretStore
metadata:
  name: vault-backend
spec:
  provider:
    vault:
      server: https://vault.grc-claw.internal:8200
      path: secret
      version: v2
      auth:
        kubernetes:
          mountPath: kubernetes
          role: external-secrets
          serviceAccountRef:
            name: external-secrets
            namespace: grc-claw-security
---
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: pdp-service-db-credentials
  namespace: grc-claw-control-plane
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: vault-backend
    kind: ClusterSecretStore
  target:
    name: pdp-service-db-credentials
    creationPolicy: Owner
    template:
      type: Opaque
      data:
        DATABASE_URL: "postgresql://{{ .username }}:{{ .password }}@postgresql:5432/grc_claw"
  data:
    - secretKey: username
      remoteRef:
        key: grc-claw/production/pdp-service
        property: db-username
    - secretKey: password
      remoteRef:
        key: grc-claw/production/pdp-service
        property: db-password
```

### 15.7 Sync Waves and Deployment Ordering

```
Wave 0:  Namespace + ResourceQuota + LimitRange + NetworkPolicy
Wave 1:  cert-manager + External Secrets Operator + Vault Agent
Wave 2:  Istio base + Ingress Controller
Wave 3:  Data layer (PostgreSQL, Redis, Kafka, MinIO, Neo4j, immudb)
Wave 4:  Observability (Prometheus, Grafana, Loki, Tempo, OTel)
Wave 5:  Control plane (Policy API, PDP, PEP, Agent Identity)
Wave 6:  Evidence pipeline (Collectors, Normalizers, Validators)
Wave 7:  Analytics + Reporting + Risk Assessment
Wave 8:  Serverless components (Knative services)
Wave 9:  Application-level policies (OPA/Gatekeeper)
```

### 15.8 Rollback Strategy

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: grc-claw-control-plane
  annotations:
    # Automated rollback on sync failure
    argocd.argoproj.io/sync-retry-limit: "5"
    # Revision history limit for rollback
    argocd.argoproj.io/revision-history-limit: "10"
spec:
  # ... other fields ...
  syncPolicy:
    automated:
      selfHeal: true
    retry:
      limit: 5
      backoff:
        duration: 5s
        factor: 2
        maxDuration: 3m
```

**Rollback procedures:**

| Scenario | Trigger | Action | Time |
|----------|---------|--------|------|
| Sync failure | Health check fails | ArgoCD auto-rollback to last healthy revision | < 2 min |
| Canary failure | Error rate > 1% or p99 > 50ms | Argo Rollout auto-rollback | < 5 min |
| Data corruption | Hash chain verification fails | Manual rollback to last known good + PITR | < 4 hours |
| Security incident | CVE detected in running image | Emergency rollback to last signed image | < 15 min |
| Config drift | Self-heal fails 3x | Alert + manual investigation | < 30 min |

### 15.9 GitOps Security Controls

| Control | Implementation |
|---------|---------------|
| **Repository access** | Branch protection, required reviews (2), signed commits |
| **Image verification** | Cosign signature verification in admission controller |
| **Policy enforcement** | OPA/Gatekeeper policies in GitOps repo |
| **Secret encryption** | SOPS or External Secrets Operator (no plaintext in Git) |
| **Audit logging** | ArgoCD audit logs → SIEM |
| **RBAC** | Dex SSO integration, project-level roles |
| **Network isolation** | ArgoCD in private subnet, no public endpoint |

---

## 16. Progressive Delivery

### 16.1 Progressive Delivery Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     Progressive Delivery Pipeline                            │
│                                                                             │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐             │
│  │  Build   │───▶│  Stage   │───▶│  Canary  │───▶│  Prod    │             │
│  │  & Test  │    │  Deploy  │    │  Deploy  │    │  Deploy  │             │
│  └──────────┘    └──────────┘    └────┬─────┘    └──────────┘             │
│                                       │                                      │
│                              ┌────────▼────────┐                            │
│                              │  Analysis &     │                            │
│                              │  Auto-Rollback  │                            │
│                              │                 │                            │
│                              │ • Error rate    │                            │
│                              │ • Latency p99   │                            │
│                              │ • Custom metrics│                            │
│                              │ • SLO burn rate │                            │
│                              └─────────────────┘                            │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 16.2 Canary Deployment with Argo Rollouts

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: pdp-service
  namespace: grc-claw-control-plane
spec:
  replicas: 10
  strategy:
    canary:
      canaryService: pdp-service-canary
      stableService: pdp-service
      trafficRouting:
        istio:
          virtualService:
            name: pdp-service-canary
            routes:
              - primary
          destinationRule:
            name: pdp-service-canary
            canarySubsetName: canary
            stableSubsetName: stable
      steps:
        # Step 1: 5% traffic to canary
        - setWeight: 5
        - pause: { duration: 10m }
        - analysis:
            templates:
              - templateName: pdp-success-rate
            args:
              - name: service-name
                value: pdp-service-canary
        # Step 2: 20% traffic to canary
        - setWeight: 20
        - pause: { duration: 10m }
        - analysis:
            templates:
              - templateName: pdp-success-rate
              - templateName: pdp-latency
        # Step 3: 50% traffic to canary
        - setWeight: 50
        - pause: { duration: 15m }
        - analysis:
            templates:
              - templateName: pdp-success-rate
              - templateName: pdp-latency
              - templateName: pdp-decision-accuracy
        # Step 4: 100% traffic to canary
        - setWeight: 100
        - pause: { duration: 5m }
      analysis:
        successfulRunHistoryLimit: 3
        unsuccessfulRunHistoryLimit: 3
  selector:
    matchLabels:
      app: pdp-service
  template:
    # ... pod template same as Deployment ...
```

### 16.3 Canary Analysis Templates

```yaml
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: pdp-success-rate
  namespace: grc-claw-control-plane
spec:
  metrics:
    - name: success-rate
      interval: 1m
      count: 5
      successCondition: result[0] >= 0.99
      provider:
        prometheus:
          address: http://prometheus:9090
          query: |
            sum(rate(http_requests_total{service="pdp-service-canary",status=~"2.."}[1m]))
            /
            sum(rate(http_requests_total{service="pdp-service-canary"}[1m]))
---
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: pdp-latency
  namespace: grc-claw-control-plane
spec:
  metrics:
    - name: p99-latency
      interval: 1m
      count: 5
      successCondition: result[0] <= 0.050
      provider:
        prometheus:
          address: http://prometheus:9090
          query: |
            histogram_quantile(0.99,
              sum(rate(http_request_duration_seconds_bucket{service="pdp-service-canary"}[1m])) by (le)
            )
---
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: pdp-decision-accuracy
  namespace: grc-claw-control-plane
spec:
  metrics:
    - name: decision-accuracy
      interval: 2m
      count: 3
      successCondition: result[0] >= 0.999
      provider:
        prometheus:
          address: http://prometheus:9090
          query: |
            sum(rate(grc_decision_total{service="pdp-service-canary",outcome="correct"}[2m]))
            /
            sum(rate(grc_decision_total{service="pdp-service-canary"}[2m]))
```

### 16.4 Blue-Green Deployment

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: policy-api
  namespace: grc-claw-control-plane
spec:
  replicas: 6
  strategy:
    blueGreen:
      activeService: policy-api-active
      previewService: policy-api-preview
      autoPromotionEnabled: false
      autoPromotionSeconds: 300
      maxUnavailable: 0
      scaleDownDelaySeconds: 600
      scaleDownDelayRevisionLimit: 2
      previewReplicaCount: 3
      previewAnalysisTemplates:
        - templateName: policy-api-health
  selector:
    matchLabels:
      app: policy-api
  template:
    # ... pod template ...
```

**Blue-green deployment flow:**

```
1. Deploy "preview" version alongside "active" version
2. Run automated tests against preview
3. Switch traffic: active → preview (atomic service switch)
4. Monitor for 10 minutes (auto-rollback on failure)
5. Scale down previous version after 10-minute cooldown
6. Previous version kept for 2 revisions for instant rollback
```

### 16.5 Feature Flags Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     Feature Flag System                                      │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                  Feature Flag Control Plane                          │   │
│  │                                                                     │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │   │
│  │  │ Flag Service │  │ Flag State   │  │ Audit Log    │             │   │
│  │  │ (gRPC/REST)  │  │ (Redis +     │  │ (immudb)     │             │   │
│  │  │              │  │  PostgreSQL) │  │              │             │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘             │   │
│  │                                                                     │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │   │
│  │  │ SDK (Python/ │  │ Rule Engine  │  │ Web UI       │             │   │
│  │  │  Go/Rust)    │  │ (OPA/Cedar)  │  │ (React)      │             │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                    ┌───────────────┼───────────────┐                        │
│                    │               │               │                        │
│                    ▼               ▼               ▼                        │
│          ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │
│          │  PDP Service │  │  PEP Gateway │  │  Analytics   │            │
│          │              │  │              │  │  Engine      │            │
│          │ Feature-aware│  │ Feature-aware│  │ Feature-aware│            │
│          │ enforcement  │  │ interception │  │ scoring      │            │
│          └──────────────┘  └──────────────┘  └──────────────┘            │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Feature flag configuration:**

```yaml
apiVersion: grc-claw.io/v1alpha1
kind: FeatureFlag
metadata:
  name: new-risk-scoring-algorithm
  namespace: grc-claw-control-plane
spec:
  flagKey: new_risk_scoring_v2
  description: "New ML-based risk scoring algorithm"
  enabled: true
  rollout:
    strategy: percentage
    percentage: 10
    # strategy: targeted
    # targets:
    #   - tenant: tenant-acme
    #     percentage: 100
    #   - tenant: tenant-globex
    #     percentage: 50
  rules:
    - name: enterprise-tenants
      condition: "context.tier == 'enterprise'"
      value: true
    - name: beta-tenants
      condition: "context.tags contains 'beta'"
      value: true
  defaultValue: false
  audit:
    logAccess: true
    logChanges: true
    retentionDays: 90
```

### 16.6 Progressive Delivery by Component

| Component | Strategy | Analysis Metrics | Auto-Rollback |
|-----------|----------|-----------------|---------------|
| **PDP Service** | Canary (5% → 20% → 50% → 100%) | Success rate, p99 latency, decision accuracy | Error rate > 1% or p99 > 50ms |
| **PEP Gateway** | Canary (10% → 50% → 100%) | Success rate, p99 latency, connection errors | Error rate > 0.5% or p99 > 20ms |
| **Policy API** | Blue-green | Health checks, API response validation | Any health check failure |
| **Evidence Collector** | Rolling update | Queue depth, processing lag, error rate | Lag > 50K or error rate > 5% |
| **Analytics Engine** | Canary (5% → 25% → 50% → 100%) | Scoring accuracy, processing time | Accuracy drop > 0.1% |
| **Reporting Engine** | Blue-green | Report generation success rate | Any generation failure |
| **Agent Identity** | Blue-green | SVID issuance success rate | Issuance failure > 0.1% |

### 16.7 Traffic Splitting with Istio

```yaml
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: pdp-service-traffic-split
  namespace: grc-claw-control-plane
spec:
  hosts:
    - pdp-service
  http:
    - name: canary-route
      match:
        - headers:
            x-canary:
              exact: "true"
        - headers:
            x-tenant-tier:
              exact: "beta"
      route:
        - destination:
            host: pdp-service
            subset: canary
          weight: 100
    - name: weighted-route
      route:
        - destination:
            host: pdp-service
            subset: canary
          weight: 10
        - destination:
            host: pdp-service
            subset: stable
          weight: 90
```

---

## 17. Multi-Cloud Deployment Patterns

### 17.1 Multi-Cloud Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Multi-Cloud Control Plane                            │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                  Global Control Plane (ArgoCD)                       │   │
│  │                                                                     │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │   │
│  │  │ Global App   │  │ Multi-Cluster│  │ Cross-Cloud  │             │   │
│  │  │ Set          │  │ Service Mesh │  │ Secrets      │             │   │
│  │  │ Controller   │  │ (Istio)      │  │ (Vault)      │             │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
└────────────────────────────────────┼────────────────────────────────────────┘
                                     │
          ┌──────────────────────────┼──────────────────────────┐
          │                          │                          │
          ▼                          ▼                          ▼
┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐
│   AWS (Primary)     │  │   GCP (Secondary)   │  │   Azure (Tertiary)  │
│                     │  │                     │  │                     │
│  ┌───────────────┐  │  │  ┌───────────────┐  │  │  ┌───────────────┐  │
│  │ EKS Cluster   │  │  │  │ GKE Cluster   │  │  │  │ AKS Cluster   │  │
│  │               │  │  │  │               │  │  │  │               │  │
│  │ • PDP (active)│  │  │  │ • PDP (active)│  │  │  │ • PDP (active)│  │
│  │ • PEP (active)│  │  │  │ • PEP (active)│  │  │  │ • PEP (active)│  │
│  │ • Evidence    │  │  │  │ • Evidence    │  │  │  │ • Evidence    │  │
│  │ • Analytics   │  │  │  │ • Analytics   │  │  │  │ • Analytics   │  │
│  └───────────────┘  │  │  └───────────────┘  │  │  └───────────────┘  │
│                     │  │                     │  │                     │
│  ┌───────────────┐  │  │  ┌───────────────┐  │  │  ┌───────────────┐  │
│  │ RDS Aurora    │  │  │  │ Cloud SQL     │  │  │  │ Azure DB      │  │
│  │ (Primary)     │  │  │  │ (Replica)     │  │  │  │ (Replica)     │  │
│  └───────────────┘  │  │  └───────────────┘  │  │  └───────────────┘  │
│                     │  │                     │  │                     │
│  ┌───────────────┐  │  │  ┌───────────────┐  │  │  ┌───────────────┐  │
│  │ ElastiCache   │  │  │  │ Memorystore   │  │  │  │ Azure Cache   │  │
│  │ (Primary)     │  │  │  │ (Replica)     │  │  │  │ (Replica)     │  │
│  └───────────────┘  │  │  └───────────────┘  │  │  └───────────────┘  │
│                     │  │                     │  │                     │
│  ┌───────────────┐  │  │  ┌───────────────┐  │  │  ┌───────────────┐  │
│  │ MSK (Kafka)   │  │  │  │ Pub/Sub       │  │  │  │ Event Hubs    │  │
│  │ (Primary)     │  │  │  │ (Replica)     │  │  │  │ (Replica)     │  │
│  └───────────────┘  │  │  └───────────────┘  │  │  └───────────────┘  │
│                     │  │                     │  │                     │
│  ┌───────────────┐  │  │  ┌───────────────┐  │  │  ┌───────────────┐  │
│  │ S3 (Primary)  │  │  │  │ GCS (Replica) │  │  │  │ Blob (Replica)│  │
│  └───────────────┘  │  │  └───────────────┘  │  │  └───────────────┘  │
└─────────────────────┘  └─────────────────────┘  └─────────────────────┘
```

### 17.2 Cloud-Agnostic Abstraction Layer

```yaml
# Cross-cloud service abstraction
apiVersion: grc-claw.io/v1alpha1
kind: CloudService
metadata:
  name: grc-claw-database
  namespace: grc-claw-data
spec:
  serviceType: database
  engine: postgresql
  version: "16"
  tier: production
  replication:
    mode: synchronous
    replicas: 2
  backup:
    enabled: true
    schedule: "0 2 * * *"
    retention: 30d
  providers:
    aws:
      service: rds-aurora
      instanceClass: db.r6g.2xlarge
      region: us-east-1
      multiAZ: true
    gcp:
      service: cloud-sql
      instanceType: db-custom-8-32768
      region: us-central1
      availabilityType: REGIONAL
    azure:
      service: postgresql-flexible
      sku: GP_Standard_D8s_v3
      region: eastus
      zoneRedundant: true
```

### 17.3 Multi-Cluster Service Mesh

```yaml
apiVersion: networking.istio.io/v1beta1
kind: ServiceEntry
metadata:
  name: pdp-service-multi-cloud
  namespace: grc-claw-control-plane
spec:
  hosts:
    - pdp-service.grc-claw.svc.cluster.local
  location: MESH_INTERNAL
  ports:
    - number: 8080
      name: http
      protocol: HTTP
    - number: 9090
      name: grpc
      protocol: gRPC
  resolution: DNS
  endpoints:
    - address: pdp-service.grc-claw-control-plane.svc.cluster.local
      locality: us-east-1/aws
      labels:
        cloud: aws
        region: us-east-1
    - address: pdp-service.gcp.grc-claw-control-plane.svc.cluster.local
      locality: us-central1/gcp
      labels:
        cloud: gcp
        region: us-central1
    - address: pdp-service.azure.grc-claw-control-plane.svc.cluster.local
      locality: eastus/azure
      labels:
        cloud: azure
        region: eastus
```

### 17.4 Cross-Cloud Data Replication

| Data Store | Primary | Secondary | Tertiary | Replication Method | Lag |
|-----------|---------|-----------|----------|-------------------|-----|
| PostgreSQL | AWS RDS Aurora | GCP Cloud SQL | Azure DB | Native logical replication | < 5s |
| Redis | AWS ElastiCache | GCP Memorystore | Azure Cache | Redis Sentinel + custom sync | < 1s |
| Kafka | AWS MSK | GCP Pub/Sub | Azure Event Hubs | MirrorMaker2 / custom bridge | < 2s |
| MinIO | AWS S3 | GCP GCS | Azure Blob | Bucket replication (native) | < 30s |
| Neo4j | AWS (self-managed) | GCP (self-managed) | Azure (self-managed) | Causal cluster + backup restore | < 60s |
| immudb | AWS (self-managed) | GCP (self-managed) | Azure (self-managed) | Read replica + WAL shipping | < 10s |

### 17.5 Cloud Bursting Pattern

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Cloud Bursting Architecture                          │
│                                                                             │
│  Normal Load (100% capacity in AWS)                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  AWS EKS: 100% traffic  │  GCP GKE: 0% (standby)  │  Azure: 0%    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Burst Load (150% capacity — overflow to GCP)                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  AWS EKS: 100% traffic  │  GCP GKE: 50% (burst)  │  Azure: 0%    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Emergency (AWS failure — full failover to GCP + Azure)                    │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  AWS EKS: DOWN          │  GCP GKE: 70% (failover) │  Azure: 30%  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 17.6 Multi-Cloud Cost Management

| Strategy | Implementation | Savings |
|----------|---------------|---------|
| **Spot/preemptible across clouds** | Use spot instances on all clouds for stateless workloads | 60-90% compute |
| **Cross-cloud arbitrage** | Route burst traffic to cheapest cloud provider | 10-30% variable |
| **Reserved capacity planning** | 1-year commit on primary cloud, spot on secondary | 30-50% baseline |
| **Storage replication optimization** | Replicate only critical data cross-cloud | 40-60% storage |
| **Network cost optimization** | Use cloud interconnects, avoid public internet | 20-40% network |
| **Unified cost dashboard** | Kubecost + cloud provider billing APIs | Visibility |

### 17.7 Vendor Lock-In Mitigation

| Layer | Lock-In Risk | Mitigation |
|-------|-------------|------------|
| **Compute** | Low | Kubernetes (EKS/GKE/AKS) — same manifests |
| **Service mesh** | Low | Istio — cloud-agnostic |
| **Databases** | Medium | Use PostgreSQL/Redis everywhere; avoid proprietary DBs |
| **Message queue** | Medium | Kafka (self-managed) — avoid SQS/PubSub/Event Hubs |
| **Object storage** | Low | MinIO — S3-compatible API everywhere |
| **Secrets** | Low | HashiCorp Vault — cloud-agnostic |
| **CI/CD** | Low | GitHub Actions + ArgoCD — cloud-agnostic |
| **Monitoring** | Low | Prometheus/Grafana — cloud-agnostic |
| **Serverless** | Medium | Knative on K8s — avoid Lambda/Cloud Functions |

---

## 18. Edge Deployment Architecture

### 18.1 Edge Computing Patterns for GRC_Claw

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Edge Deployment Topology                             │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     Cloud Control Plane                              │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │   │
│  │  │ Policy       │  │ Analytics    │  │ Global       │             │   │
│  │  │ Distribution │  │ Aggregation  │  │ Tenant       │             │   │
│  │  │              │  │              │  │ Registry     │             │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                    ┌───────────────┼───────────────┐                        │
│                    │               │               │                        │
│                    ▼               ▼               ▼                        │
│  ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐ │
│  │   Edge Site 1       │  │   Edge Site 2       │  │   Edge Site N       │ │
│  │   (Factory Floor)   │  │   (Branch Office)   │  │   (Data Center)     │ │
│  │                     │  │                     │  │                     │ │
│  │  ┌───────────────┐  │  │  ┌───────────────┐  │  │  ┌───────────────┐  │ │
│  │  │ Edge PDP      │  │  │  │ Edge PDP      │  │  │  │ Edge PDP      │  │ │
│  │  │ (Lightweight) │  │  │  │ (Lightweight) │  │  │  │ (Lightweight) │  │ │
│  │  └───────────────┘  │  │  └───────────────┘  │  │  └───────────────┘  │ │
│  │                     │  │                     │  │                     │ │
│  │  ┌───────────────┐  │  │  ┌───────────────┐  │  │  ┌───────────────┐  │ │
│  │  │ Edge PEP      │  │  │  │ Edge PEP      │  │  │  │ Edge PEP      │  │ │
│  │  │ (Local        │  │  │  │ (Local        │  │  │  │ (Local        │  │ │
│  │  │  Enforcement) │  │  │  │  Enforcement) │  │  │  │  Enforcement) │  │ │
│  │  └───────────────┘  │  │  └───────────────┘  │  │  └───────────────┘  │ │
│  │                     │  │                     │  │                     │ │
│  │  ┌───────────────┐  │  │  ┌───────────────┐  │  │  ┌───────────────┐  │ │
│  │  │ Local Cache   │  │  │  │ Local Cache   │  │  │  │ Local Cache   │  │ │
│  │  │ (Redis        │  │  │  │ (Redis        │  │  │  │ (Redis        │  │ │
│  │  │  Embedded)    │  │  │  │  Embedded)    │  │  │  │  Embedded)    │  │ │
│  │  └───────────────┘  │  │  └───────────────┘  │  │  └───────────────┘  │ │
│  │                     │  │                     │  │                     │ │
│  │  ┌───────────────┐  │  │  ┌───────────────┐  │  │  ┌───────────────┐  │ │
│  │  │ Evidence      │  │  │  │ Evidence      │  │  │  │ Evidence      │  │ │
│  │  │ Buffer        │  │  │  │ Buffer        │  │  │  │ Buffer        │  │ │
│  │  │ (Local WAL)   │  │  │  │ (Local WAL)   │  │  │  │ (Local WAL)   │  │ │
│  │  └───────────────┘  │  │  └───────────────┘  │  │  └───────────────┘  │ │
│  │                     │  │                     │  │                     │ │
│  │  ┌───────────────┐  │  │  ┌───────────────┐  │  │  ┌───────────────┐  │ │
│  │  │ Sync Agent    │  │  │  │ Sync Agent    │  │  │  │ Sync Agent    │  │ │
│  │  │ (Cloud ↔ Edge)│  │  │  │ (Cloud ↔ Edge)│  │  │  │ (Cloud ↔ Edge)│  │ │
│  │  └───────────────┘  │  │  └───────────────┘  │  │  └───────────────┘  │ │
│  └─────────────────────┘  └─────────────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 18.2 Lightweight Edge Enforcement

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: edge-pdp-service
  namespace: grc-claw-edge
spec:
  replicas: 1
  selector:
    matchLabels:
      app: edge-pdp-service
  template:
    metadata:
      labels:
        app: edge-pdp-service
    spec:
      containers:
        - name: edge-pdp
          image: ghcr.io/grc-claw/edge-pdp:v1.2.0
          resources:
            requests:
              cpu: 100m
              memory: 128Mi
            limits:
              cpu: 500m
              memory: 512Mi
          env:
            - name: EDGE_MODE
              value: "true"
            - name: POLICY_SYNC_INTERVAL
              value: "30s"
            - name: OFFLINE_ENFORCEMENT
              value: "true"
            - name: MAX_OFFLINE_DURATION
              value: "24h"
            - name: LOCAL_CACHE_SIZE
              value: "10000"
          volumeMounts:
            - name: policy-cache
              mountPath: /cache
            - name: evidence-wal
              mountPath: /wal
      volumes:
        - name: policy-cache
          emptyDir:
            sizeLimit: 100Mi
        - name: evidence-wal
          emptyDir:
            sizeLimit: 500Mi
```

### 18.3 Edge-to-Cloud Synchronization

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     Edge-to-Cloud Sync Protocol                              │
│                                                                             │
│  ┌─────────────┐                    ┌─────────────┐                        │
│  │  Edge Site  │                    │   Cloud     │                        │
│  │             │                    │             │                        │
│  │  ┌───────┐  │  1. Policy Sync   │  ┌───────┐  │                        │
│  │  │ Sync  │◀─┼───────────────────┼──│ Policy│  │                        │
│  │  │ Agent │  │  (delta, 30s)     │  │ Dist  │  │                        │
│  │  └───┬───┘  │                   │  └───────┘  │                        │
│  │      │      │                   │             │                        │
│  │  ┌───▼───┐  │  2. Evidence      │  ┌───────┐  │                        │
│  │  │ Sync  │──┼──────────────────▶│  │Evidence│  │                        │
│  │  │ Agent │  │  Upload (batch)   │  │ Ingest │  │                        │
│  │  └───┬───┘  │                   │  └───────┘  │                        │
│  │      │      │                   │             │                        │
│  │  ┌───▼───┐  │  3. Heartbeat     │  ┌───────┐  │                        │
│  │  │ Sync  │──┼──────────────────▶│  │Health │  │                        │
│  │  │ Agent │  │  (status, 10s)    │  │ Check │  │                        │
│  │  └───────┘  │                   │  └───────┘  │                        │
│  │             │                   │             │                        │
│  └─────────────┘                   └─────────────┘                        │
│                                                                             │
│  Sync Modes:                                                                │
│  • Real-time: Policy changes pushed to edge (< 5s)                         │
│  • Batch: Evidence uploaded in batches (configurable interval)              │
│  • Offline: Edge operates autonomously, syncs when connectivity restored    │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 18.4 Offline-First Enforcement

| Scenario | Behavior | Data |
|----------|----------|------|
| **Normal** | Real-time policy evaluation with cloud sync | Full policy set cached |
| **Network degraded** | Local policy evaluation, evidence buffered | Cached policies + local WAL |
| **Network lost** | Autonomous enforcement with cached policies | Local cache only |
| **Extended offline (> 24h)** | Degrade to last-known-good policies | Alert + manual intervention |
| **Network restored** | Sync buffered evidence, update policies | Full reconciliation |

### 18.5 Edge Node Management

```yaml
apiVersion: grc-claw.io/v1alpha1
kind: EdgeNode
metadata:
  name: factory-floor-01
  namespace: grc-claw-edge
spec:
  site: factory-floor-01
  location: "Building A, Floor 2"
  region: us-east-1
  capabilities:
    enforcement: true
    evidenceCollection: true
    analytics: false
  resources:
    maxAgents: 500
    maxPolicies: 1000
  sync:
    policyInterval: 30s
    evidenceInterval: 60s
    heartbeatInterval: 10s
    offlineTolerance: 24h
  security:
    tamperDetection: true
    secureBoot: true
    encryption: AES-256
  status:
    phase: Active
    lastSync: "2026-10-01T12:00:00Z"
    policyVersion: "v1.2.3"
    bufferedEvidence: 0
```

### 18.6 Data Residency at Edge

```yaml
apiVersion: grc-claw.io/v1alpha1
kind: DataResidencyPolicy
metadata:
  name: eu-data-residency
  namespace: grc-claw-edge
spec:
  region: EU
  allowedEdgeSites:
    - berlin-office-01
    - paris-datacenter-01
  dataClassification:
    - personalData
    - sensitiveCompliance
  rules:
    - action: store
      constraint: "edge_site.region == 'EU'"
    - action: replicate
      constraint: "cloud_region in ['eu-west-1', 'eu-central-1']"
    - action: process
      constraint: "edge_site.region == 'EU'"
  enforcement: strict
```

---

## 19. Serverless Components

### 19.1 Knative Serving Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     Knative Serving on Kubernetes                            │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     Knative Serving Control Plane                    │   │
│  │                                                                     │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │   │
│  │  │ Activator    │  │ Autoscaler   │  │ Controller   │             │   │
│  │  │ (Buffer      │  │ (KPA/HPA)    │  │ (Reconciler) │             │   │
│  │  │  requests)   │  │              │  │              │             │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     Knative Services (Scale-to-Zero)                 │   │
│  │                                                                     │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │   │
│  │  │ Evidence     │  │ Report       │  │ Regulatory   │             │   │
│  │  │ Packaging    │  │ Generation   │  │ Change       │             │   │
│  │  │              │  │              │  │ Monitor      │             │   │
│  │  │ Scale: 0→10  │  │ Scale: 0→5   │  │ Scale: 0→3   │             │   │
│  │  │ Trigger:     │  │ Trigger:     │  │ Trigger:     │             │   │
│  │  │ Scheduled    │  │ HTTP request │  │ Event-driven │             │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘             │   │
│  │                                                                     │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │   │
│  │  │ Compliance   │  │ Anomaly      │  │ Data         │             │   │
│  │  │ Score        │  │ Response     │  │ Retention    │             │   │
│  │  │ Recalc       │  │              │  │ Enforcement  │             │   │
│  │  │              │  │              │  │              │             │   │
│  │  │ Scale: 0→5   │  │ Scale: 0→3   │  │ Scale: 0→2   │             │   │
│  │  │ Trigger:     │  │ Trigger:     │  │ Trigger:     │             │   │
│  │  │ Event-driven │  │ Event-driven │  │ Scheduled    │             │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 19.2 Knative Service Definitions

```yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: evidence-packaging
  namespace: grc-claw-serverless
  annotations:
    # Scale-to-zero configuration
    autoscaling.knative.dev/minScale: "0"
    autoscaling.knative.dev/maxScale: "10"
    autoscaling.knative.dev/target: "5"
    autoscaling.knative.dev/targetBurstCapacity: "10"
    autoscaling.knative.dev/scale-down-delay: "5m"
    autoscaling.knative.dev/window: "60s"
    # Concurrency
    autoscaling.knative.dev/targetUtilizationPercentage: "70"
    autoscaling.knative.dev/metric: "concurrency"
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/class: "kpa.autoscaling.knative.dev"
    spec:
      containerConcurrency: 5
      timeoutSeconds: 300
      containers:
        - image: ghcr.io/grc-claw/evidence-packaging:v1.2.0
          resources:
            requests:
              cpu: 250m
              memory: 256Mi
            limits:
              cpu: 1000m
              memory: 1Gi
          env:
            - name: EVIDENCE_BUCKET
              value: grc-claw-evidence
            - name: OUTPUT_FORMAT
              value: OSCAL
---
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: report-generation
  namespace: grc-claw-serverless
  annotations:
    autoscaling.knative.dev/minScale: "0"
    autoscaling.knative.dev/maxScale: "5"
    autoscaling.knative.dev/scale-down-delay: "10m"
spec:
  template:
    spec:
      containerConcurrency: 1
      timeoutSeconds: 600
      containers:
        - image: ghcr.io/grc-claw/report-generation:v1.2.0
          resources:
            requests:
              cpu: 500m
              memory: 512Mi
            limits:
              cpu: 2000m
              memory: 2Gi
```

### 19.3 Event-Driven Serverless Patterns

```yaml
# Kafka-triggered serverless function
apiVersion: eventing.knative.dev/v1
kind: Trigger
metadata:
  name: anomaly-response-trigger
  namespace: grc-claw-serverless
spec:
  broker: default
  filter:
    attributes:
      type: grc.anomaly.detected
  subscriber:
    ref:
      apiVersion: serving.knative.dev/v1
      kind: Service
      name: anomaly-response
---
# Scheduled serverless function (CronJob → Knative)
apiVersion: batch/v1
kind: CronJob
metadata:
  name: compliance-score-recalc
  namespace: grc-claw-serverless
spec:
  schedule: "0 */6 * * *"  # Every 6 hours
  jobTemplate:
    spec:
      template:
        spec:
          containers:
            - name: trigger
              image: ghcr.io/grc-claw/knative-trigger:v1.0.0
              env:
                - name: TARGET_SERVICE
                  value: compliance-score-recalc
                - name: PAYLOAD
                  value: '{"action": "recalculate_all"}'
          restartPolicy: OnFailure
```

### 19.4 Cold Start Mitigation

| Strategy | Implementation | Impact |
|----------|---------------|--------|
| **Min scale = 1** | Keep 1 warm instance for critical services | Eliminates cold start for first request |
| **Prewarming** | Scheduled ping every 5 minutes | Keeps instances warm |
| **Resource optimization** | Smaller images, faster startup | Reduces cold start time |
| **Concurrency tuning** | Set containerConcurrency appropriately | Balances throughput vs. cold starts |
| **Scale-down delay** | 5-10 minute delay before scale-to-zero | Avoids thrashing |

### 19.5 Serverless Security Model

| Control | Implementation |
|---------|---------------|
| **Authentication** | Knative broker with OIDC |
| **Authorization** | RBAC per Knative service |
| **Network isolation** | NetworkPolicy per service |
| **Secret injection** | External Secrets Operator |
| **Resource limits** | Strict CPU/memory limits |
| **Timeout enforcement** | Max 600s execution time |
| **Audit logging** | All invocations logged to immudb |

### 19.6 Serverless Cost Optimization

| Strategy | Implementation | Savings |
|----------|---------------|---------|
| **Scale-to-zero** | Non-critical functions scale to 0 when idle | 70-90% for bursty workloads |
| **Right-size resources** | Match CPU/memory to actual usage | 20-40% |
| **Concurrency tuning** | Optimize containerConcurrency | 10-20% |
| **Scheduled vs. event-driven** | Use scheduled for predictable workloads | 15-25% |
| **Multi-tenant functions** | Share function instances across tenants | 30-50% |

---

## 20. Cost Optimization Strategies

### 20.1 FinOps Framework

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         FinOps Lifecycle                                     │
│                                                                             │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐             │
│  │  Inform  │───▶│ Optimize │───▶│ Operate  │───▶│ Iterate  │             │
│  │          │    │          │    │          │    │          │             │
│  │ • Cost   │    │ • Right- │    │ • Budget │    │ • Review │             │
│  │   visibility│  │   sizing │    │   alerts │    │ • Adjust │             │
│  │ • Tagging│    │ • Spot   │    │ • Anomaly│    │ • Automate│            │
│  │ • Allocation│  │   instances│  │   detection│  │ • Improve│            │
│  │ • Showback│    │ • Storage│    │ • Forecast│    │          │             │
│  │          │    │   tiering│    │          │    │          │             │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘             │
│                                                                             │
│  Tools: Kubecost + CloudHealth + Custom dashboards                          │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 20.2 Resource Right-Sizing Automation

```yaml
apiVersion: grc-claw.io/v1alpha1
kind: RightSizingPolicy
metadata:
  name: production-rightsizing
  namespace: grc-claw-observability
spec:
  analysisWindow: 7d
  updateFrequency: 24h
  thresholds:
    cpu:
      underutilized: 30    # < 30% average → recommend smaller
      overutilized: 80     # > 80% average → recommend larger
    memory:
      underutilized: 40
      overutilized: 85
  actions:
    - type: recommendation
      target: slack-channel
    - type: auto-apply
      target: non-production
      requireApproval: false
    - type: auto-apply
      target: production
      requireApproval: true
  exclusions:
    - component: pdp-service
      reason: "Latency-sensitive, keep headroom"
    - component: postgresql
      reason: "Stateful, manual sizing only"
```

### 20.3 Spot Instance Management

```yaml
apiVersion: karpenter.sh/v1beta1
kind: NodePool
metadata:
  name: grc-claw-spot
spec:
  template:
    spec:
      requirements:
        - key: karpenter.sh/capacity-type
          operator: In
          values: ["spot"]
        - key: node.kubernetes.io/instance-type
          operator: In
          values: ["m6i.2xlarge", "m6i.4xlarge", "c6i.2xlarge", "r6i.2xlarge"]
      taints:
        - key: spot
          value: "true"
          effect: NoSchedule
  limits:
    cpu: 500
    memory: 2000Gi
  disruption:
    consolidationPolicy: WhenUnderutilized
    expireAfter: 720h
    budgets:
      - nodes: "10%"
      # Disruption handling
  weight: 50  # Prefer spot over on-demand
---
# Pod toleration for spot instances
apiVersion: apps/v1
kind: Deployment
metadata:
  name: evidence-collector
  namespace: grc-claw-evidence
spec:
  template:
    spec:
      tolerations:
        - key: spot
          operator: Equal
          value: "true"
          effect: NoSchedule
      affinity:
        nodeAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
            - weight: 100
              preference:
                matchExpressions:
                  - key: karpenter.sh/capacity-type
                    operator: In
                    values: ["spot"]
```

### 20.4 Storage Tiering Automation

```yaml
apiVersion: grc-claw.io/v1alpha1
kind: StorageTieringPolicy
metadata:
  name: evidence-tiering
  namespace: grc-claw-data
spec:
  rules:
    - name: hot-to-warm
      source: hot
      target: warm
      age: 30d
      action: move
    - name: warm-to-cold
      source: warm
      target: cold
      age: 90d
      action: move
    - name: cold-to-archive
      source: cold
      target: archive
      age: 365d
      action: move
    - name: archive-to-delete
      source: archive
      target: delete
      age: 2555d  # 7 years
      action: delete
  storageClasses:
    hot:
      type: ssd
      replication: 3
      iops: 10000
    warm:
      type: ssd
      replication: 2
      iops: 3000
    cold:
      type: object
      replication: 2
      endpoint: s3
    archive:
      type: glacier
      replication: 1
      endpoint: s3-glacier
```

### 20.5 Network Cost Optimization

| Strategy | Implementation | Savings |
|----------|---------------|---------|
| **Service mesh locality** | Route traffic to same-zone instances | 20-40% cross-zone |
| **Compression** | Enable gRPC/HTTP compression | 10-30% bandwidth |
| **Connection pooling** | Reuse connections via PgBouncer/Envoy | 15-25% connection overhead |
| **CDN for static assets** | CloudFront/Cloud CDN for dashboards | 30-50% egress |
| **Private connectivity** | VPC peering / Cloud Interconnect | 40-60% vs. public internet |
| **Data compression** | Compress evidence before cross-region replication | 50-70% replication bandwidth |

### 20.6 Cost Allocation and Showback

```yaml
apiVersion: grc-claw.io/v1alpha1
kind: CostAllocationPolicy
metadata:
  name: tenant-cost-allocation
  namespace: grc-claw-observability
spec:
  allocationModel: proportional  # proportional | fixed | usage-based
  dimensions:
    - tenant
    - component
    - environment
    - region
  sharedCosts:
    - component: kubernetes-control-plane
      allocation: proportional-by-namespace
    - component: observability
      allocation: proportional-by-tenant
    - component: ingress
      allocation: proportional-by-request-volume
  reporting:
    frequency: daily
    destination: grafana-dashboard
    apiEndpoint: https://cost-api.grc-claw.internal/v1/costs
  budgets:
    - name: monthly-total
      amount: 100000
      currency: USD
      alertThresholds: [80, 90, 100]
    - name: per-tenant
      amount: 10000
      currency: USD
      alertThresholds: [80, 90, 100]
```

### 20.7 Continuous Cost Optimization

| Practice | Frequency | Tool | Owner |
|----------|-----------|------|-------|
| **Right-sizing review** | Weekly | VPA recommendations + Kubecost | Platform team |
| **Spot instance review** | Daily | Karpenter + cloud APIs | Automated |
| **Storage tiering review** | Monthly | Custom scripts + S3 lifecycle | Platform team |
| **Reserved capacity planning** | Quarterly | Cloud provider APIs + forecasts | FinOps team |
| **Orphaned resource cleanup** | Daily | Custom scripts + cloud APIs | Automated |
| **Cost anomaly detection** | Real-time | Kubecost alerts | Automated |
| **Budget vs. actual review** | Monthly | Grafana dashboards | FinOps + Engineering |
| **Unit cost analysis** | Monthly | Cost per tenant, cost per decision | FinOps team |

### 20.8 Cost Optimization Targets

| Category | Current | Target | Strategy |
|----------|---------|--------|----------|
| **Compute** | $50K/month | $35K/month | Spot + right-sizing + autoscaling |
| **Storage** | $15K/month | $8K/month | Tiering + compression + lifecycle |
| **Network** | $10K/month | $6K/month | Locality + compression + CDN |
| **Licensing** | $5K/month | $3K/month | Open-source alternatives |
| **Total** | $80K/month | $52K/month | 35% reduction |

---

## 23. GitOps Pipeline Design (Expanded)

### 23.1 Branching Strategy

GRC_Claw uses a **trunk-based development** model with short-lived feature branches, optimized for continuous delivery:

```
main (production)
  │
  ├── feature/policy-v2 ──▶ PR ──▶ main ──▶ staging ──▶ production
  │
  ├── hotfix/cve-patch ──▶ PR ──▶ main ──▶ production (emergency)
  │
  └── release/v1.3 ──▶ main (tag) ──▶ production
```

| Branch | Purpose | Lifetime | Protection |
|--------|---------|----------|------------|
| `main` | Production-ready code | Permanent | 2 reviews, signed commits, all checks pass |
| `feature/*` | Feature development | < 3 days | 1 review, CI passing |
| `hotfix/*` | Emergency fixes | < 24 hours | 1 review, CI passing, post-merge review |
| `release/*` | Release preparation | < 1 week | 2 reviews, full test suite |
| `dependabot/*` | Automated dependency updates | < 7 days | Auto-merge if CI passes |

### 23.2 Pipeline Stages and Gates

```
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│  Build   │──▶│  Test    │──▶│  Scan    │──▶│  Stage   │──▶│  Deploy  │
│          │   │          │   │          │   │          │   │          │
│ • Compile│   │ • Unit   │   │ • SAST   │   │ • Integ  │   │ • Dev    │
│ • Lint   │   │ • Integ  │   │ • DAST   │   │ • E2E    │   │ • Staging│
│ • Package│   │ • Contract│  │ • Vuln   │   │ • Perf   │   │ • Prod   │
│ • Sign   │   │ • Migrate│   │ • License│   │ • Chaos  │   │          │
└──────────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘
     │              │              │              │              │
     ▼              ▼              ▼              ▼              ▼
  Gate:         Gate:          Gate:          Gate:          Gate:
  Compile       80% coverage   0 CRITICAL     p99 < 50ms    SLOs met
  Lint clean    All tests pass 0 HIGH vulns   0 errors      Health OK
```

### 23.3 Promotion Gates

| Promotion | Gate Criteria | Approval | Automated |
|-----------|--------------|----------|-----------|
| Dev → Staging | All tests pass, 0 CRITICAL vulns, lint clean | No | Yes |
| Staging → Production | E2E tests pass, perf within 10% of baseline, chaos test pass | Yes (1 approver) | Yes |
| Production → DR | Sync verification, replication lag < 5s | No | Yes |
| Emergency (any) | CVE fix, security patch | Yes (security team) | Yes |

### 23.4 Change Management Workflow

```
1. Developer creates feature branch from main
2. CI runs: build → unit tests → lint → SAST
3. PR opened → peer review → merge to main
4. CD pipeline: build image → scan → sign → push to registry
5. ArgoCD detects GitOps repo change → syncs to dev
6. Automated integration tests run in dev
7. Promotion to staging (automated)
8. E2E + performance tests run in staging
9. Approval gate → promotion to production
10. Canary deployment (5% → 20% → 50% → 100%)
11. Post-deployment verification
12. GitOps repo updated with new image tag
```

### 23.5 GitOps Repository Structure (Complete)

```
grc-claw-gitops/
├── apps/
│   ├── control-plane/
│   │   ├── appproject.yaml
│   │   ├── applicationset.yaml
│   │   ├── kustomization.yaml
│   │   └── rollouts/
│   │       ├── pdp-service-rollout.yaml
│   │       ├── pep-gateway-rollout.yaml
│   │       └── policy-api-rollout.yaml
│   ├── evidence/
│   ├── analytics/
│   ├── observability/
│   └── data/
├── environments/
│   ├── production/
│   │   ├── us-east-1/
│   │   │   ├── kustomization.yaml
│   │   │   ├── values-pdp.yaml
│   │   │   ├── values-pep.yaml
│   │   │   ├── values-policy-api.yaml
│   │   │   ├── values-agent-identity.yaml
│   │   │   ├── values-evidence.yaml
│   │   │   ├── values-analytics.yaml
│   │   │   ├── values-data.yaml
│   │   │   └── secrets/                    # Encrypted with SOPS
│   │   │       ├── db-credentials.enc.yaml
│   │   │       ├── api-keys.enc.yaml
│   │   │       └── tls-certs.enc.yaml
│   │   ├── eu-west-1/
│   │   └── ap-south-1/
│   ├── staging/
│   │   └── us-east-1/
│   ├── development/
│   │   └── us-east-1/
│   └── dr/
│       └── us-west-2/
├── infrastructure/
│   ├── istio/
│   │   ├── base/
│   │   └── overlays/
│   │       ├── production/
│   │       └── staging/
│   ├── cert-manager/
│   ├── external-secrets/
│   ├── monitoring/
│   │   ├── prometheus/
│   │   ├── grafana/
│   │   ├── loki/
│   │   └── tempo/
│   ├── ingress/
│   └── argocd/
├── policies/
│   ├── require-labels/
│   ├── restrict-image-registries/
│   ├── require-pdb/
│   ├── restrict-node-selectors/
│   └── require-resource-limits/
├── scripts/
│   ├── validate.sh
│   ├── promote.sh
│   └── rollback.sh
└── bootstrap/
    ├── root-application.yaml
    └── argocd-install/
```

---

## 24. Deployment Automation

### 24.1 CI/CD Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CI/CD Pipeline                                      │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        Build Stage (GitHub Actions)                  │   │
│  │                                                                     │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐          │   │
│  │  │ Checkout │─▶│  Build   │─▶│  Test    │─▶│  Package │          │   │
│  │  │          │  │          │  │          │  │          │          │   │
│  │  │ • Code   │  │ • Compile│  │ • Unit   │  │ • Image  │          │   │
│  │  │ • Submod │  │ • Lint   │  │ • Integ  │  │ • SBOM   │          │   │
│  │  │          │  │ • Format │  │ • Contract│ │ • Sign   │          │   │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        Scan Stage                                    │   │
│  │                                                                     │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐          │   │
│  │  │  SAST    │  │  DAST    │  │  Vuln    │  │  License │          │   │
│  │  │ (Semgrep)│  │ (OWASP Z)│  │ (Trivy)  │  │ (FOSSA)  │          │   │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        Deploy Stage (ArgoCD)                         │   │
│  │                                                                     │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐          │   │
│  │  │   Dev    │─▶│  Staging │─▶│  Prod    │─▶│   DR     │          │   │
│  │  │  Sync    │  │  Sync    │  │  Sync    │  │  Sync    │          │   │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘          │   │
│  │                                                                     │   │
│  │  Each sync: Validate → Plan → Apply → Verify → Health Check        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 24.2 Build Pipeline Details

```yaml
# .github/workflows/build.yml
name: build
on:
  push:
    branches: [main, 'release/**', 'hotfix/**']
  pull_request:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Setup build environment
        uses: ./.github/actions/setup-build

      - name: Compile and lint
        run: |
          make lint
          make compile

      - name: Run unit tests
        run: make test-unit
        # Coverage gate: 80% minimum

      - name: Run integration tests
        run: make test-integration
        # Spins up testcontainers for PostgreSQL, Redis, Kafka

      - name: Build container image
        run: |
          docker build \
            --tag ghcr.io/grc-claw/${{ matrix.service }}:${{ github.sha }} \
            --tag ghcr.io/grc-claw/${{ matrix.service }}:latest \
            --file Dockerfile \
            .

      - name: Generate SBOM
        run: |
          syft ghcr.io/grc-claw/${{ matrix.service }}:${{ github.sha }} \
            -o spdx-json > sbom.json

      - name: Scan image
        run: |
          trivy image \
            --severity CRITICAL,HIGH \
            --exit-code 1 \
            ghcr.io/grc-claw/${{ matrix.service }}:${{ github.sha }}

      - name: Sign image
        run: |
          cosign sign --yes \
            ghcr.io/grc-claw/${{ matrix.service }}@${{ steps.build.outputs.digest }}

      - name: Push image
        run: |
          docker push ghcr.io/grc-claw/${{ matrix.service }}:${{ github.sha }}
          docker push ghcr.io/grc-claw/${{ matrix.service }}:latest

      - name: Update GitOps repo
        run: |
          # Update image tag in GitOps repo
          yq e '.spec.template.spec.containers[0].image = "ghcr.io/grc-claw/${{ matrix.service }}:${{ github.sha }}"' \
            -i gitops/environments/development/us-east-1/${{ matrix.service }}/deployment.yaml
          git commit -am "chore: update ${{ matrix.service }} to ${{ github.sha }}"
          git push
```

### 24.3 Test Automation in Pipeline

| Test Type | Stage | Tool | Duration | Gate |
|-----------|-------|------|----------|------|
| Unit tests | Build | pytest / go test | 2-5 min | 80% coverage |
| Integration tests | Build | testcontainers | 5-10 min | All pass |
| Contract tests | Build | Pact | 3-5 min | All pass |
| SAST | Scan | Semgrep | 2-3 min | 0 CRITICAL |
| DAST | Scan | OWASP ZAP | 10-15 min | 0 HIGH |
| Vulnerability | Scan | Trivy | 2-3 min | 0 CRITICAL, 0 HIGH |
| License | Scan | FOSSA | 1-2 min | No GPL/AGPL |
| E2E tests | Staging | Playwright / k6 | 15-30 min | All pass |
| Performance | Staging | k6 / Locust | 10-15 min | p99 < 50ms |
| Chaos | Staging | Litmus | 15-20 min | Recovery < 5min |
| Smoke | Production | Custom | 2-3 min | All pass |

### 24.4 Infrastructure as Code

All infrastructure is defined as code and versioned in Git:

```
infrastructure/
├── terraform/
│   ├── modules/
│   │   ├── eks/
│   │   ├── gke/
│   │   ├── aks/
│   │   ├── rds/
│   │   ├── elasticache/
│   │   ├── msk/
│   │   ├── s3/
│   │   ├── iam/
│   │   └── networking/
│   ├── environments/
│   │   ├── production/
│   │   │   ├── us-east-1/
│   │   │   │   ├── main.tf
│   │   │   │   ├── variables.tf
│   │   │   │   ├── outputs.tf
│   │   │   │   └── terraform.tfvars
│   │   │   ├── eu-west-1/
│   │   │   └── ap-south-1/
│   │   ├── staging/
│   │   └── dr/
│   └── backend/
│       ├── production.tfbackend
│       └── staging.tfbackend
├── crossplane/
│   ├── compositions/
│   │   ├── database.yaml
│   │   ├── cache.yaml
│   │   ├── queue.yaml
│   │   └── storage.yaml
│   └── providers/
│       ├── aws.yaml
│       ├── gcp.yaml
│       └── azure.yaml
└── ansible/
    ├── playbooks/
    │   ├── k8s-bootstrap.yml
    │   ├── vault-setup.yml
    │   └── monitoring-setup.yml
    └── inventory/
        ├── production/
        └── staging/
```

### 24.5 Deployment Orchestration

```yaml
# Deployment orchestration with ArgoCD sync waves
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: grc-claw-full-sync
  namespace: argocd
  annotations:
    argocd.argoproj.io/sync-wave: "0"
spec:
  project: grc-claw-production
  source:
    repoURL: https://github.com/grc-claw/grc-claw-gitops.git
    targetRevision: HEAD
    path: environments/production/us-east-1
  destination:
    server: https://prod-us-east-1.grc-claw.internal
    namespace: grc-claw
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
      - PrunePropagationPolicy=foreground
      - PruneLast=true
      - RespectIgnoreDifferences=true
    retry:
      limit: 5
      backoff:
        duration: 5s
        factor: 2
        maxDuration: 3m
```

---

## 25. Environment Management

### 25.1 Environment Hierarchy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Environment Hierarchy                                  │
│                                                                             │
│  ┌─────────────┐                                                            │
│  │ Production  │  ← Live governance enforcement, 99.95% SLA                │
│  │             │     Full replication, multi-region, multi-cloud           │
│  └──────┬──────┘                                                            │
│         │ promote (gate: E2E + perf + chaos)                                │
│  ┌──────▼──────┐                                                            │
│  │   Staging   │  ← Pre-production validation, 99.5% SLA                   │
│  │             │     Anonymized data, full feature parity                   │
│  └──────┬──────┘                                                            │
│         │ promote (gate: all tests pass)                                    │
│  ┌──────▼──────┐                                                            │
│  │ Development │  ← Feature development, 99% SLA                            │
│  │             │     Synthetic data, single region                          │
│  └──────┬──────┘                                                            │
│         │ spin up (on-demand)                                               │
│  ┌──────▼──────┐                                                            │
│  │   Ephemeral │  ← PR preview, integration testing                        │
│  │             │     Synthetic data, auto-destroy after 24h                 │
│  └─────────────┘                                                            │
│                                                                             │
│  ┌─────────────┐                                                            │
│  │     DR      │  ← Disaster recovery standby, 99.9% SLA                   │
│  │             │     Cross-region replica, scaled-to-0 microservices        │
│  └─────────────┘                                                            │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 25.2 Environment Promotion

```yaml
# Promotion pipeline
promotion:
  dev_to_staging:
    trigger: merge to main
    automated: true
    steps:
      - sync_argocd: staging
      - run_e2e_tests: staging
      - verify_metrics: staging
    rollback_on_failure: true

  staging_to_production:
    trigger: manual_approval
    automated: true
    steps:
      - sync_argocd: production
      - run_smoke_tests: production
      - canary_deploy: 5% → 20% → 50% → 100%
      - verify_slo: production
    rollback_on_failure: true
    approval:
      required: true
      approvers: [sre-oncall, platform-lead]
      timeout: 24h

  production_to_dr:
    trigger: scheduled (weekly)
    automated: true
    steps:
      - sync_argocd: dr
      - verify_replication: dr
      - run_smoke_tests: dr
    rollback_on_failure: false
```

### 25.3 Ephemeral Environments

```yaml
# Ephemeral environment for PR preview
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: grc-claw-pr-{{ .pr.number }}
  namespace: argocd
  annotations:
    argocd.argoproj.io/sync-wave: "1"
  finalizers:
    - resources-finalizer.argocd.argoproj.io
spec:
  project: grc-claw-ephemeral
  source:
    repoURL: https://github.com/grc-claw/grc-claw-gitops.git
    targetRevision: HEAD
    path: environments/ephemeral
    helm:
      valueFiles:
        - values-ephemeral.yaml
      parameters:
        - name: pr.number
          value: "{{ .pr.number }}"
        - name: pr.branch
          value: "{{ .pr.branch }}"
        - name: image.tag
          value: "{{ .pr.sha }}"
  destination:
    server: https://dev-us-east-1.grc-claw.internal
    namespace: grc-claw-pr-{{ .pr.number }}
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
  # Auto-destroy after 24 hours
  # Implemented via ArgoCD Application TTL or external controller
```

### 25.4 Environment-Specific Configuration

| Setting | Production | Staging | Development | Ephemeral |
|---------|-----------|---------|-------------|-----------|
| Replicas (min) | 3 | 2 | 1 | 1 |
| Replicas (max) | 20 | 5 | 2 | 2 |
| CPU request | 1000m | 500m | 250m | 250m |
| Memory request | 1Gi | 512Mi | 256Mi | 256Mi |
| Log level | WARN | INFO | DEBUG | DEBUG |
| Trace sampling | 10% | 50% | 100% | 100% |
| Feature flags | All | All | All | All |
| Data | Live | Anonymized | Synthetic | Synthetic |
| Network policies | Strict | Strict | Relaxed | Relaxed |
| Pod disruption budget | minAvailable: 2 | minAvailable: 1 | None | None |
| Backup | Daily | Weekly | None | None |
| DR | Cross-region | None | None | None |

### 25.5 Environment Provisioning

```bash
#!/bin/bash
# scripts/provision-environment.sh

ENVIRONMENT=$1
REGION=$2

# 1. Create Kubernetes cluster (if not exists)
eksctl create cluster \
  --name grc-claw-${ENVIRONMENT}-${REGION} \
  --region ${REGION} \
  --node-type m6i.2xlarge \
  --nodes-min 3 \
  --nodes-max 50 \
  --managed

# 2. Install infrastructure components
helm install istio istio/istio --namespace istio-system
helm install cert-manager jetstack/cert-manager --namespace cert-manager
helm install external-secrets external-secrets/external-secrets --namespace external-secrets
helm install argocd argo/argo-cd --namespace argocd

# 3. Deploy application stack
argocd app create grc-claw-${ENVIRONMENT} \
  --repo https://github.com/grc-claw/grc-claw-gitops.git \
  --path environments/${ENVIRONMENT}/${REGION} \
  --dest-server https://kubernetes.default.svc \
  --dest-namespace grc-claw \
  --sync-policy automated

# 4. Verify deployment
kubectl wait --for=condition=ready pod -l app=pdp-service --timeout=300s
kubectl wait --for=condition=ready pod -l app=pep-gateway --timeout=300s

# 5. Run smoke tests
./scripts/smoke-tests.sh ${ENVIRONMENT}

echo "Environment ${ENVIRONMENT} in ${REGION} is ready"
```

---

## 26. Configuration Management

### 26.1 Configuration Hierarchy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      Configuration Hierarchy                                  │
│                                                                             │
│  Priority (highest to lowest):                                              │
│                                                                             │
│  1. Environment variables (container runtime)                               │
│  2. Kubernetes Secrets (sensitive config)                                   │
│  3. Kubernetes ConfigMaps (non-sensitive config)                            │
│  4. Helm values (environment-specific)                                      │
│  5. Application defaults (built into image)                                 │
│                                                                             │
│  Config sources:                                                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                     │
│  │ GitOps Repo  │  │    Vault     │  │   Feature    │                     │
│  │ (versioned)  │  │  (secrets)   │  │   Flags      │                     │
│  │              │  │              │  │              │                     │
│  │ • App config │  │ • DB creds   │  │ • Runtime    │                     │
│  │ • Helm values│  │ • API keys   │  │   toggles    │                     │
│  │ • Kustomize  │  │ • TLS certs  │  │ • A/B tests  │                     │
│  │   overlays   │  │ • Encryption │  │ • Rollout    │                     │
│  │              │  │   keys       │  │   %          │                     │
│  └──────────────┘  └──────────────┘  └──────────────┘                     │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 26.2 Configuration Validation

```yaml
# Config validation schema
apiVersion: grc-claw.io/v1alpha1
kind: ConfigSchema
metadata:
  name: pdp-service-config
  namespace: grc-claw-control-plane
spec:
  schema:
    type: object
    required:
      - log_level
      - max_connections
      - cache_ttl_seconds
    properties:
      log_level:
        type: string
        enum: [DEBUG, INFO, WARN, ERROR]
        default: INFO
      max_connections:
        type: integer
        minimum: 10
        maximum: 10000
        default: 1000
      cache_ttl_seconds:
        type: integer
        minimum: 60
        maximum: 3600
        default: 300
      enable_metrics:
        type: boolean
        default: true
      decision_cache_size:
        type: integer
        minimum: 1000
        maximum: 1000000
        default: 50000
  validation:
    # Validated at admission time by OPA/Gatekeeper
    admission: true
    # Validated at startup by application
    startup: true
    # Validated at runtime by config reloader
    runtime: true
```

### 26.3 Config Drift Detection

```yaml
# Config drift detection with ArgoCD
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: grc-claw-control-plane
  annotations:
    # Self-heal corrects drift automatically
    argocd.argoproj.io/self-heal: "true"
    # Ignore replica count differences (managed by HPA)
    argocd.argoproj.io/ignore-differences: |
      [
        {
          "group": "apps",
          "kind": "Deployment",
          "jsonPointers": ["/spec/replicas"]
        }
      ]
spec:
  syncPolicy:
    automated:
      selfHeal: true
      prune: true
```

**Drift detection process:**
1. ArgoCD continuously compares desired state (Git) with actual state (cluster)
2. Drift is detected when actual state deviates from desired state
3. `selfHeal: true` automatically corrects drift by re-applying desired state
4. Drift events are logged and alerted
5. Persistent drift (> 3 self-heal failures) triggers investigation

### 26.4 Configuration Versioning and Audit

```yaml
# Configuration change audit log
apiVersion: grc-claw.io/v1alpha1
kind: ConfigChange
metadata:
  name: pdp-config-change-001
  namespace: grc-claw-control-plane
spec:
  component: pdp-service
  environment: production
  change_type: update
  author: developer@grc-claw.io
  timestamp: "2026-10-01T12:00:00Z"
  diff:
    - field: cache_ttl_seconds
      old_value: "300"
      new_value: "600"
      reason: "Reduce database load during peak hours"
    - field: max_connections
      old_value: "1000"
      new_value: "2000"
      reason: "Support increased agent count"
  approval:
    approved_by: sre-oncall@grc-claw.io
    approved_at: "2026-10-01T12:05:00Z"
  rollback:
    automatic: true
    trigger: "error_rate > 1% or p99 > 50ms"
    window: "10m"
```

### 26.5 ConfigMap Management

```yaml
# Application ConfigMap
apiVersion: v1
kind: ConfigMap
metadata:
  name: pdp-service-config
  namespace: grc-claw-control-plane
  annotations:
    grc.claw.io/config-version: "v1.2.3"
    grc.claw.io/config-hash: "a1b2c3d4"
data:
  config.yaml: |
    server:
      port: 8080
      grpc_port: 9090
      max_concurrent_requests: 10000
    
    cache:
      type: redis
      ttl_seconds: 300
      max_entries: 50000
      eviction_policy: lru
    
    policy:
      engine: opa
      bundle_refresh_interval: 30s
      decision_cache_ttl: 300s
      max_evaluation_time_ms: 50
    
    metrics:
      enabled: true
      port: 9090
      path: /metrics
    
    tracing:
      enabled: true
      sampler: 0.1
      endpoint: http://otel-collector:4317
    
    logging:
      level: INFO
      format: json
      output: stdout
```

---

## 27. Secret Management (Expanded)

### 27.1 Secret Lifecycle

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  Create  │───▶│  Distribute│──▶│  Use    │───▶│  Rotate  │───▶│  Revoke  │
│          │    │          │    │          │    │          │    │          │
│ • Vault  │    │ • ESO    │    │ • App   │    │ • Auto   │    │ • Vault  │
│   engine │    │   sync   │    │   reads │    │   rotate │    │   revoke │
│ • KMS    │    │ • K8s    │    │ • Sidecar│   │ • Manual │    │ • KMS    │
│   key    │    │   secret │    │   inject │    │   rotate │    │   delete │
└──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘
     │               │               │               │               │
     ▼               ▼               ▼               ▼               ▼
  Audit log     Access log      Usage metrics   Rotation log    Revocation
  (immudb)      (SIEM)          (Prometheus)     (immudb)        log (SIEM)
```

### 27.2 Secret Types and Storage

| Secret Type | Storage | Rotation | Access Pattern |
|-------------|---------|----------|----------------|
| Database credentials | Vault (dynamic) | 30 days | App reads via ESO |
| API tokens | Vault (KV v2) | 7 days | App reads via ESO |
| mTLS certificates | Vault PKI + cert-manager | 24 hours | Sidecar injection |
| Encryption keys (DEK) | Vault Transit | 90 days | App calls Vault API |
| Signing keys | HSM (manual) | 1 year | App calls HSM |
| Vault tokens | Kubernetes auth | 24 hours | Auto-generated |
| Cloud credentials | Vault (AWS/GCP/Azure) | 24 hours | App reads via ESO |
| Feature flag secrets | Vault (KV v2) | N/A | App reads via ESO |
| GitOps repo secrets | SOPS (encrypted in Git) | 90 days | ArgoCD decrypts |
| Container registry | Vault (KV v2) | 30 days | CI/CD reads |

### 27.3 Secret Rotation Automation

```yaml
# Automated secret rotation with Vault
apiVersion: grc-claw.io/v1alpha1
kind: SecretRotationPolicy
metadata:
  name: db-credentials-rotation
  namespace: grc-claw-data
spec:
  secret_path: database/creds/grc-claw-app
  rotation_schedule: "0 0 1 * *"  # Monthly
  rotation_window: "2h"
  strategy:
    type: dual  # dual → single → cleanup
    dual_write_duration: "24h"
    single_read_duration: "1h"
    cleanup_duration: "1h"
  notification:
    before: "24h"
    after: "1h"
    channels:
      - slack:#security
      - pagerduty:security-oncall
  rollback:
    automatic: true
    trigger: "connection_failure > 1%"
    window: "5m"
```

**Rotation process:**
1. Vault generates new credentials (dual-write phase)
2. External Secrets Operator syncs new credentials to K8s Secrets
3. Applications pick up new credentials (rolling restart if needed)
4. Old credentials remain valid for 24h (overlap period)
5. Applications switch to new credentials
6. Old credentials revoked after 24h
7. Audit log updated with rotation event

### 27.4 Secret Scanning and Detection

```yaml
# Secret scanning in CI/CD
secret_scanning:
  # Pre-commit hooks
  pre_commit:
    tool: gitleaks
    fail_on_detection: true
  
  # CI pipeline
  ci:
    tool: trufflehog
    scan_depth: full_history
    fail_on_detection: true
  
  # GitOps repo
  gitops:
    tool: sops + age
    encryption: required
    fail_on_plaintext: true
  
  # Runtime
  runtime:
    tool: falco
    rules:
      - unauthorized_secret_access
      - secret_exfiltration
      - credential_harvesting
```

### 27.5 Secret Access Patterns

```yaml
# Pattern 1: External Secrets Operator (default)
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: pdp-service-db-credentials
  namespace: grc-claw-control-plane
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: vault-backend
    kind: ClusterSecretStore
  target:
    name: pdp-service-db-credentials
    creationPolicy: Owner
  data:
    - secretKey: username
      remoteRef:
        key: grc-claw/production/pdp-service
        property: db-username
    - secretKey: password
      remoteRef:
        key: grc-claw/production/pdp-service
        property: db-password

---
# Pattern 2: Vault Agent Sidecar
apiVersion: apps/v1
kind: Deployment
metadata:
  name: pdp-service
  namespace: grc-claw-control-plane
spec:
  template:
    spec:
      serviceAccountName: pdp-service
      containers:
        - name: pdp
          image: ghcr.io/grc-claw/pdp-service:v1.2.0
          volumeMounts:
            - name: vault-secrets
              mountPath: /vault/secrets
              readOnly: true
      # Vault Agent Sidecar
        - name: vault-agent
          image: hashicorp/vault:1.15
          args:
            - agent
            - -config=/etc/vault/config.hcl
          volumeMounts:
            - name: vault-config
              mountPath: /etc/vault
            - name: vault-secrets
              mountPath: /vault/secrets
      volumes:
        - name: vault-config
          configMap:
            name: vault-agent-config
        - name: vault-secrets
          emptyDir: {}

---
# Pattern 3: Vault CSI Driver
apiVersion: secrets-store.csi.x-k8s.io/v1
kind: SecretProviderClass
metadata:
  name: vault-pdp-secrets
  namespace: grc-claw-control-plane
spec:
  provider: vault
  parameters:
    vaultAddress: "https://vault.grc-claw.internal:8200"
    roleName: "pdp-service"
    objects: |
      - objectName: "db-username"
        secretPath: "secret/data/grc-claw/production/pdp-service"
        secretKey: "db-username"
      - objectName: "db-password"
        secretPath: "secret/data/grc-claw/production/pdp-service"
        secretKey: "db-password"
  secretObjects:
    - secretName: pdp-service-db-credentials
      type: Opaque
      data:
        - objectName: db-username
          key: username
        - objectName: db-password
          key: password
```

---

## 28. Deployment Monitoring and Rollback

### 28.1 Deployment Health Monitoring

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Deployment Health Monitoring                               │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    Pre-Deployment Checks                             │   │
│  │  • Image signature verified (Cosign)                                │   │
│  │  • SBOM validated                                                   │   │
│  │  • Vulnerability scan passed (0 CRITICAL, 0 HIGH)                   │   │
│  │  • Helm chart linted and validated                                  │   │
│  │  • K8s manifests validated (kubeval)                                │   │
│  │  • Database migrations tested                                       │   │
│  │  • Config validated against schema                                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    During Deployment                                 │   │
│  │  • Pod startup time < 30s                                           │   │
│  │  • Health checks passing (liveness, readiness)                      │   │
│  │  • No crash loops                                                   │   │
│  │  • Resource usage within limits                                     │   │
│  │  • No configuration errors                                          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    Post-Deployment Verification                      │   │
│  │  • Error rate < 0.1%                                                │   │
│  │  • p99 latency < 50ms                                               │   │
│  │  • Decision accuracy > 99.9%                                        │   │
│  │  • All health endpoints returning 200                              │   │
│  │  • All dependencies connected                                       │   │
│  │  • All metrics flowing to Prometheus                                │   │
│  │  • All logs flowing to Loki                                         │   │
│  │  • All traces visible in Tempo                                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 28.2 Deployment Metrics

| Metric | Source | Threshold | Alert |
|--------|--------|-----------|-------|
| Deployment duration | ArgoCD | < 10 min | P3 |
| Pod startup time | Kubernetes | < 30s | P2 |
| Error rate | Prometheus | > 0.1% | P2 |
| p99 latency | Prometheus | > 50ms | P2 |
| CPU utilization | Prometheus | > 80% | P3 |
| Memory utilization | Prometheus | > 85% | P3 |
| Crash loop count | Kubernetes | > 0 | P1 |
| Config reload errors | App logs | > 0 | P2 |
| Health check failures | Kubernetes | > 0 | P1 |
| Decision accuracy | Custom metric | < 99.9% | P1 |

### 28.3 Automated Rollback Triggers

```yaml
# Automated rollback policy
apiVersion: grc-claw.io/v1alpha1
kind: RollbackPolicy
metadata:
  name: pdp-service-rollback
  namespace: grc-claw-control-plane
spec:
  component: pdp-service
  triggers:
    # Metric-based rollback
    - name: error-rate
      metric: http_requests_total{status=~"5.."}
      threshold: "> 0.01"  # > 1% error rate
      window: "2m"
      action: rollback
    
    - name: latency
      metric: http_request_duration_seconds
      threshold: "> 0.050"  # > 50ms p99
      window: "2m"
      action: rollback
    
    - name: decision-accuracy
      metric: grc_decision_accuracy
      threshold: "< 0.999"  # < 99.9% accuracy
      window: "5m"
      action: rollback
    
    # Health-based rollback
    - name: health-check
      metric: health_check_failures
      threshold: "> 0"
      window: "1m"
      action: rollback
    
    # Crash loop rollback
    - name: crash-loop
      metric: crash_loop_count
      threshold: "> 0"
      window: "1m"
      action: rollback
    
    # Config error rollback
    - name: config-error
      metric: config_reload_errors
      threshold: "> 0"
      window: "1m"
      action: rollback
  
  rollback:
    strategy: automatic
    target: previous_stable_revision
    max_rollback_time: "5m"
    notification:
      - slack:#deployments
      - pagerduty:deploy-oncall
    post_rollback:
      - run_smoke_tests
      - notify_stakeholders
      - create_incident_ticket
```

### 28.4 Rollback Procedures

#### Automatic Rollback (ArgoCD)

```yaml
# ArgoCD automated rollback
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: grc-claw-control-plane
  annotations:
    argocd.argoproj.io/sync-retry-limit: "5"
    argocd.argoproj.io/revision-history-limit: "10"
spec:
  syncPolicy:
    automated:
      selfHeal: true
    retry:
      limit: 5
      backoff:
        duration: 5s
        factor: 2
        maxDuration: 3m
```

#### Manual Rollback

```bash
#!/bin/bash
# scripts/rollback.sh

COMPONENT=$1
ENVIRONMENT=$2
REVISION=$3  # Optional: specific revision to rollback to

if [ -z "$REVISION" ]; then
  # Rollback to previous stable revision
  REVISION=$(argocd app history grc-claw-${COMPONENT} -n argocd | head -2 | tail -1 | awk '{print $1}')
fi

echo "Rolling back ${COMPONENT} in ${ENVIRONMENT} to revision ${REVISION}"

# 1. Pause ArgoCD sync
argocd app pause grc-claw-${COMPONENT} -n argocd

# 2. Update GitOps repo to target revision
cd grc-claw-gitops
git checkout ${REVISION} -- environments/${ENVIRONMENT}/us-east-1/${COMPONENT}/
git commit -am "rollback: ${COMPONENT} to ${REVISION}"
git push

# 3. Resume ArgoCD sync
argocd app resume grc-claw-${COMPONENT} -n argocd

# 4. Wait for sync
argocd app wait grc-claw-${COMPONENT} -n argocd --timeout 300

# 5. Verify rollback
./scripts/smoke-tests.sh ${ENVIRONMENT}

echo "Rollback complete"
```

#### Database Rollback

```bash
#!/bin/bash
# scripts/rollback-db.sh

# Database rollback uses Point-in-Time Recovery (PITR)
# PostgreSQL: pgBackRest PITR
# Redis: RDB snapshot restore
# Kafka: Log segment replay

rollback_postgresql() {
  local target_time=$1  # ISO 8601 timestamp
  
  # 1. Stop writes
  kubectl exec -it postgresql-0 -- pg_ctl stop -m fast
  
  # 2. Restore from backup
  pgbackrest restore \
    --target-time="${target_time}" \
    --target-action=promote
  
  # 3. Verify data integrity
  psql -c "SELECT count(*) FROM policies;"
  
  # 4. Resume writes
  kubectl exec -it postgresql-0 -- pg_ctl start
}

rollback_redis() {
  local snapshot=$1
  
  # 1. Stop Redis
  kubectl exec -it redis-0 -- redis-cli SHUTDOWN
  
  # 2. Restore from RDB snapshot
  kubectl cp ${snapshot} redis-0:/var/lib/redis/dump.rdb
  
  # 3. Start Redis
  kubectl exec -it redis-0 -- redis-server /etc/redis/redis.conf
}
```

### 28.5 Post-Rollback Verification

```yaml
# Post-rollback verification checklist
post_rollback_verification:
  immediate:
    - health_checks_passing
    - error_rate_below_threshold
    - latency_below_threshold
    - no_crash_loops
    - all_pods_ready
  
  short_term:
    - decision_accuracy_restored
    - all_metrics_flowing
    - all_logs_flowing
    - all_traces_visible
    - all_dependencies_connected
  
  medium_term:
    - slo_within_budget
    - no_alert_firing
    - all_dashboards_populated
    - all_backups_completing
    - all_replication_healthy
  
  notification:
    - slack:#deployments
    - slack:#incidents
    - pagerduty:resolve
    - email:stakeholders
```

### 28.6 Deployment Monitoring Dashboard

```yaml
# Grafana dashboard for deployment monitoring
apiVersion: grc-claw.io/v1alpha1
kind: Dashboard
metadata:
  name: deployment-monitoring
  namespace: grc-claw-observability
spec:
  title: "GRC_Claw Deployment Monitoring"
  panels:
    - title: "Deployment Status"
      type: table
      targets:
        - expr: argocd_application_info
          legend: "{{name}}: {{health_status}}"
    
    - title: "Deployment Duration"
      type: graph
      targets:
        - expr: argocd_application_reconcile_duration_seconds
          legend: "{{name}}"
    
    - title: "Error Rate by Component"
      type: graph
      targets:
        - expr: |
            sum(rate(http_requests_total{status=~"5.."}[5m])) by (service)
            /
            sum(rate(http_requests_total[5m])) by (service)
          legend: "{{service}}"
    
    - title: "p99 Latency by Component"
      type: graph
      targets:
        - expr: |
            histogram_quantile(0.99,
              sum(rate(http_request_duration_seconds_bucket[5m])) by (le, service)
            )
          legend: "{{service}}"
    
    - title: "Rollback Events"
      type: table
      targets:
        - expr: grc_deployment_rollback_total
          legend: "{{component}}: {{reason}}"
    
    - title: "Config Drift"
      type: graph
      targets:
        - expr: argocd_application_sync_total{status!="Synced"}
          legend: "{{name}}"
    
    - title: "Pod Restarts"
      type: graph
      targets:
        - expr: |
            sum(rate(kube_pod_container_status_restarts_total[15m])) by (pod)
          legend: "{{pod}}"
    
    - title: "Resource Utilization"
      type: graph
      targets:
        - expr: |
            sum(rate(container_cpu_usage_seconds_total[5m])) by (pod)
            /
            sum(kube_pod_container_resource_requests{resource="cpu"}) by (pod)
          legend: "{{pod}} CPU"
        - expr: |
            sum(container_memory_working_set_bytes) by (pod)
            /
            sum(kube_pod_container_resource_requests{resource="memory"}) by (pod)
          legend: "{{pod}} Memory"
```

### 28.7 Canary Analysis and Auto-Rollback

```yaml
# Argo Rollouts analysis with auto-rollback
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: pdp-service
  namespace: grc-claw-control-plane
spec:
  replicas: 10
  strategy:
    canary:
      canaryService: pdp-service-canary
      stableService: pdp-service
      trafficRouting:
        istio:
          virtualService:
            name: pdp-service-canary
      steps:
        - setWeight: 5
        - pause: { duration: 10m }
        - analysis:
            templates:
              - templateName: pdp-success-rate
              - templateName: pdp-latency
            args:
              - name: service-name
                value: pdp-service-canary
        - setWeight: 20
        - pause: { duration: 10m }
        - analysis:
            templates:
              - templateName: pdp-success-rate
              - templateName: pdp-latency
              - templateName: pdp-decision-accuracy
        - setWeight: 50
        - pause: { duration: 15m }
        - analysis:
            templates:
              - templateName: pdp-success-rate
              - templateName: pdp-latency
              - templateName: pdp-decision-accuracy
        - setWeight: 100
        - pause: { duration: 5m }
      analysis:
        successfulRunHistoryLimit: 3
        unsuccessfulRunHistoryLimit: 3
        # Auto-rollback on analysis failure
        rollback:
          enabled: true
          # Rollback to stable revision
          target: stable
```

---

## 29. Appendix A: Technology Summary

| Layer | Technology | Version |
|-------|-----------|---------|
| Container runtime | containerd | 1.7+ |
| Orchestration | Kubernetes | 1.28+ |
| Service mesh | Istio | 1.20+ |
| Ingress | NGINX Ingress Controller | 1.9+ |
| API Gateway | Kong | 3.5+ |
| Policy engine | OPA | 0.60+ |
| Policy language | Cedar | 3.0+ |
| Database | PostgreSQL | 16+ |
| Cache | Redis | 7.2+ |
| Message queue | Kafka | 3.6+ |
| Object storage | MinIO | RELEASE.2024+ |
| Graph database | Neo4j | 5+ |
| Immutable store | immudb | 1.9+ |
| Secrets | HashiCorp Vault | 1.15+ |
| Identity | SPIFFE/SPIRE | 1.8+ |
| Observability | OpenTelemetry | 1.20+ |
| Metrics | Prometheus | 2.48+ |
| Logs | Loki | 3.0+ |
| Traces | Tempo | 2.3+ |
| Dashboards | Grafana | 10.2+ |
| GitOps | ArgoCD | 2.9+ |
| Progressive Delivery | Argo Rollouts | 0.32+ |
| Serverless | Knative | 1.12+ |
| Event-driven | Knative Eventing | 1.12+ |
| Feature flags | Unleash / Flagr | 5.0+ / 1.1+ |
| Secrets sync | External Secrets Operator | 0.9+ |
| Image signing | Cosign (Sigstore) | 2.2+ |
| Vulnerability scanning | Trivy | 0.47+ |
| SBOM | Syft | 0.95+ |
| Cost management | Kubecost | 2.0+ |
| Cluster autoscaling | Karpenter | 0.34+ |
| CI/CD | GitHub Actions | N/A |
| Helm | Helm | 3.13+ |
| Cert management | cert-manager | 1.13+ |
| Edge computing | K3s / MicroK8s | 1.28+ |
| Multi-cloud | Crossplane | 1.14+ |
| Chaos engineering | Litmus | 3.0+ |
| SLO monitoring | Sloth | 0.11+ |

---

## 30. Appendix B: Glossary

| Term | Definition |
|------|------------|
| **PDP** | Policy Decision Point — evaluates policies and returns decisions |
| **PEP** | Policy Enforcement Point — intercepts actions and enforces decisions |
| **HPA** | Horizontal Pod Autoscaler — scales pod count based on metrics |
| **VPA** | Vertical Pod Autoscaler — adjusts pod resource requests/limits |
| **PDB** | Pod Disruption Budget — limits voluntary disruptions |
| **SLO** | Service Level Objective — target reliability metric |
| **RPO** | Recovery Point Objective — maximum acceptable data loss |
| **RTO** | Recovery Time Objective — maximum acceptable downtime |
| **WORM** | Write Once Read Many — immutable storage for evidence |
| **mTLS** | Mutual TLS — bidirectional certificate authentication |
| **SVID** | SPIFFE Verifiable Identity Document |
| **SBOM** | Software Bill of Materials |
| **GitOps** | Git-based operational workflow for deployment |
| **ArgoCD** | GitOps continuous delivery tool for Kubernetes |
| **Argo Rollouts** | Kubernetes controller for progressive delivery (canary, blue-green) |
| **Canary** | Progressive delivery strategy routing a small percentage of traffic to new version |
| **Blue-Green** | Deployment strategy with two identical environments, switching traffic atomically |
| **Feature Flag** | Runtime toggle enabling/disabling features without deployment |
| **Knative** | Kubernetes-based serverless platform with scale-to-zero |
| **Karpenter** | Kubernetes node provisioning and autoscaling tool |
| **FinOps** | Financial operations — framework for cloud cost management |
| **Spot Instance** | Discounted cloud compute capacity with interruption risk |
| **Edge Computing** | Distributed computing at the network edge, near data sources |
| **GSLB** | Global Server Load Balancing — DNS-based traffic distribution across regions |
| **Cell** | Independent, self-contained deployment unit serving a subset of tenants |
| **Crossplane** | Kubernetes add-on for multi-cloud infrastructure management |
| **External Secrets Operator** | Kubernetes operator syncing secrets from external stores (Vault, AWS SM) |
| **Trunk-Based Development** | Branching strategy with short-lived feature branches merged to main |
| **Promotion Gate** | Automated or manual checkpoint that must pass before deployment to next environment |
| **Ephemeral Environment** | Short-lived, on-demand environment for PR preview or testing |
| **Config Drift** | Deviation between desired state (Git) and actual state (cluster) |
| **Self-Heal** | ArgoCD feature that automatically corrects config drift |
| **Secret Rotation** | Automated process of replacing credentials/certificates at defined intervals |
| **Dual-Write Rotation** | Secret rotation strategy where old and new credentials coexist during transition |
| **Vault Agent Sidecar** | Sidecar container that fetches and refreshes secrets from Vault |
| **Vault CSI Driver** | CSI driver that mounts Vault secrets as volumes |
| **SOPS** | Secrets OPerationS — tool for encrypting secrets in Git |
| **Rollback Policy** | Automated rules that trigger rollback based on metric thresholds |
| **Canary Analysis** | Automated evaluation of canary deployment metrics to determine promotion or rollback |
| **PITR** | Point-In-Time Recovery — database restore to a specific timestamp |
| **Cosign** | Sigstore tool for signing and verifying container images |
| **Syft** | Tool for generating SBOMs from container images |
| **Trivy** | Vulnerability scanner for container images and filesystems |
| **Semgrep** | Static analysis tool for finding security vulnerabilities and code patterns |
| **OWASP ZAP** | Web application security scanner (DAST) |
| **FOSSA** | License compliance and open-source risk management tool |
| **Gitleaks** | Tool for detecting hardcoded secrets in Git repositories |
| **Trufflehog** | Tool for finding secrets in Git history and code |
| **Falco** | Runtime security tool for detecting anomalous behavior in containers |
| **Kubeval** | Tool for validating Kubernetes manifests |
| **KEDA** | Kubernetes Event-Driven Autoscaling — scales based on event sources |
| **PgBouncer** | PostgreSQL connection pooler |
| **Patroni** | PostgreSQL HA manager with leader election |
| **MirrorMaker2** | Kafka cross-cluster replication tool |

---

*End of Deployment Specification.*
